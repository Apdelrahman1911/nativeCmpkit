"""NEW bounded source controls, not Android execution or a native certificate.

These tests never invoke a planner, compiler, controller, subprocess or Git. Only
the new pure contract's manifest/receipt validators execute on inert inputs.
"""
from __future__ import annotations

import ast
import importlib.util
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
CI = ROOT / "scripts/ci"
FIXTURE = ROOT / "tests/consumer/android-permission-lifecycle"
KT = ROOT / "calf-permissions/core/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/permissions"
PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.permissionlifecycle"
APP = FIXTURE / "src/main/kotlin" / PACKAGE.replace(".", "/")
ANDROID = "{http://schemas.android.com/apk/res/android}"
FOCUSES = {
    "android-permission-location-api35": "api35ApproximateFineRequestAndForegroundBackgroundBatchUseRealDialogs",
    "android-permission-lifecycle-grant-api35": "settingsGrantRepeatedResumeAndDisposedBatchKeepTheSameNativeProcess",
    "android-permission-lifecycle-revoke-api35": "notificationSettingsRevocationRefreshesSingleAndBatchWithoutProcessDeath",
}


def source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def contract():
    path = CI / "android_permission_lifecycle_contract.py"
    spec = importlib.util.spec_from_file_location("new_permission_lifecycle_contract", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AndroidPermissionLifecycleSourceTests(unittest.TestCase):
    def test_three_api35_single_method_routes_never_use_comma_or_full_class(self):
        c = contract()
        self.assertEqual(set(FOCUSES), set(c.SPECS))
        for focus, method in FOCUSES.items():
            self.assertEqual((method,), c.SPECS[focus]["methods"])
            self.assertEqual(35, c.API)
            self.assertEqual(c.CLASS + "#" + method, c.test_filter(focus))
            self.assertNotIn(",", c.test_filter(focus))
        with self.assertRaises(ValueError):
            c.test_filter("android-permission-demo-contracts")

    def test_manifest_exact_five_runtime_permissions_and_signature_only_control(self):
        c = contract()
        payload = (FIXTURE / "src/main/AndroidManifest.xml").read_bytes()
        self.assertTrue(c.validate_manifest(payload, compiled=False)["signature_control_only"])
        manifest = ET.fromstring(payload)
        names = {p.get(ANDROID + "name") for p in manifest.findall("uses-permission")}
        self.assertEqual(c.RUNTIME_PERMISSIONS, names)
        self.assertNotIn("android.permission.CALL_PHONE", names)
        self.assertNotIn("android.permission.MANAGE_EXTERNAL_STORAGE", names)

    def test_manifest_refuses_extra_permission_shared_uid_and_unprotected_component(self):
        c = contract()
        payload = (FIXTURE / "src/main/AndroidManifest.xml").read_bytes()
        for mutation in ("permission", "uid", "component", "wrong-api", "wrong-target"):
            with self.subTest(mutation=mutation):
                manifest = ET.fromstring(payload)
                compiled = mutation in {"wrong-api", "wrong-target"}
                if mutation == "permission":
                    ET.SubElement(manifest, "uses-permission", {ANDROID + "name": "android.permission.READ_SMS"})
                elif mutation == "uid":
                    manifest.set(ANDROID + "sharedUserId", "android.uid.system")
                elif mutation == "component":
                    manifest.find("application/service").attrib.pop(ANDROID + "permission")
                else:
                    manifest.set("package", PACKAGE)
                    manifest.find("application").set(ANDROID + "debuggable", "true")
                    ET.SubElement(manifest, "uses-sdk", {ANDROID + "minSdkVersion": "35" if mutation != "wrong-api" else "34",
                        ANDROID + "targetSdkVersion": "37" if mutation != "wrong-target" else "35"})
                with self.assertRaises(ValueError):
                    c.validate_manifest(ET.tostring(manifest), compiled=compiled)

    def test_public_composition_only_actual_callbacks_and_no_manual_status_assignment(self):
        text = source(APP / "PermissionLifecycleActivity.kt")
        for token in ("rememberPermissionState(Permission.FineLocation)", "rememberPermissionState(Permission.CoarseLocation)",
                      "rememberPermissionState(Permission.BackgroundLocation)", "rememberPermissionState(Permission.Camera)",
                      "rememberPermissionState(Permission.Notification)", "rememberMultiplePermissionsState(",
                      "SideEffect", "DisposableEffect", "onDispose"):
            self.assertIn(token, text)
        self.assertNotRegex(text, r"\b(?:dispatchResult|onNativeResult|grantRuntimePermission|revokeRuntimePermission|adoptShellPermissionIdentity)\s*\(")
        self.assertNotRegex(text, r"\.status\s*=")
        self.assertNotIn("LocalInspectionMode", text)
        self.assertNotIn("sample", text.lower())

    def test_platform_result_is_observed_before_super_not_manufactured(self):
        text = source(APP / "PermissionLifecycleActivity.kt")
        self.assertIn("override fun onRequestPermissionsResult(", text)
        self.assertIn("nativePermissionResults.add", text)
        self.assertIn("super.onRequestPermissionsResult(requestCode, permissions, grantResults)", text)
        self.assertLess(text.index("nativePermissionResults.add"), text.index("super.onRequestPermissionsResult("))
        self.assertIn("permissions.toList()", text)
        self.assertIn("grantResults.toList()", text)

    def test_signed_service_binds_actual_sender_and_nonce(self):
        text = source(APP / "PermissionLifecycleService.kt")
        for token in ("request.sendingUid", "names == listOf(REPORTER)", "PackageManager.SIGNATURE_MATCH",
                      'Regex("[a-f0-9]{32}")', "Process.myPid()", "Process.myUid()", "generation"):
            self.assertIn(token, text)
        self.assertNotIn("Runtime.getRuntime", text)

    def test_bridge_rejects_binder_death_pid_and_activity_replacement_without_rebind(self):
        text = source(KT / "OwnedPermissionLifecycle.kt")
        for token in ("IBinder.DeathRecipient", "linkToDeath", 'protocolError = "Owned lifecycle Binder died"',
                      "assertEquals(nativePid, pid)", "assertEquals(generation, actual)", "assertSameIdentity",
                      'getString("activityGeneration")', "assertIs<Boolean>", "CountDownLatch", "finally"):
            self.assertIn(token, text)
        self.assertEqual(1, text.count("context.bindService("))
        self.assertNotRegex(text, r"\b(?:reconnect|restart|rebind|revive)\s*\(")
        self.assertNotIn("FLAG_ACTIVITY_CLEAR_TASK", text)

    def test_location_requires_real_native_arrays_approximate_and_settings_only(self):
        text = source(KT / "AndroidPermissionLifecycleDeviceTest.kt")
        for token in (FOCUSES["android-permission-location-api35"], 'consumer.request("request-background")',
                      '"RequiresForeground"', '"Approximate"', '"RequiresSettings"', '"SettingsOnly"',
                      'consumer.request("request-location-batch")', "assertNativePermissionResult", "Manifest.permission.ACCESS_COARSE_LOCATION",
                      "Manifest.permission.ACCESS_FINE_LOCATION", '"nativePermissionResults"'):
            self.assertIn(token, text)
        self.assertIn("assertEquals(2,", text)
        self.assertNotIn("android-geo-prerequisites", text)

    def test_grant_resume_batch_and_disposal_require_actual_settings_and_same_identity(self):
        text = source(KT / "AndroidPermissionLifecycleDeviceTest.kt")
        for token in (FOCUSES["android-permission-lifecycle-grant-api35"], 'consumer.request("open-camera-settings")',
                      "ui.cameraGrant()", "consumer.returnFromSettings(", 'consumer.request("dispose-content")',
                      'consumer.request("open-notification-settings")', "ui.notificationToggle(true)",
                      '"retained.Notification"', '"batch.Notification"', "assertSameIdentity", '"disposalCount"'):
            self.assertIn(token, text)

    def test_revocation_cannot_accept_process_restart_appop_or_synthetic_resume(self):
        text = source(KT / "AndroidPermissionLifecycleDeviceTest.kt")
        for token in (FOCUSES["android-permission-lifecycle-revoke-api35"], "ui.notificationToggle(false)",
                      "consumer.returnFromSettings(", "assertSameIdentity", "Manifest.permission.POST_NOTIFICATIONS",
                      '"batch.Notification"', '"callbacks"'):
            self.assertIn(token, text)
        combined = text + source(KT / "OwnedPermissionLifecycle.kt") + source(KT / "PermissionLifecycleSystemUi.kt")
        self.assertNotRegex(combined, r"\b(?:grantRuntimePermission|revokeRuntimePermission|dispatchResult|adoptShellPermissionIdentity|execShellCommand)\s*\(")
        self.assertNotIn("appops", combined.lower())
        self.assertNotIn("handleLifecycleEvent", combined)

    def test_ui_requires_system_root_refresh_unique_visible_node_and_absolute_bound(self):
        text = source(KT / "PermissionLifecycleSystemUi.kt")
        for token in ("SystemClock.elapsedRealtime()", "deadline", "node.refresh()", "node.isVisibleToUser", "node.isEnabled",
                      "ApplicationInfo.FLAG_SYSTEM", "ApplicationInfo.FLAG_UPDATED_SYSTEM_APP", "assertEquals(1, matches.size)",
                      "ACTION_CLICK", "GLOBAL_ACTION_BACK", "finally", "recycle()"):
            self.assertIn(token, text)
        self.assertNotIn("performGlobalAction(AccessibilityService.GLOBAL_ACTION_HOME)", text)
        self.assertNotRegex(text, r"\b(?:click|tap)\s*\(\s*\d+\s*,")

    def test_controller_preserves_source_apk_signer_and_fresh_install_no_runtime_grant(self):
        text = source(CI / "android_permission_lifecycle.py")
        for token in ("OwnedShareRecipient", "source_contract(self.root)", "self.readback() is None", "signer_certificate",
                      "private_key_certificate_sha256", 'self.control("install", "-t",', "installed_readback",
                      "validate_prepared_receipt", "source_contract(self.root) == contract", "finally", "super().close()"):
            self.assertIn(token, text)
        self.assertNotIn('"-g"', text)
        self.assertNotIn('"-r"', text)

    def test_finite_routing_reuses_existing_api35_slot_not_accepted_demo(self):
        c = contract()
        library = source(CI / "library_tests.py")
        matrix = source(CI / "workflow_matrix.py")
        workflow = source(ROOT / ".github/workflows/gradle.yml")
        self.assertIn("permission_lifecycle.SPECS", library)
        self.assertIn("permission_lifecycle.FOCUSES", matrix)
        self.assertIn('("android-device-api35",)', matrix)
        for focus in FOCUSES:
            self.assertIn(focus, workflow)
            self.assertNotIn("AndroidPermissionDemoDeviceTest", c.SPECS[focus]["classname"])
        self.assertEqual(3, len(c.SPECS))
        ast.parse(library)
        ast.parse(matrix)

    def test_device_owner_assigned_before_prepare_and_closed_in_finally(self):
        text = source(CI / "android_device_tests.py")
        self.assertIn("permission_lifecycle_required", text)
        creation = text.index("permission_lifecycle = android_permission_lifecycle.OwnedPermissionLifecycle(")
        preparation = text.index("permission_lifecycle.prepare()", creation)
        cleanup = text.index("permission_lifecycle.close()", preparation)
        self.assertLess(creation, preparation)
        self.assertLess(text.index("finally:", preparation), cleanup)
        self.assertIn("android_permission_lifecycle_receipt", text)
        self.assertIn('"owned_recipient_removed": False', text[cleanup:cleanup + 900])


    def test_new_complete_source_readback_and_receipt_refuse_missing_forged_native_inputs(self):
        c = contract()
        receipt = c.source_contract(ROOT)
        c.validate_source_receipt(receipt)
        self.assertEqual(set(c.SOURCE_FILES), set(receipt["source_inputs"]))
        self.assertEqual(len(c.SOURCE_FILES), len(set(c.SOURCE_FILES)))
        self.assertFalse(receipt["native_or_compile_success_inferred"])
        self.assertNotIn("AGENTS.md", receipt["source_inputs"])
        for name in ("library_tests.py", "android_device_tests.py", "workflow_matrix.py", "android_permission_lifecycle.py"):
            self.assertIn("scripts/ci/" + name, receipt["source_inputs"])
        for mutation in ("missing", "digest", "native", "wrong-api", "linked-claim"):
            with self.subTest(mutation=mutation):
                altered = copy.deepcopy(receipt)
                if mutation == "missing": altered["source_inputs"].pop(c.SOURCE)
                elif mutation == "digest": altered["source_inputs_sha256"] = "0" * 64
                elif mutation == "native": altered["native_or_compile_success_inferred"] = True
                elif mutation == "wrong-api": altered["verification_api_level"] = 34
                else: altered["extra"] = "not-the-exact-source-schema"
                with self.assertRaises(ValueError): c.validate_source_receipt(altered)

    def test_new_prepared_receipt_refuses_wrong_focus_api_certificate_source_and_runtime_grant(self):
        c = contract()
        inputs = dict.fromkeys(c.SOURCE_FILES, "1" * 64)
        bound = {"schema_version": 1, "source_inputs": inputs,
            "source_inputs_sha256": hashlib.sha256("".join(p + "\0" + inputs[p] + "\n" for p in sorted(inputs)).encode()).hexdigest(),
            "source_policy_verified": True, "verification_api_level": 35, "native_or_compile_success_inferred": False}
        focus = "android-permission-lifecycle-revoke-api35"
        inert = {"verification_api_level": 35, "focus": focus, "package": c.PACKAGE, "source_fixture": c.FIXTURE,
            "prepare_status": "passed", "recipient_installed": True, "automatic_runtime_permission_grant": False,
            "source_contract": bound, "source_apk_sha256": "2" * 64, "source_apk_bytes": 4096,
            "installed_readback": {"apk_sha256": "2" * 64, "exact_one_APK_path_observed": True},
            "apk_policy": {"compiled_manifest_inspected": True, "signature_control_only": True,
                "separate_uid_manifest": True, "five_runtime_permissions_only": True,
                "certificate_sha256": "3" * 64, "private_key_certificate_sha256": "3" * 64,
                "signature_verification_min_sdk_version": 35, "signature_verification_max_sdk_version": 35}}
        c.validate_prepared_receipt(inert, bound, 35, focus=focus)  # Inert validator boundary only, not a device receipt.
        changes = (("focus", "android-permission-location-api35"), ("verification_api_level", True),
            ("automatic_runtime_permission_grant", True), ("prepare_status", "failed"), ("recipient_installed", False),
            ("source_apk_bytes", False), ("source_apk_sha256", "4" * 64))
        for key, value in changes:
            with self.subTest(key=key):
                changed = copy.deepcopy(inert); changed[key] = value
                with self.assertRaises(ValueError): c.validate_prepared_receipt(changed, bound, 35, focus=focus)
        for key, value in (("private_key_certificate_sha256", "4" * 64),
                           ("signature_verification_max_sdk_version", 34), ("separate_uid_manifest", False)):
            changed = copy.deepcopy(inert); changed["apk_policy"][key] = value
            with self.assertRaises(ValueError): c.validate_prepared_receipt(changed, bound, 35, focus=focus)
        changed = copy.deepcopy(inert); changed["source_contract"]["source_inputs"][c.SOURCE] = "4" * 64
        with self.assertRaises(ValueError): c.validate_prepared_receipt(changed, bound, 35, focus=focus)

    def test_new_request_refuses_boolean_old_api_wrong_module_broad_focus_and_unbound_plan(self):
        c = contract()
        for focus in FOCUSES:
            c.validate_request(35, (c.MODULE,), focus)
        for api, modules, focus in ((True, (c.MODULE,), next(iter(FOCUSES))), (34, (c.MODULE,), next(iter(FOCUSES))),
            (35, ("calf-io",), next(iter(FOCUSES))), (35, (c.MODULE, "calf-io"), next(iter(FOCUSES))),
            (35, (c.MODULE,), None), (35, (c.MODULE,), "android-permission-demo-contracts")):
            with self.assertRaises(ValueError): c.validate_request(api, modules, focus)
        bound = c.source_contract(ROOT)
        for focus in FOCUSES:
            plan = {"suite": "android-device", "explicit_test_focus": focus, "explicit_module_subset": [c.MODULE],
                "complete_suite_requested": False, "android_permission_lifecycle": {"package": c.PACKAGE,
                    "source_fixture": c.FIXTURE, "verification_api_level": 35, "source_contract": bound}}
            c.validate_plan(plan)
            altered = copy.deepcopy(plan); altered["explicit_module_subset"] = ["calf-io", c.MODULE]
            with self.assertRaises(ValueError): c.validate_plan(altered)
            altered = copy.deepcopy(plan); altered["explicit_test_focus"] = "android-permission-demo-contracts"
            with self.assertRaises(ValueError): c.validate_plan(altered)

    def test_new_own_metadata_parser_never_expands_accepted_whitelist_or_allows_split_paths(self):
        c = contract()
        metadata = {"artifactType": {"type": "APK"}, "applicationId": c.PACKAGE, "variantName": "debug",
            "elements": [{"type": "SINGLE", "filters": [], "outputFile": "app-debug.apk"}]}
        self.assertEqual("app-debug.apk", c.validate_metadata(json.dumps(metadata).encode()))
        for mutation in ("package", "variant", "split", "path", "duplicate", "nonfinite"):
            changed = copy.deepcopy(metadata)
            if mutation == "package": changed["applicationId"] = "foreign.test"
            elif mutation == "variant": changed["variantName"] = "release"
            elif mutation == "split": changed["elements"].append(dict(changed["elements"][0]))
            elif mutation == "path": changed["elements"][0]["outputFile"] = "../foreign.apk"
            payload = (b'{"artifactType":{},"artifactType":{}}' if mutation == "duplicate" else
                       b'{"artifactType":NaN}' if mutation == "nonfinite" else json.dumps(changed).encode())
            with self.assertRaises(ValueError): c.validate_metadata(payload)
        controller = source(CI / "android_permission_lifecycle.py")
        self.assertIn("def metadata_apk(self)", controller)
        self.assertNotIn("from android_geo_probe import metadata_apk", controller)
        self.assertNotIn(c.FIXTURE, source(CI / "android_geo_probe.py"))

    def test_new_reporter_permission_exception_is_exact_signature_only_not_native_grant(self):
        c = contract()
        payload = (ROOT / c.MODULE / "src/androidDeviceTest/AndroidManifest.xml").read_bytes()
        c.validate_reporter_source(payload)
        for permission in ("android.permission.ACCESS_FINE_LOCATION", "android.permission.POST_NOTIFICATIONS",
                           c.PACKAGE + ".ARBITRARY_CONTROL"):
            manifest = ET.fromstring(payload)
            ET.SubElement(manifest, "uses-permission", {ANDROID + "name": permission})
            with self.assertRaises(ValueError): c.validate_reporter_source(ET.tostring(manifest))
        storage = source(CI / "android_storage_probe.py")
        self.assertIn('PERMISSION_LIFECYCLE_CONTROL = "' + c.PERMISSION + '"', storage)
        self.assertIn("allowed = {PERMISSION, PERMISSION_DEMO_BIND, PERMISSION_LIFECYCLE_CONTROL,", storage)
        self.assertIn("set(requested) <= {PERMISSION, PERMISSION_DEMO_BIND, PERMISSION_LIFECYCLE_CONTROL}", storage)
        self.assertIn('"Reporter cannot bypass another UID\'s native storage or SAF grant"', storage)

    def test_new_command_receipt_gates_and_actual_api_source_rechecks_preserve_assembly(self):
        text = source(CI / "library_tests.py")
        tree = ast.parse(text)
        command = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "gradle_command")
        body = ast.get_source_segment(text, command)
        self.assertIn("android_permission_lifecycle_receipt is not None and (not lifecycle_required or for_assembly)", body)
        self.assertIn("if lifecycle_required:", body)
        self.assertIn("if lifecycle_required and not for_assembly:", body)
        self.assertIn("permission_lifecycle.validate_prepared_receipt", body)
        self.assertIn('focus=test_plan["explicit_test_focus"]', body)
        self.assertIn('permission_lifecycle.source_contract(root) != test_plan["android_permission_lifecycle"]["source_contract"]', body)
        self.assertEqual(1, body.count("nativecmpkitOwnedPermissionLifecycle=true"))
        self.assertEqual(1, body.count("nativecmpkitPermissionLifecycleFocus="))
        run = ast.get_source_segment(text, next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run"))
        self.assertIn("android_permission_lifecycle_required(test_plan) and android_user_home is None", run)
        self.assertIn('if actual_api != "35":', run)
        self.assertIn('receipt["android_permission_lifecycle"] = dict(android_permission_lifecycle_receipt)', run)

    def test_new_direct_controller_route_checks_precede_sdk_output_host_and_owner_mutation(self):
        text = source(CI / "android_device_tests.py")
        tree = ast.parse(text)
        body = ast.get_source_segment(text, next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_run"))
        self.assertLess(body.index("validate_api_selection(api_level, only_modules, focus)"), body.index("output = "))
        run = ast.get_source_segment(text, next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run"))
        self.assertLess(run.index("validate_api_selection(api_level, only_modules, focus)"), run.index("require_host()"))
        self.assertLess(run.index("focus in permission_lifecycle_contract.FOCUSES"), run.index("require_host()"))
        self.assertIn("permission_lifecycle_contract.validate_request(api_level, modules, focus)", text)
        self.assertIn('mkdir(mode=0o700 if permission_lifecycle_required else 0o777)', text)
        self.assertIn('environment=env, api_level=api_level, focus=focus)', text)
        self.assertIn('result["permission_lifecycle_source_unchanged_after_cleanup"] = (', text)
        self.assertIn('result.get("permission_lifecycle", {}).get("prepare_status") == "passed"', text)
        self.assertIn('result["permission_lifecycle"].get("cleanup_status") == "passed"', text)
        self.assertIn('result["permission_lifecycle"].get("owned_recipient_removed") is True', text)
        self.assertIn('or permission_lifecycle is not None or storage_probe is not None', text)

    def test_new_back_stability_and_teardown_keep_native_failure_and_all_owned_cleanup(self):
        ui = source(KT / "PermissionLifecycleSystemUi.kt")
        self.assertIn("automation.waitForIdle(250, minOf(4000L, remaining))", ui)
        self.assertLess(ui.index("performGlobalAction(AccessibilityService.GLOBAL_ACTION_BACK)"), ui.index("automation.waitForIdle"))
        bridge = source(KT / "OwnedPermissionLifecycle.kt")
        self.assertIn('assertNull(binder, "A replacement lifecycle Binder cannot be admitted")', bridge)
        self.assertIn("if (activityGeneration == null) activityGeneration = activeGeneration else assertEquals(activityGeneration, activeGeneration)", bridge)
        self.assertIn('assertNull(protocolError, "A lifecycle protocol/death failure cannot pass as clean native disposal")', bridge)
        for text in (bridge, source(KT / "AndroidPermissionLifecycleDeviceTest.kt")):
            self.assertIn("addSuppressed(error)", text)
            self.assertIn("failure?.let { throw it }", text)

    def test_new_disposable_build_is_public_source_dependency_only_and_never_publication(self):
        build = source(FIXTURE / "build.gradle.kts")
        settings = source(FIXTURE / "settings.gradle.kts")
        self.assertIn("minSdk = 35", build)
        self.assertIn("targetSdk = 37", build)
        self.assertIn('versionName = "verification-only-api35-permission-lifecycle"', build)
        for module in ("core", "location", "background-location", "camera", "notifications"):
            self.assertIn('implementation("verification.nativecmpkit:unpublished-permission-' + module + '")', build)
            self.assertIn('project(":calf-permissions:calf-permissions-' + module + '")', settings)
        self.assertNotIn("module.publication", build)
        self.assertNotIn("maven-publish", build)
        self.assertNotIn("calf-sample", settings)
        workflow = source(ROOT / ".github/workflows/gradle.yml")
        self.assertIn("build/ci-verification/${{ matrix.slot }}/permission-lifecycle/receipt.json", workflow)


if __name__ == "__main__":
    unittest.main()
