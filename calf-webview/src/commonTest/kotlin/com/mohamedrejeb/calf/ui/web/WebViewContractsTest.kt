package com.mohamedrejeb.calf.ui.web

import androidx.compose.runtime.saveable.SaverScope
import kotlinx.coroutines.*
import kotlinx.coroutines.test.*
import kotlin.test.*

@OptIn(ExperimentalCoroutinesApi::class)
class WebViewNavigatorTest {
    @Test fun commandsBeforeAttachmentAreDeliveredOnlyOnce() = runTest {
        val navigator = WebViewNavigator(this)
        val seen = mutableListOf<WebViewNavigator.NavigationEvent>()
        navigator.loadUrl("https://example.test")
        navigator.navigateBack()
        val first = launch { navigator.consumeNavigationEvents { seen += it } }
        runCurrent()
        assertEquals(2, seen.size)
        first.cancelAndJoin()
        val second = launch { navigator.consumeNavigationEvents { seen += it } }
        runCurrent()
        assertEquals(2, seen.size, "A detached collector must not replay Back")
        second.cancelAndJoin()
    }

    @Test fun oneNavigatorRejectsTwoSimultaneousOwners() = runTest {
        val navigator = WebViewNavigator(this)
        val first = launch { navigator.consumeNavigationEvents {} }
        runCurrent()
        assertFailsWith<IllegalStateException> { navigator.consumeNavigationEvents {} }
        first.cancelAndJoin()
    }

    @Test fun attachmentSnapshotPrecedesCommandsAndRejectedOwnersCannotRunIt() = runTest {
        val navigator = WebViewNavigator(this)
        var snapshots = 0
        val seen = mutableListOf<String>()
        navigator.reload()
        val first = launch {
            navigator.consumeNavigationEvents(onAttached = { snapshots++; seen += "snapshot" }) { seen += "command" }
        }
        runCurrent()
        assertEquals(listOf("snapshot", "command"), seen)
        assertFailsWith<IllegalStateException> {
            navigator.consumeNavigationEvents(onAttached = { snapshots++; error("rejected owner must not snapshot") }) {}
        }
        assertEquals(1, snapshots)
        first.cancelAndJoin()
    }

    @Test fun pendingQueueHasAnExplicitBound() = runTest {
        val navigator = WebViewNavigator(this)
        repeat(64) { navigator.reload() }
        assertFailsWith<IllegalStateException> { navigator.reload() }
    }

    @Test fun loadHeadersAreSnapshottedAtCallBoundary() = runTest {
        val navigator = WebViewNavigator(this)
        val headers = mutableMapOf("X-Request" to "initial")
        navigator.loadUrl("https://example.test", headers)
        headers["X-Request"] = "mutated"
        var observed: WebViewNavigator.NavigationEvent.LoadUrl? = null
        val collector = launch { navigator.consumeNavigationEvents { observed = it as WebViewNavigator.NavigationEvent.LoadUrl } }
        runCurrent()
        assertEquals("initial", observed?.additionalHttpHeaders?.get("X-Request"))
        collector.cancelAndJoin()
    }

    @Test fun detachmentClearsHistoryCapabilities() = runTest {
        val navigator = WebViewNavigator(this)
        val collector = launch { navigator.consumeNavigationEvents {} }
        runCurrent()
        navigator.canGoBack = true
        navigator.canGoForward = true
        collector.cancelAndJoin()
        assertFalse(navigator.canGoBack)
        assertFalse(navigator.canGoForward)
    }
}

