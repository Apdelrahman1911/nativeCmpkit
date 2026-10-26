// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.camerapicker

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Handler
import android.os.Looper
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.platform.LocalContext
import androidx.core.content.FileProvider
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleOwner
import com.mohamedrejeb.calf.io.KmpFile
import java.io.File
import java.io.IOException

@Stable
internal class CameraPickerLauncherAndroidImpl(
    private val context: Context,
    private val launcher: ActivityResultLauncher<Uri>,
    private val request: CameraRequestState,
    private val options: () -> CameraPickerOptions,
    private val onResult: (CameraPickerResult) -> Unit,
) : CameraPickerLauncher {
    private var disposed = false

    override fun launch() = onMain {
        if (disposed) return@onMain
        if (request.pending != null) { onResult(CameraPickerResult.Busy); return@onMain }
        if (!context.packageManager.hasSystemFeature(PackageManager.FEATURE_CAMERA_ANY)) {
            onResult(CameraPickerResult.Unavailable("This device has no camera"))
            return@onMain
        }
        var output: File? = null
        var launchedRequest: PendingCameraCapture? = null
        var launchEntered = false
        val failure = try {
            val directory = File(context.cacheDir, CAMERA_DIRECTORY)
            check(directory.isDirectory || directory.mkdirs()) { "Could not create camera cache directory" }
            output = File.createTempFile("capture-", ".jpg", directory)
            val uri = if (Build.VERSION.SDK_INT >= 24) FileProvider.getUriForFile(
                context, options().androidFileProviderAuthority ?: "${context.packageName}.provider", output,
            ) else Uri.fromFile(output)
            launchedRequest = PendingCameraCapture(uri.toString(), output.absolutePath)
            request.pending = launchedRequest
            launchEntered = true
            launcher.launch(uri)
            null
        } catch (error: Exception) {
            // A synchronous registry callback can finish A, launch B and then throw. In that case
            // A no longer owns the pending slot or its successfully delivered file. Do not clear
            // B, delete A's output, or classify an application failure as a second camera result.
            if (launchEntered && request.pending !== launchedRequest) throw error
            if (request.pending === launchedRequest) request.takePending()
            output?.let { deleteOwnedFile(it.absolutePath) }
            val reason = when (error) {
                is SecurityException -> CameraFailureReason.Permission
                is IOException -> CameraFailureReason.Io
                is IllegalArgumentException -> CameraFailureReason.Configuration
                else -> CameraFailureReason.Launch
            }
            CameraPickerResult.Failed(reason, error.message ?: "Unable to launch camera")
        }
        if (failure != null) onResult(failure) // outside platform exception handling
    }

    fun handleResult(success: Boolean) = onMain {
        if (disposed) return@onMain
        val pending = request.takePending() ?: return@onMain // duplicates/stale registry results
        val file = ownedFile(pending.ownedPath)
        val result = when {
            !success -> { deleteOwnedFile(pending.ownedPath); CameraPickerResult.Cancelled }
            file == null || !file.isFile || file.length() == 0L -> {
                deleteOwnedFile(pending.ownedPath)
                CameraPickerResult.Failed(CameraFailureReason.Io, "The camera did not produce a readable non-empty output")
            }
            else -> CameraPickerResult.Captured(KmpFile(Uri.parse(pending.uri)))
        }
        onResult(result) // pending state is cleared before a reentrant/throwing callback
    }

    fun dispose(retainPendingForSuccessor: Boolean) = onMain {
        if (disposed) return@onMain
        disposed = true
        if (!retainPendingForSuccessor) request.takePending()
        // Unregistering an ActivityResult callback does not cancel an external camera, revoke its
        // open descriptor, or prove it has finished writing. Never unlink an in-flight output here.
        // A restored owner receives the terminal result; an abandoned output stays in app cache
        // for OS/host cleanup when no camera is active. Known cancellation/launch failures above
        // can clean their own output, and successful results become caller-owned.
    }

    private fun ownedFile(path: String): File? = try {
        val file = File(path).canonicalFile
        val directory = File(context.cacheDir, CAMERA_DIRECTORY).canonicalFile
        file.takeIf { it.parentFile == directory && it.name.startsWith("capture-") && it.name.endsWith(".jpg") }
    } catch (_: IOException) { null }

    private fun deleteOwnedFile(path: String) { ownedFile(path)?.delete() }
}

private const val CAMERA_DIRECTORY = "nativecmpkit-camera"
private fun onMain(action: () -> Unit) {
    if (Looper.myLooper() == Looper.getMainLooper()) action() else Handler(Looper.getMainLooper()).post(action)
}
private fun Context.activity(): Activity? = when (this) {
    is Activity -> this
    is ContextWrapper -> baseContext.takeUnless { it === this }?.activity()
    else -> null
}

/** Use the Activity's lifecycle, not a navigation entry's possibly-destroyed LifecycleOwner. */
internal fun Context.retainCameraRequestForActivityRestoration(): Boolean {
    val activity = activity() ?: return false
    if (activity.isFinishing) return false
    // Compose can dispose from the ON_DESTROY observer before Activity.isDestroyed is visible.
    // Non-finishing destruction also covers don't-keep-activities, not only configuration changes.
    return activity.isChangingConfigurations || activity.isDestroyed ||
        (activity as? LifecycleOwner)?.lifecycle?.currentState == Lifecycle.State.DESTROYED
}

@Composable
actual fun rememberCameraPickerLauncher(onResult: (KmpFile) -> Unit): CameraPickerLauncher =
    rememberCameraPickerResultLauncher { if (it is CameraPickerResult.Captured) onResult(it.file) }

@Composable
actual fun rememberCameraPickerResultLauncher(
    options: CameraPickerOptions,
    onResult: (CameraPickerResult) -> Unit,
): CameraPickerLauncher {
    val context = LocalContext.current
    val currentResult by rememberUpdatedState(onResult)
    val currentOptions by rememberUpdatedState(options)
    val request = rememberSaveable(saver = CameraRequestState.Saver) { CameraRequestState() }
    val owner = remember { mutableStateOf<CameraPickerLauncherAndroidImpl?>(null) }
    val registryLauncher = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { success ->
        owner.value?.handleResult(success)
    }
    val result = remember(context, registryLauncher, request) {
        CameraPickerLauncherAndroidImpl(context, registryLauncher, request, { currentOptions }, { currentResult(it) })
    }
    owner.value = result
    DisposableEffect(result) {
        onDispose {
            // A new LocalContext wrapper can replace this owner without replacing its saved
            // request or registry launcher. The successor, not the old owner, now owns that slot.
            val successorOwnsRequest = owner.value != null && owner.value !== result
            if (owner.value === result) owner.value = null
            result.dispose(successorOwnsRequest || context.retainCameraRequestForActivityRestoration())
        }
    }
    return result
}
