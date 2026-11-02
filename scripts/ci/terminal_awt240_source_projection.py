#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Exact, inert source inverses for the terminal/AWT240 owning patch.

Historical source-contract tests may reconstruct their previously qualified
bytes. Current library/native tests never execute reconstructed source. Each
listed change requires full source hashes, unique finite fragments, an exact
inverse and a forward round-trip. No Git, compiler, SDK, process or native action.
This is not a general repinning mechanism or a security attestation.
"""
import hashlib
import json
from pathlib import Path

SPEC_PATH = Path(__file__).parent / "fixtures/terminal-awt240-source-inverse.json"


def source_before_terminal_awt240(relative: str, payload: bytes) -> bytes:
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact source identity and ordinary bytes are required")
    bindings = json.loads(SPEC_PATH.read_text(encoding="utf-8"))["bindings"]
    if relative not in bindings:
        return payload
    binding = bindings[relative]
    if not 0 < len(payload) <= 4 * 1024 * 1024:
        raise ValueError("Bounded source bytes are required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload # A preceding exact inverse may already have restored this leaf.
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed terminal/AWT240 source is not an admitted postimage")
    restored = payload
    for item in reversed(binding["fragments"]):
        before, after = item["before"].encode(), item["after"].encode()
        if (hashlib.sha256(before).hexdigest() != item["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != item["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique terminal/AWT240 inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("Terminal/AWT240 inverse did not restore the original whole source")
    forward = restored
    for item in binding["fragments"]:
        before, after = item["before"].encode(), item["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique terminal/AWT240 forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Terminal/AWT240 forward round-trip differs from current bytes")
    return restored


def text_before_terminal_awt240(relative: str, text: str) -> str:
    if type(text) is not str:
        raise ValueError("Exact source text is required")
    return source_before_terminal_awt240(relative, text.encode("utf-8")).decode("utf-8")
