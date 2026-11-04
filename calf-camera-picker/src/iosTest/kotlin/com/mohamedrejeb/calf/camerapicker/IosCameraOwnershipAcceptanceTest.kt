@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class, kotlin.experimental.ExperimentalNativeApi::class)

package com.mohamedrejeb.calf.camerapicker

import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.uikit.LocalUIViewController
import com.mohamedrejeb.calf.camerapicker.internal.*
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.io.getPath
import com.mohamedrejeb.calf.io.readByteArray
import kotlinx.cinterop.addressOf
import kotlinx.cinterop.usePinned
import kotlinx.coroutines.runBlocking
import kotlin.native.ref.WeakReference
import kotlin.native.runtime.GC
import kotlin.test.*
import platform.CoreGraphics.CGContextFillRect
import platform.CoreGraphics.CGContextSetRGBFillColor
import platform.CoreGraphics.CGImageGetHeight
import platform.CoreGraphics.CGImageGetWidth
import platform.CoreGraphics.CGRectMake
import platform.CoreGraphics.CGSizeMake
import platform.Foundation.*
import platform.UIKit.*
import platform.darwin.NSObject

/**
 * Genuine UIApplication/Compose/UIImagePicker presentation with explicitly controlled terminal
 * delegate input. No physical acquisition, authorization denial, 12/48MP profiling, native
 * callback-throw, disk-full, cache-eviction or worker-entry/cancellation claim belongs to this batch.
 */
class IosCameraOwnershipAcceptanceTest {
    @Test fun publicOwnerSurvivesOrdinaryRecompositionAndNativeGcAndDeliversToLatestCallback() = runCameraApplicationUiTest {
        val options = mutableStateOf(CameraPickerOptions())
        val callbackVersion = mutableStateOf(0)
        val recomposition = mutableStateOf(0)
        val deliveries = mutableListOf<Pair<Int, CameraPickerResult>>()
        val mainDeliveries = mutableListOf<Boolean>()
        lateinit var parent: UIViewController
        lateinit var launcher: CameraPickerLauncher
        setContent {
            parent = LocalUIViewController.current
            recomposition.value
            val version = callbackVersion.value
            val current = rememberCameraPickerResultLauncher(options.value) {
                deliveries += version to it
                mainDeliveries += NSThread.isMainThread
            }
            SideEffect { launcher = current }
        }
        val weakOwner = runOnIdle {
            requireActualSimulatorPhotoLibrary()
            WeakReference(launcher).also { launcher.launch() }
        }
        waitForCameraNative { parent.presentedViewController is UIImagePickerController &&
            nativePickerIsPresented(parent, parent.presentedViewController as? UIImagePickerController) }
        val picker = runOnIdle { assertIs<UIImagePickerController>(parent.presentedViewController) }
        // Neither the test nor the native picker (whose delegate property is weak) holds a
        // strong delegate across GC. Only the public remembered owner may retain this operation.
        val weakDelegate = runOnIdle { WeakReference(assertIs<NSObject>(picker.delegate)) }
        repeat(4) { index ->
            runOnIdle { callbackVersion.value = 1; options.value = CameraPickerOptions(iosPhotoLibraryFallback = false); recomposition.value = index + 1 }
            waitForIdle()
            runOnIdle {
                assertSame(assertNotNull(weakOwner.get()), launcher)
                assertTrue(sameNativeObject(parent.presentedViewController, picker))
                assertEquals(UIImagePickerControllerSourceType.UIImagePickerControllerSourceTypePhotoLibrary, picker.sourceType,
                    "Changing fallback options must not replace the source of an already admitted request")
            }
        }
        repeat(3) { runOnIdle { GC.collect() } }
        runOnIdle {
            assertSame(assertNotNull(weakOwner.get()), launcher)
            assertTrue(sameNativeObject(parent.presentedViewController, picker))
            val retainedOnlyAfterGc = assertNotNull(weakDelegate.get(), "The active owner must retain its weak native delegate through actual GC")
            assertTrue(sameNativeObject(retainedOnlyAfterGc, assertIs<NSObject>(picker.delegate)))
            assertIs<UIImagePickerControllerDelegateProtocol>(picker.delegate).imagePickerControllerDidCancel(picker)
        }
        waitForCameraNative { parent.presentedViewController == null && nativePickerHasNoPresentation(parent, picker) && deliveries.size == 1 && rootIsReappeared() }
        runOnIdle {
            assertEquals(listOf(1 to CameraPickerResult.Cancelled), deliveries)
            assertEquals(listOf(true), mainDeliveries)
            launcher.launch()
            assertIs<CameraPickerResult.Unavailable>(deliveries.last().second,
                "The next request must read current fallback=false on the actually camera-unavailable simulator")
            assertEquals(listOf(1, 1), deliveries.map { it.first })
            assertEquals(2, deliveries.size)
            assertNull(parent.presentedViewController)
            assertEquals(listOf(true, true), mainDeliveries)
        }
    }

