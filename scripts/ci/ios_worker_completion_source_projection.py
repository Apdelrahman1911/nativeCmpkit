# SPDX-License-Identifier: Apache-2.0
"""Exact additive Worker completion observation history for offline readers only.

The live native selectors use current files; every old pin and manifest remains
immutable. Complete current admission, fragment custody and round-trip required.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/ios-worker-completion-source-inverse.json"
SPEC_SHA256 = "5e08c7a05137b117d080b74f698a13a0fe6cd25c439eab40750de0e260faef60"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024


def _bindings():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded Worker completion observation manifest required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact Worker completion observation manifest changed")
    document = json.loads(raw)
    if document["schema_version"] != 1 or type(document["bindings"]) is not dict:
        raise ValueError("The exact Worker completion observation manifest schema required")
    return document["bindings"]


def source_before_worker_completion(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact Worker completion observation source identity and ordinary bytes required")
    binding = _bindings().get(relative)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded Worker completion observation source bytes required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload  # Exact inverse idempotence, never current admission.
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed Worker completion observation postimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique Worker completion observation inverse required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("Complete original Worker completion observation source required")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique Worker completion observation forward site required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Exact Worker completion observation forward round-trip required")
    return restored


def current_source_before_worker_completion(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current Worker completion observation identity and ordinary bytes required")
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace the exact current Worker completion observation source")
    return source_before_worker_completion(relative, payload)
