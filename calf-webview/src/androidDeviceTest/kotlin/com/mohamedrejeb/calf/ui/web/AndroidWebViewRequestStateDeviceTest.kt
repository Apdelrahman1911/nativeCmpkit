// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import android.graphics.Bitmap
import android.os.Build
import android.os.Looper
import android.os.SystemClock
import android.security.NetworkSecurityPolicy
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebView as AndroidWebView
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Test
import org.junit.runner.RunWith
import java.io.ByteArrayOutputStream
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket
import java.util.Locale
import java.util.UUID
import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CountDownLatch
import java.util.concurrent.ThreadPoolExecutor
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlin.test.*

/** Real API35 Chromium callbacks/HTTP only. No intercepted document or synthetic previous error. */
@RunWith(AndroidJUnit4::class)
class AndroidWebViewRequestStateDeviceTest {
    @Test fun twoHeldNativeTransportFailuresResetErrorsAndNativeReloadUsesCurrentOwnerUrl() {
        assertEquals(35, Build.VERSION.SDK_INT, "This finite request is API35 only")
        onMain {
            val policy = NetworkSecurityPolicy.getInstance()
            assertTrue(policy.isCleartextTrafficPermitted("127.0.0.1"))
            assertFalse(policy.isCleartextTrafficPermitted("localhost"))
            assertFalse(policy.isCleartextTrafficPermitted("nativecmpkit.invalid"))
        }
        AndroidRequestHttpServer.create().use { server ->
            val state = WebViewState(WebContent.Url(server.seed.url)).apply { settings.javaScriptEnabled = true }
            val probe = AndroidRequestProbe(state, server.seed)
            val fixture = AndroidLifetimeFixture(state, probe)
            ActivityLease(fixture).use { host ->
                host.awaitCreated()
                val native = onMain {
                    assertSame(state, probe.state)
                    assertSame(fixture.navigator, probe.navigator)
                    assertNotNull(state.webView).also {
                        assertSame(probe, it.webViewClient)
                        assertIs<AccompanistWebChromeClient>(it.webChromeClient)
                    }
                }
                awaitDocument(server, probe, state, native, server.seed)
                onMain { assertEquals(WebContent.Url(server.seed.url), state.content) }
                var previousErrors = emptyList<Pair<Int, String>>()
                for (stage in listOf(server.firstFailure, server.secondFailure)) {
                    onMain {
                        assertSame(native, state.webView)
                        assertEquals(previousErrors, probe.snapshot().errors)
                        if (stage === server.secondFailure) assertTrue(previousErrors.isNotEmpty())
                        probe.arm(stage)
                        // Native navigation deliberately bypasses acceptContent: onPageStarted
                        // must reset the ACTUAL preceding native failure, not a helper reset.
                        native.loadUrl(stage.url)
                    }
                    awaitHeldStart(server, probe, stage)
                    stage.releaseForTest()
                    waitFor("Actual main-frame native error and actual finish after owned zero-byte refusal", server, probe) {
                        onMain { probe.failedAndFinished(stage) } && stage.pending.get() == 0 && stage.refused.get() > 0
                    }
                    server.assertSettled(stage)
                    previousErrors = onMain {
                        probe.assertTerminal(stage, native, failed = true)
                        probe.snapshot().errors.also { assertTrue(it.isNotEmpty()) }
                    }
                }
                onMain {
                    assertEquals(previousErrors, probe.snapshot().errors)
                    assertTrue(previousErrors.isNotEmpty())
                    probe.arm(server.recovery)
                    native.loadUrl(server.recovery.url)
                }
                awaitHeldStart(server, probe, server.recovery)
                server.recovery.releaseForTest()
                awaitDocument(server, probe, state, native, server.recovery)

                // A no-store second response at the SAME actual URL has a different real DOM.
                // Declarative content remains the seed, so a guessed content-based Reload fails.
                waitFor("All acquired pre-Reload sockets drain before the exact route exchange", server, probe) { server.isIdle() }
                val reload = server.installReload()
                onMain {
                    assertSame(native, state.webView)
                    assertEquals(server.recovery.url, native.url)
                    assertEquals(WebContent.Url(server.seed.url), state.content)
                    assertNotEquals(server.seed.url, native.url)
                    probe.arm(reload)
                    fixture.navigator.reload()
                }
                awaitHeldStart(server, probe, reload)
                reload.releaseForTest()
                awaitDocument(server, probe, state, native, reload)
                assertEquals(1, fixture.created.get(), "Every stage uses the same real native owner")
                assertEquals(0, fixture.disposed.get())
                waitFor("All exact acquired response leases drain before owner disposal", server, probe) { server.isIdle() }
                server.assertAllSettled()
                host.unmount()
                host.assertResumed() // Activity finish cannot supply the asserted native release.
                onMain {
                    assertNull(state.webView)
                    assertFalse(fixture.observedAttachment.get())
                    probe.clearObservations()
                }
            }
            assertEquals(1, fixture.disposed.get())
            assertFalse(fixture.scope.coroutineContext[kotlinx.coroutines.Job]!!.isActive)
            server.assertAllSettled() // Native-owner disposal precedes server cleanup.
        }
    }

