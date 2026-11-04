# SPDX-License-Identifier: Apache-2.0
"""One newest Share630 CI ingress, then unchanged exact UI/image/Calendar history.

Only complete reviewed inverse fragments are source operands. No reconstructed
Python, native controller, compiler or host query is executed by this layer.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
SPEC_RELATIVE = "scripts/ci/fixtures/macos-share-missing-ci-source-inverse.json"
SPEC_PATH = Path(__file__).parent / "fixtures/macos-share-missing-ci-source-inverse.json"
SPEC_SHA256 = "79fa2b0394b10026402bef72992385c38684f19b70414606ed1833b40e3178b9"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024
BOUND_PATHS = {
    ".github/workflows/gradle.yml", "scripts/ci/workflow_matrix.py", "scripts/ci/library_tests.py",
    "scripts/ci/ios_ui_related_source_projection.py", "scripts/ci/test_ios_ui_related_source_projection.py",
    "scripts/ci/test_calendar_share_selector_source_projection.py",
}
ADDED_PATHS = {
    "scripts/ci/macos_share_missing_ci.py", "scripts/ci/test_macos_share_missing_ci.py",
    "docs/testing/macos-share630-missing-ci.md",
}
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate missing Share630 manifest field")
        result[key] = value
    return result


def _document():
    from ios_popover_anchor_plan import _ordinary_bytes
    before = SPEC_PATH.lstat()
    if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= MAX_SPEC_BYTES):
        raise ValueError("One ordinary bounded missing Share630 manifest is required")
    raw = _ordinary_bytes(SPEC_PATH.parent, SPEC_PATH.name)[0]
    if not 0 < len(raw) <= MAX_SPEC_BYTES or sha(raw) != SPEC_SHA256:
        raise ValueError("The exact missing Share630 source manifest changed")
    try:
        document = json.loads(raw, object_pairs_hook=_unique,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite missing Share630 manifest")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("The complete missing Share630 manifest JSON is required") from None
    if (type(document) is not dict or set(document) != {"schema_version", "scope", "bindings", "added_inputs", "unchanged_inputs"} or
            type(document["schema_version"]) is not int or document["schema_version"] != 1 or
            document["scope"] != "Exact Share630 CI source/history custody only; no compiler/native acceptance" or
            type(document["bindings"]) is not dict or set(document["bindings"]) != BOUND_PATHS or
            type(document["added_inputs"]) is not dict or set(document["added_inputs"]) != ADDED_PATHS or
            type(document["unchanged_inputs"]) is not dict):
        raise ValueError("The exact finite missing Share630 manifest schema is required")
    for name, row in document["bindings"].items():
        if (type(row) is not dict or set(row) != {"before_sha256", "after_sha256", "before_bytes", "after_bytes", "fragments"} or
                any(type(row[key]) is not int or not 0 < row[key] <= MAX_SOURCE_BYTES for key in ("before_bytes", "after_bytes")) or
                any(type(row[key]) is not str or _DIGEST.fullmatch(row[key]) is None for key in ("before_sha256", "after_sha256")) or
                type(row["fragments"]) is not list or not 0 < len(row["fragments"]) <= 12):
            raise ValueError("Exact complete missing Share630 source bindings are required")
        for fragment in row["fragments"]:
            if (type(fragment) is not dict or set(fragment) != {
                    "before", "after", "before_fragment_sha256", "after_fragment_sha256", "obligation"} or
                    any(type(fragment[key]) is not str or not fragment[key] for key in fragment) or
                    any(_DIGEST.fullmatch(fragment[key]) is None for key in ("before_fragment_sha256", "after_fragment_sha256")) or
                    any(len(fragment[key].encode()) > MAX_SOURCE_BYTES for key in ("before", "after"))):
                raise ValueError("Exact finite missing Share630 fragment identities are required")
    for rows in (document["added_inputs"], document["unchanged_inputs"]):
        for name, digest in rows.items():
            if type(name) is not str or type(digest) is not str or _DIGEST.fullmatch(digest) is None:
                raise ValueError("Exact missing Share630 ordinary input hashes are required")
    return document


def _identity(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact missing Share630 relative identity and ordinary source bytes are required")


def source_before_share_missing_ci(relative, payload):
    """Complete exact inverse or its one exact preimage; never current admission."""
    _identity(relative, payload)
    from webview_content_policy_source_projection import peel_content_policy_for_history
    payload = peel_content_policy_for_history(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is None:
        return payload  # Unlisted bytes are not certified, guessed or executed.
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded complete missing Share630 source bytes are required")
    observed = sha(payload)
    if observed == binding["before_sha256"] and len(payload) == binding["before_bytes"]:
        return payload
    if observed != binding["after_sha256"] or len(payload) != binding["after_bytes"]:
        raise ValueError("Missing Share630 source is not its complete reviewed afterimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (sha(before) != fragment["before_fragment_sha256"] or sha(after) != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact finite unique missing Share630 inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if sha(restored) != binding["before_sha256"] or len(restored) != binding["before_bytes"]:
        raise ValueError("Missing Share630 inverse did not restore the complete exact prior source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact finite unique missing Share630 forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Missing Share630 complete inverse/forward source roundtrip differs")
    return restored


def current_source_before_share_missing_ci(relative, payload):
    """One raw newest ingress; old/partial/unknown images cannot be current."""
    _identity(relative, payload)
    from webview_content_policy_source_projection import current_source_before_content_policy
    payload = current_source_before_content_policy(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is not None and (sha(payload) != binding["after_sha256"] or len(payload) != binding["after_bytes"]):
        raise ValueError("An old or unknown image cannot replace exact current missing Share630 source")
    return source_before_share_missing_ci(relative, payload)


def peel_share_missing_ci_for_history(relative, payload):
    """Peel only the complete latest image; unknown bytes still need old strict pins."""
    _identity(relative, payload)
    from webview_content_policy_source_projection import peel_content_policy_for_history
    payload = peel_content_policy_for_history(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is not None and sha(payload) == binding["after_sha256"]:
        return source_before_share_missing_ci(relative, payload)
    return payload  # This is not current admission, including for exact prior bytes.


def validate_current_sources(root: Path):
    """Source custody only. Own guard/control pins are independent held-review inputs."""
    import webview_content_policy_source_projection as content_history
    content_history.validate_current_sources(root)
    document = _document()
    expected = ({name: row["after_sha256"] for name, row in document["bindings"].items()} |
                document["added_inputs"] | document["unchanged_inputs"] | {SPEC_RELATIVE: SPEC_SHA256})
    from ios_popover_anchor_plan import _ordinary_bytes
    for name, digest in expected.items():
        if sha(content_history.source_before_content_policy(name, _ordinary_bytes(root, name)[0])) != digest:
            raise ValueError("Current missing Share630 input differs from its complete owning image: " + name)
    return True


def fixture_inputs():
    """Only exact source fixtures required by the new owning validator; no execution."""
    document = _document()
    from webview_content_policy_source_projection import fixture_inputs as content_fixture_inputs
    return (set(document["bindings"]) | set(document["added_inputs"]) | set(document["unchanged_inputs"]) |
            {SPEC_RELATIVE, "scripts/ci/macos_share_missing_source_projection.py",
             "scripts/ci/test_macos_share_missing_source_projection.py"} | content_fixture_inputs())
