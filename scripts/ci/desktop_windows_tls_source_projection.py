# SPDX-License-Identifier: Apache-2.0
"""Exact Windows TLS recovery source history, offline readers only.

No native selector imports this inverse, no old pin is refreshed, and no
historical image may replace current source. Full-byte and fragment custody.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/desktop-windows-tls-source-inverse.json"
SPEC_SHA256 = 'cb16f295b53c4568991d14d9db4911283c7703c3f5864858aba0f86a23ebabfc'
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024


def _bindings():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("An ordinary bounded exact Windows TLS recovery manifest is required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact Windows TLS recovery manifest changed")
    document = json.loads(raw)
    if document["schema_version"] != 1 or type(document["bindings"]) is not dict:
        raise ValueError("The exact Windows TLS recovery manifest schema is required")
    return document["bindings"]


def source_before_windows_tls(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact Windows TLS recovery source identity and ordinary bytes are required")
    binding = _bindings().get(relative)
    # Compose the later modal patch before the unchanged historical TLS pins.
    # An already-restored TLS preimage keeps its original idempotence.
    if binding is None or hashlib.sha256(payload).hexdigest() != binding["before_sha256"]:
        from ios_modal_ownership_source_projection import source_before_modal_ownership
        payload = source_before_modal_ownership(relative, payload)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded Windows TLS recovery source bytes are required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed Windows TLS recovery source is not an admitted postimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique Windows TLS recovery inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("Windows TLS recovery inverse did not restore the complete prior source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique Windows TLS recovery forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Windows TLS recovery round-trip differs from the actual current bytes")
    return restored


def current_source_before_windows_tls(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current Windows TLS recovery source identity and ordinary bytes are required")
    from ios_modal_ownership_source_projection import current_source_before_modal_ownership
    payload = current_source_before_modal_ownership(relative, payload)
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace the exact current Windows TLS recovery source")
    return source_before_windows_tls(relative, payload)
