# SPDX-License-Identifier: Apache-2.0
"""One latest WebView raw ingress, then exact Share/UI/image/Calendar ancestors.

This layer never runs reconstructed code, native selectors or host queries.
Unknown historical bytes are left to the next unchanged strict dated reader;
they are never admitted as current. Native inputs and all dated pins stay.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
SOURCE_RELATIVE = "scripts/ci/webview_content_policy_source_projection.py"
SPEC_RELATIVE = "scripts/ci/fixtures/webview-content-policy-routing-source-inverse.json"
SPEC_PATH = Path(__file__).parent / "fixtures/webview-content-policy-routing-source-inverse.json"
SPEC_SHA256 = "c44400087570740d3248704c2165c3222229f2c05ff1a2a3840dbda9aa04b916"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024
BOUND_PATHS = {
    ".github/workflows/gradle.yml", "scripts/ci/workflow_matrix.py", "scripts/ci/library_tests.py",
    "scripts/ci/ios_ui_application.py", "scripts/ci/android_device_tests.py",
    "scripts/ci/macos_share_missing_source_projection.py", "scripts/ci/test_macos_share_missing_source_projection.py",
    "scripts/ci/test_ios_ui_related_source_projection.py",
}
ADDED_PATHS = {
    "scripts/ci/webview_content_policy_native_focus.py",
    "calf-webview/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/ui/web/AndroidContentPolicyVerificationFilter.kt",
    "scripts/ci/test_webview_content_policy_native_focus.py",
    "scripts/ci/test_webview_content_policy_application_routing.py",
}
# This exact maintainer-instruction document is not executable source. Its
# historical bytes stay in the sealed original packet, never in a runtime guard
# or source-fixture prerequisite. No other documentation or source is exempted.
NONEXECUTABLE_MAINTAINER_INPUTS = frozenset({"AGENTS.md"})
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate content-policy manifest field")
        result[key] = value
    return result


def _document():
    from ios_popover_anchor_plan import _ordinary_bytes
    before = SPEC_PATH.lstat()
    if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= MAX_SPEC_BYTES):
        raise ValueError("One ordinary bounded content-policy manifest is required")
    raw = _ordinary_bytes(SPEC_PATH.parent, SPEC_PATH.name)[0]
    if not 0 < len(raw) <= MAX_SPEC_BYTES or sha(raw) != SPEC_SHA256:
        raise ValueError("The exact content-policy source manifest changed")
    try:
        document = json.loads(raw, object_pairs_hook=_unique,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite content-policy manifest")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("The complete content-policy manifest JSON is required") from None
    if (type(document) is not dict or set(document) != {"schema_version", "scope", "bindings", "added_inputs", "unchanged_inputs"} or
            type(document["schema_version"]) is not int or document["schema_version"] != 1 or
            document["scope"] != "Exact WebView source/history custody only; no compiler/native acceptance" or
            type(document["bindings"]) is not dict or set(document["bindings"]) != BOUND_PATHS or
            type(document["added_inputs"]) is not dict or set(document["added_inputs"]) != ADDED_PATHS or
            type(document["unchanged_inputs"]) is not dict):
        raise ValueError("The exact finite content-policy manifest schema is required")
    if any(NONEXECUTABLE_MAINTAINER_INPUTS & set(document[group])
           for group in ("bindings", "added_inputs", "unchanged_inputs")):
        raise ValueError("Maintainer instructions cannot be executable content-policy inputs")
    for name, row in document["bindings"].items():
        if (type(row) is not dict or set(row) != {"before_sha256", "after_sha256", "before_bytes", "after_bytes", "fragments"} or
                any(type(row[key]) is not int or not 0 < row[key] <= MAX_SOURCE_BYTES for key in ("before_bytes", "after_bytes")) or
                any(type(row[key]) is not str or _DIGEST.fullmatch(row[key]) is None for key in ("before_sha256", "after_sha256")) or
                type(row["fragments"]) is not list or not 0 < len(row["fragments"]) <= 12):
            raise ValueError("Exact complete content-policy source bindings are required")
        for fragment in row["fragments"]:
            if (type(fragment) is not dict or set(fragment) != {
                    "before", "after", "before_fragment_sha256", "after_fragment_sha256", "obligation"} or
                    any(type(fragment[key]) is not str or not fragment[key] for key in fragment) or
                    any(_DIGEST.fullmatch(fragment[key]) is None for key in ("before_fragment_sha256", "after_fragment_sha256")) or
                    any(len(fragment[key].encode()) > MAX_SOURCE_BYTES for key in ("before", "after"))):
                raise ValueError("Exact finite content-policy fragment identities are required")
    for rows in (document["added_inputs"], document["unchanged_inputs"]):
        for name, digest in rows.items():
            if type(name) is not str or type(digest) is not str or _DIGEST.fullmatch(digest) is None:
                raise ValueError("Exact content-policy ordinary input hashes are required")
    return document


def _identity(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact content-policy relative identity and ordinary source bytes are required")


def source_before_content_policy(relative, payload):
    """Complete exact inverse or its one exact preimage; never current admission."""
    _identity(relative, payload)
    from camera_ios_ownership_source_projection import peel_camera_ios_ownership_for_history
    payload = peel_camera_ios_ownership_for_history(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is None:
        return payload  # Unlisted bytes are not certified, guessed or executed.
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded complete content-policy source bytes are required")
    observed = sha(payload)
    if observed == binding["before_sha256"] and len(payload) == binding["before_bytes"]:
        return payload
    if observed != binding["after_sha256"] or len(payload) != binding["after_bytes"]:
        raise ValueError("Content-policy source is not its complete reviewed afterimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (sha(before) != fragment["before_fragment_sha256"] or sha(after) != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact finite unique content-policy inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if sha(restored) != binding["before_sha256"] or len(restored) != binding["before_bytes"]:
        raise ValueError("Content-policy inverse did not restore the complete exact prior source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact finite unique content-policy forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Content-policy complete inverse/forward source roundtrip differs")
    return restored


def current_source_before_content_policy(relative, payload):
    """One raw newest ingress; old/partial/unknown images cannot be current."""
    _identity(relative, payload)
    from camera_ios_ownership_source_projection import current_source_before_camera_ios_ownership
    payload = current_source_before_camera_ios_ownership(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is not None and (sha(payload) != binding["after_sha256"] or len(payload) != binding["after_bytes"]):
        raise ValueError("An old or unknown image cannot replace exact current content-policy source")
    return source_before_content_policy(relative, payload)


def peel_content_policy_for_history(relative, payload):
    """Peel only the complete latest image; unknown bytes still need old strict pins."""
    _identity(relative, payload)
    from camera_ios_ownership_source_projection import peel_camera_ios_ownership_for_history
    payload = peel_camera_ios_ownership_for_history(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is not None and sha(payload) == binding["after_sha256"]:
        return source_before_content_policy(relative, payload)
    return payload  # This is not current admission, including for exact prior bytes.


def read_current_source_for_history(path: Path, root: Path):
    if (type(path) is not type(ROOT) or type(root) is not type(ROOT) or not path.is_absolute() or
            not root.is_absolute() or root.absolute() != root.resolve(strict=True)):
        raise ValueError("An exact ordinary content-policy checkout and path are required")
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        raise ValueError("A foreign content-policy path is not a checkout input") from None
    if relative not in BOUND_PATHS or path != root / relative:
        raise ValueError("Only exact bound content-policy checkout paths may be read")
    from ios_popover_anchor_plan import _ordinary_bytes
    payload = _ordinary_bytes(root, relative)[0]
    import android_external328_source_projection as bridge
    return bridge.current_source_for_history(relative, payload)  # Its existing image/UI/Share hook admits WebView once.


def validate_current_sources(root: Path):
    """Source custody only. Own guard/control pins are independent held-review inputs."""
    import camera_ios_ownership_source_projection as camera_history
    camera_history.validate_current_sources(root)
    document = _document()
    expected = ({name: row["after_sha256"] for name, row in document["bindings"].items()} |
                document["added_inputs"] | document["unchanged_inputs"] | {SPEC_RELATIVE: SPEC_SHA256})
    from ios_popover_anchor_plan import _ordinary_bytes
    for name, digest in expected.items():
        if sha(camera_history.source_before_camera_ios_ownership(name, _ordinary_bytes(root, name)[0])) != digest:
            raise ValueError("Current content-policy input differs from its complete owning image: " + name)
    return True


def fixture_inputs():
    """Only this finite latest custody fixture union; never native/controller execution."""
    document = _document()
    from camera_ios_ownership_source_projection import fixture_inputs as camera_fixture_inputs
    return (set(document["bindings"]) | set(document["added_inputs"]) | set(document["unchanged_inputs"]) |
            {SPEC_RELATIVE, SOURCE_RELATIVE, "scripts/ci/test_webview_content_policy_source_projection.py"} | camera_fixture_inputs())
