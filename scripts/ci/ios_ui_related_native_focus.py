# SPDX-License-Identifier: Apache-2.0
"""Finite related UI wiring, not a replacement native transport or compiler result.

One genuine iOS26+ owned application selects adaptive4 plus NEW drag/shader6;
pre26 adaptive4 remains independently required. Source admission and model XML
controls are not native execution, hardware profiling or issue acceptance.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re

import ios_adaptive_controls_native_focus as adaptive
import ios_adaptive_controls_runtime as adaptive_runtime
from ios_popover_anchor_plan import _ordinary_bytes, _unique_object

FOCUSES = ("ui-native-adaptive-pre26", "ui-native-adaptive-drag-shader-ios26plus")
MODULE = "calf-ui"
TASK_NAME = "iosSimulatorArm64ApplicationTest"
TASK = ":calf-ui:" + TASK_NAME
SCOPE = ("One actually matching iOS26+ owned application: four adaptive public-control methods "
         "plus six NEW actual drag/shader/resource/construction methods. Separate genuine pre26 "
         "adaptive4 remains required, never N/A or simulated. No old8/other-OS accepted replay, "
         "physical hardware, Instruments, all-OS, consumer/API-ABI/security/release or issue closure claim.")
_METHOD = re.compile(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)")
_DISABLED = re.compile(r"@(Ignore|Disabled|IgnoredTest)\b")
_SELECTIONS = {'ui-native-adaptive-drag-shader-ios26plus': {'focus_property': 'nativecmpkitUiRelatedFocus',
                                              'groups': [{'classname': 'com.mohamedrejeb.calf.ui.slider.AdaptiveSliderNativeMatrixTest',
                                                          'declared_methods': ['pre26PublicStepsTapDragAndAccessibilityMatrix',
                                                                               'ios26PublicStepsTapDragAndAccessibilityMatrix',
                                                                               'pre26PublicNegativeStepsAreRejected',
                                                                               'ios26PublicNegativeStepsAreRejected'],
                                                          'methods': ['ios26PublicStepsTapDragAndAccessibilityMatrix',
                                                                      'ios26PublicNegativeStepsAreRejected'],
                                                          'source': 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSliderNativeMatrixTest.kt'},
                                                         {'classname': 'com.mohamedrejeb.calf.ui.controls.AdaptiveControlCustomizationMatrixTest',
                                                          'declared_methods': ['pre26CustomColorsContentAndInteractionsSurviveDarkAndLargeText',
                                                                               'ios26CustomColorsContentAndInteractionsSurviveDarkAndLargeText'],
                                                          'methods': ['ios26CustomColorsContentAndInteractionsSurviveDarkAndLargeText'],
                                                          'source': 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlCustomizationMatrixTest.kt'},
                                                         {'classname': 'com.mohamedrejeb.calf.ui.toolbar.AdaptiveToolbarFallbackNativeTest',
                                                          'declared_methods': ['pre26EmptyAndPopulatedItemsRenderMaterialSlotsAndCallerPlacement',
                                                                               'ios26EmptyItemsRenderMaterialSlotsAndCallerPlacement'],
                                                          'methods': ['ios26EmptyItemsRenderMaterialSlotsAndCallerPlacement'],
                                                          'source': 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbarFallbackNativeTest.kt'},
                                                         {'classname': 'com.mohamedrejeb.calf.ui.utils.DampedDragLifecycleRegressionTest',
                                                          'declared_methods': ['cancellationFromActualStartAndStopCallbacksCannotRecreateFeedbackAndNextGestureRecovers',
                                                                               'removingAnActiveActualModifierLeavesNoReleaseWorkInTheCallerScopeAndRangeReplacementRecovers',
                                                                               'thousandSustainedUpdatesTraceActualJobTreesAcrossFramesAndRepressWithoutCancellingSiblingWork'],
                                                          'methods': ['cancellationFromActualStartAndStopCallbacksCannotRecreateFeedbackAndNextGestureRecovers',
                                                                      'removingAnActiveActualModifierLeavesNoReleaseWorkInTheCallerScopeAndRangeReplacementRecovers',
                                                                      'thousandSustainedUpdatesTraceActualJobTreesAcrossFramesAndRepressWithoutCancellingSiblingWork'],
                                                          'source': 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragLifecycleRegressionTest.kt'},
                                                         {'classname': 'com.mohamedrejeb.calf.ui.utils.InteractiveHighlightResourceLifecycleTest',
                                                          'declared_methods': ['disposingAPressedRetainedModifierClosesItsRealBuilderStopsPixelsAndNeverRestartsItsJobs',
                                                                               'removingAnActualPressedHighlightClosesItsBuilderAndNewCompositionUsesANewOwnedResource'],
                                                          'methods': ['disposingAPressedRetainedModifierClosesItsRealBuilderStopsPixelsAndNeverRestartsItsJobs',
                                                                      'removingAnActualPressedHighlightClosesItsBuilderAndNewCompositionUsesANewOwnedResource'],
                                                          'source': 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/InteractiveHighlightResourceLifecycleTest.kt'},
                                                         {'classname': 'com.mohamedrejeb.calf.ui.button.LiquidButtonConstructionTraceTest',
                                                          'declared_methods': ['hundredActualPublicButtonsKeepOptionalShaderConstructionAtZeroThroughInputDisableAndRecreation'],
                                                          'methods': ['hundredActualPublicButtonsKeepOptionalShaderConstructionAtZeroThroughInputDisableAndRecreation'],
                                                          'source': 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/button/LiquidButtonConstructionTraceTest.kt'}],
                                              'init_script': 'scripts/ci/ios_ui_adaptive_drag_shader_native.init.gradle.kts',
                                              'runtime_focus': 'ui-native-adaptive-ios26plus',
                                              'test_sources': ['calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlNativeHost.kt',
                                                               'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSliderNativeMatrixTest.kt',
                                                               'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlCustomizationMatrixTest.kt',
                                                               'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbarFallbackNativeTest.kt',
                                                               'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt',
                                                               'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt',
                                                               'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragLifecycleRegressionTest.kt',
                                                               'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/InteractiveHighlightResourceLifecycleTest.kt',
                                                               'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/button/LiquidButtonConstructionTraceTest.kt',
                                                               'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/UiDragShaderTestHost.kt',
                                                               'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/PointerCancellation.kt']},
 'ui-native-adaptive-pre26': {'focus_property': 'nativecmpkitAdaptiveControlsFocus',
                              'groups': [{'classname': 'com.mohamedrejeb.calf.ui.slider.AdaptiveSliderNativeMatrixTest',
                                          'declared_methods': ['pre26PublicStepsTapDragAndAccessibilityMatrix',
                                                               'ios26PublicStepsTapDragAndAccessibilityMatrix',
                                                               'pre26PublicNegativeStepsAreRejected',
                                                               'ios26PublicNegativeStepsAreRejected'],
                                          'methods': ['pre26PublicStepsTapDragAndAccessibilityMatrix',
                                                      'pre26PublicNegativeStepsAreRejected'],
                                          'source': 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSliderNativeMatrixTest.kt'},
                                         {'classname': 'com.mohamedrejeb.calf.ui.controls.AdaptiveControlCustomizationMatrixTest',
                                          'declared_methods': ['pre26CustomColorsContentAndInteractionsSurviveDarkAndLargeText',
                                                               'ios26CustomColorsContentAndInteractionsSurviveDarkAndLargeText'],
                                          'methods': ['pre26CustomColorsContentAndInteractionsSurviveDarkAndLargeText'],
                                          'source': 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlCustomizationMatrixTest.kt'},
                                         {'classname': 'com.mohamedrejeb.calf.ui.toolbar.AdaptiveToolbarFallbackNativeTest',
                                          'declared_methods': ['pre26EmptyAndPopulatedItemsRenderMaterialSlotsAndCallerPlacement',
                                                               'ios26EmptyItemsRenderMaterialSlotsAndCallerPlacement'],
                                          'methods': ['pre26EmptyAndPopulatedItemsRenderMaterialSlotsAndCallerPlacement'],
                                          'source': 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbarFallbackNativeTest.kt'}],
                              'init_script': 'scripts/ci/ios_adaptive_controls_native.init.gradle.kts',
                              'runtime_focus': 'ui-native-adaptive-pre26',
                              'test_sources': ['calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlNativeHost.kt',
                                               'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSliderNativeMatrixTest.kt',
                                               'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlCustomizationMatrixTest.kt',
                                               'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbarFallbackNativeTest.kt',
                                               'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt',
                                               'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt']}}
SOURCE_SHA256 = {'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/button/LiquidButtonConstructionTraceTest.kt': '1b417a078d26c7d2f09dcaa5c5e17ac9be0806fd4f8a88dffb5e616978207954',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlCustomizationMatrixTest.kt': 'c792203a97cc8bdea914856b5cd53195f7a623170820fbc3f91a4ef9fd55d61d',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlNativeHost.kt': '5132474a968f50ce40e161049b32700c28d1709d0e6b1bbd6fecb239f6fd9e20',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt': 'd3cccfc654399598abf00e04d6f40529a3802e9488448afde120da8180932df0',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt': 'ea18a76b5270fee0c95e953e6a4d280cc00b4fc2b64538a6ca23f7097ca43a0f',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/PointerCancellation.kt': '5e9aef0d114a3e4b9d992ce3be2fd5fd96951443a527e68f1c6f87f78d6a1b2b',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSliderNativeMatrixTest.kt': '9ed073effcf3b5399f4838887d271a1b893a2a9bb123afc6771fcd15d2ca87d4',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbarFallbackNativeTest.kt': 'c7cfac7363f93e1fa880378f5e38c7289faa9e0b3570e3999c9fe11b2bdc2207',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragLifecycleRegressionTest.kt': 'd1e96296dce57bb817a08abca87a2943d9924745d1208fd7591751ed9d5dd3e8',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/InteractiveHighlightResourceLifecycleTest.kt': '9ded1ba61f6702ef2b6f28312b6971a37a112564c1d030dbe22b0f25419fefbf',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/UiDragShaderTestHost.kt': '7ce8cef67a1d4df0430852e77d37967574d42fd039b76a0a6ebb347f93b8cb8c'}
INIT_SHA256 = {'ui-native-adaptive-drag-shader-ios26plus': '6f11a305e3ffbe778d4b3aaa6e8a83e50b51c30af63666d2515f26250839e3c8',
 'ui-native-adaptive-pre26': '90ac4d7f46ee8f88192eb23a3da5b3ce62ef1c00c9a8003a89800b47e305e8e8'}


def _selection(focus: str) -> dict:
    if type(focus) is not str or focus not in FOCUSES:
        raise ValueError("Select only the related iOS26+ ten or independent pre26 four")
    return _SELECTIONS[focus]


def focus_spec(focus: str) -> dict:
    return {"groups": tuple({**group, "methods": tuple(group["methods"]),
                              "declared_methods": tuple(group["declared_methods"])}
                             for group in _selection(focus)["groups"]),
            "module": MODULE, "scope": SCOPE}


def sources(focus: str) -> tuple[str, ...]:
    return tuple(_selection(focus)["test_sources"])


def selectors(focus: str) -> tuple[str, ...]:
    return tuple(group["classname"] + "." + method
                 for group in focus_spec(focus)["groups"] for method in group["methods"])


def native_request(focus: str) -> list[str]:
    return [TASK, *(argument for selector in selectors(focus) for argument in ("--tests", selector))]


def validate_request(task_names: list[str], focus: str) -> bool:
    if type(task_names) is not list or task_names != native_request(focus):
        raise ValueError("Related UI native execution requires only its exact ordered ten/four selectors")
    return True


def runtime_focus(focus: str) -> str:
    return _selection(focus)["runtime_focus"]


def init_script(focus: str) -> str:
    return _selection(focus)["init_script"]


def focus_property(focus: str) -> str:
    return _selection(focus)["focus_property"]


def identities(focus: str) -> list[dict]:
    return [{"classname": TASK_NAME + "." + group["classname"],
             "name": method + "[iosSimulatorArm64]"}
            for group in focus_spec(focus)["groups"] for method in group["methods"]]


def validate_sources(root: Path, focus: str, test_sources: list[str] | None = None) -> bool:
    wanted = sources(focus)
    if test_sources is not None and (type(test_sources) is not list or test_sources != sorted(wanted)):
        raise ValueError("Related UI requires its exact ordinary eleven/six source list, not a superset")
    text = {name: _ordinary_bytes(root, name)[0].decode("utf-8") for name in wanted}
    # Reuse the unchanged actual-UIDevice branch checker; do not replay its old controls.
    adaptive.validate_sources(root, list(wanted))
    for group in focus_spec(focus)["groups"]:
        source = text[group["source"]]
        package, classname = group["classname"].rsplit(".", 1)
        if (_METHOD.findall(source) != list(group["declared_methods"]) or _DISABLED.search(source) or
                not re.search(r"(?m)^package " + re.escape(package) + r"\s*$", source) or
                not re.search(r"\bclass\s+" + re.escape(classname) + r"\s*\{", source)):
            raise ValueError("Related UI must retain every exact enabled authored declaration")
        if group["source"] not in adaptive.SOURCES:
            for method in group["methods"]:
                if re.search(r"@Test\s+fun\s+" + re.escape(method) +
                             r"\s*\(\s*\)\s*\{\s*requireUiDragShaderApplication\(\)", source) is None:
                    raise ValueError("Each real drag/shader method must require the owned Main application")
    declaring = {group["source"] for group in focus_spec(focus)["groups"]}
    if any(re.search(r"@(Test|Ignore|Disabled|IgnoredTest)\b", text[name]) for name in set(wanted) - declaring):
        raise ValueError("Related UI ownership/cancellation/resource helpers must be zero-test ordinary inputs")
    drag_host = adaptive.BASE + "utils/UiDragShaderTestHost.kt"
    if drag_host in text and "onApplicationMain { requireOwnedApplicationWindow(); Unit }" not in text[drag_host]:
        raise ValueError("Drag/shader admission must require the real owned application window on Main")
    for name in wanted:
        if hashlib.sha256(text[name].encode()).hexdigest() != SOURCE_SHA256[name]:
            raise ValueError("Related UI authored source differs from its unchanged reviewed input: " + name)
    if hashlib.sha256(_ordinary_bytes(root, init_script(focus))[0]).hexdigest() != INIT_SHA256[focus]:
        raise ValueError("Related UI native-only init differs from its exact reviewed source admission")
    return True


def _contract(focus: str) -> dict:
    return {"schema_version": 1, "focus": focus, "runtime_focus": runtime_focus(focus),
            "module": MODULE, "task": TASK, "init_script": init_script(focus),
            "focus_property": focus_property(focus), "init_sha256": INIT_SHA256[focus],
            "selected_methods": list(selectors(focus)), "effective_sources": list(sources(focus)),
            "common_sources": [], "source_sha256": {name: SOURCE_SHA256[name] for name in sources(focus)},
            "compiler_executions_attested": 0, "apple_links_attested": 0, "native_tests_executed": 0}


def source_contract(root: Path, focus: str) -> dict:
    validate_sources(root, focus)
    return _contract(focus)


def validate_plan(test_plan: dict) -> bool:
    if type(test_plan) is not dict:
        raise ValueError("An exact finite related UI library plan is required")
    focus = test_plan.get("explicit_test_focus")
    wanted = _contract(focus)
    expected = test_plan.get("expected")
    if (test_plan.get("suite") != "ios" or test_plan.get("explicit_module_subset") != [MODULE] or
            test_plan.get("complete_suite_requested") is not False or type(expected) is not list or len(expected) != 1):
        raise ValueError("Related UI requires one explicit finite iOS calf-ui application module")
    item = expected[0]
    if (type(item) is not dict or item.get("module") != MODULE or item.get("project") != ":calf-ui" or
            item.get("task") != TASK or item.get("report_directory") != "calf-ui/build/test-results/" + TASK_NAME or
            item.get("native_test_host") != "genuine-uikit-application" or item.get("test_source_sets") != ["iosTest"] or
            item.get("test_source_files") != sorted(sources(focus)) or
            item.get("test_filter") != ",".join(selectors(focus)) or item.get("required_testcases") != identities(focus) or
            item.get("ui_related_source_contract") != wanted or
            type(item["ui_related_source_contract"].get("schema_version")) is not int or
            any(type(item["ui_related_source_contract"].get(key)) is not int
                for key in ("compiler_executions_attested", "apple_links_attested", "native_tests_executed"))):
        raise ValueError("Related UI source/task/module/focus/hash admission must equal its exact native plan")
    return True


def validate_context(context: dict, focus: str, *, udid: str) -> bool:
    if type(context) is not dict or context.get("adaptive_runtime_focus") != runtime_focus(focus):
        raise ValueError("Related UI requires its fresh mapped adaptive inventory capture marker")
    return adaptive_runtime.validate_context(context, runtime_focus(focus), udid=udid)


def admission_path(focus: str) -> str:
    _selection(focus)
    return ("build/ci-verification/adaptive-controls-native-source-admission.json" if focus == FOCUSES[0]
            else "build/ci-verification/ui-related-native-source-admission.json")


def _admission(focus: str) -> dict:
    result = {"task": TASK, "focus": focus, "selected_methods": list(selectors(focus)),
              "effective_sources": list(sources(focus)),
              "source_sha256": {name: SOURCE_SHA256[name] for name in sources(focus)},
              "excluded_unrelated_test_sources": True, "production_source_sets_changed": False,
              "compiler_executions_attested": 0, "apple_links_attested": 0, "native_tests_executed": 0,
              "scope": "Source/selection admission only; original fresh native XML/runtime/cleanup decide results"}
    if focus == FOCUSES[1]:
        result["common_sources"] = []
    return result


def validate_admission(root: Path, started_ns: int, ended_ns: int, focus: str) -> bool:
    if type(started_ns) is not int or type(ended_ns) is not int or started_ns <= 0 or ended_ns < started_ns:
        return False
    try:
        expected = _admission(focus)
        raw, info = _ordinary_bytes(root, admission_path(focus))
        if not started_ns - 2_000_000_000 <= info.st_mtime_ns <= ended_ns + 2_000_000_000:
            return False
        source_contract(root, focus)
        document = json.loads(raw, object_pairs_hook=_unique_object,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite source admission")))
        return (type(document) is dict and document == expected and
                all(type(document.get(key)) is int for key in
                    ("compiler_executions_attested", "apple_links_attested", "native_tests_executed")) and
                type(document.get("excluded_unrelated_test_sources")) is bool and
                type(document.get("production_source_sets_changed")) is bool)
    except (OSError, ValueError, UnicodeError, TypeError, RecursionError):
        return False


def _cases_shape(cases) -> bool:
    return type(cases) is list and all(type(case) is dict and
        all(type(case.get(key)) is str for key in ("classname", "name", "status")) for case in cases)


def outcomes(cases: list[dict], system: str, focus: str, *,
             cases_by_report: list[list[dict]] | None = None) -> tuple[list[dict], list[str]]:
    """Model acceptance policy only; actual owning XML/Worker/runtime/cleanup decide results."""
    expected = identities(focus)
    wanted = Counter((item["classname"], item["name"]) for item in expected)
    host_ok = type(system) is str and system.lower() in {"darwin", "macos", "mac os x"}
    errors = [] if host_ok else ["Related UI requires actual Apple-host application execution"]
    valid = _cases_shape(cases)
    actual = Counter((case["classname"], case["name"]) for case in cases) if valid else Counter()
    reports_ok = (type(cases_by_report) is list and all(_cases_shape(report) and report
                  for report in cases_by_report))
    if reports_ok:
        report_classes = [frozenset(case["classname"] for case in report) for report in cases_by_report]
        reports_ok = (Counter(report_classes) == Counter(frozenset((classname,)) for classname in {name for name, _ in wanted}) and
                      Counter((case["classname"], case["name"], case["status"])
                              for report in cases_by_report for case in report) ==
                      Counter((case["classname"], case["name"], case["status"]) for case in cases)) if valid else False
    exact = valid and actual == wanted and reports_ok
    if not exact:
        errors.append("Related UI XML must contain exactly ten/four selected methods and one fresh report per class")
    source_by_class = {TASK_NAME + "." + group["classname"]: group["source"]
                       for group in focus_spec(focus)["groups"]}
    scenarios = []
    for item in expected:
        matching = [case for case in cases if (case["classname"], case["name"]) ==
                    (item["classname"], item["name"])] if valid else []
        passed = exact and host_ok and len(matching) == 1 and matching[0]["status"] == "passed"
        if not passed:
            errors.append("Related UI native method must pass exactly once: " + item["name"])
        scenarios.append({**item, "source": source_by_class[item["classname"]], "task": TASK_NAME,
                          "target": "iosSimulatorArm64", "actual_os_branch_required": adaptive_runtime.branch(runtime_focus(focus)),
                          "required_on_host": True,
                          "disposition": "required-executed" if passed else "required-not-passed"})
    return scenarios, errors
