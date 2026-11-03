# SPDX-License-Identifier: Apache-2.0
"""Strict opt-in genuine OS geometry, never whole-issue or split-view acceptance."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re

from ios_popover_anchor_plan import RECEIPT, _ordinary_bytes, _unique_object
import ios_popover_geometry_source_projection as source_history

FOCUSES = ("ui-native-popover-portrait-traits", "ui-native-popover-os-rotation")
CLASS = "com.mohamedrejeb.calf.ui.dialog.NativePopoverGeometryTest"
METHODS = (
    "nativePortraitTraitsAndViewLocalAnchorUseTheOwnedScene",
    "nativeOSRotationRefreshesOwnedAnchorsAndRestoresTheOriginalOrientation",
)
NATIVE = "calf-ui/src/iosGeometryTest/kotlin/com/mohamedrejeb/calf/ui/dialog/NativePopoverGeometryTest.kt"
SCENE = "calf-ui/src/iosGeometryTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativePopoverGeometryScene.kt"
HOST = "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt"
IDENTITY = "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt"
INIT_SCRIPT = "scripts/ci/ios_popover_geometry_compile.init.gradle.kts"
SOURCE = "scripts/ci/ios_popover_geometry_plan.py"
SOURCES = (NATIVE, HOST, IDENTITY, SCENE)
ORIENTATIONS = ["UIInterfaceOrientationPortrait", "UIInterfaceOrientationLandscapeLeft",
                "UIInterfaceOrientationLandscapeRight", "UIInterfaceOrientationPortraitUpsideDown"]


def validate_sources(root: Path) -> bool:
    """Exact native/route/host postimages; older source projection is not current admission."""
    source_history.validate_current_sources(root)
    native = _ordinary_bytes(root, NATIVE)[0].decode("utf-8")
    scene = _ordinary_bytes(root, SCENE)[0].decode("utf-8")
    if (re.search(r"@(Ignore|Disabled|IgnoredTest)\b", native + scene) or
            re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", native) != list(METHODS) or
            re.search(r"@Test\b", scene)):
        raise ValueError("Only the two enabled native geometry declarations and zero-test scene helper are admitted")
    return True


def scene_information() -> dict:
    """One actual UIKit scene; orientations are eligibility, not proof of OS input or split view."""
    return {
        "UIApplicationSceneManifest": {
            "UIApplicationSupportsMultipleScenes": False,
            "UISceneConfigurations": {"UIWindowSceneSessionRoleApplication": [{
                "UISceneConfigurationName": "NativeCmpKitGeometry",
                "UISceneClassName": "UIWindowScene",
                "UISceneDelegateClassName": "NativeCmpKitPopoverGeometrySceneDelegate",
            }]},
        },
        "UISupportedInterfaceOrientations": list(ORIENTATIONS),
        "UISupportedInterfaceOrientations~ipad": list(ORIENTATIONS),
        "UIRequiresFullScreen": False,
    }


def expected_idiom(simulator: dict, focus: str) -> str:
    if type(simulator) is not dict or focus not in FOCUSES or simulator.get("state") != "Booted":
        raise ValueError("Geometry requires its exact booted recorded simulator and focus")
    kind = "iphone" if focus == FOCUSES[0] else "ipad"
    device = simulator.get("device_type")
    prefix = "com.apple.CoreSimulator.SimDeviceType." + ("iPhone-" if kind == "iphone" else "iPad-")
    if type(device) is not str or not device.startswith(prefix) or len(device) > 180:
        raise ValueError("Geometry cannot switch its configured native phone/tablet identity")
    version = simulator.get("runtime_version")
    if type(version) is not str or not re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,2}", version) or int(version.split('.')[0]) < 16:
        raise ValueError("Public WindowScene geometry requires an actually recorded iOS16-or-newer runtime")
    return kind


def launch_environment(simulator: dict, focus: str) -> dict:
    return {"NATIVECMPKIT_OWNED_POPOVER_GEOMETRY": "1",
            "NATIVECMPKIT_POPOVER_GEOMETRY_IDIOM": expected_idiom(simulator, focus)}


def process_launch_environment(simulator: dict, focus: str, *, environment=None) -> dict:
    """Process-local simctl forwarding; never archive the inherited host environment.

    xcrun needs the host environment, whereas simctl forwards only SIMCTL_CHILD_
    variables into the app. Plain app keys or a two-entry replacement environment
    would silently lose the scene opt-in and cannot stand in for native execution.
    """
    source = dict(os.environ) if environment is None else environment
    if type(source) is not dict or any(type(key) is not str or type(value) is not str
                                       for key, value in source.items()):
        raise ValueError("Ordinary process-local launch environment required")
    result = source.copy()
    for name, value in launch_environment(simulator, focus).items():
        key = "SIMCTL_CHILD_" + name
        if key in result and result[key] != value:
            raise ValueError("Foreign inherited geometry mode cannot be overridden")
        result[key] = value
    return result


def application_fixture(root: Path, simulator: dict, focus: str) -> dict:
    return {"schema_version": 1, "focus": focus, "expected_idiom": expected_idiom(simulator, focus),
            "scene_mode_requested": True, "legacy_activation_fallback_allowed": False,
            "scene_information": scene_information(), "launch_environment": launch_environment(simulator, focus),
            "source_sha256": {path: hashlib.sha256(_ordinary_bytes(root, path)[0]).hexdigest()
                              for path in (SOURCE, INIT_SCRIPT, NATIVE, HOST, IDENTITY, SCENE)},
            "real_split_view_verified": False, "packages_published": False, "release_readiness_certified": False}


def _exact_typed_value(actual, expected, *, depth=0, budget=None) -> bool:
    """Bounded ordinary JSON comparison: Boolean false is never numeric zero.

    Traverse the small maintainer-authored expected shape, not arbitrary receipt
    content. Reject subclasses, unknown fields, oversized collections and cycles
    before invoking foreign equality or unbounded recursion.
    """
    if budget is None:
        budget = [256]
    budget[0] -= 1
    if budget[0] < 0 or depth > 16 or type(actual) is not type(expected):
        return False
    if type(expected) is dict:
        if len(actual) != len(expected) or len(actual) > 64 or any(type(key) is not str for key in actual):
            return False
        if actual.keys() != expected.keys():
            return False
        return all(_exact_typed_value(actual[key], value, depth=depth + 1, budget=budget)
                   for key, value in expected.items())
    if type(expected) is list:
        return (len(actual) == len(expected) <= 64 and
                all(_exact_typed_value(a, e, depth=depth + 1, budget=budget) for a, e in zip(actual, expected)))
    if type(expected) in (str, int, bool, type(None)):
        return actual == expected
    return False


def validate_application_fixture(receipt, root: Path, simulator: dict, focus: str) -> bool:
    try:
        return _exact_typed_value(receipt, application_fixture(root, simulator, focus))
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        return False


def validate_compilation(root: Path, started_ns: int, ended_ns: int, focus: str) -> bool:
    if (focus not in FOCUSES or type(started_ns) is not int or type(ended_ns) is not int or
            started_ns <= 0 or ended_ns < started_ns):
        return False
    try:
        raw, info = _ordinary_bytes(root, RECEIPT)
        if not started_ns - 2_000_000_000 <= info.st_mtime_ns <= ended_ns + 2_000_000_000:
            return False
        document = json.loads(raw, object_pairs_hook=_unique_object,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite compiler receipt")))
        expected = {
            "task": ":calf-ui:compileTestKotlinIosSimulatorArm64", "focus": focus,
            "source_sha256": {name: hashlib.sha256(_ordinary_bytes(root, name)[0]).hexdigest() for name in SOURCES},
            "effective_sources": list(SOURCES), "excluded_unrelated_test_sources": True,
            "production_source_sets_changed": False, "native_tests_executed": 0,
            "scope": "Actual precompiler source admission only; compiler exit and fresh native XML decide outcomes",
        }
        return _exact_typed_value(document, expected)
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        return False
