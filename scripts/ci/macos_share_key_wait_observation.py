# SPDX-License-Identifier: Apache-2.0
"""Exact local AppKit late-snapshot source admission and finite stderr fields.

Inverse fragments are source operands only. This module does not execute restored
code, query native objects, admit shared routing or certify a native result/cause.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import posixpath
import re
import stat

from ios_popover_anchor_plan import _ordinary_bytes
import macos_share_appkit_only_source_projection as appkit_only

ROOT = Path(__file__).resolve().parents[2]
OWNER_RELATIVE = "scripts/ci/macos_share_key_wait_observation.py"
SPEC_RELATIVE = "scripts/ci/fixtures/macos-share-key-wait-observation-source-inverse.json"
SPEC_PATH = Path(__file__).parent / "fixtures/macos-share-key-wait-observation-source-inverse.json"
SPEC_SHA256 = "dd5872cb1a7e23beb064dfcad7ef10544e0b547d734498b564dd73ae5ee3a0e6"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024
MAX_STDERR = 4096
MAX_MARKER_BYTES = 512
CASES_SOURCE = "calf-share/native/tests/appkit_lifecycle/cases.rs"
BOUND_PATHS = {
    CASES_SOURCE, "scripts/ci/macos_share_appkit_lifecycle.py",
    "scripts/ci/test_macos_share_appkit_lifecycle_runner.py", "scripts/ci/test_macos_share_missing_only.py",
}
ADDED_PATHS = {
    "scripts/ci/test_macos_share_key_wait_observation.py", "docs/testing/macos-share-key-wait-observation.md",
}
UNCHANGED_PATHS = {
    "calf-share/native/Cargo.toml", "calf-share/native/Cargo.lock", "calf-share/native/src/lib.rs",
    "calf-share/native/src/macos.rs", "calf-share/native/src/operation.rs",
    "calf-share/native/tests/appkit_lifecycle_main.rs", "scripts/ci/macos_share_missing_only.py",
    "scripts/ci/macos_share_missing_ci.py",
    "calf-share/src/desktopTest/kotlin/com/mohamedrejeb/calf/share/MacOsShareCoroutineLifecycleTest.kt",
}
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


# This is file custody for the importing source, not trusted-builder attestation.
# Review packets pin the module independently; including its hash in its own spec
# would make the exact spec pin circular.
OWNER_SHA256 = sha(appkit_only.peel_appkit_only_for_history(
    OWNER_RELATIVE, _ordinary_bytes(ROOT, OWNER_RELATIVE)[0], ROOT))


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate AppKit late-snapshot manifest field")
        result[key] = value
    return result


def _document():
    metadata = SPEC_PATH.lstat()
    if (not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1 or
            not 0 < metadata.st_size <= MAX_SPEC_BYTES):
        raise ValueError("One ordinary bounded AppKit late-snapshot manifest is required")
    raw = _ordinary_bytes(SPEC_PATH.parent, SPEC_PATH.name)[0]
    if not 0 < len(raw) <= MAX_SPEC_BYTES or sha(raw) != SPEC_SHA256:
        raise ValueError("The exact AppKit late-snapshot manifest changed")
    try:
        document = json.loads(raw, object_pairs_hook=_unique,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite AppKit late-snapshot manifest")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("The complete AppKit late-snapshot manifest JSON is required") from None
    if (type(document) is not dict or set(document) != {
                "schema_version", "scope", "bindings", "added_inputs", "unchanged_inputs"} or
            type(document["schema_version"]) is not int or document["schema_version"] != 1 or
            document["scope"] != "Exact local AppKit failure-only late-snapshot source custody; no compiler/native acceptance" or
            type(document["bindings"]) is not dict or set(document["bindings"]) != BOUND_PATHS or
            type(document["added_inputs"]) is not dict or set(document["added_inputs"]) != ADDED_PATHS or
            type(document["unchanged_inputs"]) is not dict or set(document["unchanged_inputs"]) != UNCHANGED_PATHS):
        raise ValueError("The exact finite AppKit late-snapshot manifest schema is required")
    for row in document["bindings"].values():
        if (type(row) is not dict or set(row) != {
                    "before_sha256", "after_sha256", "before_bytes", "after_bytes", "fragments"} or
                any(type(row[key]) is not int or not 0 < row[key] <= MAX_SOURCE_BYTES for key in ("before_bytes", "after_bytes")) or
                any(type(row[key]) is not str or _DIGEST.fullmatch(row[key]) is None for key in ("before_sha256", "after_sha256")) or
                type(row["fragments"]) is not list or not 0 < len(row["fragments"]) <= 12):
            raise ValueError("Complete finite AppKit late-snapshot source bindings are required")
        for fragment in row["fragments"]:
            if (type(fragment) is not dict or set(fragment) != {
                        "before", "after", "before_fragment_sha256", "after_fragment_sha256", "obligation"} or
                    any(type(fragment[key]) is not str or not fragment[key] for key in fragment) or
                    any(_DIGEST.fullmatch(fragment[key]) is None for key in ("before_fragment_sha256", "after_fragment_sha256")) or
                    any(len(fragment[key].encode()) > MAX_SOURCE_BYTES for key in ("before", "after"))):
                raise ValueError("Exact finite AppKit late-snapshot fragment identities are required")
    for rows in (document["added_inputs"], document["unchanged_inputs"]):
        if any(type(digest) is not str or _DIGEST.fullmatch(digest) is None for digest in rows.values()):
            raise ValueError("Exact AppKit late-snapshot ordinary input hashes are required")
    return document


def _identity(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact AppKit late-snapshot relative identity and ordinary bytes are required")


def source_before_key_wait(relative, payload):
    """Complete exact inverse or one complete preimage; never shared/current admission."""
    _identity(relative, payload)
    payload = appkit_only.peel_appkit_only_for_history(relative, payload, ROOT)
    row = _document()["bindings"].get(relative)
    if row is None:
        return payload  # Unlisted bytes remain uncertified.
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded complete AppKit late-snapshot source is required")
    if sha(payload) == row["before_sha256"] and len(payload) == row["before_bytes"]:
        return payload
    if sha(payload) != row["after_sha256"] or len(payload) != row["after_bytes"]:
        raise ValueError("AppKit late-snapshot source is not its complete reviewed afterimage")
    restored = payload
    for fragment in reversed(row["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (sha(before) != fragment["before_fragment_sha256"] or sha(after) != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique AppKit late-snapshot inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if sha(restored) != row["before_sha256"] or len(restored) != row["before_bytes"]:
        raise ValueError("AppKit late-snapshot inverse did not restore the complete prior source")
    forward = restored
    for fragment in row["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique AppKit late-snapshot forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("AppKit late-snapshot complete inverse/forward source roundtrip differs")
    return restored


def current_source_before_key_wait(relative, payload):
    """One raw current local ingress; ancestors/partial/drift cannot replace current."""
    _identity(relative, payload)
    payload = appkit_only.current_source_before_appkit_only(relative, payload, ROOT)
    row = _document()["bindings"].get(relative)
    if row is not None and (sha(payload) != row["after_sha256"] or len(payload) != row["after_bytes"]):
        raise ValueError("Old or unknown bytes cannot replace current AppKit late-snapshot source")
    return source_before_key_wait(relative, payload)


def peel_key_wait_for_history(relative, payload):
    """Only a complete exact local afterimage is peeled; unknown still needs old pins."""
    _identity(relative, payload)
    payload = appkit_only.peel_appkit_only_for_history(relative, payload, ROOT)
    row = _document()["bindings"].get(relative)
    if row is not None and sha(payload) == row["after_sha256"]:
        return source_before_key_wait(relative, payload)
    return payload


def validate_current_sources(root: Path):
    appkit_only.validate_current_sources(root)
    document = _document()
    expected = ({name: row["after_sha256"] for name, row in document["bindings"].items()} |
                document["added_inputs"] | document["unchanged_inputs"] |
                {SPEC_RELATIVE: SPEC_SHA256, OWNER_RELATIVE: OWNER_SHA256})
    for name, digest in expected.items():
        raw = _ordinary_bytes(root, name)[0]
        if sha(appkit_only.peel_appkit_only_for_history(name, raw, root)) != digest:
            raise ValueError("Current AppKit late-snapshot owning input differs: " + name)
    return True


def fixture_inputs():
    document = _document()
    return (set(document["bindings"]) | set(document["added_inputs"]) | set(document["unchanged_inputs"]) |
            {SPEC_RELATIVE, OWNER_RELATIVE} | appkit_only.fixture_inputs(ROOT))


def cases_after_sha256():
    return _document()["bindings"][CASES_SOURCE]["after_sha256"]


def plan_description():
    return {"failure_only": True, "failed_case": "missing_content_view", "source": CASES_SOURCE,
            "source_sha256": cases_after_sha256(), "max_private_stderr_bytes": MAX_STDERR,
            "max_marker_bytes": MAX_MARKER_BYTES, "sample": "sequential-read-only-after-original-panic-before-cleanup",
            "native_cause_verified": False, "original_readiness_and_deadline_unchanged": True,
            "accepted650_jni_timeout_not_requested": True, "native_tests_executed": 0,
            "composed_shared_routing_admission": "deferred-to-lead"}


_PREFIX = "NATIVECMPKIT_APPKIT_KEY_WAIT_POST_FAILURE"
_FRAME = re.compile(r"thread 'main'(?: \([0-9]{1,20}\))? panicked at ([^\r\n]+):([0-9]{1,5}):[0-9]{1,5}:\Z")
_BOOL = r"true|false|unavailable"
_MARKER = re.compile(
    _PREFIX + r" version=1 main=(?P<main>available|unavailable) owned=(?P<owned>available|absent|unavailable) "
    r"app_active=(?P<app_active>" + _BOOL + r") app_running=(?P<app_running>" + _BOOL + r") "
    r"policy=(?P<policy>regular|accessory|prohibited|other|unavailable) visible=(?P<visible>" + _BOOL + r") "
    r"key=(?P<key>" + _BOOL + r") can_key=(?P<can_key>" + _BOOL + r") miniaturized=(?P<miniaturized>" + _BOOL + r") "
    r"app_key=(?P<app_key>absent|this-owned|other|present-unclassified|unavailable) "
    r"loop_main=(?P<loop_main>" + _BOOL + r") mode=(?P<mode>default|other|absent|unavailable)\Z")


def unavailable(reason):
    return {"available": False, "reason": reason, "exact_native_cause_verified": False,
            "raw_payload_exported": False, "reader_executed_native_queries": False,
            "original_predicate_value_captured": False, "recipient_delivery_verified": False}


def post_failure_snapshot(stderr: bytes, *, source_hash: str, failed_case: str, source_absolute: str):
    """Only finite late fields from one qualified owned stream; not an original operand."""
    if (type(source_hash) is not str or source_hash != cases_after_sha256() or
            failed_case != "missing_content_view" or type(source_absolute) is not str):
        return unavailable("unqualified-late-snapshot-source-or-case")
    if type(stderr) is not bytes or not 0 < len(stderr) <= MAX_STDERR:
        return unavailable("late-snapshot-stderr-outside-bound-or-not-emitted")
    try:
        lines = stderr.decode("utf-8", errors="strict").splitlines()
    except UnicodeDecodeError:
        return unavailable("late-snapshot-stderr-not-utf8")
    frames = [(index, _FRAME.fullmatch(line)) for index, line in enumerate(lines) if "panicked at " in line]
    if len(frames) != 1 or frames[0][1] is None:
        return unavailable("original-key-wait-frame-absent-or-ambiguous")
    index, frame = frames[0]
    allowed = {CASES_SOURCE, "tests/appkit_lifecycle/cases.rs", posixpath.normpath(source_absolute)}
    if (posixpath.normpath(frame[1]) not in allowed or int(frame[2]) != 61 or index + 1 >= len(lines) or
            lines[index + 1] != "Owned AppKit window did not become key"):
        return unavailable("exact-original-key-wait-panic-not-observed")
    emitted = [(offset, line) for offset, line in enumerate(lines) if _PREFIX in line]
    if (len(emitted) != 1 or emitted[0][0] <= index + 1 or
            len(emitted[0][1].encode()) > MAX_MARKER_BYTES):
        return unavailable("late-snapshot-marker-absent-ambiguous-or-outside-bound")
    marker = _MARKER.fullmatch(emitted[0][1])
    if marker is None:
        return unavailable("late-snapshot-marker-not-in-finite-schema")
    fields = marker.groupdict()
    if fields["main"] == "unavailable":
        if any(value != "unavailable" for value in fields.values()):
            return unavailable("late-snapshot-nonmain-fields-are-not-queryable")
    else:
        if any(fields[key] == "unavailable" for key in ("app_active", "app_running", "policy", "app_key", "loop_main", "mode")):
            return unavailable("late-snapshot-main-getter-fields-are-incomplete")
        window_keys = ("visible", "key", "can_key", "miniaturized")
        if fields["owned"] == "available":
            if any(fields[key] == "unavailable" for key in window_keys) or fields["app_key"] == "present-unclassified":
                return unavailable("late-snapshot-owned-getter-fields-are-incomplete")
        elif (any(fields[key] != "unavailable" for key in window_keys) or
                fields["app_key"] not in {"absent", "present-unclassified"}):
            return unavailable("late-snapshot-unowned-fields-cannot-be-inferred")
    boolean = lambda value: {"true": True, "false": False, "unavailable": None}[value]
    return {"available": True, "source": CASES_SOURCE, "source_sha256": source_hash,
            "sampling_phase": "post-original-panic-before-owned-cleanup", "sample_consistency": "sequential-read-only-not-atomic",
            "original_predicate_value_captured": False, "exact_native_cause_verified": False,
            "reader_executed_native_queries": False, "raw_payload_exported": False, "recipient_delivery_verified": False,
            "original_primary_failure_unwaived": True,
            "fields": {"main": fields["main"], "owned_window": fields["owned"],
                "app_active": boolean(fields["app_active"]), "app_running": boolean(fields["app_running"]),
                "activation_policy": fields["policy"], "owned_visible": boolean(fields["visible"]),
                "owned_key": boolean(fields["key"]), "owned_can_become_key": boolean(fields["can_key"]),
                "owned_miniaturized": boolean(fields["miniaturized"]), "app_key_window_relation": fields["app_key"],
                "current_run_loop_is_main": boolean(fields["loop_main"]), "current_run_loop_mode": fields["mode"]}}
