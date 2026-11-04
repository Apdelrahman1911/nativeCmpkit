// SPDX-License-Identifier: Apache-2.0
package nativecmpkit.consumer

import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.awt.ComposePanel
import com.mohamedrejeb.calf.ui.web.LoadingState
import com.mohamedrejeb.calf.ui.web.WebContent
import com.mohamedrejeb.calf.ui.web.WebView
import com.mohamedrejeb.calf.ui.web.WebViewNavigator
import com.mohamedrejeb.calf.ui.web.WebViewState
import com.mohamedrejeb.calf.ui.web.isDesktopWebViewAvailable
import javafx.application.Platform
import javafx.beans.property.SimpleStringProperty
import javafx.beans.value.ChangeListener
import javafx.concurrent.Worker
import javafx.embed.swing.JFXPanel
import javafx.scene.Scene
import javafx.scene.control.Control
import javafx.scene.media.Media
import javafx.scene.web.WebEngine
import javafx.scene.web.WebView as FxWebView
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import java.awt.Component
import java.awt.Container
import java.awt.GraphicsEnvironment
import java.io.ByteArrayOutputStream
import java.lang.management.ManagementFactory
import java.net.InetAddress
import java.net.JarURLConnection
import java.net.ServerSocket
import java.net.Socket
import java.net.SocketTimeoutException
import java.nio.file.Files
import java.nio.file.Path
import java.security.MessageDigest
import java.util.UUID
import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.FutureTask
import java.util.concurrent.ThreadPoolExecutor
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import javax.swing.JFrame
import javax.swing.SwingUtilities
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

/**
 * Genuinely NEW Maven activation/loaded-origin test, not a replay of accepted
 * library Stop tests. Only public Compose/navigation APIs operate the native
 * owner. Reading the owning class resource is provenance, never loader reflection
 * or transport manipulation. Real peer EOF must precede fixture cleanup.
 */
