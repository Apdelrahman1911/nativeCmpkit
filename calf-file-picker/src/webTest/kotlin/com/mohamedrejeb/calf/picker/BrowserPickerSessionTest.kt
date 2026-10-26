package com.mohamedrejeb.calf.picker

import kotlinx.browser.document
import org.w3c.dom.HTMLInputElement
import org.w3c.dom.events.Event
import org.w3c.files.File
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNull
import kotlin.test.assertTrue

internal expect fun pickerFixtureFile(name: String): File

/** Real DOM ownership and library sessions; does not automate native browser file-dialog UI. */
class BrowserPickerSessionTest {
    @Test fun successfulCallbackFailureNeverBecomesCancellationOrASecondResult() {
        val input = input()
        var results = 0
        var errors = 0
        val session = BrowserPickerSession(input, FilePickerSelectionMode.Single,
            onResult = { results++; error("Application callback") }, onError = { errors++ },
            readFiles = { listOf(pickerFixtureFile("a.txt")) })

        assertFailsWith<IllegalStateException> { session.selected() }
        session.cancelled()
        session.selected()
        assertEquals(1, results)
        assertEquals(0, errors)
        assertDetached(input)
    }

    @Test fun cancellingCallbackFailureStillCleansTheElementAndListeners() {
        val input = input()
        var results = 0
        val session = BrowserPickerSession(input, FilePickerSelectionMode.Single,
            onResult = { results++; error("Application callback") }, onError = { error("Unexpected error") })

        assertFailsWith<IllegalStateException> { session.cancelled() }
        session.cancelled()
        assertEquals(1, results)
        assertDetached(input)
    }

    @Test fun inputChangeAppliesTheLaunchLimitBeforeDeliveringAndIgnoresLateEvents() {
        val input = input()
        var names: List<String>? = null
        var callbacks = 0
        val session = BrowserPickerSession(input, FilePickerSelectionMode.Multiple(1),
            onResult = { callbacks++; names = it.map { file -> file.file.name } }, onError = { throw it },
            readFiles = { listOf(pickerFixtureFile("first"), pickerFixtureFile("second")) })
        input.dispatchEvent(Event("change"))
        input.dispatchEvent(Event("cancel"))
        assertEquals(listOf("first"), names)
        assertEquals(1, callbacks)
        assertTrue(session.finished)
        assertDetached(input)
    }

    @Test fun conversionFailureIsAnErrorOnlyAndStillCleansTheInput() {
        val input = input()
        var errors = 0
        val session = BrowserPickerSession(input, FilePickerSelectionMode.Single,
            onResult = { error("Unexpected result") }, onError = { errors++ },
            readFiles = { error("Unreadable FileList") })
        session.selected()
        session.selected()
        assertEquals(1, errors)
        assertDetached(input)
    }

    @Test fun ownerRejectsOverlappingDialogsAndDisposalSuppressesLateResults() {
        var results = 0
        val firstInput = input()
        val secondInput = input()
        val first = BrowserPickerSession(firstInput, FilePickerSelectionMode.Single, { results++ }, { throw it })
        val second = BrowserPickerSession(secondInput, FilePickerSelectionMode.Single, { results++ }, { throw it })
        val owner = BrowserPickerOwner()
        try {
            owner.attach(first)
            assertFailsWith<IllegalStateException> { owner.attach(second) }
            owner.close()
            first.cancelled()
            first.selected()
            assertEquals(0, results)
            assertFailsWith<IllegalStateException> { owner.attach(second) }
            assertDetached(firstInput)
        } finally { owner.close(); second.close() }
    }

    private fun input(): HTMLInputElement = (document.createElement("input") as HTMLInputElement).also { document.body!!.appendChild(it) }
    private fun assertDetached(input: HTMLInputElement) {
        assertNull(input.parentNode)
        assertNull(input.onchange)
        assertNull(input.oncancel)
    }
}
