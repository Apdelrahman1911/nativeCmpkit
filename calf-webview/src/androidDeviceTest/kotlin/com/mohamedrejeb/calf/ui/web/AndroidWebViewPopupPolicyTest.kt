// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import android.os.Looper
import android.os.SystemClock
import android.view.InputDevice
import android.view.KeyCharacterMap
import android.view.KeyEvent
import android.view.ViewGroup
import android.webkit.WebView as AndroidWebView
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.click
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onRoot
import androidx.compose.ui.test.performTouchInput
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import org.junit.After
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlin.test.*

/** Actual public composition, Chromium documents, DOM touches and owned loopback HTTP.
 * No direct native client callbacks, child-window substitute or sample application.
 */
@RunWith(AndroidJUnit4::class)
class AndroidWebViewPopupPolicyTest {
    @get:Rule val compose = createComposeRule()
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    @After fun closeScope() { scope.cancel() }

    @Test fun defaultPolicyRejectsSameCrossOriginAndUntrustedBlankLinksAndKeepsParentHistory() {
        PopupServer().use { server -> PopupServer().use { other ->
            val owner = WebViewState(WebContent.Url(server.url("parent-default")))
                .apply { settings.javaScriptEnabled = true }
            val navigator = WebViewNavigator(scope)
            var mounted by mutableStateOf(true)
            val observed = AtomicReference<AndroidPopupRejection?>()
            var creates = 0
            var disposals = 0
            compose.setContent {
                if (mounted) WebView(owner, Modifier.fillMaxSize(), navigator = navigator,
                    onCreated = { creates++ }, onDispose = { disposals++ })
                val rejection = owner.settings.androidSettings.lastPopupRejection
                SideEffect { observed.set(rejection) }
            }
            awaitDocument(owner, "parent-default")
            val native = compose.runOnIdle { assertNotNull(owner.webView) }
            compose.runOnIdle {
                assertTrue(native.settings.supportMultipleWindows())
                assertNull(owner.settings.androidSettings.lastPopupRejection)
            }
            val destinations = listOf(server.url("target-same"), other.url("target-cross"),
                "nativecmpkit-untrusted://must-not-open/handler")
            destinations.forEachIndexed { index, destination ->
                assertEquals(JavascriptResult.Value("true"), evaluate(owner,
                    "document.getElementById('go').href=${quoteJavascript(destination)}; true"))
                clickDocument()
                val number = index.toLong() + 1L
                compose.waitUntil(10_000) { observed.get()?.requestNumber == number }
                compose.runOnIdle {
                    assertEquals(AndroidPopupRejection(number, false, true), observed.get())
                    assertSame(native, owner.webView)
                    assertEquals(1, creates)
                    assertEquals(0, disposals)
                    assertEquals(1, assertNotNull(native.parent as? ViewGroup).childCount)
                    assertFalse(native.canGoBack(), "Rejected child URLs must not enter the parent history")
                }
                assertEquals(JavascriptResult.Value("true"), evaluate(owner, "window.fixtureActivated === true"))
                assertEquals(JavascriptResult.Value(number.toString()), evaluate(owner, "window.fixtureClicks"))
                awaitDocument(owner, "parent-default")
            }
            assertTrue(server.requests.none { it.startsWith("target-") })
            assertTrue(other.requests.isEmpty(), "A cross-origin child must not start a hidden network load")
            // Real input gives the parent two user-activated history entries. Rejection
            // must not break normal back dispatch or cause a new child on that route.
            assertEquals(JavascriptResult.Value("true"), evaluate(owner, "window.fixtureHistoryMode=true; true"))
            clickDocument()
            compose.waitUntil(10_000) { compose.runOnUiThread { navigator.canGoBack && native.copyBackForwardList().size == 3 } }
            assertEquals(JavascriptResult.Value("\"#second\""), evaluate(owner, "location.hash"))
            sendNativeBack()
            compose.waitUntil(10_000) { compose.runOnUiThread { native.copyBackForwardList().currentIndex == 1 } }
            assertEquals(JavascriptResult.Value("\"#first\""), evaluate(owner, "location.hash"))
            compose.runOnIdle {
                assertEquals(3L, owner.settings.androidSettings.lastPopupRejection?.requestNumber)
                mounted = false
            }
            compose.waitUntil(10_000) { compose.runOnUiThread { owner.webView == null && native.parent == null } }
            compose.runOnIdle { assertEquals(1, creates); assertEquals(1, disposals) }
        } }
    }

