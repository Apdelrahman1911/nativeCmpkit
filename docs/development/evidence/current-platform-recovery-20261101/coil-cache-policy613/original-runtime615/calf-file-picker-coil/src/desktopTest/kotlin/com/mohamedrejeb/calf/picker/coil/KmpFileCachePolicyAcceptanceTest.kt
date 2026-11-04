package com.mohamedrejeb.calf.picker.coil

import coil3.BitmapImage
import coil3.EventListener
import coil3.ImageLoader
import coil3.PlatformContext
import coil3.decode.DataSource
import coil3.decode.DecodeResult
import coil3.decode.Decoder
import coil3.decode.ImageSource
import coil3.decode.SkiaImageDecoder
import coil3.fetch.FetchResult
import coil3.fetch.Fetcher
import coil3.fetch.SourceFetchResult
import coil3.memory.MemoryCache
import coil3.request.CachePolicy
import coil3.request.ErrorResult
import coil3.request.ImageRequest
import coil3.request.Options
import coil3.request.SuccessResult
import coil3.size.Precision
import coil3.size.Size
import com.mohamedrejeb.calf.io.KmpFile
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.runTest
import okio.BufferedSource
import org.jetbrains.skia.Bitmap
import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.nio.file.Files
import java.nio.file.NoSuchFileException
import java.nio.file.Path
import java.nio.file.attribute.BasicFileAttributes
import java.util.Collections
import java.util.IdentityHashMap
import java.util.UUID
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import java.util.zip.CRC32
import java.util.zip.Deflater
import java.util.zip.DeflaterOutputStream
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNotEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNotSame
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

/** Real default Skia decoder/cache; Linux also requires actual owned-file descriptor balance. Not a memory benchmark. */
class KmpFileCachePolicyAcceptanceTest {
    @Test fun callerRevisionControlsDefaultDecoderCacheAndSourceOwnership() = runTest {
        val original = png(ORIGINAL_COLOR)
        val replacement = png(REPLACEMENT_COLOR)
        assertEquals(original.size, replacement.size, "Uncompressed PNGs must really have equal encoded lengths")
        assertFalse(original.contentEquals(replacement))
        val path = Files.createTempFile("nativecmpkit-coil-cache-policy", ".png")
        var descriptors: LinuxDescriptors? = null
        preservingCleanup({
            descriptors = if (System.getProperty("os.name") == "Linux") LinuxDescriptors(path) else null
            Files.write(path, original)
            val pipeline = Pipeline(path, descriptors)
            preservingCleanup({
                val first = pipeline.execute(1, ORIGINAL_COLOR, DataSource.DISK)
                val firstKey = assertNotNull(first.memoryCacheKey)
                assertEquals(setOf(firstKey), pipeline.cache.keys)
                assertSame(first.image, pipeline.execute(1, ORIGINAL_COLOR, DataSource.MEMORY_CACHE).image)

                // Intentional negative boundary: an unchanged revision is not automatic file invalidation.
                Files.write(path, replacement)
                assertEquals(original.size.toLong(), Files.size(path))
                descriptors?.assertSameFile(path)
                assertSame(first.image, pipeline.execute(1, ORIGINAL_COLOR, DataSource.MEMORY_CACHE).image)

                val revised = pipeline.execute(2, REPLACEMENT_COLOR, DataSource.DISK)
                val revisedKey = assertNotNull(revised.memoryCacheKey)
                assertNotEquals(firstKey, revisedKey)
                assertNotSame(first.image, revised.image)
                assertEquals(setOf(firstKey, revisedKey), pipeline.cache.keys, "New revision does not evict the old one")
                assertTrue(pipeline.cache.remove(firstKey))
                assertNull(pipeline.cache[firstKey])

                // The loader's memory cache stays enabled; only unknown-revision requests opt out.
                Files.write(path, original)
                assertNull(pipeline.execute(null, ORIGINAL_COLOR, DataSource.DISK).memoryCacheKey)
                Files.write(path, replacement)
                assertNull(pipeline.execute(null, REPLACEMENT_COLOR, DataSource.DISK).memoryCacheKey)
                assertEquals(setOf(revisedKey), pipeline.cache.keys, "Unknown revisions neither reuse nor write cache entries")
                assertSame(revised.image, assertNotNull(pipeline.cache[revisedKey]).image)
                assertEquals(6, pipeline.requests.size)
                assertEquals(4, pipeline.requests.sumOf { it.fetches.get() })
                assertEquals(4, pipeline.requests.sumOf { it.decodes.get() })
            }, { pipeline.close() })
        }, {
            descriptors?.assertCount(0)
            assertTrue(Files.deleteIfExists(path), "Remove only this fixture's newly owned file, after source closure")
        })
    }

