// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import androidx.compose.ui.awt.ComposeWindow
import javafx.application.Platform
import javafx.beans.value.ChangeListener
import javafx.concurrent.Worker
import javafx.scene.web.WebView as FxWebView
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import java.io.ByteArrayOutputStream
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket
import java.net.SocketTimeoutException
import java.util.UUID
import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CountDownLatch
import java.util.concurrent.ThreadPoolExecutor
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import javax.swing.SwingUtilities
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

/**
 * Missing literal Desktop cells only: public navigator Stop on a held real HTTP
 * request, and an actual HTTP302/native document link followed by public Reload.
 * Uses the genuine public Compose/JavaFX owner, not a manual navigation collector,
 * synthetic error/state write or direct engine loader/cancellation. Server cleanup
 * cannot witness Stop; the client EOF and native CANCELLED precede any teardown.
 */
class DesktopWebViewStopRedirectAcceptanceTest {
    @Test fun publicStopCancelsOneHeldNativeRequestBeforeAnyResponseAndRecoversOnTheSameOwner() = runBlocking<Unit> {
        OwnedServer.create().use { server ->
            val state = WebViewState(WebContent.NavigatorOnly).apply { settings.javaScriptEnabled = true }
            val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
            val navigator = WebViewNavigator(scope)
            val cancellations = AtomicInteger()
            val observer = ChangeListener<Worker.State> { _, _, current ->
                if (current == Worker.State.CANCELLED) cancellations.incrementAndGet()
            }
            var host: NativeWindow? = null
            var observed: FxWebView? = null
            var failure: Throwable? = null
            try {
                val active = NativeWindow(state, navigator).also { host = it }
                active.awaitCreated()
                val native = onFxThread { assertNotNull(state.webView) }.also { observed = it }
                val owner = onFxThread { assertNotNull(state.owner) }
                onFxThread { native.engine.loadWorker.stateProperty().addListener(observer) }
                suspend fun await(description: String, condition: () -> Boolean) = awaitFx(description) {
                    active.assertHealthy(); server.assertHealthy()
                    assertSame(native, state.webView); assertSame(owner, state.owner)
                    condition()
                }
                suspend fun document(kind: Endpoint) = await("actual native document and terminal library metadata") {
                    server.responses(kind) == 1 && server.pending(kind) == 0 &&
                        native.engine.loadWorker.state == Worker.State.SUCCEEDED &&
                        native.engine.location == server.url(kind) && state.lastLoadedUrl == server.url(kind) &&
                        native.engine.title == server.title(kind, 1) && state.pageTitle == server.title(kind, 1) &&
                        native.engine.executeScript("document.title") == server.title(kind, 1) &&
                        state.loadingState == LoadingState.Finished && state.errorsForCurrentRequest.isEmpty()
                }

                navigator.loadUrl(server.url(Endpoint.Seed))
                document(Endpoint.Seed)
                navigator.loadUrl(server.url(Endpoint.StopHeld))
                await("the real connected request held before all response bytes") {
                    server.arrivals(Endpoint.StopHeld) == 1 && server.pending(Endpoint.StopHeld) == 1 &&
                        native.engine.loadWorker.state == Worker.State.RUNNING &&
                        native.engine.location == server.url(Endpoint.StopHeld)
                }
                onFxThread {
                    assertEquals(server.url(Endpoint.StopHeld), state.requestedUrl)
                    assertTrue(state.loadingState is LoadingState.Loading)
                    assertNull(state.lastLoadedUrl); assertNull(state.pageTitle)
                    assertTrue(state.errorsForCurrentRequest.isEmpty())
                }
                assertEquals(0, server.responses(Endpoint.StopHeld))
                assertEquals(0, server.peerEofs(Endpoint.StopHeld))
                assertEquals(0, cancellations.get())
                assertFalse(server.isClosing(), "Fixture teardown must not manufacture the Stop witness")

                navigator.stopLoading() // Actual public command consumed by the mounted library owner.
                // Scalar-only last FX-poll sample; not an acceptance predicate or a transport action.
                // Counter reads are sequential observations, not a simultaneous snapshot of the peer.
                val stopSnapshot = AtomicReference("sampled=false")
                try {
                    await("public Stop native cancellation and actual pre-header client EOF") {
                        stopSnapshot.set("sampled=true" +
                            ";worker=${native.engine.loadWorker.state.name}" +
                            ";running=${native.engine.loadWorker.isRunning}" +
                            ";finished=${state.loadingState == LoadingState.Finished}" +
                            ";cancellations=${cancellations.get()}" +
                            ";peerEofs=${server.peerEofs(Endpoint.StopHeld)}" +
                            ";pending=${server.pending(Endpoint.StopHeld)}" +
                            ";arrivals=${server.arrivals(Endpoint.StopHeld)}" +
                            ";responses=${server.responses(Endpoint.StopHeld)}" +
                            ";closing=${server.isClosing()}")
                        native.engine.loadWorker.state == Worker.State.CANCELLED &&
                            !native.engine.loadWorker.isRunning && state.loadingState == LoadingState.Finished &&
                            cancellations.get() == 1 && server.peerEofs(Endpoint.StopHeld) == 1 &&
                            server.pending(Endpoint.StopHeld) == 0
                    }
                } catch (error: AssertionError) {
                    // Preserve the original timeout/owning refusal as the cause; failure stays failure.
                    runCatching { captureWindowsStopFailureResources(native.javaClass) }
                    throw AssertionError("public Stop witness refused; ${stopSnapshot.get()}", error)
                }
                assertFalse(server.isClosing())
                assertEquals(1, server.arrivals(Endpoint.StopHeld), "Stop must not feed another navigation request")
                assertEquals(0, server.responses(Endpoint.StopHeld), "The held request never received an HTTP response")
                onFxThread {
                    assertEquals(server.url(Endpoint.StopHeld), state.requestedUrl)
                    assertNull(state.lastLoadedUrl); assertNull(state.pageTitle)
                    assertTrue(state.errorsForCurrentRequest.isEmpty(), "Cancellation is not an injected transport error")
                }
                assertEquals(1, active.created.get()); assertEquals(0, active.disposed.get())

                navigator.loadUrl(server.url(Endpoint.Recovery))
                document(Endpoint.Recovery)
                onFxThread { assertEquals(server.url(Endpoint.Recovery), state.requestedUrl) }
                assertEquals(1, cancellations.get())
                assertEquals(1, server.arrivals(Endpoint.StopHeld))
                assertEquals(1, active.created.get()); assertEquals(0, active.disposed.get())
            } catch (error: Throwable) { failure = error; throw error }
            finally {
                runWebViewCleanup(failure,
                    { observed?.let { view -> runBlocking { withTimeout(10_000) {
                        onFxThread { view.engine.loadWorker.stateProperty().removeListener(observer) }
                    } } } },
                    { host?.close() }, { scope.cancel() },
                )
            }
        }
    }

