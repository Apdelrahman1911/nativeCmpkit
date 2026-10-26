package com.mohamedrejeb.calf.io

import com.mohamedrejeb.calf.core.PlatformContext
import java.io.File
import kotlin.io.path.createTempDirectory
import kotlin.test.AfterTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull

class KmpFileMetadataTest {
    private val context = PlatformContext.INSTANCE
    private val directory = createTempDirectory("calf-io-metadata").toFile()

    @AfterTest
    fun deleteDirectory() {
        directory.deleteRecursively()
    }

    @Test
    fun fromUriStringReadsBackToUriString() {
        val file = KmpFile(File(directory, "Report Final.pdf"))

        val restored = assertNotNull(KmpFile.fromUriString(assertNotNull(file.toUriString())))

        assertEquals(file.file.absolutePath, restored.file.absolutePath)
    }

    @Test
    fun fromUriStringAcceptsAPlainPath() {
        // Absolute paths follow the actual host's drive/root/separator rules.
        // A Unix /tmp path is not absolute to java.io.File on Windows.
        val path = File(directory, "Report Final.pdf").absolutePath
        val restored = assertNotNull(KmpFile.fromUriString(path))

        assertEquals(path, restored.getPath(context))
    }

    @Test
    fun fromUriStringRejectsWhatIsNotAFile() {
        assertNull(KmpFile.fromUriString("https://example.com/Report.pdf"))
        assertNull(KmpFile.fromUriString("file:bad uri"))
        assertNull(KmpFile.fromUriString(""))
    }

    @Test
    fun getSizeIsTheNumberOfBytes() {
        val file = File(directory, "data.bin").apply { writeBytes(ByteArray(1_234)) }

        assertEquals(1_234L, KmpFile(file).getSize(context))
    }

    @Test
    fun getSizeOfAMissingFileOrADirectoryIsNull() {
        assertNull(KmpFile(File(directory, "missing.bin")).getSize(context))
        assertNull(KmpFile(directory).getSize(context))
    }

    @Test
    fun getMimeTypeFollowsTheExtension() {
        assertEquals("application/pdf", KmpFile(File(directory, "Report.PDF")).getMimeType(context))
        assertEquals("image/png", KmpFile(File(directory, "photo.png")).getMimeType(context))
        assertNull(KmpFile(File(directory, "data.calfunknown")).getMimeType(context))
    }
}
