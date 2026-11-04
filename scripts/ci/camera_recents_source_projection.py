# SPDX-License-Identifier: Apache-2.0
"""Exact failure-only camera483 source history, never native or parser admission.

This newest leaf runs before older fixture/boot history. Its manifest restores
only the two existing tooling paths. Original parser/helper/cleanup/native bytes
and every older manifest/pin remain unchanged. No recursive normalization.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/camera-recents-observation-source-inverse.json"
SPEC_SHA256 = "0329eb385d26e9ef90e6c3f92604672e1e76215c9513bbf88c06498eb5f1e028"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 256 * 1024


def _bindings():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded recents-observation manifest required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact recents-observation manifest changed")
    document = json.loads(raw)
    if document["schema_version"] != 1 or type(document["bindings"]) is not dict:
        raise ValueError("The exact recents-observation manifest schema required")
    return document["bindings"]


def source_before_recents_observation(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact recents-observation source identity and ordinary bytes required")
    from webview_content_policy_source_projection import peel_content_policy_for_history
    payload = peel_content_policy_for_history(relative, payload)
    from camera_recents_fixture_source_projection import source_before_recents_fixture
    payload = source_before_recents_fixture(relative, payload)
    binding = _bindings().get(relative)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded recents-observation source bytes required")
    observed = hashlib.sha256(payload).hexdigest()
    if (observed == binding["before_sha256"] or
            observed in binding.get("historical_composition_sha256", [])):
        return payload  # Exact already-qualified older composition, never current admission.
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed recents-observation postimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique recents-observation inverse required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("Complete original recents-observation source required")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique recents-observation forward site required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Exact recents-observation forward round-trip required")
    return restored


def current_source_before_recents_observation(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current recents-observation identity and ordinary bytes required")
    from webview_content_policy_source_projection import peel_content_policy_for_history
    payload = peel_content_policy_for_history(relative, payload)
    from camera_recents_fixture_source_projection import current_source_before_recents_fixture
    payload = current_source_before_recents_fixture(relative, payload)
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace exact current recents-observation source")
    return source_before_recents_observation(relative, payload)
