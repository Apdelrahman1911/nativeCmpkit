# SPDX-License-Identifier: Apache-2.0
"""Exact fixture581 descendant of owned575; never a native/compiler input.

Historical workflow hashes qualify their own source stage. Current validation
still admits the actual complete latest bytes first, without changing any dated
pin or interpreting a source-only pass as native execution.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/ios-owned-geometry581-fixture-recovery.json"
SPEC_SHA256 = "441995a9a586509700a8359c744c6a2d7420abed2df2924333c6f111598dcd58"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024

# One later fixture-only mirror leaf; every dated manifest remains immutable.
# The exact full before/after files and unique fragment are independently bound.
MIRROR_BINDING = {'after_fragment': '        paths = set(spec["bindings"]) | set(spec["added_inputs"])\n'
                   '        owning = owned_history._document()\n'
                   '        paths |= set(owning["bindings"]) | set(owning["added_inputs"])\n'
                   '        import ios_owned_geometry_fixture_recovery as fixture_recovery\n'
                   '        newest = fixture_recovery._document()\n'
                   '        paths |= set(newest["bindings"]) | set(newest["added_inputs"])\n'
                   '        with tempfile.TemporaryDirectory() as temporary:\n'
                   '            root = Path(temporary)\n'
                   '            for name in paths:\n',
 'after_fragment_sha256': '05c0912d0b3f50d06185ea519585e7abd169cec10905ce8fbdb9c21fd978d5c8',
 'after_sha256': '734e2dbfa3c86ae32e73043054c25918e46f4723822de7e8f98c86f810f1cdab',
 'before_fragment': '        paths = set(spec["bindings"]) | set(spec["added_inputs"])\n'
                    '        owning = owned_history._document()\n'
                    '        paths |= set(owning["bindings"]) | set(owning["added_inputs"])\n'
                    '        with tempfile.TemporaryDirectory() as temporary:\n'
                    '            root = Path(temporary)\n'
                    '            for name in paths:\n',
 'before_fragment_sha256': '3c7bb38f56a9f311fbe63ca2e053c25dc61c4d0b249c854863199170ec136213',
 'before_sha256': 'bd857ba589e0f5db208e7a218f02aaba82cd45827c95d97f8aa27717c332c6fa',
 'path': 'scripts/ci/test_ios_popover_geometry.py'}


def _mirror_stage(relative, payload, *, current, strict):
    binding = MIRROR_BINDING
    if relative != binding["path"]:
        return payload
    observed = hashlib.sha256(payload).hexdigest()
    if current and observed != binding["after_sha256"]:
        raise ValueError("Only the exact current geometry fixture mirror can admit")
    if observed == binding["before_sha256"]:
        return payload  # Ancestor only; the current check above has already refused it.
    if observed != binding["after_sha256"]:
        if strict:
            raise ValueError("Unreviewed geometry fixture mirror is not an exact image")
        return payload  # A later dated pin must refuse unknown ancestor bytes.
    before, after = binding["before_fragment"].encode(), binding["after_fragment"].encode()
    if (not 0 < len(payload) <= MAX_SOURCE_BYTES or payload.count(after) != 1 or
            hashlib.sha256(before).hexdigest() != binding["before_fragment_sha256"] or
            hashlib.sha256(after).hexdigest() != binding["after_fragment_sha256"]):
        raise ValueError("The exact bounded geometry fixture mirror fragment is required")
    restored = payload.replace(after, before, 1)
    if (hashlib.sha256(restored).hexdigest() != binding["before_sha256"] or
            restored.count(before) != 1 or restored.replace(before, after, 1) != payload):
        raise ValueError("The complete geometry fixture mirror must round trip exactly")
    return restored


def _document():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded fixture581 manifest is required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact fixture581 manifest changed")
    document = json.loads(raw)
    if (type(document.get("schema_version")) is not int or document["schema_version"] != 1 or
            type(document.get("bindings")) is not dict or type(document.get("added_inputs")) is not dict):
        raise ValueError("The exact fixture581 manifest schema is required")
    return document


def source_before_recovery(relative, payload):
    """Exact reversible ancestor view; never certify an old image as current."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact fixture581 source identity and ordinary bytes are required")
    from camera_home_affinity_source_projection import peel_home_affinity_for_history
    payload = peel_home_affinity_for_history(relative, payload)
    payload = _mirror_stage(relative, payload, current=False, strict=True)
    binding = _document()["bindings"].get(relative)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded fixture581 source bytes are required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed fixture581 source is not the exact afterimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique fixture581 inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("Fixture581 inverse did not restore its complete prior source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique fixture581 forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Fixture581 round trip differs from actual current bytes")
    return restored


def current_source_before_recovery(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current fixture581 identity and ordinary bytes are required")
    from camera_home_affinity_source_projection import current_source_before_home_affinity
    payload = current_source_before_home_affinity(relative, payload)
    payload = _mirror_stage(relative, payload, current=True, strict=True)
    binding = _document()["bindings"].get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("An old fixture cannot replace exact current fixture581 source")
    return source_before_recovery(relative, payload)


def peel_current_recovery_for_history(relative, payload):
    """No admission: unchanged or unknown bytes still require their next pin."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact ancestor fixture581 identity and ordinary bytes are required")
    from camera_home_affinity_source_projection import peel_home_affinity_for_history
    payload = peel_home_affinity_for_history(relative, payload)
    payload = _mirror_stage(relative, payload, current=False, strict=False)
    binding = _document()["bindings"].get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() == binding["after_sha256"]:
        return source_before_recovery(relative, payload)
    return payload


def validate_current_sources(root: Path):
    document = _document()
    expected = {name: binding["after_sha256"] for name, binding in document["bindings"].items()} | document["added_inputs"]
    from ios_popover_anchor_plan import _ordinary_bytes
    from camera_home_affinity_source_projection import current_source_before_home_affinity
    for name, digest in expected.items():
        if hashlib.sha256(current_source_before_home_affinity(name, _ordinary_bytes(root, name)[0])).hexdigest() != digest:
            raise ValueError("Current fixture581 source differs from its exact owning image: " + name)
    return True
