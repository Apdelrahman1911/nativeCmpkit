"""Synthetic dependency-key fixtures, not Actions cache/build/trust verification."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import dependency_cache_inputs as d


class DependencyCacheInputTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='nativecmpkit-dependency-key-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.write('settings.gradle.kts', 'include(\n ":calf-core", ":calf-io", ":sample:desktop",\n)\n')
        for name in ('calf-core/build.gradle.kts', 'calf-io/build.gradle.kts', 'sample/desktop/build.gradle.kts',
                     'build.gradle.kts', 'gradle.properties', 'gradle/libs.versions.toml',
                     'gradle/wrapper/gradle-wrapper.properties', 'gradle/wrapper/gradle-wrapper.jar',
                     'convention-plugins/build.gradle.kts', 'convention-plugins/settings.gradle.kts',
                     'convention-plugins/src/main/kotlin/dependencies.kt', 'calf-io/native/Cargo.toml',
                     'calf-io/native/Cargo.lock', 'kotlin-js-store/yarn.lock', 'rust-toolchain.toml',
                     'tests/consumer/build.gradle.kts', 'tests/consumer/io-desktop/build.gradle.kts', *d.RECIPE_FILES):
            self.write(name, 'synthetic-config-not-executed-' + name)

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def key(self, scope='libraries'):
        return d.fingerprint(scope, d.selected_inputs(self.root, scope))

    def test_source_geo_probe_configurations_change_the_library_dependency_key_not_its_test_outputs(self):
        before = self.key()
        self.write('tests/consumer/android-geo-probe/build.gradle.kts', 'synthetic-source-consumer-dependencies')
        self.assertNotEqual(before, self.key())
        held = self.key()
        self.write('tests/consumer/android-geo-probe/build/test-results/old.xml', 'not-fresh-evidence')
        self.assertEqual(held, self.key())
        self.assertIn('tests/consumer/android-geo-probe/build.gradle.kts', d.selected_inputs(self.root, 'libraries'))

    def test_native_share_recipient_configurations_are_keyed_but_private_signing_apks_and_xml_are_not(self):
        before = self.key()
        self.write('tests/consumer/android-share-recipient/build.gradle.kts', 'synthetic-recipient-config')
        self.assertNotEqual(before, self.key())
        held = self.key()
        for name in ('build/outputs/apk/debug/old.apk', 'build/test-results/old.xml', 'build/android-user/debug.keystore'):
            self.write('tests/consumer/android-share-recipient/' + name, 'not-a-cache-input')
        self.assertEqual(held, self.key())
        self.assertIn('tests/consumer/android-share-recipient/build.gradle.kts', d.selected_inputs(self.root, 'libraries'))
        self.write('tests/consumer/android-share-documents/build.gradle.kts', 'synthetic-third-UID-config')
        self.assertNotEqual(held, self.key())
        self.assertIn('tests/consumer/android-share-documents/build.gradle.kts', d.selected_inputs(self.root, 'libraries'))

    def test_repeat_keys_are_exact_content_bound_and_include_all_configured_builds(self):
        values = d.selected_inputs(self.root, 'libraries')
        self.assertIn('calf-core/build.gradle.kts', values)
        self.assertIn('calf-io/build.gradle.kts', values)
        self.assertIn('sample/desktop/build.gradle.kts', values)
        self.assertEqual(self.key(), self.key())
        self.assertEqual(64, len(self.key()))

    def test_dependency_toolchain_recipe_or_plugin_changes_invalidate_the_key(self):
        paths = d.selected_inputs(self.root, 'libraries')
        for relative in paths:
            with self.subTest(path=relative):
                old = (self.root / relative).read_text()
                before = self.key()
                (self.root / relative).write_text(old + '\n// synthetic change\n')
                self.assertNotEqual(before, self.key())
                (self.root / relative).write_text(old)

    def test_source_test_docs_archives_and_build_outputs_do_not_make_cache_misses(self):
        before = self.key()
        for name in ('calf-core/src/commonMain/source.kt', 'calf-io/src/desktopTest/test.kt', 'AGENTS.md',
                     'docs/development/evidence/old/build.gradle.kts', 'docs/migration/upstream-metadata/archive.json',
                     'convention-plugins/build/old.kt', 'calf-io/build/gradle.properties',
                     'build/verification-repo/candidate.jar', 'calf-media/build.gradle.kts'):
            self.write(name, 'synthetic-irrelevant-to-dependency-declarations')
        self.assertEqual(before, self.key())

    def test_new_or_modified_active_lock_or_native_config_invalidates_the_key(self):
        for name in ('calf-core/gradle.lockfile', 'gradle/verification-metadata.xml', 'calf-io/native/.cargo/config.toml',
                     '.cargo/config.toml', 'calf-io/native/build.rs', 'sample/desktop/gradle.properties'):
            with self.subTest(path=name):
                before = self.key()
                self.write(name, 'synthetic-new-config')
                self.assertNotEqual(before, self.key())

    def test_core_io_scope_adds_independent_consumer_and_exact_staging_recipes(self):
        library = self.key()
        consumer = self.key('core-io')
        self.assertNotEqual(library, consumer)
        self.write('tests/consumer/io-desktop/build.gradle.kts', 'synthetic-standalone-build-change')
        self.assertEqual(library, self.key())
        self.assertNotEqual(consumer, self.key('core-io'))
        for name in ('scripts/ci/stage-core-io.init.gradle.kts', 'scripts/ci/core_io_consumer.py'):
            before = self.key('core-io')
            self.write(name, 'synthetic-owning-recipe-change')
            self.assertNotEqual(before, self.key('core-io'))

    def test_added_configured_project_is_bound_and_missing_project_fails(self):
        before = self.key()
        self.write('settings.gradle.kts', 'include(\n ":calf-core", ":calf-io", ":calf-ui", ":sample:desktop",\n)\n')
        with self.assertRaises(ValueError): self.key()
        self.write('calf-ui/build.gradle.kts', 'synthetic-new-project')
        self.assertNotEqual(before, self.key())
        self.assertIn('calf-ui/build.gradle.kts', d.selected_inputs(self.root, 'libraries'))

    def test_unknown_scope_or_changed_include_syntax_does_not_guess_a_key(self):
        with self.assertRaises(ValueError): self.key('unreviewed')
        self.write('settings.gradle.kts', 'include(computedProject())')
        with self.assertRaises(ValueError): self.key()

    def test_selected_symlinks_hardlinks_and_oversized_inputs_are_rejected(self):
        source = self.root / 'gradle/libs.versions.toml'
        saved = source.read_bytes()
        outside = self.write('outside.toml', 'synthetic-link-source')
        source.unlink(); source.symlink_to(outside)
        with self.assertRaises(ValueError): self.key()
        source.unlink(); os.link(outside, source)
        with self.assertRaises(ValueError): self.key()
        source.unlink(); source.write_bytes(saved)
        with patch.object(d, 'MAX_INPUT_BYTES', 1), self.assertRaises(ValueError): self.key()

    def test_key_is_independent_of_commit_sha_and_root_directory(self):
        values = d.selected_inputs(self.root, 'libraries')
        with patch.object(d.lt, 'git_revision', side_effect=AssertionError('Revision must not enter the cache content key')):
            self.assertEqual(self.key(), d.fingerprint('libraries', values))


if __name__ == '__main__':
    unittest.main()
