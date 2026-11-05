# SPDX-License-Identifier: Apache-2.0
"""Finite source-history bridge for the already reviewed ExternalStorage focus.

Only offline historical fixture readers use this module. Actual Gradle, Android,
profile selection and result admission continue to use the unchanged live files.
The manifest binds complete current/previous sources, unique reversible edits and
both fragment hashes. It never recalculates or replaces a historical expected pin.
Raw current readers refuse a previous image; composable inverses may receive one.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/android-external328-source-inverse.json"
SPEC_SHA256 = "ec166c161309144efd8ffc2b5726a7fa98cbd0f83a6becbfd37ea539562a2c7a"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024


def _bindings() -> dict:
    info = SPEC_PATH.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or
            not 0 < info.st_size <= MAX_SPEC_BYTES):
        raise ValueError("An ordinary bounded exact External328 manifest is required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact External328 manifest changed")
    contract = json.loads(raw)
    if contract["schema_version"] != 1 or type(contract["bindings"]) is not dict:
        raise ValueError("The exact External328 manifest schema is required")
    return contract["bindings"]


def source_before_android_external328(relative: str, payload: bytes) -> bytes:
    """Pure exact inverse; an already restored listed leaf is idempotent."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact External328 source identity and ordinary bytes are required")
    bindings = _bindings()
    # Preserve the original exact complete preimage's compositional idempotence.
    # Actual current admission below never accepts this historical shortcut.
    if (relative in bindings and 0 < len(payload) <= MAX_SOURCE_BYTES and
            hashlib.sha256(payload).hexdigest() == bindings[relative]["before_sha256"]):
        return payload
    from arm64_stop_candidate_source_projection import source_before_arm64_stop_candidate
    payload = source_before_arm64_stop_candidate(relative, payload)
    if relative not in bindings:
        return payload
    binding = bindings[relative]
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded External328 source bytes are required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed External328 source is not an admitted postimage")
    restored = payload
    for item in reversed(binding["fragments"]):
        before, after = item["before"].encode("utf-8"), item["after"].encode("utf-8")
        if (hashlib.sha256(before).hexdigest() != item["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != item["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique External328 inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("External328 inverse did not restore the complete prior source")
    forward = restored
    for item in binding["fragments"]:
        before, after = item["before"].encode("utf-8"), item["after"].encode("utf-8")
        if forward.count(before) != 1:
            raise ValueError("Exact unique External328 forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("External328 round-trip differs from the current bytes")
    return restored


def current_source_for_history(relative: str, payload: bytes) -> bytes:
    """Admit actual current bytes before constructing a historical fixture view."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current source identity and ordinary bytes are required")
    # Exact Android18 admission occurs only at this outer raw boundary.
    # Its literal before-view is not admitted as new current, and nested older
    # readers retain their original ancestor-idempotence/pins.
    from macos_share_ci668_composition import ANDROID_PATCH_PATHS, source_before_android_lifecycle
    # Qualify each newest complete image ONCE, at this raw checkout boundary.
    # Nested readers receive exact ancestors, not another raw-current admission.
    if relative in ANDROID_PATCH_PATHS:
        payload = source_before_android_lifecycle(relative, payload)
        from ios_geometry_simulator_source_projection import source_before_owned_geometry
        payload = source_before_owned_geometry(relative, payload)
    else:
        from ios_geometry_simulator_source_projection import current_source_before_owned_geometry
        payload = current_source_before_owned_geometry(relative, payload)
    from camera_tooling566_source_projection import current_source_before_tooling566
    payload = current_source_before_tooling566(relative, payload)
    from camera_tooling562_source_projection import current_source_before_tooling
    payload = current_source_before_tooling(relative, payload)
    from camera_home_baseline_source_projection import current_source_before_home_baseline
    payload = current_source_before_home_baseline(relative, payload)
    from arm64_stop_candidate_source_projection import current_source_before_arm64_stop_candidate
    payload = current_source_before_arm64_stop_candidate(relative, payload)
    bindings = _bindings()
    if relative in bindings and hashlib.sha256(payload).hexdigest() != bindings[relative]["after_sha256"]:
        raise ValueError("A historical image cannot replace the exact current source")
    return source_before_android_external328(relative, payload)


def text_before_android_external328(relative: str, text: str) -> str:
    if type(text) is not str:
        raise ValueError("Exact External328 source text is required")
    return source_before_android_external328(relative, text.encode("utf-8")).decode("utf-8")


def read_current_source_for_history(path: Path, root: Path) -> bytes:
    """Path identity is explicit; no digest-based guessing or general hash rewrite."""
    relative = path.relative_to(root).as_posix()
    return current_source_for_history(relative, path.read_bytes())
