// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.web

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.mohamedrejeb.calf.ui.web.internal.NativeApplicationUiTest
import com.mohamedrejeb.calf.ui.web.internal.onApplicationMain
import com.mohamedrejeb.calf.ui.web.internal.requireOwnedApplicationWindow
import com.mohamedrejeb.calf.ui.web.internal.runApplicationUiTest
import com.mohamedrejeb.calf.ui.web.internal.sameNativeObject
import com.mohamedrejeb.calf.ui.web.internal.waitForNative
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import platform.Foundation.NSThread
import platform.CoreGraphics.CGRectMake
import platform.UIKit.UIView
import platform.WebKit.WKWebView
import platform.WebKit.WKWebViewConfiguration
import kotlin.test.*

/** Real library-owned WKWebViews, WebKit JavaScript and Compose removal, not mocked delegates. */
class IosWebViewLifecycleAcceptanceTest {
    @Test fun nativeBridgeOwnershipAcceptsCurrentKvoAndDelegateButRejectsForeignAndNullViews() = withScope { scope ->
        val state = WebViewState(WebContent.NavigatorOnly)
        val navigator = WebViewNavigator(scope)
        runApplicationUiTest {
            setContent { WebView(state, Modifier.fillMaxSize(), navigator = navigator) }
            waitForIdle()
            waitForNative { sameNativeObject(state.webView?.window, requireOwnedApplicationWindow()) }
            runOnIdle {
                val current = assertNotNull(state.webView)
                val parent = assertNotNull(current.superview)
                // Retrieve the actual native child through an Objective-C collection, rather
                // than assuming that the original Kotlin factory wrapper is reused by KVO.
                val bridged = parent.subviews.filterIsInstance<WKWebView>().single { sameNativeObject(it, current) }
                assertTrue(hasSameNativeWebView(current, bridged))
                assertFalse(hasSameNativeWebView(null, null))
                assertFalse(hasSameNativeWebView(current, null))
                val foreign = WKWebView(frame = CGRectMake(0.0, 0.0, 1.0, 1.0), configuration = WKWebViewConfiguration())
                try {
                    assertFalse(hasSameNativeWebView(current, foreign))
                    val observer = assertNotNull(state.nativeObserver)
                    state.loadingState = LoadingState.Loading(.5f)
                    observer.observeValueForKeyPath("loading", foreign, null, null)
                    state.webView(foreign, didFinishNavigation = null)
                    assertEquals(LoadingState.Loading(.5f), state.loadingState, "A foreign native callback cannot update this owner")
                    observer.observeValueForKeyPath("loading", bridged, null, null)
                    assertEquals(LoadingState.Finished, state.loadingState)
                    state.loadingState = LoadingState.Loading(.5f)
                    state.webView(bridged, didFinishNavigation = null)
                    assertEquals(LoadingState.Finished, state.loadingState)
                    assertTrue(sameNativeObject(current, state.webView))
                } finally { foreign.stopLoading(); foreign.navigationDelegate = null }
            }
        }
        onApplicationMain { assertNull(state.webView); assertNull(state.nativeObserver); assertNull(state.navigator) }
        // Direct callback inputs above are explicit bridge/ownership checks, not a successful
        // page load. The other six methods still require real WebKit document readiness.
    }