    @Test fun doubleLaunchDuplicateTerminalInputAndReentrantReplacementKeepOneNativeOwner() = runCameraApplicationUiTest {
        val deliveries = mutableListOf<CameraPickerResult>()
        val mainDeliveries = mutableListOf<Boolean>()
        val terminalTeardowns = mutableListOf<Boolean>()
        var cancellations = 0
        var callbackPicker: UIImagePickerController? = null
        lateinit var parent: UIViewController
        lateinit var launcher: CameraPickerLauncher
        setContent {
            parent = LocalUIViewController.current
            val current = rememberCameraPickerResultLauncher {
                deliveries += it
                mainDeliveries += NSThread.isMainThread
                if (it == CameraPickerResult.Cancelled) {
                    terminalTeardowns += NSThread.isMainThread && callbackPicker?.let { picker ->
                        parent.presentedViewController == null && nativePickerHasNoPresentation(parent, picker)
                    } == true
                    cancellations++
                    // Ordinary application reentry, after observing A's genuine native teardown.
                    // No throwing callback is injected across an Objective-C completion boundary.
                    if (cancellations == 1) launcher.launch()
                }
            }
            SideEffect { launcher = current }
        }
        runOnIdle { requireActualSimulatorPhotoLibrary(); launcher.launch() }
        waitForCameraNative { nativePickerIsPresented(parent, parent.presentedViewController as? UIImagePickerController) }
        val first = runOnIdle { assertIs<UIImagePickerController>(parent.presentedViewController) }
        val lateFirstDelegate = runOnIdle {
            callbackPicker = first
            launcher.launch()
            assertEquals(listOf(CameraPickerResult.Busy), deliveries)
            assertTrue(sameNativeObject(first, parent.presentedViewController))
            assertIs<UIImagePickerControllerDelegateProtocol>(first.delegate).also {
                it.imagePickerControllerDidCancel(first)
                it.imagePickerControllerDidCancel(first)
            }
        }
        waitForCameraNative { cancellations == 1 && nativePickerIsPresented(parent, parent.presentedViewController as? UIImagePickerController) &&
            !sameNativeObject(parent.presentedViewController, first) }
        val second = runOnIdle { assertIs<UIImagePickerController>(parent.presentedViewController) }
        runOnIdle {
            assertFalse(sameNativeObject(first, second))
            assertEquals(listOf(CameraPickerResult.Busy, CameraPickerResult.Cancelled), deliveries)
            assertEquals(listOf(true), terminalTeardowns)
            val secondDelegate = assertIs<NSObject>(second.delegate)
            // Controlled retained old-delegate inputs are deliberately late, not actual user gestures.
            lateFirstDelegate.imagePickerControllerDidCancel(first)
            lateFirstDelegate.imagePickerController(picker = first, didFinishPickingMediaWithInfo = emptyMap())
            assertTrue(sameNativeObject(second, parent.presentedViewController))
            assertTrue(sameNativeObject(secondDelegate, assertIs<NSObject>(second.delegate)))
            assertEquals(2, deliveries.size)
            callbackPicker = second
            val delegate = assertIs<UIImagePickerControllerDelegateProtocol>(second.delegate)
            delegate.imagePickerControllerDidCancel(second)
            delegate.imagePickerControllerDidCancel(second)
        }
        waitForCameraNative { cancellations == 2 && parent.presentedViewController == null && nativePickerHasNoPresentation(parent, second) && rootIsReappeared() }
        runOnIdle {
            lateFirstDelegate.imagePickerControllerDidCancel(first)
            assertEquals(listOf(CameraPickerResult.Busy, CameraPickerResult.Cancelled, CameraPickerResult.Cancelled), deliveries)
            assertEquals(listOf(true, true), terminalTeardowns)
            assertEquals(listOf(true, true, true), mainDeliveries)
            assertNull(parent.presentedViewController)
        }
        // Native observations establish one surviving owner/outcome, not an instrumented native
        // dismiss-call count. The separate owning source-red control checks the first input claim.
    }

