package com.mohamedrejeb.calf.picker.coil

import coil3.decode.DataSource
import coil3.decode.ImageSource
import coil3.fetch.SourceFetchResult
import coil3.request.Options
import com.mohamedrejeb.calf.io.KmpFile
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.runBlocking
import kotlinx.io.Buffer as KioBuffer
import kotlinx.io.IOException
import kotlinx.io.RawSource
import okio.Buffer as OkioBuffer
import okio.BufferedSource
import okio.FileSystem
import java.io.File
import java.nio.file.Files
import kotlin.test.AfterTest
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

private const val STREAM_SIZE = 100_003
private const val EXPECTED_READ_BUFFER = 8 * 1024

class KmpFileFetcherStreamingTest {

    private val content = ByteArray(STREAM_SIZE) { index -> (index % 251).toByte() }

    private val file: File = Files.createTempFile("nativecmpkit-coil-streaming", ".bin")
        .toFile()
        .apply { writeBytes(content) }

    @AfterTest
    fun cleanUp() {
        file.delete()
    }

    private fun fetcher(
        rawSource: RawSource,
        onOpen: () -> Unit = {},
        wrap: (BufferedSource) -> ImageSource = { ImageSource(it, FileSystem.SYSTEM) },
    ) = KmpFileFetcher(
        file = KmpFile(file),
        options = Options(coil3.PlatformContext.INSTANCE),
        openSource = { _, _ ->
            onOpen()
            rawSource
        },
        wrapSource = wrap,
    )

    @Test
    fun `fetch streams a real desktop file with binary parity and stable classification`() = runBlocking {
        val result = KmpFileFetcher(
            file = KmpFile(file),
            options = Options(coil3.PlatformContext.INSTANCE),
        ).fetch() as SourceFetchResult

        assertEquals(DataSource.MEMORY, result.dataSource)
        assertNull(result.mimeType)

        val actual = result.source.source().use { it.readByteArray() }

        assertContentEquals(content, actual)
    }

    @Test
    fun `successful fetch opens once and lets ImageSource close the owned source once`() = runBlocking {
        var opens = 0
        val rawSource = ByteArrayRawSource(content)

        val result = fetcher(rawSource, onOpen = { opens++ }).fetch() as SourceFetchResult

        assertEquals(1, opens)
        assertEquals(0, rawSource.closeCalls)

        val actual = result.source.source().use { it.readByteArray() }
        assertContentEquals(content, actual)
        assertEquals(1, rawSource.closeCalls)

        result.source.close()
        assertEquals(1, rawSource.closeCalls)
    }

    @Test
    fun `result construction failure closes the opened source and preserves the failure`() = runBlocking {
        val rawSource = ByteArrayRawSource(content)
        val failure = IllegalStateException("wrap failed")

        val actual = assertFailsWith<IllegalStateException> {
            fetcher(rawSource, wrap = { throw failure }).fetch()
        }

        assertSame(failure, actual)
        assertEquals(1, rawSource.closeCalls)
        assertEquals(0, rawSource.readCalls)
    }

    @Test
    fun `cleanup failure is suppressed on the original fetch failure`() = runBlocking {
        val rawSource = ThrowingCloseRawSource()
        val failure = IllegalStateException("wrap failed")

        val actual = assertFailsWith<IllegalStateException> {
            fetcher(
                rawSource,
                wrap = {
                    throw failure
                },
            ).fetch()
        }

        assertSame(failure, actual)
        assertEquals(1, actual.suppressed.size)
        assertEquals("close failed", actual.suppressed.single().message)
        assertEquals(1, rawSource.closeCalls)
    }

    @Test
    fun `cancellation after opening closes the source`() = runBlocking {
        val rawSource = ByteArrayRawSource(content)
        val cancellation = CancellationException("cancelled")

        val actual = assertFailsWith<CancellationException> {
            fetcher(rawSource, wrap = { throw cancellation }).fetch()
        }

        assertSame(cancellation, actual)
        assertEquals(1, rawSource.closeCalls)
    }

