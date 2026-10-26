package com.mohamedrejeb.calf.picker

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
internal fun presentIosDialog(presenter: UIViewController, session: IosDialogSession) {
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
    session.beginPresentation { completed -> dismissOwnedIosDialog(controller, completed) }
    try {
        presenter.presentViewController(controller, true) { session.presentationCompleted() }
    } catch (failure: Throwable) {
        // An exception is not evidence that an already-attached native consumer stopped.
        if (controller.hasNoPresentation()) session.presentationRejected() else session.finish()
        throw failure
    }
    if (session.phase == IosDialogPhase.Presenting && controller.hasNoPresentation()) {
        session.presentationRejected()
        error("UIKit did not accept the dialog presentation")
    }
}

/** True only outside both animation phases; absence of a parent DURING presentation is not enough. */
private fun UIViewController.hasNoPresentation(): Boolean =
    presentingViewController == null && !isBeingPresented() && !isBeingDismissed()

private fun dismissOwnedIosDialog(controller: UIViewController, completed: () -> Unit) {
    check(NSThread.isMainThread) { "Dismiss iOS dialogs from the main thread" }
    if (controller.hasNoPresentation()) {
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
                dispatch_async(dispatch_get_main_queue()) { dismissOwnedIosDialog(controller, completed) }
            }
        } == true
        if (registered) return
    }
    // No usable coordinator: request dismissal of OUR controller only. Completion and the
    // adaptive didDismiss delegate are both idempotent. If UIKit supplies neither, retaining
    // ownership is safer than a timer/early deletion; hosted UIKit tests must cover this path.
    controller.dismissViewControllerAnimated(false, completed)
    if (controller.hasNoPresentation()) completed()
}
