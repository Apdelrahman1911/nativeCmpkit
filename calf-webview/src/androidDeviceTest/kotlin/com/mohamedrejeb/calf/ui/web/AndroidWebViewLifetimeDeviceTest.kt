package com.mohamedrejeb.calf.ui.web

import android.content.Intent
import android.os.Bundle
import android.os.Looper
import android.os.Parcel
import android.os.SystemClock
import android.security.NetworkSecurityPolicy
import android.view.ViewGroup
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView as AndroidWebView
import android.widget.FrameLayout
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.SaverScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.Lifecycle
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import org.junit.Test
import org.junit.runner.RunWith
import java.io.ByteArrayInputStream
import java.io.IOException
import java.lang.ref.WeakReference
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlin.test.*

/** Real library Activity/Compose roots and Android provider; no Robolectric, sample or renderer stub. */
@RunWith(AndroidJUnit4::class)
class AndroidWebViewLifetimeDeviceTest {
    @Test fun retainedStateReleasesRepeatedRealActivitiesAndViewsAndRestoresSerializedNativeState() {
        val url = "https://nativecmpkit.invalid/lifetime"
        val html = "<html><head><title>native-lifetime</title></head><body>owned native document</body></html>".toByteArray()
        fun client() = object : AccompanistWebViewClient() {
            override fun shouldInterceptRequest(view: AndroidWebView, request: WebResourceRequest): WebResourceResponse =
                WebResourceResponse("text/html", "UTF-8", if (request.url.toString() == url) 200 else 404,
                    if (request.url.toString() == url) "OK" else "Not Found", emptyMap(),
                    ByteArrayInputStream(if (request.url.toString() == url) html else byteArrayOf()))
        }
        val retained = WebViewState(WebContent.Url(url))
        val witnesses = mutableListOf<WeakReference<*>>()
        repeat(3) {
            val fixture = AndroidLifetimeFixture(retained, client())
            ActivityLease(fixture).use { host ->
                host.awaitCreated()
                await("Real native URL/title completion") { onMain {
                    retained.webView?.title == "native-lifetime" && retained.webView?.url == url &&
                        retained.loadingState == LoadingState.Finished
                } }
                witnesses += fixture.references
            }
            assertEquals(1, fixture.created.get())
            assertEquals(1, fixture.disposed.get())
            onMain { assertNull(retained.webView); assertNotNull(retained.viewState) }
            assertCollected(fixture.references)
        }
        assertCollected(witnesses) // The original state remains strongly reachable during collection.

        // Exercise the actual public saver through Android's process-state serialization format.
        // This is a Parcelable round trip + new real Activity, NOT an OS process-death claim.
        val restored = onMain {
            val scope = object : SaverScope { override fun canBeSaved(value: Any) = true }
            val saved = assertNotNull(with(WebStateSaver) { scope.save(retained) })
            val parcel = Parcel.obtain()
            val wire = try {
                parcel.writeValue(saved)
                assertTrue(parcel.dataSize() > 0)
                parcel.setDataPosition(0)
                @Suppress("DEPRECATION")
                assertNotNull(parcel.readValue(WebViewState::class.java.classLoader))
            } finally { parcel.recycle() }
            assertNotNull(WebStateSaver.restore(wire)).apply { assertNotNull(viewState) }
        }
        assertNotSame(retained, restored)
        val fixture = AndroidLifetimeFixture(restored, client())
        ActivityLease(fixture).use { host ->
            host.awaitCreated()
            onMain {
                assertEquals(url, restored.webView!!.copyBackForwardList().currentItem?.url)
                fixture.navigator.reload() // Supported navigator restoration, not a synthetic list/DOM.
            }
            await("Serialized native history restores a real document") { onMain {
                restored.webView?.title == "native-lifetime" && restored.webView?.url == url &&
                    restored.loadingState == LoadingState.Finished
            } }
        }
        assertCollected(fixture.references)
        onMain { assertNull(restored.webView); assertNull(retained.webView) }
    }

