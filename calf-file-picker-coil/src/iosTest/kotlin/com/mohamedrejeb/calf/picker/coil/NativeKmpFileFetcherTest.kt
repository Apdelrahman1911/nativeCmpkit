package com.mohamedrejeb.calf.picker.coil

import coil3.ImageLoader
import coil3.PlatformContext
import coil3.decode.DataSource
import coil3.decode.Decoder
import coil3.fetch.SourceFetchResult
import coil3.request.ErrorResult
import coil3.request.ImageRequest
import coil3.request.Options
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.io.readByteArray
import kotlinx.cinterop.BetaInteropApi
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.addressOf
import kotlinx.cinterop.alloc
import kotlinx.cinterop.memScoped
import kotlinx.cinterop.ptr
import kotlinx.cinterop.usePinned
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.awaitCancellation
import kotlinx.coroutines.cancel
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.runTest
import kotlinx.io.IOException
import platform.Foundation.NSData
import platform.Foundation.NSFileManager
import platform.Foundation.NSTemporaryDirectory
import platform.Foundation.NSURL
import platform.Foundation.NSUUID
import platform.Foundation.create
import platform.Foundation.writeToURL
import platform.posix.chmod
import platform.posix.fstat
import platform.posix.getdtablesize
import platform.posix.geteuid
import platform.posix.stat
import kotlin.test.AfterTest
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertIs
import kotlin.test.assertSame
import kotlin.test.assertTrue

/** Actual Coil/KmpFile/kotlinx-io/Okio stream and error pipeline on Native Foundation files. */
@OptIn(ExperimentalForeignApi::class, BetaInteropApi::class)
class NativeKmpFileFetcherTest {
    private val directory = "${NSTemporaryDirectory()}/nativecmpkit-coil-${NSUUID().UUIDString}"
    private val context = PlatformContext.INSTANCE

    init { check(NSFileManager.defaultManager.createDirectoryAtPath(directory, true, null, null)) }

    @AfterTest fun cleanup() {
        check(NSFileManager.defaultManager.removeItemAtPath(directory, null))
    }

    @Test fun realCoilStreamingSourceHasExactBytesAndOwnedDescriptor() = runTest {
        val bytes = ByteArray(300_000) { (it % 251).toByte() }
        val file = write("stream.bin", bytes)
        assertEquals(emptySet(), descriptors(file))
        val result = KmpFileFetcher(file, Options(context)).fetch() as SourceFetchResult
        assertEquals(DataSource.DISK, result.dataSource)
        try {
            assertEquals(1, descriptors(file).size)
            assertContentEquals(bytes, result.source.source().readByteArray())
        } finally { result.source.close() }
        assertEquals(emptySet(), descriptors(file))
    }

    @Test fun missingAndUnreadableFilesPropagateThroughActualCoilRequests() = runTest {
        check(geteuid() != 0u) { "Unreadable-file verification cannot use root's permission bypass" }
        val loader = ImageLoader.Builder(context).components { add(KmpFileFetcher.Factory()) }.build()
        val unreadable = write("unreadable.bin", byteArrayOf(3, 5))
        val path = checkNotNull(unreadable.url.path)
        check(chmod(path, 0u) == 0)
        try {
            val missing = KmpFile(NSURL.fileURLWithPath("$directory/missing.bin"))
            for (file in listOf(missing, unreadable)) {
                val result = assertIs<ErrorResult>(loader.execute(ImageRequest.Builder(context).data(file).build()))
                assertIs<IOException>(result.throwable, "The original native opening error must reach Coil")
            }
            assertEquals(emptySet(), descriptors(unreadable))
        } finally {
            check(chmod(path, 384u) == 0)
            loader.shutdown()
        }
        assertContentEquals(byteArrayOf(3, 5), unreadable.readByteArray())
    }

    @Test fun nonFileUrlsFailBeforeOpeningMatchingLocalContent() = runTest {
        val bytes = byteArrayOf(4, 0, -1)
        val file = write("local.bin", bytes)
        val nonFile = KmpFile(NSURL(string = "https://127.0.0.1:1${file.url.path}"))
        assertEquals(file.url.path, nonFile.url.path)
        assertFailsWith<IOException> { KmpFileFetcher(nonFile, Options(context)).fetch() }
        assertEquals(emptySet(), descriptors(file))
        assertContentEquals(bytes, file.readByteArray())
    }

    @Test fun cancelledFetchCannotOpenADescriptor() = runTest {
        val file = write("cancel.bin", byteArrayOf(6))
        var rejectionObserved = false
        val job = launch(start = CoroutineStart.UNDISPATCHED) {
            cancel()
            assertFailsWith<CancellationException> { KmpFileFetcher(file, Options(context)).fetch() }
            rejectionObserved = true
        }
        job.join()
        assertTrue(rejectionObserved, "The cancelled fetch actually ran and rejected before opening")
        assertEquals(emptySet(), descriptors(file))
    }

