"""Finite selection/source/receipt fixtures, not Apple/UI functionality tests."""
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


class IOSUiStateFocusTests(unittest.TestCase):
    def plan(self, root=r.ROOT):
        return r.plan(root, "ios", only_modules=("calf-ui",), focus=r.IOS_UI_STATE_FOCUS)

    def collect(self, cases=None, outcome="", marker=1):
        plan = self.plan()
        cases = r.ui_application_focus_identities(r.IOS_UI_STATE_FOCUS) if cases is None else cases
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = root / plan["expected"][0]["report_directory"]
            reports.mkdir(parents=True)
            (reports / "TEST-synthetic.xml").write_text("<testsuite>" + "".join(
                f'<testcase classname="{case["classname"]}" name="{case["name"]}">{outcome}</testcase>'
                for case in cases) + "</testsuite>")
            now = time.time_ns()
            return r.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                     Counter({plan["expected"][0]["task"]: marker}), host_system="Darwin")

    def test_eight_exact_methods_single_real_application_and_cli_do_not_replay_dates(self):
        row, = m.matrix("ios-ui-state")["include"]
        self.assertEqual(("ios-iphone", "calf-ui", r.IOS_UI_STATE_FOCUS),
                         tuple(row[key] for key in ("slot", "test-modules", "test-focus")))
        plan = self.plan()
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual("genuine-uikit-application", plan["expected"][0]["native_test_host"])
        self.assertEqual(8, len(plan["expected"][0]["required_testcases"]))
        filters = r.ui_application_focus_filter(r.IOS_UI_STATE_FOCUS).split(",")
        self.assertNotIn("datepicker", ",".join(filters))
        self.assertNotIn("ThemeOwnershipTest", ",".join(filters))
        selectors = [arg for value in filters for arg in ("--tests", value)]
        self.assertEqual(selectors, r.gradle_command(
            "ios", plan, simulator="00000000-0000-4000-8000-000000000001")[-16:])
        result = subprocess.run([r.sys.executable, str(r.ROOT / "scripts/ci/library_tests.py"), "plan",
                                 "--suite", "ios", "--module", "calf-ui", "--focus", r.IOS_UI_STATE_FOCUS],
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        for selection in (filters, list(reversed(filters))):
            self.assertEqual(r.IOS_UI_STATE_FOCUS, app.application_test_focus(
                sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + ",".join(selection)]))
        self.assertEqual(11, len(m.matrix("all")["include"]))

    def test_missing_extra_foreign_duplicate_skipped_failed_and_unexecuted_cases_are_red(self):
        identities = r.ui_application_focus_identities(r.IOS_UI_STATE_FOCUS)
        positive = self.collect(identities)
        self.assertEqual([], positive["errors"])
        self.assertEqual(8, positive["totals"]["passed"])
        for cases in ([], identities[:-1], identities * 2, [*identities, {**identities[0], "name": "unrelated"}]):
            self.assertTrue(self.collect(cases)["errors"])
        for field, value in (("classname", r.IOS_TIME_STATE_CLASS),
                             ("name", r.IOS_TIME_STATE_METHODS[0] + "[iosArm64]")):
            cases = copy.deepcopy(identities)
            cases[0][field] = value
            self.assertTrue(self.collect(cases)["errors"])
        for outcome in ("<failure/>", "<error/>", "<skipped/>"):
            self.assertTrue(self.collect(outcome=outcome)["errors"])
        self.assertTrue(self.collect(marker=0)["errors"])
        for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-file-picker",)), ("ios", None)):
            with self.assertRaises(ValueError): r.plan(r.ROOT, suite, only_modules=modules, focus=r.IOS_UI_STATE_FOCUS)

    def fixture(self):
        f = receipts.IosApplicationReceipts("test_exact_app_protocol_xml_runtime_binary_and_cleanup_are_required")
        self.addCleanup(f.doCleanups)
        f.setUp()
        for group in r.IOS_UI_STATE_GROUPS:
            f.write(group["source"], (r.ROOT / group["source"]).read_bytes())
        f.plan = self.plan(f.root)
        f.cases = [{"classname": group["classname"], "name": method, "status": "passed"}
                   for group in r.IOS_UI_STATE_GROUPS for method in group["methods"]]
        f.document["explicit_test_focus"] = r.IOS_UI_STATE_FOCUS
        f.document["application_protocol"].update(testcases=copy.deepcopy(f.cases), counts=r.case_counts(f.cases))
        f.document["application_protocol"].pop("image_lifetime_observation", None)
        f.modules[0]["testcases"] = f.xml_cases(f.cases)
        f.save()
        return f

    def test_actual_receipt_contract_still_requires_worker_runtime_binary_and_owned_cleanup(self):
        f = self.fixture()
        self.assertEqual([], f.collect()["errors"])
        for key in ("owned_app_stopped_verified", "owned_local_bundle_removed", "owned_app_absence_verified"):
            f.document["cleanup"][key] = False; f.save()
            self.assertTrue(f.collect()["errors"])
            f.document["cleanup"][key] = True
        f.document["application_protocol"]["completion"]["worker_terminated"] = False; f.save()
        self.assertTrue(f.collect()["errors"])
        f.document["application_protocol"]["completion"]["worker_terminated"] = True
        f.document["runtime_after"]["source_revision"] = "b" * 40; f.save()
        self.assertTrue(f.collect()["errors"])

    def test_declaration_drift_and_missing_host_cannot_silently_shrink_the_finite_selection(self):
        f = self.fixture()
        self.assertTrue(r.validate_test_focus(f.plan))
        source = f.root / r.IOS_TIME_STATE_SOURCE
        original = source.read_text()
        for changed in (original.replace("@Test", "@IgnoredTest", 1), original + "\n@Test fun unrelated() {}\n"):
            source.write_text(changed)
            with self.assertRaises(ValueError): self.plan(f.root)
        source.write_text(original)
        (f.root / r.IOS_APPLICATION_SOURCES[0]).unlink()
        with self.assertRaises(ValueError): self.plan(f.root)

    def test_source_keeps_calendar_copy_picker_zone_explicit_action_cleanup_and_real_host_appearance(self):
        manager = (r.ROOT / "calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/TimePickerManager.kt").read_text()
        self.assertIn("copyWithZone(null) as NSCalendar", manager)
        self.assertIn("timeZone = picker.timeZone ?: NSTimeZone.localTimeZone", manager)
        self.assertIn("datePicker.removeTarget(datePickerDelegate", manager)
        self.assertIn("if (disposed) return", manager)
        composition = (r.ROOT / "calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/AdaptiveTimePicker.ios.kt").read_text()
        self.assertIn("onDispose { datePickerManager.dispose() }", composition)
        time_state = (r.ROOT / r.IOS_TIME_STATE_SOURCE).read_text()
        for value in ("onApplicationMain { NSTimeZone.defaultTimeZone = priorDefaultZone }",
                      "assertTime(picker, 14, 35)", "setNativeTime(picker, 9, 18)",
                      "assertEquals(9, second.hour)", "assertEquals(18, second.minute)",
                      "assertEquals(previousHour, first.hour)", "assertEquals(previousMinute, first.minute)"):
            self.assertIn(value, time_state)
        host = (r.ROOT / r.IOS_APPLICATION_SOURCES[0]).read_text()
        for value in ("override fun viewDidAppear", "override fun viewWillDisappear", "rootHasAppeared &&",
                      "owned root reappearance after presenter teardown", "!rootIsAppeared && controller.view.window == null"):
            self.assertIn(value, host)
        sheet = (r.ROOT / r.IOS_SHEET_STATE_SOURCE).read_text()
        for value in ("registry.performSave()", "restoredValues = assertNotNull(saved)", "Density(3f, 1.5f)",
                      "assertSame(restored, state)", "assertNull(restored.iosSheetManager)", "assertEquals(1, sheet.detents.size)"):
            self.assertIn(value, sheet)


if __name__ == "__main__": unittest.main()