    @Test fun compositionDisposalClosesItsRealSlowConnectionAndStopsTheLiveMediaDocument() {
        onMain {
            val policy = NetworkSecurityPolicy.getInstance()
            assertTrue(policy.isCleartextTrafficPermitted("127.0.0.1"))
            assertFalse(policy.isCleartextTrafficPermitted("nativecmpkit.invalid"))
            assertFalse(policy.isCleartextTrafficPermitted("localhost"))
        }
        AndroidLifetimeHttpServer().use { server ->
            val state = WebViewState(WebContent.Url(server.baseUrl)).apply {
                settings.javaScriptEnabled = true
                settings.androidSettings.mediaPlaybackRequiresUserGesture = false
            }
            val fixture = AndroidLifetimeFixture(state)
            ActivityLease(fixture).use { host ->
                host.awaitCreated()
                assertTrue(server.slowStarted.await(10, TimeUnit.SECONDS), "A real native slow connection must be open")
                await("Actual provider must decode/play media before disposal") {
                    onMain { state.webView?.title == "native-media-live" } && server.beats.get() >= 5 && server.writes.get() >= 2
                }
                assertEquals("true", evaluate(state, "!media.paused && media.currentTime > 0.1 && media.readyState >= 2"))
                assertEquals(1L, server.disconnected.count, "Already-disconnected IO is not cancellation coverage")
                host.unmount() // The Activity is still RESUMED: its pause/finish cannot supply cleanup.
                host.assertResumed()
                assertTrue(server.disconnected.await(10, TimeUnit.SECONDS), "Native disposal must disconnect before fixture cleanup")
                await("Old media document must stop its real timer/network work") {
                    val before = server.beats.get(); Thread.sleep(700); before == server.beats.get()
                }
                val stopped = server.beats.get(); Thread.sleep(700)
                assertEquals(stopped, server.beats.get())
                assertEquals(1, fixture.disposed.get())
                assertCollected(fixture.references.filter { it.get() !is WebViewLifetimeActivity })
                onMain { assertNull(state.webView) }
            }
        }
    }

    @Test fun throwingNativeReleaseCannotRetainItsActivityViewOrClearTheLiveReplacement() {
        val previousState = WebViewState(WebContent.Data("<html><title>previous-native</title></html>"))
        val currentState = WebViewState(WebContent.Data("<html><title>current-native</title></html>")).apply {
            settings.javaScriptEnabled = true
        }
        val aFixture = AndroidLifetimeFixture(previousState, initiallyMounted = false)
        val bFixture = AndroidLifetimeFixture(currentState)
        val a = ActivityLease(aFixture)
        var b: ActivityLease? = null
        var previousWitness: WeakReference<AndroidWebView>? = null
        try {
            val activeSecond = ActivityLease(bFixture).also { b = it }
            activeSecond.awaitCreated()
            a.onActivity { activity ->
                val native = createAndroidWebView(previousState, { AndroidWebView(activity) }, {
                    it.layoutParams = FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)
                }, {})
                activity.addContentView(native, native.layoutParams)
                previousWitness = WeakReference(native)
                loadAndroidContent(native, previousState, previousState.content)
            }
            await("Both real native documents must be ready") { onMain {
                previousState.webView?.title == "previous-native" && currentState.webView?.title == "current-native"
            } }
            val expected = IllegalStateException("controlled application disposal failure")
            onMain {
                val old = assertNotNull(previousState.webView)
                val replacement = assertNotNull(currentState.webView)
                val failure = assertFailsWith<IllegalStateException> {
                    releaseAndroidWebView(previousState, old) {
                        previousState.webView = replacement // Simulate a native ownership handoff inside the callback.
                        throw expected
                    }
                }
                assertSame(expected, failure)
                assertSame(replacement, previousState.webView)
                assertSame(replacement, currentState.webView)
                assertNull(old.parent, "Library release must remove the real native child, even after callback failure")
            }
            assertCollected(listOf(assertNotNull(previousWitness)))
            a.close()
            assertEquals("3", evaluate(currentState, "1 + 2"), "Another real Compose/Activity engine must keep working")
            assertEquals(0, bFixture.disposed.get())
        } finally {
            try { onMain { previousState.webView = null } } finally {
                try { a.close() } finally { b?.close() }
            }
        }
        assertCollected(aFixture.references + bFixture.references)
    }

    private fun evaluate(state: WebViewState, script: String): String {
        val result = AtomicReference<String?>()
        onMain { assertNotNull(state.webView).evaluateJavascript(script) { result.set(it) } }
        await("Real provider JavaScript callback") { result.get() != null }
        return assertNotNull(result.get())
    }

    private fun assertCollected(references: List<WeakReference<*>>) {
        assertTrue(references.isNotEmpty())
        repeat(60) {
            System.gc(); System.runFinalization(); onMain {}
            if (references.all { it.get() == null }) return
            Thread.sleep(100)
        }
        assertTrue(references.all { it.get() == null }, "Retained native/Activity references: ${references.mapNotNull { it.get()?.javaClass?.name }}")
    }
}

