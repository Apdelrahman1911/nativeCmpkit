package com.mohamedrejeb.calf.ui.web

import kotlinx.browser.document
import kotlinx.browser.window
import kotlinx.coroutines.*
import kotlinx.coroutines.test.runTest
import org.w3c.dom.HTMLIFrameElement
import org.w3c.dom.MessageEvent
import org.w3c.dom.events.Event
import kotlin.test.*

/** Executes actual library iframe/cookie code in the browser runner, not mirrored DOM snippets. */
class BrowserWebViewTest {
    @Test fun stateAndNavigatorUrlLoadsBothRemoveSrcdoc() = runTest {
        val state = WebViewState(WebContent.NavigatorOnly)
        val navigator = WebViewNavigator(this)
        var created = false
        var disposed = 0
        val owner = BrowserWebViewOwner(state, { navigator }, { created = state.iframe != null }, { disposed++ })
        val frame = owner.create()
        document.body!!.appendChild(frame)
        try {
            assertTrue(created)
            owner.load(WebContent.Data("<p>inline</p>"))
            assertTrue(frame.hasAttribute("srcdoc"))
            owner.load(WebContent.Url("about:blank"))
            assertFalse(frame.hasAttribute("srcdoc"))
            owner.load(WebContent.Data("<p>again</p>"))
            owner.navigate(WebViewNavigator.NavigationEvent.LoadUrl("about:blank"))
            assertFalse(frame.hasAttribute("srcdoc"))
            owner.dispose()
            owner.dispose()
            assertEquals(1, disposed)
            assertNull(state.iframe)
            frame.dispatchEvent(Event("error"))
            assertTrue(state.errorsForCurrentRequest.isEmpty(), "Disposed listeners must not update retained state")
        } finally { owner.dispose(); frame.remove() }
    }

    @Test fun scriptEnabledIsolatedHtmlCannotMutateParentDom() = runTest { withContext(Dispatchers.Default) {
        val state = WebViewState(WebContent.NavigatorOnly)
        state.settings.javaScriptEnabled = true
        val navigator = WebViewNavigator(this)
        val owner = BrowserWebViewOwner(state, { navigator }, {}, {})
        val frame = owner.create()
        val message = CompletableDeferred<String>()
        val listener = browserEventListener { event ->
            val incoming = event as? MessageEvent ?: return@browserEventListener
            if (incoming.source === frame.contentWindow) message.complete(incoming.data.toString())
        }
        window.addEventListener("message", listener)
        document.body!!.appendChild(frame)
        try {
            owner.load(WebContent.Data("""<script>try{parent.document.documentElement.setAttribute('nativecmpkit-escaped','yes');parent.postMessage('escaped','*')}catch(e){parent.postMessage('isolated','*')}</script>"""))
            assertEquals("isolated", withTimeout(5000) { message.await() })
            assertFalse(document.documentElement!!.hasAttribute("nativecmpkit-escaped"))
            assertTrue(frame.getAttribute("sandbox")!!.contains("allow-scripts"))
            assertFalse(frame.getAttribute("sandbox")!!.contains("allow-same-origin"))
        } finally { window.removeEventListener("message", listener); owner.dispose(); frame.remove() }
    } }

    @Test fun disposalCleanupRunsEvenWhenApplicationCallbackThrows() = runTest {
        val state = WebViewState(WebContent.NavigatorOnly)
        val navigator = WebViewNavigator(this)
        val owner = BrowserWebViewOwner(state, { navigator }, {}, { error("application callback") })
        val frame = owner.create()
        assertFailsWith<IllegalStateException> { owner.dispose() }
        assertNull(state.iframe)
        owner.dispose()
        frame.remove()
    }

