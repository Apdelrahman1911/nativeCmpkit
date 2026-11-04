// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import android.os.Build
import android.os.Parcel
import android.security.NetworkSecurityPolicy
import androidx.compose.runtime.saveable.SaverScope
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Test
import org.junit.runner.RunWith
import java.util.concurrent.atomic.AtomicReference
import kotlin.test.*

/** NEW actual API35 library content-policy criteria. Accepted ordinary URL restoration is excluded. */
@RunWith(AndroidJUnit4::class)
class AndroidWebViewContentPolicyAcceptanceTest {
    @Test fun savedRemainingStatesRemountWithoutBlankTitleOrFalseHistory() = withFixture("restore") { server ->
        for (row in listOf("html", "navigator", "redirect", "null")) {
            val state = policyState(WebContent.NavigatorOnly)
            var restored: WebViewState? = null
            withMounted(state) { fixture, host ->
                when (row) {
                    "html" -> { onMain { state.content = WebContent.Data(OwnedWebViewContentPolicyHttpFixture.inline("restore-inline")) }; awaitInline(state, "restore-inline") }
                    "navigator" -> { onMain { fixture.navigator.loadUrl(server.url(row)) }; awaitDocument(state, server, row, 1) }
                    "redirect" -> { onMain { state.content = WebContent.Url(server.url(row)) }; awaitDocument(state, server, "final", 1) }
                    "null" -> assertBlank(state, fixture.navigator)
                }
                restored = onMain { parcelRestore(state) }
                host.unmount(); host.assertResumed()
            }
            val current = policyState(assertNotNull(restored))
            assertNotSame(state, current)
            onMain { assertNull(current.pageTitle); assertNull(current.lastLoadedUrl) }
            withMounted(current) { fixture, _ ->
                assertMetadataMatchesRealDocument(current, fixture.navigator)
                when (row) {
                    "navigator", "redirect" -> {
                        val stage = if (row == "redirect") "final" else row
                        onMain {
                            val native = assertNotNull(current.webView)
                            assertEquals(server.url(stage), native.copyBackForwardList().currentItem?.url)
                            // Android preserves its actual native history Bundle; display data is not
                            // promised. Explicit supported Reload supplies an actual new document.
                            fixture.navigator.reload()
                        }
                        awaitDocument(current, server, stage, 2, allowNativeRestoreGet = true)
                        onMain {
                            val native = assertNotNull(current.webView)
                            assertEquals(native.canGoBack(), fixture.navigator.canGoBack)
                            assertEquals(native.canGoForward(), fixture.navigator.canGoForward)
                        }
                    }
                    "html" -> {
                        // Native history is not display/form persistence: reprovide the HTML explicitly.
                        onMain { fixture.navigator.loadHtml(OwnedWebViewContentPolicyHttpFixture.inline("restore-inline-explicit")) }
                        awaitInline(current, "restore-inline-explicit")
                        exact(server, "html-recovery", "get" to 0)
                    }
                    "null" -> {
                        assertBlank(current, fixture.navigator)
                        onMain { fixture.navigator.loadUrl(server.url("null-recovery")) }
                        awaitDocument(current, server, "null-recovery", 1)
                    }
                }
            }
        }
        exact(server, "url", "get" to 0) // Accepted plain-URL restore method is not repeated here.
        exact(server, "redirect", "get" to 1, "redirect" to 1, "page" to 0)
        exact(server, "null-recovery", "get" to 1)
    }