internal fun <T> onMain(body: () -> T): T {
    val result = AtomicReference<Result<T>>()
    InstrumentationRegistry.getInstrumentation().runOnMainSync { result.set(runCatching(body)) }
    return assertNotNull(result.get()).getOrThrow()
}

internal fun await(description: String, condition: () -> Boolean) {
    val end = SystemClock.elapsedRealtime() + 20_000
    while (!condition() && SystemClock.elapsedRealtime() < end) Thread.sleep(25)
    assertTrue(condition(), description)
}

internal class AndroidLifetimeFixture(val state: WebViewState, val client: AccompanistWebViewClient? = null,
                                     initiallyMounted: Boolean = true) {
    val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    val navigator = WebViewNavigator(scope)
    val references = CopyOnWriteArrayList<WeakReference<*>>()
    val created = AtomicInteger()
    val disposed = AtomicInteger()
    val observedAttachment = AtomicBoolean()
    var mounted by mutableStateOf(initiallyMounted)
    fun created() {
        check(Looper.myLooper() == Looper.getMainLooper())
        references += WeakReference(checkNotNull(state.webView))
        created.incrementAndGet()
    }
}

internal object AndroidLifetimeRegistry { val fixtures = ConcurrentHashMap<String, AndroidLifetimeFixture>() }

/** Test-APK component only; independent registry slots permit two real Activity/native owners. */
class WebViewLifetimeActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val fixture = checkNotNull(AndroidLifetimeRegistry.fixtures[checkNotNull(intent.getStringExtra("nativecmpkit-lifetime"))])
        fixture.references += WeakReference(this)
        setContent {
            if (fixture.mounted) {
                if (fixture.client == null) {
                    WebView(fixture.state, Modifier.fillMaxSize(), navigator = fixture.navigator,
                        onCreated = { fixture.created() }, onDispose = { fixture.disposed.incrementAndGet() })
                } else {
                    WebView(fixture.state, FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT),
                        Modifier.fillMaxSize(), navigator = fixture.navigator, client = fixture.client,
                        onCreated = { fixture.created() }, onDispose = { fixture.disposed.incrementAndGet() })
                }
            }
            val attached = fixture.state.webView != null
            SideEffect { fixture.observedAttachment.set(attached) }
        }
    }
}

internal class ActivityLease(val fixture: AndroidLifetimeFixture) : AutoCloseable {
    private val key = UUID.randomUUID().toString()
    private val scenario = AtomicReference<ActivityScenario<WebViewLifetimeActivity>?>()
    init {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        check(context.packageName == InstrumentationRegistry.getInstrumentation().context.packageName) {
            "This AGP library test host must be the same real target/test APK, not a foreign application"
        }
        AndroidLifetimeRegistry.fixtures[key] = fixture
        try {
            scenario.set(ActivityScenario.launch(Intent(context, WebViewLifetimeActivity::class.java).putExtra("nativecmpkit-lifetime", key)))
        } catch (failure: Throwable) {
            AndroidLifetimeRegistry.fixtures.remove(key); fixture.scope.cancel(); throw failure
        }
    }
    fun awaitCreated() = await("Real attached native view and Compose attachment notification") {
        fixture.created.get() == 1 && fixture.observedAttachment.get() && onMain { fixture.state.webView?.isAttachedToWindow == true }
    }
    fun onActivity(body: (WebViewLifetimeActivity) -> Unit) { assertNotNull(scenario.get()).onActivity { body(it) } }
    fun unmount() {
        onMain { fixture.mounted = false }
        await("Real composition release and observable null attachment") {
            fixture.disposed.get() == 1 && !fixture.observedAttachment.get() && onMain { fixture.state.webView == null }
        }
    }
    fun assertResumed() = onActivity {
        assertFalse(it.isFinishing); assertFalse(it.isDestroyed)
        assertEquals(Lifecycle.State.RESUMED, it.lifecycle.currentState)
    }
    override fun close() {
        try { scenario.getAndSet(null)?.close() }
        finally { AndroidLifetimeRegistry.fixtures.remove(key); fixture.scope.cancel() }
    }
}

