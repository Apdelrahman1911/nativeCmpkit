package com.mohamedrejeb.calf.picker

import androidx.compose.runtime.AbstractApplier
import androidx.compose.runtime.Composition
import androidx.compose.runtime.Recomposer
import com.mohamedrejeb.calf.io.KmpFile
import kotlinx.browser.document
import org.w3c.dom.HTMLInputElement
import org.w3c.dom.events.Event
import org.w3c.files.File
import kotlin.coroutines.EmptyCoroutineContext
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotSame
import kotlin.test.assertNull
import kotlin.test.assertSame

/**
 * Intercepts only the native chooser opening. Composition, public launcher,
 * input/FileList/DataTransfer and event handlers are real browser/runtime objects.
 * Does not automate or certify the OS chooser's user-activation/cancel-event UI.
 */
internal expect class BrowserPickerDialogSpy() {
    val clickCount: Int
    fun inputAt(index: Int): HTMLInputElement
    fun select(input: HTMLInputElement, file: File)
    fun close()
}

class BrowserPickerCompositionTest {
    @Test fun normalCancellationCleansBeforeTheCallbackAndAllowsAnotherPublicLaunch() {
        val runtime = PickerComposition()
        val dialog = BrowserPickerDialogSpy()
        var results = 0
        var launcher: FilePickerLauncher? = null
        try {
            // The retained compatibility overload must own the same DOM lifetime.
            runtime.composition.setContent {
                launcher = rememberFilePickerLauncher { files ->
                    assertEquals(emptyList(), files)
                    assertDetached(dialog.inputAt(results))
                    results++
                }
            }
            checkNotNull(launcher).launch()
            val first = dialog.inputAt(0)
            first.dispatchEvent(Event("cancel"))
            first.dispatchEvent(Event("cancel"))
            first.dispatchEvent(Event("change"))
            assertEquals(1, results)
            checkNotNull(launcher).launch()
            val second = dialog.inputAt(1)
            assertNotSame(first, second)
            assertEquals("", second.value)
            second.dispatchEvent(Event("cancel"))
            assertEquals(2, results)
            assertEquals(2, dialog.clickCount)
            assertDetached(second)
        } finally {
            runtime.close()
            dialog.close()
        }
    }

    @Test fun theSameRealFileCanBeReselectedOnTwoFreshPublicLaunches() {
        val runtime = PickerComposition()
        val dialog = BrowserPickerDialogSpy()
        val file = pickerFixtureFile("same.txt")
        val results = mutableListOf<List<KmpFile>>()
        var launcher: FilePickerLauncher? = null
        try {
            runtime.composition.setContent {
                launcher = rememberFilePickerLauncher(onError = { throw it }) { results += it }
            }
            repeat(2) { index ->
                checkNotNull(launcher).launch()
                val input = dialog.inputAt(index)
                assertSame(document.body, input.parentNode)
                assertEquals("", input.value) // No old input value can suppress a same-file change.
                dialog.select(input, file)
                assertEquals(1, checkNotNull(input.files).length)
                input.dispatchEvent(Event("change"))
                assertEquals(index + 1, results.size)
                assertEquals("same.txt", results.last().single().file.name)
                assertSame(file, results.last().single().file)
                assertDetached(input)
            }
            assertNotSame(dialog.inputAt(0), dialog.inputAt(1))
            assertEquals(2, dialog.clickCount)
        } finally {
            runtime.close()
            dialog.close()
        }
    }

    @Test fun publicCompositionDisposalDetachesInputAndSuppressesCapturedLateHandlers() {
        val runtime = PickerComposition()
        val dialog = BrowserPickerDialogSpy()
        var results = 0
        var errors = 0
        var launcher: FilePickerLauncher? = null
        try {
            runtime.composition.setContent {
                launcher = rememberFilePickerLauncher(onError = { errors++ }) { results++ }
            }
            checkNotNull(launcher).launch()
            val input = dialog.inputAt(0)
            dialog.select(input, pickerFixtureFile("late.txt"))
            val lateChange = checkNotNull(input.onchange)
            val lateCancel = checkNotNull(input.oncancel)
            runtime.composition.dispose() // Execute the actual production DisposableEffect.
            assertDetached(input)
            lateChange(Event("change"))
            lateCancel(Event("cancel"))
            input.dispatchEvent(Event("change"))
            checkNotNull(launcher).launch()
            assertEquals(0, results)
            assertEquals(0, errors)
            assertEquals(1, dialog.clickCount)
        } finally {
            runtime.close()
            dialog.close()
        }
    }

    @Test fun removingPublicLauncherContentDisposesTheOwnerWithoutDisposingComposition() {
        val runtime = PickerComposition()
        val dialog = BrowserPickerDialogSpy()
        var results = 0
        var launcher: FilePickerLauncher? = null
        try {
            runtime.composition.setContent {
                launcher = rememberFilePickerLauncher { results++ }
            }
            checkNotNull(launcher).launch()
            val input = dialog.inputAt(0)
            val lateCancel = checkNotNull(input.oncancel)
            runtime.composition.setContent { }
            assertDetached(input)
            lateCancel(Event("cancel"))
            checkNotNull(launcher).launch()
            assertEquals(0, results)
            assertEquals(1, dialog.clickCount)
        } finally {
            runtime.close()
            dialog.close()
        }
    }

    @Test fun overlappingPublicLaunchReportsOneErrorAndPreservesTheFirstSession() {
        val runtime = PickerComposition()
        val dialog = BrowserPickerDialogSpy()
        var results = 0
        val errors = mutableListOf<FilePickerException>()
        var launcher: FilePickerLauncher? = null
        try {
            runtime.composition.setContent {
                launcher = rememberFilePickerLauncher(onError = { errors += it }) { results++ }
            }
            checkNotNull(launcher).launch()
            val first = dialog.inputAt(0)
            checkNotNull(launcher).launch()
            assertEquals(1, dialog.clickCount)
            assertEquals(1, errors.size)
            assertEquals("A browser picker is already open", errors.single().message)
            assertSame(document.body, first.parentNode)
            dialog.select(first, pickerFixtureFile("first.txt"))
            first.dispatchEvent(Event("change"))
            assertEquals(1, results)
            assertDetached(first)
            checkNotNull(launcher).launch()
            assertEquals(2, dialog.clickCount)
            runtime.composition.dispose()
            assertDetached(dialog.inputAt(1))
            assertEquals(1, results)
            assertEquals(1, errors.size)
        } finally {
            runtime.close()
            dialog.close()
        }
    }

    private fun assertDetached(input: HTMLInputElement) {
        assertNull(input.parentNode)
        assertNull(input.onchange)
        assertNull(input.oncancel)
    }

    /** Initial composition and disposal are synchronous; no UI or frame loop is needed. */
    private class PickerComposition {
        private val recomposer = Recomposer(EmptyCoroutineContext)
        val composition = Composition(NoUiApplier(), recomposer)
        fun close() {
            try { composition.dispose() } finally { recomposer.cancel() }
        }
    }

    private class NoUiApplier : AbstractApplier<Unit>(Unit) {
        override fun insertTopDown(index: Int, instance: Unit) { error("No UI nodes expected") }
        override fun insertBottomUp(index: Int, instance: Unit) { error("No UI nodes expected") }
        override fun remove(index: Int, count: Int) { error("No UI nodes expected") }
        override fun move(from: Int, to: Int, count: Int) { error("No UI nodes expected") }
        override fun onClear() = Unit
    }
}
