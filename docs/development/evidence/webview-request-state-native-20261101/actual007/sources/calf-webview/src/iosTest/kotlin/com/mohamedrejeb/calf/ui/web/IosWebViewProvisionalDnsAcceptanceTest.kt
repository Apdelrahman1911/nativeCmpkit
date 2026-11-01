// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.web

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import com.mohamedrejeb.calf.ui.web.internal.NativeApplicationUiTest
import com.mohamedrejeb.calf.ui.web.internal.onApplicationMain
import com.mohamedrejeb.calf.ui.web.internal.requireOwnedApplicationWindow
import com.mohamedrejeb.calf.ui.web.internal.runApplicationUiTest
import com.mohamedrejeb.calf.ui.web.internal.sameNativeObject
import com.mohamedrejeb.calf.ui.web.internal.waitForNative
import kotlinx.cinterop.ObjCSignatureOverride
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import platform.Foundation.NSError
import platform.Foundation.NSThread
import platform.Foundation.NSURLErrorCannotFindHost
import platform.Foundation.NSURLErrorDomain
import platform.Foundation.NSUUID
import platform.UIKit.UIWindow
import platform.WebKit.WKNavigation
import platform.WebKit.WKNavigationDelegateProtocol
import platform.WebKit.WKWebView
import platform.darwin.NSObject
import kotlin.test.*

/**
 * Genuine WK/system-resolver DNS failures, not an injected NSError or controlled resolver.
 * Fresh reserved .invalid hosts may still time out or fail differently on a given runner;
 * only actual provisional NSURLErrorDomain/NSURLErrorCannotFindHost (-1003) can pass.
 * No DNS/TLS/offline equivalence, resolver override, certificate or ATS bypass is used.
 */
class IosWebViewProvisionalDnsAcceptanceTest {
    @Test fun nativeProvisionalDnsFailFailResetsPreviousErrorBeforeCommitOnSameDocument() {
        val nonce = NSUUID().UUIDString.replace("-", "").lowercase()
        assertTrue(Regex("[0-9a-f]{32}").matches(nonce), "A fresh reserved-host nonce is required")
        val targets = listOf("https://dns-one-$nonce.nativecmpkit.invalid/$nonce/one",
                             "https://dns-two-$nonce.nativecmpkit.invalid/$nonce/two")
        val ids = listOf("nativecmpkit-dns-one", "nativecmpkit-dns-two")
        val title = "nativecmpkit-dns-retained-$nonce"
        val body = "owned dns document $nonce"
        // Inline-only initial document: no endpoint, listener, proxy or external resource.
        val html = "<html><head><title>$title</title></head><body>" +
            "<p id='nativecmpkit-retained'>$body</p>" +
            "<a id='${ids[0]}' href='${targets[0]}'>one</a>" +
            "<a id='${ids[1]}' href='${targets[1]}'>two</a></body></html>"
        val state = WebViewState(WebContent.Data(html)).apply { settings.javaScriptEnabled = true }
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
        val navigator = WebViewNavigator(scope)
        var retainedNative: WKWebView? = null
        try {
            runApplicationUiTest {
                setContent { WebView(state, Modifier.fillMaxSize(), navigator = navigator) }
                waitForIdle()
                waitForNative {
                    state.webView?.title == title && state.pageTitle == title &&
                        state.webView?.loading == false && state.loadingState == LoadingState.Finished
                }
                val native = runOnIdle {
                    val view = assertNotNull(state.webView)
                    assertTrue(sameNativeObject(view.window, requireOwnedApplicationWindow()))
                    assertNotNull(view.superview)
                    assertTrue(sameNativeObject(view.navigationDelegate as? WebViewState, state))
                    assertNotNull(state.nativeObserver)
                    assertTrue(state.errorsForCurrentRequest.isEmpty())
                    retainedNative = view
                    view
                }
                val documentScript = "[document.title, document.getElementById('nativecmpkit-retained').textContent, document.URL]"
                val retainedDocument = evaluate(state, documentScript)
                assertTrue(retainedDocument is JavascriptResult.Value &&
                    retainedDocument.json.startsWith("[" + quoteJavascript(title) + "," + quoteJavascript(body) + ","),
                    "Initial inline native document identity is missing")
                val lease = runOnIdle { DnsForwarder.acquire(state, native, requireOwnedApplicationWindow()) }
                var primary: Throwable? = null
                try {
                    for (index in targets.indices) {
                        runOnIdle { lease.arm(index, targets[index]) }
                        // Both requests originate from actual retained-document links.
                        // A state/content/navigator loader would pre-clear the preceding
                        // error and cannot witness provisional-start reset on request two.
                        assertTrue(evaluate(state, "document.getElementById('${ids[index]}').click(); 1") == JavascriptResult.Value("1"),
                            "The genuine native document link did not execute")
                        // Existing genuine host wait is finite (10s). Timeout, commit,
                        // offline/-1009, TLS/-1200 and any other terminal code are red.
                        waitForNative { lease.hasFault || (lease.hasTerminalCallback && !native.loading) }
                        runOnIdle { lease.requireDnsAttempt(index) }
                        assertTrue(evaluate(state, documentScript) == retainedDocument,
                            "A DNS-failed provisional navigation replaced the retained native document")
                        runOnIdle {
                            assertTrue(native.title == title, "The native retained title changed without commit")
                            assertTrue(sameNativeObject(native, state.webView))
                            assertTrue(sameNativeObject(native.window, requireOwnedApplicationWindow()))
                            assertNotNull(native.superview)
                            lease.requireDnsAttempt(index) // Also refuse callbacks arriving during the DOM witness.
                        }
                    }
                    runOnIdle { lease.requireBothAttempts() }
                } catch (failure: Throwable) {
                    primary = failure
                    throw failure
                } finally {
                    // Restore only the exact acquired weak-delegate lease. Do not stop
                    // navigation to manufacture DNS success or touch a foreign owner.
                    try { onApplicationMain { lease.restore() } } catch (cleanup: Throwable) {
                        val prior = primary
                        if (prior == null) throw cleanup else if (prior !== cleanup) prior.addSuppressed(cleanup)
                    }
                }
            }
            // runApplicationUiTest performs genuine Compose/WebKit release while its
            // owned UIApplication root remains attached, then restores the prior root.
            onApplicationMain {
                assertNull(state.webView); assertNull(state.nativeObserver); assertNull(state.navigator)
                val released = assertNotNull(retainedNative)
                assertNull(released.navigationDelegate); assertNull(released.superview); assertNull(released.window)
                requireOwnedApplicationWindow()
            }
        } finally { scope.cancel() }
    }

