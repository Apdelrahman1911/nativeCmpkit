# SPDX-License-Identifier: Apache-2.0
"""Exact ARM64 Stop-only source history; never imported by live native selectors.

Admit complete current sources before composing the preserved External328 inverse.
An inverse may receive its own complete prior image; a current reader may not.
No historical hash refresh, digest-based identity guessing or native fallback.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/arm64-stop-candidate-source-inverse.json"
SPEC_SHA256 = "a3b72d71cf22c65dcd39e29d5cec0c2dbc3ebe6648fd0134b1dfb283c4edbf1f"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024


def _bindings():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("An ordinary bounded exact ARM64 Stop manifest is required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact ARM64 Stop manifest changed")
    document = json.loads(raw)
    if document["schema_version"] != 1 or type(document["bindings"]) is not dict:
        raise ValueError("The exact ARM64 Stop manifest schema is required")
    return document["bindings"]


def source_before_arm64_stop_candidate(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact ARM64 Stop source identity and ordinary bytes are required")
    from camera_tooling566_source_projection import peel_current_tooling566_for_older_history
    payload = peel_current_tooling566_for_older_history(relative, payload)
    from camera_tooling562_source_projection import peel_current_tooling_for_older_history
    payload = peel_current_tooling_for_older_history(relative, payload)
    binding = _bindings().get(relative)
    # Retain this stage's original complete-preimage idempotence before newer admission.
    if (binding is not None and 0 < len(payload) <= MAX_SOURCE_BYTES and
            hashlib.sha256(payload).hexdigest() == binding["before_sha256"]):
        return payload
    from desktop_policy_creation_source_projection import source_before_policy_creation
    payload = source_before_policy_creation(relative, payload)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded ARM64 Stop source bytes are required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed ARM64 Stop source is not an admitted postimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique ARM64 Stop inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("ARM64 Stop inverse did not restore the complete prior source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique ARM64 Stop forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("ARM64 Stop round-trip differs from the actual current bytes")
    return restored


def current_source_before_arm64_stop_candidate(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current ARM64 Stop source identity and ordinary bytes are required")
    # The outer raw checkout reader already qualified the latest tooling image.
    # Exact stage peeling must remain idempotent inside this older composition.
    from camera_tooling566_source_projection import peel_current_tooling566_for_older_history
    payload = peel_current_tooling566_for_older_history(relative, payload)
    from camera_tooling562_source_projection import peel_current_tooling_for_older_history
    payload = peel_current_tooling_for_older_history(relative, payload)
    from desktop_policy_creation_source_projection import current_source_before_policy_creation
    payload = current_source_before_policy_creation(relative, payload)
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace the exact current ARM64 Stop source")
    return source_before_arm64_stop_candidate(relative, payload)
