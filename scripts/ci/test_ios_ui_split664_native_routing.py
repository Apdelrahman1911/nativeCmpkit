# SPDX-License-Identifier: Apache-2.0
"""Exactly NEW16 UI664 source/routing/receipt models; never Apple/native evidence.

Every external process boundary is forbidden. Existing fixtures are definitions
only: no old test body, reconstructed historical code or accepted population is
executed. Explicit synthetic SDK/runtime/Mach-O/XML records stay tooling models.
"""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

import ios_adaptive_controls_native_focus as adaptive
import ios_ui_application as application
import ios_ui_related_native_focus as related
import ios_ui_related_source_projection as old_ui
import ios_ui_split664_source_projection as split
import library_tests as library
import platform_recovery659_source_projection as prior
import webview_current_contract667_source_projection as contract
import webview_content_policy_source_projection as content
import workflow_matrix as workflow
from test_ios_application_receipts import IosApplicationReceipts
from test_ios_ui_application import OwnedApplicationTests
from test_ios_ui_related_native_wiring import NEW_UUID, PRE_UUID, synthetic_context

ROOT = Path(__file__).resolve().parents[2]
PROFILES = ("ios-ui-related-nine-ios26plus", "ios-ui-adaptive-customization-ios26plus")
TASKS = (":calf-ui:iosSimulatorArm64UiNineApplicationTest",
         ":calf-ui:iosSimulatorArm64AdaptiveCustomizationApplicationTest")
CHILDREN = ("native-ui-nine-application", "native-adaptive-customization-application")
CUSTOM = adaptive.CUSTOM_SOURCE
CURRENT_CUSTOM = "b58eafaa3f097de27d0e8babe1059ce818fca903d954a77cdbd2a4c1a73252b9"
OLD_CUSTOM = "c792203a97cc8bdea914856b5cd53195f7a623170820fbc3f91a4ef9fd55d61d"
SEALED667 = "56574379b6d9621e8b72009cad3551115401b860250f5c40af23bf3be279f937"
SEALED659 = "c9a56d4288e1d6a71914de27b0218d0877840136e9d24d448e2d192fcf7d90e9"
SEALED_OWNER = "52e9d31c624e3bfbeab6d02fb7c5f97d1b196fb8fbaefe85be86a87587569837"
SEALED_PRIOR_GUARD = "4505c503a7cf2b354e7d18dbf9129a43071ffc9a0fbb8e2093dfbca8f179960a"
SEALED_COMPANION = "d59f9fe5c3d0352f012f9655a70877bf3cea00410b2c76a72d9e2cc92b646ced"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def copy_inputs(root, *, complete=True):
    names = (split.fixture_inputs() if complete else set(related.sources(related.FOCUSES[1])) |
             {related.init_script(focus) for focus in related.ALL_FOCUSES})
    for name in names:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())


def model_plan(focus):
    return {"schema_version": 1, "suite": "ios", "explicit_module_subset": ["calf-ui"],
            "explicit_test_focus": focus, "complete_suite_requested": False,
            "expected": [{"module": "calf-ui", "project": ":calf-ui", "task": related.task(focus),
                          "report_directory": "calf-ui/build/test-results/" + related.task_name(focus),
                          "native_test_host": "genuine-uikit-application", "test_source_sets": ["iosTest"],
                          "test_source_files": sorted(related.sources(focus)),
                          "test_filter": ",".join(related.selectors(focus)),
                          "required_testcases": related.identities(focus),
                          "ui_related_source_contract": related.source_contract(ROOT, focus)}]}


def model_cases(focus):
    cases = [{**item, "status": "passed"} for item in related.identities(focus)]
    classes = dict.fromkeys(case["classname"] for case in cases)
    return cases, [[case for case in cases if case["classname"] == classname] for classname in classes]


def accounting(focus):
    return {"transport_timeout_seconds": 1920 if focus == related.SPLIT_FOCUSES[0] else 600,
            "native_task_timeout_seconds": 2400}


def write_admission(root, focus):
    path = root / related.admission_path(focus)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(related._admission(focus)))
    stamp = time.time_ns(); os.utime(path, ns=(stamp, stamp))
    return path, stamp


def functions(raw):
    return {node.name: node for node in ast.parse(raw).body if isinstance(node, ast.FunctionDef)}


def dump(node):
    return ast.dump(node, include_attributes=False)


