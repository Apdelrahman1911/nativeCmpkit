// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)
package com.mohamedrejeb.calf.ui.web

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.saveable.SaverScope
import androidx.compose.ui.Modifier
import com.mohamedrejeb.calf.ui.web.internal.*
import kotlinx.coroutines.*
import platform.Foundation.NSThread
import kotlin.test.*

/** NEW actual library UIApplication/WKWebView content-policy criteria, not accepted request/lifecycle replay. */
class IosWebViewContentPolicyAcceptanceTest {
    @Test fun savedRemainingStatesRemountWithoutBlankTitleOrFalseHistory() = withFixture("restore") { fixture, scope ->
        for (row in listOf("url", "html", "navigator", "redirect", "null")) {
            val state = policyState(WebContent.NavigatorOnly)
            val navigator = WebViewNavigator(scope)
            var saved: Any? = null
            withMounted(state, navigator) {
                when (row) {
                    "url", "redirect" -> { runOnIdle { state.content = WebContent.Url(fixture.url(row)) }; awaitDocument(state, fixture, if (row == "redirect") "final" else row, 1) }
                    "navigator" -> { runOnIdle { navigator.loadUrl(fixture.url(row)) }; awaitDocument(state, fixture, row, 1) }
                    "html" -> { runOnIdle { state.content = WebContent.Data(IosContentPolicyFixture.inline("restore-inline")) }; awaitInline(state, "restore-inline") }
                    "null" -> assertBlank(state, navigator)
                }
                saved = runOnIdle { save(state) }
            }
            val restored = policyState(assertNotNull(WebStateSaver.restore(assertNotNull(saved))))
            assertNotSame(state, restored)
            assertNull(restored.pageTitle); assertNull(restored.lastLoadedUrl)
            val restoredNavigator = WebViewNavigator(scope)
            withMounted(restored, restoredNavigator) {
                when (row) {
                    "url", "navigator", "redirect" -> {
                        val stage = if (row == "redirect") "final" else row
                        awaitDocument(restored, fixture, stage, 2)
                        runOnIdle {
                            val native = assertNotNull(restored.webView)
                            assertEquals(fixture.url(stage), restored.lastLoadedUrl)
                            assertTrue(native.backForwardList.backList.isEmpty()); assertTrue(native.backForwardList.forwardList.isEmpty())
                            assertFalse(restoredNavigator.canGoBack); assertFalse(restoredNavigator.canGoForward)
                        }
                    }
                    else -> {
                        assertEquals(WebContent.NavigatorOnly, restored.content)
                        assertBlank(restored, restoredNavigator)
                        val stage = if (row == "html") "html-recovery" else "null-recovery"
                        runOnIdle { restoredNavigator.loadUrl(fixture.url(stage)) }; awaitDocument(restored, fixture, stage, 1)
                    }
                }
            }
        }
        exact(fixture, "url", "get" to 2, "page" to 2); exact(fixture, "navigator", "get" to 2, "page" to 2)
        exact(fixture, "redirect", "get" to 1, "redirect" to 1, "page" to 0); exact(fixture, "final", "get" to 2, "page" to 2)
        exact(fixture, "html-recovery", "get" to 1); exact(fixture, "null-recovery", "get" to 1)
    }

    @Test fun documentedGetReplayAndNonSaveablePostOneTimeOptOutAreObserved() = withFixture("replay") { fixture, scope ->
        val first = policyState(WebContent.Url(fixture.url("get"), fixture.initialHeaders))
        var saved: Any? = null
        withMounted(first, WebViewNavigator(scope)) { awaitDocument(first, fixture, "get", 1); saved = runOnIdle { save(first) } }
        val restored = policyState(assertNotNull(WebStateSaver.restore(assertNotNull(saved))))
        withMounted(restored, WebViewNavigator(scope)) { awaitDocument(restored, fixture, "get", 2) }
        // The documented ordinary/non-saveable opt-out is explicit: no saver ever sees these requests.
        val sensitive = policyState(WebContent.NavigatorOnly)
        val navigator = WebViewNavigator(scope)
        withMounted(sensitive, navigator) {
            runOnIdle { navigator.loadUrl(fixture.url("one-time")) }; awaitDocument(sensitive, fixture, "one-time", 1)
            runOnIdle { navigator.loadUrl(fixture.url("form")) }; awaitDocument(sensitive, fixture, "form", 1)
            assertEquals(JavascriptResult.Value("true"), evaluate(sensitive, "document.getElementById('policy-form').submit(); true"))
            awaitDocument(sensitive, fixture, "posted", 1)
            exact(fixture, "posted", "get" to 0, "post" to 1, "page" to 1)
        }
        val fresh = policyState(WebContent.NavigatorOnly)
        val explicit = WebViewNavigator(scope)
        withMounted(fresh, explicit) {
            assertBlank(fresh, explicit)
            runOnIdle { explicit.loadUrl(fixture.url("safe")) }; awaitDocument(fresh, fixture, "safe", 1)
            exact(fixture, "one-time", "get" to 1, "post" to 0); exact(fixture, "posted", "get" to 0, "post" to 1)
            runOnIdle { assertFalse(explicit.canGoBack); assertFalse(explicit.canGoForward) }
        }
        // Exactly one initial header-bearing load; the saved URL's second GET restores no headers.
        exact(fixture, "get", "get" to 2, "page" to 2, "main_initial" to 1, "main_authorization" to 1)
        exact(fixture, "form", "get" to 1); exact(fixture, "safe", "get" to 1)
    }

