// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.web

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import com.mohamedrejeb.calf.ui.web.internal.NativeApplicationUiTest
import com.mohamedrejeb.calf.ui.web.internal.onApplicationMain
import com.mohamedrejeb.calf.ui.web.internal.requireOwnedApplicationWindow
import com.mohamedrejeb.calf.ui.web.internal.runApplicationUiTest
import com.mohamedrejeb.calf.ui.web.internal.sameNativeObject
import com.mohamedrejeb.calf.ui.web.internal.waitForNative
import kotlinx.cinterop.*
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import platform.Foundation.*
import platform.posix.getpid
import platform.posix.usleep
import kotlin.test.*

/**
 * Genuine application/library WKWebView networking, not direct delegate inputs.
 * Only localhost transports are used; no certificates, keys, trust bypass or DNS claim.
 * The second TLS request is a real document link: no content loader pre-reset can
 * substitute for didStartProvisionalNavigation clearing the preceding native error.
 */
class IosWebViewRequestAcceptanceTest {
    @Test fun nativeProvisionalTlsFailFailSuccessAndReloadResetOnlyCurrentPublicErrors() = withScope { scope ->
        val fixture = Fixture("tls")
        val state = WebViewState(WebContent.NavigatorOnly).apply { settings.javaScriptEnabled = true }
        val navigator = WebViewNavigator(scope)
        runApplicationUiTest {
            setContent { WebView(state, Modifier.fillMaxSize(), navigator = navigator) }
            loadPage(fixture, state, navigator, "tls-prior", declarative = true)
            val native = runOnIdle { assertNotNull(state.webView) }
            for ((index, stage) in listOf("tls-one", "tls-two").withIndex()) {
                fixture.arm(stage)
                val target = fixture.tlsUrl(stage)
                if (index == 0) runOnIdle { state.content = WebContent.Url(target) }
                else {
                    assertEquals(JavascriptResult.Value("1"), evaluate(state,
                        "document.getElementById('nativecmpkit-tls-two').click(); 1"))
                }
                // The owned endpoint has received a complete actual ClientHello but
                // has sent zero bytes. It has not supplied HTTP/HTML or a certificate.
                fixture.awaitStage(stage) { it["hello"] > 0 && it["pending"] > 0 && it["response_bytes"] == 0 }
                runOnIdle { assertStarted(state, target); assertTrue(sameNativeObject(native, state.webView)) }
                fixture.release(stage)
                waitForNative {
                    state.loadingState == LoadingState.Finished && state.webView?.loading == false &&
                        state.errorsForCurrentRequest.map { it.code } == listOf(NSURLErrorSecureConnectionFailed.toInt())
                }
                val transport = fixture.awaitStage(stage) {
                    it["pending"] == 0 && it["alert"] == it["hello"] && it["closed"] == it["arrived"]
                }
                assertEquals(0, transport["page"])
                assertEquals(7 * transport["alert"], transport["response_bytes"])
                runOnIdle {
                    assertTrue(state.errorsForCurrentRequest.single().description.isNotBlank(), "Native public error description is missing")
                    assertTrue(state.lastLoadedUrl == null, "No TLS-failed navigation committed a final URL")
                    assertTrue(state.pageTitle.isNullOrEmpty(), "A prior request title survived a provisional failure")
                    assertTrue(sameNativeObject(native, state.webView))
                }
                // -1200 + complete ClientHello/fatal alert/no HTTP + retained real old
                // document is the before-commit witness. No delegate is replaced/invoked.
                assertEquals(JavascriptResult.Value("\"tls-prior-1\""), evaluate(state, "document.title"))
            }
            loadPage(fixture, state, navigator, "tls-recover")
            val currentUrl = fixture.httpUrl("tls-recover")
            runOnIdle { navigator.loadHtml("<title>must-not-replace-real-page</title>", encoding = "utf-16") }
            waitForNative { state.errorsForCurrentRequest.map { it.code } == listOf(-2) && state.loadingState == LoadingState.Finished }
            assertEquals(JavascriptResult.Value("\"tls-recover-1\""), evaluate(state, "document.title"))
            fixture.arm("tls-recover")
            runOnIdle { navigator.reload() }
            fixture.awaitStage("tls-recover") { it["generation"] == 2 && it["pending"] > 0 }
            runOnIdle { assertStarted(state, currentUrl) }
            fixture.release("tls-recover")
            awaitDocument(state, "tls-recover-2", currentUrl)
            fixture.awaitStage("tls-recover") { it["page"] == 2 && it["pending"] == 0 && it["closed"] == it["arrived"] }
            runOnIdle { assertTrue(sameNativeObject(native, state.webView)); assertTrue(state.errorsForCurrentRequest.isEmpty()) }
        }
        onApplicationMain { assertNull(state.webView); assertNull(state.nativeObserver); assertNull(state.navigator) }
        fixture.complete()
    }

