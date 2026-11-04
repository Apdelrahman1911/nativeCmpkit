# SPDX-License-Identifier: Apache-2.0
"""One raw-current ingress, followed by exact idempotent tooling ancestors.

This inverse serves offline source controls only. It never changes actual
helpers, native methods, compiler inputs, old pins or a result collector.
Unknown and historical bytes cannot replace a listed current image. Nested
readers use only the ancestor peel: they must not admit current bytes twice.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/camera-tooling566-source-inverse.json"
SPEC_SHA256 = "04fe85ecea2e04df03f05386250168b1b12fe1d3c1aae0783e3b22fa6344ee6e"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024


def _bindings():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded camera-tooling566 manifest is required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact camera-tooling566 manifest changed")
    document = json.loads(raw)
    if type(document.get("schema_version")) is not int or document["schema_version"] != 1 or type(document.get("bindings")) is not dict:
        raise ValueError("The exact camera-tooling566 manifest schema is required")
    return document["bindings"]


def source_before_tooling566(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact camera-tooling566 identity and ordinary source bytes are required")
    binding = _bindings().get(relative)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded camera-tooling566 source bytes are required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload  # Ancestor-only idempotence; not raw-current admission.
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed camera-tooling566 source is not an admitted afterimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique camera-tooling566 inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("Camera-tooling566 inverse did not restore its complete prior source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique camera-tooling566 forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Camera-tooling566 round trip differs from the actual current bytes")
    return restored


def current_source_before_tooling566(relative, payload):
    """The only new raw ingress; old bytes must not masquerade as current."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current camera-tooling566 identity and ordinary bytes are required")
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace the exact current camera-tooling566 source")
    return source_before_tooling566(relative, payload)


def peel_current_tooling566_for_older_history(relative, payload):
    """Not current admission: every untouched image still needs its older pin."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact ancestor camera-tooling566 identity and ordinary bytes are required")
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() == binding["after_sha256"]:
        return source_before_tooling566(relative, payload)
    return payload
