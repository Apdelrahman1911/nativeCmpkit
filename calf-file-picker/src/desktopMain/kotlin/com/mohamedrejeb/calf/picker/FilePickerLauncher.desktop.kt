// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.picker

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.Stable
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.window.FrameWindowScope
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.picker.platform.PlatformFilePicker
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import kotlinx.coroutines.isActive

// Retain the original platform file-facade entry point as well as its common signature.
@Composable
actual fun rememberFilePickerLauncher(
    type: FilePickerFileType,
    selectionMode: FilePickerSelectionMode,
    settings: FilePickerSettings,
    onResult: (List<KmpFile>) -> Unit,
): FilePickerLauncher = rememberFilePickerLauncher(type, selectionMode, settings, { onResult(emptyList()) }, onResult)


@Composable
actual fun rememberFilePickerLauncher(
    type: FilePickerFileType,
    selectionMode: FilePickerSelectionMode,
    settings: FilePickerSettings,
    onError: (FilePickerException) -> Unit,
    onResult: (List<KmpFile>) -> Unit,
): FilePickerLauncher {
    // Resolve parent window: settings.parentWindow > LocalFilePickerParentWindow > null
    val localWindow = LocalFilePickerParentWindow.current
    val resolvedSettings = remember(
        settings.title,
        settings.initialDirectory,
        settings.parentWindow,
        localWindow,
    ) {
        if (settings.parentWindow == null && localWindow != null) {
            FilePickerSettings(
                title = settings.title,
                initialDirectory = settings.initialDirectory,
                imageRepresentationMode = settings.imageRepresentationMode,
                parentWindow = localWindow,
            )
        } else {
            settings
        }
    }

    return rememberFilePickerLauncherInternal(type, selectionMode, resolvedSettings, onError, onResult)
}

/**
 * Desktop-only extension that automatically captures the [FrameWindowScope.window]
 * as the parent window for the file picker dialog. Failures are not reported; use the overload
 * with `onError` to observe them.
 */
@Composable
fun FrameWindowScope.rememberFilePickerLauncher(
    type: FilePickerFileType = FilePickerFileType.All,
    selectionMode: FilePickerSelectionMode = FilePickerSelectionMode.Single,
    settings: FilePickerSettings = defaultFilePickerSettings(),
    onResult: (List<KmpFile>) -> Unit,
): FilePickerLauncher = rememberFilePickerLauncher(
    type = type,
    selectionMode = selectionMode,
    settings = settings,
    onError = { onResult(emptyList()) },
    onResult = onResult,
)

/**
 * Desktop-only extension that automatically captures the [FrameWindowScope.window]
 * as the parent window for the file picker dialog.
 *
 * @param onError Called when the dialog cannot be created or shown, for example when the native
 * library cannot be loaded. Cancelling the dialog is not a failure.
 */
@Composable
fun FrameWindowScope.rememberFilePickerLauncher(
    type: FilePickerFileType = FilePickerFileType.All,
    selectionMode: FilePickerSelectionMode = FilePickerSelectionMode.Single,
    settings: FilePickerSettings = defaultFilePickerSettings(),
    onError: (FilePickerException) -> Unit,
    onResult: (List<KmpFile>) -> Unit,
): FilePickerLauncher {
    val resolvedSettings = remember(
        settings.title,
        settings.initialDirectory,
        settings.parentWindow,
        window,
    ) {
        if (settings.parentWindow == null) {
            FilePickerSettings(
                title = settings.title,
                initialDirectory = settings.initialDirectory,
                imageRepresentationMode = settings.imageRepresentationMode,
                parentWindow = window,
            )
        } else {
            settings
        }
    }

    return rememberFilePickerLauncherInternal(type, selectionMode, resolvedSettings, onError, onResult)
}

@Composable
private fun rememberFilePickerLauncherInternal(
    type: FilePickerFileType,
    selectionMode: FilePickerSelectionMode,
    settings: FilePickerSettings,
    onError: (FilePickerException) -> Unit,
    onResult: (List<KmpFile>) -> Unit,
): FilePickerLauncher {
    val scope = rememberCoroutineScope()
    val currentOnResult by rememberUpdatedState(onResult)
    val currentOnError by rememberUpdatedState(onError)
    val currentType by rememberUpdatedState(type)
    val currentMode by rememberUpdatedState(selectionMode)
    val currentSettings by rememberUpdatedState(settings)
    val busy = remember { java.util.concurrent.atomic.AtomicBoolean(false) }
    return remember {
        FilePickerLauncher(type, selectionMode) launch@{
            if (!scope.isActive) return@launch
            if (!busy.compareAndSet(false, true)) {
                currentOnError(FilePickerException("A picker is already open"))
                return@launch
            }
            // Inputs belong to this launch, not to whatever composition exists at completion.
            val launchType = currentType
            val launchMode = currentMode
            val launchSettings = currentSettings
            scope.launch {
                val result = try {
                    Result.success(PlatformFilePicker.pick(
                        initialDirectory = launchSettings.initialDirectory,
                        type = launchType,
                        selectionMode = launchMode,
                        title = launchSettings.title,
                        parentWindow = launchSettings.parentWindow,
                    ).limitedTo(launchMode).map(::KmpFile))
                } catch (cancelled: CancellationException) {
                    throw cancelled
                } catch (failure: Throwable) {
                    if (failure is VirtualMachineError) throw failure
                    Result.failure(failure)
                } finally {
                    busy.set(false)
                }
                // Handle is already destroyed. Application callbacks are deliberately outside catch.
                result.fold(currentOnResult) { currentOnError(FilePickerException("Could not pick files", it)) }
            }
        }
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
