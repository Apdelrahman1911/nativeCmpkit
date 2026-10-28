package com.mohamedrejeb.calf.picker.platform

import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.async
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.runBlocking
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertSame
import kotlin.test.assertTrue

/** Actual coroutine/worker gates; counted handles are controlled, not live OS dialogs. */
class DialogHandleCancellationTest {
    @Test fun cancelledBeforeAllocationDoesNotCreateOrEnterUse() {
        val job = Job().apply { cancel() }
        var creates = 0
        var closes = 0
        var uses = 0
        assertFailsWith<CancellationException> {
            withActiveDialogHandle(job, { creates++; 7L }, { closes++ }) { uses++; "unwanted modal" }
        }
        assertEquals(0, creates)
        assertEquals(0, closes)
        assertEquals(0, uses)
    }

    @Test fun cancellationDuringRealWorkerCreationClosesOnceWithoutEnteringUse() = runBlocking {
        val entered = CountDownLatch(1)
        val release = CountDownLatch(1)
        val creates = AtomicInteger()
        val closes = AtomicInteger()
        val uses = AtomicInteger()
        val operation = async(Dispatchers.IO) {
            withActiveDialogHandle(currentCoroutineContext(), {
                creates.incrementAndGet()
                entered.countDown()
                check(release.await(10, TimeUnit.SECONDS)) { "Creation gate was not released" }
                8L
            }, {
                assertEquals(8L, it)
                closes.incrementAndGet()
            }) { uses.incrementAndGet(); "unwanted modal" }
        }
        try {
            assertTrue(entered.await(10, TimeUnit.SECONDS), "The real IO worker must enter synchronous creation")
            operation.cancel()
            release.countDown()
            assertFailsWith<CancellationException> { operation.await() }
            operation.join()
            assertEquals(1, creates.get())
            assertEquals(1, closes.get())
            assertEquals(0, uses.get(), "Cancelled creation must not subsequently enter native show")
        } finally {
            release.countDown()
            operation.cancelAndJoin()
        }
    }

    @Test fun cancellationDuringUseClosesAndRejectsTheUnclaimedResult() {
        val job = Job()
        var closes = 0
        var uses = 0
        assertFailsWith<CancellationException> {
            withActiveDialogHandle(job, { 9L }, { closes++ }) {
                uses++
                job.cancel()
                "result from a synchronous modal that outlived its owner"
            }
        }
        assertEquals(1, closes)
        assertEquals(1, uses)
    }

    @Test fun creationFailureNeverDestroysAnUnclaimedHandle() {
        val job = Job()
        val expected = IllegalStateException("native creation failed")
        var closes = 0
        var uses = 0
        try {
            assertSame(expected, assertFailsWith<IllegalStateException> {
                withActiveDialogHandle(job, { throw expected }, { closes++ }) { uses++ }
            })
            assertEquals(0, closes)
            assertEquals(0, uses)
        } finally { job.cancel() }
    }

    @Test fun activeAndFailedUseEachCloseTheClaimedHandleExactlyOnce() {
        val job = Job()
        var closes = 0
        var uses = 0
        val expected = IllegalStateException("native show failed")
        try {
            assertEquals("selected", withActiveDialogHandle(job, { 10L }, { closes++ }) { uses++; "selected" })
            assertSame(expected, assertFailsWith<IllegalStateException> {
                withActiveDialogHandle(job, { 11L }, { closes++ }) { uses++; throw expected }
            })
            assertEquals(2, closes)
            assertEquals(2, uses)
        } finally { job.cancel() }
    }
}
