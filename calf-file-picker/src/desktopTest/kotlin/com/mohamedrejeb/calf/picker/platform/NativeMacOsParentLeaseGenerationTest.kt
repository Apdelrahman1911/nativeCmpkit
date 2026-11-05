// NativeCmpKit library-level regression proposal (2026-11-05); not an executed result.
package com.mohamedrejeb.calf.picker.platform

import java.awt.EventQueue
import java.awt.Frame
import java.awt.GraphicsEnvironment
import java.util.Locale
import java.util.concurrent.atomic.AtomicReference
import org.junit.Assume.assumeTrue
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotEquals
import kotlin.test.assertTrue

/**
 * Real AWT Window/peer, production RetainAction and packaged JNI parent lease.
 * The DIRECTORY configuration is queried through showFileDialog deliberately:
 * the actual parent/view scope runs, but that kind cannot open an OS modal.
 * This is NOT parent replacement while a panel is open or release-completion proof.
 */
class NativeMacOsParentLeaseGenerationTest {
    @Test fun actualAwtPeerReplacementRejectsOldOwnedLeaseBeforeAnyModal() {
        val os = System.getProperty("os.name").orEmpty().lowercase(Locale.ROOT)
        assumeTrue("macOS-specific parent-generation regression; other platform criteria remain separate", "mac" in os || "darwin" in os)
        assertEquals("17", System.getProperty("java.specification.version"), "The actual production parent contract requires the reviewed JDK17")
        check(!GraphicsEnvironment.isHeadless()) { "A real macOS AWT/WindowServer session is required; no UI skip" }
        check(!EventQueue.isDispatchThread()) { "Synchronous JNI must not occupy the AWT EDT" }

        // Capacity is prepared before the two successful native creations.
        val handles = ArrayList<Long>(2)
        val window = onEdt {
            val created = Frame("NativeCmpKit owned AWT generation regression")
            try {
                created.setSize(280, 180)
                created.isVisible = true
                assertTrue(created.isDisplayable && created.isShowing)
                created
            } catch (failure: Throwable) {
                try { created.dispose() } catch (cleanup: Throwable) {
                    if (cleanup !== failure) failure.addSuppressed(cleanup)
                }
                throw failure
            }
        }
        var primary: Throwable? = null
        try {
            val oldLease = NativeFilePickerBridge.createDirectoryDialogForParent(
                "NativeCmpKit old AWT generation", null, window,
            )
            assertTrue(oldLease > 0)
            handles.add(oldLease)
            // lib.rs invokes with_parent before dispatching on configuration kind.
            // DIRECTORY + showFileDialog returns an empty array without calling rfd pick.
            assertEquals(0, NativeFilePickerBridge.showFileDialog(oldLease).size)

            onEdt {
                window.dispose()
                assertTrue(!window.isDisplayable)
                window.isVisible = true // The same Java Window obtains a new native peer.
                assertTrue(window.isDisplayable && window.isShowing)
            }
            val stale = assertFailsWith<IllegalStateException> {
                NativeFilePickerBridge.showFileDialog(oldLease)
            }
            assertEquals("Requested native parent generation was replaced", stale.message)

            val newLease = NativeFilePickerBridge.createDirectoryDialogForParent(
                "NativeCmpKit new AWT generation", null, window,
            )
            assertTrue(newLease > 0)
            handles.add(newLease)
            assertNotEquals(oldLease, newLease)
            assertEquals(0, NativeFilePickerBridge.showFileDialog(newLease).size)
        } catch (failure: Throwable) {
            primary = failure
            throw failure
        } finally {
            closeOwned(handles, window, primary)
        }
        // After every assertion and the owning cleanup; assumptions/failures cannot emit this.
        // This observes registry/AWT cleanup returning, NOT CFRelease completion.
        println("NATIVECMPKIT_AWT_GENERATION807 old_refused=true new_scope_returned=true registry_and_awt_cleanup_returned=true")
    }

    private fun closeOwned(handles: List<Long>, window: Frame, primary: Throwable?) {
        var cleanupFailure: Throwable? = null
        fun attempt(action: () -> Unit) {
            try { action() } catch (failure: Throwable) {
                val previous = cleanupFailure
                if (previous == null) cleanupFailure = failure
                else if (previous !== failure) previous.addSuppressed(failure)
            }
        }
        for (index in handles.indices.reversed()) {
            attempt { NativeFilePickerBridge.destroyDialog(handles[index]) }
        }
        attempt { onEdt { window.dispose(); assertTrue(!window.isDisplayable) } }
        cleanupFailure?.let { failure ->
            if (primary == null) throw failure
            if (primary !== failure) primary.addSuppressed(failure)
        }
        // Config close and AWT disposal are observations, not CFRelease completion.
    }

    private fun <T> onEdt(action: () -> T): T {
        check(!EventQueue.isDispatchThread()) { "This helper is called only by the owning test worker" }
        val value = AtomicReference<T>()
        val failure = AtomicReference<Throwable>()
        EventQueue.invokeAndWait {
            try { value.set(action()) } catch (error: Throwable) { failure.set(error) }
        }
        failure.get()?.let { throw it }
        return value.get()
    }
}
