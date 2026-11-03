# SPDX-License-Identifier: Apache-2.0
"""Exact iOS modal ownership source history, offline readers only.

No native selector imports this inverse, no old pin is refreshed, and no
historical image may replace current source. Full-byte and fragment custody.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

import ios_modal_lifecycle_source_projection as lifecycle_history

SPEC_PATH = Path(__file__).parent / "fixtures/ios-modal-ownership-source-inverse.json"
SPEC_SHA256 = '541e0e1f5d08dc699a8a450361ef00780de2e5c92607b0a141c487fd1156c72f'
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024


def _bindings():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("An ordinary bounded exact iOS modal ownership manifest is required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact iOS modal ownership manifest changed")
    document = json.loads(raw)
    if document["schema_version"] != 1 or type(document["bindings"]) is not dict:
        raise ValueError("The exact iOS modal ownership manifest schema is required")
    return document["bindings"]


def source_before_modal_ownership(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact iOS modal ownership source identity and ordinary bytes are required")
    binding = _bindings().get(relative)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded iOS modal ownership source bytes are required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload
    payload = lifecycle_history.source_before_modal_lifecycle(relative, payload)
    observed = hashlib.sha256(payload).hexdigest()
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed iOS modal ownership source is not an admitted postimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique iOS modal ownership inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("iOS modal ownership inverse did not restore the complete prior source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique iOS modal ownership forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("iOS modal ownership round-trip differs from the actual current bytes")
    return restored


def current_source_before_modal_ownership(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current iOS modal ownership source identity and ordinary bytes are required")
    binding = _bindings().get(relative)
    if binding is not None:
        payload = lifecycle_history.current_source_before_modal_lifecycle(relative, payload)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace the exact current iOS modal ownership source")
    return source_before_modal_ownership(relative, payload)
