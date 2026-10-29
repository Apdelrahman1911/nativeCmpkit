package com.mohamedrejeb.calf.ui.web

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.awt.ComposeWindow
import com.sun.net.httpserver.HttpServer
import javafx.application.Platform
import javafx.concurrent.Worker
import javafx.scene.web.WebView as FxWebView
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import java.io.IOException
import java.lang.ref.WeakReference
import java.net.InetSocketAddress
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicReference
import javax.swing.SwingUtilities
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

/** Real public Compose windows, JavaFX/WebKit and loopback IO; no replacement native engine. */
class DesktopWebViewLifetimeTest {
    @Test fun retainedStateCannotRetainRepeatedRealNativeViewsOrEngines() = runBlocking {
        val state = WebViewState(WebContent.Data("<html><head><title>owned-page</title></head><body>owned</body></html>"))
        val witnesses = mutableListOf<Pair<String, WeakReference<*>>>()
        repeat(3) { iteration ->
            val host = WindowHost(state)
            try {
                host.awaitCreated()
                awaitFx { state.webView?.engine?.title == "owned-page" }
                witnesses += host.references.map { (name, reference) -> "$iteration:$name" to reference }
                host.unmount()
                // Collect while the real host window and observing composition remain alive:
                // another mount/write must not be needed to discard a native predecessor.
                assertCollected(host.references)
            } finally { host.close() }
            onFxThread {
                assertNull(state.webView)
                assertNull(state.owner)
                assertEquals(LoadingState.Finished, state.loadingState)
            }
            assertEquals(1, host.created.get())
            assertEquals(1, host.disposed.get())
        }
        assertCollected(witnesses)
        // The retained state and actual toolkit still work after all old native owners collect.
        WindowHost(state).use { host -> host.awaitCreated(); awaitFx { state.webView?.engine?.title == "owned-page" } }
    }

    @Test fun throwingDisposeCannotKeepItsViewOrStopAnotherRealWindow() = runBlocking {
        val first = WebViewState(WebContent.Data("<html><head><title>first</title></head></html>"))
        val second = WebViewState(WebContent.Data("<html><head><title>second</title></head></html>")).apply {
            settings.javaScriptEnabled = true
        }
        val expected = IllegalStateException("controlled application disposal failure")
        val observed = CompletableDeferred<Throwable>()
        var original: Thread.UncaughtExceptionHandler? = null
        var handlerInstalled = false
        val a = WindowHost(first, disposeFailure = expected)
        var b: WindowHost? = null
        try {
            val activeSecond = WindowHost(second).also { b = it }
            a.awaitCreated(); activeSecond.awaitCreated()
            awaitFx { first.webView?.engine?.title == "first" && second.webView?.engine?.title == "second" }
            onFxThread {
                original = Thread.currentThread().uncaughtExceptionHandler
                Thread.currentThread().uncaughtExceptionHandler = Thread.UncaughtExceptionHandler { thread, failure ->
                    if (failure === expected) observed.complete(failure)
                    else {
                        observed.completeExceptionally(failure)
                        original?.uncaughtException(thread, failure)
                    }
                }
                handlerInstalled = true
            }
            a.close()
            assertSame(expected, withTimeout(10_000) { observed.await() })
            onFxThread {
                assertNull(first.webView)
                assertNull(first.owner)
                // Disposing one native owner must not exit the shared JavaFX toolkit or clear another.
                assertEquals("second", second.webView!!.engine.title)
                assertEquals(3, (second.webView!!.engine.executeScript("1 + 2") as Number).toInt())
            }
            assertEquals(1, a.disposed.get())
            assertEquals(0, activeSecond.disposed.get())
            assertCollected(a.references)
        } finally {
            try {
                if (handlerInstalled) onFxThread { Thread.currentThread().uncaughtExceptionHandler = original }
            } finally {
                try { a.close() } finally { b?.close() }
            }
        }
    }

