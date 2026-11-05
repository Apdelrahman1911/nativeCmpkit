# SPDX-License-Identifier: Apache-2.0
"""NEW pure/synthetic regression controls; not dependency or native approval.

Every digest here identifies unmistakably synthetic test bytes, not a publisher,
review, graph, package or source-recipe approval. Production authority stays None.
Only the pure NEW helper is imported. The controller and actual library_tests
safe_path are read as source: only four inert controller function definitions and
safe_path are AST-extracted. No main/run, historical tests, Gradle or network runs.

For an isolated source candidate lacking library_tests.py, the lead must specify
NATIVECMPKIT_EXPECTATION_SAFE_PATH_SOURCE_ROOT as the actual read-only source root.
All fixture XML/manifests/files are inside unittest-owned TemporaryDirectory only.
The binary-substitution control requires the separately proposed narrow follow-on
fragment; do not weaken its refusal or overwrite the sealed R1 helper silently.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock
import tempfile
import xml.etree.ElementTree as ET
import re

import javafx_ordinary_dependency_expectations as expectations

HERE = Path(__file__).resolve().parent
CONTROLLER_SOURCE = HERE / 'javafx_ordinary_maven_consumer.py'
SAFE_SOURCE_ROOT = Path(os.environ.get('NATIVECMPKIT_EXPECTATION_SAFE_PATH_SOURCE_ROOT', str(HERE.parents[1])))
SAFE_SOURCE = SAFE_SOURCE_ROOT / 'scripts/ci/library_tests.py'
EXTRACTED = ('need', 'read', 'dependency_metadata_preflight', 'dependency_expectations_preflight')
NS = '{https://schema.gradle.org/dependency-verification}'


def synthetic_digest(label):
    return hashlib.sha256(('SYNTHETIC-NOT-INDEPENDENT-REVIEW:' + label).encode()).hexdigest()


def encoded(document):
    return json.dumps(document, sort_keys=True, separators=(',', ':')).encode()


def sorted_rows(document):
    document['artifacts'].sort(key=lambda row: tuple(row[key] for key in ('root', 'group', 'module', 'version', 'name')))
    return document


def synthetic_manifest():
    """A complete schema fixture, NEVER the production reviewed manifest."""
    coverage = {'producer': {scope: synthetic_digest('producer:' + scope) for scope in expectations.PRODUCER_SCOPES},
                'consumer': {mode: {scope: synthetic_digest(mode + ':' + scope) for scope in expectations.CONSUMER_SCOPES}
                             for mode in expectations.MODES}}
    staging = {'library': {}, 'private': {}}
    rows = []
    classpaths = sorted(f'{mode}:{name}' for mode in expectations.MODES for name in expectations.CLASSPATHS)
    for kind, group, modules, version in (
            ('library', expectations.LIBRARY_GROUP, expectations.LIBRARY_MODULES, expectations.LIBRARY_VERSION),
            ('private', expectations.PRIVATE_GROUP, (expectations.PRIVATE_MODULE,), expectations.PRIVATE_VERSION)):
        for module in modules:
            suffixes = ('.pom', '.module', '.jar', '-sources.jar') if (
                kind == 'private' or module == 'nativecmpkit-webview-desktop') else ('.pom', '.module')
            for suffix in suffixes:
                name = f'{module}-{version}{suffix}'
                path = f'{group.replace(".", "/")}/{module}/{version}/{name}'
                identity = {'bytes': 17 + len(name), 'sha256': synthetic_digest(path)}
                staging[kind][path] = identity
                contexts = (['module:metadata'] if suffix == '.module' else ['pom:metadata'] if suffix == '.pom' else
                            classpaths if suffix == '.jar' else ['module:metadata', 'pom:metadata'])
                rows.append({'root': 'consumer', 'group': group, 'module': module, 'version': version, 'name': name,
                             **identity, 'contexts': contexts,
                             'provenance': {'kind': 'local-' + kind, 'path': path,
                                            'evidence_sha256': synthetic_digest('local-review:' + path)}})
    def external(root, group, module, version, name, contexts):
        rows.append({'root': root, 'group': group, 'module': module, 'version': version, 'name': name,
                     'bytes': 29 + len(name), 'sha256': synthetic_digest(name), 'contexts': sorted(contexts),
                     'provenance': {'kind': 'external', 'basis': 'reproducible-source-build',
                                    'url': f'https://repo.maven.apache.org/maven2/{group.replace(".", "/")}/{module}/{version}/{name}',
                                    'evidence_sha256': synthetic_digest('external-review:' + name)}})
    external('producer', 'fixture.synthetic', 'bootstrap', '1.0', 'bootstrap-1.0.jar', expectations.PRODUCER_SCOPES)
    external('consumer', 'fixture.synthetic', 'compiler', '1.0', 'compiler-1.0.jar',
             [f'{mode}:{scope}' for mode in expectations.MODES for scope in ('plugins', 'compiler', 'metadata')])
    for companion in expectations.COMPANIONS:
        module = 'javafx-' + companion
        external('consumer', 'org.openjfx', module, '21.0.13', module + '-21.0.13-win.jar', classpaths)
    return sorted_rows({'schema_version': 1, 'source_recipe_authority_sha256': expectations.SOURCE_RECIPE_AUTHORITY,
                        'review_basis_sha256': synthetic_digest('schema-fixture-only'), 'coverage': coverage,
                        'staging_inputs': staging, 'artifacts': rows})


class FixtureEvidenceError(ValueError):
    """Test-only packaged.EvidenceError stand-in; no packaged controller import."""


class WindowsDependencyExpectation742Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controller_bytes = CONTROLLER_SOURCE.read_bytes()
        cls.safe_bytes = SAFE_SOURCE.read_bytes()
        cls.controller_tree = ast.parse(cls.controller_bytes, filename=str(CONTROLLER_SOURCE))
        cls.safe_tree = ast.parse(cls.safe_bytes, filename=str(SAFE_SOURCE))
        cls.helper_path = Path(expectations.__file__)
        cls.helper_bytes = cls.helper_path.read_bytes()
        cls.nodes = {node.name: node for node in cls.controller_tree.body if isinstance(node, ast.FunctionDef)}
        assert set(EXTRACTED) <= set(cls.nodes), 'Exact inert controller definitions required'
        cls.safe_nodes = [node for node in cls.safe_tree.body if isinstance(node, ast.FunctionDef) and node.name == 'safe_path']
        assert len(cls.safe_nodes) == 1, 'Actual unique library_tests.safe_path required'

    def setUp(self):
        self.document = synthetic_manifest()
        self.payload = encoded(self.document)
        self.pin = hashlib.sha256(self.payload).hexdigest()  # Synthetic test-only pin, NEVER production trust.

    def tearDown(self):
        self.assertEqual(CONTROLLER_SOURCE.read_bytes(), self.controller_bytes)
        self.assertEqual(SAFE_SOURCE.read_bytes(), self.safe_bytes)
        self.assertEqual(self.helper_path.read_bytes(), self.helper_bytes)

    def refuse_manifest(self, document):
        payload = encoded(sorted_rows(document))
        with self.assertRaises(expectations.ExpectationError) as raised:
            expectations.parse_reviewed_manifest(payload, hashlib.sha256(payload).hexdigest())
        self.assertLessEqual(len(str(raised.exception)), 512)
        self.assertNotIn('SYNTHETIC-NOT-INDEPENDENT-REVIEW:', str(raised.exception))

    def namespace(self, root, pin=None):
        safe_namespace = {'Path': Path}
        safe_definitions = ast.Module(body=self.safe_nodes, type_ignores=[])
        exec(compile(safe_definitions, str(SAFE_SOURCE), 'exec'), safe_namespace)
        namespace = {'ROOT': root, 'METADATA_FILES': tuple(expectations.METADATA_PATHS.values()),
                     'EXPECTATIONS_SOURCE': 'tests/consumer/javafx-ordinary-webview/gradle/reviewed-windows-staging-expectations.json',
                     'REVIEWED_EXPECTATIONS_SHA256': pin, 'dependency_expectations': expectations,
                     'lt': SimpleNamespace(safe_path=safe_namespace['safe_path']),
                     'packaged': SimpleNamespace(EvidenceError=FixtureEvidenceError),
                     'hashlib': hashlib, 'ET': ET, 're': re}
        definitions = ast.Module(body=[self.nodes[name] for name in EXTRACTED], type_ignores=[])
        exec(compile(definitions, str(CONTROLLER_SOURCE), 'exec'), namespace)
        return namespace

    def materialize_synthetic(self, root):
        namespace = self.namespace(root, self.pin)
        files = {namespace['EXPECTATIONS_SOURCE']: self.payload, **expectations.metadata_payloads(self.payload, self.pin)}
        for relative, value in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)  # Unittest-owned temporary root only.
        return namespace, files

    def test_two_root_renderer_exact_identities_determinism_and_immutable_input(self):
        policies = expectations.metadata_payloads(self.payload, self.pin)
        self.assertEqual(set(policies), set(expectations.METADATA_PATHS.values()))
        self.assertEqual(policies, expectations.metadata_payloads(self.payload, self.pin))
        for invocation, relative in expectations.METADATA_PATHS.items():
            with self.subTest(invocation=invocation):
                xml = ET.fromstring(policies[relative])
                self.assertEqual(xml.tag, NS + 'verification-metadata')
                configuration = xml.find(NS + 'configuration')
                self.assertEqual([child.tag for child in configuration], [NS + 'verify-metadata', NS + 'verify-signatures'])
                self.assertEqual(configuration.findtext(NS + 'verify-metadata'), 'true')
                self.assertEqual(configuration.findtext(NS + 'verify-signatures'), 'false')
                actual = {}
                for component in xml.findall(NS + 'components/' + NS + 'component'):
                    for artifact in component.findall(NS + 'artifact'):
                        identity = (component.get('group'), component.get('name'), component.get('version'), artifact.get('name'))
                        self.assertNotIn(identity, actual)
                        self.assertEqual([child.tag for child in artifact], [NS + 'sha256'])
                        actual[identity] = artifact.find(NS + 'sha256').get('value')
                expected = {tuple(row[k] for k in ('group', 'module', 'version', 'name')): row['sha256']
                            for row in self.document['artifacts'] if row['root'] == invocation}
                self.assertEqual(actual, expected)
                self.assertFalse(xml.findall('.//' + NS + 'trusted-artifact'))
                self.assertFalse(xml.findall('.//' + NS + 'trusted-artifacts'))
        parsed = expectations.parse_reviewed_manifest(self.payload, self.pin)
        parsed['artifacts'].clear()
        parsed['staging_inputs']['library'].clear()
        self.assertEqual(policies, expectations.metadata_payloads(self.payload, self.pin))
        with self.assertRaises(expectations.ExpectationError):
            expectations.metadata_payloads(parsed, self.pin)
        changed = copy.deepcopy(self.document)
        changed['artifacts'][0]['provenance']['evidence_sha256'] = synthetic_digest('mutated-review')
        with self.assertRaises(expectations.ExpectationError):
            expectations.metadata_payloads(encoded(changed), self.pin)
        self.assertEqual(hashlib.sha256(self.payload).hexdigest(), self.pin)

    def test_manifest_authority_schema_coverage_paths_and_provenance_fail_closed(self):
        for pin in (None, '', '0' * 64, self.pin.upper(), True, 7):
            with self.subTest(pin_type=type(pin).__name__, pin=pin), self.assertRaises(expectations.ExpectationError):
                expectations.parse_reviewed_manifest(self.payload, pin)
        for payload in (b'', bytearray(self.payload), b'null', b'{"schema_version":NaN}',
                        b'{"schema_version":1,"schema_version":1}'):
            pin = hashlib.sha256(bytes(payload)).hexdigest()
            with self.subTest(payload_type=type(payload).__name__, bytes=len(payload)), self.assertRaises(expectations.ExpectationError):
                expectations.parse_reviewed_manifest(payload, pin)
        mutations = []
        for key, value in (('schema_version', True), ('source_recipe_authority_sha256', synthetic_digest('wrong-recipe')),
                           ('review_basis_sha256', None), ('unknown_trust', True)):
            changed = copy.deepcopy(self.document)
            changed[key] = value
            mutations.append(('top:' + key, changed))
        for root, scopes in self.document['coverage'].items():
            if root == 'producer':
                for scope in scopes:
                    changed = copy.deepcopy(self.document)
                    del changed['coverage'][root][scope]
                    mutations.append(('missing-producer:' + scope, changed))
            else:
                for mode, mode_scopes in scopes.items():
                    for scope in mode_scopes:
                        changed = copy.deepcopy(self.document)
                        del changed['coverage'][root][mode][scope]
                        mutations.append(('missing-consumer:' + mode + ':' + scope, changed))
                changed = copy.deepcopy(self.document)
                del changed['coverage']['consumer']['pom']
                mutations.append(('missing-mode:pom', changed))
        for root in expectations.METADATA_PATHS:
            changed = copy.deepcopy(self.document)
            changed['artifacts'] = [row for row in changed['artifacts'] if row['root'] != root]
            mutations.append(('absent-artifact-root:' + root, changed))
        duplicate = copy.deepcopy(self.document)
        duplicate['artifacts'].append(copy.deepcopy(duplicate['artifacts'][0]))
        mutations.append(('duplicate-artifact', duplicate))
        external = next(index for index, row in enumerate(self.document['artifacts']) if row['provenance']['kind'] == 'external')
        for field, value in (('basis', 'registry-sidecar'), ('basis', 'self-observed'), ('basis', 'TOFU'),
                             ('url', 'https://example.invalid/unreviewed.jar'), ('evidence_sha256', 'invalid')):
            changed = copy.deepcopy(self.document)
            changed['artifacts'][external]['provenance'][field] = value
            mutations.append(('unaccepted-provenance:' + field + ':' + value, changed))
        for field, value in (('root', 'unexpected'), ('version', '1.+'), ('version', 'latest.release'),
                             ('version', '1.0-SNAPSHOT'), ('name', '*.jar'), ('bytes', True), ('sha256', 'F' * 64),
                             ('contexts', ['module:unobserved']), ('contexts', ['pom:metadata', 'pom:metadata'])):
            changed = copy.deepcopy(self.document)
            changed['artifacts'][external][field] = value
            mutations.append(('nonexact-artifact:' + field + ':' + repr(value), changed))
        for path in ('../foreign.jar', '/absolute.jar', 'a/../b.jar', 'a//b.jar', r'a\b.jar', 'C:/foreign.jar', 'a/./b.jar'):
            changed = copy.deepcopy(self.document)
            old = next(iter(changed['staging_inputs']['library']))
            changed['staging_inputs']['library'][path] = changed['staging_inputs']['library'].pop(old)
            mutations.append(('unsafe-staged-path:' + path, changed))
        for label, changed in mutations:
            with self.subTest(mutation=label):
                self.refuse_manifest(changed)

    def test_all_eight_classpaths_require_exact_binary_pair_and_classified_five(self):
        pair_names = {f'nativecmpkit-webview-desktop-{expectations.LIBRARY_VERSION}.jar',
                      f'{expectations.PRIVATE_MODULE}-{expectations.PRIVATE_VERSION}.jar'}
        providers = [row['name'] for row in self.document['artifacts'] if row['name'] in pair_names or
                     (row['group'] == 'org.openjfx' and row['name'].endswith('-win.jar'))]
        self.assertEqual(len(providers), 7)
        for mode in expectations.MODES:
            for classpath in expectations.CLASSPATHS:
                context = f'{mode}:{classpath}'
                for name in providers:
                    changed = copy.deepcopy(self.document)
                    next(row for row in changed['artifacts'] if row['name'] == name)['contexts'].remove(context)
                    with self.subTest(cell=context, missing=name):
                        self.refuse_manifest(changed)
                # A reviewed source JAR is NOT the desktop binary provider.
                changed = copy.deepcopy(self.document)
                binary = next(row for row in changed['artifacts'] if row['name'] == f'nativecmpkit-webview-desktop-{expectations.LIBRARY_VERSION}.jar')
                sources = next(row for row in changed['artifacts'] if row['name'] == f'nativecmpkit-webview-desktop-{expectations.LIBRARY_VERSION}-sources.jar')
                binary['contexts'].remove(context)
                sources['contexts'] = sorted([*sources['contexts'], context])
                with self.subTest(cell=context, substitution='sources-not-binary'):
                    self.refuse_manifest(changed)
                changed = copy.deepcopy(self.document)
                companion = next(row for row in changed['artifacts'] if row['module'] == 'javafx-base')
                companion['contexts'].remove(context)
                generic = copy.deepcopy(companion)
                generic['name'] = 'javafx-base-21.0.13.jar'
                generic['contexts'] = [context]
                generic['provenance']['url'] = generic['provenance']['url'].replace('-win.jar', '.jar')
                changed['artifacts'].append(generic)
                with self.subTest(cell=context, substitution='generic-not-classified'):
                    self.refuse_manifest(changed)
        changed = copy.deepcopy(self.document)
        official = copy.deepcopy(next(row for row in changed['artifacts'] if row['module'] == 'javafx-base'))
        official['module'] = 'javafx-web'
        official['name'] = 'javafx-web-21.0.13-win.jar'
        official['provenance']['url'] = official['provenance']['url'].replace('javafx-base', 'javafx-web')
        changed['artifacts'].append(official)
        self.refuse_manifest(changed)

    def test_local_descriptors_aliases_and_artifact_staging_bindings_are_exact(self):
        required = [(module, '.module') for module in expectations.LIBRARY_MODULES] + [
            (expectations.PRIVATE_MODULE, '.module'), ('nativecmpkit-webview-desktop', '.pom'), (expectations.PRIVATE_MODULE, '.pom')]
        for module, suffix in required:
            changed = copy.deepcopy(self.document)
            changed['artifacts'] = [row for row in changed['artifacts'] if not (row['module'] == module and row['name'].endswith(suffix))]
            with self.subTest(absent_descriptor=(module, suffix)):
                self.refuse_manifest(changed)
        local = next(index for index, row in enumerate(self.document['artifacts']) if row['provenance']['kind'] == 'local-library')
        for field, value in (('sha256', synthetic_digest('wrong-local-digest')), ('bytes', 777), ('group', 'foreign.local'),
                             ('version', '0.1.0-preview.2'), ('name', 'unreviewed-name.jar')):
            changed = copy.deepcopy(self.document)
            changed['artifacts'][local][field] = value
            with self.subTest(local_mismatch=field):
                self.refuse_manifest(changed)
        alias_document = copy.deepcopy(self.document)
        canonical = next(row for row in alias_document['artifacts'] if row['name'] == f'nativecmpkit-webview-desktop-{expectations.LIBRARY_VERSION}.jar')
        alias = copy.deepcopy(canonical)
        alias['name'] = f'calf-webview-desktop-{expectations.LIBRARY_VERSION}.jar'
        alias['contexts'] = [value for value in canonical['contexts'] if value.startswith('module:')]
        canonical['contexts'] = [value for value in canonical['contexts'] if value.startswith('pom:')]
        alias_document['artifacts'].append(alias)
        alias_payload = encoded(sorted_rows(alias_document))
        expectations.parse_reviewed_manifest(alias_payload, hashlib.sha256(alias_payload).hexdigest())
        for field, value in (('name', f'calf-webview-desktop-{expectations.LIBRARY_VERSION}-sources.jar'),
                             ('sha256', synthetic_digest('wrong-alias')), ('bytes', 3), ('contexts', ['pom:compileClasspath'])):
            changed = copy.deepcopy(alias_document)
            target = next(row for row in changed['artifacts'] if row['name'] == alias['name'])
            target[field] = value
            with self.subTest(alias_mismatch=field):
                self.refuse_manifest(changed)
        changed = copy.deepcopy(alias_document)
        canonical = next(row for row in changed['artifacts'] if row['name'] == f'nativecmpkit-webview-desktop-{expectations.LIBRARY_VERSION}.jar')
        canonical['contexts'] = sorted([*canonical['contexts'], 'module:compileClasspath'])
        self.refuse_manifest(changed)  # Canonical plus alias must not produce duplicate providers.

    def test_fresh_staging_primary_tamper_and_administrative_scope_never_refresh_trust(self):
        library, private = (copy.deepcopy(self.document['staging_inputs'][kind]) for kind in ('library', 'private'))
        held = encoded({'library': library, 'private': private})
        result = expectations.compare_staging(self.payload, self.pin, library, private)
        self.assertEqual(result['primary_library_files'], len(library))
        self.assertEqual(result['private_files'], 4)
        self.assertTrue(result['all_physical_files_still_require_existing_before_after_custody'])
        for flag in ('independent_trust_certified', 'graph_completeness_certified', 'publication_ready'):
            self.assertIs(result[flag], False)
        for kind, actual in (('library', library), ('private', private)):
            for path in actual:
                for field, value in (('bytes', actual[path]['bytes'] + 1), ('sha256', synthetic_digest('fresh-tamper:' + path))):
                    changed = copy.deepcopy(actual)
                    changed[path][field] = value
                    args = (changed, private) if kind == 'library' else (library, changed)
                    with self.subTest(kind=kind, path=path, mismatch=field), self.assertRaises(expectations.ExpectationError):
                        expectations.compare_staging(self.payload, self.pin, *args)
                changed = copy.deepcopy(actual)
                del changed[path]
                args = (changed, private) if kind == 'library' else (library, changed)
                with self.subTest(kind=kind, path=path, mismatch='absent'), self.assertRaises(expectations.ExpectationError):
                    expectations.compare_staging(self.payload, self.pin, *args)
        endpoint = {'bytes': 19, 'sha256': synthetic_digest('synthetic-administrative-not-trust')}
        primary = next(path for path in library if path.endswith('.jar'))
        module_prefix = f'{expectations.LIBRARY_GROUP.replace(".", "/")}/nativecmpkit-webview-desktop/'
        physical = copy.deepcopy(library)
        for name in ('maven-metadata.xml', 'maven-metadata.xml.md5', 'maven-metadata.xml.sha1',
                     'maven-metadata.xml.sha256', 'maven-metadata.xml.sha512'):
            physical[module_prefix + name] = endpoint.copy()
        for suffix in ('.md5', '.sha1', '.sha256', '.sha512'):
            physical[primary + suffix] = endpoint.copy()
        physical_before = encoded(physical)
        self.assertEqual(result, expectations.compare_staging(self.payload, self.pin, physical, private))
        self.assertEqual(encoded(physical), physical_before)  # Synthetic endpoint maps stay unchanged; real physical-byte custody is not inferred.
        for path in (primary.replace('.jar', '-unreviewed.jar'), primary.replace('.jar', '-orphan.jar.sha256'),
                     module_prefix + 'maven-metadata.json', primary.rsplit('/', 1)[0] + '/maven-metadata.xml', '../foreign.jar'):
            changed = copy.deepcopy(library)
            changed[path] = endpoint.copy()
            with self.subTest(unexpected_path=path), self.assertRaises(expectations.ExpectationError):
                expectations.compare_staging(self.payload, self.pin, changed, private)
        extra_private = copy.deepcopy(private)
        extra_private[next(path for path in private if path.endswith('.jar')) + '.sha256'] = endpoint.copy()
        with self.assertRaises(expectations.ExpectationError):
            expectations.compare_staging(self.payload, self.pin, library, extra_private)
        changed_manifest = copy.deepcopy(self.document)
        changed_manifest['coverage']['consumer']['module']['runtimeClasspath'] = synthetic_digest('graph-mutated-after-approval')
        with self.assertRaises(expectations.ExpectationError):
            expectations.compare_staging(encoded(changed_manifest), self.pin, library, private)
        self.assertEqual(encoded({'library': library, 'private': private}), held)
        self.assertEqual(hashlib.sha256(self.payload).hexdigest(), self.pin)

    def test_actual_inert_path_read_xml_controls_refuse_links_xxe_and_exceptions(self):
        with tempfile.TemporaryDirectory(prefix='synthetic-expectations742-') as temporary:
            root = Path(temporary)
            namespace, files = self.materialize_synthetic(root)
            result = namespace['dependency_metadata_preflight']()
            self.assertTrue(result['metadata_usable_for_strict_execution'])
            self.assertIs(result['independent_trust_qualified'], False)
            self.assertIs(result['dependencies_resolved'], False)
            self.assertTrue(all(row['reason'] == 'checksum-structure-only' for row in result['metadata']))
            relative = expectations.METADATA_PATHS['producer']
            path, original = root / relative, files[relative]
            for declaration in (b'<!DOCTYPE verification-metadata [<!ENTITY synthetic SYSTEM "file:///SYNTHETIC-NO-ENTITY-ACCESS">]>',
                                b'<!ENTITY synthetic "SYNTHETIC-NO-ENTITY-ACCESS">', b'<! dOcTyPe verification-metadata>'):
                path.write_bytes(original.split(b'?>', 1)[0] + b'?>\n' + declaration + b'\n' + original.split(b'?>', 1)[1])
                result = namespace['dependency_metadata_preflight']()
                self.assertFalse(result['metadata_usable_for_strict_execution'])
                self.assertEqual(result['metadata'][0]['reason'], 'unusable')
            for mutation in ('metadata-false', 'trusted-artifacts', 'wrong-sha256'):
                xml = ET.fromstring(original)
                if mutation == 'metadata-false':
                    xml.find(NS + 'configuration/' + NS + 'verify-metadata').text = 'false'
                elif mutation == 'trusted-artifacts':
                    ET.SubElement(xml.find(NS + 'configuration'), NS + 'trusted-artifacts')
                else:
                    xml.find(NS + 'components/' + NS + 'component/' + NS + 'artifact/' + NS + 'sha256').set('value', '0' * 63)
                path.write_bytes(ET.tostring(xml, encoding='utf-8'))
                with self.subTest(xml_mutation=mutation):
                    self.assertFalse(namespace['dependency_metadata_preflight']()['metadata_usable_for_strict_execution'])
            path.write_bytes(original)
            for relative in ('../foreign', str(root / 'absolute'), 'nested/../foreign', '.'):
                with self.subTest(unsafe_path=relative), self.assertRaises(ValueError):
                    namespace['lt'].safe_path(root, relative)
            target = root / 'synthetic-target'
            target.write_bytes(b'SYNTHETIC-UNTRUSTED')
            symlink = root / 'synthetic-link'
            symlink.symlink_to(target)
            with self.assertRaises(ValueError):
                namespace['lt'].safe_path(root, 'synthetic-link')
            with self.assertRaises(FixtureEvidenceError):
                namespace['read'](symlink)
            linked_directory = root / 'synthetic-directory-link'
            linked_directory.symlink_to(root / 'tests', target_is_directory=True)
            with self.assertRaises(ValueError):
                namespace['lt'].safe_path(root, 'synthetic-directory-link/consumer')
            hardlink = root / 'synthetic-hardlink'
            os.link(target, hardlink)
            with self.assertRaises(FixtureEvidenceError):
                namespace['read'](hardlink)
            with self.assertRaises(FixtureEvidenceError):
                namespace['read'](target)
            bounded = root / 'synthetic-bounded'
            bounded.write_bytes(b'123456789')
            with self.assertRaises(FixtureEvidenceError):
                namespace['read'](bounded, 8)
            self.assertEqual(namespace['dependency_expectations_preflight'](), self.payload)

    def test_missing_authority_precedes_read_and_each_actual_root_policy_is_exact(self):
        assignments = [node for node in self.controller_tree.body if isinstance(node, ast.Assign) and
                       any(isinstance(target, ast.Name) and target.id == 'REVIEWED_EXPECTATIONS_SHA256' for target in node.targets)]
        self.assertEqual(len(assignments), 1)
        self.assertIs(ast.literal_eval(assignments[0].value), None)
        with tempfile.TemporaryDirectory(prefix='synthetic-preflight742-') as temporary:
            root = Path(temporary)
            for missing_pin in (None, '', 'NOT-A-REVIEW-PIN', True):
                namespace = self.namespace(root, missing_pin)
                reader = mock.Mock(side_effect=AssertionError('Authority refusal must precede file read'))
                with mock.patch.dict(namespace, {'read': reader}), self.assertRaises(FixtureEvidenceError):
                    namespace['dependency_expectations_preflight']()
                reader.assert_not_called()
            self.assertEqual(list(root.iterdir()), [])
            namespace, files = self.materialize_synthetic(root)
            self.assertEqual(namespace['dependency_expectations_preflight'](), self.payload)
            for invocation, relative in expectations.METADATA_PATHS.items():
                path, original = root / relative, files[relative]
                path.unlink()
                with self.subTest(root=invocation, mismatch='absent'), self.assertRaises(FixtureEvidenceError):
                    namespace['dependency_expectations_preflight']()
                path.write_bytes(original)
                for mutation in ('absent-component', 'unexpected-component', 'duplicate-component', 'wrong-component', 'wrong-sha256'):
                    xml = ET.fromstring(original)
                    components = xml.find(NS + 'components')
                    component = components.find(NS + 'component')
                    if mutation == 'absent-component':
                        components.remove(component)
                    elif mutation in ('unexpected-component', 'duplicate-component'):
                        added = copy.deepcopy(component)
                        if mutation == 'unexpected-component':
                            added.set('name', 'unreviewed-component')
                        components.append(added)
                    elif mutation == 'wrong-component':
                        component.set('version', 'unreviewed-version')
                    else:
                        component.find(NS + 'artifact/' + NS + 'sha256').set('value', synthetic_digest('wrong-XML-digest'))
                    path.write_bytes(ET.tostring(xml, encoding='utf-8'))
                    with self.subTest(root=invocation, mismatch=mutation), self.assertRaises(FixtureEvidenceError):
                        namespace['dependency_expectations_preflight']()
                    path.write_bytes(original)
            changed = copy.deepcopy(self.document)
            changed['review_basis_sha256'] = synthetic_digest('mutated-provenance-after-policy')
            (root / namespace['EXPECTATIONS_SOURCE']).write_bytes(encoded(changed))
            with self.assertRaises(expectations.ExpectationError):
                namespace['dependency_expectations_preflight']()
            # A caller cannot substitute only one invoked root's policy map.
            (root / namespace['EXPECTATIONS_SOURCE']).write_bytes(self.payload)
            fake_helper = SimpleNamespace(MAX_MANIFEST_BYTES=expectations.MAX_MANIFEST_BYTES,
                                          metadata_payloads=lambda *_: {expectations.METADATA_PATHS['producer']: files[expectations.METADATA_PATHS['producer']]})
            with mock.patch.dict(namespace, {'dependency_expectations': fake_helper}), self.assertRaises(FixtureEvidenceError):
                namespace['dependency_expectations_preflight']()

    def test_controller_source_custody_order_and_native_guards_are_not_bypassed(self):
        source = self.controller_bytes.decode()
        segments = {name: ast.get_source_segment(source, self.nodes[name]) for name in ('inputs', 'run', 'main', 'command')}
        self.assertIn('*METADATA_FILES, EXPECTATIONS_SOURCE', segments['inputs'])
        self.assertIn("'scripts/ci/javafx_ordinary_dependency_expectations.py'", segments['inputs'])
        run = segments['run']
        ordered = ('expectation_payload = dependency_expectations_preflight()',
                   "need(os.name == 'nt' and sys.platform == 'win32'", 'runtime_context.capture(', 'before = inputs()',
                   "invoke(phase, producer,", 'dependency_expectations.compare_staging(',
                   "'observePrivateWebResolution'", "phase = 'complete-four-classpath-graph-comparison'",
                   "phase = 'NEW-ordinary-public-Stop-native1'")
        positions = [run.index(fragment) for fragment in ordered]
        self.assertEqual(positions, sorted(positions))
        for guard in ("record['source_inputs_held'] = before == after and lt.git_revision(ROOT) == record['source_revision']",
                      "record['staged_library_inputs_held'] = staged == after_staged",
                      "record['private_staged_inputs_held'] = private_files == after_private",
                      "need(equal, 'Distinct module/POM byte graph requires",
                      "record['native']['exact_source_method_passed']", "record['native']['all_reports_fresh']",
                      "need(current.get('metadata_mode') == 'module' and graph_signature(current) == signatures['module']",
                      "record['passed'] = record['passed'] and bool(held) and all(held)"):
            self.assertIn(guard, run)
        self.assertIn("'--dependency-verification', 'strict'", segments['command'])
        for statement in ast.walk(self.nodes['run']):
            if isinstance(statement, ast.Assign):
                self.assertFalse(any(isinstance(target, ast.Name) and target.id == 'REVIEWED_EXPECTATIONS_SHA256' for target in statement.targets))
        flag_branch = next(statement for statement in self.nodes['main'].body if isinstance(statement, ast.If) and
                           isinstance(statement.test, ast.Attribute) and statement.test.attr == 'metadata_preflight_only')
        call_names = {node.func.id for node in ast.walk(flag_branch) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertFalse(call_names & {'run', 'resources', 'inputs', 'invoke'})
        self.assertIn('dependency_expectations_preflight', call_names)
        self.assertTrue(any(isinstance(statement, ast.Return) for statement in flag_branch.body))
        helper_tree = ast.parse(self.helper_bytes)
        imports = {node.module for node in helper_tree.body if isinstance(node, ast.ImportFrom)} | {
            alias.name for node in helper_tree.body if isinstance(node, ast.Import) for alias in node.names}
        self.assertEqual(imports, {'__future__', 'hashlib', 'json', 'pathlib', 're', 'xml.etree.ElementTree'})
        calls = {node.func.attr for node in ast.walk(helper_tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(calls & {'write', 'write_bytes', 'write_text', 'open', 'unlink', 'mkdir', 'urlopen', 'run', 'Popen'})


if __name__ == '__main__':
    unittest.main()
