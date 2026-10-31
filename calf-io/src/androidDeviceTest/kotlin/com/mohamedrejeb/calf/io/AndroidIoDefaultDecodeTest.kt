// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.io

import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Color
import android.media.ExifInterface
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Looper
import android.os.Process
import androidx.core.content.FileProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import coil3.BitmapImage
import coil3.EventListener
import coil3.ImageLoader
import coil3.decode.BitmapFactoryDecoder
import coil3.decode.DataSource
import coil3.decode.DecodeResult
import coil3.decode.Decoder
import coil3.fetch.FetchResult
import coil3.fetch.Fetcher
import coil3.fetch.SourceFetchResult
import coil3.request.CachePolicy
import coil3.request.ErrorResult
import coil3.request.ImageRequest
import coil3.request.ImageResult
import coil3.request.Options
import coil3.request.SuccessResult
import coil3.request.allowHardware
import coil3.request.bitmapConfig
import coil3.size.Size
import com.mohamedrejeb.calf.io.instrumentation.DeviceIoFileProvider
import com.mohamedrejeb.calf.picker.coil.KmpFileFetcher
import java.io.File
import java.util.Random
import java.util.UUID
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.*

/** Default Coil decoders over real Android sources, not injected Decoder/BitmapFactory shadows. */
@RunWith(AndroidJUnit4::class)
class AndroidIoDefaultDecodeTest {
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val read = Intent.FLAG_GRANT_READ_URI_PERMISSION
    private val write = Intent.FLAG_GRANT_WRITE_URI_PERMISSION

    @Test fun defaultPngDecodeStreamsUnknownSizeBinaryAndPreservesEveryPixel() = localFiles { directory ->
        val width = 257; val height = 193
        val random = Random(0x4e617469766543L)
        val pixels = IntArray(width * height) { index ->
            if (index % 509 == 0) Color.TRANSPARENT else 0xff000000.toInt() or random.nextInt(0x1000000)
        }
        val file = encode(directory, "unknown-size.png", width, height, Bitmap.CompressFormat.PNG, pixels)
        val bytes = boundedBytes(file)
        assertTrue(bytes.size > 64 * 1024, "The real native PNG encoder must produce more than one encoded segment")
        val identity = DeviceDescriptorIdentity.of(file)
        assertEquals(0, openDeviceDescriptorsFor(identity))
        val uri = localUri(file).buildUpon().appendQueryParameter(DeviceIoFileProvider.FIXTURE_MODE,
            DeviceIoFileProvider.UNKNOWN_SIZE).build()
        val source = KmpFile(uri)
        assertTrue(source.exists(context)); assertFalse(source.isDirectory(context))
        assertNull(source.getSize(context), "Actual binary provider row deliberately has null size")
        assertEquals("image/png", source.getMimeType(context)); assertEquals(file.name, source.getName(context))
        assertNull(source.getPath(context)); assertEquals(uri.toString(), source.toUriString())
        assertEquals(0, localStats(uri).getInt("opens"), "Metadata must not open the actual file")
        val witness = DefaultDecodeWitness(bytes, "image/png", { identity }, requirePartialFetch = true)
        pipeline { loader ->
            val result = assertIs<SuccessResult>(runBlocking(Dispatchers.IO) { loader.execute(source, witness) })
            bitmap(assertIs<BitmapImage>(result.image).bitmap) { decoded ->
                assertEquals(DataSource.DISK, result.dataSource); assertFalse(result.isSampled)
                assertEquals(width, decoded.width); assertEquals(height, decoded.height)
                assertEquals(Bitmap.Config.ARGB_8888, decoded.config)
                val actual = IntArray(width * height)
                decoded.getPixels(actual, 0, width, 0, 0, width, height)
                assertContentEquals(pixels, actual, "Default native PNG decode must retain every opaque/transparent pixel")
            }
            witness.assertOutcome(success = true)
            assertEquals(1, localStats(uri).getInt("opens"))
            assertEquals(0, openDeviceDescriptorsFor(identity), "Successful default decode must close its real source")
        }
        assertContentEquals(bytes, boundedBytes(file), "Fetching must not mutate or replace the source")
        assertEquals(0, openDeviceDescriptorsFor(identity))
    }

