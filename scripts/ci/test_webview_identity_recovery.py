"""Owning failed-case recovery guards; Python/source fixtures are not native executions."""
from collections import Counter
import copy
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET
import android_device_tests as android
import library_tests as lt
import workflow_matrix as matrix

FOCUS = 'webview-public-identity-recovery'
IOS_FOCUS = 'webview-ios-native-remount-recovery'


class WebViewIdentityRecoveryTests(unittest.TestCase):
    def test_android_real_controller_cli_plans_the_selected_new_focus_before_any_native_setup(self):
        for focus in (lt.WEBVIEW_IDENTITY_FOCUS, FOCUS):
            args = ['android_device_tests.py', 'plan', '--api-level', '35', '--output', 'build/ci-plan',
                    '--module', 'calf-webview', '--focus', focus]
            output = io.StringIO()
            with patch('sys.argv', args), patch('sys.stdout', output), \
                    patch.object(android, 'run', side_effect=AssertionError('No emulator/Gradle allowed during source plan')), \
                    patch.object(android.signal, 'signal', side_effect=AssertionError('No process-control changes during source plan')):
                self.assertEqual(0, android.main())
            self.assertEqual(lt.plan(lt.ROOT, 'android-device', only_modules=('calf-webview',), focus=focus),
                             json.loads(output.getvalue()))

    def test_recovery_requests_only_failed_or_never_executed_methods_not_twelve_successful_executions(self):
        rows = matrix.matrix('webview-identity-recovery')['include']
        self.assertEqual({'desktop-linux-x64', 'ios-iphone', 'android-device-api35'}, {r['slot'] for r in rows})
        requested = []
        for row in rows:
            self.assertEqual('calf-webview', row['test-modules'])
            focus = IOS_FOCUS if row['suite'] == 'ios' else FOCUS
            self.assertEqual(focus, row['test-focus'])
            plan = lt.plan(lt.ROOT, row['suite'], only_modules=('calf-webview',), focus=focus)
            self.assertFalse(plan['complete_suite_requested'])
            self.assertTrue(lt.validate_test_focus(plan))
            selected, = plan['expected']
            requested += selected['required_testcases']
            command = lt.gradle_command(row['suite'], plan, '11111111-1111-1111-1111-111111111111' if row['suite'] == 'ios' else None,
                                        android_serial='emulator-5588' if row['suite'] == 'android-device' else None)
            if row['suite'] == 'desktop':
                self.assertEqual(1, len(selected['required_testcases']))
                self.assertTrue(command[-1].endswith('.' + lt.WEBVIEW_IDENTITY_METHOD))
            elif row['suite'] == 'ios':
                self.assertEqual(1, len(selected['required_testcases']))
                self.assertTrue(command[-1].endswith('.' + lt.IOS_WEBVIEW_LIFECYCLE_METHODS[0]))
            else:
                self.assertEqual(2, len(selected['required_testcases']))
                self.assertEqual(['-Pandroid.testInstrumentationRunnerArguments.class=' + lt.WEBVIEW_IDENTITY_SPECS['android-device']['classname']],
                                 [c for c in command if c.startswith('-Pandroid.testInstrumentationRunnerArguments.class=')])
        self.assertEqual(4, len(requested))
        self.assertFalse(any('rapidReplacement' in c['name'] or 'actualFxTyped' in c['name'] or 'Browser' in c['classname'] for c in requested))
        self.assertEqual(11, len(matrix.matrix('all')['include']))
        self.assertEqual(9, sum(len(lt.plan(lt.ROOT, suite, only_modules=('calf-webview',), focus=lt.WEBVIEW_IDENTITY_FOCUS)['expected'][0]['required_testcases'])
                                for suite in ('desktop', 'android-device', 'js', 'wasm')))
        self.assertEqual(7, len(lt.ui_application_focus_identities(lt.IOS_WEBVIEW_RECOVERY_FOCUS)))

    def test_final_ios_release_detaches_owned_view_before_owner_reset_and_keeps_failed_parent_predicate(self):
        source = (lt.ROOT / 'calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt').read_text()
        release = source.split('private fun releaseIosWebView', 1)[1].split('internal fun runOnIosMain', 1)[0]
        self.assertIn('{ view.removeFromSuperview() }', release,
                      'Final release must not depend on Compose wrapper deallocation to detach the retained child')
        self.assertLess(release.index('view.stopLoading()'), release.index('view.removeFromSuperview()'))
        self.assertLess(release.index('view.removeFromSuperview()'), release.index('state.webView = null'))
        test = (lt.ROOT / lt.IOS_WEBVIEW_LIFECYCLE_SOURCE).read_text().split('@Test fun ' + lt.IOS_WEBVIEW_LIFECYCLE_METHODS[0], 1)[1].split('@Test fun ', 1)[0]
        self.assertIn('state.webView == null && first.superview == null', test)
        self.assertIn('val retainedParent = runOnIdle { assertNotNull(first.superview) }', test)
        self.assertIn('assertFalse(retainedParent.subviews.any { sameNativeObject(it, first) })', test)
        self.assertIn('assertEquals(1, disposed.size)', test)

    def test_failed_desktop_cold_start_waits_for_actual_public_creation_before_fx_and_does_not_weaken_assertions(self):
        source = (lt.ROOT / lt.WEBVIEW_IDENTITY_SPECS['desktop']['source']).read_text()
        failed = source.split('@Test fun ' + lt.WEBVIEW_IDENTITY_METHOD, 1)[1].split('@Test fun ', 1)[0]
        self.assertIn('host.awaitCreation(first)', failed, 'Only actual public onCreated makes the FX toolkit ready')
        self.assertLess(failed.index('host.awaitCreation(first)'), failed.index('host.awaitDocument(first'))
        self.assertIn('created.none { it.state === state }', source)
        self.assertIn('failure.get()?.let { throw it }', source)
        self.assertIn('withTimeout(20_000)', source)
        self.assertNotRegex(source, r'(?m)^\s*Platform\.startup\s*\(')
        self.assertIn('Initial common settings cannot overwrite creation customization', source)

    def test_recovery_xml_requires_one_fresh_exact_desktop_case_no_unrequested_successes_or_skips(self):
        plan = lt.plan(lt.ROOT, 'desktop', only_modules=('calf-webview',), focus=FOCUS)
        required = plan['expected'][0]['required_testcases']
        self.assertEqual(1, len(required))
        for invalid in ('missing', 'foreign', 'duplicate', 'skipped', 'failure', 'no-marker'):
            with self.subTest(invalid=invalid), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                folder = root / plan['expected'][0]['report_directory']; folder.mkdir(parents=True)
                cases = copy.deepcopy(required)
                if invalid == 'missing': cases = []
                if invalid == 'foreign': cases[0]['name'] = 'actualFxTypedValuesOffMainAndThrowingOrDetachedCallbacksAreExactlyOnce[desktop]'
                if invalid == 'duplicate': cases += copy.deepcopy(cases)
                xml = ET.Element('testsuite')
                for c in cases:
                    node = ET.SubElement(xml, 'testcase', **c)
                    if invalid in ('skipped', 'failure'): ET.SubElement(node, invalid)
                (folder / 'TEST-explicitly-synthetic.xml').write_bytes(ET.tostring(xml))
                import time
                now = time.time_ns()
                actual = lt.collect_reports(root, plan, now-1_000_000_000, now+1_000_000_000,
                                             Counter({plan['expected'][0]['task']: 0 if invalid == 'no-marker' else 1}), host_system='Linux')
                self.assertTrue(actual['errors'])

    def test_real_profile_preflight_uses_the_actual_android_controller_parser_and_original_nondevice_cli(self):
        result = matrix.preflight_plans('webview-identity-recovery')
        self.assertEqual(3, len(result['slots']))
        for row in result['slots']:
            self.assertEqual('plan', row['command'][3])
            self.assertEqual(0, row['exit_code'])
            self.assertTrue(result['source_only'])
            if row['suite'] == 'android-device':
                self.assertTrue(row['command'][2].endswith('android_device_tests.py'))
                self.assertNotIn('--suite', row['command'])
            else: self.assertTrue(row['command'][2].endswith('library_tests.py'))

    def test_accepted_method_bodies_and_other_engine_helpers_remain_exactly_unchanged(self):
        revision = '5e2479b1d32a39eca026f1d4e1ed95068b6ccbed'
        for suite in ('desktop', 'android-device', 'js'):
            path = lt.WEBVIEW_IDENTITY_SPECS[suite]['source']
            old = subprocess.check_output(['git', 'show', revision + ':' + path], cwd=lt.ROOT, text=True)
            new = (lt.ROOT / path).read_text()
            if suite != 'desktop': self.assertEqual(old, new)
            else:
                for start, end in (('    @Test fun rapidReplacement', '    private suspend fun evaluate'),
                                   ('    private suspend fun evaluate', '        suspend fun awaitGeneration')):
                    # The new failure-only readiness method is inserted before awaitGeneration;
                    # all actually accepted method bodies and invoked existing helpers stay.
                    old_section = old.split(start, 1)[1].split(end, 1)[0]
                    new_section = new.split(start, 1)[1].split(end, 1)[0]
                    new_section = new_section.split('        suspend fun awaitCreation', 1)[0]
                    self.assertEqual(old_section, new_section)
        path = lt.IOS_WEBVIEW_LIFECYCLE_SOURCE
        old = subprocess.check_output(['git', 'show', '2fe53ffc6644920c7afc5c1ad4dcd6b8401b9ce9:' + path], cwd=lt.ROOT, text=True)
        new = (lt.ROOT / path).read_text()
        # The source-only final-detach extension changes only the failed native method.
        for method in (lt.IOS_WEBVIEW_BRIDGE_METHOD, *lt.IOS_WEBVIEW_LIFECYCLE_METHODS[1:]):
            start = '@Test fun ' + method
            self.assertEqual(old.split(start, 1)[1].split('@Test fun ', 1)[0], new.split(start, 1)[1].split('@Test fun ', 1)[0])


if __name__ == '__main__': unittest.main()
