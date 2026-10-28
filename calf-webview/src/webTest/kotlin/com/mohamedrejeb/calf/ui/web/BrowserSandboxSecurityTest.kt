// NativeCmpKit regression tests: real library iframes/native browser security decisions.
package com.mohamedrejeb.calf.ui.web

import kotlinx.browser.document
import kotlinx.browser.window
import kotlinx.coroutines.*
import kotlinx.coroutines.test.runTest
import org.w3c.dom.HTMLIFrameElement
import org.w3c.dom.MessageEvent
import kotlin.test.*

/** No synthetic MessageEvents, window.open/submit replacements or copied sandbox implementation. */
class BrowserSandboxSecurityTest {
    @Test fun javascriptOptInKeepsParentDomStorageAndCookiesOpaque() = runTest {
        withContext(Dispatchers.Default) {
            withHostProbe { key ->
                withFrame(this) { f ->
                    assertEquals(BrowserSandboxPolicy.Isolated, f.state.settings.browserSandboxPolicy)
                    assertEquals("allow-scripts", f.element.getAttribute("sandbox"))
                    val result = f.receive("isolation", f.html("isolation", """
                        function probe(name, action) {
                            try { action(); return name + ':allowed'; }
                            catch (error) { return name + ':' + error.name; }
                        }
                        report([
                            probe('dom-read', function() { return parent.document.documentElement.tagName; }),
                            probe('dom-write', function() { parent.document.documentElement.setAttribute(${literal(key)}, 'escaped'); }),
                            probe('parent-storage-read', function() { return parent.localStorage.getItem(${literal(key)}); }),
                            probe('parent-storage-write', function() { parent.localStorage.setItem(${literal(key)}, 'escaped'); }),
                            probe('own-storage', function() { return localStorage.getItem(${literal(key)}); }),
                            probe('parent-cookie', function() { return parent.document.cookie; }),
                            probe('own-cookie', function() { return document.cookie; })
                        ].join('|'));
                    """))
                    assertEquals("null", result.origin)
                    assertEquals(listOf("dom-read", "dom-write", "parent-storage-read", "parent-storage-write",
                        "own-storage", "parent-cookie", "own-cookie").joinToString("|") { "$it:SecurityError" }, result.payload)
                    assertHostProbe(key, "host")
                }
            }
        }
    }

    @Test fun onlyExplicitTrustedPolicyPermitsHostIntegrationAndNextNavigationReisolates() = runTest {
        withContext(Dispatchers.Default) {
            withHostProbe { key ->
                withFrame(this) { f ->
                    assertEquals(BrowserSandboxPolicy.Isolated, f.state.settings.browserSandboxPolicy)
                    f.state.settings.browserSandboxPolicy = BrowserSandboxPolicy.Trusted
                    assertNull(f.element.getAttribute("sandbox"))
                    val trusted = f.receive("trusted", f.html("trusted", """
                        if (parent.document.documentElement.getAttribute(${literal(key)}) !== 'host' ||
                            parent.localStorage.getItem(${literal(key)}) !== 'host' ||
                            !parent.document.cookie.includes(${literal(key + "=host")})) throw new Error('Host fixture not readable');
                        parent.document.documentElement.setAttribute(${literal(key)}, 'trusted');
                        parent.localStorage.setItem(${literal(key)}, 'trusted');
                        report('host-integration');
                    """))
                    assertEquals(window.location.origin, trusted.origin)
                    assertEquals("host-integration", trusted.payload)
                    assertHostProbe(key, "trusted")

                    // Changing the attribute governs the NEXT navigation, not instant revocation.
                    f.state.settings.browserSandboxPolicy = BrowserSandboxPolicy.Isolated
                    assertEquals("allow-scripts", f.element.getAttribute("sandbox"))
                    val isolated = f.receive("reisolated", f.html("reisolated", """
                        try { parent.document.documentElement.setAttribute(${literal(key)}, 'escaped'); report('escaped'); }
                        catch (error) { report(error.name); }
                    """))
                    assertEquals("null", isolated.origin)
                    assertEquals("SecurityError", isolated.payload)
                    assertHostProbe(key, "trusted")
                }
            }
        }
    }

