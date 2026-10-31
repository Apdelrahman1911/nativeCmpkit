// SPDX-License-Identifier: Apache-2.0
@file:Suppress("INVISIBLE_MEMBER", "INVISIBLE_REFERENCE")
@file:OptIn(androidx.compose.ui.ExperimentalComposeUiApi::class)

package com.mohamedrejeb.calf.ui.web

import androidx.compose.foundation.layout.size
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.ComposeViewport
import androidx.compose.ui.window.LocalComposeWindow
import kotlinx.browser.document
import kotlinx.browser.window
import kotlinx.coroutines.*
import kotlinx.coroutines.test.runTest
import org.w3c.dom.HTMLIFrameElement
import org.w3c.dom.HTMLElement
import org.w3c.dom.MessageEvent
import kotlin.random.Random
import kotlin.test.*

/** Real public Compose/DOM loads. Framing responses come from the owned Karma HTTP server. */
class BrowserWebViewContentAcceptanceTest {
    @Test fun directAndRememberedContentTransitionsMatchNavigatorAttributesAndDocuments() = runTest {
        withContext(Dispatchers.Default) {
            withFixture { fixture ->
                for (urlFactory in listOf(true, false)) {
                    var rememberedUrl by mutableStateOf(fixture.url("allow", "initial-url"))
                    var rememberedHtml by mutableStateOf(html("initial-data"))
                    var observed: WebViewState? = null
                    var created = 0
                    var disposed = 0
                    val navigator = WebViewNavigator(this)
                    val viewport = Viewport {
                        val owner = if (urlFactory) rememberWebViewState(rememberedUrl)
                            else rememberWebViewStateWithHTMLData(rememberedHtml)
                        owner.settings.browserSandboxPolicy = BrowserSandboxPolicy.Trusted
                        owner.settings.javaScriptEnabled = true
                        SideEffect { observed = owner }
                        WebView(owner, Modifier.size(160.dp), navigator = navigator,
                            onCreated = { created++ }, onDispose = { disposed++ })
                    }
                    var primary: Throwable? = null
                    try {
                        awaitCondition { observed != null }
                        val owner = assertNotNull(observed)
                        val frame = awaitDocument(owner, if (urlFactory) "initial-url" else "initial-data")
                        owner.content = WebContent.Data(html("direct-data"))
                        assertSame(frame, awaitDocument(owner, "direct-data"))
                        assertFalse(frame.hasAttribute("src"))
                        assertTrue(frame.hasAttribute("srcdoc"))

                        val sharedUrl = fixture.url("allow", "shared-url")
                        owner.content = WebContent.Url(sharedUrl)
                        awaitDocument(owner, "shared-url")
                        assertFalse(frame.hasAttribute("srcdoc"))
                        assertEquals(sharedUrl, frame.getAttribute("src"))
                        val stateUrl = snapshot(frame)
                        owner.content = WebContent.Data(html("shared-data"))
                        awaitDocument(owner, "shared-data")
                        val stateData = snapshot(frame)
                        navigator.loadUrl(sharedUrl)
                        awaitDocument(owner, "shared-url")
                        assertEquals(stateUrl, snapshot(frame), "Compare the actual page and attributes, not src alone")
                        navigator.loadHtml(html("shared-data"))
                        awaitDocument(owner, "shared-data")
                        assertEquals(stateData, snapshot(frame))

                        if (urlFactory) {
                            rememberedUrl = fixture.url("allow", "remembered-url")
                            awaitDocument(owner, "remembered-url")
                            assertFalse(frame.hasAttribute("srcdoc"))
                            owner.content = WebContent.Data(html("remembered-back-data"))
                            awaitDocument(owner, "remembered-back-data")
                        } else {
                            owner.content = WebContent.Url(fixture.url("allow", "remembered-out-url"))
                            awaitDocument(owner, "remembered-out-url")
                            rememberedHtml = html("remembered-back-data")
                            awaitDocument(owner, "remembered-back-data")
                            owner.content = WebContent.Url(fixture.url("allow", "remembered-out-again"))
                            awaitDocument(owner, "remembered-out-again")
                            rememberedHtml = html("remembered-final-data")
                            awaitDocument(owner, "remembered-final-data")
                        }
                        assertSame(owner, observed)
                        assertSame(frame, owner.iframe)
                        assertFalse(frame.hasAttribute("src"))
                        assertEquals(1, created)
                        assertEquals(0, disposed)
                        viewport.close()
                        awaitCondition { owner.iframe == null && !frame.isConnected }
                        assertEquals(1, disposed)
                    } catch (error: Throwable) { primary = error; throw error }
                    finally { runWebViewCleanup(primary, { viewport.close() }) }
                }
            }
        }
    }

