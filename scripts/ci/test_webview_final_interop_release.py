"""Owning lifecycle/selection guards; not native runtime or library passes."""
from pathlib import Path
import subprocess
import unittest

import library_tests as lt
import workflow_matrix as wm


# Exact reviewed additions only. Removing them must recover the original worker,
# root/presenter lifecycle and cleanup bytes; no broad regex or new expected revision.
FINAL_INTEROP_ADDITIONS = (
    'import platform.UIKit.UIView\n',
    'import platform.WebKit.WKWebView\n',
    '''/** Snapshot the real children of our test-owned controller, not global windows. */
private fun UIView.ownedWebViewDescendants(): List<WKWebView> {
    check(NSThread.isMainThread)
    val result = mutableListOf<WKWebView>()
    fun visit(view: UIView) {
        if (view is WKWebView) result += view
        view.subviews.forEach { child ->
            visit(child as? UIView ?: error("An owned native child was not a UIView"))
        }
    }
    visit(this)
    return result
}

''',
    '        var ownedInteropViews = emptyList<WKWebView>()\n',
    '''        stage {
            onApplicationMain {
                check(sameNativeObject(window.rootViewController, controller)) { "Refuse inspecting a foreign root" }
                ownedInteropViews = controller.view.ownedWebViewDescendants()
            }
        }
''',
    '''        // Compose1.12 queues UIKit onRelease until a real rendered transaction.
        // Recomposer idle is not that witness. Keep the root visible while its
        // captured native children actually release; never perform their cleanup here.
        stage { awaitMain("owned final WKWebView interop release while root remains attached") {
            check(sameNativeObject(window.rootViewController, controller)) { "Native test no longer owns the root" }
            ownedInteropViews.all { it.superview == null && it.window == null && it.navigationDelegate == null }
        } }
''',
)


def without_reviewed_final_interop_witness(source):
    for addition in FINAL_INTEROP_ADDITIONS:
        if source.count(addition) != 1:
            raise ValueError('Final interop witness changed; review its exact owning additions')
        source = source.replace(addition, '', 1)
    return source


class WebViewFinalInteropReleaseTests(unittest.TestCase):
    def test_normalization_recovers_exact_prior_host_not_changed_worker_or_test_bytes(self):
        path = lt.IOS_WEBVIEW_APPLICATION_SOURCES[0]
        original = subprocess.check_output(['git', 'show', '16c9a53026cb087f359a45bcfbbe4d56c1473243:' + path],
                                           cwd=lt.ROOT, text=True)
        current = (lt.ROOT / path).read_text()
        self.assertEqual(original, without_reviewed_final_interop_witness(current))
        changed_worker = current.replace('check(!started && worker == null', 'check(started && worker == null')
        self.assertNotEqual(original, without_reviewed_final_interop_witness(changed_worker))

    def test_normalization_rejects_changed_or_missing_witness_not_just_semantic_greps(self):
        current = (lt.ROOT / lt.IOS_WEBVIEW_APPLICATION_SOURCES[0]).read_text()
        for before, after in (('ownedInteropViews.all', 'ownedInteropViews.any'),
                              ('it.navigationDelegate == null', 'true'),
                              ('it.superview == null', 'true')):
            with self.assertRaises(ValueError):
                without_reviewed_final_interop_witness(current.replace(before, after))
        for addition in FINAL_INTEROP_ADDITIONS:
            with self.assertRaises(ValueError):
                without_reviewed_final_interop_witness(current.replace(addition, '', 1))

    def test_final_native_release_is_observed_before_detaching_the_owned_compose_root(self):
        source = (lt.ROOT / lt.IOS_WEBVIEW_APPLICATION_SOURCES[0]).read_text()
        close = source.split('internal fun close()', 1)[1].split('internal fun runApplicationUiTest', 1)[0]
        self.assertIn('ownedInteropViews = controller.view.ownedWebViewDescendants()', close)
        phase = 'owned final WKWebView interop release while root remains attached'
        self.assertIn(phase, close)
        self.assertLess(close.index('stage { setContent {} }'), close.index(phase))
        self.assertLess(close.index('owned root reappearance after presenter teardown'), close.index(phase))
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
