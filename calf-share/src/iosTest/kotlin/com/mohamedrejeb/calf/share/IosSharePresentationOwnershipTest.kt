// Test-only NativeCmpKit genuine Share presentation regressions (2026-11-01); unexecuted proposal.
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class, com.mohamedrejeb.calf.core.ExperimentalCalfApi::class,
    com.mohamedrejeb.calf.core.InternalCalfApi::class)

package com.mohamedrejeb.calf.share

import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.uikit.LocalUIViewController
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.share.internal.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.IO
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import platform.Foundation.NSData
import platform.Foundation.NSFileManager
import platform.Foundation.NSTemporaryDirectory
import platform.Foundation.NSThread
import platform.Foundation.NSURL
import platform.Foundation.NSUUID
import platform.UIKit.UIActivityViewController
import platform.UIKit.UIViewController
import kotlin.test.*

/**
 * Actual library UIApplication/Compose/ShareLauncher/UIActivityViewController and native animation
 * callbacks, never a sample app. Only the second method controls the per-call scheduling boundary;
 * its eventual native call/completions are still real. Activity results below are deliberate inputs
 * through the installed native completion block, not user/recipient success or OS cancellation.
 * Sandbox URLs acquire actual library scope objects, but a successful security-scope start is not
 * assumed: positive-start balancing and cross-process/delayed-recipient access need separate gates.
 */
class IosSharePresentationOwnershipTest {
    @Test fun realAnimatedShareDisposalWaitsForNativePresentationAndDismissalBeforeLeaseRelease() = runApplicationUiTest {
        disposalFixture(deferNativeCall = false, disposeAfterPresented = false)
    }

    @Test fun deferredNativeSharePresentationRetainsDisposedRequestWhileBothLinksAreNil() = runApplicationUiTest {
        disposalFixture(deferNativeCall = true, disposeAfterPresented = false)
    }

    @Test fun disposalAfterRealPresentationClosesOneRequestAndSuppressesLateActivityCompletion() = runApplicationUiTest {
        disposalFixture(deferNativeCall = false, disposeAfterPresented = true)
    }

    @Test fun disposedPublicShareLaunchersCalledFromDefaultAndIoCannotRestartNativeWork() = runApplicationUiTest {
        setContent {}
        lateinit var parent: UIViewController
        lateinit var owner: IosShareOwner
        lateinit var launcher: ShareLauncher
        val deliveries = mutableListOf<ShareOutcome>()
        runOnIdle {
            parent = assertNotNull(requireOwnedApplicationWindow().rootViewController)
            owner = IosShareOwner(parent) { deliveries += it }
            retainIosShareOwner(owner)
            launcher = ShareLauncher(owner::launch)
            owner.dispose()
            launcher.launch(ShareContent.Text("Disposed on main"))
        }
        // The library queues these calls to UIKit's actual main queue. The owner was disposed
        // before dispatch; no synthetic dispatcher/global hook or manually assigned phase.
        for (dispatcher in listOf(Dispatchers.Default, Dispatchers.IO)) {
            runBlocking {
                withContext(dispatcher) {
                    assertFalse(NSThread.isMainThread)
                    launcher.launch(ShareContent.Text("Disposed before queued launch"))
                }
            }
            // dispatch_sync in the owned host is FIFO after the library's main-queue enqueue.
            onApplicationMain {
                assertNull(owner.currentRequest)
                assertNull(parent.presentedViewController)
                assertTrue(deliveries.isEmpty())
            }
        }
    }

