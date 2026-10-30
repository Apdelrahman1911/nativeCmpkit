package com.mohamedrejeb.calf.camerapicker

import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.Saver
import androidx.compose.runtime.saveable.listSaver
import com.mohamedrejeb.calf.io.KmpFile

/** A separate contract preserves exhaustive callers of older APIs. */
sealed interface CameraPickerResult {
    /** App-owned cache output. Copy it for persistence; the OS may evict cache files. */
    data class Captured(val file: KmpFile) : CameraPickerResult
    data object Cancelled : CameraPickerResult
    data object Busy : CameraPickerResult
    data class Unavailable(val reason: String) : CameraPickerResult
    data class Failed(val reason: CameraFailureReason, val message: String) : CameraPickerResult
}

enum class CameraFailureReason { Configuration, Permission, Io, Launch }
enum class CameraImageFormat { Png, Jpeg }

/** Options are read for each new request; changing them never replaces an active owner. */
data class CameraPickerOptions(
    /** Android API23+: defaults to ${'$'}{applicationId}.provider; the host must configure a narrow FileProvider. */
    val androidFileProviderAuthority: String? = null,
    val iosPhotoLibraryFallback: Boolean = true,
    /** Android's external camera controls its own JPEG output. These options apply to iOS only. */
    val iosImageFormat: CameraImageFormat = CameraImageFormat.Png,
    val iosJpegQuality: Double = 0.9,
) {
    init { require(iosJpegQuality in 0.0..1.0) { "JPEG quality must be between 0 and 1" } }
}

/**
 * Reports capture, cancellation, unavailable, busy or failure. The latest callback handles an
 * in-flight result. Native work is marshalled to the main thread. Disposal abandons/cancels owned
 * work; Android non-finishing Activity destruction retains pending state for ActivityResult
 * restoration. Unregistering cannot stop an external camera: abandoned in-flight Android outputs
 * remain in app cache for later OS/host cleanup instead of being unlinked during writing.
 * Desktop and browser return Unavailable, never a silent successful no-op.
 */
@Composable
expect fun rememberCameraPickerResultLauncher(
    options: CameraPickerOptions = CameraPickerOptions(),
    onResult: (CameraPickerResult) -> Unit,
): CameraPickerLauncher

internal data class PendingCameraCapture(val uri: String, val ownedPath: String)

/** Saved before external launch, independent of the transient launcher/Activity instance. */
@Stable
internal class CameraRequestState(pending: PendingCameraCapture? = null) {
    var pending by mutableStateOf(pending)
    fun takePending(): PendingCameraCapture? = pending.also { pending = null }

    companion object {
        val Saver: Saver<CameraRequestState, Any> = listSaver(
            save = { it.pending?.let { request -> listOf(request.uri, request.ownedPath) } ?: emptyList() },
            restore = { values ->
                CameraRequestState(if (values.size == 2) PendingCameraCapture(values[0], values[1]) else null)
            },
        )
    }
}
