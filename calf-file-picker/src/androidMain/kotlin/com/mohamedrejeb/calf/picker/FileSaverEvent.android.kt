package com.mohamedrejeb.calf.picker

import androidx.compose.runtime.Composable
import com.mohamedrejeb.calf.core.ExperimentalCalfApi

actual fun fileSaverCapability(): FileSaverCapability = FileSaverCapability.SaveDestination

@ExperimentalCalfApi
@Composable
actual fun rememberFileSaverEventLauncher(
    settings: FilePickerSettings,
    onEvent: (FileSaverEvent) -> Unit,
): FileSaverLauncher = rememberFileSaverLauncher(
    settings = settings,
    onError = { onEvent(FileSaverEvent.Failed(it)) },
    onResult = { onEvent(if (it == null) FileSaverEvent.Cancelled else FileSaverEvent.Saved(it)) },
)
