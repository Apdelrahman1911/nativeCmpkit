@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class, com.mohamedrejeb.calf.core.InternalCalfApi::class)

package com.mohamedrejeb.calf.picker

import com.mohamedrejeb.calf.io.*
import kotlinx.cinterop.addressOf
import kotlinx.cinterop.usePinned
import kotlinx.coroutines.runBlocking
import platform.Foundation.NSData
import platform.Foundation.NSFileManager
import platform.Foundation.NSTemporaryDirectory
import platform.Foundation.NSURL
import platform.Foundation.NSUUID
import platform.Foundation.dataWithBytes
import kotlin.test.*

/** Real Foundation copies/files. Deleting an owned source is not a cloud-provider expiry claim. */
class NativePickedCopyBoundaryTest {
    @Test fun readableUnicodeCopySurvivesDeletedOriginAndUriRestorationDoesNotInventCopyAccess() = runBlocking {
        val bytes = byteArrayOf(0, 1, 127, -128, -1, 37)
        val source = assertNotNull(stageExportData(copyData(bytes), "Résumé % 研究 🧪.bin"))
        val picked = assertNotNull(source.toStagedKmpFile())
        val path = assertNotNull(picked.getPath())
        val originUri = assertNotNull(picked.toUriString())
        try {
            assertEquals(picked.url.path, path, "Readable path is native decoded filesystem text, not encoded original URI")
            assertEquals(source.lastPathComponent, picked.getName())
            assertEquals(source.absoluteString, originUri)
            assertTrue(originUri.contains("%25"))
            assertNotEquals(source.path, path)
            assertTrue(removeStaging(source), "Controlled real source removal must actually succeed")
            assertFalse(NSFileManager.defaultManager.fileExistsAtPath(source.path!!))
            assertTrue(picked.exists())
            assertContentEquals(bytes, picked.readByteArray())
            val restoredOrigin = assertNotNull(KmpFile.fromUriString(originUri))
            assertEquals(originUri, restoredOrigin.toUriString())
            assertEquals(source.path, restoredOrigin.getPath())
            assertFalse(restoredOrigin.exists(), "URI serialization restores the origin, never a hidden temporary-copy capability")
            val escapedOrigin = NSURL(string = "https://example.invalid/percent%25%20slash%2Fname.bin")
            val metadataView = KmpFile(picked.url, escapedOrigin)
            assertEquals(escapedOrigin.lastPathComponent, metadataView.getName(), "Origin metadata follows NSURL's native component contract")
            assertEquals(escapedOrigin.absoluteString, metadataView.toUriString())
            assertEquals(path, metadataView.getPath(), "Slash-escaped origin metadata cannot replace the readable copy")
            assertNull(KmpFile.fromUriString(escapedOrigin.absoluteString!!))
        } finally { picked.releaseTemporaryCopy(); removeStaging(source) }
        assertFalse(NSFileManager.defaultManager.fileExistsAtPath(path))
    }

    @Test fun sameNamesHaveIndependentBytesAndExplicitPersistenceOutlivesTemporaryRelease() = runBlocking {
        val firstSource = assertNotNull(stageExportData(copyData(byteArrayOf(1, 2)), "same-name.bin"))
        val secondSource = assertNotNull(stageExportData(copyData(byteArrayOf(9, 0, -1)), "same-name.bin"))
        val first = assertNotNull(firstSource.toStagedKmpFile())
        val second = assertNotNull(secondSource.toStagedKmpFile())
        val manager = NSFileManager.defaultManager
        val directory = "${NSTemporaryDirectory().removeSuffix("/")}/nativecmpkit-persistence-${NSUUID().UUIDString}"
        val destination = NSURL.fileURLWithPath("$directory/same-name.bin")
        try {
            assertNotEquals(first.getPath(), second.getPath())
            assertEquals(first.getName(), second.getName())
            assertContentEquals(byteArrayOf(1, 2), first.readByteArray())
            assertContentEquals(byteArrayOf(9, 0, -1), second.readByteArray())
            assertTrue(manager.createDirectoryAtPath(directory, true, null, null))
            assertTrue(manager.copyItemAtURL(first.url, destination, error = null))
            assertTrue(first.releaseTemporaryCopy())
            assertTrue(second.releaseTemporaryCopy())
            assertFalse(first.exists())
            assertFalse(second.exists())
            assertContentEquals(byteArrayOf(1, 2), KmpFile(destination).readByteArray())
            assertTrue(manager.fileExistsAtPath(firstSource.path!!))
            assertTrue(manager.fileExistsAtPath(secondSource.path!!))
        } finally {
            first.releaseTemporaryCopy(); second.releaseTemporaryCopy()
            removeStaging(firstSource); removeStaging(secondSource)
            if (manager.fileExistsAtPath(directory)) assertTrue(manager.removeItemAtPath(directory, error = null))
        }
    }

    @Test fun repeatedRealCopyReadReleaseReturnsOwnedDirectoryAccountingToItsBaseline() = runBlocking {
        val source = assertNotNull(stageExportData(copyData(byteArrayOf(5, -1, 0)), "retained-source.bin"))
        val root = "${NSTemporaryDirectory().removeSuffix("/")}/calf-file-picker"
        fun count() = NSFileManager.defaultManager.contentsOfDirectoryAtPath(root, error = null)?.size ?: 0
        val before = count()
        try {
            repeat(30) {
                val picked = assertNotNull(source.toStagedKmpFile())
                try {
                    assertEquals(before + 1, count())
                    assertContentEquals(byteArrayOf(5, -1, 0), picked.readByteArray())
                    assertTrue(picked.releaseTemporaryCopy())
                    assertFalse(picked.releaseTemporaryCopy())
                } finally { picked.releaseTemporaryCopy() }
                assertEquals(before, count())
                assertTrue(NSFileManager.defaultManager.fileExistsAtPath(source.path!!))
            }
        } finally { removeStaging(source) }
        assertEquals(before, count())
    }
}

private fun copyData(bytes: ByteArray): NSData = bytes.usePinned {
    NSData.dataWithBytes(it.addressOf(0), bytes.size.toULong())
}
