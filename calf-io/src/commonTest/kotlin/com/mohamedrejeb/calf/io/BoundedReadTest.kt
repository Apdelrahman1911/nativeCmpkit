package com.mohamedrejeb.calf.io

import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.runTest
import kotlinx.io.Buffer
import kotlinx.io.IOException
import kotlinx.io.RawSource
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class BoundedReadTest {
    @Test fun validatesNativeAllocationLengthWithoutAllocating() {
        assertEquals(0, checkedByteArraySize(0u))
        assertEquals(Int.MAX_VALUE, checkedByteArraySize(Int.MAX_VALUE.toULong()))
        assertFailsWith<IOException> { checkedByteArraySize(Int.MAX_VALUE.toULong() + 1u) }
        assertFailsWith<IOException> { checkedByteArraySize(ULong.MAX_VALUE) }
    }

    @Test fun emptyAndExactlyAtLimitAreNotTruncated() = runTest {
        assertContentEquals(byteArrayOf(), Buffer().readBounded(0))
        val bytes = byteArrayOf(0, 1, -1, 42)
        assertContentEquals(bytes, Buffer().apply { write(bytes) }.readBounded(4))
    }

    @Test fun exceedingLimitFailsAndCloses() = runTest {
        val source = RecordingSource(Buffer().apply { write(byteArrayOf(1, 2)) })
        assertFailsWith<IOException> { source.readBounded(1) }
        assertEquals(1, source.closes)
    }

    @Test fun failedReadClosesAndPreservesFailure() = runTest {
        val failure = IOException("read failed")
        val source = RecordingSource(Buffer(), failure)
        assertEquals(failure, assertFailsWith<IOException> { source.readBounded(5) })
        assertEquals(1, source.closes)
    }

    @Test fun cancellationBetweenChunksCloses() = runTest {
        val source = RecordingSource(Buffer().apply { write(ByteArray(200_000)) })
        val job = launch(start = CoroutineStart.UNDISPATCHED) { source.readBounded(200_000) }
        job.cancel()
        job.join()
        assertTrue(job.isCancelled)
        assertEquals(1, source.closes)
    }

    private class RecordingSource(private val buffer: Buffer, private val failure: IOException? = null) : RawSource {
        var closes = 0
        override fun readAtMostTo(sink: Buffer, byteCount: Long): Long {
            failure?.let { throw it }
            return buffer.readAtMostTo(sink, byteCount)
        }
        override fun close() { closes++; buffer.close() }
    }
}
