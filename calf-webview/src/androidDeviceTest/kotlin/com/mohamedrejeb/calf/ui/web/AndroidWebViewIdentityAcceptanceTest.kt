// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import android.os.Looper
import android.webkit.WebView as AndroidWebView
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import org.junit.After
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlin.test.*

/** Public library composition and actual Chromium documents, not a shadow or sample application. */
@RunWith(AndroidJUnit4::class)
class AndroidWebViewIdentityAcceptanceTest {
    @get:Rule val compose = createComposeRule()
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    @After fun closeScope() { scope.cancel() }

    @Test fun publicCreationReplacementAndRetainedRemountUseOnlyTheCurrentNativeOwner() {
        val first = state("owner-a")
        val second = state("owner-b")
        var currentState by mutableStateOf(first)
        var currentNavigator by mutableStateOf(WebViewNavigator(scope))
        var generation by mutableStateOf("a")
        var mounted by mutableStateOf(true)
        val observedGeneration = AtomicReference<String>()
        val created = mutableListOf<Pair<String, AndroidWebView>>()
        val disposed = mutableListOf<String>()
        compose.setContent {
            val owner = currentState
            val callbackGeneration = generation
            if (mounted) WebView(owner, Modifier.fillMaxSize(), navigator = currentNavigator,
                onCreated = {
                    assertSame(Looper.getMainLooper(), Looper.myLooper())
                    val native = assertNotNull(owner.webView)
                    assertTrue(native.settings.javaScriptEnabled)
                    assertEquals(owner.settings.androidSettings.textZoom, native.settings.textZoom)
                    assertTrue(created.none { it.second === native }, "Creation cannot expose a predecessor")
                    native.alpha = .875f
                    native.settings.textZoom = 125
                    created += callbackGeneration to native
                }, onDispose = {
                    assertSame(Looper.getMainLooper(), Looper.myLooper())
                    assertNotNull(owner.webView)
                    disposed += callbackGeneration
                })
            SideEffect { observedGeneration.set(callbackGeneration) }
        }
        awaitDocument(first, "owner-a")
        val oldView = compose.runOnIdle {
            val native = assertNotNull(first.webView)
            assertSame(created.single().second, native)
            assertEquals(.875f, native.alpha)
            assertEquals(125, native.settings.textZoom, "Initial common setup cannot overwrite the creation hook")
            first.settings.androidSettings.textZoom = 150
            assertEquals(150, native.settings.textZoom, "An explicit later common setting owns this field")
            native
        }
        val oldNavigator = compose.runOnIdle { currentNavigator }
        val replacement = WebViewNavigator(scope)
        compose.runOnIdle { generation = "latest-a"; currentNavigator = replacement }
        compose.waitUntil(10_000) { observedGeneration.get() == "latest-a" }
        compose.waitForIdle()
        compose.runOnIdle {
            assertSame(oldView, first.webView)
            assertEquals(listOf("a"), created.map { it.first })
            assertTrue(disposed.isEmpty())
            replacement.loadHtml(document("current-navigation"), mimeType = "text/html", encoding = "UTF-8")
        }
        awaitDocument(first, "current-navigation")
        compose.runOnIdle { oldNavigator.loadHtml(document("must-not-load")) }
        assertEquals(JavascriptResult.Value("\"current-navigation\""), evaluate(first, "document.title"))
        compose.runOnIdle { currentState = second }
        awaitDocument(second, "owner-b")
        val secondView = compose.runOnIdle {
            assertNull(first.webView)
            assertNull(oldView.parent)
            assertEquals(listOf("latest-a"), disposed)
            assertEquals(listOf("a", "latest-a"), created.map { it.first })
            assertNotNull(second.webView).also { assertNotSame(oldView, it) }
        }
        compose.runOnIdle { generation = "latest-b" }
        compose.waitUntil(10_000) { observedGeneration.get() == "latest-b" }
        compose.waitForIdle()
        compose.runOnIdle { mounted = false }
        compose.waitUntil(10_000) { compose.runOnUiThread { second.webView == null && secondView.parent == null } }
        compose.runOnIdle {
            assertEquals(listOf("latest-a", "latest-b"), disposed)
            mounted = true
        }
        awaitDocument(second, "owner-b")
        compose.runOnIdle {
            val remounted = assertNotNull(second.webView)
            assertNotSame(oldView, remounted)
            assertNotSame(secondView, remounted)
            assertSame(created.last().second, remounted)
            assertEquals(listOf("a", "latest-a", "latest-b"), created.map { it.first })
            assertEquals(.875f, remounted.alpha)
            assertEquals(125, remounted.settings.textZoom)
            mounted = false
        }
        compose.waitUntil(10_000) { compose.runOnUiThread { second.webView == null } }
        compose.runOnIdle {
            assertEquals(listOf("latest-a", "latest-b", "latest-b"), disposed)
            assertNull(first.webView)
            assertNull(second.webView)
        }
    }

