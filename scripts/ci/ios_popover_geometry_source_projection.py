# SPDX-License-Identifier: Apache-2.0
"""Exact additive popover history for offline readers; never live native inputs.

The current reader requires the complete newest afterimage. The ancestor adapter
peels only that exact image and leaves older images to their existing pinned
readers; it does not certify arbitrary old or unknown bytes as current.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/ios-popover-geometry-source-inverse.json"
SPEC_SHA256 = "a19b28201b2e77644109c97f636323865ff7a250b2e58474a6ac567a36cbc723"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024


def _bindings():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded popover-geometry manifest is required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact popover-geometry manifest changed")
    document = json.loads(raw)
    if type(document.get("schema_version")) is not int or document["schema_version"] != 1 or type(document.get("bindings")) is not dict:
        raise ValueError("The exact popover-geometry manifest schema is required")
    return document["bindings"]


def source_before_geometry(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact popover-geometry identity and ordinary source bytes are required")
    from ios_geometry_simulator_source_projection import peel_current_owned_geometry_for_older_history
    payload = peel_current_owned_geometry_for_older_history(relative, payload)
    binding = _bindings().get(relative)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded popover-geometry source bytes are required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload  # Historical idempotence only, never current admission.
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed popover-geometry source is not an admitted postimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique popover-geometry inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("Popover-geometry inverse did not restore its complete prior source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique popover-geometry forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Popover-geometry round-trip differs from the actual current bytes")
    return restored


def current_source_before_geometry(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current popover-geometry identity and ordinary bytes are required")
    # Nested historical reader: never readmit the outer raw source a second time.
    from ios_geometry_simulator_source_projection import peel_current_owned_geometry_for_older_history
    payload = peel_current_owned_geometry_for_older_history(relative, payload)
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace the exact current popover-geometry source")
    return source_before_geometry(relative, payload)


def peel_current_geometry_for_older_history(relative, payload):
    """Not current admission: untouched old bytes MUST pass their older pinned reader."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact ancestor popover-geometry identity and ordinary bytes are required")
    from ios_geometry_simulator_source_projection import peel_current_owned_geometry_for_older_history
    payload = peel_current_owned_geometry_for_older_history(relative, payload)
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() == binding["after_sha256"]:
        return source_before_geometry(relative, payload)
    return payload


def validate_current_sources(root: Path):
    """Exact latest postimages/additions only; no historical or partial source acceptance."""
    bindings = _bindings()
    raw = SPEC_PATH.read_bytes()
    document = json.loads(raw)
    expected = {path: value["after_sha256"] for path, value in bindings.items()} | document["added_inputs"]
    import ios_geometry_simulator_source_projection as owned_history
    owned_history.validate_current_sources(root)
    from ios_popover_anchor_plan import _ordinary_bytes
    for path, digest in expected.items():
        payload = _ordinary_bytes(root, path)[0]
        payload = owned_history.current_source_before_owned_geometry(path, payload)
        if hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError("Current geometry source differs from its exact owning postimage: " + path)
    return True
