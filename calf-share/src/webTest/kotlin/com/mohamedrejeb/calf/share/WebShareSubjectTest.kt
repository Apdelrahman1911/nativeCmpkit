package com.mohamedrejeb.calf.share

import com.mohamedrejeb.calf.io.KmpFile
import org.w3c.files.File
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNull
import kotlin.test.assertTrue

class WebShareSubjectTest {
    @Test
    fun textIncludesSubjectTitleAndOriginalBody() = assertText("Subject – text")

    @Test
    fun textOmitsNullTitle() = assertText(null)

    @Test
    fun textRetainsEmptyTitle() = assertText("")

    @Test
    fun urlIncludesSubjectTitleAndOriginalUrl() = assertUrl("Subject – URL")

    @Test
    fun urlOmitsNullTitle() = assertUrl(null)

    @Test
    fun urlRetainsEmptyTitle() = assertUrl("")

    @Test
    fun fileIncludesSubjectTitleAndOriginalFile() = assertFile("Subject – file")

    @Test
    fun fileOmitsNullTitle() = assertFile(null)

    @Test
    fun fileRetainsEmptyTitle() = assertFile("")

    @Test
    fun filesIncludeSubjectTitleAndOriginalOrder() = assertFiles("Subject – files")

    @Test
    fun filesOmitNullTitle() = assertFiles(null)

    @Test
    fun filesRetainEmptyTitle() = assertFiles("")

    @Test
    fun restoresOriginalShareDescriptorAfterCapture() {
        val descriptorUnchanged = snapshotNavigatorShareDescriptor()
        try {
            withShareCapture { outerCapture ->
                val ownedDescriptorUnchanged = snapshotNavigatorShareDescriptor()
                try {
                    withShareCapture { capture ->
                        handleShare(ShareContent.Text("Descriptor restoration")) {}
                        assertEquals(1, capture.callCount)
                    }
                } finally {
                    assertTrue(ownedDescriptorUnchanged(), "The outer fixture's own descriptor must be restored")
                }
                assertEquals(0, outerCapture.callCount)
                handleShare(ShareContent.Text("Restored outer capture")) {}
                assertEquals(1, outerCapture.callCount)
                assertEquals("Restored outer capture", outerCapture.stringField("text"))
            }
        } finally {
            assertTrue(descriptorUnchanged(), "navigator.share's original descriptor must be restored")
        }
    }

    @Test
    fun restoresOriginalShareDescriptorAfterAssertionFailure() {
        val descriptorUnchanged = snapshotNavigatorShareDescriptor()
        try {
            withShareCapture { outerCapture ->
                val ownedDescriptorUnchanged = snapshotNavigatorShareDescriptor()
                try {
                    assertFailsWith<AssertionError> {
                        withShareCapture { capture ->
                            handleShare(ShareContent.Text("Actual production payload")) {}
                            assertEquals("Intentional mismatch", capture.stringField("text"))
                        }
                    }
                } finally {
                    assertTrue(ownedDescriptorUnchanged(), "Failure must restore the outer fixture's own descriptor")
                }
                assertEquals(0, outerCapture.callCount)
                handleShare(ShareContent.Text("Restored after failure")) {}
                assertEquals(1, outerCapture.callCount)
                assertEquals("Restored after failure", outerCapture.stringField("text"))
            }
        } finally {
            assertTrue(descriptorUnchanged(), "navigator.share must be restored even when an assertion throws")
        }
    }

    private fun assertText(subject: String?) = withShareCapture { capture ->
        val text = "Original body\nπ, not the subject"
        handleShare(ShareContent.Text(text, subject)) {}
        assertPayloadFields(capture, "text", subject)
        assertEquals(text, capture.stringField("text"))
    }

    private fun assertUrl(subject: String?) = withShareCapture { capture ->
        val url = "https://example.invalid/path?q=one%20two#fragment"
        handleShare(ShareContent.Url(url, subject)) {}
        assertPayloadFields(capture, "url", subject)
        assertEquals(url, capture.stringField("url"))
    }

    private fun assertFile(subject: String?) = withShareCapture { capture ->
        val file = browserFile("first résumé.txt", "Original bytes π", "text/plain")
        handleShare(ShareContent.File(KmpFile(file), "application/x-share-hint", subject)) {}
        assertPayloadFields(capture, "files", subject)
        assertFilesUnchanged(capture, listOf(file))
    }

    private fun assertFiles(subject: String?) = withShareCapture { capture ->
        val firstFile = browserFile("first résumé.txt", "First original bytes π", "text/plain")
        val secondFile = browserFile("second.bin", "Second original bytes", "application/octet-stream")
        val originals = listOf(secondFile, firstFile, secondFile)
        handleShare(
            ShareContent.Files(originals.map { KmpFile(it) }, "application/x-share-hint", subject),
        ) {}
        assertPayloadFields(capture, "files", subject)
        assertFilesUnchanged(capture, originals)
    }

    private fun assertPayloadFields(capture: WebShareCapture, payloadField: String, subject: String?) {
        assertEquals(1, capture.callCount)
        val expectedFields = if (subject == null) listOf(payloadField) else listOf(payloadField, "title")
        assertEquals(expectedFields.sorted().joinToString(","), capture.fieldNames())
        assertTrue(capture.hasOwnField(payloadField))
        assertEquals(subject != null, capture.hasOwnField("title"))
        if (subject == null) {
            assertNull(capture.stringField("title"))
        } else {
            assertEquals(subject, capture.stringField("title"))
        }
    }

    private fun assertFilesUnchanged(capture: WebShareCapture, originals: List<File>) {
        assertEquals(originals.size, capture.fileCount())
        originals.forEachIndexed { index, original ->
            assertTrue(capture.isSameFile(index, original), "Original browser File identity at index $index")
            assertEquals(original.name, capture.fileAt(index).name)
            assertEquals(original.type, capture.fileAt(index).type)
        }
    }
}

internal interface WebShareCapture {
    val callCount: Int
    fun fieldNames(): String
    fun hasOwnField(field: String): Boolean
    fun stringField(field: String): String?
    fun fileCount(): Int
    fun fileAt(index: Int): File
    fun isSameFile(index: Int, original: File): Boolean
    fun restore()
}

internal expect fun installShareCapture(): WebShareCapture

internal expect fun snapshotNavigatorShareDescriptor(): () -> Boolean

internal expect fun browserFile(name: String, contents: String, mimeType: String): File

private fun withShareCapture(block: (WebShareCapture) -> Unit) {
    val capture = installShareCapture()
    try {
        block(capture)
    } finally {
        capture.restore()
    }
}
