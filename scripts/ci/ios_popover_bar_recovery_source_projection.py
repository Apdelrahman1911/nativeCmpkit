# SPDX-License-Identifier: Apache-2.0
"""Exact additive popover history for offline readers; never live native inputs.

The current reader requires the complete newest afterimage. The ancestor adapter
peels only that exact image and leaves older images to their existing pinned
readers; it does not certify arbitrary old or unknown bytes as current.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/ios-popover-bar-recovery-source-inverse.json"
SPEC_SHA256 = "73d76bddfa722ec816c397e0dd1fbb069178908475742ff5424162615e1f2127"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024


def _bindings():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded bar-recovery manifest is required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact bar-recovery manifest changed")
    document = json.loads(raw)
    if type(document.get("schema_version")) is not int or document["schema_version"] != 1 or type(document.get("bindings")) is not dict:
        raise ValueError("The exact bar-recovery manifest schema is required")
    return document["bindings"]


def source_before_bar_recovery(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact bar-recovery identity and ordinary source bytes are required")
    binding = _bindings().get(relative)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded bar-recovery source bytes are required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload  # Historical idempotence only, never current admission.
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed bar-recovery source is not an admitted postimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique bar-recovery inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("Bar-recovery inverse did not restore its complete prior source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique bar-recovery forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Bar-recovery round-trip differs from the actual current bytes")
    return restored


def current_source_before_bar_recovery(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current bar-recovery identity and ordinary bytes are required")
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace the exact current bar-recovery source")
    return source_before_bar_recovery(relative, payload)


def peel_current_bar_for_older_history(relative, payload):
    """Not current admission: untouched old bytes MUST pass their older pinned reader."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact ancestor bar-recovery identity and ordinary bytes are required")
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() == binding["after_sha256"]:
        return source_before_bar_recovery(relative, payload)
    return payload
