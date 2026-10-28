package com.mohamedrejeb.calf.picker.coil

import coil3.ImageLoader
import coil3.PlatformContext
import coil3.request.ErrorResult
import coil3.request.ImageRequest
import coil3.request.Options
import coil3.request.SuccessResult
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.io.readByteArray
import kotlinx.browser.window
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.async
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.runTest
import kotlinx.io.IOException
import org.w3c.dom.events.Event
import org.w3c.files.File
import org.w3c.files.FileReader
import kotlin.coroutines.resume
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

internal expect fun browserCoilFile(name: String, size: Int): File

/**
 * Wraps only the constructor/read boundary, forwarding to actual browser FileReader objects.
 * Empty failureName performs a real read. A named failure injects a DOMException/error event
 * after starting the real read; it is NOT a revoked OS permission or an inaccessible OS file.
 */
internal expect class BrowserReaderProbe(failureName: String) {
    val createdCount: Int
    val readCount: Int
    val lastReader: FileReader?
    fun close()
}

/** Real public IO/Coil/browser objects and coroutine cancellation, not a sample or fake fetcher. */
class BrowserFileReadCoilAcceptanceTest {
    private val context = PlatformContext.INSTANCE

    @Test fun publicEmptyAndAllByteValuesCompleteOnceDespiteLateLoadAndAbort() = runTest {
        val probe = BrowserReaderProbe("")
        try {
            for (size in listOf(0, 65_537)) {
                val read = async(start = CoroutineStart.UNDISPATCHED) {
                    KmpFile(browserCoilFile("binary.bin", size)).readByteArray()
                }
                val reader = assertNotNull(probe.lastReader)
                assertEquals(FileReader.LOADING, reader.readyState)
                val lateLoad = assertNotNull(reader.onload)
                val lateAbort = assertNotNull(reader.onabort)
                val expected = ByteArray(size) { it.toByte() }
                assertContentEquals(expected, read.await())
                assertDetached(reader)
                // Invoke the actual captured Kotlin listeners after their owner finished.
                lateLoad(Event("load"))
                lateAbort(Event("abort"))
                reader.abort()
                assertContentEquals(expected, read.await())
                assertDetached(reader)
            }
            assertEquals(2, probe.createdCount)
            assertEquals(2, probe.readCount)
        } finally { probe.close() }
    }

    @Test fun disposingActualCoilRequestDuringLargeReadAbortsAndDetachesTheRealReader() = runTest {
        val probe = BrowserReaderProbe("")
        val loader = ImageLoader.Builder(context).components { add(KmpFileFetcher.Factory()) }.build()
        var cancelled = 0
        var terminal = 0
        val cancellation = CompletableDeferred<Unit>()
        val request = ImageRequest.Builder(context).data(KmpFile(browserCoilFile("large.bin", 8 * 1024 * 1024)))
            .coroutineContext(StandardTestDispatcher(testScheduler))
            .listener(object : ImageRequest.Listener {
                override fun onCancel(request: ImageRequest) { cancelled++; cancellation.complete(Unit) }
                override fun onError(request: ImageRequest, result: ErrorResult) { terminal++ }
                override fun onSuccess(request: ImageRequest, result: SuccessResult) { terminal++ }
            }).build()
        val operation = loader.enqueue(request)
        try {
            testScheduler.runCurrent()
            val reader = awaitReader(probe)
            assertEquals(FileReader.LOADING, reader.readyState, "Dispose during read, not before fetch or after decoding")
            assertNotNull(reader.onload)
            operation.dispose()
            operation.job.join()
            cancellation.await()
            assertTrue(operation.isDisposed)
            assertEquals(1, cancelled)
            assertEquals(0, terminal)
            assertEquals(1, probe.createdCount)
            assertEquals(1, probe.readCount)
            assertTrue(reader.readyState != FileReader.LOADING, "The real native read must stop")
            assertDetached(reader)
            browserTask()
            assertEquals(1, cancelled)
            assertEquals(0, terminal, "Late native events must not publish an obsolete result")
        } finally {
            operation.dispose()
            operation.job.join()
            loader.shutdown()
            probe.close()
        }
    }

    @Test fun actualCoilNotReadableAndSecurityErrorsKeepOnlyTheNameAndCannotCompleteTwice() = runTest {
        for (name in listOf("NotReadableError", "SecurityError")) {
            val probe = BrowserReaderProbe(name)
            val loader = ImageLoader.Builder(context).components { add(KmpFileFetcher.Factory()) }.build()
            var failures = 0
            var successes = 0
            val request = ImageRequest.Builder(context).data(KmpFile(browserCoilFile("error.bin", 65_537)))
                .coroutineContext(StandardTestDispatcher(testScheduler))
                .listener(object : ImageRequest.Listener {
                    override fun onError(request: ImageRequest, result: ErrorResult) { failures++ }
                    override fun onSuccess(request: ImageRequest, result: SuccessResult) { successes++ }
                }).build()
            try {
                val result = assertIs<ErrorResult>(loader.execute(request))
                assertEquals("Browser file read failed: $name", assertIs<IOException>(result.throwable).message)
                val reader = assertNotNull(probe.lastReader)
                assertEquals(1, failures)
                assertEquals(0, successes)
                assertDetached(reader)
                reader.abort() // A synthetic error alone does not stop the actual browser read.
                reader.dispatchEvent(Event("load"))
                reader.dispatchEvent(Event("abort"))
                browserTask()
                assertEquals(1, failures)
                assertEquals(0, successes)
                assertDetached(reader)
            } finally {
                loader.shutdown()
                probe.close()
            }
        }
    }

    @Test fun browserCapRefusesThePublicFetcherBeforeCreatingAnyReader() = runTest {
        val probe = BrowserReaderProbe("")
        try {
            val file = KmpFile(browserCoilFile("oversized.bin", 1_025))
            val failure = kotlin.test.assertFailsWith<IOException> { KmpFileFetcher(file, Options(context), 1_024).fetch() }
            assertEquals("Browser image exceeds the 1024 byte in-memory limit", failure.message)
            assertEquals(0, probe.createdCount)
            assertEquals(0, probe.readCount)
            assertNull(probe.lastReader)
        } finally { probe.close() }
    }

    private suspend fun awaitReader(probe: BrowserReaderProbe): FileReader {
        repeat(100) {
            probe.lastReader?.let { return it }
            browserTask() // Actual browser tasks, not a virtual-time readiness delay.
        }
        error("Actual Coil never created its real FileReader; no zero-read/fake-fetcher substitute")
    }

    private suspend fun browserTask(): Unit = suspendCancellableCoroutine { continuation ->
        val timer = window.setTimeout({ if (continuation.isActive) continuation.resume(Unit); null }, 0)
        continuation.invokeOnCancellation { window.clearTimeout(timer) }
    }

    private fun assertDetached(reader: FileReader) {
        assertNull(reader.onload)
        assertNull(reader.onerror)
        assertNull(reader.onabort)
    }
}