    @Test fun javascriptAutomaticAndMultipleWindowCombinationsHaveExplicitNativeOutcomes() {
        PopupServer().use { server ->
            val owner = WebViewState(WebContent.Url(server.url("parent-initial")))
            var mounted by mutableStateOf(true)
            compose.setContent { if (mounted) WebView(owner, Modifier.fillMaxSize()) }
            awaitDocument(owner, "parent-initial")
            val native = compose.runOnIdle { assertNotNull(owner.webView) }
            var rejections = 0L
            var scenario = 0
            for (multiple in listOf(true, false)) for (javascript in listOf(false, true)) for (automatic in listOf(false, true)) {
                scenario++
                val automaticPage = "auto-$scenario"
                val automaticTarget = "target-$automaticPage"
                compose.runOnIdle {
                    owner.settings.batch {
                        javaScriptEnabled = javascript
                        javaScriptCanOpenWindowsAutomatically = automatic
                        androidSettings.supportMultipleWindows = multiple
                    }
                    owner.content = WebContent.Url(server.url(automaticPage))
                }
                val attempted = javascript && automatic
                awaitDocument(owner, if (attempted && !multiple) automaticTarget else automaticPage)
                if (attempted && multiple) rejections++
                compose.runOnIdle {
                    assertSame(native, owner.webView)
                    assertEquals(rejections, owner.settings.androidSettings.lastPopupRejection?.requestNumber ?: 0L)
                    if (attempted && multiple) assertFalse(assertNotNull(owner.settings.androidSettings.lastPopupRejection).isUserGesture)
                }
                assertEquals(if (attempted && !multiple) 1 else 0, server.requests.count { it == automaticTarget })

                // A real link works even with JS disabled; automatic-window permission
                // does not suppress a user-initiated request. False native multiple-
                // window mode deliberately navigates this same view instead of a child.
                val userPage = "user-$scenario"
                compose.runOnIdle { owner.content = WebContent.Url(server.url(userPage)) }
                awaitDocument(owner, userPage)
                clickDocument()
                if (multiple) {
                    rejections++
                    compose.waitUntil(10_000) { compose.runOnUiThread {
                        owner.settings.androidSettings.lastPopupRejection?.requestNumber == rejections
                    } }
                    awaitDocument(owner, userPage)
                } else awaitDocument(owner, "target-$userPage")
                compose.runOnIdle {
                    assertSame(native, owner.webView)
                    assertEquals(rejections, owner.settings.androidSettings.lastPopupRejection?.requestNumber ?: 0L)
                    if (multiple) assertTrue(assertNotNull(owner.settings.androidSettings.lastPopupRejection).isUserGesture)
                }
                assertEquals(if (multiple) 0 else 1, server.requests.count { it == "target-$userPage" })
                if (javascript && multiple) {
                    // User window.open is distinct from an anchor and remains allowed
                    // to request a window when automatic script popups are disabled.
                    val scriptPage = "user-script-$scenario"
                    compose.runOnIdle { owner.content = WebContent.Url(server.url(scriptPage)) }
                    awaitDocument(owner, scriptPage)
                    clickDocument()
                    rejections++
                    compose.waitUntil(10_000) { compose.runOnUiThread {
                        owner.settings.androidSettings.lastPopupRejection?.requestNumber == rejections
                    } }
                    assertEquals(JavascriptResult.Value("true"), evaluate(owner, "window.fixtureActivated === true"))
                    assertTrue(server.requests.none { it == "target-$scriptPage" })
                }
            }
            compose.runOnIdle { mounted = false }
            compose.waitUntil(10_000) { compose.runOnUiThread { owner.webView == null && native.parent == null } }
        }
    }

