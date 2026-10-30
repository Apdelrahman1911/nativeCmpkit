"""Finite native sharing plan/collector guards; synthetic XML is not recipient evidence."""
from collections import Counter
from copy import deepcopy
import io
from pathlib import Path
import re
import tempfile
import time
import unittest
from unittest.mock import patch

import library_tests as l
import workflow_matrix as w


class AndroidShareGrantPlanTests(unittest.TestCase):
    def plan(self):
        return l.plan(l.ROOT, "android-device", only_modules=("calf-share",), focus="android-share-uri-grants")

    def test_one_exact_three_method_native_job_preserves_all_prior_device_modules_and_full_slots(self):
        row, = w.matrix("android-share-grants")["include"]
        self.assertEqual(("android-device-api35", "android-device", "calf-share", "android-share-uri-grants"),
                         (row["slot"], row["suite"], row["test-modules"], row["test-focus"]))
        plan = self.plan(); self.assertTrue(l.validate_test_focus(plan))
        self.assertTrue(l.android_share_recipient_required(plan)); self.assertFalse(l.android_geo_probe_required(plan))
        self.assertFalse(plan["complete_suite_requested"]); self.assertEqual(["calf-share"], plan["explicit_module_subset"])
        self.assertEqual(3, len(plan["expected"][0]["required_testcases"]))
        self.assertEqual({"calf-io", "calf-file-picker", "calf-geo", "calf-webview", "calf-ui", "calf-navigation", "calf-share"},
                         set(l.MINIMUM_MODULES["android-device"]))
        self.assertEqual(7, len(l.plan(l.ROOT, "android-device")["expected"]))
        self.assertEqual(11, len(w.matrix("all")["include"]))

    def test_single_class_selector_carries_no_ate_comma_and_only_the_owned_recipient_marker(self):
        plan = self.plan(); command = l.gradle_command("android-device", plan, android_serial="emulator-5588")
        self.assertEqual(1, command.count("-Pandroid.testInstrumentationRunnerArguments.nativecmpkitOwnedShareRecipient=true"))
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.class=com.mohamedrejeb.calf.share.AndroidShareGrantTest", command)
        self.assertFalse(any("," in arg for arg in command if arg.startswith("-Pandroid.testInstrumentationRunnerArguments.")))
        self.assertNotIn("-Pandroid.testInstrumentationRunnerArguments.nativecmpkitOwnedGeoProbe=true", command)
        self.assertEqual(":calf-share:connectedAndroidDeviceTest", command[-1])

    def test_actual_controller_and_library_clis_agree_on_source_plan_not_native_success(self):
        import android_device_tests as device
        for module, args in [(l, ["library_tests.py", "plan", "--suite", "android-device", "--module", "calf-share", "--focus", "android-share-uri-grants"]),
                             (device, ["android_device_tests.py", "plan", "--api-level", "35", "--module", "calf-share", "--focus", "android-share-uri-grants",
                                       "--output", "build/ci-verification/synthetic-share-grants"])]:
            output = io.StringIO()
            with patch("sys.argv", args), patch("sys.stdout", output): self.assertEqual(0, module.main())
            import json
            self.assertEqual(self.plan(), json.loads(output.getvalue()))
        self.assertEqual(0, w.preflight_plans("android-share-grants")["slots"][0]["exit_code"])

    def test_exact_fresh_three_cases_require_task_marker_and_reject_missing_duplicate_extra_skip_and_failure(self):
        plan = self.plan(); expected = plan["expected"][0]; identities = expected["required_testcases"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); report = root / expected["report_directory"] / "TEST-synthetic.xml"; report.parent.mkdir(parents=True)
            variants = [identities, identities[:2], identities + identities[:1],
                        identities + [{"classname": "Foreign.Test", "name": "extra"}],
                        [identities[0] | {"outcome": "<failure/>"}, *identities[1:]],
                        [identities[0] | {"outcome": "<skipped/>"}, *identities[1:]]]
            for cases in variants:
                report.write_text("<testsuite>" + "".join('<testcase classname="' + c["classname"] + '" name="' + c["name"] + '">' + c.get("outcome", "") + '</testcase>' for c in cases) + "</testsuite>")
                now = time.time_ns()
                actual = l.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000, Counter({expected["task"]: 1}))
                self.assertEqual(cases != identities, bool(actual["errors"]))
            self.assertTrue(l.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000, Counter())["errors"])
            self.assertTrue(l.collect_reports(root, plan, now + 10_000_000_000, now + 11_000_000_000, Counter({expected["task"]: 1}))["errors"])
        invalid = deepcopy(plan); invalid["expected"][0]["test_filter"] = "Foreign.Test"
        with self.assertRaises(ValueError): l.validate_test_focus(invalid)

    def test_native_fixture_preserves_os_grants_distinct_uid_bounded_reads_owned_streams_and_no_manual_grant(self):
        native = (l.ROOT / "calf-share/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/share/AndroidShareGrantTest.kt").read_text()
        recipient = l.ROOT / "tests/consumer/android-share-recipient"
        service = (recipient / "src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/sharerecipient/ShareRecipientService.java").read_text()
        helper = (l.ROOT / "calf-share/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/share/OwnedShareRecipient.kt").read_text()
        self.assertEqual(3, len(re.findall(r"@Test fun [A-Za-z0-9_]+", native)))
        for token in ["file.toKmpFile()", "ShareOutcome.Presented", "DocumentsContract.isDocumentUri", "FLAG_GRANT_WRITE_URI_PERMISSION",
                      "context.revokeUriPermission", "startActivityForResult", "ShareFailureReason.Permission", "closeErrors", "No manual grant"]:
            self.assertIn(token, native)
        self.assertNotIn("grantUriPermission(", native); self.assertNotIn("grantUriPermission(", helper)
        documents = l.ROOT / "tests/consumer/android-share-documents"
        grant = (documents / "src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/sharedocuments/ShareDocumentGrantActivity.java").read_text()
        provider = (documents / "src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/sharedocuments/OwnedShareDocumentsProvider.java").read_text()
        self.assertIn("setResult(RESULT_OK, result)", grant); self.assertNotIn("grantUriPermission(", grant)
        self.assertIn("three distinct native UIDs", native)
        for token in ["openDocument(", "MODE_READ_ONLY", "record.closes.incrementAndGet()", "Binder.getCallingUid()", "checkSignatures"]:
            self.assertIn(token, provider)
        for token in ["openFileDescriptor(uri, \"r\")", "AutoCloseInputStream", "getPackagesForUid", "checkSignatures", "total > 8192", "checkUriPermission"]:
            self.assertIn(token, service)
        self.assertIn("assertNotEquals(Process.myUid(), it.uid)", helper)
        manifest = (recipient / "src/main/AndroidManifest.xml").read_text()
        self.assertIn('android:protectionLevel="signature"', manifest); self.assertNotIn("<uses-permission", manifest)
        for token in ["maven-publish", "module.publication", "publishTo"]: self.assertNotIn(token, (recipient / "build.gradle.kts").read_text())

    def test_separate_recipient_sources_but_not_its_binary_or_private_signing_inputs_are_frozen(self):
        inputs = l.snapshot_inputs(l.ROOT)
        self.assertIn("tests/consumer/android-share-recipient/build.gradle.kts", inputs,
                      "The owning recipient build must be input-bound, not a private or cached APK")
        self.assertIn("tests/consumer/android-share-recipient/src/main/AndroidManifest.xml", inputs,
                      "The actual recipient manifest must be frozen")
        self.assertIn("tests/consumer/android-share-documents/src/main/AndroidManifest.xml", inputs,
                      "The third-UID grant source manifest must be frozen")
        self.assertFalse(any("/android-user/" in name or name.endswith((".apk", ".jks", ".keystore")) for name in inputs))


if __name__ == "__main__": unittest.main()
