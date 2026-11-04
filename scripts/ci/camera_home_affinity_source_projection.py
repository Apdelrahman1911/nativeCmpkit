# SPDX-License-Identifier: Apache-2.0
"""Exact HOME-affinity source stage, only for source/history qualification.

One newest raw-checkout ingress requires a complete pinned afterimage. Nested
history only peels an exact afterimage and retains all earlier pins. Neither
inverse bytes nor source-control acceptance substitute for compiler/native IO.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

SPEC_PATH = Path(__file__).parent / "fixtures/camera-home-affinity-source-inverse.json"
SPEC_SHA256 = "51cc224488eb366034f8edea83f1a31465f8818059bad96a802a1fff0aa655ca"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate HOME-affinity manifest field")
        result[key] = value
    return result


def _bindings():
    before = SPEC_PATH.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded HOME-affinity manifest required")
    raw = SPEC_PATH.read_bytes()
    after = SPEC_PATH.lstat()
    identity = lambda info: (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size, info.st_mtime_ns)
    if identity(before) != identity(after) or len(raw) != before.st_size or hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact held HOME-affinity manifest changed")
    document = json.loads(raw, object_pairs_hook=_unique)
    if type(document.get("schema_version")) is not int or document["schema_version"] != 1 or type(document.get("bindings")) is not dict:
        raise ValueError("The exact HOME-affinity manifest schema required")
    return document["bindings"]


def source_before_home_affinity(relative, payload):
    """Exact ancestor view; an older image is not an admission to current code."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact HOME-affinity source identity and ordinary bytes required")
    binding = _bindings().get(relative)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded HOME-affinity source bytes required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload  # Idempotent dated ancestor, not current raw admission.
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed HOME-affinity source is not its exact afterimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique HOME-affinity inverse fragment required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("HOME-affinity inverse did not restore the complete prior source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique HOME-affinity forward fragment required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("HOME-affinity complete source round trip differs")
    return restored


def current_source_before_home_affinity(relative, payload):
    """Only one outer raw-checkout boundary admits a listed current afterimage."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current HOME-affinity identity and ordinary bytes required")
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("An old/unknown image cannot replace current HOME-affinity source")
    return source_before_home_affinity(relative, payload)


def peel_home_affinity_for_history(relative, payload):
    """No admission: unchanged or unknown bytes still require the next dated pin."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact ancestor HOME-affinity identity and ordinary bytes required")
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() == binding["after_sha256"]:
        return source_before_home_affinity(relative, payload)
    return payload
