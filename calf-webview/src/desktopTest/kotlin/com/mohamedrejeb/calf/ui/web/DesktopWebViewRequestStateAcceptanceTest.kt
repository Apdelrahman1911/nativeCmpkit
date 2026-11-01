// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import androidx.compose.ui.awt.ComposeWindow
import javafx.application.Platform
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
 * Real library-owned Compose/JavaFX and owned TCP responses. No URL handler,
 * synthetic WebViewError, manual Worker callback, proxy or global networking change.
 * Native engine.load deliberately exercises SCHEDULED without acceptContent's
 * earlier reset. This is HTTP transport-refusal coverage, not offline/DNS/TLS.
 */
class DesktopWebViewRequestStateAcceptanceTest {
    @Test fun twoHeldNativeTransportFailuresResetOldErrorsAndRecoverOnTheSameOwner() = runBlocking<Unit> {
        OwnedRequestServer.create().use { server ->
            val state = WebViewState(WebContent.NavigatorOnly).apply { settings.javaScriptEnabled = true }
            val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
            var host: RequestWindow? = null
            var failure: Throwable? = null
            try {
                val active = RequestWindow(state, WebViewNavigator(scope)).also { host = it }
                active.awaitCreated()
                val native = onFxThread { assertNotNull(state.webView) }

                suspend fun awaitFx(description: String, condition: () -> Boolean) {
                    try {
                        withTimeout(10_000) {
                            while (!onFxThread {
                                active.assertHealthy()
                                server.assertHealthy()
                                assertSame(native, state.webView, "A request must not replace the owned native engine")
                                assertNotNull(state.owner)
                                condition()
                            }) delay(25)
                        }
                    } catch (timeout: TimeoutCancellationException) {
                        throw AssertionError("Timed out awaiting $description", timeout)
                    }
                }

                suspend fun load(stage: RequestStage) = onFxThread {
                    active.assertHealthy()
                    server.assertHealthy()
                    assertSame(native, state.webView)
                    native.engine.load(server.url(stage))
                }

                suspend fun awaitHeld(stage: RequestStage) {
                    awaitFx("actual owned request held before any response header") {
                        server.arrivals(stage) >= 1 && server.pending(stage) >= 1 &&
                            native.engine.loadWorker.state == Worker.State.RUNNING &&
                            native.engine.location == server.url(stage)
                    }
                    onFxThread {
                        assertTrue(state.loadingState is LoadingState.Loading)
                        assertEquals(server.url(stage), state.requestedUrl)
                        assertNull(state.lastLoadedUrl)
                        assertNull(state.pageTitle)
                        assertTrue(state.errorsForCurrentRequest.isEmpty(), "Native request start clears the previous request's errors")
                    }
                    assertEquals(0, server.refusals(stage), "The client must still be connected before the test releases refusal")
                    assertEquals(0, server.responses(stage), "A held/refused endpoint sends no response headers or body")
                }

                suspend fun awaitFailure(stage: RequestStage) {
                    awaitFx("real native Worker failure after owned pre-header response destruction") {
                        server.refusals(stage) >= 1 && server.pending(stage) == 0 &&
                            native.engine.loadWorker.state == Worker.State.FAILED
                    }
                    onFxThread {
                        assertNotNull(native.engine.loadWorker.exception)
                        assertEquals(LoadingState.Finished, state.loadingState)
                        assertEquals(server.url(stage), state.requestedUrl)
                        assertEquals(1, state.errorsForCurrentRequest.size, "Only this request's native terminal error is retained")
                        assertEquals(-1, state.errorsForCurrentRequest.single().code)
                    }
                    assertEquals(0, server.responses(stage), "A native failed request is not an HTTP error document")
                }

                suspend fun awaitDocument(stage: RequestStage) {
                    awaitFx("complete authored native document and library metadata") {
                        server.responses(stage) == 1 && server.pending(stage) == 0 &&
                            native.engine.loadWorker.state == Worker.State.SUCCEEDED &&
                            state.loadingState == LoadingState.Finished &&
                            native.engine.location == server.url(stage) && state.lastLoadedUrl == server.url(stage) &&
                            native.engine.title == server.title(stage) && state.pageTitle == server.title(stage) &&
                            native.engine.executeScript("document.title") == server.title(stage)
                    }
                    onFxThread {
                        assertEquals(server.url(stage), state.requestedUrl)
                        assertTrue(state.errorsForCurrentRequest.isEmpty())
                    }
                }

                load(RequestStage.Seed)
                awaitDocument(RequestStage.Seed)
                load(RequestStage.FirstFailure)
                awaitHeld(RequestStage.FirstFailure)
                server.release(RequestStage.FirstFailure)
                awaitFailure(RequestStage.FirstFailure)

                // No common state write, content update or manually injected error occurs
                // between the two actual failures: only the current native loader starts work.
                load(RequestStage.SecondFailure)
                awaitHeld(RequestStage.SecondFailure)
                server.release(RequestStage.SecondFailure)
                awaitFailure(RequestStage.SecondFailure)

                load(RequestStage.Recovery)
                awaitHeld(RequestStage.Recovery)
                server.release(RequestStage.Recovery)
                awaitDocument(RequestStage.Recovery)
                assertEquals(1, active.created.get())
                assertEquals(0, active.disposed.get())
            } catch (error: Throwable) {
                failure = error
                throw error
            } finally {
                // Window disposal must run before fixture cleanup; never declare server
                // cleanup to be the native stop or the request's refusal/recovery witness.
                runWebViewCleanup(failure, { host?.close() }, { scope.cancel() })
            }
        }
    }

