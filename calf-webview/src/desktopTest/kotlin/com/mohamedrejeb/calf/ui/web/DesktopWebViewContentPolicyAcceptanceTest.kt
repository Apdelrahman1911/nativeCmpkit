// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import androidx.compose.runtime.saveable.SaverScope
import javafx.concurrent.Worker
import kotlinx.coroutines.*
import kotlin.test.*

/** Only NEW #66/#73 criteria: real Compose/JavaFX documents, public savers/loaders and actual wire counts. */
class DesktopWebViewContentPolicyAcceptanceTest {
    @Test fun savedRemainingStatesRemountWithoutBlankTitleOrFalseHistory() = runBlocking<Unit> {
        OwnedWebViewContentPolicyHttpFixture.create("restore").use { fixture ->
            for (row in listOf("url", "html", "navigator", "redirect", "null")) {
                val state = policyState(WebContent.NavigatorOnly)
                var saved: Any? = null
                withWindow(state) { host ->
                    when (row) {
                        "url", "redirect" -> { state.content = WebContent.Url(fixture.url(row)); awaitDocument(host, fixture, if (row == "redirect") "final" else row, 1) }
                        "navigator" -> { host.navigator.loadUrl(fixture.url(row)); awaitDocument(host, fixture, row, 1) }
                        "html" -> { state.content = WebContent.Data(OwnedWebViewContentPolicyHttpFixture.inline("restore-inline")); awaitInline(host, "restore-inline") }
                        "null" -> assertBlank(host)
                    }
                    saved = onFxThread { save(state) }
                }
                val restored = policyState(assertNotNull(WebStateSaver.restore(assertNotNull(saved))))
                assertNotSame(state, restored)
                assertNull(restored.pageTitle); assertNull(restored.lastLoadedUrl)
                withWindow(restored) { host ->
                    when (row) {
                        "url", "navigator", "redirect" -> {
                            val target = if (row == "redirect") "final" else row
                            awaitDocument(host, fixture, target, 2)
                            onFxThread {
                                assertEquals(fixture.url(target), restored.lastLoadedUrl)
                                assertEquals(0, assertNotNull(restored.webView).engine.history.currentIndex)
                                assertFalse(host.navigator.canGoBack); assertFalse(host.navigator.canGoForward)
                            }
                        }
                        else -> {
                            assertEquals(WebContent.NavigatorOnly, restored.content)
                            assertBlank(host) // Deliberately discarded HTML/null URL is not a restored document.
                            val stage = if (row == "html") "html-recovery" else "null-recovery"
                            host.navigator.loadUrl(fixture.url(stage)); awaitDocument(host, fixture, stage, 1)
                        }
                    }
                }
            }
            exact(fixture, "url", "get" to 2, "page" to 2)
            exact(fixture, "navigator", "get" to 2, "page" to 2)
            exact(fixture, "redirect", "get" to 1, "redirect" to 1, "page" to 0)
            exact(fixture, "final", "get" to 2, "page" to 2)
            exact(fixture, "html-recovery", "get" to 1); exact(fixture, "null-recovery", "get" to 1)
            fixture.report()
        }
    }

    @Test fun documentedGetReplayAndNonSaveablePostOneTimeOptOutAreObserved() = runBlocking<Unit> {
        OwnedWebViewContentPolicyHttpFixture.create("replay").use { fixture ->
            val first = policyState(WebContent.Url(fixture.url("get")))
            var saved: Any? = null
            withWindow(first) { host -> awaitDocument(host, fixture, "get", 1); saved = onFxThread { save(first) } }
            val restored = policyState(assertNotNull(WebStateSaver.restore(assertNotNull(saved))))
            withWindow(restored) { host ->
                awaitDocument(host, fixture, "get", 2)
                assertEquals(WebContent.Url(fixture.url("get")), restored.content)
            }
            // Explicit opt-out: this ordinary state is never passed to WebStateSaver/rememberSaveable.
            val sensitive = policyState(WebContent.NavigatorOnly)
            withWindow(sensitive) { host ->
                host.navigator.loadUrl(fixture.url("one-time")); awaitDocument(host, fixture, "one-time", 1)
                host.navigator.loadUrl(fixture.url("form")); awaitDocument(host, fixture, "form", 1)
                assertEquals(JavascriptResult.Value("true"), host.evaluate("document.getElementById('policy-form').submit(); true"))
                awaitDocument(host, fixture, "posted", 1)
                exact(fixture, "posted", "get" to 0, "post" to 1, "page" to 1)
            }
            val fresh = policyState(WebContent.NavigatorOnly)
            withWindow(fresh) { host ->
                assertBlank(host)
                // A genuine later native document/HTTP round trip, not a timed absence or fabricated callback.
                host.navigator.loadUrl(fixture.url("safe")); awaitDocument(host, fixture, "safe", 1)
                exact(fixture, "one-time", "get" to 1, "post" to 0)
                exact(fixture, "posted", "get" to 0, "post" to 1)
                assertFalse(host.navigator.canGoBack); assertFalse(host.navigator.canGoForward)
            }
            exact(fixture, "get", "get" to 2, "page" to 2)
            exact(fixture, "form", "get" to 1, "post" to 0); exact(fixture, "safe", "get" to 1)
            fixture.report()
        }
    }

