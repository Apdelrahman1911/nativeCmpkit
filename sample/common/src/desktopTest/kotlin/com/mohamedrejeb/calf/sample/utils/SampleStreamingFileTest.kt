// Modified for NativeCmpKit (2026-10-29): large real JVM input and bounded cancellation.
package com.mohamedrejeb.calf.sample.utils

import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.io.source
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import kotlinx.io.Buffer
import kotlinx.io.RawSource
import java.io.RandomAccessFile
import java.nio.file.Files
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFails
import kotlin.test.assertTrue

class SampleStreamingFileTest {
    @Test fun real64MiBFileStreamsBoundedRequestsAndClosesAtEof() = runBlocking {
        val path = Files.createTempFile("nativecmpkit-sample-stream-", ".bin")
        var ownedSource: RawSource? = null
        try {
            RandomAccessFile(path.toFile(), "rw").use { it.setLength(64L * 1024 * 1024) }
            val real = KmpFile(path.toFile()).source()
            ownedSource = real
            var closed = false
            var maxRequest = 0L
            val observed = object : RawSource {
                override fun readAtMostTo(sink: Buffer, byteCount: Long): Long {
                    maxRequest = maxOf(maxRequest, byteCount)
                    return real.readAtMostTo(sink, byteCount)
                }
                override fun close() { real.close(); closed = true }
            }
            assertEquals(64L * 1024 * 1024, observed.consumeByteCount())
            assertTrue(closed)
            assertTrue(maxRequest <= SAMPLE_STREAM_CHUNK_SIZE)
            assertFails { real.readAtMostTo(Buffer(), 1) }
            Unit // JUnit4 requires a void method; assertFails otherwise becomes its return value.
        } finally { ownedSource?.close(); Files.delete(path) }
    }

    @Test fun cancellationDuringAnOwnedBlockingReadStopsAtTheNextChunkAndClosesWithinOneSecond() = runBlocking {
        val path = Files.createTempFile("nativecmpkit-sample-cancel-", ".bin")
        val inRead = CountDownLatch(1)
        val releaseRead = CountDownLatch(1)
        var ownedSource: RawSource? = null
        try {
            RandomAccessFile(path.toFile(), "rw").use { it.setLength(64L * 1024 * 1024) }
            val real = KmpFile(path.toFile()).source()
            ownedSource = real
            val reads = AtomicInteger()
            var closed = false
            val observed = object : RawSource {
                override fun readAtMostTo(sink: Buffer, byteCount: Long): Long {
                    if (reads.incrementAndGet() == 2) {
                        inRead.countDown()
                        check(releaseRead.await(5, TimeUnit.SECONDS)) { "Owned read fixture was not released" }
                    }
                    return real.readAtMostTo(sink, byteCount)
                }
                override fun close() { real.close(); closed = true }
            }
            val job = launch(Dispatchers.IO) { observed.consumeByteCount() }
            try {
                assertTrue(inRead.await(5, TimeUnit.SECONDS), "A real publishing stream must reach the second read")
                val before = System.nanoTime()
                job.cancel()
                releaseRead.countDown()
                withTimeout(1_000) { job.join() }
                val elapsedMillis = (System.nanoTime() - before) / 1_000_000
                assertTrue(elapsedMillis < 1_000, "Cancellation took ${elapsedMillis}ms after the owned read was released")
                assertTrue(job.isCancelled)
                assertEquals(2, reads.get())
                assertTrue(closed)
                assertFails { real.readAtMostTo(Buffer(), 1) }
                println("NATIVECMPKIT_SAMPLE_STREAM cancellation_ms=$elapsedMillis reads=${reads.get()} closed=$closed")
            } finally {
                releaseRead.countDown()
                job.cancel()
                withTimeout(5_000) { job.join() }
            }
        } finally { releaseRead.countDown(); ownedSource?.close(); Files.delete(path) }
    }
}
