# SPDX-License-Identifier: Apache-2.0
"""Exact CI476 fixture recovery, not a change to Android/native admission.

The original boot-handoff manifest, old endpoint pins and native predicates
remain intact. This independent inverse admits the three current tooling paths
before composing their previous fixture stage. No digest is guessed or rebased.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/camera-handoff-fixture-source-inverse.json"
SPEC_SHA256 = "29da5ee28cd1aa1c1859c076895c0d62080743d2ab4bd447983dddd15684b565"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 256 * 1024


def _bindings():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded handoff-fixture manifest required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact handoff-fixture manifest changed")
    document = json.loads(raw)
    if document["schema_version"] != 1 or type(document["bindings"]) is not dict:
        raise ValueError("The exact handoff-fixture manifest schema required")
    return document["bindings"]


def source_before_handoff_fixture(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact handoff-fixture source identity and ordinary bytes required")
    from camera_recents_source_projection import source_before_recents_observation
    payload = source_before_recents_observation(relative, payload)
    binding = _bindings().get(relative)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded handoff-fixture source bytes required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload  # Historical composition only; never current admission.
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed handoff-fixture postimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique handoff-fixture inverse required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("Complete original handoff-fixture source required")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique handoff-fixture forward site required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Exact handoff-fixture forward round-trip required")
    return restored


def current_source_before_handoff_fixture(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current handoff-fixture identity and ordinary bytes required")
    from camera_recents_source_projection import current_source_before_recents_observation
    payload = current_source_before_recents_observation(relative, payload)
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace exact current handoff-fixture source")
    return source_before_handoff_fixture(relative, payload)