    private fun awaitHeldStart(server: AndroidRequestHttpServer, probe: AndroidRequestProbe, stage: AndroidRequestStage) {
        waitFor("A real onPageStarted and still-held exact owned HTTP request", server, probe) {
            onMain { probe.hasStart(stage) } && stage.attempts.get() > 0 && stage.pending.get() > 0
        }
        assertFalse(stage.testReleased.get(), "A pre-disconnected endpoint cannot prove the loading interval")
        assertEquals(0, stage.responseBytes.get())
        assertEquals(0, stage.refused.get())
        assertEquals(0, stage.completed.get())
        onMain {
            probe.assertStarts(stage)
            val snapshot = probe.snapshot()
            assertEquals(stage.url, snapshot.requested)
            assertNull(snapshot.loaded)
            assertNull(snapshot.title)
            assertTrue(snapshot.errors.isEmpty())
            assertIs<LoadingState.Loading>(snapshot.loading)
        }
    }

    private fun awaitDocument(server: AndroidRequestHttpServer, probe: AndroidRequestProbe, state: WebViewState,
                              native: AndroidWebView, stage: AndroidRequestStage) {
        waitFor("Actual native finish/title/location and common completion", server, probe) { onMain {
            probe.finished(stage) && state.webView === native && native.title == stage.title && native.url == stage.url &&
                state.pageTitle == stage.title && state.loadingState == LoadingState.Finished
        } && stage.pending.get() == 0 && stage.completed.get() > 0 }
        val answer = AtomicReference<JavascriptResult?>()
        val calls = AtomicInteger()
        val callbackFailure = AtomicReference<Throwable?>()
        val expected = "document.title === '${stage.title}' && location.href === '${stage.url}' && " +
            "document.body.getAttribute('data-nativecmpkit') === '${server.nonce}' && " +
            "document.body.getAttribute('data-stage') === '${stage.name}'"
        state.evaluateJavascriptResult(expected) { result ->
            // Record diagnostics without throwing through an asynchronous native callback.
            runCatching {
                check(Looper.myLooper() == Looper.getMainLooper())
                check(state.webView === native && probe.isCurrent(stage))
                check(calls.incrementAndGet() == 1)
                answer.set(result)
            }.exceptionOrNull()?.let { callbackFailure.compareAndSet(null, it) }
        }
        waitFor("The same current native owner's exact authored Chromium DOM", server, probe) {
            callbackFailure.get()?.let { throw AssertionError("Native DOM observation failed", it) }
            answer.get() != null
        }
        assertEquals(JavascriptResult.Value("true"), answer.get())
        assertEquals(1, calls.get())
        server.assertSettled(stage)
        onMain { probe.assertTerminal(stage, native, failed = false) }
    }

