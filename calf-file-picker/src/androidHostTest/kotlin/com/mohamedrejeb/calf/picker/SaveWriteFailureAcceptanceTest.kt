package com.mohamedrejeb.calf.picker

import android.content.ContentProvider
import android.content.ContentValues
import android.content.pm.ProviderInfo
import android.content.res.AssetFileDescriptor
import android.database.Cursor
import android.net.Uri
import android.os.Bundle
import android.provider.DocumentsContract
import android.system.ErrnoException
import android.system.OsConstants
import com.mohamedrejeb.calf.io.KmpFile
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.FileNotFoundException
import java.io.IOException
import java.io.InputStream
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.async
import kotlinx.coroutines.runBlocking
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config
import org.robolectric.shadows.ShadowContentResolver
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNotNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

/**
 * Executes the production resolver writer on real coroutine IO threads. Null opens go through
 * the actual host Android ContentResolver/ContentProvider contract. Registered counted streams
 * deterministically inject read, write and close faults; they are NOT device/OS grant/disk proof.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class SaveWriteFailureAcceptanceTest {
    @get:Rule val folder = TemporaryFolder()

    @Test fun nullOutputIsAnErrorAndDeletesOnlyTheNewDestination() = runBlocking {
        val provider = provider()
        val failure = assertNotNull(resolver.writeSaveSource(SaveSource.Bytes(CONTENT), DESTINATION))
        assertIs<FileNotFoundException>(failure.cause)
        assertTrue(failure.cause!!.message.orEmpty().contains("no output stream"))
        assertEquals(listOf("wt"), provider.openModes)
        assertCleaned(provider)
    }

    @Test fun nullInputCannotOpenOutputOrReportSuccessfulCopy() = runBlocking {
        val provider = provider()
        val failure = assertNotNull(resolver.writeSaveSource(SaveSource.File(KmpFile(SOURCE)), DESTINATION))
        assertIs<FileNotFoundException>(failure.cause)
        assertTrue(failure.cause!!.message.orEmpty().contains("no input stream"))
        assertEquals(listOf("r"), provider.openModes)
        assertCleaned(provider)
    }

    @Test fun accessRevokedDuringReadClosesBothStreamsAndCleansPartialOutput() = runBlocking {
        val provider = provider()
        val denied = SecurityException("Controlled provider read permission revoked")
        val input = TrackingInput(LARGE_CONTENT, readFailure = denied)
        val output = TrackingOutput()
        register(input, output)

        val failure = assertNotNull(resolver.writeSaveSource(SaveSource.File(KmpFile(SOURCE)), DESTINATION))

        assertOriginalFailure(denied, failure.cause)
        assertEquals(64 * 1024, output.size())
        assertContentEquals(LARGE_CONTENT.copyOf(64 * 1024), output.toByteArray())
        assertClosed(input, output)
        assertCleaned(provider)
    }

    @Test fun diskFullWriteErrorIsNotSuccessAndAllOwnedStreamsClose() = runBlocking {
        val provider = provider()
        val full = IOException("Controlled ENOSPC", ErrnoException("write", OsConstants.ENOSPC))
        val input = TrackingInput(LARGE_CONTENT)
        val output = TrackingOutput(writeFailure = full)
        register(input, output)

        val failure = assertNotNull(resolver.writeSaveSource(SaveSource.File(KmpFile(SOURCE)), DESTINATION))

        assertOriginalFailure(full, failure.cause)
        assertEquals(OsConstants.ENOSPC, assertIs<ErrnoException>(full.cause).errno)
        assertEquals(64 * 1024, output.size(), "The failure follows an actual completed production copy chunk")
        assertClosed(input, output)
        assertCleaned(provider)
    }

    @Test fun accessRevokedDuringWriteIsAnErrorWithClosedResources() = runBlocking {
        val provider = provider()
        val denied = SecurityException("Controlled provider write permission revoked")
        val input = TrackingInput(LARGE_CONTENT)
        val output = TrackingOutput(writeFailure = denied)
        register(input, output)

        val failure = assertNotNull(resolver.writeSaveSource(SaveSource.File(KmpFile(SOURCE)), DESTINATION))

        assertOriginalFailure(denied, failure.cause)
        assertEquals(64 * 1024, output.size())
        assertClosed(input, output)
        assertCleaned(provider)
    }

    @Test fun failingOutputAndInputCloseNeverBecomeSuccessOrLoseThePrimaryFailure() = runBlocking {
        val provider = provider()
        val outputClose = IOException("Controlled output close failure")
        val inputClose = IOException("Controlled input close failure")
        val input = TrackingInput(CONTENT, closeFailure = inputClose)
        val output = TrackingOutput(closeFailure = outputClose)
        register(input, output)

        val failure = assertNotNull(resolver.writeSaveSource(SaveSource.File(KmpFile(SOURCE)), DESTINATION))

        assertContentEquals(CONTENT, output.toByteArray(), "Writing all bytes is not success if close fails")
        assertOriginalFailure(outputClose, failure.cause)
        assertEquals(listOf(inputClose), outputClose.suppressed.toList())
        assertClosed(input, output)
        assertCleaned(provider)
    }

    @Test fun cancellationBetweenChunksPropagatesAndCleansWithoutAnotherWrite() = runBlocking {
        val provider = provider()
        val input = TrackingInput(LARGE_CONTENT)
        val output = TrackingOutput()
        register(input, output)
        val operation = async(start = CoroutineStart.LAZY) {
            resolver.writeSaveSource(SaveSource.File(KmpFile(SOURCE)), DESTINATION)
        }
        output.afterFirstWrite = { operation.cancel(CancellationException("Controlled copy cancellation")) }
        operation.start()

        assertFailsWith<CancellationException> { operation.await() }

        assertTrue(operation.isCancelled)
        assertEquals(1, input.reads.get())
        assertEquals(1, output.writes.get())
        assertEquals(64 * 1024, output.size())
        assertClosed(input, output)
        assertCleaned(provider)
    }

    @Test fun aNoProgressReadFailsRatherThanSpinningAndClosesItsOwner() = runBlocking {
        val provider = provider()
        val closes = AtomicInteger()
        val reads = AtomicInteger()
        val input = object : InputStream() {
            override fun read(): Int = error("The production copy must use its bounded buffer")
            override fun read(bytes: ByteArray, offset: Int, length: Int): Int { reads.incrementAndGet(); return 0 }
            override fun close() { closes.incrementAndGet() }
        }
        val output = TrackingOutput()
        register(input, output)

        val failure = assertNotNull(resolver.writeSaveSource(SaveSource.File(KmpFile(SOURCE)), DESTINATION))

        assertEquals("Source made no progress", assertIs<IOException>(failure.cause).message)
        assertEquals(1, reads.get())
        assertEquals(1, closes.get())
        assertEquals(1, output.closes.get())
        assertEquals(0, output.writes.get())
        assertCleaned(provider)
    }

    private val resolver get() = RuntimeEnvironment.getApplication().contentResolver

    private fun provider(): NullOpenProvider = NullOpenProvider(
        folder.newFile("untouched-source.bin").apply { writeBytes(CONTENT) },
        folder.newFile("new-destination.bin"),
    ).also {
        it.attachInfo(RuntimeEnvironment.getApplication(), ProviderInfo().apply { authority = AUTHORITY })
        ShadowContentResolver.registerProviderInternal(AUTHORITY, it)
    }

    private fun register(input: InputStream, output: TrackingOutput) {
        shadowOf(resolver).registerInputStream(SOURCE, input)
        shadowOf(resolver).registerOutputStream(DESTINATION, output)
    }

    private fun assertCleaned(provider: NullOpenProvider) {
        assertEquals(listOf(DESTINATION), provider.deletedUris, "Cleanup must target only the new destination once")
        assertFalse(provider.destination.exists())
        assertContentEquals(CONTENT, provider.source.readBytes(), "Failure/cancellation must never remove the source")
    }

    private fun assertClosed(input: TrackingInput, output: TrackingOutput) {
        assertEquals(1, input.closes.get())
        assertEquals(1, output.closes.get())
    }

    private fun assertOriginalFailure(expected: Exception, actual: Throwable?) {
        val reported = assertNotNull(actual)
        if (reported === expected) return
        // Coroutine debug stack-trace recovery can copy an exception across withContext.
        // Require the same type/message AND the exact original causal object, not arbitrary
        // wrapping or a newly fabricated error. Suppressed close errors stay on that original.
        assertEquals(expected.javaClass, reported.javaClass)
        assertEquals(expected.message, reported.message)
        assertSame(expected, reported.cause)
    }

    class NullOpenProvider(val source: File, val destination: File) : ContentProvider() {
        val openModes = mutableListOf<String>()
        val deletedUris = mutableListOf<Uri>()
        override fun onCreate(): Boolean = true
        override fun openAssetFile(uri: Uri, mode: String): AssetFileDescriptor? { openModes += mode; return null }
        override fun call(method: String, arg: String?, extras: Bundle?): Bundle? {
            check(method == "android:deleteDocument")
            val uri = checkNotNull(extras?.getParcelable<Uri>("uri"))
            check(uri == DESTINATION)
            deletedUris += uri
            check(destination.delete())
            return Bundle()
        }
        override fun query(uri: Uri, projection: Array<out String>?, selection: String?, selectionArgs: Array<out String>?, sortOrder: String?): Cursor? = null
        override fun getType(uri: Uri): String = "application/octet-stream"
        override fun insert(uri: Uri, values: ContentValues?): Uri? = error("unused")
        override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?): Int = error("unused")
        override fun update(uri: Uri, values: ContentValues?, selection: String?, selectionArgs: Array<out String>?): Int = error("unused")
    }

    private class TrackingInput(bytes: ByteArray, private val readFailure: RuntimeException? = null,
                                private val closeFailure: IOException? = null) : ByteArrayInputStream(bytes) {
        val reads = AtomicInteger()
        val closes = AtomicInteger()
        override fun read(bytes: ByteArray, offset: Int, length: Int): Int {
            if (reads.incrementAndGet() == 2) readFailure?.let { throw it }
            return super.read(bytes, offset, length)
        }
        override fun close() { closes.incrementAndGet(); super.close(); closeFailure?.let { throw it } }
    }

    private class TrackingOutput(private val writeFailure: Exception? = null,
                                 private val closeFailure: IOException? = null) : ByteArrayOutputStream() {
        val writes = AtomicInteger()
        val closes = AtomicInteger()
        var afterFirstWrite: (() -> Unit)? = null
        override fun write(bytes: ByteArray, offset: Int, length: Int) {
            val count = writes.incrementAndGet()
            if (count == 2) writeFailure?.let { throw it }
            super.write(bytes, offset, length)
            if (count == 1) afterFirstWrite?.invoke()
        }
        override fun close() { closes.incrementAndGet(); super.close(); closeFailure?.let { throw it } }
    }

    companion object {
        private const val AUTHORITY = "nativecmpkit.picker.test.write-failures"
        private val SOURCE = DocumentsContract.buildDocumentUri(AUTHORITY, "source")
        private val DESTINATION = DocumentsContract.buildDocumentUri(AUTHORITY, "new-destination")
        private val CONTENT = byteArrayOf(1, 2, 0, -1, 3, 9)
        private val LARGE_CONTENT = ByteArray(131_079) { (it % 251).toByte() }
    }
}