    @Test fun compositionDisposalDuringObservedPresentingAndPresentedPhasesFinishesOwnedTeardown() = runCameraApplicationUiTest {
        setContent {}
        val foreign = runOnIdle { ForeignWindowModal() }
        var failure: Throwable? = null
        try {
            waitForCameraNative { sameNativeObject(foreign.parent.view.window, foreign.window) }
            runOnIdle { foreign.beginPresentation() }
            waitForCameraNative { foreign.isActuallyPresented() }
            for (duringPresentation in listOf(true, false)) {
                val mounted = mutableStateOf(true)
                val deliveries = mutableListOf<CameraPickerResult>()
                var disposalWitness: Boolean? = null
                var picker: UIImagePickerController? = null
                lateinit var parent: UIViewController
                lateinit var launcher: CameraPickerLauncher
                setContent {
                    parent = LocalUIViewController.current
                    if (mounted.value) {
                        val current = rememberCameraPickerResultLauncher { deliveries += it }
                        SideEffect { launcher = current }
                        // A later DisposableEffect is forgotten before the launcher's earlier one.
                        // Refuse this variant unless the real UIKit flags at composition forgetting
                        // witness the requested phase; never assign a synthetic native phase.
                        DisposableEffect(current) {
                            onDispose {
                                val actual = picker
                                disposalWitness = actual != null && if (duringPresentation) actual.isBeingPresented()
                                    else nativePickerIsPresented(parent, actual)
                            }
                        }
                    }
                }
                val lateDelegate = runOnIdle {
                    requireActualSimulatorPhotoLibrary()
                    foreign.assertPreserved()
                    launcher.launch()
                    picker = assertIs<UIImagePickerController>(parent.presentedViewController)
                    val delegate = assertIs<UIImagePickerControllerDelegateProtocol>(picker!!.delegate)
                    if (duringPresentation) {
                        assertTrue(picker!!.isBeingPresented(), "The first disposal variant requires an observed real animated presentation")
                        mounted.value = false
                    }
                    delegate
                }
                if (!duringPresentation) {
                    waitForCameraNative { nativePickerIsPresented(parent, picker) }
                    runOnIdle { assertTrue(nativePickerIsPresented(parent, picker)); mounted.value = false }
                }
                waitForIdle()
                runOnIdle { assertEquals(true, disposalWitness, "Composition disposal must occur in the actually observed requested UIKit phase") }
                val ownedPicker = assertNotNull(picker)
                waitForCameraNative { parent.presentedViewController == null && nativePickerHasNoPresentation(parent, ownedPicker) && rootIsReappeared() }
                runOnIdle {
                    lateDelegate.imagePickerControllerDidCancel(ownedPicker)
                    lateDelegate.imagePickerController(picker = ownedPicker, didFinishPickingMediaWithInfo = emptyMap())
                    assertTrue(deliveries.isEmpty(), "Disposed owners suppress their late controlled terminal inputs")
                    assertTrue(nativePickerHasNoPresentation(parent, ownedPicker))
                    assertTrue(rootIsReappeared())
                    foreign.assertPreserved()
                    requireCameraApplicationWindow()
                }
            }
        } catch (error: Throwable) { failure = error; throw error } finally {
            cleanupPreserving(failure, { closeForeignWindow(foreign) })
        }
    }

