package com.mohamedrejeb.calf.picker

import platform.PhotosUI.PHPickerResult
import platform.PhotosUI.PHPickerViewController
import platform.PhotosUI.PHPickerViewControllerDelegateProtocol
import platform.UIKit.UIAdaptivePresentationControllerDelegateProtocol
import platform.UIKit.UIPresentationController
import platform.darwin.NSObject

/** The same session guard applies to empty, nonempty, duplicate and dismissal callbacks. */
internal class PhotoPickerDelegate(
    private val session: IosDialogSession,
    private val onPicked: (List<PHPickerResult>) -> Unit,
    private val onCancelled: () -> Unit,
) : NSObject(), PHPickerViewControllerDelegateProtocol, UIAdaptivePresentationControllerDelegateProtocol {
    override fun picker(picker: PHPickerViewController, didFinishPicking: List<*>) {
        if (picker != session.controller || !session.claimResult()) return
        onPicked(didFinishPicking.filterIsInstance<PHPickerResult>())
    }

    override fun presentationControllerDidDismiss(presentationController: UIPresentationController) {
        if (presentationController.presentedViewController != session.controller) return
        val notifyCancelled = session.claimResult()
        session.dismissalCompleted()
        if (notifyCancelled) onCancelled()
    }
}
