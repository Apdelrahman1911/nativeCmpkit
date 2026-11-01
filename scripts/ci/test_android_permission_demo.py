"""Important synthetic/source permission-fixture guards. ZERO real APK builds or native results."""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

import android_device_tests as device
import android_permission_demo as demo
import android_geo_probe
import library_tests as lt
import workflow_matrix as workflow

ROOT = Path(__file__).resolve().parents[2]


def prepared(source, api=35):
    return {"package": demo.PACKAGE, "source_fixture": demo.FIXTURE, "verification_api_level": api,
        "prepare_status": "passed", "recipient_installed": True, "automatic_runtime_permission_grant": False,
        "source_contract": source, "source_apk_sha256": "a" * 64,
        "installed_readback": {"apk_sha256": "a" * 64, "exact_one_APK_path_observed": True},
        "apk_policy": {"compiled_manifest_inspected": True, "dedicated_call_variant": True,
            "all_files_and_sms_absent": True, "signature_control_only": True, "separate_uid_manifest": True,
            "certificate_sha256": "b" * 64, "private_key_certificate_sha256": "b" * 64,
            "signature_verification_min_sdk_version": api, "signature_verification_max_sdk_version": api}}


class AndroidPermissionDemoGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = demo.source_contract(ROOT)
        cls.plan = lt.plan(ROOT, "android-device", only_modules=("calf-permissions/core",), focus=lt.ANDROID_PERMISSION_DEMO_FOCUS)

    def test_finite_profiles_select_three_35_methods_and_one_media_method_per_api(self):
        for profile, api, focus, count in (("android-permission-demo", "35", lt.ANDROID_PERMISSION_DEMO_FOCUS, 3),
            ("android-media-selection-api33", "33", lt.ANDROID_MEDIA_SELECTION_FOCUS, 1),
            ("android-media-selection-api34", "34", lt.ANDROID_MEDIA_SELECTION_FOCUS, 1)):
            with self.subTest(profile=profile):
                row = workflow.matrix(profile)["include"].copy().pop()
                self.assertEqual(api, row["emulator-api"])
                self.assertEqual("calf-permissions/core", row["test-modules"])
                self.assertEqual(focus, row["test-focus"])
                plan = lt.plan(ROOT, "android-device", only_modules=("calf-permissions/core",), focus=focus)
                self.assertEqual(count, len(plan["expected"][0]["required_testcases"]))
                self.assertFalse(plan["complete_suite_requested"])
                self.assertTrue(lt.validate_test_focus(plan))
        self.assertEqual(11, len(workflow.matrix("all")["include"]))
        self.assertTrue(set(("calf-io", "calf-file-picker", "calf-geo", "calf-webview", "calf-ui", "calf-navigation", "calf-share",
            "calf-camera-picker")) < set(lt.MINIMUM_MODULES["android-device"]))

    def test_api33_34_controller_selection_has_no_general_or_camera_fallback(self):
        for api in (33, 34):
            device.validate_api_selection(api, ("calf-permissions/core",), lt.ANDROID_MEDIA_SELECTION_FOCUS)
            for modules, focus in ((None, None), (("calf-permissions/core",), None),
                (("calf-permissions/core",), lt.ANDROID_PERMISSION_DEMO_FOCUS), (("calf-camera-picker",), lt.ANDROID_CAMERA_PROVIDER_FOCUS)):
                with self.subTest(api=api, modules=modules, focus=focus), self.assertRaises(ValueError):
                    device.validate_api_selection(api, modules, focus)
        for api in (True, "33", 32, 36):
            with self.subTest(api=api), self.assertRaises(ValueError):
                device.validate_api_selection(api, ("calf-permissions/core",), lt.ANDROID_MEDIA_SELECTION_FOCUS)

    def test_source_contract_pins_public_native_calls_and_never_asserts_execution(self):
        self.assertIs(True, self.contract["source_policy_verified"])
        self.assertIs(False, self.contract["native_or_compile_success_inferred"])
        for name in ("PermissionDemoActivity", "PermissionDemoService"):
            self.assertIn(demo.APPLICATION_KOTLIN + name + ".kt", self.contract["source_inputs"])
        self.assertEqual(lt.input_digest(self.contract["source_inputs"]), self.contract["source_inputs_sha256"])

    def test_variant_manifest_rejects_unapproved_permission_and_shared_uid(self):
        payload = (ROOT / demo.FIXTURE / "src/main/AndroidManifest.xml").read_bytes()
        demo.validate_manifest(payload, compiled=False)
        for permission in ("MANAGE_EXTERNAL_STORAGE", "READ_SMS", "SEND_SMS", "RECEIVE_SMS", "READ_EXTERNAL_STORAGE"):
            root = ET.fromstring(payload)
            ET.SubElement(root, "uses-permission", {demo.ANDROID + "name": "android.permission." + permission})
            with self.subTest(permission=permission), self.assertRaises(ValueError):
                demo.validate_manifest(ET.tostring(root), compiled=False)
        root = ET.fromstring(payload)
        root.set(demo.ANDROID + "sharedUserId", "android.uid.system")
        with self.assertRaises(ValueError):
            demo.validate_manifest(ET.tostring(root), compiled=False)

    def test_variant_controls_cannot_lose_their_signature_boundary(self):
        payload = (ROOT / demo.FIXTURE / "src/main/AndroidManifest.xml").read_bytes()
        for tag in ("activity", "service"):
            root = ET.fromstring(payload)
            root.find("application/" + tag).attrib.pop(demo.ANDROID + "permission")
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                demo.validate_manifest(ET.tostring(root), compiled=False)
        root = ET.fromstring(payload)
        root.find("permission").set(demo.ANDROID + "protectionLevel", "normal")
        with self.assertRaises(ValueError):
            demo.validate_manifest(ET.tostring(root), compiled=False)

    def test_generated_manifest_models_require_exact_actual_sdk_and_debug_variant(self):
        root = ET.parse(ROOT / demo.FIXTURE / "src/main/AndroidManifest.xml").getroot()
        root.set("package", demo.PACKAGE)
        root.find("application").set(demo.ANDROID + "debuggable", "true")
        sdk = ET.SubElement(root, "uses-sdk", {demo.ANDROID + "minSdkVersion": "33", demo.ANDROID + "targetSdkVersion": "37"})
        self.assertTrue(demo.validate_manifest(ET.tostring(root), compiled=True)["compiled_manifest_inspected"])
        for key, value in (("minSdkVersion", "23"), ("targetSdkVersion", "33"), ("maxSdkVersion", "34")):
            modeled = deepcopy(root)
            modeled.find("uses-sdk").set(demo.ANDROID + key, value)
            with self.subTest(key=key), self.assertRaises(ValueError):
                demo.validate_manifest(ET.tostring(modeled), compiled=True)

    def test_prepared_receipt_refuses_stale_source_apk_key_and_automatic_grant(self):
        receipt = prepared(self.contract)
        demo.validate_prepared_receipt(receipt, self.contract, 35)
        for mutate in (
            lambda value: value.update(automatic_runtime_permission_grant=True),
            lambda value: value.update(prepare_status="failed"),
            lambda value: value["installed_readback"].update(apk_sha256="c" * 64),
            lambda value: value["apk_policy"].update(private_key_certificate_sha256="c" * 64),
            lambda value: value["source_contract"].update(source_inputs_sha256="c" * 64),
        ):
            modeled = deepcopy(receipt)
            expected = deepcopy(self.contract)
            mutate(modeled)
            with self.subTest(model=modeled), self.assertRaises(ValueError):
                demo.validate_prepared_receipt(modeled, expected, 35)

    def test_signer_range_cannot_expand_or_change_type_away_from_authorized_api(self):
        for api in (33, 34, 35):
            receipt = prepared(self.contract, api)
            demo.validate_prepared_receipt(receipt, self.contract, api)
            for minimum, maximum in ((23, api), (api, 37), (str(api), api), (api, str(api)), (True, api)):
                modeled = deepcopy(receipt)
                modeled["apk_policy"].update(signature_verification_min_sdk_version=minimum,
                    signature_verification_max_sdk_version=maximum)
                with self.subTest(api=api, minimum=minimum, maximum=maximum), self.assertRaises(ValueError):
                    demo.validate_prepared_receipt(modeled, self.contract, api)
            with self.assertRaises(ValueError):
                demo.validate_prepared_receipt(receipt, self.contract, 34 if api != 34 else 35)

    def test_helper_bit_cannot_be_emitted_without_actual_prepared_receipt(self):
        with self.assertRaises(ValueError):
            lt.gradle_command("android-device", self.plan, android_serial="emulator-5588", root=ROOT)
        compile_command = lt.gradle_command("android-device", self.plan, android_serial="emulator-5588", root=ROOT, for_assembly=True)
        self.assertNotIn("-Pandroid.testInstrumentationRunnerArguments.nativecmpkitOwnedPermissionDemo=true", compile_command)
        self.assertEqual(":calf-permissions:calf-permissions-core:assembleAndroidDeviceTest", compile_command[-1])
        command = lt.gradle_command("android-device", self.plan, android_serial="emulator-5588", root=ROOT,
            android_permission_demo_receipt=prepared(self.contract))
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.nativecmpkitOwnedPermissionDemo=true", command)
        self.assertEqual(":calf-permissions:calf-permissions-core:connectedAndroidDeviceTest", command[-1])
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.class=" + lt.ANDROID_PERMISSION_DEVICE_SPECS[
            lt.ANDROID_PERMISSION_DEMO_FOCUS]["classname"], command)

    def test_finite_plan_refuses_foreign_or_missing_case_inventory(self):
        for mutate in (
            lambda plan: plan["expected"][0].update(test_filter="foreign.Class"),
            lambda plan: plan["expected"][0]["required_testcases"].pop(),
            lambda plan: plan["expected"][0].update(module="sample/android"),
            lambda plan: plan.update(android_permission_demo=None),
        ):
            modeled = deepcopy(self.plan)
            mutate(modeled)
            with self.subTest(plan=modeled), self.assertRaises(ValueError):
                lt.validate_test_focus(modeled)

    def test_apk_metadata_only_allows_the_exact_owned_unsplit_pair(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / demo.FIXTURE / "build/outputs/apk/debug"
            output.mkdir(parents=True)
            apk = output / "permission-demo-debug.apk"
            apk.write_bytes(b"synthetic metadata fixture, not a compiled APK")
            metadata = {"artifactType": {"type": "APK"}, "applicationId": demo.PACKAGE, "variantName": "debug",
                "elements": [{"type": "SINGLE", "filters": [], "outputFile": apk.name}]}
            (output / "output-metadata.json").write_text(json.dumps(metadata))
            self.assertEqual(apk, android_geo_probe.metadata_apk(root, fixture=demo.FIXTURE, package=demo.PACKAGE))
            with self.assertRaises(ValueError):
                android_geo_probe.metadata_apk(root, fixture=demo.FIXTURE, package="foreign.package")
            metadata["elements"][0]["filters"] = [{"filterType": "ABI", "value": "x86_64"}]
            (output / "output-metadata.json").write_text(json.dumps(metadata))
            with self.assertRaises(ValueError):
                android_geo_probe.metadata_apk(root, fixture=demo.FIXTURE, package=demo.PACKAGE)

    def test_modeled_junit_requires_every_new_case_one_fresh_report_and_no_skip(self):
        def collect(methods, disposition=None, split=False):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                expected = self.plan["expected"][0]
                folder = root / expected["report_directory"]
                folder.mkdir(parents=True)
                groups = [methods] if not split else [methods[:1], methods[1:]]
                started = time.time_ns()
                for index, group in enumerate(groups):
                    suite = ET.Element("testsuite", {"tests": str(len(group)), "failures": "0", "errors": "0",
                        "skipped": str(1 if disposition == "skipped" and index == 0 else 0)})
                    for position, method in enumerate(group):
                        case = ET.SubElement(suite, "testcase", {"classname": method["classname"], "name": method["name"], "time": "0.01"})
                        if disposition == "skipped" and index == 0 and position == 0: ET.SubElement(case, "skipped")
                    (folder / ("TEST-modeled" + str(index) + ".xml")).write_bytes(ET.tostring(suite))
                return lt.collect_reports(root, self.plan, started, time.time_ns(), Counter({expected["task"]: 1}))
        methods = self.plan["expected"][0]["required_testcases"]
        accepted = collect(methods)
        self.assertFalse(accepted["errors"])
        self.assertEqual(3, accepted["totals"]["passed"])
        self.assertEqual(1, len(accepted["modules"][0]["reports"]))
        for result in (collect(methods[:-1]), collect(methods, split=True), collect(methods, disposition="skipped"),
            collect(methods + [{"classname": "foreign.Class", "name": "foreignCase"}])):
            # Per-module "passed" is an observed testcase count, not the gate.
            # A missing/split/foreign report can contain individually passing
            # modeled cases while the exact-inventory gate still refuses it.
            self.assertTrue(result["errors"])


if __name__ == "__main__":
    unittest.main()
