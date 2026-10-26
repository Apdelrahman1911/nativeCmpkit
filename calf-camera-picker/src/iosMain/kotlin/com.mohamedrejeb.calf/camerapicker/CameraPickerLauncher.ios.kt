// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.camerapicker

import androidx.compose.runtime.*
import androidx.compose.ui.uikit.LocalUIViewController
import com.mohamedrejeb.calf.io.KmpFile
import kotlinx.coroutines.*
import platform.Foundation.*
import platform.UIKit.*
import platform.darwin.NSObject
import platform.darwin.dispatch_async
import platform.darwin.dispatch_get_main_queue

/** A stable owner survives callback recomposition and retains the complete active operation. */
internal class CameraPickerLauncherIosImpl(
    private val viewController: UIViewController,
    private val options: () -> CameraPickerOptions,
    private val onResult: (CameraPickerResult) -> Unit,
) : CameraPickerLauncher {
    private class Request(val options: CameraPickerOptions) {
        var picker: UIImagePickerController? = null
        var delegate: NSObject? = null
        var job: Job? = null
        var path: String? = null
        var processing = false
    }
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private var active: Request? = null
    private var disposed = false

    override fun launch() = onCameraMain {
        if (disposed) return@onCameraMain
        if (active != null) { onResult(CameraPickerResult.Busy); return@onCameraMain }
        if (viewController.presentedViewController != null || viewController.view.window == null) {
            onResult(CameraPickerResult.Failed(CameraFailureReason.Launch, "Camera presenter is not available or already presenting"))
            return@onCameraMain
        }
        val currentOptions = options()
        val source = when {
            UIImagePickerController.isSourceTypeAvailable(UIImagePickerControllerSourceType.UIImagePickerControllerSourceTypeCamera) ->
                UIImagePickerControllerSourceType.UIImagePickerControllerSourceTypeCamera
            currentOptions.iosPhotoLibraryFallback && UIImagePickerController.isSourceTypeAvailable(UIImagePickerControllerSourceType.UIImagePickerControllerSourceTypePhotoLibrary) ->
                UIImagePickerControllerSourceType.UIImagePickerControllerSourceTypePhotoLibrary
            else -> { onResult(CameraPickerResult.Unavailable("No camera or allowed photo-library fallback is available")); return@onCameraMain }
        }
        val privacyKey = if (source == UIImagePickerControllerSourceType.UIImagePickerControllerSourceTypeCamera)
            "NSCameraUsageDescription" else "NSPhotoLibraryUsageDescription"
        if ((NSBundle.mainBundle.objectForInfoDictionaryKey(privacyKey) as? String).isNullOrBlank()) {
            onResult(CameraPickerResult.Failed(CameraFailureReason.Configuration, "The host must provide $privacyKey"))
            return@onCameraMain
        }
        // UIKit construction, delegate assignment and presentation all happen on Main, not only present().
        val request = Request(currentOptions)
        val picker = UIImagePickerController().apply { sourceType = source; allowsEditing = false }
        val delegate = object : NSObject(), UIImagePickerControllerDelegateProtocol, UINavigationControllerDelegateProtocol {
            override fun imagePickerController(picker: UIImagePickerController, didFinishPickingMediaWithInfo: Map<Any?, Any?>) {
                if (active !== request || request.processing) return
                val image = didFinishPickingMediaWithInfo[UIImagePickerControllerOriginalImage] as? UIImage
                if (image == null) { finish(request, CameraPickerResult.Failed(CameraFailureReason.Io, "Camera returned no original image")); return }
                request.processing = true
                // Dismiss before expensive encoding; retain the UIImage, not a live camera UI, in the job.
                picker.delegate = null
                picker.dismissViewControllerAnimated(true) {
                    request.picker = null
                    request.delegate = null
                    if (disposed || active !== request) return@dismissViewControllerAnimated
                    encodeImage(request, image)
                }
            }
            override fun imagePickerControllerDidCancel(picker: UIImagePickerController) {
                if (active === request && !request.processing) finish(request, CameraPickerResult.Cancelled)
            }
        }
        request.picker = picker
        request.delegate = delegate
        picker.delegate = delegate
        active = request
        viewController.presentViewController(picker, true, null)
    }

    private fun encodeImage(request: Request, image: UIImage) {
        val suffix = if (request.options.iosImageFormat == CameraImageFormat.Png) ".png" else ".jpg"
        val path = NSTemporaryDirectory() + "nativecmpkit-camera-" + NSUUID().UUIDString + suffix
        request.path = path
        request.job = scope.launch {
            var transferred = false
            try {
                val written = withContext(Dispatchers.Default) {
                    val data = when (request.options.iosImageFormat) {
                        CameraImageFormat.Png -> UIImagePNGRepresentation(image)
                        CameraImageFormat.Jpeg -> UIImageJPEGRepresentation(image, request.options.iosJpegQuality)
                    }
                    data?.writeToFile(path, true) == true
                }
                if (!disposed && active === request) {
                    if (written) {
                        transferred = true
                        finish(request, CameraPickerResult.Captured(KmpFile(NSURL.fileURLWithPath(path))))
                    } else finish(request, CameraPickerResult.Failed(CameraFailureReason.Io, "Could not encode/write the captured image"))
                }
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (error: Exception) {
                if (!disposed && active === request) finish(request, CameraPickerResult.Failed(CameraFailureReason.Io, error.message ?: "Image encoding failed"))
                else throw error // An application callback exception is not an encoding failure.
            } finally {
                // Path is known before dispatch. Even cancellation while writeToFile is running
                // eventually removes the output after the worker returns (no escaped orphan file).
                if (!transferred) deleteTemporary(path)
            }
        }
    }

    private fun finish(request: Request, result: CameraPickerResult) {
        if (active !== request || disposed) return
        val complete = {
            if (active === request && !disposed) {
                active = null
                request.picker?.delegate = null
                request.picker = null
                request.delegate = null
                if (result !is CameraPickerResult.Captured) request.path?.let(::deleteTemporary)
                request.path = null // Successful output belongs to the caller, not the next request.
                onResult(result) // All internal ownership was cleared before invoking application code.
            }
        }
        val picker = request.picker
        if (picker?.presentingViewController != null) picker.dismissViewControllerAnimated(true) { complete() }
        else complete()
    }

    fun dispose() = onCameraMain {
        if (disposed) return@onCameraMain
        disposed = true
        val request = active
        active = null
        request?.picker?.delegate = null
        request?.picker?.dismissViewControllerAnimated(false, null)
        request?.delegate = null
        request?.picker = null
        request?.job?.cancel()
        request?.path?.let(::deleteTemporary)
        scope.cancel()
    }
}

private fun deleteTemporary(path: String) {
    if (path.startsWith(NSTemporaryDirectory() + "nativecmpkit-camera-")) {
        NSFileManager.defaultManager.removeItemAtPath(path, null)
    }
}
private fun onCameraMain(action: () -> Unit) {
    if (NSThread.isMainThread) action() else dispatch_async(dispatch_get_main_queue()) { action() }
}

@Composable
actual fun rememberCameraPickerLauncher(onResult: (KmpFile) -> Unit): CameraPickerLauncher =
    rememberCameraPickerResultLauncher { if (it is CameraPickerResult.Captured) onResult(it.file) }

@Composable
actual fun rememberCameraPickerResultLauncher(options: CameraPickerOptions, onResult: (CameraPickerResult) -> Unit): CameraPickerLauncher {
    val viewController = LocalUIViewController.current
    val currentResult by rememberUpdatedState(onResult)
    val currentOptions by rememberUpdatedState(options)
    val owner = remember(viewController) { CameraPickerLauncherIosImpl(viewController, { currentOptions }, { currentResult(it) }) }
    DisposableEffect(owner) { onDispose { owner.dispose() } }
    return owner
}