    @Test fun defaultJpegDecodeReplaysBoundsAndExifForRotationAndReflection() = localFiles { directory ->
        val width = 96; val height = 64
        val colors = intArrayOf(Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW)
        val pixels = IntArray(width * height) { index ->
            val x = index % width; val y = index / width
            colors[(if (y >= height / 2) 2 else 0) + (if (x >= width / 2) 1 else 0)]
        }
        // Independent geometric expectations, not Coil's EXIF utility or a predecoded Bitmap result.
        val variants = listOf(
            Triple("rotate-90.jpg", ExifInterface.ORIENTATION_ROTATE_90,
                intArrayOf(Color.BLUE, Color.RED, Color.YELLOW, Color.GREEN)),
            Triple("transverse.jpg", ExifInterface.ORIENTATION_TRANSVERSE,
                intArrayOf(Color.YELLOW, Color.GREEN, Color.BLUE, Color.RED)),
        )
        pipeline { loader ->
            for ((name, orientation, expected) in variants) {
                val file = encode(directory, name, width, height, Bitmap.CompressFormat.JPEG, pixels)
                ExifInterface(file.absolutePath).apply {
                    setAttribute(ExifInterface.TAG_ORIENTATION, orientation.toString())
                    saveAttributes()
                }
                assertEquals(orientation, ExifInterface(file.absolutePath)
                    .getAttributeInt(ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_UNDEFINED))
                val bytes = boundedBytes(file); val identity = DeviceDescriptorIdentity.of(file)
                assertEquals(0, openDeviceDescriptorsFor(identity))
                val uri = localUri(file); val source = KmpFile(uri)
                assertEquals("image/jpeg", source.getMimeType(context)); assertEquals(bytes.size.toLong(), source.getSize(context))
                val witness = DefaultDecodeWitness(bytes, "image/jpeg", { identity })
                val result = assertIs<SuccessResult>(runBlocking(Dispatchers.IO) { loader.execute(source, witness) })
                bitmap(assertIs<BitmapImage>(result.image).bitmap) { decoded ->
                    assertEquals(DataSource.DISK, result.dataSource); assertFalse(result.isSampled)
                    assertEquals(height, decoded.width); assertEquals(width, decoded.height)
                    assertEquals(Bitmap.Config.ARGB_8888, decoded.config)
                    val samples = intArrayOf(
                        decoded.getPixel(decoded.width / 4, decoded.height / 4),
                        decoded.getPixel(3 * decoded.width / 4, decoded.height / 4),
                        decoded.getPixel(decoded.width / 4, 3 * decoded.height / 4),
                        decoded.getPixel(3 * decoded.width / 4, 3 * decoded.height / 4),
                    )
                    for (index in expected.indices) assertRgbNear(expected[index], samples[index])
                }
                witness.assertOutcome(success = true)
                assertEquals(1, localStats(uri).getInt("opens"))
                assertEquals(0, openDeviceDescriptorsFor(identity))
                assertContentEquals(bytes, boundedBytes(file))
            }
        }
    }

    @Test fun repeatedDefaultCorruptDecodesReleaseActualCrossUidDescriptors() = remoteDocuments { control ->
        grantPersistedTree()
        val id = "decoder.bin"
        pipeline { loader ->
            repeat(4) { index ->
                val count = index + 1
                val witness = DefaultDecodeWitness(AndroidIoProviderContract.bytes(id), "application/octet-stream", {
                    val state = remoteStats(control, id)
                    assertEquals(count, state.getInt("opens")); assertEquals(index, state.getInt("closes"))
                    for (key in listOf("device", "inode", "mode", "fdInfoInode")) assertTrue(state.containsKey(key))
                    DeviceDescriptorIdentity.fromProviderRegularFile(state.getLong("device"), state.getLong("inode"),
                        state.getInt("mode"), state.getLong("fdInfoInode"))
                })
                val result = assertIs<ErrorResult>(runBlocking(Dispatchers.IO) {
                    loader.execute(KmpFile(AndroidIoProviderContract.child(id)), witness)
                })
                // Coil's unmodified default BitmapFactoryDecoder reports invalid image bytes this way.
                assertIs<IllegalStateException>(result.throwable)
                assertTrue(result.throwable.message?.contains("BitmapFactory returned a null bitmap") == true)
                witness.assertOutcome(success = false)
                waitUntil { remoteStats(control, id).getInt("closes") == count }
                val final = remoteStats(control, id)
                assertEquals(count, final.getInt("opens")); assertEquals(count, final.getInt("closes"))
                assertEquals(0, final.getInt("closeErrors")); assertEquals(0, final.getInt("writes"))
                assertEquals(AndroidIoProviderContract.bytes(id).size.toLong(), final.getLong("length"))
                assertEquals(0, openDeviceDescriptorsFor(assertNotNull(witness.identity.get())),
                    "Repeated actual default failures must not retain transferred native sources")
            }
        }
    }

