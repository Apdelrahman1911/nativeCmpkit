// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.picker.platform

import androidx.compose.ui.awt.ComposeWindow
import com.mohamedrejeb.calf.picker.FilePickerFileType
import com.mohamedrejeb.calf.picker.FilePickerSelectionMode
import com.mohamedrejeb.calf.picker.suggestedFileName
import jodd.net.MimeTypes
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.withContext
import java.io.File

internal object PlatformFilePicker {

    suspend fun pick(
        initialDirectory: String?, type: FilePickerFileType, selectionMode: FilePickerSelectionMode,
        title: String?, parentWindow: ComposeWindow?,
    ): List<File> = withContext(Dispatchers.IO) {
        withActiveDialogHandle(
            context = currentCoroutineContext(),
            create = {
                if (type == FilePickerFileType.Folder) createDirectoryPickerHandle(initialDirectory, title, parentWindow)
                else createFilePickerHandle(initialDirectory, type, selectionMode, title, parentWindow)
            },
            destroy = ::destroyDialog,
        ) { handle ->
            if (type == FilePickerFileType.Folder) listOfNotNull(NativeFilePickerBridge.showDirectoryDialog(handle)?.let(::File))
            else NativeFilePickerBridge.showFileDialog(handle).map(::File)
        }
    }

    suspend fun save(
        initialDirectory: String?, baseName: String, extension: String, title: String?,
        parentWindow: ComposeWindow?, source: File?, bytes: ByteArray?,
    ): File? = withContext(Dispatchers.IO) {
        withActiveDialogHandle(
            context = currentCoroutineContext(),
            create = { createSaveDialogHandle(initialDirectory, baseName, extension, title, parentWindow) },
            destroy = ::destroyDialog,
        ) { handle ->
            saveSelectedDesktopFile(NativeFilePickerBridge.showSaveDialog(handle), source, bytes)
        }
    }

    fun warmup() {
        NativeFilePickerBridge.init()
    }

    /**
     * Create a native file picker dialog handle.
     * The handle stores all configuration (title, filters, selection mode)
     * so that [showFilePicker] only needs to display it.
     *
     * Must be paired with [destroyDialog] when no longer needed.
     */
    fun createFilePickerHandle(
        initialDirectory: String?,
        type: FilePickerFileType,
        selectionMode: FilePickerSelectionMode,
        title: String?,
        parentWindow: ComposeWindow? = null,
    ): Long {
        val extensions = resolveExtensions(type)

        return NativeFilePickerBridge.createFileDialog(
            title = title,
            initialDirectory = initialDirectory,
            extensions = extensions?.toTypedArray(),
            multiple = selectionMode is FilePickerSelectionMode.Multiple,
            parentWindow = parentWindow?.windowHandle ?: 0L,
        )
    }

    /**
     * Create a native directory picker dialog handle.
     * Must be paired with [destroyDialog] when no longer needed.
     */
    fun createDirectoryPickerHandle(
        initialDirectory: String?,
        title: String?,
        parentWindow: ComposeWindow? = null,
    ): Long {
        return NativeFilePickerBridge.createDirectoryDialog(
            title = title,
            initialDirectory = initialDirectory,
            parentWindow = parentWindow?.windowHandle ?: 0L,
        )
    }

    /**
     * Create a native save-file dialog handle.
     * Must be paired with [destroyDialog] when no longer needed.
     */
    fun createSaveDialogHandle(
        initialDirectory: String?,
        baseName: String,
        extension: String,
        title: String? = null,
        parentWindow: ComposeWindow? = null,
    ): Long {
        return NativeFilePickerBridge.createSaveDialog(
            title = title,
            initialDirectory = initialDirectory,
            defaultName = suggestedFileName(baseName, extension),
            extension = extension,
            parentWindow = parentWindow?.windowHandle ?: 0L,
        )
    }

    /** Show a previously created file picker dialog. */
    suspend fun showFilePicker(handle: Long): List<File> {
        val paths = withContext(Dispatchers.IO) {
            NativeFilePickerBridge.showFileDialog(handle)
        }
        return paths.map { File(it) }
    }

    /** Show a previously created directory picker dialog. */
    suspend fun showDirectoryPicker(handle: Long): File? {
        val path = withContext(Dispatchers.IO) {
            NativeFilePickerBridge.showDirectoryDialog(handle)
        }
        return path?.let { File(it) }
    }

    /** Show a previously created save dialog and write bytes to the selected file. */
    suspend fun showSaveDialog(handle: Long, bytes: ByteArray?): File? {
        return withContext(Dispatchers.IO) {
            saveSelectedDesktopFile(NativeFilePickerBridge.showSaveDialog(handle), null, bytes)
        }
    }

    /** Show a previously created save dialog and copy a source file to the selected location. */
    suspend fun showSaveDialogWithFile(handle: Long, sourceFile: File): File? {
        return withContext(Dispatchers.IO) {
            saveSelectedDesktopFile(NativeFilePickerBridge.showSaveDialog(handle), sourceFile, null)
        }
    }

    /** Free the native memory for a dialog handle. */
    fun destroyDialog(handle: Long) {
        NativeFilePickerBridge.destroyDialog(handle)
    }
}

/**
 * Resolves [FilePickerFileType] to a list of file extensions for the native dialog filter.
 * Returns null when no filter should be applied (All, Folder).
 */
internal fun resolveExtensions(type: FilePickerFileType): List<String>? {
    return when (type) {
        is FilePickerFileType.All,
        is FilePickerFileType.Folder -> null

        is FilePickerFileType.Extension -> type.extensions.also { extensions ->
            require(extensions.isNotEmpty() && extensions.all { it.isNotBlank() && it.none { c -> c == '/' || c == '\\' || c == '*' || c == '?' || c.code < 32 } }) {
                "Expected explicit non-empty file extensions"
            }
        }

        else -> {
            type.value
                .flatMap { mimeType ->
                    MimeTypes.findExtensionsByMimeTypes(mimeType, mimeType.contains('*'))
                        .ifEmpty { throw IllegalArgumentException("Unknown MIME type '$mimeType'; use FilePickerFileType.Extension") }
                }
                .distinct()
                .ifEmpty { throw IllegalArgumentException("No extensions registered for ${type.value.toList()}; use FilePickerFileType.Extension") }
        }
    }
}