    @Test fun documentedGetReplayAndNonSaveablePostOneTimeOptOutAreObserved() = withFixture("replay") { server ->
        val first = policyState(WebContent.Url(server.url("get")))
        var restored: WebViewState? = null
        withMounted(first) { _, _ -> awaitDocument(first, server, "get", 1); restored = onMain { parcelRestore(first) } }
        val saved = policyState(assertNotNull(restored))
        withMounted(saved) { fixture, _ ->
            assertMetadataMatchesRealDocument(saved, fixture.navigator)
            onMain { assertEquals(server.url("get"), saved.webView?.copyBackForwardList()?.currentItem?.url); fixture.navigator.reload() }
            awaitDocument(saved, server, "get", 2, allowNativeRestoreGet = true)
        }
        // Ordinary non-saveable state; neither this one-time URL nor the real POST is ever saved.
        val sensitive = policyState(WebContent.NavigatorOnly)
        withMounted(sensitive) { fixture, _ ->
            onMain { fixture.navigator.loadUrl(server.url("one-time")) }; awaitDocument(sensitive, server, "one-time", 1)
            onMain { fixture.navigator.loadUrl(server.url("form")) }; awaitDocument(sensitive, server, "form", 1)
            assertEquals(JavascriptResult.Value("true"), evaluate(sensitive, "document.getElementById('policy-form').submit(); true"))
            awaitDocument(sensitive, server, "posted", 1)
            exact(server, "posted", "get" to 0, "post" to 1, "page" to 1)
        }
        val fresh = policyState(WebContent.NavigatorOnly)
        withMounted(fresh) { fixture, _ ->
            assertBlank(fresh, fixture.navigator)
            onMain { fixture.navigator.loadUrl(server.url("safe")) }; awaitDocument(fresh, server, "safe", 1)
            exact(server, "one-time", "get" to 1, "post" to 0)
            exact(server, "posted", "get" to 0, "post" to 1)
            onMain { assertFalse(fixture.navigator.canGoBack); assertFalse(fixture.navigator.canGoForward) }
        }
        exact(server, "form", "get" to 1, "post" to 0); exact(server, "safe", "get" to 1)
    }

    @Test fun initialHeadersRedirectsAndSubresourcesMatchStateAndNavigatorPolicy() = withFixture("headers") { server ->
        val state = policyState(WebContent.NavigatorOnly)
        val observations = mutableMapOf<String, List<Int>>()
        withMounted(state) { fixture, _ ->
            for (entry in listOf("state", "navigator")) {
                for (route in listOf("initial", "same", "cross")) {
                    val request = "$entry-$route"
                    onMain {
                        if (entry == "state") state.content = WebContent.Url(server.url(request), server.initialHeaders)
                        else fixture.navigator.loadUrl(server.url(request), server.initialHeaders)
                    }
                    val terminal = if (route == "initial") request else "$request-final"
                    val origin = if (route == "cross") 1 else 0
                    awaitDocument(state, server, terminal, 1, origin = origin)
                    awaitResources(state, server, terminal)
                    exact(server, request, "get" to if (route == "initial") 4 else 1, "main_initial" to 1, "main_authorization" to 1)
                    observations["$entry-$route"] = headerFacts(server.stats(terminal))
                    if (route == "cross") {
                        assertEquals(JavascriptResult.Value("true"), evaluate(state, "document.getElementById('policy-link').click(); true"))
                        val link = "$entry-link"
                        awaitDocument(state, server, link, 1, origin = 1); awaitResources(state, server, link)
                        exact(server, link, "main_initial" to 0, "main_authorization" to 0)
                        observations["$entry-link"] = headerFacts(server.stats(link))
                    }
                }
            }
        }
        for (route in listOf("initial", "same", "cross", "link")) {
            assertEquals(observations["state-$route"], observations["navigator-$route"], "Actual wire policy differs by public entry point for $route")
        }
    }

    @Test fun relativeResourcesPreserveSupportedUnicodeEncoding() = withFixture("resources") { server ->
        val state = policyState(WebContent.NavigatorOnly)
        withMounted(state) { fixture, _ ->
            for (entry in listOf("state", "navigator")) for ((suffix, encoding) in listOf("utf8" to "utf-8", "utf8-alias" to "utf8")) {
                val stage = "$entry-$suffix"
                val base = server.baseUrl(stage)
                val title = "resources-$stage"
                val html = OwnedWebViewContentPolicyHttpFixture.inline(title, base)
                onMain {
                    if (entry == "state") state.content = WebContent.Data(html, baseUrl = base, encoding = encoding)
                    else fixture.navigator.loadHtml(html, baseUrl = base, encoding = encoding)
                }
                awaitInline(state, title); awaitResources(state, server, stage)
                exact(server, stage, "get" to 3, "page" to 0, "script" to 1, "style" to 1, "image" to 1)
            }
        }
    }

