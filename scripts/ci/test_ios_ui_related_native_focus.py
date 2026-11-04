# SPDX-License-Identifier: Apache-2.0
"""NEW related native selection/source/XML models only; no native or old controls."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
import unittest

import ios_adaptive_controls_native_focus as adaptive
import ios_ui_related_native_focus as related

ROOT = Path(__file__).resolve().parents[2]


def copy_sources(root):
    names = set(related.sources(related.FOCUSES[1])) | {related.init_script(focus) for focus in related.FOCUSES}
    for name in names:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())


def model_cases(focus):
    cases = [{**item, "status": "passed"} for item in related.identities(focus)]
    classes = dict.fromkeys(case["classname"] for case in cases)
    return cases, [[case for case in cases if case["classname"] == classname] for classname in classes]


def model_plan(focus):
    return {"schema_version": 1, "suite": "ios", "explicit_module_subset": ["calf-ui"],
            "explicit_test_focus": focus, "complete_suite_requested": False,
            "expected": [{"module": "calf-ui", "project": ":calf-ui", "task": related.TASK,
                          "report_directory": "calf-ui/build/test-results/" + related.TASK_NAME,
                          "native_test_host": "genuine-uikit-application", "test_source_sets": ["iosTest"],
                          "test_source_files": sorted(related.sources(focus)),
                          "test_filter": ",".join(related.selectors(focus)),
                          "required_testcases": related.identities(focus),
                          "ui_related_source_contract": related.source_contract(ROOT, focus)}]}


class RelatedUiNativeSpecificationControls(unittest.TestCase):
    def test_only_combined_ten_and_independent_pre26_four_are_registered(self):
        self.assertEqual(("ui-native-adaptive-pre26", "ui-native-adaptive-drag-shader-ios26plus"), related.FOCUSES)
        self.assertEqual([4, 10], [len(related.selectors(focus)) for focus in related.FOCUSES])
        self.assertEqual([3, 6], [len(related.focus_spec(focus)["groups"]) for focus in related.FOCUSES])
        for bad in (None, True, "ui-native-adaptive-ios26plus", "ios-ui", "all"):
            with self.assertRaises(ValueError): related.focus_spec(bad)

    def test_exact_union_eleven_and_pre26_six_keep_all_real_branch_declarations(self):
        self.assertEqual(adaptive.SOURCES, related.sources(related.FOCUSES[0]))
        union = related.sources(related.FOCUSES[1])
        self.assertEqual(11, len(union)); self.assertEqual(11, len(set(union)))
        self.assertEqual(set(adaptive.SOURCES) | {
            adaptive.BASE + "utils/DampedDragLifecycleRegressionTest.kt",
            adaptive.BASE + "utils/InteractiveHighlightResourceLifecycleTest.kt",
            adaptive.BASE + "button/LiquidButtonConstructionTraceTest.kt",
            adaptive.BASE + "utils/UiDragShaderTestHost.kt", adaptive.BASE + "internal/PointerCancellation.kt"}, set(union))
        for focus, count in zip(related.FOCUSES, (8, 14)):
            groups = related.focus_spec(focus)["groups"]
            declared = [re.findall(r"@Test\s+fun\s+(\w+)\s*\(", (ROOT / group["source"]).read_text()) for group in groups]
            self.assertEqual(count, sum(map(len, declared)))
            self.assertEqual([list(group["declared_methods"]) for group in groups], declared)
            self.assertTrue(related.validate_sources(ROOT, focus))

    def test_requests_reject_duplicates_omissions_foreign_wildcard_and_compile_publish_tasks(self):
        for focus in related.FOCUSES:
            request = related.native_request(focus)
            self.assertEqual(related.TASK, request[0]); self.assertTrue(related.validate_request(request, focus))
            for bad in (request[:-2], request + request[-2:], request + [":calf-ui:compileTestKotlinIosSimulatorArm64"],
                        request + ["publish"], [request[0], "--tests", "*"], tuple(request),
                        [":calf-ui:allTests", *request[1:]], [request[0], "--tests", "foreign", *request[3:]]):
                with self.assertRaises(ValueError): related.validate_request(bad, focus)

    def test_source_contract_retains_exact_focus_runtime_init_and_ordinary_source_hashes(self):
        for focus, count in zip(related.FOCUSES, (6, 11)):
            contract = related.source_contract(ROOT, focus)
            self.assertEqual(focus, contract["focus"]); self.assertEqual([], contract["common_sources"])
            self.assertEqual(count, len(contract["effective_sources"]))
            self.assertEqual({name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                              for name in related.sources(focus)}, contract["source_sha256"])
            self.assertEqual(related.runtime_focus(focus), contract["runtime_focus"])
            self.assertEqual(related.INIT_SHA256[focus], hashlib.sha256((ROOT / contract["init_script"]).read_bytes()).hexdigest())
            self.assertTrue(related.validate_plan(model_plan(focus)))
            self.assertEqual([0, 0, 0], [contract[key] for key in
                ("compiler_executions_attested", "apple_links_attested", "native_tests_executed")])

    def test_missing_foreign_symlink_and_hardlink_authored_sources_refuse(self):
        focus = related.FOCUSES[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); copy_sources(root)
            name = related.sources(focus)[-1]; target = root / name; original = target.read_bytes()
            target.unlink()
            with self.assertRaises(FileNotFoundError): related.validate_sources(root, focus)
            target.symlink_to(ROOT / name)
            with self.assertRaises(ValueError): related.validate_sources(root, focus)
            target.unlink(); backing = target.with_name("source-backing.kt"); backing.write_bytes(original)
            target.hardlink_to(backing)
            with self.assertRaises(ValueError): related.validate_sources(root, focus)
            target.unlink(); backing.unlink(); target.write_bytes(original)
            for bad in (sorted(related.sources(focus))[:-1], sorted(related.sources(focus)) + ["foreign.kt"],
                        sorted(related.sources(focus)) * 2):
                with self.assertRaises(ValueError): related.validate_sources(root, focus, bad)

    def test_selected_adaptive_wrappers_require_their_actual_uiddevice_branch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); copy_sources(root)
            target = root / adaptive.SLIDER_SOURCE; original = target.read_text()
            target.write_text(original.replace("matrix(AdaptiveControlBranch.IOS26Plus)",
                                               "matrix(AdaptiveControlBranch.Pre26)", 1))
            self.assertNotEqual(original, target.read_text())
            with self.assertRaisesRegex(ValueError, "own actual OS branch"):
                related.validate_sources(root, related.FOCUSES[1])
            target.write_text(original)
            branch = root / adaptive.BRANCH_SOURCE
            branch.write_text(branch.read_text().replace("UIDevice.currentDevice.systemVersion", '"26.5"', 1))
            with self.assertRaisesRegex(ValueError, "actual owned application's iOS branch"):
                related.validate_sources(root, related.FOCUSES[1])

    def test_disabled_or_added_test_declarations_refuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); copy_sources(root)
            target = root / related.focus_spec(related.FOCUSES[1])["groups"][-1]["source"]
            original = target.read_text()
            for bad in (original.replace("@Test", "@Ignore @Test", 1), original + "\n@Test fun foreign() {}\n"):
                target.write_text(bad)
                with self.assertRaises(ValueError): related.validate_sources(root, related.FOCUSES[1])

    def test_drag_shader_helpers_require_actual_owned_application_main_and_keep_zero_test_helpers(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); copy_sources(root)
            target = root / (adaptive.BASE + "utils/UiDragShaderTestHost.kt"); original = target.read_text()
            for bad in (original.replace("onApplicationMain { requireOwnedApplicationWindow(); Unit }", "Unit", 1),
                        original + "\n@Test fun inventedHost() {}\n"):
                target.write_text(bad)
                with self.assertRaises(ValueError): related.validate_sources(root, related.FOCUSES[1])
            target.write_text(original)
            test = root / related.focus_spec(related.FOCUSES[1])["groups"][-1]["source"]
            test.write_text(test.read_text().replace("requireUiDragShaderApplication()", "Unit", 1))
            with self.assertRaisesRegex(ValueError, "owned Main application"):
                related.validate_sources(root, related.FOCUSES[1])

    def test_fresh_exact_native_task_admission_is_source_only_not_prior_klib_acceptance(self):
        for focus in related.FOCUSES:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); copy_sources(root)
                path = root / related.admission_path(focus); path.parent.mkdir(parents=True)
                path.write_text(json.dumps(related._admission(focus)))
                now = time.time_ns(); os.utime(path, ns=(now, now))
                self.assertTrue(related.validate_admission(root, now, now, focus))
                doc = json.loads(path.read_bytes())
                self.assertEqual(related.TASK, doc["task"])
                self.assertEqual(0, doc["native_tests_executed"])
                doc["task"] = ":calf-ui:compileTestKotlinIosSimulatorArm64"; path.write_text(json.dumps(doc))
                self.assertFalse(related.validate_admission(root, now, time.time_ns(), focus))

    def test_stale_future_corrupt_or_aliased_source_admission_refuses(self):
        focus = related.FOCUSES[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); copy_sources(root)
            path = root / related.admission_path(focus); path.parent.mkdir(parents=True)
            original = json.dumps(related._admission(focus)).encode(); path.write_bytes(original); now = time.time_ns()
            for stamp in (now - 3_000_000_000, now + 3_000_000_000):
                os.utime(path, ns=(stamp, stamp)); self.assertFalse(related.validate_admission(root, now, now, focus))
            for raw in (b"{}", b"", b"{bad", original[:-1] + b',"task":"duplicate"}', b'{"value":NaN}'):
                path.write_bytes(raw); self.assertFalse(related.validate_admission(root, now, time.time_ns(), focus))
            path.unlink(); backing = path.with_name("backing.json"); backing.write_bytes(original)
            path.symlink_to(backing); self.assertFalse(related.validate_admission(root, now, time.time_ns(), focus))
            path.unlink(); path.hardlink_to(backing); self.assertFalse(related.validate_admission(root, now, time.time_ns(), focus))
            for start, end in ((True, now), (now, False), (0, now), (now, now - 1)):
                self.assertFalse(related.validate_admission(root, start, end, focus))

    def test_drifted_foreign_or_wrong_band_source_receipts_refuse(self):
        focus = related.FOCUSES[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); copy_sources(root)
            path = root / related.admission_path(focus); path.parent.mkdir(parents=True)
            now = time.time_ns(); original = related._admission(focus)
            for key, value in (("focus", related.FOCUSES[0]), ("common_sources", ["foreign.kt"]),
                               ("effective_sources", original["effective_sources"][:-1]),
                               ("selected_methods", original["selected_methods"] + ["foreign"]),
                               ("source_sha256", {}), ("compiler_executions_attested", True),
                               ("native_tests_executed", 1), ("production_source_sets_changed", True)):
                doc = copy.deepcopy(original); doc[key] = value; path.write_text(json.dumps(doc))
                self.assertFalse(related.validate_admission(root, now, time.time_ns(), focus), key)
            path.write_text(json.dumps(original)); source = root / related.sources(focus)[-1]
            source.write_bytes(source.read_bytes() + b"\n")
            self.assertFalse(related.validate_admission(root, now, time.time_ns(), focus))

    def test_xml_requires_exact_methods_reports_and_no_duplicates_missing_or_foreign_cases(self):
        for focus in related.FOCUSES:
            cases, reports = model_cases(focus)
            scenarios, errors = related.outcomes(cases, "Darwin", focus, cases_by_report=reports)
            self.assertEqual([], errors); self.assertTrue(all(s["disposition"] == "required-executed" for s in scenarios))
            foreign = {**cases[-1], "name": "foreign[iosSimulatorArm64]"}
            for bad_cases, bad_reports in ((cases[:-1], reports), (cases + cases[:1], reports),
                    (cases[:-1] + [foreign], reports), (cases, reports[:-1]), (cases, [cases]),
                    (cases, reports + reports[:1]), (cases, None)):
                _, errors = related.outcomes(bad_cases, "Darwin", focus, cases_by_report=bad_reports)
                self.assertTrue(errors)

    def test_xml_failures_errors_skips_and_other_host_are_required_not_passed(self):
        focus = related.FOCUSES[1]; cases, reports = model_cases(focus)
        for status in ("failed", "error", "skipped", "unknown"):
            changed = copy.deepcopy(cases); changed[0]["status"] = status
            changed_reports = [[c for c in changed if c["classname"] == report[0]["classname"]] for report in reports]
            scenarios, errors = related.outcomes(changed, "Darwin", focus, cases_by_report=changed_reports)
            self.assertTrue(errors); self.assertEqual("required-not-passed", scenarios[0]["disposition"])
        scenarios, errors = related.outcomes(cases, "Linux", focus, cases_by_report=reports)
        self.assertTrue(errors); self.assertTrue(all(s["disposition"] == "required-not-passed" for s in scenarios))
        for malformed in (None, {}, [True], [{"classname": True, "name": "x", "status": "passed"}]):
            self.assertTrue(related.outcomes(malformed, "Darwin", focus, cases_by_report=[])[1])

    def test_pre26_remains_independently_required_without_26plus_or_na_substitution(self):
        self.assertEqual("ui-native-adaptive-pre26", related.runtime_focus(related.FOCUSES[0]))
        self.assertEqual("ui-native-adaptive-ios26plus", related.runtime_focus(related.FOCUSES[1]))
        self.assertTrue(set(related.selectors(related.FOCUSES[0])).isdisjoint(related.selectors(related.FOCUSES[1])))
        cases, reports = model_cases(related.FOCUSES[1])
        scenarios, errors = related.outcomes(cases, "Darwin", related.FOCUSES[0], cases_by_report=reports)
        self.assertTrue(errors); self.assertEqual(4, len(scenarios))
        self.assertTrue(all(s["required_on_host"] and s["disposition"] == "required-not-passed" for s in scenarios))
        self.assertIn("Separate genuine pre26", related.SCOPE)


if __name__ == "__main__":
    unittest.main()
