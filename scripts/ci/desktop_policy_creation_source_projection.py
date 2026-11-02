# SPDX-License-Identifier: Apache-2.0
"""Exact policy creation/recovery source history, offline readers only.

No native selector imports this inverse, no old pin is refreshed, and no
historical image may replace current source. Full-byte and fragment custody.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/desktop-policy-creation-source-inverse.json"
SPEC_SHA256 = "51df07d4bab5a532747535d572e69c54ac289902935c6aecb6ef2b21b0950ce5"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024


def _bindings():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("An ordinary bounded exact policy creation manifest is required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact policy creation manifest changed")
    document = json.loads(raw)
    if document["schema_version"] != 1 or type(document["bindings"]) is not dict:
        raise ValueError("The exact policy creation manifest schema is required")
    return document["bindings"]


def source_before_policy_creation(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact policy creation source identity and ordinary bytes are required")
    binding = _bindings().get(relative)
    # A later exact offline stage must compose before the unchanged seven pins.
    # Already-restored historical preimages retain their original idempotence.
    if binding is None or hashlib.sha256(payload).hexdigest() != binding["before_sha256"]:
        from desktop_windows_tls_source_projection import source_before_windows_tls
        payload = source_before_windows_tls(relative, payload)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded policy creation source bytes are required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed policy creation source is not an admitted postimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique policy creation inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("policy creation inverse did not restore the complete prior source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique policy creation forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("policy creation round-trip differs from the actual current bytes")
    return restored


def current_source_before_policy_creation(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current policy creation source identity and ordinary bytes are required")
    from desktop_windows_tls_source_projection import current_source_before_windows_tls
    payload = current_source_before_windows_tls(relative, payload)
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace the exact current policy creation source")
    return source_before_policy_creation(relative, payload)