    @Test fun actualSimulatorUnavailableAndCompetingModalOutcomesPreserveForeignPresenter() = runCameraApplicationUiTest {
        val mounted = mutableStateOf(true)
        val options = mutableStateOf(CameraPickerOptions(iosPhotoLibraryFallback = false))
        val deliveries = mutableListOf<CameraPickerResult>()
        val mainDeliveries = mutableListOf<Boolean>()
        lateinit var parent: UIViewController
        lateinit var launcher: CameraPickerLauncher
        setContent {
            parent = LocalUIViewController.current
            if (mounted.value) {
                val current = rememberCameraPickerResultLauncher(options.value) { deliveries += it; mainDeliveries += NSThread.isMainThread }
                SideEffect { launcher = current }
            }
        }
        runOnIdle {
            requireActualSimulatorPhotoLibrary()
            launcher.launch()
            assertEquals(1, deliveries.size)
            assertIs<CameraPickerResult.Unavailable>(deliveries.single())
            assertNull(parent.presentedViewController)
            options.value = CameraPickerOptions()
        }
        waitForIdle()
        runOnIdle { launcher.launch() }
        waitForCameraNative { nativePickerIsPresented(parent, parent.presentedViewController as? UIImagePickerController) }
        val picker = runOnIdle {
            assertIs<UIImagePickerController>(parent.presentedViewController).also {
                assertEquals(UIImagePickerControllerSourceType.UIImagePickerControllerSourceTypePhotoLibrary, it.sourceType)
                assertIs<UIImagePickerControllerDelegateProtocol>(it.delegate).imagePickerControllerDidCancel(it)
            }
        }
        waitForCameraNative { deliveries.size == 2 && parent.presentedViewController == null && nativePickerHasNoPresentation(parent, picker) && rootIsReappeared() }
        val competing = runOnIdle { UIViewController() }
        var presentedCompletion = false
        var dismissalCompletion = false
        var failure: Throwable? = null
        try {
            runOnIdle { parent.presentViewController(competing, true) { presentedCompletion = true } }
            waitForCameraNative { presentedCompletion && sameNativeObject(parent.presentedViewController, competing) &&
                sameNativeObject(competing.presentingViewController, parent) && !competing.isBeingPresented() }
            runOnIdle {
                launcher.launch()
                assertEquals(3, deliveries.size)
                assertEquals(CameraFailureReason.Launch, assertIs<CameraPickerResult.Failed>(deliveries.last()).reason)
                assertTrue(sameNativeObject(parent.presentedViewController, competing))
                assertTrue(sameNativeObject(competing.presentingViewController, parent))
                assertFalse(competing.isBeingDismissed())
                mounted.value = false
            }
            waitForIdle()
            runOnIdle {
                assertTrue(sameNativeObject(parent.presentedViewController, competing), "Refusal/disposal must not dismiss a foreign modal")
                assertTrue(sameNativeObject(competing.presentingViewController, parent))
                assertFalse(competing.isBeingDismissed())
                assertEquals(CameraPickerResult.Cancelled, deliveries[1])
                assertEquals(listOf(true, true, true), mainDeliveries)
                assertEquals(3, deliveries.size)
            }
        } catch (error: Throwable) { failure = error; throw error } finally {
            cleanupPreserving(failure,
                { waitForCameraNative { presentedCompletion && !competing.isBeingPresented() } },
                { onCameraApplicationMain {
                    check(sameNativeObject(parent.presentedViewController, competing)) { "Refuse cleanup of another modal" }
                    competing.dismissViewControllerAnimated(false) { dismissalCompletion = true }
                } },
                { waitForCameraNative { dismissalCompletion && parent.presentedViewController == null && competing.presentingViewController == null &&
                    !competing.isBeingPresented() && !competing.isBeingDismissed() && rootIsReappeared() } })
        }
    }

