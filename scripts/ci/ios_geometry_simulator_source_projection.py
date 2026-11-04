# SPDX-License-Identifier: Apache-2.0
"""Exact owned-geometry source stages for offline fixtures, not native inputs.

Raw checkout admission requires the complete latest bound image exactly once.
Nested readers peel only that exact image and still enforce their dated pins.
No old expected hash, native assertion, compiler input or result is replaced.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/ios-owned-geometry575-source-inverse.json"
SPEC_SHA256 = "736ef0e38d1e89baa0c7cbdd0707189d28a197b08fb11500943d94cede28efdd"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024


def _document():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded owned-geometry manifest is required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact owned-geometry manifest changed")
    document = json.loads(raw)
    if (type(document.get("schema_version")) is not int or document["schema_version"] != 1 or
            type(document.get("bindings")) is not dict or type(document.get("added_inputs")) is not dict):
        raise ValueError("The exact owned-geometry manifest schema is required")
    return document


def _bindings():
    return _document()["bindings"]


def source_before_owned_geometry(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact owned-geometry identity and ordinary source bytes are required")
    binding = _bindings().get(relative)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded owned-geometry source bytes are required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload  # Ancestor-only idempotence, never current admission.
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed owned-geometry source is not an admitted afterimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique owned-geometry inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("Owned-geometry inverse did not restore its complete prior source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique owned-geometry forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Owned-geometry round trip differs from the actual current bytes")
    return restored


def current_source_before_owned_geometry(relative, payload):
    """Only the outer raw checkout boundary may certify a listed latest image."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current owned-geometry identity and ordinary bytes are required")
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace the exact current owned-geometry source")
    return source_before_owned_geometry(relative, payload)


def peel_current_owned_geometry_for_older_history(relative, payload):
    """Not current admission: unknown/older bytes still need their next older pin."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact ancestor owned-geometry identity and ordinary bytes are required")
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() == binding["after_sha256"]:
        return source_before_owned_geometry(relative, payload)
    return payload


def validate_current_sources(root: Path):
    """Live admission uses actual new bytes; the inverse is never a native input."""
    document = _document()
    expected = {name: row["after_sha256"] for name, row in document["bindings"].items()} | document["added_inputs"]
    from ios_popover_anchor_plan import _ordinary_bytes
    for name, digest in expected.items():
        if hashlib.sha256(_ordinary_bytes(root, name)[0]).hexdigest() != digest:
            raise ValueError("Current owned-geometry source differs from its owning image: " + name)
    return True
