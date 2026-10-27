"""Current branding guards; not compilation, ABI or publication evidence."""
from pathlib import Path
import json
import plistlib
import unittest


ROOT = Path(__file__).resolve().parents[2]


class CurrentIdentityTest(unittest.TestCase):
    def test_library_and_exact_producer_root_use_the_owner_requested_name(self):
        identity = json.loads((ROOT / "docs/migration/identity.json").read_bytes())
        self.assertEqual("NativeCmpKit", identity["project"])
        self.assertIn('rootProject.name = "NativeCmpKit"', (ROOT / "settings.gradle.kts").read_text())
        self.assertIn('check(root.name == "NativeCmpKit")', (ROOT / "scripts/ci/stage-core-io.init.gradle.kts").read_text())

    def test_current_docs_and_publication_display_use_the_same_brand(self):
        for name in ("README.md", "docs/index.md", "AGENTS.md"):
            with self.subTest(path=name):
                self.assertTrue((ROOT / name).read_text().startswith("# NativeCmpKit"))
        self.assertIn("site_name: 'NativeCmpKit'", (ROOT / "mkdocs.yml").read_text())
        self.assertIn('name.set("NativeCmpKit - "', (ROOT / "convention-plugins/src/main/kotlin/module.publication.gradle.kts").read_text())

    def test_sample_display_names_change_without_changing_framework_or_packages(self):
        self.assertIn('title = "NativeCmpKit"', (ROOT / "sample/desktop/src/jvmMain/kotlin/Main.kt").read_text())
        self.assertIn('android:label="NativeCmpKit"', (ROOT / "sample/android/src/main/AndroidManifest.xml").read_text())
        for name in ("sample/web-js/src/jsMain/resources/index.html", "sample/web-wasm/src/wasmJsMain/resources/index.html"):
            with self.subTest(path=name):
                self.assertIn("<title>NativeCmpKit Demo</title>", (ROOT / name).read_text())
        info = plistlib.loads((ROOT / "sample/ios/Calf/Info.plist").read_bytes())
        self.assertEqual("NativeCmpKit", info["CFBundleDisplayName"])
        show = (ROOT / "sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/ShowcaseScreen.kt").read_text()
        self.assertIn('title = "About NativeCmpKit"', show)

    def test_lowercase_coordinates_and_retained_public_names_stay_compatible(self):
        identity = json.loads((ROOT / "docs/migration/identity.json").read_bytes())
        self.assertEqual("io.github.apdelrahman1911.nativecmpkit", identity["maven_group"])
        self.assertEqual("com.mohamedrejeb.calf", identity["public_kotlin_namespace"])
        self.assertEqual(21, len(identity["modules"]))
        self.assertTrue(all(m["new_artifact"].startswith("nativecmpkit-") and m["gradle_project"].startswith(":calf-")
                            for m in identity["modules"]))
        self.assertFalse(identity["binary_compatibility_verified"])
        build = (ROOT / "build.gradle.kts").read_text()
        self.assertIn('gradleProperty("nativeCmpkit.version")', build)
        self.assertIn('gradleProperty("nativeCmpkit.allowPublishing")', build)
        resources = (ROOT / "calf-cupertino-icons/build.gradle.kts").read_text()
        self.assertIn('packageOfResClass = "com.mohamedrejeb.calf.calf_cupertino_icons.generated.resources"', resources)

    def test_existing_attribution_is_not_rewritten_by_a_display_name_change(self):
        notice = (ROOT / "NOTICE").read_text()
        self.assertIn("Mohamed Rejeb", notice)
        self.assertIn("Calf", notice)
        self.assertIn('publish = false', (ROOT / "calf-share/native/Cargo.toml").read_text())
        self.assertIn('publish = false', (ROOT / "calf-file-picker/native/Cargo.toml").read_text())


if __name__ == "__main__":
    unittest.main()