    @Test fun creationHookSeesConfiguredCurrentNativeOwnerAndRemountCannotExposeThePriorView() = withScope { scope ->
        val state = newState("first")
        val navigator = WebViewNavigator(scope)
        val created = mutableListOf<WKWebView>()
        val disposed = mutableListOf<WKWebView>()
        var mounted by mutableStateOf(true)
        runApplicationUiTest {
            setContent {
                if (mounted) WebView(state, Modifier.fillMaxSize(), navigator = navigator,
                    onCreated = {
                        assertTrue(NSThread.isMainThread)
                        val view = assertNotNull(state.webView)
                        assertTrue(sameNativeObject(view.navigationDelegate as? WebViewState, state))
                        assertNotNull(state.nativeObserver)
                        assertTrue(view.configuration.allowsInlineMediaPlayback)
                        assertTrue(view.configuration.defaultWebpagePreferences.allowsContentJavaScript)
                        assertFalse(created.any { sameNativeObject(it, view) })
                        view.alpha = 0.875 // Not a common setting; this native customization must survive.
                        created += view
                    }, onDispose = {
                        assertTrue(NSThread.isMainThread)
                        disposed += assertNotNull(state.webView)
                    })
            }
            awaitDocument(state, "first")
            val first = runOnIdle {
                assertEquals(1, created.size)
                assertEquals(0.875, assertNotNull(state.webView).alpha)
                assertNotNull(state.webView)
            }
            // Keep the real Compose wrapper alive: final child detachment must not
            // depend on wrapper deallocation, autorelease timing or Kotlin GC.
            val retainedParent = runOnIdle { assertNotNull(first.superview) }
            runOnIdle { mounted = false }
            waitForIdle()
            waitForNative { state.webView == null && first.superview == null }
            runOnIdle {
                assertNull(state.webView)
                assertNull(state.nativeObserver)
                assertNull(state.navigator)
                assertNull(first.navigationDelegate)
                assertNull(first.superview)
                assertFalse(retainedParent.subviews.any { sameNativeObject(assertIs<UIView>(it), first) })
                assertEquals(1, disposed.size)
                assertTrue(sameNativeObject(first, disposed.single()))
                state.content = document("remounted")
                mounted = true
            }
            awaitDocument(state, "remounted")
            runOnIdle {
                assertEquals(2, created.size)
                assertFalse(sameNativeObject(first, state.webView))
                assertEquals(0.875, assertNotNull(state.webView).alpha)
            }
        }
        onApplicationMain {
            assertEquals(2, disposed.size)
            assertNull(state.webView)
            assertNull(state.nativeObserver)
            created.forEach { assertNull(it.navigationDelegate); assertNull(it.superview) }
        }
    }

    @Test fun stableCompositionReplacementRebindsCallbacksStateNavigatorAndRealDocument() = withScope { scope ->
        val firstState = newState("owner-a")
        val secondState = newState("owner-b")
        var currentState by mutableStateOf(firstState)
        var currentNavigator by mutableStateOf(WebViewNavigator(scope))
        var generation by mutableStateOf("a")
        val creations = mutableListOf<String>()
        val disposals = mutableListOf<String>()
        runApplicationUiTest {
            setContent {
                // Capture each composition's values, not a mutable variable read at callback time.
                val owner = currentState
                val callbackGeneration = generation
                WebView(owner, Modifier.fillMaxSize(), navigator = currentNavigator,
                    onCreated = { assertNotNull(owner.webView); creations += callbackGeneration },
                    onDispose = { assertNotNull(owner.webView); disposals += callbackGeneration })
            }
            awaitDocument(firstState, "owner-a")
            val firstView = runOnIdle { assertNotNull(firstState.webView) }
            val oldNavigator = runOnIdle { currentNavigator }
            val replacement = WebViewNavigator(scope)
            runOnIdle { generation = "latest-a"; currentNavigator = replacement }
            waitForIdle()
            runOnIdle {
                assertTrue(sameNativeObject(firstView, firstState.webView))
                assertSame(replacement, firstState.navigator)
                assertEquals(firstView.canGoBack, replacement.canGoBack)
                assertEquals(firstView.canGoForward, replacement.canGoForward)
                assertFalse(oldNavigator.canGoBack)
                assertFalse(oldNavigator.canGoForward)
                assertEquals(listOf("a"), creations)
                assertTrue(disposals.isEmpty())
                // Update the existing owner first, so its release must use the latest callback.
                currentState = secondState
            }
            awaitDocument(secondState, "owner-b")
            waitForNative { firstState.webView == null && firstView.superview == null }
            runOnIdle {
                assertEquals(listOf("latest-a"), disposals)
                assertEquals(listOf("a", "latest-a"), creations)
                assertNull(firstState.webView)
                assertNull(firstState.nativeObserver)
                assertNull(firstState.navigator)
                assertNull(firstView.navigationDelegate)
                assertNull(firstView.superview)
                assertFalse(sameNativeObject(firstView, secondState.webView))
                assertTrue(sameNativeObject(assertNotNull(secondState.webView).navigationDelegate as? WebViewState, secondState))
                generation = "latest-b"
            }
            waitForIdle()
            assertEquals(JavascriptResult.Value("\"owner-b\""), evaluate(secondState, "document.title"))
        }
        onApplicationMain {
            assertEquals(listOf("latest-a", "latest-b"), disposals)
            assertNull(firstState.webView)
            assertNull(secondState.webView)
            assertNull(secondState.nativeObserver)
            assertNull(secondState.navigator)
        }
    }

