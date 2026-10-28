"""Focused native factory selection only; these fixtures are not iOS execution."""
import copy
from collections import Counter
from pathlib import Path
import tempfile
import time
import unittest

import library_tests as r
import workflow_matrix as m


class IOSPermissionFocusTests(unittest.TestCase):
    def plan(self):
        return r.plan(r.ROOT, "ios", only_modules=(r.IOS_PERMISSION_MODULE,), focus=r.IOS_PERMISSION_FOCUS)

    def test_only_seven_owning_methods_on_one_native_target_are_requested(self):
        rows = m.matrix("permissions-ios")["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual("ios-iphone", rows[0]["slot"])
        self.assertEqual(r.IOS_PERMISSION_FOCUS, rows[0]["test-focus"])
        self.assertEqual(r.IOS_PERMISSION_MODULE, rows[0]["test-modules"])
        plan = self.plan()
        self.assertTrue(r.validate_test_focus(plan))
        self.assertEqual(r.ios_permission_identities(), plan["expected"][0]["required_testcases"])
        command = r.gradle_command("ios", plan, simulator="00000000-0000-4000-8000-000000000001")
        self.assertEqual(["--tests", r.IOS_PERMISSION_CLASS], command[-2:])
        self.assertFalse(plan["complete_suite_requested"])

    def test_filters_cannot_escape_the_reviewed_native_scope_or_drop_a_method(self):
        for suite, modules in (("desktop", (r.IOS_PERMISSION_MODULE,)), ("ios", ("calf-ui",))):
            with self.assertRaises(ValueError):
                r.plan(r.ROOT, suite, only_modules=modules, focus=r.IOS_PERMISSION_FOCUS)
        plan = copy.deepcopy(self.plan())
        plan["expected"][0]["required_testcases"].pop()
        with self.assertRaises(ValueError):
            r.validate_test_focus(plan)
        for profile in ("all", "ios", "ios-ui", "permissions-unsupported"):
            self.assertTrue(all(row.get("test-focus") != r.IOS_PERMISSION_FOCUS for row in m.matrix(profile)["include"]))

    def test_tests_use_the_real_darwin_main_queue_and_acknowledge_late_callbacks(self):
        source = (r.ROOT / r.IOS_PERMISSION_SOURCE).read_text()
        self.assertNotIn("Dispatchers.setMain(", source)
        self.assertIn("Dispatchers.Main.immediate", source)
        self.assertIn("NSRunLoop.mainRunLoop.runUntilDate", source)
        self.assertIn("import platform.Foundation.runUntilDate", source)
        self.assertIn("import platform.Foundation.dateWithTimeIntervalSinceNow", source)
        self.assertIn("dispatch_async(dispatch_get_global_queue", source)
        self.assertIn("dispatch_async(dispatch_get_main_queue()) { mainDeliveries++ }", source)
        self.assertIn("secondHelper.mainDeliveries == 2", source)
        self.assertIn("registry.observerCount", source)

    def collect_xml(self, payloads, markers=1):
        """Synthetic collector inputs, not another native test execution."""
        plan = self.plan()
        expected = plan["expected"][0]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            reports = root / expected["report_directory"]
            reports.mkdir(parents=True)
            for index, payload in enumerate(payloads):
                (reports / f"TEST-fixture-{index}.xml").write_bytes(payload)
            now = time.time_ns()
            return r.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                     Counter({expected["task"]: markers}), host_system="Darwin")

    def native_xml(self, identities=None, outcome=""):
        identities = r.ios_permission_identities() if identities is None else identities
        return ("<testsuite>" + "".join(
            f'<testcase classname="{case["classname"]}" name="{case["name"]}">{outcome}</testcase>'
            for case in identities) + "</testsuite>").encode()

    def test_expected_native_identities_are_exact_without_changing_gradle_filter(self):
        expected = [{"classname": "iosSimulatorArm64Test.com.mohamedrejeb.calf.permissions.IOSPublicPermissionFactoryTest",
                     "name": method + "[iosSimulatorArm64]"} for method in r.IOS_PERMISSION_METHODS]
        self.assertEqual(expected, r.ios_permission_identities())
        self.assertEqual(["--tests", "com.mohamedrejeb.calf.permissions.IOSPublicPermissionFactoryTest"],
                         r.gradle_command("ios", self.plan(),
                                          simulator="00000000-0000-4000-8000-000000000001")[-2:])

    def test_held_actual_native_xml_passes_the_strict_collector_without_runtime_replay(self):
        report = r.ROOT / ("docs/development/evidence/permission-ios-important-20261028/"
                           "fixed001-attempt2/reports/TEST-iosSimulatorArm64Test."
                           "com.mohamedrejeb.calf.permissions.IOSPublicPermissionFactoryTest.xml")
        result = self.collect_xml([report.read_bytes()])
        self.assertFalse(result["errors"])
        self.assertEqual(7, result["totals"]["passed"])
        self.assertEqual(0, result["totals"]["not_applicable"])

    def test_missing_extra_wrong_target_class_and_unadorned_identities_are_rejected(self):
        expected = r.ios_permission_identities()
        variants = [expected[:-1], [*expected, {"classname": expected[0]["classname"], "name": "extraMethod[iosSimulatorArm64]"}]]
        for key, value in (("classname", r.IOS_PERMISSION_CLASS),
                           ("classname", "iosSimulatorArm64Test.OtherClass"),
                           ("classname", "iosArm64Test." + r.IOS_PERMISSION_CLASS),
                           ("name", r.IOS_PERMISSION_METHODS[0]),
                           ("name", r.IOS_PERMISSION_METHODS[0] + "[iosArm64]")):
            changed = copy.deepcopy(expected)
            changed[0][key] = value
            variants.append(changed)
        for identities in variants:
            with self.subTest(identities=identities):
                self.assertTrue(self.collect_xml([self.native_xml(identities)])["errors"])

    def test_duplicates_within_and_across_reports_are_rejected(self):
        expected = r.ios_permission_identities()
        for payloads in ([self.native_xml([*expected, expected[0]])],
                         [self.native_xml(expected), self.native_xml(expected[:1])]):
            with self.subTest(report_count=len(payloads)):
                self.assertTrue(self.collect_xml(payloads)["errors"])

    def test_native_failure_error_skip_and_missing_fresh_marker_never_pass(self):
        for outcome in ("<failure/>", "<error/>", "<skipped/>"):
            with self.subTest(outcome=outcome):
                self.assertTrue(self.collect_xml([self.native_xml(outcome=outcome)])["errors"])
        self.assertTrue(self.collect_xml([self.native_xml()], markers=0)["errors"])


if __name__ == "__main__":
    unittest.main()
