"""Source guards for the actual UIKit alert-delegate crash, not native tests.

The immutable simulator failure is the runtime red. These lexical checks keep
the repair within supported UIKit contracts; fresh application XML and real
popover/gesture/device behavior still require their own executed evidence.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AlertDialogManager.kt"
NATIVE_TESTS = ROOT / "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/dialog/NativeAlertLifecycleTest.kt"
METHOD = "outsideDismissRequestsAndDisposalRemainExactlyOnce"


class NativeAlertDelegateContractTests(unittest.TestCase):
    def setUp(self):
        self.source = MANAGER.read_text()

    def section(self, start, end):
        self.assertIn(start, self.source)
        self.assertIn(end, self.source)
        return self.source.split(start, 1)[1].split(end, 1)[0]

    def test_alert_presentation_delegate_is_never_set_or_cleared(self):
        self.assertNotIn("presentationController?.delegate =", self.source)
        self.assertNotIn("presentationController.delegate =", self.source)
        self.assertNotIn(": UIAlertController()", self.source)
        self.assertIn("UIAlertController.alertControllerWithTitle", self.source)

    def test_only_action_sheet_popovers_receive_the_owned_supported_delegate(self):
        creation = self.section("private fun createController()", "/** Fetch callbacks")
        guard = "if (iosProperties.style == AlertDialogIosStyle.ActionSheet)"
        self.assertIn(guard, creation)
        self.assertLess(creation.index(guard), creation.index("popoverPresentationController?.apply"))
        self.assertIn("delegate = presentationDelegate", creation)
        self.assertIn("ownedPopover = this", creation)
        self.assertIn("sourceView = parentUIViewController.view", creation)

    def test_popover_and_adapted_dismissal_callbacks_share_one_owning_reconciliation(self):
        delegate = self.section("private val presentationDelegate", "private fun requireMain")
        self.assertIn("UIPopoverPresentationControllerDelegateProtocol", delegate)
        for method in ("presentationControllerShouldDismiss", "presentationControllerDidDismiss",
                       "popoverPresentationControllerShouldDismissPopover", "popoverPresentationControllerDidDismissPopover"):
            self.assertIn("override fun " + method, delegate)
        self.assertEqual(2, delegate.count("dismissedNatively("))
        self.assertEqual(2, delegate.count("canDismissNatively("))
        self.assertNotIn("onDismissRequest()", delegate)

    def test_native_dismissal_checks_main_phase_and_exact_nonnull_controller_ownership(self):
        ownership = self.section("private fun ownsNativeController", "private fun canDismissNatively")
        self.assertIn("val current = controller ?: return false", ownership)
        self.assertIn("native.presentedViewController.objcPtr() == current.objcPtr()", ownership)
        callback = self.section("private fun dismissedNatively", "private fun getController")
        self.assertIn("requireMain()", callback)
        self.assertIn("!ownsNativeController(native)", callback)
        self.assertIn("presentation.phase == NativePresentationState.Phase.Hidden", callback)
        self.assertLess(callback.index("presentation.dismissedInteractively()"), callback.index("clearController()"))
        self.assertLess(callback.index("clearController()"), callback.index("NativePresentationQueue.release"))
        self.assertLess(callback.index("NativePresentationQueue.release"), callback.index("if (notify) onDismissRequest()"))

    def test_native_policy_and_cleanup_do_not_mutate_a_foreign_delegate(self):
        policy = self.section("private fun canDismissNatively", "private fun dismissedNatively")
        self.assertIn("requireMain()", policy)
        self.assertIn("ownsNativeController(native) && !presentation.disposed && properties.dismissOnClickOutside", policy)
        cleanup = self.section("private fun clearController()", "companion object")
        self.assertIn("ownedPopover?.let", cleanup)
        self.assertIn("delegate.objcPtr() == presentationDelegate.objcPtr()", cleanup)
        self.assertIn("popover.delegate = null", cleanup)
        self.assertIn("ownedPopover = null", cleanup)
        self.assertNotIn("presentationController", cleanup)

    def test_alert_outside_gesture_retains_its_main_hit_test_and_no_action_sheet_competitor(self):
        gesture = self.section("fun onOutsideTap", "fun showAlertDialog")
        self.assertIn("requireMain()", gesture)
        self.assertIn("if (!properties.dismissOnClickOutside) return", gesture)
        self.assertIn("CGRectContainsPoint(view.bounds, sender.locationInView(view))", gesture)
        pump = self.section("private fun pump()", "private fun clearController()")
        self.assertIn("if (viewController.preferredStyle == UIAlertControllerStyleAlert)", pump)
        self.assertIn("it.cancelsTouchesInView = false", pump)
        self.assertIn("presentation.complete(transition)", pump)

    def test_new_regression_is_mandatory_without_removing_original_native_methods(self):
        native = NATIVE_TESTS.read_text()
        self.assertIn("@Test fun " + METHOD + "() = runApplicationUiTest", native)
        required = (ROOT / "scripts/ci/library_tests.py").read_text()
        self.assertIn('("dialog.NativeAlertLifecycleTest", "' + METHOD + '")', required)
        for original in ("presentedAlertUsesLatestActionAndTextFieldCallbacks",
                         "disposalDuringPresentationQueuesCleanupAndReplacement",
                         "actionSheetHasAPresentingViewPopoverAnchor"):
            self.assertIn("@Test fun " + original, native)
            self.assertIn('("dialog.NativeAlertLifecycleTest", "' + original + '")', required)
        self.assertIn("first?.dismiss(); first?.dismiss()", native)
        self.assertIn("assertEquals(1, dismissals)", native)
        self.assertIn("first?.dispose(); second?.dispose()", native)


if __name__ == "__main__":
    unittest.main()
