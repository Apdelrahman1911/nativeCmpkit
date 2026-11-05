# SPDX-License-Identifier: Apache-2.0
"""Exactly the reviewed final668 CI outer inverse, not native/result reuse proof.

No restored module, workflow job, network, subprocess, Git operation or historical
fixture is executed. Current ingress is strict; history peels only exact endpoints.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
SOURCE_RELATIVE = "scripts/ci/ci668_outer_source_projection.py"
SPEC_RELATIVE = "scripts/ci/fixtures/ci668-outer-source-inverse.json"
SPEC_PATH = Path(__file__).parent / "fixtures/ci668-outer-source-inverse.json"
SPEC_SHA256 = "bbfdb2454182ce8c1fc90e793c3552e49f317b35437b61fcd3e8743b86f9d86e"
ORIGINAL671_SPEC = "scripts/ci/fixtures/tooling-recovery671-source-inverse.json"
ORIGINAL671_SPEC_SHA256 = "9def6c416e199237600bdcdc2a16a3fd22dc2158796e1116f999b8681c96a110"
ORIGINAL671_GUARD = "scripts/ci/tooling_recovery671_source_projection.py"
ORIGINAL671_GUARD_SHA256 = "40467cf06076eb57ac68e64d9db147245051d8f020e6c1c6117b68640e09b057"
ORIGINAL671_GUARD_BYTES = 33105
ORIGINAL671_PACKET_SHA256 = "bb66a323951a226ab76f1d2c5aeeaf4d3888e5214b7fdd86728c9d79625f811b"
FUTURE_CI_PACKET_SHA256 = "bcd9aa9bda2cf935ac63e70f1e5ddd020ead10fae5cd5bdbbb435c18fcca1cb8"
WORKFLOW = ".github/workflows/gradle.yml"
WORKFLOW_BEFORE_SHA256 = "46de0540c5e252a1bb9016e96758e79de2f0e728ca4ba2a746b709b88652106b"
WORKFLOW_AFTER_SHA256 = "47878318993f0ca28899f782b1ba8780fe1c6e210e187ef097acfaa4fb1d19f8"
BOUND_FRAGMENT_COUNTS = {'.github/workflows/gradle.yml': 5, 'scripts/ci/test_android_io_remote_routing.py': 1, 'scripts/ci/test_android_io_remote_routing_source_projection.py': 1, 'scripts/ci/test_ios_ui_split664_native_routing.py': 1, 'scripts/ci/test_shared_tooling_recovery671.py': 1, 'scripts/ci/tooling_recovery671_source_projection.py': 7}
BOUND_PATHS = frozenset(BOUND_FRAGMENT_COUNTS)
NEW_CONTROL = "scripts/ci/test_ci668_outer_source_projection.py"
SEALED_CI_LEAVES = {'docs/testing/offline-tooling-provenance.md': 'f4386a3d0e4ba165abf293b121c056f7f431c1e4fe541d1c0f1e4678cd07780b', 'docs/testing/offline-tooling-reuse.md': 'cf7b74bb55babc6512aa7102a1562f66621fa40c832f2413f0b5e184c3a9c717', 'scripts/ci/offline_tooling_provenance.py': 'b9f4cfb7465d390bff39141e2ec399c166dc4b9df24bf655eff92f5c50a550a3', 'scripts/ci/offline_tooling_reuse.py': '9bd6b6d8daa7d8e6270fc874c28a8b7692f815334d4d77130fb3d81c35d7897b', 'scripts/ci/test_offline_tooling_provenance.py': 'c0b7c6b869860268d461f9d25db6a2c26041a25c9d3f240d0c231673772b8cef', 'scripts/ci/test_offline_tooling_reuse.py': '6012ff90b004ec2631c17c05f65e116c88766d3089113a5ad2fee7a6e61ff94e', 'scripts/ci/test_offline_tooling_workflow.py': '2e80e09f8e67add098e1f4f3407c41230ad5ae3f92c97efa214faf93bffa0484'}
ADDED_PATHS = frozenset(SEALED_CI_LEAVES) | {NEW_CONTROL}
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_SCOPE = "Exact668 final five workflow spans, seven671 ingress hooks and four owning fixture ancestor comparisons only; no native/library/consumer/results reuse or issue acceptance"


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate exact CI668 manifest field")
        result[key] = value
    return result


def _ordinary(root, relative, limit):
    from ios_popover_anchor_plan import _ordinary_bytes
    path = root / relative
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= limit:
        raise ValueError("One ordinary bounded exact CI668 source input is required")
    raw = _ordinary_bytes(root, relative)[0]
    if not 0 < len(raw) <= limit:
        raise ValueError("One complete bounded exact CI668 source input is required")
    return raw


def _parse(raw):
    try:
        return json.loads(raw, object_pairs_hook=_unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite CI668 manifest")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("One complete exact CI668 manifest JSON is required") from None


def _original671_inputs():
    raw = _ordinary(ROOT, ORIGINAL671_SPEC, MAX_SPEC_BYTES)
    if sha(raw) != ORIGINAL671_SPEC_SHA256:
        raise ValueError("The original671 sealed manifest changed")
    document = _parse(raw)
    return ({name: row["after_sha256"] for name, row in document["bindings"].items()} |
            document["added_inputs"] | document["unchanged_inputs"] |
            {ORIGINAL671_SPEC: ORIGINAL671_SPEC_SHA256, ORIGINAL671_GUARD: ORIGINAL671_GUARD_SHA256})


def _shape(document):
    if (type(document) is not dict or set(document) != {
            "schema_version", "scope", "original671_packet_sha256", "future_ci_packet_sha256",
            "bindings", "added_inputs", "unchanged_inputs", "own_guard"} or
            type(document["schema_version"]) is not int or document["schema_version"] != 1 or
            document["scope"] != _SCOPE or document["original671_packet_sha256"] != ORIGINAL671_PACKET_SHA256 or
            document["future_ci_packet_sha256"] != FUTURE_CI_PACKET_SHA256 or
            type(document["bindings"]) is not dict or set(document["bindings"]) != BOUND_PATHS or
            type(document["added_inputs"]) is not dict or set(document["added_inputs"]) != ADDED_PATHS or
            type(document["unchanged_inputs"]) is not dict or
            type(document["own_guard"]) is not dict or set(document["own_guard"]) != {"template_sha256", "bytes"} or
            type(document["own_guard"]["bytes"]) is not int or not 0 < document["own_guard"]["bytes"] <= MAX_SOURCE_BYTES or
            type(document["own_guard"]["template_sha256"]) is not str or _DIGEST.fullmatch(document["own_guard"]["template_sha256"]) is None):
        raise ValueError("The exact finite final CI668 schema is required")
    original = _original671_inputs()
    if len(original) != 165 or document["unchanged_inputs"] != {name: digest for name, digest in original.items() if name not in BOUND_PATHS}:
        raise ValueError("All159 unchanged original671 inputs and manifests must remain sealed")
    if any(document["added_inputs"][name] != digest for name, digest in SEALED_CI_LEAVES.items()):
        raise ValueError("Exactly the seven original reviewed CI668 source leaves are required")
    if any(type(digest) is not str or _DIGEST.fullmatch(digest) is None for digest in document["added_inputs"].values()):
        raise ValueError("Exact finite new CI668 input hashes are required")
    for relative, row in document["bindings"].items():
        if (type(row) is not dict or set(row) != {"before_sha256", "after_sha256", "before_bytes", "after_bytes", "fragments"} or
                any(type(row[key]) is not str or _DIGEST.fullmatch(row[key]) is None for key in ("before_sha256", "after_sha256")) or
                any(type(row[key]) is not int or not 0 < row[key] <= MAX_SOURCE_BYTES for key in ("before_bytes", "after_bytes")) or
                type(row["fragments"]) is not list or len(row["fragments"]) != BOUND_FRAGMENT_COUNTS[relative] or
                row["before_sha256"] != original[relative]):
            raise ValueError("Exactly five workflow, seven original671 and four owning fixture hook fragments are required")
        if (relative == WORKFLOW and (row["before_sha256"] != WORKFLOW_BEFORE_SHA256 or row["before_bytes"] != 70598 or
                                     row["after_sha256"] != WORKFLOW_AFTER_SHA256 or row["after_bytes"] != 87031) or
                relative == ORIGINAL671_GUARD and row["before_bytes"] != ORIGINAL671_GUARD_BYTES):
            raise ValueError("Only the sealed final workflow and original671 singleton endpoints are defined")
        for fragment in row["fragments"]:
            if (type(fragment) is not dict or set(fragment) != {"before", "after", "before_fragment_sha256", "after_fragment_sha256", "obligation"} or
                    any(type(fragment[key]) is not str or not fragment[key] for key in fragment) or fragment["before"] == fragment["after"] or
                    any(_DIGEST.fullmatch(fragment[key]) is None for key in ("before_fragment_sha256", "after_fragment_sha256")) or
                    any(len(fragment[key].encode()) > MAX_SOURCE_BYTES for key in ("before", "after"))):
                raise ValueError("Exact unique bounded CI668 fragment identities are required")
    return document


def _document():
    raw = _ordinary(SPEC_PATH.parent, SPEC_PATH.name, MAX_SPEC_BYTES)
    if sha(raw) != SPEC_SHA256:
        raise ValueError("The exact final CI668 manifest changed")
    return _shape(_parse(raw))


def _identity(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact CI668 relative identity and ordinary source bytes are required")


def source_before_ci668(relative, payload):
    """Complete reviewed inverse or its one exact declared ancestor, not admission."""
    _identity(relative, payload)
    import cookie_ci668_outer_source_projection as cookie_outer
    current_raw = payload
    payload = cookie_outer.peel_cookie_outer_for_history(relative, current_raw)
    import producer698_source_fixture_recovery as producer698
    producer = producer698.peel_producer698_for_history(relative, current_raw)
    if payload == current_raw:
        payload = producer  # Independent producer ancestry, not a Cookie inverse readmission.
    import macos_share_ci668_composition as joint
    named = joint.peel_for_history(relative, current_raw, joint.CI_VIEW)
    if named != current_raw:
        payload = named  # The exact named view, never restored-as-current.
    row = _document()["bindings"].get(relative)
    if row is None:
        return payload  # Unlisted bytes are not certified, guessed, reconstructed or executed.
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Complete bounded final CI668 source bytes are required")
    observed = sha(payload)
    if observed == row["before_sha256"] and len(payload) == row["before_bytes"]:
        return payload
    if observed != row["after_sha256"] or len(payload) != row["after_bytes"]:
        raise ValueError("CI668 source is neither its complete reviewed endpoint nor its one exact ancestor")
    restored = payload
    for fragment in reversed(row["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (sha(before) != fragment["before_fragment_sha256"] or sha(after) != fragment["after_fragment_sha256"] or restored.count(after) != 1):
            raise ValueError("Exact unique final CI668 inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if sha(restored) != row["before_sha256"] or len(restored) != row["before_bytes"]:
        raise ValueError("CI668 inverse did not restore its exact complete sealed predecessor")
    forward = restored
    for fragment in row["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique final CI668 forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Complete final CI668 inverse/forward custody differs")
    return restored


def _own_guard_payload(payload, document):
    needle = ('SPEC_SHA256 = "' + SPEC_SHA256 + '"\n').encode()
    template = ('SPEC_SHA256 = "' + '0' * 64 + '"\n').encode()
    if (len(payload) != document["own_guard"]["bytes"] or payload.count(needle) != 1 or
            sha(payload.replace(needle, template, 1)) != document["own_guard"]["template_sha256"]):
        raise ValueError("Current CI668 own guard differs from its exact singleton template")
    return sha(payload)


def current_source_before_ci668(relative, payload):
    """The sole strict final raw ingress; old, partial, displaced and drift refuse."""
    _identity(relative, payload)
    import cookie_ci668_outer_source_projection as cookie_outer
    current_raw = payload
    payload = cookie_outer.current_source_before_cookie_outer(relative, current_raw)
    import producer698_source_fixture_recovery as producer698
    producer = producer698.current_source_before_producer698(relative, current_raw)
    if payload == current_raw:
        payload = producer  # Exactly one producer current ingress on the original raw bytes.
    import macos_share_ci668_composition as joint
    named = joint.current_source_in_view(relative, current_raw, joint.CI_VIEW)
    if named != current_raw:
        payload = named  # Independently qualify original raw, not the Cookie inverse.
    document = _document()
    if relative == SOURCE_RELATIVE:
        _own_guard_payload(payload, document)
    else:
        row = document["bindings"].get(relative)
        digest = (row["after_sha256"] if row is not None else
                  (document["added_inputs"] | document["unchanged_inputs"] | {SPEC_RELATIVE: SPEC_SHA256}).get(relative))
        if digest is not None and (sha(payload) != digest or row is not None and len(payload) != row["after_bytes"]):
            raise ValueError("An old or unknown image cannot replace exact current final CI668 source")
    return source_before_ci668(relative, payload)


def peel_ci668_for_history(relative, payload):
    """Only exact complete final endpoints peel; all other bytes face older pins."""
    _identity(relative, payload)
    import cookie_ci668_outer_source_projection as cookie_outer
    current_raw = payload
    payload = cookie_outer.peel_cookie_outer_for_history(relative, current_raw)
    import producer698_source_fixture_recovery as producer698
    producer = producer698.peel_producer698_for_history(relative, current_raw)
    if payload == current_raw:
        payload = producer  # Independent producer ancestry, not a Cookie inverse readmission.
    import macos_share_ci668_composition as joint
    named = joint.peel_for_history(relative, current_raw, joint.CI_VIEW)
    if named != current_raw:
        payload = named  # The exact named view, never restored-as-current.
    row = _document()["bindings"].get(relative)
    if row is not None and sha(payload) == row["after_sha256"] and len(payload) == row["after_bytes"]:
        return source_before_ci668(relative, payload)
    return payload  # No generic search, raw-current certificate or repeated strict admission.


def _validate_own_guard(root, document):
    import cookie_ci668_outer_source_projection as cookie_outer
    current_raw = _ordinary(root, SOURCE_RELATIVE, MAX_SOURCE_BYTES)
    payload = cookie_outer.current_source_before_cookie_outer(SOURCE_RELATIVE, current_raw, root)
    import producer698_source_fixture_recovery as producer698
    producer698.current_source_before_producer698(SOURCE_RELATIVE, current_raw)
    import macos_share_ci668_composition as joint
    named = joint.current_source_in_view(SOURCE_RELATIVE, current_raw, joint.CI_VIEW, root)
    if named != current_raw:
        payload = named
    _own_guard_payload(payload, document)
    return sha(current_raw)


def _expected(document):
    return ({name: row["after_sha256"] for name, row in document["bindings"].items()} |
            document["added_inputs"] | document["unchanged_inputs"] | {SPEC_RELATIVE: SPEC_SHA256})


def current_input_hashes():
    """Actual joint279 custody; original current207 and producer190 stay historical."""
    validate_current_sources(ROOT)
    import macos_share_ci668_composition as joint
    return joint.current_input_hashes(ROOT)


def sealed_ci668_175_hashes():
    """The immutable original raw175 snapshot, never relabeled latest current."""
    from producer698_source_fixture_recovery import original_ci668_input_hashes
    return original_ci668_input_hashes()


def _source_before_ci668_operation(relative, payload, document, operation):
    """Complete reviewed inverse or its one exact declared ancestor, not admission."""
    _identity(relative, payload)
    import cookie_ci668_outer_source_projection as cookie_outer
    current_raw = payload
    payload = cookie_outer.peel_cookie_outer_for_history(relative, current_raw)
    import producer698_source_fixture_recovery as producer698
    producer = operation._producer_history(relative, current_raw)
    if payload == current_raw:
        payload = producer  # Independent producer ancestry, not a Cookie inverse readmission.
    import macos_share_ci668_composition as joint
    named = operation._history(relative, current_raw, joint.CI_VIEW)
    if named != current_raw:
        payload = named  # The exact named view, never restored-as-current.
    row = document["bindings"].get(relative)
    if row is None:
        return payload  # Unlisted bytes are not certified, guessed, reconstructed or executed.
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Complete bounded final CI668 source bytes are required")
    observed = sha(payload)
    if observed == row["before_sha256"] and len(payload) == row["before_bytes"]:
        return payload
    if observed != row["after_sha256"] or len(payload) != row["after_bytes"]:
        raise ValueError("CI668 source is neither its complete reviewed endpoint nor its one exact ancestor")
    restored = payload
    for fragment in reversed(row["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (sha(before) != fragment["before_fragment_sha256"] or sha(after) != fragment["after_fragment_sha256"] or restored.count(after) != 1):
            raise ValueError("Exact unique final CI668 inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if sha(restored) != row["before_sha256"] or len(restored) != row["before_bytes"]:
        raise ValueError("CI668 inverse did not restore its exact complete sealed predecessor")
    forward = restored
    for fragment in row["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique final CI668 forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Complete final CI668 inverse/forward custody differs")
    return restored



def _validate_current_sources_operation(root: Path, document, operation):
    """Strict finite ordinary current bytes only; no source/test/native execution."""
    import cookie_ci668_outer_source_projection as cookie_outer
    cookie_outer.validate_current_sources(root)
    import macos_share_ci668_composition as joint
    import producer698_source_fixture_recovery as producer698
    operation._validate_producer(root)  # Whole raw279, then original645/190 guard/rows.
    _validate_own_guard(root, document)
    for relative, digest in _expected(document).items():
        raw = _ordinary(root, relative, MAX_SOURCE_BYTES)
        comparison = cookie_outer.peel_cookie_outer_for_history(relative, raw, root)
        named = operation._current(relative, raw, joint.CI_VIEW, root)
        if named != raw:
            comparison = named  # Owning CI fixture8e is historical, raw7d stays current.
        if sha(comparison) != digest:
            raise ValueError("Current final CI668 input differs from its complete reviewed raw image: " + relative)
    for relative in BOUND_PATHS:
        operation._ci_history(relative, _ordinary(root, relative, MAX_SOURCE_BYTES))
    return True



def validate_current_sources(root: Path):
    """Fresh owning operation; strict current rows, original histories and custody."""
    import macos_share_ci668_composition as joint
    with joint._source_projection_operation(root) as operation:
        return operation._validate_ci(root)

def fixture_inputs():
    """Actual joint279 source union; original finite207 and producer190 are historical, not a selector."""
    import macos_share_ci668_composition as joint
    return joint.fixture_inputs(ROOT)
