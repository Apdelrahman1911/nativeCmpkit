// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.awt.ComposeWindow
import javafx.application.Platform
import javafx.embed.swing.JFXPanel
import javafx.scene.web.WebView as FxWebView
import kotlinx.coroutines.*
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import javax.swing.SwingUtilities
import kotlin.test.*

/** Genuine public Compose windows and JavaFX WebKit; no replacement native engine or sample. */
class DesktopWebViewIdentityAcceptanceTest {
    @Test fun publicCreationReplacementAndRetainedRemountUseOnlyTheCurrentNativeOwner() = runBlocking {
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
        val first = state("owner-a")
        val second = state("owner-b")
        val host = WindowHost(first, WebViewNavigator(scope))
        try {
            // Public composition creates JFXPanel asynchronously. Its real onCreated
            // callback, not test order or an artificial Platform.startup, proves FX ready.
            host.awaitCreation(first)
            host.awaitDocument(first, "owner-a")
            val oldView = onFxThread {
                val native = assertNotNull(first.webView)
                assertSame(host.created.single().native, native)
                assertEquals(1.25, native.fontScale)
                assertEquals("NativeCmpKit-creation", native.engine.userAgent,
                    "Initial common settings cannot overwrite creation customization")
                native
            }
            host.update { first.settings.desktopSettings.customUserAgent = "NativeCmpKit-common" }
            awaitFx { oldView.engine.userAgent == "NativeCmpKit-common" }
            val oldNavigator = host.navigator
            val replacement = WebViewNavigator(scope)
            host.update { generation = "latest-a"; navigator = replacement }
            host.awaitGeneration("latest-a")
            onFxThread {
                assertSame(oldView, first.webView)
                assertEquals(listOf("a"), host.created.map { it.generation })
                assertTrue(host.disposed.isEmpty())
            }
            replacement.loadHtml(html("current-navigation"))
            host.awaitDocument(first, "current-navigation")
            oldNavigator.loadHtml(html("must-not-load"))
            delay(50)
            assertEquals(JavascriptResult.Value("\"current-navigation\""), evaluate(first, "document.title"))
            host.update { owner = second }
            host.awaitDocument(second, "owner-b")
            val secondView = onFxThread {
                assertNull(first.webView)
                assertNull(first.owner)
                assertEquals(listOf("latest-a"), host.disposed.toList())
                assertEquals(listOf("a", "latest-a"), host.created.map { it.generation })
                assertNotNull(second.webView).also { assertNotSame(oldView, it) }
            }
            host.update { generation = "latest-b" }
            host.awaitGeneration("latest-b")
            host.update { mounted = false }
            awaitFx { second.webView == null && second.owner == null }
            assertEquals(listOf("latest-a", "latest-b"), host.disposed.toList())
            host.update { mounted = true }
            host.awaitDocument(second, "owner-b")
            onFxThread {
                val remounted = assertNotNull(second.webView)
                assertNotSame(oldView, remounted)
                assertNotSame(secondView, remounted)
                assertSame(host.created.last().native, remounted)
                assertEquals(1.25, remounted.fontScale)
                assertEquals("NativeCmpKit-creation", remounted.engine.userAgent)
                assertEquals(listOf("a", "latest-a", "latest-b"), host.created.map { it.generation })
            }
            host.close()
            assertEquals(listOf("latest-a", "latest-b", "latest-b"), host.disposed.toList())
            onFxThread { assertNull(first.webView); assertNull(second.webView); assertNull(second.owner) }
        } finally { try { host.close() } finally { scope.cancel() } }
    }

