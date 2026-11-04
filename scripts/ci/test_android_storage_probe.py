"""Source/guard and injected-controller models only; no SDK/build/native evidence."""
from collections import Counter
from contextlib import ExitStack, contextmanager
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

import android_device_tests as device
import android_storage_probe as s
import android_storage_compatibility_plan as storage
import dependency_cache_inputs as cache
import library_tests as lt
import workflow_matrix as matrix


# Source-bound 540c1c1e baseline; additional disjoint profiles may coexist,
# but none of these original profile rows or full slots may change silently.
FROZEN_PROFILE_NAMES = (
    'core',
    'android-geo-ownership',
    'android-geo-provider',
    'android-geo-prerequisites',
    'android-share-grants',
    'android-io-provider-lifecycle',
    'android-io-default-decode',
    'android-camera-provider',
    'android-camera-provider-minimum',
    'android-camera-no-handler-minimum',
    'android-camera-restoration',
    'android-camera-restoration-dont-keep',
    'browser',
    'browser-picker',
    'browser-coil-io',
    'browser-coil-io-js',
    'browser-coil-io-wasm',
    'webview-browser',
    'webview-content-transitions',
    'webview-wasm',
    'share-browser',
    'ui-date-browser',
    'ui-date-js',
    'ui-date-platforms',
    'ui-date-wasm',
    'ui-date-android',
    'ui-dropdown-platforms',
    'ui-dropdown-android-recovery',
    'navigation-geo',
    'navigation-desktop',
    'webview-desktop',
    'webview-identity',
    'webview-identity-linux',
    'webview-identity-browser',
    'webview-identity-wasm',
    'webview-identity-android',
    'webview-identity-recovery',
    'webview-identity-remount-recovery',
    'webview-identity-ios-remount-recovery',
    'webview-lifetime',
    'webview-lifetime-android',
    'webview-lifetime-android-media',
    'webview-lifetime-linux',
    'webview-lifetime-macos-arm64',
    'webview-lifetime-macos-x64',
    'webview-lifetime-macos-media',
    'webview-lifetime-windows',
    'picker-batch',
    'picker-batch-recovery',
    'picker-batch-linux',
    'picker-batch-macos',
    'picker-batch-windows',
    'picker-saver-state',
    'picker-linux-portal',
    'picker-linux-portal-save',
    'desktop-data-safety',
    'android-resource-safety',
    'android-coil-resource',
    'android-permission-alias',
    'permissions-unsupported',
    'permissions-unsupported-windows',
    'permissions-ios',
    'permissions-ios-safety',
    'permissions-ios-empty-batch',
    'permissions-completion-android',
    'navigation-geo-matrix',
    'apple',
    'ios',
    'ios-ui',
    'ios-date-bounds',
    'ios-date-replacement',
    'ios-date-compact',
    'ios-dates-important',
    'ios-io',
    'ios-saver-write-failure',
    'ios-picker-batch',
    'ios-picker-recovery',
    'ios-picker-admission',
    'ios-switch-cancellation',
    'ios-switch-ownership',
    'ios-slider-numeric',
    'ios-ui-state',
    'ios-time-state-recovery',
    'ios-slider-lifecycle',
    'ios-slider-remaining',
    'ios-slider-structure',
    'ios-slider-tap',
    'ios-slider-pair-structure',
    'ios-vector-theme',
    'ios-vector-theme-recovery',
    'ios-vector-rendering-recovery',
    'ios-vector-rendering-iphone-recovery',
    'ios-vector-native-screen-pair',
    'ios-slider-recovery',
    'ios-image-memory',
    'ios-image-memory-darwin',
    'ios-image-profile-recovery',
    'ios-appinfo-capability',
    'ios-webview-lifecycle',
    'ios-webview-recovery',
    'windows',
    'windows-cache',
    'windows-share-loader',
    'windows-share-boundaries',
    'extended',
    'android-device',
    'android-webview',
    'android-webview-popups',
    'android-navigation-back',
    'android-io-oversize',
    'android-saver-identity',
    'android-saver-identity-missing',
    'consumer-core-io',
    'consumer-webview',
    'consumer-webview-remaining',
    'consumer-webview-linux-x64',
    'consumer-webview-linux-arm64',
    'consumer-webview-macos-arm64',
    'consumer-webview-macos-x64',
    'consumer-webview-windows-x64',
    'sample-platforms-linux',
    'sample-platforms-apple',
    'sample-builds-linux',
    'sample-builds-apple',
    'all',
    'tooling',
)
FROZEN_PROFILE_MATRIX_SHA256 = 'a8b7d9de60745a77b30041342c7310dd68869e3785ccb6efaeb9359322d3402d'
FROZEN_FULL_SLOTS_SHA256 = 'b2b9f0727ce6c041050910f4b024c7e76156c0a583e40c4f8ac2752d1de90755'

