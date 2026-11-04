// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.camerapicker

import androidx.compose.runtime.Composable
import com.mohamedrejeb.calf.io.KmpFile


interface CameraPickerLauncher {
    fun launch()
}

/**
 * Legacy success-only adapter. For cancellation/unavailable/errors use
 * [rememberCameraPickerResultLauncher]. Successful cache files belong to the caller; copy them
 * for persistence and delete them when finished. The library deletes only failed/cancelled output.
 */
@Composable
expect fun rememberCameraPickerLauncher(
    onResult: (KmpFile) -> Unit,
): CameraPickerLauncher


