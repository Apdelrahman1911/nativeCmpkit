package com.mohamedrejeb.calf.ui.web

import android.webkit.WebView as AndroidWebView
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.view.ViewGroup.LayoutParams
import android.widget.FrameLayout
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.ComposeTimeoutException
import androidx.compose.ui.test.click
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onRoot
import androidx.compose.ui.test.performTouchInput
import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import org.junit.After
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.io.ByteArrayInputStream
import java.util.concurrent.atomic.AtomicInteger
import kotlin.test.*

/** Requires an Android emulator/device with a real WebView provider. Not a Robolectric suite. */
@RunWith(AndroidJUnit4::class)
class AndroidWebViewHistoryDeviceTest {
    @get:Rule val compose = createComposeRule()
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    @After fun closeScope() { scope.cancel() }

    @Test fun navigatorReplacementReadsRealBrowserHistoryWithoutAnotherPageEvent() {
        val url = "https://nativecmpkit.invalid/fixture"
        val document = """
                <!doctype html><html><head><title>Local history fixture</title>
                <meta name="viewport" content="width=device-width,initial-scale=1">
                <style>html,body{margin:0;width:100%;height:100%}
                button{display:block;width:100vw;height:100vh;border:0}</style></head>
                <body><button id="history" type="button">Create local history</button>
                <script>
                window.fixtureClicks = 0;
                document.getElementById('history').addEventListener('click', function() {
                    window.fixtureClicks++;
                    window.fixtureActivated = navigator.userActivation.isActive;
                    history.pushState(null, '', '#first');
                    history.pushState(null, '', '#second');
                    document.title = 'history-ready';
                });
                </script></body></html>
            """.trimIndent().toByteArray(Charsets.UTF_8)
        val served = AtomicInteger()
        // Use a genuine URL document, not loadDataWithBaseURL. The observed
        // inline provider restored the data entry with an empty DOM hash even
        // though its native list reached index1/size3. A library-owned client
        // serves deterministic bytes for this URL without network/cleartext
        // exemptions, a server dependency or replacing the history contract.
        val client = object : AccompanistWebViewClient() {
            override fun shouldInterceptRequest(view: AndroidWebView, request: WebResourceRequest): WebResourceResponse {
                val fixture = request.url.toString() == url
                if (fixture) served.incrementAndGet()
                return WebResourceResponse(
                    "text/html", "UTF-8", if (fixture) 200 else 404,
                    if (fixture) "OK" else "Not Found", emptyMap(),
                    ByteArrayInputStream(if (fixture) document else byteArrayOf()),
                )
            }
        }
        val state = WebViewState(WebContent.Url(url)).apply { settings.javaScriptEnabled = true }
        var navigator by mutableStateOf(WebViewNavigator(scope))
        var created = 0
        var disposed = 0
        compose.setContent {
            WebView(state, layoutParams = FrameLayout.LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT),
                modifier = Modifier.fillMaxSize(), navigator = navigator, client = client,
                onCreated = { created++ }, onDispose = { disposed++ })
        }
        compose.waitUntil(timeoutMillis = 15_000) {
            compose.runOnUiThread { state.webView != null && state.loadingState == LoadingState.Finished }
        }
        val native = compose.runOnIdle { assertNotNull(state.webView) }
        assertEquals(1, served.get(), "The real URL fixture must be served once by the library-owned client")
        // A real gesture, not evaluateJavascript, creates the history. Chromium
        // can skip script-only entries on goBack without user activation. Keep
        // the native history precondition and verify the DOM actually saw input.
        compose.onRoot().performTouchInput { click(center) }
        waitForNativeHistory(native, "DOM gesture completion") { native.title == "history-ready" }
        var scriptResult: String? = null
        compose.runOnIdle {
            native.evaluateJavascript(
                "window.fixtureActivated === true && window.fixtureClicks === 1 && location.hash === '#second'",
            ) { scriptResult = it }
        }
        compose.waitUntil(timeoutMillis = 10_000) { compose.runOnUiThread { scriptResult != null } }
        assertEquals("true", compose.runOnUiThread { scriptResult }, "Real DOM click must have active user activation and create both entries")
        compose.runOnIdle {
            val history = native.copyBackForwardList()
            assertEquals(3, history.size, "Real input must create two native entries after the initial page")
            assertEquals(2, history.currentIndex)
            assertTrue(native.canGoBack())
            assertFalse(native.canGoForward())
            native.goBack()
        }
        waitForNativeHistory(native, "backward/forward history precondition") {
            val history = native.copyBackForwardList()
            native.canGoBack() && native.canGoForward() && history.currentIndex == 1 && history.size == 3
        }
        // Require real DOM restoration as well as native list/capability state.
        // A list index alone is not proof that the intended document returned.
        var backedHash: String? = null
        compose.runOnIdle { native.evaluateJavascript("location.hash") { backedHash = it } }
        compose.waitUntil(timeoutMillis = 10_000) { compose.runOnUiThread { backedHash != null } }
        assertEquals("\"#first\"", compose.runOnUiThread { backedHash }, "The actual DOM must return to the first entry")

        val replacement = WebViewNavigator(scope)
        assertFalse(replacement.canGoBack)
        assertFalse(replacement.canGoForward)
        compose.runOnIdle { navigator = replacement }
        compose.waitForIdle()
        compose.runOnIdle {
            assertSame(native, state.webView)
            assertEquals(native.canGoBack(), replacement.canGoBack)
            assertEquals(native.canGoForward(), replacement.canGoForward)
            assertTrue(replacement.canGoBack)
            assertTrue(replacement.canGoForward)
            assertEquals(1, created)
            assertEquals(0, disposed)
        }
    }

    private fun waitForNativeHistory(native: AndroidWebView, phase: String, condition: () -> Boolean) {
        try {
            compose.waitUntil(timeoutMillis = 10_000) { compose.runOnUiThread { condition() } }
        } catch (failure: ComposeTimeoutException) {
            // Bounded actual browser state, not a fabricated history assumption.
            val diagnostic = compose.runOnUiThread {
                val history = native.copyBackForwardList()
                val urls = (0 until minOf(history.size, 16)).map { history.getItemAtIndex(it).url.take(256) }
                "url=${native.url?.take(256)}, back=${native.canGoBack()}, forward=${native.canGoForward()}, " +
                    "index=${history.currentIndex}, size=${history.size}, entries=$urls"
            }
            throw AssertionError("$phase timed out; actual native history: $diagnostic", failure)
        }
    }
}
