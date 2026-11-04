"""Read one retained sanitized image sidecar, never relax native/profile gates.

The caller/producer remain the owning source of the observation. This confined
reader checks ordinary bounded files, their canonical correspondence and the
independent receipt/source/session/simulator/signed-byte identities. It does not
reparse appinfo, query tools, identify an unseen original entry or a launch cause,
delete evidence, retry anything, or supply a trusted-builder/security attestation.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat

FOCUS = "ios-native-image-allocation-profile-recovery"
RECORD_NAME = "image-launch-readiness-observation.json"
INLINE_KEY = "owned_image_launch_readiness"
MAX_RECORD_BYTES, MAX_RECEIPT_BYTES = 65536, 2 * 1024**2
MAX_CAPTURE_BYTES, MAX_NODES = 131072, 4096
HELP_SHA256 = "9c46f397f21aeff951b7d13baf1a7cc9f704cc14a6bba1b1a920920698f6a426"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
FIXED_FIELDS = {"CFBundleIdentifier", "CFBundleExecutable", "CFBundlePackageType"}
DELIMITERS = {"left-brace", "right-brace", "left-bracket", "right-bracket", "left-parenthesis",
              "right-parenthesis", "less-than", "greater-than", "equals", "colon", "semicolon", "double-quote"}
VALUE_KINDS = {"dictionary", "array", "string", "boolean", "integer", "real", "data", "date", "null"}
FORMATS = {"json", "ascii-plist", "xml-plist-v1", "binary-plist-v00"}
FALSE_FLAGS = {"installed_identity_drift_observed", "appinfo_output_schema_observed", "registration_observed",
               "launch_readiness_verified", "root_cause_proven", "native_functionality_verified", "profile_passed",
               "packages_published", "release_readiness_certified", "raw_payload_keys_values_paths_or_inventory_uploaded"}
NULL_FLAGS = {"registered_container_matches_verified_container", "registered_executable_identity_verified"}
REQUIRED = FALSE_FLAGS | NULL_FLAGS | {
    "schema_version", "operation", "status", "query_attempted", "query_count", "query_timeout_seconds",
    "observation_budget_seconds", "maximum_capture_bytes", "installed_executable_before", "installed_executable_after",
    "installed_identity_stable_observed", "tool_path_resolution", "owned_private_output_removed", "source_revision",
    "capability_receipt_sha256", "simulator_uuid_sha256", "bundle_identifier_sha256",
    "verified_installed_container_path_sha256", "query_argv_template", "tool_identities_before", "elapsed_seconds"}
OPTIONAL = {"query", "streams", "serialized_structure", "tool_identities_after", "error_type", "error_guard",
            "installed_identity_after_error_type", "owned_control_cleanup_refused", "budget_exhausted"}


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _fields(value, required, optional=()):
    _need(type(value) is dict and required <= set(value) <= required | set(optional),
          "Unexpected retained image observation fields")


def _integer(value, maximum, minimum=0):
    _need(type(value) is int and minimum <= value <= maximum, "Invalid bounded image observation integer")


def _digest(value):
    _need(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value), "Invalid image observation digest")


def _errors(value):
    for key in ("error_type", "installed_identity_after_error_type"):
        if key in value:
            _need(type(value[key]) is str and re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,63}", value[key]),
                  "Unsanitized image observation error type")
    if "error_guard" in value:
        _need("error_type" in value and type(value["error_guard"]) is str and
              re.fullmatch(r"[a-z][a-z0-9_]{0,95}", value["error_guard"]), "Unsanitized image observation source guard")


def _identity(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_uid,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _membership(session, module, focus):
    _need(isinstance(session, Path) and session.is_absolute() and session == session.resolve(strict=True) and
          re.fullmatch(r"[0-9a-f]{32}", session.name), "An ordinary exact owned application session is required")
    directory = session.lstat()
    _need(stat.S_ISDIR(directory.st_mode) and directory.st_uid == os.getuid(), "Invalid owned application session directory")
    allowed = {"receipt.json", RECORD_NAME} if module == "calf-ui" and focus == FOCUS else {"receipt.json"}
    entries = {}
    for path in session.iterdir():
        _need(path.name in allowed and path.name not in entries and len(entries) < len(allowed),
              "Receipt missing or disposable app/other files remain")
        info = path.lstat()
        _need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.getuid(),
              "Application evidence entries must be ordinary owned unshared files")
        entries[path.name] = _identity(info)
    _need(set(entries) == allowed, "Missing exact owned application receipt or retained image sidecar")
    _need(_identity(session.lstat()) == _identity(directory), "Application session changed during membership observation")
    return _identity(directory), entries


def require_session_membership(session: Path, module: str, focus: str | None):
    """Only calf-ui's exact allocation recovery adds its one named evidence file."""
    _membership(session, module, focus)


