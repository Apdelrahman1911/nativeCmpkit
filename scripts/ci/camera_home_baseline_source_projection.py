# SPDX-License-Identifier: Apache-2.0
"""Exact preserved-HOME history for offline fixtures, never native admission.

Current admission requires the full new source. Ancestor readers peel only the
declared exact afterimage and still enforce their unchanged older pins. Unknown,
partial or displaced sources are never guessed or patched into an ancestor.
The new parser/epoch/action behavior has its own controls and native gate.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/camera-home-baseline-source-inverse.json"
SPEC_SHA256 = "b968373d8de34a53525efd291055ad61f8d034a17236f663d8c58ba4c0716dcb"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024


def _bindings():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded preserved-HOME manifest is required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact preserved-HOME manifest changed")
    document = json.loads(raw)
    if type(document.get("schema_version")) is not int or document["schema_version"] != 1 or type(document.get("bindings")) is not dict:
        raise ValueError("The exact preserved-HOME manifest schema is required")
    return document["bindings"]


def source_before_home_baseline(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact preserved-HOME identity and ordinary source bytes are required")
    binding = _bindings().get(relative)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded preserved-HOME source bytes are required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload  # Historical idempotence only, never current admission.
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed preserved-HOME source is not an admitted afterimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique preserved-HOME inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("Preserved-HOME inverse did not restore its complete prior source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique preserved-HOME forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Preserved-HOME round trip differs from the actual current bytes")
    return restored


def current_source_before_home_baseline(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current preserved-HOME identity and ordinary bytes are required")
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace the exact current preserved-HOME source")
    return source_before_home_baseline(relative, payload)


def peel_current_home_baseline_for_older_history(relative, payload):
    """Ancestor-only: untouched bytes MUST satisfy the next older pinned reader."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact ancestor preserved-HOME identity and ordinary bytes are required")
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() == binding["after_sha256"]:
        return source_before_home_baseline(relative, payload)
    return payload
