"""Finite GC/ownership selection guards; synthetic checks, never ART/native passes."""
from collections import Counter
from copy import deepcopy
import io
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import library_tests as lt
import workflow_matrix as wm


FOCUS = "geo-android-owner-lifetime"
PROFILE = "android-geo-ownership"
CLASS = "com.mohamedrejeb.calf.geo.AndroidLocationOwnershipTest"
METHOD = "nativeRebindingRestartAndTerminalCleanupReleaseOwnersDespiteRetainedCallbacks"
SOURCE = "calf-geo/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/geo/AndroidLocationOwnershipTest.kt"


class AndroidGeoOwnershipTests(unittest.TestCase):
    def plan(self):
        return lt.plan(lt.ROOT, "android-device", only_modules=("calf-geo",), focus=FOCUS)

    def collect(self, cases=None, marker=1, stale=False):
        plan = self.plan()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / plan["expected"][0]["report_directory"] / "TEST-explicitly-synthetic.xml"
            report.parent.mkdir(parents=True)
            cases = [{"classname": CLASS, "name": METHOD}] if cases is None else cases
            report.write_text("<testsuite>" + "".join(
                '<testcase classname="' + c["classname"] + '" name="' + c["name"] + '">' +
                c.get("outcome", "") + "</testcase>" for c in cases) + "</testsuite>")
            now = time.time_ns()
            if stale:
                import os
                os.utime(report, ns=(now - 20_000_000_000, now - 20_000_000_000))
            return lt.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                      Counter({plan["expected"][0]["task"]: marker}))

    def test_exact_one_new_native_method_not_replay_of_accepted_geo_or_navigation(self):
        row, = wm.matrix(PROFILE)["include"]
        self.assertEqual(("android-device-api35", "android-device", "calf-geo", FOCUS),
                         (row["slot"], row["suite"], row["test-modules"], row["test-focus"]))
        plan = self.plan()
        self.assertTrue(lt.validate_test_focus(plan))
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(CLASS, plan["expected"][0]["test_filter"])
        self.assertEqual([{"classname": CLASS, "name": METHOD}], plan["expected"][0]["required_testcases"])
        self.assertIn(SOURCE, plan["expected"][0]["test_source_files"])

    def test_both_real_source_clis_and_host_preflight_accept_the_same_finite_selection(self):
        import android_device_tests as device
        for module, args in ((lt, ["library_tests.py", "plan", "--suite", "android-device", "--module", "calf-geo", "--focus", FOCUS]),
                             (device, ["android_device_tests.py", "plan", "--api-level", "35", "--module", "calf-geo", "--focus", FOCUS,
                                       "--output", "build/ci-verification/geo-synthetic-plan"])):
            with patch("sys.argv", args), patch("sys.stdout", io.StringIO()):
                self.assertEqual(0, module.main())
        preflight = wm.preflight_plans(PROFILE)
        self.assertEqual(1, len(preflight["slots"]))
        self.assertEqual(0, preflight["slots"][0]["exit_code"])

    def test_foreign_targets_modules_arbitrary_filters_and_full_success_claim_are_rejected(self):
        for suite, modules in (("desktop", ("calf-geo",)), ("android-host", ("calf-geo",)), ("ios", ("calf-geo",)),
                               ("js", ("calf-geo",)), ("wasm", ("calf-geo",)), ("android-device", None),
                               ("android-device", ("calf-navigation",)), ("android-device", ("calf-geo", "calf-io"))):
            with self.assertRaises(ValueError):
                lt.plan(lt.ROOT, suite, only_modules=modules, focus=FOCUS)
        for key, value in (("test_filter", "*"), ("required_testcases", []), ("test_source_files", []), ("task", ":calf-geo:publish")):
            plan = deepcopy(self.plan())
            plan["expected"][0][key] = value
            with self.assertRaises(ValueError):
                lt.validate_test_focus(plan)
        plan = self.plan()
        plan["complete_suite_requested"] = True
        with self.assertRaises(ValueError):
            lt.validate_test_focus(plan)

    def test_only_exact_fresh_passed_xml_with_one_task_marker_can_be_accepted(self):
        identity = {"classname": CLASS, "name": METHOD}
        self.assertEqual([], self.collect()["errors"])
        for cases in ([], [identity, identity], [identity | {"classname": "Foreign.Test"}],
                      [identity | {"outcome": "<failure/>"}], [identity | {"outcome": "<skipped/>"}]):
            self.assertTrue(self.collect(cases)["errors"])
        self.assertTrue(self.collect(stale=True)["errors"])
        for marker in (0, 2):
            self.assertTrue(self.collect(marker=marker)["errors"])

    def test_art_ownership_fixture_keeps_real_lifecycle_tasks_gc_and_explicit_injection_boundary(self):
        source = (lt.ROOT / SOURCE).read_text()
        for token in ("InstrumentationRegistry.getInstrumentation()", "runOnMainSync", "waitForIdleSync()",
                      "LifecycleRegistry(this)", "AndroidLocationTrackingBackend(", "Task<Void>", "Tasks.forResult<Void>(null)",
                      "WeakReference", "System.gc()", "repeat(32)", "ownerA.destroy()", "ownerB.destroy()",
                      "tracker.close()", "retainedCallbacks", "observerCount", "startTrackingWithResult()",
                      "oldCallback.onLocationResult", "assertSame(Looper.getMainLooper(), looper)",
                      "injected transport", "not a live GMS"):
            self.assertIn(token, source)
        for forbidden in ("@Ignore", "@Disabled", "assumeTrue(", "Robolectric", "Dispatchers.setMain", "sample.", "Thread.sleep(60_000"):
            self.assertNotIn(forbidden, source)
        self.assertEqual(1, source.count("@Test fun "))

    def test_full_native_plan_retains_all_existing_modules_and_all_eleven_host_slots(self):
        plan = lt.plan(lt.ROOT, "android-device")
        self.assertTrue(plan["complete_suite_requested"])
        self.assertEqual(["calf-io", "calf-file-picker", "calf-geo", "calf-webview", "calf-ui", "calf-navigation", "calf-share"],
                         [item["module"] for item in plan["expected"]])
        self.assertEqual(11, len(wm.matrix("all")["include"]))

    def test_exact_instrumentation_filter_minimum_permissions_and_no_publication(self):
        command = lt.gradle_command("android-device", self.plan(), android_serial="emulator-5588")
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.class=" + CLASS, command)
        self.assertNotIn("--tests", command)
        self.assertEqual(":calf-geo:connectedAndroidDeviceTest", command[-1])
        workflow = (lt.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn(PROFILE, workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)


if __name__ == "__main__":
    unittest.main()
