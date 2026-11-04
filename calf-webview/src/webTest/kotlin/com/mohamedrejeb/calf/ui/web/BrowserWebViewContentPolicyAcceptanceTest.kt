// SPDX-License-Identifier: Apache-2.0
@file:OptIn(androidx.compose.ui.ExperimentalComposeUiApi::class)
package com.mohamedrejeb.calf.ui.web

import androidx.compose.foundation.layout.size
import androidx.compose.runtime.saveable.SaverScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.*
import kotlinx.coroutines.test.runTest
import kotlin.test.*

/** NEW public-library Compose/DOM and wire-count contracts, independently executed in JS and Wasm. */
class BrowserWebViewContentPolicyAcceptanceTest {
    @Test fun savedRemainingStatesRemountWithoutBlankTitleOrFalseHistory() = runTest {
        withContext(Dispatchers.Default) { withFixture("restore") { fixture ->
            for (row in listOf("url", "html", "navigator", "redirect", "null")) {
                val state = policyState(WebContent.NavigatorOnly)
                var saved: Any? = null
                withMounted(state) { navigator ->
                    when (row) {
                        "url", "redirect" -> { state.content = WebContent.Url(fixture.url(row)); awaitDocument(state, fixture, if (row == "redirect") "final" else row, 1) }
                        "navigator" -> { navigator.loadUrl(fixture.url(row)); awaitDocument(state, fixture, row, 1) }
                        "html" -> { state.content = WebContent.Data(BrowserContentPolicyFixture.inline("restore-inline")); awaitInline(state, "restore-inline") }
                        "null" -> assertBlank(state, navigator)
                    }
                    saved = save(state)
                }
                val restored = policyState(assertNotNull(WebStateSaver.restore(assertNotNull(saved))))
                assertNotSame(state, restored); assertNull(restored.pageTitle); assertNull(restored.lastLoadedUrl)
                withMounted(restored) { navigator ->
                    when (row) {
                        "url", "navigator", "redirect" -> {
                            val stage = if (row == "redirect") "final" else row
                            awaitDocument(restored, fixture, stage, 2)
                            assertEquals(fixture.url(stage), restored.lastLoadedUrl)
                            assertFalse(navigator.canGoBack); assertFalse(navigator.canGoForward) // Unavailable iframe history is never fabricated.
                        }
                        else -> {
                            assertEquals(WebContent.NavigatorOnly, restored.content)
                            assertBlank(restored, navigator)
                            val stage = if (row == "html") "html-recovery" else "null-recovery"
                            navigator.loadUrl(fixture.url(stage)); awaitDocument(restored, fixture, stage, 1)
                        }
                    }
                }
            }
            exact(fixture, "url", "get" to 2, "page" to 2); exact(fixture, "navigator", "get" to 2, "page" to 2)
            exact(fixture, "redirect", "get" to 1, "redirect" to 1, "page" to 0); exact(fixture, "final", "get" to 2, "page" to 2)
            exact(fixture, "html-recovery", "get" to 1); exact(fixture, "null-recovery", "get" to 1)
        } }
    }

    @Test fun documentedGetReplayAndNonSaveablePostOneTimeOptOutAreObserved() = runTest {
        withContext(Dispatchers.Default) { withFixture("replay") { fixture ->
            val first = policyState(WebContent.Url(fixture.url("get")))
            var saved: Any? = null
            withMounted(first) { awaitDocument(first, fixture, "get", 1); saved = save(first) }
            val restored = policyState(assertNotNull(WebStateSaver.restore(assertNotNull(saved))))
            withMounted(restored) { awaitDocument(restored, fixture, "get", 2) }
            // Deliberate documented non-saveable, explicit-navigator opt-out, not token recognition.
            val sensitive = policyState(WebContent.NavigatorOnly)
            withMounted(sensitive) { navigator ->
                navigator.loadUrl(fixture.url("one-time")); awaitDocument(sensitive, fixture, "one-time", 1)
                navigator.loadUrl(fixture.url("form")); awaitDocument(sensitive, fixture, "form", 1)
                assertEquals(JavascriptResult.Value("true"), evaluate(sensitive, "document.getElementById('policy-form').submit(); true"))
                awaitDocument(sensitive, fixture, "posted", 1)
                exact(fixture, "posted", "get" to 0, "post" to 1, "page" to 1)
            }
            val fresh = policyState(WebContent.NavigatorOnly)
            withMounted(fresh) { navigator ->
                assertBlank(fresh, navigator)
                navigator.loadUrl(fixture.url("safe")); awaitDocument(fresh, fixture, "safe", 1)
                exact(fixture, "one-time", "get" to 1, "post" to 0); exact(fixture, "posted", "get" to 0, "post" to 1)
                assertFalse(navigator.canGoBack); assertFalse(navigator.canGoForward)
            }
            exact(fixture, "get", "get" to 2, "page" to 2); exact(fixture, "form", "get" to 1); exact(fixture, "safe", "get" to 1)
        } }
    }

