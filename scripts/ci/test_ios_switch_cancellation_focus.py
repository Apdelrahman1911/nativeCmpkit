"""Finite iOS switch cancellation selection/receipt guards; these are not native executions."""
from collections import Counter
import copy
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

import ios_ui_application as app
import library_tests as r
import test_ios_application_receipts as receipts
import workflow_matrix as m


class IOSSwitchCancellationFocusTests(unittest.TestCase):
    def plan(self):
        return r.plan(r.ROOT, "ios", only_modules=("calf-ui",), focus=r.IOS_SWITCH_CANCELLATION_FOCUS)

    def collect(self, identities=None, outcome="", markers=1, duplicate=False):
        expected = self.plan()["expected"][0]
        identities = r.ios_switch_cancellation_identities() if identities is None else identities
        xml = "<testsuite>" + "".join(
            f'<testcase classname="{c["classname"]}" name="{c["name"]}">{outcome}</testcase>' for c in identities) + "</testsuite>"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = root / expected["report_directory"]
            reports.mkdir(parents=True)
            (reports / "TEST-synthetic.xml").write_text(xml)
            if duplicate:
                (reports / "TEST-duplicate.xml").write_text(xml)
            now = time.time_ns()
            return r.collect_reports(root, self.plan(), now - 1_000_000_000, now + 1_000_000_000,
                                     Counter({expected["task"]: markers}), host_system="Darwin")

    def test_finite_profile_cli_and_command_select_only_the_two_new_native_methods(self):
        rows = m.matrix("ios-switch-cancellation")["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual("ios-iphone", rows[0]["slot"])
        self.assertEqual("calf-ui", rows[0]["test-modules"])
        self.assertEqual(r.IOS_SWITCH_CANCELLATION_FOCUS, rows[0]["test-focus"])
        plan = self.plan()
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(":calf-ui:" + r.IOS_APPLICATION_TASK, plan["expected"][0]["task"])
        self.assertEqual("genuine-uikit-application", plan["expected"][0]["native_test_host"])
        selectors = [item for method in r.IOS_SWITCH_CANCELLATION_METHODS
                     for item in ("--tests", r.IOS_SWITCH_CANCELLATION_CLASS + "." + method)]
        self.assertEqual(selectors, r.gradle_command(
            "ios", plan, simulator="00000000-0000-4000-8000-000000000001")[-4:])
        result = subprocess.run([r.sys.executable, str(r.ROOT / "scripts/ci/library_tests.py"), "plan",
                                 "--suite", "ios", "--module", "calf-ui", "--focus", r.IOS_SWITCH_CANCELLATION_FOCUS],
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        report = self.collect()
        self.assertFalse(report["errors"])
        self.assertEqual(2, report["totals"]["passed"])
        self.assertEqual(r.IOS_SWITCH_CANCELLATION_SOURCE, report["modules"][0]["native_scenarios"][0]["source"])

    def test_wrong_scope_or_weakened_filter_cannot_run(self):
        for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-file-picker",)), ("ios", None)):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                r.plan(r.ROOT, suite, only_modules=modules, focus=r.IOS_SWITCH_CANCELLATION_FOCUS)
        for key, value in (("test_filter", "*"), ("required_testcases", []), ("task", ":calf-ui:publish")):
            plan = copy.deepcopy(self.plan())
            plan["expected"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.gradle_command("ios", plan, simulator="00000000-0000-4000-8000-000000000001")

    def test_all_original_declarations_remain_and_cannot_be_filtered_away(self):
        source = (r.ROOT / r.IOS_SWITCH_CANCELLATION_SOURCE).read_text()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "settings.gradle.kts").write_text('include(\n    ":calf-ui",\n)\n')
            (root / "calf-ui").mkdir()
            (root / "calf-ui/build.gradle.kts").write_text("// synthetic build, not a runtime fixture\n")
            for relative in r.IOS_APPLICATION_SOURCES:
                host_source = root / relative
                host_source.parent.mkdir(parents=True, exist_ok=True)
                host_source.write_bytes((r.ROOT / relative).read_bytes())
            path = root / r.IOS_SWITCH_CANCELLATION_SOURCE
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source)
            unchanged = r.plan(root, "ios", only_modules=("calf-ui",), focus=r.IOS_SWITCH_CANCELLATION_FOCUS)
            self.assertTrue(r.validate_test_focus(unchanged))
            self.assertEqual(r.ios_switch_cancellation_identities(), unchanged["expected"][0]["required_testcases"])
            for changed in (source.replace(r.IOS_SWITCH_CANCELLATION_METHODS[0], "wrongMethod"),
                            source.replace("@Test", "@IgnoredTest", 1), source + "\n@Test fun unrelated() {}\n"):
                path.write_text(changed)
                with self.subTest(change=changed[-70:]), self.assertRaises(ValueError):
                    r.plan(root, "ios", only_modules=("calf-ui",), focus=r.IOS_SWITCH_CANCELLATION_FOCUS)

    def test_real_application_accepts_only_the_exact_two_method_filter_in_either_kgp_order(self):
        full = sorted(app.TEST_ARGUMENTS)
        prefix = "--ktest_gradle_filter="
        methods = r.ui_application_focus_filter(r.IOS_SWITCH_CANCELLATION_FOCUS).split(",")
        for ordered in (methods, list(reversed(methods))):
            self.assertEqual(r.IOS_SWITCH_CANCELLATION_FOCUS,
                             app.application_test_focus(full + [prefix + ",".join(ordered)]))
        for selected in (methods[:1], methods * 2, [*methods, "other"], [methods[0], "*"],
                         [methods[0], r.IOS_SWITCH_CANCELLATION_CLASS]):
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                app.application_test_focus(full + [prefix + ",".join(selected)])
        for arguments in (full + [prefix + methods[0], prefix + methods[1]],
                          full[:1] + [prefix + ",".join(methods)], full + [full[0], prefix + ",".join(methods)]):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                app.application_test_focus(arguments)

    def test_missing_extra_duplicate_or_foreign_target_xml_is_not_success(self):
        original = r.ios_switch_cancellation_identities()
        variants = [[], original * 2, [*original, {"classname": original[0]["classname"], "name": "unrelated"}]]
        for key, value in (("classname", r.IOS_SWITCH_CANCELLATION_CLASS), ("classname", "iosSimulatorArm64ApplicationTest.Foreign"),
                           ("name", r.IOS_SWITCH_CANCELLATION_METHODS[0]), ("name", r.IOS_SWITCH_CANCELLATION_METHODS[0] + "[iosArm64]")):
            changed = copy.deepcopy(original)
            changed[0][key] = value
            variants.append(changed)
        for identities in variants:
            with self.subTest(identities=identities):
                self.assertTrue(self.collect(identities)["errors"])
        self.assertTrue(self.collect(duplicate=True)["errors"])

    def test_failed_skipped_or_no_actual_task_marker_never_passes(self):
        for outcome in ("<failure/>", "<error/>", "<skipped/>"):
            with self.subTest(outcome=outcome):
                self.assertTrue(self.collect(outcome=outcome)["errors"])
        self.assertTrue(self.collect(markers=0)["errors"])


class IOSSwitchApplicationReceiptTests(unittest.TestCase):
    """Synthetic host/protocol/cleanup calibration; never counted as native tests."""

    def setUp(self):
        self.fixture = receipts.IosApplicationReceipts("test_exact_app_protocol_xml_runtime_binary_and_cleanup_are_required")
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        f = self.fixture
        f.write(r.IOS_SWITCH_CANCELLATION_SOURCE, (r.ROOT / r.IOS_SWITCH_CANCELLATION_SOURCE).read_bytes())
        f.plan = r.plan(f.root, "ios", only_modules=("calf-ui",), focus=r.IOS_SWITCH_CANCELLATION_FOCUS)
        f.cases = [{"classname": r.IOS_SWITCH_CANCELLATION_CLASS, "name": method, "status": "passed"}
                   for method in r.IOS_SWITCH_CANCELLATION_METHODS]
        f.document["explicit_test_focus"] = r.IOS_SWITCH_CANCELLATION_FOCUS
        f.document["application_protocol"]["testcases"] = copy.deepcopy(f.cases)
        f.document["application_protocol"]["counts"] = r.case_counts(f.cases)
        f.document["application_protocol"].pop("image_lifetime_observation", None)
        f.modules[0]["testcases"] = f.xml_cases(f.cases)
        f.save()

    def test_two_cases_still_require_real_host_protocol_worker_and_owned_cleanup(self):
        f = self.fixture
        accepted = f.collect()
        self.assertEqual([], accepted["errors"])
        self.assertEqual(2, accepted["ios_applications"][0]["counts"]["passed"])
        for key in ("owned_app_stopped_verified", "owned_local_bundle_removed", "owned_app_absence_verified"):
            f.document["cleanup"][key] = False
            f.save()
            with self.subTest(key=key):
                self.assertTrue(f.collect()["errors"])
            f.document["cleanup"][key] = True
        f.document["explicit_test_focus"] = None
        f.save()
        self.assertTrue(f.collect()["errors"], "Two switch cases are not a full UIKit suite pass")
