"""Synthetic/source NAV-015 guards only. No merged build, OS prompt or native permission result."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from android_permission_menu import ANDROID, EXPECTED, MANIFEST, declarations, inspect, mapping

ROOT = Path(__file__).resolve().parents[2]


class AndroidPermissionMenuTest(unittest.TestCase):
    def test_all_current_rows_and_supported_api_predictions_are_explicit(self):
        result = inspect(ROOT)
        self.assertEqual(24, result["menu_count"])
        self.assertEqual([name for name, _, _ in EXPECTED], [row["menu"] for row in result["rows"]])
        self.assertEqual("source-only", result["manifest_kind"])
        self.assertIs(False, result["manifest_generation_execution_proven"])
        self.assertIs(False, result["status_predictions_are_native_results"])
        self.assertEqual(0, result["native_executions"])
        for row in result["rows"]:
            self.assertEqual({str(api) for api in range(24, 38)}, set(row["fresh_install_status_predictions_by_api"]))
            if row["native_permission"] is not None:
                self.assertIsInstance(row["manifest_declaration"], dict)

    def test_sdk_cutoffs_and_apns_no_gate_are_not_native_support_claims(self):
        rows = {row["menu"]: row for row in inspect(ROOT)["rows"]}
        for name, before, after in (("WriteStorage", 28, 29), ("Gallery", 32, 33), ("ReadStorage", 32, 33)):
            self.assertEqual("Available", rows[name]["fresh_install_status_predictions_by_api"][str(before)]["availability"])
            self.assertEqual("NotRequired", rows[name]["fresh_install_status_predictions_by_api"][str(after)]["availability"])
            self.assertEqual("Unknown", rows[name]["fresh_install_status_predictions_by_api"][str(after)]["access"])
        for name, minimum in (("ReadImage", 33), ("ReadVideo", 33), ("ReadAudio", 33), ("Notification", 33),
            ("BluetoothScan", 31), ("BluetoothConnect", 31), ("BluetoothAdvertise", 31), ("WifiNearbyDevices", 33)):
            self.assertEqual("NotRequired", rows[name]["fresh_install_status_predictions_by_api"][str(minimum - 1)]["availability"])
            self.assertEqual("Available", rows[name]["fresh_install_status_predictions_by_api"][str(minimum)]["availability"])
        self.assertIsNone(rows["RemoteNotification"]["native_permission"])
        self.assertTrue(rows["RemoteNotification"]["always_granted"])
        self.assertEqual("NotRequired", rows["RemoteNotification"]["fresh_install_status_predictions_by_api"]["37"]["availability"])

    def test_merged_declaration_models_refuse_broad_call_sms_caps_and_duplicates(self):
        payload = (ROOT / MANIFEST).read_bytes()
        for name in ("CALL_PHONE", "MANAGE_EXTERNAL_STORAGE", "READ_SMS", "SEND_SMS", "RECEIVE_SMS"):
            manifest = ET.fromstring(payload)
            ET.SubElement(manifest, "uses-permission", {ANDROID + "name": "android.permission." + name})
            with self.subTest(name=name), self.assertRaises(ValueError):
                declarations(ET.tostring(manifest))
        manifest = ET.fromstring(payload)
        ET.SubElement(manifest, "uses-permission", {ANDROID + "name": "android.permission.CAMERA"})
        with self.assertRaises(ValueError):
            declarations(ET.tostring(manifest))
        for permission in ("READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE"):
            manifest = ET.fromstring(payload)
            row = next(node for node in manifest.findall("uses-permission") if node.get(ANDROID + "name") == "android.permission." + permission)
            row.attrib.pop(ANDROID + "maxSdkVersion")
            with self.subTest(cap=permission), self.assertRaises(ValueError):
                declarations(ET.tostring(manifest))

    def test_source_xml_is_refused_as_generated_merge_input(self):
        for path in (MANIFEST, "/tmp/AndroidManifest.xml", "sample/android/build/other/AndroidManifest.xml"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                inspect(ROOT, path)

    def test_empty_or_ambiguous_mapping_cannot_silently_become_support(self):
        for body in ('AndroidPermissionMapping("")',
            'AndroidPermissionMapping(permissionString = Manifest.permission.CAMERA, permissionString = Manifest.permission.RECORD_AUDIO)'):
            payload = ('internal actual fun registerCameraPermission(permission: Permission) {\n' + body + '\n}').encode()
            with self.subTest(body=body), self.assertRaises(ValueError):
                mapping("Camera", payload)
        payload = b'internal actual fun registerRemoteNotificationPermission(permission: Permission) {\nAndroidPermissionMapping("", alwaysGranted = true)\n}'
        self.assertIsNone(mapping("RemoteNotification", payload)["native_permission"])

    def test_dtd_and_entity_manifest_models_are_refused(self):
        for value in (b'<!DOCTYPE manifest [<!ENTITY value "android.permission.CAMERA">]><manifest/>',
            b'<!DOCTYPE manifest SYSTEM "file:///private/not-read"><manifest/>'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                declarations(value)


if __name__ == "__main__":
    unittest.main()