    @Test fun nestedInlineFramesInheritIsolationAndCannotNavigateTheTop() = runTest {
        withContext(Dispatchers.Default) {
            // Do not round-trip a foreign-realm Window through assertNotNull<T : Any>:
            // Wasm's generic result cast checks this realm's Window constructor.
            val top = window.top ?: error("A browser fixture must have a top window")
            val originalHref = top.location.href
            val marker = "#nativecmpkit-sandbox-" + nextToken()
            withHostProbe { key ->
                try {
                    for (trusted in listOf(false, true)) withFrame(this, trusted = trusted) { f ->
                        val nested = """<!doctype html><script>
                            function probe(name, action) {
                                try { action(); return name + ':allowed'; }
                                catch (error) { return name + ':' + error.name; }
                            }
                            parent.postMessage(${literal(f.prefix("nested"))} + [
                                probe('dom', function() { parent.parent.document.documentElement.setAttribute(${literal(key)}, 'nested'); }),
                                probe('storage', function() { parent.parent.localStorage.setItem(${literal(key)}, 'nested'); }),
                                probe('top', function() { top.location.href = ${literal(originalHref.substringBefore('#') + marker)}; })
                            ].join('|'), '*');
                        </script>"""
                        val result = f.receive("nested", f.html("nested", """
                            var nested = document.createElement('iframe');
                            addEventListener('message', function(event) {
                                if (event.source === nested.contentWindow && typeof event.data === 'string' &&
                                    event.data.startsWith(${literal(f.prefix("nested"))})) {
                                    report(event.data.substring(${f.prefix("nested").length}) + '|nested-origin:' + event.origin);
                                }
                            });
                            nested.srcdoc = ${literal(nested)};
                            document.body.appendChild(nested);
                        """))
                        val decision = if (trusted) "allowed" else "SecurityError"
                        val origin = if (trusted) window.location.origin else "null"
                        assertEquals(origin, result.origin)
                        assertEquals("dom:$decision|storage:$decision|top:$decision|nested-origin:$origin", result.payload)
                        if (trusted) {
                            assertEquals(marker, top.location.hash)
                            assertHostProbe(key, "nested")
                        } else {
                            assertEquals(originalHref, top.location.href)
                            assertHostProbe(key, "host")
                        }
                    }
                } finally { top.history.replaceState(null, "", originalHref) }
            }
        }
    }

    @Test fun defaultIsolationBlocksActualFormSubmissionWhileTrustedControlSubmits() = runTest {
        withContext(Dispatchers.Default) {
            // Owned subframe navigation to the local test server's inert favicon,
            // not an external endpoint, context.html or another test application.
            val targetUrl = window.location.origin + "/favicon.ico"
            for (trusted in listOf(true, false)) withFrame(this, trusted = trusted) { f ->
                val result = f.receive("form", f.html("form", """
                    var target = document.createElement('iframe');
                    var form = document.createElement('form');
                    var phase = 0, attempts = 0, navigations = 0, finished = false, timer;
                    target.name = ${literal(f.token + "formtarget")};
                    form.target = target.name;
                    form.method = 'get';
                    form.action = ${literal(targetUrl)};
                    function finish(value) {
                        if (finished) return;
                        finished = true; clearTimeout(timer);
                        report(value + '|attempts:' + attempts + '|navigations:' + navigations);
                    }
                    target.addEventListener('load', function() {
                        if (phase === 0) {
                            phase = 1; attempts++;
                            form.submit();
                            timer = setTimeout(function() { finish('blocked'); }, 250);
                        } else {
                            navigations++;
                            var url = target.contentWindow.location.href;
                            finish(url.startsWith(${literal(targetUrl)}) ? 'submitted' : 'unexpected-target');
                        }
                    });
                    target.src = 'about:blank';
                    document.body.appendChild(form);
                    document.body.appendChild(target);
                """))
                assertEquals(if (trusted) window.location.origin else "null", result.origin)
                assertEquals(if (trusted) "submitted|attempts:1|navigations:1" else "blocked|attempts:1|navigations:0", result.payload)
                if (!trusted) assertFalse(assertNotNull(f.element.getAttribute("sandbox")).contains("allow-forms"))
            }
        }
    }

