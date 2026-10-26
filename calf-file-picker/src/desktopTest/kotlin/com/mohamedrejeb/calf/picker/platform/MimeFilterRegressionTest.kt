package com.mohamedrejeb.calf.picker.platform

import com.mohamedrejeb.calf.picker.FilePickerFileType
import jodd.net.MimeTypes
import jodd.util.Wildcard
import java.util.Locale
import java.util.concurrent.Executors
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class MimeFilterRegressionTest {
    @Test fun contemporaryImagesAreIncludedAndUnknownMimeIsNeverAnUnfilteredDialog() {
        val images = resolveExtensions(FilePickerFileType.Image)!!
        for (extension in listOf("avif", "heic", "heif")) assertTrue(extension in images, extension)
        assertFailsWith<IllegalArgumentException> { resolveExtensions(FilePickerFileType.Custom(listOf("application/x-nativecmpkit-unknown"))) }
        assertFailsWith<IllegalArgumentException> { resolveExtensions(FilePickerFileType.Custom(listOf("image/png", "application/x-nativecmpkit-unknown"))) }
        assertEquals(listOf("custom"), resolveExtensions(FilePickerFileType.Extension(listOf("custom"))))
    }

    @Test fun protocolCaseFoldingDoesNotDependOnTurkishDefaultLocale() {
        val previous = Locale.getDefault()
        try {
            Locale.setDefault(Locale.forLanguageTag("tr-TR"))
            assertEquals("image/tiff", MimeTypes.lookupMimeType("TIFF"))
            assertEquals(listOf("png"), MimeTypes.findExtensionsByMimeTypes("IMAGE/PNG", false))
        } finally { Locale.setDefault(previous) }
    }

    @Test fun commaListsIgnoreOptionalWhitespaceAndWildcardEqualsScalarForExactPatterns() {
        val expected = MimeTypes.findExtensionsByMimeTypes("image/jpeg, image/png", false).toSet()
        for (value in listOf("image/jpeg,image/png", " image/jpeg ,   image/png, ")) {
            assertEquals(expected, MimeTypes.findExtensionsByMimeTypes(value, false).toSet())
            assertEquals(expected, MimeTypes.findExtensionsByMimeTypes(value, true).toSet())
        }
    }

    @Test fun retainedRegistrationIsSynchronizedWithTheReverseIndex() {
        val executor = Executors.newFixedThreadPool(4)
        try {
            val futures = (0 until 40).map { index -> executor.submit {
                val extension = "nativecmpkittest$index"
                val type = "application/x-nativecmpkit-test$index"
                MimeTypes.registerMimeType(extension.uppercase(Locale.ROOT), type.uppercase(Locale.ROOT))
                assertEquals(type, MimeTypes.lookupMimeType(extension))
                assertTrue(extension in MimeTypes.findExtensionsByMimeTypes(type, false))
            } }
            futures.forEach { it.get() }
        } finally { executor.shutdownNow() }
    }

    @Test fun wildcardEscapesEmptyPatternsAndTrailingEscapesKeepTheirContract() {
        assertTrue(Wildcard.match("a*b?c", "a\\*b\\?c"))
        assertTrue(Wildcard.match("", "***"))
        assertTrue(Wildcard.match("abc", "a?*"))
        assertFalse(Wildcard.match("abc", "a\\"))
        assertFalse(Wildcard.match("", "?"))
        assertFalse(Wildcard.match("abcd", "a*c"))
    }

    @Test fun adversarialWildcardDoesNotUseRecursiveExponentialSuffixExploration() {
        assertFalse(Wildcard.match("a".repeat(50_000), "*a".repeat(40) + "b"))
        assertTrue(Wildcard.match("a".repeat(50_000) + "b", "*a".repeat(40) + "b"))
    }
}
