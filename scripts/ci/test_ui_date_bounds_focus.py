"""Finite native date-bound verification guards. Synthetic tooling, not iOS tests."""
from collections import Counter
import copy
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

import ios_ui_application as app
import library_tests as r
import test_ios_application_receipts as receipts
import workflow_matrix as matrix


class DateBoundsFocus(unittest.TestCase):
    def plan(self):
        return r.plan(r.ROOT, "ios", only_modules=("calf-ui",), focus=r.UI_DATE_BOUNDS_FOCUS)

    def test_exact_six_methods_keep_real_application_and_partial_scope(self):
        plan = self.plan()
        self.assertTrue(r.validate_test_focus(plan))
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(["calf-ui"], plan["explicit_module_subset"])
        item, = plan["expected"]
        self.assertEqual(":calf-ui:" + r.IOS_APPLICATION_TASK, item["task"])
        self.assertEqual("genuine-uikit-application", item["native_test_host"])
        self.assertEqual(6, len(item["required_testcases"]))
        self.assertEqual(r.UI_DATE_BOUNDS_CLASS, item["test_filter"])
        self.assertIn(r.UI_DATE_BOUNDS_SOURCE, item["test_source_files"])

    def test_one_fixed_iphone_job_does_not_change_complete_profiles(self):
        row, = matrix.matrix("ios-date-bounds")["include"]
        self.assertEqual("ios-iphone", row["slot"])
        self.assertEqual("calf-ui", row["test-modules"])
        self.assertEqual(r.UI_DATE_BOUNDS_FOCUS, row["test-focus"])
        for profile in ("all", "ios", "ios-ui", "extended"):
            self.assertTrue(all("test-focus" not in row for row in matrix.matrix(profile)["include"]))

    def test_actual_gradle_selector_is_only_the_bare_reviewed_class(self):
        command = r.gradle_command("ios", self.plan(), "11111111-1111-1111-1111-111111111111")
        index = command.index("--tests")
        self.assertEqual(["--tests", r.UI_DATE_BOUNDS_CLASS], command[index:index + 2])
        self.assertEqual(1, command.count("--tests"))
        self.assertEqual([":calf-ui:" + r.IOS_APPLICATION_TASK], [v for v in command if v.startswith(":")])

    def test_native_arguments_only_accept_full_protocol_or_exact_kgp_filter(self):
        full = sorted(app.TEST_ARGUMENTS)
        self.assertIsNone(app.application_test_focus(full))
        self.assertEqual(r.UI_DATE_BOUNDS_FOCUS,
                         app.application_test_focus(full + ["--ktest_gradle_filter=" + r.UI_DATE_BOUNDS_CLASS]))
        for extra in ("--ktest_gradle_filter=*", "--ktest_filter=" + r.UI_DATE_BOUNDS_CLASS,
                      "--ktest_gradle_filter=" + r.UI_DATE_BOUNDS_CLASS + ".*",
                      "--ktest_negative_gradle_filter=other", "--ktest_gradle_filter=" + r.UI_DATE_BOUNDS_CLASS + ",other"):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                app.application_test_focus(full + [extra])
        for arguments in (full[:1], full + [app.DATE_BOUNDS_ARGUMENT] * 2, full + [full[0]], []):
            with self.assertRaises(ValueError):
                app.application_test_focus(arguments)

    def test_foreign_suite_module_or_declared_complete_scope_is_rejected(self):
        for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-io",)),
                               ("ios", ("calf-ui", "calf-io")), ("ios", None)):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                r.plan(r.ROOT, suite, only_modules=modules, focus=r.UI_DATE_BOUNDS_FOCUS)
        for section, key, value in (("plan", "complete_suite_requested", True),
                                    ("item", "native_test_host", "skiko-only"),
                                    ("item", "test_filter", "*"),
                                    ("item", "required_testcases", []),
                                    ("item", "task", ":calf-ui:iosSimulatorArm64Test")):
            plan = self.plan()
            (plan if section == "plan" else plan["expected"][0])[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.validate_test_focus(plan)

    def test_source_declaration_drift_cannot_silently_reduce_the_selection(self):
        source = (r.ROOT / r.UI_DATE_BOUNDS_SOURCE).read_text()
        with tempfile.TemporaryDirectory() as folder:
            changed = Path(folder) / "changed.kt"
            real = r.safe_path
            for content in (source.replace("@Test fun every", "fun every", 1),
                            source.replace(r.UI_DATE_BOUNDS_METHODS[0], "differentMethod", 1),
                            source + "\n@Test fun anotherMethod() {}\n"):
                changed.write_text(content)
                with patch.object(r, "safe_path", side_effect=lambda root, path:
                                  changed if path == r.UI_DATE_BOUNDS_SOURCE else real(root, path)), self.assertRaises(ValueError):
                    self.plan()

    def collect(self, cases, marker=1, age=0):
        plan = self.plan()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / plan["expected"][0]["report_directory"] / "TEST-synthetic.xml"
            path.parent.mkdir(parents=True)
            suite = ET.Element("testsuite", tests=str(len(cases)), failures="0", errors="0", skipped="0")
            for case in cases:
                node = ET.SubElement(suite, "testcase", classname=case["classname"], name=case["name"])
                if case.get("status") in {"failure", "error", "skipped"}:
                    ET.SubElement(node, case["status"])
            path.write_bytes(ET.tostring(suite))
            now = time.time_ns()
            os.utime(path, ns=(now - age, now - age))
            return r.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                     Counter({plan["expected"][0]["task"]: marker}), host_system="Darwin")

    def test_exact_native_task_and_target_xml_inventory_is_required(self):
        cases = r.ui_date_bounds_identities()
        result = self.collect(cases)
        self.assertEqual([], result["errors"])
        self.assertEqual(6, result["totals"]["passed"])
        for invalid in (cases[:-1], cases + [cases[0]],
                        [{**c, "classname": r.UI_DATE_BOUNDS_CLASS} for c in cases],
                        [{**c, "name": c["name"].replace("iosSimulatorArm64", "iosArm64")} for c in cases],
                        cases + [{"classname": "other", "name": "unrelated"}]):
            self.assertTrue(self.collect(invalid)["errors"])

    def test_failure_skip_stale_or_missing_task_is_never_accepted(self):
        cases = r.ui_date_bounds_identities()
        for status in ("failure", "error", "skipped"):
            self.assertTrue(self.collect([{**cases[0], "status": status}, *cases[1:]])["errors"])
        self.assertTrue(self.collect(cases, marker=0)["errors"])
        self.assertTrue(self.collect(cases, age=10_000_000_000)["errors"])