    @Test fun actual302RedirectAndPublicReloadKeepNativeRequestAndTerminalMetadataDistinct() = runBlocking<Unit> {
        OwnedServer.create().use { server ->
            val state = WebViewState(WebContent.NavigatorOnly).apply { settings.javaScriptEnabled = true }
            val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
            val navigator = WebViewNavigator(scope)
            var host: NativeWindow? = null
            var failure: Throwable? = null
            try {
                val active = NativeWindow(state, navigator).also { host = it }
                active.awaitCreated()
                val native = onFxThread { assertNotNull(state.webView) }
                val owner = onFxThread { assertNotNull(state.owner) }
                suspend fun await(description: String, condition: () -> Boolean) = awaitFx(description) {
                    active.assertHealthy(); server.assertHealthy()
                    assertSame(native, state.webView); assertSame(owner, state.owner)
                    condition()
                }
                navigator.loadUrl(server.url(Endpoint.Seed))
                await("authored native seed document") {
                    server.responses(Endpoint.Seed) == 1 && native.engine.loadWorker.state == Worker.State.SUCCEEDED &&
                        state.lastLoadedUrl == server.url(Endpoint.Seed) && state.pageTitle == server.title(Endpoint.Seed, 1) &&
                        native.engine.executeScript("document.title") == server.title(Endpoint.Seed, 1) &&
                        native.engine.title == server.title(Endpoint.Seed, 1)
                }
                onFxThread {
                    assertEquals(server.url(Endpoint.Seed), state.requestedUrl)
                    native.engine.executeScript("document.getElementById('nativecmpkit-next').click(); 1")
                }
                suspend fun heldTarget(attempt: Int, requested: String) {
                    await("actual302 destination/Reload request held before its response") {
                        server.arrivals(Endpoint.Redirect) == 1 && server.responses(Endpoint.Redirect) == 1 &&
                            server.arrivals(Endpoint.Target) == attempt && server.pending(Endpoint.Target) == 1 &&
                            server.responses(Endpoint.Target) == attempt - 1 &&
                            native.engine.loadWorker.state == Worker.State.RUNNING &&
                            native.engine.location == server.url(Endpoint.Target)
                    }
                    onFxThread {
                        assertEquals(requested, state.requestedUrl)
                        assertTrue(state.loadingState is LoadingState.Loading)
                        assertNull(state.lastLoadedUrl); assertNull(state.pageTitle)
                        assertTrue(state.errorsForCurrentRequest.isEmpty())
                    }
                }
                suspend fun completedTarget(attempt: Int, requested: String) {
                    await("new actual target document, native title and terminal library URL") {
                        server.responses(Endpoint.Target) == attempt && server.pending(Endpoint.Target) == 0 &&
                            native.engine.loadWorker.state == Worker.State.SUCCEEDED &&
                            native.engine.location == server.url(Endpoint.Target) && state.lastLoadedUrl == server.url(Endpoint.Target) &&
                            native.engine.title == server.title(Endpoint.Target, attempt) &&
                            native.engine.executeScript("document.title") == server.title(Endpoint.Target, attempt) &&
                            state.pageTitle == server.title(Endpoint.Target, attempt) &&
                            state.loadingState == LoadingState.Finished && state.errorsForCurrentRequest.isEmpty()
                    }
                    onFxThread { assertEquals(requested, state.requestedUrl) }
                }
                heldTarget(1, server.url(Endpoint.Redirect))
                server.releaseTarget(1)
                completedTarget(1, server.url(Endpoint.Redirect))

                navigator.reload() // Reload must use the actual final target, not repeat the redirect origin.
                heldTarget(2, server.url(Endpoint.Target))
                server.releaseTarget(2)
                completedTarget(2, server.url(Endpoint.Target))
                assertEquals(1, server.arrivals(Endpoint.Redirect))
                assertEquals(2, server.arrivals(Endpoint.Target))
                assertEquals(2, server.responses(Endpoint.Target))
                assertEquals(1, active.created.get()); assertEquals(0, active.disposed.get())
            } catch (error: Throwable) { failure = error; throw error }
            finally { runWebViewCleanup(failure, { host?.close() }, { scope.cancel() }) }
        }
    }

