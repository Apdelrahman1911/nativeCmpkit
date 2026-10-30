"""Finite real-popup selection/source guards; synthetic, not native test execution."""
from collections import Counter
from copy import deepcopy
import io
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import library_tests as lt
import workflow_matrix as wm


class AndroidPopupPolicyTests(unittest.TestCase):
    def test_rejection_is_observable_bounded_and_bound_to_the_actual_native_owner(self):
        source = (lt.ROOT / 'calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt').read_text()
        body = source.split('override fun onCreateWindow(', 1)[1].split('override fun onReceivedTitle(', 1)[0]
        self.assertIn('::state.isInitialized && state.webView === view', body)
        self.assertIn('recordPopupRejection(isDialog, isUserGesture)', body)
        self.assertIn('return false', body)
        for forbidden in ('startActivity(', 'WebView(', 'sendToTarget(', 'hitTestResult', 'resultMsg.obj'):
            self.assertNotIn(forbidden, body)
        settings = (lt.ROOT / 'calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt').read_text()
        self.assertIn('var lastPopupRejection: AndroidPopupRejection? by mutableStateOf(null)', settings)
        self.assertIn('private set', settings.split('var lastPopupRejection:', 1)[1].split('var supportZoom', 1)[0])
        self.assertIn('var supportMultipleWindows = true', settings)

    def plan(self):
        return lt.plan(lt.ROOT, 'android-device', only_modules=('calf-webview',), focus=lt.ANDROID_POPUP_FOCUS)

    def collect(self, cases=None, markers=1, stale=False):
        plan = self.plan()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / plan['expected'][0]['report_directory'] / 'TEST-explicitly-synthetic.xml'
            report.parent.mkdir(parents=True)
            cases = lt.android_popup_identities() if cases is None else cases
            report.write_text('<testsuite>' + ''.join(
                '<testcase classname="' + c['classname'] + '" name="' + c['name'] + '">' + c.get('outcome', '') + '</testcase>'
                for c in cases) + '</testsuite>')
            now = time.time_ns()
            if stale:
                import os
                os.utime(report, ns=(now-20_000_000_000, now-20_000_000_000))
            return lt.collect_reports(root, plan, now-1_000_000_000, now+1_000_000_000,
                                      Counter({plan['expected'][0]['task']: markers}))

    def test_exact_three_actual_device_methods_and_no_accepted_lifetime_or_identity_replay(self):
        row, = wm.matrix('android-webview-popups')['include']
        self.assertEqual(('android-device-api35', 'android-device', 'calf-webview', lt.ANDROID_POPUP_FOCUS),
                         (row['slot'], row['suite'], row['test-modules'], row['test-focus']))
        plan = self.plan()
        self.assertTrue(lt.validate_test_focus(plan))
        self.assertEqual(lt.android_popup_identities(), plan['expected'][0]['required_testcases'])
        self.assertEqual(3, len(lt.android_popup_identities()))
        self.assertEqual(11, len(wm.matrix('all')['include']))
        self.assertEqual(lt.ANDROID_POPUP_CLASS, plan['expected'][0]['test_filter'])

    def test_real_controller_and_cli_preflights_accept_only_the_finite_focus(self):
        import android_device_tests as device
        for module, args in ((lt, ['library_tests.py', 'plan', '--suite', 'android-device', '--module', 'calf-webview', '--focus', lt.ANDROID_POPUP_FOCUS]),
                             (device, ['android_device_tests.py', 'plan', '--api-level', '35', '--module', 'calf-webview', '--focus', lt.ANDROID_POPUP_FOCUS,
                                       '--output', 'build/ci-verification/popup-fixture'])):
            with patch('sys.argv', args), patch('sys.stdout', io.StringIO()):
                self.assertEqual(0, module.main())
        preflight = wm.preflight_plans('android-webview-popups')
        self.assertEqual(1, len(preflight['slots']))
        self.assertEqual(0, preflight['slots'][0]['exit_code'])

    def test_foreign_suite_module_selection_or_full_suite_claims_are_rejected(self):
        for suite, modules in [('desktop', ('calf-webview',)), ('android-host', ('calf-webview',)), ('ios', ('calf-webview',)),
                               ('js', ('calf-webview',)), ('wasm', ('calf-webview',)), ('android-device', ('calf-ui',)),
                               ('android-device', ('calf-webview', 'calf-io'))]:
            with self.assertRaises(ValueError):
                lt.plan(lt.ROOT, suite, only_modules=modules, focus=lt.ANDROID_POPUP_FOCUS)
        for key, value in [('test_filter', '*'), ('required_testcases', []), ('test_source_files', []), ('task', ':calf-webview:publish')]:
            plan = deepcopy(self.plan()); plan['expected'][0][key] = value
            with self.assertRaises(ValueError): lt.validate_test_focus(plan)
        plan = self.plan(); plan['complete_suite_requested'] = True
        with self.assertRaises(ValueError): lt.validate_test_focus(plan)

    def test_exact_fresh_nonzero_results_required_not_skipped_duplicate_stale_or_unexecuted(self):
        cases = lt.android_popup_identities()
        self.assertEqual([], self.collect(cases)['errors'])
        for changed in [[], cases[:-1], cases + [cases[0]], [cases[0] | {'classname': 'Foreign.Test'}] + cases[1:],
                        [cases[0] | {'outcome': '<failure/>'}] + cases[1:], [cases[0] | {'outcome': '<skipped/>'}] + cases[1:]]:
            self.assertTrue(self.collect(changed)['errors'])
        self.assertTrue(self.collect(stale=True)['errors'])
        for marker in (0, 2): self.assertTrue(self.collect(markers=marker)['errors'])

    def test_native_input_network_and_cleanup_checks_cannot_be_replaced_by_direct_client_calls(self):
        source = (lt.ROOT / lt.ANDROID_POPUP_SOURCE).read_text()
        for required in ('WebView(owner, Modifier.fillMaxSize()', 'performTouchInput', 'fixtureActivated',
                         'ServerSocket', 'native.parent', 'lastPopupRejection', 'KeyCharacterMap.VIRTUAL_KEYBOARD', 'sendNativeBack'):
            self.assertIn(required, source)
        for forbidden in ('onCreateWindow(', 'sendActionsForControlEvents', 'assumeTrue(', '@Ignore', 'client =', 'factory ='):
            self.assertNotIn(forbidden, source)
        command = lt.gradle_command('android-device', self.plan(), android_serial='emulator-5588')
        self.assertIn('-Pandroid.testInstrumentationRunnerArguments.class='+lt.ANDROID_POPUP_CLASS, command)
        self.assertNotIn('--tests', command)
        self.assertTrue(command[-1].endswith(':connectedAndroidDeviceTest'))
        workflow = (lt.ROOT / '.github/workflows/gradle.yml').read_text()
        self.assertIn('android-webview-popups', workflow)
        self.assertIn('permissions:\n  contents: read', workflow)
        self.assertIn('persist-credentials: false', workflow)


if __name__ == '__main__':
    unittest.main()
