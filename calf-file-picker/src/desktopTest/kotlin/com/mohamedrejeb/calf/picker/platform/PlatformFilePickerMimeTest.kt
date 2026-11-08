package com.mohamedrejeb.calf.picker.platform

import com.mohamedrejeb.calf.picker.FilePickerFileType
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNull
import kotlin.test.assertTrue

internal class PlatformFilePickerMimeTest {

    @Test
    fun imageFilterIncludesContemporaryImageFormats() {
        val extensions = resolveExtensions(FilePickerFileType.Image) ?: error("Image must be filtered")

        assertTrue(extensions.contains("avif"), "AVIF must be selectable by the image filter")
        assertTrue(extensions.contains("heic"), "HEIC must be selectable by the image filter")
        assertTrue(extensions.contains("heif"), "HEIF must be selectable by the image filter")
        assertTrue(extensions.contains("heics"), "HEIC sequences must be selectable by the image filter")
        assertTrue(extensions.contains("heifs"), "HEIF sequences must be selectable by the image filter")
        assertTrue(extensions.contains("jpg"))
        assertTrue(extensions.contains("png"))
        assertTrue(extensions.contains("webp"))
    }

    @Test
    fun customContemporaryMimeTypesResolveThroughTheRealTable() {
        assertEquals(listOf("avif"), resolveExtensions(FilePickerFileType.Custom(listOf("image/avif"))))
        assertEquals(listOf("heic"), resolveExtensions(FilePickerFileType.Custom(listOf("image/heic"))))
        assertEquals(listOf("heif"), resolveExtensions(FilePickerFileType.Custom(listOf("image/heif"))))
        assertEquals(listOf("heics"), resolveExtensions(FilePickerFileType.Custom(listOf("image/heic-sequence"))))
        assertEquals(listOf("heifs"), resolveExtensions(FilePickerFileType.Custom(listOf("image/heif-sequence"))))
    }

    @Test
    fun unknownMimeTypeFailsInsteadOfDisablingTheFilter() {
        val error = assertFailsWith<IllegalArgumentException> {
            resolveExtensions(
                FilePickerFileType.Custom(listOf("application/x-nativecmpkit-unknown")),
            )
        }

        assertTrue(error.message.orEmpty().contains("application/x-nativecmpkit-unknown"))
    }

    @Test
    fun mixedKnownAndUnknownMimeTypesFailAsAWhole() {
        val error = assertFailsWith<IllegalArgumentException> {
            resolveExtensions(
                FilePickerFileType.Custom(
                    listOf("image/png", "application/x-nativecmpkit-unknown"),
                ),
            )
        }

        assertTrue(error.message.orEmpty().contains("application/x-nativecmpkit-unknown"))
    }

    @Test
    fun commaSeparatedMixedMimeTypesFailAsAWhole() {
        assertFailsWith<IllegalArgumentException> {
            resolveExtensions(
                FilePickerFileType.Custom(
                    listOf("image/png, application/x-nativecmpkit-unknown"),
                ),
            )
        }
    }

    @Test
    fun commaSeparatedKnownMimeTypesIgnoreCaseAndWhitespace() {
        assertEquals(
            listOf("avif", "heic"),
            resolveExtensions(FilePickerFileType.Custom(listOf(" IMAGE/AVIF, image/heic "))),
        )
    }

    @Test
    fun emptyCustomFilterAndUnknownWildcardFailExplicitly() {
        assertFailsWith<IllegalArgumentException> {
            resolveExtensions(FilePickerFileType.Custom(emptyList()))
        }
        assertFailsWith<IllegalArgumentException> {
            resolveExtensions(FilePickerFileType.Custom(listOf("application/x-nativecmpkit-*")))
        }
    }

    @Test
    fun extensionModeBypassesTheMimeTable() {
        val extensions = listOf("avif", "nativecmpkit-custom", "heic", "heif")

        assertEquals(extensions, resolveExtensions(FilePickerFileType.Extension(extensions)))
    }

    @Test
    fun unfilteredModesStillReturnNull() {
        assertNull(resolveExtensions(FilePickerFileType.All))
        assertNull(resolveExtensions(FilePickerFileType.Folder))
    }

    @Test
    fun existingMimeModesStillResolveTheirKnownExtensions() {
        val expectedExtensions = mapOf(
            FilePickerFileType.Video to "mp4",
            FilePickerFileType.ImageVideo to "jpg",
            FilePickerFileType.Audio to "mp3",
            FilePickerFileType.Document to "pdf",
            FilePickerFileType.Presentation to "pptx",
            FilePickerFileType.Spreadsheet to "xlsx",
            FilePickerFileType.Word to "docx",
            FilePickerFileType.Pdf to "pdf",
            FilePickerFileType.Text to "txt",
        )

        expectedExtensions.forEach { (type, expected) ->
            val extensions = resolveExtensions(type) ?: error("$type must be filtered")

            assertTrue(extensions.contains(expected), "$type must keep $expected")
        }
    }
}
