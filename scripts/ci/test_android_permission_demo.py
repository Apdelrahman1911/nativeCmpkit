"""Important synthetic/source permission-fixture guards. ZERO real APK builds or native results."""
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
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


class AndroidPermissionDemoInstallerReplyTest(unittest.TestCase):
    """New owning parser/prepare models only; every SDK/build/device call is mocked."""
    UNKNOWN_STDOUTS = (
        b"", b"Failure [modeled]\nSuccess\n", b"Unknown installer mode\nSuccess\n",
        b"Success\nSuccess\n", b"Success\nextra\n", b" Success\n", b"Success \n",
        b"\nSuccess\n", b"Success\n\n", b"SUCCESS\n", b"\xff\nSuccess\n",
        b"Performing streamed Install\nSuccess\n", b"Performing Streamed Install \nSuccess\n",
        b"Performing Streamed Install\n Success\n", b"Performing Streamed Install\nSuccess\x00\n",
        b"Performing Streamed Install\nSuccess\nextra\n",
    )

    @classmethod
    def setUpClass(cls):
        cls.contract = demo.source_contract(ROOT)

    @contextmanager
    def modeled_owner(self, stdout=b"Success\n", stderr=b"", exit_code=0):
        with tempfile.TemporaryDirectory(prefix="permission-installer-model-") as directory:
            root = Path(directory)
            output = root / "build/ci-verification/modeled-permission"
            output.mkdir(parents=True)
            owner = demo.OwnedPermissionDemo(root, output, root / "modeled-sdk", "emulator-5588", lambda: True,
                environment={"ANDROID_SERIAL": "emulator-5588", "ANDROID_USER_HOME": str(output / "android-user")},
                api_level=33)
            apk = root / "synthetic-not-an-APK.txt"
            apk.write_bytes(b"Modeled APK identity bytes only; not a compiled application.\n")
            installed = {"apk_sha256": lt.sha256(apk), "exact_one_APK_path_observed": True}
            owner.inspectors = Mock()
            owner.inspect_apk = Mock(return_value=deepcopy(prepared(self.contract, 33)["apk_policy"]))
            owner.readback = Mock(side_effect=[None, installed])
            owner.control = Mock(return_value=subprocess.CompletedProcess(["modeled-installer"], exit_code, stdout, stderr))
            with patch.object(demo, "source_contract", return_value=deepcopy(self.contract)) as source, \
                    patch.object(demo, "metadata_apk", return_value=apk), \
                    patch.object(demo.lt, "execute", return_value={"exit_code": 0, "elapsed_seconds": 0.01}) as assembly:
                yield owner, apk, installed, source, assembly

    def test_exact_official_reply_facts_preserve_original_line_endings_without_raw_output(self):
        for stdout, shape in ((b"Success", "success"), (b"Success\n", "success"),
            (b"Success\r\n", "success"), (b"Performing Streamed Install\nSuccess", "streamed-success"),
            (b"Performing Streamed Install\nSuccess\n", "streamed-success"),
            (b"Performing Streamed Install\r\nSuccess\r\n", "streamed-success")):
            result = subprocess.CompletedProcess(["modeled-installer"], 0, stdout, b"")
            with self.subTest(stdout=stdout):
                facts = demo.installer_reply_facts(result)
                self.assertEqual(shape, facts["stdout_shape"])
                self.assertEqual(len(stdout), facts["stdout_bytes"])
                self.assertEqual(hashlib.sha256(stdout).hexdigest(), facts["stdout_sha256"])
                self.assertEqual(0, facts["stderr_bytes"])
                self.assertTrue(facts["stderr_empty_after_trim"])
                self.assertFalse(facts["raw_stdout_stderr_or_paths_uploaded"])
                self.assertFalse(facts["native_success_inferred"])
                self.assertEqual(stdout, result.stdout)

    def test_unknown_extra_duplicate_or_success_anywhere_reply_is_never_an_official_shape(self):
        for stdout in self.UNKNOWN_STDOUTS:
            with self.subTest(stdout=stdout):
                facts = demo.installer_reply_facts(subprocess.CompletedProcess(["modeled-installer"], 0, stdout, b""))
                self.assertEqual("unrecognized", facts["stdout_shape"])
                self.assertFalse(facts["native_success_inferred"])

    def test_reply_diagnostics_are_typed_bounded_hashes_not_raw_bodies_or_acceptance(self):
        stdout, stderr = b"MODELED_BODY_NEVER_UPLOAD\xff", b"MODELED_WARNING_NEVER_UPLOAD"
        facts = demo.installer_reply_facts(subprocess.CompletedProcess(["modeled-installer"], 1, stdout, stderr))
        self.assertEqual(len(stderr), facts["stderr_bytes"])
        self.assertEqual(hashlib.sha256(stderr).hexdigest(), facts["stderr_sha256"])
        self.assertFalse(facts["stderr_empty_after_trim"])
        self.assertNotIn("MODELED_BODY", json.dumps(facts))
        self.assertNotIn("MODELED_WARNING", json.dumps(facts))
        boundary = b"x" * demo.MAX_INSTALLER_REPLY_BYTES
        self.assertEqual(len(boundary), demo.installer_reply_facts(
            subprocess.CompletedProcess(["modeled-installer"], 0, boundary, b""))["stdout_bytes"])
        for code, out, err in ((0, boundary, b"x"), (False, b"Success", b""),
            ("0", b"Success", b""), (None, b"Success", b""), (0, "Success", b""), (0, b"Success", None)):
            with self.subTest(exit_code=code, stdout_type=type(out).__name__, stderr_type=type(err).__name__), \
                    self.assertRaises(ValueError):
                demo.installer_reply_facts(subprocess.CompletedProcess(["modeled-installer"], code, out, err))

    def test_prepare_accepts_exact_streamed_success_with_unchanged_source_and_signer(self):
        with self.modeled_owner(b"Performing Streamed Install\nSuccess\n") as (owner, apk, installed, source, assembly):
            receipt = owner.prepare()
            self.assertEqual("passed", receipt["prepare_status"])
            self.assertEqual("complete", receipt["prepare_phase"])
            self.assertEqual("streamed-success", receipt["installer_reply"]["stdout_shape"])
            self.assertEqual(installed, receipt["installed_readback"])
            self.assertEqual(lt.sha256(apk), receipt["source_apk_sha256"])
            self.assertEqual(self.contract, receipt["source_contract"])
            self.assertEqual(2, source.call_count)
            owner.inspect_apk.assert_called_once_with(apk)
            owner.control.assert_called_once_with("install", "-t", str(apk), timeout=120)
            self.assertEqual(2, owner.readback.call_count)
            self.assertFalse(receipt["automatic_runtime_permission_grant"])
            self.assertFalse(receipt["manual_URI_grant"])
            demo.validate_prepared_receipt(receipt, self.contract, 33)
            self.assertNotIn("connectedAndroidDeviceTest", " ".join(assembly.call_args.args[1]))

    def test_prepare_refuses_unknown_reply_nonzero_exit_or_stderr_despite_matching_installed_bytes(self):
        models = [(stdout, b"", 0) for stdout in self.UNKNOWN_STDOUTS]
        models += [(b"Success\n", b"modeled warning\n", 0), (b"Success\n", b"", 1),
            (b"Performing Streamed Install\nSuccess\n", b"", -1)]
        for stdout, stderr, code in models:
            with self.subTest(stdout=stdout, stderr=stderr, exit_code=code), \
                    self.modeled_owner(stdout, stderr, code) as (owner, apk, installed, source, assembly):
                with self.assertRaises(ValueError):
                    owner.prepare()
                receipt = owner.receipt
                self.assertEqual("failed", receipt["prepare_status"])
                self.assertEqual("installer-reply-validation", receipt["prepare_error_phase"])
                self.assertEqual(installed, receipt["installed_readback"])
                self.assertTrue(receipt["recipient_installed"])
                self.assertTrue(owner.install_attempted)
                self.assertFalse(receipt["installer_reply"]["native_success_inferred"])
                owner.control.assert_called_once()
                with self.assertRaises(ValueError):
                    demo.validate_prepared_receipt(receipt, self.contract, 33)

    def test_installer_facts_survive_readback_failure_without_failure_body_or_passed_prepare(self):
        with self.modeled_owner() as (owner, apk, installed, source, assembly):
            owner.readback.side_effect = [None, ValueError("MODELED_READBACK_BODY_NEVER_UPLOAD")]
            with self.assertRaises(ValueError):
                owner.prepare()
            receipt = owner.receipt
            self.assertEqual("failed", receipt["prepare_status"])
            self.assertEqual("installed-byte-readback", receipt["prepare_error_phase"])
            self.assertEqual("success", receipt["installer_reply"]["stdout_shape"])
            self.assertEqual(0, receipt["install_exit_code"])
            self.assertNotIn("MODELED_READBACK_BODY", json.dumps(receipt))
            self.assertEqual(receipt, json.loads((owner.output / "receipt.json").read_text()))

    def test_prepare_phase_diagnostics_keep_source_existing_app_bytes_and_signer_refusals(self):
        for mutation, phase in (("source", "source-contract"), ("existing-app", "initial-install-absence"),
            ("assembly", "source-app-assembly"), ("policy", "source-apk-policy"),
            ("changed-source", "source-apk-source-recheck"), ("installed-bytes", "installer-reply-validation"),
            ("certificate", "prepared-receipt-validation"), ("signer-range", "prepared-receipt-validation")):
            with self.subTest(mutation=mutation), self.modeled_owner() as (owner, apk, installed, source, assembly):
                if mutation == "source": source.side_effect = ValueError("modeled-source-refusal")
                elif mutation == "existing-app": owner.readback.side_effect = [installed]
                elif mutation == "assembly": assembly.return_value = {"exit_code": 1, "elapsed_seconds": 0.01}
                elif mutation == "policy": owner.inspect_apk.side_effect = ValueError("modeled-policy-refusal")
                elif mutation == "changed-source": source.side_effect = [deepcopy(self.contract), {"foreign": True}]
                elif mutation == "installed-bytes": owner.readback.side_effect = [None, {**installed, "apk_sha256": "c" * 64}]
                elif mutation == "certificate": owner.inspect_apk.return_value["private_key_certificate_sha256"] = "c" * 64
                elif mutation == "signer-range": owner.inspect_apk.return_value["signature_verification_min_sdk_version"] = 23
                with self.assertRaises((ValueError, RuntimeError)):
                    owner.prepare()
                self.assertEqual("failed", owner.receipt["prepare_status"])
                self.assertEqual(phase, owner.receipt["prepare_error_phase"])
                self.assertEqual(owner.receipt, json.loads((owner.output / "receipt.json").read_text()))
                if phase in {"source-contract", "initial-install-absence", "source-app-assembly",
                    "source-apk-policy", "source-apk-source-recheck"}: owner.control.assert_not_called()

    def test_failed_reply_keeps_owned_cleanup_admission_without_laundering_the_failed_prepare(self):
        with self.modeled_owner(b"unknown\nSuccess\n") as (owner, apk, installed, source, assembly):
            owner.readback.side_effect = [None, installed, installed, None]
            owner.control.side_effect = [subprocess.CompletedProcess(["modeled-installer"], 0, b"unknown\nSuccess\n", b""),
                subprocess.CompletedProcess(["modeled-stop"], 0, b"", b""),
                subprocess.CompletedProcess(["modeled-uninstall"], 0, b"Success\n", b"")]
            with self.assertRaises(ValueError):
                owner.prepare()
            reply = deepcopy(owner.receipt["installer_reply"])
            receipt = owner.close()
            self.assertEqual("failed", receipt["prepare_status"])
            self.assertEqual("installer-reply-validation", receipt["prepare_error_phase"])
            self.assertEqual(reply, receipt["installer_reply"])
            self.assertEqual("passed", receipt["cleanup_status"])
            self.assertTrue(receipt["owned_identity_reverified"])
            self.assertTrue(receipt["owned_recipient_removed"])
            self.assertEqual(3, owner.control.call_count)
            self.assertEqual(("shell", "am", "force-stop", demo.PACKAGE), owner.control.call_args_list[1].args)
            self.assertEqual(("uninstall", demo.PACKAGE), owner.control.call_args_list[2].args)


if __name__ == "__main__":
    unittest.main()
