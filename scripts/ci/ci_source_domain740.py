# SPDX-License-Identifier: Apache-2.0
"""Exact source-code/context740 transitions above immutable current303.

The broader671 caller may carry unlisted data to its unchanged historical owner;
it does not enroll that data in current303. The bridge inverse is one separately
sealed718 source transition, not a named view or restored executable.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = "scripts/ci/ci_source_domain740.py"
CONTROL = "scripts/ci/test_ci_source_domain740.py"
SPEC = "scripts/ci/fixtures/ci-source-domain740-source-inverse.json"
SPEC_SHA256 = "5b450daf9874a62a4b452b0d6502c3a77426e670ec6fd79a6b1ed3a3aecf6e52"
CURRENT303_SPEC = "scripts/ci/fixtures/macos-share-ci668-composition.json"
CURRENT303_SPEC_SHA256 = "06d04d038b06c00e5aafb9b7defdf39ae069f3df305e4dbc84198bc8ed178a24"
MAX_SOURCE = 4 * 1024 * 1024
MAX_SPEC = 512 * 1024
SCOPE = "Exact broader671 routing, reader code and dated test contexts above unchanged current303; source-only"
BEFORE = {'scripts/ci/tooling_recovery671_source_projection.py': {'sha256': '311353d09543805a3e2f9f4b9744a45ad73d59ef7812fd47fb1d5d27857f592d', 'bytes': 33878}, 'scripts/ci/macos_share_ci668_composition.py': {'sha256': 'e4a44aa4c769c69be7bd99d6d7793c767d8c187717ecd24f4fd08cd8afeabf34', 'bytes': 64373}, 'scripts/ci/test_camera_home_baseline_source_projection.py': {'sha256': '19590fbd0158d6642d2eb63849755587bd4b20882e10c6ad89b14db658ecd2a9', 'bytes': 10225}, 'scripts/ci/test_camera_tooling562_source_projection.py': {'sha256': '8021189d7f5d9e02f9e729050a9e978d75d4c6ce631cf0015990e342610ae341', 'bytes': 7881}, 'scripts/ci/test_camera_tooling566_source_projection.py': {'sha256': '11213a71c53679fa3e736d93e1eb6e06469cd8aeb72ad21a4132902b81f23161', 'bytes': 9390}, 'scripts/ci/test_macos_share_ci668_composition.py': {'sha256': '829fe4cd17bcbd6dc155278c094b82848e51f2b5478cca5d4781def9bc900fcf', 'bytes': 69459}}
FRAGMENT_COUNTS = {'scripts/ci/tooling_recovery671_source_projection.py': 3, 'scripts/ci/macos_share_ci668_composition.py': 8, 'scripts/ci/test_camera_home_baseline_source_projection.py': 2, 'scripts/ci/test_camera_tooling562_source_projection.py': 1, 'scripts/ci/test_camera_tooling566_source_projection.py': 2, 'scripts/ci/test_macos_share_ci668_composition.py': 2}
MODIFIED = frozenset(BEFORE)
BRIDGE = "scripts/ci/android_external328_source_projection.py"
BRIDGE_BEFORE = {"sha256": "d931688dd5f1bd196c6ee358a35e3c7664e1ee24639320cdecefa7057a2358f9", "bytes": 6031}
BRIDGE_AFTER = {"sha256": "2d5a75be4b8619c1a9ad23e8ecd1d665aed1fffc214946a2e4d658d4999d9e3b", "bytes": 6627}
BRIDGE_BINDING_SHA256 = "bf94e68ba3dd5e3574ad7fc01b21bda2cd82554f7e761b6dd0f3daa939ab2349"
BRIDGE_AUTHORITY = {"saved718_patch_sha256": "100d41166b3cac306f2a092c277c77f7b9b6026cf526a43f32c96512392840df",
                    "parent_commit": "626eba139830661cffe777301f83b923128fd5b7",
                    "parent_blob": "0ac1a0fd9579c099c2b1a974cbb9252173dc45f4"}


def need(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _identity(relative, payload):
    from macos_share_appkit_only_source_projection import _path
    need(type(relative) is str and 0 < len(relative) <= 4096 and type(payload) is bytes,
         "exact740-source-identity-and-ordinary-bytes-required")
    _path(relative)
    need(0 < len(payload) <= MAX_SOURCE, "bounded740-source-payload-required")


def _ordinary(root, relative, maximum=MAX_SOURCE):
    from macos_share_appkit_only_source_projection import ordinary_bytes
    from ci_source_recovery740_742 import current_source_before_recovery
    raw, identity = ordinary_bytes(root, relative, maximum)
    return current_source_before_recovery(relative, raw, root), identity


from functools import lru_cache as _fragment_utf8_lru793

_FRAGMENT_UTF8_STR793 = str
_FRAGMENT_UTF8_ENCODER793 = str.encode


@_fragment_utf8_lru793(maxsize=64)
def _cached_fragment_utf8_bytes793(text, encoder, encoding, errors):
    """Only immutable successful encoding; never a digest or source/schema result."""
    return encoder(text, encoding, errors)


def _fragment_utf8_bytes793(text):
    """Bound exact text before key hashing; foreign/large inputs stay uncached."""
    if (type(text) is _FRAGMENT_UTF8_STR793 and str is _FRAGMENT_UTF8_STR793
            and str.encode is _FRAGMENT_UTF8_ENCODER793 and 0 < len(text) <= 32768):
        return _cached_fragment_utf8_bytes793(text, str.encode, "utf-8", "strict")
    return text.encode()


def _binding(row, before, count):
    need(type(row) is dict and set(row) == {
         "before_sha256", "after_sha256", "before_bytes", "after_bytes", "fragments"}
         and all(type(row[key]) is str and len(row[key]) == 64
                 and all(c in "0123456789abcdef" for c in row[key])
                 for key in ("before_sha256", "after_sha256"))
         and all(type(row[key]) is int and 0 < row[key] <= MAX_SOURCE
                 for key in ("before_bytes", "after_bytes"))
         and (row["before_sha256"], row["before_bytes"]) == (before["sha256"], before["bytes"])
         and type(row["fragments"]) is list and len(row["fragments"]) == count and 0 < count <= 16,
         "exact740-complete-source-endpoints-and-finite-count-required")
    for fragment in row["fragments"]:
        need(type(fragment) is dict and set(fragment) == {
             "before", "after", "before_fragment_sha256", "after_fragment_sha256"}
             and type(fragment["before"]) is str and type(fragment["after"]) is str
             and 0 < len(_fragment_utf8_bytes793(fragment["before"])) <= MAX_SOURCE
             and 0 < len(_fragment_utf8_bytes793(fragment["after"])) <= MAX_SOURCE
             and fragment["before"] != fragment["after"]
             and sha(_fragment_utf8_bytes793(fragment["before"])) == fragment["before_fragment_sha256"]
             and sha(_fragment_utf8_bytes793(fragment["after"])) == fragment["after_fragment_sha256"],
             "exact740-unique-reversible-source-fragments-required")


def _document(root=ROOT):
    from macos_share_ci668_composition import _json as json_bytes
    raw = _ordinary(root, SPEC, MAX_SPEC)[0]
    need(sha(raw) == SPEC_SHA256, "exact740-transition-manifest-required")
    document = json_bytes(raw)
    need(type(document) is dict and set(document) == {
         "schema_version", "scope", "current303_spec", "bindings", "bridge_binding", "bridge_authority", "control", "own_guard"}
         and type(document["schema_version"]) is int and document["schema_version"] == 1
         and document["scope"] == SCOPE
         and document["current303_spec"] == {"path": CURRENT303_SPEC, "sha256": CURRENT303_SPEC_SHA256, "bytes": 518906}
         and type(document["bindings"]) is dict and set(document["bindings"]) == MODIFIED
         and document["bridge_authority"] == BRIDGE_AUTHORITY,
         "finite740-source-context-and-original718-bridge-schema-required")
    for relative, row in document["bindings"].items():
        _binding(row, BEFORE[relative], FRAGMENT_COUNTS[relative])
    bridge = document["bridge_binding"]
    _binding(bridge, BRIDGE_BEFORE, 1)
    encoded = (json.dumps(bridge, sort_keys=True, separators=(",", ":")) + "\n").encode()
    need(sha(encoded) == BRIDGE_BINDING_SHA256
         and (bridge["after_sha256"], bridge["after_bytes"]) == (BRIDGE_AFTER["sha256"], BRIDGE_AFTER["bytes"]),
         "exact740-original718-one-fragment-bridge-cannot-be-repinned")
    control, own = document["control"], document["own_guard"]
    need(type(control) is dict and set(control) == {"path", "sha256", "bytes"} and control["path"] == CONTROL
         and type(control["sha256"]) is str and len(control["sha256"]) == 64
         and all(c in "0123456789abcdef" for c in control["sha256"])
         and type(control["bytes"]) is int and 0 < control["bytes"] <= MAX_SOURCE
         and type(own) is dict and set(own) == {"template_sha256", "bytes"}
         and type(own["template_sha256"]) is str and len(own["template_sha256"]) == 64
         and all(c in "0123456789abcdef" for c in own["template_sha256"])
         and type(own["bytes"]) is int and 0 < own["bytes"] <= MAX_SOURCE,
         "exact740-own-helper-and-new-control-bindings-required")
    return document


def _inverse(payload, row):
    need((sha(payload), len(payload)) == (row["after_sha256"], row["after_bytes"]),
         "complete740-current-source-afterimage-required")
    restored = payload
    for fragment in reversed(row["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        need(restored.count(after) == 1, "unique740-inverse-source-site-required")
        restored = restored.replace(after, before, 1)
    need((sha(restored), len(restored)) == (row["before_sha256"], row["before_bytes"]),
         "complete740-original-source-preimage-required")
    forward = restored
    for fragment in row["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        need(forward.count(before) == 1, "unique740-forward-source-site-required")
        forward = forward.replace(before, after, 1)
    need(forward == payload, "exact740-source-inverse-forward-roundtrip-required")
    return restored


# Retain the unchanged inverse above as the uncached authority.  Only complete,
# bounded immutable arithmetic keys/results may enter this separately finite
# cache; every caller still reads/adopts its document and source context afresh.
from functools import lru_cache as _inverse_lru743

_inverse_uncached743 = _inverse
_INVERSE_FUNCTION743 = _inverse
_INVERSE_CODE743 = _inverse.__code__
_INVERSE_SHA743, _INVERSE_SHA_CODE743 = sha, sha.__code__
_INVERSE_NEED743, _INVERSE_NEED_CODE743 = need, need.__code__
_INVERSE_HASHLIB743, _INVERSE_DIGEST743 = hashlib, hashlib.sha256
_INVERSE_GETATTR743 = getattr
_INVERSE_GLOBALS743 = globals()
_INVERSE_BUILTINS743 = _inverse.__builtins__
_INVERSE_BUILTIN_VALUES743 = tuple(
    (name, _INVERSE_BUILTINS743[name]) for name in
    ("len", "reversed", "ValueError", "type", "bytes", "str", "dict", "list", "tuple", "int"))
_INVERSE_BUILTIN_DIGEST743 = (
    type(_INVERSE_DIGEST743) is type(len)
    and getattr(_INVERSE_DIGEST743, "__module__", None) == "_hashlib"
    and getattr(_INVERSE_DIGEST743, "__name__", None) == "openssl_sha256")
MAX_INVERSE_CACHE_PAYLOAD743 = 512 * 1024
MAX_INVERSE_CACHE_KEY_CHARS743 = 128 * 1024


def _inverse_key743(payload, row):
    """Snapshot exact scalar data before hashing; foreign/large keys run uncached."""
    if (type(payload) is not bytes or not 0 < len(payload) <= MAX_INVERSE_CACHE_PAYLOAD743
            or type(row) is not dict or len(row) != 5):
        return None
    for name in row:
        if type(name) is not str:
            return None
    before_sha, after_sha = row.get("before_sha256"), row.get("after_sha256")
    before_bytes, after_bytes = row.get("before_bytes"), row.get("after_bytes")
    if (type(before_sha) is not str or len(before_sha) != 64
            or type(after_sha) is not str or len(after_sha) != 64
            or type(before_bytes) is not int or not 0 < before_bytes <= MAX_INVERSE_CACHE_PAYLOAD743
            or type(after_bytes) is not int or not 0 < after_bytes <= MAX_INVERSE_CACHE_PAYLOAD743):
        return None
    fragments = row.get("fragments")
    if type(fragments) is not list or not 0 < len(fragments) <= 16:
        return None
    frozen, characters = [], len(before_sha) + len(after_sha)
    for fragment in fragments:
        if type(fragment) is not dict or len(fragment) != 4:
            return None
        for name in fragment:
            if type(name) is not str:
                return None
        before, after = fragment.get("before"), fragment.get("after")
        before_hash, after_hash = fragment.get("before_fragment_sha256"), fragment.get("after_fragment_sha256")
        if (type(before) is not str or not before or type(after) is not str or not after
                or type(before_hash) is not str or len(before_hash) != 64
                or type(after_hash) is not str or len(after_hash) != 64):
            return None
        characters += len(before) + len(after) + len(before_hash) + len(after_hash)
        if characters > MAX_INVERSE_CACHE_KEY_CHARS743:
            return None
        frozen.append((before, after, before_hash, after_hash))
    return (payload, before_sha, after_sha, before_bytes, after_bytes, tuple(frozen))


@_inverse_lru743(maxsize=16)
def _inverse_cached743(key):
    """Successful immutable bytes only; exceptions are never retained.

    No row/list, path/root, document, descriptor, admission result or executable
    enters the key.  Concurrent misses may repeat the original pure arithmetic;
    this is not a synchronization guarantee for hostile concurrent monkeypatches.
    """
    payload, before_sha, after_sha, before_bytes, after_bytes, fragments = key
    row = {"before_sha256": before_sha, "after_sha256": after_sha,
           "before_bytes": before_bytes, "after_bytes": after_bytes,
           "fragments": [{"before": before, "after": after,
                          "before_fragment_sha256": before_hash, "after_fragment_sha256": after_hash}
                         for before, after, before_hash, after_hash in fragments]}
    restored = _inverse_uncached743(payload, row)
    if type(restored) is not bytes or not 0 < len(restored) <= MAX_INVERSE_CACHE_PAYLOAD743:
        raise ValueError("bounded743-immutable-inverse-cache-result-required")
    return restored


_INVERSE_KEY_FUNCTION743, _INVERSE_KEY_CODE743 = _inverse_key743, _inverse_key743.__code__
_INVERSE_CACHE_FUNCTION743 = _inverse_cached743
_INVERSE_CACHE_BODY743 = _inverse_cached743.__wrapped__
_INVERSE_CACHE_CODE743 = _INVERSE_CACHE_BODY743.__code__


def _inverse_context743():
    """Even warm hits must fall back when original helper/crypto/builtins drift."""
    if (not _INVERSE_BUILTIN_DIGEST743
            or _inverse_uncached743 is not _INVERSE_FUNCTION743
            or _INVERSE_GETATTR743(_inverse_uncached743, "__code__", None) is not _INVERSE_CODE743
            or sha is not _INVERSE_SHA743 or _INVERSE_GETATTR743(sha, "__code__", None) is not _INVERSE_SHA_CODE743
            or need is not _INVERSE_NEED743 or _INVERSE_GETATTR743(need, "__code__", None) is not _INVERSE_NEED_CODE743
            or hashlib is not _INVERSE_HASHLIB743
            or _INVERSE_GETATTR743(hashlib, "sha256", None) is not _INVERSE_DIGEST743
            or _inverse_key743 is not _INVERSE_KEY_FUNCTION743
            or _INVERSE_GETATTR743(_inverse_key743, "__code__", None) is not _INVERSE_KEY_CODE743
            or _inverse_cached743 is not _INVERSE_CACHE_FUNCTION743
            or _INVERSE_GETATTR743(_inverse_cached743, "__wrapped__", None) is not _INVERSE_CACHE_BODY743
            or _INVERSE_GETATTR743(_INVERSE_CACHE_BODY743, "__code__", None) is not _INVERSE_CACHE_CODE743
            or MAX_INVERSE_CACHE_PAYLOAD743 != 512 * 1024
            or MAX_INVERSE_CACHE_KEY_CHARS743 != 128 * 1024):
        return False
    for name, reference in _INVERSE_BUILTIN_VALUES743:
        if _INVERSE_GLOBALS743.get(name, _INVERSE_BUILTINS743.get(name)) is not reference:
            return False
    return True


def _inverse_memo743(payload, row):
    if not _inverse_context743():
        return _inverse_uncached743(payload, row)
    key = _inverse_key743(payload, row)
    return _inverse_uncached743(payload, row) if key is None else _inverse_cached743(key)


_inverse = _inverse_memo743


def current_source_before_domain740(relative, payload, root=ROOT):
    """Qualify exact outer recovery first; unlisted data earns no303 acceptance."""
    _identity(relative, payload)
    from ci_source_recovery740_742 import current_source_before_recovery
    payload = current_source_before_recovery(relative, payload, root)
    if relative not in MODIFIED:
        return payload
    return _inverse(payload, _document(root)["bindings"][relative])


def peel_domain740_for_history(relative, payload, root=ROOT):
    """After-only outer then740 code inverse; OLD data keeps its next owner pin."""
    _identity(relative, payload)
    from ci_source_recovery740_742 import peel_recovery_for_history
    payload = peel_recovery_for_history(relative, payload, root)
    if relative not in MODIFIED:
        return payload
    row = _document(root)["bindings"][relative]
    if (sha(payload), len(payload)) == (row["after_sha256"], row["after_bytes"]):
        return _inverse(payload, row)
    return payload


def bridge_after_qualified_current_ingress(relative, payload, root=ROOT):
    """Broader671 calls this AFTER strict listed admission; not a named view."""
    _identity(relative, payload)
    if relative != BRIDGE:
        return payload
    return _inverse(payload, _document(root)["bridge_binding"])


def peel_bridge740_for_history(relative, payload, root=ROOT):
    """One exact718 bridge data inverse only, never enrollment or execution."""
    _identity(relative, payload)
    if relative != BRIDGE:
        return payload
    row = _document(root)["bridge_binding"]
    if (sha(payload), len(payload)) == (row["after_sha256"], row["after_bytes"]):
        return _inverse(payload, row)
    return payload


def dependency_inputs():
    """Separate finite code-stage custody; NEVER current303 registration."""
    return MODIFIED | {OWNER, CONTROL, SPEC, BRIDGE, CURRENT303_SPEC}


def validate_current_sources(root=ROOT):
    """Fresh finite source/descriptor custody only; inverse code is not executed."""
    document = _document(root)
    identities = {}
    raw, identities[CURRENT303_SPEC] = _ordinary(root, CURRENT303_SPEC, MAX_SPEC)
    need((sha(raw), len(raw)) == (CURRENT303_SPEC_SHA256, 518906), "unchanged740-current303-manifest-required")
    for relative, row in document["bindings"].items():
        raw, identities[relative] = _ordinary(root, relative)
        _inverse(raw, row)
    raw, identities[BRIDGE] = _ordinary(root, BRIDGE)
    _inverse(raw, document["bridge_binding"])
    raw, identities[OWNER] = _ordinary(root, OWNER)
    needle = ('SPEC_SHA256 = "' + SPEC_SHA256 + '"\n').encode()
    template = ('SPEC_SHA256 = "' + '0' * 64 + '"\n').encode()
    own = document["own_guard"]
    need(len(raw) == own["bytes"] and raw.count(needle) == 1
         and sha(raw.replace(needle, template, 1)) == own["template_sha256"],
         "exact740-own-helper-singleton-template-required")
    raw, identities[CONTROL] = _ordinary(root, CONTROL)
    control = document["control"]
    need((sha(raw), len(raw)) == (control["sha256"], control["bytes"]), "exact740-new-control-source-required")
    raw, identities[SPEC] = _ordinary(root, SPEC, MAX_SPEC)
    need(sha(raw) == SPEC_SHA256, "exact740-manifest-held-through-validation-required")
    for relative, identity in identities.items():
        maximum = MAX_SPEC if relative in {SPEC, CURRENT303_SPEC} else MAX_SOURCE
        need(_ordinary(root, relative, maximum)[1] == identity, "finite740-source-custody-changed-during-validation")
    return True
