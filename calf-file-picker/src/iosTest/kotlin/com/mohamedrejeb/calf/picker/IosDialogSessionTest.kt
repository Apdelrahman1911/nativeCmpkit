package com.mohamedrejeb.calf.picker

import kotlinx.coroutines.Job
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.async
import kotlinx.coroutines.test.runTest
import platform.UIKit.UIViewController
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

/** Tests the production native-session owner; UIKit sheet animations still need device tests. */
class IosDialogSessionTest {
    @Test fun allResultPathsShareOneTerminalClaim() {
        val session = IosDialogSession()
        assertTrue(session.claimResult())
        assertFalse(session.claimResult())
        session.finish()
        assertFalse(session.claimResult())
    }

    @Test fun ownerRejectsOverlapAndOldCompletionCannotEndANewSession() {
        val owner = IosDialogOwner()
        val old = owner.begin()
        assertFailsWith<IllegalStateException> { owner.begin() }
        owner.end(old)
        val next = owner.begin()
        owner.end(old)
        assertTrue(owner.current === next)
        owner.close()
        assertFalse(next.claimResult())
        assertNull(owner.current)
        assertFailsWith<IllegalStateException> { owner.begin() }
    }

    @Test fun cancellationCancelsProviderWorkAndCleansOwnershipOnlyOnce() {
        val owner = IosDialogOwner()
        val session = owner.begin()
        val job = Job()
        var cleaned = 0
        var detached = 0
        session.job = job
        session.cleanup = { cleaned++ }
        session.detachDelegate = { detached++ }
        owner.close()
        owner.close()
        session.finish()
        assertTrue(job.isCancelled)
        assertTrue(session.cancelled)
        assertEquals(1, cleaned)
        assertEquals(1, detached)
        assertFalse(session.claimResult())
    }

    @Test fun throwingCleanupDoesNotLeaveTheOwnerBusyOrRepeatCleanup() {
        val owner = IosDialogOwner()
        val session = owner.begin()
        var cleaned = 0
        session.cleanup = { cleaned++; error("cleanup failure") }
        assertFailsWith<IllegalStateException> { owner.end(session) }
        assertNull(owner.current)
        session.finish()
        assertEquals(1, cleaned)
        owner.end(owner.begin())
    }

    @Test fun disposalDuringPresentationKeepsNativeResourcesUntilDismissalCompletes() {
        val owner = IosDialogOwner()
        val session = owner.begin()
        val controller = UIViewController()
        val delegate = Any()
        val job = Job()
        var cleanups = 0
        var detached = 0
        var dismissals = 0
        var completeDismissal: (() -> Unit)? = null
        session.controller = controller
        session.retainedDelegate = delegate
        session.job = job
        session.cleanup = { cleanups++ }
        session.detachDelegate = { detached++ }
        session.beginPresentation { complete -> dismissals++; completeDismissal = complete }

        owner.close()
        assertTrue(job.isCancelled)
        assertFalse(session.claimResult())
        assertEquals(IosDialogPhase.Presenting, session.phase)
        assertEquals(0, dismissals)
        assertEquals(0, cleanups)
        assertEquals(0, detached)
        assertTrue(session.controller === controller)
        assertTrue(session.retainedDelegate === delegate)
        assertTrue(owner.current === session)

        session.presentationCompleted()
        assertEquals(IosDialogPhase.Dismissing, session.phase)
        assertEquals(1, dismissals)
        assertEquals(0, cleanups)
        assertEquals(0, detached)
        assertNotNull(completeDismissal).invoke()
        assertEquals(1, cleanups)
        assertEquals(1, detached)
        assertNull(session.controller)
        assertNull(session.retainedDelegate)
        assertNull(owner.current)
        session.presentationCompleted()
        session.dismissalCompleted()
        session.finish()
        assertEquals(1, cleanups)
    }

    @Test fun finishingAPresentedDialogDoesNotAdmitAnotherUntilNativeDismissal() {
        val owner = IosDialogOwner()
        val session = owner.begin()
        var completeDismissal: (() -> Unit)? = null
        session.beginPresentation { completeDismissal = it }
        session.presentationCompleted()
        assertTrue(session.claimResult())
        owner.end(session)
        assertFalse(session.cancelled)
        assertEquals(IosDialogPhase.Dismissing, session.phase)
        assertFailsWith<IllegalStateException> { owner.begin() }
        assertNotNull(completeDismissal).invoke()
        val next = owner.begin()
        session.dismissalCompleted()
        session.finish()
        assertTrue(owner.current === next)
        owner.close()
    }

    @Test fun dismissedSheetKeepsProviderOwnershipUntilProcessingFinishes() {
        val owner = IosDialogOwner()
        val session = owner.begin()
        var completeDismissal: (() -> Unit)? = null
        var cleaned = 0
        session.cleanup = { cleaned++ }
        session.beginPresentation { completeDismissal = it }
        session.presentationCompleted()
        assertTrue(session.claimResult())
        session.requestDismissal()
        assertNotNull(completeDismissal).invoke()
        assertEquals(IosDialogPhase.Dismissed, session.phase)
        assertEquals(0, cleaned)
        assertTrue(owner.current === session)
        owner.end(session)
        assertEquals(1, cleaned)
        assertNull(owner.current)
    }

    @Test fun aRejectedNativeCallCleansEvenWhenDisposalArrivedWhilePresenting() {
        val owner = IosDialogOwner()
        val session = owner.begin()
        var cleaned = 0
        var dismissed = 0
        session.cleanup = { cleaned++ }
        session.beginPresentation { dismissed++ }
        owner.close()
        session.presentationRejected()
        assertEquals(1, cleaned)
        assertEquals(0, dismissed)
        assertEquals(IosDialogPhase.Finished, session.phase)
        assertNull(owner.current)
        session.presentationRejected()
        session.presentationCompleted()
        assertEquals(1, cleaned)
    }

    @Test fun disposalDuringDismissalNeitherCleansEarlyNorRequestsItTwice() {
        val session = IosDialogSession()
        var cleaned = 0
        var dismissals = 0
        var completeDismissal: (() -> Unit)? = null
        session.cleanup = { cleaned++ }
        session.beginPresentation { dismissals++; completeDismissal = it }
        session.presentationCompleted()
        session.requestDismissal()
        session.cancel()
        session.cancel()
        assertEquals(1, dismissals)
        assertEquals(0, cleaned)
        assertFalse(session.claimResult())
        assertNotNull(completeDismissal).invoke()
        assertNotNull(completeDismissal).invoke()
        assertEquals(1, cleaned)
    }

    @Test fun anAdaptiveDismissalDuringPresentationIsAlsoANativeCompletion() {
        val session = IosDialogSession()
        var cleaned = 0
        var dismissals = 0
        session.cleanup = { cleaned++ }
        session.beginPresentation { dismissals++ }
        session.cancel()
        session.dismissalCompleted()
        assertEquals(IosDialogPhase.Finished, session.phase)
        assertEquals(1, cleaned)
        session.presentationCompleted()
        assertEquals(0, dismissals)
    }

    @Test fun awaitingFinishDoesNotReturnBeforeNativeCleanup() = runTest {
        val session = IosDialogSession()
        var completeDismissal: (() -> Unit)? = null
        var cleaned = false
        session.cleanup = { cleaned = true }
        session.beginPresentation { completeDismissal = it }
        session.presentationCompleted()
        session.finish()
        val waiter = async(start = CoroutineStart.UNDISPATCHED) { session.awaitFinished(); cleaned }
        assertFalse(waiter.isCompleted)
        assertNotNull(completeDismissal).invoke()
        assertTrue(waiter.await())
    }
}
