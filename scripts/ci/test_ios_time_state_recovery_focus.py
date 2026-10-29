"""Finite recovery/receipt fixtures; these are NOT actual UIKit library tests."""
import copy
import subprocess
import unittest

import ios_ui_application as app
import library_tests as r
import test_ios_ui_state_focus as batch
import workflow_matrix as m


class IosTimeStateRecoveryTests(unittest.TestCase):
    def plan(self, root=r.ROOT):
        return r.plan(root, "ios", only_modules=("calf-ui",), focus=r.IOS_TIME_STATE_RECOVERY_FOCUS)

    def helper(self):
        helper = batch.IOSUiStateFocusTests("test_eight_exact_methods_single_real_application_and_cli_do_not_replay_dates")
        self.addCleanup(helper.doCleanups)
        return helper

    def test_only_failed_method_is_selected_without_replaying_seven_accepted_methods(self):
        row, = m.matrix("ios-time-state-recovery")["include"]
        self.assertEqual(("ios-iphone", "calf-ui", r.IOS_TIME_STATE_RECOVERY_FOCUS),
                         tuple(row[k] for k in ("slot", "test-modules", "test-focus")))
        plan = self.plan()
        self.assertFalse(plan["complete_suite_requested"])
        required = plan["expected"][0]["required_testcases"]
        self.assertEqual(1, len(required))
        old = r.ui_application_focus_identities(r.IOS_UI_STATE_FOCUS)
        self.assertEqual(8, len(old))
        self.assertEqual([old[4]], required)
        selector = r.IOS_TIME_STATE_CLASS + "." + r.IOS_TIME_STATE_METHODS[0]
        self.assertEqual(["--tests", selector], r.gradle_command(
            "ios", plan, simulator="00000000-0000-4000-8000-000000000001")[-2:])
        self.assertEqual("genuine-uikit-application", plan["expected"][0]["native_test_host"])
        self.assertEqual(r.IOS_TIME_STATE_RECOVERY_FOCUS, app.application_test_focus(
            sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + selector]))
        result = subprocess.run([r.sys.executable, str(r.ROOT / "scripts/ci/library_tests.py"), "plan",
                                 "--suite", "ios", "--module", "calf-ui", "--focus", r.IOS_TIME_STATE_RECOVERY_FOCUS],
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(11, len(m.matrix("all")["include"]))

    def test_old_eight_missing_duplicate_failed_skipped_foreign_or_unexecuted_xml_is_red(self):
        helper = self.helper()
        helper.plan = self.plan
        cases = r.ui_application_focus_identities(r.IOS_TIME_STATE_RECOVERY_FOCUS)
        self.assertEqual(1, helper.collect(cases)["totals"]["passed"])
        self.assertEqual([], helper.collect(cases)["errors"])
        for invalid in ([], cases * 2, r.ui_application_focus_identities(r.IOS_UI_STATE_FOCUS)):
            self.assertTrue(helper.collect(invalid)["errors"])
        foreign = copy.deepcopy(cases)
        foreign[0]["name"] = foreign[0]["name"].replace("iosSimulatorArm64", "iosArm64")
        self.assertTrue(helper.collect(foreign)["errors"])
        for outcome in ("<failure/>", "<error/>", "<skipped/>"):
            self.assertTrue(helper.collect(cases, outcome=outcome)["errors"])
        self.assertTrue(helper.collect(cases, marker=0)["errors"])

    def test_one_case_still_requires_native_protocol_worker_runtime_binary_and_owned_cleanup(self):
        f = self.helper().fixture()
        f.plan = self.plan(f.root)
        f.cases = [{"classname": r.IOS_TIME_STATE_CLASS, "name": r.IOS_TIME_STATE_METHODS[0], "status": "passed"}]
        f.document["explicit_test_focus"] = r.IOS_TIME_STATE_RECOVERY_FOCUS
        f.document["application_protocol"].update(testcases=copy.deepcopy(f.cases), counts=r.case_counts(f.cases))
        f.modules[0]["testcases"] = f.xml_cases(f.cases)
        f.save()
        accepted = f.collect()
        self.assertEqual([], accepted["errors"])
        self.assertEqual(1, accepted["ios_applications"][0]["counts"]["passed"])
        for section, key, value in (("cleanup", "owned_app_absence_verified", False),
                                    ("cleanup", "owned_app_stopped_verified", False),
                                    ("runtime_after", "source_revision", "b" * 40),
                                    ("application_protocol", "testcases", [])):
            prior = f.document[section][key]
            f.document[section][key] = value; f.save()
            self.assertTrue(f.collect()["errors"])
            f.document[section][key] = prior
        f.document["application_protocol"]["completion"]["worker_terminated"] = False; f.save()
        self.assertTrue(f.collect()["errors"])

    def test_recovery_does_not_hide_declared_method_drift_or_remove_required_host(self):
        for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-file-picker",)), ("ios", None)):
            with self.assertRaises(ValueError): r.plan(r.ROOT, suite, only_modules=modules, focus=r.IOS_TIME_STATE_RECOVERY_FOCUS)
        f = self.helper().fixture()
        source = f.root / r.IOS_TIME_STATE_SOURCE
        original = source.read_text()
        for changed in (original.replace("@Test", "@IgnoredTest", 1), original + "\n@Test fun unrelated() {}\n",
                        original.replace("@Test fun " + r.IOS_TIME_STATE_METHODS[1], "@IgnoredTest fun " + r.IOS_TIME_STATE_METHODS[1])):
            source.write_text(changed)
            with self.assertRaises(ValueError): self.plan(f.root)
        source.write_text(original)
        (f.root / r.IOS_APPLICATION_SOURCES[0]).unlink()
        with self.assertRaises(ValueError): self.plan(f.root)


if __name__ == "__main__": unittest.main()
