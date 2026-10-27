"""Adversarial partial-consumer controller fixtures, NOT Java/Gradle/library passes."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import core_io_consumer as c


class TemporaryTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-partial-consumer-tooling-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def fixture(self):
        destination = self.root / c.FIXTURE
        shutil.copytree(c.ROOT / c.FIXTURE, destination)
        full = self.root / "tests/consumer/src/desktopTest/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt"
        full.parent.mkdir(parents=True)
        full.write_bytes((destination / c.FIXTURE_FILES[-1]).read_bytes())
        return destination

    def staging(self, *, metadata=False):
        repository = self.root / c.REPOSITORY
        for coordinate in c.COORDINATES:
            directory = repository / c.GROUP.replace('.', '/') / coordinate / c.VERSION
            directory.mkdir(parents=True)
            (directory / (coordinate + '-' + c.VERSION + '.jar')).write_bytes(b"synthetic-inert-artifact-" + coordinate.encode())
            if metadata:
                root = coordinate.removesuffix('-desktop')
                file = directory / (coordinate + '-' + c.VERSION + '.jar')
                entry = {'name': file.name, 'url': file.name, 'size': file.stat().st_size, 'sha256': c.lt.sha256(file)}
                component = {'group': c.GROUP, 'module': root, 'version': c.VERSION}
                if coordinate.endswith('-desktop'):
                    component['url'] = f'../../{root}/{c.VERSION}/{root}-{c.VERSION}.module'
                value = {'formatVersion': '1.1', 'component': component, 'variants': [
                    {'name': usage, 'attributes': {'org.gradle.category': 'library',
                     'org.gradle.libraryelements': 'jar', 'org.gradle.usage': usage,
                     'org.jetbrains.kotlin.platform.type': 'jvm'}, 'files': [dict(entry)]}
                    for usage in ('java-api', 'java-runtime')]}
                (directory / (coordinate + '-' + c.VERSION + '.module')).write_text(json.dumps(value))
        return repository

    def resolution(self):
        rows = []
        staged = {}
        bindings = {}
        for configuration in sorted(c.CLASSPATHS):
            for module in c.ROOTS:
                coordinate = module + "-desktop"
                file = coordinate + '-' + c.VERSION + '.jar'
                relative = c.GROUP.replace('.', '/') + '/' + coordinate + '/' + c.VERSION + '/' + file
                metadata = relative.removesuffix('.jar') + '.module'
                binding = {'declared_file_name': file, 'declared_file_url': file,
                           'staged_file': relative, 'metadata_file': metadata,
                           'metadata_sha256': 'b' * 64, 'bytes': 123, 'sha256': 'a' * 64}
                bindings[coordinate] = binding
                row = {"configuration": configuration, "group": c.GROUP, "module": coordinate,
                       "version": c.VERSION, "file": file, **binding}
                rows.append(row)
                staged[relative] = {"bytes": 123, "sha256": "a" * 64}
                staged[metadata] = {"bytes": 234, "sha256": "b" * 64}
        return {"schema_version": 2, "scope": "PARTIAL Core/IO desktop Maven consumer",
                "candidate_group": c.GROUP, "candidate_version": c.VERSION, "publication_roots_requested": list(c.ROOTS),
                "candidate_variants_resolved": sorted(m + "-desktop" for m in c.ROOTS),
                "complete_21_root_KMP_matrix_requested": False, "release_readiness_certified": False,
                "resolved_artifacts": rows}, staged, bindings

    def reports(self):
        consumer = self.root / "independent-consumer"
        output = self.root / "evidence"
        output.mkdir()
        folder = consumer / "build/test-results/test"
        folder.mkdir(parents=True)
        for classname in sorted({cls for cls, name in c.EXPECTED_CASES}):
            suite = ET.Element("testsuite")
            for cls, method in sorted(c.EXPECTED_CASES):
                if cls == classname:
                    ET.SubElement(suite, "testcase", classname=cls, name=method)
            ET.ElementTree(suite).write(folder / ('TEST-' + classname + '.xml'), encoding="UTF-8")
        log = self.root / "consumer.log"
        log.write_text("NATIVECMPKIT_PARTIAL_CONSUMER_TEST task=:test gradle=9.7.1 java=17\n")
        stamp = time.time_ns()
        return consumer, output, stamp - 2_000_000_000, stamp, log


class CommandAndEnvironmentTests(TemporaryTest):
    def test_fixed_producer_stages_only_core_io_and_cannot_enable_remote_publication(self):
        producer, consumer = c.commands(self.root, self.root / "independent-consumer")
        self.assertEqual("stageCoreIoVerificationPublications", producer[-1])
        self.assertIn("-PnativecmpkitVerification=true", producer)
        self.assertIn("-PnativecmpkitVerificationTargets=desktop", producer)
        self.assertIn("-PnativeCmpkit.version=0.1.0-preview.1", producer)
        self.assertFalse(any(x.startswith(("-PnativeCmpkit.allowPublishing", "--scan")) for x in producer + consumer))
        self.assertNotIn("stageVerificationPublications", producer)

    def test_independent_consumer_uses_own_cwd_settings_exact_repo_and_draft_version(self):
        child = self.root / "independent-consumer"
        producer, consumer = c.commands(self.root, child)
        self.assertEqual(str(child), consumer[consumer.index('-p') + 1])
        self.assertEqual(["verifyCandidateResolution", "test"], consumer[-2:])
        self.assertIn("-PnativecmpkitVersion=" + c.VERSION, consumer)
        self.assertIn("-PnativecmpkitRepository=" + str(self.root / c.REPOSITORY), consumer)
        self.assertNotIn("--init-script", consumer)

    def test_partial_staging_marker_binds_only_the_exact_canonical_producer_root(self):
        producer, consumer = c.commands(self.root, self.root / "independent-consumer")
        marker = "-Dnativecmpkit.partialStagingRoot=" + str(self.root.resolve())
        self.assertEqual(1, producer.count(marker))
        self.assertFalse(any(arg.startswith("-Dnativecmpkit.partialStagingRoot=") for arg in consumer))

    def test_both_phases_bound_toolchain_and_avoid_build_or_configuration_cache_test_reuse(self):
        for command in c.commands(self.root, self.root / "independent-consumer"):
            for flag in ("--no-daemon", "--no-parallel", "--no-configuration-cache", "--no-build-cache", "--max-workers=2",
                         "-Pkotlin.compiler.execution.strategy=in-process", "--console=plain"):
                self.assertIn(flag, command)
            self.assertEqual("strict", command[command.index("--dependency-verification") + 1])

    def test_private_child_environment_drops_credentials_and_inherited_jvm_overrides(self):
        jdk = self.root / "jdk"
        (jdk / 'bin').mkdir(parents=True)
        (jdk / 'bin/java').write_bytes(b"synthetic-jdk-selection-not-executed")
        inherited = {"JAVA_HOME": str(jdk), "JAVA_TOOL_OPTIONS": "unreviewed", "JAVA_OPTS": "unreviewed",
                     "_JAVA_OPTIONS": "unreviewed", "GRADLE_OPTS": "unreviewed", "GH_TOKEN": "synthetic-secret",
                     "AWS_SECRET_ACCESS_KEY": "synthetic-secret", "PATH": "/safe/bin", "ANDROID_HOME": "/sdk"}
        with patch.dict(os.environ, inherited, clear=True):
            actual = c.environment(self.root, self.root / "evidence")
        for name in ("JAVA_OPTS", "_JAVA_OPTIONS", "GRADLE_OPTS", "GH_TOKEN", "AWS_SECRET_ACCESS_KEY"):
            self.assertNotIn(name, actual)
        self.assertNotEqual(inherited['JAVA_TOOL_OPTIONS'], actual['JAVA_TOOL_OPTIONS'])
        self.assertEqual(str(self.root / c.GRADLE_HOME), actual['GRADLE_USER_HOME'])
        self.assertEqual('/sdk', actual['ANDROID_HOME'])

    def test_restored_user_init_scripts_or_properties_are_rejected(self):
        jdk = self.root / "jdk"
        (jdk / 'bin').mkdir(parents=True)
        (jdk / 'bin/java').write_bytes(b"inert")
        home = self.root / c.GRADLE_HOME
        home.mkdir(parents=True)
        with patch.dict(os.environ, {"JAVA_HOME": str(jdk)}):
            for name in ('init.gradle', 'init.gradle.kts', 'gradle.properties', 'init.d'):
                with self.subTest(name=name):
                    path = home / name
                    path.write_bytes(b"inert-unreviewed-user-configuration")
                    with self.assertRaises(c.ConsumerEvidenceError): c.environment(self.root, self.root / "evidence")
                    path.unlink()


class CopyAndStagingTests(TemporaryTest):
    def test_exact_fixture_copy_is_independent_and_byte_identical(self):
        self.fixture()
        output = self.root / "evidence"
        output.mkdir()
        copied, hashes = c.copy_fixture(self.root, output)
        self.assertEqual(set(c.FIXTURE_FILES), set(hashes))
        for file, digest in hashes.items():
            self.assertEqual(digest, c.lt.sha256(copied / file))
            self.assertNotEqual((self.root / c.FIXTURE / file).stat().st_ino, (copied / file).stat().st_ino)

    def test_copy_rejects_preexisting_output_without_deleting_it(self):
        self.fixture()
        output = self.root / "evidence"
        (output / "independent-consumer").mkdir(parents=True)
        sentinel = output / "independent-consumer/foreign.txt"
        sentinel.write_text('preserve')
        with self.assertRaises(c.ConsumerEvidenceError): c.copy_fixture(self.root, output)
        self.assertEqual('preserve', sentinel.read_text())

    def test_fixture_scope_rejects_missing_added_or_altered_original_scenarios(self):
        fixture = self.fixture()
        extra = fixture / "additional.kt"
        extra.write_text('inert')
        with self.assertRaises(c.ConsumerEvidenceError): c.fixture_inputs(self.root)
        extra.unlink()
        full = self.root / 'tests/consumer/src/desktopTest/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt'
        full.write_text('changed original scenarios')
        with self.assertRaises(c.ConsumerEvidenceError): c.fixture_inputs(self.root)

    def test_symlinked_or_hardlinked_consumer_sources_are_not_copied(self):
        fixture = self.fixture()
        path = fixture / "README.md"
        outside = self.root / "outside"
        path.rename(outside)
        path.symlink_to(outside)
        with self.assertRaises(ValueError): c.fixture_inputs(self.root)
        path.unlink()
        os.link(outside, path)
        with self.assertRaises(c.ConsumerEvidenceError): c.fixture_inputs(self.root)

    def test_four_coordinate_staged_inventory_hashes_real_files_and_holds_read_bytes(self):
        repo = self.staging()
        first = c.staged_inputs(repo)
        self.assertEqual(4, len(first))
        self.assertEqual(first, c.staged_inputs(repo))
        path = repo / next(iter(first))
        path.write_bytes(b"changed-inert-fixture")
        self.assertNotEqual(first, c.staged_inputs(repo))

    def test_coordinate_level_maven_metadata_and_checksums_are_allowed(self):
        repo = self.staging()
        coordinate = repo / c.GROUP.replace('.', '/') / c.ROOTS[0]
        (coordinate / 'maven-metadata.xml').write_bytes(b"inert-xml-fixture")
        (coordinate / 'maven-metadata.xml.sha256').write_bytes(b"inert-checksum-fixture")
        self.assertEqual(6, len(c.staged_inputs(repo)))

    def test_wrong_group_coordinate_version_and_directory_layout_fail_closed(self):
        repo = self.staging()
        invalid = [repo / 'foreign', repo / c.GROUP.replace('.', '/') / 'nativecmpkit-share',
                   repo / c.GROUP.replace('.', '/') / c.ROOTS[0] / '0.1.0-preview.2',
                   repo / c.GROUP.replace('.', '/') / c.ROOTS[0] / c.VERSION / 'nested']
        for path in invalid:
            with self.subTest(path=path):
                path.mkdir()
                with self.assertRaises(c.ConsumerEvidenceError): c.staged_inputs(repo)
                path.rmdir()

    def test_staging_symlinks_hardlinks_and_nonregular_files_are_rejected_before_read(self):
        repo = self.staging()
        original = next(repo.rglob('*.jar'))
        link = original.with_suffix('.link')
        link.symlink_to(original)
        with self.assertRaises(ValueError): c.staged_inputs(repo)
        link.unlink()
        os.link(original, link)
        with self.assertRaises(c.ConsumerEvidenceError): c.staged_inputs(repo)
        link.unlink()
        if hasattr(os, 'mkfifo'):
            os.mkfifo(link)
            with self.assertRaises(c.ConsumerEvidenceError): c.staged_inputs(repo)

    def test_staging_bounds_and_missing_fourth_coordinate_cannot_be_success(self):
        repo = self.staging()
        with patch.object(c, 'MAX_REPOSITORY_BYTES', 4):
            with self.assertRaises(c.ConsumerEvidenceError): c.staged_inputs(repo)
        shutil.rmtree(repo / c.GROUP.replace('.', '/') / c.ROOTS[0])
        with self.assertRaises(c.ConsumerEvidenceError): c.staged_inputs(repo)


class ResolutionTests(TemporaryTest):
    def test_all_four_classpaths_require_exact_core_and_io_staged_bytes(self):
        document, staged, bindings = self.resolution()
        result = c.resolution_contract(document, staged, bindings)
        self.assertEqual(4, result['classpath_count'])
        self.assertEqual(8, len(result['candidate_artifact_rows']))

    def test_missing_classpath_or_root_tampered_bytes_and_duplicate_rows_fail(self):
        document, staged, bindings = self.resolution()
        for changed in [dict(document, resolved_artifacts=document['resolved_artifacts'][1:]),
                        dict(document, resolved_artifacts=document['resolved_artifacts'] + [document['resolved_artifacts'][0]])]:
            with self.assertRaises(c.ConsumerEvidenceError): c.resolution_contract(changed, staged, bindings)
        wrong = deepcopy(staged)
        next(iter(wrong.values()))['sha256'] = 'b' * 64
        with self.assertRaises(c.ConsumerEvidenceError): c.resolution_contract(document, wrong, bindings)

    def test_foreign_old_calf_coordinate_or_wrong_version_fail(self):
        document, staged, bindings = self.resolution()
        for key, value in [('group', 'com.mohamedrejeb.calf'), ('module', 'nativecmpkit-share-desktop'),
                           ('module', 'nativecmpkit-core'), ('version', '0.1.0-preview.2')]:
            with self.subTest(key=key, value=value):
                changed = deepcopy(document)
                changed['resolved_artifacts'][0][key] = value
                with self.assertRaises(c.ConsumerEvidenceError): c.resolution_contract(changed, staged, bindings)

    def test_missing_extra_or_invalid_resolved_row_fields_are_rejected(self):
        document, staged, bindings = self.resolution()
        changes = [('bytes', 0), ('bytes', True), ('sha256', 'invalid'), ('file', '../escape.jar'),
                   ('file', 'wrong.jar'), ('configuration', 'unselected'), ('group', None)]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                changed = deepcopy(document)
                changed['resolved_artifacts'][0][key] = value
                with self.assertRaises(c.ConsumerEvidenceError): c.resolution_contract(changed, staged, bindings)
        changed = deepcopy(document)
        changed['resolved_artifacts'][0]['project_substitution'] = True
        with self.assertRaises(c.ConsumerEvidenceError): c.resolution_contract(changed, staged, bindings)

    def test_partial_report_cannot_claim_full_matrix_release_or_another_variant_inventory(self):
        document, staged, bindings = self.resolution()
        for key, value in [('complete_21_root_KMP_matrix_requested', True), ('release_readiness_certified', True),
                           ('candidate_variants_resolved', ['nativecmpkit-core-desktop']), ('candidate_version', '0.1.0-preview.2'),
                           ('publication_roots_requested', ['nativecmpkit-core']), ('schema_version', True), ('schema_version', 1)]:
            with self.subTest(key=key, value=value):
                changed = dict(document, **{key: value})
                with self.assertRaises(c.ConsumerEvidenceError): c.resolution_contract(changed, staged, bindings)

    def test_bounded_json_rejects_duplicates_nonfinite_and_symlinks(self):
        path = self.root / 'receipt.json'
        for data in [b'{"value":1,"value":2}', b'{"value":NaN}', b'[]']:
            path.write_bytes(data)
            with self.assertRaises(ValueError): c.json_document(path)
        path.write_text('{"value":1}')
        with self.assertRaises(c.ConsumerEvidenceError): c.json_document(path, maximum=1)
        link = self.root / 'link.json'
        link.symlink_to(path)
        with self.assertRaises(c.ConsumerEvidenceError): c.json_document(link)

    def test_read_atime_is_not_a_content_or_identity_change(self):
        path = self.root / 'receipt.json'
        path.write_text('{"value":1}')
        os.utime(path, ns=(0, path.stat().st_mtime_ns))
        self.assertEqual({'value': 1}, c.json_document(path))

    def test_fresh_resolution_checks_bytes_and_rejects_stale_report(self):
        consumer = self.root / 'consumer'
        path = consumer / 'build/reports/partial-consumer-resolution.json'
        path.parent.mkdir(parents=True)
        document, staged, bindings = self.resolution()
        path.write_text(json.dumps(document))
        stamp = time.time_ns()
        actual, review = c.fresh_resolution(consumer, staged, bindings, stamp - 1_000_000_000, stamp)
        self.assertEqual(document, actual)
        self.assertEqual(4, review['classpath_count'])
        os.utime(path, ns=(stamp - 30_000_000_000, stamp - 30_000_000_000))
        with self.assertRaises(c.ConsumerEvidenceError): c.fresh_resolution(consumer, staged, bindings, stamp, stamp)

    def test_static_partial_scope_is_not_the_default_full_publication_gate(self):
        good = {'success': True, 'check_count': 308, 'failed_check_count': 0, 'group': c.GROUP, 'version': c.VERSION,
                'modules': list(c.ROOTS), 'targets': ['metadata', 'desktop'], 'native_platforms_requested': ['linux-x64'],
                'complete_declared_artifact_matrix_requested': False, 'release_readiness_certified': False}
        c.static_contract(good)
        for key, value in [('success', False), ('check_count', 0), ('failed_check_count', 1),
                           ('modules', ['nativecmpkit-core']), ('complete_declared_artifact_matrix_requested', True),
                           ('release_readiness_certified', True)]:
            with self.subTest(key=key, value=value), self.assertRaises(c.ConsumerEvidenceError):
                c.static_contract(dict(good, **{key: value}))


class FreshXmlTests(TemporaryTest):
    def discard_owned_synthetic_capture(self, output):
        for path in (output / 'junit', output / 'test-outcomes.json'):
            if path.is_dir(): shutil.rmtree(path)
            elif path.exists(): path.unlink()

    def test_seven_exact_synthetic_cases_and_xml_hashes_pass_tooling_only(self):
        args = self.reports()
        result = c.fresh_tests(*args)
        self.assertEqual(7, result['totals']['executed'])
        self.assertEqual(7, result['totals']['passed'])
        self.assertEqual(2, len(result['reports']))
        for report in result['reports']:
            self.assertEqual(report['sha256'], c.lt.sha256(args[1] / report['path']))

    def test_no_stale_missing_or_future_xml_is_accepted(self):
        args = self.reports()
        path = next((args[0] / 'build/test-results/test').glob('TEST-*.xml'))
        stamp = time.time_ns()
        for age in (-30_000_000_000, 30_000_000_000):
            os.utime(path, ns=(stamp + age, stamp + age))
            with self.assertRaises(c.ConsumerEvidenceError): c.fresh_tests(*args)
            shutil.rmtree(args[1] / 'junit')
        path.unlink()
        with self.assertRaises(c.ConsumerEvidenceError): c.fresh_tests(*args)

    def test_missing_duplicate_or_wrong_gradle_jdk_task_marker_fails(self):
        args = self.reports()
        valid = args[-1].read_text()
        for text in ['', valid + valid, valid.replace('9.7.1', '9.7.0'), valid.replace('java=17', 'java=21'),
                     valid.replace('task=:test', 'task=:desktopTest')]:
            args[-1].write_text(text)
            with self.assertRaises(c.ConsumerEvidenceError): c.fresh_tests(*args)

    def test_failed_and_skipped_cases_stay_failed_not_not_applicable(self):
        args = self.reports()
        path = next((args[0] / 'build/test-results/test').glob('TEST-*.xml'))
        original = path.read_bytes()
        for tag in ('failure', 'error', 'skipped'):
            document = ET.fromstring(original)
            ET.SubElement(next(document.iter('testcase')), tag)
            path.write_bytes(ET.tostring(document))
            with self.assertRaises(c.ConsumerEvidenceError): c.fresh_tests(*args)
            observed = json.loads((args[1] / 'test-outcomes.json').read_text())
            self.assertEqual(7, observed['totals']['tests'])
            self.assertEqual(6, observed['totals']['passed'])
            self.discard_owned_synthetic_capture(args[1])

    def test_missing_new_or_duplicate_method_does_not_replace_the_required_origin_assertion(self):
        args = self.reports()
        path = args[0] / 'build/test-results/test/TEST-nativecmpkit.consumer.PublishedArtifactOriginTest.xml'
        original = path.read_bytes()
        for change in ('rename', 'delete', 'duplicate'):
            document = ET.fromstring(original)
            case = next(document.iter('testcase'))
            if change == 'rename': case.set('name', 'differentScenario')
            elif change == 'delete': document.remove(case)
            else: ET.SubElement(document, 'testcase', classname=case.get('classname'), name=case.get('name'))
            path.write_bytes(ET.tostring(document))
            with self.assertRaises(ValueError): c.fresh_tests(*args)
            self.discard_owned_synthetic_capture(args[1])

    def test_symlinked_hardlinked_or_dtd_reports_fail_closed(self):
        args = self.reports()
        path = next((args[0] / 'build/test-results/test').glob('TEST-*.xml'))
        original = path.read_bytes()
        outside = self.root / 'outside.xml'
        path.rename(outside)
        path.symlink_to(outside)
        with self.assertRaises(ValueError): c.fresh_tests(*args)
        path.unlink()
        os.link(outside, path)
        with self.assertRaises(c.ConsumerEvidenceError): c.fresh_tests(*args)
        shutil.rmtree(args[1] / 'junit')
        path.unlink()
        path.write_bytes(b'<!DOCTYPE testsuite [<!ENTITY external SYSTEM "file:///unused">]>' + original)
        with self.assertRaises(ValueError): c.fresh_tests(*args)


class ControllerPreflightTests(TemporaryTest):
    def model_run(self, *, consumer_exit=0, source_changed=False, cache_candidate=False, staged_changed=False, copy_changed=False):
        self.fixture()
        revision = 'a' * 40
        context = {'source_revision': revision, 'source_tree_dirty': False, 'host': {'system': 'Linux', 'architecture': 'x64'},
                   'java': {'major': 17}, 'rust': {'release': '1.98.0'}, 'android_platform': {'package': 'platforms;android-37.0'},
                   'compiler_runtime_fingerprint': 'b' * 64}
        static = {'success': True, 'check_count': 1, 'failed_check_count': 0, 'group': c.GROUP, 'version': c.VERSION,
                  'modules': list(c.ROOTS), 'targets': ['metadata', 'desktop'], 'native_platforms_requested': ['linux-x64'],
                  'complete_declared_artifact_matrix_requested': False, 'release_readiness_certified': False}
        calls = []

        def simulated_execute(cwd, command, log, timeout, reserve, *, env):
            # Inert artifacts/XML only. This never starts Gradle/Java or a library.
            calls.append((cwd, command, env))
            if command[-1] == 'stageCoreIoVerificationPublications':
                self.staging(metadata=True)
                tasks = [f':calf-{module}:publish{publication}PublicationToNativecmpkitVerificationRepository'
                         for module in ('core', 'io') for publication in ('KotlinMultiplatform', 'Desktop')]
                log.write_text(''.join('NATIVECMPKIT_PARTIAL_STAGE task=' + task + ' group=' + c.GROUP + ' version=' + c.VERSION + '\n' for task in tasks))
                return {'exit_code': 0, 'elapsed_seconds': 0.0}
            document, _, _ = self.resolution()
            staged = c.staged_inputs(self.root / c.REPOSITORY)
            bindings = c.module_file_bindings(self.root / c.REPOSITORY, staged)
            for row in document['resolved_artifacts']:
                row.update(bindings[row['module']])
                row['file'] = row['declared_file_name']
            path = cwd / 'build/reports/partial-consumer-resolution.json'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(document))
            folder = cwd / 'build/test-results/test'
            folder.mkdir(parents=True)
            for classname in sorted({cls for cls, name in c.EXPECTED_CASES}):
                suite = ET.Element('testsuite')
                for cls, name in sorted(c.EXPECTED_CASES):
                    if cls == classname: ET.SubElement(suite, 'testcase', classname=cls, name=name)
                (folder / ('TEST-' + classname + '.xml')).write_bytes(ET.tostring(suite))
            log.write_text('NATIVECMPKIT_PARTIAL_CONSUMER_TEST task=:test gradle=9.7.1 java=17\n')
            if cache_candidate:
                file = self.root / c.GRADLE_HOME / 'caches/modules-2/files-2.1' / c.GROUP / 'foreign.jar'
                file.parent.mkdir(parents=True)
                file.write_bytes(b'inert-candidate-must-not-be-exported')
            if staged_changed:
                next((self.root / c.REPOSITORY).rglob('*.jar')).write_bytes(b'inert-artifact-changed-after-consumption')
            if copy_changed:
                (cwd / 'README.md').write_text('inert-copy-changed-after-consumption')
            return {'exit_code': consumer_exit, 'elapsed_seconds': 0.0}

        before = {'model-input': 'b' * 64}
        after = {'model-input': 'c' * 64} if source_changed else before
        with patch.object(c.lt, 'git_revision', return_value=revision), \
             patch.object(c.runtime_context, 'capture', return_value=context), \
             patch.object(c.shutil, 'disk_usage', return_value=shutil._ntuple_diskusage(20 * 1024**3, 0, 20 * 1024**3)), \
             patch.object(c, 'inputs', side_effect=[before, after, after] if source_changed else [before, before, before]), \
             patch.object(c, 'environment', side_effect=lambda *args, consumer=False: {'synthetic_owned_phase': 'consumer' if consumer else 'producer'}), \
             patch.object(c, 'verify_static', return_value=static), \
             patch.object(c.lt, 'execute', side_effect=simulated_execute):
            result = c.run(self.root, 'build/ci-consumer/model')
        return result, calls

    def test_synthetic_full_controller_keeps_independent_cwd_scope_bytes_and_source_bindings(self):
        result, calls = self.model_run()
        self.assertTrue(result['passed'])
        self.assertEqual(7, result['actual_consumer_methods_verified'])
        self.assertEqual(2, len(calls))
        self.assertEqual(self.root, calls[0][0])
        self.assertEqual(self.root / 'build/ci-consumer/model/independent-consumer', calls[1][0])
        self.assertEqual({'synthetic_owned_phase': 'producer'}, calls[0][2])
        self.assertEqual({'synthetic_owned_phase': 'consumer'}, calls[1][2])
        self.assertTrue(result['cache_containment']['candidate_payload_group_absent_before'])
        self.assertTrue(result['cache_containment']['candidate_payload_group_absent_after'])
        self.assertTrue(result['cache_containment']['consumer_home_fresh_and_not_cached'])
        self.assertTrue(result['staging_inputs_held'])
        self.assertTrue(result['independent_fixture_inputs_held'])
        self.assertTrue(result['source_inputs_held'])
        self.assertTrue(result['owned_lock_removed'])
        self.assertFalse(result['release_readiness_certified'])
        self.assertFalse(result['ordinary_dependency_trust_certified'])
        self.assertFalse(result['packages_published'])
        self.assertEqual([], result['changed_inputs'])

    def test_nonzero_consumer_cannot_be_promoted_from_complete_passing_synthetic_xml(self):
        result, calls = self.model_run(consumer_exit=1)
        self.assertFalse(result['passed'])
        self.assertEqual(0, result['actual_consumer_methods_verified'])
        self.assertEqual(7, result['consumer_tests']['totals']['passed'])
        self.assertTrue(result['source_inputs_held'])
        self.assertTrue((self.root / 'build/ci-consumer/model/test-outcomes.json').is_file())
        self.assertTrue(result['owned_lock_removed'])

    def test_changed_inputs_override_passing_synthetic_staging_and_xml(self):
        result, _ = self.model_run(source_changed=True)
        self.assertFalse(result['passed'])
        self.assertFalse(result['source_inputs_held'])
        self.assertEqual(['model-input'], result['changed_inputs'])
        self.assertEqual(0, result['actual_consumer_methods_verified'])
        self.assertTrue(result['owned_lock_removed'])

    def test_new_candidate_in_producer_cache_forbids_success_and_preserves_the_data(self):
        result, _ = self.model_run(cache_candidate=True)
        self.assertFalse(result['passed'])
        self.assertFalse(result['cache_containment']['candidate_payload_group_absent_after'])
        self.assertEqual('producer-cache-containment', result['error']['phase'])
        file = self.root / c.GRADLE_HOME / 'caches/modules-2/files-2.1' / c.GROUP / 'foreign.jar'
        self.assertEqual(b'inert-candidate-must-not-be-exported', file.read_bytes())
        self.assertTrue((self.root / 'build/ci-consumer/model/producer-cache-after.json').is_file())

    def test_failed_consumer_still_records_changed_staging_and_copied_source(self):
        result, _ = self.model_run(consumer_exit=1, staged_changed=True, copy_changed=True)
        self.assertFalse(result['passed'])
        self.assertFalse(result['staging_inputs_held'])
        self.assertFalse(result['independent_fixture_inputs_held'])
        self.assertEqual(0, result['actual_consumer_methods_verified'])
        self.assertTrue((self.root / 'build/ci-consumer/model/staging-after.json').is_file())
        self.assertTrue((self.root / 'build/ci-consumer/model/fixture-copy-after.json').is_file())

    def test_preexecution_reserve_rejection_starts_no_java_and_preserves_false_receipt(self):
        with patch.object(c.lt, 'git_revision', return_value='a' * 40), \
             patch.object(c.shutil, 'disk_usage', return_value=shutil._ntuple_diskusage(10, 9, 1)), \
             patch.object(c.lt, 'execute') as execute, patch.object(c.runtime_context, 'capture') as runtime:
            result = c.run(self.root, 'build/ci-consumer/reserve-rejected')
        self.assertFalse(result['passed'])
        self.assertEqual(0, result['actual_consumer_methods_verified'])
        self.assertFalse(result['release_readiness_certified'])
        self.assertIn('Disk reserve unavailable', result['error']['contract'])
        execute.assert_not_called()
        runtime.assert_not_called()
        self.assertFalse((self.root / 'build/ci-consumer/.core-io-consumer.lock').exists())
        self.assertEqual(result, json.loads((self.root / 'build/ci-consumer/reserve-rejected/receipt.json').read_text()))

    def test_existing_lock_is_not_unlinked_or_treated_as_permission_to_run(self):
        lock = self.root / 'build/ci-consumer/.core-io-consumer.lock'
        lock.parent.mkdir(parents=True)
        lock.write_text('foreign')
        with patch.object(c.lt, 'git_revision', return_value='a' * 40), patch.object(c.lt, 'execute') as execute:
            result = c.run(self.root, 'build/ci-consumer/locked')
        self.assertFalse(result['passed'])
        self.assertEqual('foreign', lock.read_text())
        execute.assert_not_called()

    def test_unsafe_or_preexisting_output_is_rejected_without_deletion(self):
        for path in ('build/ci-consumer', '../escape', '/outside', 'tests/consumer/output'):
            with self.subTest(path=path), self.assertRaises(ValueError): c.run(self.root, path)
        output = self.root / 'build/ci-consumer/previous'
        output.mkdir(parents=True)
        sentinel = output / 'preserve.txt'
        sentinel.write_text('preserve')
        with self.assertRaises(c.ConsumerEvidenceError): c.run(self.root, 'build/ci-consumer/previous')
        self.assertEqual('preserve', sentinel.read_text())


if __name__ == '__main__':
    unittest.main()
