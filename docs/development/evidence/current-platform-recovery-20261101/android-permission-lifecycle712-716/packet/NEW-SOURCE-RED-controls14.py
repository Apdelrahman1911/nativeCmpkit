"""NEW bounded source controls, not Android execution or a native certificate.

These tests never invoke a planner, compiler, controller, subprocess or Git. Only
the new pure contract's manifest/receipt validators execute on inert inputs.
"""
from __future__ import annotations

import ast
import importlib.util
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


if __name__ == "__main__":
    unittest.main()