class UiSplit664SourceControls(unittest.TestCase):
    def setUp(self):
        for name in ("run", "Popen", "check_output", "check_call", "call"):
            guard = patch.object(subprocess, name, side_effect=AssertionError("Real external process forbidden in UI664 source models"))
            guard.start(); self.addCleanup(guard.stop)
        guard = patch.object(os, "system", side_effect=AssertionError("Real shell forbidden in UI664 source models"))
        guard.start(); self.addCleanup(guard.stop)

    def receipt_fixture(self, focus):
        # Reuse only an explicit synthetic fixture definition, never its tests.
        fixture = IosApplicationReceipts(); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        copy_inputs(fixture.root)
        # The unchanged module build discovers this single external helper before
        # the exact split init/plan excludes all other tests. Copy source only.
        helper = library.secure_alert.HELPER
        target = fixture.root / helper; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / helper).read_bytes())
        fixture.plan = library.plan(fixture.root, "ios", only_modules=("calf-ui",), focus=focus)
        context = synthetic_context(focus, NEW_UUID)
        context.update({key: fixture.context[key] for key in ("java", "rust", "xcode", "apple_sdks")})
        fixture.context = context
        fixture.document.update(task=related.task(focus), explicit_test_focus=focus,
                                runtime_before=copy.deepcopy(context), runtime_after=copy.deepcopy(context),
                                ui_split_timeout_accounting=accounting(focus),
                                application_transport={"timeout_seconds": accounting(focus)["transport_timeout_seconds"]})
        for key in ("system_appearance_driver", "image_memory_profile"):
            fixture.document.pop(key, None)
        fixture.cases = [{"classname": group["classname"], "name": method, "status": "passed"}
                         for group in related.focus_spec(focus)["groups"] for method in group["methods"]]
        protocol = fixture.document["application_protocol"]
        protocol.update(testcases=copy.deepcopy(fixture.cases), counts=library.case_counts(fixture.cases))
        for key in ("image_lifetime_observation", "image_profile_observations", "system_appearance_observations"):
            protocol.pop(key, None)
        xml, _ = model_cases(focus)
        fixture.modules = [{"module": "calf-ui", "task": related.task(focus), "testcases": xml}]
        fixture.app_root = fixture.output / related.receipt_subdirectory(focus)
        fixture.receipt_path = fixture.app_root / ("b" * 32) / "receipt.json"
        fixture.save(); write_admission(fixture.root, focus)
        return fixture

    def test_nine_and_one_partition_the_unchanged_ten_without_pre26_or_accepted_methods(self):
        self.assertEqual(("ui-native-adaptive-pre26", "ui-native-adaptive-drag-shader-ios26plus"), related.FOCUSES)
        nine, one = (related.selectors(focus) for focus in related.SPLIT_FOCUSES)
        ten = related.selectors(related.FOCUSES[1]); pre = related.selectors(related.FOCUSES[0])
        self.assertEqual((9, 1, 10, 4), tuple(map(len, (nine, one, ten, pre))))
        self.assertEqual({CUSTOM}, {group["source"] for group in related.focus_spec(related.SPLIT_FOCUSES[1])["groups"]})
        self.assertEqual("com.mohamedrejeb.calf.ui.controls.AdaptiveControlCustomizationMatrixTest.ios26CustomColorsContentAndInteractionsSurviveDarkAndLargeText", one[0])
        self.assertFalse(set(nine) & set(one)); self.assertEqual(set(ten), set(nine) | set(one))
        self.assertFalse(set(pre) & (set(nine) | set(one)))
        before = functions(split.source_before_ui_split664("scripts/ci/ios_ui_related_native_focus.py",
                            (ROOT / "scripts/ci/ios_ui_related_native_focus.py").read_bytes()))
        source = (ROOT / "scripts/ci/ios_ui_related_native_focus.py").read_bytes()
        tree = ast.parse(source)
        old_tree = ast.parse(split.source_before_ui_split664("scripts/ci/ios_ui_related_native_focus.py", source))
        def literal(tree, name):
            return next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == name for t in node.targets))
        for name in ("FOCUSES", "SOURCE_SHA256"):
            self.assertEqual(literal(old_tree, name), literal(tree, name))
        self.assertEqual(OLD_CUSTOM, related.SOURCE_SHA256[CUSTOM])
        self.assertEqual({focus: related.INIT_SHA256[focus] for focus in related.FOCUSES}, literal(old_tree, "INIT_SHA256"))
        self.assertIn("native_request", before)  # Parsed predecessor only; never executed.

    def test_split_profiles_are_literal_independent_iphone_rows_and_wrong_hosts_refuse(self):
        tree = ast.parse((ROOT / "scripts/ci/workflow_matrix.py").read_bytes())
        definitions = {target.id: node.value for node in tree.body if isinstance(node, ast.Assign)
                       for target in node.targets if isinstance(target, ast.Name) and target.id in {"PROFILES", "MODULE_SUBSETS"}}
        for profile, focus in zip(PROFILES, related.SPLIT_FOCUSES):
            for name, wanted in (("PROFILES", ("ios-iphone",)), ("MODULE_SUBSETS", "calf-ui")):
                node = definitions[name]
                value = next(value for key, value in zip(node.keys, node.values)
                             if isinstance(key, ast.Constant) and key.value == profile)
                self.assertEqual(wanted, ast.literal_eval(value))
            row = {"slot": "ios-iphone", "suite": "ios", "runner": "macos-26", "arch": "arm64", "python": "python3",
                   "simulator-kind": "iphone", "test-modules": "calf-ui", "test-focus": focus}
            self.assertEqual({"include": [row]}, workflow.matrix(profile))
            for field, bad in (("runner", "macos-15"), ("arch", "x64"), ("python", "python"),
                               ("suite", "desktop"), ("simulator-kind", "ipad"), ("unknown", "extra")):
                slots = copy.deepcopy(workflow.SLOTS)
                for slot in slots:
                    if slot["slot"] == "ios-iphone": slot[field] = bad
                with patch.object(workflow, "SLOTS", slots), self.assertRaises(ValueError): workflow.matrix(profile)
            with patch.dict(workflow.PROFILES, {profile: ("ios-iphone", "ios-ipad")}), self.assertRaises(ValueError):
                workflow.matrix(profile)
            with patch.dict(workflow.MODULE_SUBSETS, {profile: "calf-share"}), self.assertRaises(ValueError): workflow.matrix(profile)

    def test_split_native_plans_requests_tasks_reports_and_hashes_are_exact(self):
        for focus, task, child, count in zip(related.SPLIT_FOCUSES, TASKS, CHILDREN, (9, 1)):
            plan = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=focus)
            self.assertTrue(library.validate_test_focus(plan)); self.assertTrue(related.validate_plan(plan))
            item = plan["expected"][0]; self.assertEqual(task, item["task"])
            self.assertEqual("calf-ui/build/test-results/" + task.rsplit(":", 1)[1], item["report_directory"])
            self.assertEqual(related.identities(focus), item["required_testcases"])
            self.assertEqual(count, len(item["required_testcases"]))
            source = item["ui_related_source_contract"]
            self.assertEqual(child, source["receipt_subdirectory"])
            self.assertEqual(accounting(focus), {key: source[key] for key in accounting(focus)})
            self.assertEqual({name: sha((ROOT / name).read_bytes()) for name in related.sources(focus)}, source["source_sha256"])
            self.assertEqual(sha((ROOT / source["init_script"]).read_bytes()), source["init_sha256"])
            command = library.gradle_command("ios", plan, NEW_UUID, root=ROOT)
            self.assertEqual(related.native_request(focus), command[command.index(task):])
            self.assertIn("-PnativecmpkitUiSplitFocus=" + focus, command)
            self.assertIn("-PnativecmpkitSimulatorDevice=" + NEW_UUID, command)
            self.assertIn("scripts/ci/ios_ui_split_native.init.gradle.kts", command)
            self.assertNotIn(related.TASK, command); self.assertNotIn(TASKS[1 if task == TASKS[0] else 0], command)
            self.assertNotIn("scripts/ci/ui_drag_shader_compile.init.gradle.kts", command)

    def test_split_plan_and_request_broadening_cross_task_old_prefix_and_boolean_budgets_refuse(self):
        for focus in related.SPLIT_FOCUSES:
            plan = model_plan(focus); request = related.native_request(focus)
            other = related.SPLIT_FOCUSES[1 if focus == related.SPLIT_FOCUSES[0] else 0]
            for bad in (request[:-2], request + request[-2:], tuple(request), [related.TASK, *request[1:]],
                        [related.task(other), *request[1:]], request + ["publish"], request + [":calf-ui:compileTestKotlinIosSimulatorArm64"],
                        [request[0], "--tests", "*"]):
                with self.assertRaises(ValueError): related.validate_request(bad, focus)
            for key, value in (("task", related.TASK), ("report_directory", "calf-ui/build/test-results/" + related.TASK_NAME),
                               ("required_testcases", related.identities(other)), ("test_filter", "*"),
                               ("test_source_files", sorted(set(related.sources(focus)) | {CUSTOM})),
                               ("native_test_host", "skiko")):
                if key == "test_source_files" and value == plan["expected"][0][key]: value = value + ["foreign.kt"]
                changed = copy.deepcopy(plan); changed["expected"][0][key] = value
                with self.assertRaises(ValueError): library.validate_test_focus(changed)
            for key, value in (("transport_timeout_seconds", True), ("native_task_timeout_seconds", False),
                               ("receipt_subdirectory", related.receipt_subdirectory(other)),
                               ("native_tests_executed", False), ("common_sources", ["foreign.kt"])):
                changed = copy.deepcopy(plan); changed["expected"][0]["ui_related_source_contract"][key] = value
                with self.assertRaises(ValueError): related.validate_plan(changed)
            for selectors in (related.selectors(focus), tuple(reversed(related.selectors(focus)))):
                args = [*sorted(application.TEST_ARGUMENTS), "--ktest_gradle_filter=" + ",".join(selectors)]
                self.assertEqual(focus, application.application_test_focus(args))
            for selectors in (related.selectors(focus) + related.selectors(other), related.selectors(focus) * 2, ("*",)):
                args = [*sorted(application.TEST_ARGUMENTS), "--ktest_gradle_filter=" + ",".join(selectors)]
                if set(selectors) == set(related.selectors(related.FOCUSES[1])):
                    self.assertEqual(related.FOCUSES[1], application.application_test_focus(args))
                    self.assertNotEqual(focus, application.application_test_focus(args))
                else:
                    with self.assertRaises(ValueError): application.application_test_focus(args)

    def test_only_actual_ios26plus_inventory_and_exact_uuid_context_can_admit_each_split(self):
        for focus in related.SPLIT_FOCUSES:
            context = synthetic_context(focus, NEW_UUID)
            self.assertTrue(related.validate_context(context, focus, udid=NEW_UUID))
            self.assertEqual("ui-native-adaptive-ios26plus", context["adaptive_runtime_focus"])
            self.assertEqual("26.4.1", context["simulator"]["runtime_version"])
            for key, value in (("adaptive_runtime_focus", related.FOCUSES[0]), ("source_tree_dirty", True)):
                changed = copy.deepcopy(context); changed[key] = value
                with self.assertRaises(ValueError): related.validate_context(changed, focus, udid=NEW_UUID)
            for key, value in (("udid", PRE_UUID), ("runtime_version", "18.0"), ("state", "Shutdown"),
                               ("device_type", "com.apple.CoreSimulator.SimDeviceType.iPad-Pro")):
                changed = copy.deepcopy(context); changed["simulator"][key] = value
                with self.assertRaises(ValueError): related.validate_context(changed, focus, udid=NEW_UUID)
            with self.assertRaises(ValueError): related.validate_context(context, focus, udid=PRE_UUID)
            source = (ROOT / "scripts/ci/ios_ui_application.py").read_bytes()
            calls = [node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Call)
                     and ast.unparse(node.func) == "runtime.capture" and any(keyword.arg is None for keyword in node.keywords)]
            self.assertEqual(2, len(calls))
            self.assertTrue(all("lt.ui_related.ALL_FOCUSES" in ast.unparse(node) for node in calls))
            self.assertIn('for when in ("runtime_before", "runtime_after"):', (ROOT / "scripts/ci/library_tests.py").read_text())

    def test_split_source_sets_skip_only_the_other_group_and_current_ui609_exact_derivative_is_bound(self):
        nine, one = related.SPLIT_FOCUSES
        self.assertEqual((10, 4), tuple(len(related.sources(focus)) for focus in (nine, one)))
        self.assertNotIn(CUSTOM, related.sources(nine)); self.assertIn(CUSTOM, related.sources(one))
        self.assertEqual(set(related.sources(related.FOCUSES[1])) - {CUSTOM}, set(related.sources(nine)))
        self.assertEqual({adaptive.BRANCH_SOURCE, CUSTOM, adaptive.HOST_SOURCE, adaptive.IDENTITY_SOURCE}, set(related.sources(one)))
        current = (ROOT / CUSTOM).read_bytes(); before = split.current_source_before_ui_split664(CUSTOM, current)
        self.assertEqual((CURRENT_CUSTOM, OLD_CUSTOM), (sha(current), sha(before)))
        self.assertEqual(16, len(split._document()["bindings"][CUSTOM]["fragments"]))
        for focus in (nine, one):
            self.assertTrue(related.validate_sources(ROOT, focus, sorted(related.sources(focus))))
            self.assertEqual([], related.source_contract(ROOT, focus)["common_sources"])
            with self.assertRaises(ValueError): related.validate_sources(ROOT, focus, sorted(related.sources(focus)) + ["foreign.kt"])
        for marker in ("durationMillis = 240", "waitForIdle()", "waitUntil"):
            self.assertEqual(before.count(marker.encode()), current.count(marker.encode()))
        self.assertEqual(re.findall(rb"\b(assert[A-Z]\w*)\s*\(", before), re.findall(rb"\b(assert[A-Z]\w*)\s*\(", current))
        self.assertEqual(3, current.count(b"screenshot.asSkiaBitmap().close()"))
        self.assertEqual(3, current.count(b"} finally {\n            screenshot.asSkiaBitmap().close()"))

    def test_separate_fresh_source_admissions_reject_cross_paths_hashes_budgets_and_stale_aliases(self):
        for focus in related.SPLIT_FOCUSES:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); copy_inputs(root, complete=False); path, stamp = write_admission(root, focus)
                self.assertTrue(related.validate_admission(root, stamp, stamp, focus))
                original = path.read_bytes(); other = related.SPLIT_FOCUSES[1 if focus == related.SPLIT_FOCUSES[0] else 0]
                self.assertFalse(related.validate_admission(root, stamp, stamp, other))
                document = json.loads(original)
                for key, value in (("task", related.task(other)), ("focus", other), ("source_sha256", {}),
                                   ("receipt_subdirectory", related.receipt_subdirectory(other)),
                                   ("transport_timeout_seconds", True), ("native_task_timeout_seconds", 600),
                                   ("compiler_executions_attested", False), ("native_tests_executed", 1)):
                    changed = copy.deepcopy(document); changed[key] = value; path.write_text(json.dumps(changed))
                    self.assertFalse(related.validate_admission(root, stamp, time.time_ns(), focus), key)
                path.write_bytes(original)
                for stale in (stamp - 3_000_000_000, stamp + 3_000_000_000):
                    os.utime(path, ns=(stale, stale)); self.assertFalse(related.validate_admission(root, stamp, stamp, focus))
                os.utime(path, ns=(stamp, stamp)); path.unlink(); backing = path.with_name("admission-backing.json"); backing.write_bytes(original)
                for link in ("symlink", "hardlink"):
                    path.symlink_to(backing) if link == "symlink" else path.hardlink_to(backing)
                    self.assertFalse(related.validate_admission(root, stamp, time.time_ns(), focus)); path.unlink()
                path.write_bytes(original)
                for raw in (original[:-1] + b',"task":"duplicate"}', b'{"unexpected":NaN}', b"{}", b""):
                    path.write_bytes(raw); self.assertFalse(related.validate_admission(root, stamp, time.time_ns(), focus))

    def test_task_specific_xml_reports_cannot_accept_the_other_split_or_legacy_ten_or_any_duplicate_skip(self):
        for focus in related.SPLIT_FOCUSES:
            cases, reports = model_cases(focus)
            scenarios, errors = related.outcomes(cases, "Darwin", focus, cases_by_report=reports)
            self.assertEqual([], errors); self.assertTrue(all(row["disposition"] == "required-executed" for row in scenarios))
            self.assertEqual({related.task_name(focus)}, {row["task"] for row in scenarios})
            for bad_focus in (*related.FOCUSES, *[other for other in related.SPLIT_FOCUSES if other != focus]):
                wrong, wrong_reports = model_cases(bad_focus)
                self.assertTrue(related.outcomes(wrong, "Darwin", focus, cases_by_report=wrong_reports)[1])
            for wrong, wrong_reports in ((cases[:-1], reports), (cases + cases[:1], reports), (cases, reports + reports[:1]),
                                         (cases, []), (cases, None)):
                self.assertTrue(related.outcomes(wrong, "Darwin", focus, cases_by_report=wrong_reports)[1])
            for status in ("failed", "error", "skipped", "unknown"):
                changed = copy.deepcopy(cases); changed[0]["status"] = status
                changed_reports = [[case for case in changed if case["classname"] == report[0]["classname"]] for report in reports]
                rows, errors = related.outcomes(changed, "Darwin", focus, cases_by_report=changed_reports)
                self.assertTrue(errors); self.assertEqual("required-not-passed", rows[0]["disposition"])
            self.assertTrue(related.outcomes(cases, "Linux", focus, cases_by_report=reports)[1])

    def test_child_receipt_roots_are_independent_and_inherited_cross_roots_refuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); output = root / "build/ci-verification/model-ui664"
            values = []
            for focus, child in zip(related.SPLIT_FOCUSES, CHILDREN):
                plan = model_plan(focus)
                with patch.dict(os.environ, {}, clear=True):
                    before = dict(os.environ); environment = library.ios_application_environment(root, output, plan)
                    self.assertEqual(before, dict(os.environ))
                expected = "build/ci-verification/model-ui664/" + child
                self.assertEqual(expected, environment["NATIVECMPKIT_UIKIT_RESULT_ROOT"]); values.append(expected)
                for wrong in ("build/ci-verification/model-ui664/native-ui-application", "foreign", values[0] if len(values) == 2 else CHILDREN[1]):
                    if wrong == expected: continue
                    with patch.dict(os.environ, {"NATIVECMPKIT_UIKIT_RESULT_ROOT": wrong}), self.assertRaises(ValueError):
                        library.ios_application_environment(root, output, plan)
                host = application.application_host(application.EXPECTED_BINARY_DIRECTORY + "/application.kexe", focus)
                self.assertEqual((related.task(focus), child), (host["task"], host["receipt_subdirectory"]))
            self.assertNotEqual(*values)
        fixture = OwnedApplicationTests(); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        arguments = [*sorted(application.TEST_ARGUMENTS), "--ktest_gradle_filter=" + ",".join(related.selectors(related.SPLIT_FOCUSES[1]))]
        with patch.object(application, "execute_control", side_effect=AssertionError("Wrong receipt root reached an owned action")) as action:
            with self.assertRaises(ValueError): fixture.fixture_run(arguments=arguments)
            action.assert_not_called()

    def test_receipt_review_requires_exact_split_task_prefix_transport_budget_and_full_cleanup(self):
        for focus in related.SPLIT_FOCUSES:
            fixture = self.receipt_fixture(focus)
            result = fixture.collect(); self.assertEqual([], result["errors"])
            self.assertEqual(len(related.selectors(focus)), result["ios_applications"][0]["counts"]["executed"])
            original, original_modules = copy.deepcopy(fixture.document), copy.deepcopy(fixture.modules)
            for key, value in (("task", related.TASK), ("ui_split_timeout_accounting", accounting(related.SPLIT_FOCUSES[1 if focus == related.SPLIT_FOCUSES[0] else 0])),
                               ("application_transport", {"timeout_seconds": True}), ("application_transport", {"timeout_seconds": 1921}),
                               ("transport_passed", False)):
                fixture.document = copy.deepcopy(original); fixture.document[key] = value; fixture.save()
                self.assertTrue(fixture.collect()["errors"], key)
            for key in ("owned_app_identity_reverified", "owned_app_stopped_verified", "owned_app_absence_verified", "owned_local_bundle_removed"):
                fixture.document = copy.deepcopy(original); fixture.document["cleanup"][key] = False; fixture.save()
                self.assertTrue(fixture.collect()["errors"], key)
            fixture.document = copy.deepcopy(original); fixture.save()
            for prefix in (related.TASK_NAME, related.task_name(related.SPLIT_FOCUSES[1 if focus == related.SPLIT_FOCUSES[0] else 0])):
                fixture.modules = copy.deepcopy(original_modules)
                for case in fixture.modules[0]["testcases"]:
                    case["classname"] = prefix + "." + case["classname"].split(".", 1)[1]
                self.assertTrue(fixture.collect()["errors"])
            fixture.modules = copy.deepcopy(original_modules)
            fixture.modules[0]["testcases"] += fixture.modules[0]["testcases"][:1]
            self.assertTrue(fixture.collect()["errors"])

    def test_adaptive600_transport_timeout_remains_failure_with_original_owned_cleanup_and_no_inner_wait_changes(self):
        focus = related.SPLIT_FOCUSES[1]
        self.assertEqual(600, application.application_timeout_seconds(focus))
        self.assertEqual(1920, application.application_timeout_seconds(related.SPLIT_FOCUSES[0]))
        self.assertEqual([1920, 1920], [application.application_timeout_seconds(old) for old in related.FOCUSES])
        fixture = OwnedApplicationTests(); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        context = synthetic_context(focus, NEW_UUID)
        # The fake owned-control fixture's explicit device must match its inventory model.
        device = os.environ["NATIVECMPKIT_UIKIT_SIMULATOR"]
        context["simulator"]["udid"] = device
        observed = []
        def timeout(argv, protocol, *, timeout):
            observed.append(timeout)
            protocol.transport_observation = {"timeout_seconds": timeout, "error_type": "TimeoutError", "failure_stage": "protocol-read"}
            raise TimeoutError("Synthetic cooperative transport deadline; not a native hang diagnosis")
        arguments = [*sorted(application.TEST_ARGUMENTS), "--ktest_gradle_filter=" + ",".join(related.selectors(focus))]
        with patch.dict(os.environ, {"NATIVECMPKIT_UIKIT_RESULT_ROOT": "build/ci-verification/fixture/" + CHILDREN[1]}), \
                patch.object(application.crashes, "collect", return_value={"status": "unavailable", "native_functionality_verified": False}):
            result = fixture.fixture_run(arguments=arguments, contexts=[context, context], launch=timeout)
        self.assertEqual([600], observed); self.assertFalse(result["transport_passed"])
        self.assertEqual({"phase": "launch-and-real-test-transport", "type": "TimeoutError"}, result["error"])
        self.assertEqual(accounting(focus), result["ui_split_timeout_accounting"])
        self.assertEqual(600, result["application_transport"]["timeout_seconds"])
        self.assertTrue(result["cleanup"]["owned_app_identity_reverified"])
        self.assertTrue(result["cleanup"]["owned_app_absence_verified"]); self.assertTrue(result["cleanup"]["owned_local_bundle_removed"])
        self.assertFalse(fixture.installed.exists()); self.assertIn("application_protocol_partial", result)
        current = (ROOT / "scripts/ci/ios_ui_application.py").read_bytes()
        before = split.source_before_ui_split664("scripts/ci/ios_ui_application.py", current)
        def final_bodies(raw):
            return [dump(ast.Module(body=node.finalbody, type_ignores=[])) for node in ast.walk(functions(raw)["run"])
                    if isinstance(node, ast.Try) and node.finalbody]
        self.assertEqual(final_bodies(before), final_bodies(current))
        self.assertEqual(dump(functions(before)["forward_application"]), dump(functions(current)["forward_application"]))
        leaf = (ROOT / CUSTOM).read_bytes(); old = split.source_before_ui_split664(CUSTOM, leaf)
        self.assertEqual([line.strip() for line in old.splitlines() if b"waitForIdle" in line or b"waitUntil" in line or b"durationMillis" in line],
                         [line.strip() for line in leaf.splitlines() if b"waitForIdle" in line or b"waitUntil" in line or b"durationMillis" in line])

    def test_split_init_and_build_tasks_match_exact_compilations_and_independent_results_without_cross_dependencies(self):
        init = (ROOT / related.init_script(related.SPLIT_FOCUSES[0])).read_text()
        build = (ROOT / "calf-ui/build.gradle.kts").read_bytes()
        old = split.source_before_ui_split664("calf-ui/build.gradle.kts", build)
        original_start = old.index(b'        tasks.register<KotlinNativeHostTest>("iosSimulatorArm64ApplicationTest")')
        original_task = old[original_start:old.rfind(b"    }\n}")]
        self.assertIn(original_task, build)
        self.assertNotIn("import org.jetbrains.kotlin.gradle.targets.native.tasks.KotlinNativeHostTest", init)
        for focus, task, child in zip(related.SPLIT_FOCUSES, TASKS, CHILDREN):
            self.assertIn('"' + focus + '" to "' + task.rsplit(":", 1)[1] + '"', init)
            self.assertIn('"' + focus + '" to "' + child + '"', init)
            for selector in related.selectors(focus): self.assertIn('"' + selector + '"', init)
            self.assertIn('"' + focus + '" to ' + str(accounting(focus)["transport_timeout_seconds"]), init)
            for name in related.sources(focus): self.assertIn('"' + name + '"', init)
        self.assertEqual(1, init.count('common.setFrom(emptyList<Any>())'))
        self.assertIn('gradle.startParameter.taskNames == applicationRequest', init)
        self.assertIn('nativeTask.timeout.get() == Duration.ofSeconds(2400)', init)
        self.assertIn('"native_tests_executed" to 0', init)
        self.assertIn('"Mac OS X"', init); self.assertIn('setOf("aarch64", "arm64")', init)
        split_block = build[build.index(b"        val splitApplications = mapOf("):].decode()
        self.assertEqual(1, split_block.count("dependsOn(application.linkTaskProvider)"))
        self.assertEqual(1, split_block.count('test-results/$name/binary'))
        self.assertEqual(1, split_block.count('test-results/$name"'))
        self.assertNotRegex(split_block, r'dependsOn\([^\n]*(UiNine|AdaptiveCustomization|ApplicationTest)')
        self.assertIn('timeout.set(Duration.ofSeconds(2400))', split_block)
        self.assertIn('outputs.upToDateWhen { false }', split_block)

    def test_workflow_keeps_legacy_route_block_and_collects_only_the_two_new_receipts_admissions_and_exact_xml(self):
        current = (ROOT / ".github/workflows/gradle.yml").read_bytes()
        old = split.source_before_ui_split664(".github/workflows/gradle.yml", current)
        legacy = (b'            case "$TEST_FOCUS" in\n'
                  b'              ui-native-adaptive-pre26) args+=(--adaptive-focus ui-native-adaptive-pre26) ;;\n'
                  b'              ui-native-adaptive-drag-shader-ios26plus) args+=(--adaptive-focus ui-native-adaptive-ios26plus) ;;\n'
                  b'            esac\n')
        self.assertEqual((1, 1), (old.count(legacy), current.count(legacy)))
        for focus, child in zip(related.SPLIT_FOCUSES, CHILDREN):
            self.assertEqual(1, current.count((focus + ") args+=(--adaptive-focus ui-native-adaptive-ios26plus) ;;").encode()))
            self.assertEqual(1, current.count(("build/ci-verification/${{ matrix.slot }}/" + child + "/*/receipt.json").encode()))
            self.assertEqual(1, current.count(related.admission_path(focus).encode()))
        options = current.decode().split("options: [", 1)[1].split("]", 1)[0].split(", ")
        for profile in PROFILES: self.assertEqual(1, options.count(profile))
        self.assertIn(b"${{ steps.plan.outputs.reports }}", current)
        self.assertNotIn(b"test-results/iosSimulatorArm64*", current)
        self.assertIn(b'--timeout 4200', current)
        self.assertIn(b'cancel-in-progress: false', current)
        self.assertEqual(old.count(b"timeout-minutes:"), current.count(b"timeout-minutes:"))

    def test_complete_current_split_source_inverses_and_own_template_reject_prior_partial_foreign_and_link_drift(self):
        document = split._document(); self.assertEqual(9, len(document["bindings"]))
        from android_io_remote_routing_source_projection import source_before_remote_routing as qualified_io_ancestor
        for name, row in document["bindings"].items():
            current = (ROOT / name).read_bytes(); before = split.current_source_before_ui_split664(name, current)
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(before), len(before)))
            self.assertEqual(before, split.source_before_ui_split664(name, before))
            forward = before
            for fragment in row["fragments"]:
                left, right = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual((fragment["before_fragment_sha256"], fragment["after_fragment_sha256"]), (sha(left), sha(right)))
                self.assertEqual(1, forward.count(left)); forward = forward.replace(left, right, 1)
            self.assertEqual(qualified_io_ancestor(name, current), forward)
            for bad in (before, current + b"\n", current[:-1], b"foreign", b"", None, bytearray(current)):
                with self.assertRaises(ValueError): split.current_source_before_ui_split664(name, bad)
            unknown = before + b"\n# synthetic unreviewed ancestor\n"
            self.assertIs(unknown, split.peel_ui_split664_for_history(name, unknown))
            with self.assertRaises(ValueError): split.source_before_ui_split664(name, unknown)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); copy_inputs(root)
            target = root / split.SOURCE_RELATIVE; raw = target.read_bytes()
            for mode in ("drift", "missing", "symlink", "hardlink"):
                target.unlink(); backing = target.with_name("guard-backing.py")
                if mode == "drift": target.write_bytes(raw + b"\n")
                elif mode == "symlink": target.symlink_to(ROOT / split.SOURCE_RELATIVE)
                elif mode == "hardlink": backing.write_bytes(raw); target.hardlink_to(backing)
                with self.assertRaises((ValueError, OSError)): split._validate_own_guard(root, document)
                if target.exists() or target.is_symlink(): target.unlink()
                if backing.exists(): backing.unlink()
                target.write_bytes(raw)
            manifest = root / split.SPEC_RELATIVE; original = manifest.read_bytes()
            with patch.object(split, "SPEC_PATH", manifest):
                for payload in (original + b"\n", b"{}", b"", b"x" * (split.MAX_SPEC_BYTES + 1)):
                    manifest.write_bytes(payload)
                    with self.assertRaises(ValueError): split._document()
                changed = json.loads(original); changed["schema_version"] = True
                payload = json.dumps(changed).encode(); manifest.write_bytes(payload)
                with patch.object(split, "SPEC_SHA256", sha(payload)), self.assertRaises(ValueError): split._document()

    def test_one_newest_split_ingress_reaches_sealed667_and659_without_repinning_or_recursive_controller_calls(self):
        for name in split.BOUND_PATHS:
            current = (ROOT / name).read_bytes()
            with patch.object(split, "current_source_before_ui_split664", wraps=split.current_source_before_ui_split664) as ingress:
                prior.current_source_before_platform_recovery659(name, current)
                ingress.assert_called_once_with(name, current)
            self.assertEqual(split.source_before_ui_split664(name, current), contract.peel_contract667_for_history(name, current)
                             if name not in contract.BOUND_PATHS else contract.source_before_contract667(name, current))
        self.assertEqual(SEALED667, sha((ROOT / contract.SPEC_RELATIVE).read_bytes()))
        self.assertEqual(SEALED659, sha((ROOT / prior.SPEC_RELATIVE).read_bytes()))
        self.assertEqual(SEALED_PRIOR_GUARD, sha((ROOT / prior.SOURCE_RELATIVE).read_bytes()))
        self.assertEqual(SEALED_OWNER, sha((ROOT / contract.SOURCE).read_bytes()))
        source = (ROOT / split.SOURCE_RELATIVE).read_bytes()
        imports = [node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.ImportFrom)]
        self.assertEqual({"__future__", "pathlib", "ios_popover_anchor_plan"}, {node.module for node in imports})
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"exec", "eval", "compile"}
                             for node in ast.walk(ast.parse(source))))
        raw_guard = (ROOT / contract.SOURCE_RELATIVE).read_bytes()
        self.assertEqual(SEALED_COMPANION, sha(split.current_source_before_ui_split664(contract.SOURCE_RELATIVE, raw_guard)))
        self.assertEqual(sha(raw_guard), contract._validate_own_guard(ROOT, contract._qualified_document()))
        self.assertNotEqual(SEALED_COMPANION, contract.current_contract_hashes()[contract.SOURCE_RELATIVE])
        self.assertEqual(sha(raw_guard), contract.current_contract_hashes()[contract.SOURCE_RELATIVE])

    def test_latest_raw_validator_and_fixture_union_hold_native_bodies_original_failures_and_unchanged_667_contract(self):
        self.assertTrue(split.validate_current_sources(ROOT)); self.assertTrue(contract.validate_current_sources(ROOT))
        self.assertTrue(prior.validate_current_sources(ROOT))
        self.assertEqual(split.fixture_inputs(), set(split.current_input_hashes()))
        self.assertTrue(split.fixture_inputs() <= contract.fixture_inputs())
        self.assertTrue(split.fixture_inputs() <= prior.fixture_inputs())
        self.assertEqual(contract.contract_input_paths(), set(contract.current_contract_hashes()))
        self.assertNotIn("AGENTS.md", split.fixture_inputs())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); copy_inputs(root); (root / "AGENTS.md").write_text("Unrelated synthetic maintainer prose is not a UI664 input.\n")
            self.assertTrue(split.validate_current_sources(root))
            for name in (related.sources(related.SPLIT_FOCUSES[0])[-1], related.sources(related.SPLIT_FOCUSES[1])[0],
                         related.init_script(related.SPLIT_FOCUSES[0]), contract.SOURCE_RELATIVE):
                path = root / name; current = path.read_bytes(); path.write_bytes(current + b"\n")
                with self.assertRaises(ValueError): split.validate_current_sources(root)
                path.write_bytes(current)
        old_test_path = "scripts/ci/test_ios_ui_related_source_projection.py"
        current = (ROOT / old_test_path).read_bytes(); before = split.source_before_ui_split664(old_test_path, current)
        def test_nodes(raw):
            return {node.name: node for node in ast.walk(ast.parse(raw)) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
        old_nodes, new_nodes = test_nodes(before), test_nodes(current)
        changed = {"test_original_application_launch_argv_deadlines_finally_sdk_and_native_bodies_are_unchanged",
                   "test_camera_bridge_175c_and_runtime620_inputs_are_not_edited_or_replayed"}
        self.assertEqual(set(old_nodes), set(new_nodes))
        for name in set(old_nodes) - changed: self.assertEqual(dump(old_nodes[name]), dump(new_nodes[name]))
        for name in changed:
            def assertions(node):
                return [child.func.attr for child in ast.walk(node) if isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Attribute) and child.func.attr.startswith("assert")]
            self.assertEqual(assertions(old_nodes[name]), assertions(new_nodes[name]))
        self.assertEqual(SEALED667, contract.SPEC_SHA256); self.assertEqual(SEALED659, prior.SPEC_SHA256)
        self.assertEqual(OLD_CUSTOM, related.SOURCE_SHA256[CUSTOM])
        # Neither source custody nor a passing synthetic model supplies native outcomes.
        for focus in related.ALL_FOCUSES:
            self.assertEqual([0, 0, 0], [related.source_contract(ROOT, focus)[key]
                                      for key in ("compiler_executions_attested", "apple_links_attested", "native_tests_executed")])


if __name__ == "__main__":
    unittest.main()
