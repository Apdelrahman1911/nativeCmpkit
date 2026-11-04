@file:OptIn(com.mohamedrejeb.calf.core.ExperimentalCalfApi::class)

package com.mohamedrejeb.calf.share

import com.mohamedrejeb.calf.share.platform.NativeShareBridge
import kotlinx.coroutines.*
import org.junit.Assume.assumeFalse
import org.junit.Assume.assumeTrue
import java.awt.GraphicsEnvironment
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicReference
import javax.swing.JFrame
import javax.swing.SwingUtilities
import kotlin.test.*

/**
 * Actual DesktopShareOwner -> generated JNI -> AppKit dispatch/owners. No fake native operation,
 * virtual test scheduler, sample application, OS clipboard mutation or external recipient.
 * A retained AppKit request is not by itself proof of visible picker/user service completion.
 */
class MacOsShareCoroutineLifecycleTest {
    @Test
    fun cancellingRetainedAppKitRequestFreesOwnersAndDoesNotOccupySingleCoroutineWorker() = withRealWindow {
        withRealOwner(ShareOptions(desktopTimeoutMillis = 15_000, allowClipboardFallback = false)) { fixture ->
            fixture.owner.launch(ShareContent.Text("NativeCmpKit owned cancellation fixture"))
            awaitRetainedRequest()
            assertTrue(fixture.results.isEmpty())
            // This is the same single worker running the real native polling coroutine. A blocking
            // new JNI operation would prevent the heartbeat, regardless of eventual UI dismissal.
            runBlocking {
                withTimeout(2_000) { fixture.scope.async { true }.await() }.also { assertTrue(it) }
            }
            val cancelledAt = System.nanoTime()
            fixture.job.cancel()
            runBlocking { withTimeout(2_000) { fixture.job.join() } }
            assertTrue(System.nanoTime() - cancelledAt < TimeUnit.SECONDS.toNanos(2),
                "Coroutine cancellation waited for a native UI deadline")
            awaitNoNativeOwners()
            assertTrue(fixture.results.isEmpty(), "Disposed scope received a late native outcome")
            assertTrue(fixture.failures.isEmpty(), "Real native coroutine raised an unexpected failure")
            assertFreshAdmissionAndCancel()
        }
    }

    @Test
    fun realNativeTimeoutReportsOnceWithoutFallbackAndAllowsFreshRequestAfterMainCleanup() = withRealWindow {
        withRealOwner(ShareOptions(desktopTimeoutMillis = 2_000, allowClipboardFallback = false)) { fixture ->
            fixture.owner.launch(ShareContent.Text("NativeCmpKit owned timeout fixture"))
            awaitTimeoutRetention(fixture, RetentionPhase.InitialTimeout)
            awaitCondition("Native deadline did not deliver its outcome", 5_000) { fixture.results.size == 1 }
            val failed = assertIs<ShareOutcome.Failed>(fixture.results.single())
            assertEquals(ShareFailureReason.TimedOut, failed.reason)
            awaitNoNativeOwners()
            assertTrue(fixture.failures.isEmpty())
            fixture.options.set(ShareOptions(desktopTimeoutMillis = 15_000, allowClipboardFallback = false))
            fixture.owner.launch(ShareContent.Text("NativeCmpKit fresh request after timeout"))
            awaitTimeoutRetention(fixture, RetentionPhase.ReplacementAfterTimeout)
            assertEquals(1, fixture.results.size, "Completed timeout generated another callback")
            fixture.job.cancel()
            runBlocking { withTimeout(2_000) { fixture.job.join() } }
            awaitNoNativeOwners()
            assertEquals(1, fixture.results.size, "Cancelled replacement delivered an outcome")
        }
    }