    @Test fun realWebKitResultsDispatchOffMainAndDetachedCallbacksRemainExactlyOnce() = withScope { scope ->
        assertFalse(NSThread.isMainThread)
        val state = newState("javascript")
        val navigator = WebViewNavigator(scope)
        runApplicationUiTest {
            assertIs<JavascriptResult.Unavailable>(evaluate(state, "1"))
            setContent { WebView(state, Modifier.fillMaxSize(), navigator = navigator) }
            awaitDocument(state, "javascript")
            for ((script, expected) in listOf(
                "'NativeCmpKit'" to JavascriptResult.Value("\"NativeCmpKit\""),
                "42" to JavascriptResult.Value("42"),
                "({answer:42})" to JavascriptResult.Value("{\"answer\":42}"),
                "null" to JavascriptResult.Value("null"),
                "undefined" to JavascriptResult.Undefined,
            )) assertEquals(expected, evaluate(state, script))
            val error = assertIs<JavascriptResult.Error>(evaluate(state, "throw new Error('owned-script-error')"))
            assertTrue(error.message.contains("owned-script-error"))
            runOnIdle { state.settings.javaScriptEnabled = false }
            assertIs<JavascriptResult.Unavailable>(evaluate(state, "1"))
            runOnIdle { state.settings.javaScriptEnabled = true }
            assertEquals(JavascriptResult.Value("7"), evaluate(state, "7"))
            setContent {}
            waitForIdle()
            assertIs<JavascriptResult.Unavailable>(evaluate(state, "1"))
            // No native asynchronous callback exception is allowed to cross Objective-C.
            // Before attach/after dispose the documented immediate-main path can be caught.
            runOnIdle {
                var calls = 0
                val original = OwnedCallbackFailure()
                val actual = assertFailsWith<OwnedCallbackFailure> {
                    state.evaluateJavascriptResult("1") { calls++; throw original }
                }
                assertSame(original, actual)
                assertEquals(1, calls, "Application callback failure is never a second script result")
            }
        }
    }

    @Test fun gesturePrecedenceSurvivesEverySettingCombinationRecompositionAndRealContentLoad() = withScope { scope ->
        val state = newState("gestures")
        val navigator = WebViewNavigator(scope)
        var capture by mutableStateOf(true)
        runApplicationUiTest {
            setContent { WebView(state, Modifier.fillMaxSize(), captureBackPresses = capture, navigator = navigator) }
            awaitDocument(state, "gestures")
            val original = runOnIdle { assertNotNull(state.webView) }
            var iteration = 0
            for ((captureFlag, settingFlag) in listOf(false to false, false to true, true to false, true to true)) {
                runOnIdle {
                    capture = captureFlag
                    state.settings.iosSettings.allowsBackForwardNavigationGestures = settingFlag
                    state.content = document("gesture-${++iteration}")
                }
                awaitDocument(state, "gesture-$iteration")
                runOnIdle {
                    assertTrue(sameNativeObject(original, state.webView))
                    assertEquals(captureFlag && settingFlag, original.allowsBackForwardNavigationGestures)
                }
            }
        }
        // This verifies actual WKWebView flags, not physical swipe input or a device matrix.
    }

    @Test fun creationOnlyInlineMediaSettingIsAppliedBeforeConstructionAndRejectsRuntimeMutation() = withScope { scope ->
        for (initial in listOf(false, true)) {
            val state = newState("media-$initial").apply { settings.iosSettings.allowsInlineMediaPlayback = initial }
            val navigator = WebViewNavigator(scope)
            runApplicationUiTest {
                setContent { WebView(state, Modifier.fillMaxSize(), navigator = navigator) }
                awaitDocument(state, "media-$initial")
                val view = runOnIdle {
                    assertNotNull(state.webView).also { assertEquals(initial, it.configuration.allowsInlineMediaPlayback) }
                }
                runOnIdle { state.settings.iosSettings.allowsInlineMediaPlayback = !initial }
                waitForNative { state.errorsForCurrentRequest.any { it.code == -2 && it.description.contains("creation-only") } }
                runOnIdle {
                    assertTrue(sameNativeObject(view, state.webView))
                    assertEquals(initial, view.configuration.allowsInlineMediaPlayback)
                }
            }
            // Explicit new owner/remount applies the desired changed creation-only option.
            val replacement = newState("new-media-$initial").apply { settings.iosSettings.allowsInlineMediaPlayback = !initial }
            runApplicationUiTest {
                setContent { WebView(replacement, Modifier.fillMaxSize(), navigator = navigator) }
                awaitDocument(replacement, "new-media-$initial")
                runOnIdle { assertEquals(!initial, assertNotNull(replacement.webView).configuration.allowsInlineMediaPlayback) }
            }
        }
        // No video playback/fullscreen or physical-device behavior is inferred from these flags.
    }

