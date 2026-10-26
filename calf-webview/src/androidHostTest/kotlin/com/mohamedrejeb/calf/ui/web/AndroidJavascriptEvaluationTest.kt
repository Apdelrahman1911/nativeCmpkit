package com.mohamedrejeb.calf.ui.web

import android.os.Looper
import android.webkit.ValueCallback
import android.webkit.WebView
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import kotlin.test.*

/** Native invocation/callback timing is controlled; no Chromium JavaScript execution is claimed. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
class AndroidJavascriptEvaluationTest {
    private class ControlledWebView : WebView(RuntimeEnvironment.getApplication()) {
        var evaluate: (ValueCallback<String>?) -> Unit = { it?.onReceiveValue("\"v42\"") }
        override fun evaluateJavascript(script: String, resultCallback: ValueCallback<String>?) = evaluate(resultCallback)
    }

    private fun withEvaluator(action: (WebViewState, ControlledWebView) -> Unit) {
        assertSame(Looper.getMainLooper(), Looper.myLooper(), "The actual Android Main dispatch path must execute in this test")
        val view = ControlledWebView().apply { settings.javaScriptEnabled = true }
        val state = WebViewState(WebContent.NavigatorOnly).apply { webView = view }
        try { action(state, view) } finally {
            if (state.webView === view) releaseAndroidWebView(state, view, saveState = false) {}
        }
    }

    @Test fun nativeInvocationFailureBeforeAnyCallbackProducesOneTypedError() = withEvaluator { state, view ->
        view.evaluate = { throw IllegalStateException("native evaluator unavailable") }
        val results = mutableListOf<JavascriptResult>()
        state.evaluateJavascriptResult("42", results::add)
        assertEquals(JavascriptResult.Error("native evaluator unavailable"), results.single())
    }

    @Test fun synchronousCompletionThenNativeThrowCannotDeliverASecondResult() = withEvaluator { state, view ->
        val expected = IllegalStateException("native throw after completion")
        view.evaluate = { callback -> callback!!.onReceiveValue("\"v42\""); throw expected }
        val results = mutableListOf<JavascriptResult>()
        assertSame(expected, assertFailsWith<IllegalStateException> { state.evaluateJavascriptResult("42", results::add) })
        assertEquals(JavascriptResult.Value("42"), results.single())
    }

    @Test fun queuedCompletionAfterSynchronousNativeFailureIsSuppressed() = withEvaluator { state, view ->
        var deferred: ValueCallback<String>? = null
        view.evaluate = { callback -> deferred = callback; throw IllegalStateException("failure after queueing callback") }
        val results = mutableListOf<JavascriptResult>()
        state.evaluateJavascriptResult("42", results::add)
        assertEquals(JavascriptResult.Error("failure after queueing callback"), results.single())
        assertNotNull(deferred).onReceiveValue("\"v42\"")
        assertEquals(1, results.size)
    }

    @Test fun synchronousApplicationFailureIsNotCaughtOrDeliveredTwice() = withEvaluator { state, view ->
        var deferred: ValueCallback<String>? = null
        view.evaluate = { callback -> deferred = callback; callback!!.onReceiveValue("\"v42\"") }
        var calls = 0
        val expected = IllegalArgumentException("application callback")
        assertSame(expected, assertFailsWith<IllegalArgumentException> {
            state.evaluateJavascriptResult("42") { calls++; throw expected }
        })
        assertNotNull(deferred).onReceiveValue("\"v42\"")
        assertEquals(1, calls)
    }

    @Test fun asynchronousApplicationFailureIsNotReclassifiedAndDuplicateIsIgnored() = withEvaluator { state, view ->
        var deferred: ValueCallback<String>? = null
        view.evaluate = { deferred = it }
        var calls = 0
        val expected = IllegalArgumentException("asynchronous application callback")
        state.evaluateJavascriptResult("42") { calls++; throw expected }
        assertEquals(0, calls)
        assertSame(expected, assertFailsWith<IllegalArgumentException> { assertNotNull(deferred).onReceiveValue("\"v42\"") })
        assertNotNull(deferred).onReceiveValue("\"v42\"")
        assertEquals(1, calls)
    }

    @Test fun asynchronousNativeThrowAfterCompletionRemainsOutsideResultHandling() = withEvaluator { state, view ->
        val expected = IllegalStateException("native async dispatch failed after callback")
        var deliver: (() -> Unit)? = null
        view.evaluate = { callback -> deliver = { callback!!.onReceiveValue("\"v42\""); throw expected } }
        val results = mutableListOf<JavascriptResult>()
        state.evaluateJavascriptResult("42", results::add)
        assertTrue(results.isEmpty())
        assertSame(expected, assertFailsWith<IllegalStateException> { assertNotNull(deliver).invoke() })
        assertEquals(JavascriptResult.Value("42"), results.single())
    }

    @Test fun callbackWhichArrivesAfterNativeOwnerReleaseReportsUnavailableOnce() = withEvaluator { state, view ->
        var deferred: ValueCallback<String>? = null
        view.evaluate = { deferred = it }
        val results = mutableListOf<JavascriptResult>()
        state.evaluateJavascriptResult("42", results::add)
        releaseAndroidWebView(state, view, saveState = false) {}
        assertNotNull(deferred).onReceiveValue("\"v42\"")
        assertIs<JavascriptResult.Unavailable>(results.single())
        assertNotNull(deferred).onReceiveValue("\"v42\"")
        assertEquals(1, results.size)
    }

    @Test fun legacyInvocationFailureIsOneNullAndLaterNativeCallbackIsIgnored() = withEvaluator { state, view ->
        var deferred: ValueCallback<String>? = null
        view.evaluate = { callback -> deferred = callback; throw IllegalStateException("native failure") }
        val results = mutableListOf<String?>()
        state.evaluateJavascript("42", results::add)
        assertEquals<List<String?>>(listOf(null), results)
        assertNotNull(deferred).onReceiveValue("42")
        assertEquals(1, results.size)
    }
}