    @Test fun controlledOriginalNativeImageWritesRealPngAndJpegAndSuccessOutlivesOwner() = runCameraApplicationUiTest {
        val mounted = mutableStateOf(true)
        val options = mutableStateOf(CameraPickerOptions())
        val deliveries = mutableListOf<CameraPickerResult>()
        val mainDeliveries = mutableListOf<Boolean>()
        val callbackTeardowns = mutableListOf<Boolean>()
        val successfulFiles = mutableListOf<KmpFile>()
        val successfulBytes = mutableListOf<ByteArray>() // Test-Worker readback snapshots, never fabricated encoded results.
        var callbackPicker: UIImagePickerController? = null
        lateinit var parent: UIViewController
        lateinit var launcher: CameraPickerLauncher
        setContent {
            parent = LocalUIViewController.current
            if (mounted.value) {
                val current = rememberCameraPickerResultLauncher(options.value) {
                    deliveries += it
                    if (it is CameraPickerResult.Captured) successfulFiles += it.file
                    mainDeliveries += NSThread.isMainThread
                    callbackTeardowns += NSThread.isMainThread && callbackPicker?.let { picker ->
                        parent.presentedViewController == null && nativePickerHasNoPresentation(parent, picker)
                    } == true
                }
                SideEffect { launcher = current }
            }
        }
        val sentinelBytes = "unrelated caller-owned sentinel".encodeToByteArray()
        val sentinelPath = NSTemporaryDirectory() + "nativecmpkit-camera-unrelated-" + NSUUID().UUIDString + ".bin"
        var failure: Throwable? = null
        try {
            runOnIdle { requireActualSimulatorPhotoLibrary() }
            assertTrue(sentinelBytes.usePinned { NSData.dataWithBytes(it.addressOf(0), sentinelBytes.size.toULong()) }.writeToFile(sentinelPath, true))
            val input = runOnIdle { tinyControlledOriginalImage() }
            val firstOwner = runOnIdle { launcher }
            val formats = listOf(CameraImageFormat.Png, CameraImageFormat.Jpeg, CameraImageFormat.Png)
            for ((index, expectedFormat) in formats.withIndex()) {
                if (index == 1) {
                    runOnIdle { mounted.value = false }
                    waitForIdle()
                    assertContentEquals(successfulBytes.first(), readPublicBytes(onCameraApplicationMain { successfulFiles.first() }))
                    runOnIdle { options.value = CameraPickerOptions(iosImageFormat = CameraImageFormat.Jpeg, iosJpegQuality = 0.7); mounted.value = true }
                    waitForIdle()
                    runOnIdle { assertNotSame(firstOwner, launcher, "Composition replacement creates a new owner without owning A's successful file") }
                }
                runOnIdle { launcher.launch() }
                waitForCameraNative { nativePickerIsPresented(parent, parent.presentedViewController as? UIImagePickerController) }
                val picker = runOnIdle {
                    assertIs<UIImagePickerController>(parent.presentedViewController).also {
                        callbackPicker = it
                        // Encoding must use the admitted request's options, not this live replacement.
                        options.value = CameraPickerOptions(iosImageFormat = if (expectedFormat == CameraImageFormat.Png) CameraImageFormat.Jpeg else CameraImageFormat.Png)
                    }
                }
                waitForIdle()
                runOnIdle {
                    assertTrue(sameNativeObject(parent.presentedViewController, picker))
                    assertIs<UIImagePickerControllerDelegateProtocol>(picker.delegate).imagePickerController(
                        picker = picker, didFinishPickingMediaWithInfo = mapOf(UIImagePickerControllerOriginalImage to input))
                }
                waitForCameraNative { successfulFiles.size == index + 1 && parent.presentedViewController == null && nativePickerHasNoPresentation(parent, picker) && rootIsReappeared() }
                val file = onCameraApplicationMain { successfulFiles[index] }
                assertRealEncodedFile(file, expectedFormat)
                successfulBytes += readPublicBytes(file)
                val paths = onCameraApplicationMain { successfulFiles.map { assertNotNull(it.getPath()) } }
                assertEquals(paths.size, paths.toSet().size, "Each real repeated write uses a distinct UUID path")
                for ((priorIndex, prior) in onCameraApplicationMain { successfulFiles.toList() }.withIndex()) {
                    assertContentEquals(successfulBytes[priorIndex], readPublicBytes(prior))
                }
                assertContentEquals(sentinelBytes, readPublicBytes(KmpFile(NSURL.fileURLWithPath(sentinelPath))))
            }
            // A real missing-original-image delegate input checks one pre-encoding Io outcome.
            // It is not a write failure, disk-full or an observed mid-worker cancellation.
            runOnIdle { launcher.launch() }
            waitForCameraNative { nativePickerIsPresented(parent, parent.presentedViewController as? UIImagePickerController) }
            val missing = runOnIdle {
                assertIs<UIImagePickerController>(parent.presentedViewController).also {
                    callbackPicker = it
                    val delegate = assertIs<UIImagePickerControllerDelegateProtocol>(it.delegate)
                    delegate.imagePickerController(picker = it, didFinishPickingMediaWithInfo = emptyMap())
                    delegate.imagePickerController(picker = it, didFinishPickingMediaWithInfo = emptyMap())
                }
            }
            waitForCameraNative { deliveries.size == 4 && parent.presentedViewController == null && nativePickerHasNoPresentation(parent, missing) && rootIsReappeared() }
            runOnIdle {
                assertEquals(3, successfulFiles.size)
                assertEquals(CameraFailureReason.Io, assertIs<CameraPickerResult.Failed>(deliveries.last()).reason)
                assertEquals(listOf(true, true, true, true), mainDeliveries)
                assertEquals(listOf(true, true, true, true), callbackTeardowns)
                mounted.value = false
            }
            waitForIdle()
            for ((index, file) in onCameraApplicationMain { successfulFiles.toList() }.withIndex()) {
                assertRealEncodedFile(file, formats[index])
                assertContentEquals(successfulBytes[index], readPublicBytes(file))
            }
            assertContentEquals(sentinelBytes, readPublicBytes(KmpFile(NSURL.fileURLWithPath(sentinelPath))))
        } catch (error: Throwable) { failure = error; throw error } finally {
            cleanupPreserving(failure,
                { setContent {}; waitForIdle() },
                { removeCallerOwnedOutputs(onCameraApplicationMain { successfulFiles.toList() }) },
                { if (NSFileManager.defaultManager.fileExistsAtPath(sentinelPath)) assertTrue(NSFileManager.defaultManager.removeItemAtPath(sentinelPath, null)) })
        }
    }