    private suspend fun awaitFx(description: String, condition: () -> Boolean) {
        try { withTimeout(10_000) { while (!onFxThread(condition)) delay(25) } }
        catch (timeout: TimeoutCancellationException) { throw AssertionError("Timed out awaiting $description", timeout) }
    }

    private class NativeWindow(private val state: WebViewState, navigator: WebViewNavigator) : AutoCloseable {
        val created = AtomicInteger()
        val disposed = AtomicInteger()
        private val ready = CompletableDeferred<Unit>()
        private val failure = AtomicReference<Throwable>()
        private val window = BoundedDesktopAwtWindow(
            schedule = { work -> SwingUtilities.invokeLater(work) },
            create = { ComposeWindow() },
            configure = { view ->
                view.setSize(320, 240)
                view.setContent {
                    WebView(state, Modifier.fillMaxSize(), navigator = navigator,
                        onCreated = {
                            runCatching {
                                assertTrue(Platform.isFxApplicationThread()); assertNotNull(state.webView); assertNotNull(state.owner)
                                assertEquals(1, created.incrementAndGet())
                            }.onFailure { failure.compareAndSet(null, it) }
                            ready.complete(Unit)
                        }, onDispose = {
                            runCatching {
                                assertTrue(Platform.isFxApplicationThread()); assertNotNull(state.webView)
                                assertEquals(1, disposed.incrementAndGet())
                            }.onFailure { failure.compareAndSet(null, it) }
                        })
                }
                view.isVisible = true; assertTrue(view.isVisible && view.isShowing)
            },
            dispose = { view -> view.dispose() },
        )
        init {
            try {
                window.awaitCreated(30_000)
            } catch (error: Throwable) { runWebViewCleanup(error, { close() }) }
        }
        suspend fun awaitCreated() = withTimeout(30_000) { ready.await(); assertHealthy() }
        fun assertHealthy() { failure.get()?.let { throw it } }
        override fun close() {
            runWebViewCleanup(null,
                { window.close(10_000) },
                { runBlocking { withTimeout(10_000) { while (state.webView != null || state.owner != null) delay(25) } } },
                { if (created.get() == 1) assertEquals(1, disposed.get()) },
                { assertNull(state.webView); assertNull(state.owner) }, { assertHealthy() },
            )
        }
    }