class OrdinaryCuredWebStopConsumerTest {
    @OptIn(ExperimentalComposeUiApi::class)
    @Test fun normalMavenActivationBindsCuredPublicStopTransportAndOwnedLifetime() {
        assertFalse(GraphicsEnvironment.isHeadless(), "Actual graphical session required; no assumption skip")
        assertNull(System.getProperty("com.sun.webkit.useHTTP2Loader"), "No private loader route override")
        assertTrue(ManagementFactory.getRuntimeMXBean().inputArguments.none {
            it.startsWith("--patch-module") || it.startsWith("-javaagent")
        }, "No runtime module transform or injected activation")
        assertLoadedJar(WebViewState::class.java, "webview")
        val curedJar = assertLoadedJar(WebEngine::class.java, "javafx")
        assertLoadedCompanionJars() // Actual public-class origins, not graph labels.
        assertTrue(isDesktopWebViewAvailable())
        val loaderResource = assertNotNull(WebEngine::class.java.getResource("/com/sun/webkit/network/HTTP2Loader.class"))
        assertEquals("jar", loaderResource.protocol, "Loose/shadow owning class is forbidden")
        val loaderConnection = loaderResource.openConnection() as JarURLConnection
        loaderConnection.useCaches = false
        assertEquals(curedJar, Path.of(loaderConnection.jarFileURL.toURI()))
        val loaderBytes = loaderConnection.getInputStream().use { it.readNBytes(256 * 1024 + 1) }
        assertTrue(loaderBytes.size <= 256 * 1024, "Owning resource must be bounded")
        assertEquals(assertNotNull(System.getProperty("nativecmpkit.expected.javafx.loader.sha256")), digest(loaderBytes))

        val state = WebViewState(WebContent.NavigatorOnly).apply { settings.javaScriptEnabled = true }
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
        val navigator = WebViewNavigator(scope)
        val created = AtomicInteger()
        val disposed = AtomicInteger()
        val cancellations = AtomicInteger()
        val callbackError = AtomicReference<Throwable>()
        val panelRef = AtomicReference<ComposePanel>()
        val frameRef = AtomicReference<JFrame>()
        var observed: FxWebView? = null
        var observerAttached = false
        var primary: Throwable? = null
        var serverRef: HeldServer? = null
        val observer = ChangeListener<Worker.State> { _, _, value ->
            if (value == Worker.State.CANCELLED) cancellations.incrementAndGet()
        }
        try {
            val server = HeldServer.create().also { serverRef = it }
            onEdt {
                val panel = ComposePanel().also { panelRef.set(it) }
                val frame = JFrame("NativeCmpKit ordinary private cured WebView").also { frameRef.set(it) }
                frame.defaultCloseOperation = JFrame.DISPOSE_ON_CLOSE
                frame.contentPane.add(panel)
                frame.setSize(480, 320)
                panel.setContent {
                    WebView(state, navigator = navigator,
                        onCreated = {
                            runCatching { assertTrue(Platform.isFxApplicationThread()); assertEquals(1, created.incrementAndGet()) }
                                .onFailure { callbackError.compareAndSet(null, it) }
                        },
                        onDispose = {
                            runCatching { assertTrue(Platform.isFxApplicationThread()); assertEquals(1, disposed.incrementAndGet()) }
                                .onFailure { callbackError.compareAndSet(null, it) }
                        })
                }
                frame.isVisible = true
            }
            await("one real attached native owner", 30) {
                callbackError.get()?.let { throw it }
                created.get() == 1 && onFx { state.webView != null } &&
                    onEdt { nativePanels(assertNotNull(frameRef.get())).singleOrNull()?.isShowing == true }
            }
            val native = onFx { assertNotNull(state.webView) }.also { observed = it }
            val embedding = onEdt { nativePanels(assertNotNull(frameRef.get())).single() }
            onFx {
                assertSame(native.scene, assertNotNull(embedding.scene))
                native.engine.loadWorker.stateProperty().addListener(observer)
                observerAttached = true
            }
            fun awaitNative(description: String, ready: () -> Boolean) = await(description) {
                server.assertHealthy()
                callbackError.get()?.let { throw it }
                onEdt { assertTrue(assertNotNull(frameRef.get()).isShowing) }
                onFx { assertSame(native, state.webView); ready() }
            }
            fun document(path: String) = awaitNative("native terminal $path document on the same owner") {
                native.engine.loadWorker.state == Worker.State.SUCCEEDED &&
                    native.engine.location == server.url(path) && state.lastLoadedUrl == server.url(path) &&
                    state.pageTitle == server.title(path) && native.engine.executeScript("document.title") == server.title(path) &&
                    state.loadingState == LoadingState.Finished && state.errorsForCurrentRequest.isEmpty()
            }
            navigator.loadUrl(server.url("seed"))
            document("seed")
            navigator.loadUrl(server.url("held"))
            awaitNative("exactly one real held request before any response bytes") {
                server.arrivals.get() == 1 && server.pending.get() == 1 &&
                    native.engine.loadWorker.state == Worker.State.RUNNING && native.engine.location == server.url("held")
            }
            onFx {
                assertEquals(server.url("held"), state.requestedUrl)
                assertTrue(state.loadingState is LoadingState.Loading)
                assertNull(state.lastLoadedUrl); assertNull(state.pageTitle)
                assertTrue(state.errorsForCurrentRequest.isEmpty())
            }
            assertEquals(0, server.responses.get()); assertEquals(0, server.peerEofs.get()); assertEquals(0, cancellations.get())
            assertFalse(server.closing.get(), "Owned teardown cannot manufacture a public Stop witness")

            navigator.stopLoading() // Public library owner handles Stop; no engine/loader cancel.
            // Preserve the original ten-second/six-predicate transport semantics.
            awaitNative("public Stop and real pre-response peer EOF before cleanup") {
                native.engine.loadWorker.state == Worker.State.CANCELLED && !native.engine.loadWorker.isRunning &&
                    state.loadingState == LoadingState.Finished && cancellations.get() == 1 &&
                    server.peerEofs.get() == 1 && server.pending.get() == 0
            }
            assertFalse(server.closing.get())
            assertEquals(1, server.arrivals.get()); assertEquals(0, server.responses.get())
            onFx {
                assertEquals(server.url("held"), state.requestedUrl)
                assertNull(state.lastLoadedUrl); assertNull(state.pageTitle)
                assertTrue(state.errorsForCurrentRequest.isEmpty())
            }
            assertEquals(1, created.get()); assertEquals(0, disposed.get())
            navigator.loadUrl(server.url("recovery"))
            document("recovery")
            assertEquals(1, cancellations.get()); assertEquals(1, server.arrivals.get())
            assertEquals(1, created.get()); assertEquals(0, disposed.get())

            onEdt { assertNotNull(panelRef.get()).setContent { } }
            await("public exactly-once disposal and native owner detachment") {
                callbackError.get()?.let { throw it }
                disposed.get() == 1 && onFx { state.webView == null && embedding.scene == null }
            }
            onEdt {
                val panel = assertNotNull(panelRef.get())
                panel.dispose(); panelRef.compareAndSet(panel, null)
                val frame = assertNotNull(frameRef.get())
                frame.dispose(); assertFalse(frame.isDisplayable); frameRef.compareAndSet(frame, null)
            }
            server.assertHealthy()
            assertFalse(server.closing.get())
            assertLoadedCompanionJars() // Hold each admitted official JAR through disposal.
        } catch (error: Throwable) { primary = error; throw error }
        finally {
            cleanup(primary,
                { observed?.let { view -> onFx { if (observerAttached) view.engine.loadWorker.stateProperty().removeListener(observer) } } },
                { onEdt { panelRef.get()?.dispose() } },
                { onEdt { frameRef.get()?.dispose(); frameRef.get()?.let { assertFalse(it.isDisplayable) } } },
                { scope.cancel() },
                { serverRef?.close() },
                { await("owned composable detached after final cleanup") { onFx { state.webView == null } } },
                { if (created.get() == 1) assertEquals(1, disposed.get()) },
                { callbackError.get()?.let { throw it } },
            )
        }
    }

