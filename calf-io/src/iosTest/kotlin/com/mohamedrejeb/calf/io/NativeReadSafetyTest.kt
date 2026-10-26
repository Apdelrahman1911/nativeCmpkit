package com.mohamedrejeb.calf.io

import com.mohamedrejeb.calf.core.InternalCalfApi
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.addressOf
import kotlinx.cinterop.usePinned
import kotlinx.coroutines.test.runTest
import kotlinx.io.IOException
import kotlinx.io.buffered
import kotlinx.io.files.FileNotFoundException
import kotlinx.io.readByteArray
import platform.Foundation.NSData
import platform.Foundation.NSFileManager
import platform.Foundation.NSTemporaryDirectory
import platform.Foundation.NSURL
import platform.Foundation.NSUUID
import platform.Foundation.create
import platform.Foundation.writeToURL
import kotlin.test.AfterTest
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

@OptIn(ExperimentalForeignApi::class, InternalCalfApi::class)
class NativeReadSafetyTest {
    private val directory = "${NSTemporaryDirectory()}/nativecmpkit-read-${NSUUID().UUIDString}"
    init {
        check(NSFileManager.defaultManager.createDirectoryAtPath(directory, true, null, null))
    }
    @AfterTest fun cleanup() { NSFileManager.defaultManager.removeItemAtPath(directory, null) }

    @Test fun readsARealEmptyNSDataFileWithoutAddressOfZero() = runTest {
        val file = write("empty", byteArrayOf())
        assertContentEquals(byteArrayOf(), file.readByteArray())
        assertTrue(file.isFile())
    }

    @Test fun realNativeMemcpyAndStreamHaveIdenticalBinaryBytes() = runTest {
        val bytes = byteArrayOf(0, -1, 42, -128, 127, 1)
        val file = write("binary", bytes)
        assertContentEquals(bytes, file.readByteArray())
        assertContentEquals(bytes, file.source().buffered().use { it.readByteArray() })
    }

    @Test fun missingFileIsNotEmptyOrAFile() = runTest {
        val missing = KmpFile(NSURL.fileURLWithPath("$directory/missing"))
        assertFailsWith<IOException> { missing.readByteArray() }
        assertFalse(missing.isFile())
    }

    @Test fun temporaryOwnershipDoesNotDeleteAnArbitraryOriginal() {
        val original = write("original", byteArrayOf(7))
        val copy = write("copy", byteArrayOf(7))
        val owned = KmpFile(copy.url, original.url) {
            NSFileManager.defaultManager.removeItemAtURL(copy.url, null)
        }
        assertFalse(original.releaseTemporaryCopy())
        assertTrue(owned.releaseTemporaryCopy())
        assertFalse(owned.releaseTemporaryCopy())
        assertTrue(original.exists())
        assertFalse(copy.exists())
    }

    @Test fun aNonFileUrlWithTheSamePathCannotReadOrDescribeALocalFile() = runTest {
        val bytes = byteArrayOf(5, 0, -1, 8)
        val local = write("private.bin", bytes)
        // A real NSURL, not a filesystem/NSURL shadow. Rejection must occur before any HTTP
        // operation; the loopback port also avoids an external endpoint if this regresses.
        val remote = KmpFile(NSURL(string = "https://127.0.0.1:1${local.url.path}"))
        assertEquals(local.url.path, remote.url.path, "NSURL.path alone is not file authority")
        assertNull(remote.getPath())
        assertFalse(remote.exists())
        assertFalse(remote.isFile())
        assertFalse(remote.isDirectory())
        assertNull(remote.getSize())
        assertNull(remote.createBookmark())
        assertFailsWith<FileNotFoundException> { remote.source().use { } }
        assertFailsWith<FileNotFoundException> { remote.readByteArray() }
        assertFailsWith<FileNotFoundException> { remote.readByteArray(maxBytes = 16) }
        assertEquals("private.bin", remote.getName(), "origin metadata is not content access")
        assertContentEquals(bytes, local.readByteArray())
    }

    @Test fun aNonFileUrlCannotDescribeALocalDirectoryOrDeleteAnOriginal() {
        val original = write("kept.bin", byteArrayOf(9))
        val remoteDirectory = KmpFile(NSURL(string = "https://127.0.0.1:1$directory"))
        assertNull(remoteDirectory.getPath())
        assertFalse(remoteDirectory.exists())
        assertFalse(remoteDirectory.isDirectory())
        assertFalse(remoteDirectory.releaseTemporaryCopy())
        assertNull(remoteDirectory.getSize())
        assertTrue(original.exists())
    }

    private fun write(name: String, bytes: ByteArray): KmpFile {
        val url = NSURL.fileURLWithPath("$directory/$name")
        val data = if (bytes.isEmpty()) NSData() else bytes.usePinned {
            NSData.create(bytes = it.addressOf(0), length = bytes.size.toULong())
        }
        check(data.writeToURL(url, atomically = true))
        return KmpFile(url)
    }
}
