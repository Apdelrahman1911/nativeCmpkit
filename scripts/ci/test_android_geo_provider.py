"""Finite Android geo permission/provider guards; synthetic, not OS/GMS passes."""
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

FOCUS = "geo-android-provider-contracts"
PROFILE = "android-geo-provider"
CLASS = "com.mohamedrejeb.calf.geo.AndroidLocationProviderTest"
SOURCE = "calf-geo/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/geo/AndroidLocationProviderTest.kt"
METHODS = (
    "nativeForegroundDeniedCoarseAndFinePermissionsUseRealGmsRegistration",
    "nativeRevocationKillsOnlyOwnedProbeAndRestartReportsDenied",
    "nativeMissingDisabledPlayServicesAndLocationSettingsBlockStartAndRecover",
    "nativeProviderTaskErrorsRemovalRetryAndRecoveryAreObservable",
    "nativeBackgroundCancellationAndQueuedOldCallbacksCannotOwnANewStart",
)


class AndroidGeoProviderTests(unittest.TestCase):
    def plan(self):
        return lt.plan(lt.ROOT, "android-device", only_modules=("calf-geo",), focus=FOCUS)

    def collect(self, cases=None, marker=1, stale=False):
        plan = self.plan()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / plan["expected"][0]["report_directory"] / "TEST-synthetic.xml"
            path.parent.mkdir(parents=True)
            cases = [{"classname": CLASS, "name": m} for m in METHODS] if cases is None else cases
            path.write_text("<testsuite>" + "".join(
                '<testcase classname="' + c["classname"] + '" name="' + c["name"] + '">' +
                c.get("outcome", "") + "</testcase>" for c in cases) + "</testsuite>")
            now = time.time_ns()
            if stale:
                import os
                os.utime(path, ns=(now - 20_000_000_000, now - 20_000_000_000))
            return lt.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                      Counter({plan["expected"][0]["task"]: marker}))

    def test_full_five_case_profile_keeps_its_inventory_without_owner_gc_or_host_cases(self):
        row, = wm.matrix(PROFILE)["include"]
        self.assertEqual(("android-device-api35", "android-device", "calf-geo", FOCUS),
                         (row["slot"], row["suite"], row["test-modules"], row["test-focus"]))
        plan = self.plan()
        self.assertTrue(lt.validate_test_focus(plan))
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(CLASS, plan["expected"][0]["test_filter"])
        self.assertEqual([{"classname": CLASS, "name": m} for m in METHODS],
                         plan["expected"][0]["required_testcases"])

    def test_both_actual_clis_and_workflow_preflight_agree(self):
        import android_device_tests as device
        for module, args in ((lt, ["library_tests.py", "plan", "--suite", "android-device", "--module", "calf-geo", "--focus", FOCUS]),
                             (device, ["android_device_tests.py", "plan", "--api-level", "35", "--module", "calf-geo", "--focus", FOCUS,
                                       "--output", "build/ci-verification/provider-synthetic-plan"])):
            with patch("sys.argv", args), patch("sys.stdout", io.StringIO()):
                self.assertEqual(0, module.main())
        self.assertEqual(0, wm.preflight_plans(PROFILE)["slots"][0]["exit_code"])

    def test_foreign_suite_module_filters_and_broad_success_are_rejected(self):
        for suite, modules in (("desktop", ("calf-geo",)), ("android-host", ("calf-geo",)), ("ios", ("calf-geo",)),
                               ("android-device", None), ("android-device", ("calf-io",)),
                               ("android-device", ("calf-geo", "calf-io"))):
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

    def test_no_missing_extra_failed_skipped_stale_or_unexecuted_xml_acceptance(self):
        identities = [{"classname": CLASS, "name": m} for m in METHODS]
        self.assertEqual([], self.collect()["errors"])
        for cases in ([], identities[:2], identities + identities[:1],
                      identities + [{"classname": "Foreign.Test", "name": "extra"}],
                      [identities[0] | {"outcome": "<failure/>"}, *identities[1:]],
                      [identities[0] | {"outcome": "<skipped/>"}, *identities[1:]]):
            self.assertTrue(self.collect(cases)["errors"])
        self.assertTrue(self.collect(stale=True)["errors"])
        for marker in (0, 2):
            self.assertTrue(self.collect(marker=marker)["errors"])

    def test_native_permissions_and_live_transport_are_not_replaced_by_mock_success(self):
        source = (lt.ROOT / SOURCE).read_text()
        for token in ("UiAutomation", "grantRuntimePermission", "revokeRuntimePermission", "ACCESS_COARSE_LOCATION", "ACCESS_FINE_LOCATION",
                      "PackageManager.PERMISSION_DENIED", "context.packageManager.checkPermission", "OwnedGeoProbe",
                      "probe.foreground()", "probe.request(\"bind\")", "GoogleApiAvailabilityLight",
                      "Approximate", "Precise", "PermissionDenied", "NotBound", "withTimeout", "AlreadyStarted", "awaitStopped",
                      "real default provider", "not GPS/fix"):
            self.assertIn(token, source)
        self.assertEqual(5, source.count("@Test fun "))
        for token in ("@Ignore", "@Disabled", "assumeTrue(", "Robolectric", "Dispatchers.setMain", "sample."):
            self.assertNotIn(token, source)
        manifest = (lt.ROOT / "calf-geo/src/androidDeviceTest/AndroidManifest.xml").read_text()
        self.assertIn("GeoTrackingVerificationActivity", manifest)
        self.assertIn('android:exported="false"', manifest)
        self.assertNotIn("ACCESS_BACKGROUND_LOCATION", manifest)

    def test_native_tasks_threads_queue_and_cleanup_keep_injected_boundary_explicit(self):
        source = (lt.ROOT / SOURCE).read_text()
        for token in ("TaskCompletionSource<Void>", "ApiException(Status(17))", "SecurityException",
                      "Dispatchers.Default", "Handler(Looper.getMainLooper()).post", "cancelAndJoin",
                      "setException", "RemovalFailed", "ProviderUnavailable", "InProgress",
                      "assertSame", "assertEquals(Looper.getMainLooper()", "tracker.close()",
                      "injected transport", "not GPS/fix accuracy"):
            self.assertIn(token, source)

    def test_filter_readonly_workflow_and_full_inventory_are_preserved(self):
        command = lt.gradle_command("android-device", self.plan(), android_serial="emulator-5588")
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.class=" + CLASS, command)
        self.assertEqual(":calf-geo:connectedAndroidDeviceTest", command[-1])
        self.assertEqual(11, len(wm.matrix("all")["include"]))
        self.assertEqual(["calf-io", "calf-file-picker", "calf-geo", "calf-webview", "calf-ui", "calf-navigation"],
                         [m["module"] for m in lt.plan(lt.ROOT, "android-device")["expected"]])
        workflow = (lt.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn(PROFILE, workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)


if __name__ == "__main__":
    unittest.main()
