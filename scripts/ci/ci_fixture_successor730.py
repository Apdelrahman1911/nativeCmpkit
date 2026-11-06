# SPDX-License-Identifier: Apache-2.0
"""One exact finite fixture successor; original740/742/current303 pins remain sealed.

No reconstructed source is imported, executed, written or enrolled as current.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = "scripts/ci/ci_fixture_successor730.py"
CONTROL = "scripts/ci/test_ci_fixture_successor730.py"
SPEC = "scripts/ci/fixtures/ci-fixture-successor730-source-inverse.json"
SPEC_SHA256 = "65e45763c96ee12d6317f35be7566038ea21b319661ccbb68b3c8e34013694f7"
MAX_SOURCE = 4 * 1024 * 1024
MAX_SPEC = 512 * 1024
SCOPE = 'Exact six failed-producer742 fixture successors and their two owning routing sources/control above unchanged740742/raw301/current303; copied dependencies are never raw enrollment; source-only'
ORIGINALS = {'scripts/ci/fixtures/macos-share-ci668-composition.json': {'bytes': 518906, 'sha256': '06d04d038b06c00e5aafb9b7defdf39ae069f3df305e4dbc84198bc8ed178a24'}, 'scripts/ci/fixtures/ci-source-domain740-source-inverse.json': {'bytes': 36274, 'sha256': '5b450daf9874a62a4b452b0d6502c3a77426e670ec6fd79a6b1ed3a3aecf6e52'}, 'scripts/ci/fixtures/ci-source-recovery740-742-source-inverse.json': {'bytes': 209811, 'sha256': '2be8ac55c4253f303f0e93bd120b4277f9dc3b22c0b7ec209a452aebb3f59835'}}
BEFORE = {'scripts/ci/ci_source_recovery740_742.py': {'bytes': 20636, 'sha256': 'b891572937299dbf8ca1eef6327774d5b9076a9968b4304fd57ec65732edaab7'}, 'scripts/ci/macos_share_ci668_composition.py': {'bytes': 80011, 'sha256': 'fad15c34dbe4b4b91a347527c24e86a56a332fd5217b75aaee9dcdfed8d8670f'}, 'scripts/ci/test_android_io_remote_routing.py': {'bytes': 33865, 'sha256': 'e0e25800d691e4fc859f22d16c1ca4362da2bae36f80b76a3e976ddf35628018'}, 'scripts/ci/test_android_io_remote_routing_source_projection.py': {'bytes': 30209, 'sha256': '1ebc15e15b782b54411351116aff9fa070fde4190576643b78d34fa97023fb47'}, 'scripts/ci/test_camera_ios_ownership_source_projection.py': {'bytes': 15167, 'sha256': 'ab5f18af2709ca9eab5ccaff30249dd85e120aadf1c24068a72e448d7bd9e263'}, 'scripts/ci/test_camera_tooling562_source_projection.py': {'bytes': 7953, 'sha256': '73a402c49c93a29db3bb5d8a46ad20423b84a803b333cbc0ec1f717c6db21dbd'}, 'scripts/ci/test_camera_tooling566_source_projection.py': {'bytes': 9498, 'sha256': 'b5fb8f12b24df974931c5cb8c850afee8f9a1c103fdd4b01f742290ad7f346db'}, 'scripts/ci/test_ci_source_domain740.py': {'bytes': 16648, 'sha256': '2e6184cd259db9acd0148815dfc7890199b985aa7319e0415737361f3d233e5f'}, 'scripts/ci/test_ci_source_recovery740_742.py': {'bytes': 28844, 'sha256': 'b995929d6e6538631ff0b176bba281940bc41e8924e29c114214c35e497465c6'}}
FRAGMENT_COUNTS = {'scripts/ci/ci_source_recovery740_742.py': 5, 'scripts/ci/macos_share_ci668_composition.py': 4, 'scripts/ci/test_android_io_remote_routing.py': 2, 'scripts/ci/test_android_io_remote_routing_source_projection.py': 2, 'scripts/ci/test_camera_ios_ownership_source_projection.py': 2, 'scripts/ci/test_camera_tooling562_source_projection.py': 3, 'scripts/ci/test_camera_tooling566_source_projection.py': 4, 'scripts/ci/test_ci_source_domain740.py': 8, 'scripts/ci/test_ci_source_recovery740_742.py': 4}
FIXTURES = frozenset(('scripts/ci/test_android_io_remote_routing.py', 'scripts/ci/test_android_io_remote_routing_source_projection.py', 'scripts/ci/test_camera_ios_ownership_source_projection.py', 'scripts/ci/test_camera_tooling562_source_projection.py', 'scripts/ci/test_camera_tooling566_source_projection.py', 'scripts/ci/test_ci_source_domain740.py'))
RAW_FIXTURES = frozenset(('scripts/ci/test_android_io_remote_routing.py', 'scripts/ci/test_android_io_remote_routing_source_projection.py', 'scripts/ci/test_camera_tooling566_source_projection.py'))
CAPACITY = 'scripts/ci/offline_tooling_reuse.py'
CAPACITY_SCOPE = 'One exact existing raw301 producer-capacity734 row, two fixed copied NEW734 sources and one owning joint inventory tuple before the sealed r1 nine bindings; no raw301/current303 enrollment or generic layer search'
CAPACITY_BEFORE = {'bytes': 60138, 'sha256': '3f19d0f4e93a66b8ba4928e88819fb35ac469709f9c26bfef87ee57fbd4778ca'}
ROUTING = 'scripts/ci/macos_share_ci668_composition.py'
ROUTING_BEFORE = {'bytes': 80498, 'sha256': '1cf7d1faea1f053b9873ec175549745d0914c81f1246cb23754bd4357527f84a'}
COPIED734 = {'scripts/ci/offline_tooling_ci_parallel734.py': {'bytes': 15740, 'sha256': 'ace02723bb3c11cf1dd9fadf835df6b1a02b78ede07b3760de773080acdfdd34'}, 'scripts/ci/test_offline_tooling_ci_parallel734.py': {'bytes': 23853, 'sha256': 'b279fd83c9fcdac642878287a54767943016a5ca0a2c62e90c996d9e95aefe0f'}}
REMOTE = 'scripts/ci/android_io_remote_routing_source_projection.py'
REMOTE_BEFORE = {'bytes': 15979, 'sha256': 'da51c70226edceedddbc6176c8244680f1fa6a3350e7adab56fe6faf982c0cc0'}
MODIFIED = frozenset(BEFORE) | {CAPACITY, REMOTE}


def need(value, reason):
    if not value:
        raise ValueError(reason)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _identity(relative, payload):
    from ci_source_domain740 import _identity as identity740
    identity740(relative, payload)  # Original exact-str/path/bytes/size grammar.


def _ordinary(root, relative, maximum=MAX_SOURCE):
    from macos_share_appkit_only_source_projection import ordinary_bytes
    return ordinary_bytes(root, relative, maximum)  # Actual descriptor bytes only.


def _endpoint(value):
    need(type(value) is dict and set(value) == {"bytes", "sha256"}
         and type(value["bytes"]) is int and 0 < value["bytes"] <= MAX_SOURCE
         and type(value["sha256"]) is str and len(value["sha256"]) == 64
         and all(char in "0123456789abcdef" for char in value["sha256"]),
         "exact-finite-fixture-successor-endpoint-required")


def _document(root=ROOT):
    from ci_source_domain740 import _binding
    from macos_share_ci668_composition import _json as json_bytes
    raw = _ordinary(root, SPEC, MAX_SPEC)[0]
    need(sha(raw) == SPEC_SHA256, "exact-six-fixture-successor-manifest-required")
    document = json_bytes(raw)
    need(type(document) is dict and set(document) == {
         "schema_version", "scope", "originals", "bindings", "control", "own_guard",
         "capacity_scope", "capacity_binding", "routing_binding", "remote_binding"}
         and type(document["schema_version"]) is int and document["schema_version"] == 1
         and document["scope"] == SCOPE and document["originals"] == ORIGINALS
         and document["capacity_scope"] == CAPACITY_SCOPE
         and type(document["bindings"]) is dict and set(document["bindings"]) == frozenset(BEFORE),
         "unchanged740742-current303-and-finite-fixture-successor-schema-required")
    for relative, row in document["bindings"].items():
        _identity(relative, b"finite-fixture-successor-identity")
        _binding(row, BEFORE[relative], FRAGMENT_COUNTS[relative])
    _binding(document["capacity_binding"], CAPACITY_BEFORE, 2)
    _binding(document["routing_binding"], ROUTING_BEFORE, 1)
    _binding(document["remote_binding"], REMOTE_BEFORE, 1)
    control, own = document["control"], document["own_guard"]
    need(type(control) is dict and set(control) == {"path", "bytes", "sha256"}
         and control["path"] == CONTROL,
         "exact-fixture-successor-control-source-required")
    _endpoint({key: control[key] for key in ("bytes", "sha256")})
    need(type(own) is dict and set(own) == {"bytes", "template_sha256"},
         "exact-fixture-successor-own-template-required")
    _endpoint({"bytes": own["bytes"], "sha256": own["template_sha256"]})
    return document


def _inverse(payload, row):
    from ci_source_domain740 import _inverse as inverse740
    return inverse740(payload, row)  # Unchanged strict inverse/forward arithmetic.


def current_source_before_fixture_successor(relative, payload, root=ROOT):
    """Exact current capacity/remote/tuple first, then sealed r1 rows; no OLD admission."""
    _identity(relative, payload)
    if relative not in MODIFIED:
        return payload  # Unlisted bytes gain no301/303 or other admission.
    document = _document(root)
    if relative == CAPACITY:
        return _inverse(payload, document["capacity_binding"])
    if relative == REMOTE:
        return _inverse(payload, document["remote_binding"])
    if relative == ROUTING:
        payload = _inverse(payload, document["routing_binding"])
    return _inverse(payload, document["bindings"][relative])


def peel_fixture_successor_for_history(relative, payload, root=ROOT):
    """Exact after-only capacity/remote/tuple and r1 history; no generic layer search."""
    _identity(relative, payload)
    if relative not in MODIFIED:
        return payload
    document = _document(root)
    if relative == CAPACITY:
        row = document["capacity_binding"]
    elif relative == REMOTE:
        row = document["remote_binding"]
    else:
        if relative == ROUTING:
            routing = document["routing_binding"]
            if (sha(payload), len(payload)) == (routing["after_sha256"], routing["after_bytes"]):
                payload = _inverse(payload, routing)
        row = document["bindings"][relative]
    if (sha(payload), len(payload)) == (row["after_sha256"], row["after_bytes"]):
        return _inverse(payload, row)
    return payload  # OLD/unknown remains history data; every next-owner pin stays exact.  # OLD/unknown stays data; every next-owner pin is retained.  # No generic layer search or reconstructed-as-current execution.


def dependency_inputs():
    """Finite copied custody only, never fixture_inputs/raw301/current303 growth."""
    return MODIFIED | set(ORIGINALS) | {OWNER, CONTROL, SPEC} | set(COPIED734)


def validate_current_sources(root=ROOT):
    """Before all shaping, exact ordinary custody; final failures preserve primary."""
    from macos_share_ci668_composition import _source_projection_custody
    with _source_projection_custody() as capture:
        raw = {relative: capture(root, relative, MAX_SPEC if relative in set(ORIGINALS) | {SPEC}
                                 else MAX_SOURCE) for relative in sorted(dependency_inputs())}
        document = _document(root)  # Fresh schema/refusals, never a cached admission.
        for relative, endpoint in ORIGINALS.items():
            need((sha(raw[relative]), len(raw[relative])) == (endpoint["sha256"], endpoint["bytes"]),
                 "unchanged-fixture-successor740742-current303-authority-required")
        for relative, row in document["bindings"].items():
            payload = _inverse(raw[relative], document["routing_binding"]) if relative == ROUTING else raw[relative]
            _inverse(payload, row)
        _inverse(raw[CAPACITY], document["capacity_binding"])
        _inverse(raw[REMOTE], document["remote_binding"])
        for relative, endpoint in COPIED734.items():
            need((sha(raw[relative]), len(raw[relative])) == (endpoint["sha256"], endpoint["bytes"]),
                 "exact-two-capacity734-copied-current-sources-required")
        own = document["own_guard"]
        needle = ('SPEC_SHA256 = "' + SPEC_SHA256 + '"\n').encode()
        template = ('SPEC_SHA256 = "' + '0' * 64 + '"\n').encode()
        need(len(raw[OWNER]) == own["bytes"] and raw[OWNER].count(needle) == 1
             and sha(raw[OWNER].replace(needle, template, 1)) == own["template_sha256"],
             "exact-fixture-successor-own-helper-singleton-template-required")
        control = document["control"]
        need((sha(raw[CONTROL]), len(raw[CONTROL])) == (control["sha256"], control["bytes"]),
             "exact-fixture-successor-control-current-source-required")
        need(sha(raw[SPEC]) == SPEC_SHA256, "fixture-successor-manifest-held-through-validation-required")
    return True