    private enum class Endpoint { Seed, StopHeld, Recovery, Redirect, Target }

    /** Fixed loopback-only raw HTTP; StopHeld can only end through real peer EOF or owned cleanup. */
    private class OwnedServer private constructor(private val listener: ServerSocket, private val workers: ThreadPoolExecutor) : AutoCloseable {
        private class Stage {
            val arrivals = AtomicInteger(); val pending = AtomicInteger(); val responses = AtomicInteger(); val peerEofs = AtomicInteger()
        }
        private val nonce = UUID.randomUUID().toString().replace("-", "")
        private val stages = Endpoint.entries.associateWith { Stage() }
        private val targetGates = (1..2).associateWith { CountDownLatch(1) }
        private val sockets = ConcurrentHashMap.newKeySet<Socket>()
        private val closing = AtomicBoolean()
        private val failure = AtomicReference<Throwable>()
        private val connections = AtomicInteger()
        private val acceptor = Thread({ accept() }, "nativecmpkit-owned-stop-redirect-acceptor").apply { isDaemon = true }
        private fun path(kind: Endpoint) = "/nativecmpkit-stop-redirect-$nonce/${kind.name}"
        fun url(kind: Endpoint) = "http://127.0.0.1:${listener.localPort}${path(kind)}"
        fun title(kind: Endpoint, attempt: Int) = "nativecmpkit-$nonce-${kind.name}-$attempt"
        fun arrivals(kind: Endpoint) = stages.getValue(kind).arrivals.get()
        fun pending(kind: Endpoint) = stages.getValue(kind).pending.get()
        fun responses(kind: Endpoint) = stages.getValue(kind).responses.get()
        fun peerEofs(kind: Endpoint) = stages.getValue(kind).peerEofs.get()
        fun isClosing() = closing.get()
        fun releaseTarget(attempt: Int) { check(attempt in 1..2 && !closing.get()); targetGates.getValue(attempt).countDown() }
        fun assertHealthy() { failure.get()?.let { throw AssertionError("Owned Stop/redirect fixture failed", it) } }
        private fun record(error: Throwable) { if (!closing.get()) failure.compareAndSet(null, error) }
        private fun closeOwnedSocket(socket: Socket) {
            try { socket.close(); check(socket.isClosed); sockets -= socket }
            catch (error: Throwable) { failure.compareAndSet(null, error); throw error }
        }
        private fun accept() {
            while (!closing.get()) {
                var accepted: Socket? = null
                try {
                    val socket = listener.accept().also { accepted = it }; sockets += socket
                    check(connections.incrementAndGet() <= 64) { "Owned connection budget exceeded" }
                    workers.execute { serve(socket) }; accepted = null
                } catch (error: Throwable) {
                    accepted?.let { socket -> runCatching { closeOwnedSocket(socket) } }
                    record(error); if (!closing.get()) break
                }
            }
        }
        private fun serve(socket: Socket) {
            var stage: Stage? = null
            var registered = false
            try {
                if (closing.get()) return
                val input = socket.getInputStream(); val headerDeadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5)
                val bytes = ByteArrayOutputStream(); var tail = 0
                while (true) {
                    val remaining = headerDeadline - System.nanoTime(); check(remaining > 0) { "HTTP header deadline exceeded" }
                    socket.soTimeout = TimeUnit.NANOSECONDS.toMillis(remaining).coerceIn(1, 5_000).toInt()
                    val value = input.read(); check(value >= 0); check(bytes.size() < 8_192)
                    bytes.write(value); tail = (tail shl 8) or value; if (tail == 0x0d0a0d0a) break
                }
                val lines = bytes.toString(Charsets.US_ASCII.name()).split("\r\n"); val request = lines.first().split(' ')
                check(request.size == 3 && request[0] == "GET" && request[2] in setOf("HTTP/1.0", "HTTP/1.1"))
                val hosts = lines.drop(1).filter { it.startsWith("Host:", true) }
                check(hosts.size == 1 && hosts.single().substringAfter(':').trim() == "127.0.0.1:${listener.localPort}")
                if (request[1] == "/favicon.ico") { respond(socket, 204, byteArrayOf()); return }
                val kind = Endpoint.entries.singleOrNull { path(it) == request[1] } ?: error("Unowned request path refused")
                val current = stages.getValue(kind); stage = current
                val attempt = current.arrivals.incrementAndGet(); check(attempt <= if (kind == Endpoint.Target) 2 else 1)
                current.pending.incrementAndGet(); registered = true
                when (kind) {
                    Endpoint.StopHeld -> {
                        // Do not close/release the server side or send headers to witness Stop.
                        // Native client cancellation must close this actual connected request.
                        val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(15)
                        socket.soTimeout = 100
                        while (!closing.get()) {
                            check(System.nanoTime() < deadline) { "Public Stop did not close its held native request" }
                            try {
                                check(input.read() == -1) { "Unexpected bytes after the owned GET header" }
                                current.peerEofs.incrementAndGet(); return
                            } catch (_: SocketTimeoutException) { /* Bounded peer-EOF poll, no response bytes. */ }
                        }
                    }
                    Endpoint.Redirect -> {
                        respond(socket, 302, byteArrayOf(), path(Endpoint.Target))
                        closeOwnedSocket(socket); current.responses.incrementAndGet()
                    }
                    else -> {
                        if (kind == Endpoint.Target) check(targetGates.getValue(attempt).await(15, TimeUnit.SECONDS))
                        if (closing.get()) return
                        val link = if (kind == Endpoint.Seed) "<a id='nativecmpkit-next' href='${path(Endpoint.Redirect)}'>next</a>" else "owned"
                        val payload = "<!doctype html><html><head><title>${title(kind, attempt)}</title></head><body>$link</body></html>".toByteArray(Charsets.UTF_8)
                        respond(socket, 200, payload); closeOwnedSocket(socket); current.responses.incrementAndGet()
                    }
                }
            } catch (error: Throwable) { record(error) }
            finally {
                if (registered) checkNotNull(stage).pending.decrementAndGet()
                runCatching { closeOwnedSocket(socket) } // Socket-close failures latch even during shutdown.
            }
        }
        private fun respond(socket: Socket, code: Int, body: ByteArray, location: String? = null) {
            check(code in setOf(200, 204, 302)); check((code == 302) == (location != null))
            val reason = when (code) { 200 -> "OK"; 302 -> "Found"; else -> "No Content" }
            val redirect = location?.let { "Location: $it\r\n" } ?: ""
            val output = socket.getOutputStream()
            output.write(("HTTP/1.1 $code $reason\r\n" + redirect + "Content-Type: text/html; charset=utf-8\r\n" +
                "Content-Length: ${body.size}\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n").toByteArray(Charsets.US_ASCII))
            output.write(body); output.flush()
        }
        override fun close() {
            if (!closing.compareAndSet(false, true)) return
            runWebViewCleanup(null,
                { targetGates.values.forEach { it.countDown() } },
                { listener.close(); assertTrue(listener.isClosed) },
                { acceptor.join(5_000); assertFalse(acceptor.isAlive) },
                { runWebViewCleanup(stages = sockets.toList().map { socket -> { closeOwnedSocket(socket) } }.toTypedArray()) },
                { workers.shutdownNow(); assertTrue(workers.awaitTermination(5, TimeUnit.SECONDS)) },
                { assertTrue(sockets.isEmpty()); assertTrue(stages.values.all { it.pending.get() == 0 }) },
                { assertHealthy() },
            )
        }
        companion object {
            fun create(): OwnedServer {
                var listener: ServerSocket? = null; var workers: ThreadPoolExecutor? = null
                try {
                    val socket = ServerSocket(0, 8, InetAddress.getByName("127.0.0.1")).also { listener = it }
                    val pool = ThreadPoolExecutor(4, 4, 0, TimeUnit.MILLISECONDS, ArrayBlockingQueue<Runnable>(8),
                        { runnable -> Thread(runnable, "nativecmpkit-owned-stop-redirect-worker").apply { isDaemon = true } },
                        ThreadPoolExecutor.AbortPolicy()).also { workers = it }
                    return OwnedServer(socket, pool).also { it.acceptor.start() }
                } catch (error: Throwable) {
                    runWebViewCleanup(error, { listener?.close() }, {
                        workers?.let { pool -> pool.shutdownNow(); check(pool.awaitTermination(5, TimeUnit.SECONDS)) }
                    }); throw error
                }
            }
        }
    }
}
