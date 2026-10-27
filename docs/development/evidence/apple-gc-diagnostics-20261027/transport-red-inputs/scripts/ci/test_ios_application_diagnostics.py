"""Python/source diagnostics guards; never real UIImage/GC/native test passes."""
import io
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import ios_ui_application as a
import test_ios_ui_application as f

BUNDLE = "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + "a" * 12 + ".t" + "b" * 32
CLASS = "com.mohamedrejeb.calf.ui.utils.UIImageConversionTest"
METHOD = "returnedImageOwnsItsPixelsAfterTemporaryArraysAndContextsAreCollected"


def marker(phase, iteration=None, main=True):
    return "NATIVECMPKIT_UIKIT_IMAGE_LIFETIME phase=" + phase + (" iteration=" + str(iteration) if iteration is not None else "") + " mainThread=" + str(main).lower()


def markers():
    result = [marker("retained-ready")]
    for iteration in range(1, 21):
        result += [marker("before-conversion", iteration), marker("before-gc", iteration), marker("after-gc", iteration)]
    return result + [marker("before-verify"), marker("verified")]


def begun():
    protocol = a.NativeProtocol()
    for line in [f.ACTIVE, f.frame("testSuiteStarted", name=CLASS), f.frame("testStarted", name=METHOD)]:
        protocol.feed(line)
    return protocol


class PartialProtocolTests(unittest.TestCase):
    def test_a_started_case_is_running_not_passing_before_actual_finish(self):
        protocol = begun()
        self.assertEqual("running", next(iter(protocol.cases.values()))["status"])
        result = protocol.partial()
        self.assertFalse(result["complete_native_lifecycle"])
        self.assertEqual(0, result["counts"]["executed"]); self.assertEqual(0, result["counts"]["passed"])
        self.assertEqual([], result["testcases"])
        self.assertEqual({"classname": CLASS, "name": METHOD, "status": "incomplete", "failure_frame_observed": False},
                         result["unfinished_testcase"])

    def test_failure_frame_without_finish_is_still_unfinished_not_counted(self):
        protocol = begun(); protocol.feed(f.frame("testFailed", name=METHOD, message="synthetic failure"))
        result = protocol.partial()
        self.assertEqual(0, result["counts"]["tests"])
        self.assertTrue(result["unfinished_testcase"]["failure_frame_observed"])
        with self.assertRaises(ValueError): protocol.finish(1)

    def test_finished_cases_are_counted_separately_from_a_later_interruption(self):
        protocol = a.NativeProtocol()
        for line in f.complete_lines()[:-2]: protocol.feed(line)
        protocol.feed(f.frame("testStarted", name="interrupted"))
        result = protocol.partial()
        self.assertEqual(1, result["counts"]["executed"]); self.assertEqual(1, result["counts"]["passed"])
        self.assertEqual("interrupted", result["unfinished_testcase"]["name"])
        self.assertIsNone(result["completion"])

    def test_only_exact_source_bound_pre_activation_launch_line_supplies_application_pid(self):
        protocol = a.NativeProtocol(bundle_id=BUNDLE)
        protocol.feed("foreign.application: 123")
        self.assertIsNone(protocol.observed_launch_pid)
        protocol.feed(BUNDLE + ": 321")
        self.assertEqual(321, protocol.observed_launch_pid)
        self.assertEqual(321, protocol.partial()["observed_launch_pid"])
        with self.assertRaises(ValueError): protocol.feed(BUNDLE + ": 321")

    def test_invalid_zero_overflow_or_late_launch_pid_is_not_accepted(self):
        for text in ["0", "-1", "2147483648", "True", "321 private suffix"]:
            with self.subTest(text=text):
                protocol = a.NativeProtocol(bundle_id=BUNDLE)
                with self.assertRaises(ValueError): protocol.feed(BUNDLE + ": " + text)
                self.assertIsNone(protocol.observed_launch_pid)
        protocol = a.NativeProtocol(bundle_id=BUNDLE); protocol.feed(f.ACTIVE)
        with self.assertRaises(ValueError): protocol.feed(BUNDLE + ": 321")

    def test_foreign_or_shell_shaped_expected_bundle_is_refused(self):
        for bundle in ["foreign.bundle", BUNDLE + "\n", BUNDLE + "; echo unsafe"]:
            with self.subTest(bundle=bundle), self.assertRaises(ValueError): a.NativeProtocol(bundle_id=bundle)

    def test_complete_native_lifecycle_requires_closed_cases_and_suites(self):
        protocol = begun()
        with self.assertRaises(ValueError): protocol.feed(f.COMPLETE)
        self.assertFalse(protocol.partial()["complete_native_lifecycle"])


