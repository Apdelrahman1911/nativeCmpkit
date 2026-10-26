package com.mohamedrejeb.calf.picker.coil

import coil3.PlatformContext
import coil3.decode.DataSource
import coil3.decode.ImageSource
import coil3.fetch.SourceFetchResult
import coil3.request.Options
import com.mohamedrejeb.calf.io.KmpFile
import kotlinx.coroutines.test.runTest
import kotlinx.io.Buffer
import kotlinx.io.RawSource
import kotlinx.io.okio.asOkioSource
import okio.FileSystem
import okio.buffer
import java.nio.file.Files
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class KmpFileFetcherTest {
    @Test fun fetchReturnsRealStreamingSourceWithFileDataClassification() = runTest {
        val path = Files.createTempFile("nativecmpkit-coil", ".bin")
        val bytes = ByteArray(300_000) { (it % 251).toByte() }
        Files.write(path, bytes)
        try {
            val result = KmpFileFetcher(KmpFile(path.toFile()), Options(PlatformContext.INSTANCE)).fetch() as SourceFetchResult
            assertEquals(DataSource.DISK, result.dataSource)
            result.source.use { assertContentEquals(bytes, it.source().readByteArray()) }
        } finally { Files.deleteIfExists(path) }
    }

    @Test fun imageSourceCloseClosesTheOfficialBridgeUnderlyingSource() {
        var closes = 0
        val raw = object : RawSource {
            override fun readAtMostTo(sink: Buffer, byteCount: Long): Long = -1L
            override fun close() { closes++ }
        }
        ImageSource(raw.asOkioSource().buffer(), FileSystem.SYSTEM).close()
        assertEquals(1, closes)
    }

    @Test fun negativeMemoryLimitsAreRejected() {
        assertFailsWith<IllegalArgumentException> { KmpFileFetcher.Factory(-1) }
    }
}
