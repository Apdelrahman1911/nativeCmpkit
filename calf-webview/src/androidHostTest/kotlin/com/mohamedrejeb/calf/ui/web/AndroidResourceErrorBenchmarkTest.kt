// NativeCmpKit regression: actual Android library callbacks; controlled errors, not Chromium/network.
package com.mohamedrejeb.calf.ui.web

import android.net.Uri
import android.webkit.NativeCmpKitControlledResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebView
import androidx.compose.runtime.snapshots.Snapshot
import androidx.compose.runtime.snapshots.SnapshotStateList
import androidx.compose.runtime.snapshots.SnapshotStateObserver
import com.sun.management.ThreadMXBean
import java.lang.management.ManagementFactory
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import kotlin.test.*

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
class AndroidResourceErrorBenchmarkTest {
    private object ResourceRequest : WebResourceRequest {
        override fun getUrl(): Uri = Uri.parse("https://example.invalid/controlled-resource")
        override fun isForMainFrame() = false
        override fun isRedirect() = false
        override fun hasGesture() = false
        override fun getMethod() = "GET"
        override fun getRequestHeaders(): Map<String, String> = emptyMap()
    }

    @Volatile private var referenceSink: List<WebViewError> = emptyList()

    private data class Measurement(val allocatedBytes: Long, val elapsedNanos: Long)

    private fun measure(action: () -> Unit): Measurement {
        val bean = assertNotNull(ManagementFactory.getThreadMXBean() as? ThreadMXBean,
            "This host benchmark requires the configured JDK's allocation counter")
        assertTrue(bean.isThreadAllocatedMemorySupported)
        if (!bean.isThreadAllocatedMemoryEnabled) bean.isThreadAllocatedMemoryEnabled = true
        val threadId = Thread.currentThread().id
        val bytes = bean.getThreadAllocatedBytes(threadId)
        val start = System.nanoTime()
        action()
        val elapsed = System.nanoTime() - start
        val allocated = bean.getThreadAllocatedBytes(threadId) - bytes
        assertTrue(allocated > 0, "Actual allocation measurement must be available")
        assertTrue(elapsed > 0)
        return Measurement(allocated, elapsed)
    }

    @Test fun benchmarkActualCallbacksPreservesAllFiveThousandObservableResourceRecords() {
        val view = WebView(RuntimeEnvironment.getApplication())
        val state = WebViewState(WebContent.NavigatorOnly).apply { webView = view }
        val client = AccompanistWebViewClient().apply { this.state = state }
        val input = List(5000) { NativeCmpKitControlledResourceError(it) }
        val errors = state.errorsForCurrentRequest
        assertIs<SnapshotStateList<*>>(errors)
        val observationScope = Any()
        val observer = SnapshotStateObserver { it() }
        var changes = 0
        observer.start()
        try {
            // Warm only the actual owning callback; setup and metadata assertions are outside timing.
            input.take(256).forEach { client.onReceivedError(view, ResourceRequest, it) }
            client.onPageStarted(view, "https://example.invalid/current", null)
            assertTrue(errors.isEmpty())
            observer.observeReads(observationScope, { _: Any -> changes++ }) { errors.size }
            val current = measure {
                input.forEach { client.onReceivedError(view, ResourceRequest, it) }
            }
            Snapshot.sendApplyNotifications()
            assertTrue(changes > 0, "The same collection's additions must invalidate actual Compose observations")
            assertSame(errors, state.errorsForCurrentRequest)
            assertEquals(5000, errors.size)
            input.forEachIndexed { index, error ->
                assertEquals(error.errorCode, errors[index].code)
                assertEquals(error.description.toString(), errors[index].description)
            }
            // Owning baseline add/toList algorithm only, NOT a run of a historical APK/native engine.
            val originalCopyAlgorithm = measure {
                val accumulated = mutableListOf<WebViewError>()
                input.forEach { error ->
                    accumulated.add(WebViewError(error.errorCode, error.description.toString()))
                    referenceSink = accumulated.toList()
                }
            }
            assertEquals(errors.toList(), referenceSink)
            println("NATIVE-039 RESOURCE_BENCHMARK " +
                "{\"errors\":5000,\"current_callback_allocated_bytes\":${current.allocatedBytes}," +
                "\"current_callback_elapsed_nanos\":${current.elapsedNanos}," +
                "\"copy_algorithm_allocated_bytes\":${originalCopyAlgorithm.allocatedBytes}," +
                "\"copy_algorithm_elapsed_nanos\":${originalCopyAlgorithm.elapsedNanos}," +
                "\"copy_algorithm_cumulative_copied_references\":12502500}")
            val previousChanges = changes
            observer.observeReads(observationScope, { _: Any -> changes++ }) { errors.size }
            client.onPageStarted(view, "https://example.invalid/next", null)
            Snapshot.sendApplyNotifications()
            assertSame(errors, state.errorsForCurrentRequest)
            assertTrue(errors.isEmpty())
            assertTrue(changes > previousChanges, "Clearing for the next request must remain observable")
            assertEquals("https://example.invalid/next", state.requestedUrl)
        } finally {
            observer.clear()
            observer.stop()
            referenceSink = emptyList()
            releaseAndroidWebView(state, view) {}
            assertNull(state.webView)
        }
    }
}