    @Test
    fun `adapter bounds each read to eight kilobytes and preserves every byte`() {
        val rawSource = ByteArrayRawSource(content)
        val source = KmpFileOkioSource(rawSource)
        val sink = OkioBuffer()
        var reads = 0

        try {
            while (true) {
                val read = source.read(sink, 100_000L)
                if (read == -1L) break
                assertTrue(read >= 1L && read <= EXPECTED_READ_BUFFER.toLong(), "unexpected read: $read")
                reads++
            }
        } finally {
            source.close()
        }

        assertEquals((STREAM_SIZE + EXPECTED_READ_BUFFER - 1) / EXPECTED_READ_BUFFER, reads)
        assertTrue(rawSource.maxRequested <= EXPECTED_READ_BUFFER.toLong())
        assertContentEquals(content, sink.readByteArray())
    }

    @Test
    fun `zero byte request returns zero without reading and negative byte count is refused`() {
        val rawSource = ByteArrayRawSource(content)
        val source = KmpFileOkioSource(rawSource)
        try {
            assertEquals(0L, source.read(OkioBuffer(), 0L))
            assertEquals(0, rawSource.readCalls)

            assertFailsWith<IllegalArgumentException> { source.read(OkioBuffer(), -1L) }
            assertEquals(0, rawSource.readCalls)
        } finally {
            source.close()
        }
    }

    @Test
    fun `empty source reports end of stream`() {
        val rawSource = ByteArrayRawSource(ByteArray(0))
        val source = KmpFileOkioSource(rawSource)
        try {
            assertEquals(-1L, source.read(OkioBuffer(), EXPECTED_READ_BUFFER.toLong()))
            assertEquals(-1L, source.read(OkioBuffer(), EXPECTED_READ_BUFFER.toLong()))
            assertEquals(2, rawSource.readCalls)
        } finally {
            source.close()
        }
    }

    @Test
    fun `close is idempotent and read after close fails without touching the raw source`() {
        val rawSource = ByteArrayRawSource(content)
        val source = KmpFileOkioSource(rawSource)

        source.close()
        source.close()

        assertEquals(1, rawSource.closeCalls)
        assertFailsWith<IllegalStateException> { source.read(OkioBuffer(), 1L) }
        assertEquals(0, rawSource.readCalls)
    }

    @Test
    fun `close failure propagates once and later closes are no-ops`() {
        val rawSource = ThrowingCloseRawSource()
        val source = KmpFileOkioSource(rawSource)

        val failure = assertFailsWith<IOException> { source.close() }
        assertEquals("close failed", failure.message)

        source.close()
        assertEquals(1, rawSource.closeCalls)
    }

    @Test
    fun `mid read failure propagates and leaves closing to the caller`() {
        val rawSource = ByteArrayRawSource(content, failAfter = 0)
        val source = KmpFileOkioSource(rawSource)

        val failure = assertFailsWith<IOException> { source.read(OkioBuffer(), 1L) }
        assertEquals("synthetic read failure", failure.message)
        assertEquals(0, rawSource.closeCalls)

        source.close()
        assertEquals(1, rawSource.closeCalls)
    }

    @Test
    fun `a positive request that makes no progress fails instead of spinning`() {
        val rawSource = ByteArrayRawSource(content, zeroOnce = true)
        val source = KmpFileOkioSource(rawSource)
        try {
            assertFailsWith<IOException> { source.read(OkioBuffer(), 1L) }
            assertEquals(1, rawSource.readCalls)
        } finally {
            source.close()
        }
    }
}

private class ByteArrayRawSource(
    private val bytes: ByteArray,
    private val failAfter: Int? = null,
    private val zeroOnce: Boolean = false,
) : RawSource {

    var readCalls: Int = 0
        private set

    var closeCalls: Int = 0
        private set

    var maxRequested: Long = 0L
        private set

    private var offset = 0
    private var returnedZero = false

    override fun readAtMostTo(sink: KioBuffer, byteCount: Long): Long {
        readCalls++
        maxRequested = maxOf(maxRequested, byteCount)

        val failureOffset = failAfter
        if (failureOffset != null && offset >= failureOffset) {
            throw IOException("synthetic read failure")
        }
        if (zeroOnce && !returnedZero) {
            returnedZero = true
            return 0L
        }
        if (offset >= bytes.size) return -1L

        val count = minOf(byteCount, (bytes.size - offset).toLong()).toInt()
        sink.write(bytes, offset, offset + count)
        offset += count
        return count.toLong()
    }

    override fun close() {
        closeCalls++
    }
}

private class ThrowingCloseRawSource : RawSource {

    var closeCalls: Int = 0
        private set

    override fun readAtMostTo(sink: KioBuffer, byteCount: Long): Long = -1L

    override fun close() {
        closeCalls++
        throw IOException("close failed")
    }
}