    @Test fun publicRememberedShareMainDefaultIoReentryAndDisposalUseCurrentCallbacks() = runApplicationUiTest {
        verifyControlledIosShareTerminalBarriers()
        val visible = mutableStateOf(true)
        val callbackVersion = mutableStateOf(0)
        val deliveries = mutableListOf<Pair<Int, ShareOutcome>>()
        var allCallbacksOnMain = true
        var reenter = false
        lateinit var parent: UIViewController
        lateinit var launcher: ShareLauncher
        setContent {
            if (visible.value) {
                parent = LocalUIViewController.current
                val version = callbackVersion.value
                val current = rememberShareOutcomeLauncher { outcome ->
                    allCallbacksOnMain = allCallbacksOnMain && NSThread.isMainThread
                    deliveries += version to outcome
                    if (reenter && outcome == ShareOutcome.Completed) {
                        reenter = false
                        // The old request must already have released ownership before application code.
                        launcher.launch(ShareContent.Text("Reentered from the current result callback"))
                    }
                }
                SideEffect { launcher = current }
            }
        }
        val retained = runOnIdle { launcher.also { retainIosShareOwner(assertNotNull(it.currentIosOwner)) } }
        var lateOriginal: (() -> Unit)? = null
        var original: UIActivityViewController? = null
        for (index in 0..2) {
            if (index == 0) runOnIdle { retained.launch(ShareContent.Text("Main-thread fixture")) }
            else runBlocking {
                withContext(if (index == 1) Dispatchers.Default else Dispatchers.IO) {
                    assertFalse(NSThread.isMainThread)
                    retained.launch(ShareContent.Text("Background-dispatched fixture"))
                }
            }
            waitForNative {
                val native = parent.presentedViewController
                val active = retained.currentIosOwner?.currentRequest
                native is UIActivityViewController && !native.isBeingPresented() && native.view.window != null &&
                    active?.presentationCompletionObserved == true && active.phase == IosShareRequestPhase.Presented
            }
            val native = onApplicationMain { assertIs<UIActivityViewController>(parent.presentedViewController) }
            val request = onApplicationMain {
                assertNotNull(assertNotNull(retained.currentIosOwner).currentRequest).also {
                    assertTrue(sameNativeObject(native, it.controller))
                    assertEquals(IosShareRequestPhase.Presented, it.phase)
                }
            }
            runOnIdle {
                assertSame(retained, launcher)
                callbackVersion.value = index + 1
                reenter = index == 2
            }
            waitForIdle()
            onApplicationMain {
                val completed = assertNotNull(native.completionWithItemsHandler)
                lateOriginal = { completed(null, true, null, null) }
                original = native
                // Deliver the deliberately controlled FIRST activity terminal input while
                // presented, not after programmatic dismissal has already cancelled sharing.
                // Production must perform/acknowledge its own genuine UIKit dismissal before
                // releasing ownership or notifying this remembered callback. No recipient/OS
                // success, manual phase assignment or test-owned native dismissal is inferred.
                completed(null, true, null, null)
                completed(null, true, null, null)
            }
            waitForNative {
                deliveries.size == index + 1 && if (index == 2) {
                    val next = parent.presentedViewController
                    next is UIActivityViewController && !sameNativeObject(next, native) && !next.isBeingPresented()
                } else parent.presentedViewController == null
            }
            runOnIdle {
                assertSame(retained, launcher)
                assertTrue(allCallbacksOnMain)
                assertTrue(request.presentationCompletionObserved)
                assertTrue(request.dismissalCompletionObserved, "An activity input is not a native dismissal barrier")
                assertEquals(IosShareRequestPhase.Released, request.phase)
                assertTrue(hasNoOwnedNativePresentation(parent, native))
                assertEquals<List<Pair<Int, ShareOutcome>>>((1..index + 1).map { it to ShareOutcome.Completed }, deliveries)
                assertNotNull(lateOriginal).invoke()
                assertEquals(index + 1, deliveries.size, "An old native block cannot deliver or clear a new generation")
                if (index == 2) {
                    assertFalse(sameNativeObject(parent.presentedViewController, original))
                }
            }
        }
        val replacement = onApplicationMain { assertIs<UIActivityViewController>(parent.presentedViewController) }
        val lateReplacement = onApplicationMain {
            val callback = assertNotNull(replacement.completionWithItemsHandler)
            val deliver: () -> Unit = { callback(null, false, null, null) }
            deliver
        }
        runOnIdle { visible.value = false }
        waitForIdle() // Actual DisposableEffect must dispose the remembered library owner.
        waitForNative { hasNoOwnedNativePresentation(parent, replacement) }
        onApplicationMain {
            assertNull(replacement.completionWithItemsHandler)
            lateReplacement()
            lateReplacement()
            assertNotNull(lateOriginal).invoke()
            retained.launch(ShareContent.Text("Retained launcher after real composition disposal"))
            assertNull(parent.presentedViewController)
            assertEquals<List<Pair<Int, ShareOutcome>>>((1..3).map { it to ShareOutcome.Completed }, deliveries)
            assertTrue(allCallbacksOnMain)
        }
    }

