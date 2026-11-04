# SPDX-License-Identifier: Apache-2.0
"""Finite public adaptive-control selections; not a replacement native transport.

The lead registers these specifications in the existing library runner. Source
validation is lexical admission only. Actual branch assertions, fresh KGP XML,
runtime/source custody and owned application cleanup remain independent gates.
"""
from __future__ import annotations

from pathlib import Path
import re

FOCUSES = ("ui-native-adaptive-pre26", "ui-native-adaptive-ios26plus")
MODULE = "calf-ui"
TASK_NAME = "iosSimulatorArm64ApplicationTest"
TASK = ":calf-ui:" + TASK_NAME
INIT_SCRIPT = "scripts/ci/ios_adaptive_controls_native.init.gradle.kts"
FOCUS_PROPERTY = "nativecmpkitAdaptiveControlsFocus"
PREFIX = "com.mohamedrejeb.calf.ui."
BASE = "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/"
SLIDER_CLASS = PREFIX + "slider.AdaptiveSliderNativeMatrixTest"
CUSTOM_CLASS = PREFIX + "controls.AdaptiveControlCustomizationMatrixTest"
TOOLBAR_CLASS = PREFIX + "toolbar.AdaptiveToolbarFallbackNativeTest"
SLIDER_SOURCE = BASE + "slider/AdaptiveSliderNativeMatrixTest.kt"
CUSTOM_SOURCE = BASE + "controls/AdaptiveControlCustomizationMatrixTest.kt"
TOOLBAR_SOURCE = BASE + "toolbar/AdaptiveToolbarFallbackNativeTest.kt"
BRANCH_SOURCE = BASE + "controls/AdaptiveControlNativeHost.kt"
HOST_SOURCE = BASE + "internal/NativeUiApplicationHost.kt"
IDENTITY_SOURCE = BASE + "internal/NativeObjectIdentity.kt"
SOURCES = (BRANCH_SOURCE, SLIDER_SOURCE, CUSTOM_SOURCE, TOOLBAR_SOURCE, HOST_SOURCE, IDENTITY_SOURCE)
SLIDER_METHODS = (
    "pre26PublicStepsTapDragAndAccessibilityMatrix",
    "ios26PublicStepsTapDragAndAccessibilityMatrix",
    "pre26PublicNegativeStepsAreRejected",
    "ios26PublicNegativeStepsAreRejected",
)
CUSTOM_METHODS = (
    "pre26CustomColorsContentAndInteractionsSurviveDarkAndLargeText",
    "ios26CustomColorsContentAndInteractionsSurviveDarkAndLargeText",
)
TOOLBAR_METHODS = (
    "pre26EmptyAndPopulatedItemsRenderMaterialSlotsAndCallerPlacement",
    "ios26EmptyItemsRenderMaterialSlotsAndCallerPlacement",
)
SCOPE = (
    "Four NEW public Adaptive library methods on the actually matching pre26 OR iOS26+ runtime: "
    "12 slider step/range/LTR-RTL rows with completed tap/drag/SetProgress and positive caller "
    "interaction pairs, exact public negative-steps refusal, dark/light x fontScale1/2 supplied "
    "customization/pixels/disabled input, and positive Material toolbar fallback. The other OS "
    "branch is independently required, never ignored or simulated. No accepted LiquidGlass replay, "
    "populated native26+ toolbar/safe-area/keyboard/OS rotation/bottom-bar integration, spoken "
    "assistive/OS Settings, sample, physical/all-OS, consumer/API-ABI/security or release certification."
)
_METHOD_PATTERN = re.compile(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)")
_DISABLED = re.compile(r"@(Ignore|Disabled|IgnoredTest)\b")
_UUID = re.compile(r"[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}")


def branch(focus: str) -> str:
    if focus not in FOCUSES:
        raise ValueError("Select exactly one reviewed public adaptive OS branch")
    return "pre26" if focus == FOCUSES[0] else "ios26plus"


