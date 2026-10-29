package com.mohamedrejeb.calf.picker

import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.objcPtr
import platform.Foundation.NSThread
import platform.UIKit.UISceneActivationStateForegroundActive
import platform.UIKit.UIViewController
import platform.UIKit.transitionCoordinator
import platform.darwin.dispatch_async
import platform.darwin.dispatch_get_main_queue

/**
 * Admission and native call are one non-suspending main-thread operation. In particular, the
 * saver calls this AFTER its suspendable staging: an earlier idle check is not a reservation.
 * Do not replace another launcher's modal or present from a detached/background scene.
 */
internal fun presentIosDialog(presenter: UIViewController, session: IosDialogSession) =
    presentIosDialog(presenter, session) { controller, completed ->
        presenter.presentViewController(controller, true, completed)
    }

/** Per-call scheduling boundary for the deferred-admission regression; no global native hook. */
internal fun presentIosDialog(
    presenter: UIViewController,
    session: IosDialogSession,
    present: (UIViewController, () -> Unit) -> Unit,
) {
    check(NSThread.isMainThread) { "Present iOS dialogs from the main thread" }
    val window = checkNotNull(presenter.viewIfLoaded?.window) { "The presenter is not attached to a window" }
    check(!window.hidden) { "The presenter's window is hidden" }
    window.windowScene?.let { scene ->
        check(scene.activationState == UISceneActivationStateForegroundActive) { "The presenter's scene is not active" }
    }
    var ancestor: UIViewController? = presenter
    while (ancestor != null) {
        check(!ancestor.isBeingPresented() && !ancestor.isBeingDismissed()) { "The presenter is transitioning" }
        check(ancestor.presentedViewController == null) { "The presenter already has a presented controller" }
        ancestor = ancestor.parentViewController
    }
    val controller = checkNotNull(session.controller)
    check(controller.presentingViewController == null && !controller.isBeingPresented() && !controller.isBeingDismissed())
    session.beginPresentation { completed -> dismissOwnedIosDialog(presenter, controller, completed) }
    try {
        present(controller, session::presentationCompleted)
    } catch (failure: Throwable) {
        // UIKit's void call may enqueue work before links/transition flags appear. Even an
        // exception after entering that call does not prove the queued consumer cannot attach.
        // Request finish, but keep ownership until a real presentation/dismissal completion.
        session.finish()
        throw failure
    }
    // Absence of synchronous links is NOT a rejection acknowledgement. Cancellation in this
    // interval remains Presenting and retains delegates/export staging until UIKit completes.
    // If UIKit supplies no completion at all, fail-closed retention is intentional; admission
    // preflight cannot certify every OS/provider refusal, and that remains a native test gate.
}

/**
 * UIKit may defer all links, or establish an owning presenter's forward link before the
 * controller's backlink/animation flags. Absence is meaningful for dismissal only after the
 * session observed a native completion; never infer admission rejection from this projection.
 * Observe both directions and the presenter's containment ancestors, by exact native identity.
 * Never mistake an unrelated modal or two nil pointers for our controller. Keep these objects
 * alive during this UI-thread operation; do not cache/export native addresses.
 */
@OptIn(ExperimentalForeignApi::class)
internal fun iosDialogHasNoPresentation(presenter: UIViewController, controller: UIViewController): Boolean {
    check(NSThread.isMainThread) { "Observe iOS dialogs from the main thread" }
    if (controller.presentingViewController != null || controller.isBeingPresented() || controller.isBeingDismissed()) return false
    var ancestor: UIViewController? = presenter
    while (ancestor != null) {
        val presented = ancestor.presentedViewController
        if (presented != null && presented.objcPtr() == controller.objcPtr()) return false
        ancestor = ancestor.parentViewController
    }
    return true
}

private fun dismissOwnedIosDialog(presenter: UIViewController, controller: UIViewController, completed: () -> Unit) {
    check(NSThread.isMainThread) { "Dismiss iOS dialogs from the main thread" }
    if (iosDialogHasNoPresentation(presenter, controller)) {
        completed()
        return
    }
    if (controller.isBeingDismissed()) {
        // UIDocumentPicker can already be dismissing itself. Interactive cancellation is a
        // rollback, not permission to delete export staging: dismiss our controller afterwards.
        val registered = controller.transitionCoordinator?.animateAlongsideTransition(null) { context ->
            if (context != null && !context.isCancelled()) completed()
            else {
                // Let UIKit finish its rollback before requesting a noninteractive dismissal.
                dispatch_async(dispatch_get_main_queue()) { dismissOwnedIosDialog(presenter, controller, completed) }
            }
        } == true
        if (registered) return
    }
    // No usable coordinator: request dismissal of OUR controller only. Completion and the
    // adaptive didDismiss delegate are both idempotent. If UIKit supplies neither, retaining
    // ownership is safer than a timer/early deletion; hosted UIKit tests must cover this path.
    controller.dismissViewControllerAnimated(false, completed)
    if (iosDialogHasNoPresentation(presenter, controller)) completed()
}
