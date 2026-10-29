"""Finite timeout-localization guards; synthetic tools, zero native executions."""
import copy
import re
import unittest

import ios_ui_application as app
import library_tests as tests
import test_ios_slider_lifecycle_focus as fixtures


class SliderTapDiagnosticsTests(unittest.TestCase):
    def protocol(self, renderer="Liquid"):
        protocol = app.NativeProtocol()
        protocol.feed("NATIVECMPKIT_UIKIT_ACTIVE mainWorker=1 ownedWorker=2")
        owner, method = app.SLIDER_TAP_CASES[renderer]
        protocol.feed(f"##teamcity[testSuiteStarted name='{owner}']")
        protocol.feed(f"##teamcity[testStarted name='{method}']")
        return protocol, owner, method

    def marker(self, renderer, phase):
        return f"NATIVECMPKIT_SLIDER_TAP renderer={renderer} phase={phase}"

    def finish(self, protocol, owner, method):
        protocol.feed(f"##teamcity[testFinished name='{method}']")
        protocol.feed(f"##teamcity[testSuiteFinished name='{owner}']")
        protocol.feed("NATIVECMPKIT_UIKIT_COMPLETED runnerExit=0 workerTerminated=true")
        return protocol.finish(0)

    def test_both_renderers_require_all24_actual_phases_before_native_passing_completion(self):
        self.assertEqual(24, len(app.SLIDER_TAP_STEPS))
        for renderer in app.SLIDER_TAP_CASES:
            protocol, owner, method = self.protocol(renderer)
            for phase in app.SLIDER_TAP_STEPS:
                protocol.feed(self.marker(renderer, phase))
            result = self.finish(protocol, owner, method)
            self.assertEqual(1, result["counts"]["passed"])
            self.assertEqual([{"phase": phase} for phase in app.SLIDER_TAP_STEPS],
                             result["slider_tap_observations"][renderer])
            with self.assertRaises(ValueError): protocol.feed(self.marker(renderer, "complete"))

    def test_missing_duplicate_reordered_foreign_malformed_or_outside_case_markers_are_rejected(self):
        for line in (self.marker("Liquid", "content-installed"),
                     self.marker("Cupertino", "before-content"),
                     self.marker("Liquid", "unknown"),
                     self.marker("foreign", "before-content")):
            protocol, _, _ = self.protocol()
            with self.subTest(line=line), self.assertRaises(ValueError): protocol.feed(line)
        first = self.marker("Liquid", "before-content")
        protocol, _, method = self.protocol()
        protocol.feed(first)
        with self.assertRaises(ValueError): protocol.feed(first)
        with self.assertRaises(ValueError): protocol.feed(f"##teamcity[testFinished name='{method}']")
        with self.assertRaises(ValueError): app.NativeProtocol().feed(first)

    def test_last_finite_phase_localizes_interruption_but_cannot_finish_a_case_or_worker(self):
        protocol, _, method = self.protocol()
        index = app.SLIDER_TAP_STEPS.index("cancelled-injector") + 1
        for phase in app.SLIDER_TAP_STEPS[:index]: protocol.feed(self.marker("Liquid", phase))
        partial = protocol.partial()
        self.assertEqual([{"phase": phase} for phase in app.SLIDER_TAP_STEPS[:index]],
                         partial["slider_tap_observations"]["Liquid"])
        self.assertEqual(method, partial["unfinished_testcase"]["name"])
        self.assertEqual(0, partial["counts"]["passed"])
        self.assertIsNone(partial["completion"])
        with self.assertRaises(ValueError): protocol.finish(0)

    def test_original_assertion_failure_is_retained_even_when_the_native_runner_exits_zero(self):
        protocol, owner, method = self.protocol()
        protocol.feed(self.marker("Liquid", "before-content"))
        protocol.feed(f"##teamcity[testFailed name='{method}' message='Original assertion failure']")
        result = self.finish(protocol, owner, method)
        self.assertEqual(1, result["counts"]["failures"])
        self.assertEqual(0, result["counts"]["passed"])
        self.assertEqual([{"phase": "before-content"}], result["slider_tap_observations"]["Liquid"])

    def test_forged_report_only_pass_cannot_omit_or_change_either_renderer_sequence(self):
        helper = fixtures.IosSliderLifecycleTests()
        self.addCleanup(helper.doCleanups)
        fixture = helper.fixture()
        self.assertEqual([], fixture.collect()["errors"])
        original = copy.deepcopy(fixture.document)
        for invalid in (None, [], "foreign"):
            fixture.document = copy.deepcopy(original)
            fixture.document["application_protocol"]["slider_tap_observations"] = invalid
            fixture.save()
            self.assertTrue(fixture.collect()["errors"])
        for renderer in app.SLIDER_TAP_CASES:
            for mutate in (lambda rows: rows.clear(), lambda rows: rows.pop(),
                           lambda rows: rows[0].update(phase="foreign")):
                fixture.document = copy.deepcopy(original)
                mutate(fixture.document["application_protocol"]["slider_tap_observations"][renderer])
                fixture.save()
                self.assertTrue(fixture.collect()["errors"])

    def test_diagnostics_keep_all_original_actions_assertions_and_512ms_waits(self):
        source = (tests.ROOT / tests.IOS_SLIDER_LIFECYCLE_SOURCE).read_text()
        body = source.split("    private fun tapDragCancellation", 1)[1].split("    private fun tapPhase", 1)[0]
        self.assertEqual(app.SLIDER_TAP_STEPS, tuple(re.findall(r'tapPhase\(renderer, "([a-z-]+)"\)', body)))
        self.assertEqual(2, body.count("mainClock.advanceTimeBy(512)"))
        for original in ("assertEquals(-1f, value); assertEquals(2, finished)",
                         "assertEquals(-1f, value); assertEquals(4, finished)",
                         "assertEquals(countAfterSuccessfulInput, values.size",
                         "it.start === cancelled", "assertFalse(observedDragging)",
                         "assertEquals(4, finished)", "assertEquals(countAtCancellation, values.size)",
                         "values.all { it in setOf(-1f, -.5f, 0f, .5f, 1f) }",
                         "assertEquals(-.5f, value); assertEquals(5, finished)",
                         "cancelScenePointerInput()"):
            self.assertIn(original, body)
        self.assertEqual(6, source.count("@Test fun "))
        self.assertNotIn("Assume.", body)
        self.assertNotIn("Thread.sleep", body)


if __name__ == "__main__": unittest.main()