    @Test fun rawCurrentViewFallbackAndReplacementRetainIndependentRejectionStateAndCleanup() {
        PopupServer().use { server ->
            val first = WebViewState(WebContent.Url(server.url("parent-first"))).apply {
                settings.javaScriptEnabled = true
                settings.androidSettings.supportMultipleWindows = false
            }
            val second = WebViewState(WebContent.Url(server.url("parent-second")))
                .apply { settings.javaScriptEnabled = true }
            var owner by mutableStateOf(first)
            var mounted by mutableStateOf(true)
            val nativeOwners = mutableListOf<AndroidWebView>()
            var disposals = 0
            compose.setContent {
                val current = owner
                if (mounted) WebView(current, Modifier.fillMaxSize(),
                    onCreated = { nativeOwners += assertNotNull(current.webView) }, onDispose = { disposals++ })
            }
            awaitDocument(first, "parent-first")
            val firstNative = compose.runOnIdle { assertNotNull(first.webView) }
            clickDocument()
            awaitDocument(first, "target-parent-first")
            compose.runOnIdle {
                assertSame(firstNative, first.webView)
                assertNull(first.settings.androidSettings.lastPopupRejection)
                assertTrue(firstNative.canGoBack())
            }
            sendNativeBack()
            awaitDocument(first, "parent-first")
            compose.runOnIdle { first.settings.androidSettings.supportMultipleWindows = true }
            clickDocument()
            compose.waitUntil(10_000) { compose.runOnUiThread { first.settings.androidSettings.lastPopupRejection?.requestNumber == 1L } }
            assertEquals(1, server.requests.count { it == "target-parent-first" })
            compose.runOnIdle { owner = second }
            awaitDocument(second, "parent-second")
            val secondNative = compose.runOnIdle {
                assertNull(first.webView)
                assertNull(firstNative.parent)
                assertEquals(1, disposals)
                assertNotNull(second.webView).also { assertNotSame(firstNative, it) }
            }
            clickDocument()
            compose.waitUntil(10_000) { compose.runOnUiThread { second.settings.androidSettings.lastPopupRejection?.requestNumber == 1L } }
            compose.runOnIdle {
                assertEquals(AndroidPopupRejection(1L, false, true), first.settings.androidSettings.lastPopupRejection)
                assertEquals(AndroidPopupRejection(1L, false, true), second.settings.androidSettings.lastPopupRejection)
                assertSame(secondNative, second.webView)
                assertEquals(listOf(firstNative, secondNative), nativeOwners)
                mounted = false
            }
            compose.waitUntil(10_000) { compose.runOnUiThread { second.webView == null && secondNative.parent == null } }
            compose.runOnIdle { assertEquals(2, disposals) }
        }
    }

    private fun clickDocument() = compose.onRoot().performTouchInput { click(center) }

    private fun sendNativeBack() {
        val automation = InstrumentationRegistry.getInstrumentation().uiAutomation
        val downTime = SystemClock.uptimeMillis()
        for (action in listOf(KeyEvent.ACTION_DOWN, KeyEvent.ACTION_UP)) {
            val event = KeyEvent(downTime, SystemClock.uptimeMillis(), action, KeyEvent.KEYCODE_BACK,
                0, 0, KeyCharacterMap.VIRTUAL_KEYBOARD, 0, KeyEvent.FLAG_FROM_SYSTEM, InputDevice.SOURCE_KEYBOARD)
            assertTrue(automation.injectInputEvent(event, true), "Real Android back input must be delivered")
        }
    }

