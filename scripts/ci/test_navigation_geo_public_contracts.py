"""Focused source/finite-runner regressions. Synthetic checks, not compiler/native passes."""
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


class NavigationGeoPublicContractsTests(unittest.TestCase):
    def plan(self):
        return lt.plan(lt.ROOT, 'android-device', only_modules=('calf-navigation',),
                       focus=lt.ANDROID_NAV_BACK_FOCUS)

    def collect(self, cases=None, markers=1, stale=False):
        plan = self.plan()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / plan['expected'][0]['report_directory'] / 'TEST-explicitly-synthetic.xml'
            report.parent.mkdir(parents=True)
            cases = lt.android_nav_back_identities() if cases is None else cases
            report.write_text('<testsuite>' + ''.join(
                '<testcase classname="' + c['classname'] + '" name="' + c['name'] + '">' +
                c.get('outcome', '') + '</testcase>' for c in cases) + '</testsuite>')
            now = time.time_ns()
            if stale:
                import os
                os.utime(report, ns=(now-20_000_000_000, now-20_000_000_000))
            return lt.collect_reports(root, plan, now-1_000_000_000, now+1_000_000_000,
                                      Counter({plan['expected'][0]['task']: markers}))

    def test_existing_public_android_types_are_exported_without_consumer_workarounds(self):
        nav = (lt.ROOT / 'calf-navigation/build.gradle.kts').read_text()
        geo = (lt.ROOT / 'calf-geo/build.gradle.kts').read_text()
        self.assertIn('api(libs.android.navigation.compose)', nav)
        for dependency in ('appcompat', 'lifecycle.extensions', 'play.services.location'):
            self.assertIn('api(libs.'+dependency+')', geo)
            self.assertNotIn('implementation(libs.'+dependency+')', geo)
        build = (lt.ROOT / 'tests/consumer/navigation-geo-source/build.gradle.kts').read_text()
        for forbidden in ('androidx.navigation:', 'play-services-location:', 'androidx.fragment:',
                          'androidx.lifecycle:', 'module.publication', 'mavenLocal()'):
            self.assertNotIn(forbidden, build)

    def test_common_consumer_keeps_two_explicit_source_substitutions_and_six_compiler_tasks(self):
        fixture = lt.ROOT / 'tests/consumer/navigation-geo-source'
        settings = (fixture / 'settings.gradle.kts').read_text()
        self.assertEqual(2, settings.count('substitute(module('))
        self.assertIn('project(":calf-navigation")', settings)
        self.assertIn('project(":calf-geo")', settings)
        for forbidden in ('mavenLocal()', 'upstream', 'publishToMavenLocal'):
            self.assertNotIn(forbidden, settings.split('// Fixed explicit substitutions:', 1)[0])
        build = (fixture / 'build.gradle.kts').read_text()
        for task in ('compileAndroidMain', 'compileKotlinDesktop', 'compileKotlinJs',
                     'compileKotlinWasmJs', 'compileKotlinIosArm64', 'compileKotlinIosSimulatorArm64'):
            self.assertIn('"'+task+'"', build)
        self.assertIn('outputs.upToDateWhen { false }', build)
        self.assertIn('outputs.doNotCacheIf(', build)
        source = (fixture / 'src/commonMain/kotlin/nativecmpkit/consumer/unpublished/PublicNavGeoConsumer.kt').read_text()
        for symbol in ('rememberAdaptiveNavController()', 'rememberNavController()', 'AdaptiveNavHost(',
                       'controller: NavHostController', 'createLocationTracker()', 'startTrackingWithResult()',
                       'snapshotState.value', 'tracker.close()'):
            self.assertIn(symbol, source)
        android = (fixture / 'src/androidMain/kotlin/nativecmpkit/consumer/unpublished/PublicAndroidGeoConsumer.kt').read_text()
        for symbol in ('FragmentManager', 'Lifecycle', 'LocationResult', 'tracker.bind(lifecycle, context, fragments)',
                       'tracker.bind(lifecycle, context)', 'tracker.onLocationResult(result)', 'tracker.unbind()'):
            self.assertIn(symbol, android)

    def test_exact_one_native_method_no_accepted_navigation_geo_replay_or_slot_removal(self):
        row, = wm.matrix('android-navigation-back')['include']
        self.assertEqual(('android-device-api35', 'android-device', 'calf-navigation', lt.ANDROID_NAV_BACK_FOCUS),
                         (row['slot'], row['suite'], row['test-modules'], row['test-focus']))
        plan = self.plan()
        self.assertTrue(lt.validate_test_focus(plan))
        self.assertFalse(plan['complete_suite_requested'])
        self.assertEqual(lt.android_nav_back_identities(), plan['expected'][0]['required_testcases'])
        self.assertEqual(lt.ANDROID_NAV_BACK_CLASS, plan['expected'][0]['test_filter'])
        self.assertEqual(11, len(wm.matrix('all')['include']))
        self.assertIn('calf-navigation', lt.MINIMUM_MODULES['android-device'])

    def test_cli_choices_have_the_same_guarded_exact_focus(self):
        import android_device_tests as device
        for module, args in ((lt, ['library_tests.py', 'plan', '--suite', 'android-device', '--module',
                                  'calf-navigation', '--focus', lt.ANDROID_NAV_BACK_FOCUS]),
                             (device, ['android_device_tests.py', 'plan', '--api-level', '35', '--module',
                                      'calf-navigation', '--focus', lt.ANDROID_NAV_BACK_FOCUS,
                                      '--output', 'build/ci-verification/navback-fixture'])):
            with patch('sys.argv', args), patch('sys.stdout', new=io.StringIO()) as output:
                self.assertEqual(0, module.main())
            self.assertIn(lt.ANDROID_NAV_BACK_FOCUS, output.getvalue())

    def test_invalid_suite_module_arbitrary_filter_and_broad_success_claim_are_rejected(self):
        for suite, modules in (('desktop', ('calf-navigation',)), ('android-host', ('calf-navigation',)),
                               ('android-device', None), ('android-device', ('calf-navigation', 'calf-geo')),
                               ('android-device', ('calf-webview',))):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                lt.plan(lt.ROOT, suite, only_modules=modules, focus=lt.ANDROID_NAV_BACK_FOCUS)
        for field, value in (('test_filter', '*'), ('required_testcases', [])):
            bad = deepcopy(self.plan()); bad['expected'][0][field] = value
            with self.assertRaises(ValueError): lt.validate_test_focus(bad)
        bad = deepcopy(self.plan()); bad['complete_suite_requested'] = True
        with self.assertRaises(ValueError): lt.validate_test_focus(bad)

    def test_missing_skipped_failed_duplicate_unrelated_stale_or_no_task_marker_cannot_pass(self):
        self.assertEqual([], self.collect()['errors'])
        identity = lt.android_nav_back_identities()[0]
        for cases in ([], [{**identity, 'outcome':'<skipped/>'}], [{**identity, 'outcome':'<failure/>'}],
                      [identity, identity], [identity, {'classname':'unrelated', 'name':'not-selected'}]):
            result = self.collect(cases=cases)
            self.assertTrue(result['errors'] or result['totals']['skipped'] or result['totals']['failures'])
        self.assertTrue(self.collect(markers=0)['errors'])
        self.assertTrue(self.collect(stale=True)['errors'])

    def test_public_host_uses_real_native_back_and_preserves_explicit_unsupported_contracts(self):
        source = (lt.ROOT / lt.ANDROID_NAV_BACK_SOURCE).read_text()
        for token in ('rememberAdaptiveNavController()', 'rememberNavController()', 'AdaptiveNavHost(current, "home")',
                      'automation.injectInputEvent(event, true)', 'SystemClock.uptimeMillis()',
                      'InputDevice.SOURCE_KEYBOARD', 'KeyCharacterMap.VIRTUAL_KEYBOARD', 'KeyEvent.KEYCODE_BACK',
                      'assertEquals(1, disposedVisits.count', 'mounted = false'):
            self.assertIn(token, source)
        for forbidden in ('onBackPressed()', 'onBackPressedDispatcher.onBackPressed()', 'AndroidBackHandler(',
                          '@Ignore', '@Disabled', 'sample.'):
            self.assertNotIn(forbidden, source)
        docs = (lt.ROOT / 'calf-navigation/README.md').read_text()
        for token in ('predictive', 'gesture progress/animation is not implemented', 'not implemented', 'popBackStack'):
            self.assertIn(token, docs)

    def test_native_command_uses_exact_instrumentation_class_and_read_only_workflow(self):
        command = lt.gradle_command('android-device', self.plan(), android_serial='emulator-5588', root=lt.ROOT)
        self.assertIn('-Pandroid.testInstrumentationRunnerArguments.class='+lt.ANDROID_NAV_BACK_CLASS, command)
        self.assertNotIn('--tests', command)
        self.assertEqual(':calf-navigation:connectedAndroidDeviceTest', command[-1])
        workflow = (lt.ROOT / '.github/workflows/gradle.yml').read_text()
        self.assertIn('android-navigation-back', workflow)
        self.assertIn('permissions:\n  contents: read', workflow)
        self.assertIn('persist-credentials: false', workflow)


if __name__ == '__main__':
    unittest.main()
