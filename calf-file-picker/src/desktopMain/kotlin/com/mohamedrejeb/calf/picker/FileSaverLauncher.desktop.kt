// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.picker

import androidx.compose.runtime.Composable
import androidx.compose.runtime.Stable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import com.mohamedrejeb.calf.core.ExperimentalCalfApi
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.picker.platform.PlatformFilePicker
import java.io.File
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import kotlinx.coroutines.isActive
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive

// Retain the original platform file-facade entry point for existing binaries.
@ExperimentalCalfApi
@Composable
actual fun rememberFileSaverLauncher(
    settings: FilePickerSettings,
    onResult: (KmpFile?) -> Unit,
): FileSaverLauncher = rememberFileSaverLauncher(settings, { onResult(null) }, onResult)


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
    val currentParent by rememberUpdatedState(settings.parentWindow ?: LocalFilePickerParentWindow.current)
    val busy = remember { java.util.concurrent.atomic.AtomicBoolean(false) }
    val save: (ByteArray?, File?, String, String, String?) -> Unit = launch@{ bytes, source, name, extension, directory ->
        if (!scope.isActive) return@launch
        if (!busy.compareAndSet(false, true)) {
            currentOnError(FilePickerException("A save is already open"))
            return@launch
        }
        val launchSettings = currentSettings
        val launchParent = currentParent
        scope.launch {
            val result = try {
                Result.success(PlatformFilePicker.save(directory ?: launchSettings.initialDirectory,
                    name, extension, launchSettings.title, launchParent, source, bytes))
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (failure: Throwable) {
                if (failure is VirtualMachineError) throw failure
                Result.failure(failure)
            } finally {
                busy.set(false)
            }
            currentCoroutineContext().ensureActive()
            result.fold({ currentOnResult(it?.let(::KmpFile)) }) { currentOnError(FilePickerException("Could not save the file", it)) }
        }
    }
    return remember {
        FileSaverLauncher(
            onLaunch = { bytes, name, extension, directory -> save(bytes, null, name, extension, directory) },
            onLaunchFile = { file, name, extension, directory -> save(null, file.file, name, extension, directory) },
        )
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
        launch(KmpFile(file), baseName, extension, initialDirectory)
    }
}
