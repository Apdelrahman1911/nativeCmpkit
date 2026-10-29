package com.mohamedrejeb.calf.picker

import android.content.Intent
import androidx.activity.compose.LocalActivityResultRegistryOwner
import androidx.activity.result.ActivityResultRegistry
import androidx.activity.result.ActivityResultRegistryOwner
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import kotlin.test.*

/** Actual public Compose factory/AndroidX contract with a recorded registry, not Android device UI. */
@RunWith(RobolectricTestRunner::class)
class DocumentFilterBoundaryAcceptanceTest {
    @get:Rule val compose = createComposeRule()

    @Test fun recomposedDocumentAndSpecificFiltersKeepExactApplicationMimeRequests() {
        val registry = RecordingActivityResultRegistry()
        val owner = object : ActivityResultRegistryOwner {
            override val activityResultRegistry: ActivityResultRegistry = registry
        }
        val requested = mutableStateOf<FilePickerFileType>(FilePickerFileType.Document)
        lateinit var launcher: FilePickerLauncher
        var cancellations = 0
        val failures = mutableListOf<FilePickerException>()
        compose.setContent {
            CompositionLocalProvider(LocalActivityResultRegistryOwner provides owner) {
                val current = rememberFilePickerLauncher(type = requested.value,
                    onError = { failures += it }, onResult = { assertTrue(it.isEmpty()); cancellations++ })
                SideEffect { launcher = current }
            }
        }
        compose.waitForIdle()
        val retained = launcher
        val types = listOf(FilePickerFileType.Document, FilePickerFileType.Pdf,
            FilePickerFileType.Word, FilePickerFileType.Spreadsheet)
        for ((index, type) in types.withIndex()) {
            compose.runOnIdle { requested.value = type }
            compose.waitForIdle()
            compose.runOnIdle {
                assertSame(retained, launcher)
                retained.launch()
                val intent = registry.lastIntent()
                assertEquals(Intent.ACTION_OPEN_DOCUMENT, intent.action)
                assertEquals(type.value.toList(), intent.getStringArrayExtra(Intent.EXTRA_MIME_TYPES)?.toList())
                assertEquals("*/*", intent.type, "AndroidX uses MIME extras; the broad base type is not a lost filter")
                if (type == FilePickerFileType.Document) assertEquals(listOf("application/*"), type.value.toList())
                registry.dispatchLast(null)
            }
            compose.waitForIdle()
            compose.runOnIdle { assertEquals(index + 1, cancellations); assertTrue(failures.isEmpty()) }
        }
    }
}
