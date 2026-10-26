package com.mohamedrejeb.calf.share.platform

import org.junit.Assume.assumeFalse
import org.junit.Assume.assumeTrue
import java.awt.GraphicsEnvironment
import java.util.concurrent.TimeUnit
import javax.swing.JFrame
import javax.swing.SwingUtilities
import kotlin.test.*

/** Calls the real packaged/generated JNI library. No fake bridge or Rust-registry substitute. */
class NativeShareBridgeTest {
    private val mac: Boolean get() = System.getProperty("os.name").lowercase().let { "mac" in it || "darwin" in it }

    @Test fun nativeAbiAndDiagnosticsLoadOnTheActualHost() {
        NativeShareBridge.init()
        assertEquals(1, NativeShareBridge.abiVersion())
        assertEquals(0, NativeShareBridge.activeRequestCount())
        assertEquals(0, NativeShareBridge.liveUiOperationCount())
        if (!mac) assertFalse(NativeShareBridge.isNativeShareSupported())
    }

    @Test fun unsupportedHostRequestsAndCancellationNeverRetainNativeOwners() {
        assumeFalse("Non-macOS unavailable contract only; macOS requires native UI tests", mac)
        repeat(1_000) {
            assertEquals(0L, NativeShareBridge.beginShareSheet("test", null, emptyArray(), "subject", 0))
            assertEquals(NativeShareBridge.RESULT_UNAVAILABLE, NativeShareBridge.takeShareResult(it.toLong() + 1))
            NativeShareBridge.cancelShare(it.toLong() + 1)
        }
        assertEquals(0, NativeShareBridge.activeRequestCount())
        assertEquals(0, NativeShareBridge.liveUiOperationCount())
        assertEquals(NativeShareBridge.RESULT_UNAVAILABLE, NativeShareBridge.showShareSheet("test", null, emptyArray(), 0))
    }

    @Test fun borrowedNativeWindowPointersAreRejectedWithoutDereference() {
        assertEquals(0L, NativeShareBridge.beginShareSheet("test", null, emptyArray(), null, 1))
        NativeShareBridge.cancelShare(0)
        NativeShareBridge.cancelShare(-1)
        assertEquals(0, NativeShareBridge.activeRequestCount())
        assertEquals(0, NativeShareBridge.liveUiOperationCount())
    }

    @Test fun macOsPickerCancellationReleasesRealMainThreadOwners() {
        assumeTrue("Real AppKit UI test: macOS only", mac)
        assumeFalse("Real AppKit UI test requires a graphical session", GraphicsEnvironment.isHeadless())
        assumeTrue("Opt in with NATIVECMPKIT_NATIVE_UI_TESTS=true; a skip is not a native UI pass",
            java.lang.Boolean.getBoolean("nativecmpkit.test.nativeUi") || System.getenv("NATIVECMPKIT_NATIVE_UI_TESTS") == "true")
        assertTrue(NativeShareBridge.isNativeShareSupported(), "The running AppKit must support picker cancellation")
        var frame: JFrame? = null
        SwingUtilities.invokeAndWait {
            frame = JFrame("nativeCmpkit share cancellation test").apply {
                setSize(360, 160)
                isVisible = true
                toFront()
                requestFocus()
            }
        }
        try {
            awaitRealCondition("AWT window never became active") { frame!!.isActive }
            repeat(3) {
                val id = NativeShareBridge.beginShareSheet("Native cancellation fixture", null, emptyArray(), "Fixture", 0)
                assertTrue(id > 0, "Native request was not admitted")
                try {
                    awaitRealCondition("No retained AppKit picker; presentation is not verified") { NativeShareBridge.liveUiOperationCount() == 1 }
                } finally { NativeShareBridge.cancelShare(id) }
                awaitRealCondition("Native cancellation did not release Main-thread ownership") {
                    NativeShareBridge.activeRequestCount() == 0 && NativeShareBridge.liveUiOperationCount() == 0
                }
                NativeShareBridge.cancelShare(id)
            }
        } finally { SwingUtilities.invokeAndWait { frame?.dispose() } }
    }

    private fun awaitRealCondition(message: String, condition: () -> Boolean) {
        val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(10)
        while (!condition() && System.nanoTime() < deadline) Thread.sleep(20)
        assertTrue(condition(), message)
    }
}
