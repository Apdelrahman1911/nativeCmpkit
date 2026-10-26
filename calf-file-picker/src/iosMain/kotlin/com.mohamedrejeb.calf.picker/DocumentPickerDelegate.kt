package com.mohamedrejeb.calf.picker

import platform.Foundation.NSURL
import platform.UIKit.UIAdaptivePresentationControllerDelegateProtocol
import platform.UIKit.UIDocumentPickerDelegateProtocol
import platform.UIKit.UIDocumentPickerViewController
import platform.UIKit.UIPresentationController
import platform.UIKit.presentationController
import platform.darwin.NSObject
import kotlin.concurrent.AtomicInt

/**
 * Delegate of a presented [UIDocumentPickerViewController] that reports exactly one outcome per
 * presentation.
 *
 * A dismissal can arrive through `documentPickerWasCancelled`, through
 * `presentationControllerDidDismiss` alone (a swipe that starts before the presentation animation
 * ends fires only that one), or through both, so every callback goes through one guard.
 */
internal class DocumentPickerDelegate(
    private val onPicked: (List<NSURL>) -> Unit,
    private val onCancelled: () -> Unit,
    private val onDismissed: () -> Unit = {},
) : NSObject(), UIDocumentPickerDelegateProtocol, UIAdaptivePresentationControllerDelegateProtocol {
    private val finished = AtomicInt(0)
    private val dismissed = AtomicInt(0)
    private var attachedPicker: UIDocumentPickerViewController? = null
    private var attachedOnce = false

    /** Arms this delegate for a new presentation of [picker]; call it before presenting. */
    fun attachTo(picker: UIDocumentPickerViewController) {
        check(!attachedOnce) { "Use a new delegate for each document-picker session" }
        attachedOnce = true
        attachedPicker = picker
        picker.delegate = this
        picker.presentationController?.delegate = this
    }

    override fun documentPicker(
        controller: UIDocumentPickerViewController,
        didPickDocumentsAtURLs: List<*>,
    ) {
        if (controller == attachedPicker && finishOnce()) onPicked(didPickDocumentsAtURLs.filterIsInstance<NSURL>())
    }

    override fun documentPicker(controller: UIDocumentPickerViewController, didPickDocumentAtURL: NSURL) {
        if (controller == attachedPicker && finishOnce()) onPicked(listOf(didPickDocumentAtURL))
    }

    override fun documentPickerWasCancelled(controller: UIDocumentPickerViewController) {
        if (controller == attachedPicker && finishOnce()) onCancelled()
    }

    override fun presentationControllerDidDismiss(presentationController: UIPresentationController) {
        if (presentationController.presentedViewController != attachedPicker || !dismissed.compareAndSet(0, 1)) return
        val notifyCancelled = finishOnce()
        // This is a native lifetime event even when a result/disposal already claimed the outcome.
        onDismissed()
        if (notifyCancelled) onCancelled()
    }

    private fun finishOnce(): Boolean = finished.compareAndSet(0, 1)

    /** Invalidates late native callbacks before disposal; no synthetic cancellation delivery. */
    fun close() {
        finished.compareAndSet(0, 1)
        dismissed.compareAndSet(0, 1)
        attachedPicker?.delegate = null
        attachedPicker?.presentationController?.delegate = null
        attachedPicker = null
    }
}
