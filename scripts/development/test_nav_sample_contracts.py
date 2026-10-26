"""Source/configuration policy guards; these are NOT native UI/device tests."""
from pathlib import Path
import plistlib
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SCREENS = ROOT / "sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens"
ANDROID = "{http://schemas.android.com/apk/res/android}"


class NavSampleContractTest(unittest.TestCase):
    def test_secure_dialog_demo_has_no_input_logging(self):
        text = (SCREENS / "AlertDialogScreen.kt").read_text()
        self.assertIn("isSecure = true", text)
        self.assertNotRegex(text, r"\b(?:println|print)\s*\(|\bLog\.[diewv]\s*\(|\blogger\.")
        self.assertIn("Secure input must never", text)

    def test_showcase_does_not_claim_clipboard_or_share_side_effect(self):
        text = (SCREENS / "ShowcaseScreen.kt").read_text()
        self.assertNotIn("Link copied to clipboard!", text)
        self.assertIn("No link was copied or shared.", text)

    def test_permission_demo_does_not_request_unused_sensitive_capabilities(self):
        root = ET.parse(ROOT / "sample/android/src/main/AndroidManifest.xml").getroot()
        permissions = {row.attrib[ANDROID + "name"]: row for row in root.findall("uses-permission")}
        for name in ("MANAGE_EXTERNAL_STORAGE", "READ_SMS", "SEND_SMS", "RECEIVE_SMS", "CALL_PHONE"):
            self.assertNotIn("android.permission." + name, permissions)
        self.assertEqual("32", permissions["android.permission.READ_EXTERNAL_STORAGE"].attrib[ANDROID + "maxSdkVersion"])
        self.assertEqual("28", permissions["android.permission.WRITE_EXTERNAL_STORAGE"].attrib[ANDROID + "maxSdkVersion"])
        self.assertNotIn("Permission.Call,", (SCREENS / "PermissionsScreen.kt").read_text())

    def test_apple_demo_declares_current_calendar_and_local_network_prerequisites(self):
        plist = plistlib.loads((ROOT / "sample/ios/Calf/Info.plist").read_bytes())
        for key in ("NSCalendarsFullAccessUsageDescription", "NSCalendarsWriteOnlyAccessUsageDescription",
                    "NSLocalNetworkUsageDescription"):
            self.assertTrue(plist.get(key, "").strip())
        self.assertIn("_lnp._tcp.", plist["NSBonjourServices"])

    def test_image_demo_uses_bounded_preparation_and_lazy_bounded_previews(self):
        saver = (SCREENS / "FileSaverScreen.kt").read_text()
        self.assertIn("readByteArray(maxBytes = MAX_SAMPLE_IMAGE_BYTES)", saver)
        self.assertNotIn("model = selectedFile", saver)
        self.assertIn("model = preparedImage", saver)
        self.assertIn("if (selectionVersion == generation)", saver)
        picker = (SCREENS / "ImagePickerScreen.kt").read_text()
        self.assertIn("LazyColumn(", picker)
        self.assertIn("items(files)", picker)
        self.assertIn(".height(240.dp)", picker)

    def test_unused_jetbrains_navigation_dependency_is_not_declared_by_sample(self):
        text = (ROOT / "sample/common/build.gradle.kts").read_text()
        self.assertNotIn("implementation(libs.jetbrains.navigation.compose)", text)
        self.assertIn("implementation(projects.calfNavigation)", text)


if __name__ == "__main__":
    unittest.main()