    @Test fun actualChromiumTypedValuesOffMainAndDetachedCallbacksAreExactlyOnce() {
        val owner = state("javascript")
        val navigator = WebViewNavigator(scope)
        var mounted by mutableStateOf(true)
        assertIs<JavascriptResult.Unavailable>(evaluate(owner, "1"))
        compose.setContent { if (mounted) WebView(owner, Modifier.fillMaxSize(), navigator = navigator) }
        awaitDocument(owner, "javascript")
        for ((script, expected) in listOf(
            "'NativeCmpKit'" to JavascriptResult.Value("\"NativeCmpKit\""),
            "42" to JavascriptResult.Value("42"),
            "({answer:42})" to JavascriptResult.Value("{\"answer\":42}"),
            "null" to JavascriptResult.Value("null"),
            "undefined" to JavascriptResult.Undefined,
        )) assertEquals(expected, evaluate(owner, script))
        val error = assertIs<JavascriptResult.Error>(evaluate(owner, "throw new Error('owned-script-error')"))
        assertTrue(error.message.contains("owned-script-error"))
        compose.runOnIdle { owner.settings.javaScriptEnabled = false }
        assertIs<JavascriptResult.Unavailable>(evaluate(owner, "1"))
        compose.runOnIdle { owner.settings.javaScriptEnabled = true }
        assertEquals(JavascriptResult.Value("7"), evaluate(owner, "7"))
        compose.runOnIdle { mounted = false }
        compose.waitUntil(10_000) { compose.runOnUiThread { owner.webView == null } }
        assertIs<JavascriptResult.Unavailable>(evaluate(owner, "1"))
        compose.runOnIdle {
            val expected = OwnedCallbackFailure()
            var calls = 0
            val actual = assertFailsWith<OwnedCallbackFailure> {
                owner.evaluateJavascriptResult("1") { calls++; throw expected }
            }
            assertSame(expected, actual)
            assertEquals(1, calls, "A callback exception is not another script result")
        }
        // Attached throwing-callback/native-invocation boundaries also retain the accepted
        // eight Android-host fault-injection regressions; this is actual value/dispatch evidence.
    }

    private fun awaitDocument(owner: WebViewState, title: String) {
        compose.waitUntil(15_000) {
            compose.runOnUiThread { owner.webView?.title == title && owner.pageTitle == title && owner.loadingState == LoadingState.Finished }
        }
        assertEquals(JavascriptResult.Value("\"$title\""), evaluate(owner, "document.title"))
    }

    private fun evaluate(owner: WebViewState, script: String): JavascriptResult {
        assertNotSame(Looper.getMainLooper(), Looper.myLooper(), "Exercise public dispatch from the instrumentation worker")
        val result = AtomicReference<JavascriptResult>()
        val calls = AtomicInteger()
        owner.evaluateJavascriptResult(script) {
            assertSame(Looper.getMainLooper(), Looper.myLooper())
            assertEquals(0, calls.getAndIncrement(), "Only this invocation's current callback receives one result")
            result.set(it)
        }
        compose.waitUntil(15_000) { result.get() != null }
        return compose.runOnIdle { assertEquals(1, calls.get()); assertNotNull(result.get()) }
    }

    private fun state(title: String) = WebViewState(WebContent.Data(document(title), mimeType = "text/html", encoding = "UTF-8"))
        .apply { settings.javaScriptEnabled = true }
    private fun document(title: String) = "<!doctype html><html><head><title>$title</title></head><body>$title</body></html>"
    private class OwnedCallbackFailure : IllegalStateException("Controlled detached application callback failure")
}
