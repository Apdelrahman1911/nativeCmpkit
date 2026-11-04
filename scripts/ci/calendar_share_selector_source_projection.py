# SPDX-License-Identifier: Apache-2.0
"""Exact calendar/share selector history; never a native/compiler input.

One newest raw ingress precedes the camera stage. Ancestor readers only peel a
complete known afterimage: old or unknown bytes still need their next dated pin.
The owning validator explicitly checks the four new selector helper/control
inputs, separately from older geometry validators and their immutable inputs.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_RELATIVE = "scripts/ci/fixtures/calendar-share-selector-source-inverse.json"
SPEC_PATH = Path(__file__).parent / "fixtures/calendar-share-selector-source-inverse.json"
SPEC_SHA256 = "0a9267ec0455668688ce3a4a76dc20f534294bf2d48edf1f4c80fd3e43a34bab"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024
BOUND_PATHS = {
    ".github/workflows/gradle.yml", "scripts/ci/library_tests.py",
    "scripts/ci/workflow_matrix.py", "scripts/ci/camera_home_affinity_source_projection.py",
}
ADDED_PATHS = {
    "scripts/ci/ios_calendar_native_focus.py", "scripts/ci/macos_share_native_focus.py",
    "scripts/ci/test_ios_calendar_native_focus.py", "scripts/ci/test_macos_share_native_focus.py",
}


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate calendar/share selector manifest field")
        result[key] = value
    return result


def _document():
    before = SPEC_PATH.lstat()
    if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or
            not 0 < before.st_size <= MAX_SPEC_BYTES):
        raise ValueError("One ordinary bounded calendar/share selector manifest is required")
    raw = SPEC_PATH.read_bytes()
    after = SPEC_PATH.lstat()
    fields = ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns")
    if (any(getattr(before, field) != getattr(after, field) for field in fields) or
            len(raw) != before.st_size or hashlib.sha256(raw).hexdigest() != SPEC_SHA256):
        raise ValueError("The exact calendar/share selector manifest changed")
    document = json.loads(raw, object_pairs_hook=_unique)
    if (type(document) is not dict or type(document.get("schema_version")) is not int or
            document["schema_version"] != 1 or type(document.get("bindings")) is not dict or
            set(document["bindings"]) != BOUND_PATHS or type(document.get("added_inputs")) is not dict or
            set(document["added_inputs"]) != ADDED_PATHS or
            type(document.get("unchanged_inputs")) is not dict):
        raise ValueError("The exact finite calendar/share selector manifest schema is required")
    return document


def source_before_calendar_share_selectors(relative, payload):
    """Exact inverse or exact idempotent ancestor; never current admission."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact calendar/share selector identity and ordinary source bytes are required")
    binding = _document()["bindings"].get(relative)
    if binding is None:
        return payload  # An unlisted identity is not certified or digest-guessed.
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded calendar/share selector source bytes are required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload  # Dated ancestor only, never an alternate current image.
    if observed != binding["after_sha256"] or len(payload) != binding["after_bytes"]:
        raise ValueError("Unreviewed calendar/share selector source is not its complete afterimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                not before or not after or restored.count(after) != 1):
            raise ValueError("Exact finite unique calendar/share selector inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if (hashlib.sha256(restored).hexdigest() != binding["before_sha256"] or
            len(restored) != binding["before_bytes"]):
        raise ValueError("Calendar/share selector inverse did not restore its complete prior source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact finite unique calendar/share selector forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Calendar/share selector complete source round trip differs")
    return restored


def current_source_before_calendar_share_selectors(relative, payload):
    """Only the outer raw-checkout boundary admits a listed latest image."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current calendar/share selector identity and ordinary bytes are required")
    binding = _document()["bindings"].get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("An old/unknown image cannot replace current calendar/share selector source")
    return source_before_calendar_share_selectors(relative, payload)


def peel_calendar_share_selectors_for_history(relative, payload):
    """No admission: unknown/older bytes remain subject to their next dated pin."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact ancestor calendar/share selector identity and ordinary bytes are required")
    binding = _document()["bindings"].get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() == binding["after_sha256"]:
        return source_before_calendar_share_selectors(relative, payload)
    return payload


def validate_current_sources(root: Path):
    """Own current/additive source validation, not compiler or native evidence.

Unlike an old geometry mirror, this validator requires every new calendar/share
helper/control input. The exact manifest is checked both at the loaded source
location and at the requested root. Its new implementation/control source has
independent explicit pins in the new controls and the lead's held input map.
"""
    document = _document()
    expected = ({name: binding["after_sha256"] for name, binding in document["bindings"].items()} |
                document["added_inputs"] | document["unchanged_inputs"] | {SPEC_RELATIVE: SPEC_SHA256})
    from ios_popover_anchor_plan import _ordinary_bytes
    for name, digest in expected.items():
        if hashlib.sha256(_ordinary_bytes(root, name)[0]).hexdigest() != digest:
            raise ValueError("Current calendar/share selector input differs from its exact owning image: " + name)
    return True
