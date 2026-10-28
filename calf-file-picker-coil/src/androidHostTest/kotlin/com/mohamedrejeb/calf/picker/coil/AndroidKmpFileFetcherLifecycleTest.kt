@file:OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)

package com.mohamedrejeb.calf.picker.coil

import android.content.ContentProvider
import android.content.ContentValues
import android.content.pm.ProviderInfo
import android.content.res.AssetFileDescriptor
import android.database.Cursor
import android.net.Uri
import coil3.ImageLoader
import coil3.decode.DataSource
import coil3.decode.Decoder
import coil3.fetch.SourceFetchResult
import coil3.request.ErrorResult
import coil3.request.ImageRequest
import coil3.request.Options
import com.mohamedrejeb.calf.io.KmpFile
import java.io.File
import java.io.FileInputStream
import java.io.FilterInputStream
import java.io.FileNotFoundException
import java.io.IOException
import java.util.UUID
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.*
import kotlinx.coroutines.test.*
import org.junit.After
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import org.robolectric.shadows.ShadowContentResolver
import kotlin.test.*

/** Real Coil/IO/Okio + real JVM file descriptors; controlled Android resolver transport, not device IPC. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], manifest = Config.NONE)
class AndroidKmpFileFetcherLifecycleTest {
    private val context = RuntimeEnvironment.getApplication()
    private val local = File.createTempFile("nativecmpkit-android-coil", ".bin", context.cacheDir)
    private val authority = "nativecmpkit.coil." + UUID.randomUUID().toString().replace("-", "")
    private val uri = Uri.parse("content://$authority/file.bin")
    private val file = KmpFile(uri)
    private val provider = MetadataProvider().apply {
        // ContentProvider.context is also an implicit receiver property, initially null.
        attachInfo(this@AndroidKmpFileFetcherLifecycleTest.context,
            ProviderInfo().apply { authority = this@AndroidKmpFileFetcherLifecycleTest.authority })
    }
    private val opens = AtomicInteger()
    private val closes = AtomicInteger()
    private var input: TrackedInput? = null

    init {
        assertSame(context, provider.context, "The provider must actually be attached, not have a null transport context")
        local.writeBytes(ByteArray(300_000) { (it % 251).toByte() })
        ShadowContentResolver.registerProviderInternal(authority, provider)
        org.robolectric.Shadows.shadowOf(context.contentResolver).registerInputStreamSupplier(uri) {
            if (provider.nullInput) null else TrackedInput(FileInputStream(local)).also { input = it; opens.incrementAndGet() }
        }
    }

    @After fun cleanup() {
        input?.takeIf { it.fd.valid() }?.close()
        check(local.delete())
    }

    @Test fun sourceHasExactBytesAndImageSourceCloseReleasesTheActualDescriptor() = mainTest {
        val result = KmpFileFetcher(file, Options(context)).fetch() as SourceFetchResult
        assertEquals(DataSource.DISK, result.dataSource)
        assertEquals("application/octet-stream", result.mimeType)
        assertTrue(checkNotNull(input).fd.valid())
        result.source.use { assertContentEquals(local.readBytes(), it.source().readByteArray()) }
        assertReleased()
    }

    @Test fun metadataFailureAfterSourceOpenClosesBeforePropagating() = mainTest {
        val failure = IllegalStateException("provider MIME lookup failed after opening")
        provider.failure = failure
        assertSame(failure, assertFailsWith<IllegalStateException> { KmpFileFetcher(file, Options(context)).fetch() })
        assertReleased()
    }

    @Test fun nullProviderSourceBecomesATruthfulCoilErrorWithoutOpeningAnyDescriptor() = mainTest {
        provider.nullInput = true
        assertNull(context.contentResolver.openInputStream(uri), "Supplier null must take the real registered-provider null path")
        val loader = ImageLoader.Builder(context).components { add(KmpFileFetcher.Factory()) }.build()
        try {
            val request = ImageRequest.Builder(context).data(file).coroutineContext(StandardTestDispatcher(testScheduler)).build()
            assertIs<FileNotFoundException>(assertIs<ErrorResult>(loader.execute(request)).throwable)
            assertEquals(0, opens.get())
            assertEquals(0, closes.get())
            assertNull(input)
            assertEquals(2, provider.nullOpens, "Both fixture and Coil must take the actual registered-provider null path")
        } finally { loader.shutdown() }
    }

    @Test fun actualCoilDecoderFailureClosesTheTransferredAndroidSource() = mainTest {
        val failure = IOException("decoder failed after actual file read")
        val loader = ImageLoader.Builder(context).components { add(KmpFileFetcher.Factory()) }.build()
        try {
            val request = ImageRequest.Builder(context).data(file).coroutineContext(StandardTestDispatcher(testScheduler))
                .decoderFactory(Decoder.Factory { result, _, _ -> Decoder {
                    assertTrue(checkNotNull(input).fd.valid())
                    assertEquals(0, result.source.source().readByte().toInt())
                    throw failure
                } }).build()
            val reported = assertIs<IOException>(assertIs<ErrorResult>(loader.execute(request)).throwable)
            assertEquals(failure.message, reported.message)
            // JVM coroutine stack-trace recovery can copy an exception across a
            // dispatcher boundary, retaining the original as its cause. Do not
            // disable recovery; require the exact injected origin and truthful type.
            val causes = mutableSetOf<Throwable>()
            var cause: Throwable? = reported
            while (cause != null && causes.size < 8 && causes.add(cause)) cause = cause.cause
            assertTrue(causes.any { it === failure }, "Reported decoder error must retain the exact injected origin")
            assertReleased()
        } finally { loader.shutdown() }
    }

    @Test fun actualCoilCancellationClosesAfterTransferWithoutLateSuccess() = mainTest {
        val entered = CompletableDeferred<Unit>()
        val loader = ImageLoader.Builder(context).components { add(KmpFileFetcher.Factory()) }.build()
        val request = ImageRequest.Builder(context).data(file).coroutineContext(StandardTestDispatcher(testScheduler))
            .decoderFactory(Decoder.Factory { result, _, _ -> Decoder {
                assertTrue(checkNotNull(input).fd.valid())
                assertEquals(0, result.source.source().readByte().toInt())
                entered.complete(Unit)
                awaitCancellation()
            } }).build()
        var cancelled = false
        val job = launch {
            try { loader.execute(request); error("Paused decoder must not complete") }
            catch (failure: CancellationException) { cancelled = true; throw failure }
        }
        try {
            withTimeout(10_000) { entered.await() }
            assertEquals(0, closes.get(), "Cancel while the real descriptor is still owned by Coil")
            job.cancelAndJoin()
            assertTrue(cancelled)
            assertReleased()
        } finally { job.cancelAndJoin(); loader.shutdown() }
    }

    private fun assertReleased() {
        assertEquals(1, opens.get())
        assertEquals(1, closes.get())
        assertFalse(checkNotNull(input).fd.valid(), "Real FileInputStream descriptor must be invalid, not just a recorded close callback")
        assertFailsWith<IOException> { checkNotNull(input).read() }
        assertEquals(300_000L, local.length())
    }

    private fun mainTest(block: suspend TestScope.() -> Unit) = runTest {
        Dispatchers.setMain(StandardTestDispatcher(testScheduler))
        try { block() } finally { Dispatchers.resetMain() }
    }

    private inner class TrackedInput(private val delegate: FileInputStream) : FilterInputStream(delegate) {
        val fd get() = delegate.fd
        override fun close() { try { super.close() } finally { closes.incrementAndGet() } }
    }

    class MetadataProvider : ContentProvider() {
        var failure: IllegalStateException? = null
        var nullInput = false
        var nullOpens = 0
        override fun onCreate(): Boolean = true
        override fun openAssetFile(uri: Uri, mode: String): AssetFileDescriptor? {
            check(nullInput) { "Positive file reads must use the controlled supplier, not an unregistered stream" }
            nullOpens++
            return null
        }
        override fun getType(uri: Uri): String { failure?.let { throw it }; return "application/octet-stream" }
        override fun query(uri: Uri, projection: Array<out String>?, selection: String?, selectionArgs: Array<out String>?, sortOrder: String?): Cursor? = null
        override fun insert(uri: Uri, values: ContentValues?): Uri? = error("unused")
        override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?): Int = error("unused")
        override fun update(uri: Uri, values: ContentValues?, selection: String?, selectionArgs: Array<out String>?): Int = error("unused")
    }
}
