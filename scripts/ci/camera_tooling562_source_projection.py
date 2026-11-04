# SPDX-License-Identifier: Apache-2.0
"""Exact camera-tooling562 history for offline fixtures, never native admission.

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

SPEC_PATH = Path(__file__).parent / "fixtures/camera-tooling562-source-inverse.json"
SPEC_SHA256 = "e91e9f3ccbf98238d7fcb7f82a6cedce492451fb15bfcb381ace6616cd43dfdc"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024


def _bindings():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded camera-tooling562 manifest is required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact camera-tooling562 manifest changed")
    document = json.loads(raw)
    if type(document.get("schema_version")) is not int or document["schema_version"] != 1 or type(document.get("bindings")) is not dict:
        raise ValueError("The exact camera-tooling562 manifest schema is required")
    return document["bindings"]


def source_before_tooling(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact camera-tooling562 identity and ordinary source bytes are required")
    binding = _bindings().get(relative)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded camera-tooling562 source bytes are required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload  # Historical idempotence only, never current admission.
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed camera-tooling562 source is not an admitted afterimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique camera-tooling562 inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("Camera-tooling562 inverse did not restore its complete prior source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique camera-tooling562 forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Camera-tooling562 round trip differs from the actual current bytes")
    return restored


def current_source_before_tooling(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current camera-tooling562 identity and ordinary bytes are required")
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace the exact current camera-tooling562 source")
    return source_before_tooling(relative, payload)


def peel_current_tooling_for_older_history(relative, payload):
    """Ancestor-only: untouched bytes MUST satisfy the next older pinned reader."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact ancestor camera-tooling562 identity and ordinary bytes are required")
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() == binding["after_sha256"]:
        return source_before_tooling(relative, payload)
    return payload