    private fun NativeApplicationUiTest.disposalFixture(deferNativeCall: Boolean, disposeAfterPresented: Boolean) {
        setContent {}
        val file = OwnedShareFile()
        var owner: IosShareOwner? = null
        var request: IosShareOwner.Request? = null
        var parent: UIViewController? = null
        var native: UIActivityViewController? = null
        var pendingPresentation: (() -> Unit)? = null
        var lateActivityCallback: (() -> Unit)? = null
        var nativeCalls = 0
        var nativePresentationCompletions = 0
        var presentationCallbackOnMain = true
        var presentationCallbackHadOwnLinks = false
        var releases = 0
        var releaseOnMain = true
        var releaseAfterDismissalCompletion = false
        var releasedNativeWasAbsent = false
        val deliveries = mutableListOf<ShareOutcome>()
        var primary: Throwable? = null
        try {
            runOnIdle {
                val presenter = assertNotNull(requireOwnedApplicationWindow().rootViewController)
                parent = presenter
                val owning = IosShareOwner(presenter) { deliveries += it }
                owner = owning
                retainIosShareOwner(owning)
                val present: (UIActivityViewController, () -> Unit) -> Unit = { controller, completed ->
                    // Capture the actual active Request before this per-call boundary can throw.
                    retainIosShareOwner(owning)
                    val enterNative = {
                        nativeCalls++
                        presenter.presentViewController(controller, true) {
                            nativePresentationCompletions++
                            presentationCallbackOnMain = presentationCallbackOnMain && NSThread.isMainThread
                            presentationCallbackHadOwnLinks = !hasNoOwnedNativePresentation(presenter, controller)
                            completed() // Forward the actual UIKit completion to the owning Request.
                        }
                    }
                    if (deferNativeCall) {
                        assertNull(pendingPresentation)
                        pendingPresentation = enterNative
                    } else enterNative()
                }
                val launcher = ShareLauncher { content -> owning.launch(content, present) }
                launcher.launch(ShareContent.File(file.file, "application/octet-stream"))
                val held = assertNotNull(owning.currentRequest)
                request = held
                native = held.controller
                assertEquals(1, held.leases.size, "Exercise the real library file-scope acquisition path")
                val notifyOwner = held.onReleased
                held.onReleased = {
                    releases++
                    releaseOnMain = releaseOnMain && NSThread.isMainThread
                    releaseAfterDismissalCompletion = held.dismissalCompletionObserved
                    releasedNativeWasAbsent = hasNoOwnedNativePresentation(presenter, held.controller)
                    notifyOwner()
                }
                val callback = assertNotNull(held.controller.completionWithItemsHandler)
                lateActivityCallback = { callback(null, true, null, null) }
                if (!disposeAfterPresented) {
                    assertEquals(IosShareRequestPhase.Presenting, held.phase)
                    assertFalse(held.presentationCompletionObserved, "Disposal must precede real UIKit presentation completion")
                    assertEquals(0, nativePresentationCompletions)
                    if (deferNativeCall) {
                        assertEquals(0, nativeCalls)
                        assertTrue(hasNoOwnedNativePresentation(presenter, held.controller),
                            "Both native links/transition projections must actually be absent at this controlled gap")
                    } else {
                        assertEquals(1, nativeCalls)
                        // UIKit may legitimately return before either native link is installed.
                        // The actual call/zero-completion gap and later matching native completion
                        // establish this regression; immediate attachment is not an admission gate.
                    }
                    owning.dispose()
                    owning.dispose()
                    assertSame(held, owning.currentRequest)
                    assertEquals(IosShareRequestPhase.Presenting, held.phase)
                    assertEquals(0, releases)
                    assertNull(held.controller.completionWithItemsHandler)
                    assertTrue(file.exists())
                    assertNotNull(lateActivityCallback).invoke()
                    assertTrue(deliveries.isEmpty())
                    if (deferNativeCall) {
                        assertNotNull(pendingPresentation).invoke()
                        pendingPresentation = null
                    }
                }
            }
            val held = assertNotNull(request)
            val owning = assertNotNull(owner)
            if (disposeAfterPresented) {
                waitForNative { held.presentationCompletionObserved && held.phase == IosShareRequestPhase.Presented }
                runOnIdle {
                    assertEquals(1, nativePresentationCompletions)
                    assertTrue(presentationCallbackHadOwnLinks)
                    assertEquals(0, releases)
                    owning.dispose()
                    owning.dispose()
                    assertNotNull(lateActivityCallback).invoke()
                    assertTrue(deliveries.isEmpty())
                }
            }
            waitForNative {
                held.presentationCompletionObserved && held.dismissalCompletionObserved &&
                    held.phase == IosShareRequestPhase.Released && owning.currentRequest == null &&
                    hasNoOwnedNativePresentation(assertNotNull(parent), assertNotNull(native))
            }
            runOnIdle {
                assertEquals(1, nativeCalls)
                assertEquals(1, nativePresentationCompletions)
                assertTrue(presentationCallbackOnMain)
                assertTrue(presentationCallbackHadOwnLinks, "Native presentation completion must witness this controller, not two nil objects")
                assertTrue(held.dismissalCompletionObserved, "The real native dismissal acknowledgement, not elapsed time, owns cleanup")
                assertTrue(releaseAfterDismissalCompletion)
                assertTrue(releasedNativeWasAbsent)
                assertTrue(releaseOnMain)
                assertEquals(1, releases)
                assertNull(owning.currentRequest)
                assertNull(held.controller.completionWithItemsHandler)
                assertTrue(file.exists(), "The launcher owns scopes, not deletion of the caller's file")
                assertNotNull(lateActivityCallback).invoke()
                // Late/duplicate controls only AFTER the real native barrier has independently passed.
                held.presentationCompleted()
                held.dispose()
                held.release()
                owning.dispose()
                owning.launch(ShareContent.Text("Disposed owner must stay inert"))
                assertEquals(1, releases)
                assertTrue(deliveries.isEmpty())
                assertNull(assertNotNull(parent).presentedViewController)
            }
        } catch (failure: Throwable) {
            primary = failure
            throw failure
        } finally {
            try {
                onApplicationMain {
                    owner?.dispose()
                    // Failure cleanup may enter only this still-owned deferred native call. Never
                    // present a released request or delete a file during an unacknowledged transition.
                    if (request?.phase == IosShareRequestPhase.Presenting && pendingPresentation != null) {
                        pendingPresentation?.invoke()
                        pendingPresentation = null
                    }
                }
                request?.let { held -> waitForNative { held.phase == IosShareRequestPhase.Released } }
                // A null local capture after a throwing launch is not absence of owner/native work.
                owner?.let { owning -> awaitOwnedIosShareRelease(owning) }
                file.close()
            } catch (cleanup: Throwable) {
                val prior = primary
                if (prior == null) throw cleanup else if (prior !== cleanup) prior.addSuppressed(cleanup)
            }
        }
    }
}

