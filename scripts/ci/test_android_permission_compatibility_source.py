"""Genuinely NEW inert source controls; no compiler/controller/native/Git execution."""
from pathlib import Path
import ast
import copy
import importlib.util
import re
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/consumer/android-permission-compatibility"
KT = FIXTURE / "reporter/src/androidTest/kotlin/com/mohamedrejeb/calf/permissions"
APP = FIXTURE / "helper/src/main/kotlin/io/github/apdelrahman1911/nativecmpkit/verification/permissioncompat"
ANDROID = "{http://schemas.android.com/apk/res/android}"


def contract():
    spec = importlib.util.spec_from_file_location("new_permission_compatibility_pure_plan", ROOT / "scripts/ci/android_permission_compatibility_plan.py")
    value = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = value
    spec.loader.exec_module(value)
    return value


def text(path):
    return path.read_text(encoding="utf-8")


def helper_manifest(c, profile, role, *, compiled=False):
    root = ET.fromstring((FIXTURE / ("helper/src/manifests/" + role + ".xml")).read_bytes())
    if compiled:
        package = c.PACKAGE + "." + role
        root.set("package", package)
        for node in root.iter():
            for name, value in list(node.attrib.items()):
                node.set(name, value.replace("${applicationId}", package))
        root.find("application").set(ANDROID + "debuggable", "true")
        ET.SubElement(root, "uses-sdk", {ANDROID + "minSdkVersion": "23", ANDROID + "targetSdkVersion": str(c.row_for(profile).target)})
    return root