    private class RequestWindow(private val state: WebViewState, navigator: WebViewNavigator) : AutoCloseable {
        val created = AtomicInteger()
        val disposed = AtomicInteger()
        private val ready = CompletableDeferred<Unit>()
        private val failure = AtomicReference<Throwable>()
        private val window = AtomicReference<ComposeWindow?>()

        init {
            try {
                SwingUtilities.invokeAndWait {
                    val view = ComposeWindow()
                    window.set(view)
                    view.setSize(320, 240)
                    view.setContent {
                        WebView(state, Modifier.fillMaxSize(), navigator = navigator,
                            onCreated = {
                                // Keep callback assertions observable without throwing into
                                // the toolkit event loop or replacing its global handler.
                                runCatching {
                                    assertTrue(Platform.isFxApplicationThread())
                                    assertNotNull(state.webView)
                                    assertNotNull(state.owner)
                                    assertEquals(1, created.incrementAndGet())
                                }.onFailure { failure.compareAndSet(null, it) }
                                ready.complete(Unit)
                            }, onDispose = {
                                runCatching {
                                    assertTrue(Platform.isFxApplicationThread())
                                    assertNotNull(state.webView)
                                    assertEquals(1, disposed.incrementAndGet())
                                }.onFailure { failure.compareAndSet(null, it) }
                            })
                    }
                    view.isVisible = true
                    assertTrue(view.isVisible && view.isShowing)
                }
            } catch (error: Throwable) {
                runWebViewCleanup(error, { close() })
            }
        }

        suspend fun awaitCreated() = withTimeout(30_000) { ready.await(); assertHealthy() }
        fun assertHealthy() { failure.get()?.let { throw it } }

        override fun close() {
            runWebViewCleanup(null,
                { window.getAndSet(null)?.let { view -> SwingUtilities.invokeAndWait { view.dispose() } } },
                { runBlocking { withTimeout(10_000) {
                    // These owning handle fields are atomic/volatile. Never cold-call
                    // Platform.runLater when creation failed before toolkit readiness.
                    while (state.webView != null || state.owner != null) delay(25)
                } } },
                { if (created.get() == 1) assertEquals(1, disposed.get()) },
                { assertNull(state.webView); assertNull(state.owner) },
                { assertHealthy() },
            )
        }
    }

    private enum class RequestStage(val fails: Boolean, val held: Boolean) {
        Seed(false, false), FirstFailure(true, true), SecondFailure(true, true), Recovery(false, true),
    }

