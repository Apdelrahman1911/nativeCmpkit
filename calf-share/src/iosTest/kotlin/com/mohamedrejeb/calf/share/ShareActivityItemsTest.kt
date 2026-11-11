@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.share

import com.mohamedrejeb.calf.io.KmpFile
import platform.Foundation.NSURL
import platform.UIKit.UIActivityItemSourceProtocol
import platform.UIKit.UIActivityTypeMail
import platform.UIKit.UIActivityViewController
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNotNull

class ShareActivityItemsTest {
    @Test
    fun textSuppliesSubjectWithOriginalBody() = assertText("Mail subject – text")

    @Test
    fun textWithoutSubjectRemainsUnwrapped() = assertText(null)

    @Test
    fun textRetainsEmptySubject() = assertText("")

    @Test
    fun urlSuppliesSubjectWithOriginalUrl() = assertUrl("Mail subject – URL")

    @Test
    fun urlWithoutSubjectRemainsUnwrapped() = assertUrl(null)

    @Test
    fun urlRetainsEmptySubject() = assertUrl("")

    @Test
    fun fileSuppliesSubjectWithOriginalUrl() = assertFile("Mail subject – file")

    @Test
    fun fileWithoutSubjectRemainsUnwrapped() = assertFile(null)

    @Test
    fun fileRetainsEmptySubject() = assertFile("")

    @Test
    fun filesSupplySubjectForEveryOriginalUrl() = assertFiles("Mail subject – files")

    @Test
    fun filesWithoutSubjectRemainUnwrappedInOrder() = assertFiles(null)

    @Test
    fun filesRetainEmptySubjectForEveryItem() = assertFiles("")

    private fun assertText(subject: String?) {
        val text = "Original body\nπ, not the subject"
        assertItems(ShareContent.Text(text, subject), subject, listOf(text))
    }

    private fun assertUrl(subject: String?) {
        val url = "https://example.invalid/path?q=one%20two#fragment"
        val content = ShareContent.Url(url, subject)
        assertItems(content, subject, listOf(assertNotNull(NSURL.URLWithString(url))), compareNativeUrlEquality = false)
    }

    private fun assertFile(subject: String?) {
        val fileUrl = NSURL.fileURLWithPath("/tmp/share subject/first résumé.txt")
        val content = ShareContent.File(KmpFile(fileUrl), "text/plain", subject)
        assertItems(content, subject, listOf(fileUrl))
    }

    private fun assertFiles(subject: String?) {
        val firstUrl = NSURL.fileURLWithPath("/tmp/share subject/first résumé.txt")
        val secondUrl = NSURL.fileURLWithPath("/tmp/share subject/second.bin")
        val content = ShareContent.Files(
            listOf(KmpFile(secondUrl), KmpFile(firstUrl), KmpFile(secondUrl)),
            "application/octet-stream",
            subject,
        )
        assertItems(content, subject, listOf(secondUrl, firstUrl, secondUrl))
    }

    private fun assertItems(
        content: ShareContent,
        subject: String?,
        expectedItems: List<Any>,
        compareNativeUrlEquality: Boolean = true,
    ) {
        val items = content.toActivityItems()
        assertEquals(expectedItems.size, items.size)
        if (subject == null) {
            items.forEachIndexed { index, item ->
                assertFalse(item is UIActivityItemSourceProtocol)
                assertPayload(expectedItems[index], item, compareNativeUrlEquality)
            }
            return
        }

        val controller = UIActivityViewController(activityItems = items, applicationActivities = null)
        items.forEachIndexed { index, item ->
            val source = assertIs<UIActivityItemSourceProtocol>(item)
            val placeholder = source.activityViewControllerPlaceholderItem(controller)
            assertPayload(expectedItems[index], placeholder, compareNativeUrlEquality)
            listOf(null, UIActivityTypeMail).forEach { activityType ->
                val actualItem = assertNotNull(
                    source.activityViewController(
                        activityViewController = controller,
                        itemForActivityType = activityType,
                    ),
                )
                assertPayload(placeholder, actualItem, compareNativeUrlEquality = true)
                assertEquals(
                    subject,
                    source.activityViewController(
                        activityViewController = controller,
                        subjectForActivityType = activityType,
                    ),
                )
            }
        }
    }

    private fun assertPayload(expected: Any, actual: Any, compareNativeUrlEquality: Boolean) {
        when (expected) {
            is String -> assertEquals(expected, assertIs<String>(actual))
            is NSURL -> {
                val actualUrl = assertIs<NSURL>(actual)
                assertEquals(expected.absoluteString, actualUrl.absoluteString)
                // Objective-C interop can return a different Kotlin wrapper for the same URL.
                // Check Foundation URL equality as well as its serialized payload.
                if (compareNativeUrlEquality) assertEquals(expected, actualUrl)
            }
            else -> error("Unexpected activity-item fixture")
        }
    }
}
