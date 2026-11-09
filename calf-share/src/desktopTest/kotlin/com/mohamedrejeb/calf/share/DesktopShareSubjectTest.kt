package com.mohamedrejeb.calf.share

import com.mohamedrejeb.calf.io.KmpFile
import java.io.File
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertNull

class DesktopShareSubjectTest {
    @Test
    fun textSubjectDoesNotReplaceOrPrefixNativeText() = assertText("Subject – text")

    @Test
    fun textNullSubjectPreservesNativeText() = assertText(null)

    @Test
    fun textEmptySubjectPreservesNativeText() = assertText("")

    @Test
    fun urlSubjectDoesNotRewriteNativeUrl() = assertUrl("Subject – URL")

    @Test
    fun urlNullSubjectPreservesNativeUrl() = assertUrl(null)

    @Test
    fun urlEmptySubjectPreservesNativeUrl() = assertUrl("")

    @Test
    fun fileSubjectDoesNotReplaceNativePath() = assertFile("Subject – file")

    @Test
    fun fileNullSubjectPreservesNativePath() = assertFile(null)

    @Test
    fun fileEmptySubjectPreservesNativePath() = assertFile("")

    @Test
    fun filesSubjectPreservesNativePathsAndOrder() = assertFiles("Subject – files")

    @Test
    fun filesNullSubjectPreservesNativePathsAndOrder() = assertFiles(null)

    @Test
    fun filesEmptySubjectPreservesNativePathsAndOrder() = assertFiles("")

    private fun assertText(subject: String?) {
        val text = "Original body\nπ, not the subject"
        assertNativeArguments(ShareContent.Text(text, subject), expectedText = text)
    }

    private fun assertUrl(subject: String?) {
        val url = "https://example.invalid/path?q=one%20two#fragment"
        assertNativeArguments(ShareContent.Url(url, subject), expectedUrl = url)
    }

    private fun assertFile(subject: String?) {
        val file = File("share subject/first résumé.txt")
        assertNativeArguments(
            ShareContent.File(KmpFile(file), "text/plain", subject),
            expectedPaths = arrayOf(file.absolutePath),
        )
    }

    private fun assertFiles(subject: String?) {
        val firstFile = File("share subject/first résumé.txt")
        val secondFile = File("share subject/second.bin")
        assertNativeArguments(
            ShareContent.Files(
                listOf(KmpFile(secondFile), KmpFile(firstFile), KmpFile(secondFile)),
                "application/octet-stream",
                subject,
            ),
            expectedPaths = arrayOf(secondFile.absolutePath, firstFile.absolutePath, secondFile.absolutePath),
        )
    }

    private fun assertNativeArguments(
        content: ShareContent,
        expectedText: String? = null,
        expectedUrl: String? = null,
        expectedPaths: Array<String>? = null,
    ) {
        var invocationCount = 0
        val result = showNativeShare(content) { text, url, paths, parentWindow ->
            invocationCount += 1
            assertEquals(expectedText, text)
            assertEquals(expectedUrl, url)
            if (expectedPaths == null) {
                assertNull(paths)
            } else {
                assertContentEquals(expectedPaths, paths)
            }
            assertEquals(0L, parentWindow)
            0
        }
        assertEquals(1, invocationCount)
        assertEquals(ShareResult.Success, result)
    }
}
