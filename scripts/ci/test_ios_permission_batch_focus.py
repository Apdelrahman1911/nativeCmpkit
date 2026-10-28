"""Finite one-method batch selection guards. Synthetic tooling, not native execution."""
from collections import Counter
import copy
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

import library_tests as r
import workflow_matrix as matrix


class IOSPermissionBatchFocusTests(unittest.TestCase):
    def plan(self):
        return r.plan(r.ROOT, "ios", only_modules=(r.IOS_PERMISSION_MODULE,),
                      focus=r.IOS_PERMISSION_BATCH_FOCUS)

    def collect(self, cases=None, marker=1, age=0):
        plan = self.plan()
        item, = plan["expected"]
        cases = r.ios_permission_safety_identities(r.IOS_PERMISSION_BATCH_FOCUS) if cases is None else cases
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / item["report_directory"] / "TEST-synthetic.xml"
            path.parent.mkdir(parents=True)
            suite = ET.Element("testsuite", tests=str(len(cases)))
            for case in cases:
                node = ET.SubElement(suite, "testcase", classname=case["classname"], name=case["name"])
                if case.get("status") in {"failure", "error", "skipped"}:
                    ET.SubElement(node, case["status"])
            path.write_bytes(ET.tostring(suite))
            now = time.time_ns()
            os.utime(path, ns=(now - age, now - age))
            return r.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                     Counter({item["task"]: marker}), host_system="Darwin")

    def test_one_exact_new_native_method_has_real_task_and_target_identity(self):
        row, = matrix.matrix("permissions-ios-empty-batch")["include"]
        self.assertEqual("ios-iphone", row["slot"])
        self.assertEqual(r.IOS_PERMISSION_MODULE, row["test-modules"])
        self.assertEqual(r.IOS_PERMISSION_BATCH_FOCUS, row["test-focus"])
        plan = self.plan()
        self.assertTrue(r.validate_test_focus(plan))
        self.assertFalse(plan["complete_suite_requested"])
        item, = plan["expected"]
        self.assertEqual(":calf-permissions:calf-permissions-core:iosSimulatorArm64Test", item["task"])
        self.assertEqual(r.IOS_PERMISSION_BATCH_CLASS, item["test_filter"])
        self.assertEqual([{"classname": "iosSimulatorArm64Test." + r.IOS_PERMISSION_BATCH_CLASS,
                           "name": r.IOS_PERMISSION_BATCH_METHODS[0] + "[iosSimulatorArm64]"}],
                         item["required_testcases"])
        self.assertEqual(["--tests", r.IOS_PERMISSION_BATCH_CLASS],
                         r.gradle_command("ios", plan, simulator="00000000-0000-4000-8000-000000000001")[-2:])
        result = self.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual(1, result["totals"]["passed"])

    def test_existing_successful_and_complete_profiles_are_unchanged(self):
        safety = r.plan(r.ROOT, "ios", only_modules=(r.IOS_PERMISSION_MODULE,),
                        focus=r.IOS_PERMISSION_SAFETY_FOCUS)
        self.assertEqual(r.IOS_PERMISSION_SAFETY_CLASS, safety["expected"][0]["test_filter"])
        self.assertEqual(2, len(safety["expected"][0]["required_testcases"]))
        factories = r.plan(r.ROOT, "ios", only_modules=(r.IOS_PERMISSION_MODULE,), focus=r.IOS_PERMISSION_FOCUS)
        self.assertEqual(7, len(factories["expected"][0]["required_testcases"]))
        for profile in ("all", "ios", "extended"):
            self.assertTrue(all("test-focus" not in row for row in matrix.matrix(profile)["include"]))

    def test_cross_scope_arbitrary_filters_and_false_complete_claims_are_rejected(self):
        for suite, modules in (("desktop", (r.IOS_PERMISSION_MODULE,)), ("js", (r.IOS_PERMISSION_MODULE,)),
                               ("ios", ("calf-ui",)), ("ios", None)):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                r.plan(r.ROOT, suite, only_modules=modules, focus=r.IOS_PERMISSION_BATCH_FOCUS)
        for section, key, value in (("item", "test_filter", "*"),
                                    ("item", "test_filter", r.IOS_PERMISSION_SAFETY_CLASS),
                                    ("item", "required_testcases", []),
                                    ("item", "required_testcases", r.ios_permission_safety_identities()),
                                    ("item", "task", ":calf-permissions:calf-permissions-core:publish"),
                                    ("plan", "complete_suite_requested", True)):
            plan = copy.deepcopy(self.plan())
            (plan if section == "plan" else plan["expected"][0])[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.validate_test_focus(plan)

    def test_source_declaration_drift_cannot_reduce_or_expand_the_selection(self):
        source = (r.ROOT / r.IOS_PERMISSION_BATCH_SOURCE).read_text()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "changed.kt"
            real = r.safe_path
            for content in (source.replace("@Test fun", "fun", 1),
                            source.replace(r.IOS_PERMISSION_BATCH_METHODS[0], "anotherName", 1),
                            source + "\n@Test fun anotherMethod() {}\n"):
                path.write_text(content)
                with patch.object(r, "safe_path", side_effect=lambda root, name:
                                  path if name == r.IOS_PERMISSION_BATCH_SOURCE else real(root, name)), self.assertRaises(ValueError):
                    self.plan()

    def test_missing_extra_duplicate_unadorned_and_foreign_xml_cannot_pass(self):
        case, = r.ios_permission_safety_identities(r.IOS_PERMISSION_BATCH_FOCUS)
        variants = ([], [case, case], [case, {**case, "name": "unrelated[iosSimulatorArm64]"}],
                    [{**case, "classname": r.IOS_PERMISSION_BATCH_CLASS}],
                    [{**case, "classname": "iosSimulatorArm64Test.ForeignClass"}],
                    [{**case, "name": r.IOS_PERMISSION_BATCH_METHODS[0]}],
                    [{**case, "name": case["name"].replace("iosSimulatorArm64", "iosArm64")}])
        for cases in variants:
            with self.subTest(cases=cases):
                self.assertTrue(self.collect(cases)["errors"])

    def test_error_skip_stale_or_missing_execution_marker_is_never_accepted(self):
        case, = r.ios_permission_safety_identities(r.IOS_PERMISSION_BATCH_FOCUS)
        for status in ("failure", "error", "skipped"):
            self.assertTrue(self.collect([{**case, "status": status}])["errors"])
        self.assertTrue(self.collect(marker=0)["errors"])
        self.assertTrue(self.collect(age=10_000_000_000)["errors"])

    def test_real_public_factory_fixture_and_supervisor_ownership_remain_explicit(self):
        source = (r.ROOT / r.IOS_PERMISSION_BATCH_SOURCE).read_text()
        for required in ("rememberMultiplePermissionsState(requested)", "NSRunLoop.mainRunLoop.runUntilDate",
                         "NSThread.isMainThread", "observerCount", "host.errors.single()", "assertSame(original, batch)",
                         "original.launchMultiplePermissionRequest()", "last.permissions.single().launchPermissionRequest()"):
            self.assertIn(required, source)
        self.assertNotIn("Dispatchers.setMain", source)
        self.assertNotIn("PermissionDelegateRegistry.register", source)
        owning = (r.ROOT / "calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MutableMultiplePermissionsState.ios.kt").read_text()
        self.assertIn("SupervisorJob(scope.coroutineContext[Job])", owning)
        self.assertIn("try { batch.dispose() } finally { operationJob.cancel() }", owning)


if __name__ == "__main__":
    unittest.main()
