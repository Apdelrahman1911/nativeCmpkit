"""Important Gradle source controls, not DSL compilation, task or JNI execution."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_METHODS = {
    "pickerNativeLibraryLoadsAndInitializes",
    "packagedPickerCreatesAndReleasesValidHandles",
    "shareNativeLibraryLoadsAndReportsActualHostCapability",
}


class NativeConsumerPreflightSourceTest(unittest.TestCase):
    def setUp(self):
        self.build = (ROOT / "tests/consumer/build.gradle.kts").read_text()
        self.preflight = self.build.split('tasks.register<Exec>("verifyCandidateNativePackages")', 1)[1].split('} else null', 1)[0]
        self.result = self.build.split('tasks.register<Exec>("verifyNativeConsumerResults")', 1)[1].split('} else null', 1)[0]
        self.focus = self.build.split('tasks.withType<Test>().configureEach {', 1)[1].split('maxParallelForks = 1', 1)[0]

    def test_native_jni_task_depends_on_package_and_actual_resolution_preflight(self):
        self.assertIn('dependsOn("verifyCandidateResolution")', self.preflight)
        self.assertIn('if (name == "desktopTest")', self.focus)
        self.assertIn('dependsOn(checkNotNull(nativePackagePreflight))', self.focus)
        self.assertLess(self.build.index('dependsOn(checkNotNull(nativePackagePreflight))'),
                        self.build.index('systemProperty("nativecmpkit.expected.$module.sha256"'))

    def test_independent_root_revision_and_clean_checkout_are_required_not_manifest_inferred(self):
        for field in (
            'gradleProperty("nativecmpkitExpectedNativeRevision").orNull',
            'Regex("[0-9a-f]{40}").matches(expectedRevision)',
            'gradleProperty("nativecmpkitProducerSourceRoot").orNull',
            'sourceRoot.isAbsolute && sourceRoot.isDirectory',
            'commandLine("git", "rev-parse", "HEAD")',
            'check(actualRevision == expectedRevision)',
            'commandLine("git", "status", "--porcelain", "--untracked-files=normal")',
            'check(sourceStatus.isBlank())',
            '"--source-root", sourceRoot.absolutePath',
            '"--expected-native-revision", expectedRevision',
        ):
            with self.subTest(field=field):
                self.assertIn(field, self.preflight)
        self.assertNotIn('JsonSlurper', self.preflight)
        self.assertNotIn('sourceRevision', self.preflight)

    def test_preflight_keeps_all21_roots_and_forbids_dirty_or_reduced_module_flags(self):
        modules = self.build.split('val candidateModules = listOf(', 1)[1].split('\n)', 1)[0]
        self.assertEqual(21, len(re.findall(r'"([a-z-]+)"', modules)))
        self.assertIn('"file-picker"', modules)
        self.assertIn('"share"', modules)
        self.assertIn('"--target", "desktop", "--native-platform", consumerNativePlatform()', self.preflight)
        self.assertNotIn('"--module"', self.preflight)
        self.assertNotIn('--allow-dirty-native-diagnostic', self.preflight)
        self.assertIn('outputs.upToDateWhen { false }', self.preflight)

    def test_native_focus_selects_exact_original3_and_preserves_default_all(self):
        native = (ROOT / "tests/consumer/src/desktopTest/kotlin/nativecmpkit/consumer/PublishedNativeConsumerTest.kt").read_text()
        originals = set(re.findall(r'@Test fun (\w+)\(', native))
        methods = self.focus.split('val methods = listOf(', 1)[1].split(')', 1)[0]
        self.assertEqual(EXPECTED_METHODS, originals)
        self.assertEqual(EXPECTED_METHODS, set(re.findall(r'"(\w+)"', methods)))
        self.assertIn('includeTestsMatching("nativecmpkit.consumer.PublishedNativeConsumerTest.$it")', self.focus)
        self.assertIn('gradleProperty("nativecmpkitConsumerTestFocus").orElse("all")', self.build)
        self.assertIn('consumerTargets == setOf("desktop")', self.build)
        self.assertIn('consumerTestFocus in setOf("all", "native")', self.build)

    def test_native_focus_is_fresh_not_up_to_date_or_build_cache_xml_reuse(self):
        for field in (
            'UUID.randomUUID().toString()',
            '"test-results/native-focused/$nativeInvocation"',
            'check(!focusedNativeResults.get().asFile.exists())',
        ):
            with self.subTest(field=field):
                self.assertIn(field, self.build)
        self.assertIn('outputs.upToDateWhen { false }', self.focus)
        self.assertIn('outputs.doNotCacheIf("Native-only consumer focus requires actual fresh JNI execution") { true }', self.focus)
        self.assertIn('reports.junitXml.outputLocation.set(focusedNativeResults)', self.focus)

    def test_empty_failed_or_skipped_selection_cannot_silently_omit_result_gate(self):
        self.assertIn('isFailOnNoMatchingTests = true', self.focus)
        self.assertIn('failOnNoDiscoveredTests.set(true)', self.focus)
        self.assertIn('finalizedBy(checkNotNull(nativeFocusedResultCheck))', self.focus)
        self.assertIn('dependsOn("desktopTest")', self.result)
        self.assertIn('outputs.upToDateWhen { false }', self.result)
        self.assertIn('"--results-dir", focusedNativeResults.get().asFile.absolutePath', self.result)
        self.assertIn('"--invocation-id", nativeInvocation', self.result)

    def test_five_intended_native_slots_are_exact_and_windows_arm_is_not_claimed(self):
        mapping = self.build.split('fun consumerNativePlatform(): String = when (consumerJavaFxClassifier()) {', 1)[1].split('\n}', 1)[0]
        self.assertEqual({
            "linux": "linux-x64", "linux-aarch64": "linux-arm64", "mac": "macos-x64",
            "mac-aarch64": "macos-arm64", "win": "windows-x64",
        }, dict(re.findall(r'"([^\"]+)" -> "([^\"]+)"', mapping)))
        self.assertIn('os.contains("win") && !arm', self.build)
        self.assertIn('consumerNativePlatform() == "windows-x64") "python" else "python3"', self.build)

    def test_checked_consumer_copy_and_documented_native_route_preserve_jni_ownership(self):
        self.assertIn('layout.projectDirectory.file("verify_artifacts.py")', self.preflight)
        self.assertIn('check(checker.isFile)', self.preflight)
        self.assertIn('layout.projectDirectory.file("verify_native_test_results.py")', self.result)
        for field in (
            'maxParallelForks = 1', 'jvmArgs("-Xcheck:jni")',
            'systemProperty("java.library.path", emptyLibraryPath.get().asFile.absolutePath)',
            'val binding = bindCandidateArtifact(id, artifact.file)',
        ):
            with self.subTest(field=field):
                self.assertIn(field, self.build)
        readme = (ROOT / "tests/consumer/README.md").read_text()
        self.assertIn('verifyCandidateResolution verifyNativeConsumerResults', readme)
        self.assertIn('-PnativecmpkitExpectedNativeRevision="$REVIEWED_PRODUCER_REVISION"', readme)
        self.assertIn('-PnativecmpkitProducerSourceRoot="$REVIEWED_PRODUCER_ROOT"', readme)
        self.assertIn('not an executed Gradle/JNI pass', readme)


if __name__ == "__main__":
    unittest.main()
