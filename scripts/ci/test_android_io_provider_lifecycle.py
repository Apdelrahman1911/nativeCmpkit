"""Focused synthetic IO source/identity/controller/cache hooks, never Android/Coil executions."""
from collections import Counter
from contextlib import ExitStack, contextmanager
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
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

import android_device_tests as device
import android_io_documents as helper
import dependency_cache_inputs as cache
import library_tests as r
import workflow_matrix as matrix

FOCUS = 'android-io-provider-lifecycle'
CLASS = 'com.mohamedrejeb.calf.io.AndroidIoProviderLifecycleTest'
SOURCE = 'calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/AndroidIoProviderLifecycleTest.kt'
FIXTURE = 'tests/consumer/android-io-documents'
ANDROID = '{http://schemas.android.com/apk/res/android}'
METHODS = (
    'persistedTreeBookmarkSurvivesOwnedClientRestartAndExplicitRelease',
    'ownerRevocationDeniesTreeAndChildMetadataAndActualContentRead',
    'ownedProviderDeathProducesRealBinderFailureAndTreeMetadataRecovers',
    'nativeCoilDecoderFailureClosesCrossUidSourceAfterExactBinaryRead',
    'nativeCoilCancellationClosesTransferredSourceWithoutLateSuccess',
)

class AndroidIoProviderLifecycleHooks(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='nativecmpkit-io-provider-hooks-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.write('settings.gradle.kts', 'include(\n    ":calf-io",\n)\n')
        self.write('calf-io/src/commonTest/kotlin/Unrelated.kt', '// retained, never requested\n')
        for relative in ('calf-io/build.gradle.kts', 'calf-io/src/androidDeviceTest/AndroidManifest.xml',
                         'gradle/libs.versions.toml', 'scripts/ci/android_io_documents.py'):
            self.copy(relative)
        for path in (r.ROOT / FIXTURE).rglob('*'):
            if path.is_file() and 'build' not in path.relative_to(r.ROOT / FIXTURE).parts:
                self.copy(path.relative_to(r.ROOT).as_posix())
        for path in (r.ROOT / 'calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io').glob('*.kt'):
            self.copy(path.relative_to(r.ROOT).as_posix())

    def copy(self, relative):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((r.ROOT / relative).read_bytes())

    def write(self, relative, value):
        path = self.root / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(value)
        return path

    def plan(self):
        return r.plan(self.root, 'android-device', only_modules=('calf-io',), focus=FOCUS)

    def test_exact_five_case_focus_is_authored_api35_only_and_excludes_the_accepted_precheck(self):
        self.assertTrue(r.allowed_test_focus('android-device', ('calf-io',), FOCUS))
        plan = self.plan(); item, = plan['expected']
        self.assertFalse(plan['complete_suite_requested']); self.assertTrue(r.validate_test_focus(plan))
        self.assertEqual(CLASS, item['test_filter'])
        self.assertEqual([{'classname': CLASS, 'name': method} for method in METHODS], item['required_testcases'])
        self.assertIn(SOURCE, item['test_source_files'])
        self.assertIn(r.ANDROID_IO_DEVICE_SOURCE, item['test_source_files'])
        self.assertNotIn(r.android_io_oversize_identities()[0], item['required_testcases'])
        self.assertEqual('calf-io/build/outputs/androidTest-results/connected/androidMain', item['report_directory'])

    def test_real_profile_preserves_all_eleven_slots_eight_modules_and_additive_iframe_focus(self):
        row, = matrix.matrix(FOCUS)['include']
        self.assertEqual(('android-device-api35', 'calf-io', FOCUS),
                         (row['slot'], row['test-modules'], row['test-focus']))
        self.assertEqual(11, len(matrix.matrix('all')['include']))
        self.assertEqual(8, len(r.MINIMUM_MODULES['android-device']))
        self.assertEqual(2, len(matrix.matrix('webview-content-transitions')['include']))
        self.assertTrue(all(row['test-focus'] == r.WEBVIEW_CONTENT_FOCUS
                            for row in matrix.matrix('webview-content-transitions')['include']))
        choices = re.search(r'options: \[([^\n]+)\]', (r.ROOT / '.github/workflows/gradle.yml').read_text()).group(1)
        self.assertEqual(set(matrix.PROFILES), {part.strip() for part in choices.split(',')})

    def test_all_actual_helper_sources_are_held_library_inputs_and_outputs_are_not(self):
        values = r.snapshot_inputs(self.root)
        for relative in ('build.gradle.kts', 'settings.gradle.kts', 'gradle.properties', 'src/main/AndroidManifest.xml'):
            self.assertIn(FIXTURE + '/' + relative, values)
        java = list((self.root / FIXTURE / 'src/main/java').rglob('*.java'))
        self.assertEqual(5, len(java))
        self.assertTrue(all(path.relative_to(self.root).as_posix() in values for path in java))
        held = dict(values)
        self.write(FIXTURE + '/build/outputs/apk/debug/old.apk', 'not an input or proof')
        self.write(FIXTURE + '/build/android-user/debug.keystore', 'not a source input')
        self.assertEqual(held, r.snapshot_inputs(self.root))

    def test_helper_dependency_policy_declarations_are_keyed_but_sources_outputs_signing_and_xml_are_not(self):
        values = cache.selected_inputs(self.root, 'libraries')
        for relative in ('build.gradle.kts', 'settings.gradle.kts', 'gradle.properties', 'src/main/AndroidManifest.xml'):
            self.assertIn(FIXTURE + '/' + relative, values)
        before = cache.fingerprint('libraries', values)
        for relative in ('build.gradle.kts', 'settings.gradle.kts', 'gradle.properties', 'src/main/AndroidManifest.xml'):
            path = self.root / FIXTURE / relative; data = path.read_bytes()
            path.write_bytes(data + b'\n<!-- synthetic input alteration; not compiled -->\n')
            self.assertNotEqual(before, cache.fingerprint('libraries', cache.selected_inputs(self.root, 'libraries')))
            path.write_bytes(data)
        for relative in ('src/main/java/Unrequested.java', 'build/outputs/apk/debug/old.apk',
                         'build/android-user/debug.keystore', 'build/test-results/TEST-old.xml'):
            self.write(FIXTURE + '/' + relative, 'not a dependency declaration')
        self.assertEqual(before, cache.fingerprint('libraries', cache.selected_inputs(self.root, 'libraries')))

    def test_controller_has_exact_helper_before_reporter_assembly_and_failure_safe_close(self):
        source = (r.ROOT / 'scripts/ci/android_device_tests.py').read_text()
        self.assertIn('android_io_documents.OwnedIoDocuments', source)
        block = source.split('if lt.android_io_documents_required(plan):', 1)[1].split('if focus == lt.WEBVIEW_ANDROID_MEDIA_FOCUS:', 1)[0]
        self.assertLess(block.index('io_documents.prepare()'), block.index('output / "apk-assembly.log"'))
        self.assertIn('reporter_compile_deferred_until_io_documents_identity', source)
        self.assertIn('dict(io_documents.receipt)', source)
        self.assertIn('io_documents.close()', source)
        self.assertIn('"android_io_documents.py"', source)

    def test_actual_helper_manifest_shape_uses_manage_documents_and_signature_only_control(self):
        body = (self.root / FIXTURE / 'src/main/AndroidManifest.xml').read_bytes()
        self.assertTrue(helper.validate_manifest(body, compiled=False)['content_requires_android_grant'])
        document = ET.fromstring(body)
        provider = document.find('application/provider'); provider.set(ANDROID + 'permission', helper.PERMISSION)
        with self.assertRaises(ValueError): helper.validate_manifest(ET.tostring(document), compiled=False)
        document = ET.fromstring(body)
        document.find('permission').set(ANDROID + 'protectionLevel', 'normal')
        with self.assertRaises(ValueError): helper.validate_manifest(ET.tostring(document), compiled=False)

    def identities(self):
        return [{'classname': CLASS, 'name': method} for method in METHODS]

    def prepared(self):
        source = self.plan()['android_io_documents']['source_contract']
        return {'package': helper.PACKAGE, 'source_fixture': FIXTURE, 'prepare_status': 'passed',
            'verification_api_level': 35, 'recipient_installed': True, 'manual_URI_grant': False,
            'automatic_runtime_permission_grant': False, 'source_apk_sha256': 'a' * 64,
            'source_contract': source,
            'installed_readback': {'apk_sha256': 'a' * 64, 'exact_one_APK_path_observed': True},
            'apk_policy': {'compiled_manifest_inspected': True, 'content_requires_android_grant': True,
                'signature_control_only': True, 'certificate_sha256': 'b' * 64,
                'private_key_certificate_sha256': 'b' * 64,
                'signature_verification_min_sdk_version': 35, 'signature_verification_max_sdk_version': 35}}

    def compiled_manifest(self):
        root = ET.fromstring((self.root / FIXTURE / 'src/main/AndroidManifest.xml').read_bytes())
        root.set('package', helper.PACKAGE)
        ET.SubElement(root, 'uses-sdk', {ANDROID + 'minSdkVersion': '23', ANDROID + 'targetSdkVersion': '37'})
        root.find('application').set(ANDROID + 'debuggable', 'true')
        root.find('application/provider').set(ANDROID + 'authorities', helper.PACKAGE + '.documents')
        return root

    def collect(self, cases=None, *, marker=1, age=0, split=False):
        plan = self.plan(); cases = self.identities() if cases is None else cases
        folder = self.root / plan['expected'][0]['report_directory']
        if folder.exists(): shutil.rmtree(folder)
        chunks = [cases[:2], cases[2:]] if split else [cases]
        for index, chunk in enumerate(chunks):
            suite = ET.Element('testsuite')
            for case in chunk:
                node = ET.SubElement(suite, 'testcase', classname=case['classname'], name=case['name'])
                if case.get('status', 'passed') != 'passed': ET.SubElement(node, case['status'])
            target = folder / ('TEST-io-' + str(index) + '.xml')
            target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(ET.tostring(suite))
        now = time.time_ns()
        return r.collect_reports(self.root, plan, now - 1_000_000_000 + age, now + 1_000_000_000 + age,
                                 Counter({plan['expected'][0]['task']: marker}))

    def test_real_read_only_controller_and_library_clis_select_api35_without_outputs_or_builds(self):
        commands = [
            [sys.executable, '-B', str(r.ROOT / 'scripts/ci/library_tests.py'), 'plan',
             '--suite', 'android-device', '--module', 'calf-io', '--focus', FOCUS],
            [sys.executable, '-B', str(r.ROOT / 'scripts/ci/android_device_tests.py'), 'plan',
             '--output', 'build/ci-plan', '--api-level', '35', '--module', 'calf-io', '--focus', FOCUS],
        ]
        for command in commands:
            with self.subTest(controller='android_device_tests.py' in command[2]):
                result = subprocess.run(command, cwd=r.ROOT, capture_output=True, timeout=30)
                self.assertEqual(0, result.returncode, result.stderr.decode())
                plan = json.loads(result.stdout)
                self.assertEqual(self.identities(), plan['expected'][0]['required_testcases'])
                self.assertEqual(35, plan['android_io_documents']['verification_api_level'])
        witness = matrix.preflight_plans(FOCUS)
        self.assertTrue(witness['source_only']); self.assertEqual(0, witness['Gradle_builds_executed'])
        self.assertEqual(0, witness['library_tests_executed']); self.assertEqual(1, len(witness['slots']))

    def test_wrong_module_suite_duplicate_wildcard_and_api23_refuse_before_runtime_mutation(self):
        for suite, modules, focus in (('desktop', ('calf-io',), FOCUS), ('android-host', ('calf-io',), FOCUS),
                ('android-device', ('calf-ui',), FOCUS), ('android-device', ('calf-io', 'calf-io'), FOCUS),
                ('android-device', ('calf-io', 'calf-ui'), FOCUS), ('android-device', ('calf-io',), 'android-io-*')):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                r.plan(self.root, suite, only_modules=modules, focus=focus)
        with patch.object(device, 'require_host') as host:
            for modules, api in ((('calf-ui',), 35), (('calf-io',), 23)):
                with self.assertRaises(ValueError):
                    device.run(self.root, 'build/ci-verification/refused', only_modules=modules, focus=FOCUS, api_level=api)
            host.assert_not_called()
        self.assertFalse((self.root / 'build').exists())
        result = subprocess.run([sys.executable, '-B', str(r.ROOT / 'scripts/ci/android_device_tests.py'), 'plan',
            '--output', 'build/ci-plan', '--api-level', '23', '--module', 'calf-io', '--focus', FOCUS],
            cwd=r.ROOT, capture_output=True, timeout=30)
        self.assertEqual(2, result.returncode)

    def test_changed_method_class_package_ignore_and_missing_source_refuse_before_cost(self):
        path = self.root / SOURCE; original = path.read_text()
        for changed in (original.replace(METHODS[0], 'unreviewed'), original.replace('@Test', '@Ignore @Test', 1),
                        original.replace('class AndroidIoProviderLifecycleTest', 'class ChangedTest'),
                        original.replace('package com.mohamedrejeb.calf.io', 'package foreign.io'),
                        original + '\n@Test fun unreviewedExtra() {}\n'):
            with self.subTest(change=hashlib.sha256(changed.encode()).hexdigest()):
                path.write_text(changed)
                with self.assertRaises(ValueError): self.plan()
        path.unlink()
        with self.assertRaises((OSError, ValueError)): self.plan()

    def test_tampered_filter_task_module_report_inventory_and_source_binding_cannot_run(self):
        original = self.plan()
        for key, value in (('test_filter', CLASS + '*'), ('module', 'calf-file-picker-coil'), ('project', ':calf-ui'),
                ('task', ':calf-io:testAndroidHostTest'), ('report_directory', 'calf-ui/build/test-results/forged'),
                ('required_testcases', self.identities()[:-1]), ('test_source_files', [])):
            changed = deepcopy(original); changed['expected'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): r.validate_test_focus(changed)
        for key, value in (('complete_suite_requested', True), ('explicit_module_subset', []), ('suite', 'android-host')):
            changed = deepcopy(original); changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): r.validate_test_focus(changed)
        for key, value in (('package', 'foreign'), ('verification_api_level', 23), ('source_fixture', 'tests/consumer/foreign'),
                ('source_contract', {})):
            changed = deepcopy(original); changed['android_io_documents'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): r.validate_test_focus(changed)
        changed = deepcopy(original); changed.pop('android_io_documents')
        with self.assertRaises(ValueError): r.validate_test_focus(changed)

    def test_exact_five_fresh_cases_need_one_report_and_one_actual_task_marker(self):
        result = self.collect()
        self.assertEqual([], result['errors']); self.assertEqual(5, result['totals']['passed'])
        self.assertEqual(5, result['totals']['executed']); self.assertEqual(1, len(result['modules'][0]['reports']))
        self.assertTrue(all(case['source'] == SOURCE and case['disposition'] == 'required-executed'
                            for case in result['modules'][0]['native_scenarios']))
        for options in ({'marker': 0}, {'marker': 2}, {'age': 10_000_000_000}, {'split': True}):
            with self.subTest(options=options): self.assertTrue(self.collect(**options)['errors'])

    def test_missing_extra_duplicate_foreign_failure_error_and_skip_cannot_be_native_green(self):
        cases = self.identities()
        for altered in ([], cases[:-1], cases + [cases[0]], cases + r.android_io_oversize_identities(),
                [dict(case, classname='foreign.IoTest') for case in cases],
                [dict(case, name=case['name'] + '[android]') for case in cases],
                *([dict(case, status=status) if index == 0 else case for index, case in enumerate(cases)]
                    for status in ('failure', 'error', 'skipped'))):
            with self.subTest(size=len(altered)): self.assertTrue(self.collect(altered)['errors'])

    def test_native_helper_flag_requires_verified_preparation_but_assembly_never_requests_a_native_task(self):
        plan = self.plan()
        with self.assertRaises(ValueError): r.gradle_command('android-device', plan, root=self.root, android_serial=device.SERIAL)
        assembly = r.gradle_command('android-device', plan, root=self.root, android_serial=device.SERIAL, for_assembly=True)
        self.assertEqual(':calf-io:assembleAndroidDeviceTest', assembly[-1])
        self.assertNotIn(':calf-io:connectedAndroidDeviceTest', assembly)
        self.assertFalse(any('nativecmpkitOwnedIoDocuments=' in value for value in assembly))
        native = r.gradle_command('android-device', plan, root=self.root, android_serial=device.SERIAL,
                                  android_io_documents_receipt=self.prepared())
        self.assertEqual(':calf-io:connectedAndroidDeviceTest', native[-1])
        self.assertEqual(1, native.count('-Pandroid.testInstrumentationRunnerArguments.nativecmpkitOwnedIoDocuments=true'))
        self.assertIn('-Pandroid.testInstrumentationRunnerArguments.class=' + CLASS, native)
        self.assertNotIn('--tests', native)
        with self.assertRaises(ValueError): r.gradle_command('android-host', plan, root=self.root, for_assembly=True)

    def test_standalone_native_execution_without_controller_receipt_refuses_before_lock_or_output(self):
        with patch.object(r, 'execute') as execute, patch.object(r.runtime_context, 'capture') as capture:
            with self.assertRaises(ValueError):
                r.run(self.root, 'android-device', 'build/ci-verification/refused', None, 10, 8192,
                    only_modules=('calf-io',), focus=FOCUS, android_serial=device.SERIAL)
            execute.assert_not_called(); capture.assert_not_called()
        self.assertFalse((self.root / 'build').exists())

    def test_full_authored_io_keeps_helper_while_accepted_oversize_focus_excludes_it(self):
        full = r.plan(self.root, 'android-device', only_modules=('calf-io',))
        self.assertFalse(r.validate_test_focus(full)); self.assertTrue(r.android_io_documents_required(full))
        self.assertIn('android_io_documents', full)
        with self.assertRaises(ValueError): r.gradle_command('android-device', full, root=self.root, android_serial=device.SERIAL)
        command = r.gradle_command('android-device', full, root=self.root, android_serial=device.SERIAL,
                                   android_io_documents_receipt=self.prepared())
        self.assertFalse(any('.class=' in value for value in command))
        accepted = r.plan(self.root, 'android-device', only_modules=('calf-io',), focus=r.ANDROID_IO_OVERSIZE_FOCUS)
        self.assertFalse(r.android_io_documents_required(accepted)); self.assertNotIn('android_io_documents', accepted)
        command = r.gradle_command('android-device', accepted, root=self.root, android_serial=device.SERIAL)
        self.assertIn('-Pandroid.testInstrumentationRunnerArguments.class=' + r.ANDROID_IO_DEVICE_CLASS + '#' + r.ANDROID_IO_OVERSIZE_METHOD, command)
        self.assertFalse(any('nativecmpkitOwnedIoDocuments=' in value for value in command))
        with self.assertRaises(ValueError):
            r.gradle_command('android-device', accepted, root=self.root, android_serial=device.SERIAL,
                             android_io_documents_receipt=self.prepared())

    def test_source_contract_binds_actual_nineteen_inputs_without_native_or_compiler_success(self):
        value = helper.source_contract(self.root); helper.validate_source_receipt(value)
        self.assertEqual(19, len(value['source_inputs'])); self.assertEqual(set(helper.SOURCE_FILES), set(value['source_inputs']))
        self.assertTrue(value['source_policy_verified']); self.assertFalse(value['native_or_compile_success_inferred'])
        self.assertEqual(value, self.plan()['android_io_documents']['source_contract'])
        for relative in helper.SOURCE_FILES:
            self.assertEqual(hashlib.sha256((self.root / relative).read_bytes()).hexdigest(), value['source_inputs'][relative])

    def test_source_nonce_uid_thread_shutdown_and_manual_grant_changes_refuse(self):
        replacements = {
            helper.JAVA + 'IoControlService.java': [('nonce.matches("[a-f0-9]{32}")', 'true'), ('message.sendingUid', 'message.arg1')],
            helper.KOTLIN + 'OwnedIoEndpoint.kt': [('binder.linkToDeath', 'binder.pingBinder'), ('thread.quitSafely(); thread.join(10_000)', 'thread.quit()')],
            SOURCE: [('withImageLoader { loader ->', 'unsafeLoader { loader ->'), ('withContext(NonCancellable)', 'withContext(Dispatchers.IO)'),
                ('acquireUnstableContentProviderClient', 'acquireContentProviderClient')],
            helper.JAVA + 'IoDocumentGrantActivity.java': [('FLAG_GRANT_PREFIX_URI_PERMISSION', 'FLAG_GRANT_WRITE_URI_PERMISSION')],
        }
        for relative, changes in replacements.items():
            path = self.root / relative; original = path.read_text()
            for old, new in changes:
                with self.subTest(relative=relative, token=old):
                    self.assertIn(old, original); path.write_text(original.replace(old, new))
                    with self.assertRaises(ValueError): helper.source_contract(self.root)
            path.write_text(original)
        path = self.root / SOURCE; original = path.read_text(); path.write_text(original + '\n// grantUriPermission( forbidden bypass\n')
        with self.assertRaises(ValueError): helper.source_contract(self.root)

    def test_source_missing_unknown_hardlink_symlink_or_unbounded_file_refuses(self):
        path = self.root / helper.JAVA / 'IoFixture.java'; payload = path.read_bytes(); path.unlink()
        with self.assertRaises((OSError, ValueError)): helper.source_contract(self.root)
        path.write_bytes(payload)
        extra = self.write(helper.JAVA + 'Unexpected.java', '// unreviewed source')
        with self.assertRaises(ValueError): helper.source_contract(self.root)
        extra.unlink()
        link = self.root / 'private-hardlink'; os.link(path, link)
        with self.assertRaises(ValueError): helper.source_contract(self.root)
        link.unlink(); path.unlink(); link.write_bytes(payload); path.symlink_to(link)
        with self.assertRaises(ValueError): helper.source_contract(self.root)
        path.unlink(); link.unlink(); path.write_bytes(b'x' * (256 * 1024 + 1))
        with self.assertRaises(ValueError): helper.source_contract(self.root)

    def test_reporter_cannot_obtain_manage_documents_or_extra_grant_permissions(self):
        path = self.root / 'calf-io/src/androidDeviceTest/AndroidManifest.xml'; original = path.read_bytes()
        for permission in ('android.permission.MANAGE_DOCUMENTS', 'android.permission.READ_MEDIA_IMAGES'):
            root = ET.fromstring(original); ET.SubElement(root, 'uses-permission', {ANDROID + 'name': permission})
            path.write_bytes(ET.tostring(root))
            with self.subTest(permission=permission), self.assertRaises(ValueError): helper.source_contract(self.root)

    def test_source_sdk_declaration_cannot_override_the_catalog_reference(self):
        path = self.root / FIXTURE / 'build.gradle.kts'; original = path.read_text()
        for old, new in (('compileSdk = libs.versions.android.compileSdk.get().toInt()', 'compileSdk = 35'),
                         ('minSdk = libs.versions.android.minSdk.get().toInt()', 'minSdk = 35'),
                         ('targetSdk = libs.versions.android.compileSdk.get().toInt()', 'targetSdk = 35')):
            path.write_text(original.replace(old, new))
            with self.subTest(declaration=old), self.assertRaises(ValueError): helper.source_contract(self.root)

    def test_compiled_manifest_exact_sdk_signatures_authority_and_process_boundary(self):
        root = self.compiled_manifest()
        result = helper.validate_manifest(ET.tostring(root), compiled=True)
        self.assertTrue(result['compiled_manifest_inspected']); self.assertFalse(result['native_grant_UID_or_result_inferred'])
        for tag, name, value in (('.', 'package', 'foreign'), ('uses-sdk', ANDROID + 'minSdkVersion', '35'),
                ('uses-sdk', ANDROID + 'targetSdkVersion', '35'), ('application', ANDROID + 'debuggable', 'false'),
                ('permission', ANDROID + 'protectionLevel', 'normal'),
                ('application/provider', ANDROID + 'authorities', 'foreign.documents'),
                ('application/provider', ANDROID + 'permission', helper.PERMISSION),
                ('application/provider', ANDROID + 'process', ':wrong')):
            altered = self.compiled_manifest(); altered.find(tag).set(name, value)
            with self.subTest(tag=tag, name=name), self.assertRaises(ValueError):
                helper.validate_manifest(ET.tostring(altered), compiled=True)
        for malformed in (b'', b'not XML', b'x' * 65537, b'<!DOCTYPE manifest><manifest/>'):
            with self.assertRaises(ValueError): helper.validate_manifest(malformed, compiled=True)

    def test_manifest_cannot_add_shared_uid_app_process_intent_routes_or_grant_bypass(self):
        original = (self.root / FIXTURE / 'src/main/AndroidManifest.xml').read_bytes()
        edits = [lambda root: root.set(ANDROID + 'sharedUserId', 'android.uid.system'),
            lambda root: root.find('application').set(ANDROID + 'process', ':wrong'),
            lambda root: ET.SubElement(root.find('queries'), 'package', {ANDROID + 'name': 'foreign.app'}),
            lambda root: ET.SubElement(root.find('application/provider/intent-filter'), 'action', {ANDROID + 'name': 'foreign.ROUTE'}),
            lambda root: ET.SubElement(root.find('application/provider'), 'grant-uri-permission', {ANDROID + 'pathPrefix': '/'}),
            lambda root: root.find('application/activity').set(ANDROID + 'enabled', 'false'),
        ]
        for change in edits:
            root = ET.fromstring(original); change(root)
            with self.subTest(change=edits.index(change)), self.assertRaises(ValueError):
                helper.validate_manifest(ET.tostring(root), compiled=False)

    def test_actual_apk_signer_parser_requires_one_verified_scheme_digest_and_clean_bounded_result(self):
        good = ('Verifies\nVerified using v1 scheme (JAR signing): true\n'
                'Verified using v2 scheme (APK Signature Scheme v2): true\nNumber of signers: 1\n'
                'Signer #1 certificate SHA-256 digest: ' + 'b' * 64 + '\n').encode()
        result = subprocess.CompletedProcess([], 0, good, b'')
        self.assertEqual('b' * 64, helper.signer_certificate(result))
        for code, stdout, stderr in ((1, good, b''), (0, good, b'unknown error'),
                (0, good.replace(b'Number of signers: 1', b'Number of signers: 2'), b''),
                (0, good.replace(b'): true', b'): false'), b''), (0, good + b'Signer #2 unknown\n', b''),
                (0, good + b'WARNING: unverified detail\n', b''), (0, b'x' * (1024 ** 2 + 1), b'')):
            with self.subTest(code=code, bytes=len(stdout)), self.assertRaises(ValueError):
                helper.signer_certificate(subprocess.CompletedProcess([], code, stdout, stderr))

    def test_prepared_receipt_cannot_accept_unknown_status_api_installed_bytes_signer_or_source(self):
        good = self.prepared(); helper.validate_prepared_receipt(good, self.plan()['android_io_documents']['source_contract'])
        for keys, value in ((('prepare_status',), 'failed'), (('recipient_installed',), False), (('verification_api_level',), 23),
            (('automatic_runtime_permission_grant',), True), (('manual_URI_grant',), True), (('source_apk_sha256',), None),
            (('installed_readback', 'apk_sha256'), 'c' * 64), (('installed_readback', 'exact_one_APK_path_observed'), False),
            (('apk_policy', 'compiled_manifest_inspected'), False), (('apk_policy', 'content_requires_android_grant'), False),
            (('apk_policy', 'private_key_certificate_sha256'), 'c' * 64), (('source_contract', 'source_inputs_sha256'), 'd' * 64)):
            changed = deepcopy(good); at = changed
            for key in keys[:-1]: at = at[key]
            at[keys[-1]] = value
            with self.subTest(keys=keys), self.assertRaises(ValueError): helper.validate_prepared_receipt(changed)
        changed = deepcopy(good); changed['source_contract']['source_inputs'][SOURCE] = 'e' * 64
        changed['source_contract']['source_inputs_sha256'] = r.input_digest(changed['source_contract']['source_inputs'])
        helper.validate_prepared_receipt(changed)
        with self.assertRaises(ValueError): helper.validate_prepared_receipt(changed, good['source_contract'])

    def test_source_receipt_unknown_key_or_native_success_claim_is_not_accepted(self):
        original = helper.source_contract(self.root)
        for key, value in (('native_or_compile_success_inferred', True), ('source_policy_verified', False),
                           ('unknown_native_success', True)):
            changed = deepcopy(original); changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): helper.validate_source_receipt(changed)

    def test_adapter_public_error_origin_contains_no_exception_body_machine_path_or_local(self):
        try: helper.validate_source_receipt({})
        except ValueError as error: origin = device.preflight_error_origin(error)
        self.assertEqual('android_io_documents.py', origin['source'])
        self.assertEqual('require', origin['symbol']); self.assertGreater(origin['line'], 0)
        self.assertEqual({'source', 'symbol', 'line'}, set(origin)); self.assertNotIn('/dev/', json.dumps(origin))

    def test_dependency_key_binds_actual_adapter_recipe_without_apk_or_key_inputs(self):
        values = cache.selected_inputs(self.root, 'libraries')
        self.assertIn('scripts/ci/android_io_documents.py', values)
        before = cache.fingerprint('libraries', values)
        path = self.root / 'scripts/ci/android_io_documents.py'; path.write_text(path.read_text() + '\n# different explicit recipe\n')
        self.assertNotEqual(before, cache.fingerprint('libraries', cache.selected_inputs(self.root, 'libraries')))
        self.assertNotIn(FIXTURE + '/src/main/AndroidManifest.xml', cache.selected_inputs(self.root, 'webview'))
        self.assertNotIn('scripts/ci/android_io_documents.py', cache.selected_inputs(self.root, 'core-io'))
        workflow = (r.ROOT / '.github/workflows/gradle.yml').read_text()
        self.assertIn('build-tools;' + helper.SIGNER_REVISION, workflow)
        self.assertIn("inputs.profile == 'android-io-provider-lifecycle'", workflow)

    @contextmanager
    def controlled_controller(self, *, prepare_error=False, invalid_prepare=False, cleanup_error=False, transport=True):
        order = []; prepared = self.prepared(); owned = Mock()
        owned.receipt = deepcopy(prepared)
        def prepare():
            order.append('helper-prepare')
            if prepare_error:
                owned.receipt.update(prepare_status='failed', prepare_error='ValueError')
                raise ValueError('private synthetic prepare diagnostic never persisted')
            if invalid_prepare: owned.receipt['apk_policy']['certificate_sha256'] = 'c' * 64
            return dict(owned.receipt)
        def close():
            order.append('helper-close')
            if cleanup_error: raise ValueError('private synthetic cleanup diagnostic never persisted')
            owned.receipt.update(cleanup_status='passed', owned_recipient_removed=True)
            return dict(owned.receipt)
        owned.prepare.side_effect = prepare; owned.close.side_effect = close
        process = Mock(pid=1234); process.poll.return_value = None
        def execute(root, command, log_path, *args, **kwargs):
            order.append(log_path.stem)
            return {'exit_code': 0}
        def tests(*args, **kwargs):
            order.append('tests'); return {'passed': True, 'totals': {'executed': 5, 'passed': 5}}
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, {'ANDROID_HOME': str(self.root / 'synthetic-sdk')}))
            stack.enter_context(patch.object(device, 'require_host'))
            stack.enter_context(patch.object(device, 'sdk_assets', return_value={'system_image': device.IMAGE}))
            stack.enter_context(patch.object(device, 'ensure_ports_unused'))
            stack.enter_context(patch.object(device, 'adb', return_value='List of devices attached'))
            stack.enter_context(patch.object(device.runtime, 'capture', return_value={'source_revision': 'f' * 40, 'source_tree_dirty': False}))
            stack.enter_context(patch.object(r, 'git_revision', return_value='f' * 40))
            execute_mock = stack.enter_context(patch.object(r, 'execute', side_effect=execute))
            stack.enter_context(patch.object(device.subprocess, 'Popen', return_value=process))
            stack.enter_context(patch.object(device, 'wait_for_owned_boot', side_effect=lambda *a, **k: order.append('boot') or {'api_level': '35', 'selinux': 'Enforcing'}))
            stack.enter_context(patch.object(helper, 'OwnedIoDocuments', return_value=owned))
            tests_mock = stack.enter_context(patch.object(r, 'run', side_effect=tests))
            stack.enter_context(patch.object(device, 'stop_owned_emulator', side_effect=lambda *a: order.append('shutdown') or {'clean_shutdown': True}))
            stack.enter_context(patch.object(device, 'wait_for_owned_transport_removal', side_effect=lambda *a: order.append('transport-removal') or transport))
            yield order, owned, execute_mock, tests_mock

    def invoke_controller(self):
        relative = 'build/ci-verification/controller-synthetic'
        result = device.run(self.root, relative, only_modules=('calf-io',), focus=FOCUS)
        self.assertEqual(result, json.loads((self.root / relative / 'controller.json').read_text()))
        self.assertFalse((self.root / 'build/ci-verification/.android-device-controller.lock').exists())
        self.assertNotIn('private synthetic', json.dumps(result))
        return result

    def test_mocked_controller_exact_helper_identity_precedes_reporter_and_native_then_owned_cleanup(self):
        with self.controlled_controller() as (order, owned, execute, tests): result = self.invoke_controller()
        self.assertTrue(result['passed']); self.assertTrue(result['reporter_compile_deferred_until_io_documents_identity'])
        self.assertEqual(['owned-avd-create', 'boot', 'helper-prepare', 'apk-assembly', 'tests', 'helper-close', 'shutdown', 'transport-removal'], order)
        self.assertEqual(self.prepared(), tests.call_args.kwargs['android_io_documents_receipt'])
        assembly = execute.call_args_list[-1].args[1]
        self.assertIn(':calf-io:assembleAndroidDeviceTest', assembly)
        self.assertNotIn(':calf-io:connectedAndroidDeviceTest', assembly)
        self.assertFalse(any('nativecmpkitOwnedIoDocuments=' in argument for argument in assembly))
        self.assertTrue(result['emulator_shutdown']['owned_adb_transport_removed'])

    def test_mocked_helper_preparation_failure_prevents_reporter_native_and_preserves_partial_receipt(self):
        with self.controlled_controller(prepare_error=True) as (order, owned, execute, tests): result = self.invoke_controller()
        self.assertFalse(result['passed']); tests.assert_not_called()
        self.assertNotIn('apk-assembly', order); self.assertEqual('failed', result['io_documents']['prepare_status'])
        self.assertEqual('passed', result['io_documents']['cleanup_status'])
        self.assertEqual('a' * 64, result['io_documents']['source_apk_sha256'])
        self.assertIn('helper-close', order); self.assertIn('shutdown', order)

    def test_mocked_unknown_signer_preparation_cannot_trigger_reporter_or_native(self):
        with self.controlled_controller(invalid_prepare=True) as (order, owned, execute, tests): result = self.invoke_controller()
        self.assertFalse(result['passed']); tests.assert_not_called(); self.assertNotIn('apk-assembly', order)
        self.assertEqual('ValueError', result['controller_error'])
        self.assertEqual('c' * 64, result['io_documents']['apk_policy']['certificate_sha256'])

    def test_mocked_helper_cleanup_failure_cannot_be_green_or_erase_preparation_facts(self):
        with self.controlled_controller(cleanup_error=True) as (order, owned, execute, tests): result = self.invoke_controller()
        self.assertFalse(result['passed']); self.assertTrue(result['test_suite_passed'])
        self.assertEqual('passed', result['io_documents']['prepare_status'])
        self.assertEqual('failed', result['io_documents']['cleanup_status'])
        self.assertFalse(result['io_documents']['owned_recipient_removed'])
        self.assertEqual(self.prepared()['source_contract'], result['io_documents']['source_contract'])
        self.assertEqual('a' * 64, result['io_documents']['source_apk_sha256']); self.assertIn('shutdown', order)

    def test_mocked_graceful_engine_exit_without_owned_adb_disappearance_is_not_green(self):
        with self.controlled_controller(transport=False) as (order, owned, execute, tests): result = self.invoke_controller()
        self.assertFalse(result['passed']); self.assertTrue(result['test_suite_passed'])
        self.assertFalse(result['emulator_shutdown']['owned_adb_transport_removed'])
        self.assertFalse(result['emulator_shutdown']['clean_shutdown'])


