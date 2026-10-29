"""Finite slider recovery/progress/deadline guards; synthetic, not native executions."""
import copy
import json
import subprocess
import unittest

import ios_ui_application as app
import library_tests as r
import test_ios_slider_lifecycle_focus as original
import workflow_matrix as matrix


class IosSliderRecoveryFocusTests(unittest.TestCase):
    def plan(self, focus, root=r.ROOT):
        return r.plan(root, "ios", only_modules=("calf-ui",), focus=focus)

    def test_two_unstarted_tap_methods_are_separate_from_both_failed_structure_methods_and_two_accepted_passes(self):
        for profile, focus, methods in (
            ("ios-slider-tap", r.IOS_SLIDER_TAP_FOCUS, r.IOS_SLIDER_LIFECYCLE_METHODS[4:]),
            ("ios-slider-pair-structure", r.IOS_SLIDER_PAIR_STRUCTURE_FOCUS, r.IOS_SLIDER_LIFECYCLE_METHODS[2:4]),
        ):
            row, = matrix.matrix(profile)["include"]
            self.assertEqual(("ios-iphone", "calf-ui", focus), tuple(row[k] for k in ("slot", "test-modules", "test-focus")))
            plan = self.plan(focus)
            self.assertTrue(r.validate_test_focus(plan))
            self.assertEqual(tuple(method + "[iosSimulatorArm64]" for method in methods),
                             tuple(c["name"] for c in plan["expected"][0]["required_testcases"]))
            self.assertEqual(2, len(r.ui_application_focus_filter(focus).split(",")))
            self.assertEqual(300, app.application_timeout_seconds(focus))
            slot, = matrix.preflight_plans(profile)["slots"]
            self.assertEqual(0, slot["exit_code"])
        self.assertFalse(set(r.IOS_SLIDER_LIFECYCLE_METHODS[:2]) & set(r.IOS_SLIDER_LIFECYCLE_METHODS[2:]))

    def drag_marker(self, renderer="Liquid", axis=1, observed="true"):
        return f"NATIVECMPKIT_SLIDER_DRAG renderer={renderer} axis={axis} started=true changed=true observed={observed}"

    def dragged_protocol(self):
        p, owner, method = self.protocol()
        for phase in app.SLIDER_STRUCTURAL_STEPS[:6]:
            p.feed(self.marker("Liquid", phase))
        return p, owner, method

    def test_pre_assertion_diagnostics_preserve_false_native_observer_without_finishing_or_inventing_the_root_cause(self):
        p, _, method = self.dragged_protocol()
        p.feed(self.drag_marker(observed="false"))
        partial = p.partial()
        self.assertEqual({"axis": 1, "started": True, "changed": True, "observed": False},
                         partial["slider_drag_observations"]["Liquid"][0])
        self.assertEqual(0, partial["counts"]["passed"])
        self.assertEqual(method, partial["unfinished_testcase"]["name"])
        self.assertIsNone(partial["completion"])
        with self.assertRaises(ValueError):
            p.feed(self.drag_marker())
        for line in (self.drag_marker("Cupertino"), self.drag_marker(axis=2), self.drag_marker(observed="unknown")):
            with self.subTest(line=line), self.assertRaises(ValueError):
                self.dragged_protocol()[0].feed(line)
        with self.assertRaises(ValueError):
            app.NativeProtocol().feed(self.drag_marker())

    def test_failure_only_real_pointer_cleanup_remains_an_original_failed_testcase_not_success(self):
        p, owner, method = self.dragged_protocol()
        p.feed(self.drag_marker(observed="false"))
        prefix = "NATIVECMPKIT_SLIDER_FAILURE_CLEANUP renderer=Liquid axis=1 phase="
        with self.assertRaises(ValueError):
            p.feed(prefix + "verified")
        p.feed(prefix + "request")
        with self.assertRaises(ValueError):
            p.feed(prefix + "request")
        p.feed(prefix + "verified")
        partial = p.partial()
        self.assertEqual([{"axis": 1, "phase": "request"}, {"axis": 1, "phase": "verified"}],
                         partial["slider_failure_cleanup_observations"]["Liquid"])
        p.feed(f"##teamcity[testFailed name='{method}' message='Original test assertion']")
        p.feed(f"##teamcity[testFinished name='{method}']")
        p.feed(f"##teamcity[testSuiteFinished name='{owner}']")
        p.feed("NATIVECMPKIT_UIKIT_COMPLETED runnerExit=0 workerTerminated=true")
        result = p.finish(0)
        self.assertEqual(1, result["counts"]["failures"])
        self.assertEqual(0, result["counts"]["passed"])
        with self.assertRaises(ValueError):
            p.feed(prefix + "failed")

    def test_source_observes_before_original_assertions_and_cleans_only_failed_held_pointer_without_changing_accepted_methods(self):
        source = (r.ROOT / r.IOS_SLIDER_LIFECYCLE_SOURCE).read_text()
        self.assertLess(source.index("NATIVECMPKIT_SLIDER_DRAG"), source.index("val start = starts.last()"))
        self.assertIn('assertTrue(changes > changesBeforeDrag, "$name must replace', source)
        self.assertIn("assertTrue(observedDragging)", source)
        self.assertIn("if (pointerOutstanding) cleanFailedStructuralPointer(renderer, axis, failure)", source)
        self.assertIn("throw failure // Never turn an assertion or cleanup failure into success.", source)
        self.assertIn("if (cleanup !== failure) failure.addSuppressed(cleanup)", source)
        self.assertIn("cancelScenePointerInput() // Reset the real scene", source)
        self.assertEqual(6, source.count("@Test fun "))
        self.assertNotIn("Assume.", source)

    def test_every_registered_native_application_focus_reaches_the_real_cli_and_keeps_its_suite_module_interlock(self):
        # Exercise the workflow's subprocess boundary, not only plan() in-process.
        for focus, spec in r.UI_APPLICATION_FOCUS_SPECS.items():
            module = spec.get("module", "calf-ui")
            command = [r.sys.executable, "-B", str(r.ROOT / "scripts/ci/library_tests.py"), "plan",
                       "--suite", "ios", "--module", module, "--focus", focus]
            with self.subTest(focus=focus):
                actual = subprocess.run(command, cwd=r.ROOT, capture_output=True, text=True, timeout=15)
                self.assertEqual(0, actual.returncode, actual.stderr)
                self.assertEqual(r.plan(r.ROOT, "ios", only_modules=(module,), focus=focus), json.loads(actual.stdout))
                wrong_suite = command.copy()
                wrong_suite[wrong_suite.index("--suite") + 1] = "desktop"
                refused = subprocess.run(wrong_suite, cwd=r.ROOT, capture_output=True, text=True, timeout=15)
                self.assertEqual(2, refused.returncode)
                self.assertIn("requires its exact reviewed suite and single --module", refused.stderr)

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
