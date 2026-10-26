package com.mohamedrejeb.calf.ui.web

import com.sun.net.httpserver.HttpServer
import androidx.compose.runtime.saveable.SaverScope
import javafx.application.Platform
import javafx.concurrent.Worker
import javafx.embed.swing.JFXPanel
import kotlinx.coroutines.*
import org.junit.Assume.assumeFalse
import java.awt.GraphicsEnvironment
import java.net.InetSocketAddress
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.Semaphore
import java.util.concurrent.atomic.AtomicInteger
import javax.swing.SwingUtilities
import kotlin.test.*

/** These use a real JavaFX WebEngine/Scene, not a fake command queue; a display/Xvfb is required. */
class JavaFxWebViewTest {
    /** Keep strict identity meaningful across onFxThread's coroutine stack-trace recovery. */
    @OptIn(ExperimentalCoroutinesApi::class)
    private class CreationCallbackFailure :
        IllegalStateException("application creation callback"),
        CopyableThrowable<CreationCallbackFailure> {
        override fun createCopy(): CreationCallbackFailure? = null
    }

    private class Fixture : AutoCloseable {
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
        val state = WebViewState(WebContent.NavigatorOnly)
        val navigator = WebViewNavigator(scope)
        val panel: JFXPanel
        var disposedCalls = 0
        val owner: DesktopWebViewOwner
        init {
            assumeFalse("JavaFX native integration requires a display (run under Xvfb)", GraphicsEnvironment.isHeadless())
            var createdPanel: JFXPanel? = null
            SwingUtilities.invokeAndWait { createdPanel = JFXPanel() }
            Platform.setImplicitExit(false)
            panel = createdPanel!!
            val created = CountDownLatch(1)
            owner = DesktopWebViewOwner(state, panel, { navigator }, {
                assertNotNull(state.webView, "Native reference must exist inside onCreated")
                created.countDown()
            }, { disposedCalls++ })
            owner.create()
            assertTrue(created.await(15, TimeUnit.SECONDS), "JavaFX creation timed out")
        }
        override fun close() {
            owner.dispose()
            runBlocking { onFxThread {} }
            scope.cancel()
        }
    }

    @Test fun customUserAgentCanBeRestoredAndNativeStateIsReleased() = runBlocking {
        Fixture().use { fixture ->
            val default = onFxThread { fixture.state.webView!!.engine.userAgent }
            fixture.state.settings.desktopSettings.customUserAgent = "nativecmpkit-test"
            assertEquals("nativecmpkit-test", onFxThread { fixture.state.webView!!.engine.userAgent })
            fixture.state.settings.desktopSettings.customUserAgent = null
            assertEquals(default, onFxThread { fixture.state.webView!!.engine.userAgent })
            fixture.owner.dispose()
            fixture.owner.dispose()
            onFxThread {}
            assertNull(fixture.state.webView)
            assertNull(onFxThread { fixture.panel.scene })
            assertEquals(1, fixture.disposedCalls)
        }
    }

    @Test fun javascriptUsesActualEngineAndTypedJsonResults() = runBlocking<Unit> {
        Fixture().use { fixture ->
            fixture.state.settings.javaScriptEnabled = true
            fixture.owner.load(WebContent.Data("<html><title>native-test</title><body>test</body></html>"))
            withTimeout(10_000) { while (fixture.state.loadingState != LoadingState.Finished) delay(10) }
            suspend fun evaluate(script: String): JavascriptResult {
                val result = CompletableDeferred<JavascriptResult>()
                fixture.state.evaluateJavascriptResult(script) { result.complete(it) }
                return withTimeout(5000) { result.await() }
            }
            assertEquals(JavascriptResult.Value("{\"answer\":42}"), evaluate("({answer:42})"))
            assertEquals(JavascriptResult.Value("null"), evaluate("null"))
            assertEquals(JavascriptResult.Undefined, evaluate("undefined"))
            assertIs<JavascriptResult.Error>(evaluate("throw new Error('intentional')"))
        }
    }