class ImageLifetimeProtocolTests(unittest.TestCase):
    def test_all_twenty_actual_collection_positions_are_finite_and_correctly_ordered(self):
        protocol = begun()
        for line in markers(): protocol.feed(line)
        result = protocol.partial()["image_lifetime_observation"]
        self.assertEqual(63, result["marker_count"])
        self.assertEqual("verified", result["last_phase"])
        self.assertTrue(result["retained_image_bytes_verified"])
        # Even all diagnostics cannot finish a testcase or runner on their own.
        self.assertEqual(0, protocol.partial()["counts"]["passed"])
        for line in [f.frame("testFinished", name=METHOD), f.frame("testSuiteFinished", name=CLASS), f.COMPLETE]: protocol.feed(line)
        self.assertEqual(1, protocol.finish(0)["counts"]["passed"])

    def test_interruption_between_before_and_after_gc_remains_exactly_located_and_unfinished(self):
        protocol = begun()
        for line in markers()[:6]: protocol.feed(line)
        result = protocol.partial()
        self.assertEqual("before-gc", result["image_lifetime_observation"]["last_phase"])
        self.assertEqual(2, result["image_lifetime_observation"]["last_iteration"])
        self.assertFalse(result["image_lifetime_observation"]["retained_image_bytes_verified"])
        self.assertEqual(0, result["counts"]["passed"])

    def test_skipped_duplicate_reordered_zero_or_unbounded_iteration_is_rejected(self):
        for extra in [marker("before-gc", 1), marker("before-conversion", 0), marker("before-conversion", 21),
                      marker("retained-ready"), marker("before-conversion", 2), marker("verified")]:
            with self.subTest(extra=extra):
                protocol = begun(); protocol.feed(marker("retained-ready"))
                with self.assertRaises(ValueError): protocol.feed(extra)

    def test_marker_cannot_cross_test_class_name_suite_activation_or_completion(self):
        protocols = [a.NativeProtocol()]
        other = a.NativeProtocol()
        for line in f.complete_lines()[:3]: other.feed(line)
        protocols.append(other)
        closed = a.NativeProtocol()
        for line in f.complete_lines(): closed.feed(line)
        protocols.append(closed)
        for protocol in protocols:
            with self.subTest(protocol=protocol), self.assertRaises(ValueError): protocol.feed(marker("retained-ready"))
            self.assertIsNone(protocol.partial()["image_lifetime_observation"])

    def test_malformed_private_payload_or_unknown_phase_cannot_enter_receipts(self):
        for line in [marker("retained-ready") + " private=synthetic-secret", marker("unknown"),
                     marker("before-gc", True), marker("before-gc", 10**30)]:
            with self.subTest(line=line):
                protocol = begun()
                with self.assertRaises(ValueError): protocol.feed(line)
                self.assertIsNone(protocol.partial()["image_lifetime_observation"])

    def test_observed_nonmain_callback_is_retained_as_failure_not_weakened(self):
        protocol = begun()
        with self.assertRaises(ValueError): protocol.feed(marker("retained-ready", main=False))
        self.assertFalse(protocol.partial()["image_lifetime_observation"]["main_thread"])
        self.assertEqual(0, protocol.partial()["counts"]["passed"])

    def test_missing_diagnostics_cannot_be_a_passing_image_lifetime_test(self):
        protocol = begun()
        with self.assertRaises(ValueError): protocol.feed(f.frame("testFinished", name=METHOD))
        self.assertEqual(0, protocol.partial()["counts"]["passed"])

    def test_a_real_failure_can_finish_but_is_never_promoted_by_partial_diagnostics(self):
        protocol = begun(); protocol.feed(marker("retained-ready"))
        for line in [f.frame("testFailed", name=METHOD, message="synthetic assertion"),
                     f.frame("testFinished", name=METHOD), f.frame("testSuiteFinished", name=CLASS), f.COMPLETE]: protocol.feed(line)
        self.assertEqual(1, protocol.finish(0)["counts"]["failures"])
        self.assertEqual(0, protocol.finish(0)["counts"]["passed"])