def focus_spec(focus: str) -> dict:
    index = FOCUSES.index(focus) if focus in FOCUSES else None
    if index is None:
        raise ValueError("Unknown adaptive native focus")
    return {"groups": (
        {"classname": SLIDER_CLASS, "source": SLIDER_SOURCE,
         "methods": (SLIDER_METHODS[index], SLIDER_METHODS[index + 2]), "declared_methods": SLIDER_METHODS},
        {"classname": CUSTOM_CLASS, "source": CUSTOM_SOURCE,
         "methods": (CUSTOM_METHODS[index],), "declared_methods": CUSTOM_METHODS},
        {"classname": TOOLBAR_CLASS, "source": TOOLBAR_SOURCE,
         "methods": (TOOLBAR_METHODS[index],), "declared_methods": TOOLBAR_METHODS},
    ), "module": MODULE, "scope": SCOPE}


def selectors(focus: str) -> tuple[str, ...]:
    return tuple(group["classname"] + "." + method
                 for group in focus_spec(focus)["groups"] for method in group["methods"])


def test_filter(focus: str) -> str:
    return ",".join(selectors(focus))


def native_request(focus: str) -> list[str]:
    return [TASK, *(argument for selector in selectors(focus) for argument in ("--tests", selector))]


def validate_request(task_names: list[str], focus: str) -> bool:
    if type(task_names) is not list or task_names != native_request(focus):
        raise ValueError("Adaptive native execution requires its exact four method selectors only")
    return True


def identities(focus: str) -> list[dict]:
    return [{"classname": TASK_NAME + "." + group["classname"],
             "name": method + "[iosSimulatorArm64]"}
            for group in focus_spec(focus)["groups"] for method in group["methods"]]


def _ordinary_source(root: Path, name: str) -> str:
    path = root / name
    if (not path.is_file() or path.absolute() != path.resolve() or
            not path.resolve().is_relative_to(root.resolve())):
        raise ValueError("Adaptive source admission requires ordinary exact repository files")
    return path.read_text(encoding="utf-8")


def validate_sources(root: Path, test_sources: list[str] | None = None) -> bool:
    """Keep both real branch declarations, regardless of the selected runtime."""
    if test_sources is not None and not set(SOURCES) <= set(test_sources):
        raise ValueError("Adaptive selection requires all six exact authored test inputs")
    text = {name: _ordinary_source(root, name) for name in SOURCES}
    for group in focus_spec(FOCUSES[0])["groups"]:
        source = text[group["source"]]
        package, classname = group["classname"].rsplit(".", 1)
        if (_METHOD_PATTERN.findall(source) != list(group["declared_methods"]) or
                not re.search(r"(?m)^package " + re.escape(package) + r"\s*$", source) or
                not re.search(r"\bclass\s+" + re.escape(classname) + r"\s*\{", source) or
                _DISABLED.search(source) or "requireAdaptiveControlHost(branch)" not in source):
            raise ValueError("Adaptive native declarations must retain both enabled real OS branches")
    for focus, enum in zip(FOCUSES, ("Pre26", "IOS26Plus")):
        for group in focus_spec(focus)["groups"]:
            for method in group["methods"]:
                wrapper = re.search(r"@Test\s+fun\s+" + re.escape(method) +
                    r"\s*\(\s*\)\s*=\s*\w+\(AdaptiveControlBranch\." + enum + r"\b", text[group["source"]])
                if wrapper is None:
                    raise ValueError("Every adaptive selected method must enter its own actual OS branch")
    for name in (BRANCH_SOURCE, HOST_SOURCE, IDENTITY_SOURCE):
        if re.search(r"@(Test|Ignore|Disabled|IgnoredTest)\b", text[name]):
            raise ValueError("Adaptive native ownership/admission helpers must remain enabled zero-test inputs")
    host = text[BRANCH_SOURCE]
    for fragment in ("val version = onApplicationMain", "requireOwnedApplicationWindow()",
                     "UIDevice.currentDevice.systemVersion", "assertTrue(major > 0",
                     "major < 26 else major >= 26"):
        if fragment not in host:
            raise ValueError("Adaptive admission must read and assert the actual owned application's iOS branch")
    for name, public_calls in (
        (SLIDER_SOURCE, ("AdaptiveSlider(",)),
        (CUSTOM_SOURCE, ("AdaptiveButton(", "AdaptiveIconButton(", "AdaptiveSlider(", "AdaptiveSwitch(")),
        (TOOLBAR_SOURCE, ("AdaptiveToolbar(",)),
    ):
        if (any(call not in text[name] for call in public_calls) or
                re.search(r"\b(?:CupertinoSlider|LiquidGlassSliderImpl|CupertinoSwitch|LiquidGlassSwitchImpl)\s*\(", text[name])):
            raise ValueError("Adaptive matrices require public platform-selected controls, not forced renderers")
    return True


