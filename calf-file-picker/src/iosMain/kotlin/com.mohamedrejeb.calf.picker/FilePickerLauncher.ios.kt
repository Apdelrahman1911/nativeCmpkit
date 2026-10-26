// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
// Retains reviewed type/staging logic from MohamedRejeb/Calf PR #551; sessions are nativeCmpkit-owned.
package com.mohamedrejeb.calf.picker

import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.Stable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.uikit.LocalUIViewController
import com.mohamedrejeb.calf.core.InternalCalfApi
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.io.releaseTemporaryCopy
import kotlinx.cinterop.BetaInteropApi
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.IO
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import platform.Foundation.NSItemProvider
import platform.Foundation.NSThread
import platform.Foundation.NSURL
import platform.PhotosUI.PHPickerConfiguration
import platform.PhotosUI.PHPickerConfigurationAssetRepresentationModeCompatible
import platform.PhotosUI.PHPickerConfigurationAssetRepresentationModeCurrent
import platform.PhotosUI.PHPickerFilter
import platform.PhotosUI.PHPickerResult
import platform.PhotosUI.PHPickerViewController
import platform.PhotosUI.PHPickerViewControllerDelegateProtocol
import platform.UIKit.UIDocumentPickerViewController
import platform.UIKit.presentationController
import platform.UniformTypeIdentifiers.UTType
import platform.UniformTypeIdentifiers.UTTypeAudio
import platform.UniformTypeIdentifiers.UTTypeData
import platform.UniformTypeIdentifiers.UTTypeFolder
import platform.UniformTypeIdentifiers.UTTypeImage
import platform.UniformTypeIdentifiers.UTTypeText
import platform.UniformTypeIdentifiers.UTTypeVideo
import platform.UniformTypeIdentifiers.UTTypeMovie
import kotlin.concurrent.AtomicInt
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

@Composable
actual fun rememberFilePickerLauncher(
    type: FilePickerFileType,
    selectionMode: FilePickerSelectionMode,
    settings: FilePickerSettings,
    onResult: (List<KmpFile>) -> Unit,
): FilePickerLauncher = rememberFilePickerLauncher(type, selectionMode, settings, { onResult(emptyList()) }, onResult)

