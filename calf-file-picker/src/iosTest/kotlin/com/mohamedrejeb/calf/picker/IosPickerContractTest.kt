package com.mohamedrejeb.calf.picker

import platform.PhotosUI.PHPickerConfigurationAssetRepresentationModeCompatible
import platform.PhotosUI.PHPickerConfigurationAssetRepresentationModeCurrent
import platform.PhotosUI.PHPickerViewController
import platform.UIKit.UIPresentationController
import platform.UniformTypeIdentifiers.UTTypeData
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

/** Real UIKit/PhotosUI/UTType construction, not presentation or a cloud-provider integration. */
class IosPickerContractTest {
    @Test fun documentMeansDataNotAnApplicationBundleAndPdfStaysSpecific() {
        assertEquals(listOf(UTTypeData.identifier), iosDocumentContentTypes(FilePickerFileType.Document).map { it.identifier })
        assertEquals(listOf("com.adobe.pdf"), iosDocumentContentTypes(FilePickerFileType.Pdf).map { it.identifier })
        assertTrue(iosDocumentContentTypes(FilePickerFileType.Word).none { it.identifier == UTTypeData.identifier })
        assertTrue(iosDocumentContentTypes(FilePickerFileType.Spreadsheet).none { it.identifier == UTTypeData.identifier })
    }

    @Test fun emptyFiltersAndPathComponentsAreRejectedRatherThanWideningThePicker() {
        assertFailsWith<IllegalArgumentException> { iosDocumentContentTypes(FilePickerFileType.Custom(emptyList())) }
        assertFailsWith<IllegalArgumentException> { iosDocumentContentTypes(FilePickerFileType.Extension(listOf("folder/file"))) }
    }

    @Test fun nativeSelectionLimitAndRepresentationUseTheLaunchArguments() {
        val first = createPHPickerConfiguration(FilePickerFileType.Image, FilePickerSelectionMode.Multiple(2), ImageRepresentationMode.Compatible)
        val next = createPHPickerConfiguration(FilePickerFileType.Image, FilePickerSelectionMode.Multiple(5), ImageRepresentationMode.Current)
        val unlimited = createPHPickerConfiguration(FilePickerFileType.Image, FilePickerSelectionMode.Multiple(), ImageRepresentationMode.Current)
        assertEquals(2L, first.selectionLimit)
        assertEquals(5L, next.selectionLimit)
        assertEquals(0L, unlimited.selectionLimit)
        assertEquals(PHPickerConfigurationAssetRepresentationModeCompatible, first.preferredAssetRepresentationMode)
        assertEquals(PHPickerConfigurationAssetRepresentationModeCurrent, next.preferredAssetRepresentationMode)
    }

    @Test fun emptyPhotoResultAndSwipeHaveOnlyOneTerminalEvent() {
        val session = IosDialogSession()
        val picker = PHPickerViewController(createPHPickerConfiguration(FilePickerFileType.Image, FilePickerSelectionMode.Single, ImageRepresentationMode.Current))
        session.controller = picker
        var picked = 0
        var cancelled = 0
        val delegate = PhotoPickerDelegate(session, { picked++ }, { cancelled++ })
        delegate.picker(picker, emptyList<Any>())
        delegate.picker(picker, emptyList<Any>())
        delegate.presentationControllerDidDismiss(UIPresentationController(picker, null))
        assertEquals(1, picked)
        assertEquals(0, cancelled)
        session.finish()
    }

    @Test fun disposedPhotoSessionSuppressesCallbacksFromItsOldController() {
        val session = IosDialogSession()
        val picker = PHPickerViewController(createPHPickerConfiguration(FilePickerFileType.Image, FilePickerSelectionMode.Single, ImageRepresentationMode.Current))
        session.controller = picker
        var callbacks = 0
        val delegate = PhotoPickerDelegate(session, { callbacks++ }, { callbacks++ })
        session.cancel()
        delegate.picker(picker, emptyList<Any>())
        delegate.presentationControllerDidDismiss(UIPresentationController(picker, null))
        assertEquals(0, callbacks)
    }
}