    private fun assertLoadedCompanionJars() {
        assertLoadedCompanionJar(SimpleStringProperty::class.java, "base")
        assertLoadedCompanionJar(Scene::class.java, "graphics")
        assertLoadedCompanionJar(Control::class.java, "controls")
        assertLoadedCompanionJar(Media::class.java, "media")
        assertLoadedCompanionJar(JFXPanel::class.java, "swing")
    }
    private fun assertLoadedCompanionJar(type: Class<*>, companion: String) {
        val suffix = "javafx.$companion"
        val file = assertLoadedJar(type, suffix)
        val bytes = assertNotNull(System.getProperty("nativecmpkit.expected.$suffix.bytes")).toLong()
        assertTrue(bytes > 0)
        assertEquals(bytes, Files.size(file), "Loaded official companion length must equal its trusted pin")
        val admitted = Path.of(assertNotNull(System.getProperty("nativecmpkit.expected.$suffix.path"))).toRealPath()
        assertEquals(admitted, file.toRealPath(), "Each public class must come from the exact admitted classified artifact")
    }
    private fun assertLoadedJar(type: Class<*>, suffix: String): Path {
        val url = assertNotNull(type.protectionDomain.codeSource?.location)
        assertEquals("file", url.protocol)
        val file = Path.of(url.toURI())
        assertTrue(Files.isRegularFile(file) && !Files.isSymbolicLink(file), "Only real normally resolved packaged JARs")
        assertEquals(assertNotNull(System.getProperty("nativecmpkit.expected.$suffix.name")), file.fileName.toString())
        val sha = MessageDigest.getInstance("SHA-256")
        Files.newInputStream(file).use { input ->
            val buffer = ByteArray(64 * 1024)
            while (true) { val count = input.read(buffer); if (count < 0) break; sha.update(buffer, 0, count) }
        }
        assertEquals(assertNotNull(System.getProperty("nativecmpkit.expected.$suffix.sha256")), hex(sha.digest()))
        return file
    }
    private fun digest(bytes: ByteArray): String = hex(MessageDigest.getInstance("SHA-256").digest(bytes))
    private fun hex(bytes: ByteArray): String = bytes.joinToString("") { "%02x".format(it) }
    private val operationDeadline = ThreadLocal<Long?>()
    private fun await(description: String, seconds: Long = 10, ready: () -> Boolean) {
        val previous = operationDeadline.get()
        val deadline = minOf(previous ?: Long.MAX_VALUE, System.nanoTime() + TimeUnit.SECONDS.toNanos(seconds))
        operationDeadline.set(deadline)
        try {
            while (true) {
                assertTrue(System.nanoTime() < deadline, "$description timed out")
                val accepted = ready()
                assertTrue(System.nanoTime() <= deadline, "$description exceeded its absolute deadline")
                if (accepted) return
                Thread.sleep(25)
            }
        } finally { if (previous == null) operationDeadline.remove() else operationDeadline.set(previous) }
    }
    private fun nativePanels(component: Component): List<JFXPanel> = when (component) {
        is JFXPanel -> listOf(component)
        is Container -> component.components.flatMap { nativePanels(it) }
        else -> emptyList()
    }
    private fun <T> scheduled(isCurrent: Boolean, submit: (() -> Unit) -> Unit, action: () -> T): T {
        if (isCurrent) return action()
        val remaining = (operationDeadline.get() ?: (System.nanoTime() + TimeUnit.SECONDS.toNanos(10))) - System.nanoTime()
        assertTrue(remaining > 0, "Owned UI scheduling deadline exhausted")
        val task = FutureTask(action)
        submit { task.run() }
        try { return task.get(remaining, TimeUnit.NANOSECONDS) }
        catch (error: Throwable) { task.cancel(false); throw error }
    }
    private fun <T> onEdt(action: () -> T): T = scheduled(SwingUtilities.isEventDispatchThread(), { SwingUtilities.invokeLater(it) }, action)
    private fun <T> onFx(action: () -> T): T = scheduled(Platform.isFxApplicationThread(), { Platform.runLater(it) }, action)
    private fun cleanup(primary: Throwable?, vararg actions: () -> Unit) {
        var failure = primary
        actions.forEach { action -> try { action() } catch (error: Throwable) {
            if (failure == null) failure = error else if (failure !== error) failure!!.addSuppressed(error)
        } }
        if (primary == null) failure?.let { throw it }
    }

