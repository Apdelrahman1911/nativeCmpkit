"""Adversarial controller fixtures only; no JavaFX/native/consumer runtime evidence."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import webview_consumer as c


def resolution(host='linux-x64', mode='module'):
    target = c.MODULE + '-desktop'
    canonical = target + '-' + c.VERSION + '.jar'
    label = 'calf-webview-desktop-' + c.VERSION + '.jar'
    directory = c.GROUP.replace('.', '/') + '/' + target + '/' + c.VERSION + '/'
    artifact, metadata = directory + canonical, directory + target + '-' + c.VERSION + '.module'
    staged = {artifact: {'bytes': 17, 'sha256': 'a' * 64}, metadata: {'bytes': 31, 'sha256': 'b' * 64}}
    rows = []
    for configuration in sorted(c.CLASSPATHS):
        filename = label if mode == 'module' else canonical
        rows.append({'configuration': configuration, 'group': c.GROUP, 'module': target, 'version': c.VERSION,
                     'file': filename, 'bytes': 17, 'sha256': 'a' * 64, 'declared_file_name': label, 'resolved_file_name': filename,
                     'declared_file_url': canonical, 'staged_file': artifact, 'metadata_file': metadata, 'metadata_sha256': 'b' * 64})
        for module in sorted(c.FX_MODULES):
            rows.append({'configuration': configuration, 'group': 'org.openjfx', 'module': 'javafx-' + module, 'version': '21.0.13',
                         'file': 'javafx-' + module + '-21.0.13-' + c.HOSTS[host][2] + '.jar', 'bytes': 23, 'sha256': 'c' * 64})
    document = {'schema_version': 2, 'scope': 'PARTIAL WebView desktop Maven consumer', 'candidate_group': c.GROUP,
                'candidate_version': c.VERSION, 'publication_roots_requested': [c.MODULE], 'metadata_mode': mode,
                'complete_21_root_KMP_matrix_requested': False, 'release_readiness_certified': False,
                'candidate_variants_resolved': [target], 'resolved_artifacts': rows}
    return document, staged


class WebViewConsumerControllerTests(unittest.TestCase):
    def test_all_five_hosts_and_both_metadata_modes_use_distinct_exact_runtime_classifiers(self):
        for host in c.HOSTS:
            for mode in c.MODES:
                with self.subTest(host=host, mode=mode):
                    document, staged = resolution(host, mode)
                    result = c.resolution_contract(document, staged, host, mode)
                    self.assertEqual(result['classpath_count'], 4)
                    self.assertEqual(result['native_classifier'], c.HOSTS[host][2])

    def test_finite_matrix_all_and_recovery_never_dispatch_unrelated_library_jobs(self):
        self.assertEqual({row['host'] for row in c.workflow_matrix('consumer-webview')['include']}, set(c.HOSTS))
        remaining = c.workflow_matrix('consumer-webview-remaining')['include']
        self.assertEqual(len(remaining), 4)
        self.assertEqual({row['host'] for row in remaining}, set(c.HOSTS) - {'linux-x64'})
        for host in c.HOSTS:
            rows = c.workflow_matrix('consumer-webview-' + host)['include']
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['host'], host)
        self.assertEqual(c.workflow_matrix('core')['include'], [])
        self.assertEqual(c.workflow_matrix('consumer-webview-../windows')['include'], [])

    def test_foreign_host_classifier_is_rejected(self):
        document, staged = resolution()
        document['resolved_artifacts'][1]['file'] = 'javafx-base-21.0.13-win.jar'
        with self.assertRaises(c.EvidenceError):
            c.resolution_contract(document, staged, 'linux-x64', 'module')

    def test_missing_native_module_is_rejected_on_every_classpath(self):
        for configuration in c.CLASSPATHS:
            document, staged = resolution()
            document['resolved_artifacts'] = [row for row in document['resolved_artifacts']
                if not (row['configuration'] == configuration and row['module'] == 'javafx-web')]
            with self.subTest(configuration=configuration), self.assertRaises(c.EvidenceError):
                c.resolution_contract(document, staged, 'linux-x64', 'module')

    def test_generic_javafx_jars_never_replace_the_required_native_classifiers(self):
        document, staged = resolution()
        for row in document['resolved_artifacts']:
            if row['group'] == 'org.openjfx':
                row['file'] = row['module'] + '-21.0.13.jar'
        with self.assertRaises(c.EvidenceError):
            c.resolution_contract(document, staged, 'linux-x64', 'module')

    def test_duplicate_rows_original_group_and_unselected_candidate_are_rejected(self):
        original, staged = resolution()
        cases = [deepcopy(original) for _ in range(3)]
        cases[0]['resolved_artifacts'].append(deepcopy(cases[0]['resolved_artifacts'][0]))
        cases[1]['resolved_artifacts'][0]['group'] = 'com.mohamedrejeb.calf'
        cases[2]['resolved_artifacts'][0]['module'] = 'nativecmpkit-io-desktop'
        for document in cases:
            with self.assertRaises(c.EvidenceError):
                c.resolution_contract(document, staged, 'linux-x64', 'module')

    def test_candidate_bytes_metadata_hash_and_display_maven_names_are_bound(self):
        original, staged = resolution()
        changes = {'sha256': 'd' * 64, 'bytes': 19, 'metadata_sha256': 'e' * 64,
                   'declared_file_url': 'elsewhere.jar', 'declared_file_name': 'arbitrary.jar', 'resolved_file_name': 'loose-classes'}
        for key, value in changes.items():
            document = deepcopy(original)
            document['resolved_artifacts'][0][key] = value
            with self.subTest(key=key), self.assertRaises(c.EvidenceError):
                c.resolution_contract(document, staged, 'linux-x64', 'module')

    def test_pom_canonical_filename_is_not_silently_accepted_as_a_module_display_label(self):
        document, staged = resolution(mode='pom')
        document['metadata_mode'] = 'module'
        with self.assertRaises(c.EvidenceError):
            c.resolution_contract(document, staged, 'linux-x64', 'module')

    def test_partial_resolution_cannot_claim_full_matrix_or_release_readiness(self):
        for key in ('complete_21_root_KMP_matrix_requested', 'release_readiness_certified'):
            document, staged = resolution()
            document[key] = True
            with self.subTest(key=key), self.assertRaises(c.EvidenceError):
                c.resolution_contract(document, staged, 'linux-x64', 'module')

    def test_json_duplicates_nonfinite_links_and_unbounded_inputs_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'receipt.json'
            for payload in ('{"key":1,"key":2}', '{"x":NaN}'):
                path.write_text(payload)
                with self.assertRaises(c.EvidenceError):
                    c.read_json(path)
            linked = Path(temporary) / 'linked.json'
            linked.symlink_to(path)
            with self.assertRaises(c.EvidenceError):
                c.read_json(linked)
            with path.open('wb') as stream:
                stream.truncate(16 * 1024**2 + 1)
            with self.assertRaises(c.EvidenceError):
                c.read_json(path)

    def test_stale_repository_and_foreign_coordinates_are_not_mutated(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            foreign = repository / 'com/foreign/module/1/payload.jar'
            foreign.parent.mkdir(parents=True)
            foreign.write_bytes(b'preserved')
            with self.assertRaises(c.EvidenceError):
                c.staged_inputs(repository)
            self.assertEqual(foreign.read_bytes(), b'preserved')

    def test_generated_selectors_reject_javafx_in_both_pom_and_module(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            for module in c.COORDINATES:
                directory = repository / c.GROUP.replace('.', '/') / module / c.VERSION
                directory.mkdir(parents=True)
                (directory / (module + '-' + c.VERSION + '.pom')).write_text(
                    '<project xmlns="http://maven.apache.org/POM/4.0.0"><dependencies/></project>')
                (directory / (module + '-' + c.VERSION + '.module')).write_text(json.dumps({'variants': [{'name': 'api', 'dependencies': []}]}))
            self.assertEqual(len(c.selectors(repository)), 4)
            directory = repository / c.GROUP.replace('.', '/') / c.MODULE / c.VERSION
            path = directory / (c.MODULE + '-' + c.VERSION + '.module')
            path.write_text(json.dumps({'variants': [{'name': 'api', 'dependencies': [{'group': 'org.openjfx', 'module': 'javafx-web'}]}]}))
            with self.assertRaises(c.EvidenceError):
                c.selectors(repository)
            path.write_text(json.dumps({'variants': [{'name': 'api', 'dependencies': []}]}))
            (directory / (c.MODULE + '-' + c.VERSION + '.pom')).write_text(
                '<project xmlns="http://maven.apache.org/POM/4.0.0"><dependencies><dependency><groupId>org.openjfx</groupId></dependency></dependencies></project>')
            with self.assertRaises(c.EvidenceError):
                c.selectors(repository)

    def test_fresh_xml_requires_both_actual_methods_and_no_skip_failure_duplicate_or_extra(self):
        for mutation in ('valid', 'missing', 'extra', 'duplicate', 'skipped', 'failure'):
            with tempfile.TemporaryDirectory() as temporary:
                consumer, output = Path(temporary) / 'consumer', Path(temporary) / 'evidence'
                directory = consumer / 'build/test-results/test'
                directory.mkdir(parents=True)
                output.mkdir()
                log = output / 'consumer.log'
                log.write_text('NATIVECMPKIT_WEBVIEW_CONSUMER_TEST task=:test gradle=9.7.1 java=17 mode=module\n')
                methods = sorted(c.METHODS)
                if mutation == 'missing': methods.pop()
                if mutation == 'extra': methods.append('notReviewed')
                if mutation == 'duplicate': methods.append(methods[0])
                status = {'skipped': '<skipped/>', 'failure': '<failure/>'}.get(mutation, '')
                cases = ''.join(f'<testcase classname="{c.CLASS}" name="{name}">{status}</testcase>' for name in methods)
                start = time.time_ns()
                (directory / ('TEST-' + c.CLASS + '.xml')).write_text('<testsuite>' + cases + '</testsuite>')
                end = time.time_ns()
                with self.subTest(mutation=mutation):
                    if mutation == 'valid':
                        self.assertEqual(c.fresh_tests(consumer, output, 'module', start, end, log)['totals']['passed'], 2)
                    else:
                        with self.assertRaises(ValueError):
                            c.fresh_tests(consumer, output, 'module', start, end, log)
                    self.assertTrue(list((output / 'module/junit').glob('TEST-*.xml')), 'Preserve original XML even when duplicate identities are rejected')
                    if mutation != 'duplicate':
                        self.assertTrue((output / 'module/test-outcomes.json').is_file(), 'Preserve actual observed failures')

    def test_consumer_commands_are_local_exact_and_never_select_publication_tasks(self):
        producer = c.commands(c.ROOT, None)
        self.assertIn('--stacktrace', producer, 'Expose an actual producer failure location without exporting the full log')
        self.assertIn('stageWebViewVerificationPublications', producer)
        for mode in c.MODES:
            child = c.commands(c.ROOT, c.ROOT / 'build/ci-webview-consumer/fixture', mode)
            self.assertIn('-PnativecmpkitMetadataMode=' + mode, child)
            self.assertIn('test', child)
            self.assertFalse(any('allowPublishing' in value or value.startswith('publish') for value in child))
        with self.assertRaises(c.EvidenceError):
            c.commands(c.ROOT, c.ROOT / 'fixture', 'pom,arbitrary')

    def test_fixture_uses_public_composable_attached_native_panel_and_strict_pom_mode(self):
        source = (c.ROOT / c.FIXTURE / c.FILES[-1]).read_text()
        self.assertIn('WebView(state,', source)
        self.assertIn('actualPanel.scene', source)
        self.assertNotIn('DesktopWebViewOwner', source)
        self.assertNotIn('Assume', source)
        settings = (c.ROOT / c.FIXTURE / 'settings.gradle.kts').read_text()
        self.assertIn('ignoreGradleMetadataRedirection()', settings)
        self.assertNotIn('includeBuild', settings)
        self.assertNotIn('mavenLocal', settings)

    def test_workflow_is_read_only_and_never_caches_consumers_or_uploads_packages(self):
        workflow = (c.ROOT / '.github/workflows/gradle.yml').read_text()
        job = workflow.split('\n  webview-consumer:\n', 1)[1].split('\n  consumer-core-io:\n', 1)[0]
        self.assertIn('max-parallel: 2', job)
        self.assertIn('persist-credentials: false', job)
        self.assertIn('contents: read', workflow)
        cache = job.split('Exact producer dependencies only', 1)[1].split('- name:', 1)[0]
        self.assertNotIn('restore-keys:', cache)
        self.assertNotIn('independent-consumer', cache)
        upload = job.split('Keep bounded JSON', 1)[1]
        for forbidden in ('*.log', '.jar', '.aar', '.apk', 'verification-repo', 'independent-consumer/**'):
            self.assertNotIn(forbidden, upload)

    def test_explicit_jdk_launcher_uses_java_exe_on_windows_without_inheriting_credentials(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for system, executable in (('Windows', 'java.exe'), ('Linux', 'java'), ('Darwin', 'java')):
                with self.subTest(system=system):
                    jdk = root / system / 'jdk'
                    (jdk / 'bin').mkdir(parents=True)
                    (jdk / 'bin' / executable).write_bytes(b'inert launcher selection only; never executed')
                    output = root / system / 'output'
                    with patch.object(c.platform, 'system', return_value=system), patch.dict(os.environ,
                            {'JAVA_HOME': str(jdk), 'PATH': os.defpath, 'GITHUB_TOKEN': 'synthetic-do-not-inherit'}, clear=True):
                        environment = c.environment(root, output)
                        self.assertEqual(str(jdk), environment['JAVA_HOME'])
                        self.assertNotIn('GITHUB_TOKEN', environment)
                        self.assertTrue((output / 'producer-private/home').is_dir())

    def test_public_failure_diagnostics_keep_exact_compiler_causes_not_unrelated_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'build/ci-webview-consumer/fixture'
            output.mkdir(parents=True)
            payload = 'unrelated application output\ne: public.kt:7: Missing symbol\n* What went wrong:\n> Could not resolve fixture\n> password=synthetic\n\n* Try:\n'
            (output / 'producer.log').write_text(payload)
            observed = c.diagnostics(root, output)
            self.assertFalse(observed['test_success_inferred'])
            self.assertFalse(observed['full_logs_uploaded'])
            text = json.dumps(observed)
            self.assertIn('public.kt:7: Missing symbol', text)
            self.assertIn('Could not resolve fixture', text)
            self.assertNotIn('unrelated application output', text)
            self.assertNotIn('password=synthetic', text)
            self.assertIn('omitted credential-related', text)
            self.assertEqual(payload, (output / 'producer.log').read_text())

    def test_failure_diagnostics_reject_foreign_or_shared_logs_and_bound_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'build/ci-webview-consumer/fixture'
            output.mkdir(parents=True)
            path = output / 'producer.log'
            with path.open('wb') as stream:
                stream.truncate(c.failure_diagnostics.MAX_LOG_BYTES + 1)
            observed = c.diagnostics(root, output)
            self.assertFalse(observed['logs'][0]['inspected'])
            self.assertNotIn('excerpts', observed['logs'][0])
            for foreign in (root, root / 'build/ci-webview-consumer'):
                with self.assertRaises(c.EvidenceError):
                    c.diagnostics(root, foreign)
            linked = output / 'other.log'
            os.link(path, linked)
            with self.assertRaises(c.EvidenceError):
                c.diagnostics(root, output)


if __name__ == '__main__':
    unittest.main()
