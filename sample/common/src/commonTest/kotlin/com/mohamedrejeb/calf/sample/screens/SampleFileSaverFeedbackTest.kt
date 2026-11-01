// Test-only sample caller regression (2026-11-01); unexecuted proposal, not library/browser evidence.
package com.mohamedrejeb.calf.sample.screens

import com.mohamedrejeb.calf.picker.FilePickerException
import com.mohamedrejeb.calf.picker.FileSaverEvent
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Exercises the exact pure event-to-UI mapping used by FileSaverScreen, not an OS download. */
class SampleFileSaverFeedbackTest {
    @Test fun downloadStartedLeavesWaitingWithoutClaimingSavedOrCancelled() {
        var feedback = SampleSaverFeedback(true, false, "Waiting for save destination…")
        assertTrue(feedback.isSaving)
        feedback = FileSaverEvent.DownloadStarted("profile_picture.png").toSampleSaverFeedback()
        assertFalse(feedback.isSaving)
        assertFalse(feedback.failed)
        assertEquals("Download requested: profile_picture.png. Check your browser's downloads.", feedback.message)
        assertFalse(feedback.message.contains("Saved"))
        assertFalse(feedback.message.contains("cancelled"))
    }

    @Test fun cancellationLeavesWaitingButDoesNotBecomeAFailure() {
        val feedback = FileSaverEvent.Cancelled.toSampleSaverFeedback()
        assertFalse(feedback.isSaving)
        assertFalse(feedback.failed)
        assertEquals("Save cancelled", feedback.message)
    }

    @Test fun failureLeavesWaitingAndDoesNotExposeTheDiagnosticMessage() {
        val feedback = FileSaverEvent.Failed(FilePickerException("not user-facing platform detail")).toSampleSaverFeedback()
        assertFalse(feedback.isSaving)
        assertTrue(feedback.failed)
        assertEquals("Export failed. Try again.", feedback.message)
        assertFalse(feedback.message.contains("platform detail"))
    }

    @Test fun laterDownloadRequestClearsEarlierFailureAndKeepsItsLiteralSuggestedName() {
        var feedback = FileSaverEvent.Failed(FilePickerException("diagnostic")).toSampleSaverFeedback()
        assertTrue(feedback.failed)
        feedback = FileSaverEvent.DownloadStarted("Résumé 最終.png").toSampleSaverFeedback()
        assertFalse(feedback.isSaving)
        assertFalse(feedback.failed)
        assertEquals("Download requested: Résumé 最終.png. Check your browser's downloads.", feedback.message)
        feedback = FileSaverEvent.Cancelled.toSampleSaverFeedback()
        assertFalse(feedback.isSaving)
        assertFalse(feedback.failed)
        assertEquals("Save cancelled", feedback.message)
    }
}