def _read(path, maximum, expected, *, mode=None):
    before = path.lstat()
    _need(_identity(before) == expected and stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
          before.st_uid == os.getuid() and 0 < before.st_size <= maximum and
          (mode is None or stat.S_IMODE(before.st_mode) == mode), "Invalid or unbounded retained image evidence file")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        _need(_identity(os.fstat(descriptor)) == expected, "Image evidence open identity changed")
        body = os.read(descriptor, maximum + 1)
        os.lseek(descriptor, 0, os.SEEK_SET)
        _need(os.read(descriptor, maximum + 1) == body and _identity(os.fstat(descriptor)) == expected,
              "Image evidence payload or descriptor identity changed")
    finally:
        os.close(descriptor)
    _need(len(body) == before.st_size and _identity(path.lstat()) == expected, "Image evidence path or read identity changed")
    return body


def _unique(pairs):
    value = {}
    for key, item in pairs:
        _need(key not in value, "Duplicate retained image observation JSON key")
        value[key] = item
    return value


def _metadata(value):
    _fields(value, {"exit_code", "stop_reason", "stdout_bytes", "stdout_sha256", "stderr_bytes", "stderr_sha256"})
    if value["exit_code"] is not None:
        _integer(value["exit_code"], 2**31 - 1, -(2**31))
    _need(value["stop_reason"] in (None, "timeout", "output-bound", "owned-control-refusal"), "Invalid image query stop observation")
    for name in ("stdout", "stderr"):
        _integer(value[name + "_bytes"], MAX_CAPTURE_BYTES); _digest(value[name + "_sha256"])
        _need(value[name + "_bytes"] != 0 or value[name + "_sha256"] == EMPTY_SHA256, "Empty image stream hash differs")
    _need(value["stdout_bytes"] + value["stderr_bytes"] <= MAX_CAPTURE_BYTES, "Image query capture bound exceeded")


def _lexical(value):
    fields = {"bytes", "sha256", "utf8_decodable", "nul_byte_count", "lf_byte_count", "cr_byte_count", "nonempty_line_count",
              "maximum_line_bytes", "first_non_whitespace_byte_kind", "last_non_whitespace_byte_kind", "fixed_prefix_markers",
              "delimiter_byte_counts", "allowlisted_name_literal_counts", "serializer_or_field_schema_accepted"}
    _fields(value, fields); _integer(value["bytes"], MAX_CAPTURE_BYTES); _digest(value["sha256"])
    _need(type(value["utf8_decodable"]) is bool and value["serializer_or_field_schema_accepted"] is False,
          "Image lexical observations cannot certify schema")
    for key in ("nul_byte_count", "lf_byte_count", "cr_byte_count", "nonempty_line_count", "maximum_line_bytes"):
        _integer(value[key], value["bytes"])
    for key in ("first_non_whitespace_byte_kind", "last_non_whitespace_byte_kind"):
        _need(value[key] in DELIMITERS | {"empty", "other-byte"}, "Unknown image lexical byte category")
    markers = value["fixed_prefix_markers"]
    _need(type(markers) is list and len(markers) <= 2 and all(type(item) is str for item in markers) and
          len(markers) == len(set(markers)) and set(markers) <= {"xml-declaration-literal", "bplist00-literal"},
          "Unknown image lexical prefix category")
    for key, names in (("delimiter_byte_counts", DELIMITERS), ("allowlisted_name_literal_counts", FIXED_FIELDS)):
        _fields(value[key], names)
        for count in value[key].values(): _integer(count, value["bytes"])
    if not value["bytes"]:
        _need(value["sha256"] == EMPTY_SHA256 and value["utf8_decodable"] is True and not markers and
              value["first_non_whitespace_byte_kind"] == value["last_non_whitespace_byte_kind"] == "empty",
              "Invalid empty image lexical observation")


