package com.mohamedrejeb.calf.picker.platform

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

/** Loads the packaged host library and crosses JNI, but NEVER opens an OS dialog or parents one. */
class NativeBridgeSmokeTest {
    @Test fun actualNativePayloadHasExpectedAbiAndOwnsEveryConfigurationKind() {
        assertEquals(1, NativeFilePickerBridge.abiVersion())
        NativeFilePickerBridge.init()
        val handles = mutableListOf<Long>()
        try {
            handles += NativeFilePickerBridge.createFileDialog("Résumé 研究 😀", null, arrayOf("png", "heic"), true, 0L)
            handles += NativeFilePickerBridge.createDirectoryDialog(null, null, 0L)
            handles += NativeFilePickerBridge.createSaveDialog("Save", null, "研究.txt", "txt", 0L)
            assertTrue(handles.all { it > 0 })
            assertEquals(handles.size, handles.toSet().size)
        } finally {
            handles.forEach { NativeFilePickerBridge.destroyDialog(it) }
            handles.forEach { NativeFilePickerBridge.destroyDialog(it) }
        }
    }

    @Test fun staleAndInvalidHandlesThrowThroughJniWithoutOpeningADialog() {
        val handle = NativeFilePickerBridge.createDirectoryDialog(null, null, 0L)
        NativeFilePickerBridge.destroyDialog(handle)
        NativeFilePickerBridge.destroyDialog(handle)
        assertFailsWith<RuntimeException> { NativeFilePickerBridge.showFileDialog(handle) }
        assertFailsWith<RuntimeException> { NativeFilePickerBridge.showDirectoryDialog(handle) }
        assertFailsWith<RuntimeException> { NativeFilePickerBridge.showSaveDialog(handle) }
        assertFailsWith<RuntimeException> { NativeFilePickerBridge.showDirectoryDialog(0L) }
        assertFailsWith<RuntimeException> { NativeFilePickerBridge.showFileDialog(-1L) }
    }
}