class AndroidPermissionCompatibilitySourceTests(unittest.TestCase):
    def test_new_exact_five_sdk_pairs_have_legacy_and_current_target_rows(self):
        c = contract()
        pairs = {(row.api, row.target) for row in c.ROWS if row.method == c.MATRIX_METHOD}
        self.assertEqual({(api, target) for api, legacy in ((23, 23), (29, 28), (30, 29), (31, 30), (33, 32)) for target in (legacy, 37)}, pairs)
        self.assertEqual(14, len(c.ROWS))
        self.assertEqual(14, len({row.profile for row in c.ROWS}))

    def test_new_profile_refuses_unknown_boolean_wrong_actual_api_and_target(self):
        c = contract()
        profile = "android-permission-compat-api29-target28"
        for value in (True, None, "all", "android-permission-demo-contracts", "android-permission-one-time-expiry"):
            with self.subTest(value=value), self.assertRaises(ValueError): c.row_for(value)
        for api, target in ((True, 28), (29.0, 28), (28, 28), (29, True), (29, 37), (29, "28")):
            with self.subTest(api=api, target=target), self.assertRaises(ValueError): c.row_for(profile, actual_api=api, actual_target=target)
        self.assertEqual(28, c.row_for(profile, actual_api=29, actual_target=28).target)

    def test_new_each_plan_is_one_method_fresh_role_apps_without_native_certificate(self):
        c = contract()
        for row in c.ROWS:
            plan = c.proposed_plan(row.profile)
            self.assertEqual(c.CLASS + "#" + row.method, plan["native_filter"])
            self.assertNotIn(",", plan["native_filter"])
            self.assertEqual([{"classname": c.CLASS, "name": row.method, "skipped_allowed": False}], plan["required_xml"])
            self.assertEqual(list(row.roles), plan["helper_roles"])
            self.assertEqual(len(row.roles), len(set(plan["helper_packages"])))
            self.assertTrue(plan["fresh_each_helper_uid_and_install_required"])
            self.assertTrue(plan["compiled_manifest_signer_installed_bytes_and_source_required"])
            self.assertFalse(plan["installer_runtime_grants_allowed"])
            self.assertFalse(plan["target_minimum_bypass_allowed"])
            self.assertFalse(plan["prepared_receipt_emitted"])
            self.assertFalse(plan["controller_or_standard_CI_ingress_implemented"])
            self.assertFalse(plan["native_or_compile_success_inferred"])

    def test_new_all_helper_roles_source_and_inert_compiled_manifests_keep_exact_declarations(self):
        c = contract()
        for row in c.ROWS:
            for role in row.roles:
                for compiled in (False, True):
                    with self.subTest(profile=row.profile, role=role, compiled=compiled):
                        policy = c.validate_helper_manifest(ET.tostring(helper_manifest(c, row.profile, role, compiled=compiled)), profile=row.profile, role=role, compiled=compiled)
                        self.assertFalse(policy["native_or_compile_success_inferred"])
        coarse = ET.fromstring((FIXTURE / "helper/src/manifests/coarse.xml").read_bytes())
        self.assertEqual({c.COARSE}, {node.get(ANDROID + "name") for node in coarse.findall("uses-permission")})
        omitted = ET.fromstring((FIXTURE / "helper/src/manifests/omitted.xml").read_bytes())
        self.assertFalse(omitted.findall("uses-permission"))
        self.assertFalse(ET.fromstring((FIXTURE / "helper/src/main/AndroidManifest.xml").read_bytes()).findall("uses-permission"))

    def test_new_helper_policy_refuses_extra_grants_caps_uid_process_sdk_and_unprotected_control(self):
        c = contract(); profile = "android-permission-compat-api29-target28"
        original = helper_manifest(c, profile, "fine", compiled=True)
        for mutation in ("extra", "cap", "uid", "process", "target", "min", "permission", "signature", "sdk23-node"):
            root = copy.deepcopy(original)
            if mutation == "extra": ET.SubElement(root, "uses-permission", {ANDROID + "name": "android.permission.MANAGE_EXTERNAL_STORAGE"})
            elif mutation == "cap": root.find("uses-permission").set(ANDROID + "maxSdkVersion", "28")
            elif mutation == "uid": root.set(ANDROID + "sharedUserId", "android.uid.system")
            elif mutation == "process": root.find("application/service").set(ANDROID + "process", ":other")
            elif mutation == "target": root.find("uses-sdk").set(ANDROID + "targetSdkVersion", "37")
            elif mutation == "min": root.find("uses-sdk").set(ANDROID + "minSdkVersion", "24")
            elif mutation == "permission": root.find("application/activity").attrib.pop(ANDROID + "permission")
            elif mutation == "signature": root.find("permission").set(ANDROID + "protectionLevel", "normal")
            else: ET.SubElement(root, "uses-permission-sdk-23", {ANDROID + "name": "android.permission.READ_SMS"})
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): c.validate_helper_manifest(ET.tostring(root), profile=profile, role="fine", compiled=True)
        with self.assertRaises(ValueError): c.validate_helper_manifest(ET.tostring(original), profile=profile, role="camera", compiled=True)

    def test_new_only_exact_compiled_androidx_startup_profile_components_are_admitted(self):
        c = contract(); profile = "android-permission-compat-api31-target37"
        root = helper_manifest(c, profile, "fine", compiled=True); app = root.find("application")
        provider = ET.SubElement(app, "provider", {ANDROID + "name": "androidx.startup.InitializationProvider", ANDROID + "authorities": c.PACKAGE + ".fine.androidx-startup", ANDROID + "exported": "false"})
        for name in sorted(c.STARTUP_INITIALIZERS): ET.SubElement(provider, "meta-data", {ANDROID + "name": name, ANDROID + "value": "androidx.startup"})
        receiver = ET.SubElement(app, "receiver", {ANDROID + "name": "androidx.profileinstaller.ProfileInstallReceiver", ANDROID + "permission": "android.permission.DUMP", ANDROID + "exported": "true"})
        for action in sorted(c.PROFILE_ACTIONS): ET.SubElement(ET.SubElement(receiver, "intent-filter"), "action", {ANDROID + "name": action})
        self.assertFalse(c.validate_helper_manifest(ET.tostring(root), profile=profile, role="fine", compiled=True)["native_or_compile_success_inferred"])
        for mutation in ("provider-export", "receiver-unprotected", "startup-unexpected", "foreign-component"):
            changed = copy.deepcopy(root)
            if mutation == "provider-export": changed.find("application/provider").set(ANDROID + "exported", "true")
            elif mutation == "receiver-unprotected": changed.find("application/receiver").attrib.pop(ANDROID + "permission")
            elif mutation == "startup-unexpected": changed.find("application/provider/meta-data").set(ANDROID + "name", "unexpected.initializer")
            else: ET.SubElement(changed.find("application"), "provider", {ANDROID + "name": "foreign.Provider"})
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): c.validate_helper_manifest(ET.tostring(changed), profile=profile, role="fine", compiled=True)

    def test_new_reporter_has_only_six_signature_controls_and_exact_helper_system_visibility(self):
        c = contract(); payload = (FIXTURE / "reporter/src/main/AndroidManifest.xml").read_bytes()
        self.assertFalse(c.validate_reporter_manifest(payload, compiled=False)["native_or_compile_success_inferred"])
        root = ET.fromstring(payload)
        ET.SubElement(root, "uses-permission", {ANDROID + "name": "android.permission.ACCESS_FINE_LOCATION"})
        with self.assertRaises(ValueError): c.validate_reporter_manifest(ET.tostring(root), compiled=False)

    def test_new_xml_bounds_malformed_and_utf16_dtd_refuse_without_parser_payload_leaks(self):
        c = contract(); profile = "android-permission-compat-api23-target23"
        for domain in ("helper", "reporter"):
            validator = (lambda payload: c.validate_reporter_manifest(payload, compiled=False)) if domain == "reporter" else (lambda payload: c.validate_helper_manifest(payload, profile=profile, role="fine", compiled=False))
            for payload in (b"", b"x" * 65537, b"<manifest><application></manifest>"):
                with self.subTest(domain=domain, payload_bytes=len(payload)), self.assertRaises(ValueError) as failure: validator(payload)
                self.assertNotIn("mismatched tag", str(failure.exception))
            relative = "reporter/src/main/AndroidManifest.xml" if domain == "reporter" else "helper/src/manifests/fine.xml"
            body = ET.tostring(ET.fromstring((FIXTURE / relative).read_bytes()), encoding="unicode")
            dtd = ('<?xml version="1.0" encoding="utf-16"?><!DOCTYPE manifest [<!ENTITY unused "inert">]>' + body).encode("utf-16")
            self.assertNotIn(b"<!DOCTYPE", dtd)
            with self.assertRaisesRegex(ValueError, "DTD/entity"): validator(dtd)

    def test_new_gradle_and_native_literal_profiles_agree_and_only_selected_debug_roles_build(self):
        c = contract(); gradle = text(FIXTURE / "helper/build.gradle.kts"); native = text(KT / "PermissionCompatibilityProfiles.kt")
        for row in c.ROWS:
            self.assertIn('"' + row.profile + '" to (' + str(row.target) + ' to setOf(', gradle)
            self.assertIn('"' + row.profile + '" to Spec(' + str(row.api) + ', ' + str(row.target) + ', setOf(', native)
            self.assertIn('"' + row.method + '"', native)
        for token in ('minSdk = 23', 'targetSdk = selected.first', 'variant.enable = role in selected.second && variant.buildType == "debug"', 'getByName("main").manifest.srcFile("src/main/AndroidManifest.xml")', 'providers.gradleProperty("nativecmpkitPermissionCompatProfile").get()'):
            self.assertIn(token, gradle)
        settings = text(FIXTURE / "settings.gradle.kts")
        for module in ("core", "location", "background-location", "camera"): self.assertIn("verification.nativecmpkit:unpublished-permission-" + module, settings)
        self.assertNotIn("maven-publish", settings + gradle)
        self.assertNotIn("overrideLibrary", "".join(text(p) for p in FIXTURE.rglob("*.xml")))

    def test_new_activity_uses_real_public_states_and_framework_arrays_before_super(self):
        value = text(APP / "PermissionCompatibilityActivity.kt")
        for token in ("rememberPermissionState(permission)", "rememberMultiplePermissionsState(permissions)", "Permission.FineLocation", "Permission.CoarseLocation", "Permission.BackgroundLocation", "Permission.Camera", "SideEffect", "onDispose", "frameworkResults.add", "permissions.toList()", "grantResults.toList()", "super.onRequestPermissionsResult"):
            self.assertIn(token, value)
        self.assertLess(value.index("frameworkResults.add"), value.index("super.onRequestPermissionsResult"))
        self.assertNotRegex(value, r"\.status\s*=")
        self.assertNotIn("AndroidPermissionRegistry.register", value)
        self.assertNotIn("refreshPermissionStatus()", value)

    def test_new_bridge_actual_sender_uid_signature_nonce_pid_generation_and_one_bind_are_strict(self):
        service = text(APP / "PermissionCompatibilityService.kt"); bridge = text(KT / "OwnedPermissionCompatibility.kt")
        for token in ("request.sendingUid", "names == listOf(REPORTER)", "PackageManager.SIGNATURE_MATCH", 'Regex("[a-f0-9]{32}")', "Process.myPid()", "BuildConfig.VERIFICATION_PROFILE"):
            self.assertIn(token, service)
        for token in ("IBinder.DeathRecipient", "linkToDeath", "assertSameIdentity", "activityGeneration", "selected.second.target", "assertIs<Int>", "thread.quitSafely()", "thread.join(5000)", "addSuppressed", "finally"):
            self.assertIn(token, bridge)
        self.assertEqual(1, bridge.count("context.bindService("))
        self.assertNotRegex(bridge, r"\b(?:restart|rebind|reconnect|revive)\s*\(")

    def test_new_native_ui_is_sdk_owned_refreshed_unique_bounded_and_restores_accessibility(self):
        value = text(KT / "PermissionCompatibilitySystemUi.kt")
        for token in ("Build.VERSION.SDK_INT == 23", "com.android.packageinstaller", "com.google.android.packageinstaller", "permission_location_accuracy_radio_coarse", "node.refresh()", "node.isVisibleToUser", "node.isEnabled", "matches.size <= 1", "check(acquired.size <= 256)", "waitForIdle", "SystemClock.elapsedRealtime()", "finally", "recycle()", "flags = originalFlags"):
            self.assertIn(token, value)
        self.assertNotRegex(value, r"\b(?:click|tap)\s*\(\s*\d+\s*,")

    def test_new_native_matrix_requires_fresh_shapes_foreground_first_native_arrays_and_real_settings(self):
        value = text(KT / "AndroidPermissionCompatibilityDeviceTest.kt")
        for token in ('listOf("fine", "coarse", "pair", "batch")', "seenUids.add", 'owner.request("request-background")', "RequiresForeground", "NotRequired", "foregroundArray().contains(BACKGROUND)", 'listOf(BACKGROUND)', "RequiresSettings", "owner.returnFromSettings", "assertResultMap", "PackageManager.PERMISSION_DENIED"):
            self.assertIn(token, value)
        for token in ("locationServicesEnabled", "isLocationEnabled", "originalEnabled", "ui.setLocationServices(originalEnabled)", "primary!!.addSuppressed(cleanup)", 'state(after, "Camera", retained = true)', 'owner.request("request-batch-retained")', "ui.assertPermissionDialog()"):
            self.assertIn(token, value)
        combined = value + text(APP / "PermissionCompatibilityActivity.kt") + text(KT / "OwnedPermissionCompatibility.kt") + text(KT / "PermissionCompatibilitySystemUi.kt")
        self.assertNotRegex(combined, r"\b(?:grantRuntimePermission|revokeRuntimePermission|adoptShellPermissionIdentity|execShellCommand|handleLifecycleEvent|dispatchResult)\s*\(")
        self.assertNotIn("appops", combined.lower())

    def test_new_exact_five_native_methods_match_plans_without_broad_or_accepted_filters(self):
        c = contract(); value = text(KT / "AndroidPermissionCompatibilityDeviceTest.kt")
        methods = re.findall(r"@Test\s+fun\s+(\w+)\s*\(", value)
        self.assertEqual(5, len(methods))
        self.assertEqual({row.method for row in c.ROWS}, set(methods))
        for method in methods: self.assertIn('requireMethod("' + method + '")', value)
        self.assertNotIn("AndroidPermissionDemoDeviceTest", value)
        self.assertNotIn("AndroidMediaSelectionDeviceTest", value)

    def test_new_one_time_expiry_remains_unregistered_unverified_without_importance_handoff(self):
        c = contract(); plan = c.unavailable_one_time_expiry_plan()
        for key in ("profile_registered", "native_dispatch_allowed", "grant_expiry_observed", "same_process_expiry_verified", "native_or_compile_success_inferred"):
            self.assertFalse(plan[key])
        self.assertIn("importance", plan["blocker"])
        self.assertIn("restart", plan["forbidden_substitutes"])
        with self.assertRaises(ValueError): c.proposed_plan("android-permission-one-time-expiry")
        ast.parse(text(ROOT / "scripts/ci/android_permission_compatibility_plan.py"))


    def test_new_pending_dialog_disposes_actual_compose_view_without_synthetic_lifecycle_or_status(self):
        value = text(APP / "PermissionCompatibilityActivity.kt")
        start = value.index('"dispose-content" -> {')
        end = value.index('"finish" ->', start)
        operation = value[start:end]
        self.assertIn("content.disposeComposition()", operation)
        self.assertLess(operation.index("visible = false"), operation.index("content.disposeComposition()"))
        self.assertNotIn("mounted = false", operation)
        self.assertNotIn("disposalCount++", operation)
        self.assertNotIn("handleLifecycleEvent", operation)
        self.assertNotRegex(operation, r"\.status\s*=")
        self.assertIn("onDispose { mounted = false; disposalCount++ }", value)
        native = text(KT / "AndroidPermissionCompatibilityDeviceTest.kt")
        beginning = native.index("@Test fun pendingNativeCameraDialogDisposalSuppressesRealLateResult")
        pending = native[beginning:native.index("private fun state(", beginning)]
        self.assertLess(pending.index("ui.assertPermissionDialog()"), pending.index('owner.request("dispose-content")'))
        self.assertLess(pending.index("owner.await { !it.getBoolean(\"mounted\")"), pending.index("ui.denyRuntime()"))


    def test_new_reporter_policy_rejects_alternate_runtime_caps_unknown_and_duplicate_application_nodes(self):
        c = contract()
        original = ET.fromstring((FIXTURE / "reporter/src/main/AndroidManifest.xml").read_bytes())
        for mutation in ("alternate-runtime", "cap", "request-child", "declaration", "duplicate-app", "process", "disabled", "control", "instrumentation", "feature", "source-sdk"):
            root = copy.deepcopy(original)
            if mutation == "alternate-runtime": ET.SubElement(root, "uses-permission-sdk-23", {ANDROID + "name": "android.permission.CAMERA"})
            elif mutation == "cap": root.find("uses-permission").set(ANDROID + "maxSdkVersion", "34")
            elif mutation == "request-child": ET.SubElement(root.find("uses-permission"), "unknown")
            elif mutation == "declaration": ET.SubElement(root, "permission", {ANDROID + "name": "unexpected.control", ANDROID + "protectionLevel": "normal"})
            elif mutation == "duplicate-app": root.append(copy.deepcopy(root.find("application")))
            elif mutation == "process": root.find("application").set(ANDROID + "process", ":other")
            elif mutation == "disabled": root.find("application").set(ANDROID + "enabled", "false")
            elif mutation == "control": root.find("application").set(ANDROID + "permission", "unexpected.control")
            elif mutation == "instrumentation": ET.SubElement(root, "instrumentation", {ANDROID + "name": "unexpected.Runner", ANDROID + "targetPackage": c.REPORTER})
            elif mutation == "feature": ET.SubElement(root, "uses-feature", {ANDROID + "name": "android.hardware.camera"})
            else: ET.SubElement(root, "uses-sdk", {ANDROID + "minSdkVersion": "23", ANDROID + "targetSdkVersion": "37"})
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): c.validate_reporter_manifest(ET.tostring(root), compiled=False)

    def test_new_reporter_inert_compiled_policy_requires_one_uncapped_exact_sdk_and_actual_debuggable_shape(self):
        c = contract()
        original = ET.fromstring((FIXTURE / "reporter/src/main/AndroidManifest.xml").read_bytes())
        original.set("package", c.REPORTER)
        original.find("application").set(ANDROID + "debuggable", "true")
        ET.SubElement(original, "uses-sdk", {ANDROID + "minSdkVersion": "23", ANDROID + "targetSdkVersion": "37"})
        self.assertFalse(c.validate_reporter_manifest(ET.tostring(original), compiled=True)["native_or_compile_success_inferred"])
        for mutation in ("duplicate-sdk", "missing-sdk", "wrong-min", "wrong-target", "max-sdk", "sdk-child", "missing-debug", "release-debug", "duplicate-app", "alternate-runtime", "cap"):
            root = copy.deepcopy(original)
            if mutation == "duplicate-sdk": root.append(copy.deepcopy(root.find("uses-sdk")))
            elif mutation == "missing-sdk": root.remove(root.find("uses-sdk"))
            elif mutation == "wrong-min": root.find("uses-sdk").set(ANDROID + "minSdkVersion", "24")
            elif mutation == "wrong-target": root.find("uses-sdk").set(ANDROID + "targetSdkVersion", "35")
            elif mutation == "max-sdk": root.find("uses-sdk").set(ANDROID + "maxSdkVersion", "35")
            elif mutation == "sdk-child": ET.SubElement(root.find("uses-sdk"), "unknown")
            elif mutation == "missing-debug": root.find("application").attrib.pop(ANDROID + "debuggable")
            elif mutation == "release-debug": root.find("application").set(ANDROID + "debuggable", "false")
            elif mutation == "duplicate-app": root.append(copy.deepcopy(root.find("application")))
            elif mutation == "alternate-runtime": ET.SubElement(root, "uses-permission-sdk-23", {ANDROID + "name": "android.permission.ACCESS_FINE_LOCATION"})
            else: root.find("uses-permission").set(ANDROID + "maxSdkVersion", "34")
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): c.validate_reporter_manifest(ET.tostring(root), compiled=True)
        with self.assertRaises(ValueError): c.validate_reporter_manifest(ET.tostring(original), compiled=1)

    def test_new_target_reporter_policy_keeps_test_apk_domain_separate_and_cannot_certify_native_success(self):
        c = contract()
        value = text(ROOT / "scripts/ci/android_permission_compatibility_plan.py")
        beginning = value.index("def validate_reporter_manifest(")
        domain = value[beginning:value.index("def unavailable_one_time_expiry_plan", beginning)]
        self.assertIn("test instrumentation has a separate domain", domain)
        self.assertIn("test APK is not this domain", domain)
        self.assertIn('"native_or_compile_success_inferred": False', domain)
        self.assertIn("uses-permission", domain)
        self.assertNotIn('"instrumentation"}', domain)


if __name__ == "__main__":
    unittest.main(verbosity=2)
