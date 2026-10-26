package com.mohamedrejeb.calf.picker

import org.w3c.dom.HTMLAnchorElement
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Registers unchanged native timers; fireCallback deliberately invokes the captured callback by hand. */
internal expect class BrowserTimeoutSpy() {
    val timerCount: Int
    fun delayAt(index: Int): Int
    fun fireCallback(index: Int): Boolean
    fun close()
}

class BrowserDownloadTest {
    @Test fun defaultSchedulerRegistersNativeDelayAndReleasesCapacityWhenCallbacksAreInvoked() {
        val spy = BrowserTimeoutSpy()
        var failure: Throwable? = null
        try {
            val blob = createBlob(byteArrayOf(1, 2), "application/octet-stream")
            assertEquals(40_000, OBJECT_URL_REVOKE_DELAY_MS)
            // Two full rounds prove recovered capacity, not just one newly available slot.
            repeat(2) { round ->
                repeat(32) { index ->
                    var anchor: HTMLAnchorElement? = null
                    val name = "default-$round-$index.bin"
                    // Omit schedule: this must exercise the production default adapter.
                    triggerDownload(blob, name, click = {
                        anchor = it
                        assertNotNull(it.parentNode)
                        assertTrue(it.href.startsWith("blob:"))
                        assertEquals(name, it.download)
                    })
                    assertNull(assertNotNull(anchor).parentNode)
                }
                val registered = (round + 1) * 32
                assertEquals(registered, spy.timerCount)
                assertFailsWith<IllegalStateException> {
                    triggerDownload(blob, "overflow.bin", click = { error("must not click") })
                }
                assertEquals(registered, spy.timerCount)
                repeat(32) { index ->
                    val timer = round * 32 + index
                    assertEquals(40_000, spy.delayAt(timer))
                    // Manual invocation is not evidence of elapsed 40-second native delivery.
                    assertTrue(spy.fireCallback(timer), "The native callback adapter must return null")
                    assertTrue(spy.fireCallback(timer), "A repeated callback must be harmless")
                }
            }
        } catch (error: Throwable) {
            failure = error
            throw error
        } finally {
            // No suspension while installed. Close restores the descriptor, clears every native
            // handle and attempts every retained release callback, even after an earlier failure.
            try {
                spy.close()
            } catch (cleanup: Throwable) {
                val primary = failure
                if (primary == null) throw cleanup
                primary.addSuppressed(cleanup)
            }
        }
    }

    @Test fun successfulRequestRetainsTheBlobUrlUntilDeferredCleanupButRemovesTheAnchor() {
        val callbacks = mutableListOf<() -> Unit>()
        var anchor: HTMLAnchorElement? = null
        try {
            triggerDownload(createBlob(byteArrayOf(1, 2), "application/octet-stream"), "file.bin", callbacks::add) {
                anchor = it
                assertNotNull(it.parentNode)
                assertTrue(it.href.startsWith("blob:"))
                assertEquals("file.bin", it.download)
            }
            assertNull(assertNotNull(anchor).parentNode)
            assertEquals(1, callbacks.size)
            assertTrue(OBJECT_URL_REVOKE_DELAY_MS > 0)
        } finally { callbacks.forEach { it() } }
    }

    @Test fun clickAndSchedulerFailuresCleanTheAnchorAndDoNotExhaustTheUrlBudget() {
        val callbacks = mutableListOf<() -> Unit>()
        try {
            repeat(40) {
                var anchor: HTMLAnchorElement? = null
                assertFailsWith<IllegalStateException> {
                    triggerDownload(createBlob(byteArrayOf(), "text/plain"), "file.txt", callbacks::add) {
                        anchor = it; error("click failed")
                    }
                }
                assertNull(assertNotNull(anchor).parentNode)
            }
            assertFailsWith<IllegalStateException> {
                triggerDownload(createBlob(byteArrayOf(), "text/plain"), "file.txt", { error("timer failed") }) { error("must not click") }
            }
        } finally { callbacks.forEach { it() } }
    }

    @Test fun retainedUrlsAreBoundedAndCapacityReturnsAfterCleanup() {
        val callbacks = mutableListOf<() -> Unit>()
        val blob = createBlob(byteArrayOf(), "text/plain")
        try {
            repeat(32) { triggerDownload(blob, "file.txt", callbacks::add) {} }
            assertFailsWith<IllegalStateException> { triggerDownload(blob, "overflow.txt", callbacks::add) {} }
            callbacks.forEach { it() }
            callbacks.clear()
            triggerDownload(blob, "next.txt", callbacks::add) {}
        } finally { callbacks.forEach { it() } }
    }

    @Test fun saveOwnerRejectsDuplicateAndStaleCompletionAndSuppressesDisposedEvents() {
        val owner = BrowserSaveOwner()
        val first = owner.begin()
        assertFailsWith<IllegalStateException> { owner.begin() }
        assertTrue(owner.complete(first))
        assertFalse(owner.complete(first))
        val second = owner.begin()
        assertFalse(owner.complete(first))
        owner.close()
        assertFalse(owner.complete(second))
        assertFailsWith<IllegalStateException> { owner.begin() }
    }
}