    private fun NativeApplicationUiTest.evaluate(state: WebViewState, script: String): JavascriptResult {
        assertFalse(NSThread.isMainThread)
        var result: JavascriptResult? = null
        var calls = 0
        var offMain = false
        state.evaluateJavascriptResult(script) {
            // Never throw through an asynchronous Objective-C completion handler.
            if (!NSThread.isMainThread) offMain = true
            calls++
            result = it
        }
        waitForNative { result != null || offMain }
        return onApplicationMain {
            assertFalse(offMain, "WebKit completion left the owned main thread")
            assertEquals(1, calls)
            assertNotNull(result)
        }
    }

    private class Attempt(val target: String, val priorErrors: List<WebViewError>) {
        var starts = 0
        var commits = 0
        var finishes = 0
        var committedFailures = 0
        var provisionalFailures = 0
        var navigation: WKNavigation? = null
        var beforeStart: List<WebViewError>? = null
        var afterStart: List<WebViewError>? = null
        var startResetBeforeCommit = false
        var beforeFailure: List<WebViewError>? = null
        var afterFailure: List<WebViewError>? = null
        var error: NSError? = null
        var sameFailureNavigation = false
    }

    private enum class CallbackFault { OffMain, LostOwnedLease, UnarmedCallback, DuplicateStart, ForwardedCallbackFailed }

