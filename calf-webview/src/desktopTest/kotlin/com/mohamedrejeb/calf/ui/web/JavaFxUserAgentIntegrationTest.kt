package com.mohamedrejeb.calf.ui.web

import com.sun.net.httpserver.HttpServer
import kotlinx.coroutines.*
import java.net.InetSocketAddress
import java.net.URI
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlin.test.*

/** Actual production JavaFX owners/settings/WebEngines and outgoing HTTP headers. */
class JavaFxUserAgentIntegrationTest {
    private class HttpFixture : AutoCloseable {
        private val id = UUID.randomUUID().toString().replace("-", "")
        private val server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        private val executor = Executors.newFixedThreadPool(2) { runnable ->
            Thread(runnable, "nativecmpkit-user-agent-response").apply { isDaemon = true }
        }
        private val requests = ConcurrentHashMap<String, String>()
        private val sequence = AtomicInteger()
        private val path = "/nativecmpkit-user-agent-$id/"
        private val base = "http://127.0.0.1:${server.address.port}$path"
        init {
            server.executor = executor
            server.createContext(path) { exchange ->
                try {
                    val requestPath = exchange.requestURI.path
                    requests[requestPath] = exchange.requestHeaders.getFirst("User-Agent") ?: "<absent>"
                    val title = requestPath.substringAfterLast('/')
                    val bytes = "<html><title>$title</title><body>real outgoing user-agent fixture</body></html>".toByteArray()
                    exchange.responseHeaders.add("Content-Type", "text/html; charset=utf-8")
                    exchange.responseHeaders.add("Cache-Control", "no-store")
                    exchange.sendResponseHeaders(200, bytes.size.toLong())
                    exchange.responseBody.use { it.write(bytes) }
                } finally { exchange.close() }
            }
            server.start()
        }
        suspend fun loadAndAssert(view: JavaFxWebViewTest.Fixture, expected: String) {
            val title = "request_${sequence.incrementAndGet()}"
            val url = base + title
            view.state.settings.javaScriptEnabled = true
            view.owner.load(WebContent.Url(url))
            withTimeout(10_000) {
                while (!onFxThread {
                    val engine = assertNotNull(view.state.webView).engine
                    view.state.loadingState == LoadingState.Finished && view.state.lastLoadedUrl == url &&
                        engine.title == title && engine.executeScript("document.title") == title && view.state.pageTitle == title
                }) delay(10)
            }
            onFxThread {
                val engine = assertNotNull(view.state.webView).engine
                assertEquals(expected, engine.userAgent, "The public setting must reach the actual native engine")
                assertEquals("text/html", engine.executeScript("document.contentType"))
            }
            assertEquals(expected, requests[URI(url).path], "The actual outgoing request must carry this view's current User-Agent")
        }
        override fun close() {
            server.stop(0)
            executor.shutdownNow()
            assertTrue(executor.awaitTermination(5, TimeUnit.SECONDS), "Owned HTTP response threads must terminate")
        }
    }

    @Test fun actualHttpUserAgentChangesFromAToBAndNullRestoresTheNativeDefault() = runBlocking<Unit> {
        HttpFixture().use { http ->
            JavaFxWebViewTest.Fixture().use { view ->
                val original = onFxThread { assertNotNull(view.state.webView).engine.userAgent }
                assertTrue(original.isNotBlank(), "Capture the real native default, never an invented fallback")
                view.state.settings.desktopSettings.customUserAgent = "NativeCmpKit-UA-A"
                http.loadAndAssert(view, "NativeCmpKit-UA-A")
                view.state.settings.desktopSettings.customUserAgent = "NativeCmpKit-UA-B"
                http.loadAndAssert(view, "NativeCmpKit-UA-B")
                view.state.settings.desktopSettings.customUserAgent = null
                http.loadAndAssert(view, original)
            }
        }
    }

    @Test fun twoActualViewsKeepIndependentDefaultsAndResetOnlyTheirOwnRequestHeaders() = runBlocking<Unit> {
        HttpFixture().use { http ->
            JavaFxWebViewTest.Fixture().use { first ->
                JavaFxWebViewTest.Fixture().use { second ->
                    val defaults = onFxThread {
                        val firstEngine = assertNotNull(first.state.webView).engine
                        val secondEngine = assertNotNull(second.state.webView).engine
                        assertNotSame(firstEngine, secondEngine)
                        firstEngine.userAgent to secondEngine.userAgent
                    }
                    // This host can legitimately have equal native defaults. Capture
                    // each actual engine separately; do not invent unequal defaults.
                    assertTrue(defaults.first.isNotBlank() && defaults.second.isNotBlank())
                    first.state.settings.desktopSettings.customUserAgent = "NativeCmpKit-UA-first"
                    second.state.settings.desktopSettings.customUserAgent = "NativeCmpKit-UA-second"
                    coroutineScope {
                        awaitAll(async { http.loadAndAssert(first, "NativeCmpKit-UA-first") },
                            async { http.loadAndAssert(second, "NativeCmpKit-UA-second") })
                    }
                    first.state.settings.desktopSettings.customUserAgent = null
                    coroutineScope {
                        awaitAll(async { http.loadAndAssert(first, defaults.first) },
                            async { http.loadAndAssert(second, "NativeCmpKit-UA-second") })
                    }
                    first.state.settings.desktopSettings.customUserAgent = "NativeCmpKit-UA-first-again"
                    second.state.settings.desktopSettings.customUserAgent = null
                    coroutineScope {
                        awaitAll(async { http.loadAndAssert(first, "NativeCmpKit-UA-first-again") },
                            async { http.loadAndAssert(second, defaults.second) })
                    }
                }
            }
        }
    }
}