@OptIn(BetaInteropApi::class, InternalCalfApi::class)
@Composable
actual fun rememberFilePickerLauncher(
    type: FilePickerFileType,
    selectionMode: FilePickerSelectionMode,
    settings: FilePickerSettings,
    onError: (FilePickerException) -> Unit,
    onResult: (List<KmpFile>) -> Unit,
): FilePickerLauncher {
    val scope = rememberCoroutineScope()
    val presenter = LocalUIViewController.current
    val currentOnResult by rememberUpdatedState(onResult)
    val currentOnError by rememberUpdatedState(onError)
    val currentType by rememberUpdatedState(type)
    val currentMode by rememberUpdatedState(selectionMode)
    val currentSettings by rememberUpdatedState(settings)
    val owner = remember(presenter) { IosDialogOwner() }
    DisposableEffect(owner) { onDispose { owner.close() } }
    return remember(owner) {
        FilePickerLauncher(type, selectionMode) launch@{
            if (!scope.isActive) return@launch
            val session = try {
                check(NSThread.isMainThread) { "Launch the iOS picker from the main thread" }
                check(presenter.presentedViewController == null) { "The presenter already has a presented controller" }
                owner.begin()
            } catch (failure: Exception) {
                currentOnError(FilePickerException("Could not begin picking", failure))
                return@launch
            }
            val launchType = currentType
            val launchMode = currentMode
            val launchSettings = currentSettings

            fun stageAndDeliver(stage: suspend (MutableList<KmpFile>) -> Unit) {
                session.job = scope.launch {
                    val owned = mutableListOf<KmpFile>()
                    var transferred = false
                    try {
                        val failure = try {
                            withContext(Dispatchers.IO) { stage(owned) }
                            currentCoroutineContext().ensureActive()
                            if (session.cancelled) throw CancellationException("Picker disposed")
                            null
                        } catch (cancelled: CancellationException) {
                            throw cancelled
                        } catch (error: Exception) {
                            if (error is FilePickerException) error else FilePickerException("Could not read picked files", error)
                        }
                        owner.end(session)
                        session.awaitFinished()
                        currentCoroutineContext().ensureActive()
                        if (session.cancelled) throw CancellationException("Picker disposed")
                        if (failure != null) currentOnError(failure)
                        else {
                            // Transfer before user code; its exception must not delete returned files.
                            transferred = true
                            currentOnResult(owned.toList())
                        }
                    } finally {
                        if (!transferred) owned.forEach { it.releaseTemporaryCopy() }
                        owner.end(session)
                    }
                }
            }
            fun deliverCancellation() {
                session.job = scope.launch {
                    owner.end(session)
                    session.awaitFinished()
                    if (!session.cancelled) currentOnResult(emptyList())
                }
            }
            val launchFailure = try {
                if (launchType == FilePickerFileType.Image || launchType == FilePickerFileType.Video || launchType == FilePickerFileType.ImageVideo) {
                    val delegate = PhotoPickerDelegate(session,
                        onPicked = { results ->
                            val picked = results.limitedTo(launchMode)
                            session.requestDismissal()
                            stageAndDeliver { files ->
                                // Deliberately bounded to one provider copy at a time. Limit before copying.
                                for (result in picked) {
                                    currentCoroutineContext().ensureActive()
                                    val file = result.itemProvider.loadFileRepresentationForTypeIdentifierSuspend(launchType)
                                        ?: throw FilePickerException("A selected photo/video could not be copied")
                                    files += file
                                }
                            }
                        },
                        onCancelled = ::deliverCancellation,
                    )
                    val picker = createPHPickerViewController(delegate, launchType, launchMode, launchSettings.imageRepresentationMode)
                    session.controller = picker
                    session.detachDelegate = { picker.delegate = null; picker.presentationController?.delegate = null }
                    picker.presentationController?.delegate = delegate
                    // Capture the delegate strongly across Apple's weak delegate properties.
                    session.retainedDelegate = delegate
                    presentIosDialog(presenter, session)
                    if (session.controller === picker) picker.presentationController?.delegate = delegate
                } else {
                    val picker = createUIDocumentPickerViewController(launchType, launchMode, launchSettings.initialDirectory)
                    val delegate = DocumentPickerDelegate(
                        onPicked = { urls ->
                            if (session.claimResult()) {
                                stageAndDeliver { files ->
                                    val context = currentCoroutineContext()
                                    if (launchType == FilePickerFileType.Folder) {
                                        for (url in urls.limitedTo(launchMode)) {
                                            context.ensureActive()
                                            files += KmpFile(url)
                                        }
                                    } else {
                                        val staged = stagePickedUrls(urls, launchMode) { context.ensureActive() }
                                        files += staged.files
                                        staged.failure?.let { throw it }
                                    }
                                }
                            }
                        },
                        onCancelled = {
                            if (session.claimResult()) deliverCancellation()
                        },
                        onDismissed = session::dismissalCompleted,
                    )
                    session.controller = picker
                    session.detachDelegate = { delegate.close() }
                    delegate.attachTo(picker)
                    presentIosDialog(presenter, session)
                    if (session.controller === picker) picker.presentationController?.delegate = delegate
                }
                null
            } catch (failure: Exception) {
                owner.end(session)
                FilePickerException("Could not present the picker", failure)
            }
            if (launchFailure != null) currentOnError(launchFailure)
        }
    }
}

@OptIn(InternalCalfApi::class)
private suspend fun NSItemProvider.loadFileRepresentationForTypeIdentifierSuspend(type: FilePickerFileType): KmpFile? =
    suspendCancellableCoroutine { continuation ->
        val finished = AtomicInt(0)
        val identifier = when (type) {
            FilePickerFileType.Image -> UTTypeImage.identifier
            FilePickerFileType.Video -> UTTypeMovie.identifier
            else -> registeredTypeIdentifiers.firstOrNull() as? String ?: UTTypeImage.identifier
        }
        val progress = loadFileRepresentationForTypeIdentifier(identifier) { url, error ->
            if (!finished.compareAndSet(0, 1)) return@loadFileRepresentationForTypeIdentifier
            // The provider's temporary URL expires as soon as this callback returns. Copy here.
            val result = try { Result.success(if (error == null) url?.toStagedKmpFile() else null) }
                catch (failure: Exception) { Result.failure(failure) }
            // Resume is deliberately outside staging's catch; it can never cause a second resume.
            result.fold(
                onSuccess = { file -> continuation.resume(file) { _, unconsumed, _ -> unconsumed?.releaseTemporaryCopy() } },
                onFailure = { failure -> continuation.resumeWithException(failure) },
            )
        }
        continuation.invokeOnCancellation {
            finished.compareAndSet(0, 1)
            progress.cancel()
        }
    }