    @Test fun stopCancelsRealSlowLoadWithoutFeedbackLoop() = runBlocking {
        Fixture().use { fixture ->
            val server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
            val executor = Executors.newSingleThreadExecutor { runnable -> Thread(runnable, "webview-slow-response").apply { isDaemon = true } }
            server.executor = executor
            server.createContext("/slow") { exchange ->
                try {
                    Thread.sleep(2500)
                    val bytes = "<html>slow</html>".toByteArray()
                    exchange.sendResponseHeaders(200, bytes.size.toLong())
                    exchange.responseBody.use { it.write(bytes) }
                } catch (_: Exception) { exchange.close() }
            }
            server.start()
            try {
                fixture.owner.load(WebContent.Url("http://127.0.0.1:${server.address.port}/slow"))
                withTimeout(5000) {
                    while (onFxThread { fixture.state.webView!!.engine.loadWorker.state } != Worker.State.RUNNING) delay(10)
                }
                var commands = 0
                val collector = launch {
                    fixture.navigator.consumeNavigationEvents { commands++; fixture.owner.navigate(it) }
                }
                fixture.navigator.stopLoading()
                withTimeout(5000) {
                    while (onFxThread { fixture.state.webView!!.engine.loadWorker.isRunning }) delay(10)
                }
                delay(100)
                assertEquals(1, commands, "Stop must not enqueue another navigation event")
                collector.cancelAndJoin()
            } finally { server.stop(0); executor.shutdownNow() }
        }
    }

    @Test fun nativeLinkRedirectReloadAndHistoryKeepRequestedAndRestoredUrlsCurrent() = runBlocking<Unit> {
        Fixture().use { fixture ->
            val server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
            val executor = Executors.newFixedThreadPool(2) { runnable ->
                Thread(runnable, "webview-history-response").apply { isDaemon = true }
            }
            server.executor = executor
            val completions = Semaphore(0)
            val cRequests = AtomicInteger()
            server.createContext("/") { exchange ->
                try {
                    val path = exchange.requestURI.path
                    if (path == "/b") {
                        exchange.responseHeaders.add("Location", "/c")
                        exchange.sendResponseHeaders(302, -1)
                    } else if (path == "/a" || path == "/c") {
                        val name = if (path == "/a") "A" else "C"
                        if (name == "C" && cRequests.incrementAndGet() <= 2) {
                            check(completions.tryAcquire(15, TimeUnit.SECONDS)) { "Test did not release C response" }
                        }
                        val body = "<html><title>$name</title><body><a id='next' href='/b'>next</a></body></html>".toByteArray()
                        exchange.responseHeaders.add("Content-Type", "text/html; charset=utf-8")
                        exchange.responseHeaders.add("Cache-Control", "no-store")
                        exchange.sendResponseHeaders(200, body.size.toLong())
                        exchange.responseBody.use { it.write(body) }
                    } else {
                        // Incidental requests such as favicon.ico must not consume a C gate.
                        exchange.sendResponseHeaders(404, -1)
                    }
                } finally { exchange.close() }
            }
            server.start()
            val base = "http://127.0.0.1:${server.address.port}"
            suspend fun awaitLoaded(url: String) = withTimeout(10_000) {
                while (!onFxThread {
                    fixture.state.loadingState == LoadingState.Finished && fixture.state.lastLoadedUrl == url
                }) delay(10)
            }
            suspend fun savedUrl(): String? = onFxThread {
                val saver = urlReloadWebStateSaver()
                val scope = object : SaverScope { override fun canBeSaved(value: Any) = true }
                val saved = with(saver) { scope.save(fixture.state) }
                (saved?.let(saver::restore)?.content as? WebContent.Url)?.url
            }
            try {
                fixture.state.settings.javaScriptEnabled = true
                fixture.owner.load(WebContent.Url("$base/a"))
                awaitLoaded("$base/a")
                assertEquals("$base/a", onFxThread { fixture.state.requestedUrl })
                onFxThread {
                    fixture.state.errorsForCurrentRequest = listOf(WebViewError(-1, "previous request"))
                    fixture.state.webView!!.engine.executeScript("document.getElementById('next').click()")
                }
                withTimeout(10_000) {
                    while (cRequests.get() < 1 || !onFxThread { fixture.state.loadingState is LoadingState.Loading }) delay(10)
                }
                assertEquals("$base/b", onFxThread { fixture.state.requestedUrl }, "The native link, not declarative content or previous A, started this request")
                assertNull(onFxThread { fixture.state.lastLoadedUrl })
                assertTrue(onFxThread { fixture.state.errorsForCurrentRequest.isEmpty() })
                assertEquals("$base/b", savedUrl(), "Pending restoration uses the accepted request")
                completions.release()
                awaitLoaded("$base/c")
                assertEquals("$base/b", onFxThread { fixture.state.requestedUrl })
                assertEquals("C", onFxThread { fixture.state.pageTitle })
                assertEquals("$base/c", savedUrl(), "Completed restoration uses observed redirect destination")

                fixture.owner.navigate(WebViewNavigator.NavigationEvent.Reload)
                withTimeout(10_000) {
                    while (cRequests.get() < 2 || !onFxThread { fixture.state.loadingState is LoadingState.Loading }) delay(10)
                }
                assertEquals("$base/c", onFxThread { fixture.state.requestedUrl }, "Reload must not reuse B")
                completions.release()
                awaitLoaded("$base/c")
                fixture.owner.navigate(WebViewNavigator.NavigationEvent.Back)
                awaitLoaded("$base/a")
                assertEquals("$base/a", onFxThread { fixture.state.requestedUrl })
                assertEquals("$base/a", savedUrl())
                fixture.owner.navigate(WebViewNavigator.NavigationEvent.Forward)
                awaitLoaded("$base/c")
                assertEquals("$base/c", onFxThread { fixture.state.requestedUrl })
                assertEquals("$base/c", savedUrl())
            } finally {
                completions.release(8)
                server.stop(0)
                executor.shutdownNow()
            }
        }
    }

