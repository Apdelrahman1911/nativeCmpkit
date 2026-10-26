// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.camerapicker

import androidx.compose.runtime.*
import com.mohamedrejeb.calf.io.KmpFile

@Composable
actual fun rememberCameraPickerLauncher(onResult: (KmpFile) -> Unit): CameraPickerLauncher =
    rememberCameraPickerResultLauncher { if (it is CameraPickerResult.Captured) onResult(it.file) }

@Composable
actual fun rememberCameraPickerResultLauncher(options: CameraPickerOptions, onResult: (CameraPickerResult) -> Unit): CameraPickerLauncher {
    val currentResult by rememberUpdatedState(onResult)
    return remember {
        object : CameraPickerLauncher {
            override fun launch() { currentResult(CameraPickerResult.Unavailable("Desktop camera capture is not implemented")) }
        }
    }
}
