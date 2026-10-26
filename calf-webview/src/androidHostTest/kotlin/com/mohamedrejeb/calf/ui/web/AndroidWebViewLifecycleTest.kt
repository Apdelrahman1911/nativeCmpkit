package com.mohamedrejeb.calf.ui.web

import android.content.Context
import android.os.Bundle
import android.webkit.WebBackForwardList
import android.webkit.WebView
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import kotlin.test.*

/** Robolectric validates library ownership/error paths; it is not a Chromium/device UI test. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
class AndroidWebViewLifecycleTest {
    private class TrackedWebView(context: Context) : WebView(context) {
        var stopCalls = 0
        var destroyCalls = 0
        var stopFailure: Throwable? = null
        var destroyFailure: Throwable? = null
        var restoreFailure: Throwable? = null
        override fun stopLoading() { stopCalls++; stopFailure?.let { throw it }; super.stopLoading() }
        override fun destroy() { destroyCalls++; destroyFailure?.let { throw it }; super.destroy() }
        override fun restoreState(inState: Bundle): WebBackForwardList? {
            restoreFailure?.let { throw it }
            return super.restoreState(inState)
        }
    }

    @Test fun throwingOnDisposeCannotRetainOwnedNativeView() {
        val view = TrackedWebView(RuntimeEnvironment.getApplication())
        val state = WebViewState(WebContent.NavigatorOnly)
        state.webView = view
        assertFailsWith<IllegalStateException> {
            releaseAndroidWebView(state, view) { assertSame(view, state.webView); error("application callback") }
        }
        assertEquals(1, view.stopCalls)
        assertEquals(1, view.destroyCalls)
        assertNull(state.webView)
    }

    @Test fun oldViewReleaseDoesNotClearReplacementIdentity() {
        val context = RuntimeEnvironment.getApplication()
        val previous = TrackedWebView(context)
        val replacement = TrackedWebView(context)
        val state = WebViewState(WebContent.NavigatorOnly)
        state.webView = replacement
        releaseAndroidWebView(state, previous) {}
        assertSame(replacement, state.webView)
        releaseAndroidWebView(state, replacement) {}
    }

    @Test fun oldNativeCallbacksCannotUpdateNewState() {
        val context = RuntimeEnvironment.getApplication()
        val previous = TrackedWebView(context)
        val replacement = TrackedWebView(context)
        val state = WebViewState(WebContent.NavigatorOnly)
        state.webView = replacement
        val chrome = AccompanistWebChromeClient().apply { this.state = state }
        chrome.onReceivedTitle(previous, "stale")
        assertNull(state.pageTitle)
        chrome.onReceivedTitle(replacement, "current")
        assertEquals("current", state.pageTitle)
        releaseAndroidWebView(state, previous) {}
        releaseAndroidWebView(state, replacement) {}
    }

    @Test fun resourceErrorsUseOneObservableCollectionInsteadOfRepeatedCopies() {
        val state = WebViewState(WebContent.NavigatorOnly)
        val errors = state.errorsForCurrentRequest
        repeat(1000) { state.mutableErrorsForCurrentRequest.add(WebViewError(it, "resource")) }
        assertSame(errors, state.errorsForCurrentRequest)
        assertEquals(1000, errors.size)
        state.beginRequest("https://example.test")
        assertTrue(errors.isEmpty())
    }

    @Test fun throwingCreationCallbackReleasesViewBeforeFactoryCanReturn() {
        val view = TrackedWebView(RuntimeEnvironment.getApplication())
        val state = WebViewState(WebContent.NavigatorOnly)
        val expected = IllegalStateException("application creation callback")
        val thrown = assertFailsWith<IllegalStateException> {
            createAndroidWebView(state, { view }, {}) {
                assertSame(view, state.webView)
                throw expected
            }
        }
        assertSame(expected, thrown)
        assertNull(state.webView)
        assertEquals(1, view.stopCalls)
        assertEquals(1, view.destroyCalls)
    }

    @Test fun configurationFailureStillDestroysAnUnpublishedNativeView() {
        val view = TrackedWebView(RuntimeEnvironment.getApplication())
        val state = WebViewState(WebContent.NavigatorOnly)
        var callbackCalls = 0
        assertFailsWith<IllegalStateException> {
            createAndroidWebView(state, { view }, { error("native setting failure") }, { callbackCalls++ })
        }
        assertEquals(0, callbackCalls)
        assertEquals(1, view.destroyCalls)
        assertNull(state.webView)
    }

    @Test fun failedRestorationPreservesSavedBundleAndDestroysPartialView() {
        val view = TrackedWebView(RuntimeEnvironment.getApplication()).apply {
            restoreFailure = IllegalStateException("restore failed")
        }
        val saved = Bundle()
        val state = WebViewState(WebContent.NavigatorOnly).apply { viewState = saved }
        var callbackCalls = 0
        assertFailsWith<IllegalStateException> {
            createAndroidWebView(state, { view }, {}, { callbackCalls++ })
        }
        assertSame(saved, state.viewState)
        assertEquals(0, callbackCalls)
        assertEquals(1, view.destroyCalls)
        assertNull(state.webView)
    }

    @Test fun cleanupContinuesAfterStopAndDestroyFailuresAndPreservesCallbackFailure() {
        val stop = IllegalStateException("stop failed")
        val destroy = IllegalArgumentException("destroy failed")
        val primary = IllegalStateException("application disposal failed")
        val view = TrackedWebView(RuntimeEnvironment.getApplication()).apply {
            stopFailure = stop
            destroyFailure = destroy
        }
        val state = WebViewState(WebContent.NavigatorOnly).apply { webView = view }
        val thrown = assertFailsWith<IllegalStateException> {
            releaseAndroidWebView(state, view) { throw primary }
        }
        assertSame(primary, thrown)
        assertEquals(listOf(stop, destroy), thrown.suppressedExceptions)
        assertEquals(1, view.stopCalls)
        assertEquals(1, view.destroyCalls)
        assertNull(state.webView)
        assertEquals(LoadingState.Finished, state.loadingState)
    }
}
