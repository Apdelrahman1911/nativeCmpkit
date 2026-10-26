package com.mohamedrejeb.calf.sample.utils

import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.runTest
import kotlinx.io.Buffer
import kotlinx.io.IOException
import kotlinx.io.RawSource
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class SampleStreamingTest {
    @Test
    fun countsBoundedChunksAndClosesTheSourceAtEof() = runTest {
        val source = CountingSource(SAMPLE_STREAM_CHUNK_SIZE * 2 + 3)
        assertEquals(SAMPLE_STREAM_CHUNK_SIZE * 2 + 3, source.consumeByteCount())
        assertTrue(source.closed)
        assertTrue(source.maxRequest <= SAMPLE_STREAM_CHUNK_SIZE)
        assertEquals(4, source.reads) // Three data reads and one EOF.
    }

    @Test
    fun emptySourceIsClosedAndReturnsZero() = runTest {
        val source = CountingSource(0)
        assertEquals(0L, source.consumeByteCount())
        assertTrue(source.closed)
    }

    @Test
    fun cancellationStopsBetweenChunksAndClosesInsteadOfReadingTheWholeSource() = runTest {
        lateinit var job: Job
        val source = CountingSource(SAMPLE_STREAM_CHUNK_SIZE * 100) { reads -> if (reads == 2) job.cancel() }
        job = launch(start = CoroutineStart.LAZY) { source.consumeByteCount() }
        job.start()
        job.join()
        assertTrue(job.isCancelled)
        assertTrue(source.closed)
        assertEquals(2, source.reads)
    }

    @Test
    fun noProgressAndReadFailureCloseTheSource() = runTest {
        for (throwOnRead in listOf(false, true)) {
            var closed = false
            val source = object : RawSource {
                override fun readAtMostTo(sink: Buffer, byteCount: Long): Long {
                    if (throwOnRead) throw IOException("read failure")
                    return 0
                }
                override fun close() { closed = true }
            }
            assertFailsWith<IOException> { source.consumeByteCount() }
            assertTrue(closed)
        }
    }

    private class CountingSource(private var remaining: Long, private val afterRead: (Int) -> Unit = {}) : RawSource {
        var closed = false
        var reads = 0
        var maxRequest = 0L
        override fun readAtMostTo(sink: Buffer, byteCount: Long): Long {
            check(!closed)
            reads++
            maxRequest = maxOf(maxRequest, byteCount)
            if (remaining == 0L) return -1
            val count = minOf(remaining, byteCount)
            sink.write(ByteArray(count.toInt()))
            remaining -= count
            afterRead(reads)
            return count
        }
        override fun close() { closed = true }
    }
}