    @Test fun stateAndNavigatorUnicodeHtmlShareNativeBaseUrlAndUnsupportedOptionsFailVisibly() = withScope { scope ->
        val base = "https://nativecmpkit.invalid/owned/"
        val html = "<!doctype html><title>Nàtive-日本</title><a id='relative' href='child'>link</a>"
        val state = newState("unused").apply { content = WebContent.Data(html, baseUrl = base) }
        val navigator = WebViewNavigator(scope)
        runApplicationUiTest {
            setContent { WebView(state, Modifier.fillMaxSize(), navigator = navigator) }
            awaitDocument(state, "Nàtive-日本")
            assertEquals(JavascriptResult.Value("\"${base}child\""), evaluate(state, "document.getElementById('relative').href"))
            runOnIdle { navigator.loadHtml(html.replace("Nàtive-日本", "navigator-Δ"), baseUrl = base) }
            awaitDocument(state, "navigator-Δ")
            assertEquals(JavascriptResult.Value("\"${base}child\""), evaluate(state, "document.getElementById('relative').href"))
            runOnIdle { navigator.loadHtml("<title>must-not-load</title>", encoding = "utf-16") }
            waitForNative { state.errorsForCurrentRequest.any { it.code == -2 && it.description.contains("encoding") } }
            assertEquals(JavascriptResult.Value("\"navigator-Δ\""), evaluate(state, "document.title"))
            runOnIdle { state.content = WebContent.Data("<title>must-not-load-either</title>", historyUrl = base) }
            waitForNative { state.errorsForCurrentRequest.any { it.code == -2 && it.description.contains("historyUrl") } }
            assertEquals(JavascriptResult.Value("\"navigator-Δ\""), evaluate(state, "document.title"))
        }
        // The base is never fetched. Custom-header/redirect/authentication cases remain separate.
    }

    private fun NativeApplicationUiTest.awaitDocument(state: WebViewState, title: String) {
        waitForIdle()
        try {
            waitForNative {
                val view = state.webView
                view != null && view.title == title && state.pageTitle == title &&
                    !view.loading && state.loadingState == LoadingState.Finished &&
                    sameNativeObject(view.window, requireOwnedApplicationWindow())
            }
        } catch (failure: IllegalStateException) {
            val observed = onApplicationMain {
                val view = state.webView
                // Test-controlled titles and bounded native facts only: no addresses,
                // private app paths, cookies, arbitrary NSError text or console transcript.
                "expected=${title.take(128)}, nativeTitle=${view?.title?.take(128)}, " +
                    "stateTitle=${state.pageTitle?.take(128)}, nativeLoading=${view?.loading}, " +
                    "stateLoading=${state.loadingState}, progress=${view?.estimatedProgress}, " +
                    "nativePresent=${view != null}, parentPresent=${view?.superview != null}, " +
                    "ownedWindow=${sameNativeObject(view?.window, requireOwnedApplicationWindow())}, " +
                    "ownDelegate=${sameNativeObject(view?.navigationDelegate as? WebViewState, state)}, " +
                    "observerPresent=${state.nativeObserver != null}, errors=${state.errorsForCurrentRequest.take(8).map { it.code }}"
            }
            throw IllegalStateException("Real WebKit readiness failed: $observed", failure)
        }
    }

    private fun NativeApplicationUiTest.evaluate(state: WebViewState, script: String): JavascriptResult {
        assertFalse(NSThread.isMainThread, "Public evaluation is deliberately invoked off the native main thread")
        var result: JavascriptResult? = null
        var calls = 0
        state.evaluateJavascriptResult(script) { value ->
            assertTrue(NSThread.isMainThread)
            assertEquals(0, calls, "A result callback must not be called twice")
            calls++
            result = value
        }
        waitForNative { result != null }
        return onApplicationMain { assertEquals(1, calls); assertNotNull(result) }
    }

    private fun newState(title: String) = WebViewState(document(title)).apply { settings.javaScriptEnabled = true }
    private fun document(title: String) = WebContent.Data("<!doctype html><html><head><title>$title</title></head><body>$title</body></html>")
    private fun withScope(block: (CoroutineScope) -> Unit) {
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
        try { block(scope) } finally { scope.cancel() }
    }
    private class OwnedCallbackFailure : IllegalStateException("Intentional caught application callback failure")
}