    private fun waitFor(description: String, server: AndroidRequestHttpServer, probe: AndroidRequestProbe,
                        condition: () -> Boolean) {
        val end = SystemClock.elapsedRealtime() + 10_000
        do {
            server.checkHealthy(); probe.checkHealthy()
            if (condition()) return
            Thread.sleep(25)
        } while (SystemClock.elapsedRealtime() < end)
        server.checkHealthy(); probe.checkHealthy()
        fail(description)
    }
}

private data class AndroidRequestSnapshot(val requested: String?, val loaded: String?, val title: String?,
                                          val errors: List<Pair<Int, String>>, val loading: LoadingState)
private data class AndroidRequestError(val generation: Int, val url: String?, val mainFrame: Boolean?,
                                      val code: Int?, val description: String?)
private class AndroidRequestObservation(val stage: AndroidRequestStage) {
    var generation = 0
    val starts = mutableListOf<AndroidRequestSnapshot>()
    val finishes = mutableListOf<Pair<Int, AndroidRequestSnapshot>>()
    val errors = mutableListOf<AndroidRequestError>()
}

/** Normal library client subclassing; every native callback is forwarded BEFORE observation. */
private class AndroidRequestProbe(private val owner: WebViewState, seed: AndroidRequestStage) : AccompanistWebViewClient() {
    private var active: AndroidRequestObservation? = AndroidRequestObservation(seed)
    private var serial = 0
    private val failure = AtomicReference<Throwable?>()
    fun snapshot() = AndroidRequestSnapshot(owner.requestedUrl, owner.lastLoadedUrl, owner.pageTitle,
        owner.errorsForCurrentRequest.map { it.code to it.description }, owner.loadingState)
    fun arm(stage: AndroidRequestStage) {
        check(Looper.myLooper() == Looper.getMainLooper())
        check(owner.webView != null)
        active = AndroidRequestObservation(stage)
    }
    fun isCurrent(stage: AndroidRequestStage) = active?.stage === stage
    fun hasStart(stage: AndroidRequestStage) = isCurrent(stage) && active!!.generation > 0
    fun finished(stage: AndroidRequestStage) = hasStart(stage) && active!!.finishes.any { it.first == active!!.generation }
    fun failedAndFinished(stage: AndroidRequestStage) = finished(stage) && active!!.errors.any {
        it.generation == active!!.generation && it.url == stage.url && it.mainFrame == true && it.code != null
    } && snapshot().errors.isNotEmpty()
    fun assertStarts(stage: AndroidRequestStage) {
        assertTrue(hasStart(stage))
        active!!.starts.forEach {
            assertEquals(stage.url, it.requested); assertNull(it.loaded); assertNull(it.title)
            assertTrue(it.errors.isEmpty()); assertEquals(LoadingState.Loading(0f), it.loading)
        }
    }
    fun assertTerminal(stage: AndroidRequestStage, native: AndroidWebView, failed: Boolean) {
        assertSame(native, owner.webView)
        assertStarts(stage); assertTrue(finished(stage))
        val observed = active!!
        val nativeErrors = observed.errors.filter { it.generation == observed.generation && it.code != null }
            .map { it.code!! to (it.description ?: "Unknown error") }
        // ALL resource callbacks participate, exactly as the documented library error list does.
        // Only the transport-failure witness additionally requires the matching main-frame error.
        assertEquals(nativeErrors, snapshot().errors)
        assertEquals(stage.url, snapshot().requested); assertEquals(stage.url, snapshot().loaded)
        assertEquals(LoadingState.Finished, snapshot().loading)
        if (failed) assertTrue(failedAndFinished(stage)) else {
            assertTrue(nativeErrors.isEmpty()); assertEquals(stage.title, snapshot().title)
        }
    }
    override fun onPageStarted(view: AndroidWebView, url: String?, favicon: Bitmap?) {
        super.onPageStarted(view, url, favicon)
        observe(view) {
            val observed = checkNotNull(active)
            check(url == observed.stage.url && ++serial <= 32)
            observed.generation = serial
            observed.starts += snapshot()
        }
    }
    override fun onReceivedError(view: AndroidWebView, request: WebResourceRequest?, error: WebResourceError?) {
        super.onReceivedError(view, request, error)
        observe(view) {
            val observed = checkNotNull(active)
            check(observed.generation > 0 && observed.errors.size < 64)
            val url = request?.url?.toString()
            check(request?.isForMainFrame != true || url == observed.stage.url)
            observed.errors += AndroidRequestError(observed.generation, url, request?.isForMainFrame,
                error?.errorCode, error?.description?.toString())
        }
    }
    override fun onPageFinished(view: AndroidWebView, url: String?) {
        super.onPageFinished(view, url)
        observe(view) {
            val observed = checkNotNull(active)
            // Late finishes from the replaced request are not witnesses for the new one.
            if (url == observed.stage.url) {
                check(observed.generation > 0 && observed.finishes.size < 32)
                observed.finishes += observed.generation to snapshot()
            }
        }
    }
    private fun observe(view: AndroidWebView, body: () -> Unit) {
        if (owner.webView !== view) return // Same current-owner gate as the forwarded production callbacks.
        runCatching { check(Looper.myLooper() == Looper.getMainLooper()); body() }
            .exceptionOrNull()?.let { failure.compareAndSet(null, it) }
    }
    fun checkHealthy() { failure.get()?.let { throw AssertionError("Native callback observation failed", it) } }
    fun clearObservations() { check(owner.webView == null); active = null; checkHealthy() }
}

