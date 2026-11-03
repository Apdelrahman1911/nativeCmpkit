# SPDX-License-Identifier: Apache-2.0
"""Exact additive foreground-readiness history for offline source readers only.

Current native input uses current files. The old Worker six/23 manifest, live
identity/foreground/input/lifecycle gates and original native bodies are held.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/ios-xcui-foreground-source-inverse.json"
SPEC_SHA256 = "f26e8270b6c8d950bbce725371120316b6a9a55c8b3e2b36fa009c2820d3f6d3"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 256 * 1024


def _bindings():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded foreground-readiness manifest required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact foreground-readiness manifest changed")
    document = json.loads(raw)
    if document["schema_version"] != 1 or type(document["bindings"]) is not dict:
        raise ValueError("The exact foreground-readiness manifest schema required")
    return document["bindings"]


def source_before_xcui_foreground(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact foreground-readiness source identity and ordinary bytes required")
    from camera_boot_handoff_source_projection import source_before_boot_handoff
    payload = source_before_boot_handoff(relative, payload)
    binding = _bindings().get(relative)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded foreground-readiness source bytes required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload  # Exact historical idempotence, not current admission.
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed foreground-readiness postimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique foreground-readiness inverse required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("Complete original foreground-readiness source required")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique foreground-readiness forward site required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Exact foreground-readiness forward round-trip required")
    return restored


def current_source_before_xcui_foreground(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current foreground-readiness identity and ordinary bytes required")
    from camera_boot_handoff_source_projection import current_source_before_boot_handoff
    payload = current_source_before_boot_handoff(relative, payload)
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace the exact current foreground-readiness source")
    return source_before_xcui_foreground(relative, payload)