class StorageOperationalGuards(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="storage-source-model-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for relative in s.SOURCE_FILES:
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((lt.ROOT / relative).read_bytes())
        (self.root / "settings.gradle.kts").write_text('include(\n    ":calf-permissions:core",\n)\nproject(":calf-permissions:core").name = "calf-permissions-core"\n')
        self.source = s.source_contract(self.root)

    def row(self, profile="android-storage-api35-all-files"):
        return storage.row_for(profile)

    def status(self, row, *, operation="status", cleanup=False, write=False, manager=False):
        return {"schema": "nativecmpkit-storage-control-v1", "operation": operation,
            "case_nonce": "1" * 32, "request_nonce": "2" * 32, "status": "passed", "package": s.PACKAGE,
            "uid": 11000, "pid": 1234, "sdk": row.api, "target": row.target, "mode": row.flavor,
            "apk_sha256": "b" * 64, "certificate_sha256": "a" * 64, "splits_absent": True,
            "record_present": False, "activity_active": False, "persisted_read_count": 0,
            "foreign_persisted_count": 0, "native_read_grant": False, "write_granted": write,
            "manager": manager if row.api >= 30 else None, "manager_mode": (0 if manager else 3) if row.api >= 30 else None,
            "release_verified": cleanup, "record_cleared": cleanup}

    def receipt(self, profile="android-storage-api35-all-files"):
        row = self.row(profile)
        return {"package": s.PACKAGE, "source_fixture": s.FIXTURE, "profile": profile,
            "verification_api_level": row.api, "target_sdk": row.target, "flavor": row.flavor,
            "case_nonce": "1" * 32, "prepare_status": "passed", "recipient_installed": True,
            "manual_URI_grant": False, "automatic_runtime_permission_grant": False, "installed_uid": 11000,
            "source_apk_sha256": "b" * 64, "source_contract": copy.deepcopy(self.source),
            "installed_readback": {"apk_sha256": "b" * 64, "exact_one_APK_path_observed": True},
            "apk_policy": {"compiled_manifest_inspected": True, "signature_control_only": True,
                "shell_cleanup_requires_DUMP_and_UID2000": True, "fixed_helper_components_verified": True,
                "static_storage_permissions_verified": True, "certificate_sha256": "a" * 64,
                "private_key_certificate_sha256": "a" * 64, "manifest_sha256": "e" * 64, "apk_signer_revision": s.SIGNER_REVISION,
                "signature_verification_min_sdk_version": row.api,
                "signature_verification_max_sdk_version": row.api},
            "reporter_policy": {"package": s.REPORTER, "compiled_manifest_inspected": True,
                "native_storage_permissions_absent": True, "document_requires_android_grant": True,
                "certificate_sha256": "a" * 64, "private_key_certificate_sha256": "a" * 64,
                "manifest_sha256": "f" * 64, "apk_signer_revision": s.SIGNER_REVISION, "source_apk_sha256": "c" * 64,
                "signature_verification_min_sdk_version": row.api, "signature_verification_max_sdk_version": row.api},
            "initial_native_status": self.status(row)}

    def plan(self, profile="android-storage-api35-all-files"):
        return lt.plan(self.root, "android-device", only_modules=(s.MODULE,), focus=profile)

    def helper(self, profile="android-storage-api35-all-files"):
        output = self.root / "build/ci-verification" / profile
        (output / "android-user").mkdir(parents=True)
        instance = s.OwnedStorageProbe(self.root, output, self.root / "sdk", "emulator-5588", lambda: True,
            environment={"ANDROID_SERIAL": "emulator-5588", "ANDROID_USER_HOME": str(output / "android-user")}, profile=profile)
        instance.receipt.update(self.receipt(profile))
        instance.digest = instance.receipt["source_apk_sha256"]
        return instance

    def compiled_helper(self, profile):
        row = self.row(profile)
        manifest = s.xml((self.root / (s.FIXTURE + "/src/main/AndroidManifest.xml")).read_bytes())
        manifest.set("package", s.PACKAGE)
        sdk = ET.SubElement(manifest, "uses-sdk", {s.ANDROID + "minSdkVersion": "23", s.ANDROID + "targetSdkVersion": str(row.target)})
        flavor = s.xml((self.root / (s.FIXTURE + "/src/" + row.flavor + "/AndroidManifest.xml")).read_bytes())
        for node in flavor:
            if node.tag == "application":
                manifest.find("application").attrib.update(node.attrib)
            else:
                manifest.append(node)
        app = manifest.find("application"); app.set(s.ANDROID + "debuggable", "true")
        app.find("provider").set(s.ANDROID + "authorities", s.AUTHORITY)
        return ET.tostring(manifest)

    def compiled_reporter(self):
        manifest = s.xml((self.root / (s.MODULE + "/src/androidDeviceTest/AndroidManifest.xml")).read_bytes())
        manifest.set("package", s.REPORTER)
        ET.SubElement(manifest, "uses-sdk", {s.ANDROID + "minSdkVersion": "23", s.ANDROID + "targetSdkVersion": "37"})
        ET.SubElement(manifest, "instrumentation", {s.ANDROID + "name": "androidx.test.runner.AndroidJUnitRunner", s.ANDROID + "targetPackage": s.REPORTER})
        manifest.find("application").set(s.ANDROID + "debuggable", "true")
        manifest.find("application/provider").set(s.ANDROID + "authorities", s.REPORTER + ".storage-documents")
        return ET.tostring(manifest)

    def test_exact_eight_plans_bind_one_method_api_target_and_flavor(self):
        for row in storage.ROWS:
            with self.subTest(profile=row.profile):
                plan = self.plan(row.profile)
                self.assertTrue(lt.validate_test_focus(plan))
                self.assertFalse(plan["complete_suite_requested"])
                self.assertEqual(row.api, plan["android_storage_probe"]["verification_api_level"])
                self.assertEqual(row.target, plan["android_storage_probe"]["target_sdk"])
                self.assertEqual(row.flavor, plan["android_storage_probe"]["flavor"])
                self.assertEqual(storage.CLASS + "#" + row.method, plan["expected"][0]["test_filter"])
                self.assertEqual([{ "classname": storage.CLASS, "name": row.method}], plan["expected"][0]["required_testcases"])
                self.assertEqual(storage.MODULE, plan["expected"][0]["module"])

    def test_api_extension_cannot_widen_unrelated_or_wrong_storage_selections(self):
        for row in storage.ROWS:
            device.validate_api_selection(row.api, (s.MODULE,), row.profile)
            for api in {23, 28, 29, 30, 35} - {row.api}:
                with self.subTest(profile=row.profile, api=api), self.assertRaises(ValueError):
                    device.validate_api_selection(api, (s.MODULE,), row.profile)
            for modules in (None, ("calf-io",), (s.MODULE, "calf-io")):
                with self.assertRaises(ValueError):
                    device.validate_api_selection(row.api, modules, row.profile)
        for api in (28, 29, 30):
            with self.assertRaises(ValueError): device.validate_api_selection(api, ("calf-io",), lt.ANDROID_IO_PROVIDER_FOCUS)
        device.validate_api_selection(35, ("calf-io",), lt.ANDROID_IO_PROVIDER_FOCUS)
        device.validate_api_selection(23, ("calf-camera-picker",), lt.ANDROID_CAMERA_PROVIDER_FOCUS)

    def test_all_existing_profiles_and_eleven_full_slots_are_unchanged(self):
        self.assertTrue(set(FROZEN_PROFILE_NAMES) <= matrix.PROFILES.keys())
        observed = {profile: matrix.matrix(profile) for profile in FROZEN_PROFILE_NAMES}
        self.assertEqual(FROZEN_PROFILE_MATRIX_SHA256, hashlib.sha256(json.dumps(observed, separators=(",", ":"), sort_keys=True).encode()).hexdigest())
        self.assertEqual(FROZEN_FULL_SLOTS_SHA256, hashlib.sha256(json.dumps(matrix.SLOTS, separators=(",", ":"), sort_keys=True).encode()).hexdigest())
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        for row in storage.ROWS:
            selected = matrix.matrix(row.profile)["include"]
            self.assertEqual(1, len(selected)); self.assertEqual(str(row.api), selected[0]["emulator-api"])
            self.assertEqual(s.MODULE, selected[0]["test-modules"]); self.assertEqual(row.profile, selected[0]["test-focus"])

    def test_default_eight_modules_exclude_only_explicit_finite_storage_metadata(self):
        # Eight ordinary hosts remain inventory metadata, not executable default coverage.
        inventory = ('calf-io', 'calf-file-picker', 'calf-geo', 'calf-webview', 'calf-ui', 'calf-navigation', 'calf-share', 'calf-camera-picker')
        self.assertEqual(8, len(inventory))
        self.assertEqual((*inventory, "calf-permissions/core"), lt.MINIMUM_MODULES["android-device"])
        with self.assertRaises(ValueError) as refused:
            lt.plan(lt.ROOT, "android-device")
        self.assertIn(str(refused.exception), (
            'Unfiltered Android discovery requires a qualified remote IO fixture route; full aggregate is blocked',
            'Enabled API35-only callback requires exact finite Camera selection; unrestricted Camera/all discovery refuses before host work',
        ))
        # An unrelated explicit subset cannot admit the unfiltered Camera/IO domains.
        unrelated = ('calf-file-picker', 'calf-geo', 'calf-webview', 'calf-ui', 'calf-navigation', 'calf-share')
        plan = lt.plan(lt.ROOT, "android-device", minimum_modules=unrelated, only_modules=unrelated)
        self.assertEqual(list(unrelated), [item["module"] for item in plan["expected"]])
        self.assertEqual(list(unrelated), plan["explicit_module_subset"])
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(["calf-permissions/core"], plan["finite_only_device_modules_not_requested"])
        self.assertEqual(["calf-camera-picker", "calf-io", "calf-permissions/core"],
                         plan["test_bearing_modules_not_requested"])
        self.assertEqual(9, len(lt.MINIMUM_MODULES["android-device"]))
        self.assertEqual([s.MODULE], plan["finite_only_device_modules_not_requested"])
        self.assertIn(s.MODULE, plan["test_bearing_modules_not_requested"])
        self.assertNotIn("android_storage_probe", plan)
        self.assertFalse(lt.validate_test_focus(plan))
        forged = copy.deepcopy(plan); forged["complete_suite_requested"] = True
        with self.assertRaises(ValueError): lt.validate_test_focus(forged)

    def test_unfocused_or_wrong_suite_core_device_requests_are_refused(self):
        for modules in ((s.MODULE,), (s.MODULE, "calf-io")):
            with self.assertRaises(ValueError): lt.plan(self.root, "android-device", only_modules=modules)
        for row in storage.ROWS:
            self.assertFalse(lt.allowed_test_focus("android-host", (s.MODULE,), row.profile))
            self.assertFalse(lt.allowed_test_focus("android-device", ("calf-io",), row.profile))
        with self.assertRaises(ValueError): lt.gradle_command("android-device", {"suite": "android-device",
            "expected": [{"module": s.MODULE}], "complete_suite_requested": True}, android_serial="emulator-5588")

    def test_focused_plan_tampering_never_widens_the_class_or_module(self):
        original = self.plan()
        for key, value in (("test_filter", storage.CLASS), ("required_testcases", []), ("module", "calf-io"),
                           ("project", ":calf-io"), ("task", ":calf-io:connectedAndroidDeviceTest")):
            forged = copy.deepcopy(original); forged["expected"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): lt.validate_test_focus(forged)
        for key, value in (("verification_api_level", 30), ("target_sdk", 28), ("flavor", "modern"),
                           ("profile", "android-storage-api30-normal")):
            forged = copy.deepcopy(original); forged["android_storage_probe"][key] = value
            with self.assertRaises(ValueError): lt.validate_test_focus(forged)

    def test_real_read_only_controller_clis_admit_all_eight_without_outputs(self):
        output_existed = (lt.ROOT / "build/ci-plan").exists()
        for row in storage.ROWS:
            result = matrix.preflight_plans(row.profile, lt.ROOT)
            self.assertTrue(result["source_only"]); self.assertEqual(0, result["Gradle_builds_executed"])
            self.assertEqual(0, result["library_tests_executed"]); self.assertEqual(1, len(result["slots"]))
            self.assertEqual(0, result["slots"][0]["exit_code"])
        self.assertEqual(output_existed, (lt.ROOT / "build/ci-plan").exists())

    def test_source_snapshot_holds_every_helper_and_native_file_not_build_outputs(self):
        inputs = lt.snapshot_inputs(self.root)
        self.assertTrue(set(s.SOURCE_FILES) <= inputs.keys())
        new = self.root / (s.FIXTURE + "/src/main/kotlin/new.kt"); new.write_text("// synthetic source change")
        self.assertIn(new.relative_to(self.root).as_posix(), lt.snapshot_inputs(self.root))
        generated = self.root / (s.FIXTURE + "/build/outputs/apk/old.apk")
        generated.parent.mkdir(parents=True); generated.write_bytes(b"synthetic old output")
        self.assertNotIn(generated.relative_to(self.root).as_posix(), lt.snapshot_inputs(self.root))

    def test_dependency_key_binds_exact_declarations_controllers_and_all_flavor_manifests(self):
        inputs = cache.selected_inputs(self.root, "libraries")
        expected = {s.FIXTURE + "/" + name for name in ("build.gradle.kts", "settings.gradle.kts", "gradle.properties")}
        expected |= {relative for relative in s.HELPER_SOURCE_FILES if relative.endswith("AndroidManifest.xml")}
        expected |= {"scripts/ci/android_storage_probe.py", "scripts/ci/android_storage_compatibility_plan.py"}
        self.assertTrue(expected <= inputs.keys())
        for relative in expected:
            path = self.root / relative; before = cache.fingerprint("libraries", cache.selected_inputs(self.root, "libraries"))
            saved = path.read_bytes(); path.write_bytes(saved + b"\n// synthetic recipe mutation\n")
            self.assertNotEqual(before, cache.fingerprint("libraries", cache.selected_inputs(self.root, "libraries")))
            path.write_bytes(saved)

    def test_dependency_key_excludes_native_sources_apks_signing_and_xml(self):
        before = cache.selected_inputs(self.root, "libraries")
        source = self.root / (s.HELPER_KOTLIN + "StorageProbe.kt"); source.write_text(source.read_text() + "\n// model-only code change\n")
        for relative in (s.FIXTURE + "/build/outputs/apk/old.apk", s.FIXTURE + "/build/test-results/old.xml",
                         s.FIXTURE + "/build/android-user/debug.keystore"):
            path = self.root / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text("not a dependency input")
        self.assertEqual(before, cache.selected_inputs(self.root, "libraries"))
        for scope in ("core-io", "webview"):
            self.assertNotIn("scripts/ci/android_storage_probe.py", cache.selected_inputs(self.root, scope))

    def test_compiled_helper_manifest_enforces_every_static_mode_and_no_unknown_ingress(self):
        for row in storage.ROWS:
            payload = self.compiled_helper(row.profile)
            result = s.validate_manifest(payload, compiled=True, profile=row.profile)
            self.assertTrue(result["compiled_manifest_inspected"])
            for mutation in (lambda m: m.set(s.ANDROID + "sharedUserId", "android.uid.shell"),
                             lambda m: m.find("uses-sdk").set(s.ANDROID + "targetSdkVersion", "27"),
                             lambda m: m.find("application").set(s.ANDROID + "process", ":foreign"),
                             lambda m: m.find("application/provider").set(s.ANDROID + "permission", s.PERMISSION),
                             lambda m: ET.SubElement(m.find("application"), "service", {s.ANDROID + "name": ".Foreign", s.ANDROID + "exported": "true"})):
                manifest = s.xml(payload); mutation(manifest)
                with self.assertRaises(ValueError): s.validate_manifest(ET.tostring(manifest), compiled=True, profile=row.profile)

    def test_reporter_manifest_cannot_bypass_other_uid_storage_or_document_grants(self):
        payload = self.compiled_reporter(); self.assertTrue(s.validate_reporter_manifest(payload)["document_requires_android_grant"])
        for mutation in (lambda m: ET.SubElement(m, "uses-permission", {s.ANDROID + "name": s.WRITE}),
                         lambda m: m.find("application/provider").set(s.ANDROID + "permission", s.PERMISSION),
                         lambda m: m.find("instrumentation").set(s.ANDROID + "targetPackage", s.PACKAGE),
                         lambda m: m.find("uses-sdk").set(s.ANDROID + "minSdkVersion", "28")):
            manifest = s.xml(payload); mutation(manifest)
            with self.assertRaises(ValueError): s.validate_reporter_manifest(ET.tostring(manifest))

    def test_signer_inspection_is_exact_runtime_api_to_api_not_relaxed_io_policy(self):
        certificate = b"synthetic DER certificate, never a real signing input"
        digest = hashlib.sha256(certificate).hexdigest()
        signer = ("Verifies\nVerified using v2 scheme (APK Signature Scheme v2): true\nNumber of signers: 1\nSigner #1 certificate SHA-256 digest: " + digest + "\n").encode()
        for row in storage.ROWS:
            helper = self.helper(row.profile)
            key = Path(helper.environment["ANDROID_USER_HOME"]) / "debug.keystore"; key.write_bytes(b"synthetic bounded private-key placeholder")
            apk = self.root / (row.profile + ".apk"); apk.write_bytes(b"synthetic APK placeholder")
            with patch.object(helper, "inspectors", return_value=(self.root / "apkanalyzer", self.root / "apksigner")), patch.object(helper, "host", side_effect=[
                    subprocess.CompletedProcess([], 0, self.compiled_helper(row.profile), b""),
                    subprocess.CompletedProcess([], 0, signer, b""), subprocess.CompletedProcess([], 0, certificate, b"")]) as host:
                result = helper.inspect_apk(apk)
            args = host.call_args_list[1].args[0]
            self.assertEqual(str(row.api), args[args.index("--min-sdk-version") + 1])
            self.assertEqual(str(row.api), args[args.index("--max-sdk-version") + 1])
            self.assertEqual(row.api, result["signature_verification_min_sdk_version"])
            self.assertEqual(row.api, result["signature_verification_max_sdk_version"])

    def test_signer_errors_warnings_or_duplicate_signers_never_become_passes(self):
        good = b"Verified using v2 scheme (APK Signature Scheme v2): true\nNumber of signers: 1\nSigner #1 certificate SHA-256 digest: " + b"a" * 64 + b"\n"
        self.assertEqual("a" * 64, s.signer_certificate(subprocess.CompletedProcess([], 0, good, b"")))
        for payload, stderr, code in ((good + b"WARNING: unknown\n", b"", 0), (good + b"Unknown protocol row\n", b"", 0), (good, b"unknown", 0), (good, b"", 1),
                (good + b"Signer #2 certificate SHA-256 digest: " + b"a" * 64 + b"\n", b"", 0),
                (good.replace(b"true", b"false"), b"", 0), (good + good, b"", 0)):
            with self.assertRaises(ValueError): s.signer_certificate(subprocess.CompletedProcess([], code, payload, stderr))

    def test_metadata_uses_one_exact_selected_variant_and_refuses_fallbacks(self):
        for reporter in (False, True):
            row = self.row(); base = self.root / (s.MODULE + "/build/outputs/apk/androidTest" if reporter else s.FIXTURE + "/build/outputs/apk/allFiles/debug")
            base.mkdir(parents=True); apk = base / "owned.apk"; apk.write_bytes(b"synthetic APK, not executable")
            metadata = {"artifactType": {"type": "APK"}, "applicationId": s.REPORTER if reporter else s.PACKAGE,
                "variantName": "androidDeviceTest" if reporter else "allFilesDebug", "elements": [{"type": "SINGLE", "filters": [], "outputFile": "owned.apk"}]}
            path = base / "output-metadata.json"; path.write_text(json.dumps(metadata))
            self.assertEqual(apk, s.metadata_apk(self.root, row.profile, reporter=reporter))
            for key, value in (("applicationId", "foreign"), ("variantName", "debug"), ("elements", [])):
                bad = copy.deepcopy(metadata); bad[key] = value; path.write_text(json.dumps(bad))
                with self.assertRaises(ValueError): s.metadata_apk(self.root, row.profile, reporter=reporter)
            bad = copy.deepcopy(metadata); bad["elements"][0]["outputFile"] = "../foreign.apk"; path.write_text(json.dumps(bad))
            with self.assertRaises(ValueError): s.metadata_apk(self.root, row.profile, reporter=reporter)
            path.unlink()
            with self.assertRaises(ValueError): s.metadata_apk(self.root, row.profile, reporter=reporter)

    def test_prepared_receipt_requires_hashes_private_signer_range_uid_and_source_freeze(self):
        original = self.receipt(); s.validate_prepared_receipt(original, self.source)
        for key, value in (("verification_api_level", True), ("target_sdk", 28), ("installed_uid", 2000),
                           ("manual_URI_grant", True), ("automatic_runtime_permission_grant", True), ("case_nonce", "foreign")):
            forged = copy.deepcopy(original); forged[key] = value
            with self.assertRaises(ValueError): s.validate_prepared_receipt(forged, self.source)
        for key, value in (("certificate_sha256", "d" * 64), ("signature_verification_min_sdk_version", 23),
                           ("signature_verification_max_sdk_version", True), ("compiled_manifest_inspected", False)):
            forged = copy.deepcopy(original); forged["apk_policy"][key] = value
            with self.assertRaises(ValueError): s.validate_prepared_receipt(forged, self.source)
        forged = copy.deepcopy(original); forged["source_contract"]["source_inputs"].pop(next(iter(s.SOURCE_FILES)))
        with self.assertRaises(ValueError): s.validate_prepared_receipt(forged, self.source)
        forged = copy.deepcopy(original); forged.pop("reporter_policy")
        with self.assertRaises(ValueError): s.validate_prepared_receipt(forged, self.source)
        s.validate_prepared_receipt(forged, self.source, require_reporter=False)

    def test_native_hooks_exist_only_after_exact_preparation_not_for_assembly(self):
        plan = self.plan(); receipt = self.receipt()
        with self.assertRaises(ValueError): lt.gradle_command("android-device", plan, android_serial="emulator-5588")
        assemble = lt.gradle_command("android-device", plan, android_serial="emulator-5588", for_assembly=True)
        self.assertEqual(1, assemble.count(lt.ANDROID_STORAGE_PROJECT + ":assembleAndroidDeviceTest"))
        self.assertFalse(any("nativecmpkitStorage" in arg or "nativecmpkitOwnedStorageProbe" in arg for arg in assemble))
        command = lt.gradle_command("android-device", plan, android_serial="emulator-5588", android_storage_probe_receipt=receipt)
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.nativecmpkitOwnedStorageProbe=true", command)
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.nativecmpkitStorageReporterApkSha256=" + "c" * 64, command)
        unrelated = lt.plan(lt.ROOT, "android-device", only_modules=("calf-io",), focus=lt.ANDROID_IO_OVERSIZE_FOCUS)
        with self.assertRaises(ValueError): lt.gradle_command("android-device", unrelated, android_serial="emulator-5588", android_storage_probe_receipt=receipt)

    def test_atomic_native_status_refuses_replay_foreign_grants_and_missing_release(self):
        receipt = self.receipt(); status = self.status(self.row(), operation="cleanup", cleanup=True)
        s.validate_native_status(status, receipt, operation="cleanup", request_nonce="2" * 32)
        with self.assertRaises(ValueError): s.validate_native_status(status, receipt, operation="cleanup", request_nonce="3" * 32)
        for key, value in (("uid", 2000), ("case_nonce", "foreign"), ("status", "failed"), ("foreign_persisted_count", 1),
                           ("release_verified", False), ("record_cleared", False), ("activity_active", True),
                           ("native_read_grant", True), ("persisted_read_count", True), ("apk_sha256", "d" * 64)):
            forged = copy.deepcopy(status); forged[key] = value
            with self.assertRaises(ValueError): s.validate_native_status(forged, receipt, operation="cleanup")

    def test_human_content_call_output_never_substitutes_for_fresh_atomic_json(self):
        helper = self.helper(); status = self.status(self.row())
        def control(*arguments, **options):
            if arguments[:3] == ("shell", "content", "call"):
                status["request_nonce"] = arguments[arguments.index("--extra") + 1].removeprefix("s:request_nonce:")
                return subprocess.CompletedProcess([], 0, b"Bundle[{published=true}]", b"")
            self.assertEqual(("shell", "run-as", s.PACKAGE, "cat", "files/storage-control-" + "1" * 32 + ".json"), arguments)
            return subprocess.CompletedProcess([], 0, json.dumps(status).encode(), b"")
        with patch.object(helper, "control", side_effect=control):
            self.assertEqual("passed", helper.native_status("status")["status"])
        with patch.object(helper, "control", side_effect=[subprocess.CompletedProcess([], 0, b"Bundle[{published=true}]", b""),
                subprocess.CompletedProcess([], 0, json.dumps(status).encode(), b"")]), self.assertRaises(ValueError):
            helper.native_status("status")

    def test_host_cleanup_orders_saf_activity_proof_then_restore_then_stop_and_uninstall(self):
        for profile in ("android-storage-api28", "android-storage-api35-all-files"):
            helper = self.helper(profile); helper.install_attempted = True; events = []
            row = helper.row
            def native(operation):
                events.append(operation)
                return self.status(row, operation=operation, cleanup=operation == "cleanup", write=operation == "cleanup" and row.declares_write,
                                   manager=operation == "cleanup" and row.declares_all_files)
            def control(*arguments, **options):
                events.append(arguments)
                return subprocess.CompletedProcess([], 0, b"Success\n" if arguments[0] == "uninstall" else b"", b"")
            with patch.object(helper, "readback", side_effect=[helper.receipt["installed_readback"], None]), patch.object(helper, "installed_uid", return_value=11000), \
                    patch.object(helper, "native_status", side_effect=native), patch.object(helper, "control", side_effect=control):
                result = helper.close()
            self.assertEqual("passed", result["cleanup_status"]); self.assertTrue(result["owned_recipient_removed"])
            restore = next(index for index, event in enumerate(events) if isinstance(event, tuple) and event[:2] in {("shell", "pm"), ("shell", "cmd")})
            stop = events.index(("shell", "am", "force-stop", s.PACKAGE))
            self.assertLess(events.index("cleanup"), restore); self.assertLess(restore, events.index("status")); self.assertLess(events.index("status"), stop)
            self.assertLess(stop, events.index(("uninstall", s.PACKAGE)))

    def test_failed_ordered_cleanup_never_blindly_force_stops_or_uninstalls(self):
        helper = self.helper(); helper.install_attempted = True
        with patch.object(helper, "readback", return_value=helper.receipt["installed_readback"]), patch.object(helper, "installed_uid", return_value=11000), \
                patch.object(helper, "native_status", side_effect=ValueError("synthetic native cleanup refusal")), patch.object(helper, "control") as control:
            with self.assertRaises(ValueError): helper.close()
        self.assertEqual("failed", helper.receipt["cleanup_status"]); self.assertFalse(helper.receipt["owned_recipient_removed"])
        self.assertEqual("passed", helper.receipt["prepare_status"]); control.assert_not_called()

    def test_changed_installed_uid_refuses_before_any_mutating_native_cleanup(self):
        helper = self.helper(); helper.install_attempted = True
        with patch.object(helper, "readback", return_value=helper.receipt["installed_readback"]), patch.object(helper, "installed_uid", return_value=11001), \
                patch.object(helper, "native_status") as native, patch.object(helper, "control") as control:
            with self.assertRaises(ValueError): helper.close()
        native.assert_not_called(); control.assert_not_called()
        self.assertEqual("failed", helper.receipt["cleanup_status"]); self.assertFalse(helper.receipt["owned_recipient_removed"])

    def test_failed_preparation_is_preserved_even_when_no_owned_app_needs_cleanup(self):
        helper = self.helper(); helper.receipt.update(prepare_status="failed", prepare_error="ValueError", recipient_installed=False)
        result = helper.close()
        self.assertEqual("failed", result["prepare_status"]); self.assertEqual("ValueError", result["prepare_error"])
        self.assertEqual("passed", result["cleanup_status"]); self.assertTrue(result["owned_recipient_removed"])

    def test_source_policy_refuses_extra_flavors_or_disabled_methods(self):
        extra = self.root / (s.FIXTURE + "/src/foreign/AndroidManifest.xml"); extra.parent.mkdir(parents=True); extra.write_text("<manifest/>")
        with self.assertRaises(ValueError): s.source_contract(self.root)
        extra.unlink()
        test = self.root / (s.KOTLIN + "AndroidStorageCompatibilityTest.kt"); test.write_text(test.read_text().replace("@Test fun", "@Ignore @Test fun", 1))
        with self.assertRaises(ValueError): s.source_contract(self.root)

    def test_native_source_gates_write_revocation_on_verified_saf_removal(self):
        source = (self.root / (s.KOTLIN + "AndroidStorageCompatibilityTest.kt")).read_text()
        section = source.split("private fun nativeWriteGrant", 1)[1].split("private fun cleanup(", 1)[0]
        self.assertIn("var safCleanupVerified = false", section)
        self.assertLess(section.index("safCleanupVerified = true"), section.index("assertTrue(safCleanupVerified"))
        self.assertLess(section.index("assertTrue(safCleanupVerified"), section.index("revokeRuntimePermission"))
        control = (self.root / (s.HELPER_KOTLIN + "StorageProbeControlProvider.kt")).read_text()
        self.assertLess(control.index("Binder.getCallingUid() == 2000"), control.index("Binder.clearCallingIdentity()"))
        self.assertIn("enforceCallingPermission", control); self.assertIn("AtomicFile", control); self.assertIn("request_nonce", control)
        self.assertNotIn("grantUriPermission(", control)
        self.assertLess(control.index("checkUriPermission"), control.index("StorageControlRecord.clear(context, nonce)"))

    def test_helper_apk_inspection_precedes_fresh_install_and_admits_only_known_success_shapes(self):
        helper = self.helper(); events = []
        apk = self.root / "synthetic-prepare.apk"; apk.write_bytes(b"synthetic APK bytes, not an actual package")
        digest = lt.sha256(apk)
        def inspect(apk):
            events.append("inspect")
            return copy.deepcopy(helper.receipt["apk_policy"])
        def control(*arguments, **kwargs):
            events.append("install")
            self.assertEqual(("install", "-t", str(apk)), arguments)
            return subprocess.CompletedProcess([], 0, b"Performing Streamed Install\nSuccess\n", b"")
        def native(operation):
            events.append(operation)
            value = self.status(helper.row); value["apk_sha256"] = digest
            return value
        with patch.object(helper, "inspectors"), patch.object(lt, "execute", side_effect=lambda *a, **k: events.append("helper-assembly") or {"exit_code": 0}), \
                patch.object(s, "metadata_apk", return_value=apk), patch.object(helper, "inspect_apk", side_effect=inspect), \
                patch.object(helper, "readback", side_effect=[None, None, {"apk_sha256": digest, "exact_one_APK_path_observed": True}]), \
                patch.object(helper, "installed_uid", return_value=11000), patch.object(helper, "control", side_effect=control), \
                patch.object(helper, "native_status", side_effect=native):
            result = helper.prepare()
        self.assertEqual(["helper-assembly", "inspect", "install", "status"], events)
        self.assertEqual("passed", result["prepare_status"]); self.assertTrue(helper.install_attempted)
        self.assertFalse(result["automatic_runtime_permission_grant"]); self.assertFalse(result["manual_URI_grant"])

    def test_helper_inspection_refusal_cannot_install_or_promote_partial_preparation(self):
        helper = self.helper(); apk = self.root / "synthetic-refused.apk"; apk.write_bytes(b"synthetic APK bytes")
        with patch.object(helper, "inspectors"), patch.object(helper, "readback", return_value=None), \
                patch.object(lt, "execute", return_value={"exit_code": 0}), patch.object(s, "metadata_apk", return_value=apk), \
                patch.object(helper, "inspect_apk", side_effect=ValueError("synthetic manifest/signer refusal")), patch.object(helper, "control") as control:
            with self.assertRaises(ValueError): helper.prepare()
        control.assert_not_called(); self.assertFalse(helper.install_attempted)
        self.assertEqual("failed", helper.receipt["prepare_status"])
        self.assertEqual(lt.sha256(apk), helper.receipt["source_apk_sha256"])
        self.assertTrue((helper.output / "receipt.json").is_file())

    @contextmanager
    def controlled_controller(self, profile="android-storage-api35-all-files", *, prepare_failure=False,
                              invalid_helper=False, reporter_failure=False, cleanup_failure=False, transport=True):
        order = []; owned = Mock(); row = self.row(profile)
        owned.receipt = self.receipt(profile); reporter = owned.receipt.pop("reporter_policy")
        def prepare():
            order.append("helper-prepare")
            if prepare_failure:
                owned.receipt.update(prepare_status="failed", prepare_error="ValueError")
                raise ValueError("synthetic helper prepare refusal")
            if invalid_helper: owned.receipt["apk_policy"]["certificate_sha256"] = "d" * 64
            return dict(owned.receipt)
        def prepare_reporter():
            order.append("reporter-inspect")
            if reporter_failure:
                owned.receipt["reporter_prepare_error"] = "ValueError"
                raise ValueError("synthetic reporter inspection refusal")
            owned.receipt["reporter_policy"] = copy.deepcopy(reporter)
            return dict(owned.receipt)
        def close():
            order.append("helper-close")
            if cleanup_failure: raise ValueError("synthetic ordered cleanup refusal")
            owned.receipt.update(cleanup_status="passed", owned_recipient_removed=True)
            return dict(owned.receipt)
        owned.prepare.side_effect = prepare; owned.prepare_reporter.side_effect = prepare_reporter; owned.close.side_effect = close
        process = Mock(pid=1234); process.poll.return_value = None
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, {"ANDROID_HOME": str(self.root / "synthetic-sdk")}))
            stack.enter_context(patch.object(device, "require_host"))
            stack.enter_context(patch.object(device, "sdk_assets", return_value={"system_image": "system-images;android-" + str(row.api) + ";google_apis;x86_64"}))
            stack.enter_context(patch.object(device, "ensure_ports_unused"))
            stack.enter_context(patch.object(device, "adb", return_value="List of devices attached"))
            stack.enter_context(patch.object(device.runtime, "capture", return_value={"source_revision": "f" * 40, "source_tree_dirty": False}))
            stack.enter_context(patch.object(lt, "git_revision", return_value="f" * 40))
            execute = stack.enter_context(patch.object(lt, "execute", side_effect=lambda root, command, log, *a, **k: order.append(log.stem) or {"exit_code": 0}))
            stack.enter_context(patch.object(device.subprocess, "Popen", return_value=process))
            stack.enter_context(patch.object(device, "wait_for_owned_boot", side_effect=lambda *a, **k: order.append("boot") or {"api_level": str(row.api), "selinux": "Enforcing"}))
            stack.enter_context(patch.object(s, "OwnedStorageProbe", return_value=owned))
            tests = stack.enter_context(patch.object(lt, "run", side_effect=lambda *a, **k: order.append("tests") or {"passed": True, "totals": {"executed": 1, "passed": 1}}))
            stack.enter_context(patch.object(device, "stop_owned_emulator", side_effect=lambda *a: order.append("shutdown") or {"clean_shutdown": True}))
            stack.enter_context(patch.object(device, "wait_for_owned_transport_removal", side_effect=lambda *a: order.append("transport-removal") or transport))
            yield order, owned, execute, tests

    def invoke_controller(self, profile="android-storage-api35-all-files"):
        relative = "build/ci-verification/controller-" + profile
        result = device.run(self.root, relative, only_modules=(s.MODULE,), focus=profile, api_level=self.row(profile).api)
        self.assertEqual(result, json.loads((self.root / relative / "controller.json").read_text()))
        self.assertFalse((self.root / "build/ci-verification/.android-device-controller.lock").exists())
        self.assertFalse(result["packages_published"]); self.assertFalse(result["release_readiness_certified"])
        return result

    def test_injected_controller_preserves_all_eight_identity_compile_dispatch_cleanup_orderings(self):
        for row in storage.ROWS:
            with self.controlled_controller(row.profile) as (order, owned, execute, tests):
                result = self.invoke_controller(row.profile)
            self.assertTrue(result["passed"])
            self.assertEqual(["owned-avd-create", "boot", "helper-prepare", "apk-assembly", "reporter-inspect", "tests", "helper-close", "shutdown", "transport-removal"], order)
            self.assertTrue(result["reporter_compile_deferred_until_storage_identity"])
            self.assertFalse(result["complete_suite_requested"])
            self.assertEqual(row.profile, tests.call_args.kwargs["focus"])
            self.assertEqual(s.MODULE, tests.call_args.kwargs["only_modules"][0])
            self.assertIn("reporter_policy", tests.call_args.kwargs["android_storage_probe_receipt"])
            assemble = execute.call_args_list[-1].args[1]
            self.assertIn(lt.ANDROID_STORAGE_PROJECT + ":assembleAndroidDeviceTest", assemble)
            self.assertNotIn(lt.ANDROID_STORAGE_PROJECT + ":connectedAndroidDeviceTest", assemble)
            self.assertFalse(any("nativecmpkitOwnedStorageProbe=" in arg for arg in assemble))

    def test_injected_failed_helper_identity_prevents_reporter_compile_and_native_dispatch(self):
        for profile, options in (("android-storage-api28", {"prepare_failure": True}), ("android-storage-api35-all-files", {"invalid_helper": True})):
            with self.controlled_controller(profile, **options) as (order, owned, execute, tests):
                result = self.invoke_controller(profile)
            self.assertFalse(result["passed"]); self.assertNotIn("apk-assembly", order); tests.assert_not_called()
            self.assertIn("helper-close", order); self.assertIn("shutdown", order)
            self.assertIn("source_apk_sha256", result["storage_probe"])

    def test_injected_reporter_refusal_preserves_helper_facts_without_native_execution(self):
        profile = "android-storage-api35-normal"
        with self.controlled_controller(profile, reporter_failure=True) as (order, owned, execute, tests):
            result = self.invoke_controller(profile)
        self.assertFalse(result["passed"]); tests.assert_not_called()
        self.assertIn("reporter-inspect", order); self.assertIn("helper-close", order); self.assertIn("shutdown", order)
        self.assertEqual("passed", result["storage_probe"]["prepare_status"])
        self.assertEqual("ValueError", result["storage_probe"]["reporter_prepare_error"])

    def test_injected_cleanup_or_transport_refusal_cannot_promote_modeled_native_passes(self):
        for profile, options in (("android-storage-api30-all-files", {"cleanup_failure": True}), ("android-storage-api30-normal", {"transport": False})):
            with self.controlled_controller(profile, **options) as (order, owned, execute, tests):
                result = self.invoke_controller(profile)
            self.assertFalse(result["passed"]); self.assertTrue(result["test_suite_passed"])
            self.assertEqual("passed", result["storage_probe"]["prepare_status"])
            self.assertIn("shutdown", order); self.assertIn("transport-removal", order)

    def test_fresh_xml_must_be_exactly_one_selected_non_skipped_native_case(self):
        plan = self.plan(); selected = plan["expected"][0]
        folder = self.root / selected["report_directory"]; folder.mkdir(parents=True)
        report = folder / "TEST-storage.xml"; row = self.row()
        def collect(payload):
            report.write_bytes(payload)
            now = time.time_ns()
            return lt.collect_reports(self.root, plan, now - 1_000_000_000, now + 1_000_000_000, Counter({selected["task"]: 1}))
        good = ('<testsuite tests="1"><testcase classname="' + storage.CLASS + '" name="' + row.method + '"/></testsuite>').encode()
        self.assertFalse(collect(good)["errors"])
        for payload in (good.replace(row.method.encode(), b"foreign"), good.replace(b"/></testsuite>", b"><skipped/></testcase></testsuite>"),
                        good.replace(b"/></testsuite>", b"><failure/></testcase></testsuite>"), b"<testsuite tests=\"0\"/>"):
            self.assertTrue(collect(payload)["errors"])
        report.write_bytes(good)
        other = folder / "TEST-unrelated.xml"; other.write_bytes(b'<testsuite tests="0"/>')
        now = time.time_ns(); self.assertTrue(lt.collect_reports(self.root, plan, now - 1_000_000_000, now + 1_000_000_000, Counter({selected["task"]: 1}))["errors"])


if __name__ == "__main__":
    unittest.main()
