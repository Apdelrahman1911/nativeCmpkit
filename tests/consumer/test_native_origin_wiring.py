"""Important source wiring checks; not Kotlin/Gradle compilation or JNI execution."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "tests/consumer/build.gradle.kts"
NATIVE = ROOT / "tests/consumer/src/desktopTest/kotlin/nativecmpkit/consumer/PublishedNativeConsumerTest.kt"


class NativeOriginWiringTest(unittest.TestCase):
    def setUp(self):
        self.build = BUILD.read_text()
        self.native = NATIVE.read_text()

    def test_expected_hashes_come_from_exact_native_runtime_maven_bindings(self):
        for required in (
            'if (name == "desktopTest")',
            'configurations.getByName("desktopTestRuntimeClasspath").incoming.artifacts.artifacts',
            'for (module in listOf("file-picker", "share"))',
            'id is ModuleComponentIdentifier && id.group == candidateGroup &&',
            'id.module == "nativecmpkit-$module-desktop" && id.version == candidateVersion',
            'check(selected.size == 1)',
            'val binding = bindCandidateArtifact(id, artifact.file)',
            'check(classpath.files.any { it.canonicalFile == artifact.file.canonicalFile })',
            'systemProperty("nativecmpkit.expected.$module.name", artifact.file.name)',
            'systemProperty("nativecmpkit.expected.$module.sha256", binding.getValue("sha256"))',
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.build)
        self.assertLess(self.build.index('val binding = bindCandidateArtifact(id, artifact.file)'),
                        self.build.index('systemProperty("nativecmpkit.expected.$module.sha256"'))

    def test_loaded_class_and_payload_are_checked_before_native_initialization(self):
        ordered = (
            'assertEquals(1, resources.size',
            'assertEquals("jar", resources.single().protocol',
            'Class.forName(name, false, loader)',
            'assertEquals("file", origin.protocol',
            'assertTrue(Files.isRegularFile(jar)',
            'System.getProperty("nativecmpkit.expected.$module.sha256")',
            'Files.newInputStream(jar).use',
            'assertEquals(expected, hash.digest()',
            'assertEquals(jar.toRealPath(), Path.of(resource.jarFileURL.toURI()).toRealPath()',
            'return type',
        )
        positions = [self.native.index(fragment) for fragment in ordered]
        self.assertEqual(sorted(positions), positions)
        self.assertNotIn('Class.forName(name, true', self.native)
        self.assertLess(positions[-1], self.native.index('type.getMethod("init").invoke(null)'))

    def test_jar_hash_reader_closes_stream_and_does_not_allocate_whole_jar(self):
        helper = self.native[:self.native.index('@Test fun pickerNativeLibraryLoadsAndInitializes')]
        self.assertIn('val buffer = ByteArray(64 * 1024)', helper)
        self.assertIn('Files.newInputStream(jar).use { stream ->', helper)
        self.assertIn('if (count < 0) break', helper)
        self.assertIn('hash.update(buffer, 0, count)', helper)
        self.assertNotIn('readAllBytes', helper)
        self.assertNotIn('readBytes()', helper)

    def test_same_owning_resource_jar_is_required_without_opening_cached_jar_files(self):
        self.assertIn('resources.single().openConnection() as JarURLConnection', self.native)
        self.assertLess(self.native.index('resource.useCaches = false'),
                        self.native.index('resource.jarFileURL.toURI()'))
        self.assertIn('jar.toRealPath(), Path.of(resource.jarFileURL.toURI()).toRealPath()', self.native)
        self.assertNotIn('resource.jarFile.', self.native)
        self.assertNotIn('resource.inputStream', self.native)

    def test_original_three_jni_scenarios_and_valid_handle_finally_remain(self):
        self.assertEqual([
            'pickerNativeLibraryLoadsAndInitializes', 'packagedPickerCreatesAndReleasesValidHandles',
            'shareNativeLibraryLoadsAndReportsActualHostCapability',
        ], re.findall(r'@Test fun (\w+)\(', self.native))
        for required in (
            'type.getMethod("init").invoke(null)',
            'type.getMethod("createDirectoryDialog", String::class.java, String::class.java, Long::class.javaPrimitiveType)',
            'type.getMethod("destroyDialog", Long::class.javaPrimitiveType)',
            'repeat(100)',
            'assertNotEquals(0L, handle)',
            'try { /* No native modal is displayed. */ } finally { destroy.invoke(null, handle) }',
            'type.getMethod("isNativeShareSupported").invoke(null) as Boolean',
            'assertEquals(os.contains("mac") || os.contains("darwin"), supported)',
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.native)
        self.assertIn('"calf_filepicker_native", "file-picker")', self.native)
        self.assertIn('"calf_share_native", "share")', self.native)

    def test_jni_checks_empty_system_library_path_and_serial_forks_are_retained(self):
        for required in (
            'maxParallelForks = 1', 'jvmArgs("-Xcheck:jni")',
            'systemProperty("java.library.path", emptyLibraryPath.get().asFile.absolutePath)',
            'systemProperty("user.home", nativeHome.get().asFile.absolutePath)',
            'check(emptyLibraryPath.get().asFile.listFiles()?.isEmpty() == true)',
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.build)
        self.assertNotIn('trustSystemLibrary=true', self.build)
        self.assertNotIn('trustSystemLibrary=true', self.native)


if __name__ == "__main__":
    unittest.main()
