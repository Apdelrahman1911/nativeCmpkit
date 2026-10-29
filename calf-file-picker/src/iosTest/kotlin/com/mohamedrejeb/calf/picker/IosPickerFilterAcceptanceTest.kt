@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.picker

import com.mohamedrejeb.calf.picker.internal.onApplicationMain
import platform.Foundation.NSUUID
import platform.UniformTypeIdentifiers.UTType
import platform.UniformTypeIdentifiers.UTTypeApplication
import platform.UniformTypeIdentifiers.UTTypeData
import platform.UniformTypeIdentifiers.conformsToType
import kotlin.test.*

/** Actual application-loaded Apple type database; no MIME/type database substitutes. */
class IosPickerFilterAcceptanceTest {
    @Test fun applicationDocumentFilterAdmitsPdfOfficeAndZipNotJustApplicationBundles() = onApplicationMain {
        val allowed = iosDocumentContentTypes(FilePickerFileType.Document)
        assertEquals(listOf(UTTypeData.identifier), allowed.map { it.identifier })
        assertFalse(allowed.any { it.identifier == UTTypeApplication.identifier })
        for (extension in listOf("pdf", "docx", "xlsx", "zip")) {
            val actual = assertNotNull(UTType.typeWithFilenameExtension(extension), "Actual native type database must resolve $extension")
            assertTrue(allowed.any { actual.conformsToType(it) }, "$extension must conform to the actual document filter")
            assertFalse(actual.conformsToType(UTTypeApplication), "$extension is data, not an application bundle")
        }
    }

    @Test fun explicitPdfWordAndSpreadsheetKeepSpecificNativeFilters() = onApplicationMain {
        val groups = listOf(
            FilePickerFileType.Pdf to listOf("pdf"),
            FilePickerFileType.Word to listOf("doc", "docx", "odt"),
            FilePickerFileType.Spreadsheet to listOf("xls", "xlsx", "ods"),
        )
        for ((requested, extensions) in groups) {
            val allowed = iosDocumentContentTypes(requested)
            assertTrue(allowed.isNotEmpty())
            assertFalse(allowed.any { it.identifier == UTTypeData.identifier || it.identifier == UTTypeApplication.identifier })
            for (extension in extensions) {
                val actual = assertNotNull(UTType.typeWithFilenameExtension(extension))
                assertTrue(allowed.any { actual.conformsToType(it) }, "$extension must remain admitted by its explicit filter")
            }
        }
        assertEquals(listOf("com.adobe.pdf"), iosDocumentContentTypes(FilePickerFileType.Pdf).map { it.identifier })
        val zip = assertNotNull(UTType.typeWithFilenameExtension("zip"))
        assertFalse(iosDocumentContentTypes(FilePickerFileType.Pdf).any { zip.conformsToType(it) })
    }

    @Test fun unknownAndMixedTypesFollowActualNativeRegistrationWithoutSilentWidening(): Unit = onApplicationMain {
        // Apple may synthesize a dynamic type or return nil. Assert the real
        // finite contract in either domain, never turn a missing type into data.
        val token = NSUUID().UUIDString.replace("-", "").lowercase()
        val mime = "application/x-nativecmpkit-$token"
        val extension = "nativecmpkit$token"
        val mimeType = UTType.typeWithMIMEType(mime)
        val extensionType = UTType.typeWithFilenameExtension(extension)
        if (mimeType == null) {
            assertFailsWith<IllegalArgumentException> { iosDocumentContentTypes(FilePickerFileType.Custom(listOf(mime))) }
            assertFailsWith<IllegalArgumentException> { iosDocumentContentTypes(FilePickerFileType.Custom(listOf("application/pdf", mime))) }
        } else {
            assertNotEquals(UTTypeData.identifier, mimeType.identifier)
            assertEquals(listOf(mimeType.identifier), iosDocumentContentTypes(FilePickerFileType.Custom(listOf(mime))).map { it.identifier })
            assertEquals(listOf("com.adobe.pdf", mimeType.identifier), iosDocumentContentTypes(FilePickerFileType.Custom(listOf("application/pdf", mime))).map { it.identifier })
        }
        if (extensionType == null) {
            assertFailsWith<IllegalArgumentException> { iosDocumentContentTypes(FilePickerFileType.Extension(listOf(extension))) }
            assertFailsWith<IllegalArgumentException> { iosDocumentContentTypes(FilePickerFileType.Extension(listOf("pdf", extension))) }
        } else {
            assertNotEquals(UTTypeData.identifier, extensionType.identifier)
            assertEquals(listOf(extensionType.identifier), iosDocumentContentTypes(FilePickerFileType.Extension(listOf(extension))).map { it.identifier })
            assertEquals(listOf("com.adobe.pdf", extensionType.identifier), iosDocumentContentTypes(FilePickerFileType.Extension(listOf("pdf", extension))).map { it.identifier })
        }
    }

    @Test fun emptyAndInvalidFiltersRejectBeforeAnyNativePickerIsConstructed() = onApplicationMain {
        for (type in listOf(FilePickerFileType.Custom(emptyList()), FilePickerFileType.Extension(emptyList()),
            FilePickerFileType.Extension(listOf("folder/file")), FilePickerFileType.Extension(listOf("..")))) {
            assertFailsWith<IllegalArgumentException> { createUIDocumentPickerViewController(type, FilePickerSelectionMode.Single, null) }
        }
    }
}