    @Test fun unsupportedHeadersAndBaseUrlRefuseBeforeNetworkForBothEntryPoints() = runBlocking<Unit> {
        OwnedWebViewContentPolicyHttpFixture.create("unsupported").use { fixture ->
            val state = policyState(WebContent.Url(fixture.url("seed")))
            withWindow(state) { host ->
                awaitDocument(host, fixture, "seed", 1)
                val native = onFxThread { assertNotNull(state.webView) }
                val oldDocument = host.evaluate("document.documentElement.outerHTML")
                for (entry in listOf("state", "navigator")) {
                    val url = fixture.url("$entry-headers")
                    if (entry == "state") state.content = WebContent.Url(url, fixture.initialHeaders)
                    else host.navigator.loadUrl(url, fixture.initialHeaders)
                    awaitRejected(host, "additionalHttpHeaders")
                    assertEquals(oldDocument, host.evaluate("document.documentElement.outerHTML"))
                    exact(fixture, "$entry-headers", "get" to 0)
                    val base = fixture.baseUrl("$entry-base")
                    val html = OwnedWebViewContentPolicyHttpFixture.inline("must-not-load", base)
                    if (entry == "state") state.content = WebContent.Data(html, baseUrl = base)
                    else host.navigator.loadHtml(html, baseUrl = base)
                    awaitRejected(host, "baseUrl")
                    assertEquals(oldDocument, host.evaluate("document.documentElement.outerHTML"))
                    exact(fixture, "$entry-base", "get" to 0, "script" to 0, "style" to 0, "image" to 0)
                    onFxThread { assertSame(native, state.webView) }
                }
                // Supported plain inline Unicode stays honest too; no base URL/resource support is claimed.
                val inlineTitles = mutableListOf<String>()
                for (entry in listOf("state", "navigator")) for (encoding in listOf("utf-8", "utf8", "UTF-8", "UTF8")) {
                    val title = "supported-$entry-$encoding"
                    val historyBefore = onFxThread { native.engine.history.currentIndex to native.engine.history.entries.size }
                    val unicode = OwnedWebViewContentPolicyHttpFixture.unicode
                    val html = OwnedWebViewContentPolicyHttpFixture.inline(title) +
                        "<p id='policy-script'></p><p id='policy-attribute' data-unicode='$unicode'></p>" +
                        "<p id='policy-css'></p><style>#policy-css::after { content: '$unicode'; }</style>" +
                        "<script>document.getElementById('policy-script').textContent='$unicode';</script>"
                    if (entry == "state") state.content = WebContent.Data(html, encoding = encoding)
                    else host.navigator.loadHtml(html, encoding = encoding)
                    awaitInline(host, title)
                    assertEquals(JavascriptResult.Value(quoteJavascript(OwnedWebViewContentPolicyHttpFixture.unicode)),
                        host.evaluate("document.getElementById('policy-document').textContent"))
                    onFxThread { assertSame(native, state.webView); assertTrue(state.errorsForCurrentRequest.isEmpty()) }
                    assertInlineUnicodeContexts(host)
                    assertInlineMetadataAndHistory(host)
                    onFxThread {
                        // Do not hide the data URL's actual native history entry to imitate loadContent.
                        assertEquals(historyBefore.first + 1, native.engine.history.currentIndex)
                        assertEquals(historyBefore.second + 1, native.engine.history.entries.size)
                    }
                    inlineTitles += title
                }
                val inlineHistory = onFxThread { native.engine.history.currentIndex to native.engine.history.entries.size }
                // A real reload must replace the document marker, not merely observe the same old title.
                assertEquals(JavascriptResult.Value("true"), host.evaluate(
                    "document.getElementById('policy-document').setAttribute('data-before-reload','owned-marker'); true"))
                host.navigator.reload()
                host.awaitFx {
                    native.engine.loadWorker.state == Worker.State.SUCCEEDED &&
                        native.engine.document?.getElementById("policy-document")?.hasAttribute("data-before-reload") == false
                }
                awaitInline(host, inlineTitles.last())
                assertInlineUnicodeContexts(host); assertInlineMetadataAndHistory(host)
                onFxThread {
                    assertEquals(inlineHistory.first, native.engine.history.currentIndex)
                    assertEquals(inlineHistory.second, native.engine.history.entries.size)
                    // The explicit data-URL metadata path is intentionally private too, before native events.
                    val explicit = WebViewState(WebContent.NavigatorOnly)
                    assertTrue(explicit.acceptContent(WebContent.Url(native.engine.location), WebContentPlatform.Desktop))
                    assertNull(explicit.requestedUrl); assertNull(explicit.lastLoadedUrl)
                    assertEquals(WebContent.NavigatorOnly, assertNotNull(WebStateSaver.restore(save(explicit))).content)
                }
                // Visit only these eight actual inline entries, never replay the owned HTTP seed.
                // Every state/navigator alias is observed again through genuine native history.
                for (index in inlineTitles.lastIndex - 1 downTo 0) {
                    host.navigator.navigateBack(); awaitInline(host, inlineTitles[index])
                    assertInlineUnicodeContexts(host); assertInlineMetadataAndHistory(host)
                    onFxThread {
                        assertEquals(inlineHistory.first - (inlineTitles.lastIndex - index), native.engine.history.currentIndex)
                        assertEquals(inlineHistory.second, native.engine.history.entries.size)
                    }
                }
                for (index in 1..inlineTitles.lastIndex) {
                    host.navigator.navigateForward(); awaitInline(host, inlineTitles[index])
                    assertInlineUnicodeContexts(host); assertInlineMetadataAndHistory(host)
                    onFxThread {
                        assertEquals(inlineHistory.first - (inlineTitles.lastIndex - index), native.engine.history.currentIndex)
                        assertEquals(inlineHistory.second, native.engine.history.entries.size)
                    }
                }
                host.navigator.loadUrl(fixture.url("recovery")); awaitDocument(host, fixture, "recovery", 1)
            }
            exact(fixture, "seed", "get" to 1); exact(fixture, "recovery", "get" to 1)
            fixture.report()
        }
    }