    /** Finite loopback-only raw HTTP fixture; deliberate refusal writes exactly zero bytes. */
    private class OwnedRequestServer private constructor(
        private val listener: ServerSocket,
        private val workers: ThreadPoolExecutor,
    ) : AutoCloseable {
        private class Stage(val kind: RequestStage) {
            val release = CountDownLatch(if (kind.held) 1 else 0)
            val arrivals = AtomicInteger()
            val pending = AtomicInteger()
            val refusals = AtomicInteger()
            val responses = AtomicInteger()
        }
        private val nonce = UUID.randomUUID().toString().replace("-", "")
        private val stages = RequestStage.entries.associateWith { Stage(it) }
        private val sockets = ConcurrentHashMap.newKeySet<Socket>()
        private val closing = AtomicBoolean()
        private val failure = AtomicReference<Throwable>()
        private val connections = AtomicInteger()
        private val acceptor = Thread({ accept() }, "nativecmpkit-owned-request-acceptor").apply { isDaemon = true }
        private fun path(kind: RequestStage) = "/nativecmpkit-request-$nonce/${kind.name}"
        fun url(kind: RequestStage) = "http://127.0.0.1:${listener.localPort}${path(kind)}"
        fun title(kind: RequestStage) = "nativecmpkit-$nonce-${kind.name}"
        fun arrivals(kind: RequestStage) = stages.getValue(kind).arrivals.get()
        fun pending(kind: RequestStage) = stages.getValue(kind).pending.get()
        fun refusals(kind: RequestStage) = stages.getValue(kind).refusals.get()
        fun responses(kind: RequestStage) = stages.getValue(kind).responses.get()
        fun release(kind: RequestStage) { check(kind.held && !closing.get()); stages.getValue(kind).release.countDown() }
        fun assertHealthy() { failure.get()?.let { throw AssertionError("Owned request fixture failed", it) } }
        private fun record(error: Throwable) { if (!closing.get()) failure.compareAndSet(null, error) }

        /** A failed close remains owned and red even after work admission has stopped. */
        private fun closeOwnedSocket(socket: Socket) {
            try {
                socket.close()
                check(socket.isClosed) { "Owned request socket close was not observed" }
                sockets -= socket
            } catch (error: Throwable) {
                // Work cancellation during shutdown may be expected; socket-close
                // failure is not. Retain it before returning to a worker/acceptor.
                failure.compareAndSet(null, error)
                throw error
            }
        }

        private fun accept() {
            while (!closing.get()) {
                var accepted: Socket? = null
                try {
                    val socket = listener.accept().also { accepted = it }
                    sockets += socket
                    check(connections.incrementAndGet() <= 64) { "Owned request fixture connection budget exceeded" }
                    workers.execute { serve(socket) }
                    accepted = null
                } catch (error: Throwable) {
                    accepted?.let { socket -> runCatching { closeOwnedSocket(socket) } }
                    record(error)
                    if (!closing.get()) break
                }
            }
        }

        private fun serve(socket: Socket) {
            var stage: Stage? = null
            var pendingRegistered = false
            try {
                if (closing.get()) return
                val input = socket.getInputStream()
                val headerDeadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5)
                val bytes = ByteArrayOutputStream()
                var tail = 0
                while (true) {
                    val remaining = headerDeadline - System.nanoTime()
                    check(remaining > 0) { "Owned request header deadline exceeded" }
                    socket.soTimeout = TimeUnit.NANOSECONDS.toMillis(remaining).coerceIn(1, 5_000).toInt()
                    val value = input.read()
                    check(value >= 0) { "Owned request ended before bounded HTTP headers" }
                    check(bytes.size() < 8_192) { "Owned request header byte budget exceeded" }
                    bytes.write(value)
                    tail = (tail shl 8) or value
                    if (tail == 0x0d0a0d0a) break
                }
                val lines = bytes.toString(Charsets.US_ASCII.name()).split("\r\n")
                val request = lines.first().split(' ')
                check(request.size == 3 && request[0] == "GET" && request[2] in setOf("HTTP/1.0", "HTTP/1.1"))
                val host = lines.drop(1).filter { it.startsWith("Host:", true) }
                check(host.size == 1 && host.single().substringAfter(':').trim() == "127.0.0.1:${listener.localPort}")
                if (request[1] == "/favicon.ico") {
                    respond(socket, 204, byteArrayOf())
                    return
                }
                val owned = stages.values.singleOrNull { path(it.kind) == request[1] }
                    ?: error("Unowned request path refused")
                stage = owned
                check(owned.arrivals.incrementAndGet() <= 16) { "Owned endpoint retry budget exceeded" }
                owned.pending.incrementAndGet()
                pendingRegistered = true
                check(owned.release.await(15, TimeUnit.SECONDS)) { "Owned held response was not released within its finite deadline" }
                if (closing.get()) return
                if (owned.kind.fails) {
                    // No response header/body has been written. Retries remain bounded
                    // and receive the same deliberate transport refusal, not a 4xx page.
                    closeOwnedSocket(socket)
                    owned.refusals.incrementAndGet()
                } else {
                    val body = "<!doctype html><html><head><title>${title(owned.kind)}</title></head><body>owned</body></html>"
                        .toByteArray(Charsets.UTF_8)
                    respond(socket, 200, body)
                    closeOwnedSocket(socket)
                    owned.responses.incrementAndGet()
                }
            } catch (error: Throwable) { record(error) }
            finally {
                // A parse/budget refusal before pending registration cannot decrement a
                // different request. The retry count is bounded before registration.
                if (pendingRegistered) checkNotNull(stage).pending.decrementAndGet()
                // closeOwnedSocket latches any failure even while closing and
                // removes ownership only after successful native close/readback.
                runCatching { closeOwnedSocket(socket) }
            }
        }