    private class Pipeline(private val path: Path, private val descriptors: LinuxDescriptors?) {
        private val context = PlatformContext.INSTANCE
        private val contentId = "test-owned-${UUID.randomUUID()}"
        private val pending = AtomicReference<Witness?>()
        private val bitmaps = Collections.newSetFromMap(IdentityHashMap<Bitmap, Boolean>())
        val requests = mutableListOf<Witness>()
        val cache = MemoryCache.Builder().maxSizeBytes(1024 * 1024L).weakReferencesEnabled(false).build()
        private val loader = ImageLoader.Builder(context)
            .components { add(KmpFileFetcher.Factory()) } // No custom decoder, keyer, mapper or interceptor.
            .memoryCache(cache).memoryCachePolicy(CachePolicy.ENABLED).diskCache { null }
            .mainCoroutineContext(Dispatchers.Default) // execute-only fixture, no UI target or global Main replacement.
            .eventListenerFactory { assertNotNull(pending.getAndSet(null), "One witness per sequential real request") }
            .build()

        suspend fun execute(revision: Long?, color: Int, expectedSource: DataSource): SuccessResult {
            descriptors?.assertCount(0)
            val witness = Witness(descriptors, bitmaps)
            requests.add(witness)
            assertTrue(pending.compareAndSet(null, witness))
            val key = revision?.let {
                "test:kmp-image:v1:${contentId.length}:$contentId:r$it:original:exact:no-transform:v1"
            }
            // A fresh wrapper proves the supplied content identity, not object identity, controls reuse.
            val request = ImageRequest.Builder(context).data(KmpFile(path.toFile()))
                .size(Size.ORIGINAL).precision(Precision.EXACT).coroutineContext(Dispatchers.IO)
                .diskCachePolicy(CachePolicy.DISABLED)
                .apply {
                    if (key == null) memoryCachePolicy(CachePolicy.DISABLED)
                    else memoryCacheKey(key).memoryCachePolicy(CachePolicy.ENABLED)
                }.build()
            try {
                val actual = loader.execute(request)
                val result = if (actual is ErrorResult) {
                    throw AssertionError("Actual Coil request returned ErrorResult instead of SuccessResult", actual.throwable)
                } else assertIs<SuccessResult>(actual)
                assertEquals(expectedSource, result.dataSource)
                assertEquals(key?.let { MemoryCache.Key(it) }, result.memoryCacheKey)
                val image = assertIs<BitmapImage>(result.image)
                assertFalse(image.bitmap.isClosed)
                assertEquals(WIDTH, image.width); assertEquals(HEIGHT, image.height)
                for (y in 0 until HEIGHT) for (x in 0 until WIDTH) assertEquals(color, image.bitmap.getColor(x, y))
                witness.assertCompleted(expectedSource != DataSource.MEMORY_CACHE)
                descriptors?.assertCount(0)
                return result
            } finally { pending.set(null) }
        }

