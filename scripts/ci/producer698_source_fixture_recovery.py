# SPDX-License-Identifier: Apache-2.0
"""One finite producer698 successor of sealed CI668/671, source custody only.

Never executes reconstructed source, changes an old pin, or certifies an old
image as current. Raw combined current hashes and the original raw175 snapshot
are intentionally distinct. This owner does not grant producer/cache/native,
consumer, compiler, issue, API, dependency or publication acceptance.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
SOURCE_RELATIVE = "scripts/ci/producer698_source_fixture_recovery.py"
SPEC_RELATIVE = "scripts/ci/fixtures/producer698-source-fixture-recovery.json"
SPEC_PATH = Path(__file__).parent / "fixtures/producer698-source-fixture-recovery.json"
SPEC_SHA256 = "64538883def9615a5c92060dcdc121404165b23278666c947e016b8eb67145d8"
ORIGINAL_CI668_SOURCE = "scripts/ci/ci668_outer_source_projection.py"
ORIGINAL_CI668_SOURCE_SHA256 = "57ea22a07713ee542a14f8d57338767f57e6cab4e2133a14b8096f9269e18337"
ORIGINAL_CI668_SPEC = "scripts/ci/fixtures/ci668-outer-source-inverse.json"
ORIGINAL_CI668_SPEC_SHA256 = "bbfdb2454182ce8c1fc90e793c3552e49f317b35437b61fcd3e8743b86f9d86e"
BASELINE = "97b3013e033ce64b6cc3d5dd3bf24bfbe405cb68"
SCOPE = "Exact producer698 nine-fixture, diagnostics and owning668 successor; source-only, not original aggregate/cache/native/issue acceptance"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")

BOUND_BEFORE = {'scripts/ci/ci668_outer_source_projection.py': {'bytes': 14044,
                                                 'fragments': 8,
                                                 'sha256': '57ea22a07713ee542a14f8d57338767f57e6cab4e2133a14b8096f9269e18337'},
 'scripts/ci/offline_tooling_reuse.py': {'bytes': 43632,
                                         'fragments': 1,
                                         'sha256': '9bd6b6d8daa7d8e6270fc874c28a8b7692f815334d4d77130fb3d81c35d7897b'},
 'scripts/ci/test_camera_home_baseline_source_projection.py': {'bytes': 9937,
                                                               'fragments': 1,
                                                               'sha256': '1afc43d19e87da2f8f66c98a75ea54c45e083b40dc804928c57dcab67738c405'},
 'scripts/ci/test_camera_ios_ownership_application_routing.py': {'bytes': 18477,
                                                                 'fragments': 2,
                                                                 'sha256': 'c18dffb16f6a5e4c51f601b4e17d2b7df26ea36a9fdd20ba9f08934beb007b63'},
 'scripts/ci/test_camera_tooling566_source_projection.py': {'bytes': 8309,
                                                            'fragments': 2,
                                                            'sha256': '31eca5b7b20aeb93e86ac33aa7bf0f86285046265b07c4a47c13f0dad91ae65d'},
 'scripts/ci/test_ci668_outer_source_projection.py': {'bytes': 7650,
                                                      'fragments': 2,
                                                      'sha256': '8e6d2e76f9de755f5d53bdc6a5a29aeb7161e9777ffcf7b5a0a163164889dfce'},
 'scripts/ci/test_ios_geometry_simulator_source_projection.py': {'bytes': 9925,
                                                                 'fragments': 1,
                                                                 'sha256': 'a13aa64cdc102fe1d755c5e4c95c7a5e4b24330f32109312927a688713b150d4'},
 'scripts/ci/test_ios_ui_split664_native_routing.py': {'bytes': 42720,
                                                       'fragments': 1,
                                                       'sha256': '58a6e93641d2f221fb09a74f2ae69fa28b2b2278624c96605782cd1bc89447a2'},
 'scripts/ci/test_library_sdk_context.py': {'bytes': 4151,
                                            'fragments': 3,
                                            'sha256': '9b5440cd7e52f7b41be1b2c088c2669a6ab6b08e2b4eedacca5e6dd7e8c44aec'},
 'scripts/ci/test_tooling656_fixture_recovery.py': {'bytes': 13493,
                                                    'fragments': 2,
                                                    'sha256': '8107f77ebc0e2c74aa4fcf6b55eed9b644160fb8bdfb8e19d8670dee4bd71e33'},
 'scripts/ci/test_webview_content_policy_source_projection.py': {'bytes': 21769,
                                                                 'fragments': 1,
                                                                 'sha256': '22d11f050ee284d1002fb1349425cd17e2638964790bf577b83c6844a5e0c3ef'},
 'scripts/ci/test_workflow_source.py': {'bytes': 10349,
                                        'fragments': 3,
                                        'sha256': '238b118e71e48690b8a8d3a49bc807516ead7ee7d8a059edd68c200ddc83f89b'}}
BOUND_PATHS = frozenset(BOUND_BEFORE)
ADDED_PATHS = frozenset({'scripts/ci/offline_tooling_failure_inventory.py',
 'scripts/ci/test_camera_producer698_fixture_recovery.py',
 'scripts/ci/test_offline_tooling_failure_inventory.py',
 'scripts/ci/test_producer698_batch_source_fixture_recovery.py',
 'scripts/ci/test_producer698_shared_fixture_recovery676.py'})


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _identity(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact producer698 relative identity and ordinary source bytes are required")
    path = Path(relative)
    if not relative or path.is_absolute() or ".." in path.parts or path.as_posix() != relative:
        raise ValueError("One canonical relative producer698 source identity is required")


def _ordinary(root, relative, limit):
    _identity(relative, b"source identity only")
    from ios_popover_anchor_plan import _ordinary_bytes
    info = (root / relative).lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= limit:
        raise ValueError("One ordinary bounded producer698 source input is required")
    raw = _ordinary_bytes(root, relative)[0]
    if not 0 < len(raw) <= limit:
        raise ValueError("One complete bounded producer698 source input is required")
    return raw


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate producer698 manifest field")
        result[key] = value
    return result


def _parse(raw):
    try:
        return json.loads(raw, object_pairs_hook=_unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite producer698 manifest")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("One complete producer698 manifest JSON is required") from None


def _original_ci668_inputs():
    raw = _ordinary(ROOT, ORIGINAL_CI668_SPEC, MAX_SPEC_BYTES)
    if sha(raw) != ORIGINAL_CI668_SPEC_SHA256:
        raise ValueError("The original CI668 manifest must remain immutable")
    original = _parse(raw)
    expected = ({name: row["after_sha256"] for name, row in original["bindings"].items()} |
                original["added_inputs"] | original["unchanged_inputs"] |
                {ORIGINAL_CI668_SPEC: ORIGINAL_CI668_SPEC_SHA256,
                 ORIGINAL_CI668_SOURCE: ORIGINAL_CI668_SOURCE_SHA256})
    if len(expected) != 175:
        raise ValueError("The named original CI668 raw175 snapshot changed")
    return expected


def _shape(document):
    if (type(document) is not dict or set(document) != {
            "schema_version", "scope", "source_before", "original_ci668_spec_sha256",
            "original_ci668_inputs", "bindings", "added_inputs", "own_guard"} or
            type(document["schema_version"]) is not int or document["schema_version"] != 1 or
            document["scope"] != SCOPE or document["source_before"] != BASELINE or
            document["original_ci668_spec_sha256"] != ORIGINAL_CI668_SPEC_SHA256 or
            document["original_ci668_inputs"] != _original_ci668_inputs() or
            type(document["bindings"]) is not dict or set(document["bindings"]) != BOUND_PATHS or
            type(document["added_inputs"]) is not dict or set(document["added_inputs"]) != ADDED_PATHS or
            type(document["own_guard"]) is not dict or set(document["own_guard"]) != {"template_sha256", "bytes"} or
            type(document["own_guard"]["bytes"]) is not int or not 0 < document["own_guard"]["bytes"] <= MAX_SOURCE_BYTES or
            type(document["own_guard"]["template_sha256"]) is not str or _DIGEST.fullmatch(document["own_guard"]["template_sha256"]) is None):
        raise ValueError("The exact finite producer698 successor schema is required")
    for name, row in document["bindings"].items():
        before = BOUND_BEFORE[name]
        if (type(row) is not dict or set(row) != {"before_sha256", "after_sha256", "before_bytes", "after_bytes", "fragments"} or
                any(type(row[key]) is not str or _DIGEST.fullmatch(row[key]) is None for key in ("before_sha256", "after_sha256")) or
                any(type(row[key]) is not int or not 0 < row[key] <= MAX_SOURCE_BYTES for key in ("before_bytes", "after_bytes")) or
                row["before_sha256"] != before["sha256"] or row["before_bytes"] != before["bytes"] or
                type(row["fragments"]) is not list or len(row["fragments"]) != before["fragments"]):
            raise ValueError("Only the exact twelve producer698 predecessor bindings are allowed")
        for fragment in row["fragments"]:
            if (type(fragment) is not dict or set(fragment) != {"before", "after", "before_fragment_sha256", "after_fragment_sha256", "obligation"} or
                    any(type(fragment[key]) is not str or not fragment[key] for key in fragment) or fragment["before"] == fragment["after"] or
                    any(_DIGEST.fullmatch(fragment[key]) is None for key in ("before_fragment_sha256", "after_fragment_sha256")) or
                    any(len(fragment[key].encode()) > MAX_SOURCE_BYTES for key in ("before", "after"))):
                raise ValueError("Exact finite unique producer698 fragment identities are required")
    if any(type(digest) is not str or _DIGEST.fullmatch(digest) is None for digest in document["added_inputs"].values()):
        raise ValueError("Exact producer698 new source hashes are required")
    if BOUND_PATHS & ADDED_PATHS or {SOURCE_RELATIVE, SPEC_RELATIVE} & (BOUND_PATHS | ADDED_PATHS):
        raise ValueError("The finite producer698 source domains cannot overlap")
    return document


def _document():
    raw = _ordinary(SPEC_PATH.parent, SPEC_PATH.name, MAX_SPEC_BYTES)
    if sha(raw) != SPEC_SHA256:
        raise ValueError("The exact producer698 successor manifest changed")
    return _shape(_parse(raw))


def _inverse(payload, row):
    if (not 0 < len(payload) <= MAX_SOURCE_BYTES or sha(payload) != row["after_sha256"] or
            len(payload) != row["after_bytes"]):
        raise ValueError("One exact complete producer698 afterimage is required")
    restored = payload
    for fragment in reversed(row["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (sha(before) != fragment["before_fragment_sha256"] or sha(after) != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique producer698 inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if sha(restored) != row["before_sha256"] or len(restored) != row["before_bytes"]:
        raise ValueError("Producer698 inverse must restore the complete named predecessor")
    forward = restored
    for fragment in row["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique producer698 forward sites are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("The complete producer698 source must round trip exactly")
    return restored


def source_before_producer698(relative, payload):
    """One exact complete ancestor view; never current admission or code execution."""
    _identity(relative, payload)
    import macos_share_ci668_composition as joint
    payload = joint.peel_for_history(relative, payload, joint.PRODUCER_VIEW)
    row = _document()["bindings"].get(relative)
    if row is None:
        return payload  # Unlisted data is not certified or globally peeled.
    if sha(payload) == row["before_sha256"] and len(payload) == row["before_bytes"]:
        return payload
    return _inverse(payload, row)


def peel_producer698_for_history(relative, payload):
    """Only exact declared current endpoints peel; unknown ancestors face older pins."""
    _identity(relative, payload)
    import macos_share_ci668_composition as joint
    payload = joint.peel_for_history(relative, payload, joint.PRODUCER_VIEW)
    row = _document()["bindings"].get(relative)
    if row is not None and sha(payload) == row["after_sha256"] and len(payload) == row["after_bytes"]:
        return _inverse(payload, row)
    return payload


def _own_guard_payload(payload, document):
    needle = ('SPEC_SHA256 = "' + SPEC_SHA256 + '"\n').encode()
    template = ('SPEC_SHA256 = "' + '0' * 64 + '"\n').encode()
    if (len(payload) != document["own_guard"]["bytes"] or payload.count(needle) != 1 or
            sha(payload.replace(needle, template, 1)) != document["own_guard"]["template_sha256"]):
        raise ValueError("The producer698 own guard differs from its exact singleton template")
    return sha(payload)


def _expected(document):
    return (document["original_ci668_inputs"] | {name: row["after_sha256"] for name, row in document["bindings"].items()} |
            document["added_inputs"] | {SPEC_RELATIVE: SPEC_SHA256})


def current_source_before_producer698(relative, payload):
    """One newest raw ingress; old, partial, duplicate, displaced and drift images refuse."""
    _identity(relative, payload)
    document = _document()
    import macos_share_ci668_composition as joint
    payload = joint.current_source_in_view(relative, payload, joint.PRODUCER_VIEW)
    if relative == SOURCE_RELATIVE:
        _own_guard_payload(payload, document)
        return payload
    row = document["bindings"].get(relative)
    digest = _expected(document).get(relative)
    if digest is not None and (sha(payload) != digest or row is not None and len(payload) != row["after_bytes"]):
        raise ValueError("An old or unknown image cannot replace exact current producer698 source")
    return _inverse(payload, row) if row is not None else payload


def validate_current_sources(root: Path):
    """Whole exact raw279, then distinctly named original190 guard/645 rows only."""
    import macos_share_ci668_composition as joint
    joint.validate_current_sources(root)
    document = _document()
    raw = _ordinary(root, SOURCE_RELATIVE, MAX_SOURCE_BYTES)
    _own_guard_payload(joint.current_source_in_view(SOURCE_RELATIVE, raw, joint.PRODUCER_VIEW, root), document)
    for name, digest in _expected(document).items():
        raw = _ordinary(root, name, MAX_SOURCE_BYTES)
        named = joint.current_source_in_view(name, raw, joint.PRODUCER_VIEW, root)
        if sha(named) != digest:
            raise ValueError("The named original producer190 input differs: " + name)
    for name, row in document["bindings"].items():
        raw = _ordinary(root, name, MAX_SOURCE_BYTES)
        _inverse(joint.current_source_in_view(name, raw, joint.PRODUCER_VIEW, root), row)
    return True


def current_input_hashes(root=None):
    """Actual combined raw279; original190 is a distinctly named sealed snapshot."""
    root = ROOT if root is None else root
    validate_current_sources(root)
    import macos_share_ci668_composition as joint
    return joint.current_input_hashes(root)


def original_producer190_input_hashes(root=None):
    """Named immutable producer676 raw190 bytes, never current279 identities."""
    root = ROOT if root is None else root
    import macos_share_ci668_composition as joint
    return joint.predecessor_input_hashes(joint.PRODUCER_VIEW, root)


def original_ci668_input_hashes():
    """Named immutable original raw175 bytes, not latest current identities."""
    return dict(_document()["original_ci668_inputs"])


def fixture_inputs():
    """Finite actual joint279 source custody only; never a native/cache selector."""
    import macos_share_ci668_composition as joint
    return joint.fixture_inputs(ROOT)
