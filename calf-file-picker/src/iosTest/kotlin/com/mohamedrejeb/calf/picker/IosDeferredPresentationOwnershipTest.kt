@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.picker

import com.mohamedrejeb.calf.picker.internal.*
import platform.Foundation.NSData
import platform.Foundation.NSFileManager
import platform.UIKit.UIDocumentPickerViewController
import platform.UIKit.UIViewController
import kotlin.test.*

/**
 * Deliberately holds the per-call scheduling boundary BEFORE a real UIKit export presentation.
 * The later call, completion, dismissal, weak native delegate and Foundation files are genuine.
 * This is not an OS-controlled refusal, provider selection or swipe-gesture simulation.
 */
class IosDeferredPresentationOwnershipTest {
    @Test fun deferredVoidPresentationKeepsCancelledExportAndWeakDelegateUntilActualNativeCompletion() =
        deferredPresentationFixture(throwAfterScheduling = false)

    @Test fun exceptionAfterQueuedPresentationCannotDeleteStagingBeforeActualNativeCompletion() =
        deferredPresentationFixture(throwAfterScheduling = true)

    private fun deferredPresentationFixture(throwAfterScheduling: Boolean) = runApplicationUiTest {
        setContent {}
        val source = assertNotNull(stageExportData(NSData(), "deferred-original.bin"))
        val staged = assertNotNull(stageExportFile(source, "deferred-export.bin"))
        val owner = IosDialogOwner()
        val session = onApplicationMain { owner.begin() }
        var cleanups = 0
        var detaches = 0
        var finishes = 0
        var request: (() -> Unit)? = null
        var invoked = false
        lateinit var parent: UIViewController
        lateinit var picker: UIDocumentPickerViewController
        val priorFinished = onApplicationMain { session.onFinished }
        var primary: Throwable? = null
        try {
            runOnIdle {
                parent = assertNotNull(requireOwnedApplicationWindow().rootViewController)
                picker = UIDocumentPickerViewController(forExportingURLs = listOf(staged), asCopy = true)
                val delegate = DocumentPickerDelegate({}, {}, session::dismissalCompleted)
                session.controller = picker
                session.retainedDelegate = delegate
                session.detachDelegate = { detaches++; delegate.close() }
                session.cleanup = { cleanups++; assertTrue(removeStaging(staged)) }
                session.onFinished = { finishes++; priorFinished() }
                delegate.attachTo(picker)
                val enqueue: (UIViewController, () -> Unit) -> Unit = { controller, completed ->
                    assertTrue(sameNativeObject(picker, controller))
                    assertNull(request)
                    request = {
                        assertFalse(invoked)
                        invoked = true
                        parent.presentViewController(controller, true, completed)
                    }
                    if (throwAfterScheduling) throw QueuedPresentationProbeFailure()
                }
                if (throwAfterScheduling) {
                    assertFailsWith<QueuedPresentationProbeFailure> { presentIosDialog(parent, session, enqueue) }
                } else {
                    presentIosDialog(parent, session, enqueue)
                }
                assertEquals(IosDialogPhase.Presenting, session.phase)
                assertFalse(session.presentationCompletionObserved)
                assertTrue(iosDialogHasNoPresentation(parent, picker), "The controlled scheduling boundary must actually have no synchronous native links")
                assertTrue(sameNativeObject(picker, session.controller))
                assertNotNull(picker.delegate, "The native weak delegate must remain owned before deferred admission")
                assertSame(delegate, session.retainedDelegate)
                assertSame(session, owner.current)
                assertFailsWith<IllegalStateException> { owner.begin() }
                if (!throwAfterScheduling) session.cancel()
                assertEquals(IosDialogPhase.Presenting, session.phase)
                assertEquals(0, cleanups)
                assertEquals(0, detaches)
                assertEquals(0, finishes)
                assertTrue(NSFileManager.defaultManager.fileExistsAtPath(staged.path!!))
                assertNotNull(request).invoke()
                request = null
            }
            waitForNative {
                session.presentationCompletionObserved && session.phase == IosDialogPhase.Finished &&
                    iosDialogHasNoPresentation(parent, picker)
            }
            runOnIdle {
                assertTrue(invoked)
                assertTrue(session.presentationCompletionObserved)
                assertEquals(1, cleanups)
                assertEquals(1, detaches)
                assertEquals(1, finishes)
                assertNull(picker.delegate)
                assertNull(session.controller)
                assertNull(session.retainedDelegate)
                assertNull(owner.current)
                assertFalse(NSFileManager.defaultManager.fileExistsAtPath(staged.path!!))
                assertTrue(NSFileManager.defaultManager.fileExistsAtPath(source.path!!))
                val next = owner.begin()
                session.presentationCompleted()
                session.dismissalCompleted()
                session.cancel()
                assertSame(next, owner.current, "Late old completions must not release a new generation")
                owner.end(next)
                assertEquals(1, cleanups)
                assertEquals(1, detaches)
                assertEquals(1, finishes)
            }
        } catch (failure: Throwable) {
            primary = failure
            throw failure
        } finally {
            try {
                onApplicationMain {
                    session.cancel()
                    // Only a still-owned queued request may be entered on assertion failure.
                    // A rejected/finished owner must never present a now-unowned native consumer.
                    if (!invoked && session.phase == IosDialogPhase.Presenting) {
                        request?.invoke()
                        request = null
                    }
                }
                waitForNative { session.phase == IosDialogPhase.Finished }
                onApplicationMain { owner.close() }
            } catch (cleanup: Throwable) {
                val prior = primary
                if (prior == null) throw cleanup else if (prior !== cleanup) prior.addSuppressed(cleanup)
            } finally {
                // Source is never handed to UIKit; export staging remains the session's owner.
                removeStaging(source)
            }
        }
    }

    private class QueuedPresentationProbeFailure : IllegalStateException("Intentional caught queued-native-call fixture")
}
