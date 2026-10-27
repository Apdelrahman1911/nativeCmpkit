"""Lexical fixture fences, not Gradle/Kotlin/runtime/security certification."""
from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/consumer/io-desktop"
IO_TEST = Path("src/test/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt")
EXPECTED_METHODS = {
    "emptyFileReadsThroughBothPublicOverloads", "boundaryAndLargeStreamsPreserveAllBytes",
    "concurrentSourcesHaveIndependentPositions", "existingDirectoryAndMissingFileAreNotRegularFiles",
    "extensionlessFileAndUnicodeNameArePreserved", "repeatedStreamUseLeavesSourceReadableAndDeletable",
}


class CoreIoFixtureContractTest(unittest.TestCase):
    def code(self, file: str) -> str:
        # A narrow lexical guard for these known fixtures, NOT a Kotlin parser.
        return re.sub(r"//[^\n]*", "", (FIXTURE / file).read_text())

    def test_exact_six_existing_IO_scenarios_are_copied_without_edits(self):
        actual = (FIXTURE / IO_TEST).read_bytes()
        original = ROOT / "tests/consumer/src/desktopTest/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt"
        self.assertEqual(original.read_bytes(), actual)
        self.assertEqual(EXPECTED_METHODS, set(re.findall(r"@Test\s+fun\s+(\w+)", actual.decode())))

    def test_the_partial_fixture_has_only_the_explicit_test_source(self):
        files = sorted(p.relative_to(FIXTURE).as_posix() for p in (FIXTURE / "src").rglob("*") if p.is_file())
        self.assertEqual(["src/test/kotlin/nativecmpkit/consumer/PublishedArtifactOriginTest.kt", IO_TEST.as_posix()], files)

    def test_fixed_two_root_scope_does_not_shrink_the_original21_root_gate(self):
        build = self.code("build.gradle.kts")
        self.assertIn('val candidateRoots = listOf("nativecmpkit-core", "nativecmpkit-io")', build)
        full = (ROOT / "tests/consumer/build.gradle.kts").read_text()
        selected = re.search(r"val candidateModules = listOf\((.*?)\n\)", full, re.S)
        self.assertIsNotNone(selected)
        names = set(re.findall(r'"([a-z0-9-]+)"', selected.group(1)))
        identity = json.loads((ROOT / "docs/migration/identity.json").read_bytes())
        expected = {x["new_artifact"].removeprefix("nativecmpkit-") for x in identity["modules"]}
        self.assertEqual(21, len(names))
        self.assertEqual(expected, names)

    def test_candidate_group_remains_exclusive_to_an_absolute_existing_repository(self):
        settings = self.code("settings.gradle.kts")
        for value in ['exclusiveContent {', 'includeGroup("io.github.apdelrahman1911.nativecmpkit")',
                      'candidateDirectory.isAbsolute && candidateDirectory.isDirectory',
                      'RepositoriesMode.FAIL_ON_PROJECT_REPOS', 'gradleMetadata()', 'mavenPom()']:
            self.assertIn(value, settings)

    def test_no_composite_project_local_Maven_or_producer_source_substitutions(self):
        code = self.code("build.gradle.kts") + self.code("settings.gradle.kts")
        for call in ["includeBuild", "project", "mavenLocal", "dependencySubstitution", "srcDir"]:
            self.assertNotRegex(code, r"\b" + call + r"\s*\(")
        self.assertIn('check(id !is ProjectComponentIdentifier)', code)
        self.assertIn('check(id.group != "com.mohamedrejeb.calf")', code)

    def test_every_selected_classpath_requires_two_roots_and_exact_staged_bytes(self):
        build = self.code("build.gradle.kts")
        self.assertIn('listOf("compileClasspath", "runtimeClasspath", "testCompileClasspath", "testRuntimeClasspath")', build)
        self.assertIn('id.version == candidateVersion && id.module in allowedCandidates', build)
        self.assertIn('staged.isFile && artifactSha256(staged) == hash', build)
        self.assertIn('candidateRoots.all { it in seen || "$it-desktop" in seen }', build)
        self.assertIn('"complete_21_root_KMP_matrix_requested" to false', build)
        self.assertIn('"release_readiness_certified" to false', build)

    def test_test_task_cannot_succeed_using_old_results_or_missing_matching_methods(self):
        build = self.code("build.gradle.kts")
        self.assertIn('dependsOn(verifyCandidateResolution)', build)
        self.assertIn('includeTestsMatching("nativecmpkit.consumer.PublishedIoConsumerTest")', build)
        self.assertIn('includeTestsMatching("nativecmpkit.consumer.PublishedArtifactOriginTest")', build)
        self.assertIn('isFailOnNoMatchingTests = true', build)
        self.assertIn('outputs.upToDateWhen { false }', build)
        self.assertIn('maxParallelForks = 1', build)
        self.assertIn('jvmArgs("-Xcheck:jni")', build)

    def test_same_toolchain_and_exact_unpublished_candidate_are_required(self):
        build = self.code("build.gradle.kts")
        self.assertIn('kotlin("jvm") version "2.4.20"', build)
        self.assertIn('jvmToolchain(17)', build)
        self.assertIn('JvmTarget.JVM_17', build)
        self.assertIn('providers.gradleProperty("nativecmpkitVersion").orNull', build)
        self.assertIn('!candidateVersion.endsWith("-SNAPSHOT")', build)
        self.assertNotIn('maven-publish', build)

    def test_runtime_origin_check_requires_loaded_classes_and_staged_hashes(self):
        build = self.code("build.gradle.kts")
        self.assertIn('systemProperty("nativecmpkit.expected.$suffix.sha256", artifactSha256(staged))', build)
        code = (FIXTURE / "src/test/kotlin/nativecmpkit/consumer/PublishedArtifactOriginTest.kt").read_text()
        self.assertIn('type.protectionDomain.codeSource?.location', code)
        self.assertIn('Files.isRegularFile(jar)', code)
        self.assertIn('hash.digest().joinToString', code)
        self.assertEqual(["runtimeLibraryClassesComeFromExactStagedDesktopJars"], re.findall(r"@Test\s+fun\s+(\w+)", code))

    def test_partial_stage_adapter_does_not_change_the_full_producer_or_remote_guards(self):
        init = (ROOT / "scripts/ci/stage-core-io.init.gradle.kts").read_text()
        self.assertIn('listOf(root.project(":calf-core"), root.project(":calf-io"))', init)
        self.assertIn('check(selected.size == 4)', init)
        self.assertIn('url.scheme == "file" && url.authority.isNullOrEmpty()', init)
        self.assertIn('stageCoreIoVerificationPublications', init)
        root = (ROOT / "build.gradle.kts").read_text()
        self.assertIn('dependsOn(subprojects.flatMap', root)
        self.assertIn('Local verification mode forbids ALL remote/arbitrary-repository publication', root)

    def test_partial_stage_adapter_requires_an_explicit_absolute_canonical_root_binding(self):
        init = (ROOT / "scripts/ci/stage-core-io.init.gradle.kts").read_text()
        self.assertIn('System.getProperty("nativecmpkit.partialStagingRoot")', init)
        self.assertIn('check(stagingRootFile.isAbsolute && stagingRootFile.isDirectory)', init)
        self.assertIn('val stagingRoot = stagingRootFile.canonicalFile', init)

    def test_included_builds_return_before_any_verification_flag_or_library_lookup(self):
        init = (ROOT / "scripts/ci/stage-core-io.init.gradle.kts").read_text()
        guard = 'if (root.projectDir.canonicalFile != stagingRoot) return@projectsEvaluated'
        self.assertIn(guard, init)
        self.assertLess(init.index(guard), init.index('root.providers.gradleProperty("nativecmpkitVerification")'))
        self.assertLess(init.index(guard), init.index('root.project(":calf-core")'))
        self.assertIn('check(root.name == "nativeCmpkit")', init)

    def test_java_types_are_imported_instead_of_resolved_through_a_java_extension_receiver(self):
        for path in (FIXTURE / "build.gradle.kts", ROOT / "tests/consumer/build.gradle.kts"):
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                source = path.read_text()
                self.assertIn("import java.io.File", source)
                self.assertIn("import java.security.MessageDigest", source)
                self.assertIn("fun artifactSha256(file: File): String", source)
                self.assertIn('val digest = MessageDigest.getInstance("SHA-256")', source)
                self.assertNotIn("val digest = java.security.", source)
        self.assertIn("val candidateRepository = File(", self.code("build.gradle.kts"))

    def test_metadata_to_maven_binding_is_identical_in_partial_and_full_fixtures(self):
        sources = [(FIXTURE / 'build.gradle.kts').read_text(), (ROOT / 'tests/consumer/build.gradle.kts').read_text()]
        helpers = [source.split('fun bindCandidateArtifact(', 1)[1].split('\n}\n', 1)[0] for source in sources]
        self.assertEqual(helpers[0], helpers[1])
        for expression in ('declared["name"] == resolved.name', 'declared["url"] == canonicalName',
                           '"staged_file" to stagedRelative', '"metadata_sha256" to artifactSha256(metadataFile)',
                           'artifactSha256(staged) == hash', 'primaryBindings.size == 1'):
            self.assertIn(expression, helpers[0])

    def test_partial_resolution_and_loaded_class_names_follow_actual_declared_metadata(self):
        build = self.code('build.gradle.kts')
        self.assertIn('"schema_version" to 2', build)
        self.assertIn('bindCandidateArtifact(id, artifact.file)', build)
        self.assertIn('val expectedName = binding.getValue("declared_file_name") as String', build)
        self.assertIn('candidateRepository.resolve(binding.getValue("staged_file") as String)', build)
        self.assertIn('systemProperty("nativecmpkit.expected.$suffix.name", expectedName)', build)
        self.assertNotIn('check(artifact.file.name == expectedName)', build)