    @Test
    fun independentRealNativeOwnersRejectOverlapWithoutReplacingTheRetainedRequest() = withRealWindow {
        withRealOwner(ShareOptions(desktopTimeoutMillis = 15_000, allowClipboardFallback = false)) { original ->
            withRealOwner(ShareOptions(desktopTimeoutMillis = 15_000, allowClipboardFallback = false)) { overlap ->
                original.owner.launch(ShareContent.Text("NativeCmpKit original native owner"))
                awaitRetainedRequest()
                overlap.owner.launch(ShareContent.Text("NativeCmpKit independent rejected native owner"))
                awaitCondition("Native single-flight rejection was not delivered", 2_000) { overlap.results.size == 1 }
                assertEquals(ShareOutcome.Busy, overlap.results.single())
                assertTrue(original.results.isEmpty(), "Native Busy completed the original owner")
                assertEquals(1, NativeShareBridge.activeRequestCount())
                assertEquals(1, NativeShareBridge.liveUiOperationCount())
                overlap.job.cancel()
                runBlocking { withTimeout(2_000) { overlap.job.join() } }
                assertEquals(1, NativeShareBridge.activeRequestCount(), "Rejected owner cancelled a different request")
                original.job.cancel()
                runBlocking { withTimeout(2_000) { original.job.join() } }
                awaitNoNativeOwners()
                assertTrue(original.results.isEmpty())
                assertTrue(original.failures.isEmpty())
                assertTrue(overlap.failures.isEmpty())
                assertFreshAdmissionAndCancel()
            }
        }
    }

    private class Fixture {
        private val dispatcher = Executors.newSingleThreadExecutor().asCoroutineDispatcher()
        val job = SupervisorJob()
        val results = CopyOnWriteArrayList<ShareOutcome>()
        val failures = CopyOnWriteArrayList<Throwable>()
        val options = AtomicReference(ShareOptions())
        val scope = CoroutineScope(job + dispatcher + CoroutineExceptionHandler { _, error -> failures += error })
        // Default operation: this is the actual library native policy, not an injected stub.
        val owner = DesktopShareOwner(scope, { options.get() }, { results += it })

        fun close() {
            try {
                job.cancel()
                runBlocking { withTimeout(5_000) { job.join() } }
            } finally {
                dispatcher.close()
            }
        }
    }

    private fun withRealOwner(options: ShareOptions, body: (Fixture) -> Unit) {
        val fixture = Fixture().apply { this.options.set(options) }
        var primary: Throwable? = null
        try {
            body(fixture)
        } catch (error: Throwable) {
            primary = error
            throw error
        } finally {
            try { fixture.close() }
            catch (cleanup: Throwable) { if (primary != null) primary.addSuppressed(cleanup) else throw cleanup }
        }
    }

    private fun withRealWindow(body: () -> Unit) {
        val mac = System.getProperty("os.name").lowercase().let { "mac" in it || "darwin" in it }
        assumeTrue("AppKit lifecycle is macOS-only; opposite host is exact N/A", mac)
        assumeFalse("Required AppKit regression needs a graphical session; headless is not a native pass", GraphicsEnvironment.isHeadless())
        assumeTrue("Explicit native GUI opt-in is required; opt-out on macOS is not a pass",
            java.lang.Boolean.getBoolean("nativecmpkit.test.nativeUi") || System.getenv("NATIVECMPKIT_NATIVE_UI_TESTS") == "true")
        NativeShareBridge.init()
        assertEquals(1, NativeShareBridge.abiVersion())
        assertTrue(NativeShareBridge.isNativeShareSupported(), "Actual AppKit does not support cancellable sharing")
        assertEquals(0, NativeShareBridge.activeRequestCount(), "Do not replace another native request")
        assertEquals(0, NativeShareBridge.liveUiOperationCount(), "Do not replace another native UI owner")
        var frame: JFrame? = null
        SwingUtilities.invokeAndWait {
            frame = JFrame("NativeCmpKit disposable coroutine lifecycle test").apply {
                setSize(360, 160)
                isVisible = true
                toFront()
                requestFocus()
            }
        }
        var primary: Throwable? = null
        try {
            awaitCondition("Owned AWT window never became active", 10_000) { frame!!.isActive }
            body()
        } catch (error: Throwable) {
            primary = error
            throw error
        } finally {
            try {
                SwingUtilities.invokeAndWait { frame?.dispose() }
                awaitNoNativeOwners()
            } catch (cleanup: Throwable) {
                if (primary != null) primary.addSuppressed(cleanup) else throw cleanup
            }
        }
    }