    private class HeldServer private constructor(private val listener: ServerSocket, private val workers: ThreadPoolExecutor) : AutoCloseable {
        private val sockets = ConcurrentHashMap.newKeySet<Socket>()
        private val heldSocket = AtomicReference<Socket>()
        val arrivals = AtomicInteger()
        val pending = AtomicInteger()
        val responses = AtomicInteger()
        val peerEofs = AtomicInteger()
        val closing = AtomicBoolean()
        private val failure = AtomicReference<Throwable>()
        private val accepted = AtomicInteger()
        private val nonce = UUID.randomUUID().toString().replace("-", "")
        private val acceptor = Thread({ accept() }, "nativecmpkit-NEW-ordinary-held-acceptor").apply { isDaemon = true }
        fun url(path: String) = "http://127.0.0.1:${listener.localPort}/ordinary-$nonce/$path"
        fun title(path: String) = "NativeCmpKit ordinary-$nonce-$path"
        fun assertHealthy() { failure.get()?.let { throw AssertionError("Owned ordinary-Maven HTTP fixture failed", it) } }
        private fun record(error: Throwable) { if (!closing.get()) failure.compareAndSet(null, error) }
        private fun accept() {
            while (!closing.get()) {
                var owned: Socket? = null
                try {
                    val socket = listener.accept().also { owned = it; sockets += it }
                    check(accepted.incrementAndGet() <= 32) { "Owned connection budget exceeded" }
                    workers.execute { serve(socket) }; owned = null
                } catch (error: Throwable) {
                    owned?.let { socket -> runCatching { socket.close(); sockets -= socket }.onFailure { failure.compareAndSet(null, it) } }
                    record(error); break
                }
            }
        }
        private fun serve(socket: Socket) {
            var held = false
            try {
                if (closing.get()) return
                val input = socket.getInputStream()
                val header = ByteArrayOutputStream()
                val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5)
                var tail = 0
                while (true) {
                    val remaining = deadline - System.nanoTime(); check(remaining > 0 && header.size() < 8192)
                    socket.soTimeout = TimeUnit.NANOSECONDS.toMillis(remaining).coerceIn(1, 5000).toInt()
                    val value = input.read(); check(value >= 0); header.write(value); tail = (tail shl 8) or value
                    if (tail == 0x0d0a0d0a) break
                }
                val lines = header.toString(Charsets.US_ASCII.name()).split("\r\n")
                val request = lines.first().split(' ')
                check(request.size == 3 && request[0] == "GET" && request[2] in setOf("HTTP/1.0", "HTTP/1.1"))
                val hosts = lines.filter { it.startsWith("Host:", true) }
                check(hosts.size == 1 && hosts.single().substringAfter(':').trim() == "127.0.0.1:${listener.localPort}")
                if (request[1] == "/favicon.ico") { respond(socket, byteArrayOf()); return }
                val endpoint = listOf("seed", "held", "recovery").singleOrNull { request[1] == "/ordinary-$nonce/$it" }
                    ?: error("Unowned HTTP path refused")
                if (endpoint == "held") {
                    check(heldSocket.compareAndSet(null, socket))
                    check(arrivals.incrementAndGet() == 1); pending.incrementAndGet(); held = true
                    socket.soTimeout = 250
                    val heldDeadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(30)
                    while (!closing.get()) {
                        check(System.nanoTime() < heldDeadline) { "Owned held request deadline exceeded" }
                        try {
                            val value = input.read()
                            if (value == -1) { peerEofs.incrementAndGet(); return }
                            error("Unexpected bytes after held request headers")
                        } catch (_: SocketTimeoutException) { }
                    }
                    // A cleanup termination never increments peerEofs/responses.
                } else {
                    val body = "<html><head><meta charset=\"utf-8\"><title>${title(endpoint)}</title></head><body>ordinary adoption</body></html>".toByteArray()
                    respond(socket, body)
                }
            } catch (error: Throwable) { record(error) }
            finally {
                if (held) pending.decrementAndGet()
                try { socket.close(); check(socket.isClosed); sockets -= socket }
                catch (error: Throwable) { failure.compareAndSet(null, error) }
            }
        }
        private fun respond(socket: Socket, body: ByteArray) {
            // Any attempted HTTP response to the identified held handle is
            // observable even if a later fixture change accidentally sends one.
            if (socket === heldSocket.get()) responses.incrementAndGet()
            val header = "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: ${body.size}\r\nConnection: close\r\n\r\n".toByteArray(Charsets.US_ASCII)
            socket.getOutputStream().apply { write(header); write(body); flush() }
        }
        override fun close() {
            if (!closing.compareAndSet(false, true)) return
            var primary: Throwable? = null
            fun attempt(action: () -> Unit) { try { action() } catch (error: Throwable) {
                if (primary == null) primary = error else if (primary !== error) primary!!.addSuppressed(error)
            } }
            attempt { listener.close() }
            attempt { acceptor.join(5000); check(!acceptor.isAlive) }
            // Preserve foreign processes/toolkits. Every socket is this fixture's accepted handle.
            sockets.toList().forEach { socket -> attempt { socket.close(); check(socket.isClosed); sockets -= socket } }
            attempt { workers.shutdown(); if (!workers.awaitTermination(5, TimeUnit.SECONDS)) {
                workers.shutdownNow(); check(workers.awaitTermination(5, TimeUnit.SECONDS))
            } }
            attempt { check(listener.isClosed && sockets.isEmpty() && workers.isTerminated && pending.get() == 0) }
            attempt { assertHealthy() }
            heldSocket.set(null)
            primary?.let { throw it }
        }
        companion object {
            fun create(): HeldServer {
                val listener = ServerSocket(0, 8, InetAddress.getByAddress(byteArrayOf(127, 0, 0, 1)))
                var workers: ThreadPoolExecutor? = null
                var server: HeldServer? = null
                try {
                    val pool = ThreadPoolExecutor(3, 3, 0, TimeUnit.SECONDS, ArrayBlockingQueue<Runnable>(8),
                        { work -> Thread(work, "nativecmpkit-NEW-ordinary-held-worker").apply { isDaemon = true } })
                    workers = pool
                    return HeldServer(listener, pool).also { server = it; it.acceptor.start() }
                } catch (error: Throwable) {
                    try { server?.close() } catch (cleanup: Throwable) { if (cleanup !== error) error.addSuppressed(cleanup) }
                    try { listener.close() } catch (cleanup: Throwable) { if (cleanup !== error) error.addSuppressed(cleanup) }
                    try { workers?.shutdownNow() } catch (cleanup: Throwable) { if (cleanup !== error) error.addSuppressed(cleanup) }
                    throw error
                }
            }
        }
    }
}
