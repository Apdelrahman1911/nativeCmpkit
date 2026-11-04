# SPDX-License-Identifier: Apache-2.0
"""Exact CI491 fixture recovery; not native or parser admission.

This independent leaf restores four tooling paths before older recents/boot
history. Original manifests, parser, helper, cleanup and native predicates remain.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/camera-recents-fixture-source-inverse.json"
SPEC_SHA256 = "4aaaac4178b727c388ae0969985171de0df802d0f1268b4dc6100b255c25d982"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 256 * 1024


def _bindings():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded recents-fixture manifest required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact recents-fixture manifest changed")
    document = json.loads(raw)
    if document["schema_version"] != 1 or type(document["bindings"]) is not dict:
        raise ValueError("The exact recents-fixture manifest schema required")
    return document["bindings"]


def source_before_recents_fixture(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact recents-fixture source identity and ordinary bytes required")
    from camera_tooling562_source_projection import peel_current_tooling_for_older_history
    payload = peel_current_tooling_for_older_history(relative, payload)
    from camera_boot_busy_source_projection import peel_current_boot_busy_for_older_history
    payload = peel_current_boot_busy_for_older_history(relative, payload)
    binding = _bindings().get(relative)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded recents-fixture source bytes required")
    observed = hashlib.sha256(payload).hexdigest()
    if (observed == binding["before_sha256"] or
            observed in binding.get("historical_composition_sha256", [])):
        return payload  # Exact already-qualified older composition, never current admission.
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed recents-fixture postimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique recents-fixture inverse required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("Complete original recents-fixture source required")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique recents-fixture forward site required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Exact recents-fixture forward round-trip required")
    return restored


def current_source_before_recents_fixture(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current recents-fixture identity and ordinary bytes required")
    from camera_tooling562_source_projection import current_source_before_tooling
    payload = current_source_before_tooling(relative, payload)
    from camera_boot_busy_source_projection import peel_current_boot_busy_for_older_history
    payload = peel_current_boot_busy_for_older_history(relative, payload)
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace exact current recents-fixture source")
    return source_before_recents_fixture(relative, payload)
