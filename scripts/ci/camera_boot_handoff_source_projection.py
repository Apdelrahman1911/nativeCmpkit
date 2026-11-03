# SPDX-License-Identifier: Apache-2.0
"""Exact camera boot-handoff history for offline fixture readers, never native.

The old camera compiler/order controls still test their unchanged old stage.
Current admission is separate, full-byte and reversible; historical pins and
test bodies are not recalculated. New handoff behavior has its own controls.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/camera-boot-handoff-source-inverse.json"
SPEC_SHA256 = "525f7f43222f92ab5730d0154e817dbfc60858e21b1daaa60d5203d954535367"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 256 * 1024


def _bindings():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded boot-handoff manifest required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact boot-handoff manifest changed")
    document = json.loads(raw)
    if document["schema_version"] != 1 or type(document["bindings"]) is not dict:
        raise ValueError("The exact boot-handoff manifest schema required")
    return document["bindings"]


def source_before_boot_handoff(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact boot-handoff source identity and ordinary bytes required")
    from camera_handoff_fixture_source_projection import source_before_handoff_fixture
    payload = source_before_handoff_fixture(relative, payload)
    binding = _bindings().get(relative)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded boot-handoff source bytes required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload  # Historical idempotence, never current admission.
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed boot-handoff postimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique boot-handoff inverse required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("Complete original boot-handoff source required")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique boot-handoff forward site required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Exact boot-handoff forward round-trip required")
    return restored


def current_source_before_boot_handoff(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current boot-handoff identity and ordinary bytes required")
    from camera_handoff_fixture_source_projection import current_source_before_handoff_fixture
    payload = current_source_before_handoff_fixture(relative, payload)
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace exact current boot-handoff source")
    return source_before_boot_handoff(relative, payload)
