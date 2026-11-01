// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import androidx.compose.ui.awt.ComposeWindow
import javafx.application.Platform
import javafx.concurrent.Worker
import javafx.scene.SnapshotParameters
import javafx.scene.image.WritableImage
import javafx.scene.web.WebView as FxWebView
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import java.awt.GraphicsEnvironment
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import javax.swing.SwingUtilities
import kotlin.math.abs
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

/**
 * NEW, UNCOMPILED, UNEXECUTED: public Compose owner and default JavaFX networking.
 * One isolated worker only; no public network, SSL bypass, manual native outcome,
 * DOM/title-only rendering oracle, or accepted cookie/policy/media test replay.
 */
class DesktopWebViewTlsRenderingAcceptanceTest {
    @Test fun trustedHttpsPaintsTwoAuthoredDocumentsAndUntrustedCertificateFailsBeforeHttpOnTheSameOwner() = runBlocking<Unit> {
        assertEquals("one-selected-class", System.getProperty("nativecmpkit.desktop.security.worker"),
            "The owning finite focus must fork a fresh JVM per selected test class")
        assertEquals(17, Runtime.version().feature(), "Use the owning Java17 runtime, not a substitute")
        assertFalse(GraphicsEnvironment.isHeadless(), "Actual mounted rendering requires a graphical session")
        assertNull(System.getProperty("com.sun.webkit.useHTTP2Loader"), "Retain JavaFX's default Java17 networking choice")
        assertNull(System.getProperty("jdk.internal.httpclient.disableHostnameVerification"), "Never disable hostname checks")

        // Install ordinary PKIX trust before ANY JavaFX creation. HTTP2Loader's static
        // HttpClient captures SSLContext.getDefault(); changing only the legacy
        // HttpsURLConnection factory after engine creation would not test that path.
        OwnedDesktopTlsFixture.create().use { tls ->
            val state = WebViewState(WebContent.NavigatorOnly)
            assertFalse(state.settings.javaScriptEnabled) // Painted CSS needs no page/evaluation JS.
            val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
            var host: VisibleOwner? = null
            var primary: Throwable? = null
            try {
                val mounted = VisibleOwner(state, WebViewNavigator(scope)).also { host = it }
                mounted.awaitCreated()
                val native = onFxThread { assertNotNull(state.webView) }
                onFxThread {
                    assertSame(native, state.webView)
                    assertSame(native, assertNotNull(native.scene).root)
                    assertFalse(native.engine.isJavaScriptEnabled)
                }

                suspend fun awaitFx(description: String, condition: () -> Boolean) {
                    try {
                        withTimeout(20_000) {
                            while (!onFxThread {
                                mounted.assertHealthy(); tls.assertHealthy(); tls.assertTrustLease()
                                assertSame(native, state.webView, "All stages retain the same mounted native engine")
                                assertNotNull(state.owner)
                                condition()
                            }) delay(25)
                        }
                    } catch (timeout: TimeoutCancellationException) {
                        throw AssertionError("Timed out awaiting $description", timeout)
                    }
                }

                suspend fun load(stage: DesktopTlsStage) {
                    tls.assertHealthy(); tls.assertTrustLease()
                    mounted.load(tls.url(stage)) // Public declarative content, real production loader.
                    awaitFx("native start or terminal stage ${stage.name}") {
                        native.engine.location == tls.url(stage) && state.requestedUrl == tls.url(stage) &&
                            native.engine.loadWorker.state !in setOf(Worker.State.READY, Worker.State.CANCELLED)
                    }
                }

                suspend fun awaitPaint(stage: DesktopTlsStage) {
                    // A real next-pulse Node snapshot, NOT a synthesized bitmap or DOM style read.
                    // Two distinct color pairs after two successful HTTPS documents reject
                    // blank/default backing surfaces and a stale preceding document.
                    awaitFx("visible mounted native geometry for ${stage.name}") {
                        native.isVisible && native.width >= 128 && native.height >= 96
                    }
                    withTimeout(20_000) {
                        while (true) {
                            mounted.assertHealthy(); tls.assertHealthy(); tls.assertTrustLease()
                            val result = CompletableDeferred<WritableImage>()
                            onFxThread {
                                assertSame(native, state.webView)
                                assertSame(native, assertNotNull(native.scene).root)
                                assertTrue(native.isVisible && native.width >= 128 && native.height >= 96)
                                native.snapshot({ captured ->
                                    runCatching { result.complete(captured.image) }
                                        .onFailure { result.completeExceptionally(it) }
                                    null
                                }, SnapshotParameters(), null)
                            }
                            val image = result.await()
                            if (hasPaintedPair(image, stage.leftRgb, stage.rightRgb)) break
                            delay(50)
                        }
                    }
                }

                suspend fun awaitTrusted(stage: DesktopTlsStage) {
                    assertTrue(stage.trusted)
                    awaitFx("real successful HTTPS document ${stage.name}") {
                        if (native.engine.loadWorker.state == Worker.State.FAILED) {
                            throw AssertionError("Trusted fixture HTTPS failed", native.engine.loadWorker.exception)
                        }
                        tls.responses(stage) == 1 &&
                            native.engine.loadWorker.state == Worker.State.SUCCEEDED &&
                            native.engine.location == tls.url(stage) && state.lastLoadedUrl == tls.url(stage) &&
                            native.engine.title == tls.title(stage) && state.pageTitle == tls.title(stage) &&
                            state.loadingState == LoadingState.Finished
                    }
                    onFxThread { assertTrue(state.errorsForCurrentRequest.isEmpty()); assertFalse(native.engine.isJavaScriptEnabled) }
                    assertTrue(tls.successfulHandshakes(stage) >= 1, "The authored HTTP document crossed actual TLS")
                    awaitPaint(stage)
                }

                load(DesktopTlsStage.Seed)
                awaitTrusted(DesktopTlsStage.Seed)
                load(DesktopTlsStage.Untrusted)
                awaitFx("actual native certificate failure, not timeout/HTTP status") {
                    if (native.engine.loadWorker.state == Worker.State.SUCCEEDED) {
                        throw AssertionError("The actual engine accepted the untrusted certificate")
                    }
                    native.engine.loadWorker.state == Worker.State.FAILED
                }
                onFxThread {
                    // Both current JavaFX loaders map SSLHandshakeException to this native
                    // LoadWorker error. Do not accept ordinary connection refusal, fabricated
                    // WebViewError, cancellation, or merely 'no response' as TLS rejection.
                    val nativeFailure = assertNotNull(native.engine.loadWorker.exception)
                    assertEquals("SSL handshake failed", nativeFailure.message)
                    assertEquals(LoadingState.Finished, state.loadingState)
                    assertNull(state.lastLoadedUrl)
                    assertEquals(tls.url(DesktopTlsStage.Untrusted), state.requestedUrl)
                    assertEquals(1, state.errorsForCurrentRequest.size)
                    assertEquals(-1, state.errorsForCurrentRequest.single().code)
                    assertEquals(nativeFailure.message, state.errorsForCurrentRequest.single().description)
                }
                assertTrue(tls.handshakeAttempts(DesktopTlsStage.Untrusted) >= 1)
                assertEquals(0, tls.responses(DesktopTlsStage.Untrusted), "No rejected endpoint's HTTP body may reach the engine")
                assertEquals(0, tls.httpRequests(DesktopTlsStage.Untrusted), "Certificate rejection precedes the HTTP request")
                tls.confirmNativeCertificateRejection() // Only after the unchanged native witness and zero-HTTP assertions.

                load(DesktopTlsStage.Recovery)
                awaitTrusted(DesktopTlsStage.Recovery)
                assertEquals(1, mounted.created.get())
                assertEquals(0, mounted.disposed.get())
                mounted.close()
                onFxThread { assertNull(state.webView); assertNull(state.owner) }
            } catch (failure: Throwable) {
                primary = failure
                throw failure
            } finally {
                // Production owner disposal precedes server close, trust restoration and
                // owned certificate removal (the fixture's use/close). Cleanup is never
                // counted as the native certificate rejection or painted-content witness.
                runWebViewCleanup(primary, { host?.close() }, { scope.cancel() })
            }
        }
    }