    @Test fun popupOptInRetainsIsolationRatherThanAllowingPopupEscape() = runTest {
        withContext(Dispatchers.Default) {
            withHostProbe { key ->
                for ((trusted, popups) in listOf(false to false, false to true, true to true)) {
                    withFrame(this, trusted = trusted, popups = popups) { f ->
                        val popup = """<!doctype html><script>
                            function probe(name, action) {
                                try { action(); return name + ':allowed'; }
                                catch (error) { return name + ':' + error.name; }
                            }
                            opener.postMessage(${literal(f.prefix("popup"))} + [
                                probe('dom', function() { opener.parent.document.documentElement.setAttribute(${literal(key)}, 'popup'); }),
                                probe('storage', function() { opener.parent.localStorage.setItem(${literal(key)}, 'popup'); })
                            ].join('|'), '*');
                        </script>"""
                        val result = f.receive("popup", f.html("popup", """
                            var popup, url, timer, done = false;
                            function closeOwned() {
                                if (popup && !popup.closed) popup.close();
                                if (url) { URL.revokeObjectURL(url); url = null; }
                            }
                            addEventListener('pagehide', closeOwned);
                            addEventListener('message', function(event) {
                                if (!done && event.source === popup && typeof event.data === 'string' &&
                                    event.data.startsWith(${literal(f.prefix("popup"))})) {
                                    done = true; clearTimeout(timer);
                                    var payload = event.data.substring(${f.prefix("popup").length});
                                    var origin = event.origin;
                                    closeOwned();
                                    setTimeout(function() { report(payload + '|popup-origin:' + origin + '|closed:' + popup.closed + '|revoked:' + (url === null)); }, 0);
                                }
                            });
                            timer = setTimeout(function() { closeOwned(); report('popup-timeout'); }, 4000);
                            url = URL.createObjectURL(new Blob([${literal(popup)}], {type:'text/html'}));
                            popup = window.open(url, ${literal(f.token + "popup")}, 'width=80,height=80');
                            if (!popup) { done = true; clearTimeout(timer); closeOwned(); report('blocked'); }
                        """))
                        val origin = if (trusted) window.location.origin else "null"
                        assertEquals(origin, result.origin)
                        if (!popups) {
                            assertEquals("blocked", result.payload)
                            assertHostProbe(key, "host")
                        } else {
                            val decision = if (trusted) "allowed" else "SecurityError"
                            assertEquals("dom:$decision|storage:$decision|popup-origin:$origin|closed:true|revoked:true", result.payload)
                            assertHostProbe(key, if (trusted) "popup" else "host")
                        }
                        if (!trusted) {
                            val flags = assertNotNull(f.element.getAttribute("sandbox"))
                            assertEquals(popups, flags.split(' ').contains("allow-popups"))
                            assertFalse(flags.contains("allow-same-origin"))
                            assertFalse(flags.contains("allow-popups-to-escape-sandbox"))
                        }
                    }
                }
            }
        }
    }

    @Test fun messageConsumersMustCheckBothNativeSourceAndOpaqueOrTrustedOrigin() = runTest {
        withContext(Dispatchers.Default) {
            withFrame(this) { f -> withFrame(this) { sibling ->
                val prefix = f.prefix("protocol")
                var expectedOrigin = "null"
                var accepted = 0
                val foreignSource = CompletableDeferred<String>()
                val foreignOrigin = CompletableDeferred<String>()
                val first = CompletableDeferred<String>()
                val second = CompletableDeferred<String>()
                // Example application-owned protocol, NOT a claimed built-in library bridge.
                val listener = browserEventListener { raw ->
                    val event = raw as? MessageEvent ?: return@browserEventListener
                    val data = event.data.toString()
                    if (!data.startsWith(prefix)) return@browserEventListener
                    assertTrue(event.isTrusted, "These must be native postMessage deliveries, not dispatched test events")
                    when {
                        event.source !== f.element.contentWindow -> foreignSource.complete(event.origin)
                        event.origin != expectedOrigin -> foreignOrigin.complete(event.origin)
                        else -> {
                            accepted++
                            if (accepted == 1) first.complete(data.removePrefix(prefix))
                            else second.complete(data.removePrefix(prefix))
                        }
                    }
                }
                window.addEventListener("message", listener)
                try {
                    sibling.owner.load(WebContent.Data(sibling.html("ignored", "parent.postMessage(${literal(prefix + "spoof")}, '*');")))
                    assertEquals("null", withTimeout(5_000) { foreignSource.await() })
                    assertEquals(0, accepted, "Another opaque-origin frame can have origin=null; source identity is also required")
                    f.owner.load(WebContent.Data(f.html("protocol", "report('legitimate-opaque');")))
                    assertEquals("legitimate-opaque", withTimeout(5_000) { first.await() })
                    f.state.settings.browserSandboxPolicy = BrowserSandboxPolicy.Trusted
                    f.owner.load(WebContent.Data(f.html("protocol", "report('stale-origin-rule');")))
                    assertEquals(window.location.origin, withTimeout(5_000) { foreignOrigin.await() })
                    assertEquals(1, accepted, "Same WindowProxy with a different native origin must not reuse an opaque-origin rule")
                    expectedOrigin = window.location.origin
                    f.owner.load(WebContent.Data(f.html("protocol", "report('legitimate-trusted');")))
                    assertEquals("legitimate-trusted", withTimeout(5_000) { second.await() })
                    assertEquals(2, accepted)
                } finally { window.removeEventListener("message", listener) }
            } }
        }
    }

