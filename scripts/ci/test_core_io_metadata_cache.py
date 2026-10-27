"""Adversarial metadata/cache fences; synthetic Python tests, not consumer runs."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import core_io_consumer as c


class MetadataAndCacheTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-consumer-binding-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repository = self.root / c.REPOSITORY
        self.metadata = {}
        for module in c.ROOTS:
            for suffix in ("", "-desktop"):
                coordinate = module + suffix
                directory = self.repository / c.GROUP.replace('.', '/') / coordinate / c.VERSION
                directory.mkdir(parents=True)
                payload = b"synthetic-inert-not-a-library-" + coordinate.encode()
                primary = coordinate + '-' + c.VERSION + '.jar'
                (directory / primary).write_bytes(payload)
                component = {"group": c.GROUP, "module": module, "version": c.VERSION}
                if suffix:
                    component['url'] = f'../../{module}/{c.VERSION}/{module}-{c.VERSION}.module'
                entry = {"name": coordinate.replace('nativecmpkit-', 'calf-', 1) + '-' + c.VERSION + '.jar',
                         "url": primary, "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
                variants = [{"name": name, "attributes": {"org.gradle.category": "library",
                             "org.gradle.libraryelements": "jar", "org.gradle.usage": usage,
                             "org.jetbrains.kotlin.platform.type": "jvm"}, "files": [deepcopy(entry)]}
                            for name, usage in (("desktopApiElements-published", "java-api"),
                                                ("desktopRuntimeElements-published", "java-runtime"))]
                value = {"formatVersion": "1.1", "component": component, "variants": variants}
                path = directory / (coordinate + '-' + c.VERSION + '.module')
                path.write_text(json.dumps(value))
                if suffix:
                    self.metadata[coordinate] = (path, value)

    def bindings(self):
        return c.module_file_bindings(self.repository, c.staged_inputs(self.repository))

    def resolution(self, bindings):
        rows = [{"configuration": configuration, "group": c.GROUP, "module": module,
                 "version": c.VERSION, "file": value['declared_file_name'], **value}
                for configuration in sorted(c.CLASSPATHS) for module, value in sorted(bindings.items())]
        return {"schema_version": 2, "scope": "PARTIAL Core/IO desktop Maven consumer",
                "candidate_group": c.GROUP, "candidate_version": c.VERSION,
                "publication_roots_requested": list(c.ROOTS), "candidate_variants_resolved": sorted(bindings),
                "complete_21_root_KMP_matrix_requested": False, "release_readiness_certified": False,
                "resolved_artifacts": rows}

    def change(self, key, value):
        path, document = self.metadata[c.ROOTS[0] + '-desktop']
        for variant in document['variants']:
            variant['files'][0][key] = value
        path.write_text(json.dumps(document))

    def jdk(self):
        jdk = self.root / 'jdk'
        (jdk / 'bin').mkdir(parents=True)
        (jdk / 'bin/java').write_bytes(b'inert-jdk-path-selection-only')
        return jdk

    def test_cached_display_name_binds_to_canonical_maven_url_and_exact_bytes(self):
        values = self.bindings()
        staged = c.staged_inputs(self.repository)
        self.assertEqual({module + '-desktop' for module in c.ROOTS}, set(values))
        for module, value in values.items():
            self.assertTrue(value['declared_file_name'].startswith('calf-'))
            self.assertTrue(value['declared_file_url'].startswith('nativecmpkit-'))
            self.assertEqual(staged[value['staged_file']], {key: value[key] for key in ('bytes', 'sha256')})
            self.assertEqual(staged[value['metadata_file']]['sha256'], value['metadata_sha256'])
        result = c.resolution_contract(self.resolution(values), staged, values)
        self.assertEqual(4, result['classpath_count'])
        self.assertEqual(8, len(result['candidate_artifact_rows']))

    def test_canonical_display_name_is_accepted_only_when_actually_declared(self):
        for coordinate, (path, document) in self.metadata.items():
            for variant in document['variants']:
                variant['files'][0]['name'] = coordinate + '-' + c.VERSION + '.jar'
            path.write_text(json.dumps(document))
        values = self.bindings()
        c.resolution_contract(self.resolution(values), c.staged_inputs(self.repository), values)

    def test_arbitrary_old_group_or_unrelated_display_aliases_are_rejected(self):
        for name in ('unrelated.jar', 'calf-share-desktop-' + c.VERSION + '.jar',
                     'nativecmpkit-core-desktop-' + c.VERSION + '-sources.jar', '../escape.jar', 'C:\\escape.jar'):
            with self.subTest(name=name):
                self.change('name', name)
                with self.assertRaises(c.ConsumerEvidenceError): self.bindings()

    def test_url_must_be_the_exact_same_coordinate_primary_filename(self):
        for url in ('../escape.jar', 'file:///escape.jar', 'https://example.invalid/a.jar',
                    'nativecmpkit-io-desktop-' + c.VERSION + '.jar',
                    'nativecmpkit-core-desktop-' + c.VERSION + '.jar?anything=1'):
            with self.subTest(url=url):
                self.change('url', url)
                with self.assertRaises(c.ConsumerEvidenceError): self.bindings()

    def test_metadata_checksum_size_and_type_must_match_staged_bytes(self):
        for key, value in (('size', True), ('size', 0), ('size', 9999), ('sha256', 'f' * 64), ('sha256', None)):
            with self.subTest(key=key, value=value):
                path, original = self.metadata[c.ROOTS[0] + '-desktop']
                saved = deepcopy(original)
                self.change(key, value)
                with self.assertRaises(c.ConsumerEvidenceError): self.bindings()
                self.metadata[c.ROOTS[0] + '-desktop'] = (path, saved)
                path.write_text(json.dumps(saved))

    def test_metadata_identity_and_root_redirect_cannot_change(self):
        path, original = self.metadata[c.ROOTS[0] + '-desktop']
        for key, value in (('group', 'com.mohamedrejeb.calf'), ('module', 'nativecmpkit-io'),
                           ('version', '0.1.0-preview.2'), ('url', '../../elsewhere.module')):
            with self.subTest(key=key):
                changed = deepcopy(original)
                changed['component'][key] = value
                path.write_text(json.dumps(changed))
                with self.assertRaises(c.ConsumerEvidenceError): self.bindings()
        path.write_text(json.dumps(original))

    def test_missing_module_metadata_or_root_redirect_target_is_not_a_fallback(self):
        path, _ = self.metadata[c.ROOTS[0] + '-desktop']
        saved = path.read_bytes()
        path.unlink()
        with self.assertRaises(c.ConsumerEvidenceError): self.bindings()
        path.write_bytes(saved)
        root = path.parent.parent.parent / c.ROOTS[0] / c.VERSION / (c.ROOTS[0] + '-' + c.VERSION + '.module')
        root.unlink()
        with self.assertRaises(c.ConsumerEvidenceError): self.bindings()

    def test_conflicting_or_missing_api_runtime_primary_entries_fail(self):
        path, original = self.metadata[c.ROOTS[0] + '-desktop']
        for modification in ('conflict', 'missing', 'extra'):
            with self.subTest(modification=modification):
                changed = deepcopy(original)
                if modification == 'conflict':
                    changed['variants'][0]['files'][0]['name'] = 'nativecmpkit-core-desktop-' + c.VERSION + '.jar'
                elif modification == 'missing':
                    changed['variants'].pop()
                else:
                    changed['variants'][0]['files'].append(deepcopy(changed['variants'][0]['files'][0]))
                path.write_text(json.dumps(changed))
                with self.assertRaises(c.ConsumerEvidenceError): self.bindings()
        path.write_text(json.dumps(original))

    def test_read_metadata_must_match_the_previously_held_staging_hash(self):
        staged = c.staged_inputs(self.repository)
        path, original = self.metadata[c.ROOTS[0] + '-desktop']
        path.write_text(json.dumps(original) + '\n')
        with self.assertRaises(c.ConsumerEvidenceError): c.module_file_bindings(self.repository, staged)

    def test_duplicate_json_key_and_nonfinite_number_are_not_accepted(self):
        path, _ = self.metadata[c.ROOTS[0] + '-desktop']
        for payload in ('{"formatVersion":"1.1","formatVersion":"1.1"}', '{"invalid":NaN}'):
            with self.subTest(payload=payload):
                path.write_text(payload)
                with self.assertRaises(c.ConsumerEvidenceError): self.bindings()

    def test_resolution_cannot_use_the_other_known_name_or_switch_metadata_paths(self):
        values = self.bindings()
        good = self.resolution(values)
        changes = [('file', 'nativecmpkit-core-desktop-' + c.VERSION + '.jar'),
                   ('declared_file_name', 'nativecmpkit-core-desktop-' + c.VERSION + '.jar'),
                   ('declared_file_url', '../escape.jar'), ('staged_file', '../escape.jar'),
                   ('metadata_file', values[c.ROOTS[1] + '-desktop']['metadata_file']), ('metadata_sha256', 'f' * 64)]
        for key, value in changes:
            with self.subTest(key=key):
                changed = deepcopy(good)
                changed['resolved_artifacts'][0][key] = value
                with self.assertRaises(c.ConsumerEvidenceError):
                    c.resolution_contract(changed, c.staged_inputs(self.repository), values)

    def test_resolution_bindings_and_metadata_inventory_must_be_complete(self):
        values = self.bindings()
        incomplete = dict(values)
        incomplete.pop(c.ROOTS[0] + '-desktop')
        with self.assertRaises(c.ConsumerEvidenceError):
            c.resolution_contract(self.resolution(values), c.staged_inputs(self.repository), incomplete)

    def test_child_gradle_home_is_fresh_confined_and_not_the_cached_producer_home(self):
        jdk = self.jdk()
        output = self.root / 'evidence'
        with patch.dict(os.environ, {'JAVA_HOME': str(jdk)}, clear=True):
            producer = c.environment(self.root, output)
            child = c.environment(self.root, output, consumer=True)
        self.assertEqual(str(self.root / c.GRADLE_HOME), producer['GRADLE_USER_HOME'])
        self.assertEqual(str(output / 'consumer-gradle-home'), child['GRADLE_USER_HOME'])
        self.assertNotEqual(producer['HOME'], child['HOME'])
        self.assertNotEqual(producer['TMPDIR'], child['TMPDIR'])
        self.assertNotIn('GRADLE_RO_DEP_CACHE', child)
        self.assertFalse(Path(child['GRADLE_USER_HOME']).is_relative_to(self.root / c.GRADLE_HOME))

    def test_preexisting_consumer_home_is_preserved_but_refused(self):
        jdk = self.jdk()
        output = self.root / 'evidence'
        sentinel = output / 'consumer-gradle-home/foreign.bin'
        sentinel.parent.mkdir(parents=True)
        sentinel.write_bytes(b'synthetic-foreign-do-not-delete')
        with patch.dict(os.environ, {'JAVA_HOME': str(jdk)}, clear=True), self.assertRaises(c.ConsumerEvidenceError):
            c.environment(self.root, output, consumer=True)
        self.assertEqual(b'synthetic-foreign-do-not-delete', sentinel.read_bytes())

    def test_candidate_payload_group_in_producer_cache_is_detected_without_deletion(self):
        home = self.root / c.GRADLE_HOME
        file = home / 'caches/modules-2/files-2.1' / c.GROUP / 'nativecmpkit-core-desktop/foreign.jar'
        file.parent.mkdir(parents=True)
        file.write_bytes(b'synthetic-unverified-candidate')
        result = c.producer_cache_state(self.root)
        self.assertIs(result['candidate_payload_group_absent'], False)
        self.assertEqual(b'synthetic-unverified-candidate', file.read_bytes())
        jdk = self.jdk()
        with patch.dict(os.environ, {'JAVA_HOME': str(jdk)}, clear=True), self.assertRaises(c.ConsumerEvidenceError):
            c.environment(self.root, self.root / 'evidence')

    def test_candidate_metadata_group_or_symlink_in_cached_home_is_rejected(self):
        home = self.root / c.GRADLE_HOME
        path = home / 'caches/modules-2/metadata-2.107/descriptors' / c.GROUP
        path.mkdir(parents=True)
        self.assertIs(c.producer_cache_state(self.root)['candidate_payload_group_absent'], False)
        path.rmdir()
        path.symlink_to(self.repository)
        with self.assertRaises(ValueError): c.producer_cache_state(self.root)

    def test_unrelated_third_party_cache_remains_available_and_unmodified(self):
        cache = self.root / c.GRADLE_HOME / 'caches/modules-2/files-2.1/org.example/fixture.bin'
        cache.parent.mkdir(parents=True)
        cache.write_bytes(b'synthetic-third-party-cache-not-trusted')
        before = cache.stat()
        result = c.producer_cache_state(self.root)
        self.assertIs(result['candidate_payload_group_absent'], True)
        self.assertEqual(before.st_ino, cache.stat().st_ino)
        self.assertEqual(b'synthetic-third-party-cache-not-trusted', cache.read_bytes())


if __name__ == '__main__':
    unittest.main()
