"""Finite safety selection and synthetic XML guards, not native runtime evidence."""
from collections import Counter
import copy
from pathlib import Path
import tempfile
import time
import unittest

import library_tests as r
import workflow_matrix as m


class IOSPermissionSafetyFocusTests(unittest.TestCase):
    def plan(self):
        return r.plan(r.ROOT, "ios", only_modules=(r.IOS_PERMISSION_MODULE,), focus=r.IOS_PERMISSION_SAFETY_FOCUS)

    def collect(self, identities=None, outcome="", markers=1, duplicate_report=False):
        expected = self.plan()["expected"][0]
        identities = r.ios_permission_safety_identities() if identities is None else identities
        payload = ("<testsuite>" + "".join(
            f'<testcase classname="{case["classname"]}" name="{case["name"]}">{outcome}</testcase>'
            for case in identities) + "</testsuite>")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = root / expected["report_directory"]
            reports.mkdir(parents=True)
            (reports / "TEST-synthetic.xml").write_text(payload)
            if duplicate_report:
                (reports / "TEST-synthetic-duplicate.xml").write_text(payload)
            now = time.time_ns()
            return r.collect_reports(root, self.plan(), now - 1_000_000_000, now + 1_000_000_000,
                                     Counter({expected["task"]: markers}), host_system="Darwin")

    def test_only_two_new_native_methods_are_requested_with_exact_target_identities(self):
        rows = m.matrix("permissions-ios-safety")["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual("ios-iphone", rows[0]["slot"])
        self.assertEqual(r.IOS_PERMISSION_MODULE, rows[0]["test-modules"])
        self.assertEqual(r.IOS_PERMISSION_SAFETY_FOCUS, rows[0]["test-focus"])
        plan = self.plan()
        expected = [{"classname": "iosSimulatorArm64Test.com.mohamedrejeb.calf.permissions.IOSPermissionSafetyAcceptanceTest",
                     "name": name + "[iosSimulatorArm64]"} for name in r.IOS_PERMISSION_SAFETY_METHODS]
        self.assertEqual(expected, plan["expected"][0]["required_testcases"])
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(["--tests", r.IOS_PERMISSION_SAFETY_CLASS],
                         r.gradle_command("ios", plan, simulator="00000000-0000-4000-8000-000000000001")[-2:])
        result = self.collect()
        self.assertFalse(result["errors"])
        self.assertEqual(2, result["totals"]["passed"])
        self.assertEqual(0, result["totals"]["not_applicable"])

    def test_wrong_scope_and_weaker_or_arbitrary_filters_are_rejected(self):
        for suite, modules in (("desktop", (r.IOS_PERMISSION_MODULE,)), ("ios", ("calf-ui",)),
                               ("ios", None)):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                r.plan(r.ROOT, suite, only_modules=modules, focus=r.IOS_PERMISSION_SAFETY_FOCUS)
        for key, value in (("test_filter", "*"), ("required_testcases", []),
                           ("task", ":calf-permissions:calf-permissions-core:publish")):
            plan = copy.deepcopy(self.plan())
            plan["expected"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.gradle_command("ios", plan)

    def test_changed_missing_or_extra_declared_tests_cannot_be_filtered_away(self):
        source = (r.ROOT / r.IOS_PERMISSION_SAFETY_SOURCE).read_text()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "settings.gradle.kts").write_text(
                'include(":calf-permissions:core")\nproject(":calf-permissions:core").name = "calf-permissions-core"\n')
            module = root / r.IOS_PERMISSION_MODULE
            module.mkdir(parents=True)
            (module / "build.gradle.kts").write_text("// Synthetic discovery fixture\n")
            path = root / r.IOS_PERMISSION_SAFETY_SOURCE
            path.parent.mkdir(parents=True)
            for changed in (source.replace(r.IOS_PERMISSION_SAFETY_METHODS[0], "wrongMethod"),
                            source.replace("@Test", "@IgnoredTest", 1), source + "\n@Test fun extraTest() {}\n"):
                path.write_text(changed)
                with self.subTest(change=changed[-70:]), self.assertRaises(ValueError):
                    r.plan(root, "ios", only_modules=(r.IOS_PERMISSION_MODULE,), focus=r.IOS_PERMISSION_SAFETY_FOCUS)

    def test_missing_extra_foreign_unadorned_and_duplicate_xml_never_pass(self):
        expected = r.ios_permission_safety_identities()
        variants = [expected[:-1], [*expected, expected[0]],
                    [*expected, {"classname": expected[0]["classname"], "name": "unrelated[iosSimulatorArm64]"}]]
        for key, value in (("classname", r.IOS_PERMISSION_SAFETY_CLASS),
                           ("classname", "iosSimulatorArm64Test.ForeignClass"),
                           ("name", r.IOS_PERMISSION_SAFETY_METHODS[0]),
                           ("name", r.IOS_PERMISSION_SAFETY_METHODS[0] + "[iosArm64]")):
            changed = copy.deepcopy(expected)
            changed[0][key] = value
            variants.append(changed)
        for identities in variants:
            with self.subTest(identities=identities):
                self.assertTrue(self.collect(identities)["errors"])
        self.assertTrue(self.collect(duplicate_report=True)["errors"])

    def test_failure_error_skip_or_no_fresh_execution_marker_never_pass(self):
        for outcome in ("<failure/>", "<error/>", "<skipped/>"):
            with self.subTest(outcome=outcome):
                self.assertTrue(self.collect(outcome=outcome)["errors"])
        self.assertTrue(self.collect(markers=0)["errors"])

    def test_native_safety_cases_use_actual_public_factories_queues_and_owned_cleanup(self):
        source = (r.ROOT / r.IOS_PERMISSION_SAFETY_SOURCE).read_text()
        for required in ("rememberPermissionState(permission)", "dispatch_get_global_queue", "NSLock()",
                         "NSThread.isMainThread", "NSRunLoop.mainRunLoop.runUntilDate",
                         "observerCount", "host.errors.single()", "nativeQueriesAtDisposal"):
            self.assertIn(required, source)
        self.assertNotIn("Dispatchers.setMain", source)
        self.assertNotIn("PermissionBackend", source)
        controller = (r.ROOT / "calf-permissions/core/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/CallbackPermissionState.kt").read_text()
        self.assertIn("SupervisorJob(scope.coroutineContext[Job])", controller)
        self.assertIn("try { owned?.dispose() } finally { operationJob.cancel() }", controller)


if __name__ == "__main__":
    unittest.main()
