package com.mohamedrejeb.calf.picker.platform

import com.mohamedrejeb.calf.picker.FilePickerFileType
import kotlin.test.*

/** Actual owning MIME resolver, not a native OS chooser or provider visibility test. */
class DocumentFilterBoundaryAcceptanceTest {
    @Test fun documentAndSpecificFiltersKeepThePortableApplicationMimeMatrix() {
        assertEquals(listOf("application/*"), FilePickerFileType.Document.value.toList())
        val groups = listOf(
            FilePickerFileType.Document to listOf("pdf", "docx", "xlsx", "zip"),
            FilePickerFileType.Pdf to listOf("pdf"),
            FilePickerFileType.Word to listOf("doc", "docx", "odt"),
            FilePickerFileType.Spreadsheet to listOf("xls", "xlsx", "ods"),
        )
        for ((type, required) in groups) {
            val actual = assertNotNull(resolveExtensions(type)).map { it.lowercase() }.toSet()
            assertTrue(actual.containsAll(required), "Actual owning resolver must include $required for $type")
        }
        assertNull(resolveExtensions(FilePickerFileType.All))
        assertEquals(listOf("pdf"), resolveExtensions(FilePickerFileType.Extension(listOf("pdf"))))
        assertFailsWith<IllegalArgumentException> {
            resolveExtensions(FilePickerFileType.Custom(listOf("application/pdf", "application/x-nativecmpkit-no-registration")))
        }
    }
}