    private fun requireActualSimulatorPhotoLibrary() {
        assertTrue(NSThread.isMainThread)
        assertFalse(UIImagePickerController.isSourceTypeAvailable(UIImagePickerControllerSourceType.UIImagePickerControllerSourceTypeCamera),
            "This finite host requires actual native camera unavailability, not a guessed simulator device name")
        assertTrue(UIImagePickerController.isSourceTypeAvailable(UIImagePickerControllerSourceType.UIImagePickerControllerSourceTypePhotoLibrary))
        for (key in listOf("NSCameraUsageDescription", "NSPhotoLibraryUsageDescription")) {
            assertFalse((NSBundle.mainBundle.objectForInfoDictionaryKey(key) as? String).isNullOrBlank(), "The genuine application host must supply $key")
        }
    }

    private fun tinyControlledOriginalImage(): UIImage {
        assertTrue(NSThread.isMainThread)
        UIGraphicsBeginImageContextWithOptions(CGSizeMake(24.0, 16.0), true, 1.0)
        try {
            val context = assertNotNull(UIGraphicsGetCurrentContext())
            CGContextSetRGBFillColor(context, 0.2, 0.5, 0.8, 1.0)
            CGContextFillRect(context, CGRectMake(0.0, 0.0, 24.0, 16.0))
            return assertNotNull(UIGraphicsGetImageFromCurrentImageContext())
        } finally { UIGraphicsEndImageContext() }
    }

    private fun assertRealEncodedFile(file: KmpFile, format: CameraImageFormat) {
        val bytes = readPublicBytes(file) // Real public KmpFile/Foundation read on the test Worker.
        val path = assertNotNull(file.getPath())
        assertTrue(path.startsWith(NSTemporaryDirectory() + "nativecmpkit-camera-"))
        when (format) {
            CameraImageFormat.Png -> {
                assertTrue(path.endsWith(".png"))
                assertContentEquals(byteArrayOf(0x89.toByte(), 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a), bytes.take(8).toByteArray())
            }
            CameraImageFormat.Jpeg -> {
                assertTrue(path.endsWith(".jpg"))
                assertContentEquals(byteArrayOf(0xff.toByte(), 0xd8.toByte(), 0xff.toByte()), bytes.take(3).toByteArray())
                assertContentEquals(byteArrayOf(0xff.toByte(), 0xd9.toByte()), bytes.takeLast(2).toByteArray())
            }
        }
        onCameraApplicationMain {
            val decoded = assertNotNull(UIImage.imageWithContentsOfFile(path), "UIKit must decode the actually written output")
            val nativeImage = assertNotNull(decoded.CGImage)
            assertEquals(24uL, CGImageGetWidth(nativeImage))
            assertEquals(16uL, CGImageGetHeight(nativeImage))
        }
    }

    private fun readPublicBytes(file: KmpFile): ByteArray = runBlocking { file.readByteArray() }
}

