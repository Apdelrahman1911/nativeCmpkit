// SPDX-License-Identifier: Apache-2.0
@file:Suppress("DEPRECATION")
package com.mohamedrejeb.calf.camerapicker

import android.content.ComponentName
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.os.Process
import android.provider.MediaStore
import android.view.ViewTreeObserver
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.DisposableEffect
import androidx.lifecycle.Lifecycle
import java.io.File
import java.util.Locale

/**
 * Genuine public consumer in a different process from the instrumentation reporter.
 * No ActivityResultRegistry adapter or manual URI grant/state restoration. Android
 * saves/recreates the Activity and the library's own rememberSaveable request.
 * Only the external recipient selection is redirected at the real Activity launch
 * boundary: Android15 restricts unqualified implicit camera intents to system apps.
 */
class CameraRestorationVerificationActivity : ComponentActivity() {
    private lateinit var nonce: String
    private val preferences get() = getSharedPreferences("nativecmpkit-camera-restoration-$nonce", 0)
    private var restored = false
    private var launched = false
    private var firstDraw = false
    private var activeLauncher: CameraPickerLauncher? = null
    private var drawObserver: ViewTreeObserver? = null
    private lateinit var drawListener: ViewTreeObserver.OnDrawListener

    private fun launchWhenForeground() {
        val current = activeLauncher ?: return
        if (restored || launched || !firstDraw || !hasWindowFocus() || lifecycle.currentState != Lifecycle.State.RESUMED) return
        // A background reporter and an initial Compose effect do not establish a
        // foreground/saved caller. Use actual native resume/focus/first draw, then
        // the genuine public launcher on the main thread. A restored owner waits
        // for its real registry result and must never create a second request.
        check(preferences.getInt("launches", 0) == 0)
        launched = true
        preferences.edit().putInt("launches", 1).putBoolean("foregroundLaunch", true)
            .commit().also { check(it) }
        current.launch()
    }

    override fun startActivityForResult(intent: Intent, requestCode: Int, options: Bundle?) {
        // Validate the genuine TakePicture contract before selecting the one owned
        // recipient. Keep ComponentActivity's saved registry, request code/options
        // and Android's EXTRA_OUTPUT grant migration/result delivery untouched.
        check(intent.action == MediaStore.ACTION_IMAGE_CAPTURE && intent.component == null)
        check(intent.`package` == null && intent.selector == null)
        check(intent.data == null && intent.type == null && intent.categories == null)
        check(intent.clipData == null && intent.flags == 0 && requestCode > 0)
        val uri = checkNotNull(intent.getParcelableExtra<Uri>(MediaStore.EXTRA_OUTPUT))
        check(uri.scheme == "content" && uri.authority == "$packageName.camera-files")
        check(uri.pathSegments.size == 2 && uri.pathSegments[0] == "camera")
        val name = uri.pathSegments[1]
        check(name.matches(Regex("capture-[A-Za-z0-9._-]+\\.jpg")) && ".." !in name)
        val directory = File(cacheDir, "nativecmpkit-camera").canonicalFile
        val file = File(directory, name)
        check(file.canonicalFile == file && file.parentFile == directory && file.isFile && file.length() == 0L)
        val recipient = ComponentName(OwnedCameraReceiver.PACKAGE,
            "${OwnedCameraReceiver.PACKAGE}.CameraDelayedReceiverActivity")
        val info = packageManager.getActivityInfo(recipient, 0)
        check(ComponentName(info.packageName, info.name) == recipient && info.exported)
        check(info.applicationInfo.uid != Process.myUid() && info.permission == OwnedCameraReceiver.PERMISSION)
        check(packageManager.checkSignatures(packageName, recipient.packageName) == PackageManager.SIGNATURE_MATCH)
        check(checkSelfPermission(OwnedCameraReceiver.PERMISSION) == PackageManager.PERMISSION_GRANTED)
        check(packageManager.getComponentEnabledSetting(recipient) == PackageManager.COMPONENT_ENABLED_STATE_ENABLED)
        check(preferences.getInt("externalLaunches", 0) == 0)
        preferences.edit().putInt("externalLaunches", 1).putInt("selectionUid", info.applicationInfo.uid)
            .putInt("selectionRequestCode", requestCode).commit().also { check(it) }
        super.startActivityForResult(Intent(intent).setComponent(recipient), requestCode, options)
    }

    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        restored = state != null
        nonce = checkNotNull(intent.getStringExtra("nativecmpkit.nonce"))
        check(nonce.matches(Regex("[a-f0-9]{32}")))
        preferences.edit().putString("nonce", nonce).putInt("pid", Process.myPid())
            .putInt("uid", Process.myUid()).putInt("task", taskId)
            .putInt("creates", preferences.getInt("creates", 0) + 1)
            .putInt("orientation", resources.configuration.orientation).commit().also { check(it) }
        if (!restored) {
            val decor = window.decorView
            val observer = decor.viewTreeObserver
            drawListener = ViewTreeObserver.OnDrawListener {
                if (!firstDraw) {
                    firstDraw = true
                    preferences.edit().putInt("draws", preferences.getInt("draws", 0) + 1)
                        .commit().also { check(it) }
                    // Never launch/reenter Activity during the native draw callback.
                    check(decor.post { launchWhenForeground() })
                }
            }
            drawObserver = observer
            observer.addOnDrawListener(drawListener)
        }
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
            DisposableEffect(launcher) {
                activeLauncher = launcher
                launchWhenForeground()
                onDispose { if (activeLauncher === launcher) activeLauncher = null }
            }
        }
    }

    override fun onSaveInstanceState(state: Bundle) {
        super.onSaveInstanceState(state) // Real ComponentActivity / Compose / registry state.
        preferences.edit().putInt("saves", preferences.getInt("saves", 0) + 1).commit().also { check(it) }
    }

    override fun onPostResume() {
        super.onPostResume()
        preferences.edit().putInt("resumes", preferences.getInt("resumes", 0) + 1).commit().also { check(it) }
        launchWhenForeground()
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (::nonce.isInitialized) {
            preferences.edit().putBoolean("windowFocused", hasFocus).commit().also { check(it) }
            launchWhenForeground()
        }
    }

    override fun onStop() {
        super.onStop()
        preferences.edit().putInt("stops", preferences.getInt("stops", 0) + 1).commit().also { check(it) }
    }

    override fun onDestroy() {
        drawObserver?.takeIf { it.isAlive }?.removeOnDrawListener(drawListener)
        drawObserver = null
        preferences.edit().putInt("destroys", preferences.getInt("destroys", 0) + 1)
            .putBoolean("configurationDestroyed", isChangingConfigurations)
            .putBoolean("nonFinishingDestroyed", !isFinishing).commit().also { check(it) }
        super.onDestroy()
    }
}
