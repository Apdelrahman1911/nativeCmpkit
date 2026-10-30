// SPDX-License-Identifier: Apache-2.0
@file:Suppress("DEPRECATION")
package com.mohamedrejeb.calf.camerapicker

import android.content.res.Configuration
import android.os.Bundle
import android.os.Process
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.LaunchedEffect
import java.util.Locale

/**
 * Genuine public consumer in a different process from the instrumentation reporter.
 * No ActivityResultRegistry adapter or manual URI grant/state restoration. Android
 * saves/recreates the Activity and the library's own rememberSaveable request.
 */
class CameraRestorationVerificationActivity : ComponentActivity() {
    private lateinit var nonce: String
    private val preferences get() = getSharedPreferences("nativecmpkit-camera-restoration-$nonce", 0)

    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        nonce = checkNotNull(intent.getStringExtra("nativecmpkit.nonce"))
        check(nonce.matches(Regex("[a-f0-9]{32}")))
        preferences.edit().putString("nonce", nonce).putInt("pid", Process.myPid())
            .putInt("uid", Process.myUid()).putInt("task", taskId)
            .putInt("creates", preferences.getInt("creates", 0) + 1)
            .putInt("orientation", resources.configuration.orientation).commit().also { check(it) }
        setContent {
            val launcher = rememberCameraPickerResultLauncher(
                CameraPickerOptions(androidFileProviderAuthority = "$packageName.camera-files"),
            ) { outcome ->
                val kind = when (outcome) {
                    is CameraPickerResult.Captured -> "captured"
                    CameraPickerResult.Cancelled -> "cancelled"
                    is CameraPickerResult.Failed -> "failed-${outcome.reason.name.lowercase(Locale.ROOT)}"
                    CameraPickerResult.Busy -> "busy"
                    is CameraPickerResult.Unavailable -> "unavailable"
                }
                preferences.edit().putInt("results", preferences.getInt("results", 0) + 1)
                    .putString("kind", kind)
                    .putString("uri", (outcome as? CameraPickerResult.Captured)?.file?.uri?.toString() ?: "")
                    .commit().also { check(it) }
                // A terminal callback owns no extra external request. Keep the source
                // result file caller-owned; the reporter reads/closes it independently.
                finishAndRemoveTask()
            }
            LaunchedEffect(Unit) {
                if (state == null) {
                    preferences.edit().putInt("launches", preferences.getInt("launches", 0) + 1)
                        .commit().also { check(it) }
                    launcher.launch()
                }
            }
        }
    }

    override fun onSaveInstanceState(state: Bundle) {
        super.onSaveInstanceState(state) // Real ComponentActivity / Compose / registry state.
        preferences.edit().putInt("saves", preferences.getInt("saves", 0) + 1).commit().also { check(it) }
    }

    override fun onStop() {
        super.onStop()
        preferences.edit().putInt("stops", preferences.getInt("stops", 0) + 1).commit().also { check(it) }
    }

    override fun onDestroy() {
        preferences.edit().putInt("destroys", preferences.getInt("destroys", 0) + 1)
            .putBoolean("configurationDestroyed", isChangingConfigurations)
            .putBoolean("nonFinishingDestroyed", !isFinishing).commit().also { check(it) }
        super.onDestroy()
    }
}
