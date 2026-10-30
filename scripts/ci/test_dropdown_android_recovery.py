"""Owning Android input/finite-recovery fixtures; not actual library/native passes."""
from collections import Counter
from copy import deepcopy
import io
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

import library_tests as lt
import workflow_matrix as wm


class DropdownAndroidRecoveryTests(unittest.TestCase):
    def test_native_key_events_have_current_uptime_and_explicit_keyboard_identity(self):
        source = (lt.ROOT / lt.dropdown_platform_source('android-device')).read_text()
        back = source.split('internal actual fun ComposeUiTest.dropdownBack(', 1)[1].split('internal actual fun ComposeUiTest.dropdownOutside()', 1)[0]
        for required in ('val downTime = SystemClock.uptimeMillis()', 'KeyEvent(downTime, SystemClock.uptimeMillis()',
                         'KeyCharacterMap.VIRTUAL_KEYBOARD', 'KeyEvent.FLAG_FROM_SYSTEM', 'InputDevice.SOURCE_KEYBOARD',
                         'assertTrue(automation.injectInputEvent(event, true)'):
            self.assertIn(required, back)
        self.assertNotIn('KeyEvent(KeyEvent.ACTION_', back)
        outside = source.split('internal actual fun ComposeUiTest.dropdownOutside()', 1)[1]
        self.assertIn('MotionEvent.obtain(time, SystemClock.uptimeMillis()', outside)
        self.assertNotIn('time +', outside)

    def plan(self):
        return lt.plan(lt.ROOT, 'android-device', only_modules=('calf-ui',), focus=lt.DROPDOWN_ANDROID_RECOVERY_FOCUS)

    def cases(self):
        return [{'classname': lt.DROPDOWN_CLASS, 'name': lt.DROPDOWN_METHODS[-1], 'status': 'passed'}]

    def collect(self, cases, markers=1):
        plan = self.plan()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / plan['expected'][0]['report_directory'] / 'TEST-recovery.xml'
            report.parent.mkdir(parents=True)
            outcomes = {'passed': '', 'failed': '<failure/>', 'skipped': '<skipped/>'}
            report.write_text('<testsuite>' + ''.join(
                '<testcase classname="' + c['classname'] + '" name="' + c['name'] + '">' + outcomes[c['status']] + '</testcase>' for c in cases) + '</testsuite>')
            now = time.time_ns()
            return lt.collect_reports(root, plan, now-1_000_000_000, now+1_000_000_000,
                                      Counter({plan['expected'][0]['task']: markers}))

    def test_exact_one_failed_android_method_without_replaying_fifteen_accepted_executions(self):
        row, = wm.matrix('ui-dropdown-android-recovery')['include']
        self.assertEqual(('android-device-api35', 'android-device', 'calf-ui', lt.DROPDOWN_ANDROID_RECOVERY_FOCUS),
                         (row['slot'], row['suite'], row['test-modules'], row['test-focus']))
        plan = self.plan()
        self.assertTrue(lt.validate_test_focus(plan))
        self.assertEqual([{'classname': lt.DROPDOWN_CLASS, 'name': lt.DROPDOWN_METHODS[-1]}], plan['expected'][0]['required_testcases'])
        self.assertEqual(lt.DROPDOWN_CLASS+'#'+lt.DROPDOWN_METHODS[-1], plan['expected'][0]['test_filter'])
        self.assertEqual(11, len(wm.matrix('all')['include']))
        for row in wm.matrix('ui-dropdown-platforms')['include']:
            full = lt.plan(lt.ROOT, row['suite'], only_modules=('calf-ui',), focus=lt.DROPDOWN_FOCUS)
            self.assertEqual(4, len(full['expected'][0]['required_testcases']))

    def test_actual_library_device_and_workflow_cli_preflights_allow_only_the_finite_recovery(self):
        import android_device_tests as device
        for module, args in [(lt, ['library_tests.py', 'plan', '--suite', 'android-device', '--module', 'calf-ui', '--focus', lt.DROPDOWN_ANDROID_RECOVERY_FOCUS]),
                             (device, ['android_device_tests.py', 'plan', '--api-level', '35', '--module', 'calf-ui', '--focus', lt.DROPDOWN_ANDROID_RECOVERY_FOCUS,
                                       '--output', 'build/ci-verification/recovery-fixture'])]:
            with patch('sys.argv', args), patch('sys.stdout', io.StringIO()):
                self.assertEqual(0, module.main())
        preflight = wm.preflight_plans('ui-dropdown-android-recovery')
        self.assertEqual(1, len(preflight['slots']))
        self.assertEqual(0, preflight['slots'][0]['exit_code'])

    def test_foreign_suite_modules_wildcards_and_full_suite_claims_are_rejected(self):
        for suite, modules in [('desktop', ('calf-ui',)), ('js', ('calf-ui',)), ('wasm', ('calf-ui',)), ('ios', ('calf-ui',)),
                               ('android-host', ('calf-ui',)), ('android-device', ('calf-io',)), ('android-device', ('calf-ui', 'calf-io'))]:
            with self.assertRaises(ValueError):
                lt.plan(lt.ROOT, suite, only_modules=modules, focus=lt.DROPDOWN_ANDROID_RECOVERY_FOCUS)
        plan = self.plan()
        for key, value in [('test_filter', '*'), ('required_testcases', lt.dropdown_identities()), ('test_source_files', [])]:
            changed = deepcopy(plan); changed['expected'][0][key] = value
            with self.assertRaises(ValueError): lt.validate_test_focus(changed)
        plan['complete_suite_requested'] = True
        with self.assertRaises(ValueError): lt.validate_test_focus(plan)

    def test_exact_nonzero_pass_is_accepted_not_missing_duplicate_old_matrix_or_unexecuted_xml(self):
        self.assertEqual([], self.collect(self.cases())['errors'])
        full = [{'classname': lt.DROPDOWN_CLASS, 'name': n, 'status': 'passed'} for n in lt.DROPDOWN_METHODS]
        variants = [[], self.cases()*2, full, [self.cases()[0] | {'name': 'foreign'}],
                    [self.cases()[0] | {'classname': 'Foreign.Test'}], [self.cases()[0] | {'status': 'failed'}],
                    [self.cases()[0] | {'status': 'skipped'}]]
        for cases in variants:
            with self.subTest(cases=cases): self.assertTrue(self.collect(cases)['errors'])
        for marker in [0, 2]: self.assertTrue(self.collect(self.cases(), marker)['errors'])

    def test_device_transport_filters_exactly_the_failed_native_method(self):
        command = lt.gradle_command('android-device', self.plan(), android_serial='emulator-5588')
        self.assertIn('-Pandroid.testInstrumentationRunnerArguments.class='+lt.DROPDOWN_CLASS+'#'+lt.DROPDOWN_METHODS[-1], command)
        self.assertNotIn('-Pandroid.testInstrumentationRunnerArguments.class='+lt.DROPDOWN_CLASS+'.'+lt.DROPDOWN_METHODS[-1], command)
        self.assertNotIn('--tests', command)

    def test_accepted_skiko_shared_material_and_wrapper_bytes_remain_unchanged(self):
        paths = [lt.DROPDOWN_SCENARIOS_SOURCE,
                 'calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/dropdown/AdaptiveDropDown.material.kt']
        for suite in ['desktop', 'js', 'wasm']:
            paths += [lt.dropdown_source(suite), lt.dropdown_platform_source(suite)]
        paths += [lt.dropdown_source('android-device')]
        for path in paths:
            original = subprocess.check_output(['git', 'show', '36ec139b2a0e6ead1b161abcd72afef493d7665d:'+path], cwd=lt.ROOT)
            self.assertEqual(original, (lt.ROOT/path).read_bytes())
        path = lt.dropdown_platform_source('android-device')
        before = subprocess.check_output(['git', 'show', '36ec139b2a0e6ead1b161abcd72afef493d7665d:'+path], cwd=lt.ROOT, text=True)
        actual = (lt.ROOT/path).read_text()
        self.assertEqual(before.split('internal actual fun dropdownPosition(',1)[1].split('internal actual fun ComposeUiTest.dropdownBack(',1)[0],
                         actual.split('internal actual fun dropdownPosition(',1)[1].split('internal actual fun ComposeUiTest.dropdownBack(',1)[0])

    def test_native_input_never_calls_the_menu_callback_or_weakens_delivery_or_resource_checks(self):
        source = (lt.ROOT/lt.dropdown_platform_source('android-device')).read_text()
        for required in ['KeyEvent.KEYCODE_ESCAPE', 'InputDevice.SOURCE_TOUCHSCREEN', 'event.recycle()', 'screen.recycle()']:
            self.assertIn(required, source)
        for forbidden in ['input.completeBack()', 'onDismissRequest(', '@Ignore', 'assumeTrue(', 'Thread.sleep(', 'delay(']:
            self.assertNotIn(forbidden, source)
        workflow = (lt.ROOT/'.github/workflows/gradle.yml').read_text()
        self.assertIn('ui-dropdown-android-recovery', workflow)
        self.assertIn('permissions:\n  contents: read', workflow)
        self.assertIn('persist-credentials: false', workflow)


if __name__ == '__main__':
    unittest.main()