class WebSettingsTest {
    @Test fun equalValuesDoNotScheduleNativeUpdates() {
        var calls = 0
        val settings = WebSettings { calls++ }
        repeat(100) {
            settings.javaScriptEnabled = false
            settings.androidSettings.textZoom = 100
            settings.iosSettings.allowsInlineMediaPlayback = true
            settings.desktopSettings.customUserAgent = null
        }
        assertEquals(0, calls)
    }
    @Test fun nestedBatchNotifiesOnce() {
        var calls = 0
        val settings = WebSettings { calls++ }
        settings.batch {
            javaScriptEnabled = true
            batch { androidSettings.textZoom = 125; desktopSettings.customUserAgent = "test" }
        }
        assertEquals(1, calls)
    }
    @Test fun throwingBatchStillPublishesItsChangesOnce() {
        var calls = 0
        val settings = WebSettings { calls++ }
        assertFailsWith<IllegalStateException> { settings.batch { javaScriptEnabled = true; error("caller") } }
        assertEquals(1, calls)
        settings.javaScriptEnabled = false
        assertEquals(2, calls)
    }
    @Test fun javascriptDoesNotEscalateBrowserOriginTrust() {
        val settings = WebSettings {}
        settings.javaScriptEnabled = true
        assertEquals(BrowserSandboxPolicy.Isolated, settings.browserSandboxPolicy)
    }
}

class WebContentContractsTest {
    @Test fun requestStartClearsPreviousErrorsAndFinalMetadata() {
        val state = WebViewState(WebContent.NavigatorOnly)
        state.errorsForCurrentRequest = listOf(WebViewError(-1, "previous"))
        state.lastLoadedUrl = "https://old.test"
        state.pageTitle = "Old"
        state.beginRequest("https://new.test")
        assertEquals("https://new.test", state.requestedUrl)
        assertNull(state.lastLoadedUrl)
        assertNull(state.pageTitle)
        assertTrue(state.errorsForCurrentRequest.isEmpty())
        assertIs<LoadingState.Loading>(state.loadingState)
    }
    @Test fun unsupportedOptionsAreNotSilentlyDiscarded() {
        val content = WebContent.Data("é", "https://base.test", "latin-1", "application/pdf", "https://history.test")
        assertEquals(setOf("baseUrl", "encoding", "mimeType", "historyUrl"), content.unsupportedOptions(WebContentPlatform.Browser).toSet())
        assertTrue(content.unsupportedOptions(WebContentPlatform.Android).isEmpty())
        val state = WebViewState(content)
        assertFalse(state.acceptContent(content, WebContentPlatform.Desktop))
        assertEquals(-2, state.errorsForCurrentRequest.single().code)
        assertEquals(LoadingState.Finished, state.loadingState)
    }
    @Test fun urlSaverRestoresContentWithoutSensitiveHeadersOrStaleTitle() {
        val state = WebViewState(WebContent.Url("https://example.test/path", mapOf("Authorization" to "not-saved")))
        state.pageTitle = "stale"
        val saver = urlReloadWebStateSaver()
        val scope = object : SaverScope { override fun canBeSaved(value: Any): Boolean = true }
        val saved = with(saver) { scope.save(state) }!!
        assertFalse(saved.toString().contains("not-saved"))
        val restored = saver.restore(saved)!!
        assertEquals(WebContent.Url("https://example.test/path"), restored.content)
        assertNull(restored.pageTitle)
        assertNull(restorableWebUrl("javascript:alert(1)"))
        assertNull(restorableWebUrl("file:///private/document"))
    }
    @Test fun javascriptResultEnvelopeDistinguishesNullUndefinedAndFailure() {
        assertEquals(JavascriptResult.Value("null"), decodeJavascriptResult("vnull"))
        assertEquals(JavascriptResult.Undefined, decodeJavascriptResult("u"))
        assertEquals(JavascriptResult.Error("failure"), decodeJavascriptResult("efailure"))
        assertIs<JavascriptResult.Error>(decodeJavascriptResult(null))
        assertEquals("\"a\\n\\\"\\\\\\u2028\"", quoteJavascript("a\n\"\\\u2028"))
    }

