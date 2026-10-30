"""Synthetic exact-plan/engine/archive guards only. No Android/native or release outcomes."""
from collections import Counter
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch, Mock

import library_tests as l
import android_device_tests as device
import android_camera_receiver as receiver
import android_geo_probe as geo
import workflow_matrix as w


class CameraProviderPlanTests(unittest.TestCase):
    def plan(self): return l.plan(l.ROOT, "android-device", only_modules=("calf-camera-picker",), focus=l.ANDROID_CAMERA_PROVIDER_FOCUS)

    def test_exact_four_methods_and_two_serial_real_api_plans_preserve_all_prior_slots(self):
        row, = w.matrix("android-camera-provider")["include"]
        self.assertEqual(("android-device-api35", "android-device", "calf-camera-picker", "35", "23", l.ANDROID_CAMERA_PROVIDER_FOCUS),
                         tuple(row[k] for k in ("slot", "suite", "test-modules", "emulator-api", "serial-emulator-api", "test-focus")))
        p = self.plan(); self.assertTrue(l.validate_test_focus(p)); self.assertTrue(l.android_camera_receiver_required(p))
        self.assertFalse(p["complete_suite_requested"]); self.assertEqual(4, len(p["expected"][0]["required_testcases"]))
        self.assertEqual(11, len(w.matrix("all")["include"])); self.assertEqual(8, len(l.plan(l.ROOT, "android-device")["expected"]))
        actual = w.preflight_plans("android-camera-provider")
        self.assertEqual(2, len(actual["slots"]))
        for api, selection in zip(("35", "23"), actual["slots"]):
            self.assertEqual(api, selection["command"][selection["command"].index("--api-level") + 1])
            self.assertEqual(0, selection["exit_code"])

    def test_one_class_no_ate_comma_or_foreign_marker_requires_only_owned_camera_receiver(self):
        c = l.gradle_command("android-device", self.plan(), android_serial="emulator-5588")
        self.assertEqual(1, c.count("-Pandroid.testInstrumentationRunnerArguments.nativecmpkitOwnedCameraReceiver=true"))
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.class=" + l.ANDROID_CAMERA_PROVIDER_CLASS, c)
        self.assertFalse(any("," in x for x in c if x.startswith("-Pandroid.testInstrumentationRunnerArguments.")))
        self.assertFalse(any("OwnedShare" in x or "OwnedGeo" in x for x in c))
        self.assertEqual(":calf-camera-picker:connectedAndroidDeviceTest", c[-1])

    def test_api23_never_escapes_exact_camera_focus_and_default_api35_stays_available(self):
        device.validate_api_selection(35, None, None)
        device.validate_api_selection(23, ("calf-camera-picker",), l.ANDROID_CAMERA_PROVIDER_FOCUS)
        for api, modules, focus in [(23, None, None), (23, ("calf-io",), l.ANDROID_CAMERA_PROVIDER_FOCUS),
                                    (23, ("calf-camera-picker",), None), (24, ("calf-camera-picker",), l.ANDROID_CAMERA_PROVIDER_FOCUS),
                                    (23, ("calf-camera-picker", "calf-io"), l.ANDROID_CAMERA_PROVIDER_FOCUS)]:
            with self.assertRaises(ValueError): device.validate_api_selection(api, modules, focus)
        for api in (23, 35):
            args = ["android_device_tests.py", "plan", "--api-level", str(api), "--module", "calf-camera-picker", "--focus", l.ANDROID_CAMERA_PROVIDER_FOCUS, "--output", "build/ci-plan"]
            output = io.StringIO()
            with patch("sys.argv", args), patch("sys.stdout", output): self.assertEqual(0, device.main())
            self.assertEqual(self.plan(), json.loads(output.getvalue()))

    def test_api23_boot_requires_actual_enforcing_23_not_selected_label_or_35_fallback(self):
        process = Mock(); process.poll.return_value = None
        for api, security in (("23", "Enforcing"), ("35", "Enforcing"), ("23", "Permissive")):
            props = {"sys.boot_completed": "1", "ro.build.version.sdk": api, "ro.build.version.release": "6.0", "ro.product.cpu.abi": "x86_64"}
            with patch.object(device.shutil, "disk_usage", return_value=Mock(free=20 * 1024**3)), \
                 patch.object(device, "avd_name", return_value="owned"), \
                 patch.object(device, "adb", side_effect=lambda home, *args: security if args[-1] == "getenforce" else props[args[-1]]):
                if api == "23" and security == "Enforcing":
                    self.assertEqual("23", device.wait_for_owned_boot(Path("/synthetic/sdk"), process, "owned", Path("/synthetic"), api_level=23)["api_level"])
                else:
                    with self.assertRaises(ValueError): device.wait_for_owned_boot(Path("/synthetic/sdk"), process, "owned", Path("/synthetic"), api_level=23)

    def test_exact_four_fresh_cases_reject_missing_duplicate_extra_fail_skip_and_stale_task(self):
        plan = self.plan(); expected = plan["expected"][0]; cases = expected["required_testcases"]
        variants = [cases, cases[:2], cases + cases[:1], cases + [{"classname": "Foreign", "name": "extra"}],
                    [cases[0] | {"outcome": "<failure/>"}, *cases[1:]], [cases[0] | {"outcome": "<skipped/>"}, *cases[1:]]]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); report = root / expected["report_directory"] / "TEST-synthetic.xml"; report.parent.mkdir(parents=True)
            for variant in variants:
                report.write_text("<testsuite>" + "".join('<testcase classname="' + c["classname"] + '" name="' + c["name"] + '">' + c.get("outcome", "") + '</testcase>' for c in variant) + "</testsuite>")
                now = time.time_ns()
                result = l.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000, Counter({expected["task"]: 1}))
                self.assertEqual(variant != cases, bool(result["errors"]))
            self.assertTrue(l.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000, Counter())["errors"])
            self.assertTrue(l.collect_reports(root, plan, now + 10_000_000_000, now + 11_000_000_000, Counter({expected["task"]: 1}))["errors"])
        altered = deepcopy(plan); altered["expected"][0]["test_filter"] = "Foreign"
        with self.assertRaises(ValueError): l.validate_test_focus(altered)

    def test_native_sources_are_frozen_and_real_grants_not_manual_or_synthetic_camera_claims(self):
        inputs = l.snapshot_inputs(l.ROOT)
        base = "tests/consumer/android-camera-receiver"
        self.assertIn(base + "/build.gradle.kts", inputs); self.assertIn(base + "/src/main/AndroidManifest.xml", inputs)
        self.assertFalse(any(name.endswith((".apk", ".jks", ".keystore")) for name in inputs))
        native = (l.ROOT / l.ANDROID_CAMERA_PROVIDER_SOURCE).read_text()
        activity = (l.ROOT / base / "src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraReceiverActivity.java").read_text()
        service = (l.ROOT / base / "src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraReceiverService.java").read_text()
        for value in ("rememberCameraPickerResultLauncher", "startActivityForResult", "NonexistentCameraActivity", "FileProvider.getUriForFile", "CameraFailureReason.Configuration", "CameraFailureReason.Launch", "contentResolver.openInputStream"):
            self.assertIn(value, native)
        self.assertNotIn("grantUriPermission(", native + activity + service)
        self.assertNotIn("putExtra(Intent.EXTRA_STREAM", native)
        for value in ("checkUriPermission", 'openFileDescriptor(uri, "w")', "AutoCloseOutputStream", "getCallingPackage", "checkSignatures"):
            self.assertIn(value, activity)
        for value in ("getPackagesForUid", "request.sendingUid", "checkSignatures", '"Unknown operation"'):
            self.assertIn(value, service)
        self.assertIn('android:protectionLevel="signature"', (l.ROOT / base / "src/main/AndroidManifest.xml").read_text())
        for value in ("maven-publish", "module.publication", "publishTo"):
            self.assertNotIn(value, (l.ROOT / base / "build.gradle.kts").read_text())

    def test_workflow_serial_minimum_job_has_distinct_outputs_and_receipts_only(self):
        source = (l.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn("system-images;android-23;google_apis;x86_64", source)
        self.assertIn('matrix.serial-emulator-api == \'23\'', source)
        self.assertIn('--output "build/ci-verification/$SLOT-minimum-api23"', source)
        self.assertIn('matrix.slot }}-minimum-api23/fresh-reports/*.xml', source)
        self.assertIn('matrix.slot }}/camera-receiver/receipt.json', source)
        self.assertNotIn('matrix.slot }}/camera-receiver/*.apk', source)


class CameraArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); self.root = Path(self.temp.name)
        self.plan = l.plan(l.ROOT, "android-device", only_modules=("calf-camera-picker",), focus=l.ANDROID_CAMERA_PROVIDER_FOCUS)
        expected = self.plan["expected"][0]
        self.path = self.root / expected["report_directory"] / "TEST-synthetic.xml"; self.path.parent.mkdir(parents=True)
        self.path.write_text('<testsuite><properties><property name="private" value="not-for-archive"/></properties>' +
            ''.join('<testcase classname="' + c['classname'] + '" name="' + c['name'] + '"/>' for c in expected['required_testcases']) +
            '<system-out>private-console-not-for-archive</system-out></testsuite>')
        cases = l.junit_cases(self.path.read_bytes())
        self.receipt = {"suite": "android-device", "explicit_test_focus": l.ANDROID_CAMERA_PROVIDER_FOCUS,
            "source_tree_dirty": False, "source_revision": "a"*40, "source_revision_after": "a"*40, "changed_inputs": [], "passed": True,
            "task_execution_markers": {expected["task"]: 1}, "totals": l.case_counts(cases),
            "modules": [{"module": "calf-camera-picker", "testcases": cases, "reports": [{"path": self.path.relative_to(self.root).as_posix(), "sha256": l.sha256(self.path)}]}]}
        self.output = self.root / "build/ci-verification/synthetic-camera"; self.output.mkdir(parents=True)

    def test_archive_preserves_actual_outcomes_and_original_hash_while_removing_only_console_properties(self):
        original = self.path.read_bytes()
        result = receiver.archive_focused_reports(self.root, self.output, self.receipt, self.plan)
        archived = (self.root / result["archived_path"]).read_bytes()
        self.assertNotIn(b"not-for-archive", archived)
        self.assertEqual(hashlib.sha256(original).hexdigest(), result["original_sha256"])
        self.assertEqual(l.junit_cases(original), l.junit_cases(archived))
        self.assertFalse(result["native_success_inferred_from_archival"])
        with self.assertRaises(ValueError): receiver.archive_focused_reports(self.root, self.output, self.receipt, self.plan)

    def test_actual_gradle_avd_filename_is_archived_without_changing_test_or_source_guards(self):
        renamed = self.path.with_name('TEST-nativecmpkit-api35-58bff09dc20d(AVD) - 15.xml')
        self.path.rename(renamed); self.path = renamed
        self.receipt['modules'][0]['reports'][0]['path'] = renamed.relative_to(self.root).as_posix()
        archived = receiver.archive_focused_reports(self.root, self.output, self.receipt, self.plan)
        self.assertEqual(renamed.name, Path(archived['archived_path']).name)
        self.assertEqual(self.receipt['modules'][0]['testcases'], archived['actual_testcases'])

    def test_each_native_provider_authority_has_a_distinct_android_component_identity(self):
        manifest = ET.fromstring((l.ROOT / 'calf-camera-picker/src/androidDeviceTest/AndroidManifest.xml').read_bytes())
        providers = manifest.findall('application/provider')
        names = [p.attrib['{http://schemas.android.com/apk/res/android}name'] for p in providers]
        self.assertEqual(3, len(names)); self.assertEqual(3, len(set(names)))

    def test_owned_adb_shutdown_transition_is_observed_without_device_mutation_or_foreign_fallback(self):
        with patch.object(device, 'adb', side_effect=['List of devices attached\nemulator-5588\toffline', 'List of devices attached']) as adb, \
             patch.object(device.time, 'sleep'):
            self.assertTrue(device.wait_for_owned_transport_removal(Path('/synthetic/sdk'), timeout=1))
        self.assertEqual([(('devices',), {})] * 2, [(call.args[1:], call.kwargs) for call in adb.call_args_list])
        with patch.object(device, 'adb', return_value='List of devices attached\nprivate-foreign-device\tdevice'), \
             patch.object(device.time, 'sleep') as sleep, self.assertRaises(ValueError):
            device.wait_for_owned_transport_removal(Path('/synthetic/sdk'), timeout=1)
        sleep.assert_not_called()

    def test_wrong_hash_changed_source_or_task_and_foreign_selection_fail_before_archival(self):
        for bad in (self.receipt | {"source_tree_dirty": True}, self.receipt | {"changed_inputs": ["source"]},
                    self.receipt | {"source_revision_after": "b"*40}, self.receipt | {"task_execution_markers": {}},
                    self.receipt | {"explicit_test_focus": l.ANDROID_SHARE_GRANT_FOCUS}):
            with self.assertRaises(ValueError): receiver.archive_focused_reports(self.root, self.output, bad, self.plan)
            self.assertFalse((self.output / "fresh-reports").exists())
        self.path.write_text(self.path.read_text().replace('private-console', 'changed-console'))
        with self.assertRaises(ValueError): receiver.archive_focused_reports(self.root, self.output, self.receipt, self.plan)

    def test_failed_actual_xml_remains_failed_and_cannot_become_a_passing_archive_receipt(self):
        self.path.write_text(self.path.read_text().replace('/><testcase', '><failure message="synthetic failure"/></testcase><testcase', 1))
        cases = l.junit_cases(self.path.read_bytes())
        self.receipt["modules"][0]["testcases"] = cases; self.receipt["modules"][0]["reports"][0]["sha256"] = l.sha256(self.path)
        self.receipt.update(totals=l.case_counts(cases), passed=False)
        result = receiver.archive_focused_reports(self.root, self.output, self.receipt, self.plan)
        self.assertFalse(result["original_passed"]); self.assertEqual(1, l.case_counts(result["actual_testcases"])["failures"])

    def test_symlink_or_entity_xml_is_not_archived(self):
        original = self.path.read_bytes(); self.path.unlink(); other = self.root / "outside.xml"; other.write_bytes(original); self.path.symlink_to(other)
        with self.assertRaises(ValueError): receiver.archive_focused_reports(self.root, self.output, self.receipt, self.plan)
        self.path.unlink(); self.path.write_text('<!DOCTYPE testsuite [<!ENTITY x "private">]><testsuite/>')
        with self.assertRaises(ValueError): receiver.archive_focused_reports(self.root, self.output, self.receipt, self.plan)

    def test_exact_owned_camera_fixture_metadata_and_private_signing_context_reuse_installer_contract(self):
        env = {"ANDROID_SERIAL": "emulator-5588", "ANDROID_USER_HOME": str(self.output / "android-user"), "PRIVATE_SYNTHETIC": "not-for-receipt"}
        owner = receiver.OwnedCameraReceiver(self.root, self.output, Path("/synthetic/sdk"), "emulator-5588", lambda: True, environment=env)
        self.assertEqual(self.output / "camera-receiver", owner.output)
        self.assertNotIn("PRIVATE_SYNTHETIC", json.dumps(owner.receipt))
        base = self.root / owner.FIXTURE / "build/outputs/apk/debug"; base.mkdir(parents=True)
        apk = base / "camera-debug.apk"; apk.write_bytes(b"synthetic-not-native")
        (base / "output-metadata.json").write_text(json.dumps({"applicationId": owner.PACKAGE, "variantName": "debug", "artifactType": {"type": "APK"},
            "elements": [{"type": "SINGLE", "filters": [], "outputFile": apk.name}]}))
        self.assertEqual(apk, geo.metadata_apk(self.root, fixture=owner.FIXTURE, package=owner.PACKAGE))
        with self.assertRaises(ValueError): geo.metadata_apk(self.root, fixture=owner.FIXTURE, package=geo.PACKAGE)
        owner.is_owned = lambda: False
        with patch.object(owner, "readback") as read, self.assertRaises(ValueError): owner.control("uninstall", owner.PACKAGE)
        read.assert_not_called()


if __name__ == "__main__": unittest.main()
