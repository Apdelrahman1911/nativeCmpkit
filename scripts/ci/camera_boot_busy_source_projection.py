# SPDX-License-Identifier: Apache-2.0
"""Exact additive busy-boot history for offline readers; never live native inputs.

The current reader requires the complete newest afterimage. The ancestor adapter
peels only that exact image and leaves older images to their existing pinned
readers; it does not certify arbitrary old or unknown bytes as current.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/camera-boot-busy-source-inverse.json"
SPEC_SHA256 = "280c1c631b570d62588458d01dbd02030be3e6d7a0535a34c30e701b6fff1f3e"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024


def _bindings():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded busy-boot manifest is required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact busy-boot manifest changed")
    document = json.loads(raw)
    if type(document.get("schema_version")) is not int or document["schema_version"] != 1 or type(document.get("bindings")) is not dict:
        raise ValueError("The exact busy-boot manifest schema is required")
    return document["bindings"]


def source_before_boot_busy(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact busy-boot identity and ordinary source bytes are required")
    from camera_home_baseline_source_projection import peel_current_home_baseline_for_older_history
    payload = peel_current_home_baseline_for_older_history(relative, payload)
    binding = _bindings().get(relative)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded busy-boot source bytes are required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload  # Historical idempotence only, never current admission.
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed busy-boot source is not an admitted postimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique busy-boot inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("Busy-boot inverse did not restore its complete prior source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique busy-boot forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Busy-boot round-trip differs from the actual current bytes")
    return restored


def current_source_before_boot_busy(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current busy-boot identity and ordinary bytes are required")
    from camera_home_baseline_source_projection import current_source_before_home_baseline
    payload = current_source_before_home_baseline(relative, payload)
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace the exact current busy-boot source")
    return source_before_boot_busy(relative, payload)


def peel_current_boot_busy_for_older_history(relative, payload):
    """Not current admission: untouched old bytes MUST pass their older pinned reader."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact ancestor busy-boot identity and ordinary bytes are required")
    from camera_home_baseline_source_projection import peel_current_home_baseline_for_older_history
    payload = peel_current_home_baseline_for_older_history(relative, payload)
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() == binding["after_sha256"]:
        return source_before_boot_busy(relative, payload)
    return payload