private class AndroidRequestStage(val name: String, val path: String, val url: String, val title: String?, held: Boolean = true) {
    val gate = CountDownLatch(if (held) 1 else 0)
    val testReleased = AtomicBoolean(!held)
    val attempts = AtomicInteger()
    val pending = AtomicInteger()
    val refused = AtomicInteger()
    val completed = AtomicInteger()
    val responseBytes = AtomicInteger()
    fun releaseForTest() { check(testReleased.compareAndSet(false, true)); gate.countDown() }
}

/** Finite raw loopback HTTP. A refusal writes ZERO bytes; no HTTP/DNS/TLS/offline error is invented. */
private class AndroidRequestHttpServer private constructor(private val listener: ServerSocket,
                                                           private val workers: ThreadPoolExecutor) : AutoCloseable {
    val nonce = UUID.randomUUID().toString().replace("-", "")
    private val origin = "http://127.0.0.1:${listener.localPort}"
    private fun stage(name: String, title: String?, held: Boolean = true, path: String = "/$nonce/$name") =
        AndroidRequestStage(name, path, origin + path, title, held)
    val seed = stage("seed", "native-request-seed", held = false)
    val firstFailure = stage("fail-a", null)
    val secondFailure = stage("fail-b", null)
    val recovery = stage("recover", "native-request-recovered")
    private val stages = CopyOnWriteArrayList(listOf(seed, firstFailure, secondFailure, recovery))
    private val routes = stages.associateBy { it.path }.toMutableMap()
    private val sockets = ConcurrentHashMap.newKeySet<Socket>()
    private val admitted = AtomicInteger()
    private val favicons = AtomicInteger()
    private val closing = AtomicBoolean()
    private val failure = AtomicReference<Throwable?>()
    private val acceptor = Thread({ accept() }, "nativecmpkit-owned-request-acceptor").apply { isDaemon = true }

    fun installReload(): AndroidRequestStage = synchronized(routes) {
        checkHealthy(); assertAllSettled()
        check(routes[recovery.path] === recovery)
        stage("reload", "native-request-reloaded", path = recovery.path).also {
            routes[recovery.path] = it; stages += it
        }
    }
    private fun accept() {
        while (!closing.get()) {
            var acquired: Socket? = null
            try {
                val socket = listener.accept().also { acquired = it; sockets += it }
                check(socket.inetAddress.isLoopbackAddress && admitted.incrementAndGet() <= 64)
                workers.execute { serve(socket) }
                acquired = null // The exact acquired worker now owns close/removal.
            } catch (error: Throwable) {
                acquired?.let { socket ->
                    runCatching { socket.close(); sockets -= socket }.exceptionOrNull()?.let { record(it) }
                }
                if (!closing.get()) record(error)
                return
            }
        }
    }
    private fun serve(socket: Socket) {
        var acquiredStage: AndroidRequestStage? = null
        try {
            val path = readRequest(socket)
            if (path == "/favicon.ico") {
                check(favicons.incrementAndGet() <= 8)
                writeResponse(socket, byteArrayOf(), "text/plain", null, code = "204 No Content")
                return
            }
            val owned = synchronized(routes) {
                val candidate = checkNotNull(routes[path]) { "Unowned request path" }
                check(candidate.attempts.incrementAndGet() <= 16)
                candidate.pending.incrementAndGet(); candidate
            }
            acquiredStage = owned // Every decrement belongs to THIS acquired lease, even after Reload swaps the route.
            check(owned.gate.await(15, TimeUnit.SECONDS)) { "Owned held-stage deadline expired" }
            if (closing.get()) return // Fixture cleanup is NEVER a test refusal/completion.
            check(owned.testReleased.get())
            if (owned.title == null) {
                socket.close() // No status/header/body byte has been written on this branch.
                owned.refused.incrementAndGet()
            } else {
                val body = ("<!doctype html><html><head><title>${owned.title}</title>" +
                    "<link rel=\"icon\" href=\"data:,\"></head><body data-nativecmpkit=\"$nonce\" " +
                    "data-stage=\"${owned.name}\">${owned.title}</body></html>").toByteArray(Charsets.UTF_8)
                writeResponse(socket, body, "text/html; charset=utf-8", owned)
                owned.completed.incrementAndGet()
            }
        } catch (error: Throwable) {
            if (!closing.get()) record(error)
        } finally {
            try { socket.close(); sockets -= socket } catch (error: Throwable) { record(error) }
            acquiredStage?.let { owned ->
                runCatching { check(owned.pending.decrementAndGet() >= 0) }.exceptionOrNull()?.let { record(it) }
            }
        }
    }
    private fun readRequest(socket: Socket): String {
        val end = SystemClock.elapsedRealtime() + 5_000
        val bytes = ByteArrayOutputStream()
        val input = socket.getInputStream()
        var marker = 0
        while (true) {
            val remaining = end - SystemClock.elapsedRealtime()
            check(remaining > 0 && bytes.size() < 8_192) { "Bounded owned HTTP header refused" }
            socket.soTimeout = remaining.toInt().coerceAtLeast(1)
            val next = input.read(); check(next >= 0) { "Incomplete owned HTTP header" }
            check(next in 32..126 || next == 13 || next == 10)
            bytes.write(next)
            marker = (marker shl 8) or next
            if (marker == 0x0D0A0D0A) break
        }
        val lines = bytes.toString("US-ASCII").removeSuffix("\r\n\r\n").split("\r\n")
        val request = lines.first().split(' ')
        check(request.size == 3 && request[0] == "GET" && request[2] == "HTTP/1.1")
        val headers = mutableMapOf<String, String>()
        for (line in lines.drop(1)) {
            val colon = line.indexOf(':'); check(colon > 0)
            val name = line.substring(0, colon).lowercase(Locale.US)
            check(headers.put(name, line.substring(colon + 1).trim()) == null) { "Duplicate HTTP header" }
        }
        check(headers["host"] == "127.0.0.1:${listener.localPort}")
        check(headers["content-length"] == null || headers["content-length"] == "0")
        check(headers["transfer-encoding"] == null)
        return request[1] // No query stripping, authority fallback or unknown-path success.
    }
    private fun writeResponse(socket: Socket, body: ByteArray, type: String, stage: AndroidRequestStage?, code: String = "200 OK") {
        val header = ("HTTP/1.1 $code\r\nContent-Type: $type\r\nContent-Length: ${body.size}\r\n" +
            "Cache-Control: no-store\r\nConnection: close\r\n\r\n").toByteArray(Charsets.US_ASCII)
        val output = socket.getOutputStream()
        output.write(header); stage?.responseBytes?.addAndGet(header.size)
        output.write(body); stage?.responseBytes?.addAndGet(body.size)
        output.flush(); socket.close() // Completion is counted only after full write/flush/owned close.
    }
    private fun record(error: Throwable) {
        if (!failure.compareAndSet(null, error)) failure.get()?.takeIf { it !== error }?.addSuppressed(error)
    }
    fun checkHealthy() { failure.get()?.let { throw AssertionError("Owned HTTP fixture failed", it) } }
    fun assertSettled(stage: AndroidRequestStage) {
        checkHealthy(); assertEquals(0, stage.pending.get()); assertTrue(stage.attempts.get() in 1..16)
        if (stage.title == null) {
            assertEquals(stage.attempts.get(), stage.refused.get()); assertEquals(0, stage.completed.get())
            assertEquals(0, stage.responseBytes.get())
        } else {
            assertEquals(stage.attempts.get(), stage.completed.get()); assertEquals(0, stage.refused.get())
            assertTrue(stage.responseBytes.get() > 0)
        }
    }
    fun isIdle() = sockets.isEmpty() && stages.all { it.pending.get() == 0 }
    fun assertAllSettled() { checkHealthy(); stages.forEach { assertSettled(it) }; assertTrue(isIdle()) }
    override fun close() {
        if (!closing.compareAndSet(false, true)) return
        stages.forEach { it.gate.countDown() } // Cleanup release does NOT mark testReleased.
        runWebViewCleanup(stages = arrayOf(
            { listener.close() },
            { acceptor.join(5_000); check(!acceptor.isAlive) },
            { runWebViewCleanup(stages = sockets.toList().map { socket ->
                { socket.close(); sockets -= socket; Unit }
            }.toTypedArray()) },
            { workers.shutdown() }, // Closed sockets/released gates also drain admitted queued workers.
            { check(workers.awaitTermination(5, TimeUnit.SECONDS)) },
            { if (!workers.isTerminated) workers.shutdownNow(); check(workers.awaitTermination(5, TimeUnit.SECONDS)) },
            { check(sockets.isEmpty()); check(stages.all { it.pending.get() == 0 }) },
            { checkHealthy() },
        ))
    }
    companion object {
        fun create(): AndroidRequestHttpServer {
            val listener = ServerSocket(0, 8, InetAddress.getByName("127.0.0.1"))
            var workers: ThreadPoolExecutor? = null
            var acquired: AndroidRequestHttpServer? = null
            try {
                val acquiredWorkers = ThreadPoolExecutor(4, 4, 0L, TimeUnit.MILLISECONDS, ArrayBlockingQueue<Runnable>(8),
                    { task -> Thread(task, "nativecmpkit-owned-request-worker").apply { isDaemon = true } },
                    ThreadPoolExecutor.AbortPolicy())
                workers = acquiredWorkers
                return AndroidRequestHttpServer(listener, acquiredWorkers).also { acquired = it; it.acceptor.start() }
            } catch (error: Throwable) {
                val owned = acquired
                if (owned != null) runWebViewCleanup(error, { owned.close() }) else runWebViewCleanup(error,
                    { listener.close() }, { workers?.shutdownNow() },
                    { workers?.let { check(it.awaitTermination(5, TimeUnit.SECONDS)) } })
                throw error
            }
        }
    }
}