    @Test fun nativeLinkRedirectAndStoppedPrecommitHttpRequestFinishWithoutFalseSuccess() = withScope { scope ->
        val fixture = Fixture("matrix")
        val state = WebViewState(WebContent.NavigatorOnly).apply { settings.javaScriptEnabled = true }
        val navigator = WebViewNavigator(scope)
        runApplicationUiTest {
            setContent { WebView(state, Modifier.fillMaxSize(), navigator = navigator) }
            loadPage(fixture, state, navigator, "matrix-prior", declarative = true)
            val native = runOnIdle { assertNotNull(state.webView) }
            fixture.arm("matrix-redirect")
            fixture.arm("matrix-final")
            assertEquals(JavascriptResult.Value("1"), evaluate(state,
                "document.getElementById('nativecmpkit-redirect').click(); 1"))
            fixture.awaitStage("matrix-redirect") { it["redirect"] == 1 && it["closed"] == 1 }
            fixture.awaitStage("matrix-final") { it["pending"] > 0 }
            runOnIdle { assertStarted(state, fixture.httpUrl("matrix-redirect")) }
            fixture.release("matrix-final")
            awaitDocument(state, "matrix-final-1", fixture.httpUrl("matrix-final"))
            runOnIdle {
                assertTrue(state.requestedUrl == fixture.httpUrl("matrix-redirect"), "Requested URL must remain the native redirect entry")
                assertTrue(sameNativeObject(native, state.webView))
                assertTrue(state.errorsForCurrentRequest.isEmpty())
            }
            fixture.awaitStage("matrix-final") { it["page"] == 1 && it["pending"] == 0 }
            fixture.arm("matrix-hold")
            val stoppedUrl = fixture.httpUrl("matrix-hold")
            runOnIdle { navigator.loadUrl(stoppedUrl) }
            fixture.awaitStage("matrix-hold") { it["pending"] == 1 && it["response_bytes"] == 0 }
            runOnIdle { assertStarted(state, stoppedUrl); navigator.stopLoading() }
            // No server release or fixture cleanup closes this connection. Actual
            // client EOF is required while the held response still has zero bytes.
            val stopped = fixture.awaitStage("matrix-hold") {
                it["client_cancelled"] == 1 && it["pending"] == 0 && it["closed"] == 1
            }
            assertEquals(0, stopped["page"]); assertEquals(0, stopped["response_bytes"])
            waitForNative { state.loadingState == LoadingState.Finished && state.webView?.loading == false }
            runOnIdle {
                assertTrue(state.requestedUrl == stoppedUrl, "Stop must retain the accepted current request")
                val codes = state.errorsForCurrentRequest.map { it.code }
                assertTrue(codes.size <= 1 && codes.all { it == NSURLErrorCancelled.toInt() }, "Stop may expose only one actual native cancellation error")
                assertTrue(state.pageTitle.isNullOrEmpty(), "An uncommitted held page has no title")
                assertTrue(state.lastLoadedUrl == null, "Finished after Stop is not a committed response")
            }
            assertEquals(JavascriptResult.Value("\"matrix-final-1\""), evaluate(state, "document.title"))
            loadPage(fixture, state, navigator, "matrix-recover")
            runOnIdle { assertTrue(sameNativeObject(native, state.webView)); assertTrue(state.errorsForCurrentRequest.isEmpty()) }
        }
        onApplicationMain { assertNull(state.webView); assertNull(state.nativeObserver); assertNull(state.navigator) }
        fixture.complete()
    }

    private fun NativeApplicationUiTest.loadPage(fixture: Fixture, state: WebViewState, navigator: WebViewNavigator,
                                                stage: String, declarative: Boolean = false) {
        fixture.arm(stage)
        val target = fixture.httpUrl(stage)
        runOnIdle { if (declarative) state.content = WebContent.Url(target) else navigator.loadUrl(target) }
        fixture.awaitStage(stage) { it["pending"] > 0 && it["response_bytes"] == 0 }
        runOnIdle { assertStarted(state, target) }
        fixture.release(stage)
        awaitDocument(state, "$stage-1", target)
        fixture.awaitStage(stage) { it["page"] == 1 && it["pending"] == 0 && it["closed"] == it["arrived"] }
    }

    private fun assertStarted(state: WebViewState, url: String) {
        assertTrue(state.loadingState is LoadingState.Loading, "Actual held native request must be Loading")
        assertTrue(assertNotNull(state.webView).loading)
        assertTrue(state.requestedUrl == url, "Native provisional start did not retain the current requested URL")
        assertTrue(state.lastLoadedUrl == null, "No held provisional request committed a final URL"); assertTrue(state.pageTitle.isNullOrEmpty())
        assertTrue(state.errorsForCurrentRequest.isEmpty(), "Previous request errors were not reset before response/commit")
        assertTrue(sameNativeObject(state.webView?.navigationDelegate as? WebViewState, state))
        assertTrue(sameNativeObject(state.webView?.window, requireOwnedApplicationWindow()))
    }

