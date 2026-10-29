"""Finite slider recovery/progress/deadline guards; synthetic, not native executions."""
import copy
import unittest

import ios_ui_application as app
import library_tests as r
import test_ios_slider_lifecycle_focus as original
import workflow_matrix as matrix


class IosSliderRecoveryFocusTests(unittest.TestCase):
    def plan(self, focus, root=r.ROOT):
        return r.plan(root, "ios", only_modules=("calf-ui",), focus=focus)

    def fixture(self, focus):
        helper = original.IosSliderLifecycleTests()
        self.addCleanup(helper.doCleanups)
        f = helper.fixture()
        f.plan = self.plan(focus, f.root)
        f.cases = [{"classname": c["classname"].removeprefix(r.IOS_APPLICATION_TASK + "."),
                    "name": c["name"].removesuffix("[iosSimulatorArm64]"), "status": "passed"}
                   for c in r.ui_application_focus_identities(focus)]
        f.document["explicit_test_focus"] = focus
        f.document["application_protocol"].update(testcases=copy.deepcopy(f.cases), counts=r.case_counts(f.cases))
        f.modules[0]["testcases"] = f.xml_cases(f.cases)
        f.save()
        return f

    def test_three_unstarted_and_one_interrupted_exact_methods_are_disjoint_and_do_not_replay_two_passes(self):
        for profile, focus, methods in (
            ("ios-slider-remaining", r.IOS_SLIDER_REMAINING_FOCUS, r.IOS_SLIDER_LIFECYCLE_METHODS[3:]),
            ("ios-slider-structure", r.IOS_SLIDER_STRUCTURE_FOCUS, r.IOS_SLIDER_LIFECYCLE_METHODS[2:3]),
        ):
            row, = matrix.matrix(profile)["include"]
            self.assertEqual(("ios-iphone", "calf-ui", focus), tuple(row[k] for k in ("slot", "test-modules", "test-focus")))
            plan = self.plan(focus)
            self.assertFalse(plan["complete_suite_requested"])
            self.assertTrue(r.validate_test_focus(plan))
            self.assertEqual(tuple(n + "[iosSimulatorArm64]" for n in methods),
                             tuple(c["name"] for c in plan["expected"][0]["required_testcases"]))
            filters = r.ui_application_focus_filter(focus).split(",")
            self.assertEqual(len(methods), len(filters))
            self.assertTrue(all(not any(n in f for n in r.IOS_SLIDER_LIFECYCLE_METHODS[:2]) for f in filters))
            self.assertEqual(focus, app.application_test_focus(sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + ",".join(reversed(filters))]))
        self.assertEqual(6, len(r.ui_application_focus_identities(r.IOS_SLIDER_LIFECYCLE_FOCUS)))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))

    def test_exact_fresh_nonzero_reports_and_full_native_worker_runtime_binary_cleanup_are_still_required(self):
        for focus in (r.IOS_SLIDER_REMAINING_FOCUS, r.IOS_SLIDER_STRUCTURE_FOCUS):
            f = self.fixture(focus)
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
            f.document["runtime_after"]["source_revision"] = f.document["source_revision"]
            f.modules[0]["testcases"] = []; f.save()
            self.assertTrue(f.collect()["errors"])

    def protocol(self, renderer="Liquid"):
        p = app.NativeProtocol()
        p.feed("NATIVECMPKIT_UIKIT_ACTIVE mainWorker=1 ownedWorker=2")
        owner, method = app.SLIDER_STRUCTURAL_CASES[renderer]
        p.feed(f"##teamcity[testSuiteStarted name='{owner}']")
        p.feed(f"##teamcity[testStarted name='{method}']")
        return p, owner, method

    def marker(self, renderer, step):
        axis, phase = step
        return f"NATIVECMPKIT_SLIDER_STRUCTURE renderer={renderer} axis={axis} phase={phase}"

    def test_each_renderer_needs_all_62_native_phases_before_a_passing_structural_result(self):
        self.assertEqual(62, len(app.SLIDER_STRUCTURAL_STEPS))
        for renderer in app.SLIDER_STRUCTURAL_CASES:
            p, owner, method = self.protocol(renderer)
            for step in app.SLIDER_STRUCTURAL_STEPS: p.feed(self.marker(renderer, step))
            p.feed(f"##teamcity[testFinished name='{method}']")
            p.feed(f"##teamcity[testSuiteFinished name='{owner}']")
            p.feed("NATIVECMPKIT_UIKIT_COMPLETED runnerExit=0 workerTerminated=true")
            result = p.finish(0)
            self.assertEqual(1, result["counts"]["passed"])
            self.assertEqual(62, len(result["slider_structural_observations"][renderer]))
            self.assertEqual({"axis": 6, "phase": "fresh-input-verified"}, result["slider_structural_observations"][renderer][-1])

    def test_missing_reordered_duplicate_foreign_malformed_or_outside_case_phase_cannot_pass(self):
        p, _, method = self.protocol()
        with self.assertRaises(ValueError): p.feed(f"##teamcity[testFinished name='{method}']")
        for invalid in (
            self.marker("Cupertino", app.SLIDER_STRUCTURAL_STEPS[0]),
            self.marker("Liquid", app.SLIDER_STRUCTURAL_STEPS[1]),
            "NATIVECMPKIT_SLIDER_STRUCTURE renderer=Liquid axis=7 phase=before-reset",
            "NATIVECMPKIT_SLIDER_STRUCTURE renderer=unknown axis=0 phase=before-content",
        ):
            p, _, _ = self.protocol()
            with self.assertRaises(ValueError): p.feed(invalid)
        p, _, _ = self.protocol(); first = self.marker("Liquid", app.SLIDER_STRUCTURAL_STEPS[0]); p.feed(first)
        with self.assertRaises(ValueError): p.feed(first)
        with self.assertRaises(ValueError): app.NativeProtocol().feed(first)

    def test_partial_progress_identifies_the_last_step_but_never_finishes_a_case_or_worker(self):
        p, _, method = self.protocol()
        for step in app.SLIDER_STRUCTURAL_STEPS[:7]: p.feed(self.marker("Liquid", step))
        partial = p.partial()
        self.assertEqual(0, partial["counts"]["passed"])
        self.assertIsNone(partial["completion"])
        self.assertFalse(partial["complete_native_lifecycle"])
        self.assertEqual(method, partial["unfinished_testcase"]["name"])
        self.assertEqual({"axis": 1, "phase": "before-replace"}, partial["slider_structural_observations"]["Liquid"][-1])
        with self.assertRaises(ValueError): p.finish(0)

    def test_only_focused_slider_transport_has_a_stricter_300_second_deadline(self):
        self.assertEqual(1920, app.application_timeout_seconds(None))
        self.assertEqual(1920, app.application_timeout_seconds(r.IOS_UI_STATE_FOCUS))
        for focus in (r.IOS_SLIDER_LIFECYCLE_FOCUS, r.IOS_SLIDER_REMAINING_FOCUS, r.IOS_SLIDER_STRUCTURE_FOCUS):
            self.assertEqual(300, app.application_timeout_seconds(focus))
        with self.assertRaises(ValueError): app.application_timeout_seconds("unknown")
        source = (r.ROOT / "scripts/ci/ios_ui_application.py").read_text()
        self.assertIn("protocol, timeout=application_timeout_seconds(focus)", source)
        self.assertIn('"timeout_seconds": timeout', source)
        native = (r.ROOT / r.IOS_SLIDER_LIFECYCLE_SOURCE).read_text()
        self.assertEqual(6, native.count("@Test fun "))
        self.assertIn("changesToContract.withIndex()", native)
        self.assertIn('structuralPhase(renderer, axis, "before-replace")', native)
        self.assertIn('structuralPhase(renderer, axis, "fresh-input-verified")', native)
        self.assertIn('assertFalse(observedDragging, "$name must clear', native)
        self.assertNotIn("Thread.sleep", native)
        self.assertNotIn("Assume.", native)


if __name__ == "__main__": unittest.main()
