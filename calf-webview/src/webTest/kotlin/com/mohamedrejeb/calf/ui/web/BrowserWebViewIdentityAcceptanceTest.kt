// SPDX-License-Identifier: Apache-2.0
// Test-only owning disposal handle, following the accepted ComposeViewport fixture.
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
import kotlin.test.*

/** Public Compose/DOM and real host-controlled iframe documents on both JS and Wasm. */
class BrowserWebViewIdentityAcceptanceTest {
    @Test fun publicCreationReplacementAndRetainedRemountUseOnlyTheCurrentIframeOwner() = runTest {
        withContext(Dispatchers.Default) {
            val first = state("owner-a")
            val second = state("owner-b")
            var currentState by mutableStateOf(first)
            var currentNavigator by mutableStateOf(WebViewNavigator(this))
            var generation by mutableStateOf("a")
            var mounted by mutableStateOf(true)
            var observedGeneration: String? = null
            val created = mutableListOf<Pair<String, HTMLIFrameElement>>()
            val disposed = mutableListOf<String>()
            val viewport = Viewport {
                val owner = currentState
                val callbackGeneration = generation
                if (mounted) WebView(owner, Modifier.size(120.dp), navigator = currentNavigator,
                    onCreated = {
                        val frame = assertNotNull(owner.iframe)
                        assertNotNull(owner.owner)
                        assertFalse(frame.hasAttribute("sandbox"), "Common trusted/script configuration precedes the hook")
                        assertTrue(created.none { it.second === frame })
                        frame.setAttribute("referrerpolicy", "no-referrer") // Native customization not owned by common settings.
                        frame.setAttribute("sandbox", "allow-same-origin allow-forms") // Common settings intentionally own sandbox.
                        created += callbackGeneration to frame
                    }, onDispose = { assertNotNull(owner.iframe); disposed += callbackGeneration })
                SideEffect { observedGeneration = callbackGeneration }
            }
            try {
                val oldFrame = awaitDocument(first, "owner-a")
                assertSame(created.single().second, oldFrame)
                assertEquals("no-referrer", oldFrame.getAttribute("referrerpolicy"))
                assertFalse(oldFrame.hasAttribute("sandbox"), "A later content load intentionally reapplies common sandbox policy")
                first.settings.javaScriptEnabled = false
                assertEquals("allow-same-origin allow-forms", oldFrame.getAttribute("sandbox"))
                first.settings.javaScriptEnabled = true
                assertFalse(oldFrame.hasAttribute("sandbox"))
                val oldNavigator = currentNavigator
                val replacement = WebViewNavigator(this)
                generation = "latest-a"; currentNavigator = replacement
                awaitCondition { observedGeneration == "latest-a" }
                assertSame(oldFrame, first.iframe)
                assertEquals(listOf("a"), created.map { it.first })
                assertTrue(disposed.isEmpty())
                replacement.loadHtml(html("current-navigation"))
                awaitDocument(first, "current-navigation")
                oldNavigator.loadHtml(html("must-not-load"))
                delay(50) // Real browser turns; old navigator has no current consumer.
                assertEquals(JavascriptResult.Value("\"current-navigation\""), evaluate(first, "document.title"))
                currentState = second
                val secondFrame = awaitDocument(second, "owner-b")
                awaitCondition { first.iframe == null && !oldFrame.isConnected }
                assertNull(first.owner)
                assertNotSame(oldFrame, secondFrame)
                assertEquals(listOf("latest-a"), disposed)
                assertEquals(listOf("a", "latest-a"), created.map { it.first })
                generation = "latest-b"
                awaitCondition { observedGeneration == "latest-b" }
                mounted = false
                awaitCondition { second.iframe == null && !secondFrame.isConnected }
                assertNull(second.owner)
                assertEquals(listOf("latest-a", "latest-b"), disposed)
                mounted = true
                val remounted = awaitDocument(second, "owner-b")
                assertNotSame(oldFrame, remounted)
                assertNotSame(secondFrame, remounted)
                assertSame(created.last().second, remounted)
                assertEquals(listOf("a", "latest-a", "latest-b"), created.map { it.first })
                assertEquals("no-referrer", remounted.getAttribute("referrerpolicy"))
                viewport.close()
                awaitCondition { second.iframe == null && !remounted.isConnected }
                assertEquals(listOf("latest-a", "latest-b", "latest-b"), disposed)
                assertNull(second.owner)
            } finally { viewport.close() }
        }
    }