class OwnedIoPreparationPolicyTests(unittest.TestCase):
    """Direct helper orchestration, synthetic APK/DER/executables; no Android SDK runs."""
    def setUp(self):
        self.fixture = AndroidIoProviderLifecycleHooks()
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.output = self.root / 'build/ci-verification/owned-io-synthetic'
        (self.output / 'android-user').mkdir(parents=True)
        self.key = self.output / 'android-user/debug.keystore'
        self.key.write_bytes(b'synthetic non-key material; never imported by a real signer')
        self.home = self.root / 'synthetic-sdk'
        for relative in ('cmdline-tools/23.0/bin/apkanalyzer', 'build-tools/' + helper.SIGNER_REVISION + '/apksigner'):
            target = self.home / relative; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('synthetic executable marker; never executed'); target.chmod(0o700)
        self.operator = helper.OwnedIoDocuments(self.root, self.output, self.home, device.SERIAL,
            lambda: True, environment={'ANDROID_SERIAL': device.SERIAL, 'ANDROID_USER_HOME': str(self.output / 'android-user')})
        self.apk = self.root / FIXTURE / 'build/outputs/apk/debug/synthetic.apk'
        self.apk.parent.mkdir(parents=True); self.apk.write_bytes(b'synthetic APK bytes, not a compiled/installable artifact')
        self.base_receipt = self.fixture.prepared()
        self.der = b'synthetic DER witness, never used as an actual certificate'
        self.certificate = hashlib.sha256(self.der).hexdigest()
        self.manifest = ET.tostring(self.fixture.compiled_manifest())
        self.policy = helper.validate_manifest(self.manifest, compiled=True) | {
            'certificate_sha256': self.certificate, 'private_key_certificate_sha256': self.certificate,
            'apk_signer_revision': helper.SIGNER_REVISION,
            'signature_verification_min_sdk_version': 35, 'signature_verification_max_sdk_version': 35,
            'raw_manifest_certificate_key_or_paths_uploaded': False}

    def complete_base_prepare(self):
        self.operator.digest = r.sha256(self.apk); self.operator.install_attempted = True
        prepared = deepcopy(self.base_receipt)
        prepared['source_apk_sha256'] = self.operator.digest
        prepared['installed_readback']['apk_sha256'] = self.operator.digest
        self.operator.receipt.update(prepared)
        return self.operator.receipt

    def completed(self, stdout=b'', stderr=b'', code=0):
        return subprocess.CompletedProcess([], code, stdout, stderr)

    def signature_result(self, digest=None):
        return self.completed(('Verifies\nVerified using v2 scheme (APK Signature Scheme v2): true\n'
            'Number of signers: 1\nSigner #1 certificate SHA-256 digest: ' + (digest or self.certificate) + '\n').encode())

    def test_prepare_reads_source_before_helper_assembly_and_inspects_exact_apk_before_pass(self):
        order = []; source = helper.source_contract(self.root)
        def base(): order.append('helper-assembly-install'); return self.complete_base_prepare()
        with (patch.object(helper, 'source_contract', side_effect=lambda root: order.append('source') or source),
              patch.object(helper.OwnedShareRecipient, 'prepare', side_effect=base),
              patch.object(helper, 'metadata_apk', return_value=self.apk),
              patch.object(self.operator, 'inspect_apk', side_effect=lambda apk: order.append('APK-manifest-signer') or self.policy)):
            receipt = self.operator.prepare()
        self.assertEqual(['source', 'helper-assembly-install', 'APK-manifest-signer', 'source'], order)
        self.assertEqual('passed', receipt['prepare_status'])
        self.assertEqual(r.sha256(self.apk), receipt['source_apk_sha256'])
        self.assertEqual(receipt, json.loads((self.operator.output / 'receipt.json').read_text()))
        self.assertFalse(receipt['source_contract']['native_or_compile_success_inferred'])

    def test_bad_source_has_no_helper_assembly_and_keeps_failed_prepare_then_owned_cleanup(self):
        source = self.root / helper.JAVA / 'IoControlService.java'
        source.write_text(source.read_text().replace('nonce.matches("[a-f0-9]{32}")', 'true'))
        with patch.object(helper.OwnedShareRecipient, 'prepare') as assemble:
            with self.assertRaises(ValueError): self.operator.prepare()
            assemble.assert_not_called()
        self.assertEqual('failed', self.operator.receipt['prepare_status'])
        receipt = self.operator.close()
        self.assertEqual('failed', receipt['prepare_status']); self.assertEqual('passed', receipt['cleanup_status'])
        self.assertTrue(receipt['owned_recipient_removed']); self.assertFalse(receipt['foreign_or_preexisting_recipient_mutated'])
        self.assertEqual(receipt, json.loads((self.operator.output / 'receipt.json').read_text()))

    def test_apk_policy_refusal_preserves_installed_bytes_and_failed_status_for_owned_cleanup(self):
        with (patch.object(helper.OwnedShareRecipient, 'prepare', side_effect=self.complete_base_prepare),
              patch.object(helper, 'metadata_apk', return_value=self.apk),
              patch.object(self.operator, 'inspect_apk', side_effect=ValueError('private policy detail'))):
            with self.assertRaises(ValueError): self.operator.prepare()
        self.assertTrue(self.operator.receipt['recipient_installed'])
        def close(): self.operator.receipt['owned_recipient_removed'] = True; return self.operator.receipt
        with patch.object(helper.OwnedShareRecipient, 'close', side_effect=close): receipt = self.operator.close()
        self.assertEqual('failed', receipt['prepare_status']); self.assertEqual('passed', receipt['cleanup_status'])
        self.assertEqual(r.sha256(self.apk), receipt['source_apk_sha256']); self.assertNotIn('private policy detail', json.dumps(receipt))

    def test_inspector_uses_fixed_official_paths_manifest_signer_and_exact_private_certificate_without_exported_raw_data(self):
        results = [self.completed(self.manifest), self.signature_result(), self.completed(self.der)]
        with patch.object(self.operator, 'host', side_effect=results) as host:
            policy = self.operator.inspect_apk(self.apk)
        self.assertEqual(self.policy, policy)
        commands = [call.args[0] for call in host.call_args_list]
        self.assertEqual(str(self.home / 'cmdline-tools/23.0/bin/apkanalyzer'), commands[0][0])
        self.assertEqual(['manifest', 'print', str(self.apk)], commands[0][1:])
        self.assertEqual(str(self.home / ('build-tools/' + helper.SIGNER_REVISION + '/apksigner')), commands[1][0])
        self.assertEqual(['verify', '--verbose', '--print-certs', '--min-sdk-version', '35',
                          '--max-sdk-version', '35', str(self.apk)], commands[1][1:])
        self.assertEqual(['keytool', '-exportcert', '-keystore', str(self.key), '-alias', 'androiddebugkey', '-storepass', 'android'], commands[2])
        self.assertNotIn(str(self.key), json.dumps(policy)); self.assertNotIn(str(self.apk), json.dumps(policy))
        self.assertFalse(policy['raw_manifest_certificate_key_or_paths_uploaded'])

    def test_api35_signature_scope_uses_exact_range_and_explicit_integer_policy(self):
        with patch.object(self.operator, 'host', side_effect=[self.completed(self.manifest),
                self.signature_result(), self.completed(self.der)]) as host:
            policy = self.operator.inspect_apk(self.apk)
        command = host.call_args_list[1].args[0]
        self.assertEqual([str(self.home / ('build-tools/' + helper.SIGNER_REVISION + '/apksigner')),
            'verify', '--verbose', '--print-certs', '--min-sdk-version', '35',
            '--max-sdk-version', '35', str(self.apk)], command)
        for key in ('signature_verification_min_sdk_version', 'signature_verification_max_sdk_version'):
            self.assertIs(type(policy[key]), int); self.assertEqual(35, policy[key])
        self.assertEqual('23', ET.fromstring(self.manifest).find('uses-sdk').get(ANDROID + 'minSdkVersion'))
        self.assertFalse(policy['native_grant_UID_or_result_inferred'])
        self.assertFalse(policy['raw_manifest_certificate_key_or_paths_uploaded'])

    def test_api35_signature_scope_exact_prepared_receipt_is_accepted(self):
        receipt = deepcopy(self.base_receipt)
        helper.validate_prepared_receipt(receipt, receipt['source_contract'])
        self.assertEqual(35, receipt['verification_api_level'])
        self.assertFalse(receipt['source_contract']['native_or_compile_success_inferred'])

    def test_api35_signature_scope_missing_min_max_or_both_refuses(self):
        minimum, maximum = 'signature_verification_min_sdk_version', 'signature_verification_max_sdk_version'
        for absent in ((minimum,), (maximum,), (minimum, maximum)):
            receipt = deepcopy(self.base_receipt)
            for key in absent: receipt['apk_policy'].pop(key)
            with self.subTest(absent=absent), self.assertRaises(ValueError):
                helper.validate_prepared_receipt(receipt)

    def test_api35_signature_scope_broad_foreign_or_inverted_range_refuses(self):
        for minimum, maximum in ((23, 35), (35, 36), (23, 37), (34, 34), (36, 36), (36, 35), (0, 35), (35, 2147483647)):
            receipt = deepcopy(self.base_receipt)
            receipt['apk_policy'].update(signature_verification_min_sdk_version=minimum,
                                         signature_verification_max_sdk_version=maximum)
            with self.subTest(minimum=minimum, maximum=maximum), self.assertRaises(ValueError):
                helper.validate_prepared_receipt(receipt)

    def test_api35_signature_scope_noninteger_receipt_values_refuse(self):
        for key in ('signature_verification_min_sdk_version', 'signature_verification_max_sdk_version'):
            for value in ('35', 35.0, True, False, None):
                receipt = deepcopy(self.base_receipt); receipt['apk_policy'][key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    helper.validate_prepared_receipt(receipt)

    def test_api35_signature_scope_original_metadata_warning_still_refuses_before_key_export(self):
        warning = (b'WARNING: META-INF/com/android/build/gradle/app-metadata.properties not protected by signature. '
            b'Unauthorized modifications to this JAR entry will not be detected. '
            b'Delete or move the entry outside of META-INF/.\n')
        result = self.completed(self.signature_result().stdout + warning)
        with patch.object(self.operator, 'host', side_effect=[self.completed(self.manifest), result]) as host:
            with self.assertRaises(ValueError): self.operator.inspect_apk(self.apk)
        self.assertEqual(2, host.call_count)

    def test_api35_signature_scope_v1_only_still_refuses_before_key_export(self):
        text = ('Verifies\nVerified using v1 scheme (JAR signing): true\n'
            'Verified using v2 scheme (APK Signature Scheme v2): false\n'
            'Verified using v3 scheme (APK Signature Scheme v3): false\n'
            'Number of signers: 1\nSigner #1 certificate SHA-256 digest: ' + self.certificate + '\n').encode()
        with patch.object(self.operator, 'host', side_effect=[self.completed(self.manifest), self.completed(text)]) as host:
            with self.assertRaises(ValueError): self.operator.inspect_apk(self.apk)
        self.assertEqual(2, host.call_count)

    def test_api35_signature_scope_unknown_warning_error_stderr_or_failure_is_never_waived(self):
        good = self.signature_result().stdout
        for result in (self.completed(good + b'WARNING: other APK detail\n'),
                self.completed(good + b'ERROR: other APK detail\n'),
                self.completed(good + b'DOES NOT VERIFY\n'),
                self.completed(good, b'unknown signer detail'), self.completed(good, code=1)):
            with self.subTest(code=result.returncode, stderr=bool(result.stderr)), \
                    patch.object(self.operator, 'host', side_effect=[self.completed(self.manifest), result]) as host:
                with self.assertRaises(ValueError): self.operator.inspect_apk(self.apk)
                self.assertEqual(2, host.call_count)

    def test_keytool_unknown_error_stderr_oversize_or_actual_certificate_mismatch_refuses(self):
        for result, signer in ((self.completed(self.der, b'unknown warning'), self.signature_result()),
                (self.completed(self.der, code=1), self.signature_result()),
                (self.completed(b'x' * 16385), self.signature_result()),
                (self.completed(self.der), self.signature_result('a' * 64))):
            with (self.subTest(code=result.returncode, bytes=len(result.stdout)),
                  patch.object(self.operator, 'host', side_effect=[self.completed(self.manifest), signer, result])):
                with self.assertRaises(ValueError): self.operator.inspect_apk(self.apk)

    def test_missing_exact_sdk_inspector_recipe_refuses_before_helper_assembly(self):
        (self.home / ('build-tools/' + helper.SIGNER_REVISION + '/apksigner')).unlink()
        with patch.object(helper.OwnedShareRecipient, 'prepare') as assemble, patch.object(self.operator, 'host') as host:
            with self.assertRaises(ValueError): self.operator.prepare()
            assemble.assert_not_called(); host.assert_not_called()
        self.assertEqual('failed', self.operator.receipt['prepare_status'])

    def test_private_key_changed_during_certificate_read_is_not_accepted_as_stable_identity(self):
        def host(command):
            if command[0] == 'keytool':
                self.key.write_bytes(b'changed synthetic non-key input'); return self.completed(self.der)
            if 'manifest' in command: return self.completed(self.manifest)
            return self.signature_result()
        with patch.object(self.operator, 'host', side_effect=host):
            with self.assertRaises(ValueError): self.operator.inspect_apk(self.apk)

    def test_source_changed_during_helper_preparation_cannot_be_published_green(self):
        source = helper.source_contract(self.root); changed = deepcopy(source)
        changed['source_inputs'][SOURCE] = 'a' * 64
        changed['source_inputs_sha256'] = r.input_digest(changed['source_inputs'])
        with (patch.object(helper, 'source_contract', side_effect=[source, changed]),
              patch.object(helper.OwnedShareRecipient, 'prepare', side_effect=self.complete_base_prepare),
              patch.object(helper, 'metadata_apk', return_value=self.apk),
              patch.object(self.operator, 'inspect_apk', return_value=self.policy)):
            with self.assertRaises(ValueError): self.operator.prepare()
        self.assertEqual('failed', self.operator.receipt['prepare_status'])
        self.assertEqual(source, self.operator.receipt['source_contract'])

    def test_cleanup_refusal_keeps_primary_preparation_facts_and_persists_failed_cleanup(self):
        self.complete_base_prepare(); self.operator.receipt.update(prepare_status='failed', prepare_error='RuntimeError')
        with patch.object(helper.OwnedShareRecipient, 'close', side_effect=ValueError('private cleanup identity')):
            with self.assertRaises(ValueError): self.operator.close()
        receipt = json.loads((self.operator.output / 'receipt.json').read_text())
        self.assertEqual('failed', receipt['prepare_status']); self.assertEqual('failed', receipt['cleanup_status'])
        self.assertEqual('RuntimeError', receipt['prepare_error']); self.assertEqual('ValueError', receipt['cleanup_error'])
        self.assertFalse(receipt['owned_recipient_removed']); self.assertEqual(r.sha256(self.apk), receipt['source_apk_sha256'])
        self.assertNotIn('private cleanup identity', json.dumps(receipt))

    def test_exact_helper_metadata_package_single_apk_boundary_preserves_all_existing_pairs(self):
        metadata = self.apk.parent / 'output-metadata.json'
        good = {'applicationId': helper.PACKAGE, 'variantName': 'debug', 'artifactType': {'type': 'APK'},
                'elements': [{'type': 'SINGLE', 'filters': [], 'outputFile': self.apk.name}]}
        metadata.write_text(json.dumps(good))
        self.assertEqual(self.apk, helper.metadata_apk(self.root, fixture=FIXTURE, package=helper.PACKAGE))
        for fixture, package in ((FIXTURE, 'foreign.package'), ('tests/consumer/arbitrary', helper.PACKAGE),
                ('tests/consumer/android-share-documents', helper.PACKAGE), ('../escape', helper.PACKAGE)):
            with self.subTest(fixture=fixture), self.assertRaises(ValueError):
                helper.metadata_apk(self.root, fixture=fixture, package=package)
        for key, value in (('applicationId', 'foreign.package'), ('variantName', 'release'), ('elements', [])):
            changed = deepcopy(good); changed[key] = value; metadata.write_text(json.dumps(changed))
            with self.subTest(key=key), self.assertRaises(ValueError):
                helper.metadata_apk(self.root, fixture=FIXTURE, package=helper.PACKAGE)
        metadata.write_text(json.dumps(good))
        link = self.root / 'synthetic-linked-apk'; os.link(self.apk, link)
        with self.assertRaises(ValueError): helper.metadata_apk(self.root, fixture=FIXTURE, package=helper.PACKAGE)

if __name__ == '__main__': unittest.main()