def validate_runtime(simulator: dict, focus: str) -> bool:
    """Recorded simctl runtime gate; UIDevice independently asserts it in native tests."""
    selected_branch = branch(focus)
    if type(simulator) is not dict or simulator.get("state") != "Booted":
        raise ValueError("Adaptive matrices require the actual recorded booted simulator")
    version, identifier = simulator.get("runtime_version"), simulator.get("runtime_identifier")
    udid = simulator.get("udid")
    if (type(udid) is not str or not _UUID.fullmatch(udid) or type(version) is not str or
            not re.fullmatch(r"[1-9][0-9]{0,2}(?:\.[0-9]{1,3}){0,2}", version) or
            type(identifier) is not str or
            not re.fullmatch(r"com\.apple\.CoreSimulator\.SimRuntime\.iOS-[0-9]+(?:-[0-9]+)*", identifier)):
        raise ValueError("Adaptive runtime must retain its exact recorded iOS version, identifier and UDID")
    major = int(version.split(".")[0])
    if (major < 26) != (selected_branch == "pre26"):
        raise ValueError("Unavailable or wrong adaptive OS branches are failures, never N/A substitutes")
    return True


def outcomes(cases: list[dict], system: str, focus: str) -> tuple[list[dict], list[str]]:
    """XML identities are native-task exact; no skips, duplicates or foreign cases."""
    expected = identities(focus)
    host_ok = type(system) is str and system.lower() in {"darwin", "macos", "mac os x"}
    errors = [] if host_ok else ["Adaptive acceptance requires actual Apple-host application execution"]
    valid_shape = type(cases) is list and all(type(case) is dict and
        all(type(case.get(key)) is str for key in ("classname", "name", "status")) for case in cases)
    actual = [(case["classname"], case["name"]) for case in cases] if valid_shape else []
    wanted = [(item["classname"], item["name"]) for item in expected]
    exact = valid_shape and len(actual) == len(wanted) and set(actual) == set(wanted)
    if not exact:
        errors.append("Adaptive XML must contain exactly four selected application methods with no duplicates or foreign cases")
    sources = {TASK_NAME + "." + group["classname"]: group["source"] for group in focus_spec(focus)["groups"]}
    scenarios = []
    for item in expected:
        matching = [case for case in cases if (case["classname"], case["name"]) ==
                    (item["classname"], item["name"])] if valid_shape else []
        passed = exact and host_ok and len(matching) == 1 and matching[0]["status"] == "passed"
        if not passed:
            errors.append("Adaptive native method must pass exactly once: " + item["name"])
        scenarios.append({**item, "source": sources[item["classname"]], "task": TASK_NAME,
                          "target": "iosSimulatorArm64", "actual_os_branch_required": branch(focus),
                          "required_on_host": True,
                          "disposition": "required-executed" if passed else "required-not-passed"})
    return scenarios, errors