    /** Observes the actual fetch/default decoder without replacing or consuming their source. */
    private inner class DefaultDecodeWitness(
        private val expectedBytes: ByteArray,
        private val mimeType: String,
        private val identify: () -> DeviceDescriptorIdentity,
        private val requirePartialFetch: Boolean = false,
    ) : EventListener() {
        val identity = AtomicReference<DeviceDescriptorIdentity>()
        private val fetches = AtomicInteger(); private val decodeStarts = AtomicInteger()
        private val decodeEnds = AtomicInteger(); private val successes = AtomicInteger(); private val errors = AtomicInteger()
        override fun fetchEnd(request: ImageRequest, fetcher: Fetcher, options: Options, result: FetchResult?) {
            assertNotEquals(Looper.getMainLooper(), Looper.myLooper())
            assertIs<KmpFileFetcher>(fetcher)
            val actual = assertIs<SourceFetchResult>(result)
            assertEquals(DataSource.DISK, actual.dataSource); assertEquals(mimeType, actual.mimeType)
            assertNull(actual.source.metadata); assertNull(actual.source.fileOrNull(), "No file staging/metadata shortcut")
            val native = identify(); assertTrue(identity.compareAndSet(null, native))
            assertEquals(1, openDeviceDescriptorsFor(native), "Only the actual reporter's transferred REG source")
            val buffered = actual.source.source()
            val prefix = expectedBytes.copyOfRange(0, minOf(16, expectedBytes.size))
            buffered.peek().use { peek -> assertContentEquals(prefix, peek.readByteArray(prefix.size.toLong())) }
            // The default decoder receives the same source, still positioned at its initial byte.
            if (requirePartialFetch) assertTrue(buffered.buffer.size < expectedBytes.size.toLong(),
                "A native source fetch must not materialize the complete encoded PNG before default decoding")
            assertEquals(1, openDeviceDescriptorsFor(native)); assertEquals(1, fetches.incrementAndGet())
        }
        override fun decodeStart(request: ImageRequest, decoder: Decoder, options: Options) {
            assertNotEquals(Looper.getMainLooper(), Looper.myLooper())
            assertIs<BitmapFactoryDecoder>(decoder, "Default registry fallback for a source-only KmpFile ImageSource")
            assertEquals(1, openDeviceDescriptorsFor(assertNotNull(identity.get())))
            assertEquals(1, decodeStarts.incrementAndGet())
        }
        override fun decodeEnd(request: ImageRequest, decoder: Decoder, options: Options, result: DecodeResult?) {
            assertIs<BitmapFactoryDecoder>(decoder); assertNotNull(result); assertEquals(1, decodeEnds.incrementAndGet())
        }
        override fun onSuccess(request: ImageRequest, result: SuccessResult) { successes.incrementAndGet() }
        override fun onError(request: ImageRequest, result: ErrorResult) { errors.incrementAndGet() }
        fun assertOutcome(success: Boolean) {
            assertEquals(1, fetches.get()); assertEquals(1, decodeStarts.get())
            assertEquals(if (success) 1 else 0, decodeEnds.get())
            assertEquals(if (success) 1 else 0, successes.get()); assertEquals(if (success) 0 else 1, errors.get())
            assertEquals(0, openDeviceDescriptorsFor(assertNotNull(identity.get())))
        }
    }