    private fun hasPaintedPair(image: WritableImage, leftRgb: Int, rightRgb: Int): Boolean {
        val width = image.width.toInt(); val height = image.height.toInt()
        if (width < 128 || height < 96) return false
        val reader = image.pixelReader ?: return false
        fun matches(x: Int, y: Int, expected: Int): Boolean {
            val actual = reader.getArgb(x, y)
            return (actual ushr 24) == 255 && listOf(16, 8, 0).all { shift ->
                abs(((actual ushr shift) and 255) - ((expected ushr shift) and 255)) <= 4
            }
        }
        // Interior patches, far from the half-page boundary: no fonts, driver golden,
        // anti-aliased edges, fixed device-pixel ratio or physical-screen claim.
        return listOf(0.25, 0.5, 0.75).all { fraction ->
            matches((width * 0.2).toInt(), (height * fraction).toInt(), leftRgb) &&
                matches((width * 0.8).toInt(), (height * fraction).toInt(), rightRgb)
        }
    }

    private class VisibleOwner(private val state: WebViewState, navigator: WebViewNavigator) : AutoCloseable {
        val created = AtomicInteger()
        val disposed = AtomicInteger()
        private val ready = CompletableDeferred<Unit>()
        private val failure = AtomicReference<Throwable>()
        private val window = AtomicReference<ComposeWindow?>()
        init {
            try {
                SwingUtilities.invokeAndWait {
                    val owned = ComposeWindow().also { window.set(it) }
                    owned.setSize(480, 320)
                    owned.setContent {
                        WebView(state, Modifier.fillMaxSize(), navigator = navigator,
                            onCreated = {
                                runCatching {
                                    assertTrue(Platform.isFxApplicationThread())
                                    assertNotNull(state.webView); assertNotNull(state.owner)
                                    assertEquals(1, created.incrementAndGet())
                                }.onFailure { failure.compareAndSet(null, it) }
                                ready.complete(Unit)
                            }, onDispose = {
                                runCatching {
                                    assertTrue(Platform.isFxApplicationThread())
                                    assertNotNull(state.webView)
                                    assertEquals(1, disposed.incrementAndGet())
                                }.onFailure { failure.compareAndSet(null, it) }
                            })
                    }
                    owned.isVisible = true
                    assertTrue(owned.isVisible && owned.isShowing)
                }
            } catch (error: Throwable) {
                runWebViewCleanup(error, { close() })
            }
        }
        suspend fun awaitCreated() = withTimeout(30_000) { ready.await(); assertHealthy() }
        fun assertHealthy() { failure.get()?.let { throw it } }
        fun load(url: String) = SwingUtilities.invokeAndWait { state.content = WebContent.Url(url) }
        override fun close() {
            runWebViewCleanup(null,
                { window.getAndSet(null)?.let { owned -> SwingUtilities.invokeAndWait { owned.dispose() } } },
                { runBlocking { withTimeout(10_000) { while (state.webView != null || state.owner != null) delay(25) } } },
                { assertNull(state.webView); assertNull(state.owner) },
                { if (created.get() == 1) assertEquals(1, disposed.get()) },
                { assertHealthy() },
            )
        }
    }
}