    private fun awaitRetainedRequest() = awaitCondition("Actual AppKit operation was not retained", 10_000) {
        NativeShareBridge.activeRequestCount() == 1 && NativeShareBridge.liveUiOperationCount() == 1
    }

    private enum class RetentionPhase { InitialTimeout, ReplacementAfterTimeout }

    /** Failure-only fields from the SAME original predicate; no retry, new query or deadline change. */
    private fun awaitTimeoutRetention(fixture: Fixture, phase: RetentionPhase) {
        var active: Int? = null
        var live: Int? = null
        try {
            awaitCondition("Actual AppKit operation was not retained", 10_000) {
                val queriedActive = NativeShareBridge.activeRequestCount()
                val queriedLive = if (queriedActive == 1) NativeShareBridge.liveUiOperationCount() else null
                active = queriedActive
                live = queriedLive
                queriedActive == 1 && queriedLive == 1
            }
        } catch (error: AssertionError) {
            if (error.message == "Actual AppKit operation was not retained") {
                // CopyOnWriteArrayList iterators retain one immutable emitted snapshot. Bound the
                // diagnostic iteration even if a callback bug has emitted an unexpected population.
                val emitted = fixture.results.iterator()
                var count = 0
                var first: ShareOutcome? = null
                while (emitted.hasNext() && count <= 64) {
                    val value = emitted.next()
                    if (count == 0) first = value
                    count++
                }
                val outcome = when {
                    count > 64 -> "overflow"
                    count == 0 -> "not-emitted"
                    count > 1 -> "multiple"
                    else -> when (val value = first) {
                        ShareOutcome.Presented -> "Presented"
                        ShareOutcome.Selected -> "Selected"
                        ShareOutcome.Completed -> "Completed"
                        ShareOutcome.CopiedToClipboard -> "CopiedToClipboard"
                        ShareOutcome.Dismissed -> "Dismissed"
                        ShareOutcome.Busy -> "Busy"
                        is ShareOutcome.Unavailable -> "Unavailable"
                        is ShareOutcome.Failed -> "Failed.${value.reason.name}"
                        null -> "not-emitted" // Never substitute a native count or error body.
                    }
                }
                val failures = fixture.failures.iterator()
                var failureCount = 0
                while (failures.hasNext() && failureCount <= 64) { failures.next(); failureCount++ }
                fun nativeCount(value: Int?): String = when {
                    value == null -> "unavailable"
                    value !in 0..64 -> "out-of-range"
                    else -> value.toString()
                }
                val resultCount = if (count > 64) "overflow" else count.toString()
                val recordedFailures = if (failureCount > 64) "overflow" else failureCount.toString()
                println("NATIVECMPKIT_SHARE_RETENTION phase=${phase.name} active=${nativeCount(active)} " +
                    "live=${nativeCount(live)} outcome=$outcome result_count=$resultCount failure_count=$recordedFailures")
            }
            throw error // Preserve the original assertion and independent owned cleanup.
        }
    }

    private fun awaitNoNativeOwners() = awaitCondition("Native Main cleanup did not release owned references", 5_000) {
        NativeShareBridge.activeRequestCount() == 0 && NativeShareBridge.liveUiOperationCount() == 0
    }

    private fun assertFreshAdmissionAndCancel() {
        val id = NativeShareBridge.beginShareSheet("NativeCmpKit fresh admission witness", null, emptyArray(), null, 0)
        assertTrue(id > 0, "Prior cancelled native owner still blocks fresh admission")
        try { assertEquals(1, NativeShareBridge.activeRequestCount()) }
        finally { NativeShareBridge.cancelShare(id) }
        awaitNoNativeOwners()
        NativeShareBridge.cancelShare(id)
        awaitNoNativeOwners()
    }

    private fun awaitCondition(reason: String, timeoutMillis: Long, condition: () -> Boolean) {
        val deadline = System.nanoTime() + TimeUnit.MILLISECONDS.toNanos(timeoutMillis)
        while (!condition() && System.nanoTime() < deadline) Thread.sleep(10)
        assertTrue(condition(), reason)
    }
}
