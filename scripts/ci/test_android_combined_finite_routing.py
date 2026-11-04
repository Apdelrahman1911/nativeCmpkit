"""New combined source/routing models only: no SDK, build, installation or native run."""
from copy import deepcopy
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import android_device_tests as device
import android_permission_demo as demo
import android_storage_compatibility_plan as storage
import android_storage_probe as probe
import library_tests as lt
import workflow_matrix as workflow

ROOT = Path(__file__).resolve().parents[2]
CORE = "calf-permissions/core"
BIND_DEMO = demo.PACKAGE + ".BIND_DEMO"
BASE_DEVICE_MODULES = ("calf-io", "calf-file-picker", "calf-geo", "calf-webview",
    "calf-ui", "calf-navigation", "calf-share", "calf-camera-picker")
PERMISSION_PROFILES = (("android-permission-demo", 35, lt.ANDROID_PERMISSION_DEMO_FOCUS, 3),
    ("android-media-selection-api33", 33, lt.ANDROID_MEDIA_SELECTION_FOCUS, 1),
    ("android-media-selection-api34", 34, lt.ANDROID_MEDIA_SELECTION_FOCUS, 1))


class AndroidCombinedFiniteRoutingGuards(unittest.TestCase):
    def test_permission_media_routes_require_only_the_permission_demo_helper(self):
        for profile, api, focus, count in PERMISSION_PROFILES:
            row, = workflow.matrix(profile)["include"]
            self.assertEqual((str(api), CORE, focus),
                (row["emulator-api"], row["test-modules"], row["test-focus"]))
            device.validate_api_selection(api, (CORE,), focus)
            plan = lt.plan(ROOT, "android-device", only_modules=(CORE,), focus=focus)
            self.assertTrue(lt.validate_test_focus(plan))
            self.assertTrue(lt.android_permission_demo_required(plan))
            self.assertFalse(lt.android_storage_probe_required(plan))
            self.assertNotIn("android_storage_probe", plan)
            selected, = plan["expected"]
            self.assertEqual(count, len(selected["required_testcases"]))
            self.assertEqual(lt.ANDROID_PERMISSION_DEVICE_SPECS[focus]["classname"], selected["test_filter"])
            self.assertFalse(plan["complete_suite_requested"])

    def test_storage_routes_require_only_the_selected_storage_helper(self):
        for row in storage.ROWS:
            stub = {"suite": "android-device", "explicit_test_focus": row.profile,
                "expected": [{"module": CORE}]}
            self.assertFalse(lt.android_permission_demo_required(stub))
            self.assertTrue(lt.android_storage_probe_required(stub))
            plan = lt.plan(ROOT, "android-device", only_modules=(CORE,), focus=row.profile)
            self.assertTrue(lt.validate_test_focus(plan))
            self.assertNotIn("android_permission_demo", plan)
            self.assertFalse(plan["complete_suite_requested"])
            selected, = plan["expected"]
            self.assertEqual(storage.CLASS + "#" + row.method, selected["test_filter"])
            self.assertEqual([{"classname": storage.CLASS, "name": row.method}], selected["required_testcases"])
            self.assertEqual((row.profile, row.api, row.target, row.flavor), tuple(
                plan["android_storage_probe"][key] for key in ("profile", "verification_api_level", "target_sdk", "flavor")))

    def test_source_reporter_has_only_the_two_exact_signature_controls(self):
        manifest_path = CORE + "/src/androidDeviceTest/AndroidManifest.xml"
        manifest = ET.parse(ROOT / manifest_path).getroot()
        self.assertEqual([BIND_DEMO, probe.PERMISSION],
            [node.get(probe.ANDROID + "name") for node in manifest.findall("uses-permission")])
        self.assertTrue(probe.source_contract(ROOT)["source_policy_verified"])
        self.assertTrue(demo.source_contract(ROOT)["source_policy_verified"])
        with tempfile.TemporaryDirectory(prefix="combined-source-model-") as folder:
            root = Path(folder)
            for relative in probe.SOURCE_FILES:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / relative).read_bytes())
            for permission in (probe.WRITE, probe.ALL_FILES, "android.permission.CALL_PHONE",
                    "android.permission.RECORD_AUDIO", "foreign.signature.CONTROL", BIND_DEMO):
                changed = deepcopy(manifest)
                ET.SubElement(changed, "uses-permission", {probe.ANDROID + "name": permission})
                (root / manifest_path).write_bytes(ET.tostring(changed))
                with self.subTest(permission=permission), self.assertRaises(ValueError):
                    probe.source_contract(root)
            changed = deepcopy(manifest)
            changed.remove(next(node for node in changed.findall("uses-permission")
                if node.get(probe.ANDROID + "name") == probe.PERMISSION))
            (root / manifest_path).write_bytes(ET.tostring(changed))
            with self.assertRaises(ValueError):
                probe.source_contract(root)

    def test_compiled_reporter_admits_known_bind_demo_but_no_runtime_or_foreign_control(self):
        manifest = ET.parse(ROOT / CORE / "src/androidDeviceTest/AndroidManifest.xml").getroot()
        manifest.set("package", probe.REPORTER)
        ET.SubElement(manifest, "uses-sdk", {probe.ANDROID + "minSdkVersion": "23",
            probe.ANDROID + "targetSdkVersion": "37"})
        ET.SubElement(manifest, "instrumentation", {probe.ANDROID + "name": "androidx.test.runner.AndroidJUnitRunner",
            probe.ANDROID + "targetPackage": probe.REPORTER})
        manifest.find("application").set(probe.ANDROID + "debuggable", "true")
        manifest.find("application/provider").set(probe.ANDROID + "authorities", probe.REPORTER + ".storage-documents")
        policy = probe.validate_reporter_manifest(ET.tostring(manifest))
        self.assertTrue(policy["native_storage_permissions_absent"])
        self.assertTrue(policy["document_requires_android_grant"])
        self.assertFalse(policy["native_result_inferred"])
        for permission in (probe.WRITE, probe.ALL_FILES, "android.permission.CALL_PHONE",
                "android.permission.RECORD_AUDIO", "foreign.signature.CONTROL", BIND_DEMO):
            changed = deepcopy(manifest)
            ET.SubElement(changed, "uses-permission", {probe.ANDROID + "name": permission})
            with self.subTest(permission=permission), self.assertRaises(ValueError):
                probe.validate_reporter_manifest(ET.tostring(changed))

    def test_core_device_test_dependencies_are_declared_once_not_added_to_production(self):
        source = (ROOT / CORE / "build.gradle.kts").read_text()
        blocks = re.findall(r'sourceSets\.matching \{ it\.name == "androidDeviceTest" \}\.configureEach \{\s*'
            r'dependencies \{([^}]+)\}\s*\}', source)
        self.assertEqual(1, len(blocks))
        self.assertEqual(["junit", "androidx.test.runner", "androidx.test.core", "androidx.test.junit"],
            re.findall(r"implementation\(libs\.([^\)]+)\)", blocks[0]))

    def test_default_keeps_nine_inventory_entries_eight_executions_and_the_core_deletion_guard(self):
        self.assertEqual((*BASE_DEVICE_MODULES, CORE), lt.MINIMUM_MODULES["android-device"])
        # Eight ordinary hosts remain inventory metadata, not executable default coverage.
        inventory = ('calf-io', 'calf-file-picker', 'calf-geo', 'calf-webview', 'calf-ui', 'calf-navigation', 'calf-share', 'calf-camera-picker')
        self.assertEqual(8, len(inventory))
        self.assertEqual((*inventory, "calf-permissions/core"), lt.MINIMUM_MODULES["android-device"])
        with self.assertRaises(ValueError) as refused:
            lt.plan(ROOT, "android-device")
        self.assertIn(str(refused.exception), (
            'Unfiltered Android discovery requires a qualified remote IO fixture route; full aggregate is blocked',
            'Enabled API35-only callback requires exact finite Camera selection; unrestricted Camera/all discovery refuses before host work',
        ))
        # An unrelated explicit subset cannot admit the unfiltered Camera/IO domains.
        unrelated = ('calf-file-picker', 'calf-geo', 'calf-webview', 'calf-ui', 'calf-navigation', 'calf-share')
        plan = lt.plan(ROOT, "android-device", minimum_modules=unrelated, only_modules=unrelated)
        self.assertEqual(list(unrelated), [item["module"] for item in plan["expected"]])
        self.assertEqual(list(unrelated), plan["explicit_module_subset"])
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(["calf-permissions/core"], plan["finite_only_device_modules_not_requested"])
        self.assertEqual(["calf-camera-picker", "calf-io", "calf-permissions/core"],
                         plan["test_bearing_modules_not_requested"])
        self.assertFalse(lt.validate_test_focus(plan))
        self.assertNotIn("android_permission_demo", plan)
        self.assertNotIn("android_storage_probe", plan)
        forged = deepcopy(plan); forged["complete_suite_requested"] = True
        with self.assertRaises(ValueError):
            lt.validate_test_focus(forged)
        source_files = lt.source_files
        def without_core_host(root, relative):
            return [] if relative == CORE + "/src/androidDeviceTest" else source_files(root, relative)
        # Reach the actual missing core host, not the unrelated default refusal.
        with patch.object(lt, "source_files", side_effect=without_core_host), self.assertRaisesRegex(
                ValueError, r"^Selected modules do not have android-device library test sources: \['calf-permissions/core'\]$"):
            lt.plan(ROOT, "android-device", only_modules=(CORE,), focus=lt.ANDROID_PERMISSION_DEMO_FOCUS)

    def test_core_cannot_escape_finite_focus_suite_or_single_module_boundaries(self):
        for suite, modules, focus in (("android-device", (CORE,), None),
                ("android-device", (CORE, "calf-io"), None),
                ("android-device", (CORE,), "android-storage-*"),
                ("android-device", (CORE,), "android-permission-*"),
                ("android-device", (CORE,), lt.ANDROID_IO_REFERENCE_FOCUS),
                ("android-host", (CORE,), lt.ANDROID_PERMISSION_DEMO_FOCUS),
                ("android-host", (CORE,), storage.ROWS[0].profile)):
            with self.subTest(suite=suite, modules=modules, focus=focus), self.assertRaises(ValueError):
                lt.plan(ROOT, suite, only_modules=modules, focus=focus)

    def test_io_reference_route_keeps_only_its_exact_documents_helper(self):
        focus = lt.ANDROID_IO_REFERENCE_FOCUS
        row, = workflow.matrix(focus)["include"]
        self.assertEqual(("35", "calf-io", focus),
            (row["emulator-api"], row["test-modules"], row["test-focus"]))
        plan = lt.plan(ROOT, "android-device", only_modules=("calf-io",), focus=focus)
        self.assertTrue(lt.validate_test_focus(plan))
        self.assertIn("android_io_documents", plan)
        self.assertNotIn("android_permission_demo", plan)
        self.assertNotIn("android_storage_probe", plan)
        selected, = plan["expected"]
        self.assertEqual(3, len(selected["required_testcases"]))
        self.assertEqual(lt.ANDROID_IO_REFERENCE_CLASS, selected["test_filter"])


if __name__ == "__main__":
    unittest.main()
