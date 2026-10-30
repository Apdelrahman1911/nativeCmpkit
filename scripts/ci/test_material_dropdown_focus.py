"""Owning finite-input/XML fixtures, not native or library execution results."""
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


class MaterialDropdownFocusTests(unittest.TestCase):
    SUITES = ('desktop', 'android-device', 'js', 'wasm')

    def plan(self, suite):
        return lt.plan(lt.ROOT, suite, only_modules=('calf-ui',), focus=lt.DROPDOWN_FOCUS)

    def cases(self, suite):
        prefix = lt.SUITES[suite][0] + '.' if suite in {'js', 'wasm'} else ''
        suffix = {'desktop': '[desktop]', 'android-device': '',
                  'js': '[js, browser, ChromeHeadless155.0.0.0, Linux0.0.0]',
                  'wasm': '[wasmJs, browser, ChromeHeadless155.0.0.0, Linux0.0.0]'}[suite]
        return [{'classname': prefix + lt.DROPDOWN_CLASS, 'name': method + suffix, 'status': 'passed'}
                for method in lt.DROPDOWN_METHODS]

    def collect(self, suite, cases, markers=1):
        plan = self.plan(suite)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / plan['expected'][0]['report_directory'] / 'TEST-dropdown.xml'
            destination.parent.mkdir(parents=True)
            body = ''
            for case in cases:
                status = {'passed': '', 'failed': '<failure/>', 'skipped': '<skipped/>'}[case['status']]
                body += f'<testcase classname="{case["classname"]}" name="{case["name"]}">{status}</testcase>'
            destination.write_text('<testsuite>' + body + '</testsuite>')
            now = time.time_ns()
            return lt.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                      Counter({plan['expected'][0]['task']: markers}))

    def test_exact_four_runtime_plans_and_sixteen_executions_only(self):
        rows = wm.matrix('ui-dropdown-platforms')['include']
        self.assertEqual(set(self.SUITES), {row['suite'] for row in rows})
        self.assertEqual(11, len(wm.matrix('all')['include']))
        for suite in self.SUITES:
            plan = self.plan(suite)
            self.assertTrue(lt.validate_test_focus(plan))
            self.assertFalse(plan['complete_suite_requested'])
            self.assertEqual(4, len(plan['expected'][0]['required_testcases']))
            self.assertEqual(lt.DROPDOWN_CLASS, plan['expected'][0]['test_filter'])
            self.assertIn(lt.DROPDOWN_SCENARIOS_SOURCE, plan['expected'][0]['test_source_files'])
            self.assertIn(lt.dropdown_platform_source(suite), plan['expected'][0]['test_source_files'])

    def test_real_library_and_controller_cli_accept_exact_focus(self):
        for suite in self.SUITES:
            args = ['library_tests.py', 'plan', '--suite', suite, '--module', 'calf-ui', '--focus', lt.DROPDOWN_FOCUS]
            stream = io.StringIO()
            with patch('sys.argv', args), patch('sys.stdout', stream):
                self.assertEqual(0, lt.main())
        import android_device_tests as device
        args = ['android_device_tests.py', 'plan', '--api-level', '35', '--module', 'calf-ui',
                '--focus', lt.DROPDOWN_FOCUS, '--output', 'build/ci-verification/dropdown-fixture']
        with patch('sys.argv', args), patch('sys.stdout', io.StringIO()):
            self.assertEqual(0, device.main())

    def test_exact_nonzero_target_xml_is_accepted(self):
        for suite in self.SUITES:
            result = self.collect(suite, self.cases(suite))
            self.assertEqual([], result['errors'])
            self.assertEqual(4, result['totals']['passed'])

    def test_missing_extra_duplicate_foreign_failed_skipped_or_unexecuted_xml_is_rejected(self):
        for suite in self.SUITES:
            cases = self.cases(suite)
            variants = [[], cases[:-1], cases * 2, cases + [{**cases[0], 'name': 'unrelated'}]]
            for key, value in (('classname', 'Foreign.Test'), ('name', 'wrong[foreign]'),
                               ('status', 'failed'), ('status', 'skipped')):
                changed = deepcopy(cases); changed[0][key] = value; variants.append(changed)
            for changed in variants:
                with self.subTest(suite=suite, changed=changed):
                    self.assertTrue(self.collect(suite, changed)['errors'])
            for marker in (0, 2):
                self.assertTrue(self.collect(suite, cases, marker)['errors'])

    def test_foreign_suite_module_filter_and_full_suite_claim_are_rejected(self):
        for suite, modules in (('ios', ('calf-ui',)), ('android-host', ('calf-ui',)),
                               ('desktop', ('calf-share',)), ('js', ('calf-ui', 'calf-io'))):
            with self.assertRaises(ValueError):
                lt.plan(lt.ROOT, suite, only_modules=modules, focus=lt.DROPDOWN_FOCUS)
        plan = self.plan('desktop')
        for key, value in (('test_filter', '*'), ('required_testcases', []), ('test_source_files', [])):
            changed = deepcopy(plan); changed['expected'][0][key] = value
            with self.assertRaises(ValueError): lt.validate_test_focus(changed)
        plan['complete_suite_requested'] = True
        with self.assertRaises(ValueError): lt.validate_test_focus(plan)

    def test_transports_use_exact_class_without_replaying_other_ui_methods(self):
        for suite in self.SUITES:
            command = lt.gradle_command(suite, self.plan(suite), android_serial='emulator-5588' if suite == 'android-device' else None)
            if suite == 'android-device':
                self.assertIn('-Pandroid.testInstrumentationRunnerArguments.class=' + lt.DROPDOWN_CLASS, command)
                self.assertNotIn('--tests', command)
            else:
                self.assertEqual(lt.DROPDOWN_CLASS, command[command.index('--tests') + 1])
                self.assertEqual(1, command.count('--tests'))

    def test_actual_public_material_reference_pixels_inputs_and_cleanup_are_required(self):
        shared = (lt.ROOT / lt.DROPDOWN_SCENARIOS_SOURCE).read_text()
        for required in ('AdaptiveDropDown(', 'DropdownMenu(', 'scroll.scrollTo(', 'LayoutDirection.Rtl',
                         'surfaceColorAtElevation(7.dp)', 'assertEquals(0, differences', 'matchedBorder > 10',
                         'dismissOnBackPress = false', 'dismissOnClickOutside = false', 'focusable = false'):
            self.assertIn(required, shared)
        for suite in self.SUITES:
            source = (lt.ROOT / lt.dropdown_source(suite)).read_text()
            platform = (lt.ROOT / lt.dropdown_platform_source(suite)).read_text()
            for forbidden in ('@Ignore', 'assumeTrue(', 'assumeFalse(', 'sample.'):
                self.assertNotIn(forbidden, source + platform)
        native = (lt.ROOT / lt.dropdown_platform_source('android-device')).read_text()
        for required in ('uiAutomation.takeScreenshot()', 'injectInputEvent', 'screen.recycle()',
                         'event.recycle()', 'SOURCE_TOUCHSCREEN', 'localToScreen(Offset.Zero)'):
            self.assertIn(required, native)
        browser = (lt.ROOT / lt.dropdown_source('js')).read_text()
        self.assertIn('awaitSkiko.then', browser)
        self.assertIn('.unsafeCast<TestResult>()', browser)

    def test_workflow_is_readonly_reports_only_and_has_reviewed_preflight(self):
        source = (lt.ROOT / '.github/workflows/gradle.yml').read_text()
        self.assertIn('ui-dropdown-platforms', source)
        self.assertIn('permissions:\n  contents: read', source)
        self.assertIn('persist-credentials: false', source)
        self.assertTrue(wm.preflight_plans('ui-dropdown-platforms')['slots'])

    def test_skiko_back_uses_the_real_navigation_input_not_an_unbridged_semantics_escape_key(self):
        shared = (lt.ROOT / lt.DROPDOWN_SCENARIOS_SOURCE).read_text()
        for required in ('NavigationEventInput()', 'dispatchOnBackCompleted()',
                         'dispatcher.addInput(input)', 'dispatcher.removeInput(input)'):
            self.assertIn(required, shared)
        for suite in ('desktop', 'js', 'wasm'):
            platform = (lt.ROOT / lt.dropdown_platform_source(suite)).read_text()
            self.assertIn('runOnIdle { input.completeBack() }', platform)
            self.assertNotIn('pressKey(Key.Escape)', platform)
        native = (lt.ROOT / lt.dropdown_platform_source('android-device')).read_text()
        self.assertIn('KeyEvent.KEYCODE_ESCAPE', native)
        self.assertNotIn('input.completeBack()', native)


if __name__ == '__main__':
    unittest.main()
