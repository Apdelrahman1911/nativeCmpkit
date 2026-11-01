"""Private exact-installed-app lexical observation candidate; no payload parser.

This module has no CLI, scheduler, install, launch or profile entry point. A
separately selected owning harness must supply its current verified installation
and current selected tool paths. Help acceptance supplies syntax only. Every
registration/schema/native/profile/readiness claim remains unavailable.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import time

import apple_appinfo_capability as capability
import ios_ui_application as application
import library_tests as lt
import runtime_context as runtime

ACCEPTED_HELP_RECEIPT_SHA256 = "9c46f397f21aeff951b7d13baf1a7cc9f704cc14a6bba1b1a920920698f6a426"
ACCEPTED_SYNTAX = "simctl appinfo <device> <bundle identifier>"
QUERY_PREFIX = ("/usr/bin/xcrun", "simctl", "appinfo")
PRIVATE_DIRECTORY = "appinfo-shape-private"
RECORD_NAME = "appinfo-shape-observation.json"
FIXED_FIELDS = ("CFBundleIdentifier", "CFBundleExecutable", "CFBundlePackageType")
DELIMITERS = {
    "left-brace": b"{", "right-brace": b"}", "left-bracket": b"[", "right-bracket": b"]",
    "left-parenthesis": b"(", "right-parenthesis": b")", "less-than": b"<", "greater-than": b">",
    "equals": b"=", "colon": b":", "semicolon": b";", "double-quote": b'"',
}


class ShapeError(ValueError):
    """Only fixed source guard names, never command output or machine paths."""


def need(value, guard):
    if not value:
        raise ShapeError(guard)


def digest(body):
    return hashlib.sha256(body).hexdigest()


@dataclass(frozen=True)
class OwnedInstallation:
    root: Path
    output: Path
    device: str
    bundle: str
    token: str
    source_revision: str
    signed_hash: str
    plist_hash: str
    runtime_before: dict
    preexisting: subprocess.CompletedProcess
    install: subprocess.CompletedProcess
    container: subprocess.CompletedProcess


def lexical_summary(body: bytes) -> dict:
    """Count raw syntax bytes and fixed own-plist words without parsing fields.

    The three allowlisted names come from the existing generated test app's
    Info.plist. Their literal occurrence is not a registration field, value,
    duplicate-field decision or serializer/schema observation.
    """
    need(type(body) is bytes and len(body) <= capability.MAX_COMMAND_BYTES, "stream_byte_bound")
    try:
        body.decode("utf-8", errors="strict")
        utf8 = True
    except UnicodeError:
        utf8 = False
    lines = body.split(b"\n")
    stripped = body.strip(b" \t\r\n")
    byte_kind = lambda byte: next((name for name, value in DELIMITERS.items() if value == byte), "other-byte")
    return {
        "bytes": len(body), "sha256": digest(body), "utf8_decodable": utf8,
        "nul_byte_count": body.count(b"\0"), "lf_byte_count": body.count(b"\n"),
        "cr_byte_count": body.count(b"\r"),
        "nonempty_line_count": sum(bool(line.strip(b" \t\r")) for line in lines),
        "maximum_line_bytes": max(map(len, lines)),
        "first_non_whitespace_byte_kind": byte_kind(stripped[:1]) if stripped else "empty",
        "last_non_whitespace_byte_kind": byte_kind(stripped[-1:]) if stripped else "empty",
        "fixed_prefix_markers": [name for name, value in
                                 (("xml-declaration-literal", b"<?xml"), ("bplist00-literal", b"bplist00"))
                                 if stripped.startswith(value)],
        "delimiter_byte_counts": {name: body.count(value) for name, value in DELIMITERS.items()},
        "allowlisted_name_literal_counts": {
            name: len(re.findall(rb"(?<![A-Za-z0-9_])" + name.encode() + rb"(?![A-Za-z0-9_])", body))
            for name in FIXED_FIELDS
        },
        "serializer_or_field_schema_accepted": False,
    }


def verified_context(context: OwnedInstallation, accepted: dict) -> Path:
    need(type(context) is OwnedInstallation, "owning_installation_context_required")
    need(type(context.source_revision) is str and re.fullmatch(r"[0-9a-f]{40}", context.source_revision),
         "current_source_revision_required")
    need(type(context.token) is str and re.fullmatch(r"[0-9a-f]{32}", context.token), "current_session_token_required")
    expected_bundle = ("io.github.apdelrahman1911.nativecmpkit.verification.ui.r" +
                       context.source_revision[:12] + ".t" + context.token)
    need(context.bundle == expected_bundle, "exact_current_source_session_bundle_required")
    need(type(context.device) is str and runtime.UUID.fullmatch(context.device), "explicit_simulator_uuid_required")
    before = context.runtime_before
    need(type(before) is dict and before.get("source_revision") == context.source_revision and
         before.get("source_tree_dirty") is False and before.get("host") == accepted["host"] and
         before.get("xcode") == accepted["xcode"] and
         before.get("simulator", {}).get("udid") == context.device and
         before.get("simulator", {}).get("state") == "Booted", "current_selected_runtime_required")
    need(capability.host() == accepted["host"], "actual_accepted_Darwin_arm64_Python_required")
    need(context.root == lt.ROOT and context.root.is_absolute(), "owning_harness_root_required")
    output = lt.safe_path(context.root, context.output.relative_to(context.root).as_posix())
    base = lt.safe_path(context.root, "build/ci-verification")
    need(output.is_relative_to(base) and output.name == context.token and
         output.parent.name == "native-ui-application" and output.is_dir(), "current_ui_session_output_required")
    need(all(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value)
             for value in (context.signed_hash, context.plist_hash)), "installed_hashes_required")
    need(type(context.preexisting) is subprocess.CompletedProcess and
         tuple(context.preexisting.args) == ("/usr/bin/xcrun", "simctl", "get_app_container",
                                             context.device, context.bundle, "app") and
         application.missing_app(context.preexisting), "original_foreign_app_absence_required")
    need(type(context.install) is subprocess.CompletedProcess and type(context.install.returncode) is int and
         context.install.returncode == 0 and
         tuple(context.install.args) == ("/usr/bin/xcrun", "simctl", "install", context.device,
                                        str(output / "NativeCmpkitLibraryTests.app")), "current_successful_owned_install_required")
    result = context.container
    need(type(result) is subprocess.CompletedProcess and type(result.returncode) is int and result.returncode == 0 and
         tuple(result.args) == ("/usr/bin/xcrun", "simctl", "get_app_container", context.device, context.bundle, "app") and
         type(result.stdout) is bytes and 0 < len(result.stdout) <= 4096 and type(result.stderr) is bytes and
         not result.stderr, "current_successful_exact_container_query_required")
    path = capability.actual_path(capability.Result(result.returncode, result.stdout, result.stderr, None))
    need(application.installed_identity(result, context.bundle, context.signed_hash, context.plist_hash),
         "installed_owned_bytes_required")
    return path


def selected_tools(accepted: dict, paths: dict[str, Path], developer: Path) -> dict:
    need(type(paths) is dict and set(paths) == {"xcrun", "simctl", "xcodebuild"} and
         paths["xcrun"] == Path("/usr/bin/xcrun"), "exact_selected_tool_paths_required")
    need(type(developer) is Path or isinstance(developer, Path), "selected_developer_directory_required")
    need(developer.is_absolute() and developer.is_dir() and
         digest(str(developer).encode()) == accepted["developer_directory_sha256"] and
         digest(str(developer.resolve(strict=True)).encode()) == accepted["developer_directory_canonical_sha256"],
         "accepted_developer_directory_identity_required")
    observed = {name: capability.tool_identity(path, name) for name, path in paths.items()}
    need(observed == accepted["tool_identities"], "accepted_tool_identities_required")
    return observed


def file_identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns,
            info.st_uid, info.st_nlink, info.st_mode)


def private_directory_identity(path):
    info = path.lstat()
    need(stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o700 and info.st_uid == os.getuid(),
         "owned_private_directory_required")
    return info.st_dev, info.st_ino, info.st_uid, info.st_mode


def bounded_owned_read(path, expected):
    before = path.lstat()
    need(file_identity(before) == expected and stat.S_ISREG(before.st_mode) and
         before.st_nlink == 1 and before.st_uid == os.getuid() and stat.S_IMODE(before.st_mode) == 0o600 and
         0 <= before.st_size <= capability.MAX_COMMAND_BYTES, "private_output_identity_changed")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        need(file_identity(os.fstat(descriptor)) == expected, "private_output_open_identity_changed")
        body = os.read(descriptor, capability.MAX_COMMAND_BYTES + 1)
        os.lseek(descriptor, 0, os.SEEK_SET)
        need(os.read(descriptor, capability.MAX_COMMAND_BYTES + 1) == body and
             file_identity(os.fstat(descriptor)) == expected, "private_output_payload_changed")
    finally:
        os.close(descriptor)
    need(file_identity(path.lstat()) == expected and len(body) == before.st_size,
         "private_output_read_identity_changed")
    return body


def collect(context: OwnedInstallation, *, capability_bytes: bytes, tool_paths: dict[str, Path],
            developer: Path, capture=capability.capture) -> dict:
    """One latched query; never controls the simulator/app's mutation or cleanup.

    Current installation/runtime/tool inputs come from the separately approved
    owning harness. The retained source witness and trusted tool-file reads are
    not atomic concurrent-writer or detached-child/security certification.
    """
    started = time.monotonic()
    receipt = {
        "schema_version": 1, "operation": "owned-appinfo-lexical-shape", "status": "unavailable",
        "query_attempted": False, "query_count": 0, "query_timeout_seconds": capability.COMMAND_SECONDS,
        "observation_budget_seconds": capability.TOTAL_SECONDS,
        "maximum_capture_bytes": capability.MAX_COMMAND_BYTES, "owned_private_output_removed": False,
        "appinfo_output_schema_observed": False, "subsequent_appinfo_ready": False,
        "registration_observed": False, "registered_container_matches_verified_container": None,
        "registered_executable_identity_verified": None, "root_cause_proven": False,
        "native_functionality_verified": False, "profile_passed": False,
        "packages_published": False, "release_readiness_certified": False,
        "raw_payload_keys_values_paths_or_inventory_uploaded": False,
    }
    private, directory_identity, record, record_descriptor, record_identity = None, None, None, None, None
    owned = []
    try:
        need(type(capability_bytes) is bytes and digest(capability_bytes) == ACCEPTED_HELP_RECEIPT_SHA256,
             "accepted_immutable_help_receipt_required")
        accepted = json.loads(capability_bytes)
        need(accepted["capability_available"] is True and accepted["owned_private_output_removed"] is True and
             accepted["help"]["known_syntax"] == ACCEPTED_SYNTAX and
             accepted["appinfo_output_schema_observed"] is False and accepted["subsequent_appinfo_ready"] is False and
             accepted["host"]["system"] == "Darwin" and accepted["host"]["architecture"] == "arm64",
             "help_only_syntax_prerequisite_required")
        container_path = verified_context(context, accepted)
        tools_before = selected_tools(accepted, tool_paths, developer)
        need(shutil.disk_usage(context.root).free >= 8192 * 1024**2 + capability.MAX_COMMAND_BYTES + 65536,
             "eight_GiB_capture_and_record_reserve_required")
        need(time.monotonic() - started + capability.COMMAND_SECONDS <= capability.TOTAL_SECONDS,
             "observation_budget_exhausted_before_query")
        receipt.update(source_revision=context.source_revision, capability_receipt_sha256=digest(capability_bytes),
                       accepted_syntax=ACCEPTED_SYNTAX, query_argv_template=[*QUERY_PREFIX, "<selected UUID>", "<current owned bundle>"],
                       simulator_uuid_sha256=digest(context.device.encode()), bundle_identifier_sha256=digest(context.bundle.encode()),
                       verified_installed_container_path_sha256=digest(str(container_path).encode()),
                       signed_application_executable_sha256=context.signed_hash, application_plist_sha256=context.plist_hash,
                       tool_identities_before=tools_before)
        record = context.output / RECORD_NAME
        record_descriptor = os.open(record, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        record_identity = file_identity(os.fstat(record_descriptor))
        private = context.output / PRIVATE_DIRECTORY
        private.mkdir(mode=0o700)
        directory_identity = private_directory_identity(private)
        # This exclusive record is the persistent no-retry latch for the session.
        receipt.update(query_attempted=True, query_count=1)
        capture_error = False
        try:
            result = capture((*QUERY_PREFIX, context.device, context.bundle), context.root, capability.COMMAND_SECONDS)
        except capability.CapabilityError as error:
            result = getattr(error, "control_result", None)
            capture_error = True
            need(result is not None, "owned_capture_refused_without_result")
        need(type(result) is capability.Result and (type(result.exit_code) is int or
             (capture_error and result.exit_code is None)) and type(result.stdout) is bytes and type(result.stderr) is bytes and
             len(result.stdout) + len(result.stderr) <= capability.MAX_COMMAND_BYTES and
             result.stop_reason in (None, "timeout", "output-bound", "owned-control-refusal"), "bounded_query_result_required")
        receipt.update(query=capability.metadata(result), streams={})
        for name in ("stdout", "stderr"):
            body, path = getattr(result, name), private / name
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(descriptor, "wb") as target:
                target.write(body)
            expected = file_identity(path.lstat())
            owned.append((path, expected, digest(body)))
            receipt["streams"][name] = lexical_summary(body)
        need(not capture_error and capability.valid(result) and result.exit_code == 0, "incomplete_or_nonzero_query")
        nonempty = [summary for summary in receipt["streams"].values() if summary["bytes"]]
        need(len(nonempty) == 1 and nonempty[0]["utf8_decodable"] and nonempty[0]["nul_byte_count"] == 0,
             "empty_ambiguous_or_nontext_payload")
        need(verified_context(context, accepted) == container_path, "installed_context_changed_after_query")
        receipt["tool_identities_after"] = selected_tools(accepted, tool_paths, developer)
        receipt["status"] = "observed-bounded-lexical-shape"
    except (OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.SubprocessError) as error:
        receipt["error_type"] = type(error).__name__
        if type(error) is ShapeError:
            receipt["error_guard"] = str(error)
        receipt["status"] = "unavailable"
    finally:
        if private is not None and directory_identity is not None:
            try:
                need(private_directory_identity(private) == directory_identity, "private_directory_changed")
                need(set(private.iterdir()) == {path for path, _, _ in owned}, "private_membership_changed")
                for path, expected, value in owned:
                    need(digest(bounded_owned_read(path, expected)) == value, "private_payload_hash_changed")
                for path, _, _ in owned:
                    path.unlink()
                private.rmdir()
                receipt["owned_private_output_removed"] = not private.exists()
            except (OSError, ValueError) as error:
                receipt.update(status="unavailable", cleanup_error_type=type(error).__name__)
                if type(error) is ShapeError:
                    receipt["cleanup_error_guard"] = str(error)
        receipt["elapsed_seconds"] = round(time.monotonic() - started, 3)
        if receipt["elapsed_seconds"] > capability.TOTAL_SECONDS:
            receipt.update(status="unavailable", budget_exhausted=True)
        if record_descriptor is not None:
            try:
                need(file_identity(os.fstat(record_descriptor)) == record_identity and
                     file_identity(record.lstat()) == record_identity, "observation_record_identity_changed")
                payload = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
                need(len(payload) <= 65536, "sanitized_record_byte_bound")
                with os.fdopen(record_descriptor, "wb") as target:
                    record_descriptor = None
                    target.write(payload)
            except (OSError, ValueError) as error:
                receipt.update(status="unavailable", record_error_type=type(error).__name__)
            finally:
                if record_descriptor is not None:
                    os.close(record_descriptor)
    return receipt


if __name__ == "__main__":
    raise SystemExit("Appinfo shape collection requires a separately selected current owning harness; no standalone CLI.")
