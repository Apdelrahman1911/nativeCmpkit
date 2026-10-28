// Test-only access to Compose's own window-disposal handle; no copied renderer or fake applier.
@file:Suppress("INVISIBLE_MEMBER", "INVISIBLE_REFERENCE")
@file:OptIn(androidx.compose.ui.ExperimentalComposeUiApi::class)

package com.mohamedrejeb.calf.ui.web

import androidx.compose.foundation.layout.size
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.ComposeViewport
import androidx.compose.ui.window.LocalComposeWindow
import kotlinx.browser.document
import kotlinx.browser.window
import kotlinx.coroutines.*
import kotlinx.coroutines.test.runTest
import org.w3c.dom.HTMLIFrameElement
import org.w3c.dom.HTMLElement
import org.w3c.dom.events.Event
import kotlin.test.*

/** Public WebView + actual Compose canvas/HTML interop, not just direct BrowserWebViewOwner tests. */
class BrowserWebViewCompositionTest {
    @Test fun disposingThePublicViewportCallsOnceAndReleasesTheActuallyMountedIframe() = runTest {
        withContext(Dispatchers.Default) {
            val state = localContentState()
            val navigator = WebViewNavigator(this)
            var created = 0
            var disposed = 0
            val viewport = Viewport {
                WebView(state, Modifier.size(120.dp), navigator = navigator,
                    onCreated = { assertNotNull(state.iframe); created++ }, onDispose = { disposed++ })
            }
            try {
                val old = awaitMounted(state)
                assertNotNull(state.owner)
                assertEquals(1, created)
                viewport.close()
                awaitCondition { state.iframe == null && !old.isConnected }
                assertNull(state.owner)
                assertEquals(1, disposed)
                viewport.close()
                old.dispatchEvent(Event("load"))
                old.dispatchEvent(Event("error"))
                assertEquals(1, disposed)
                assertTrue(state.errorsForCurrentRequest.isEmpty())
            } finally { viewport.close() }
        }
    }

    @Test fun removingAndRemountingThePublicWebViewCreatesAFreshOwnerInTheSameViewport() = runTest {
        withContext(Dispatchers.Default) {
            val state = localContentState()
            val navigator = WebViewNavigator(this)
            var visible by mutableStateOf(true)
            var created = 0
            var disposed = 0
            val viewport = Viewport {
                if (visible) WebView(state, Modifier.size(120.dp), navigator = navigator,
                    onCreated = { created++ }, onDispose = { disposed++ })
            }
            try {
                val first = awaitMounted(state)
                val firstOwner = assertNotNull(state.owner)
                visible = false
                awaitCondition { state.iframe == null && !first.isConnected }
                assertNull(state.owner)
                assertEquals(1, disposed)
                visible = true
                val second = awaitMounted(state)
                assertNotSame(first, second)
                assertNotSame(firstOwner, state.owner)
                assertEquals(2, created)
                assertEquals(1, disposed)
                viewport.close()
                awaitCondition { state.iframe == null && !second.isConnected }
                assertEquals(2, disposed)
            } finally { viewport.close() }
        }
    }

    @Test fun queuedCapturedOldListenersCannotMutateThePublicReplacementView() = runTest {
        withContext(Dispatchers.Default) {
            val state = localContentState()
            val navigator = WebViewNavigator(this)
            var visible by mutableStateOf(true)
            var disposed = 0
            installBrowserListenerProbe()
            var viewport: Viewport? = null
            var late: Deferred<Unit>? = null
            try {
                viewport = Viewport {
                    if (visible) WebView(state, Modifier.size(120.dp), navigator = navigator, onDispose = { disposed++ })
                }
                val first = awaitMounted(state)
                assertTrue(browserListenerProbeOwns(first))
                val releaseQueuedEvents = CompletableDeferred<Unit>()
                late = async(start = CoroutineStart.UNDISPATCHED) {
                    releaseQueuedEvents.await()
                    first.dispatchEvent(Event("load"))
                    first.dispatchEvent(Event("error"))
                    // Invoke the original objects too, representing callbacks already queued
                    // before native removeEventListener, not only events dispatched afterward.
                    browserListenerProbeDeliverCaptured("load")
                    browserListenerProbeDeliverCaptured("error")
                }
                visible = false
                awaitCondition { state.iframe == null && !first.isConnected }
                assertEquals(2, browserListenerProbeCount("matchedRemovals"))
                assertEquals(1, disposed)
                visible = true
                val second = awaitMounted(state)
                assertNotSame(first, second)
                val replacementOwner = assertNotNull(state.owner)
                val errors = listOf(WebViewError(99, "replacement state"))
                state.loadingState = LoadingState.Loading(.5f)
                state.pageTitle = "replacement title"
                state.lastLoadedUrl = "https://replacement.test/"
                state.errorsForCurrentRequest = errors
                val deliveries = browserListenerProbeCount("deliveries")
                releaseQueuedEvents.complete(Unit)
                withTimeout(5_000) { checkNotNull(late).await() }
                assertEquals(deliveries + 2, browserListenerProbeCount("deliveries"), "Captured callbacks actually ran")
                assertSame(second, state.iframe)
                assertSame(replacementOwner, state.owner)
                assertEquals(LoadingState.Loading(.5f), state.loadingState)
                assertEquals("replacement title", state.pageTitle)
                assertEquals("https://replacement.test/", state.lastLoadedUrl)
                assertEquals(errors, state.errorsForCurrentRequest)
                assertEquals(1, disposed)
            } finally {
                late?.cancel()
                try { viewport?.close() } finally { restoreBrowserListenerProbe() }
            }
        }
    }

    private fun localContentState() = WebViewState(WebContent.Data("<title>mounted</title><p>fixture</p>")).apply {
        // Test-controlled HTML only: readable DOM readiness is intentional, not a security-policy test.
        settings.browserSandboxPolicy = BrowserSandboxPolicy.Trusted
    }

    private suspend fun awaitMounted(state: WebViewState): HTMLIFrameElement {
        awaitCondition {
            val frame = state.iframe
            frame != null && frame.isConnected && frame.contentDocument?.title == "mounted" &&
                state.loadingState == LoadingState.Finished
        }
        return assertNotNull(state.iframe)
    }

    private suspend fun awaitCondition(check: () -> Boolean) = withTimeout(15_000) {
        while (!check()) delay(10)
    }

    /** Uses ComposeViewport itself. Its Unit return isn't misrepresented as a disposable handle. */
    private class Viewport(content: @Composable () -> Unit) {
        private val container = (document.createElement("div") as HTMLElement).apply {
            style.width = "320px"
            style.height = "240px"
        }
        private var releaseWindow: (() -> Unit)? = null
        private var closed = false
        init {
            try {
                document.body!!.appendChild(container)
                ComposeViewport(container) {
                    val composeWindow = checkNotNull(LocalComposeWindow.current)
                    SideEffect {
                        releaseWindow = { composeWindow.dispose() }
                        // Skiko startup may finish after a failed mount timeout. Don't leak that
                        // delayed window or mount library content after this fixture was closed.
                        if (closed) window.setTimeout({ releaseOnce(); null }, 0)
                    }
                    if (!closed) content()
                }
            } catch (error: Throwable) {
                try { close() } catch (cleanup: Throwable) { if (cleanup !== error) error.addSuppressed(cleanup) }
                throw error
            }
        }
        private fun releaseOnce() {
            val release = releaseWindow ?: return
            releaseWindow = null
            release()
        }
        fun close() {
            closed = true
            try { releaseOnce() } finally { container.remove() }
        }
    }
}