def _kinds(value):
    _need(type(value) is dict and set(value) <= VALUE_KINDS, "Unknown sanitized image value category")
    for count in value.values(): _integer(count, MAX_NODES, 1)
    return sum(value.values())


def _structure(value):
    _fields(value, {"root_kind", "nodes_including_keys", "value_kind_counts", "dictionary_key_occurrences",
        "duplicate_dictionary_key_occurrences", "root_dictionary_key_occurrences", "own_plist_name_key_structures",
        "registration_field_semantics_verified", "field_absence_or_registration_absence_proven", "raw_unknown_keys_values_or_paths_uploaded"})
    _need(value["root_kind"] in VALUE_KINDS and all(value[key] is False for key in (
        "registration_field_semantics_verified", "field_absence_or_registration_absence_proven", "raw_unknown_keys_values_or_paths_uploaded")),
        "Image structure observations cannot certify registration or absence")
    _integer(value["nodes_including_keys"], MAX_NODES, 1); _integer(value["dictionary_key_occurrences"], MAX_NODES)
    keys = value["dictionary_key_occurrences"]
    _integer(value["duplicate_dictionary_key_occurrences"], keys)
    _need(_kinds(value["value_kind_counts"]) + keys == value["nodes_including_keys"] and
          value["value_kind_counts"].get(value["root_kind"], 0) > 0, "Inconsistent sanitized image node counts")
    root_keys = value["root_dictionary_key_occurrences"]
    if value["root_kind"] == "dictionary": _integer(root_keys, keys)
    else: _need(root_keys is None, "Non-dictionary image root cannot claim root key counts")
    _fields(value["own_plist_name_key_structures"], FIXED_FIELDS)
    for row in value["own_plist_name_key_structures"].values():
        _fields(row, {"root_key_occurrences", "nested_key_occurrences", "value_kind_counts"})
        _integer(row["root_key_occurrences"], root_keys or 0); _integer(row["nested_key_occurrences"], keys - (root_keys or 0))
        _need(_kinds(row["value_kind_counts"]) == row["root_key_occurrences"] + row["nested_key_occurrences"],
              "Inconsistent fixed-name sanitized image key counts")


def _serialized(value):
    _fields(value, {"status", "complete_payload_grammar_matches", "structure", "unique_representation_format_observed",
        "serializer_implementation_identified", "appinfo_output_schema_observed", "registration_observed",
        "raw_unknown_keys_values_or_paths_uploaded"}, {"error_type", "error_guard"})
    _errors(value)
    _need(all(value[key] is False for key in ("serializer_implementation_identified", "appinfo_output_schema_observed",
              "registration_observed", "raw_unknown_keys_values_or_paths_uploaded")), "Image syntax observations cannot certify schema")
    formats = value["complete_payload_grammar_matches"]
    _need(type(formats) is list and len(formats) <= 2 and all(type(item) is str for item in formats) and
          len(formats) == len(set(formats)) and set(formats) <= FORMATS, "Unknown complete image syntax observation")
    if value["status"] == "observed-complete-serialized-structure":
        _need(formats and "error_type" not in value and
              value["unique_representation_format_observed"] is (len(formats) == 1), "Incomplete image syntax observation")
        _structure(value["structure"])
    else:
        _need(value["status"] == "unavailable" and value["structure"] is None and
              value["unique_representation_format_observed"] is False, "Unknown image syntax status")


