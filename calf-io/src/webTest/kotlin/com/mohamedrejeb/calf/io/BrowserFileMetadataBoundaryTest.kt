package com.mohamedrejeb.calf.io

import com.mohamedrejeb.calf.core.PlatformContext
import kotlinx.coroutines.async
import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertNull

/** Real DOM File/FileReader: equal display names are not paths or serialized identities. */
class BrowserFileMetadataBoundaryTest {
    @Test fun equalUnicodeDisplayNamesRetainIndependentBytesWithoutInventingPathsOrUris() = runTest {
        val name = "Résumé % 研究.bin"
        val firstContent = "\u0000A\u007f"
        val secondContent = "different % ñ bytes"
        val first = KmpFile(browserFixtureFile(name, firstContent))
        val second = KmpFile(browserFixtureFile(name, secondContent))
        val context = PlatformContext.INSTANCE
        for (file in listOf(first, second)) {
            assertEquals(name, file.getName(context))
            assertEquals(name, file.getName())
            assertNull(file.getPath(context))
            assertNull(file.getPath())
            assertNull(file.toUriString())
        }
        assertNull(KmpFile.fromUriString(name), "A display name cannot restore either browser File")
        assertNull(KmpFile.fromUriString("file:///unavailable.bin"))
        val firstRead = async { first.readByteArray(context) }
        val secondRead = async { second.readByteArray() }
        assertContentEquals(firstContent.encodeToByteArray(), firstRead.await())
        assertContentEquals(secondContent.encodeToByteArray(), secondRead.await())
        assertEquals(firstContent.encodeToByteArray().size.toLong(), first.getSize(context))
        assertEquals(secondContent.encodeToByteArray().size.toLong(), second.getSize(context))
        // Repeat after both readers complete: no filename-keyed content identity may leak through.
        assertContentEquals(firstContent.encodeToByteArray(), first.readByteArray())
        assertContentEquals(secondContent.encodeToByteArray(), second.readByteArray(context))
    }
}
