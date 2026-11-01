// Test-only sample event mapping (2026-11-01); unexecuted proposal, no file write/native-save claim.
package com.mohamedrejeb.calf.sample.screens

import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.io.fromUriString
import com.mohamedrejeb.calf.picker.FileSaverEvent
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

/** Desktop is only used to construct a KmpFile; this test never creates or writes that file. */
class SampleFileSaverSavedFeedbackTest {
    @Test fun onlyASavedEventClaimsSavedAndClearsTheWaitingState() {
        val file = assertNotNull(KmpFile.fromUriString("file:///tmp/nativecmpkit-sample-status-only.png"))
        var feedback = SampleSaverFeedback(true, false, "Waiting for save destination…")
        assertTrue(feedback.isSaving)
        feedback = FileSaverEvent.Saved(file).toSampleSaverFeedback()
        assertFalse(feedback.isSaving)
        assertFalse(feedback.failed)
        assertEquals("Saved successfully", feedback.message)
        val requested = FileSaverEvent.DownloadStarted("nativecmpkit-sample-status-only.png").toSampleSaverFeedback()
        assertFalse(requested.isSaving)
        assertFalse(requested.failed)
        assertTrue(requested.message.startsWith("Download requested:"))
        assertFalse(requested.message.contains("Saved successfully"))
    }
}