    private fun policyState(content: WebContent) = policyState(WebViewState(content))
    private fun policyState(state: WebViewState) = state.apply { settings.javaScriptEnabled = true }
    private fun withFixture(method: String, block: (OwnedWebViewContentPolicyHttpFixture) -> Unit) {
        assertEquals(35, Build.VERSION.SDK_INT, "Finite native content-policy acceptance is API35 only")
        onMain {
            assertTrue(NetworkSecurityPolicy.getInstance().isCleartextTrafficPermitted("127.0.0.1"))
            assertFalse(NetworkSecurityPolicy.getInstance().isCleartextTrafficPermitted("localhost"))
        }
        OwnedWebViewContentPolicyHttpFixture.create(method).use { server -> block(server); server.report() }
    }
    private fun withMounted(state: WebViewState, block: (AndroidLifetimeFixture, ActivityLease) -> Unit) {
        val fixture = AndroidLifetimeFixture(state)
        var host: ActivityLease? = null
        var primary: Throwable? = null
        try {
            val own = ActivityLease(fixture).also { host = it }; own.awaitCreated(); block(fixture, own)
            if (fixture.disposed.get() == 0) { own.unmount(); own.assertResumed() }
        } catch (error: Throwable) { primary = error; throw error }
        finally { runWebViewCleanup(primary, { host?.close() }, { onMain { assertNull(state.webView) } }) }
    }
    private fun parcelRestore(state: WebViewState): WebViewState {
        val scope = object : SaverScope { override fun canBeSaved(value: Any) = true }
        val saved = assertNotNull(with(WebStateSaver) { scope.save(state) })
        val parcel = Parcel.obtain()
        val wire = try {
            parcel.writeValue(saved); assertTrue(parcel.dataSize() > 0); parcel.setDataPosition(0)
            @Suppress("DEPRECATION")
            assertNotNull(parcel.readValue(WebViewState::class.java.classLoader))
        } finally { parcel.recycle() }
        return assertNotNull(WebStateSaver.restore(wire)) // Parcelable/native history, not OS process death.
    }
    private fun evaluate(state: WebViewState, script: String): JavascriptResult {
        val result = AtomicReference<JavascriptResult?>()
        state.evaluateJavascriptResult(script) { result.set(it) }
        await("Genuine owned provider evaluation") { result.get() != null }
        return assertNotNull(result.get())
    }
    private fun awaitDocument(state: WebViewState, server: OwnedWebViewContentPolicyHttpFixture, stage: String,
                              minimum: Int, allowNativeRestoreGet: Boolean = false, origin: Int = 0) {
        await("Actual complete native document and wire generation") {
            val observed = server.stats(stage)
            val page = observed.getValue("page")
            val countMatches = if (allowNativeRestoreGet) page in minimum..(minimum + 1) else page == minimum
            countMatches && observed.getValue("pending") == 0 && onMain {
                val native = state.webView
                native?.isAttachedToWindow == true && native.title == server.title(stage, observed) && native.url == server.url(stage, origin) &&
                    state.lastLoadedUrl == native.url && state.pageTitle == native.title && state.loadingState == LoadingState.Finished
            }
        }
        assertEquals(JavascriptResult.Value(quoteJavascript(server.title(stage))), evaluate(state, "document.title"))
        assertEquals(JavascriptResult.Value(quoteJavascript(OwnedWebViewContentPolicyHttpFixture.unicode)), evaluate(state, "document.getElementById('policy-document').textContent"))
        onMain { assertTrue(state.errorsForCurrentRequest.isEmpty()) }
        if (allowNativeRestoreGet) assertTrue(server.stats(stage).getValue("get") in minimum..(minimum + 1), "Record actual Android restore plus explicit Reload, never relabel as URL-only GET policy")
    }
    private fun awaitInline(state: WebViewState, title: String) {
        await("Actual authored inline native title") { onMain { state.webView?.title == title && state.pageTitle == title && state.loadingState == LoadingState.Finished } }
        assertEquals(JavascriptResult.Value(quoteJavascript(title)), evaluate(state, "document.title"))
        assertEquals(JavascriptResult.Value(quoteJavascript(OwnedWebViewContentPolicyHttpFixture.unicode)), evaluate(state, "document.getElementById('policy-document').textContent"))
    }
    private fun assertBlank(state: WebViewState, navigator: WebViewNavigator) {
        onMain {
            val native = assertNotNull(state.webView)
            assertTrue(native.url == null || native.url == "about:blank"); assertTrue(native.title.isNullOrEmpty())
            assertTrue(state.pageTitle.isNullOrEmpty()); assertTrue(state.lastLoadedUrl.isNullOrEmpty())
            assertEquals(0, native.copyBackForwardList().size)
            assertFalse(navigator.canGoBack); assertFalse(navigator.canGoForward)
        }
        assertEquals(JavascriptResult.Value("\"\""), evaluate(state, "document.title"))
    }
    private fun assertMetadataMatchesRealDocument(state: WebViewState, navigator: WebViewNavigator) {
        // A restored history item is not a rendered document. Compare public metadata
        // to the actual provider DOM BEFORE the test asks for an explicit new load.
        val title = evaluate(state, "document.title")
        val url = evaluate(state, "document.location.href")
        onMain {
            val native = assertNotNull(state.webView)
            state.pageTitle?.takeIf { it.isNotEmpty() }?.let { assertEquals(JavascriptResult.Value(quoteJavascript(it)), title) }
            state.lastLoadedUrl?.takeIf { it.isNotEmpty() }?.let { assertEquals(JavascriptResult.Value(quoteJavascript(it)), url) }
            assertEquals(native.canGoBack(), navigator.canGoBack); assertEquals(native.canGoForward(), navigator.canGoForward)
        }
    }
    private fun awaitResources(state: WebViewState, server: OwnedWebViewContentPolicyHttpFixture, stage: String) {
        await("Actual relative JS/CSS/image transports drain") {
            val observed = server.stats(stage)
            listOf("script", "style", "image").all { observed.getValue(it) == 1 } && observed.getValue("pending") == 0
        }
        assertEquals(JavascriptResult.Value(quoteJavascript(OwnedWebViewContentPolicyHttpFixture.resourceUnicode)), evaluate(state, "document.getElementById('relative-resource-text').textContent"))
        assertEquals(JavascriptResult.Value("\"rgb(17, 34, 51)\""), evaluate(state, "getComputedStyle(document.getElementById('policy-document')).color"))
        assertEquals(JavascriptResult.Value("true"), evaluate(state, "document.getElementById('relative-image').complete && document.getElementById('relative-image').naturalWidth === 7 && document.getElementById('relative-image').naturalHeight === 9"))
        val observed = server.stats(stage)
        assertEquals(JavascriptResult.Value(quoteJavascript("h${observed.getValue("script_initial")}-a${observed.getValue("script_authorization")}")), evaluate(state, "document.documentElement.getAttribute('data-policy-script')"))
        exact(server, stage, "script_initial" to 0, "script_authorization" to 0, "style_initial" to 0, "style_authorization" to 0, "image_initial" to 0, "image_authorization" to 0)
    }
    private fun headerFacts(actual: Map<String, Int>) = listOf("main_initial", "main_authorization", "script_initial", "script_authorization", "style_initial", "style_authorization", "image_initial", "image_authorization").map {
        actual.getValue(it).also { value -> assertTrue(value in 0..1) }
    }
    private fun exact(server: OwnedWebViewContentPolicyHttpFixture, stage: String, vararg expected: Pair<String, Int>) {
        val observed = server.stats(stage)
        expected.forEach { (key, value) -> assertEquals(value, observed.getValue(key), "Fixed owned stage=$stage counter=$key") }
        assertEquals(0, observed.getValue("pending")); assertEquals(0, observed.getValue("unexpected_initial")); assertEquals(0, observed.getValue("unexpected_authorization"))
    }
}
