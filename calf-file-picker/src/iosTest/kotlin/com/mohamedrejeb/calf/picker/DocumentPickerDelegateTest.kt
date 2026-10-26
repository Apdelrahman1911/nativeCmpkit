package com.mohamedrejeb.calf.picker

import platform.Foundation.NSURL
import platform.UIKit.UIDocumentPickerViewController
import platform.UIKit.UIPresentationController
import platform.UniformTypeIdentifiers.UTTypeData
import kotlin.test.Test
import kotlin.test.assertEquals

/**
 * A dismissal can report through `documentPickerWasCancelled`, through
 * `presentationControllerDidDismiss` alone (a swipe that starts before the presentation animation
 * ends), or through both. Each presentation must report exactly one outcome.
 */
class DocumentPickerDelegateTest {
    private val outcomes = mutableListOf<String>()
    private val delegate = DocumentPickerDelegate(
        onPicked = { urls -> outcomes += "picked ${urls.map { it.lastPathComponent }}" },
        onCancelled = { outcomes += "cancelled" },
    )
    private val picker = UIDocumentPickerViewController(forOpeningContentTypes = listOf(UTTypeData))
    private val presentation = UIPresentationController(
        presentedViewController = picker,
        presentingViewController = null,
    )

    @Test
    fun aSwipeDismissWithoutACancelCallbackReportsCancelled() {
        delegate.attachTo(picker)

        delegate.presentationControllerDidDismiss(presentation)

        assertEquals(listOf("cancelled"), outcomes)
    }

    @Test
    fun aCancelFollowedByASwipeDismissReportsCancelledOnce() {
        delegate.attachTo(picker)

        delegate.documentPickerWasCancelled(picker)
        delegate.presentationControllerDidDismiss(presentation)

        assertEquals(listOf("cancelled"), outcomes)
    }

    @Test
    fun aPickFollowedByASwipeDismissReportsOnlyThePick() {
        delegate.attachTo(picker)

        delegate.documentPicker(picker, didPickDocumentsAtURLs = listOf(NSURL.fileURLWithPath("/tmp/a.pdf")))
        delegate.presentationControllerDidDismiss(presentation)

        assertEquals(listOf("picked [a.pdf]"), outcomes)
    }

    @Test
    fun theNextPresentationReportsAgain() {
        delegate.attachTo(picker)
        delegate.documentPickerWasCancelled(picker)

        delegate.close()
        val next = DocumentPickerDelegate(
            onPicked = { urls -> outcomes += "picked ${urls.map { it.lastPathComponent }}" },
            onCancelled = { outcomes += "cancelled" },
        )
        next.attachTo(picker)
        delegate.documentPicker(picker, didPickDocumentsAtURLs = listOf(NSURL.fileURLWithPath("/tmp/stale.pdf")))
        next.documentPicker(picker, didPickDocumentsAtURLs = listOf(NSURL.fileURLWithPath("/tmp/b.pdf")))

        assertEquals(listOf("cancelled", "picked [b.pdf]"), outcomes)
    }

    @Test fun duplicateNonemptyCallbacksAreIgnored() {
        delegate.attachTo(picker)
        val urls = listOf(NSURL.fileURLWithPath("/tmp/a.pdf"))
        delegate.documentPicker(picker, didPickDocumentsAtURLs = urls)
        delegate.documentPicker(picker, didPickDocumentsAtURLs = urls)
        assertEquals(listOf("picked [a.pdf]"), outcomes)
    }

    @Test fun nativeDismissalIsReportedAfterAnAlreadyDeliveredResult() {
        var dismissals = 0
        val retained = DocumentPickerDelegate(
            onPicked = { outcomes += "picked" },
            onCancelled = { outcomes += "cancelled" },
            onDismissed = { dismissals++ },
        )
        retained.attachTo(picker)
        retained.documentPicker(picker, didPickDocumentsAtURLs = listOf(NSURL.fileURLWithPath("/tmp/a.pdf")))
        retained.presentationControllerDidDismiss(presentation)
        retained.presentationControllerDidDismiss(presentation)
        assertEquals(listOf("picked"), outcomes)
        assertEquals(1, dismissals)
        retained.close()
    }
}
