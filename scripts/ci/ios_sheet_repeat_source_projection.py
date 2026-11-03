# SPDX-License-Identifier: Apache-2.0
"""Exact additive same-operation cancellation history for offline readers only.

The live native selectors use current files; every old pin and manifest remains
immutable. Complete current admission, fragment custody and round-trip required.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/ios-sheet-repeat-source-inverse.json"
SPEC_SHA256 = "a821c1b93c44e71afa2142b4ba10d84e0117bbf017f790130a38c565890c971a"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024


def _bindings():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded sheet same-operation manifest required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact sheet same-operation manifest changed")
    document = json.loads(raw)
    if document["schema_version"] != 1 or type(document["bindings"]) is not dict:
        raise ValueError("The exact sheet same-operation manifest schema required")
    return document["bindings"]


def source_before_sheet_repeat(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact sheet same-operation source identity and ordinary bytes required")
    binding = _bindings().get(relative)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded sheet same-operation source bytes required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload  # Exact inverse idempotence, never current admission.
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed sheet same-operation postimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique sheet same-operation inverse required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("Complete original sheet same-operation source required")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique sheet same-operation forward site required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Exact sheet same-operation forward round-trip required")
    return restored


def current_source_before_sheet_repeat(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current sheet same-operation identity and ordinary bytes required")
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace the exact current sheet same-operation source")
    return source_before_sheet_repeat(relative, payload)