    @Test fun disposingARealWindowClosesItsSlowConnectionAndStopsTheLiveMediaDocument() = runBlocking {
        val responseStarted = CountDownLatch(1)
        val disconnected = CountDownLatch(1)
        val release = CountDownLatch(1)
        val beats = AtomicInteger()
        val writes = AtomicInteger()
        val executor = Executors.newFixedThreadPool(4) { Thread(it, "nativecmpkit-owned-lifetime-http").apply { isDaemon = true } }
        val server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0).apply { this.executor = executor }
        val wav = silentWave()
        val page = """
            <!doctype html><html><head><title>media-starting</title></head><body>
            <audio id="media" autoplay muted loop><source src="/sample.wav" type="audio/x-wav"></audio>
            <script>
            var media = document.getElementById('media');
            media.muted = true;
            media.addEventListener('error', function() { document.title = 'media-error:' + media.error.code; });
            var started = media.play();
            if (started && started.catch) started.catch(function(e) { document.title = 'media-rejected:' + e.name; });
            setInterval(function() {
                if (!media.paused && media.currentTime > 0.1) document.title = 'native-media-live';
                var request = new XMLHttpRequest(); request.open('GET', '/beat'); request.send();
            }, 100);
            </script><iframe src="/slow"></iframe></body></html>
        """.trimIndent().toByteArray()
        server.createContext("/sample.wav") { exchange ->
            exchange.responseHeaders.add("Content-Type", "audio/x-wav")
            exchange.responseHeaders.add("Content-Length", wav.size.toString())
            if (exchange.requestMethod == "HEAD") {
                exchange.sendResponseHeaders(200, -1)
                exchange.close()
            } else {
                exchange.sendResponseHeaders(200, wav.size.toLong())
                exchange.responseBody.use { it.write(wav) }
            }
        }
        server.createContext("/beat") { exchange -> beats.incrementAndGet(); exchange.sendResponseHeaders(204, -1); exchange.close() }
        server.createContext("/slow") { exchange ->
            exchange.responseHeaders.add("Content-Type", "text/html")
            exchange.responseHeaders.add("Connection", "close")
            exchange.sendResponseHeaders(200, 1_000_000)
            try {
                exchange.responseBody.write("<html><body>unfinished native request".toByteArray())
                exchange.responseBody.flush()
                responseStarted.countDown()
                while (!release.await(25, TimeUnit.MILLISECONDS)) {
                    exchange.responseBody.write(' '.code)
                    exchange.responseBody.flush()
                    writes.incrementAndGet()
                }
            } catch (_: IOException) { disconnected.countDown() }
            finally { exchange.close() }
        }
        server.createContext("/") { exchange ->
            exchange.responseHeaders.add("Content-Type", "text/html; charset=utf-8")
            exchange.sendResponseHeaders(200, page.size.toLong())
            exchange.responseBody.use { it.write(page) }
        }
        server.start()
        val state = WebViewState(WebContent.Url("http://127.0.0.1:${server.address.port}/")).apply {
            settings.javaScriptEnabled = true
        }
        var host: WindowHost? = null
        try {
            val activeHost = WindowHost(state).also { host = it }
            activeHost.awaitCreated()
            activeHost.assertShowing()
            assertTrue(responseStarted.await(10, TimeUnit.SECONDS), "A real slow connection must be open before disposal")
            val mediaStarted = System.nanoTime()
            val mediaTrace = mutableListOf<String>()
            var nextObservation = mediaStarted
            try {
                awaitFx {
                    val engine = state.webView!!.engine
                    val now = System.nanoTime()
                    if (now >= nextObservation && mediaTrace.size < 20) {
                        nextObservation = now + TimeUnit.SECONDS.toNanos(1)
                        val nativeObservation = engine.executeScript(
                            "JSON.stringify({title:document.title,hidden:document.hidden,visibility:document.visibilityState," +
                                "paused:media.paused,time:media.currentTime,duration:media.duration,ready:media.readyState," +
                                "error:media.error&&media.error.code})",
                        )
                        mediaTrace += "${TimeUnit.NANOSECONDS.toMillis(now - mediaStarted)}ms:$nativeObservation:beats=${beats.get()}:writes=${writes.get()}"
                    }
                    engine.title == "native-media-live" && beats.get() >= 5 && writes.get() >= 2 &&
                        engine.loadWorker.state == Worker.State.RUNNING &&
                        engine.executeScript("!media.paused && media.currentTime > 0.1 && media.readyState >= 2") == true
                }
            } catch (timeout: TimeoutCancellationException) {
                val media = onFxThread {
                    state.webView!!.engine.executeScript(
                        "JSON.stringify({title:document.title,paused:media.paused,time:media.currentTime," +
                            "ready:media.readyState,error:media.error&&media.error.code,src:media.currentSrc," +
                            "wav:media.canPlayType('audio/wav'),xwav:media.canPlayType('audio/x-wav')})",
                    )
                }
                throw AssertionError("Real media never became live: $media; beats=${beats.get()}, writes=${writes.get()}; nativeTrace=$mediaTrace", timeout)
            }
            println("NATIVECMPKIT_OWNED_MEDIA_TRACE:$mediaTrace") // Authored loopback document values only, no host/user data.
            onFxThread {
                assertEquals(Worker.State.RUNNING, state.webView!!.engine.loadWorker.state)
            }
            assertEquals(1L, disconnected.count, "An already-disconnected request is not cancellation coverage")
            activeHost.close()
            onFxThread { assertNull(state.webView); assertNull(state.owner) }
            assertTrue(disconnected.await(10, TimeUnit.SECONDS), "Disposal must close the live native connection before server cleanup")
            // Allow only already-in-flight HTTP work to drain, then require a continuous quiet interval.
            withTimeout(10_000) {
                while (true) {
                    val before = beats.get()
                    delay(700)
                    if (beats.get() == before) break
                }
            }
            val stopped = beats.get()
            delay(700)
            assertEquals(stopped, beats.get(), "The actual previously-playing media document cannot keep issuing timer/network work")
            assertEquals(1, activeHost.disposed.get())
            assertCollected(activeHost.references)
        } finally {
            try { host?.close() } finally {
                release.countDown()
                try { server.stop(0) } finally {
                    executor.shutdownNow()
                    assertTrue(executor.awaitTermination(5, TimeUnit.SECONDS), "Only this fixture's owned server workers may be cleaned up")
                }
            }
        }
    }

    private class WindowHost(private val state: WebViewState, private val disposeFailure: Throwable? = null) : AutoCloseable {
        val created = AtomicInteger()
        val disposed = AtomicInteger()
        val references = mutableListOf<Pair<String, WeakReference<*>>>()
        private val ready = CompletableDeferred<Unit>()
        private val released = CompletableDeferred<Unit>()
        private val window = AtomicReference<ComposeWindow?>()
        private var mounted by mutableStateOf(true)
        private val observedAttachment = AtomicBoolean(false)

        fun assertShowing() = SwingUtilities.invokeAndWait {
            val view = checkNotNull(window.get())
            assertTrue(view.isVisible && view.isShowing && view.width > 0 && view.height > 0,
                "Native media requires the actual on-screen Compose host, not only a creation callback")
        }

        init {
            SwingUtilities.invokeAndWait {
                val view = ComposeWindow()
                window.set(view)
                // Swing's process-wide RepaintManager retains its most recently painted root
                // independently of this library (verified by owning heap-root diagnostics).
                // Assert native WebView/engine collectability, not that unrelated JDK cache.
                view.setSize(320, 240)
                view.setContent {
                    if (mounted) WebView(state, Modifier.fillMaxSize(), onCreated = {
                        check(Platform.isFxApplicationThread())
                        val native: FxWebView = checkNotNull(state.webView)
                        references += "WebView" to WeakReference(native)
                        references += "WebEngine" to WeakReference(native.engine)
                        created.incrementAndGet()
                        ready.complete(Unit)
                    }, onDispose = {
                        check(Platform.isFxApplicationThread())
                        disposed.incrementAndGet()
                        released.complete(Unit)
                        disposeFailure?.let { throw it }
                    })
                    val attached = state.webView != null
                    SideEffect { observedAttachment.set(attached) }
                }
                view.isVisible = true
            }
        }

        suspend fun awaitCreated() = withTimeout(30_000) {
            ready.await()
            while (!observedAttachment.get()) delay(25)
        }

        suspend fun unmount() = withTimeout(10_000) {
            SwingUtilities.invokeAndWait { mounted = false }
            released.await()
            onFxThread {}
            while (observedAttachment.get()) delay(25)
        }

        override fun close() {
            window.getAndSet(null)?.let { view ->
                SwingUtilities.invokeAndWait { view.dispose() }
                if (ready.isCompleted) runBlocking { withTimeout(10_000) { released.await() }; onFxThread {} }
            }
        }
    }

    private suspend fun awaitFx(condition: () -> Boolean) = withTimeout(20_000) {
        while (!onFxThread(condition)) delay(25)
    }

    private suspend fun assertCollected(references: List<Pair<String, WeakReference<*>>>) {
        assertTrue(references.isNotEmpty())
        repeat(40) {
            System.gc(); System.runFinalization()
            SwingUtilities.invokeAndWait {}
            onFxThread {}
            if (references.all { it.second.get() == null }) return
            delay(50)
        }
        assertFalse(references.any { it.second.get() != null }, "Native weak references remain: ${references.filter { it.second.get() != null }.map { it.first }}")
    }

    /** Authored test-only five-second PCM WAV; no bundled external media/codec or audible-output claim. */
    private fun silentWave(): ByteArray {
        val length = 16_000 * 2 * 5
        return ByteBuffer.allocate(44 + length).order(ByteOrder.LITTLE_ENDIAN).apply {
            put("RIFF".toByteArray()); putInt(36 + length); put("WAVEfmt ".toByteArray())
            putInt(16); putShort(1); putShort(1); putInt(16_000); putInt(32_000); putShort(2); putShort(16)
            put("data".toByteArray()); putInt(length); repeat(length) { put(0) }
        }.array()
    }
}
