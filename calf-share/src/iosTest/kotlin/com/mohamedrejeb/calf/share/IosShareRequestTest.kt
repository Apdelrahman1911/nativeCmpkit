// Test-only NativeCmpKit Share barrier controls (2026-11-01); unexecuted proposal.
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class, com.mohamedrejeb.calf.core.InternalCalfApi::class)

package com.mohamedrejeb.calf.share

import com.mohamedrejeb.calf.share.internal.onApplicationMain
import platform.UIKit.UIActivityViewController
import kotlin.test.*

/**
 * Controlled production-Request transitions in the genuine library app. Empty lease lists and
 * captured callbacks count ownership releases, not real OS dismissal or security-scope success.
 * The companion native fixture independently uses real UIKit presentation/dismissal and files.
 */
class IosShareRequestTest {
    @Test fun preparedCancellationReleasesOnlyTheNeverPresentedRequestOnce() = onApplicationMain {
        val controller = UIActivityViewController(listOf("Never presented"), null)
        val request = IosShareOwner.Request(controller, emptyList())
        var notifications = 0
        request.onReleased = { notifications++ }
        controller.completionWithItemsHandler = { _, _, _, _ -> error("A cancelled callback must be detached") }
        request.dispose()
        request.dispose()
        request.release()
        assertEquals(IosShareRequestPhase.Released, request.phase)
        assertFalse(request.presentationCompletionObserved)
        assertFalse(request.dismissalCompletionObserved)
        assertNull(controller.completionWithItemsHandler)
        assertEquals(1, notifications)
    }

    @Test fun nilNativeLinksDuringControlledPresentationCannotReleaseOrDismissTheRequest() = onApplicationMain {
        val controller = UIActivityViewController(listOf("Controlled transition"), null)
        val request = IosShareOwner.Request(controller, emptyList())
        var notifications = 0
        var dismissals = 0
        var completeDismissal: (() -> Unit)? = null
        request.onReleased = { notifications++ }
        request.beginPresentation { completed -> dismissals++; completeDismissal = completed }
        assertNull(controller.presentingViewController, "The controlled native projection must actually be nil")
        request.dispose()
        assertEquals(IosShareRequestPhase.Presenting, request.phase)
        assertFalse(request.presentationCompletionObserved)
        assertEquals(0, dismissals)
        assertEquals(0, notifications)
        // Explicit controlled inputs only. These are not substitutes for the genuine UIKit fixture.
        request.presentationCompleted()
        assertEquals(IosShareRequestPhase.Dismissing, request.phase)
        assertTrue(request.presentationCompletionObserved)
        assertFalse(request.dismissalCompletionObserved)
        assertEquals(1, dismissals)
        assertEquals(0, notifications)
        assertNotNull(completeDismissal).invoke()
        assertTrue(request.dismissalCompletionObserved)
        assertEquals(IosShareRequestPhase.Released, request.phase)
        assertEquals(1, notifications)
    }

    @Test fun repeatedCancellationDuringDismissalCannotIssueOrCompleteCleanupTwice() = onApplicationMain {
        val controller = UIActivityViewController(listOf("Controlled dismissal"), null)
        val request = IosShareOwner.Request(controller, emptyList())
        var notifications = 0
        var dismissals = 0
        var completeDismissal: (() -> Unit)? = null
        request.onReleased = { notifications++ }
        request.beginPresentation { completed -> dismissals++; completeDismissal = completed }
        request.presentationCompleted()
        request.dispose()
        request.dispose()
        request.presentationCompleted()
        assertEquals(IosShareRequestPhase.Dismissing, request.phase)
        assertEquals(1, dismissals)
        assertEquals(0, notifications)
        val completed = assertNotNull(completeDismissal)
        completed()
        completed()
        request.dispose()
        request.release()
        assertEquals(IosShareRequestPhase.Released, request.phase)
        assertEquals(1, dismissals)
        assertEquals(1, notifications)
    }

    @Test fun releasedRequestIgnoresLateCompletionsAndThrowingOwnerNotificationCannotRepeatCleanup() = onApplicationMain {
        val controller = UIActivityViewController(listOf("Released transition"), null)
        val request = IosShareOwner.Request(controller, emptyList())
        var notifications = 0
        var dismissals = 0
        val primary = IllegalStateException("Intentional caught owner-notification fixture")
        request.onReleased = {
            notifications++
            assertEquals(IosShareRequestPhase.Released, request.phase)
            assertNull(controller.completionWithItemsHandler)
            throw primary
        }
        request.beginPresentation { dismissals++ }
        controller.completionWithItemsHandler = { _, _, _, _ -> Unit }
        assertSame(primary, assertFailsWith<IllegalStateException> { request.release() })
        request.presentationCompleted()
        request.dispose()
        request.release()
        assertEquals(IosShareRequestPhase.Released, request.phase)
        assertFalse(request.presentationCompletionObserved, "A released request ignores a stale presentation acknowledgement")
        assertFalse(request.dismissalCompletionObserved)
        assertEquals(0, dismissals)
        assertEquals(1, notifications)
        assertNull(controller.completionWithItemsHandler)
    }
}
