package com.mohamedrejeb.calf.picker

import com.mohamedrejeb.calf.io.releaseTemporaryCopy
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.coroutines.CancellationException
import platform.Foundation.NSData
import platform.Foundation.NSFileManager
import platform.Foundation.NSTemporaryDirectory
import platform.Foundation.NSString
import platform.Foundation.precomposedStringWithCanonicalMapping
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

@OptIn(ExperimentalForeignApi::class)
class PickedCopyOwnershipTest {
    @Test fun oneHundredSelectionsWithLimitOneCreateOnlyOneOwnedDirectory() {
        val source = assertNotNull(stageExportData(NSData(), "source.bin"))
        val before = pickedDirectoryCount()
        val picked = stagePickedUrls(List(100) { source }, FilePickerSelectionMode.Multiple(1))
        try {
            assertEquals(1, picked.files.size)
            assertEquals(before + 1, pickedDirectoryCount())
        } finally {
            picked.files.forEach { it.releaseTemporaryCopy() }
            removeStaging(source)
        }
        assertEquals(before, pickedDirectoryCount())
    }

    @Test fun cancellationBetweenCopiesRemovesEveryUnreturnedCopy() {
        val source = assertNotNull(stageExportData(NSData(), "source.bin"))
        val before = pickedDirectoryCount()
        var checks = 0
        try {
            assertFailsWith<CancellationException> {
                stagePickedUrls(List(10) { source }) { if (++checks == 3) throw CancellationException("test cancellation") }
            }
            assertEquals(before, pickedDirectoryCount())
            assertTrue(NSFileManager.defaultManager.fileExistsAtPath(source.path!!))
        } finally { removeStaging(source) }
    }

    @Test fun releasedUnicodeCopyDisappearsButTheSourceRemainsAndReleaseIsIdempotent() {
        val source = assertNotNull(stageExportData(NSData(), "Résumé 研究%.bin"))
        val picked = assertNotNull(source.toStagedKmpFile())
        try {
            // Foundation/filesystem URLs may return the canonically decomposed
            // spelling. Preserve the source's actual component byte-for-byte;
            // do not change production names to satisfy a hard-coded NFC form.
            assertEquals(source.lastPathComponent, picked.url.lastPathComponent)
            assertEquals("Résumé 研究%.bin", (picked.url.lastPathComponent!! as NSString).precomposedStringWithCanonicalMapping)
            assertTrue(picked.releaseTemporaryCopy())
            assertFalse(picked.releaseTemporaryCopy())
            assertFalse(NSFileManager.defaultManager.fileExistsAtPath(picked.url.path!!))
            assertTrue(NSFileManager.defaultManager.fileExistsAtPath(source.path!!))
        } finally { picked.releaseTemporaryCopy(); removeStaging(source) }
    }

    private fun pickedDirectoryCount(): Int =
        NSFileManager.defaultManager.contentsOfDirectoryAtPath(
            "${NSTemporaryDirectory().removeSuffix("/")}/calf-file-picker", error = null,
        )?.size ?: 0
}
