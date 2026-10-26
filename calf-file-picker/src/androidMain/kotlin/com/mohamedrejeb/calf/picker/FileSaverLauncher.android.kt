// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
// Safety/lifetime implementation adapted from MohamedRejeb/Calf PR #551.
package com.mohamedrejeb.calf.picker

import android.content.ContentResolver
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.DocumentsContract
import android.webkit.MimeTypeMap
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Stable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.platform.LocalContext
import com.mohamedrejeb.calf.core.ExperimentalCalfApi
import com.mohamedrejeb.calf.core.InternalCalfApi
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.io.initializeKmpFileContext
import java.io.File
import java.io.FileNotFoundException
import java.io.InputStream
import java.io.OutputStream
import java.util.Locale
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@ExperimentalCalfApi
@Composable
actual fun rememberFileSaverLauncher(settings: FilePickerSettings, onResult: (KmpFile?) -> Unit): FileSaverLauncher =
    rememberFileSaverLauncher(settings, { onResult(null) }, onResult)

/** URI payloads survive restoration; bytes are deliberately marked lost rather than saved in a Bundle. */
@OptIn(InternalCalfApi::class)
@ExperimentalCalfApi
@Composable
actual fun rememberFileSaverLauncher(
    settings: FilePickerSettings,
    onError: (FilePickerException) -> Unit,
    onResult: (KmpFile?) -> Unit,
): FileSaverLauncher {
    val scope = rememberCoroutineScope()
    val currentOnResult by rememberUpdatedState(onResult)
    val currentOnError by rememberUpdatedState(onError)
    val currentSettings by rememberUpdatedState(settings)
    val context = LocalContext.current.applicationContext
    initializeKmpFileContext(context)
    val resolver = context.contentResolver
    val pending = rememberSaveable(saver = PendingSaveSource.Saver) { PendingSaveSource() }
    val launcher = rememberLauncherForActivityResult(CreateSaveDocument()) { uri ->
        val request = pending.consume() ?: return@rememberLauncherForActivityResult
        if (uri == null) {
            pending.finish()
            currentOnResult(null)
        } else {
            // Enter the ownership finally immediately, even if disposal cancels before dispatch.
            scope.launch(start = CoroutineStart.UNDISPATCHED) {
                val failure = try {
                    resolver.writeSaveSource(request.source, uri)
                } finally {
                    pending.finish()
                }
                if (failure == null) currentOnResult(KmpFile(uri)) else currentOnError(failure)
            }
        }
    }
    val launchSave: (SaveSource, String, String, String?) -> Unit = launch@{ source, baseName, extension, directory ->
        if (!scope.isActive) return@launch
        var accepted = false
        val failure = try {
            val name = suggestedFileName(baseName, extension)
            pending.set(source)
            accepted = true
            launcher.launch(SaveDocumentInput(name, directory ?: currentSettings.initialDirectory))
            null
        } catch (cancelled: CancellationException) {
            if (accepted) pending.finish()
            throw cancelled
        } catch (error: Exception) {
            if (accepted) pending.finish()
            FilePickerException("Could not open the save dialog", error)
        }
        // User code is not inside the operation catch: it must never cause a second callback.
        if (failure != null) currentOnError(failure)
    }
    return remember {
        FileSaverLauncher(
            onLaunch = { bytes, name, extension, directory -> launchSave(SaveSource.Bytes(bytes ?: byteArrayOf()), name, extension, directory) },
            onLaunchFile = { file, name, extension, directory -> launchSave(SaveSource.File(file), name, extension, directory) },
        )
    }
}

