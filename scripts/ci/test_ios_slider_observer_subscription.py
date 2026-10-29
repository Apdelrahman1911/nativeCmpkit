"""Shared native-fixture subscription/diagnostic guards; zero native executions."""
import unittest

import ios_ui_application as app
import library_tests as tests
import test_ios_slider_recovery_focus as recovery
import test_ios_slider_tap_diagnostics as tap


class SliderObserverSubscriptionTests(unittest.TestCase):
    def source(self):
        return (tests.ROOT / tests.IOS_SLIDER_LIFECYCLE_SOURCE).read_text()

    def test_both_actual_sources_are_read_during_composition_not_lazily_inside_sideeffect(self):
        source = self.source()
        structure = source.split("    private fun structuralReplacement", 1)[1].split(
            "    private fun ComposeUiTest.cleanFailedStructuralPointer", 1)[0]
        cancellation = source.split("    private fun tapDragCancellation", 1)[1].split(
            "    private fun tapPhase", 1)[0]
        self.assertIn("val firstDragging = first.collectIsDraggedAsState().value", structure)
        self.assertIn("val secondDragging = second.collectIsDraggedAsState().value", structure)
        self.assertIn("val dragging = if (source === first) firstDragging else secondDragging", structure)
        self.assertIn("observedFirstDragging = firstDragging", structure)
        self.assertIn("observedSecondDragging = secondDragging", structure)
        self.assertIn("val dragging = source.collectIsDraggedAsState().value", cancellation)
        self.assertNotIn("val dragging by", structure + cancellation)
        self.assertIn("assertFalse(oldOwnerDragging()", structure)

    def test_real_observer_and_cancel_counts_are_captured_before_waits_or_cancellation_assertions(self):
        source = self.source()
        structure = source.split("    private fun structuralReplacement", 1)[1].split(
            "    private fun ComposeUiTest.cleanFailedStructuralPointer", 1)[0]
        cancellation = source.split("    private fun tapDragCancellation", 1)[1].split(
            "    private fun tapPhase", 1)[0]
        self.assertLess(structure.index('observerSnapshot(renderer, axis, "drag-wait"'),
                        structure.index("observedDragging && changes > changesBeforeDrag"))
        self.assertLess(structure.index('observerSnapshot(renderer, axis, "cancel-wait"'),
                        structure.index("!observedDragging && !oldOwnerDragging()"))
        self.assertLess(cancellation.index('observerSnapshot(renderer, 0, "cancel-wait"'),
                        cancellation.index("val cancelled ="))
        self.assertEqual(6, source.count("@Test fun "))
        self.assertEqual(2, cancellation.count("mainClock.advanceTimeBy(512)"))
        for original in ("assertTrue(observedDragging)", "it.start === start", "it.start === cancelled",
                         "assertFalse(observedDragging)", "assertEquals(4, finished)", "throw failure"):
            self.assertIn(original, source)
        self.assertNotIn("Thread.sleep", source)
        self.assertNotIn("Assume.", source)

    def marker(self, axis=1, phase="drag-wait", renderer="Liquid", observed="false"):
        return (f"NATIVECMPKIT_SLIDER_OBSERVER renderer={renderer} axis={axis} phase={phase} "
                f"starts=1 cancelled=0 stopped=0 observed={observed} finished=0")

    def structural_protocol(self):
        helper = recovery.IosSliderRecoveryFocusTests()
        protocol, owner, method = helper.protocol()
        for step in app.SLIDER_STRUCTURAL_STEPS[:5]:
            protocol.feed(helper.marker("Liquid", step))
        return protocol, owner, method

    def test_false_pre_wait_snapshot_survives_interruption_and_never_completes_the_native_case(self):
        protocol, _, method = self.structural_protocol()
        protocol.feed(self.marker())
        partial = protocol.partial()
        self.assertEqual([{"axis": 1, "phase": "drag-wait", "starts": 1,
                           "cancelled": 0, "stopped": 0, "observed": False, "finished": 0}],
                         partial["slider_observer_observations"]["Liquid"])
        self.assertEqual(0, partial["counts"]["passed"])
        self.assertEqual(method, partial["unfinished_testcase"]["name"])
        self.assertIsNone(partial["completion"])
        with self.assertRaises(ValueError): protocol.finish(0)

    def test_duplicate_reordered_foreign_unbounded_malformed_or_outside_case_snapshots_are_rejected(self):
        for line in (self.marker(axis=2), self.marker(phase="cancel-wait"), self.marker(renderer="Cupertino"),
                     self.marker(observed="unknown"), self.marker().replace("starts=1", "starts=999999"),
                     self.marker().replace("finished=0", "finished=-1"), self.marker().replace("axis=1", "axis=0")):
            with self.subTest(line=line), self.assertRaises(ValueError):
                self.structural_protocol()[0].feed(line)
        protocol, _, _ = self.structural_protocol()
        protocol.feed(self.marker())
        with self.assertRaises(ValueError): protocol.feed(self.marker())
        with self.assertRaises(ValueError): app.NativeProtocol().feed(self.marker())

    def test_tap_cancel_snapshot_is_exactly_scoped_before_original_assertions_and_retains_original_failure(self):
        helper = tap.SliderTapDiagnosticsTests()
        protocol, owner, method = helper.protocol()
        for phase in app.SLIDER_TAP_STEPS[:app.SLIDER_TAP_STEPS.index("cancellation-idle") + 1]:
            protocol.feed(helper.marker("Liquid", phase))
        line = self.marker(axis=0, phase="cancel-wait").replace("starts=1", "starts=2").replace(
            "cancelled=0", "cancelled=1").replace("finished=0", "finished=4")
        protocol.feed(line)
        protocol.feed(f"##teamcity[testFailed name='{method}' message='Original cancellation assertion']")
        result = helper.finish(protocol, owner, method)
        self.assertEqual(1, result["counts"]["failures"])
        self.assertEqual(0, result["counts"]["passed"])
        self.assertEqual(1, result["slider_observer_observations"]["Liquid"][0]["cancelled"])

    def test_one_full_native_process_keeps_structural_and_tap_diagnostics_independent_for_each_renderer(self):
        for renderer in app.SLIDER_TAP_CASES:
            with self.subTest(renderer=renderer):
                protocol = app.NativeProtocol()
                protocol.feed("NATIVECMPKIT_UIKIT_ACTIVE mainWorker=1 ownedWorker=2")
                owner, structural = app.SLIDER_STRUCTURAL_CASES[renderer]
                protocol.feed(f"##teamcity[testSuiteStarted name='{owner}']")
                protocol.feed(f"##teamcity[testStarted name='{structural}']")
                for axis, phase in app.SLIDER_STRUCTURAL_STEPS:
                    protocol.feed(f"NATIVECMPKIT_SLIDER_STRUCTURE renderer={renderer} axis={axis} phase={phase}")
                    if phase in ("before-drag", "replaced"):
                        protocol.feed(self.marker(axis=axis, renderer=renderer,
                            phase="drag-wait" if phase == "before-drag" else "cancel-wait"))
                protocol.feed(f"##teamcity[testFinished name='{structural}']")
                _, method = app.SLIDER_TAP_CASES[renderer]
                protocol.feed(f"##teamcity[testStarted name='{method}']")
                for phase in app.SLIDER_TAP_STEPS:
                    protocol.feed(f"NATIVECMPKIT_SLIDER_TAP renderer={renderer} phase={phase}")
                    if phase == "cancellation-idle":
                        protocol.feed(self.marker(axis=0, phase="cancel-wait", renderer=renderer))
                protocol.feed(f"##teamcity[testFinished name='{method}']")
                protocol.feed(f"##teamcity[testSuiteFinished name='{owner}']")
                protocol.feed("NATIVECMPKIT_UIKIT_COMPLETED runnerExit=0 workerTerminated=true")
                result = protocol.finish(0)
                self.assertEqual(2, result["counts"]["passed"])
                self.assertEqual(13, len(result["slider_observer_observations"][renderer]))


if __name__ == "__main__": unittest.main()
