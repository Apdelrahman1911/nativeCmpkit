"""Finite recovery/source guards; synthetic XML and plans never prove native behavior."""
from collections import Counter
from copy import deepcopy
import io
from pathlib import Path
import re
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

import library_tests as l
import workflow_matrix as w


class AndroidGeoPrerequisitesTests(unittest.TestCase):
    def plan(self):
        return l.plan(l.ROOT, "android-device", only_modules=("calf-geo",), focus=l.ANDROID_GEO_PREREQUISITES_FOCUS)

    def test_only_failed_default_provider_and_two_new_prerequisites_recover_without_two_accepted_replays(self):
        row, = w.matrix("android-geo-prerequisites")["include"]
        self.assertEqual(("android-device-api35", "calf-geo", l.ANDROID_GEO_PREREQUISITES_FOCUS),
                         (row["slot"], row["test-modules"], row["test-focus"]))
        plan = self.plan(); self.assertTrue(l.validate_test_focus(plan)); self.assertTrue(l.android_geo_probe_required(plan))
        cases = l.android_geo_provider_identities(l.ANDROID_GEO_PREREQUISITES_FOCUS)
        self.assertEqual(3, len(cases)); self.assertEqual(cases, plan["expected"][0]["required_testcases"])
        self.assertTrue(set(c["name"] for c in cases).isdisjoint(l.ANDROID_GEO_PROVIDER_METHODS[3:]))
        self.assertEqual(l.ANDROID_GEO_PREREQUISITES_ANNOTATION, plan["expected"][0]["test_filter"])
        command = l.gradle_command("android-device", plan, android_serial="emulator-5588")
        self.assertEqual(1, command.count("-Pandroid.testInstrumentationRunnerArguments.nativecmpkitOwnedGeoProbe=true"))
        owner = l.plan(l.ROOT, "android-device", only_modules=("calf-geo",), focus=l.ANDROID_GEO_OWNERSHIP_FOCUS)
        self.assertFalse(l.android_geo_probe_required(owner))
        self.assertEqual(11, len(w.matrix("all")["include"]))
        self.assertEqual(8, len(l.plan(l.ROOT, "android-device")["expected"]))

    def test_prerequisite_selection_uses_one_actual_runtime_annotation_without_ATE_csv_loss(self):
        plan = self.plan()
        command = l.gradle_command("android-device", plan, android_serial="emulator-5588")
        selectors = [a for a in command if a.startswith("-Pandroid.testInstrumentationRunnerArguments.") and
                     a.split("=", 1)[0].rsplit(".", 1)[-1] in {"class", "annotation", "notAnnotation"}]
        self.assertEqual(["-Pandroid.testInstrumentationRunnerArguments.annotation=" +
                          "com.mohamedrejeb.calf.geo.AndroidGeoPrerequisiteVerification"], selectors)
        self.assertTrue(all("," not in selector for selector in selectors), "ATE1.0.1 loses comma-containing selectors")
        source = (l.ROOT / l.ANDROID_GEO_PROVIDER_SOURCE).read_text()
        annotated = re.findall(r"@AndroidGeoPrerequisiteVerification\s+@Test fun ([A-Za-z0-9_]+)", source)
        self.assertEqual(list(l.ANDROID_GEO_PROVIDER_METHODS[:3]), annotated)
        self.assertIn("@Retention(AnnotationRetention.RUNTIME)", source)

    def test_both_real_clis_have_the_same_exact_finite_source_only_plan(self):
        import android_device_tests as device
        for module, args in [(l, ["library_tests.py", "plan", "--suite", "android-device", "--module", "calf-geo", "--focus", l.ANDROID_GEO_PREREQUISITES_FOCUS]),
                             (device, ["android_device_tests.py", "plan", "--api-level", "35", "--module", "calf-geo", "--focus", l.ANDROID_GEO_PREREQUISITES_FOCUS,
                                       "--output", "build/ci-verification/synthetic-geo"] )]:
            with patch("sys.argv", args), patch("sys.stdout", io.StringIO()): self.assertEqual(0, module.main())
        self.assertEqual(0, w.preflight_plans("android-geo-prerequisites")["slots"][0]["exit_code"])

    def test_missing_extra_skipped_failed_stale_or_no_task_marker_can_never_accept_recovery(self):
        plan = self.plan(); expected = plan["expected"][0]; identities = expected["required_testcases"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); report = root / expected["report_directory"] / "TEST-synthetic.xml"; report.parent.mkdir(parents=True)
            for cases in [identities, identities[:2], identities + identities[:1],
                          identities + [{"classname": "Foreign.Test", "name": "extra"}],
                          [identities[0] | {"outcome": "<failure/>"}, *identities[1:]],
                          [identities[0] | {"outcome": "<skipped/>"}, *identities[1:]]]:
                report.write_text("<testsuite>" + "".join('<testcase classname="' + c["classname"] + '" name="' + c["name"] + '">' + c.get("outcome", "") + '</testcase>' for c in cases) + "</testsuite>")
                now = time.time_ns(); actual = l.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000, Counter({expected["task"]: 1}))
                self.assertEqual(cases != identities, bool(actual["errors"]))
            self.assertTrue(l.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000, Counter())["errors"])
        invalid = deepcopy(plan); invalid["expected"][0]["test_filter"] = l.ANDROID_GEO_PROVIDER_CLASS
        with self.assertRaises(ValueError): l.validate_test_focus(invalid)

    def test_default_client_checks_actual_gms_and_location_settings_before_registration_without_enabling_them(self):
        source = (l.ROOT / "calf-geo/src/androidMain/kotlin/com/mohamedrejeb/calf/geo/AndroidLocationTrackingBackend.kt").read_text()
        for token in ["DefaultAndroidLocationClient(context)", "GoogleApiAvailabilityLight", "isGooglePlayServicesAvailable(this)",
                      "LocationManagerCompat.isLocationEnabled(manager)", "platformCode = status", "AndroidLocationPrerequisiteException",
                      "requestIssued = false", "delegate?.remove(callback) ?: Tasks.forResult<Void>(null)"]:
            self.assertIn(token, source)
        for token in ["requestPermissions(", "startResolutionForResult(", "setLocationEnabled("]: self.assertNotIn(token, source)

    def test_real_uid_revocation_foreground_native_transport_and_restoration_are_not_mocked_or_claimed_as_gps(self):
        source = (l.ROOT / l.ANDROID_GEO_PROVIDER_SOURCE).read_text()
        fixture = l.ROOT / "tests/consumer/android-geo-probe"
        service = (fixture / "src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/geoprobe/GeoProbeService.java").read_text()
        activity = (fixture / "src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/geoprobe/GeoProbeActivity.java").read_text()
        for token in ["revokeRuntimePermission(OwnedGeoProbe.PACKAGE", "probe.awaitDeath()", "probe.disconnect()", "probe.connect()",
                      "getString(\"generation\")", "Process.myPid()", "pm disable-user", "pm enable", "pm uninstall --user 0 com.google.android.gms",
                      "cmd package install-existing --user 0 com.google.android.gms", "gmsInstalled", "gmsSystem", "cmd location set-location-enabled false",
                      "cmd location set-location-enabled true", "SERVICE_DISABLED", "not GPS/fix accuracy"]: self.assertIn(token, source)
        for token in ["new LocationTracker()", "tracker.bind(activity.getLifecycle(), activity)", "current.startTrackingWithResult",
                      "ContextCompat.checkSelfPermission(this", "checkSignatures", "getPackagesForUid", "EmptyCoroutineContext.INSTANCE"]: self.assertIn(token, service)
        self.assertIn("super.onResume(); active = this", activity)
        self.assertNotIn("AndroidLocationClient", service); self.assertNotIn("LocationPermissionAccuracy.Approximate", service)
        manifest = (fixture / "src/main/AndroidManifest.xml").read_text()
        self.assertIn('android:protectionLevel="signature"', manifest); self.assertNotIn("ACCESS_BACKGROUND_LOCATION", manifest)
        build = (fixture / "build.gradle.kts").read_text()
        for token in ["maven-publish", "module.publication", "publishing {", "publishTo"]: self.assertNotIn(token, build)

    def test_two_accepted_injected_native_method_bodies_are_byte_identical_to_the_actual_failed_run(self):
        current = (l.ROOT / l.ANDROID_GEO_PROVIDER_SOURCE).read_text()
        historical = subprocess.check_output(["git", "show", "c446bad36492aec4308c63e0d6c5513b5c18af39:" + l.ANDROID_GEO_PROVIDER_SOURCE], cwd=l.ROOT, text=True)
        for method in l.ANDROID_GEO_PROVIDER_METHODS[3:]:
            pattern = r"    @Test fun " + method + r"\(\) \{[\s\S]*?(?=\n    (?:@Test|private fun))"
            self.assertEqual(re.search(pattern, historical).group(), re.search(pattern, current).group())


if __name__ == "__main__": unittest.main()