    private fun policyState(content: WebContent) = policyState(WebViewState(content))
    private fun policyState(state: WebViewState) = state.apply { settings.javaScriptEnabled = true }
    private fun save(state: WebViewState): Any = assertNotNull(with(WebStateSaver) {
        object : SaverScope { override fun canBeSaved(value: Any) = true }.save(state)
    })
    private suspend fun assertInlineUnicodeContexts(host: DesktopContentPolicyWindow) {
        val expected = JavascriptResult.Value(quoteJavascript(OwnedWebViewContentPolicyHttpFixture.unicode))
        assertEquals(expected, host.evaluate("document.getElementById('policy-document').textContent"))
        assertEquals(expected, host.evaluate("document.getElementById('policy-script').textContent"))
        assertEquals(expected, host.evaluate("document.getElementById('policy-attribute').getAttribute('data-unicode')"))
        assertEquals(expected, host.evaluate("getComputedStyle(document.getElementById('policy-css'),'::after').content.slice(1,-1)"))
        val points = OwnedWebViewContentPolicyHttpFixture.unicode.codePoints().toArray().joinToString(",")
        assertEquals(JavascriptResult.Value(quoteJavascript(points)), host.evaluate(
            "Array.from(document.getElementById('policy-document').textContent).map(function(c){return c.codePointAt(0)}).join(',')"))
    }
    private suspend fun assertInlineMetadataAndHistory(host: DesktopContentPolicyWindow) {
        onFxThread {
            val state = host.state
            val engine = assertNotNull(state.webView).engine
            assertTrue(engine.location.startsWith("data:")) // Native-only source, not a public URL/save payload.
            assertNull(state.requestedUrl); assertNull(state.lastLoadedUrl); assertNull(state.urlForGetRestoration())
            val saved = save(state)
            val restored = assertNotNull(WebStateSaver.restore(saved))
            assertEquals(WebContent.NavigatorOnly, restored.content)
            assertNull(restored.requestedUrl); assertNull(restored.lastLoadedUrl)
            assertFalse(saved.toString().contains("data:", ignoreCase = true))
            assertFalse(saved.toString().contains(OwnedWebViewContentPolicyHttpFixture.unicode))
            assertEquals(engine.history.currentIndex > 0, host.navigator.canGoBack)
            assertEquals(engine.history.currentIndex < engine.history.entries.size - 1, host.navigator.canGoForward)
            assertEquals(LoadingState.Finished, state.loadingState)
            assertTrue(state.errorsForCurrentRequest.isEmpty())
        }
    }
    private suspend fun withWindow(state: WebViewState, block: suspend (DesktopContentPolicyWindow) -> Unit) {
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
        var host: DesktopContentPolicyWindow? = null
        var primary: Throwable? = null
        try {
            val own = DesktopContentPolicyWindow(state, WebViewNavigator(scope)).also { host = it }
            own.awaitCreated(); block(own)
        } catch (error: Throwable) { primary = error; throw error }
        finally { withContext(NonCancellable) { runWebViewCleanup(primary, { host?.close() }, { scope.cancel() }) } }
    }
    private suspend fun awaitDocument(host: DesktopContentPolicyWindow, fixture: OwnedWebViewContentPolicyHttpFixture, stage: String, count: Int) {
        host.awaitFx {
            val observed = fixture.stats(stage)
            val engine = host.state.webView?.engine
            observed.getValue("page") == count && observed.getValue("pending") == 0 &&
                engine?.loadWorker?.state == Worker.State.SUCCEEDED && engine.title == fixture.title(stage, observed) &&
                engine.location == fixture.url(stage) && host.state.lastLoadedUrl == fixture.url(stage) &&
                host.state.pageTitle == engine.title && host.state.loadingState == LoadingState.Finished
        }
        assertEquals(JavascriptResult.Value(quoteJavascript(fixture.title(stage))), host.evaluate("document.title"))
        assertEquals(JavascriptResult.Value(quoteJavascript(OwnedWebViewContentPolicyHttpFixture.unicode)),
            host.evaluate("document.getElementById('policy-document').textContent"))
        onFxThread { assertTrue(host.state.errorsForCurrentRequest.isEmpty()) }
    }
    private suspend fun awaitInline(host: DesktopContentPolicyWindow, title: String) {
        host.awaitFx { host.state.webView?.engine?.title == title && host.state.pageTitle == title && host.state.loadingState == LoadingState.Finished }
        assertEquals(JavascriptResult.Value(quoteJavascript(title)), host.evaluate("document.title"))
    }
    private suspend fun assertBlank(host: DesktopContentPolicyWindow) {
        host.awaitFx {
            val view = assertNotNull(host.state.webView)
            val engine = view.engine
            engine.title.isNullOrEmpty() && engine.location.isNullOrEmpty() &&
                (engine.document == null || engine.document.documentElement?.textContent.isNullOrEmpty()) &&
                host.state.pageTitle.isNullOrEmpty() && host.state.lastLoadedUrl.isNullOrEmpty()
        }
        onFxThread { assertFalse(host.navigator.canGoBack); assertFalse(host.navigator.canGoForward) }
    }
    private suspend fun awaitRejected(host: DesktopContentPolicyWindow, option: String) {
        host.awaitFx { host.state.errorsForCurrentRequest.singleOrNull()?.let { it.code == -2 && it.description.contains(option) } == true }
        onFxThread { assertEquals(LoadingState.Finished, host.state.loadingState); assertNull(host.state.pageTitle); assertNull(host.state.lastLoadedUrl) }
    }
    private fun exact(fixture: OwnedWebViewContentPolicyHttpFixture, stage: String, vararg expected: Pair<String, Int>) {
        val actual = fixture.stats(stage)
        expected.forEach { (key, value) -> assertEquals(value, actual.getValue(key), "Fixed owned stage=$stage counter=$key") }
        assertEquals(0, actual.getValue("pending")); assertEquals(0, actual.getValue("unexpected_initial")); assertEquals(0, actual.getValue("unexpected_authorization"))
    }
}
