package com.mohamedrejeb.calf.io

import android.content.Context
import android.net.Uri
import android.os.Bundle
import android.os.Process
import android.os.ParcelFileDescriptor
import android.os.SystemClock
import android.system.Os
import android.system.OsConstants
import androidx.core.content.FileProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.mohamedrejeb.calf.io.instrumentation.DeviceIoFileProvider
import java.io.File
import java.io.IOException
import java.util.UUID
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.io.Buffer
import kotlinx.io.readByteArray
import org.junit.After
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNotEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Real Android framework/AndroidX FileProvider integration, not Robolectric or a sample screen. */
@RunWith(AndroidJUnit4::class)
class KmpFileDeviceTest {
    private lateinit var context: Context
    private lateinit var directory: File
    private lateinit var authority: String

    @Before fun createOwnedFixture() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        context = instrumentation.targetContext
        // AGP's KMP library tests are self-instrumenting. Verify, rather than assume, the APK.
        assertEquals(instrumentation.context.packageName, context.packageName)
        authority = context.packageName + ".io-device-files"
        val provider = assertNotNull(context.packageManager.resolveContentProvider(authority, 0))
        assertEquals(Process.myUid(), provider.applicationInfo.uid)
        assertFalse(provider.exported)
        assertTrue(provider.grantUriPermissions)
        directory = File(context.cacheDir, "nativecmpkit-io-device/" + UUID.randomUUID())
        assertTrue(directory.mkdirs())
    }

    @After fun removeOnlyOwnedFixture() {
        if (::directory.isInitialized) assertTrue(directory.deleteRecursively())
    }

    @Test fun nativeDescriptorProbeCountsFilesAndPipeEndsWithoutLeaksOrOffsetChanges() {
        val file = fixture("probe-offset.bin", byteArrayOf(1, 2, 3, 4, 5))
        val identity = DeviceDescriptorIdentity.of(file)
        val other = fixture("probe-other.bin", byteArrayOf(9, 8, 7))
        val otherIdentity = DeviceDescriptorIdentity.of(other)
        assertTrue(identity.device != otherIdentity.device || identity.inode != otherIdentity.inode)
        ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_READ_ONLY).use { opened ->
            assertEquals(identity, DeviceDescriptorIdentity.of(opened))
            assertEquals(2L, Os.lseek(opened.fileDescriptor, 2L, OsConstants.SEEK_SET))
            ParcelFileDescriptor.open(other, ParcelFileDescriptor.MODE_READ_ONLY).use { second ->
                assertEquals(otherIdentity, DeviceDescriptorIdentity.of(second))
                assertEquals(1L, Os.lseek(second.fileDescriptor, 1L, OsConstants.SEEK_SET))
                assertTrue(other.delete(), "an unlinked-but-open fixture must still be detectable")
                repeat(4) {
                    assertEquals(1, openDeviceDescriptorsFor(identity), "the known-open file must be detected")
                    assertEquals(1, openDeviceDescriptorsFor(otherIdentity), "deleted names must not hide open descriptors")
                    assertEquals(2L, Os.lseek(opened.fileDescriptor, 0L, OsConstants.SEEK_CUR))
                    assertEquals(1L, Os.lseek(second.fileDescriptor, 0L, OsConstants.SEEK_CUR))
                }
            }
            assertEquals(0, openDeviceDescriptorsFor(otherIdentity))
        }
        assertEquals(0, openDeviceDescriptorsFor(identity), "probe duplicates must not retain the file")

        val pipe = ParcelFileDescriptor.createPipe()
        lateinit var pipeIdentity: DeviceDescriptorIdentity
        pipe[0].use { reader ->
            pipe[1].use { writer ->
                pipeIdentity = DeviceDescriptorIdentity.of(reader)
                val second = DeviceDescriptorIdentity.of(writer)
                assertTrue(OsConstants.S_ISFIFO(pipeIdentity.mode))
                assertTrue(OsConstants.S_ISFIFO(second.mode))
                assertNotEquals(0L, pipeIdentity.inode)
                assertEquals(pipeIdentity, second)
                repeat(4) { assertEquals(2, openDeviceDescriptorsFor(pipeIdentity)) }
            }
            repeat(4) { assertEquals(1, openDeviceDescriptorsFor(pipeIdentity)) }
        }
        assertEquals(0, openDeviceDescriptorsFor(pipeIdentity), "probe duplicates must not retain either pipe end")
    }

    @Test fun fdInfoParserAcceptsUnsignedInodesAndRejectsInvalidRecords() {
        assertEquals(0uL, parseDeviceFdInfoInode("pos:\t99\nmnt_id:\t7\nino:\t0\n".lineSequence()))
        assertEquals(ULong.MAX_VALUE, parseDeviceFdInfoInode("ino:\t18446744073709551615\n".lineSequence()))
        for (invalid in listOf("pos: 0", "ino: 1\nino: 2", "ino:", "ino: -1", "ino: +1",
            "ino: 0x10", "ino: 1 2", "ino: 18446744073709551616")) {
            assertFailsWith<IllegalStateException> { parseDeviceFdInfoInode(invalid.lineSequence()) }
        }
    }

    @Test fun wholeArrayReadClosesTheActualProviderDescriptor() = runBlocking {
        val bytes = ByteArray(131_079) { (it % 251).toByte() }
        val file = fixture("binary.bin", bytes)
        val uri = uri(file)
        val identity = DeviceDescriptorIdentity.of(file)
        assertEquals(0, openDeviceDescriptorsFor(identity))

        val actual = withContext(Dispatchers.IO) { KmpFile(uri).readByteArray(context) }

        assertContentEquals(bytes, actual)
        assertEquals(1, stats(uri).getInt("opens"))
        assertNotEquals(Process.myPid(), stats(uri).getInt("providerPid"), "must cross an actual process boundary")
        assertEquals(0, openDeviceDescriptorsFor(identity))
    }

    @Test fun returnedSourceOwnsItsNativeDescriptorUntilExplicitClose() = runBlocking(Dispatchers.IO) {
        val bytes = ByteArray(100_003) { (it % 239).toByte() }
        val file = fixture("stream.bin", bytes)
        val identity = DeviceDescriptorIdentity.of(file)
        val source = KmpFile(uri(file)).source(context)
        try {
            assertTrue(openDeviceDescriptorsFor(identity) > 0)
            val buffer = Buffer()
            while (source.readAtMostTo(buffer, 4096) != -1L) { }
            assertContentEquals(bytes, buffer.readByteArray())
            assertTrue(openDeviceDescriptorsFor(identity) > 0, "EOF does not transfer close ownership")
        } finally {
            source.close()
        }
        assertEquals(0, openDeviceDescriptorsFor(identity))
    }

    @Test fun unknownSizeOverrunThrowsInsteadOfReturningTruncatedDataAndCloses() = runBlocking(Dispatchers.IO) {
        val bytes = ByteArray(100_003) { (it % 127).toByte() }
        val file = fixture("unknown.bin", bytes)
        val uri = uri(file, DeviceIoFileProvider.UNKNOWN_SIZE)
        val reference = KmpFile(uri)
        assertNull(reference.getSize(context), "exercise the consuming bound, not metadata short-circuit")

        assertFailsWith<IOException> { reference.readByteArray(context, maxBytes = 4096) }

        assertEquals(1, stats(uri).getInt("opens"))
        assertEquals(0, openDeviceDescriptorsFor(DeviceDescriptorIdentity.of(file)))
        assertContentEquals(bytes, file.readBytes())
    }

    @Test fun knownOversizeIsRejectedBeforeAnyNativeStreamIsOpened() = runBlocking(Dispatchers.IO) {
        val file = fixture("known.bin", ByteArray(64) { it.toByte() })
        val uri = uri(file)
        assertEquals(64L, KmpFile(uri).getSize(context))

        assertFailsWith<IOException> { KmpFile(uri).readByteArray(context, maxBytes = 63) }

        assertEquals(0, stats(uri).getInt("opens"))
        assertEquals(0, openDeviceDescriptorsFor(DeviceDescriptorIdentity.of(file)))
    }

    @Test fun emptyAndExactLimitFilesReturnAllBytesAndClose() = runBlocking(Dispatchers.IO) {
        for (bytes in listOf(byteArrayOf(), byteArrayOf(1, 0, -1, 4))) {
            val file = fixture("exact-${bytes.size}.bin", bytes)
            val uri = uri(file, DeviceIoFileProvider.UNKNOWN_SIZE)
            assertContentEquals(bytes, KmpFile(uri).readByteArray(context, maxBytes = bytes.size))
            assertEquals(1, stats(uri).getInt("opens"))
            assertEquals(0, openDeviceDescriptorsFor(DeviceDescriptorIdentity.of(file)))
        }
    }

    @Test fun providerReadErrorIsNotEmptySuccessAndClosesTheRealTransferredPipe() = runBlocking(Dispatchers.IO) {
        assertReadErrorCloses(bounded = false)
    }

    @Test fun boundedReadAlsoClosesOnActualProviderReadError() = runBlocking(Dispatchers.IO) {
        assertReadErrorCloses(bounded = true)
    }

    @Test fun alreadyCancelledCallerDoesNotOpenAProviderStream() = runBlocking {
        val file = fixture("cancelled.bin", byteArrayOf(1, 2, 3))
        val uri = uri(file)
        val child = launch(start = CoroutineStart.UNDISPATCHED) {
            cancel()
            KmpFile(uri).readByteArray(context, maxBytes = 100)
        }
        child.join()
        assertTrue(child.isCancelled)
        assertEquals(0, stats(uri).getInt("opens"))
        assertEquals(0, openDeviceDescriptorsFor(DeviceDescriptorIdentity.of(file)))
    }

    @Test fun repeatedSuccessAndConsumingFailureDoNotAccumulateDescriptors() = runBlocking(Dispatchers.IO) {
        val bytes = ByteArray(8193) { it.toByte() }
        val file = fixture("repeated.bin", bytes)
        val normal = uri(file)
        val unknown = uri(file, DeviceIoFileProvider.UNKNOWN_SIZE)
        val identity = DeviceDescriptorIdentity.of(file)
        repeat(16) {
            assertContentEquals(bytes, KmpFile(normal).readByteArray(context))
            assertFailsWith<IOException> { KmpFile(unknown).readByteArray(context, maxBytes = 8) }
            assertEquals(0, openDeviceDescriptorsFor(identity), "iteration $it leaked a file descriptor")
        }
        assertEquals(16, stats(normal).getInt("opens"))
        assertEquals(16, stats(unknown).getInt("opens"))
    }

    @Test fun contentReferenceRetainsItsUriAndNeverInventsAFilesystemPath() {
        val file = fixture("résumé-日本語.txt", byteArrayOf(9, 0, -1))
        val uri = uri(file)
        val reference = KmpFile(uri)
        assertTrue(reference.exists(context))
        assertFalse(reference.isDirectory(context))
        assertEquals(file.name, reference.getName(context))
        assertEquals(3L, reference.getSize(context))
        assertEquals("text/plain", reference.getMimeType(context))
        assertNull(reference.getPath(context))
        assertEquals(uri.toString(), reference.toUriString())
        assertEquals(uri, assertNotNull(KmpFile.fromUriString(uri.toString())).uri)
        assertFalse(reference.releaseTemporaryCopy(context))
        assertTrue(file.exists(), "caller-owned Android content must not be deleted as iOS staging")
    }

    private suspend fun assertReadErrorCloses(bounded: Boolean) {
        val bytes = ByteArray(512) { it.toByte() }
        val file = fixture("read-error.bin", bytes)
        val uri = uri(file, DeviceIoFileProvider.READ_ERROR)
        val error = assertFailsWith<IOException> {
            if (bounded) KmpFile(uri).readByteArray(context, maxBytes = 1024)
            else KmpFile(uri).readByteArray(context)
        }
        assertTrue(error.message.orEmpty().contains(DeviceIoFileProvider.READ_ERROR_MESSAGE))
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (!stats(uri).getBoolean("workerFinished") && SystemClock.elapsedRealtime() < deadline) {
            SystemClock.sleep(10)
        }
        val result = stats(uri)
        assertEquals(1, result.getInt("opens"))
        assertTrue(result.getBoolean("workerFinished"))
        assertFalse(result.getBoolean("workerFailed"), "the fixture producer itself must succeed")
        assertTrue(result.containsKey("pipeMode") && result.containsKey("pipeFdInfoInode"))
        val pipe = DeviceDescriptorIdentity.fromProvider(
            result.getLong("pipeDevice"), result.getLong("pipeInode"),
            result.getInt("pipeMode"), result.getLong("pipeFdInfoInode"),
        )
        assertNotEquals(0L, pipe.inode)
        assertEquals(0, openDeviceDescriptorsFor(pipe), "failed read leaked the returned real pipe descriptor")
        assertContentEquals(bytes, file.readBytes())
    }

    private fun fixture(name: String, bytes: ByteArray): File = File(directory, name).apply { writeBytes(bytes) }

    private fun uri(file: File, mode: String? = null): Uri =
        FileProvider.getUriForFile(context, authority, file).buildUpon().apply {
            if (mode != null) appendQueryParameter(DeviceIoFileProvider.FIXTURE_MODE, mode)
        }.build()

    private fun stats(uri: Uri): Bundle = assertNotNull(
        context.contentResolver.call(Uri.parse("content://$authority"), DeviceIoFileProvider.STATS, uri.toString(), null),
    )
}
