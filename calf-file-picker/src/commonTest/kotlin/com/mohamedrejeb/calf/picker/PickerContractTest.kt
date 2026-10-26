package com.mohamedrejeb.calf.picker

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNull

class PickerContractTest {
    @Test fun portableLimitsArePositiveOrUnlimited() {
        assertFailsWith<IllegalArgumentException> { FilePickerSelectionMode.Multiple(0) }
        assertFailsWith<IllegalArgumentException> { FilePickerSelectionMode.Multiple(-1) }
        assertNull(FilePickerSelectionMode.Multiple().resultLimit())
        assertEquals(1, FilePickerSelectionMode.Multiple(1).resultLimit())
        assertEquals(Int.MAX_VALUE, FilePickerSelectionMode.Multiple(Int.MAX_VALUE).resultLimit())
    }
    @Test fun resultLimitsApplyToSingleAndMultiple() {
        val data = listOf(1, 2, 3)
        assertEquals(listOf(1), data.limitedTo(FilePickerSelectionMode.Single))
        assertEquals(listOf(1, 2), data.limitedTo(FilePickerSelectionMode.Multiple(2)))
        assertEquals(data, data.limitedTo(FilePickerSelectionMode.Multiple))
    }
    @Test fun namesPreserveUnicodeAndAllowNoExtension() {
        assertEquals("Résumé 你好.pdf", suggestedFileName("Résumé 你好", "pdf"))
        assertEquals("README", suggestedFileName("README", ""))
    }
    @Test fun namesCannotEscapeStagingDirectory() {
        for (base in listOf("", " ", ".", "..", "../x", "a/b", "a\\b", "a\u0000b")) {
            assertFailsWith<IllegalArgumentException> { suggestedFileName(base, "txt") }
        }
        for (extension in listOf("../x", ".txt", "a/b", "a\\b", "\u0000")) {
            assertFailsWith<IllegalArgumentException> { suggestedFileName("name", extension) }
        }
    }
}