private fun nativePickerIsPresented(parent: UIViewController, picker: UIImagePickerController?): Boolean =
    picker != null && sameNativeObject(parent.presentedViewController, picker) && sameNativeObject(picker.presentingViewController, parent) &&
        !picker.isBeingPresented() && !picker.isBeingDismissed()

private fun nativePickerHasNoPresentation(parent: UIViewController, picker: UIImagePickerController): Boolean =
    !sameNativeObject(parent.presentedViewController, picker) && picker.presentingViewController == null &&
        !picker.isBeingPresented() && !picker.isBeingDismissed()

/** An unrelated real native window/modal, deliberately never passed to the Camera owner. */
private class ForeignWindowModal {
    val parent = UIViewController()
    val modal = UIViewController()
    val window = UIWindow(frame = UIScreen.mainScreen.bounds).apply { rootViewController = parent; hidden = false }
    var presentationStarted = false
    var presentationCompleted = false
    var dismissalCompleted = false

    fun beginPresentation() {
        check(NSThread.isMainThread && !presentationStarted)
        presentationStarted = true
        parent.presentViewController(modal, true) { presentationCompleted = true }
    }

    fun isActuallyPresented(): Boolean = presentationCompleted && sameNativeObject(parent.presentedViewController, modal) &&
        sameNativeObject(modal.presentingViewController, parent) && !modal.isBeingPresented() && !modal.isBeingDismissed()

    fun assertPreserved() {
        assertTrue(sameNativeObject(window.rootViewController, parent))
        assertTrue(sameNativeObject(parent.view.window, window))
        assertFalse(window.hidden)
        assertTrue(isActuallyPresented(), "Owned Camera cleanup must not touch an unrelated real window/modal")
    }
}

private fun NativeCameraApplicationUiTest.closeForeignWindow(foreign: ForeignWindowModal) {
    val started = onCameraApplicationMain { foreign.presentationStarted }
    cleanupPreserving(null,
        { if (started) waitForCameraNative { foreign.presentationCompleted && !foreign.modal.isBeingPresented() } },
        { onCameraApplicationMain {
            check(sameNativeObject(foreign.window.rootViewController, foreign.parent)) { "Refuse cleanup of a foreign replacement root" }
            if (started) {
                check(foreign.presentationCompleted && !foreign.modal.isBeingPresented()) { "Native presentation completion is required for cleanup" }
                check(sameNativeObject(foreign.parent.presentedViewController, foreign.modal)) { "Refuse cleanup of another foreign modal" }
                foreign.modal.dismissViewControllerAnimated(false) { foreign.dismissalCompleted = true }
            }
        } },
        { if (started) waitForCameraNative { foreign.dismissalCompleted && foreign.parent.presentedViewController == null &&
            foreign.modal.presentingViewController == null && !foreign.modal.isBeingPresented() && !foreign.modal.isBeingDismissed() } },
        { onCameraApplicationMain {
            check(sameNativeObject(foreign.window.rootViewController, foreign.parent))
            check(foreign.parent.presentedViewController == null && foreign.modal.presentingViewController == null &&
                !foreign.modal.isBeingPresented() && !foreign.modal.isBeingDismissed())
            foreign.window.hidden = true
            foreign.window.rootViewController = null
            requireCameraApplicationWindow()
        } })
}

private fun removeCallerOwnedOutputs(files: List<KmpFile>) {
    val actions = files.map { file ->
        val remove: () -> Unit = {
            val path = assertNotNull(file.getPath())
            check(path.startsWith(NSTemporaryDirectory() + "nativecmpkit-camera-"))
            if (NSFileManager.defaultManager.fileExistsAtPath(path)) assertTrue(NSFileManager.defaultManager.removeItemAtPath(path, null))
        }
        remove
    }
    cleanupPreserving(null, *actions.toTypedArray())
}

/** All cleanup attempts run; no teardown exception is allowed to replace the owning refusal. */
private fun cleanupPreserving(primary: Throwable?, vararg actions: () -> Unit) {
    var cleanup: Throwable? = null
    for (action in actions) try { action() } catch (error: Throwable) {
        val previous = cleanup
        if (previous == null) cleanup = error else if (previous !== error) previous.addSuppressed(error)
    }
    cleanup?.let { error -> if (primary == null) throw error else if (primary !== error) primary.addSuppressed(error) }
}