    @Test fun completedRedirectRestoresObservedFinalUrlInsteadOfOriginalRequest() {
        val state = WebViewState(WebContent.Url("https://first.test/"))
        state.beginRequest("https://request.test/")
        state.lastLoadedUrl = "https://final.test/"
        state.loadingState = LoadingState.Finished
        assertEquals("https://final.test/", state.urlForGetRestoration())
        val saver = urlReloadWebStateSaver()
        val scope = object : SaverScope { override fun canBeSaved(value: Any) = true }
        val saved = with(saver) { scope.save(state) }!!
        assertEquals(WebContent.Url("https://final.test/"), saver.restore(saved)!!.content)
    }

    @Test fun pendingAndFailedRequestsHaveExplicitGetRetryPrecedence() {
        val state = WebViewState(WebContent.Url("https://initial.test/"))
        assertEquals("https://initial.test/", state.urlForGetRestoration())
        state.beginRequest("https://pending.test/")
        state.lastLoadedUrl = "https://intermediate.test/"
        assertEquals("https://pending.test/", state.urlForGetRestoration(), "Loading saves the accepted request, not a provisional URL")
        state.lastLoadedUrl = null
        state.loadingState = LoadingState.Finished
        state.errorsForCurrentRequest = listOf(WebViewError(-1, "network failed"))
        assertEquals("https://pending.test/", state.urlForGetRestoration(), "Without an observed final URL restoration retries the request as GET")
    }

    @Test fun inlineAndNonHttpFinalPagesNeverResurrectOldDeclarativeUrls() {
        val state = WebViewState(WebContent.Url("https://old.test/"))
        state.beginRequest() // navigator HTML does not replace the declarative content object.
        assertNull(state.urlForGetRestoration())
        state.loadingState = LoadingState.Finished
        assertNull(state.urlForGetRestoration())
        state.beginRequest("https://request.test/")
        state.lastLoadedUrl = "file:///private/final"
        state.loadingState = LoadingState.Finished
        assertNull(state.urlForGetRestoration(), "A known non-HTTP final page is not replaced by its old HTTP request")
    }
}

class CookieRulesTest {
    @Test fun pathMatchUsesBoundariesNotStringPrefixes() {
        assertTrue(cookiePathMatches("/private/a", "/private"))
        assertTrue(cookiePathMatches("/private", "/private"))
        assertFalse(cookiePathMatches("/private-public", "/private"))
        assertFalse(cookiePathMatches("/public", "/private"))
    }
    @Test fun hostOnlyAndSecureCookiesDoNotLeakToOtherRequests() {
        assertFalse(cookieMatchesRequest("sub.example.test", "/", true, "example.test", "/", false, true))
        assertTrue(cookieMatchesRequest("sub.example.test", "/", true, ".example.test", "/", false, false))
        assertFalse(cookieMatchesRequest("badexample.test", "/", true, ".example.test", "/", false, false))
        assertFalse(cookieMatchesRequest("example.test", "/", false, "example.test", "/", true, false))
    }
    @Test fun cookieSerializationRejectsAttributeInjection() {
        listOf(Cookie("bad;name", "value"), Cookie("name", "value; Secure"), Cookie("name", "x\r\n"),
            Cookie("name", "x", path = "/; HttpOnly"), Cookie("name", "x", domain = "example.test;Secure"))
            .forEach { assertFailsWith<IllegalArgumentException> { cookieHeader(it) } }
        assertEquals("name=a=b; Path=/", cookieHeader(Cookie("name", "a=b", path = "/")))
    }
    @Test fun defaultPathsAndHostCookieRequirementsAreExplicit() {
        assertEquals("/private", defaultCookiePath("/private/page"))
        assertEquals("/", defaultCookiePath("/page"))
        assertFailsWith<IllegalArgumentException> { validateCookie(Cookie("__Host-name", "x", isSecure = true)) }
        assertFailsWith<IllegalArgumentException> { validateCookie(Cookie("name", "x", expiresDate = Long.MAX_VALUE)) }
    }
}
