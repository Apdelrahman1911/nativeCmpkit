"""New source/focus/receipt guards only; modeled XML/SDK refusals are NOT Android runs."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import android_device_tests as device
import android_io_documents as helper
import dependency_cache_inputs as cache
import library_tests as r
import workflow_matrix as matrix

FOCUS = 'android-io-reference-regressions'
CLASS = 'com.mohamedrejeb.calf.io.AndroidIoReferenceRegressionTest'
SOURCE = helper.KOTLIN + 'AndroidIoReferenceRegressionTest.kt'
CALLER = helper.KOTLIN + 'AndroidIoSingleDocumentGrantActivity.kt'
OWNER = helper.JAVA + 'IoSingleDocumentGrantActivity.java'
PROVIDER = helper.KOTLIN + 'instrumentation/DeviceIoFileProvider.kt'
PATHS = 'calf-io/src/androidDeviceTest/res/xml/nativecmpkit_io_device_paths.xml'
REPORTER_MANIFEST = 'calf-io/src/androidDeviceTest/AndroidManifest.xml'
ANDROID = '{http://schemas.android.com/apk/res/android}'
METHODS = (
    'nativeFileProviderSingleFileMetadataAndNonPersistableAccessStayDistinctFromTrees',
    'nativeSandboxFileUriSupportsDecodedPathsBookmarksDirectoriesAndMissingReadFailures',
    'nativeOrdinaryDocumentGrantBookmarkAndOwnerRevokeNeverBecomeTreeAccess',
)
BASE_ANDROID_MODULES = {'calf-io', 'calf-file-picker', 'calf-geo', 'calf-webview',
                        'calf-ui', 'calf-navigation', 'calf-share', 'calf-camera-picker'}


class AndroidIoReferenceRegressionGuards(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='nativecmpkit-io-reference-model-')
        self.addCleanup(temporary.cleanup); self.root = Path(temporary.name)
        self.write('settings.gradle.kts', 'include(\n    ":calf-io",\n)\n')
        self.write('calf-io/src/commonTest/kotlin/Unrelated.kt', '// retained, never selected for execution\n')
        for relative in (*helper.SOURCE_FILES, 'scripts/ci/android_io_documents.py',
                'scripts/ci/library_tests.py', 'scripts/ci/dependency_cache_inputs.py',
                'scripts/ci/library_dependency_cache.py', 'scripts/ci/runtime_context.py'):
            self.copy(relative)
        for relative in (helper.FIXTURE, 'calf-io/src/androidDeviceTest'):
            for path in (r.ROOT / relative).rglob('*'):
                if path.is_file() and 'build' not in path.relative_to(r.ROOT).parts:
                    self.copy(path.relative_to(r.ROOT).as_posix())

    def copy(self, relative):
        target = self.root / relative; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((r.ROOT / relative).read_bytes())

    def write(self, relative, value):
        target = self.root / relative; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value); return target

    def plan(self):
        return r.plan(self.root, 'android-device', only_modules=('calf-io',), focus=FOCUS)

    def identities(self):
        return [{'classname': CLASS, 'name': method} for method in METHODS]

    def prepared(self):
        source = self.plan()['android_io_documents']['source_contract']
        return {'package': helper.PACKAGE, 'source_fixture': helper.FIXTURE, 'prepare_status': 'passed',
            'verification_api_level': 35, 'recipient_installed': True, 'manual_URI_grant': False,
            'automatic_runtime_permission_grant': False, 'source_apk_sha256': 'a' * 64,
            'source_contract': source,
            'installed_readback': {'apk_sha256': 'a' * 64, 'exact_one_APK_path_observed': True},
            'apk_policy': {'compiled_manifest_inspected': True, 'content_requires_android_grant': True,
                'signature_control_only': True, 'certificate_sha256': 'b' * 64,
                'private_key_certificate_sha256': 'b' * 64,
                'signature_verification_min_sdk_version': 35, 'signature_verification_max_sdk_version': 35}}

    def compiled_manifest(self):
        root = ET.fromstring((self.root / helper.FIXTURE / 'src/main/AndroidManifest.xml').read_bytes())
        root.set('package', helper.PACKAGE)
        ET.SubElement(root, 'uses-sdk', {ANDROID + 'minSdkVersion': '23', ANDROID + 'targetSdkVersion': '37'})
        root.find('application').set(ANDROID + 'debuggable', 'true')
        root.find('application/provider').set(ANDROID + 'authorities', helper.PACKAGE + '.documents')
        return root

    def collect(self, cases=None, *, marker=1, split=False, age=0):
        plan = self.plan(); cases = self.identities() if cases is None else cases
        folder = self.root / plan['expected'][0]['report_directory']
        if folder.exists(): shutil.rmtree(folder)
        chunks = [cases[:1], cases[1:]] if split else [cases]
        for index, chunk in enumerate(chunks):
            suite = ET.Element('testsuite')
            for case in chunk:
                node = ET.SubElement(suite, 'testcase', classname=case['classname'], name=case['name'])
                if case.get('status', 'passed') != 'passed': ET.SubElement(node, case['status'])
            target = folder / ('TEST-reference-model-' + str(index) + '.xml')
            target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(ET.tostring(suite))
        now = time.time_ns()
        return r.collect_reports(self.root, plan, now - 1_000_000_000 + age, now + 1_000_000_000 + age,
                                 Counter({plan['expected'][0]['task']: marker}))

    def test_exact_three_authored_methods_class_dependencies_and_one_real_task_only(self):
        self.assertTrue(r.allowed_test_focus('android-device', ('calf-io',), FOCUS))
        plan = self.plan(); item, = plan['expected']
        self.assertTrue(r.validate_test_focus(plan)); self.assertFalse(plan['complete_suite_requested'])
        self.assertEqual(CLASS, item['test_filter']); self.assertEqual(self.identities(), item['required_testcases'])
        self.assertEqual(':calf-io:connectedAndroidDeviceTest', item['task'])
        self.assertEqual('calf-io/build/outputs/androidTest-results/connected/androidMain', item['report_directory'])
        for relative in (SOURCE, CALLER, PROVIDER, helper.KOTLIN + 'DeviceDescriptorProbe.kt',
                         helper.KOTLIN + 'OwnedIoEndpoint.kt', helper.KOTLIN + 'AndroidIoProviderContract.kt'):
            self.assertIn(relative, item['test_source_files'])
        self.assertIn(r.ANDROID_IO_PROVIDER_SOURCE, item['test_source_files'], 'Compile authored source; do not replay its methods')
        self.assertIn(r.ANDROID_IO_DEFAULT_DECODE_SOURCE, item['test_source_files'], 'Compile authored source; do not replay its methods')
        self.assertFalse(set(METHODS) & (set(r.ANDROID_IO_PROVIDER_METHODS) | set(r.ANDROID_IO_DEFAULT_DECODE_METHODS)))
        self.assertNotIn(r.android_io_oversize_identities()[0], item['required_testcases'])

    def test_new_profile_options_are_exact_additions_without_a_future_module_maximum(self):
        row, = matrix.matrix(FOCUS)['include']
        self.assertEqual(('android-device-api35', 'android-device', '35', 'calf-io', FOCUS),
                         (row['slot'], row['suite'], row['emulator-api'], row['test-modules'], row['test-focus']))
        self.assertEqual(11, len(matrix.matrix('all')['include']))
        self.assertTrue(BASE_ANDROID_MODULES <= set(r.MINIMUM_MODULES['android-device']))
        choices = re.search(r'options: \[([^\n]+)\]', (r.ROOT / '.github/workflows/gradle.yml').read_text()).group(1)
        values = [part.strip() for part in choices.split(',')]
        self.assertEqual(set(matrix.PROFILES), set(values)); self.assertEqual(len(values), len(set(values)))
        workflow = (r.ROOT / '.github/workflows/gradle.yml').read_text()
        self.assertIn("inputs.profile == '" + FOCUS + "'", workflow)
        self.assertIn('build-tools;36.0.0', workflow)

    def test_wrong_suite_module_duplicate_wildcard_and_api23_fail_before_host_or_outputs(self):
        for suite, modules, focus in (('desktop', ('calf-io',), FOCUS), ('android-host', ('calf-io',), FOCUS),
                ('android-device', ('calf-ui',), FOCUS), ('android-device', ('calf-io', 'calf-io'), FOCUS),
                ('android-device', ('calf-io', 'calf-ui'), FOCUS), ('android-device', ('calf-io',), 'android-io-reference-*')):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                r.plan(self.root, suite, only_modules=modules, focus=focus)
        with patch.object(device, 'require_host') as host:
            with self.assertRaises(ValueError):
                device.run(self.root, 'build/ci-verification/refused', only_modules=('calf-io',), focus=FOCUS, api_level=23)
            host.assert_not_called()
        self.assertFalse((self.root / 'build').exists())

    def test_two_real_read_only_clis_select_only_the_three_cases_without_outputs_or_builds(self):
        commands = [
            [sys.executable, '-B', str(r.ROOT / 'scripts/ci/library_tests.py'), 'plan',
             '--suite', 'android-device', '--module', 'calf-io', '--focus', FOCUS],
            [sys.executable, '-B', str(r.ROOT / 'scripts/ci/android_device_tests.py'), 'plan',
             '--output', 'build/ci-plan', '--api-level', '35', '--module', 'calf-io', '--focus', FOCUS],
        ]
        for command in commands:
            result = subprocess.run(command, cwd=r.ROOT, capture_output=True, text=True, timeout=30, check=False)
            self.assertEqual(0, result.returncode, 'Read-only CLI refused; retain private diagnostic outside this assertion')
            plan = json.loads(result.stdout); item, = plan['expected']
            self.assertEqual(FOCUS, plan['explicit_test_focus']); self.assertEqual(self.identities(), item['required_testcases'])
            self.assertFalse(plan['android_io_documents']['source_contract']['native_or_compile_success_inferred'])
        self.assertFalse((r.ROOT / 'build/ci-plan').exists())

    def test_matrix_preflight_uses_actual_controller_plan_route_not_a_build_or_library_parser_fallback(self):
        plan = self.plan()
        with patch.object(matrix.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps(plan), '')) as run:
            result = matrix.preflight_plans(FOCUS, root=self.root)
        row, = result['slots']; command = run.call_args.args[0]
        self.assertTrue(result['source_only']); self.assertEqual(0, result['Gradle_builds_executed'])
        self.assertEqual(0, result['library_tests_executed']); self.assertEqual(1, row['expected_modules'])
        self.assertEqual(str(self.root / 'scripts/ci/android_device_tests.py'), command[2])
        self.assertEqual('plan', command[3]); self.assertEqual('35', command[command.index('--api-level') + 1])
        self.assertEqual(FOCUS, command[command.index('--focus') + 1]); self.assertEqual('calf-io', command[command.index('--module') + 1])
        self.assertNotIn('run', command); self.assertFalse((self.root / 'build').exists())

    def test_changed_filter_route_identity_source_list_and_expected_order_cannot_be_laundered(self):
        original = self.plan()
        for key, value in (('module', 'calf-ui'), ('project', ':calf-ui'), ('task', ':calf-io:testAndroidHostTest'),
                ('report_directory', 'calf-io/build/test-results/desktopTest'), ('test_filter', CLASS + '#*'),
                ('required_testcases', self.identities()[:-1]), ('required_testcases', self.identities()[::-1]),
                ('required_testcases', self.identities() + self.identities()[:1]), ('test_filter_argument', 'annotation'),
                ('test_exclusion_annotation', 'org.junit.Test')):
            altered = deepcopy(original); altered['expected'][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError): r.validate_test_focus(altered)
        for relative in (SOURCE, CALLER, PROVIDER, helper.KOTLIN + 'DeviceDescriptorProbe.kt',
                         helper.KOTLIN + 'OwnedIoEndpoint.kt', helper.KOTLIN + 'AndroidIoProviderContract.kt'):
            altered = deepcopy(original); altered['expected'][0]['test_source_files'].remove(relative)
            with self.subTest(relative=relative), self.assertRaises(ValueError): r.validate_test_focus(altered)
        for key, value in (('complete_suite_requested', True), ('explicit_module_subset', ['calf-ui']), ('suite', 'desktop')):
            altered = deepcopy(original); altered[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): r.validate_test_focus(altered)
        altered = deepcopy(original); altered.pop('android_io_documents')
        with self.assertRaises(ValueError): r.validate_test_focus(altered)

    def test_modeled_positive_results_have_three_unique_cases_one_fresh_xml_and_no_order_inference(self):
        result = self.collect(self.identities()[::-1])
        self.assertEqual([], result['errors']); self.assertEqual(3, result['totals']['executed'])
        self.assertEqual(3, result['totals']['passed']); self.assertEqual(1, len(result['modules'][0]['reports']))
        self.assertTrue(all(case['source'] == SOURCE for case in result['modules'][0]['native_scenarios']))

    def test_missing_unrelated_duplicate_split_stale_skipped_failure_error_and_markers_refuse_results(self):
        good = self.identities()
        for cases in ([], good[:-1], good + good[:1], good + [{'classname': CLASS, 'name': 'unrelated'}],
                      [{**good[0], 'classname': r.ANDROID_IO_PROVIDER_CLASS}, *good[1:]]):
            with self.subTest(cases=cases): self.assertTrue(self.collect(cases)['errors'])
        for status in ('skipped', 'failure', 'error'):
            with self.subTest(status=status): self.assertTrue(self.collect([{**good[0], 'status': status}, *good[1:]])['errors'])
        self.assertTrue(self.collect(split=True)['errors']); self.assertTrue(self.collect(age=100_000_000_000)['errors'])
        for marker in (0, 2):
            with self.subTest(marker=marker): self.assertTrue(self.collect(marker=marker)['errors'])

    def test_changed_ignored_missing_duplicate_and_reordered_native_declarations_refuse_source_plan(self):
        self.plan(); path = self.root / SOURCE; original = path.read_text()
        mutations = [original.replace('@Test fun ' + METHODS[0], '@Ignore\n    @Test fun ' + METHODS[0]),
            original.replace(METHODS[0], 'unreviewedMethod'),
            original.replace(METHODS[1], METHODS[0]),
            original.replace(METHODS[0], 'temporaryOrderedName').replace(METHODS[1], METHODS[0]).replace('temporaryOrderedName', METHODS[1])]
        for index, body in enumerate(mutations):
            path.write_text(body)
            with self.subTest(index=index), self.assertRaises(ValueError): self.plan()
            path.write_text(original)
        path.unlink()
        with self.assertRaises((OSError, ValueError)): self.plan()

    def test_exact_twenty_five_source_inputs_include_six_java_ten_kotlin_existing_provider_and_paths(self):
        value = helper.source_contract(self.root); helper.validate_source_receipt(value)
        self.assertEqual(6, len(helper.JAVA_NAMES)); self.assertEqual(10, len(helper.KOTLIN_NAMES))
        self.assertEqual(25, len(value['source_inputs'])); self.assertEqual(set(helper.SOURCE_FILES), set(value['source_inputs']))
        for relative in (SOURCE, CALLER, OWNER, PROVIDER, PATHS): self.assertIn(relative, value['source_inputs'])
        self.assertFalse(value['native_or_compile_success_inferred']); self.assertEqual(r.input_digest(value['source_inputs']), value['source_inputs_sha256'])
        for relative, digest in value['source_inputs'].items():
            self.assertEqual(hashlib.sha256((self.root / relative).read_bytes()).hexdigest(), digest)
        self.write(helper.JAVA + 'Unrequested.java', 'class Unrequested {}')
        with self.assertRaises(ValueError): helper.source_contract(self.root)

    def test_fixed_document_read_persistable_only_native_callback_scope_and_owner_revoke_are_source_pinned(self):
        helper.source_contract(self.root)
        changes = {
            OWNER: [
                ('buildDocumentUri(IoFixture.AUTHORITY, "bookmark.txt")', 'buildDocumentUri(IoFixture.AUTHORITY, "survivor.bin")'),
                ('Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);', 'Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION | Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);'),
                ('revokeUriPermission(document, Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);', 'revokeUriPermission(document, Intent.FLAG_GRANT_READ_URI_PERMISSION);'),
                ('getCallingPackage()', 'getPackageName()'), ('setResult(code, result);', 'setResult(RESULT_OK, result);'),
            ],
            CALLER: [('startActivityForResult(', 'startActivity('), ('firstDraw && hasWindowFocus()', 'firstDraw')],
            SOURCE: [('onResult(actual)', 'onResult(Intent())'),
                     ('heldBookmark = assertNotNull(reference.createBookmark(context))', 'heldBookmark = reference.toUriString()'),
                     ('assertNull(uri.query,', 'assertNotNull(uri.query,'),
                     ('= runBlocking(Dispatchers.IO)', '= runBlocking(Dispatchers.Main)'),
                     ('assertEquals(0, openDeviceDescriptorsFor(identity))', 'assertEquals(1, openDeviceDescriptorsFor(identity))')],
        }
        for relative, replacements in changes.items():
            path = self.root / relative; original = path.read_text()
            for old, new in replacements:
                self.assertIn(old, original); path.write_text(original.replace(old, new))
                with self.subTest(relative=relative, old=old), self.assertRaises(ValueError): helper.source_contract(self.root)
                path.write_text(original)
        path = self.root / SOURCE; original = path.read_text()
        path.write_text(original + '\nfun forbiddenGrant() { context.grantUriPermission("unreviewed", uri, 1) }\n')
        with self.assertRaises(ValueError): helper.source_contract(self.root)

    def test_each_exact_helper_activity_keeps_signature_export_process_and_no_implicit_routes_in_both_manifest_forms(self):
        for compiled in (False, True):
            baseline = self.compiled_manifest() if compiled else ET.fromstring((self.root / helper.FIXTURE / 'src/main/AndroidManifest.xml').read_bytes())
            self.assertTrue(helper.validate_manifest(ET.tostring(baseline), compiled=compiled)['content_requires_android_grant'])
            for index in range(2):
                for field, value in (('permission', 'android.permission.READ_EXTERNAL_STORAGE'), ('exported', 'false'),
                                     ('process', ':wrong'), ('enabled', 'false'), ('name', helper.PACKAGE + '.UnrequestedActivity')):
                    root = deepcopy(baseline); root.find('application').findall('activity')[index].set(ANDROID + field, value)
                    with self.subTest(compiled=compiled, index=index, field=field), self.assertRaises(ValueError):
                        helper.validate_manifest(ET.tostring(root), compiled=compiled)
                root = deepcopy(baseline); ET.SubElement(root.find('application').findall('activity')[index], 'intent-filter')
                with self.assertRaises(ValueError): helper.validate_manifest(ET.tostring(root), compiled=compiled)
            root = deepcopy(baseline); root.find('application').append(deepcopy(root.find('application/activity')))
            with self.assertRaises(ValueError): helper.validate_manifest(ET.tostring(root), compiled=compiled)

    def test_private_caller_fileprovider_and_only_fixed_cache_paths_refuse_public_routes_or_broad_storage(self):
        helper.source_contract(self.root)
        path = self.root / REPORTER_MANIFEST; original = path.read_bytes()
        for tag, field, value in (('activity', 'exported', 'true'), ('activity', 'process', ':wrong'),
                ('activity', 'enabled', 'false'), ('provider', 'exported', 'true'), ('provider', 'process', ':wrong'),
                ('provider', 'permission', helper.PERMISSION), ('provider', 'grantUriPermissions', 'false')):
            root = ET.fromstring(original); app = root.find('application')
            node = app.findall('activity')[1] if tag == 'activity' else app.find('provider')
            node.set(ANDROID + field, value); path.write_bytes(ET.tostring(root))
            with self.subTest(tag=tag, field=field), self.assertRaises(ValueError): helper.source_contract(self.root)
            path.write_bytes(original)
        root = ET.fromstring(original); ET.SubElement(root, 'uses-permission', {ANDROID + 'name': 'android.permission.MANAGE_EXTERNAL_STORAGE'})
        path.write_bytes(ET.tostring(root))
        with self.assertRaises(ValueError): helper.source_contract(self.root)
        path.write_bytes(original)
        path = self.root / PATHS; original_paths = path.read_bytes()
        for body in (b'<paths><root-path name="io-device" path="/"/></paths>', b'<paths><cache-path name="io-device" path="."/></paths>'):
            path.write_bytes(body)
            with self.assertRaises(ValueError): helper.source_contract(self.root)
        path.write_bytes(original_paths)

    def test_new_source_caller_manifest_and_every_helper_java_byte_are_library_inputs_not_generated_outputs(self):
        self.plan(); values = r.snapshot_inputs(self.root)
        for relative in (SOURCE, CALLER, OWNER, PROVIDER, PATHS, REPORTER_MANIFEST):
            self.assertEqual(hashlib.sha256((self.root / relative).read_bytes()).hexdigest(), values[relative])
        for name in helper.JAVA_NAMES: self.assertIn(helper.JAVA + name + '.java', values)
        self.write(helper.FIXTURE + '/build/outputs/apk/debug/fake.apk', 'not compiler or native proof')
        self.write(helper.FIXTURE + '/build/android-user/debug.keystore', 'not a source input')
        self.write('calf-io/build/outputs/androidTest-results/connected/androidMain/TEST-fake.xml', '<testsuite/>')
        self.assertEqual(values, r.snapshot_inputs(self.root))

    def test_exact_io_adapter_manifest_configs_key_dependencies_but_java_library_sources_signing_xml_and_outputs_do_not(self):
        values = cache.selected_inputs(self.root, 'libraries'); before = cache.fingerprint('libraries', values)
        recipes = ('scripts/ci/android_io_documents.py', helper.FIXTURE + '/src/main/AndroidManifest.xml',
                   helper.FIXTURE + '/build.gradle.kts', helper.FIXTURE + '/settings.gradle.kts', helper.FIXTURE + '/gradle.properties')
        for relative in recipes:
            self.assertIn(relative, values); path = self.root / relative; original = path.read_bytes()
            path.write_bytes(original + b'\n// modeled dependency-policy alteration; never compiled\n')
            self.assertNotEqual(before, cache.fingerprint('libraries', cache.selected_inputs(self.root, 'libraries')))
            path.write_bytes(original)
        for relative in (SOURCE, CALLER, OWNER, PROVIDER, PATHS):
            self.assertNotIn(relative, values); path = self.root / relative; original = path.read_bytes()
            path.write_bytes(original + b'\n// modeled source byte alteration; never compiled\n')
            self.assertEqual(before, cache.fingerprint('libraries', cache.selected_inputs(self.root, 'libraries')))
            path.write_bytes(original)
        for relative in (helper.FIXTURE + '/build/outputs/apk/debug/fake.apk', helper.FIXTURE + '/build/android-user/debug.keystore',
                         'calf-io/build/outputs/androidTest-results/connected/androidMain/TEST-fake.xml'):
            self.write(relative, 'not a dependency-policy input')
        self.assertEqual(before, cache.fingerprint('libraries', cache.selected_inputs(self.root, 'libraries')))
        for scope in ('core-io', 'webview'):
            selected = cache.selected_inputs(self.root, scope)
            self.assertNotIn(recipes[0], selected); self.assertNotIn(recipes[1], selected)

    def test_connected_class_command_needs_exact_helper_identity_and_assembly_cannot_emit_native_bit(self):
        plan = self.plan(); prepared = self.prepared()
        with self.assertRaises(ValueError):
            r.gradle_command('android-device', plan, root=self.root, android_serial=device.SERIAL)
        command = r.gradle_command('android-device', plan, root=self.root, android_serial=device.SERIAL, android_io_documents_receipt=prepared)
        self.assertEqual(1, command.count(':calf-io:connectedAndroidDeviceTest'))
        self.assertIn('-Pandroid.testInstrumentationRunnerArguments.class=' + CLASS, command)
        self.assertIn('-Pandroid.testInstrumentationRunnerArguments.nativecmpkitOwnedIoDocuments=true', command)
        self.assertFalse(any('#' in value or 'Arguments.annotation=' in value for value in command))
        assembly = r.gradle_command('android-device', plan, root=self.root, android_serial=device.SERIAL, for_assembly=True)
        self.assertIn(':calf-io:assembleAndroidDeviceTest', assembly); self.assertNotIn(':calf-io:connectedAndroidDeviceTest', assembly)
        self.assertFalse(any('nativecmpkitOwnedIoDocuments=' in value for value in assembly))
        altered = deepcopy(prepared); altered['apk_policy']['signature_verification_min_sdk_version'] = True
        with self.assertRaises(ValueError):
            r.gradle_command('android-device', plan, root=self.root, android_serial=device.SERIAL, android_io_documents_receipt=altered)

    def test_new_focus_has_only_finite_private_safe_preflight_diagnostics_and_never_runs_a_failed_sdk(self):
        self.plan()
        with (patch.dict(os.environ, {'ANDROID_HOME': '/unread-modeled-sdk'}),
              patch.object(device, 'sdk_assets', side_effect=ValueError('private-sentinel-error-body')),
              patch.object(device.lt, 'execute') as execute):
            with self.assertRaises(ValueError):
                device._run(self.root, 'build/ci-verification/reference-sdk-refused', ('calf-io',), focus=FOCUS)
            execute.assert_not_called()
        receipt = self.root / 'build/ci-verification/reference-sdk-refused/preflight.json'
        self.assertTrue(receipt.is_file()); value = json.loads(receipt.read_text())
        self.assertEqual('failed', value['status']); self.assertEqual('sdk-assets', value['stage'])
        self.assertFalse(value['native_success_inferred']); self.assertNotIn('private-sentinel', receipt.read_text())
        self.assertNotIn('/unread-modeled-sdk', receipt.read_text())
        source = (r.ROOT / 'scripts/ci/android_device_tests.py').read_text()
        block = source.split('if lt.android_io_documents_required(plan):', 1)[1].split('if focus == lt.WEBVIEW_ANDROID_MEDIA_FOCUS:', 1)[0]
        self.assertLess(block.index('io_documents.prepare()'), block.index('output / "apk-assembly.log"'))
        self.assertIn('io_documents.close()', source)

    def test_new_helper_scope_distinguishes_tree_from_ordinary_document_without_claiming_grant_or_open_entry_success(self):
        source = (r.ROOT / 'scripts/ci/android_io_documents.py').read_text()
        self.assertIn('ordinary-document read/persistable', source)
        self.assertIn('tree read/persistable/prefix', source)
        self.assertIn('remain native test assertions', source)
        self.assertNotIn('one fixed synthetic folder.', source)


if __name__ == '__main__':
    unittest.main()
