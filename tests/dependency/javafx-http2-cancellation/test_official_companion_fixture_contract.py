"""NEW source obligations only: ZERO Gradle, Kotlin compiler or native execution."""
import ast
import hashlib
import json
from pathlib import Path
import re
import unittest

import stage_private_web as stage


class OfficialCompanionFixtureSourceControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = stage.HERE.parents[2]
        fixture = root / "tests/consumer/javafx-ordinary-webview"
        cls.build = (fixture / "build.gradle.kts").read_text()
        cls.native = (fixture / "src/test/kotlin/nativecmpkit/consumer/OrdinaryCuredWebStopConsumerTest.kt").read_text()
        cls.stager = (stage.HERE / "stage_private_web.py").read_text()
        cls.resolver = (stage.HERE / "private_web_resolution.py").read_text()
        cls.doc = (root / "docs/testing/javafx-private-maven-adoption.md").read_text()
        cls.supplement = (stage.HERE / "official-companion-supplement.json").read_bytes()

    def test_new_Gradle_consumes_fixed_owning_source_documents_from_same_hashed_bytes_not_caller_report_pins(self):
        for sha in (stage.OFFICIAL_ORIGINAL_PINS_SHA256, hashlib.sha256(self.supplement).hexdigest()):
            self.assertIn('"' + sha + '"', self.build)
        body = self.build[self.build.index('fun trustedCompanionPins()'):self.build.index('fun bindLibrary(')]
        for literal in ('projectDir.parentFile.parentFile.parentFile.resolve("tests/dependency/javafx-http2-cancellation")',
                        'document("artifacts.json", officialOriginalPinsSha256)',
                        'document("official-companion-supplement.json", officialCompanionSupplementSha256)',
                        'MessageDigest.getInstance("SHA-256").digest(payload)',
                        'JsonSlurper().parseText(payload.toString(Charsets.UTF_8))',
                        'Trusted official companion pin missing', 'result[classifiedFile]', 'result[genericFile]'):
            self.assertIn(literal, body)
        for forbidden in ('stageReport[', 'providers.gradleProperty(', 'JsonSlurper().parse(file)'):
            self.assertNotIn(forbidden, body)

    def test_new_real_four_classpath_admission_checks_official_length_digest_and_rechecks_inputs(self):
        body = self.build[self.build.index('fun observedResolution()'):self.build.index('val observePrivateWebResolution =')]
        for literal in ('val officialPins = trustedCompanionPins()', 'classpaths.forEach { name ->',
                        'configurations.getByName(name).incoming.artifacts.artifacts.forEach',
                        'val pin = officialPins[file.name]', 'file.length() == pin.bytes && hash == pin.sha256',
                        'check(trustedCompanionPins() == officialPins)',
                        'Actual admitted artifact changed during resolution observation'):
            self.assertIn(literal, body)
        admission = body.index('file.length() == pin.bytes && hash == pin.sha256')
        self.assertLess(admission, body.index('result += mapOf'))
        self.assertIn('check(cured == 1 && libraries == 1 && providers == 1 && classifiedCompanions == companions)', body)
        self.assertIn('filter { it["configuration"] == "testRuntimeClasspath" }', self.build)

    def test_new_five_loaded_public_companion_origins_match_each_exact_admitted_artifact_before_native_and_after_disposal(self):
        for type_name, module in (('SimpleStringProperty', 'base'), ('Scene', 'graphics'), ('Control', 'controls'), ('Media', 'media'), ('JFXPanel', 'swing')):
            self.assertIn(f'assertLoadedCompanionJar({type_name}::class.java, "{module}")', self.native)
        self.assertEqual(self.native.count('assertLoadedCompanionJars() //'), 2)
        self.assertLess(self.native.index('assertLoadedCompanionJars() // Actual'), self.native.index('assertTrue(isDesktopWebViewAvailable())'))
        self.assertLess(self.native.index('frame.dispose(); assertFalse(frame.isDisplayable)'), self.native.index('assertLoadedCompanionJars() // Hold'))
        for literal in ('val file = assertLoadedJar(type, suffix)', 'assertEquals(bytes, Files.size(file)',
                        'assertEquals(admitted, file.toRealPath()', 'type.protectionDomain.codeSource?.location',
                        '"nativecmpkit.expected.javafx.$companion.name", pin.file',
                        '"nativecmpkit.expected.javafx.$companion.bytes", pin.bytes.toString()',
                        '"nativecmpkit.expected.javafx.$companion.sha256", pin.sha256',
                        '"nativecmpkit.expected.javafx.$companion.path", artifact.getValue("path")'):
            self.assertIn(literal, self.native + self.build)

    def test_new_public_verifier_never_accepts_model_pins_and_models_never_claim_official_or_native_acceptance(self):
        tree = ast.parse(self.resolver)
        public = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'verify_private_resolution')
        self.assertEqual([argument.arg for argument in public.args.args], ['stage_report', 'resolution', 'repository'])
        self.assertFalse(public.args.kwonlyargs)
        self.assertFalse(public.args.kwarg)
        self.assertIn('stage.need(not production or model_companion_pins is None', self.resolver)
        self.assertIn('expected_companion_pins = contract.companion_pins[target]', self.resolver)
        self.assertIn('"official_companion_pins_bound": production', self.resolver)
        self.assertIn('"synthetic_companion_pin_checks": not production', self.resolver)
        self.assertIn('"ordinary_resolution_bytes_bound": production', self.resolver)
        for forbidden in ('stage_report.get("companion_pins")', 'resolution.get("official_companion_pins")'):
            self.assertNotIn(forbidden, self.resolver)

    def test_new_companion_source_supplement_preserves_original_candidate_input_contract_and_private_identity(self):
        self.assertIn('originals = {target: [pins["sources"], *pins["platforms"][target]] for target in CLASSIFIERS}', self.stager)
        self.assertIn('expected = contract.owners | {row["file"]: row["sha256"] for row in original_pins}', self.stager)
        self.assertNotIn('companion_pins', self.stager[self.stager.index('def inspect_candidate('):self.stager.index('def metadata(')])
        self.assertEqual(json.loads(self.supplement)['version'], stage.UPSTREAM)
        self.assertEqual(stage.GROUP, 'nativecmpkit.private.javafx')
        self.assertEqual(stage.VERSION, '21.0.13-nativecmpkit-cancel1-local')
        self.assertNotIn('publish(', self.stager + self.resolver + self.build)

    def test_new_documentation_distinguishes_integrity_source_native_and_immutable_original_cohorts(self):
        for literal in ('Original51', '80 admissible tamper', 'No raw JAR or sidecar',
                        'successful JSON', 'not an invented shell receipt',
                        'Both hashed documents are parsed from those same captured bytes',
                        'not signing, archive safety', 'All five actual',
                        'neither these Kotlin assertions nor their native execution is proved by source',
                        'resolution/staging JSON and caller properties cannot inject replacements',
                        '14 original/owning files'):
            self.assertIn(literal, self.doc)


if __name__ == '__main__':
    unittest.main()
