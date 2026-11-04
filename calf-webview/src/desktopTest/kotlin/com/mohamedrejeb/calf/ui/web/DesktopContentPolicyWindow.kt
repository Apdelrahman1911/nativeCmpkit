// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import androidx.compose.ui.awt.ComposeWindow
import javafx.application.Platform
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import javax.swing.SwingUtilities
import kotlin.test.*

/** New actual public-library remount host. Toolkit/native creation callbacks remain untouched. */
internal class DesktopContentPolicyWindow(val state: WebViewState, val navigator: WebViewNavigator) : AutoCloseable {
    private val ready = CompletableDeferred<Unit>()
    private val failure = AtomicReference<Throwable>()
    private val window = AtomicReference<ComposeWindow?>()
    private val created = AtomicInteger()
    private val disposed = AtomicInteger()
    init {
        try {
            SwingUtilities.invokeAndWait {
                val own = ComposeWindow().also { window.set(it) }
                own.setSize(360, 260)
                own.setContent {
                    WebView(state, Modifier.fillMaxSize(), navigator = navigator, onCreated = {
                        runCatching {
                            assertTrue(Platform.isFxApplicationThread())
                            assertNotNull(state.webView); assertNotNull(state.owner)
                            assertEquals(1, created.incrementAndGet())
                        }.onFailure { failure.compareAndSet(null, it) }
                        ready.complete(Unit)
                    }, onDispose = {
                        runCatching { assertTrue(Platform.isFxApplicationThread()); assertEquals(1, disposed.incrementAndGet()) }
                            .onFailure { failure.compareAndSet(null, it) }
                    })
                }
                own.isVisible = true
                assertTrue(own.isVisible && own.isShowing)
            }
        } catch (primary: Throwable) { runWebViewCleanup(primary, { close() }) }
    }
    fun assertHealthy() { failure.get()?.let { throw it } }
    suspend fun awaitCreated() = withTimeout(30_000) { ready.await(); assertHealthy() }
    suspend fun awaitFx(predicate: () -> Boolean) = withTimeout(15_000) {
        while (!onFxThread { assertHealthy(); predicate() }) delay(15)
    }
    suspend fun evaluate(script: String): JavascriptResult {
        val result = CompletableDeferred<JavascriptResult>()
        state.evaluateJavascriptResult(script) { result.complete(it) }
        return withTimeout(10_000) { result.await() }
    }
    override fun close() {
        runWebViewCleanup(null,
            { window.getAndSet(null)?.let { own -> SwingUtilities.invokeAndWait { own.dispose() } } },
            { runBlocking { withTimeout(10_000) { while (state.webView != null || state.owner != null) delay(15) } } },
            { assertNull(state.webView); assertNull(state.owner) },
            { if (created.get() == 1) assertEquals(1, disposed.get()) },
            { assertHealthy() },
        )
    }
}
