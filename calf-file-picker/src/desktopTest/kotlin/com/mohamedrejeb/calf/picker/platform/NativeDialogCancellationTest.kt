package com.mohamedrejeb.calf.picker.platform

import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.async
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.runBlocking
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

/** Real packaged host JNI configuration/close, without a raw parent or an OS dialog. */
class NativeDialogCancellationTest {
    @Test fun cancelledRealJniCreationHandoffClosesBeforeAnyShowEntry() = runBlocking {
        val entered = CountDownLatch(1)
        val release = CountDownLatch(1)
        val handle = AtomicLong()
        val closes = AtomicInteger()
        val uses = AtomicInteger()
        val operation = async(Dispatchers.IO) {
            withActiveDialogHandle(currentCoroutineContext(), {
                val created = NativeFilePickerBridge.createDirectoryDialog("Cancelled 研究", null, 0L)
                assertTrue(created > 0)
                handle.set(created)
                entered.countDown()
                check(release.await(10, TimeUnit.SECONDS)) { "JNI handoff gate was not released" }
                created
            }, {
                NativeFilePickerBridge.destroyDialog(it)
                closes.incrementAndGet()
            }) {
                uses.incrementAndGet()
                // A file query on this directory configuration cannot open an OS
                // modal even if the owning admission guard regresses.
                NativeFilePickerBridge.showFileDialog(it)
            }
        }
        try {
            assertTrue(entered.await(10, TimeUnit.SECONDS), "Actual packaged JNI creation must finish before cancellation")
            operation.cancel()
            release.countDown()
            assertFailsWith<CancellationException> { operation.await() }
            operation.join()
            assertEquals(0, uses.get())
            assertEquals(1, closes.get())
            assertFailsWith<RuntimeException> { NativeFilePickerBridge.showFileDialog(handle.get()) }
            NativeFilePickerBridge.destroyDialog(handle.get()) // Idempotence, not a second owner.
        } finally {
            release.countDown()
            operation.cancelAndJoin()
            if (handle.get() > 0) NativeFilePickerBridge.destroyDialog(handle.get())
        }
    }

    @Test fun cancellationAfterANonModalJniResultClosesTheActualConfiguration() {
        val job = Job()
        var handle = 0L
        var closes = 0
        try {
            assertFailsWith<CancellationException> {
                withActiveDialogHandle(job, {
                    NativeFilePickerBridge.createDirectoryDialog(null, null, 0L).also { handle = it }
                }, {
                    NativeFilePickerBridge.destroyDialog(it)
                    closes++
                }) {
                    // This real JNI operation builds the leased config but cannot
                    // display a file modal for its directory kind.
                    assertEquals(0, NativeFilePickerBridge.showFileDialog(it).size)
                    job.cancel()
                    "native result no longer owned by the cancelled caller"
                }
            }
            assertEquals(1, closes)
            assertFailsWith<RuntimeException> { NativeFilePickerBridge.showFileDialog(handle) }
        } finally {
            job.cancel()
            if (handle > 0) NativeFilePickerBridge.destroyDialog(handle)
        }
    }
}