def _executable(value, signed_hash):
    _fields(value, {"status", "bytes", "signed_executable_sha256", "installed_path_sha256", "installed_file_stat_identity_sha256",
                   "permission_mode", "host_real_id_X_OK", "access_scope", "simulator_executable_acceptance_verified",
                   "launch_readiness_verified", "raw_identity_ids_or_paths_uploaded"})
    _integer(value["bytes"], 1024 * 1024**2, 1)
    for key in ("signed_executable_sha256", "installed_path_sha256", "installed_file_stat_identity_sha256"): _digest(value[key])
    _need(value["status"] == "observed-exact-installed-executable" and value["signed_executable_sha256"] == signed_hash and
          type(value["permission_mode"]) is str and re.fullmatch(r"[0-7]{4}", value["permission_mode"]) and
          type(value["host_real_id_X_OK"]) is bool and value["access_scope"] == "calling-host-process-real-ids" and
          all(value[key] is False for key in ("simulator_executable_acceptance_verified", "launch_readiness_verified",
                                            "raw_identity_ids_or_paths_uploaded")), "Unbound or unsanitized installed image identity")


def _tools(value):
    _fields(value, {"xcrun", "simctl", "xcodebuild"})
    for name, row in value.items():
        _fields(row, {"basename", "bytes", "sha256", "path_sha256", "canonical_path_sha256"})
        _need(row["basename"] == name, "Unexpected selected image tool basename")
        _integer(row["bytes"], 128 * 1024**2, 1)
        for key in ("sha256", "path_sha256", "canonical_path_sha256"): _digest(row[key])


def _schema(value, signed_hash, elapsed_bound):
    _fields(value, REQUIRED, OPTIONAL); _errors(value)
    _integer(value["schema_version"], 1, 1); _integer(value["query_count"], 1, 1)
    _need(value["operation"] == "owned-image-prelaunch-observation" and value["query_attempted"] is True and
          all(value[key] is False for key in FALSE_FLAGS) and all(value[key] is None for key in NULL_FLAGS) and
          value["owned_private_output_removed"] is True, "Retained image observation has unbound cleanup or certification claims")
    for key, exact in (("query_timeout_seconds", 15), ("observation_budget_seconds", 90), ("maximum_capture_bytes", MAX_CAPTURE_BYTES)):
        _integer(value[key], exact, exact)
    _need(type(value["elapsed_seconds"]) in (int, float) and math.isfinite(value["elapsed_seconds"]) and
          0 <= value["elapsed_seconds"] <= elapsed_bound, "Invalid bounded image observation elapsed time")
    _executable(value["installed_executable_before"], signed_hash)
    if value["installed_executable_after"] is None:
        _need(value["installed_identity_stable_observed"] is None and "installed_identity_after_error_type" in value and
              value["status"] == "unavailable", "Missing image post-observation identity must remain unavailable")
    else:
        _executable(value["installed_executable_after"], signed_hash)
        _need(value["installed_identity_stable_observed"] is True and
              value["installed_executable_before"] == value["installed_executable_after"], "Installed image identity drift cannot be admitted")
    _tools(value["tool_identities_before"])
    if "tool_identities_after" in value:
        _tools(value["tool_identities_after"])
        _need(value["tool_identities_before"] == value["tool_identities_after"], "Selected image tool identity changed")
    paths = value["tool_path_resolution"]
    _need(type(paths) is list and len(paths) == 3, "Missing fixed image tool path observations")
    for row, name in zip(paths, ("developer", "simctl", "xcodebuild")):
        _need(type(row) is dict and row.get("name") == name, "Unexpected image tool path observation order")
        _metadata({key: item for key, item in row.items() if key != "name"})
        _need(row["exit_code"] == 0 and row["stop_reason"] is None and row["stdout_bytes"] > 0 and row["stderr_bytes"] == 0,
              "Unbound fixed image tool path observation")
    _digest(value["verified_installed_container_path_sha256"])
    _need(value["query_argv_template"] == ["/usr/bin/xcrun", "simctl", "appinfo", "<selected UUID>", "<current owned bundle>"],
          "Unexpected image query origin template")
    if "query" in value: _metadata(value["query"])
    if "streams" in value:
        _fields(value["streams"], set(), {"stdout", "stderr"})
        _need("query" in value, "Image streams lack their query metadata")
        for name, row in value["streams"].items():
            _lexical(row)
            _need(row["bytes"] == value["query"][name + "_bytes"] and row["sha256"] == value["query"][name + "_sha256"],
                  "Image stream/query digest correspondence differs")
    if "serialized_structure" in value: _serialized(value["serialized_structure"])
    for key in ("owned_control_cleanup_refused", "budget_exhausted"):
        if key in value: _need(value[key] is True and value["status"] == "unavailable", "Invalid image unavailability flag")
    if value["status"] == "observed-owned-prelaunch-structure":
        _need("query" in value and value["query"]["exit_code"] == 0 and value["query"]["stop_reason"] is None and
              value["query"]["stdout_bytes"] > 0 and value["query"]["stderr_bytes"] == 0 and
              set(value.get("streams", {})) == {"stdout", "stderr"} and "tool_identities_after" in value and
              value.get("serialized_structure", {}).get("status") == "observed-complete-serialized-structure" and
              "error_type" not in value, "Incomplete observed image prelaunch structure")
    else:
        _need(value["status"] == "unavailable", "Unknown retained image observation status")