    private fun NativeApplicationUiTest.awaitDocument(state: WebViewState, title: String, url: String) {
        waitForIdle()
        waitForNative {
            val view = state.webView
            view != null && !view.loading && view.title == title && state.pageTitle == title &&
                view.URL?.absoluteString == url && state.lastLoadedUrl == url && state.loadingState == LoadingState.Finished &&
                sameNativeObject(view.window, requireOwnedApplicationWindow())
        }
        assertEquals(JavascriptResult.Value("\"$title\""), evaluate(state, "document.title"))
        runOnIdle { assertTrue(state.errorsForCurrentRequest.isEmpty()) }
    }

    private fun NativeApplicationUiTest.evaluate(state: WebViewState, script: String): JavascriptResult {
        assertFalse(NSThread.isMainThread)
        var result: JavascriptResult? = null
        var calls = 0
        var offMain = false
        state.evaluateJavascriptResult(script) {
            // Record bounded facts only; never throw through a WebKit completion.
            if (!NSThread.isMainThread) offMain = true
            calls++
            result = it
        }
        waitForNative { result != null || offMain }
        return onApplicationMain {
            assertFalse(offMain, "WebKit completion left the owned main thread")
            assertEquals(1, calls)
            assertNotNull(result)
        }
    }

    private class Stage(private val values: Map<String, Int>) {
        operator fun get(key: String): Int = values[key] ?: error("Missing bounded owned transport counter")
    }

    /** Synchronous *control only* is confined to the generated Worker, never UIKit's main loop. */
    private class Fixture(private val method: String) {
        private val environment = NSProcessInfo.processInfo.environment
        private val token = assertNotNull(environment["NATIVECMPKIT_WEBVIEW_REQUEST_TOKEN"] as? String).also {
            assertTrue(Regex("[0-9a-f]{32}").matches(it), "Missing fresh owned transport lease")
        }
        private val httpPort = port("NATIVECMPKIT_WEBVIEW_REQUEST_HTTP_PORT")
        private val tlsPort = port("NATIVECMPKIT_WEBVIEW_REQUEST_TLS_PORT")
        private val controlBase = "http://localhost:$httpPort/$token/control/"
        init {
            assertFalse(NSThread.isMainThread)
            assertNotEquals(httpPort, tlsPort)
            assertEquals(getpid(), control("claim/${getpid()}")["pid"])
        }
        fun httpUrl(stage: String) = "http://localhost:$httpPort/$token/page/$stage"
        fun tlsUrl(stage: String) = "https://localhost:$tlsPort/$token/page/$stage"
        fun arm(stage: String) { assertEquals(1, control("arm/$stage")["armed"]) }
        fun release(stage: String) { assertEquals(1, control("release/$stage")["released"]) }
        fun complete() { assertEquals(1, control("done/$method")["done"]) }
        fun awaitStage(stage: String, predicate: (Stage) -> Boolean): Stage {
            assertFalse(NSThread.isMainThread)
            val deadline = NSProcessInfo.processInfo.systemUptime + 10.0
            while (true) {
                val observed = Stage(control("stats/$stage"))
                if (predicate(observed)) return observed
                check(NSProcessInfo.processInfo.systemUptime < deadline) { "Timed out awaiting bounded owned transport counters for $stage" }
                usleep(50_000u)
            }
        }
        private fun port(name: String): Int {
            val value = (environment[name] as? String)?.toIntOrNull()
            assertTrue(value != null && value in 1..65535, "Missing owned loopback transport port")
            return assertNotNull(value)
        }
        private fun control(action: String): Map<String, Int> = memScoped {
            assertFalse(NSThread.isMainThread, "Never block UIApplicationMain with fixture control")
            assertTrue(Regex("[a-z]+/[a-z0-9-]+").matches(action))
            val response = alloc<ObjCObjectVar<NSURLResponse?>>().apply { value = null }
            val failure = alloc<ObjCObjectVar<NSError?>>().apply { value = null }
            val request = NSMutableURLRequest().apply {
                setURL(assertNotNull(NSURL.URLWithString(controlBase + action)))
                setTimeoutInterval(2.0)
            }
            val data = NSURLConnection.sendSynchronousRequest(request, response.ptr, failure.ptr)
            // Native NSError bodies, response/header transcripts and environment paths
            // must never become diagnostic output. Only fixed messages/numeric codes.
            assertTrue(failure.value == null, "Owned loopback control failed; nativeCode=${failure.value?.code}")
            assertEquals(200L, (response.value as? NSHTTPURLResponse)?.statusCode)
            val body = assertNotNull(data)
            assertTrue(body.length in 1uL..2048uL, "Control response exceeds the finite protocol")
            val text = assertNotNull(body.bytes).reinterpret<ByteVar>().readBytes(body.length.toInt()).decodeToString()
            val result = mutableMapOf<String, Int>()
            text.trimEnd('\n').split('\n').forEach { line ->
                val pair = line.split('=')
                assertTrue(pair.size == 2 && Regex("[a-z_]+=[0-9]{1,10}").matches(line), "Unreviewed owned control record")
                assertTrue(pair[0] !in result, "Duplicate owned control counter")
                result[pair[0]] = assertNotNull(pair[1].toIntOrNull())
            }
            result
        }
    }

    private fun withScope(block: (CoroutineScope) -> Unit) {
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
        try { block(scope) } finally { scope.cancel() }
    }
}
