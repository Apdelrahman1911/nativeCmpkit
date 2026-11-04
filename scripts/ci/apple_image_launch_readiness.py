"""One owned failed-profile workload's prelaunch observations, never a repair.

Complete, source-defined JSON/plist syntax matches describe the returned bytes,
not an assumed simctl serializer implementation or registration field schema.
Unknown names/values/paths stay private. No registration mapping, inventory,
install, signing, permission mutation, launch, profile or standalone CLI exists.
The owning harness retains its original one launch and all native/profile gates.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import time
import xml.etree.ElementTree as ET

import apple_appinfo_capability as capability
import apple_appinfo_shape as shape
import apple_appinfo_shape_route as route
import ios_ui_application as application

MAX_DEPTH, MAX_NODES = 32, 4096
MAX_RECORD_BYTES, HASH_CHUNK_BYTES = 65536, 1024 * 1024
PRIVATE_DIRECTORY = "image-launch-observation-private"
RECORD_NAME = "image-launch-readiness-observation.json"
PLIST_DOCTYPE = (b'<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
                 b'"http://www.apple.com/DTDs/PropertyList-1.0.dtd">')


class ObservationError(ValueError):
    """Fixed source guards only; no exception body or command payload."""


class InstalledIdentityError(ObservationError):
    """A positive installed-byte/type/identity mismatch, not query unavailability."""


def need(value, guard):
    if not value:
        raise ObservationError(guard)


class _Mapping:
    """Preserve every pair, including duplicates; never infer field semantics."""
    def __init__(self, pairs=()):
        self.pairs = list(pairs)


class _Scalar:
    def __init__(self, kind):
        self.kind = kind


class _AsciiPlist:
    """Finite ASCII plist grammar, including quoted escapes/comments/data.

    Bare ASCII atoms are strings, not guessed booleans, numbers or paths. A
    whole dictionary/array must consume the complete payload; a header, key
    literal, prefix, incomplete tail or successful query cannot admit a format.
    """
    def __init__(self, text):
        self.text, self.index, self.nodes = text, 0, 0

    def skip(self):
        while self.index < len(self.text):
            if self.text[self.index] in " \t\r\n":
                self.index += 1
            elif self.text.startswith("//", self.index):
                end = self.text.find("\n", self.index + 2)
                self.index = len(self.text) if end < 0 else end + 1
            elif self.text.startswith("/*", self.index):
                end = self.text.find("*/", self.index + 2)
                need(end >= 0, "ascii_comment_incomplete")
                self.index = end + 2
            else:
                break

    def take(self, character):
        self.skip()
        need(self.index < len(self.text) and self.text[self.index] == character, "ascii_structure_refused")
        self.index += 1

    def string(self):
        self.skip()
        need(self.index < len(self.text), "ascii_string_incomplete")
        if self.text[self.index] != '"':
            match = re.match(r"[A-Za-z0-9_$./:-]+", self.text[self.index:])
            need(match is not None, "ascii_bare_atom_refused")
            self.index += len(match[0])
            return match[0]
        self.index += 1
        value = []
        escapes = dict(zip('abtnvfr"\\', '\a\b\t\n\v\f\r"\\'))
        while self.index < len(self.text):
            character = self.text[self.index]
            self.index += 1
            if character == '"':
                # Four-digit \U escapes are UTF-16 code units, including pairs.
                return ''.join(value).encode("utf-16-be", errors="surrogatepass").decode("utf-16-be")
            if character != "\\":
                need(ord(character) >= 32 and ord(character) != 127, "ascii_quoted_control_refused")
                value.append(character)
                continue
            need(self.index < len(self.text), "ascii_escape_incomplete")
            escape = self.text[self.index]
            self.index += 1
            if escape in escapes:
                value.append(escapes[escape])
            elif escape == "U":
                digits = self.text[self.index:self.index + 4]
                need(re.fullmatch(r"[0-9A-Fa-f]{4}", digits), "ascii_unicode_escape_refused")
                value.append(chr(int(digits, 16)))
                self.index += 4
            elif escape in "01234567":
                digits = escape
                for _ in range(2):
                    if self.index < len(self.text) and self.text[self.index] in "01234567":
                        digits += self.text[self.index]
                        self.index += 1
                need(int(digits, 8) <= 255, "ascii_octal_escape_refused")
                value.append(chr(int(digits, 8)))
            else:
                raise ObservationError("ascii_escape_refused")
        raise ObservationError("ascii_quoted_string_incomplete")

    def value(self, depth=0):
        self.skip()
        self.nodes += 1
        need(depth <= MAX_DEPTH and self.nodes <= MAX_NODES and self.index < len(self.text),
             "ascii_depth_node_or_tail_bound")
        character = self.text[self.index]
        if character == "{":
            self.index += 1
            pairs = []
            self.skip()
            while self.index < len(self.text) and self.text[self.index] != "}":
                key = self.string()
                self.nodes += 1
                self.take("=")
                pairs.append((key, self.value(depth + 1)))
                self.take(";")
                self.skip()
            self.take("}")
            return _Mapping(pairs)
        if character == "(":
            self.index += 1
            values = []
            self.skip()
            while self.index < len(self.text) and self.text[self.index] != ")":
                values.append(self.value(depth + 1))
                self.skip()
                if self.index < len(self.text) and self.text[self.index] == ")":
                    break
                self.take(",")
                self.skip()
            self.take(")")
            return values
        if character == "<":
            self.index += 1
            end = self.text.find(">", self.index)
            need(end >= 0, "ascii_data_incomplete")
            digits = re.sub(r"[ \t\r\n]", "", self.text[self.index:end])
            need(len(digits) % 2 == 0 and re.fullmatch(r"[0-9A-Fa-f]*", digits), "ascii_data_refused")
            self.index = end + 1
            return _Scalar("data")
        return self.string()

    def parse(self):
        self.skip()
        need(self.index < len(self.text) and self.text[self.index] in "{(", "ascii_root_grammar_unselected")
        value = self.value()
        self.skip()
        need(self.index == len(self.text), "ascii_unconsumed_tail")
        return value


def _xml_plist(body):
    # Permit only the standard inert plist DTD; never entities or external reads.
    need(body.count(PLIST_DOCTYPE) <= 1 and b"<!" not in body.replace(PLIST_DOCTYPE, b""),
         "xml_declaration_or_entity_refused")
    root = ET.fromstring(body)
    need(root.tag == "plist" and root.attrib == {"version": "1.0"} and len(root) == 1 and
         not (root.text or "").strip() and not (root[0].tail or "").strip(), "xml_plist_wrapper_refused")
    need(sum(1 for _ in root.iter()) <= MAX_NODES, "xml_element_bound")

    def value(node, depth=0):
        need(depth <= MAX_DEPTH and not node.attrib, "xml_depth_or_attribute_refused")
        if node.tag in ("dict", "array"):
            need(not (node.text or "").strip() and all(not (child.tail or "").strip() for child in node),
                 "xml_container_text_refused")
            if node.tag == "array":
                return [value(child, depth + 1) for child in node]
            need(len(node) % 2 == 0, "xml_dictionary_pair_refused")
            pairs = []
            for index in range(0, len(node), 2):
                key = node[index]
                need(key.tag == "key" and not key.attrib and not len(key), "xml_dictionary_key_refused")
                pairs.append((key.text or "", value(node[index + 1], depth + 1)))
            return _Mapping(pairs)
        need(not len(node), "xml_scalar_children_refused")
        text = node.text or ""
        if node.tag == "string":
            return text
        if node.tag in ("true", "false"):
            need(not text.strip(), "xml_boolean_text_refused")
            return _Scalar("boolean")
        if node.tag == "integer":
            need(re.fullmatch(r"[+-]?[0-9]+", text.strip()), "xml_integer_refused")
        elif node.tag == "real":
            need(re.fullmatch(r"[+-]?(?:(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?|inf|nan)",
                              text.strip(), re.I), "xml_real_refused")
        elif node.tag == "date":
            dt.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
            need(re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", text), "xml_date_refused")
        elif node.tag == "data":
            base64.b64decode(re.sub(r"[ \t\r\n]", "", text), validate=True)
        else:
            raise ObservationError("xml_scalar_tag_refused")
        return _Scalar(node.tag)

    return value(root[0])


def _binary_plist(body):
    """Inspect a complete bounded bplist00 object table, not a marker guess.

    Only finite plist scalar/array/dictionary kinds are supported. All object
    spans, references, string encodings and disconnected objects are checked;
    cycles/unknown markers/unused non-fill bytes are explicitly unavailable.
    Scalar values are not decoded/exported or assigned registration meanings.
    """
    need(len(body) >= 40 and body[:8] == b"bplist00", "binary_plist_header_refused")
    trailer = body[-32:]
    need(trailer[:6] == b"\0" * 6, "binary_plist_trailer_reserved_refused")
    width, ref_width = trailer[6], trailer[7]
    count, top, table = struct.unpack(">QQQ", trailer[8:])
    need(width in (1, 2, 4, 8) and ref_width in (1, 2, 4, 8) and 0 < count <= MAX_NODES and
         top < count and 8 <= table and table + count * width == len(body) - 32,
         "binary_plist_table_bound")
    offsets = [int.from_bytes(body[table + index * width:table + (index + 1) * width], "big")
               for index in range(count)]
    need(len(set(offsets)) == count and all(8 <= offset < table for offset in offsets), "binary_plist_offsets_refused")
    ordered = sorted(offsets)
    need(ordered[0] == 8, "binary_plist_leading_bytes_refused")
    ends = dict(zip(ordered, [*ordered[1:], table]))
    nodes = []
    for offset in offsets:
        marker, position, end = body[offset], offset + 1, ends[offset]
        kind, info = marker >> 4, marker & 15
        length = info
        if kind in (4, 5, 6, 10, 13) and info == 15:
            need(position < end and body[position] >> 4 == 1 and body[position] & 15 <= 3,
                 "binary_plist_length_integer_refused")
            size = 1 << (body[position] & 15)
            position += 1
            need(position + size <= end, "binary_plist_length_truncated")
            length = int.from_bytes(body[position:position + size], "big")
            position += size
        if kind == 0:
            need(info in (0, 8, 9), "binary_plist_simple_marker_refused")
            node = _Scalar("null" if info == 0 else "boolean")
        elif kind in (1, 2, 3, 8):
            need((kind == 1 and info <= 4) or (kind == 2 and info in (2, 3)) or
                 (kind == 3 and info == 3) or kind == 8, "binary_plist_scalar_marker_refused")
            position += info + 1 if kind == 8 else 1 << info
            node = _Scalar({1: "integer", 2: "real", 3: "date", 8: "uid"}[kind])
        elif kind in (4, 5, 6):
            size = length * (2 if kind == 6 else 1)
            need(size <= capability.MAX_COMMAND_BYTES and position + size <= end, "binary_plist_string_data_bound")
            payload = body[position:position + size]
            node = _Scalar("data") if kind == 4 else payload.decode("utf-16-be" if kind == 6 else "ascii")
            position += size
        elif kind in (10, 13):
            refs = length * (2 if kind == 13 else 1)
            need(length <= MAX_NODES and position + refs * ref_width <= end, "binary_plist_reference_bound")
            indices = tuple(int.from_bytes(body[position + index * ref_width:position + (index + 1) * ref_width], "big")
                            for index in range(refs))
            need(all(index < count for index in indices), "binary_plist_foreign_reference")
            node = (kind, length, indices)
            position += refs * ref_width
        else:
            raise ObservationError("binary_plist_unknown_marker")
        need(position <= end and all(byte == 15 for byte in body[position:end]), "binary_plist_span_or_unused_bytes_refused")
        nodes.append(node)
    converted, active = {}, set()

    def value(index, depth=0):
        need(depth <= MAX_DEPTH and index not in active, "binary_plist_cycle_or_depth_bound")
        if index in converted:
            return converted[index]
        active.add(index)
        node = nodes[index]
        if type(node) is tuple:
            kind, length, indices = node
            values = [value(ref, depth + 1) for ref in indices]
            if kind == 13:
                need(all(type(key) is str for key in values[:length]), "binary_plist_dictionary_key_refused")
                node = _Mapping(zip(values[:length], values[length:]))
            else:
                node = values
        active.remove(index)
        converted[index] = node
        return node

    for index in range(count):
        value(index)
    return value(top)


def _structure(value):
    counts, fields = {}, {name: {"root_key_occurrences": 0, "nested_key_occurrences": 0, "value_kind_counts": {}}
                          for name in shape.FIXED_FIELDS}
    nodes, pairs, duplicates = 0, 0, 0

    def kind(item):
        if type(item) is _Mapping: return "dictionary"
        if type(item) is list: return "array"
        if type(item) is str: return "string"
        if type(item) is _Scalar: return item.kind
        if item is None: return "null"
        if type(item) is bool: return "boolean"
        raise ObservationError("unknown_serialized_value_kind")

    def visit(item, depth=0):
        nonlocal nodes, pairs, duplicates
        nodes += 1
        need(depth <= MAX_DEPTH and nodes <= MAX_NODES, "structure_depth_or_node_bound")
        value_kind = kind(item)
        counts[value_kind] = counts.get(value_kind, 0) + 1
        if type(item) is _Mapping:
            keys = [key for key, _ in item.pairs]
            need(all(type(key) is str for key in keys), "serialized_dictionary_key_refused")
            nodes += len(keys)
            need(nodes <= MAX_NODES, "structure_key_node_bound")
            pairs += len(keys)
            duplicates += len(keys) - len(set(keys))
            for key, child in item.pairs:
                if key in fields:
                    field = fields[key]
                    field["root_key_occurrences" if depth == 0 else "nested_key_occurrences"] += 1
                    child_kind = kind(child)
                    field["value_kind_counts"][child_kind] = field["value_kind_counts"].get(child_kind, 0) + 1
                visit(child, depth + 1)
        elif type(item) is list:
            for child in item:
                visit(child, depth + 1)

    visit(value)
    return {"root_kind": kind(value), "nodes_including_keys": nodes, "value_kind_counts": counts,
            "dictionary_key_occurrences": pairs, "duplicate_dictionary_key_occurrences": duplicates,
            "root_dictionary_key_occurrences": len(value.pairs) if type(value) is _Mapping else None,
            "own_plist_name_key_structures": fields, "registration_field_semantics_verified": False,
            "field_absence_or_registration_absence_proven": False, "raw_unknown_keys_values_or_paths_uploaded": False}


def serialized_structure(body: bytes) -> dict:
    """Whole-payload grammar matches only; never infer a format from delimiters."""
    result = {"status": "unavailable", "complete_payload_grammar_matches": [], "structure": None,
              "unique_representation_format_observed": False, "serializer_implementation_identified": False,
              "appinfo_output_schema_observed": False, "registration_observed": False,
              "raw_unknown_keys_values_or_paths_uploaded": False}
    try:
        need(type(body) is bytes and 0 < len(body) <= capability.MAX_COMMAND_BYTES, "structure_payload_byte_bound")
        candidates = []
        if body.startswith(b"bplist00"):
            candidates.append(("binary-plist-v00", _binary_plist(body)))
        else:
            text = body.decode("utf-8", errors="strict")
            need("\0" not in text, "text_structure_nul_refused")
            if text.lstrip(" \t\r\n").startswith("<"):
                candidates.append(("xml-plist-v1", _xml_plist(body)))
            else:
                def constant(_):
                    raise ObservationError("nonstandard_json_number_refused")
                for name, parse in (
                    ("json", lambda: json.loads(text, object_pairs_hook=_Mapping,
                        parse_int=lambda _: _Scalar("integer"), parse_float=lambda _: _Scalar("real"), parse_constant=constant)),
                    ("ascii-plist", lambda: _AsciiPlist(text).parse()),
                ):
                    try:
                        candidates.append((name, parse()))
                    except (ValueError, UnicodeError, RecursionError):
                        pass
        summaries = []
        for name, value in candidates:
            summary = _structure(value)
            result["complete_payload_grammar_matches"].append(name)
            summaries.append(summary)
        need(summaries and all(summary == summaries[0] for summary in summaries), "unknown_or_ambiguous_payload_structure")
        result.update(status="observed-complete-serialized-structure", structure=summaries[0],
                      unique_representation_format_observed=len(summaries) == 1)
    except (ValueError, TypeError, OverflowError, RecursionError, struct.error, ET.ParseError) as error:
        result["error_type"] = type(error).__name__
        if type(error) is ObservationError:
            result["error_guard"] = str(error)
    return result


def installed_executable_observation(context: shape.OwnedInstallation, deadline: float) -> tuple[dict, tuple]:
    """Exact no-follow read and real-ID host X_OK; never chmod or guest acceptance.

    Trusted regular-file reads have a cooperative total budget, not adversarial
    filesystem-latency/CAS/security certification. Only the already-owned app
    container, executable and generated plist are inspected, never neighbours.
    """
    if not application.installed_identity(context.container, context.bundle, context.signed_hash, context.plist_hash):
        raise InstalledIdentityError("installed_owned_bytes_or_type_changed")
    path = capability.actual_path(capability.Result(context.container.returncode,
        context.container.stdout, context.container.stderr, None))
    executable = path / application.APP_EXECUTABLE
    directory_before, before = path.lstat(), executable.lstat()
    if not stat.S_ISDIR(directory_before.st_mode) or not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise InstalledIdentityError("installed_directory_or_executable_type_changed")
    need(0 < before.st_size <= application.MAX_BINARY_BYTES, "installed_executable_read_bound")
    identity = shape.file_identity(before)
    directory_identity = shape.file_identity(directory_before)
    access_before = os.access(executable, os.X_OK)
    descriptor = os.open(executable, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        if shape.file_identity(os.fstat(descriptor)) != identity:
            raise InstalledIdentityError("installed_executable_open_identity_changed")
        hashes = []
        for _ in range(2):
            os.lseek(descriptor, 0, os.SEEK_SET)
            digest, size = hashlib.sha256(), 0
            while True:
                need(time.monotonic() <= deadline, "installed_identity_observation_budget_exhausted")
                chunk = os.read(descriptor, HASH_CHUNK_BYTES)
                if not chunk:
                    break
                size += len(chunk)
                if size > before.st_size:
                    raise InstalledIdentityError("installed_executable_size_changed")
                digest.update(chunk)
            if size != before.st_size or shape.file_identity(os.fstat(descriptor)) != identity:
                raise InstalledIdentityError("installed_executable_read_identity_changed")
            hashes.append(digest.hexdigest())
        if hashes != [context.signed_hash, context.signed_hash]:
            raise InstalledIdentityError("installed_executable_payload_changed")
    finally:
        os.close(descriptor)
    access_after = os.access(executable, os.X_OK)
    if (shape.file_identity(executable.lstat()) != identity or shape.file_identity(path.lstat()) != directory_identity or
            access_after != access_before):
        raise InstalledIdentityError("installed_executable_path_or_access_changed")
    return ({"status": "observed-exact-installed-executable", "bytes": before.st_size,
             "signed_executable_sha256": context.signed_hash, "installed_path_sha256": shape.digest(str(executable).encode()),
             "installed_file_stat_identity_sha256": shape.digest(json.dumps(identity).encode()),
             "permission_mode": format(stat.S_IMODE(before.st_mode), "04o"),
             "host_real_id_X_OK": access_after, "access_scope": "calling-host-process-real-ids",
             "simulator_executable_acceptance_verified": False, "launch_readiness_verified": False,
             "raw_identity_ids_or_paths_uploaded": False}, (identity, directory_identity))


def require_current_owned_identity(context: shape.OwnedInstallation, observation: dict):
    """Only the original byte/type ownership guard and positive drift may refuse."""
    if (observation.get("installed_identity_drift_observed") is True or
            not application.installed_identity(context.container, context.bundle, context.signed_hash, context.plist_hash)):
        raise InstalledIdentityError("installed_prelaunch_ownership_or_identity_changed")


def observe(context: shape.OwnedInstallation, *, capture=capability.capture, control=capability.control) -> dict:
    """One latched exact query on this installation, before its original launch.

    Query/schema/tool unavailability is diagnostic, never a reason to bypass or
    suppress an otherwise owned original launch. Positive installed identity
    drift is separately returned for the existing owning harness to refuse.
    """
    started = time.monotonic()
    deadline = started + capability.TOTAL_SECONDS
    receipt = {"schema_version": 1, "operation": "owned-image-prelaunch-observation", "status": "unavailable",
               "query_attempted": False, "query_count": 0, "query_timeout_seconds": capability.COMMAND_SECONDS,
               "observation_budget_seconds": capability.TOTAL_SECONDS, "maximum_capture_bytes": capability.MAX_COMMAND_BYTES,
               "installed_executable_before": None, "installed_executable_after": None,
               "installed_identity_drift_observed": False, "installed_identity_stable_observed": None,
               "tool_path_resolution": [], "owned_private_output_removed": False,
               "appinfo_output_schema_observed": False, "registration_observed": False,
               "registered_container_matches_verified_container": None, "registered_executable_identity_verified": None,
               "launch_readiness_verified": False, "root_cause_proven": False, "native_functionality_verified": False,
               "profile_passed": False, "packages_published": False, "release_readiness_certified": False,
               "raw_payload_keys_values_paths_or_inventory_uploaded": False}
    record, descriptor, record_identity, private, private_identity = None, None, None, None, None
    owned, before_identity, context_verified = [], None, False
    try:
        need(type(context) is shape.OwnedInstallation, "current_owning_installation_context_required")
        payload = route.accepted_help(context.root)
        accepted = json.loads(payload)
        # The immutable existing help receipt certifies syntax/tool identity only.
        path = shape.verified_context(context, accepted)
        context_verified = True
        need(shape.digest(payload) == shape.ACCEPTED_HELP_RECEIPT_SHA256 and
             accepted["help"]["known_syntax"] == shape.ACCEPTED_SYNTAX, "accepted_help_syntax_required")
        receipt["installed_executable_before"], before_identity = installed_executable_observation(context, deadline)
        need(shape.shutil.disk_usage(context.root).free >= 8192 * 1024**2 + capability.MAX_COMMAND_BYTES +
             MAX_RECORD_BYTES + HASH_CHUNK_BYTES, "eight_GiB_observation_reserve_required")
        record = context.output / RECORD_NAME
        descriptor = os.open(record, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        record_identity = shape.file_identity(os.fstat(descriptor))
        selected = {}
        for name in ("developer", "simctl", "xcodebuild"):
            need(time.monotonic() + capability.COMMAND_SECONDS <= deadline, "path_resolution_budget_exhausted")
            result = control(capability.COMMANDS[name], context.root, capability.COMMAND_SECONDS)
            need(type(result) is capability.Result and capability.valid(result) and result.exit_code == 0 and
                 not result.stderr, "fixed_selected_tool_path_unavailable")
            receipt["tool_path_resolution"].append({"name": name, **capability.metadata(result)})
            selected[name] = capability.actual_path(result)
        paths = {"xcrun": Path("/usr/bin/xcrun"), "simctl": selected["simctl"], "xcodebuild": selected["xcodebuild"]}
        receipt["tool_identities_before"] = shape.selected_tools(accepted, paths, selected["developer"])
        need(time.monotonic() + capability.COMMAND_SECONDS <= deadline, "observation_budget_exhausted_before_query")
        private = context.output / PRIVATE_DIRECTORY
        private.mkdir(mode=0o700)
        private_identity = shape.private_directory_identity(private)
        receipt.update(source_revision=context.source_revision, capability_receipt_sha256=shape.digest(payload),
                       simulator_uuid_sha256=shape.digest(context.device.encode()), bundle_identifier_sha256=shape.digest(context.bundle.encode()),
                       verified_installed_container_path_sha256=shape.digest(str(path).encode()),
                       query_argv_template=[*shape.QUERY_PREFIX, "<selected UUID>", "<current owned bundle>"],
                       query_attempted=True, query_count=1)
        capture_error = False
        try:
            result = capture((*shape.QUERY_PREFIX, context.device, context.bundle), context.root, capability.COMMAND_SECONDS)
        except capability.CapabilityError as error:
            result = getattr(error, "control_result", None)
            capture_error = True
            need(result is not None, "owned_capture_refused_without_result")
        need(type(result) is capability.Result and (type(result.exit_code) is int or
             (capture_error and result.exit_code is None)) and type(result.stdout) is bytes and type(result.stderr) is bytes and
             len(result.stdout) + len(result.stderr) <= capability.MAX_COMMAND_BYTES and
             result.stop_reason in (None, "timeout", "output-bound", "owned-control-refusal"), "bounded_query_result_required")
        receipt.update(query=capability.metadata(result), streams={})
        if capture_error:
            receipt["owned_control_cleanup_refused"] = True
        for name in ("stdout", "stderr"):
            body, output = getattr(result, name), private / name
            owned_descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(owned_descriptor, "wb") as target:
                target.write(body)
            owned.append((output, shape.file_identity(output.lstat()), shape.digest(body)))
            receipt["streams"][name] = shape.lexical_summary(body)
        need(not capture_error and capability.valid(result) and result.exit_code == 0 and result.stdout and not result.stderr,
             "incomplete_nonzero_empty_or_ambiguous_query")
        receipt["serialized_structure"] = serialized_structure(result.stdout)
        need(shape.verified_context(context, accepted) == path, "installed_context_changed_after_query")
        receipt["tool_identities_after"] = shape.selected_tools(accepted, paths, selected["developer"])
        receipt["status"] = ("observed-owned-prelaunch-structure" if
            receipt["serialized_structure"]["status"] == "observed-complete-serialized-structure" else "unavailable")
    except (OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.SubprocessError) as error:
        receipt.update(status="unavailable", error_type=type(error).__name__)
        if type(error) in (ObservationError, InstalledIdentityError, shape.ShapeError, route.RouteError):
            receipt["error_guard"] = str(error)
        if (type(error) is InstalledIdentityError or
                (type(error) is shape.ShapeError and str(error) == "installed_owned_bytes_required")):
            receipt["installed_identity_drift_observed"] = True
    finally:
        if context_verified:
            try:
                receipt["installed_executable_after"], after_identity = installed_executable_observation(context, deadline)
                if before_identity is not None:
                    receipt["installed_identity_stable_observed"] = before_identity == after_identity
                    if before_identity != after_identity:
                        receipt.update(status="unavailable", installed_identity_drift_observed=True)
            except (OSError, ValueError, TypeError, AttributeError) as error:
                receipt.update(status="unavailable", installed_identity_after_error_type=type(error).__name__)
                if type(error) is InstalledIdentityError:
                    receipt["installed_identity_drift_observed"] = True
        if private is not None and private_identity is not None:
            try:
                need(shape.private_directory_identity(private) == private_identity and
                     set(private.iterdir()) == {output for output, _, _ in owned}, "private_directory_or_membership_changed")
                for output, expected, value in owned:
                    need(shape.digest(shape.bounded_owned_read(output, expected)) == value, "private_payload_changed")
                for output, _, _ in owned:
                    output.unlink()
                private.rmdir()
                receipt["owned_private_output_removed"] = not private.exists()
            except (OSError, ValueError) as error:
                receipt.update(status="unavailable", cleanup_error_type=type(error).__name__)
                if type(error) in (ObservationError, shape.ShapeError):
                    receipt["cleanup_error_guard"] = str(error)
        receipt["elapsed_seconds"] = round(time.monotonic() - started, 3)
        if time.monotonic() > deadline:
            receipt.update(status="unavailable", budget_exhausted=True)
        if descriptor is not None:
            try:
                need(shape.file_identity(os.fstat(descriptor)) == record_identity and
                     shape.file_identity(record.lstat()) == record_identity, "observation_record_identity_changed")
                body = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
                need(len(body) <= MAX_RECORD_BYTES, "sanitized_record_byte_bound")
                with os.fdopen(descriptor, "wb") as target:
                    descriptor = None
                    target.write(body)
            except (OSError, ValueError) as error:
                receipt.update(status="unavailable", record_error_type=type(error).__name__)
            finally:
                if descriptor is not None:
                    os.close(descriptor)
    return receipt


if __name__ == "__main__":
    raise SystemExit("Owned prelaunch observation requires its original selected workload; no standalone CLI.")
