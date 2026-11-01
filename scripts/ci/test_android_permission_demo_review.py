"""New source/model ownership review guards. No Kotlin build, native API, OS UI or CI execution."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

import android_permission_demo as demo
import dependency_cache_inputs as cache
from test_android_permission_demo_denial_absence import require_permission_absence_protocol

ROOT = Path(__file__).resolve().parents[2]
STARTUP = "androidx.startup.InitializationProvider"
INITIALIZERS = ("androidx.lifecycle.ProcessLifecycleInitializer", "androidx.profileinstaller.ProfileInstallerInitializer")
PROFILE_ACTIONS = tuple("androidx.profileinstaller.action." + name for name in
    ("INSTALL_PROFILE", "SKIP_FILE", "SAVE_PROFILE", "BENCHMARK_OPERATION"))


def compiled_model():
    root = ET.parse(ROOT / demo.FIXTURE / "src/main/AndroidManifest.xml").getroot()
    root.set("package", demo.PACKAGE)
    app = root.find("application")
    app.set(demo.ANDROID + "debuggable", "true")
    ET.SubElement(root, "uses-sdk", {demo.ANDROID + "minSdkVersion": "33", demo.ANDROID + "targetSdkVersion": "37"})
    provider = ET.SubElement(app, "provider", {demo.ANDROID + "name": STARTUP,
        demo.ANDROID + "authorities": demo.PACKAGE + ".androidx-startup", demo.ANDROID + "exported": "false"})
    for name in INITIALIZERS:
        ET.SubElement(provider, "meta-data", {demo.ANDROID + "name": name, demo.ANDROID + "value": "androidx.startup"})
    receiver = ET.SubElement(app, "receiver", {demo.ANDROID + "name": "androidx.profileinstaller.ProfileInstallReceiver",
        demo.ANDROID + "directBootAware": "false", demo.ANDROID + "enabled": "true",
        demo.ANDROID + "permission": "android.permission.DUMP", demo.ANDROID + "exported": "true"})
    for name in PROFILE_ACTIONS:
        ET.SubElement(ET.SubElement(receiver, "intent-filter"), "action", {demo.ANDROID + "name": name})
    return root


class AndroidPermissionDemoSourceReviewTest(unittest.TestCase):
    def test_compiled_startup_metadata_is_exact_and_duplicate_or_foreign_children_refuse(self):
        root = compiled_model()
        demo.validate_manifest(ET.tostring(root), compiled=True)
        for mutation in (
            lambda node: ET.SubElement(node, "meta-data", {demo.ANDROID + "name": "foreign.Initializer", demo.ANDROID + "value": "androidx.startup"}),
            lambda node: node.append(deepcopy(node[0])),
            lambda node: ET.SubElement(node, "grant-uri-permission", {demo.ANDROID + "pathPrefix": "/"}),
            lambda node: node.set(demo.ANDROID + "grantUriPermissions", "true"),
            lambda node: node.set(demo.ANDROID + "process", ":unreviewed"),
        ):
            modeled = deepcopy(root)
            mutation(modeled.find("application/provider"))
            with self.subTest(model=ET.tostring(modeled)), self.assertRaises(ValueError):
                demo.validate_manifest(ET.tostring(modeled), compiled=True)

    def test_compiled_profile_receiver_does_not_admit_new_control_actions_or_aliases(self):
        root = compiled_model()
        for mutation in (
            lambda node: ET.SubElement(ET.SubElement(node, "intent-filter"), "action", {demo.ANDROID + "name": "foreign.CONTROL"}),
            lambda node: node.append(deepcopy(node[0])),
            lambda node: ET.SubElement(node[0], "category", {demo.ANDROID + "name": "android.intent.category.DEFAULT"}),
            lambda node: node.set(demo.ANDROID + "process", ":unreviewed"),
            lambda node: node.set(demo.ANDROID + "enabled", "false"),
        ):
            modeled = deepcopy(root)
            mutation(modeled.find("application/receiver"))
            with self.subTest(model=ET.tostring(modeled)), self.assertRaises(ValueError):
                demo.validate_manifest(ET.tostring(modeled), compiled=True)

    def test_partial_owned_seed_cleanup_uses_identity_not_successful_content_as_admission(self):
        source = (ROOT / demo.APPLICATION_KOTLIN / "PermissionDemoActivity.kt").read_text()
        insert = source.split("private fun insertOwned(", 1)[1].split("private fun assertOwned", 1)[0]
        self.assertLess(insert.index("seeds[kind] = seed"), insert.index("openOutputStream"))
        close = source.split("private fun closeOwnedSeeds()", 1)[1].split("override fun onDestroy", 1)[0]
        self.assertIn("assertOwnedIdentity(seed)", close)
        self.assertIn("seed.published", close)
        self.assertIn("contentResolver.delete(seed.uri, null, null) == 1", close)
        self.assertIn("firstFailure", close)
        self.assertIn("appendFailure(firstFailure, failure)", close)
        record = source.split("private fun recordCleanupFailure(", 1)[1].split("private fun closeOwnedActivity()", 1)[0]
        self.assertIn("cleanupFailed = true", record)
        self.assertIn("cleanupFailure = appendFailure(cleanupFailure, failure)", record)
        aggregate = source.split("private fun appendFailure(", 1)[1].split("private fun recordCleanupFailure(", 1)[0]
        self.assertIn("firstFailure.addSuppressed(failure)", aggregate)

    def test_accessibility_queries_release_filtered_nodes_and_restore_only_the_original_flags(self):
        source = (ROOT / demo.KOTLIN / "PermissionDemoSystemUi.kt").read_text()
        self.assertIn("private val originalFlags = automation.serviceInfo.flags", source)
        self.assertIn("flags = originalFlags", source)
        self.assertIn("val acquired = nodes(root)", source)
        self.assertIn("val matches = acquired.filter", source)
        self.assertIn("acquired.forEach { it.recycle() }", source)
        self.assertIn("ancestors.forEach { it.recycle() }", source)
        before_click = source.split("private fun click(packages:", 1)[0]
        self.assertNotIn(".filter {", before_click)

    def test_binder_readback_pins_sender_process_and_canonical_generation_without_manual_grants(self):
        source = (ROOT / demo.KOTLIN / "OwnedPermissionDemo.kt").read_text()
        self.assertIn("message.sendingUid != owner.uid", source)
        self.assertIn("private var nativePid: Int? = null", source)
        self.assertIn("assertEquals(nativePid, pid)", source)
        self.assertIn("[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", source)
        self.assertTrue(demo.source_contract(ROOT)["source_policy_verified"])

    def test_native_teardown_refuses_dead_or_unknown_endpoint_before_still_releasing_the_binding_and_thread(self):
        source = (ROOT / demo.KOTLIN / "OwnedPermissionDemo.kt").read_text()
        close = source.split("override fun close()", 1)[1]
        self.assertIn("if (bound)", close)
        self.assertIn("assertNull(protocolError)", close)
        self.assertIn("assertNotNull(endpoint", close)
        self.assertNotIn("if (endpoint != null)", close)
        self.assertLess(close.index("assertNotNull(endpoint"), close.index('request("observe")'))
        self.assertIn("context.unbindService(connection)", close)
        self.assertIn("thread.quitSafely()", close)
        self.assertIn("check(!thread.isAlive)", close)

    def test_no_dialog_is_not_inferred_from_an_unknown_or_foreign_active_accessibility_window(self):
        source = (ROOT / demo.KOTLIN / "PermissionDemoSystemUi.kt").read_text()
        # Current approved ACTIVE/refresh/presence/owned-host protocol, not an old Boolean query.
        require_permission_absence_protocol(source)
        observation = source.split("fun permissionDialogObservation(deadline: Long)", 1)[1].split("private fun requireObservationDeadline", 1)[0]
        self.assertIn("val root = automation.rootInActiveWindow", observation)
        self.assertIn("val refreshed = root.refresh()", observation)
        self.assertIn("val visible = if (refreshed) root.isVisibleToUser else null", observation)
        self.assertLess(observation.index("if (!refreshed) return"), observation.index("val packageName = root.packageName"))
        self.assertIn("PermissionDialogKind.UNKNOWN", observation)
        self.assertIn("if (visible != true) return unknown", observation)
        self.assertIn("return unknown.copy(kind = PermissionDialogKind.PRESENT)", observation)
        self.assertIn("return if (packageName == OwnedPermissionDemo.PACKAGE)", observation)
        self.assertNotIn("?: false", observation)
        self.assertIn("root?.recycle()", observation)

    def test_new_fixture_build_settings_manifest_and_recipe_are_dependency_keyed_not_its_sources_or_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "settings.gradle.kts").write_text('include(\n    ":calf-permissions:core",\n)\n')
            for relative in ("calf-permissions/core/build.gradle.kts", "scripts/ci/android_permission_demo.py",
                demo.FIXTURE + "/build.gradle.kts", demo.FIXTURE + "/settings.gradle.kts",
                demo.FIXTURE + "/gradle.properties", demo.FIXTURE + "/src/main/AndroidManifest.xml"):
                dest = root / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes((ROOT / relative).read_bytes())
            values = cache.selected_inputs(root, "libraries")
            for relative in ("scripts/ci/android_permission_demo.py", demo.FIXTURE + "/build.gradle.kts",
                demo.FIXTURE + "/settings.gradle.kts", demo.FIXTURE + "/gradle.properties",
                demo.FIXTURE + "/src/main/AndroidManifest.xml"):
                self.assertIn(relative, values)
                path = root / relative
                before = path.read_bytes()
                path.write_bytes(before + b"\nsynthetic-key-mutation-not-compiled\n")
                self.assertNotEqual(cache.fingerprint("libraries", values),
                    cache.fingerprint("libraries", cache.selected_inputs(root, "libraries")))
                path.write_bytes(before)
            for relative in (demo.APPLICATION_KOTLIN + "Unrequested.kt", demo.FIXTURE + "/build/outputs/apk/debug/old.apk",
                demo.FIXTURE + "/build/private/debug.keystore", demo.FIXTURE + "/build/test-results/TEST-old.xml"):
                dest = root / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text("not a dependency declaration or execution evidence\n")
            self.assertEqual(values, cache.selected_inputs(root, "libraries"))


EMITTED_EMOJI_INITIALIZER = "androidx.emoji2.text.EmojiCompatInitializer"
EMITTED_OPTIONAL_LIBRARIES = ("androidx.window.extensions", "androidx.window.sidecar")


def compiled_optional_dependency_model(*, emoji=True):
    """Synthetic complete dependency additions; never an actual APK receipt."""
    root = compiled_model()
    app = root.find("application")
    if emoji:
        ET.SubElement(app.find("provider"), "meta-data", {demo.ANDROID + "name": EMITTED_EMOJI_INITIALIZER,
            demo.ANDROID + "value": "androidx.startup"})
    for name in EMITTED_OPTIONAL_LIBRARIES:
        ET.SubElement(app, "uses-library", {demo.ANDROID + "name": name, demo.ANDROID + "required": "false"})
    return root


class AndroidPermissionDemoCompiledDependencyTest(unittest.TestCase):
    def test_emitted_emoji_and_optional_libraries_are_admitted_without_filtering(self):
        root = compiled_optional_dependency_model()
        before = ET.tostring(root)
        policy = demo.validate_manifest(before, compiled=True)
        self.assertTrue(policy["compiled_manifest_inspected"])
        self.assertTrue(policy["signature_control_only"])
        self.assertEqual(before, ET.tostring(root))
        self.assertEqual(3, len(root.findall("application/provider/meta-data")))
        self.assertEqual(2, len(root.findall("application/uses-library")))

    def test_optional_libraries_without_extra_startup_are_also_admitted(self):
        root = compiled_optional_dependency_model(emoji=False)
        self.assertTrue(demo.validate_manifest(ET.tostring(root), compiled=True)["compiled_manifest_inspected"])

    def test_optional_libraries_refuse_foreign_required_or_unknown_shapes(self):
        root = compiled_optional_dependency_model()
        for mutation in (
            lambda node: node.set(demo.ANDROID + "name", "foreign.window.library"),
            lambda node: node.attrib.pop(demo.ANDROID + "name"),
            lambda node: node.set(demo.ANDROID + "required", "true"),
            lambda node: node.set(demo.ANDROID + "required", "0"),
            lambda node: node.attrib.pop(demo.ANDROID + "required"),
            lambda node: node.set(demo.ANDROID + "permission", "android.permission.MANAGE_EXTERNAL_STORAGE"),
            lambda node: node.set("unknown", "false"),
        ):
            for index in (0, 1):
                modeled = deepcopy(root)
                mutation(modeled.findall("application/uses-library")[index])
                with self.subTest(library=index, model=ET.tostring(modeled)), self.assertRaises(ValueError):
                    demo.validate_manifest(ET.tostring(modeled), compiled=True)

    def test_optional_libraries_refuse_duplicates_and_nested_declarations(self):
        root = compiled_optional_dependency_model()
        for index in (0, 1):
            modeled = deepcopy(root)
            modeled.find("application").append(deepcopy(modeled.findall("application/uses-library")[index]))
            with self.subTest(duplicate=index), self.assertRaises(ValueError):
                demo.validate_manifest(ET.tostring(modeled), compiled=True)
            modeled = deepcopy(root)
            ET.SubElement(modeled.findall("application/uses-library")[index], "meta-data",
                {demo.ANDROID + "name": "foreign.Initializer", demo.ANDROID + "value": "androidx.startup"})
            with self.subTest(child=index), self.assertRaises(ValueError):
                demo.validate_manifest(ET.tostring(modeled), compiled=True)

    def test_emoji_metadata_refuses_unknown_duplicate_value_attributes_and_children(self):
        root = compiled_optional_dependency_model()
        for mutation in (
            lambda node: node.set(demo.ANDROID + "name", "foreign.Initializer"),
            lambda node: node.set(demo.ANDROID + "value", "foreign.startup"),
            lambda node: node.set(demo.ANDROID + "resource", "@xml/foreign"),
            lambda node: ET.SubElement(node, "grant-uri-permission", {demo.ANDROID + "pathPrefix": "/"}),
        ):
            modeled = deepcopy(root)
            mutation(modeled.find("application/provider")[-1])
            with self.subTest(model=ET.tostring(modeled)), self.assertRaises(ValueError):
                demo.validate_manifest(ET.tostring(modeled), compiled=True)
        modeled = deepcopy(root)
        modeled.find("application/provider").append(deepcopy(modeled.find("application/provider")[-1]))
        with self.assertRaises(ValueError):
            demo.validate_manifest(ET.tostring(modeled), compiled=True)

    def test_dependency_admission_preserves_permissions_uid_controls_and_components(self):
        root = compiled_optional_dependency_model()
        for mutation in (
            lambda node: node.set(demo.ANDROID + "sharedUserId", "android.uid.system"),
            lambda node: node.set(demo.ANDROID + "sharedUserMaxSdkVersion", "35"),
            lambda node: ET.SubElement(node, "uses-permission", {demo.ANDROID + "name": "android.permission.MANAGE_EXTERNAL_STORAGE"}),
            lambda node: ET.SubElement(node, "uses-permission", {demo.ANDROID + "name": "android.permission.READ_SMS"}),
            lambda node: node.find("permission").set(demo.ANDROID + "protectionLevel", "normal"),
            lambda node: node.find("application/activity").attrib.pop(demo.ANDROID + "permission"),
            lambda node: node.find("application/service").attrib.pop(demo.ANDROID + "permission"),
            lambda node: node.find("application/provider").set(demo.ANDROID + "exported", "true"),
            lambda node: node.find("application/receiver").attrib.pop(demo.ANDROID + "permission"),
            lambda node: ET.SubElement(node.find("application"), "uses-native-library",
                {demo.ANDROID + "name": "foreign.native", demo.ANDROID + "required": "false"}),
        ):
            modeled = deepcopy(root)
            mutation(modeled)
            with self.subTest(model=ET.tostring(modeled)), self.assertRaises(ValueError):
                demo.validate_manifest(ET.tostring(modeled), compiled=True)

    def test_dependency_admission_does_not_add_source_manifest_components(self):
        original = ET.parse(ROOT / demo.FIXTURE / "src/main/AndroidManifest.xml").getroot()
        for tag, attrs in (("uses-library", {demo.ANDROID + "name": EMITTED_OPTIONAL_LIBRARIES[0],
            demo.ANDROID + "required": "false"}), ("provider", {demo.ANDROID + "name": STARTUP,
            demo.ANDROID + "authorities": demo.PACKAGE + ".androidx-startup", demo.ANDROID + "exported": "false"})):
            modeled = deepcopy(original)
            ET.SubElement(modeled.find("application"), tag, attrs)
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                demo.validate_manifest(ET.tostring(modeled), compiled=False)


if __name__ == "__main__":
    unittest.main()