    @Test fun rapidReplacementBeforeRealFxCreationAndNavigationCannotResurrectDiscardedOwners() = runBlocking {
        val states = listOf(state("discarded-a"), state("discarded-b"), state("current"))
        val panels = mutableListOf<JFXPanel>()
        SwingUtilities.invokeAndWait { repeat(3) { panels += JFXPanel() } }
        Platform.setImplicitExit(false)
        val creations = List(3) { AtomicInteger() }
        val disposals = List(3) { AtomicInteger() }
        val navigators = List(3) { WebViewNavigator(this) }
        val owners = states.mapIndexed { index, state ->
            DesktopWebViewOwner(state, panels[index], { navigators[index] },
                { creations[index].incrementAndGet() }, { disposals[index].incrementAndGet() })
        }
        val entered = CountDownLatch(1)
        val release = CountDownLatch(1)
        val pending = mutableListOf<Job>()
        try {
            Platform.runLater { entered.countDown(); check(release.await(10, TimeUnit.SECONDS)) }
            assertTrue(entered.await(10, TimeUnit.SECONDS), "The real FX queue must actually be held before replacement")
            for (index in 0..1) {
                owners[index].create()
                pending += launch(start = CoroutineStart.UNDISPATCHED) { owners[index].load(WebContent.Data(html("must-not-load-$index"))) }
                owners[index].dispose()
            }
            owners[2].create()
            pending += launch(start = CoroutineStart.UNDISPATCHED) { owners[2].load(WebContent.Data(html("current"))) }
            release.countDown()
            withTimeout(10_000) { pending.joinAll() }
            awaitFx { states[2].webView?.engine?.title == "current" && states[2].pageTitle == "current" }
            onFxThread {
                for (index in 0..1) { assertNull(states[index].webView); assertNull(states[index].owner); assertNull(panels[index].scene) }
                assertSame(owners[2], states[2].owner)
                assertEquals(listOf(0, 0, 1), creations.map { it.get() })
                assertEquals(listOf(0, 0, 0), disposals.map { it.get() }, "Uncreated owners cannot fabricate disposal callbacks")
            }
        } finally {
            release.countDown()
            pending.forEach { it.cancelAndJoin() }
            owners.forEach { it.dispose() }
            onFxThread {
                states.forEach { assertNull(it.webView); assertNull(it.owner) }
                panels.forEach { assertNull(it.scene) }
            }
        }
        assertEquals(listOf(0, 0, 1), disposals.map { it.get() })
        // Queue inputs are controlled, but JFXPanel/WebView/WebEngine/Scene and queued native
        // work are genuine; the other method separately verifies public composition replacement.
    }

    @Test fun actualFxTypedValuesOffMainAndThrowingOrDetachedCallbacksAreExactlyOnce() = runBlocking {
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
        val owner = state("javascript")
        assertIs<JavascriptResult.Unavailable>(evaluate(owner, "1"))
        val host = WindowHost(owner, WebViewNavigator(scope))
        try {
            host.awaitDocument(owner, "javascript")
            for ((script, expected) in listOf(
                "'NativeCmpKit'" to JavascriptResult.Value("\"NativeCmpKit\""),
                "42" to JavascriptResult.Value("42"),
                "({answer:42})" to JavascriptResult.Value("{\"answer\":42}"),
                "null" to JavascriptResult.Value("null"),
                "undefined" to JavascriptResult.Undefined,
            )) assertEquals(expected, evaluate(owner, script))
            val error = assertIs<JavascriptResult.Error>(evaluate(owner, "throw new Error('owned-script-error')"))
            assertTrue(error.message.contains("owned-script-error"))
            val expected = OwnedCallbackFailure()
            val observed = CompletableDeferred<Throwable>()
            val calls = AtomicInteger()
            var previous: Thread.UncaughtExceptionHandler? = null
            onFxThread {
                previous = Thread.currentThread().uncaughtExceptionHandler
                Thread.currentThread().uncaughtExceptionHandler = Thread.UncaughtExceptionHandler { thread, failure ->
                    if (failure === expected) observed.complete(failure)
                    else { observed.completeExceptionally(failure); previous?.uncaughtException(thread, failure) }
                }
            }
            try {
                owner.evaluateJavascriptResult("1") { calls.incrementAndGet(); throw expected }
                assertSame(expected, withTimeout(10_000) { observed.await() })
                onFxThread { assertEquals(1, calls.get(), "Callback failure cannot be delivered as another script result") }
            } finally { onFxThread { Thread.currentThread().uncaughtExceptionHandler = previous } }
            host.update { owner.settings.javaScriptEnabled = false }
            assertIs<JavascriptResult.Unavailable>(evaluate(owner, "1"))
            host.update { owner.settings.javaScriptEnabled = true }
            awaitFx { owner.webView?.engine?.isJavaScriptEnabled == true }
            assertEquals(JavascriptResult.Value("7"), evaluate(owner, "7"))
            host.close()
            assertIs<JavascriptResult.Unavailable>(evaluate(owner, "1"))
            var detachedCalls = 0
            val detached = assertFailsWith<OwnedCallbackFailure> {
                owner.evaluateJavascriptResult("1") { detachedCalls++; throw expected }
            }
            assertSame(expected, detached)
            assertEquals(1, detachedCalls)
        } finally { try { host.close() } finally { scope.cancel() } }
    }