internal fun createUIDocumentPickerViewController(
    type: FilePickerFileType,
    selectionMode: FilePickerSelectionMode,
    initialDirectory: String?,
): UIDocumentPickerViewController {
    val contentTypes = iosDocumentContentTypes(type)
    val pickerController =
        UIDocumentPickerViewController(
            forOpeningContentTypes = contentTypes,
            asCopy = type != FilePickerFileType.Folder,
        )
    pickerController.allowsMultipleSelection = selectionMode is FilePickerSelectionMode.Multiple
    pickerController.directoryURL = initialDirectoryUrl(initialDirectory)
    return pickerController
}

/** Document deliberately means broad data on Apple, not an application bundle UTI. */
internal fun iosDocumentContentTypes(type: FilePickerFileType): List<UTType> {
    val contentTypes =
        if (type is FilePickerFileType.Extension)
            type.value
                .map { extension ->
                    suggestedFileName("file", extension)
                    requireNotNull(UTType.typeWithFilenameExtension(extension)) { "Unsupported filename extension: $extension" }
                }
        else
            type.value.map { mimeType ->
                when (mimeType) {
                    FilePickerFileType.ImageContentType -> UTTypeImage
                    FilePickerFileType.VideoContentType -> UTTypeVideo
                    FilePickerFileType.AudioContentType -> UTTypeAudio
                    FilePickerFileType.DocumentContentType -> UTTypeData
                    FilePickerFileType.TextContentType -> UTTypeText
                    FilePickerFileType.AllContentType -> UTTypeData
                    FilePickerFileType.FolderContentType -> UTTypeFolder
                    else -> requireNotNull(UTType.typeWithMIMEType(mimeType)) { "Unsupported MIME type: $mimeType" }
                }
            }
    require(contentTypes.isNotEmpty()) { "At least one file type must be requested" }
    return contentTypes
}


private fun createPHPickerViewController(
    delegate: PHPickerViewControllerDelegateProtocol,
    type: FilePickerFileType,
    selectionMode: FilePickerSelectionMode,
    imageRepresentationMode: ImageRepresentationMode = ImageRepresentationMode.Compatible,
): PHPickerViewController {
    val picker = PHPickerViewController(createPHPickerConfiguration(type, selectionMode, imageRepresentationMode))
    picker.delegate = delegate
    return picker
}

internal fun createPHPickerConfiguration(
    type: FilePickerFileType,
    selectionMode: FilePickerSelectionMode,
    imageRepresentationMode: ImageRepresentationMode,
): PHPickerConfiguration {
    val configuration = PHPickerConfiguration()
    val filterList = mutableListOf<PHPickerFilter>()
    when (type) {
        FilePickerFileType.Image ->
            filterList.add(PHPickerFilter.imagesFilter())

        FilePickerFileType.Video -> {
            filterList.add(PHPickerFilter.videosFilter())
            filterList.add(PHPickerFilter.livePhotosFilter())
        }

        else -> {
            filterList.add(PHPickerFilter.imagesFilter())
            filterList.add(PHPickerFilter.videosFilter())
        }
    }
    val newFilter = PHPickerFilter.anyFilterMatchingSubfilters(filterList.toList())
    configuration.filter = newFilter
    configuration.preferredAssetRepresentationMode = when (imageRepresentationMode) {
        ImageRepresentationMode.Compatible -> PHPickerConfigurationAssetRepresentationModeCompatible
        ImageRepresentationMode.Current -> PHPickerConfigurationAssetRepresentationModeCurrent
    }
    configuration.selectionLimit = when (selectionMode) {
        is FilePickerSelectionMode.Multiple -> selectionMode.maxItems?.toLong() ?: 0
        else -> 1
    }
    return configuration
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