        fun close() = cleanup(
            { cache.clear(); assertTrue(cache.keys.isEmpty()) },
            { loader.shutdown() },
            // A failed close assertion stays a failure; only then close a leaked source for safe fixture cleanup.
            { cleanup(*requests.map { witness -> { witness.releaseAfterFailureIfNeeded() } }.toTypedArray()) },
            { cleanup(*synchronized(bitmaps) { bitmaps.map { bitmap -> { bitmap.close(); assertTrue(bitmap.isClosed) } } }.toTypedArray()) },
            { descriptors?.assertCount(0) },
        )
    }

    private class Witness(
        private val descriptors: LinuxDescriptors?,
        private val bitmaps: MutableSet<Bitmap>,
    ) : EventListener() {
        private val fetchStarts = AtomicInteger()
        val fetches = AtomicInteger()
        val decodes = AtomicInteger()
        private val decodeEnds = AtomicInteger()
        private val successes = AtomicInteger()
        private val errors = AtomicInteger()
        private val cancellations = AtomicInteger()
        private val source = AtomicReference<ImageSource?>()
        private val buffered = AtomicReference<BufferedSource?>()

        override fun fetchStart(request: ImageRequest, fetcher: Fetcher, options: Options) {
            assertIs<KmpFileFetcher>(fetcher)
            descriptors?.assertCount(0)
            assertEquals(1, fetchStarts.incrementAndGet())
        }

        override fun fetchEnd(request: ImageRequest, fetcher: Fetcher, options: Options, result: FetchResult?) {
            assertIs<KmpFileFetcher>(fetcher)
            val fetched = assertIs<SourceFetchResult>(result)
            assertTrue(source.compareAndSet(null, fetched.source))
            assertEquals(DataSource.DISK, fetched.dataSource); assertEquals("image/png", fetched.mimeType)
            assertNull(fetched.source.metadata); assertNull(fetched.source.fileOrNull(), "No staging-file decoder shortcut")
            val actual = fetched.source.source()
            assertTrue(buffered.compareAndSet(null, actual))
            actual.peek().use { assertContentEquals(PNG_SIGNATURE, it.readByteArray(PNG_SIGNATURE.size.toLong())) }
            descriptors?.assertCount(1)
            assertEquals(1, fetches.incrementAndGet())
        }

        override fun decodeStart(request: ImageRequest, decoder: Decoder, options: Options) {
            assertIs<SkiaImageDecoder>(decoder, "The actual default registry decoder must process the transferred source")
            assertSame(assertNotNull(buffered.get()), assertNotNull(source.get()).source())
            descriptors?.assertCount(1)
            assertEquals(1, decodes.incrementAndGet())
        }

        override fun decodeEnd(request: ImageRequest, decoder: Decoder, options: Options, result: DecodeResult?) {
            assertIs<SkiaImageDecoder>(decoder)
            val bitmap = assertIs<BitmapImage>(assertNotNull(result).image).bitmap
            synchronized(bitmaps) { assertTrue(bitmaps.add(bitmap), "Only fresh decodes transfer new owned bitmaps") }
            assertEquals(1, decodeEnds.incrementAndGet())
        }

        override fun onSuccess(request: ImageRequest, result: SuccessResult) { successes.incrementAndGet() }
        override fun onError(request: ImageRequest, result: ErrorResult) { errors.incrementAndGet() }
        override fun onCancel(request: ImageRequest) { cancellations.incrementAndGet() }

        fun assertCompleted(freshDecode: Boolean) {
            val expected = if (freshDecode) 1 else 0
            assertEquals(expected, fetchStarts.get()); assertEquals(expected, fetches.get())
            assertEquals(expected, decodes.get()); assertEquals(expected, decodeEnds.get())
            assertEquals(1, successes.get()); assertEquals(0, errors.get()); assertEquals(0, cancellations.get())
            if (freshDecode) assertSourceClosed() else { assertNull(source.get()); assertNull(buffered.get()) }
        }

        private fun assertSourceClosed() {
            assertEquals("closed", assertFailsWith<IllegalStateException> { assertNotNull(source.get()).source() }.message)
            assertEquals("closed", assertFailsWith<IllegalStateException> { assertNotNull(buffered.get()).exhausted() }.message)
        }

        fun releaseAfterFailureIfNeeded() {
            val actual = source.get() ?: return
            try { assertSourceClosed() } catch (failure: Throwable) {
                try { actual.close() } catch (cleanup: Throwable) { failure.addSuppressed(cleanup) }
                throw failure
            }
        }
    }