    @Test fun realCrossOriginCspAndFrameOptionsRefusalsCannotRetainOrReportTheOldDocument() = runTest {
        withContext(Dispatchers.Default) {
            withFixture { fixture ->
                val owner = WebViewState(WebContent.Data(html("initial"))).apply {
                    settings.browserSandboxPolicy = BrowserSandboxPolicy.Trusted
                    settings.javaScriptEnabled = true
                }
                val navigator = WebViewNavigator(this)
                val viewport = Viewport { WebView(owner, Modifier.size(160.dp), navigator = navigator) }
                var frame: HTMLIFrameElement? = null
                var loads = 0
                val messages = mutableListOf<String>()
                val loadListener = browserEventListener { event ->
                    assertTrue(event.isTrusted, "Only a native browser load can finish the framing request")
                    loads++
                }
                val messageListener = browserEventListener { event ->
                    val message = event as? MessageEvent ?: return@browserEventListener
                    if (message.source === frame?.contentWindow && message.origin == fixture.crossOrigin) {
                        assertTrue(message.isTrusted, "Do not accept dispatched security-witness messages")
                        messages += message.data.toString()
                    }
                }
                var primary: Throwable? = null
                try {
                    frame = awaitDocument(owner, "initial")
                    val native = assertNotNull(frame)
                    native.addEventListener("load", loadListener)
                    window.addEventListener("message", messageListener)
                    // An unblocked page at the exact second origin must execute before testing refusal.
                    val positive = fixture.url("allow", "cross-origin-control", crossOrigin = true)
                    owner.content = WebContent.Url(positive)
                    awaitCondition { messages.contains("page|${fixture.token}|cross-origin-control") &&
                        owner.loadingState == LoadingState.Finished }
                    assertFalse(native.hasAttribute("srcdoc"))
                    val positiveReceipt = fixture.receipt()
                    assertEquals(listOf("1", "0", "0"), positiveReceipt.subList(2, 5))

                    for (mode in listOf("csp", "xfo")) {
                        val oldTitle = "old-$mode"
                        owner.content = WebContent.Data(html(oldTitle))
                        awaitDocument(owner, oldTitle)
                        val oldUrl = assertNotNull(owner.lastLoadedUrl)
                        assertEquals(oldTitle, owner.pageTitle)
                        assertEquals(oldTitle, native.contentDocument?.title)
                        val before = loads
                        val target = fixture.url(mode, "blocked-$mode", crossOrigin = true)
                        if (mode == "csp") owner.content = WebContent.Url(target) else navigator.loadUrl(target)
                        awaitCondition { owner.requestedUrl == target && loads > before &&
                            owner.loadingState == LoadingState.Finished && native.contentDocument == null }
                        val receipt = fixture.receipt()
                        assertEquals(1, receipt[if (mode == "csp") 3 else 4].toInt(), "The browser actually requested the refused page")
                        assertEquals("frame-ancestors 'none'", receipt[5], "Receipt records the actual emitted CSP response header")
                        if (mode == "xfo") assertEquals("DENY", receipt[6], "Receipt records the actual emitted XFO header")
                        assertFalse(native.hasAttribute("srcdoc"))
                        assertEquals(target, native.getAttribute("src"))
                        assertNull(native.contentDocument, "The old readable document is gone; a pending about:blank load is not a refusal witness")
                        assertTrue(owner.pageTitle.isNullOrEmpty(), "A refusal must not preserve a previous title or report the target page title")
                        assertNotEquals(oldUrl, owner.lastLoadedUrl)
                        assertNotEquals(target, owner.lastLoadedUrl, "Requested URL is not an observed successful destination")
                        assertFalse(messages.contains("page|${fixture.token}|blocked-$mode"))
                        owner.content = WebContent.Data(html("recovered-$mode"))
                        assertSame(native, awaitDocument(owner, "recovered-$mode"))
                        assertFalse(native.hasAttribute("src"))
                        fixture.receipt() // A real later browser round trip, not a sleep-based denial witness.
                        assertFalse(messages.contains("page|${fixture.token}|blocked-$mode"))
                    }
                    viewport.close()
                    awaitCondition { owner.iframe == null && !native.isConnected }
                } catch (error: Throwable) { primary = error; throw error }
                finally { runWebViewCleanup(primary, { viewport.close() },
                    { frame?.removeEventListener("load", loadListener) },
                    { window.removeEventListener("message", messageListener) }) }
            }
        }
    }

    private suspend fun withFixture(block: suspend (Fixture) -> Unit) {
        val fixture = Fixture()
        var primary: Throwable? = null
        try { block(fixture) } catch (error: Throwable) { primary = error; throw error }
        finally { withContext(NonCancellable) {
            try { fixture.close() } catch (cleanup: Throwable) {
                val error = primary
                if (error == null) throw cleanup
                if (error !== cleanup) error.addSuppressed(cleanup)
            }
        } }
    }