    @Test fun unsupportedHeadersAndBaseUrlRefuseBeforeNetworkForBothEntryPoints() = runTest {
        withContext(Dispatchers.Default) { withFixture("unsupported") { fixture ->
            val state = policyState(WebContent.Url(fixture.url("seed")))
            withMounted(state) { navigator ->
                awaitDocument(state, fixture, "seed", 1)
                val native = assertNotNull(state.iframe)
                val old = native.contentDocument?.documentElement?.outerHTML
                for (entry in listOf("state", "navigator")) {
                    val url = fixture.url("$entry-headers")
                    if (entry == "state") state.content = WebContent.Url(url, fixture.initialHeaders)
                    else navigator.loadUrl(url, fixture.initialHeaders)
                    awaitRejected(state, "additionalHttpHeaders")
                    assertEquals(old, native.contentDocument?.documentElement?.outerHTML)
                    exact(fixture, "$entry-headers", "get" to 0)
                    val base = fixture.baseUrl("$entry-base")
                    val html = BrowserContentPolicyFixture.inline("must-not-load", relativeResources = true)
                    if (entry == "state") state.content = WebContent.Data(html, baseUrl = base)
                    else navigator.loadHtml(html, baseUrl = base)
                    awaitRejected(state, "baseUrl")
                    assertEquals(old, native.contentDocument?.documentElement?.outerHTML)
                    exact(fixture, "$entry-base", "get" to 0, "script" to 0, "style" to 0, "image" to 0)
                    assertSame(native, state.iframe)
                }
                for (entry in listOf("state", "navigator")) for (encoding in listOf("utf-8", "utf8")) {
                    val title = "supported-$entry-$encoding"
                    val html = BrowserContentPolicyFixture.inline(title)
                    if (entry == "state") state.content = WebContent.Data(html, encoding = encoding)
                    else navigator.loadHtml(html, encoding = encoding)
                    awaitInline(state, title)
                    assertEquals(JavascriptResult.Value(quoteJavascript(BrowserContentPolicyFixture.unicode)), evaluate(state, "document.getElementById('policy-document').textContent"))
                    assertSame(native, state.iframe); assertTrue(state.errorsForCurrentRequest.isEmpty())
                }
                navigator.loadUrl(fixture.url("recovery")); awaitDocument(state, fixture, "recovery", 1)
            }
            exact(fixture, "seed", "get" to 1); exact(fixture, "recovery", "get" to 1)
        } }
    }

