// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
// Named copy export and document delegate derived from MohamedRejeb/Calf PR #551.
package com.mohamedrejeb.calf.picker

import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.Stable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.uikit.LocalUIViewController
import com.mohamedrejeb.calf.core.ExperimentalCalfApi
import com.mohamedrejeb.calf.core.InternalCalfApi
import com.mohamedrejeb.calf.io.KmpFile
import kotlinx.cinterop.BetaInteropApi
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.addressOf
import kotlinx.cinterop.usePinned
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.IO
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import platform.Foundation.NSData
import platform.Foundation.NSThread
import platform.Foundation.NSURL
import platform.Foundation.create
import platform.UIKit.UIDocumentPickerViewController
import platform.UIKit.presentationController

@ExperimentalCalfApi
@Composable
actual fun rememberFileSaverLauncher(settings: FilePickerSettings, onResult: (KmpFile?) -> Unit): FileSaverLauncher =
    rememberFileSaverLauncher(settings, { onResult(null) }, onResult)

@OptIn(BetaInteropApi::class, InternalCalfApi::class, ExperimentalForeignApi::class)
@ExperimentalCalfApi
@Composable
actual fun rememberFileSaverLauncher(
    settings: FilePickerSettings,
    onError: (FilePickerException) -> Unit,
    onResult: (KmpFile?) -> Unit,
): FileSaverLauncher {
    val scope = rememberCoroutineScope()
    val viewController = LocalUIViewController.current
    val currentOnResult by rememberUpdatedState(onResult)
    val currentOnError by rememberUpdatedState(onError)
    val currentSettings by rememberUpdatedState(settings)
    val owner = remember(viewController) { IosDialogOwner() }
    DisposableEffect(owner) { onDispose { owner.close() } }

    fun deliverResult(session: IosDialogSession, file: KmpFile?) {
        if (!session.claimResult()) return
        session.job = scope.launch {
            owner.end(session)
            session.awaitFinished()
            if (!session.cancelled) currentOnResult(file)
        }
    }

    val launchStaged: (String, String, String?, (String) -> NSURL?) -> Unit = launch@{ name, extension, directory, stage ->
        if (!scope.isActive) return@launch
        val prepared = try {
            check(NSThread.isMainThread) { "Launch the iOS saver from the main thread" }
            check(viewController.presentedViewController == null) { "The presenter already has a presented controller" }
            suggestedFileName(name, extension) to owner.begin()
        } catch (failure: Exception) {
            currentOnError(FilePickerException("Could not begin the save operation", failure))
            return@launch
        }
        val (fileName, session) = prepared
        val initialDirectory = directory ?: currentSettings.initialDirectory
        session.job = scope.launch {
            // Retain the allocation here, not as a cancellable withContext result handoff.
            var staged: NSURL? = null
            var ownedBySession = false
            var presentationStarted = false
            val failure = try {
                withContext(Dispatchers.IO) { staged = stage(fileName) }
                withContext(Dispatchers.Main.immediate) {
                    currentCoroutineContext().ensureActive()
                    val url = staged ?: throw FilePickerException("Could not prepare the file to save")
                    if (session.cancelled) throw CancellationException("Saver disposed")
                    val picker = UIDocumentPickerViewController(forExportingURLs = listOf(url), asCopy = true)
                    picker.directoryURL = initialDirectoryUrl(initialDirectory)
                    val delegate = DocumentPickerDelegate(
                        onPicked = { urls -> deliverResult(session, urls.firstOrNull()?.let(::KmpFile)) },
                        onCancelled = { deliverResult(session, null) },
                        onDismissed = session::dismissalCompleted,
                    )
                    session.controller = picker
                    session.detachDelegate = { delegate.close() }
                    session.cleanup = { removeStaging(url) }
                    ownedBySession = true
                    delegate.attachTo(picker)
                    // Revalidate the attached, idle presenter HERE, not only before staging.
                    // From admission to present there is no suspension or unrelated UI dispatch.
                    presentIosDialog(viewController, session)
                    if (session.controller === picker) picker.presentationController?.delegate = delegate
                    presentationStarted = true
                }
                null
            } catch (cancelled: CancellationException) {
                session.cancel()
                throw cancelled
            } catch (failure: Exception) {
                if (failure is FilePickerException) failure else FilePickerException("Could not save the file", failure)
            } finally {
                if (!ownedBySession) staged?.let { removeStaging(it) }
                // After the handoff, only the session may delete staging, at native completion.
                if (!presentationStarted) owner.end(session)
            }
            if (failure != null) {
                session.awaitFinished()
                if (!session.cancelled) currentOnError(failure)
            }
        }
    }
    return remember(owner) {
        FileSaverLauncher(
            onLaunch = { bytes, name, extension, directory ->
                // Create NSData on the worker as part of staging, not on the UI launch path.
                launchStaged(name, extension, directory) { fileName ->
                    val data = if (bytes == null || bytes.isEmpty()) NSData() else bytes.usePinned {
                        NSData.create(bytes = it.addressOf(0), length = bytes.size.toULong())
                    }
                    stageExportData(data, fileName)
                }
            },
            onLaunchFile = { file, name, extension, directory ->
                launchStaged(name, extension, directory) { stageExportFile(file.url, it) }
            },
            onLaunchData = { data, name, extension, directory ->
                launchStaged(name, extension, directory) { stageExportData(data, it) }
            },
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
    private val onLaunchData: (
        data: NSData,
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
     * Launches the platform save dialog using an iOS [NSURL] as the source.
     *
     * @param url The source file URL to save.
     * @param baseName The suggested file name without extension (e.g. "document").
     * @param extension The file extension without dot (e.g. "pdf").
     * @param initialDirectory Optional initial directory for the save dialog.
     */
    fun launch(
        url: NSURL,
        baseName: String,
        extension: String,
        initialDirectory: String? = null,
    ) {
        launch(KmpFile(url), baseName, extension, initialDirectory)
    }

    /**
     * Launches the platform save dialog using [NSData] as the source.
     *
     * The data is written to a temporary file and presented via the export picker.
     *
     * @param data The raw data to save.
     * @param baseName The suggested file name without extension (e.g. "document").
     * @param extension The file extension without dot (e.g. "pdf").
     * @param initialDirectory Optional initial directory for the save dialog.
     */
    fun launch(
        data: NSData,
        baseName: String,
        extension: String,
        initialDirectory: String? = null,
    ) {
        onLaunchData(data, baseName, extension, initialDirectory)
    }
}
