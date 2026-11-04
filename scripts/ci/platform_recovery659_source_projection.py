# SPDX-License-Identifier: Apache-2.0
"""One finite659/657/660 raw ingress, then the immutable4697 Camera history.

Only exact reviewed source inverse/forward arithmetic is performed. No restored
source is executed and no compiler, native controller, network or host query is
run here. The original Camera/WebView manifests and all dated pins stay sealed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
SOURCE_RELATIVE = "scripts/ci/platform_recovery659_source_projection.py"
SPEC_RELATIVE = "scripts/ci/fixtures/platform-recovery659-source-inverse.json"
SPEC_PATH = Path(__file__).parent / "fixtures/platform-recovery659-source-inverse.json"
SPEC_SHA256 = "c9a56d4288e1d6a71914de27b0218d0877840136e9d24d448e2d192fcf7d90e9"
PREDECESSOR = "4697c3ec65427a12e53645ecffac5e2b52821dd5"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024
BOUND_PATHS = {
    "calf-camera-picker/src/iosTest/kotlin/com/mohamedrejeb/calf/camerapicker/IosCameraOwnershipAcceptanceTest.kt",
    "calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebViewContracts.kt",
    "calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt",
    "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewContentPolicyAcceptanceTest.kt",
    "scripts/ci/camera_ios_ownership_native_focus.py",
    "scripts/ci/camera_ios_ownership_source_projection.py",
    "scripts/ci/camera_recents_source_projection.py",
    "scripts/ci/ios_camera_ownership_native.init.gradle.kts",
    "scripts/ci/test_android_camera_boot_busy.py",
    "scripts/ci/test_android_camera_live_task_refusal_observation.py",
    "scripts/ci/test_android_external337_fixture_recovery.py",
    "scripts/ci/test_android_permission_demo_call_denial_recovery.py",
    "scripts/ci/test_android_permission_demo_selector.py",
    "scripts/ci/test_apple_image_launcher_source_projection.py",
    "scripts/ci/test_camera_ios_ownership_source_projection.py",
    "scripts/ci/test_camera_recents_observation.py",
    "scripts/ci/test_camera_tooling562_source_projection.py",
    "scripts/ci/test_webview_content_policy_source_projection.py",
    "scripts/ci/webview_content_policy_native_focus.py",
    "scripts/ci/webview_content_policy_source_projection.py",
}
ADDED_PATHS = {
    "scripts/ci/test_platform_recovery659_source_projection.py",
    "scripts/ci/test_tooling656_fixture_recovery.py",
}
UNCHANGED_PATHS = {
    "scripts/ci/fixtures/camera-ios-ownership-routing-source-inverse.json",
    "scripts/ci/fixtures/webview-content-policy-routing-source-inverse.json",
    "scripts/ci/ios_popover_anchor_plan.py",
}
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate platform-recovery659 manifest field")
        result[key] = value
    return result


def _document():
    from ios_popover_anchor_plan import _ordinary_bytes
    before = SPEC_PATH.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded platform-recovery659 manifest is required")
    raw = _ordinary_bytes(SPEC_PATH.parent, SPEC_PATH.name)[0]
    if not 0 < len(raw) <= MAX_SPEC_BYTES or sha(raw) != SPEC_SHA256:
        raise ValueError("The exact platform-recovery659 source manifest changed")
    try:
        document = json.loads(raw, object_pairs_hook=_unique,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite platform-recovery659 manifest")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("The complete platform-recovery659 manifest JSON is required") from None
    if (type(document) is not dict or set(document) != {
            "schema_version", "scope", "predecessor", "bindings", "added_inputs", "unchanged_inputs", "own_guard"} or
            type(document["schema_version"]) is not int or document["schema_version"] != 1 or
            document["scope"] != "Exact combined659/Unicode657/compiler660 source custody only; no compiler/native acceptance" or
            document["predecessor"] != PREDECESSOR or
            type(document["bindings"]) is not dict or set(document["bindings"]) != BOUND_PATHS or
            type(document["added_inputs"]) is not dict or set(document["added_inputs"]) != ADDED_PATHS or
            type(document["unchanged_inputs"]) is not dict or set(document["unchanged_inputs"]) != UNCHANGED_PATHS or
            type(document["own_guard"]) is not dict or set(document["own_guard"]) != {"template_sha256", "bytes"} or
            type(document["own_guard"]["bytes"]) is not int or not 0 < document["own_guard"]["bytes"] <= MAX_SOURCE_BYTES or
            type(document["own_guard"]["template_sha256"]) is not str or
            _DIGEST.fullmatch(document["own_guard"]["template_sha256"]) is None):
        raise ValueError("The exact finite platform-recovery659 manifest schema is required")
    for name, row in document["bindings"].items():
        if (type(row) is not dict or set(row) != {"before_sha256", "after_sha256", "before_bytes", "after_bytes", "fragments"} or
                any(type(row[key]) is not int or not 0 < row[key] <= MAX_SOURCE_BYTES for key in ("before_bytes", "after_bytes")) or
                any(type(row[key]) is not str or _DIGEST.fullmatch(row[key]) is None for key in ("before_sha256", "after_sha256")) or
                type(row["fragments"]) is not list or not 0 < len(row["fragments"]) <= 32):
            raise ValueError("Exact complete platform-recovery659 source bindings are required")
        for fragment in row["fragments"]:
            if (type(fragment) is not dict or set(fragment) != {
                    "before", "after", "before_fragment_sha256", "after_fragment_sha256", "obligation"} or
                    any(type(fragment[key]) is not str or not fragment[key] for key in fragment) or
                    any(_DIGEST.fullmatch(fragment[key]) is None for key in ("before_fragment_sha256", "after_fragment_sha256")) or
                    any(len(fragment[key].encode()) > MAX_SOURCE_BYTES for key in ("before", "after"))):
                raise ValueError("Exact finite platform-recovery659 fragment identities are required")
    for rows in (document["added_inputs"], document["unchanged_inputs"]):
        for name, digest in rows.items():
            if type(name) is not str or type(digest) is not str or _DIGEST.fullmatch(digest) is None:
                raise ValueError("Exact platform-recovery659 ordinary input hashes are required")
    return document


def _identity(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact platform-recovery659 relative identity and ordinary source bytes are required")


def source_before_platform_recovery659(relative, payload):
    """Exact complete inverse or its one immutable4697 preimage; not current admission."""
    _identity(relative, payload)
    from webview_current_contract667_source_projection import peel_contract667_for_history
    payload = peel_contract667_for_history(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is None:
        return payload  # Unlisted bytes are not certified, reconstructed or executed.
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded complete platform-recovery659 source bytes are required")
    observed = sha(payload)
    if observed == binding["before_sha256"] and len(payload) == binding["before_bytes"]:
        return payload
    if observed != binding["after_sha256"] or len(payload) != binding["after_bytes"]:
        raise ValueError("Platform-recovery659 source is not its complete reviewed afterimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (sha(before) != fragment["before_fragment_sha256"] or sha(after) != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact finite unique platform-recovery659 inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if sha(restored) != binding["before_sha256"] or len(restored) != binding["before_bytes"]:
        raise ValueError("Platform-recovery659 inverse did not restore the complete immutable4697 source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact finite unique platform-recovery659 forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Platform-recovery659 complete inverse/forward source roundtrip differs")
    return restored


def current_source_before_platform_recovery659(relative, payload):
    """One newest raw ingress; old, partial and unknown images cannot be current."""
    _identity(relative, payload)
    from webview_current_contract667_source_projection import current_source_before_contract667
    payload = current_source_before_contract667(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is not None and (sha(payload) != binding["after_sha256"] or len(payload) != binding["after_bytes"]):
        raise ValueError("An old or unknown image cannot replace exact current platform-recovery659 source")
    return source_before_platform_recovery659(relative, payload)


def peel_platform_recovery659_for_history(relative, payload):
    """Peel only a complete exact latest image; pass-through never certifies current."""
    _identity(relative, payload)
    from webview_current_contract667_source_projection import peel_contract667_for_history
    payload = peel_contract667_for_history(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is not None and sha(payload) == binding["after_sha256"]:
        return source_before_platform_recovery659(relative, payload)
    return payload  # Exact4697 or unknown bytes still face the unchanged old strict pins.


def _validate_own_guard(root, document):
    """Bind every new executable guard byte without a manifest/self-hash cycle.

    Only the unique literal manifest-SHA assignment is normalized to its fixed
    64-zero template. The complete ordinary raw guard and its length must match;
    the current manifest itself remains separately pinned by that exact literal.
    """
    from ios_popover_anchor_plan import _ordinary_bytes
    raw = _ordinary_bytes(root, SOURCE_RELATIVE)[0]
    from webview_current_contract667_source_projection import current_source_before_contract667
    raw = current_source_before_contract667(SOURCE_RELATIVE, raw)
    needle = ('SPEC_SHA256 = "' + SPEC_SHA256 + '"\n').encode()
    template = ('SPEC_SHA256 = "' + "0" * 64 + '"\n').encode()
    if (not 0 < len(raw) <= MAX_SOURCE_BYTES or len(raw) != document["own_guard"]["bytes"] or
            raw.count(needle) != 1 or sha(raw.replace(needle, template, 1)) != document["own_guard"]["template_sha256"]):
        raise ValueError("Current platform-recovery659 own guard differs from its exact singleton template: " + SOURCE_RELATIVE)


def validate_current_sources(root: Path):
    """Independently qualify actual raw finite inputs, own guard and NEW controls."""
    import webview_current_contract667_source_projection as current
    current.validate_current_sources(root)
    document = _document()
    _validate_own_guard(root, document)
    expected = ({name: row["after_sha256"] for name, row in document["bindings"].items()} |
                document["added_inputs"] | document["unchanged_inputs"] | {SPEC_RELATIVE: SPEC_SHA256})
    from ios_popover_anchor_plan import _ordinary_bytes
    for name, digest in expected.items():
        if sha(current.source_before_contract667(name, _ordinary_bytes(root, name)[0])) != digest:
            raise ValueError("Current platform-recovery659 input differs from its complete reviewed raw image: " + name)
    return True


def fixture_inputs():
    """Exactly this finite owning input union, with no native/controller execution."""
    document = _document()
    from webview_current_contract667_source_projection import fixture_inputs as contract_fixture_inputs
    return (set(document["bindings"]) | set(document["added_inputs"]) | set(document["unchanged_inputs"]) |
            {SPEC_RELATIVE, SOURCE_RELATIVE} | contract_fixture_inputs())
