"""NEW source-contract controls, ZERO Kotlin/compiler/Gradle/native execution."""
from pathlib import Path
import re
import unittest

import stage_private_web as stage

FIXTURE = stage.HERE.parents[2] / "tests/consumer/javafx-ordinary-webview"


class OrdinaryConsumerFixtureSourceControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = (FIXTURE / "build.gradle.kts").read_text(encoding="utf-8")
        cls.settings = (FIXTURE / "settings.gradle.kts").read_text(encoding="utf-8")
        cls.native = (FIXTURE / "src/test/kotlin/nativecmpkit/consumer/OrdinaryCuredWebStopConsumerTest.kt").read_text(encoding="utf-8")
        cls.doc = (stage.HERE.parents[2] / "docs/testing/javafx-private-maven-adoption.md").read_text(encoding="utf-8")

    def test_new_fixture_selects_only_web_from_private_normal_Maven_and_five_aligned_companions(self):
        for literal in (stage.GROUP, stage.VERSION, stage.UPSTREAM):
            self.assertIn('"' + literal + '"', self.build)
        modules = re.search(r'val companions = setOf\(([^\n]+)\)', self.build).group(1)
        self.assertEqual(set(re.findall(r'"([^\"]+)"', modules)), set(stage.COMPANIONS))
        self.assertIn('implementation("$privateGroup:$privateModule:$privateVersion")', self.build)
        self.assertIn('implementation("org.openjfx:javafx-$it:$javafxVersion:$classifier")', self.build)
        self.assertNotIn('implementation("org.openjfx:javafx-web:', self.build)

    def test_new_fixture_exclusive_routing_and_all_init_composite_project_denials_are_literal(self):
        self.assertEqual(self.settings.count('exclusiveContent {'), 2)
        self.assertIn('includeGroup("nativecmpkit.private.javafx")', self.settings)
        self.assertIn('includeGroup("io.github.apdelrahman1911.nativecmpkit")', self.settings)
        self.assertIn('RepositoriesMode.FAIL_ON_PROJECT_REPOS', self.settings)
        self.assertIn('ignoreGradleMetadataRedirection()', self.settings)
        self.assertIn('gradle.startParameter.allInitScripts.isEmpty()', self.build)
        self.assertIn('gradle.includedBuilds.isEmpty()', self.build)
        self.assertIn('check(id is ModuleComponentIdentifier)', self.build)
        for forbidden in ('includeBuild(', 'dependencySubstitution {', 'implementation(project(', 'implementation(files('):
            self.assertNotIn(forbidden, self.settings + self.build)

    def test_new_actual_host_classifiers_and_Java17_Gradle_pins_are_finite_not_cross_native_inference(self):
        observed = set(re.findall(r'-> "(linux(?:-aarch64)?|mac(?:-aarch64)?|win)"', self.build))
        self.assertEqual(observed, set(stage.CLASSIFIERS))
        self.assertIn('require(classifier == actualClassifier)', self.build)
        self.assertIn('Unsupported ordinary consumer host/CPU; no classifier fallback', self.build)
        self.assertIn('kotlin("jvm") version "2.4.20"', self.build)
        self.assertIn('id("org.jetbrains.compose") version "1.12.0"', self.build)
        self.assertIn('jvmToolchain(17)', self.build)
        self.assertIn('gradle.gradleVersion == "9.7.1" && JavaVersion.current().majorVersion == "17"', self.build)

    def test_new_real_artifact_observer_requires_all_four_exact_classpaths_and_one_provider(self):
        literal = re.search(r'val classpaths = listOf\(([^\n]+)\)', self.build).group(1)
        self.assertEqual(re.findall(r'"([^\"]+)"', literal), ['compileClasspath', 'runtimeClasspath', 'testCompileClasspath', 'testRuntimeClasspath'])
        self.assertIn('configuration', self.build)
        self.assertIn('"path" to file.absolutePath', self.build)
        self.assertIn('"bytes" to file.length(), "sha256" to hash', self.build)
        self.assertIn('check(cured == 1 && libraries == 1 && providers == 1 && classifiedCompanions == companions)', self.build)
        self.assertIn('id.module.removePrefix("javafx-") in companions', self.build)
        self.assertIn('file.length() == privateWeb.length() && hash == sha256(privateWeb)', self.build)
        self.assertIn('sha256(staged) == sha256(resolved)', self.build)

    def test_new_exact_one_NEW_public_method_and_no_old_native_or_sample_cohort_is_selected(self):
        methods = re.findall(r'@Test fun ([A-Za-z0-9_]+)\(', self.native)
        self.assertEqual(methods, ['normalMavenActivationBindsCuredPublicStopTransportAndOwnedLifetime'])
        self.assertIn('tasks.named<Test>("test") { enabled = false }', self.build)
        self.assertIn('tasks.register<Test>("ordinaryCuredWebStop")', self.build)
        self.assertIn('OrdinaryCuredWebStopConsumerTest.' + methods[0], self.build)
        self.assertIn('isFailOnNoMatchingTests = true', self.build)
        for forbidden in ('DesktopWebViewStopRedirectAcceptanceTest', 'PublishedWebViewConsumerTest', 'Assume.', 'assumeTrue(', 'samples/'):
            self.assertNotIn(forbidden, self.build + self.native)

    def test_new_public_Stop_ten_second_six_predicate_and_precleanup_EOF_semantics_are_held(self):
        self.assertIn('navigator.stopLoading()', self.native)
        anchor = self.native.index('awaitNative("public Stop and real pre-response peer EOF before cleanup")')
        body = self.native[anchor:self.native.index('assertFalse(server.closing.get())', anchor)]
        for predicate in ('native.engine.loadWorker.state == Worker.State.CANCELLED', '!native.engine.loadWorker.isRunning',
                          'state.loadingState == LoadingState.Finished', 'cancellations.get() == 1',
                          'server.peerEofs.get() == 1', 'server.pending.get() == 0'):
            self.assertIn(predicate, body)
        self.assertIn('seconds: Long = 10', self.native)
        self.assertIn('task.get(remaining, TimeUnit.NANOSECONDS)', self.native)
        self.assertIn('assertTrue(System.nanoTime() <= deadline', self.native)
        self.assertIn('if (value == -1) { peerEofs.incrementAndGet(); return }', self.native)
        self.assertIn('if (socket === heldSocket.get()) responses.incrementAndGet()', self.native)
        for forbidden in ('engine.load(', 'engine.loadWorker.cancel(', 'getDeclaredField(', 'fwkCancel(', 'Platform.exit(', 'System.exit('):
            self.assertNotIn(forbidden, self.native)

    def test_new_loaded_jar_resource_binding_and_owned_lifecycle_cleanup_are_explicit_not_json_only(self):
        for literal in ('assertLoadedJar(WebViewState::class.java, "webview")', 'assertLoadedJar(WebEngine::class.java, "javafx")',
                        'Path.of(loaderConnection.jarFileURL.toURI())', 'loaderConnection.useCaches = false',
                        'readNBytes(256 * 1024 + 1)', 'assertSame(native, state.webView)', 'embedding.scene == null',
                        'cleanup(primary,', 'task.cancel(false)', 'serverRef?.close()', 'scope.cancel()',
                        'removeListener(observer)', 'acceptor.join(5000)', 'workers.isTerminated && pending.get() == 0'):
            self.assertIn(literal, self.native)
        self.assertLess(self.native.index('attempt { acceptor.join(5000)'), self.native.index('sockets.toList().forEach'))
        self.assertIn('catch (error: Throwable)', self.native)
        self.assertIn('error.addSuppressed(cleanup)', self.native)
        self.assertIn('NativeCmpKit-Publication-Ready: false', stage.builder.CANDIDATE_MANIFEST.decode())
        self.assertIn('stageReport["production_contract"] == true', self.build)
        self.assertIn('stageReport["full_native_corresponding_source_complete"] == false', self.build)

    def test_new_documentation_preserves_unpublished_incomplete_source_and_remaining_actual_execution_gates(self):
        for literal in ('No real JAR', 'Default consumer-facing adoption is still incomplete', 'not** complete preferred corresponding source',
                        'No blanket legal', 'All five actual', 'same captured bytes', '14 original/owning files', 'Original `org.openjfx:javafx-web`'):
            self.assertIn(literal, self.doc)
        self.assertIn(stage.GROUP + ':javafx-web-<classifier>:' + stage.VERSION, self.doc)
        self.assertIn('explicitly reuse that one native result', self.doc)
        self.assertIn('not a public installation recommendation', self.doc)


if __name__ == '__main__':
    unittest.main()
