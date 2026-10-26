package com.mohamedrejeb.calf.picker

import kotlinx.browser.window
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.test.runTest
import kotlin.coroutines.resume
import kotlin.test.Test
import kotlin.test.assertEquals

internal expect class SavePickerFixture(mode: String) {
    val aborts: Int
    fun completeWrite()
    fun close()
}

/** Real JS/Wasm bridge + native browser Promises; the OS picker/writable boundary is a test double. */
class BrowserSaveOperationTest {
    @Test fun savedFileIsDeliveredOnlyAfterWritingAndClosing() = runTest {
        val fixture = SavePickerFixture("success")
        val result = CompletableDeferred<String>()
        try {
            showSaveFilePicker(createBlob(byteArrayOf(1), "text/plain"), "request.txt", "text/plain", "txt",
                onSaved = { result.complete("saved:" + it.name) },
                onCancelled = { result.complete("cancel") }, onPickerFailed = { result.complete("picker-error") }, onWriteFailed = { result.complete("write-error") })
            assertEquals("saved:fixture.txt", result.await())
        } finally { fixture.close() }
    }

    @Test fun abortPermissionAndBothAsyncAndSynchronousWriteFailuresAreDistinct() = runTest {
        for ((mode, expected) in listOf("cancel" to "cancel", "picker-failure" to "picker-error", "write-failure" to "write-error", "sync-create-failure" to "write-error")) {
            val fixture = SavePickerFixture(mode)
            val result = CompletableDeferred<String>()
            var callbacks = 0
            fun report(value: String) { callbacks++; result.complete(value) }
            try {
                showSaveFilePicker(createBlob(byteArrayOf(1), "text/plain"), "request.txt", "text/plain", "txt",
                    onSaved = { report("saved") }, onCancelled = { report("cancel") },
                    onPickerFailed = { report("picker-error") }, onWriteFailed = { report("write-error") })
                assertEquals(expected, result.await(), mode)
                browserTask()
                assertEquals(1, callbacks, mode)
            } finally { fixture.close() }
        }
    }

    @Test fun cancellationDuringWriteAbortsOnceAndSuppressesLateResults() = runTest {
        val fixture = SavePickerFixture("pending-write")
        var callbacks = 0
        try {
            val operation = showSaveFilePicker(createBlob(byteArrayOf(1), "text/plain"), "request.txt", "text/plain", "txt",
                onSaved = { callbacks++ }, onCancelled = { callbacks++ }, onPickerFailed = { callbacks++ }, onWriteFailed = { callbacks++ })
            browserTask() // Let native promise microtasks acquire the writable, not a virtual delay.
            operation.cancel()
            operation.cancel()
            fixture.completeWrite()
            browserTask()
            assertEquals(1, fixture.aborts)
            assertEquals(0, callbacks)
        } finally { fixture.close() }
    }

    private suspend fun browserTask(): Unit = suspendCancellableCoroutine { continuation ->
        val timer = window.setTimeout({ if (continuation.isActive) continuation.resume(Unit); null }, 0)
        continuation.invokeOnCancellation { window.clearTimeout(timer) }
    }
}
