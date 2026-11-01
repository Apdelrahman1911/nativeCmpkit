package com.mohamedrejeb.calf.picker

import platform.Foundation.NSItemProvider
import platform.PhotosUI.PHPickerResult
import platform.PhotosUI.PHPickerViewController
import platform.PhotosUI.PHPickerViewControllerDelegateProtocol
import platform.UIKit.UIAdaptivePresentationControllerDelegateProtocol
import platform.UIKit.UIPresentationController
import platform.darwin.NSObject

/** The same session guard applies to empty, nonempty, duplicate and dismissal callbacks. */
internal class PhotoPickerDelegate(
    private val session: IosDialogSession,
    private val onPicked: (List<() -> NSItemProvider>) -> Unit,
    private val onCancelled: () -> Unit,
) : NSObject(), PHPickerViewControllerDelegateProtocol, UIAdaptivePresentationControllerDelegateProtocol {
    override fun picker(picker: PHPickerViewController, didFinishPicking: List<*>) {
        finishProviderSources(picker) {
            didFinishPicking.filterIsInstance<PHPickerResult>().map { result ->
                { result.itemProvider }
            }
        }
    }

    /** Post-extraction provider arrival shares the native result's owning session guard. */
    internal fun pickerProviders(
        picker: PHPickerViewController,
        providers: List<NSItemProvider>,
    ) {
        finishProviderSources(picker) {
            providers.map { provider -> { provider } }
        }
    }

    private fun finishProviderSources(
        picker: PHPickerViewController,
        sources: () -> List<() -> NSItemProvider>,
    ) {
        if (picker != session.controller || !session.claimResult()) return
        onPicked(sources())
    }

    override fun presentationControllerDidDismiss(presentationController: UIPresentationController) {
        if (presentationController.presentedViewController != session.controller) return
        val notifyCancelled = session.claimResult()
        session.dismissalCompleted()
        if (notifyCancelled) onCancelled()
    }
}
