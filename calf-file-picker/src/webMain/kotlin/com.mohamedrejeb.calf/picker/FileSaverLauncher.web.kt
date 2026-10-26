// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
// Save-API support/deferred revocation derived from MohamedRejeb/Calf PR #551, with explicit events/ownership.
package com.mohamedrejeb.calf.picker

import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.Stable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import com.mohamedrejeb.calf.core.ExperimentalCalfApi
import com.mohamedrejeb.calf.io.KmpFile
import kotlinx.browser.document
import kotlinx.browser.window
import org.w3c.files.File
import org.w3c.dom.HTMLAnchorElement
import org.w3c.dom.url.URL
import org.w3c.files.Blob

internal expect fun createBlob(bytes: ByteArray, mimeType: String): Blob
internal expect fun isSaveFilePickerSupported(): Boolean
internal expect class BrowserSaveOperation { fun cancel() }
internal expect fun showSaveFilePicker(
    blob: Blob, suggestedName: String, mimeType: String, extension: String,
    onSaved: (File) -> Unit, onCancelled: () -> Unit, onPickerFailed: () -> Unit, onWriteFailed: () -> Unit,
): BrowserSaveOperation

/** Deferred bounded retention, not proof of download completion (especially on Safari/iOS). */
internal const val OBJECT_URL_REVOKE_DELAY_MS = 40_000
private const val MAX_PENDING_DOWNLOADS = 32
private val pendingDownloadUrls = mutableSetOf<String>()

actual fun fileSaverCapability(): FileSaverCapability =
    if (isSaveFilePickerSupported()) FileSaverCapability.SaveDestination else FileSaverCapability.DownloadOnly

@ExperimentalCalfApi
@Composable
actual fun rememberFileSaverLauncher(settings: FilePickerSettings, onResult: (KmpFile?) -> Unit): FileSaverLauncher =
    rememberFileSaverLauncher(settings, { onResult(null) }, onResult)

/** Legacy callbacks cannot express DownloadStarted. Prefer rememberFileSaverEventLauncher on web. */
@ExperimentalCalfApi
@Composable
actual fun rememberFileSaverLauncher(
    settings: FilePickerSettings,
    onError: (FilePickerException) -> Unit,
    onResult: (KmpFile?) -> Unit,
): FileSaverLauncher = rememberFileSaverEventLauncher(settings) { event ->
    when (event) {
        is FileSaverEvent.Saved -> onResult(event.file)
        FileSaverEvent.Cancelled -> onResult(null)
        is FileSaverEvent.Failed -> onError(event.error)
        is FileSaverEvent.DownloadStarted -> Unit // Historical API has no truthful destination result.
    }
}

@ExperimentalCalfApi
@Composable
actual fun rememberFileSaverEventLauncher(
    settings: FilePickerSettings,
    onEvent: (FileSaverEvent) -> Unit,
): FileSaverLauncher {
    val currentOnEvent by rememberUpdatedState(onEvent)
    val owner = remember { BrowserSaveOwner() }
    DisposableEffect(owner) { onDispose { owner.close() } }
    val save: (() -> Blob, String, String) -> Unit = launch@{ content, baseName, extension ->
        if (owner.disposed) return@launch
        if (owner.pending) {
            currentOnEvent(FileSaverEvent.Failed(FilePickerException("A browser save is already pending")))
            return@launch
        }
        val token = owner.begin()
        fun complete(event: FileSaverEvent) { if (owner.complete(token)) currentOnEvent(event) }
        val prepared = try { Result.success(suggestedFileName(baseName, extension) to content()) }
            catch (failure: Exception) { Result.failure(failure) }
        val preparationFailure = prepared.exceptionOrNull()
        if (preparationFailure != null) {
            complete(FileSaverEvent.Failed(FilePickerException("Could not prepare the browser save", preparationFailure)))
            return@launch
        }
        val (name, blob) = prepared.getOrThrow()
        if (isSaveFilePickerSupported()) {
            val failure = try {
                owner.operation = showSaveFilePicker(blob, name, extensionToMimeType(extension), extension,
                    onSaved = { complete(FileSaverEvent.Saved(KmpFile(it))) },
                    onCancelled = { complete(FileSaverEvent.Cancelled) },
                    onPickerFailed = { complete(FileSaverEvent.Failed(FilePickerException("Browser refused the save dialog; check user activation and permission"))) },
                    onWriteFailed = { complete(FileSaverEvent.Failed(FilePickerException("Browser could not write the selected file"))) },
                )
                null
            } catch (error: Exception) { error }
            if (failure != null) complete(FileSaverEvent.Failed(FilePickerException("Could not open the browser save dialog", failure)))
        } else {
            val failure = try { triggerDownload(blob, name); null } catch (error: Exception) { error }
            complete(if (failure == null) FileSaverEvent.DownloadStarted(name)
                else FileSaverEvent.Failed(FilePickerException("Could not request the download", failure)))
        }
    }
    return remember(owner) {
        FileSaverLauncher(
            onLaunch = { bytes, name, extension, _ -> save({ createBlob(bytes ?: byteArrayOf(), extensionToMimeType(extension)) }, name, extension) },
            onLaunchFile = { file, name, extension, _ -> save({ file.file }, name, extension) },
            onLaunchBlob = { blob, name, extension, _ -> save({ blob }, name, extension) },
        )
    }
}

