package com.mohamedrejeb.calf.camerapicker

import androidx.compose.runtime.saveable.SaverScope
import kotlin.test.*

class CameraRequestStateTest {
    @Test fun pendingUriAndOutputAreSavedAsOneRequest() {
        val original = CameraRequestState(PendingCameraCapture("content://test/capture", "/cache/nativecmpkit-camera/capture-one.jpg"))
        val scope = object : SaverScope { override fun canBeSaved(value: Any) = true }
        val saver = CameraRequestState.Saver
        val saved = with(saver) { scope.save(original) }!!
        val restored = saver.restore(saved)!!
        assertEquals(original.pending, restored.pending)
        val terminal = restored.takePending()
        assertNotNull(terminal)
        assertNull(restored.takePending(), "A terminal request must not be delivered twice")
    }
    @Test fun emptyStateDoesNotInventARestoredCapture() {
        val saver = CameraRequestState.Saver
        val scope = object : SaverScope { override fun canBeSaved(value: Any) = true }
        val saved = with(saver) { scope.save(CameraRequestState()) }
        // Compose listSaver omits empty lists; rememberSaveable then uses its initializer.
        assertNull(saved, "No pending capture should need saved state")
        val restored = saved?.let(saver::restore) ?: CameraRequestState()
        assertNull(restored.pending)
        // Older/empty serialized state must not manufacture an operation either.
        assertNull(saver.restore(emptyList<String>())!!.pending)
    }
    @Test fun iosQualityBoundsRejectInvalidValues() {
        assertFailsWith<IllegalArgumentException> { CameraPickerOptions(iosJpegQuality = -0.01) }
        assertFailsWith<IllegalArgumentException> { CameraPickerOptions(iosJpegQuality = Double.NaN) }
        assertEquals(CameraImageFormat.Png, CameraPickerOptions().iosImageFormat)
    }
}