class ActualPythonPipeObservationTests(unittest.TestCase):
    def test_real_console_return_code_and_finished_counts_survive_an_interrupted_pipe(self):
        protocol = a.NativeProtocol(); output = SimpleNamespace(buffer=io.BytesIO())
        lines = f.complete_lines()[:-2] + [f.frame("testStarted", name="interrupted")]
        code = "import sys\n" + "\n".join("print(" + repr(line) + ",flush=True)" for line in lines) + "\nsys.exit(149)\n"
        with tempfile.TemporaryDirectory() as directory, patch.object(a.lt, "ROOT", Path(directory)), \
                patch.object(a.sys, "stdout", output), patch.object(a.shutil, "disk_usage", return_value=SimpleNamespace(free=10 * 1024**3)):
            with self.assertRaises(ValueError): a.forward_application([sys.executable, "-u", "-c", code], protocol, 5)
        observation = protocol.transport_observation
        self.assertEqual(149, observation["console_process_exit"])
        self.assertFalse(observation["console_cleanup_requested"])
        self.assertEqual(1, protocol.partial()["counts"]["passed"])
        self.assertEqual("interrupted", protocol.partial()["unfinished_testcase"]["name"])
        self.assertEqual(("\n".join(lines) + "\n").encode(), output.buffer.getvalue())

    def test_owned_console_timeout_does_not_claim_forced_exit_was_native_application_exit(self):
        protocol = a.NativeProtocol(); output = SimpleNamespace(buffer=io.BytesIO())
        with tempfile.TemporaryDirectory() as directory, patch.object(a.lt, "ROOT", Path(directory)), \
                patch.object(a.sys, "stdout", output), patch.object(a.shutil, "disk_usage", return_value=SimpleNamespace(free=10 * 1024**3)):
            with self.assertRaises(TimeoutError):
                a.forward_application([sys.executable, "-u", "-c", "import time;time.sleep(60)"], protocol, 1)
        observation = protocol.transport_observation
        self.assertIsNone(observation["console_process_exit"])
        self.assertIsInstance(observation["console_process_exit_after_cleanup"], int)
        self.assertTrue(observation["console_cleanup_requested"])
        self.assertEqual(0, protocol.partial()["counts"]["executed"])


class ImageLifetimeSourceGuardTests(unittest.TestCase):
    def test_instrumentation_preserves_real_conversion_bytes_native_releases_and_twenty_gc_calls(self):
        root = Path(__file__).resolve().parents[2]
        source = (root / "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/UIImageConversionTest.kt").read_text()
        body = source.split("@Test fun " + METHOD + "() = runNativeUiTest {", 1)[1].split("private fun compareVectorWithCompose", 1)[0]
        for statement in ["val bridge = CountingBridge()", "bridge.assertBalanced()", "val expected = image.drawRgba()",
                          "repeat(20)", "GC.collect()", "assertEquals(257uL, CGImageGetWidth(other.CGImage))",
                          "assertContentEquals(expected, image.drawRgba())"]: self.assertIn(statement, body)
        self.assertEqual(1, body.count("GC.collect()"))
        for phase in ["retained-ready", "before-conversion", "before-gc", "after-gc", "before-verify", "verified"]:
            self.assertIn("NATIVECMPKIT_UIKIT_IMAGE_LIFETIME phase=" + phase, body)
        self.assertEqual(6, body.count("mainThread=${NSThread.isMainThread}"))
        self.assertLess(body.index("phase=before-gc"), body.index("GC.collect()"))
        self.assertLess(body.index("GC.collect()"), body.index("phase=after-gc"))
        self.assertLess(body.index("assertContentEquals(expected, image.drawRgba())"), body.index("phase=verified"))
        for bypass in ["Worker.", "Dispatchers.", "Thread.sleep", "usleep", "@Ignore", "return@"]: self.assertNotIn(bypass, body)


if __name__ == "__main__":
    unittest.main()