    /**
     * Test-only observer of normal framework callbacks. It forwards exactly the five
     * callbacks implemented by the acquired production WebViewState; it never constructs
     * or directly schedules a callback/NSError. Strong retention is required because
     * WKWebView.navigationDelegate is weak. All bounded snapshots stay on UIKit main.
     */
    private class DnsForwarder private constructor(
        private val owner: WebViewState,
        private val native: WKWebView,
        private val originalDelegate: WebViewState,
        private val observer: WKWebViewObserver,
        private val window: UIWindow,
    ) : NSObject(), WKNavigationDelegateProtocol {
        private val attempts = mutableListOf<Attempt>() // Exactly two arm operations, not an unbounded event log.
        private var active: Attempt? = null
        private var restored = false
        private var fault: CallbackFault? = null
        val hasFault get() = fault != null
        val hasTerminalCallback get() = active?.let {
            it.provisionalFailures > 0 || it.committedFailures > 0 || it.commits > 0 || it.finishes > 0
        } ?: false

        private fun owns(view: WKWebView): Boolean = !restored &&
            sameNativeObject(view, native) && sameNativeObject(owner.webView, native) &&
            sameNativeObject(view.navigationDelegate as? NSObject, this) &&
            sameNativeObject(owner.nativeObserver, observer) && sameNativeObject(view.window, window) && view.superview != null

        fun arm(index: Int, target: String) {
            assertTrue(NSThread.isMainThread)
            assertTrue(owns(native), "The exact observing delegate lease is no longer owned")
            assertNull(fault, "A normal WK callback violated the bounded observing lease")
            assertTrue(index == attempts.size && index in 0..1, "Only two ordered native DNS link requests are allowed")
            assertFalse(native.loading)
            if (index == 0) assertTrue(owner.errorsForCurrentRequest.isEmpty()) else {
                requireDnsAttempt(0)
                assertTrue(owner.errorsForCurrentRequest == attempts[0].afterFailure,
                    "The first actual native DNS error must survive until the second provisional callback")
            }
            val attempt = Attempt(target, owner.errorsForCurrentRequest.toList())
            attempts += attempt
            active = attempt
        }

        fun requireDnsAttempt(index: Int) {
            assertTrue(NSThread.isMainThread)
            assertTrue(owns(native), "The current native WK/state/observer/window lease changed")
            assertNull(fault, "A normal WK callback violated the bounded observing lease")
            val attempt = attempts[index]
            assertEquals(1, attempt.starts); assertEquals(1, attempt.provisionalFailures)
            assertEquals(0, attempt.commits); assertEquals(0, attempt.finishes); assertEquals(0, attempt.committedFailures)
            assertNotNull(attempt.navigation)
            assertTrue(attempt.sameFailureNavigation, "The actual provisional error belongs to another native navigation")
            assertTrue(attempt.beforeStart == attempt.priorErrors,
                "A content loader or other path pre-cleared the previous error before the real WK start")
            assertTrue(attempt.priorErrors.map { it.code } == if (index == 0) emptyList() else listOf(-1003),
                "The second provisional request must start with exactly the first native DNS error")
            assertTrue(attempt.afterStart?.isEmpty() == true && attempt.startResetBeforeCommit,
                "Previous errors/title/final URL were not reset by the forwarded provisional callback before any commit")
            assertTrue(attempt.beforeFailure?.isEmpty() == true, "An old error remained before the actual DNS failure")
            val error = assertNotNull(attempt.error)
            assertTrue(error.domain == NSURLErrorDomain, "Only the actual NSURLErrorDomain DNS failure is applicable")
            assertTrue(error.code == NSURLErrorCannotFindHost && error.code == -1003L,
                "Only actual provisional CannotFindHost/-1003 is DNS; offline, TLS, timeout or other errors refuse")
            assertTrue(error.localizedDescription.isNotBlank(), "The actual native DNS error description is missing")
            val publicError = assertNotNull(attempt.afterFailure).single()
            assertTrue(publicError.code == -1003 && publicError.description == error.localizedDescription,
                "The public current error is not the actual forwarded native DNS error")
            assertTrue(owner.loadingState == LoadingState.Finished && !native.loading)
            assertTrue(owner.errorsForCurrentRequest == attempt.afterFailure,
                "The terminal public errors must contain only this one actual DNS failure")
        }

        fun requireBothAttempts() {
            assertEquals(2, attempts.size)
            requireDnsAttempt(1)
            assertTrue(!sameNativeObject(attempts[0].navigation, attempts[1].navigation),
                "Two different fresh native link navigations are required")
            assertTrue(attempts.all { it.commits == 0 && it.finishes == 0 && it.committedFailures == 0 })
        }

        fun restore() {
            assertTrue(NSThread.isMainThread)
            assertFalse(restored, "The observing delegate lease was already restored")
            assertTrue(owns(native), "Refuse restoring a foreign native/delegate/observer/window lease")
            native.navigationDelegate = originalDelegate
            assertTrue(sameNativeObject(native.navigationDelegate as? WebViewState, originalDelegate),
                "The exact originally acquired production delegate was not restored")
            restored = true
        }

        private fun noteFault(value: CallbackFault) { if (fault == null) fault = value }
        private fun forward(view: WKWebView, before: (Attempt) -> Unit, callback: () -> Unit, after: (Attempt) -> Unit = {}) {
            // Assertions and exception diagnostics belong on the owning Worker, never
            // across asynchronous framework callback boundaries. No error body is logged.
            if (!NSThread.isMainThread) { noteFault(CallbackFault.OffMain); return }
            if (!owns(view)) { noteFault(CallbackFault.LostOwnedLease); return }
            val attempt = active
            if (attempt == null) noteFault(CallbackFault.UnarmedCallback)
            try {
                if (attempt != null) before(attempt)
                callback() // The only calls to the production delegate are normal framework forwarding below.
                if (attempt != null) after(attempt)
            } catch (_: Throwable) { noteFault(CallbackFault.ForwardedCallbackFailed) }
        }

        @Suppress("PARAMETER_NAME_CHANGED_ON_OVERRIDE")
        @ObjCSignatureOverride
        override fun webView(webView: WKWebView, didStartProvisionalNavigation: WKNavigation?) = forward(webView, before = {
            it.starts++
            if (it.starts != 1) noteFault(CallbackFault.DuplicateStart)
            else { it.navigation = didStartProvisionalNavigation; it.beforeStart = owner.errorsForCurrentRequest.toList() }
        }, callback = { originalDelegate.webView(webView, didStartProvisionalNavigation = didStartProvisionalNavigation) }, after = {
            it.afterStart = owner.errorsForCurrentRequest.toList()
            it.startResetBeforeCommit = it.commits == 0 && owner.errorsForCurrentRequest.isEmpty() &&
                owner.loadingState is LoadingState.Loading && owner.requestedUrl == it.target &&
                owner.lastLoadedUrl == null && owner.pageTitle.isNullOrEmpty()
        })

        @Suppress("PARAMETER_NAME_CHANGED_ON_OVERRIDE")
        @ObjCSignatureOverride
        override fun webView(webView: WKWebView, didCommitNavigation: WKNavigation?) = forward(webView,
            before = { it.commits++ }, callback = { originalDelegate.webView(webView, didCommitNavigation = didCommitNavigation) })

        @Suppress("PARAMETER_NAME_CHANGED_ON_OVERRIDE")
        @ObjCSignatureOverride
        override fun webView(webView: WKWebView, didFinishNavigation: WKNavigation?) = forward(webView,
            before = { it.finishes++ }, callback = { originalDelegate.webView(webView, didFinishNavigation = didFinishNavigation) })

        @Suppress("PARAMETER_NAME_CHANGED_ON_OVERRIDE")
        @ObjCSignatureOverride
        override fun webView(webView: WKWebView, didFailNavigation: WKNavigation?, withError: NSError) = forward(webView,
            before = { it.committedFailures++ }, callback = {
                originalDelegate.webView(webView, didFailNavigation = didFailNavigation, withError = withError)
            })

        @Suppress("PARAMETER_NAME_CHANGED_ON_OVERRIDE")
        @ObjCSignatureOverride
        override fun webView(webView: WKWebView, didFailProvisionalNavigation: WKNavigation?, withError: NSError) = forward(webView,
            before = {
                it.provisionalFailures++
                it.sameFailureNavigation = sameNativeObject(it.navigation, didFailProvisionalNavigation)
                it.beforeFailure = owner.errorsForCurrentRequest.toList()
                it.error = withError // Retain the actual framework NSError, never fabricate or rewrite it.
            }, callback = {
                originalDelegate.webView(webView, didFailProvisionalNavigation = didFailProvisionalNavigation, withError = withError)
            }, after = { it.afterFailure = owner.errorsForCurrentRequest.toList() })

        companion object {
            fun acquire(state: WebViewState, native: WKWebView, window: UIWindow): DnsForwarder {
                assertTrue(NSThread.isMainThread)
                assertTrue(sameNativeObject(state.webView, native) && sameNativeObject(native.window, window))
                assertNotNull(native.superview)
                val original = assertNotNull(native.navigationDelegate as? WebViewState)
                assertTrue(sameNativeObject(original, state), "Only the current production state delegate may be observed")
                val observer = assertNotNull(state.nativeObserver)
                val forwarder = DnsForwarder(state, native, original, observer, window)
                native.navigationDelegate = forwarder
                assertTrue(sameNativeObject(native.navigationDelegate as? NSObject, forwarder))
                return forwarder // Held strongly by the owning test until exact restoration in finally.
            }
        }
    }
}