    private suspend fun evaluate(owner: WebViewState, script: String): JavascriptResult {
        assertFalse(Platform.isFxApplicationThread(), "Invoke actual native evaluation from the test worker")
        val result = CompletableDeferred<JavascriptResult>()
        val calls = AtomicInteger()
        owner.evaluateJavascriptResult(script) {
            // Unavailable-without-native-work retains its documented immediate caller path.
            if (it !is JavascriptResult.Unavailable) assertTrue(Platform.isFxApplicationThread())
            assertEquals(0, calls.getAndIncrement(), "This invocation's current callback receives exactly one result")
            result.complete(it)
        }
        val value = withTimeout(15_000) { result.await() }
        assertEquals(1, calls.get())
        return value
    }
    private suspend fun awaitFx(check: () -> Boolean) = withTimeout(20_000) { while (!onFxThread(check)) delay(10) }
    private fun state(title: String) = WebViewState(WebContent.Data(html(title))).apply { settings.javaScriptEnabled = true }
    private fun html(title: String) = "<!doctype html><html><head><title>$title</title></head><body>$title</body></html>"
    private class OwnedCallbackFailure : IllegalStateException("Controlled real FX application callback failure")
    private data class Creation(val generation: String, val state: WebViewState, val native: FxWebView)

    private class WindowHost(initial: WebViewState, initialNavigator: WebViewNavigator) : AutoCloseable {
        var owner by mutableStateOf(initial)
        var navigator by mutableStateOf(initialNavigator)
        var generation by mutableStateOf("a")
        var mounted by mutableStateOf(true)
        val created = CopyOnWriteArrayList<Creation>()
        val disposed = CopyOnWriteArrayList<String>()
        private val observedGeneration = AtomicReference<String>()
        private val failure = AtomicReference<Throwable>()
        private val window = AtomicReference<ComposeWindow?>()
        init {
            try { SwingUtilities.invokeAndWait {
                val view = ComposeWindow(); window.set(view); view.setSize(320, 240)
                view.setContent {
                    val currentOwner = owner
                    val callbackGeneration = generation
                    if (mounted) WebView(currentOwner, Modifier.fillMaxSize(), navigator = navigator,
                        onCreated = {
                            try {
                                assertTrue(Platform.isFxApplicationThread())
                                val native = assertNotNull(currentOwner.webView)
                                assertNotNull(currentOwner.owner)
                                assertTrue(native.engine.isJavaScriptEnabled)
                                assertTrue(created.none { it.native === native })
                                native.fontScale = 1.25
                                native.engine.userAgent = "NativeCmpKit-creation"
                                created += Creation(callbackGeneration, currentOwner, native)
                            } catch (error: Throwable) { failure.compareAndSet(null, error); throw error }
                        }, onDispose = {
                            try {
                                assertTrue(Platform.isFxApplicationThread())
                                assertNotNull(currentOwner.webView)
                                disposed += callbackGeneration
                            } catch (error: Throwable) { failure.compareAndSet(null, error); throw error }
                        })
                    SideEffect { observedGeneration.set(callbackGeneration) }
                }
                view.isVisible = true
            } } catch (error: Throwable) {
                try { close() } catch (cleanup: Throwable) { if (cleanup !== error) error.addSuppressed(cleanup) }
                throw error
            }
        }
        fun update(action: WindowHost.() -> Unit) = SwingUtilities.invokeAndWait { action() }
        suspend fun awaitCreation(state: WebViewState) = withTimeout(20_000) {
            while (created.none { it.state === state }) { failure.get()?.let { throw it }; delay(10) }
        }
        suspend fun awaitGeneration(expected: String) = withTimeout(10_000) {
            while (observedGeneration.get() != expected) { failure.get()?.let { throw it }; delay(10) }
        }
        suspend fun awaitDocument(state: WebViewState, title: String) = withTimeout(20_000) {
            while (!onFxThread {
                failure.get()?.let { throw it }
                state.webView?.engine?.title == title && state.pageTitle == title && state.loadingState == LoadingState.Finished
            }) delay(10)
        }
        override fun close() {
            window.getAndSet(null)?.let { view ->
                SwingUtilities.invokeAndWait { view.dispose() }
                runBlocking { withTimeout(10_000) {
                    while (!onFxThread { created.all { it.state.webView == null && it.state.owner == null } }) delay(10)
                } }
            }
            failure.get()?.let { throw it }
        }
    }
}