/** Real loopback socket fixture. Only owned sockets/workers are stopped, AFTER disposal assertions. */
internal class AndroidLifetimeHttpServer : AutoCloseable {
    val slowStarted = CountDownLatch(1)
    val disconnected = CountDownLatch(1)
    val beats = AtomicInteger()
    val writes = AtomicInteger()
    private val released = CountDownLatch(1)
    private val server = ServerSocket(0, 8, InetAddress.getByName("127.0.0.1"))
    private val sockets = ConcurrentHashMap.newKeySet<Socket>()
    private val workers = Executors.newFixedThreadPool(4)
    private val acceptor = Thread({
        while (!server.isClosed) {
            try {
                val socket = server.accept(); sockets += socket
                workers.execute { try { serve(socket) } finally { sockets -= socket; socket.close() } }
            } catch (failure: IOException) { if (!server.isClosed) throw failure }
        }
    }, "nativecmpkit-owned-lifetime-acceptor").apply { isDaemon = true; start() }
    val baseUrl = "http://127.0.0.1:${server.localPort}/"
    private val wave = ByteBuffer.allocate(44 + 160_000).order(ByteOrder.LITTLE_ENDIAN).apply {
        put("RIFF".toByteArray()); putInt(36 + 160_000); put("WAVEfmt ".toByteArray())
        putInt(16); putShort(1); putShort(1); putInt(16_000); putInt(32_000); putShort(2); putShort(16)
        put("data".toByteArray()); putInt(160_000); repeat(160_000) { put(0) }
    }.array()
    private fun serve(socket: Socket) {
        socket.soTimeout = 5_000
        val input = socket.getInputStream().bufferedReader(Charsets.US_ASCII)
        val request = input.readLine() ?: return
        check(request.length <= 4_096)
        val headers = mutableMapOf<String, String>()
        var total = request.length
        while (true) {
            val line = input.readLine() ?: return
            total += line.length; check(total <= 8_192)
            if (line.isEmpty()) break
            val colon = line.indexOf(':'); check(colon > 0)
            headers[line.substring(0, colon).lowercase()] = line.substring(colon + 1).trim()
        }
        val path = request.split(' ')[1].substringBefore('?')
        val output = socket.getOutputStream()
        fun respond(code: Int, type: String, body: ByteArray, extra: String = "") {
            output.write(("HTTP/1.1 $code ${if (code == 200 || code == 206) "OK" else "No Content"}\r\n" +
                "Content-Type: $type\r\nContent-Length: ${body.size}\r\nConnection: close\r\nCache-Control: no-store\r\n$extra\r\n").toByteArray())
            if (!request.startsWith("HEAD ")) output.write(body)
            output.flush()
        }
        try {
            when (path) {
                "/beat" -> { beats.incrementAndGet(); respond(204, "text/plain", byteArrayOf()) }
                "/sample.wav" -> {
                    val range = headers["range"]?.let { Regex("bytes=([0-9]+)-([0-9]*)").matchEntire(it) }
                    val start = range?.groupValues?.get(1)?.toIntOrNull() ?: 0
                    val end = range?.groupValues?.get(2)?.toIntOrNull() ?: wave.lastIndex
                    check(start in wave.indices && end in start..wave.lastIndex)
                    respond(if (range == null) 200 else 206, "audio/wav", wave.copyOfRange(start, end + 1),
                        "Accept-Ranges: bytes\r\n" + if (range == null) "" else "Content-Range: bytes $start-$end/${wave.size}\r\n")
                }
                "/slow" -> {
                    output.write("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 1000000\r\nConnection: close\r\n\r\n<html><body>live incomplete native stream".toByteArray())
                    output.flush(); slowStarted.countDown()
                    try {
                        while (!released.await(25, TimeUnit.MILLISECONDS)) { output.write(ByteArray(1_024) { 32 }); output.flush(); writes.incrementAndGet() }
                    } catch (_: IOException) { disconnected.countDown() }
                }
                "/" -> respond(200, "text/html; charset=utf-8", """
                    <!doctype html><html><head><title>media-starting</title></head><body>
                    <audio id="media" src="/sample.wav" autoplay muted loop></audio><script>
                    var media = document.getElementById('media'); media.muted = true;
                    media.addEventListener('error', function() { document.title = 'media-error:' + media.error.code; });
                    var started = media.play(); if (started && started.catch) started.catch(function(e) { document.title = 'media-rejected:' + e.name; });
                    setInterval(function() { if (!media.paused && media.currentTime > 0.1) document.title = 'native-media-live';
                        var request = new XMLHttpRequest(); request.open('GET', '/beat'); request.send(); }, 100);
                    </script><iframe src="/slow"></iframe></body></html>
                """.trimIndent().toByteArray())
                else -> respond(404, "text/plain", byteArrayOf())
            }
        } catch (_: IOException) { /* Native clients may cancel ordinary responses during teardown. */ }
    }
    override fun close() {
        released.countDown(); server.close(); sockets.forEach { it.close() }
        acceptor.join(5_000); assertFalse(acceptor.isAlive)
        workers.shutdownNow(); assertTrue(workers.awaitTermination(5, TimeUnit.SECONDS))
    }
}