internal suspend fun ContentResolver.writeSaveSource(source: SaveSource?, destination: Uri): FilePickerException? {
    // A provider returning the original must never cause us to truncate or delete it.
    var sameSource = source is SaveSource.File && source.file.uri == destination
    var identityChecked = source !is SaveSource.File
    var completed = false
    return try {
        withContext(Dispatchers.IO) {
            currentCoroutineContext().ensureActive()
            if (source == null) throw FileNotFoundException("The pending save content was lost during app restoration")
            if (source is SaveSource.File) {
                sameSource = saveUrisReferToSameFile(source.file.uri, destination)
                identityChecked = true
            }
            when (source) {
                is SaveSource.Bytes -> {
                    val output = openOutputStream(destination, "wt") ?: throw FileNotFoundException("Provider returned no output stream")
                    output.use { source.bytes.inputStream().use { input -> copySaveContent(input, it) } }
                }
                is SaveSource.File -> {
                    val input = openInputStream(source.file.uri) ?: throw FileNotFoundException("Provider returned no input stream")
                    input.use {
                        if (!sameSource) {
                            val output = openOutputStream(destination, "wt") ?: throw FileNotFoundException("Provider returned no output stream")
                            output.use { out -> copySaveContent(input, out) }
                        }
                    }
                }
            }
            currentCoroutineContext().ensureActive()
            completed = true
            null
        }
    } catch (cancelled: CancellationException) {
        throw cancelled
    } catch (failure: Exception) {
        FilePickerException("Could not write the saved file", failure)
    } finally {
        if (!completed && identityChecked && !sameSource) {
            // This also runs if cancellation prevented the first IO dispatch from entering.
            withContext(NonCancellable + Dispatchers.IO) {
                // ACTION_CREATE_DOCUMENT owns a new destination. Providers may refuse deletion;
                // cleanup failure is not success and may leave a partial document behind.
                try { DocumentsContract.deleteDocument(this@writeSaveSource, destination) } catch (_: Exception) { }
            }
        }
    }
}

internal suspend fun copySaveContent(input: InputStream, output: OutputStream) {
    val buffer = ByteArray(64 * 1024)
    while (true) {
        currentCoroutineContext().ensureActive()
        val count = input.read(buffer)
        if (count == -1) return
        if (count == 0) throw java.io.IOException("Source made no progress")
        output.write(buffer, 0, count)
    }
}

private data class SaveDocumentInput(val name: String, val initialDirectory: String?)
private class CreateSaveDocument : androidx.activity.result.contract.ActivityResultContract<SaveDocumentInput, Uri?>() {
    private val delegate = ActivityResultContracts.CreateDocument("application/octet-stream")
    override fun createIntent(context: Context, input: SaveDocumentInput): Intent = delegate.createIntent(context, input.name).apply {
        type = MimeTypeMap.getSingleton().getMimeTypeFromExtension(input.name.substringAfterLast('.', "").lowercase(Locale.ROOT))
            ?: "application/octet-stream"
        if (Build.VERSION.SDK_INT >= 26 && input.initialDirectory != null) {
            putExtra(DocumentsContract.EXTRA_INITIAL_URI, Uri.parse(input.initialDirectory))
        }
    }
    override fun parseResult(resultCode: Int, intent: Intent?): Uri? = delegate.parseResult(resultCode, intent)
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
     * Launches the platform save dialog using an Android [Uri] as the source.
     *
     * @param uri The source content URI to save.
     * @param baseName The suggested file name without extension (e.g. "document").
     * @param extension The file extension without dot (e.g. "pdf").
     * @param initialDirectory Optional initial directory for the save dialog.
     */
    fun launch(
        uri: Uri,
        baseName: String,
        extension: String,
        initialDirectory: String? = null,
    ) {
        launch(KmpFile(uri), baseName, extension, initialDirectory)
    }

    /**
     * Launches the platform save dialog using a [java.io.File] as the source.
     *
     * @param file The source file to save.
     * @param baseName The suggested file name without extension (e.g. "document").
     * @param extension The file extension without dot (e.g. "pdf").
     * @param initialDirectory Optional initial directory for the save dialog.
     */
    fun launch(
        file: File,
        baseName: String,
        extension: String,
        initialDirectory: String? = null,
    ) {
        launch(KmpFile(Uri.fromFile(file)), baseName, extension, initialDirectory)
    }
}