    private fun awaitDocument(owner: WebViewState, title: String) {
        compose.waitUntil(15_000) { compose.runOnUiThread {
            owner.webView?.title == title && owner.pageTitle == title && owner.loadingState == LoadingState.Finished
        } }
        if (compose.runOnUiThread { owner.settings.javaScriptEnabled }) {
            assertEquals(JavascriptResult.Value("\"$title\""), evaluate(owner, "document.title"))
        }
    }

    private fun evaluate(owner: WebViewState, script: String): JavascriptResult {
        assertNotSame(Looper.getMainLooper(), Looper.myLooper())
        val result = AtomicReference<JavascriptResult?>()
        val calls = AtomicInteger()
        owner.evaluateJavascriptResult(script) {
            assertSame(Looper.getMainLooper(), Looper.myLooper())
            assertEquals(0, calls.getAndIncrement())
            result.set(it)
        }
        compose.waitUntil(15_000) { result.get() != null }
        return compose.runOnIdle { assertEquals(1, calls.get()); assertNotNull(result.get()) }
    }

    private class PopupServer : AutoCloseable {
        private val socket = ServerSocket(0, 8, InetAddress.getByName("127.0.0.1"))
        private val active = AtomicReference<Socket?>()
        private val failure = AtomicReference<Throwable?>()
        val requests = ConcurrentLinkedQueue<String>()
        private val worker = Thread({
            try {
                while (!socket.isClosed) {
                    val connection = socket.accept()
                    active.set(connection)
                    connection.use { client ->
                        client.soTimeout = 2_000
                        val reader = client.getInputStream().bufferedReader(Charsets.US_ASCII)
                        val first = reader.readLine()
                        if (first != null) {
                            check(first.length < 1_024 && first.startsWith("GET /"))
                            val path = first.split(' ')[1].substringBefore('?').removePrefix("/")
                            check(path.matches(Regex("[a-zA-Z0-9-]*")))
                            var headerBytes = first.length
                            while (true) {
                                val line = reader.readLine() ?: break
                                headerBytes += line.length
                                check(headerBytes < 8_192)
                                if (line.isEmpty()) break
                            }
                            requests.add(path)
                            val body = document(path).toByteArray(Charsets.UTF_8)
                            client.getOutputStream().apply {
                                write(("HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n" +
                                    "Content-Length: ${body.size}\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n")
                                    .toByteArray(Charsets.US_ASCII))
                                write(body); flush()
                            }
                        }
                    }
                    active.compareAndSet(connection, null)
                }
            } catch (error: Throwable) { if (!socket.isClosed) failure.set(error) }
        }, "NativeCmpKit-owned-popup-HTTP").apply { isDaemon = true; start() }

        fun url(path: String) = "http://127.0.0.1:${socket.localPort}/$path"

        private fun document(path: String): String {
            val destination = url("target-$path")
            return """<!doctype html><html><head><title>$path</title>
                <meta name="viewport" content="width=device-width,initial-scale=1">
                <link rel="icon" href="data:,">
                <style>html,body{margin:0;width:100%;height:100%}a{position:fixed;inset:0;display:block}</style></head>
                <body><a id="go" href="$destination" target="_blank">Actual native popup input</a><script>
                window.fixtureClicks=0; window.fixtureActivated=false; window.fixtureHistoryMode=false;
                document.getElementById('go').addEventListener('click',function(e){
                  window.fixtureClicks++; window.fixtureActivated=navigator.userActivation.isActive;
                  if(window.fixtureHistoryMode){e.preventDefault();history.pushState(null,'','#first');history.pushState(null,'','#second');}
                  else if(${path.startsWith("user-script-")}){e.preventDefault();window.open(this.href,'_blank');}
                });
                if(${path.startsWith("auto-")}){window.fixtureScriptAttempted=true;window.open('$destination','_blank');}
                </script></body></html>""".trimIndent()
        }

        override fun close() {
            socket.close()
            active.getAndSet(null)?.close()
            worker.join(5_000)
            assertFalse(worker.isAlive, "Only this owned HTTP worker must terminate")
            failure.get()?.let { throw AssertionError("Owned HTTP fixture failed", it) }
        }
    }
}