    /** Unknown/unavailable procfs is not reported as zero; non-Linux hosts have source closure, not this witness. */
    private class LinuxDescriptors(path: Path) {
        private val directory = Path.of("/proc/self/fd")
        private val identity = assertNotNull(Files.readAttributes(path, BasicFileAttributes::class.java).fileKey())
        init { assertTrue(Files.isDirectory(directory) && Files.isReadable(directory), "Linux requires its real descriptor view") }
        fun assertSameFile(path: Path) = assertEquals(identity, Files.readAttributes(path, BasicFileAttributes::class.java).fileKey())
        fun assertCount(expected: Int) {
            val actual = Files.newDirectoryStream(directory).use { entries -> entries.count { descriptor ->
                try { Files.readAttributes(descriptor, BasicFileAttributes::class.java).fileKey() == identity }
                catch (_: NoSuchFileException) { false } // An unrelated descriptor can close during enumeration.
            } }
            assertEquals(expected, actual, "Actual descriptors for only this newly owned device/inode")
        }
    }

    companion object {
        private const val WIDTH = 8
        private const val HEIGHT = 6
        private val ORIGINAL_COLOR = 0xffbb2200.toInt()
        private val REPLACEMENT_COLOR = 0xff0033cc.toInt()
        private val PNG_SIGNATURE = byteArrayOf(137.toByte(), 80, 78, 71, 13, 10, 26, 10)

        /** Stored zlib blocks make two real different PNGs equal-length independently of compression heuristics. */
        private fun png(color: Int): ByteArray {
            val scanlines = ByteArrayOutputStream().apply {
                repeat(HEIGHT) {
                    write(0) // PNG filter None.
                    repeat(WIDTH) { write(color ushr 16); write(color ushr 8); write(color); write(color ushr 24) }
                }
            }.toByteArray()
            val deflater = Deflater(Deflater.NO_COMPRESSION)
            val encoded = ByteArrayOutputStream()
            try { DeflaterOutputStream(encoded, deflater).use { it.write(scanlines) } } finally { deflater.end() }
            return ByteArrayOutputStream().apply {
                write(PNG_SIGNATURE)
                val header = ByteArrayOutputStream().apply { DataOutputStream(this).use {
                    it.writeInt(WIDTH); it.writeInt(HEIGHT); it.write(byteArrayOf(8, 6, 0, 0, 0))
                } }.toByteArray()
                chunk("IHDR", header); chunk("IDAT", encoded.toByteArray()); chunk("IEND", byteArrayOf())
            }.toByteArray()
        }

        private fun ByteArrayOutputStream.chunk(type: String, bytes: ByteArray) {
            val name = type.toByteArray(Charsets.US_ASCII)
            val crc = CRC32().apply { update(name); update(bytes) }
            DataOutputStream(this).apply { writeInt(bytes.size); write(name); write(bytes); writeInt(crc.value.toInt()) }
        }

        private inline fun <T> preservingCleanup(body: () -> T, close: () -> Unit): T {
            var failure: Throwable? = null
            try { return body() } catch (caught: Throwable) { failure = caught; throw caught }
            finally { try { close() } catch (cleanup: Throwable) { if (failure == null) throw cleanup else failure.addSuppressed(cleanup) } }
        }

        private fun cleanup(vararg steps: () -> Unit) {
            var failure: Throwable? = null
            for (step in steps) try { step() } catch (caught: Throwable) { if (failure == null) failure = caught else failure.addSuppressed(caught) }
            failure?.let { throw it }
        }
    }
}
