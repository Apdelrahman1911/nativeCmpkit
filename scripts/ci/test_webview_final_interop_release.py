"""Owning lifecycle/selection guards; not native runtime or library passes."""
from pathlib import Path
import unittest

import library_tests as lt
import workflow_matrix as wm


class WebViewFinalInteropReleaseTests(unittest.TestCase):
    def test_final_native_release_is_observed_before_detaching_the_owned_compose_root(self):
        source = (lt.ROOT / lt.IOS_WEBVIEW_APPLICATION_SOURCES[0]).read_text()
        close = source.split('internal fun close()', 1)[1].split('internal fun runApplicationUiTest', 1)[0]
        self.assertIn('ownedInteropViews = controller.view.ownedWebViewDescendants()', close)
        phase = 'owned final WKWebView interop release while root remains attached'
        self.assertIn(phase, close)
        self.assertLess(close.index('stage { setContent {} }'), close.index(phase))
        self.assertLess(close.index(phase), close.index('window.rootViewController = previous'))
        for required in ('it.superview == null', 'it.window == null', 'it.navigationDelegate == null'):
            self.assertIn(required, close)
        for forbidden in ('releaseIosWebView(', '.removeFromSuperview()', 'Thread.sleep(', 'delay(', 'currentDisposed('):
            self.assertNotIn(forbidden, close)
        self.assertIn('NSProcessInfo.processInfo.systemUptime + 10.0', source)
        self.assertIn('stage { awaitMain("owned root disappearance after restoration")', close)
        regression = (lt.ROOT / lt.IOS_WEBVIEW_LIFECYCLE_SOURCE).read_text()
        self.assertIn('assertEquals(2, disposed.size)', regression)
        self.assertIn('assertEquals(2, created.size)', regression)
        self.assertIn('created.forEach { assertNull(it.navigationDelegate); assertNull(it.superview) }', regression)

    def test_recovery_only_selects_the_failed_apple_remount_not_the_accepted_android_or_other_methods(self):
        profile = 'webview-identity-ios-remount-recovery'
        row, = wm.matrix(profile)['include']
        self.assertEqual(('ios-iphone', 'ios', 'calf-webview', lt.IOS_WEBVIEW_REMOUNT_RECOVERY_FOCUS),
                         (row['slot'], row['suite'], row['test-modules'], row['test-focus']))
        plan = lt.plan(lt.ROOT, 'ios', only_modules=('calf-webview',), focus=row['test-focus'])
        self.assertTrue(lt.validate_test_focus(plan))
        self.assertEqual(1, len(plan['expected'][0]['required_testcases']))
        self.assertEqual(lt.IOS_WEBVIEW_LIFECYCLE_METHODS[0] + '[iosSimulatorArm64]',
                         plan['expected'][0]['required_testcases'][0]['name'])
        self.assertEqual(11, len(wm.matrix('all')['include']))
        self.assertEqual(2, len(wm.matrix('webview-identity-remount-recovery')['include']))
        slots = wm.preflight_plans(profile)['slots']
        self.assertEqual(1, len(slots))
        self.assertEqual(0, slots[0]['exit_code'])


if __name__ == '__main__':
    unittest.main()