        private fun respond(socket: Socket, code: Int, body: ByteArray) {
            val output = socket.getOutputStream()
            output.write(("HTTP/1.1 $code ${if (code == 200) "OK" else "No Content"}\r\n" +
                "Content-Type: text/html; charset=utf-8\r\nContent-Length: ${body.size}\r\n" +
                "Cache-Control: no-store\r\nConnection: close\r\n\r\n").toByteArray(Charsets.US_ASCII))
            output.write(body)
            output.flush()
        }

        override fun close() {
            if (!closing.compareAndSet(false, true)) return
            runWebViewCleanup(null,
                { stages.values.forEach { it.release.countDown() } },
                { listener.close(); assertTrue(listener.isClosed) },
                { acceptor.join(5_000); assertFalse(acceptor.isAlive, "Owned acceptor must terminate before the final socket snapshot") },
                { runWebViewCleanup(stages = sockets.toList().map { socket ->
                    { closeOwnedSocket(socket) }
                }.toTypedArray()) },
                { workers.shutdownNow(); assertTrue(workers.awaitTermination(5, TimeUnit.SECONDS), "Owned workers must terminate") },
                { assertTrue(sockets.isEmpty()); assertTrue(stages.values.all { it.pending.get() == 0 }) },
                { assertHealthy() },
            )
        }

        companion object {
            fun create(): OwnedRequestServer {
                var listener: ServerSocket? = null
                var workers: ThreadPoolExecutor? = null
                try {
                    val socket = ServerSocket(0, 8, InetAddress.getByName("127.0.0.1")).also { listener = it }
                    val executor = ThreadPoolExecutor(4, 4, 0, TimeUnit.MILLISECONDS, ArrayBlockingQueue<Runnable>(8),
                        { runnable -> Thread(runnable, "nativecmpkit-owned-request-worker").apply { isDaemon = true } },
                        ThreadPoolExecutor.AbortPolicy()).also { workers = it }
                    return OwnedRequestServer(socket, executor).also { it.acceptor.start() }
                } catch (error: Throwable) {
                    runWebViewCleanup(error, { listener?.close() }, {
                        workers?.let { executor -> executor.shutdownNow(); check(executor.awaitTermination(5, TimeUnit.SECONDS)) }
                    })
                    throw error
                }
            }
        }
    }
}