    /** Caches disabled intentionally: this verifies fresh decodes, not request-key/invalidation policy. */
    private inner class DefaultPipeline {
        private val pending = AtomicReference<DefaultDecodeWitness>()
        val loader = ImageLoader.Builder(context).components { add(KmpFileFetcher.Factory()) }
            .eventListenerFactory { assertNotNull(pending.getAndSet(null), "Only one actual listener per sequential request") }.build()
        suspend fun execute(file: KmpFile, witness: DefaultDecodeWitness): ImageResult {
            assertTrue(pending.compareAndSet(null, witness))
            try {
                val request = ImageRequest.Builder(context).data(file).size(Size.ORIGINAL)
                    .allowHardware(false).bitmapConfig(Bitmap.Config.ARGB_8888)
                    .memoryCachePolicy(CachePolicy.DISABLED).diskCachePolicy(CachePolicy.DISABLED)
                    .coroutineContext(Dispatchers.IO).build()
                return loader.execute(request)
            } finally { pending.set(null) }
        }
    }
    private fun pipeline(body: (DefaultPipeline) -> Unit) {
        val pipeline = DefaultPipeline()
        preservingCleanup({ body(pipeline) }, { pipeline.loader.shutdown() })
    }
    private fun requireNativeFixture() {
        assertEquals("true", InstrumentationRegistry.getArguments().getString("nativecmpkitOwnedIoDocuments"))
        assertEquals(35, Build.VERSION.SDK_INT); assertTrue(Build.HARDWARE in setOf("ranchu", "goldfish"))
        assertEquals(instrumentation.context.packageName, context.packageName)
    }
    private fun localFiles(body: (File) -> Unit) {
        requireNativeFixture()
        val base = File(context.cacheDir, "nativecmpkit-io-device")
        assertTrue(base.isDirectory || base.mkdir()); assertEquals(context.cacheDir.canonicalFile, base.canonicalFile.parentFile)
        val directory = File(base, "default-decode-" + UUID.randomUUID())
        assertTrue(directory.mkdir()); assertEquals(base.canonicalFile, directory.canonicalFile.parentFile)
        preservingCleanup({ body(directory) }, {
            for (file in assertNotNull(directory.listFiles())) if (file.isFile) {
                assertEquals(0, openDeviceDescriptorsFor(DeviceDescriptorIdentity.of(file)), "Do not delete away a leaked source")
            }
            assertEquals(base.canonicalFile, directory.canonicalFile.parentFile)
            assertTrue(directory.deleteRecursively(), "Only this fixture's newly owned directory is removed")
        })
    }
    private fun encode(directory: File, name: String, width: Int, height: Int, format: Bitmap.CompressFormat, pixels: IntArray): File {
        require(name in setOf("unknown-size.png", "rotate-90.jpg", "transverse.jpg"))
        val file = File(directory, name); assertTrue(file.createNewFile()); assertEquals(directory.canonicalFile, file.canonicalFile.parentFile)
        bitmap(Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)) { encoded ->
            encoded.setPixels(pixels, 0, width, 0, 0, width, height)
            file.outputStream().use { output -> assertTrue(encoded.compress(format, 100, output)) }
        }
        return file
    }
    private fun bitmap(bitmap: Bitmap, body: (Bitmap) -> Unit) = preservingCleanup({ body(bitmap) }, { bitmap.recycle() })
    private fun boundedBytes(file: File): ByteArray {
        assertTrue(file.length() in 1L..512L * 1024L)
        return file.inputStream().use { it.readBytes() }.also { assertEquals(file.length(), it.size.toLong()) }
    }
    private fun localUri(file: File): Uri {
        val authority = context.packageName + ".io-device-files"
        val provider = assertNotNull(context.packageManager.resolveContentProvider(authority, 0))
        assertEquals(Process.myUid(), provider.applicationInfo.uid); assertFalse(provider.exported)
        assertTrue(provider.grantUriPermissions); assertEquals(context.packageName + ":nativecmpkit_io_device_provider", provider.processName)
        return FileProvider.getUriForFile(context, authority, file)
    }
    private fun localStats(uri: Uri): Bundle = assertNotNull(context.contentResolver.call(
        uri, DeviceIoFileProvider.STATS, uri.toString(), null)).also {
        assertTrue(it.containsKey("providerPid") && it.containsKey("opens"))
        assertTrue(it.getInt("providerPid") > 0); assertNotEquals(Process.myPid(), it.getInt("providerPid"))
    }
    private fun assertRgbNear(expected: Int, actual: Int) {
        assertEquals(255, Color.alpha(actual))
        for ((wanted, found) in listOf(Color.red(expected) to Color.red(actual), Color.green(expected) to Color.green(actual),
            Color.blue(expected) to Color.blue(actual))) assertTrue(kotlin.math.abs(wanted - found) <= 12,
                "JPEG interior quadrant color/orientation mismatch")
    }
    private fun remoteStats(control: OwnedIoEndpoint, id: String): Bundle = assertNotNull(control.request("stats", id).getBundle("provider")).also {
        for (key in listOf("uid", "pid", "process", "generation", "opens", "closes", "closeErrors", "writes", "length"))
            assertTrue(it.containsKey(key))
        val provider = assertNotNull(context.packageManager.resolveContentProvider(AndroidIoProviderContract.AUTHORITY, 0))
        assertEquals(provider.applicationInfo.uid, it.getInt("uid")); assertNotEquals(Process.myUid(), it.getInt("uid"))
        assertTrue(it.getInt("pid") > 0); assertNotEquals(Process.myPid(), it.getInt("pid"))
        assertEquals(AndroidIoProviderContract.PACKAGE + ":nativecmpkit_io_provider", it.getString("process"))
        assertTrue(assertNotNull(it.getString("generation")).matches(Regex("[a-f0-9-]{36}")))
    }
    private fun grantPersistedTree() {
        ActivityScenario.launch(AndroidIoGrantActivity::class.java).use { scenario ->
            var activity: AndroidIoGrantActivity? = null
            scenario.onActivity { activity = it }; val caller = assertNotNull(activity)
            waitUntil { caller.firstDraw && caller.hasWindowFocus() }
            scenario.onActivity { it.selectOwnedTree() }; waitUntil { caller.ioDocumentResultCode != null }
            assertEquals(Activity.RESULT_OK, caller.ioDocumentResultCode)
            val result = assertNotNull(caller.ioDocumentResult)
            assertEquals(AndroidIoProviderContract.tree, result.data)
            assertEquals(AndroidIoProviderContract.tree, assertNotNull(result.clipData).getItemAt(0).uri)
            assertEquals(read or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION or Intent.FLAG_GRANT_PREFIX_URI_PERMISSION,
                result.flags and (read or write or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION or Intent.FLAG_GRANT_PREFIX_URI_PERMISSION))
            assertEquals(PackageManager.PERMISSION_GRANTED, context.checkUriPermission(AndroidIoProviderContract.tree, Process.myPid(), Process.myUid(), read))
            assertEquals(PackageManager.PERMISSION_DENIED, context.checkUriPermission(AndroidIoProviderContract.tree, Process.myPid(), Process.myUid(), write))
            assertNotNull(KmpFile(AndroidIoProviderContract.tree).createBookmark(context))
        }
        val permission = context.contentResolver.persistedUriPermissions.single { it.uri == AndroidIoProviderContract.tree }
        assertTrue(permission.isReadPermission); assertFalse(permission.isWritePermission)
    }
    private fun remoteDocuments(body: (OwnedIoEndpoint) -> Unit) {
        requireNativeFixture()
        assertEquals(PackageManager.PERMISSION_DENIED, context.checkSelfPermission("android.permission.MANAGE_DOCUMENTS"))
        val provider = assertNotNull(context.packageManager.resolveContentProvider(AndroidIoProviderContract.AUTHORITY, 0))
        assertEquals(AndroidIoProviderContract.PACKAGE, provider.packageName); assertTrue(provider.exported); assertTrue(provider.grantUriPermissions)
        assertEquals("android.permission.MANAGE_DOCUMENTS", provider.readPermission); assertEquals("android.permission.MANAGE_DOCUMENTS", provider.writePermission)
        val control = OwnedIoEndpoint.control()
        var primary: Throwable? = null
        try {
            control.connect()
            val reset = assertNotNull(control.request("reset").getBundle("provider"))
            assertTrue(reset.containsKey("uid") && reset.containsKey("pid"))
            assertEquals(provider.applicationInfo.uid, reset.getInt("uid")); assertTrue(reset.getInt("pid") > 0)
            assertEquals(PackageManager.PERMISSION_DENIED, context.checkUriPermission(AndroidIoProviderContract.tree, Process.myPid(), Process.myUid(), read))
            assertEquals(PackageManager.PERMISSION_DENIED, context.checkUriPermission(AndroidIoProviderContract.tree, Process.myPid(), Process.myUid(), write))
            body(control)
        } catch (failure: Throwable) { primary = failure; throw failure }
        finally {
            cleanupAll(primary, listOf(
                { KmpFile(AndroidIoProviderContract.tree).releaseBookmark(context) },
                {
                    val ids = listOf("bookmark.txt", "decoder.bin", "cancel.bin", "survivor.bin")
                    waitUntil { ids.all { id -> remoteStats(control, id).let { it.getInt("opens") == it.getInt("closes") } } }
                    for (id in ids) {
                        val state = remoteStats(control, id); assertEquals(0, state.getInt("closeErrors")); assertEquals(0, state.getInt("writes"))
                    }
                    control.request("reset")
                },
                { control.close() },
            ))
        }
    }
    private fun preservingCleanup(body: () -> Unit, cleanup: () -> Unit) {
        var primary: Throwable? = null
        try { body() } catch (failure: Throwable) { primary = failure; throw failure }
        finally { cleanupAll(primary, listOf(cleanup)) }
    }
    private fun cleanupAll(primary: Throwable?, actions: List<() -> Unit>) {
        var cleanup: Throwable? = null
        for (action in actions) try { action() } catch (failure: Throwable) {
            val first = primary ?: cleanup
            if (first == null) cleanup = failure else if (first !== failure) first.addSuppressed(failure)
        }
        if (primary == null) cleanup?.let { throw it }
    }
    private fun waitUntil(condition: () -> Boolean) {
        val deadline = System.nanoTime() + 20_000_000_000L
        while (!condition()) { check(System.nanoTime() < deadline) { "Actual default-decoder native condition timed out" }; Thread.sleep(20) }
    }
}
