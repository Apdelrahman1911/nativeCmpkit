// Modified for NativeCmpKit (2026-10-29): shared screen job ownership/cancellation regressions.
package com.mohamedrejeb.calf.sample.utils

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.isActive
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext
import kotlinx.io.Buffer
import kotlinx.io.RawSource
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/** Controlled raw reads are deliberate: count exactly what happens after selection cancellation. */
@OptIn(ExperimentalCoroutinesApi::class)
class SampleStreamingOwnerTest {
    @Test fun reselectDuringAReadStopsTheOldSourceAndPublishesOnlyTheNewSelection() = runTest {
        val owner = SampleStreamingOwner(this)
        val published = mutableListOf<List<Long>>()
        val replacement = CountingSource(3)
        val old = CountingSource(SAMPLE_STREAM_CHUNK_SIZE * 100) { reads ->
            if (reads == 2) owner.replace(listOf(replacement), { it.consumeByteCount() }, published::add)
        }
        val oldJob = owner.replace(listOf(old), { it.consumeByteCount() }, published::add)
        advanceUntilIdle()
        assertTrue(oldJob.isCancelled)
        assertEquals(2, old.reads)
        assertTrue(old.closed)
        assertTrue(replacement.closed)
        assertEquals(listOf(listOf(3L)), published)
    }

    @Test fun clearingSelectionCancelsTheSourceAndCannotRestoreItsOldResult() = runTest {
        val owner = SampleStreamingOwner(this)
        val published = mutableListOf<List<Long>>()
        val old = CountingSource(SAMPLE_STREAM_CHUNK_SIZE * 100) { reads ->
            if (reads == 2) owner.replace(emptyList<CountingSource>(), { it.consumeByteCount() }, published::add)
        }
        val oldJob = owner.replace(listOf(old), { it.consumeByteCount() }, published::add)
        advanceUntilIdle()
        assertTrue(oldJob.isCancelled)
        assertEquals(2, old.reads)
        assertTrue(old.closed)
        assertEquals(listOf(emptyList<Long>()), published)
    }

    @Test fun cancellationClosesTheSourceAndDoesNotPublishPartialResults() = runTest {
        val owner = SampleStreamingOwner(this)
        var publications = 0
        val old = CountingSource(SAMPLE_STREAM_CHUNK_SIZE * 100) { reads -> if (reads == 2) owner.cancel() }
        val oldJob = owner.replace(listOf(old), { it.consumeByteCount() }, { publications++ })
        advanceUntilIdle()
        assertTrue(oldJob.isCancelled)
        assertTrue(old.closed)
        assertEquals(2, old.reads)
        assertEquals(0, publications)
    }

    @Test fun nonCancellableOldDecoderStillCannotOverwriteACompletedNewSelection() = runTest {
        val owner = SampleStreamingOwner(this)
        val released = CompletableDeferred<String>()
        val started = CompletableDeferred<Unit>()
        val published = mutableListOf<List<String>>()
        val oldJob = owner.replace(listOf("old"), {
            started.complete(Unit)
            withContext(NonCancellable) { released.await() }
        }, published::add)
        runCurrent()
        assertTrue(started.isCompleted)
        owner.replace(listOf("new"), { it }, published::add)
        runCurrent()
        assertEquals(listOf(listOf("new")), published)
        released.complete("late old result")
        advanceUntilIdle()
        assertTrue(oldJob.isCancelled)
        assertEquals(listOf(listOf("new")), published)
    }

    @Test fun postedWorkUsesItsImmutableInputSnapshotNotALaterMutableList() = runTest {
        val owner = SampleStreamingOwner(this)
        val inputs = mutableListOf("original")
        val published = mutableListOf<List<String>>()
        owner.replace(inputs, { it }, published::add)
        inputs[0] = "later mutation"
        advanceUntilIdle()
        assertEquals(listOf(listOf("original")), published)
    }

    @Test fun synchronousPublicationCanReenterWithoutCancellingOrClearingTheNewJob() = runTest {
        val scope = CoroutineScope(coroutineContext + UnconfinedTestDispatcher(testScheduler))
        val owner = SampleStreamingOwner(scope)
        val published = mutableListOf<List<String>>()
        val pending = CompletableDeferred<String>()
        owner.replace(listOf("first"), { it }, { result ->
            published += result
            owner.replace(listOf("second"), { pending.await() }, published::add)
        })
        assertEquals(listOf(listOf("first")), published)
        pending.complete("second")
        advanceUntilIdle()
        assertEquals(listOf(listOf("first"), listOf("second")), published)
        assertTrue(scope.isActive)
    }

    private class CountingSource(private var remaining: Long, private val afterRead: (Int) -> Unit = {}) : RawSource {
        var reads = 0
        var closed = false
        override fun readAtMostTo(sink: Buffer, byteCount: Long): Long {
            check(!closed)
            reads++
            if (remaining == 0L) return -1L
            val count = minOf(remaining, byteCount)
            sink.write(ByteArray(count.toInt()))
            remaining -= count
            afterRead(reads)
            return count
        }
        override fun close() { closed = true }
    }
}