    @Test fun repeatedImageSourceCloseAndFetchReleaseRealNativeDescriptors() = runTest {
        val bytes = ByteArray(8_193) { it.toByte() }
        val file = write("repeat.bin", bytes)
        repeat(20) {
            val result = KmpFileFetcher(file, Options(context)).fetch() as SourceFetchResult
            try {
                assertEquals(1, descriptors(file).size)
                assertContentEquals(bytes, result.source.source().readByteArray())
            } finally { result.source.close() }
            result.source.close()
            assertEquals(emptySet(), descriptors(file), "Actual Coil stream leaked at iteration $it")
        }
    }

    @Test fun actualCoilDecoderCancellationClosesTransferredNativeSource() = runTest {
        val bytes = byteArrayOf(11, 0, -1)
        val file = write("decode-cancel.bin", bytes)
        val decoderEntered = CompletableDeferred<Unit>()
        val loader = ImageLoader.Builder(context).components { add(KmpFileFetcher.Factory()) }.build()
        val request = ImageRequest.Builder(context).data(file)
            .coroutineContext(StandardTestDispatcher(testScheduler))
            .decoderFactory(Decoder.Factory { result, _, _ ->
                assertEquals(DataSource.DISK, result.dataSource)
                Decoder {
                    // Consume only in decode(), after the real EngineInterceptor transfers
                    // its SourceFetchResult. No mocked fetcher or preemptive source close.
                    assertEquals(1, descriptors(file).size)
                    assertEquals(11, result.source.source().readByte().toInt())
                    decoderEntered.complete(Unit)
                    awaitCancellation()
                }
            }).build()
        var cancellationObserved = false
        val job = launch {
            try {
                loader.execute(request)
                error("The paused real decoder unexpectedly completed")
            } catch (cancelled: CancellationException) {
                cancellationObserved = true
                throw cancelled
            }
        }
        try {
            decoderEntered.await()
            assertEquals(1, descriptors(file).size, "Cancel after transfer while the actual file remains open")
            job.cancelAndJoin()
            assertTrue(cancellationObserved, "Coil execution actually propagated cancellation")
            assertEquals(emptySet(), descriptors(file), "Coil's finally must release its transferred source")
            assertContentEquals(bytes, file.readByteArray())
        } finally {
            job.cancelAndJoin()
            loader.shutdown()
        }
    }

    @Test fun actualCoilDecoderFailureClosesTransferredNativeSource() = runTest {
        val bytes = byteArrayOf(13, 0, -128)
        val file = write("decode-fail.bin", bytes)
        val failure = IOException("Owned decoder failure after actual Native stream read")
        val loader = ImageLoader.Builder(context).components { add(KmpFileFetcher.Factory()) }.build()
        val request = ImageRequest.Builder(context).data(file)
            .coroutineContext(StandardTestDispatcher(testScheduler))
            .decoderFactory(Decoder.Factory { result, _, _ ->
                assertEquals(DataSource.DISK, result.dataSource)
                Decoder {
                    assertEquals(1, descriptors(file).size)
                    assertEquals(13, result.source.source().readByte().toInt())
                    throw failure
                }
            }).build()
        try {
            val result = assertIs<ErrorResult>(loader.execute(request))
            assertSame(failure, result.throwable, "The actual decoder error must reach the real Coil request")
            assertEquals(emptySet(), descriptors(file), "Decoder failure must close, not orphan, the real source")
            assertContentEquals(bytes, file.readByteArray())
        } finally { loader.shutdown() }
    }

    private fun write(name: String, bytes: ByteArray): KmpFile {
        val url = NSURL.fileURLWithPath("$directory/$name")
        val data = bytes.usePinned { NSData.create(bytes = it.addressOf(0), length = bytes.size.toULong()) }
        check(data.writeToURL(url, atomically = true))
        return KmpFile(url)
    }

    private fun descriptors(file: KmpFile): Set<Int> = memScoped {
        val identity = alloc<stat>()
        check(stat(checkNotNull(file.url.path), identity.ptr) == 0)
        val limit = getdtablesize()
        check(limit in 1..65_536) { "Descriptor-table range unavailable; do not guess leak-probe coverage" }
        val observed = alloc<stat>()
        buildSet {
            for (fd in 0 until limit) {
                if (fstat(fd, observed.ptr) == 0 && observed.st_dev == identity.st_dev && observed.st_ino == identity.st_ino) add(fd)
            }
        }
    }
}