    @Test fun browserCookieExpiryAndUnsupportedBoundariesAreReal() = runTest {
        val manager = CookieManager()
        val url = window.location.href
        val name = "nativecmpkit_cookie_regression"
        try {
            assertEquals("Thu, 01 Jan 1970 00:00:00 GMT", cookieHttpDate(0.0))
            manager.setCookie(url, Cookie(name, "value", path = "/", expiresDate = 4070908800000L))
            assertEquals("value", manager.getCookies(url).first { it.name == name }.value)
            manager.setCookie(url, Cookie(name, "value", path = "/", expiresDate = 0))
            assertTrue(manager.getCookies(url).none { it.name == name })
            assertFailsWith<UnsupportedCookieOperationException> { manager.setCookie(url, Cookie(name, "x", isHttpOnly = true)) }
            assertFailsWith<UnsupportedCookieOperationException> { manager.getCookies("https://foreign.invalid/") }
            assertFailsWith<UnsupportedCookieOperationException> { manager.removeAllCookies() }
        } finally { manager.removeCookiesSetByThisManager() }
    }

    @Test fun failedCreationCannotLeaveTheStatePointingAtAnUnownedIframe() = runTest {
        val state = WebViewState(WebContent.NavigatorOnly)
        val navigator = WebViewNavigator(this)
        var callbacks = 0
        val expected = IllegalStateException("creation callback")
        val owner = BrowserWebViewOwner(state, { navigator }, {
            assertNotNull(state.iframe)
            throw expected
        }, { callbacks++ })
        assertSame(expected, assertFailsWith<IllegalStateException> { owner.create() })
        assertNull(state.iframe)
        assertNull(state.owner)
        owner.dispose()
        assertEquals(0, callbacks)
    }

    @Test fun disposalRemovesTheRegisteredNativeListenersRatherThanOnlySilencingThem() = runTest {
        for (throwOnDispose in listOf(false, true)) {
            val state = WebViewState(WebContent.NavigatorOnly)
            val navigator = WebViewNavigator(this)
            val expected = IllegalStateException("application disposal callback")
            val owner = BrowserWebViewOwner(state, { navigator }, {}, {
                if (throwOnDispose) throw expected
            })
            var frame: HTMLIFrameElement? = null
            var probeInstalled = false
            // This entire instrumented interval is synchronous: no suspension or browser turns.
            try {
                installBrowserListenerProbe()
                probeInstalled = true
                val created = owner.create()
                frame = created
                assertTrue(browserListenerProbeOwns(created))
                assertEquals(2, browserListenerProbeCount("registrations"))
                created.dispatchEvent(Event("load"))
                created.dispatchEvent(Event("error"))
                assertEquals(2, browserListenerProbeCount("deliveries"))

                // Negative control: another native object cannot detach the registered listener.
                created.removeEventListener("load", browserEventListener {})
                assertEquals(1, browserListenerProbeCount("unmatchedRemovals"))
                assertEquals(0, browserListenerProbeCount("matchedRemovals"))
                created.dispatchEvent(Event("load"))
                assertEquals(3, browserListenerProbeCount("deliveries"), "The native observer must see a still-attached listener")

                if (throwOnDispose) {
                    assertSame(expected, assertFailsWith<IllegalStateException> { owner.dispose() })
                } else {
                    owner.dispose()
                }
                assertEquals(2, browserListenerProbeCount("matchedRemovals"))
                assertEquals(1, browserListenerProbeCount("unmatchedRemovals"))
                created.dispatchEvent(Event("load"))
                created.dispatchEvent(Event("error"))
                assertEquals(3, browserListenerProbeCount("deliveries"), "Disposed guards cannot hide native delivery from this counter")
                owner.dispose()
                assertEquals(2, browserListenerProbeCount("matchedRemovals"))
                assertNull(state.iframe)
            } finally {
                try {
                    owner.dispose()
                } finally {
                    try { frame?.remove() } finally {
                        if (probeInstalled) restoreBrowserListenerProbe()
                    }
                }
            }
        }
    }
}

internal expect fun installBrowserListenerProbe()
internal expect fun restoreBrowserListenerProbe()
internal expect fun browserListenerProbeOwns(frame: HTMLIFrameElement): Boolean
internal expect fun browserListenerProbeCount(name: String): Int