    private fun html(stage: String) = "<!doctype html><title>$stage</title><p id='nativecmpkit-page'>$stage</p>" +
        "<script>document.documentElement.setAttribute('data-nativecmpkit-ready','yes')</script>"
    private fun snapshot(frame: HTMLIFrameElement) =
        (0 until frame.attributes.length).map { index ->
            val attribute = assertNotNull(frame.attributes.item(index))
            attribute.name to attribute.value
        }.sortedBy { it.first } to listOf(frame.contentDocument?.title,
            frame.contentDocument?.getElementById("nativecmpkit-page")?.textContent)
    private suspend fun awaitDocument(owner: WebViewState, stage: String): HTMLIFrameElement {
        awaitCondition {
            try {
                val frame = owner.iframe
                frame != null && frame.isConnected && frame.contentDocument?.title == stage &&
                    frame.contentDocument?.documentElement?.getAttribute("data-nativecmpkit-ready") == "yes" &&
                    frame.contentDocument?.getElementById("nativecmpkit-page")?.textContent == stage &&
                    owner.pageTitle == stage && owner.loadingState == LoadingState.Finished
            } catch (_: Throwable) { false } // The preceding cross-origin page can still be committed.
        }
        return assertNotNull(owner.iframe)
    }
    private suspend fun awaitCondition(check: () -> Boolean) = withTimeout(15_000) { while (!check()) delay(10) }

    private class Fixture {
        val token = "nck" + Random.nextInt(1_000_000_000).toString()
        val crossOrigin: String
        init {
            check(window.location.protocol == "http:") { "Use Karma's owned HTTP fixture origin" }
            val host = when (window.location.hostname) {
                "localhost" -> "127.0.0.1"
                "127.0.0.1" -> "localhost"
                else -> error("No guessed or external fixture origin")
            }
            check(window.location.port.isNotEmpty())
            crossOrigin = "http://$host:${window.location.port}"
            check(crossOrigin != window.location.origin)
        }
        fun url(action: String, stage: String, crossOrigin: Boolean = false) =
            "${if (crossOrigin) this.crossOrigin else window.location.origin}/nativecmpkit-iframe-fixture/$action?token=$token&stage=$stage"
        suspend fun receipt(): List<String> = roundTrip("receipt").split('|').also {
            assertEquals(7, it.size); assertEquals("receipt", it[0]); assertEquals(token, it[1])
        }
        suspend fun close() { assertEquals("closed|$token", roundTrip("close")) }
        private suspend fun roundTrip(action: String): String {
            val native = (document.createElement("iframe") as HTMLIFrameElement).apply { style.display = "none" }
            val received = CompletableDeferred<String>()
            val listener = browserEventListener { event ->
                val message = event as? MessageEvent ?: return@browserEventListener
                if (message.source === native.contentWindow && message.origin == window.location.origin) {
                    if (message.isTrusted) received.complete(message.data.toString())
                    else received.completeExceptionally(AssertionError("Synthetic fixture receipt"))
                }
            }
            window.addEventListener("message", listener)
            var primary: Throwable? = null
            try {
                native.src = url(action, "receipt")
                document.body!!.appendChild(native)
                return withTimeout(15_000) { received.await() }
            } catch (error: Throwable) { primary = error; throw error }
            finally { runWebViewCleanup(primary,
                { window.removeEventListener("message", listener) }, { native.remove() }) }
        }
    }

    /** Uses the same actual ComposeViewport disposal handle as the accepted identity fixtures. */
    private class Viewport(content: @Composable () -> Unit) {
        private val container = (document.createElement("div") as HTMLElement).apply {
            style.width = "320px"; style.height = "240px"
        }
        private var releaseWindow: (() -> Unit)? = null
        private var closed = false
        init {
            try {
                document.body!!.appendChild(container)
                ComposeViewport(container) {
                    val composeWindow = checkNotNull(LocalComposeWindow.current)
                    SideEffect {
                        releaseWindow = { composeWindow.dispose() }
                        if (closed) window.setTimeout({ releaseOnce(); null }, 0)
                    }
                    if (!closed) content()
                }
            } catch (error: Throwable) {
                try { close() } catch (cleanup: Throwable) { if (cleanup !== error) error.addSuppressed(cleanup) }
                throw error
            }
        }
        private fun releaseOnce() { val release = releaseWindow ?: return; releaseWindow = null; release() }
        fun close() { closed = true; try { releaseOnce() } finally { container.remove() } }
    }
}