/** Both native directions/flags, observed only on main with retained objects; never two nil == owner. */
private fun hasNoOwnedNativePresentation(presenter: UIViewController, controller: UIViewController): Boolean {
    check(NSThread.isMainThread)
    if (controller.presentingViewController != null || controller.isBeingPresented() || controller.isBeingDismissed()) return false
    var ancestor: UIViewController? = presenter
    while (ancestor != null) {
        if (sameNativeObject(ancestor.presentedViewController, controller)) return false
        ancestor = ancestor.parentViewController
    }
    return true
}

/** This fixture owns only its new sandbox directory; no bookmark grant or source-file lifetime claim. */
private class OwnedShareFile {
    private val directory = "${NSTemporaryDirectory().removeSuffix("/")}/nativecmpkit-share-${NSUUID().UUIDString}"
    private val path = "$directory/barrier-fixture.bin"
    val file = KmpFile(NSURL.fileURLWithPath(path))
    init {
        check(!NSFileManager.defaultManager.fileExistsAtPath(directory))
        check(NSFileManager.defaultManager.createDirectoryAtPath(directory, true, null, null))
        check(NSFileManager.defaultManager.createFileAtPath(path, NSData(), null))
    }
    fun exists(): Boolean = NSFileManager.defaultManager.fileExistsAtPath(path)
    fun close() {
        check(NSFileManager.defaultManager.removeItemAtPath(directory, null))
        check(!NSFileManager.defaultManager.fileExistsAtPath(directory))
    }
}