class DateBoundsApplicationEvidence(unittest.TestCase):
    def setUp(self):
        self.fixture = receipts.IosApplicationReceipts("test_exact_app_protocol_xml_runtime_binary_and_cleanup_are_required")
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        f = self.fixture
        f.write(r.UI_DATE_BOUNDS_SOURCE, (r.ROOT / r.UI_DATE_BOUNDS_SOURCE).read_bytes())
        f.plan = r.plan(f.root, "ios", only_modules=("calf-ui",), focus=r.UI_DATE_BOUNDS_FOCUS)
        f.cases = [{"classname": r.UI_DATE_BOUNDS_CLASS, "name": method, "status": "passed"}
                   for method in r.UI_DATE_BOUNDS_METHODS]
        f.document["explicit_test_focus"] = r.UI_DATE_BOUNDS_FOCUS
        self.sync()

    def sync(self):
        f = self.fixture
        f.document["application_protocol"]["testcases"] = copy.deepcopy(f.cases)
        f.document["application_protocol"]["counts"] = r.case_counts(f.cases)
        f.document["application_protocol"].pop("image_lifetime_observation", None)
        f.modules[0]["testcases"] = f.xml_cases(f.cases)
        f.save()

    def test_selected_six_cases_retain_actual_lifecycle_runtime_cleanup_gates(self):
        result = self.fixture.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual(6, result["ios_applications"][0]["counts"]["passed"])
        for key in ("owned_app_stopped_verified", "owned_local_bundle_removed", "owned_app_absence_verified"):
            self.fixture.document["cleanup"][key] = False
            self.fixture.save()
            self.assertTrue(self.fixture.collect()["errors"])
            self.fixture.document["cleanup"][key] = True

    def test_green_matching_protocol_and_xml_cannot_omit_or_add_a_case(self):
        original = copy.deepcopy(self.fixture.cases)
        for changed in (original[:-1], original + [{"classname": "other", "name": "unrelated", "status": "passed"}]):
            self.fixture.cases = changed
            self.sync()
            self.assertTrue(self.fixture.collect()["errors"])

    def test_selection_cannot_be_relabelled_a_full_suite_or_mismatched_receipt(self):
        self.fixture.document["explicit_test_focus"] = None
        self.fixture.save()
        self.assertTrue(self.fixture.collect()["errors"])
        self.fixture.plan.pop("explicit_test_focus")
        for item in self.fixture.plan["expected"]:
            item.pop("test_filter")
            item.pop("required_testcases")
        self.assertTrue(self.fixture.collect()["errors"], "A six-case pass is not the full native UI suite")
