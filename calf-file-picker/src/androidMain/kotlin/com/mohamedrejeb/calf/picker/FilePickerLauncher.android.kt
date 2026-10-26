// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.picker

import android.content.ActivityNotFoundException
import android.net.Uri
import android.os.Build
import android.provider.MediaStore
import android.webkit.MimeTypeMap
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Stable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.saveable.Saver
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.platform.LocalContext
import com.mohamedrejeb.calf.core.InternalCalfApi
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.io.initializeKmpFileContext
import java.util.Locale

@Composable
actual fun rememberFilePickerLauncher(
    type: FilePickerFileType,
    selectionMode: FilePickerSelectionMode,
    settings: FilePickerSettings,
    onResult: (List<KmpFile>) -> Unit,
): FilePickerLauncher = rememberFilePickerLauncher(type, selectionMode, settings, { onResult(emptyList()) }, onResult)

@OptIn(InternalCalfApi::class)
@Composable
actual fun rememberFilePickerLauncher(
    type: FilePickerFileType,
    selectionMode: FilePickerSelectionMode,
    settings: FilePickerSettings,
    onError: (FilePickerException) -> Unit,
    onResult: (List<KmpFile>) -> Unit,
): FilePickerLauncher {
    initializeKmpFileContext(LocalContext.current.applicationContext)
    val currentType by rememberUpdatedState(type)
    val currentMode by rememberUpdatedState(selectionMode)
    val currentSettings by rememberUpdatedState(settings)
    val currentOnResult by rememberUpdatedState(onResult)
    val currentOnError by rememberUpdatedState(onError)
    val pending = rememberSaveable(saver = PendingPickRequest.Saver) { PendingPickRequest() }
    val receive: (List<Uri>) -> Unit = { uris ->
        val request = pending.consume()
        if (request != null) {
            val result = (request.limit?.let { uris.take(it) } ?: uris).map(::KmpFile)
            currentOnResult(result)
        }
    }
    // Register stable launchers outside mode/type branches: recomposition cannot remove an
    // in-flight ActivityResult registration. All callbacks use its saved launch-time limit.
    val singleDocument = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { receive(listOfNotNull(it)) }
    val multipleDocuments = rememberLauncherForActivityResult(ActivityResultContracts.OpenMultipleDocuments(), receive)
    val folder = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocumentTree()) { receive(listOfNotNull(it)) }
    val singleMedia = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { receive(listOfNotNull(it)) }
    val nativeLimit = androidPhotoPickerLimit((selectionMode as? FilePickerSelectionMode.Multiple)?.maxItems)
    val multipleMedia = rememberLauncherForActivityResult(ActivityResultContracts.PickMultipleVisualMedia(nativeLimit), receive)

    return remember {
        FilePickerLauncher(type, selectionMode) launch@{
            val launchType = currentType
            val launchMode = currentMode
            var accepted = false
            val failure = try {
                pending.begin(launchMode)
                accepted = true
                val single = launchMode.resultLimit() == 1
                when {
                    launchType == FilePickerFileType.Folder -> folder.launch(currentSettings.initialDirectory?.let(Uri::parse))
                    launchType.isVisualMedia() -> {
                        try {
                            if (single) singleMedia.launch(launchType.toPickVisualMediaRequest())
                            else multipleMedia.launch(launchType.toPickVisualMediaRequest())
                        } catch (_: ActivityNotFoundException) {
                            if (single) singleDocument.launch(launchType.toVisualMediaMimeTypes())
                            else multipleDocuments.launch(launchType.toVisualMediaMimeTypes())
                        }
                    }
                    single -> singleDocument.launch(launchType.toMimeTypes())
                    else -> multipleDocuments.launch(launchType.toMimeTypes())
                }
                null
            } catch (error: Exception) {
                if (accepted) pending.consume()
                FilePickerException("Could not open the file picker", error)
            }
            if (failure != null) currentOnError(failure)
        }
    }
}

internal fun androidPhotoPickerLimit(requested: Int?): Int {
    val platformMaximum = if (Build.VERSION.SDK_INT >= 33) MediaStore.getPickImagesMaxLimit() else Int.MAX_VALUE
    // The multiple contract requires >=2; a requested count of one uses the single contract.
    return (requested ?: platformMaximum).coerceIn(2, platformMaximum.coerceAtLeast(2))
}

internal class PendingPickRequest {
    private var current: Request? = null
    fun begin(mode: FilePickerSelectionMode) {
        check(current == null) { "A picker is already open" }
        current = Request(mode.resultLimit())
    }
    fun consume(): Request? = current.also { current = null }
    class Request(val limit: Int?)
    companion object {
        val Saver: Saver<PendingPickRequest, List<Int>> = Saver(
            save = { listOf(if (it.current == null) 0 else 1, it.current?.limit ?: 0) },
            restore = { saved -> PendingPickRequest().apply { if (saved[0] == 1) current = Request(saved[1].takeIf { it > 0 }) } },
        )
    }
}

/**
 * Additional MIME type mappings for extensions where [MimeTypeMap] may
 * return only one variant, causing files to be missing in the picker.
 */
private val extensionMimeTypeFallbacks = mapOf(
    "csv" to listOf("text/csv", "text/comma-separated-values", "application/csv"),
)

/**
 * Resolves MIME types for a [FilePickerFileType], handling extensions that need
 * multiple MIME type variants to work reliably across devices.
 */
internal fun FilePickerFileType.toMimeTypes(): Array<String> {
    if (this is FilePickerFileType.Extension) {
        val mimeTypeMap = MimeTypeMap.getSingleton()
        return value.flatMap { ext ->
            val lowerExt = ext.lowercase(Locale.ROOT)
            val fallbacks = extensionMimeTypeFallbacks[lowerExt]
            if (fallbacks != null) {
                // Use known fallbacks + system mapping (deduplicated)
                val systemType = mimeTypeMap.getMimeTypeFromExtension(lowerExt)
                (fallbacks + listOfNotNull(systemType)).distinct()
            } else {
                listOfNotNull(mimeTypeMap.getMimeTypeFromExtension(lowerExt))
            }
        }.toTypedArray()
    }
    return value.toList().toTypedArray()
}

internal fun FilePickerFileType.toVisualMediaMimeTypes(): Array<String> {
    return when (this) {
        FilePickerFileType.Image -> arrayOf(FilePickerFileType.ImageContentType)
        FilePickerFileType.Video -> arrayOf(FilePickerFileType.VideoContentType)
        else -> arrayOf(FilePickerFileType.ImageContentType, FilePickerFileType.VideoContentType)
    }
}

internal fun FilePickerFileType.toPickVisualMediaRequest(): PickVisualMediaRequest {
    return when (this) {
        FilePickerFileType.Image -> PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)
        FilePickerFileType.Video -> PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.VideoOnly)
        else -> PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageAndVideo)
    }
}

internal fun FilePickerFileType.isVisualMedia(): Boolean {
    return when (this) {
        FilePickerFileType.Image -> true
        FilePickerFileType.Video -> true
        FilePickerFileType.ImageVideo -> true
        else -> false
    }
}

@Stable
actual class FilePickerLauncher actual constructor(
    type: FilePickerFileType,
    selectionMode: FilePickerSelectionMode,
    private val onLaunch: () -> Unit,
) {
    actual fun launch() {
        onLaunch()
    }
}
