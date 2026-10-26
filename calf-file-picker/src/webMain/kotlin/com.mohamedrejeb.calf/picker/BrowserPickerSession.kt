package com.mohamedrejeb.calf.picker

import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import com.mohamedrejeb.calf.io.KmpFile
import kotlinx.browser.document
import org.w3c.dom.HTMLInputElement
import org.w3c.dom.asList
import org.w3c.files.File

/** Owns one real input element and its listeners, including terminal callback exceptions. */
internal class BrowserPickerSession(
    val input: HTMLInputElement,
    private val mode: FilePickerSelectionMode,
    private val onResult: (List<KmpFile>) -> Unit,
    private val onError: (FilePickerException) -> Unit,
    private val readFiles: () -> List<File> = { input.files?.asList().orEmpty() },
) {
    var finished = false
        private set

    init {
        input.onchange = { selected() }
        input.oncancel = { cancelled() }
    }

    fun selected() {
        if (finished) return
        val result = try { Result.success(readFiles().limitedTo(mode).map(::KmpFile)) }
            catch (error: Exception) { Result.failure(error) }
        close()
        // No user code inside the conversion catch, and cleanup precedes delivery.
        result.fold(onResult) { onError(FilePickerException("Could not read the selected files", it)) }
    }

    fun cancelled() {
        if (finished) return
        close()
        onResult(emptyList())
    }

    fun failed(failure: Exception) {
        if (finished) throw failure // Do not swallow a synchronously dispatched application exception.
        close()
        onError(FilePickerException("Could not open the browser file picker", failure))
    }

    fun close() {
        finished = true
        input.onchange = null
        input.oncancel = null
        input.remove()
    }
}

@Composable
internal fun rememberBrowserFilePickerLauncher(
    type: FilePickerFileType,
    selectionMode: FilePickerSelectionMode,
    onError: (FilePickerException) -> Unit,
    onResult: (List<KmpFile>) -> Unit,
): FilePickerLauncher {
    val currentType by rememberUpdatedState(type)
    val currentMode by rememberUpdatedState(selectionMode)
    val currentOnError by rememberUpdatedState(onError)
    val currentOnResult by rememberUpdatedState(onResult)
    val owner = remember { BrowserPickerOwner() }
    DisposableEffect(owner) { onDispose { owner.close() } }
    return remember(owner) {
        FilePickerLauncher(type, selectionMode) launch@{
            if (owner.disposed) return@launch
            if (owner.session?.finished == false) {
                currentOnError(FilePickerException("A browser picker is already open"))
                return@launch
            }
            val launchType = currentType
            val launchMode = currentMode
            if (launchType == FilePickerFileType.Folder) {
                currentOnError(FilePickerException("Folder picking is not supported by this browser File API"))
                return@launch
            }
            val input = document.createElement("input") as HTMLInputElement
            val session = BrowserPickerSession(input, launchMode, { currentOnResult(it) }, { currentOnError(it) })
            owner.attach(session)
            try {
                input.type = "file"
                input.name = "file"
                input.style.display = "none"
                input.accept = if (launchType is FilePickerFileType.Extension) launchType.value.joinToString(",") { ".$it" }
                    else launchType.value.joinToString(",")
                input.multiple = launchMode is FilePickerSelectionMode.Multiple && launchMode.maxItems != 1
                val body = document.body ?: error("The browser document has no body")
                body.appendChild(input)
                input.click() // Keep the user-activation stack; do not dispatch this asynchronously.
            } catch (failure: Exception) {
                session.failed(failure)
            }
        }
    }
}

internal class BrowserPickerOwner {
    var session: BrowserPickerSession? = null
        private set
    var disposed = false
        private set
    fun attach(next: BrowserPickerSession) {
        check(!disposed) { "The browser picker composition was disposed" }
        check(session?.finished != false) { "A browser picker is already open" }
        session = next
    }
    fun close() { disposed = true; session?.close(); session = null }
}