    @Test fun initialHeadersRedirectsAndSubresourcesMatchStateAndNavigatorPolicy() = withFixture("headers") { fixture, scope ->
        val state = policyState(WebContent.NavigatorOnly)
        val navigator = WebViewNavigator(scope)
        val observations = mutableMapOf<String, List<Int>>()
        withMounted(state, navigator) {
            for (entry in listOf("state", "navigator")) for (route in listOf("initial", "same", "cross")) {
                val request = "$entry-$route"
                runOnIdle {
                    if (entry == "state") state.content = WebContent.Url(fixture.url(request), fixture.initialHeaders)
                    else navigator.loadUrl(fixture.url(request), fixture.initialHeaders)
                }
                val terminal = if (route == "initial") request else "$request-final"
                val origin = if (route == "cross") 1 else 0
                awaitDocument(state, fixture, terminal, 1, origin); awaitResources(state, fixture, terminal)
                exact(fixture, request, "get" to if (route == "initial") 4 else 1, "main_initial" to 1, "main_authorization" to 1)
                observations["$entry-$route"] = headerFacts(fixture.stats(terminal))
                if (route == "cross") {
                    assertEquals(JavascriptResult.Value("true"), evaluate(state, "document.getElementById('policy-link').click(); true"))
                    val link = "$entry-link"
                    awaitDocument(state, fixture, link, 1, 1); awaitResources(state, fixture, link)
                    exact(fixture, link, "main_initial" to 0, "main_authorization" to 0)
                    observations["$entry-link"] = headerFacts(fixture.stats(link))
                }
            }
        }
        for (route in listOf("initial", "same", "cross", "link"))
            assertEquals(observations["state-$route"], observations["navigator-$route"], "Actual public entry-point wire policy differs for $route")
    }

    @Test fun relativeResourcesPreserveSupportedUnicodeEncoding() = withFixture("resources") { fixture, scope ->
        val state = policyState(WebContent.NavigatorOnly)
        val navigator = WebViewNavigator(scope)
        withMounted(state, navigator) {
            for (entry in listOf("state", "navigator")) for ((suffix, encoding) in listOf("utf8" to "utf-8", "utf8-alias" to "utf8")) {
                val stage = "$entry-$suffix"
                val title = "resources-$stage"
                val html = IosContentPolicyFixture.inline(title, relativeResources = true)
                runOnIdle {
                    if (entry == "state") state.content = WebContent.Data(html, baseUrl = fixture.baseUrl(stage), encoding = encoding)
                    else navigator.loadHtml(html, baseUrl = fixture.baseUrl(stage), encoding = encoding)
                }
                awaitInline(state, title); awaitResources(state, fixture, stage)
                exact(fixture, stage, "get" to 3, "page" to 0, "script" to 1, "style" to 1, "image" to 1)
            }
        }
    }