def validate_retained(session: Path, document: dict, context: dict, started_ns: int, ended_ns: int,
                      module: str, focus: str | None, *, receipt_payload: bytes) -> str | None:
    """Return the retained canonical hash only; original native/profile gates follow."""
    _need(type(document) is dict, "An owning application receipt object is required")
    if module != "calf-ui" or focus != FOCUS:
        _need(INLINE_KEY not in document, "Unexpected image prelaunch observation on another application focus")
        return None
    snapshot = _membership(session, module, focus)
    _need(type(started_ns) is int and type(ended_ns) is int and started_ns <= ended_ns and type(context) is dict,
          "A bounded independent application run context is required")
    simulator = context.get("simulator")
    _need(type(simulator) is dict, "An independent selected simulator object is required")
    source = context.get("source_revision"); device = simulator.get("udid")
    _need(type(source) is str and re.fullmatch(r"[0-9a-f]{40}", source) and type(device) is str and
          re.fullmatch(r"[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}", device) and
          context.get("source_tree_dirty") is False and document.get("source_tree_dirty") is False and
          document.get("source_revision") == source and document.get("explicit_test_focus") == FOCUS and
          document.get("task") == ":calf-ui:iosSimulatorArm64ApplicationTest", "Unbound source or selected image application origin")
    bundle = "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + source[:12] + ".t" + session.name
    _need(document.get("bundle_id") == bundle, "Retained image evidence is not this source/session bundle")
    signed_hash = document.get("signed_application_executable_sha256"); _digest(signed_hash)
    _need(type(receipt_payload) is bytes and 0 < len(receipt_payload) <= MAX_RECEIPT_BYTES and
          _read(session / "receipt.json", MAX_RECEIPT_BYTES, snapshot[1]["receipt.json"]) == receipt_payload,
          "Owning application receipt changed at the image read boundary")
    raw = _read(session / RECORD_NAME, MAX_RECORD_BYTES, snapshot[1][RECORD_NAME], mode=0o600)
    modified = snapshot[1][RECORD_NAME][-2]
    _need(started_ns - 2_000_000_000 <= modified <= ended_ns + 2_000_000_000, "Stale or future retained image observation")
    value = json.loads(raw, object_pairs_hook=_unique,
                       parse_constant=lambda _: _need(False, "Nonfinite retained image observation JSON"))
    inline = document.get(INLINE_KEY)
    _need(type(inline) is dict and raw == (json.dumps(value, indent=2, sort_keys=True) + "\n").encode() and
          raw == (json.dumps(inline, indent=2, sort_keys=True) + "\n").encode(),
          "Retained image canonical bytes differ from the owning receipt observation")
    _schema(value, signed_hash, (ended_ns - started_ns) / 1_000_000_000 + 4)
    _need(value["source_revision"] == source and value["capability_receipt_sha256"] == HELP_SHA256 and
          value["simulator_uuid_sha256"] == hashlib.sha256(device.encode()).hexdigest() and
          value["bundle_identifier_sha256"] == hashlib.sha256(bundle.encode()).hexdigest(),
          "Retained image source/capability/simulator/session digests differ")
    _need(_membership(session, module, focus) == snapshot, "Image session or evidence membership changed while reading")
    return hashlib.sha256(raw).hexdigest()