    @Test fun actualTrustedIframeTypedValuesAndCurrentOrDetachedCallbacksAreExactlyOnce() = runTest {
        withContext(Dispatchers.Default) {
            val owner = state("javascript")
            val navigator = WebViewNavigator(this)
            assertIs<JavascriptResult.Unavailable>(evaluate(owner, "1"))
            val viewport = Viewport { WebView(owner, Modifier.size(120.dp), navigator = navigator) }
            try {
                awaitDocument(owner, "javascript")
                for ((script, expected) in listOf(
                    "'NativeCmpKit'" to JavascriptResult.Value("\"NativeCmpKit\""),
                    "42" to JavascriptResult.Value("42"),
                    "({answer:42})" to JavascriptResult.Value("{\"answer\":42}"),
                    "null" to JavascriptResult.Value("null"),
                    "undefined" to JavascriptResult.Undefined,
                )) assertEquals(expected, evaluate(owner, script))
                val error = assertIs<JavascriptResult.Error>(evaluate(owner, "throw new Error('owned-script-error')"))
                assertTrue(error.message.contains("owned-script-error"))
                // The real synchronous browser callback must escape the evaluator's catch once,
                // not be converted into a second script failure. This does not mock window.eval.
                assertCallbackFailureEscapesOnce(owner)
                owner.settings.javaScriptEnabled = false
                assertIs<JavascriptResult.Unavailable>(evaluate(owner, "1"))
                owner.settings.javaScriptEnabled = true
                owner.settings.browserSandboxPolicy = BrowserSandboxPolicy.Isolated
                assertIs<JavascriptResult.Unavailable>(evaluate(owner, "1"))
                owner.settings.browserSandboxPolicy = BrowserSandboxPolicy.Trusted
                assertEquals(JavascriptResult.Value("7"), evaluate(owner, "7"))
                val frame = assertNotNull(owner.iframe)
                viewport.close()
                awaitCondition { owner.iframe == null && !frame.isConnected }
                assertIs<JavascriptResult.Unavailable>(evaluate(owner, "1"))
                assertCallbackFailureEscapesOnce(owner)
            } finally { viewport.close() }
            // Web is single-threaded: no Android/Apple/FX off-main claim or other-engine/network certification.
        }
    }

    private fun evaluate(owner: WebViewState, script: String): JavascriptResult {
        var result: JavascriptResult? = null
        var calls = 0
        owner.evaluateJavascriptResult(script) { assertEquals(0, calls++); result = it }
        assertEquals(1, calls, "Every invocation uses its own current callback exactly once")
        return assertNotNull(result)
    }

    private fun assertCallbackFailureEscapesOnce(owner: WebViewState) {
        val expected = OwnedCallbackFailure()
        var calls = 0
        val actual = assertFailsWith<OwnedCallbackFailure> { owner.evaluateJavascriptResult("1") { calls++; throw expected } }
        assertSame(expected, actual)
        assertEquals(1, calls)
    }

    private suspend fun awaitDocument(owner: WebViewState, title: String): HTMLIFrameElement {
        awaitCondition {
            val frame = owner.iframe
            frame != null && frame.isConnected && frame.contentDocument?.title == title &&
                owner.pageTitle == title && owner.loadingState == LoadingState.Finished
        }
        assertEquals(JavascriptResult.Value("\"$title\""), evaluate(owner, "document.title"))
        return assertNotNull(owner.iframe)
    }
    private suspend fun awaitCondition(check: () -> Boolean) = withTimeout(15_000) { while (!check()) delay(10) }
    private fun state(title: String) = WebViewState(WebContent.Data(html(title))).apply {
        settings.browserSandboxPolicy = BrowserSandboxPolicy.Trusted
        settings.javaScriptEnabled = true
    }
    private fun html(title: String) = "<!doctype html><title>$title</title><p>$title</p>"
    private class OwnedCallbackFailure : IllegalStateException("Controlled browser application callback failure")

    /** Same actual ComposeViewport lifetime API as the accepted library composition tests. */
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