    @Test fun disposalBeforeQueuedCreationCannotResurrectState() = runBlocking {
        Fixture().use { existing ->
            val state = WebViewState(WebContent.NavigatorOnly)
            var callbacks = 0
            val owner = DesktopWebViewOwner(state, existing.panel, { existing.navigator }, { callbacks++ }, { callbacks++ })
            onFxThread { owner.create(); owner.dispose() }
            onFxThread {}
            assertNull(state.webView)
            assertEquals(0, callbacks)
        }
    }

    @Test fun evaluationQueuedAfterDisposalReportsUnavailableNotAScriptError() = runBlocking<Unit> {
        Fixture().use { fixture ->
            val result = CompletableDeferred<JavascriptResult>()
            onFxThread {
                fixture.state.settings.javaScriptEnabled = true
                fixture.owner.dispose() // Sets disposed now; native teardown is queued next.
                assertNotNull(fixture.state.owner, "Exercise the live state reference before queued release")
                fixture.state.evaluateJavascriptResult("42") { result.complete(it) }
            }
            assertIs<JavascriptResult.Unavailable>(withTimeout(5_000) { result.await() })
            assertNull(fixture.state.webView)
        }
    }

    @Test fun throwingCreationCallbackReleasesActualEngineAndScene() = runBlocking {
        Fixture().use { fixture ->
            val state = WebViewState(WebContent.NavigatorOnly)
            var disposedCalls = 0
            val expected = CreationCallbackFailure()
            val owner = DesktopWebViewOwner(state, fixture.panel, { fixture.navigator }, {
                assertNotNull(state.webView)
                throw expected
            }, { disposedCalls++ })
            val thrown = assertFailsWith<CreationCallbackFailure> { onFxThread { owner.createNow() } }
            assertSame(expected, thrown)
            assertNull(state.webView)
            assertNull(state.owner)
            assertNull(onFxThread { fixture.panel.scene })
            owner.dispose()
            onFxThread {}
            assertEquals(0, disposedCalls, "Failed creation has no completed lifecycle to dispose again")
        }
    }
}