    private fun policyState(content: WebContent) = policyState(WebViewState(content))
    private fun policyState(state: WebViewState) = state.apply { settings.javaScriptEnabled = true }
    private fun save(state: WebViewState): Any = assertNotNull(with(WebStateSaver) {
        object : SaverScope { override fun canBeSaved(value: Any) = true }.save(state)
    })
    private fun withFixture(method: String, block: (IosContentPolicyFixture, CoroutineScope) -> Unit) {
        val fixture = IosContentPolicyFixture(method)
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
        var primary: Throwable? = null
        try { block(fixture, scope); fixture.complete() }
        catch (error: Throwable) { primary = error; throw error }
        finally { runWebViewCleanup(primary, { scope.cancel() }) }
    }
    private fun withMounted(state: WebViewState, navigator: WebViewNavigator, block: NativeApplicationUiTest.() -> Unit) {
        runApplicationUiTest { setContent { WebView(state, Modifier.fillMaxSize(), navigator = navigator) }; waitForIdle(); block() }
        onApplicationMain { assertNull(state.webView); assertNull(state.nativeObserver); assertNull(state.navigator) }
    }
    private fun NativeApplicationUiTest.awaitDocument(state: WebViewState, fixture: IosContentPolicyFixture, stage: String, count: Int, origin: Int = 0) {
        val observed = fixture.awaitStage(stage) { it.getValue("page") == count && it.getValue("pending") == 0 }
        val title = fixture.title(stage, observed)
        val url = fixture.url(stage, origin)
        waitForNative {
            val native = state.webView
            native != null && !native.loading && native.title == title && native.URL?.absoluteString == url &&
                state.pageTitle == title && state.lastLoadedUrl == url && state.loadingState == LoadingState.Finished &&
                sameNativeObject(native.window, requireOwnedApplicationWindow())
        }
        assertEquals(JavascriptResult.Value(quoteJavascript(title)), evaluate(state, "document.title"))
        assertEquals(JavascriptResult.Value(quoteJavascript(IosContentPolicyFixture.unicode)), evaluate(state, "document.getElementById('policy-document').textContent"))
        runOnIdle { assertTrue(state.errorsForCurrentRequest.isEmpty()) }
    }
    private fun NativeApplicationUiTest.awaitInline(state: WebViewState, title: String) {
        waitForNative { state.webView?.title == title && state.pageTitle == title && state.loadingState == LoadingState.Finished }
        assertEquals(JavascriptResult.Value(quoteJavascript(title)), evaluate(state, "document.title"))
        assertEquals(JavascriptResult.Value(quoteJavascript(IosContentPolicyFixture.unicode)), evaluate(state, "document.getElementById('policy-document').textContent"))
    }
    private fun NativeApplicationUiTest.assertBlank(state: WebViewState, navigator: WebViewNavigator) {
        runOnIdle {
            val native = assertNotNull(state.webView)
            assertTrue(native.URL == null || native.URL?.absoluteString == "about:blank"); assertTrue(native.title.isNullOrEmpty())
            assertTrue(state.pageTitle.isNullOrEmpty()); assertTrue(state.lastLoadedUrl.isNullOrEmpty())
            assertTrue(native.backForwardList.backList.isEmpty()); assertTrue(native.backForwardList.forwardList.isEmpty())
            assertFalse(navigator.canGoBack); assertFalse(navigator.canGoForward)
            assertTrue(sameNativeObject(native.window, requireOwnedApplicationWindow()))
        }
        assertEquals(JavascriptResult.Value("\"\""), evaluate(state, "document.title"))
    }
    private fun NativeApplicationUiTest.awaitResources(state: WebViewState, fixture: IosContentPolicyFixture, stage: String) {
        val observed = fixture.awaitStage(stage) { listOf("script", "style", "image").all { key -> it.getValue(key) == 1 } && it.getValue("pending") == 0 }
        assertEquals(JavascriptResult.Value(quoteJavascript(IosContentPolicyFixture.resourceUnicode)), evaluate(state, "document.getElementById('relative-resource-text').textContent"))
        assertEquals(JavascriptResult.Value("\"rgb(17, 34, 51)\""), evaluate(state, "getComputedStyle(document.getElementById('policy-document')).color"))
        assertEquals(JavascriptResult.Value("true"), evaluate(state, "document.getElementById('relative-image').complete && document.getElementById('relative-image').naturalWidth === 7 && document.getElementById('relative-image').naturalHeight === 9"))
        assertEquals(JavascriptResult.Value(quoteJavascript("h${observed.getValue("script_initial")}-a${observed.getValue("script_authorization")}")), evaluate(state, "document.documentElement.getAttribute('data-policy-script')"))
        exact(fixture, stage, "script_initial" to 0, "script_authorization" to 0, "style_initial" to 0, "style_authorization" to 0, "image_initial" to 0, "image_authorization" to 0)
    }
    private fun NativeApplicationUiTest.evaluate(state: WebViewState, script: String): JavascriptResult {
        assertFalse(NSThread.isMainThread)
        var result: JavascriptResult? = null
        var calls = 0
        var offMain = false
        state.evaluateJavascriptResult(script) { if (!NSThread.isMainThread) offMain = true; calls++; result = it }
        waitForNative { result != null || offMain }
        return onApplicationMain { assertFalse(offMain); assertEquals(1, calls); assertNotNull(result) }
    }
    private fun headerFacts(actual: Map<String, Int>) = listOf("main_initial", "main_authorization", "script_initial", "script_authorization", "style_initial", "style_authorization", "image_initial", "image_authorization").map {
        actual.getValue(it).also { value -> assertTrue(value in 0..1) }
    }
    private fun exact(fixture: IosContentPolicyFixture, stage: String, vararg expected: Pair<String, Int>) {
        val observed = fixture.stats(stage)
        expected.forEach { (key, value) -> assertEquals(value, observed.getValue(key), "Fixed owned stage=$stage counter=$key") }
        assertEquals(0, observed.getValue("pending")); assertEquals(0, observed.getValue("unexpected_initial")); assertEquals(0, observed.getValue("unexpected_authorization"))
    }
}