    private fun policyState(content: WebContent) = policyState(WebViewState(content))
    private fun policyState(state: WebViewState) = state.apply {
        settings.browserSandboxPolicy = BrowserSandboxPolicy.Trusted // Exclusively nonce-owned test documents.
        settings.javaScriptEnabled = true
    }
    private fun save(state: WebViewState): Any = assertNotNull(with(WebStateSaver) {
        object : SaverScope { override fun canBeSaved(value: Any) = true }.save(state)
    })
    private suspend fun withFixture(method: String, block: suspend (BrowserContentPolicyFixture) -> Unit) {
        val fixture = BrowserContentPolicyFixture(method)
        var primary: Throwable? = null
        try { fixture.open(); block(fixture); fixture.complete() }
        catch (error: Throwable) { primary = error; throw error }
        finally { withContext(NonCancellable) { preserve(primary) { fixture.close() } } }
    }
    private suspend fun withMounted(state: WebViewState, block: suspend (WebViewNavigator) -> Unit) = coroutineScope {
        val navigator = WebViewNavigator(this)
        val viewport = BrowserContentPolicyViewport { WebView(state, Modifier.size(180.dp), navigator = navigator) }
        var native = state.iframe
        var primary: Throwable? = null
        try {
            awaitCondition { state.iframe?.isConnected == true }; native = assertNotNull(state.iframe); block(navigator)
        } catch (error: Throwable) { primary = error; throw error }
        finally { withContext(NonCancellable) { preserve(primary) {
            viewport.close()
            awaitCondition { state.iframe == null && state.owner == null && native?.isConnected != true }
        } } }
    }
    private suspend fun preserve(primary: Throwable?, cleanup: suspend () -> Unit) {
        try { cleanup() } catch (error: Throwable) { if (primary == null) throw error else if (primary !== error) primary.addSuppressed(error) }
    }
    private suspend fun awaitCondition(predicate: () -> Boolean) = withTimeout(15_000) { while (!predicate()) delay(10) }
    private suspend fun awaitDocument(state: WebViewState, fixture: BrowserContentPolicyFixture, stage: String, count: Int) {
        val title = fixture.title(stage, count)
        awaitInline(state, title)
        val native = assertNotNull(state.iframe)
        assertEquals(fixture.url(stage), native.contentWindow?.location?.href); assertEquals(fixture.url(stage), state.lastLoadedUrl)
        exact(fixture, stage, "page" to count)
        assertTrue(state.errorsForCurrentRequest.isEmpty())
    }
    private suspend fun awaitInline(state: WebViewState, title: String) {
        awaitCondition {
            val native = state.iframe
            native?.isConnected == true && native.contentDocument?.title == title && state.pageTitle == title && state.loadingState == LoadingState.Finished
        }
        assertEquals(JavascriptResult.Value(quoteJavascript(title)), evaluate(state, "document.title"))
        assertEquals(JavascriptResult.Value(quoteJavascript(BrowserContentPolicyFixture.unicode)), evaluate(state, "document.getElementById('policy-document').textContent"))
    }
    private suspend fun assertBlank(state: WebViewState, navigator: WebViewNavigator) {
        awaitCondition {
            val native = state.iframe
            native?.isConnected == true && native.contentDocument?.title == "" && native.contentDocument?.body?.textContent.isNullOrEmpty() &&
                native.contentWindow?.location?.href == "about:blank" && state.pageTitle.isNullOrEmpty() &&
                (state.lastLoadedUrl == null || state.lastLoadedUrl == "about:blank")
        }
        assertFalse(navigator.canGoBack); assertFalse(navigator.canGoForward)
        assertEquals(JavascriptResult.Value("\"\""), evaluate(state, "document.title"))
    }
    private suspend fun awaitRejected(state: WebViewState, option: String) {
        awaitCondition { state.errorsForCurrentRequest.singleOrNull()?.let { it.code == -2 && it.description.contains(option) } == true }
        assertEquals(LoadingState.Finished, state.loadingState); assertNull(state.pageTitle); assertNull(state.lastLoadedUrl)
    }
    private fun evaluate(state: WebViewState, script: String): JavascriptResult {
        var result: JavascriptResult? = null
        var calls = 0
        state.evaluateJavascriptResult(script) { calls++; result = it }
        assertEquals(1, calls); return assertNotNull(result)
    }
    private suspend fun exact(fixture: BrowserContentPolicyFixture, stage: String, vararg expected: Pair<String, Int>) {
        var observed = fixture.stats(stage)
        withTimeout(10_000) { while (observed.getValue("pending") != 0) { delay(25); observed = fixture.stats(stage) } }
        expected.forEach { (key, value) -> assertEquals(value, observed.getValue(key), "Fixed owned stage=$stage counter=$key") }
        assertEquals(0, observed.getValue("unexpected_initial")); assertEquals(0, observed.getValue("unexpected_authorization"))
    }
}
