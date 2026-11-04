# SPDX-License-Identifier: Apache-2.0
"""Exact UI650 nine/one source isolation above the accepted667 predecessor.

Only finite complete inverse/forward source arithmetic is performed. Restored
source is never executed; controls, compilers, native controllers, host queries,
network and Git mutations are not run here. Original failures and pins remain.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
SOURCE_RELATIVE = "scripts/ci/ios_ui_split664_source_projection.py"
SPEC_RELATIVE = "scripts/ci/fixtures/ios-ui-split664-source-inverse.json"
SPEC_PATH = Path(__file__).parent / "fixtures/ios-ui-split664-source-inverse.json"
SPEC_SHA256 = "1455a8edb3553a87a409f7fc30568ede9f7f52fe97042690b668dc6ebc145f4a"
PREDECESSOR = "044d9aa83ad19fa77ddf94f36a7700f3b52de4b1"
BOUND_PATHS = frozenset({
    ".github/workflows/gradle.yml",
    "calf-ui/build.gradle.kts",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlCustomizationMatrixTest.kt",
    "scripts/ci/ios_ui_application.py",
    "scripts/ci/ios_ui_related_native_focus.py",
    "scripts/ci/library_tests.py",
    "scripts/ci/test_ios_ui_related_source_projection.py",
    "scripts/ci/webview_current_contract667_source_projection.py",
    "scripts/ci/workflow_matrix.py",
})
ADDED_PATHS = frozenset({
    "scripts/ci/ios_ui_split_native.init.gradle.kts",
    "scripts/ci/test_ios_ui_split664_native_routing.py",
})
UNCHANGED_PATHS = frozenset({
    "calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/button/LiquidGlassButton.kt",
    "calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragAnimation.kt",
    "calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/InteractiveHighlight.kt",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/button/LiquidButtonConstructionTraceTest.kt",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlNativeHost.kt",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/PointerCancellation.kt",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSliderNativeMatrixTest.kt",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbarFallbackNativeTest.kt",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragLifecycleRegressionTest.kt",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/InteractiveHighlightResourceLifecycleTest.kt",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/UiDragShaderTestHost.kt",
    "scripts/ci/fixtures/apple-image-launcher-source-inverse.json",
    "scripts/ci/fixtures/calendar-share-selector-source-inverse.json",
    "scripts/ci/fixtures/ios-ui-related-source-inverse.json",
    "scripts/ci/fixtures/platform-recovery659-source-inverse.json",
    "scripts/ci/fixtures/webview-content-policy-routing-source-inverse.json",
    "scripts/ci/fixtures/webview-current-contract667-source-inverse.json",
    "scripts/ci/ios_adaptive_controls_native.init.gradle.kts",
    "scripts/ci/ios_adaptive_controls_native_focus.py",
    "scripts/ci/ios_adaptive_controls_runtime.py",
    "scripts/ci/ios_popover_anchor_plan.py",
    "scripts/ci/ios_ui_adaptive_drag_shader_native.init.gradle.kts",
    "scripts/ci/ios_ui_related_source_projection.py",
    "scripts/ci/platform_recovery659_source_projection.py",
    "scripts/ci/test_platform_recovery659_source_projection.py",
    "scripts/ci/test_webview_content_policy_native_focus.py",
    "scripts/ci/test_webview_current_contract667_source_projection.py",
    "scripts/ci/webview_content_policy_native_focus.py",
})
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_SCOPE = "Exact UI650 nine/one routing664 and sealed UI609 source custody only; no compiler/native acceptance"


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate UI-split664 manifest field")
        result[key] = value
    return result


def _document():
    from ios_popover_anchor_plan import _ordinary_bytes
    before = SPEC_PATH.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded UI-split664 manifest is required")
    raw = _ordinary_bytes(SPEC_PATH.parent, SPEC_PATH.name)[0]
    if not 0 < len(raw) <= MAX_SPEC_BYTES or sha(raw) != SPEC_SHA256:
        raise ValueError("The exact UI-split664 source manifest changed")
    try:
        document = json.loads(raw, object_pairs_hook=_unique,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite UI-split664 manifest")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("The complete UI-split664 manifest JSON is required") from None
    if (type(document) is not dict or set(document) != {
            "schema_version", "scope", "predecessor", "bindings", "added_inputs", "unchanged_inputs", "own_guard"} or
            type(document["schema_version"]) is not int or document["schema_version"] != 1 or
            document["scope"] != _SCOPE or document["predecessor"] != PREDECESSOR or
            type(document["bindings"]) is not dict or set(document["bindings"]) != BOUND_PATHS or
            type(document["added_inputs"]) is not dict or set(document["added_inputs"]) != ADDED_PATHS or
            type(document["unchanged_inputs"]) is not dict or set(document["unchanged_inputs"]) != UNCHANGED_PATHS or
            type(document["own_guard"]) is not dict or set(document["own_guard"]) != {"template_sha256", "bytes"} or
            type(document["own_guard"]["bytes"]) is not int or not 0 < document["own_guard"]["bytes"] <= MAX_SOURCE_BYTES or
            type(document["own_guard"]["template_sha256"]) is not str or
            _DIGEST.fullmatch(document["own_guard"]["template_sha256"]) is None):
        raise ValueError("The exact finite UI-split664 manifest schema is required")
    for row in document["bindings"].values():
        if (type(row) is not dict or set(row) != {
                "before_sha256", "after_sha256", "before_bytes", "after_bytes", "fragments"} or
                any(type(row[key]) is not int or not 0 < row[key] <= MAX_SOURCE_BYTES
                    for key in ("before_bytes", "after_bytes")) or
                any(type(row[key]) is not str or _DIGEST.fullmatch(row[key]) is None
                    for key in ("before_sha256", "after_sha256")) or
                type(row["fragments"]) is not list or not 0 < len(row["fragments"]) <= 64):
            raise ValueError("Exact complete UI-split664 source bindings are required")
        for fragment in row["fragments"]:
            if (type(fragment) is not dict or set(fragment) != {
                    "before", "after", "before_fragment_sha256", "after_fragment_sha256", "obligation"} or
                    any(type(fragment[key]) is not str or not fragment[key] for key in fragment) or
                    any(_DIGEST.fullmatch(fragment[key]) is None
                        for key in ("before_fragment_sha256", "after_fragment_sha256")) or
                    any(len(fragment[key].encode()) > MAX_SOURCE_BYTES for key in ("before", "after"))):
                raise ValueError("Exact finite UI-split664 fragments are required")
    for rows in (document["added_inputs"], document["unchanged_inputs"]):
        if any(type(digest) is not str or _DIGEST.fullmatch(digest) is None for digest in rows.values()):
            raise ValueError("Exact UI-split664 ordinary input hashes are required")
    return document


def _identity(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact UI-split664 relative identity and ordinary source bytes are required")


def source_before_ui_split664(relative, payload):
    """Complete exact inverse or its one accepted667 preimage; not current admission."""
    _identity(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is None:
        return payload  # Unlisted bytes are not certified, reconstructed or executed.
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded complete UI-split664 source bytes are required")
    observed = sha(payload)
    if observed == binding["before_sha256"] and len(payload) == binding["before_bytes"]:
        return payload
    if observed != binding["after_sha256"] or len(payload) != binding["after_bytes"]:
        raise ValueError("UI-split664 source is not its complete reviewed afterimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (sha(before) != fragment["before_fragment_sha256"] or sha(after) != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique UI-split664 inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if sha(restored) != binding["before_sha256"] or len(restored) != binding["before_bytes"]:
        raise ValueError("UI-split664 inverse did not restore its complete accepted667 source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique UI-split664 forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("UI-split664 complete inverse/forward source roundtrip differs")
    return restored


def current_source_before_ui_split664(relative, payload):
    """One newest raw ingress; old, partial and unknown bound images must refuse."""
    _identity(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is not None and (sha(payload) != binding["after_sha256"] or len(payload) != binding["after_bytes"]):
        raise ValueError("An old or unknown image cannot replace exact current UI-split664 source")
    return source_before_ui_split664(relative, payload)


def peel_ui_split664_for_history(relative, payload):
    """Peel only complete exact latest images; pass-through never certifies current."""
    _identity(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is not None and sha(payload) == binding["after_sha256"]:
        return source_before_ui_split664(relative, payload)
    return payload  # Exact667 or unknown bytes still face the unchanged next strict pin.


def _validate_own_guard(root, document):
    """Bind all new guard bytes without a manifest/self-hash cycle."""
    from ios_popover_anchor_plan import _ordinary_bytes
    raw = _ordinary_bytes(root, SOURCE_RELATIVE)[0]
    needle = ('SPEC_SHA256 = "' + SPEC_SHA256 + '"\n').encode()
    template = ('SPEC_SHA256 = "' + "0" * 64 + '"\n').encode()
    if (not 0 < len(raw) <= MAX_SOURCE_BYTES or len(raw) != document["own_guard"]["bytes"] or
            raw.count(needle) != 1 or sha(raw.replace(needle, template, 1)) != document["own_guard"]["template_sha256"]):
        raise ValueError("Current UI-split664 own guard differs from its exact singleton template")
    return sha(raw)  # Qualified by the entire unchanged singleton template above.


def _expected(document):
    return ({name: row["after_sha256"] for name, row in document["bindings"].items()} |
            document["added_inputs"] | document["unchanged_inputs"] | {SPEC_RELATIVE: SPEC_SHA256})


def current_input_hashes():
    """Only exact qualified raw source identities; no native/compiler selection."""
    document = _document()
    return _expected(document) | {SOURCE_RELATIVE: _validate_own_guard(ROOT, document)}


def validate_current_sources(root: Path):
    """Qualify actual raw finite UI inputs before any immutable older comparison."""
    document = _document()
    _validate_own_guard(root, document)
    from ios_popover_anchor_plan import _ordinary_bytes
    for name, digest in _expected(document).items():
        if sha(_ordinary_bytes(root, name)[0]) != digest:
            raise ValueError("Current UI-split664 input differs from its complete reviewed raw image: " + name)
    return True


def fixture_inputs():
    """Exactly the finite UI source-custody union, with no other checkout binding."""
    return BOUND_PATHS | ADDED_PATHS | UNCHANGED_PATHS | {SOURCE_RELATIVE, SPEC_RELATIVE}
