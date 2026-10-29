"""Finite shared-slider selection/receipt guards; NOT native input functionality tests."""
import copy
import subprocess
import unittest

import ios_ui_application as app
import library_tests as r
import test_ios_ui_state_focus as batch
import workflow_matrix as m


class IosSliderLifecycleTests(unittest.TestCase):
    def plan(self, root=r.ROOT):
        return r.plan(root, "ios", only_modules=("calf-ui",), focus=r.IOS_SLIDER_LIFECYCLE_FOCUS)

    def helper(self):
        helper = batch.IOSUiStateFocusTests("test_eight_exact_methods_single_real_application_and_cli_do_not_replay_dates")
        self.addCleanup(helper.doCleanups)
        return helper

    def test_six_new_both_renderer_methods_share_one_app_and_never_replay_accepted_controls(self):
        row, = m.matrix("ios-slider-lifecycle")["include"]
        self.assertEqual(("ios-iphone", "calf-ui", r.IOS_SLIDER_LIFECYCLE_FOCUS),
                         tuple(row[k] for k in ("slot", "test-modules", "test-focus")))
        plan = self.plan(); required = plan["expected"][0]
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual("genuine-uikit-application", required["native_test_host"])
        self.assertEqual(6, len(required["required_testcases"]))
        filters = r.ui_application_focus_filter(r.IOS_SLIDER_LIFECYCLE_FOCUS).split(",")
        selectors = [arg for value in filters for arg in ("--tests", value)]
        self.assertEqual(selectors, r.gradle_command("ios", plan,
            simulator="00000000-0000-4000-8000-000000000001")[-12:])
        self.assertEqual(3, sum(".liquid" in f for f in filters))
        self.assertEqual(3, sum(".cupertino" in f for f in filters))
        for accepted in (r.IOS_UI_STATE_FOCUS, r.IOS_SLIDER_NUMERIC_FOCUS, r.IOS_SWITCH_CANCELLATION_FOCUS):
            old = {(c["classname"], c["name"]) for c in r.ui_application_focus_identities(accepted)}
            new = {(c["classname"], c["name"]) for c in required["required_testcases"]}
            self.assertFalse(old & new)
        self.assertEqual(r.IOS_SLIDER_LIFECYCLE_FOCUS, app.application_test_focus(
            sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + ",".join(reversed(filters))]))
        result = subprocess.run([r.sys.executable, str(r.ROOT / "scripts/ci/library_tests.py"), "plan",
                                 "--suite", "ios", "--module", "calf-ui", "--focus", r.IOS_SLIDER_LIFECYCLE_FOCUS],
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(11, len(m.matrix("all")["include"]))

    def test_missing_extra_duplicate_failed_skipped_wrong_target_or_unexecuted_xml_is_rejected(self):
        helper = self.helper(); helper.plan = self.plan
        cases = r.ui_application_focus_identities(r.IOS_SLIDER_LIFECYCLE_FOCUS)
        self.assertEqual(6, helper.collect(cases)["totals"]["passed"])
        self.assertEqual([], helper.collect(cases)["errors"])
        for invalid in ([], cases[:-1], cases * 2, cases + r.ui_application_focus_identities(r.IOS_UI_STATE_FOCUS)):
            self.assertTrue(helper.collect(invalid)["errors"])
        foreign = copy.deepcopy(cases); foreign[0]["name"] += "[foreign]"
        self.assertTrue(helper.collect(foreign)["errors"])
        for outcome in ("<failure/>", "<error/>", "<skipped/>"):
            self.assertTrue(helper.collect(cases, outcome=outcome)["errors"])
        self.assertTrue(helper.collect(cases, marker=0)["errors"])

    def fixture(self):
        f = self.helper().fixture()
        f.write(r.IOS_SLIDER_LIFECYCLE_SOURCE, (r.ROOT / r.IOS_SLIDER_LIFECYCLE_SOURCE).read_bytes())
        f.plan = self.plan(f.root)
        f.cases = [{"classname": r.IOS_SLIDER_LIFECYCLE_CLASS, "name": n, "status": "passed"}
                   for n in r.IOS_SLIDER_LIFECYCLE_METHODS]
        f.document["explicit_test_focus"] = r.IOS_SLIDER_LIFECYCLE_FOCUS
        f.document["application_protocol"].update(testcases=copy.deepcopy(f.cases), counts=r.case_counts(f.cases))
        f.modules[0]["testcases"] = f.xml_cases(f.cases); f.save()
        return f

    def test_six_cases_still_need_exact_native_protocol_worker_runtime_binary_and_cleanup(self):
        f = self.fixture()
        self.assertEqual([], f.collect()["errors"])
        for key in ("owned_app_absence_verified", "owned_app_stopped_verified", "owned_local_bundle_removed"):
            f.document["cleanup"][key] = False; f.save()
            self.assertTrue(f.collect()["errors"])
            f.document["cleanup"][key] = True
        f.document["application_protocol"]["completion"]["worker_terminated"] = False; f.save()
        self.assertTrue(f.collect()["errors"])
        f.document["application_protocol"]["completion"]["worker_terminated"] = True
        f.document["runtime_after"]["source_revision"] = "b" * 40; f.save()
        self.assertTrue(f.collect()["errors"])

    def test_declaration_host_and_module_drift_cannot_reduce_the_related_selection(self):
        for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-file-picker",)), ("ios", None)):
            with self.assertRaises(ValueError): r.plan(r.ROOT, suite, only_modules=modules, focus=r.IOS_SLIDER_LIFECYCLE_FOCUS)
        f = self.fixture(); source = f.root / r.IOS_SLIDER_LIFECYCLE_SOURCE; original = source.read_text()
        for changed in (original.replace("@Test", "@IgnoredTest", 1), original + "\n@Test fun unrelated() {}\n"):
            source.write_text(changed)
            with self.assertRaises(ValueError): self.plan(f.root)
        source.write_text(original); (f.root / r.IOS_APPLICATION_SOURCES[0]).unlink()
        with self.assertRaises(ValueError): self.plan(f.root)

    def test_each_axis_requires_live_input_current_callbacks_and_exact_cancel_pairs_not_stubs(self):
        source = (r.ROOT / r.IOS_SLIDER_LIFECYCLE_SOURCE).read_text()
        for value in ("LiquidGlassSliderImpl(value, change", "CupertinoSlider(value, change",
                      '"measured width"', '"density and thumb geometry"', '"RTL direction"',
                      '"range" to', '"steps" to', '"interaction source"', "cancelScenePointerInput()",
                      "changes > changesBeforeDrag", "assertTrue(currentChanges > 0", "it.start === start",
                      "assertFalse(observedDragging", "mainClock.advanceTimeBy(512)"):
            self.assertIn(value, source)
        self.assertNotIn("Thread.sleep", source)
        self.assertNotIn("Assume.", source)
        self.assertEqual(6, source.count("@Test fun "))
        cancelled = source.index('assertFalse(observedDragging, "$name must clear')
        reset = source.index("runOnIdle { value = (range.start + range.endInclusive) / 2f }", cancelled)
        fresh = source.index('"$name replacement must accept a fresh current-domain tap"', reset)
        self.assertLess(cancelled, reset)
        self.assertLess(reset, fresh)
        self.assertIn('"$name hoisted reset is not an input callback"', source[reset:fresh])
        self.assertIn('"$name hoisted reset is not input completion"', source[reset:fresh])


if __name__ == "__main__": unittest.main()