    @Test fun realCspViolationBlocksUnnoncedScriptWithoutWeakeningIsolation() = runTest {
        withContext(Dispatchers.Default) {
            withFrame(this) { f ->
                val control = f.receive("csp-control", f.html("csp-control", "",
                    tail = "<script>window.nativeDisallowedRan=true;report('unrestricted-ran');</script>"))
                assertEquals("unrestricted-ran", control.payload)
                val result = f.receive("csp-blocked", f.html("csp-blocked", """
                    addEventListener('securitypolicyviolation', function(event) {
                        report(event.effectiveDirective + '|' + event.blockedURI + '|' +
                            (window.nativeDisallowedRan === true) + '|trusted:' + event.isTrusted);
                    });
                """, head = "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; script-src 'nonce-${f.token}'; base-uri 'none'\">",
                    tail = "<script>window.nativeDisallowedRan=true;</script>"))
                assertEquals("null", result.origin)
                assertEquals("script-src-elem|inline|false|trusted:true", result.payload)
                assertEquals("allow-scripts", f.element.getAttribute("sandbox"))
            }
        }
    }

    private suspend fun withFrame(scope: CoroutineScope, trusted: Boolean = false, popups: Boolean = false,
                                  block: suspend (Frame) -> Unit) {
        val frame = Frame(scope, trusted, popups)
        try { block(frame) } finally {
            runWebViewCleanup(null, frame.owner::dispose, { frame.element.remove() })
        }
    }

    private suspend fun withHostProbe(block: suspend (String) -> Unit) {
        val key = nextToken()
        assertFalse(assertNotNull(document.documentElement).hasAttribute(key))
        assertNull(window.localStorage.getItem(key), "Use only fresh fixture-owned storage")
        assertFalse(document.cookie.split(';').any { it.trim().startsWith("$key=") })
        try {
            document.documentElement!!.setAttribute(key, "host")
            window.localStorage.setItem(key, "host")
            document.cookie = "$key=host; path=/"
            assertHostProbe(key, "host")
            block(key)
        } finally {
            runWebViewCleanup(null,
                { document.documentElement!!.removeAttribute(key) },
                { window.localStorage.removeItem(key) },
                { document.cookie = "$key=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/" },
            )
        }
    }

    private fun assertHostProbe(key: String, value: String) {
        assertEquals(value, document.documentElement!!.getAttribute(key))
        assertEquals(value, window.localStorage.getItem(key))
        assertTrue(document.cookie.split(';').any { it.trim() == "$key=host" })
    }

    private data class NativeMessage(val payload: String, val origin: String)

    private class Frame(scope: CoroutineScope, trusted: Boolean, popups: Boolean) {
        val token = nextToken()
        val state = WebViewState(WebContent.NavigatorOnly).apply {
            settings.javaScriptEnabled = true
            settings.javaScriptCanOpenWindowsAutomatically = popups
            if (trusted) settings.browserSandboxPolicy = BrowserSandboxPolicy.Trusted
        }
        private val navigator = WebViewNavigator(scope)
        val owner = BrowserWebViewOwner(state, { navigator }, {}, {})
        val element: HTMLIFrameElement = owner.create()
        init {
            try { assertNotNull(document.body).appendChild(element) }
            catch (error: Throwable) {
                runWebViewCleanup(error, owner::dispose, { element.remove() })
                throw error
            }
        }

        fun prefix(label: String) = "$token/$label/"
        fun html(label: String, body: String, head: String = "", tail: String = "") =
            "<!doctype html><html><head>$head</head><body><script nonce='$token'>" +
                "var report=function(value){parent.postMessage(" + literal(prefix(label)) + "+String(value),'*');};" +
                body + "</script>" + tail + "</body></html>"

        suspend fun receive(label: String, html: String): NativeMessage {
            val received = CompletableDeferred<NativeMessage>()
            val prefix = prefix(label)
            val listener = browserEventListener { raw ->
                val event = raw as? MessageEvent ?: return@browserEventListener
                val data = event.data.toString()
                if (event.source === element.contentWindow && data.startsWith(prefix)) {
                    if (event.isTrusted) received.complete(NativeMessage(data.removePrefix(prefix), event.origin))
                    else received.completeExceptionally(AssertionError("Synthetic message cannot establish browser security"))
                }
            }
            window.addEventListener("message", listener)
            try {
                owner.load(WebContent.Data(html))
                return withTimeout(5_000) { received.await() }
            } finally { window.removeEventListener("message", listener) }
        }
    }

    companion object {
        private var sequence = 0
        private fun nextToken() = "nativecmpkitSandboxSecurity" + (++sequence)
        // Encode literal '<' too: a nested </script> must not terminate its owning script.
        private fun literal(value: String) = "'" + value.replace("\\", "\\\\").replace("'", "\\'")
            .replace("\r", "\\r").replace("\n", "\\n").replace("<", "\\u003c")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029") + "'"
    }
}
