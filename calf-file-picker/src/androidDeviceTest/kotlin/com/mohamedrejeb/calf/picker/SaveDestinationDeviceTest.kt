package com.mohamedrejeb.calf.picker

import android.net.Uri
import android.os.ParcelFileDescriptor
import android.system.ErrnoException
import android.system.Os
import android.system.OsConstants
import com.mohamedrejeb.calf.io.KmpFile
import androidx.test.ext.junit.runners.AndroidJUnit4
import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
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

/** Real Android Os.stat/link/symlink and ContentResolver paths, with no Robolectric stat adapter. */
@RunWith(AndroidJUnit4::class)
class SaveDestinationDeviceTest {
    private lateinit var fixture: DeviceSaveFixture
    @Before fun setUp() { fixture = DeviceSaveFixture() }
    @After fun tearDown() { if (::fixture.isInitialized) fixture.close() }

    @Test fun nativeDescriptorProbeRejectsAKnownOpenFileWithoutChangingItsOffsetOrLeaking() {
        val file = fixture.file("probe-offset.bin", byteArrayOf(1, 2, 3, 4, 5))
        assertNotEquals(0L, Os.stat(file.path).st_ino)
        val other = fixture.file("probe-other.bin", byteArrayOf(9, 8, 7))
        lateinit var deletedIdentity: DeviceFileIdentity
        ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_READ_ONLY).use { opened ->
            val identity = DeviceFileIdentity.of(opened)
            assertEquals(2L, Os.lseek(opened.fileDescriptor, 2L, OsConstants.SEEK_SET))
            ParcelFileDescriptor.open(other, ParcelFileDescriptor.MODE_READ_ONLY).use { second ->
                deletedIdentity = DeviceFileIdentity.of(second)
                assertTrue(identity.device != deletedIdentity.device || identity.inode != deletedIdentity.inode)
                assertEquals(1L, Os.lseek(second.fileDescriptor, 1L, OsConstants.SEEK_SET))
                assertTrue(other.delete(), "an unlinked-but-open fixture must still be detectable")
                repeat(4) {
                    val failure = assertFailsWith<AssertionError> { assertNoDeviceFileDescriptors(file) }
                    assertTrue(failure.message.orEmpty().contains("Library operation leaked a real descriptor"))
                    assertEquals(1, openDeviceFileDescriptorsFor(deletedIdentity))
                    assertEquals(2L, Os.lseek(opened.fileDescriptor, 0L, OsConstants.SEEK_CUR))
                    assertEquals(1L, Os.lseek(second.fileDescriptor, 0L, OsConstants.SEEK_CUR))
                }
            }
        }
        assertNoDeviceFileDescriptors(file)
        assertEquals(0, openDeviceFileDescriptorsFor(deletedIdentity))
    }

    @Test fun fdInfoParserRejectsMissingDuplicateAndMalformedKernelInodes() {
        assertEquals(0uL, parseDeviceFdInfoInode("pos:\t99\nmnt_id:\t7\nino:\t0\n".lineSequence()))
        assertEquals(ULong.MAX_VALUE, parseDeviceFdInfoInode("ino:\t18446744073709551615\n".lineSequence()))
        for (invalid in listOf("pos: 0", "ino: 1\nino: 2", "ino:", "ino: -1", "ino: +1",
            "ino: 0x10", "ino: 1 2", "ino: 18446744073709551616")) {
            assertFailsWith<IllegalStateException> { parseDeviceFdInfoInode(invalid.lineSequence()) }
        }
    }

    @Test fun distinctNativeInodesCopyAllBytesAndCloseBothFiles() = runBlocking(Dispatchers.IO) {
        val bytes = ByteArray(131_079) { (it % 251).toByte() }
        val source = fixture.file("source.bin", bytes)
        val destination = fixture.file("destination.bin", byteArrayOf(9, 8))
        val first = Os.stat(source.path)
        val second = Os.stat(destination.path)
        assertNotEquals(0L, first.st_ino)
        assertNotEquals(0L, second.st_ino)
        assertTrue(first.st_dev != second.st_dev || first.st_ino != second.st_ino)
        assertFalse(fixture.resolver.saveUrisReferToSameFile(Uri.fromFile(source), Uri.fromFile(destination)))

        assertNull(fixture.resolver.writeSaveSource(SaveSource.File(KmpFile(Uri.fromFile(source))), Uri.fromFile(destination)))

        assertContentEquals(bytes, source.readBytes())
        assertContentEquals(bytes, destination.readBytes())
        assertNoDeviceFileDescriptors(source)
        assertNoDeviceFileDescriptors(destination)
    }

    @Test fun actualHardLinkIsNotTruncatedOrDeleted() = runBlocking(Dispatchers.IO) {
        val source = fixture.file("hardlink-source", CONTENT)
        val alias = File(fixture.directory, "hardlink-alias")
        Os.link(source.path, alias.path)
        val first = Os.stat(source.path)
        val second = Os.stat(alias.path)
        assertNotEquals(0L, first.st_ino)
        assertEquals(first.st_dev, second.st_dev)
        assertEquals(first.st_ino, second.st_ino)
        assertTrue(first.st_nlink >= 2)
        assertTrue(fixture.resolver.saveUrisReferToSameFile(Uri.fromFile(source), Uri.fromFile(alias)))

        assertNull(fixture.resolver.writeSaveSource(SaveSource.File(KmpFile(Uri.fromFile(source))), Uri.fromFile(alias)))

        assertTrue(source.exists())
        assertTrue(alias.exists())
        assertContentEquals(CONTENT, source.readBytes())
        assertContentEquals(CONTENT, alias.readBytes())
        assertNoDeviceFileDescriptors(source)
    }

    @Test fun actualSymlinkAndCanonicalPathAliasesPreserveTheOriginal() = runBlocking(Dispatchers.IO) {
        val source = fixture.file("symlink-source", CONTENT)
        val symlink = File(fixture.directory, "symlink-alias")
        Os.symlink(source.path, symlink.path)
        for (alias in listOf(symlink, File(fixture.directory, "./symlink-source"))) {
            assertTrue(fixture.resolver.saveUrisReferToSameFile(Uri.fromFile(source), Uri.fromFile(alias)))
            assertNull(fixture.resolver.writeSaveSource(SaveSource.File(KmpFile(Uri.fromFile(source))), Uri.fromFile(alias)))
            assertContentEquals(CONTENT, source.readBytes())
            assertContentEquals(CONTENT, alias.readBytes())
        }
        assertNoDeviceFileDescriptors(source)
    }

    @Test fun emptyContentDoesNotMeanUnknownOrMatchingNativeIdentity() = runBlocking(Dispatchers.IO) {
        val source = fixture.file("empty-source", byteArrayOf())
        val otherEmpty = fixture.file("other-empty", byteArrayOf())
        val destination = fixture.file("old-content", CONTENT)
        assertEquals(0L, Os.stat(source.path).st_size)
        assertNotEquals(0L, Os.stat(source.path).st_ino)
        assertNotEquals(0L, Os.stat(otherEmpty.path).st_ino)
        assertNotEquals(Os.stat(source.path).st_ino, Os.stat(otherEmpty.path).st_ino)
        assertFalse(fixture.resolver.saveUrisReferToSameFile(Uri.fromFile(source), Uri.fromFile(otherEmpty)))
        assertFalse(fixture.resolver.saveUrisReferToSameFile(Uri.fromFile(source), Uri.fromFile(destination)))

        assertNull(fixture.resolver.writeSaveSource(SaveSource.File(KmpFile(Uri.fromFile(source))), Uri.fromFile(destination)))

        assertContentEquals(byteArrayOf(), source.readBytes())
        assertContentEquals(byteArrayOf(), destination.readBytes())
        assertNoDeviceFileDescriptors(source)
        assertNoDeviceFileDescriptors(destination)
    }

    @Test fun missingSourceNeverAuthorizesWriteOrCleanupOfAnExistingDestination() = runBlocking(Dispatchers.IO) {
        val source = File(fixture.directory, "missing-source")
        val destination = fixture.file("preserved-destination", CONTENT)
        assertNotNull(fixture.resolver.writeSaveSource(SaveSource.File(KmpFile(Uri.fromFile(source))), Uri.fromFile(destination)))
        assertContentEquals(CONTENT, destination.readBytes())
        assertNoDeviceFileDescriptors(destination)
    }

    @Test fun onlyMissingDestinationIsCreatedAfterSourceIdentityIsKnown() = runBlocking(Dispatchers.IO) {
        val source = fixture.file("identified-source", CONTENT)
        val destination = File(fixture.directory, "new-destination")
        assertFalse(fixture.resolver.saveUrisReferToSameFile(Uri.fromFile(source), Uri.fromFile(destination)))
        assertNull(fixture.resolver.writeSaveSource(SaveSource.File(KmpFile(Uri.fromFile(source))), Uri.fromFile(destination)))
        assertContentEquals(CONTENT, source.readBytes())
        assertContentEquals(CONTENT, destination.readBytes())
        assertNoDeviceFileDescriptors(source)
        assertNoDeviceFileDescriptors(destination)
    }

    @Test fun realNotADirectoryStatErrorIsNotTreatedAsMissingDestination() = runBlocking(Dispatchers.IO) {
        val source = fixture.file("valid-source", CONTENT)
        val nonDirectory = fixture.file("not-directory", byteArrayOf(7, 6, 5))
        val destination = File(nonDirectory, "child")
        val statFailure = assertFailsWith<ErrnoException> { Os.stat(destination.path) }
        assertEquals(OsConstants.ENOTDIR, statFailure.errno, "exercise a real non-ENOENT identity failure")
        assertNotNull(fixture.resolver.writeSaveSource(SaveSource.File(KmpFile(Uri.fromFile(source))), Uri.fromFile(destination)))
        assertContentEquals(CONTENT, source.readBytes())
        assertContentEquals(byteArrayOf(7, 6, 5), nonDirectory.readBytes())
        assertNoDeviceFileDescriptors(source)
        assertNoDeviceFileDescriptors(nonDirectory)
    }

    @Test fun realTreeAndSingleDocumentAliasesOpenOnlyForReadAndNeverDelete() = runBlocking(Dispatchers.IO) {
        val source = fixture.file("same-document.bin", CONTENT)
        val treeUri = fixture.treeDocumentUri(source)
        val singleUri = fixture.documentUri(source)
        assertNotEquals(treeUri, singleUri)
        assertTrue(fixture.resolver.saveUrisReferToSameFile(treeUri, singleUri))

        assertNull(fixture.resolver.writeSaveSource(SaveSource.File(KmpFile(treeUri)), singleUri))

        assertContentEquals(CONTENT, source.readBytes())
        fixture.assertClosed(singleUri, reads = 1, writes = 0)
        assertEquals(0, fixture.stats(singleUri).getInt("writeAttempts"))
        assertEquals(0, fixture.stats(singleUri).getInt("deletes"))
        assertNoDeviceFileDescriptors(source)
    }

    @Test fun revokedReadOnAnIdentifiedDocumentAliasCannotTruncateOrDeleteIt() = runBlocking(Dispatchers.IO) {
        val source = fixture.file("unreadable-alias.bin", CONTENT)
        val singleUri = fixture.documentUri(source)
        assertNotNull(fixture.resolver.writeSaveSource(SaveSource.File(KmpFile(fixture.treeDocumentUri(source))), singleUri))
        assertContentEquals(CONTENT, source.readBytes())
        val stats = fixture.stats(singleUri)
        assertEquals(1, stats.getInt("readAttempts"))
        assertEquals(0, stats.getInt("readOpens"))
        assertEquals(0, stats.getInt("writeAttempts"))
        assertEquals(0, stats.getInt("deletes"))
        assertNoDeviceFileDescriptors(source)
    }

    @Test fun fileProviderToDocumentsProviderCopyUsesRealStreamsAndClosesThem() = runBlocking(Dispatchers.IO) {
        val bytes = ByteArray(65_537) { it.toByte() }
        val source = fixture.file("fileprovider-source.bin", bytes)
        val (destination, destinationUri) = fixture.createDocument("copied.bin")
        assertNull(fixture.resolver.writeSaveSource(SaveSource.File(KmpFile(fixture.fileProviderUri(source))), destinationUri))
        assertContentEquals(bytes, source.readBytes())
        assertContentEquals(bytes, destination.readBytes())
        fixture.assertClosed(destinationUri, reads = 0, writes = 1)
        assertNoDeviceFileDescriptors(source)
        assertNoDeviceFileDescriptors(destination)
    }

    @Test fun failedDistinctProviderSourceDeletesOnlyTheNewDocumentWithoutWritingIt() = runBlocking(Dispatchers.IO) {
        val source = fixture.file("unreadable-distinct.bin", CONTENT)
        val (destination, destinationUri) = fixture.createDocument("failed-copy.bin")
        assertNotNull(fixture.resolver.writeSaveSource(SaveSource.File(KmpFile(fixture.documentUri(source))), destinationUri))
        assertContentEquals(CONTENT, source.readBytes())
        assertFalse(destination.exists(), "actual DocumentsContract cleanup must remove the newly created destination")
        assertEquals(0, fixture.stats(destinationUri).getInt("writeAttempts"))
        assertEquals(1, fixture.stats(destinationUri).getInt("deletes"))
        assertNoDeviceFileDescriptors(source)
    }

    companion object { private val CONTENT = byteArrayOf(1, 2, 0, -1, 3, 9) }
}