internal class BrowserSaveOwner {
    var disposed = false
        private set
    var pending = false
        private set
    private var token = 0
    var operation: BrowserSaveOperation? = null
    fun begin(): Int { check(!disposed && !pending); pending = true; return ++token }
    fun complete(generation: Int): Boolean {
        if (disposed || !pending || generation != token) return false
        pending = false; operation = null
        return true
    }
    fun close() { disposed = true; pending = false; operation?.cancel(); operation = null }
}

internal fun triggerDownload(
    blob: Blob,
    fileName: String,
    schedule: (() -> Unit) -> Unit = { callback -> window.setTimeout({ callback(); null }, OBJECT_URL_REVOKE_DELAY_MS); Unit },
    click: (HTMLAnchorElement) -> Unit = { it.click() },
) {
    check(pendingDownloadUrls.size < MAX_PENDING_DOWNLOADS) { "Too many pending downloads; wait for Blob URL cleanup" }
    val url = URL.createObjectURL(blob)
    pendingDownloadUrls += url
    fun release() { if (pendingDownloadUrls.remove(url)) URL.revokeObjectURL(url) }
    var anchor: HTMLAnchorElement? = null
    var started = false
    try {
        anchor = document.createElement("a") as HTMLAnchorElement
        anchor.href = url
        anchor.download = fileName
        anchor.style.display = "none"
        val body = document.body ?: error("The browser document has no body")
        body.appendChild(anchor)
        schedule { release() }
        click(anchor)
        started = true
    } finally {
        anchor?.remove()
        if (!started) release()
    }
}

internal fun extensionToMimeType(extension: String): String {
    return when (extension.lowercase()) {
        "pdf" -> "application/pdf"
        "txt" -> "text/plain"
        "csv" -> "text/csv"
        "json" -> "application/json"
        "xml" -> "application/xml"
        "html", "htm" -> "text/html"
        "png" -> "image/png"
        "jpg", "jpeg" -> "image/jpeg"
        "gif" -> "image/gif"
        "svg" -> "image/svg+xml"
        "webp" -> "image/webp"
        "heic" -> "image/heic"
        "heif" -> "image/heif"
        "avif" -> "image/avif"
        "mp3" -> "audio/mpeg"
        "mp4" -> "video/mp4"
        "zip" -> "application/zip"
        "doc" -> "application/msword"
        "docx" -> "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        "xls" -> "application/vnd.ms-excel"
        "xlsx" -> "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else -> "application/octet-stream"
    }
}

@ExperimentalCalfApi
@Stable
actual class FileSaverLauncher(
    private val onLaunch: (
        bytes: ByteArray?,
        baseName: String,
        extension: String,
        initialDirectory: String?,
    ) -> Unit,
    private val onLaunchFile: (
        file: KmpFile,
        baseName: String,
        extension: String,
        initialDirectory: String?,
    ) -> Unit,
    private val onLaunchBlob: (
        blob: Blob,
        baseName: String,
        extension: String,
        initialDirectory: String?,
    ) -> Unit,
) {
    actual fun launch(
        bytes: ByteArray?,
        baseName: String,
        extension: String,
        initialDirectory: String?,
    ) {
        onLaunch(bytes, baseName, extension, initialDirectory)
    }

    actual fun launch(
        file: KmpFile,
        baseName: String,
        extension: String,
        initialDirectory: String?,
    ) {
        onLaunchFile(file, baseName, extension, initialDirectory)
    }

    /**
     * Saves a W3C [File]; see [rememberFileSaverLauncher] for when the browser shows a save dialog.
     *
     * @param file The source [org.w3c.files.File] to save.
     * @param baseName The suggested file name without extension (e.g. "document").
     * @param extension The file extension without dot (e.g. "pdf").
     * @param initialDirectory Ignored on web.
     */
    fun launch(
        file: File,
        baseName: String,
        extension: String,
        initialDirectory: String? = null,
    ) {
        launch(KmpFile(file), baseName, extension, initialDirectory)
    }

    /**
     * Saves a [Blob]; see [rememberFileSaverLauncher] for when the browser shows a save dialog.
     *
     * @param blob The source [Blob] to save.
     * @param baseName The suggested file name without extension (e.g. "document").
     * @param extension The file extension without dot (e.g. "pdf").
     * @param initialDirectory Ignored on web.
     */
    fun launch(
        blob: Blob,
        baseName: String,
        extension: String,
        initialDirectory: String? = null,
    ) {
        onLaunchBlob(blob, baseName, extension, initialDirectory)
    }
}
