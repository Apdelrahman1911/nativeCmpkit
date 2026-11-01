// SPDX-License-Identifier: Apache-2.0
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
import org.w3c.dom.MessageEvent
import kotlin.random.Random
import kotlin.test.*

/** One literal #64 offline-destination case. No system offline/DNS/TLS or reliable iframe-error claim. */
class BrowserWebViewOfflineDestinationAcceptanceTest {
    @Test fun previouslyReachableOwnedDestinationBecomesOfflineWithoutStoppingKarmaOrRetainingRequestState() = runTest {
        withContext(Dispatchers.Default) {
            val fixture = Fixture()
            var primary: Throwable? = null
            try {
                fixture.open()
                val state = WebViewState(WebContent.Data(html("before-owned-destination"))).apply {
                    // Only the exact host-controlled destination and inline pages opt into Trusted.
                    settings.browserSandboxPolicy = BrowserSandboxPolicy.Trusted
                    settings.javaScriptEnabled = true
                }
                val navigator = WebViewNavigator(this)
                val mounted = Mounted(fixture, state, navigator)
                var mountedFailure: Throwable? = null
                try {
                    val native = mounted.awaitDocument("before-owned-destination")
                    val destination = fixture.destination
                    navigator.loadUrl(destination)
                    mounted.awaitOnlinePage()
                    awaitCondition { state.requestedUrl == destination && state.loadingState == LoadingState.Finished }
                    assertEquals(destination, native.getAttribute("src"))
                    val online = fixture.awaitOnlineReceipt()
                    assertEquals(1, online.pages)
                    assertEquals(1, online.completed)
                    assertEquals(1, mounted.onlinePages)
                    assertTrue(online.listening)
                    assertFalse(online.addressAbsent)
                    assertFalse(online.closeObserved)

                    // A real readable old document, not a retained cross-origin/error document.
                    navigator.loadHtml(html("before-offline-destination"))
                    assertSame(native, mounted.awaitDocument("before-offline-destination"))
                    val oldUrl = assertNotNull(state.lastLoadedUrl)
                    assertEquals("before-offline-destination", state.pageTitle)
                    val offline = fixture.offline()
                    offline.assertAbsent()
                    assertEquals(online.pages, offline.pages)
                    assertEquals(online.completed, offline.completed)
                    assertTrue(offline.controls > online.controls, "The actual Karma control listener stays alive")

                    // Genuine previous-request error; this rejection leaves the actual old inline document intact.
                    navigator.loadHtml(html("rejected-before-offline"), encoding = "iso-8859-1")
                    awaitCondition { state.errorsForCurrentRequest.singleOrNull()?.code == -2 }
                    assertEquals("before-offline-destination", native.contentDocument?.title)
                    val terminalsBefore = mounted.terminalEvents
                    val errorsBefore = mounted.nativeErrors
                    val pagesBefore = mounted.onlinePages
                    navigator.loadUrl(destination) // The SAME previously reachable, now-closed leased URL/port.
                    awaitCondition {
                        mounted.checkEvents()
                        state.requestedUrl == destination && mounted.terminalEvents > terminalsBefore &&
                            state.loadingState == LoadingState.Finished && native.contentDocument == null
                    }
                    assertFalse(native.hasAttribute("srcdoc"))
                    assertEquals(destination, native.getAttribute("src"))
                    assertNull(native.contentDocument, "The old readable document must not survive the failed destination")
                    assertTrue(state.pageTitle.isNullOrEmpty())
                    assertNull(state.lastLoadedUrl)
                    assertNotEquals(oldUrl, state.lastLoadedUrl)
                    assertEquals(pagesBefore, mounted.onlinePages, "No new executable destination bytes after its listener closed")
                    // Chromium may emit load instead of error. Absence is proved by the exact listener/probe receipt,
                    // NEVER inferred from load/Finished. Populate errors only if the real native iframe did so.
                    if (mounted.nativeErrors == errorsBefore) assertTrue(state.errorsForCurrentRequest.isEmpty())
                    else assertEquals(listOf(-1), state.errorsForCurrentRequest.map { it.code })
                    val afterFailure = fixture.receipt()
                    afterFailure.assertAbsent()
                    assertEquals(online.pages, afterFailure.pages)
                    assertEquals(online.completed, afterFailure.completed)
                    assertTrue(afterFailure.controls > offline.controls)

                    navigator.loadHtml(html("after-offline-destination"))
                    assertSame(native, mounted.awaitDocument("after-offline-destination"))
                    assertNull(state.requestedUrl)
                    assertTrue(state.errorsForCurrentRequest.isEmpty())
                    assertEquals("after-offline-destination", state.pageTitle)
                    val recovered = fixture.receipt()
                    recovered.assertAbsent()
                    assertEquals(online.pages, recovered.pages)
                    assertEquals(online.completed, recovered.completed)
                    assertTrue(recovered.controls > afterFailure.controls)
                    mounted.checkEvents()
                } catch (error: Throwable) { mountedFailure = error; throw error }
                finally { withContext(NonCancellable) { preserveCleanupFailure(mountedFailure) {
                    mounted.close()
                    awaitCondition { state.iframe == null && mounted.frame?.isConnected != true }
                } } }
            } catch (error: Throwable) { primary = error; throw error }
            finally { withContext(NonCancellable) { preserveCleanupFailure(primary) { fixture.close() } } }
        }
    }

    private companion object {
        fun html(stage: String) = "<!doctype html><title>$stage</title><p id='nativecmpkit-offline-stage'>$stage</p>" +
            "<script>document.documentElement.setAttribute('data-nativecmpkit-offline-ready','yes')</script>"
        suspend fun awaitCondition(check: () -> Boolean) = withTimeout(15_000) { while (!check()) delay(10) }
        suspend fun preserveCleanupFailure(primary: Throwable?, cleanup: suspend () -> Unit) {
            try { cleanup() } catch (error: Throwable) {
                if (primary == null) throw error
                if (error !== primary) primary.addSuppressed(error)
            }
        }
    }

    private class Mounted(private val fixture: Fixture, private val state: WebViewState, navigator: WebViewNavigator) {
        var frame: HTMLIFrameElement? = null
            private set
        private var eventFailure: Throwable? = null
        var terminalEvents = 0
            private set
        var nativeErrors = 0
            private set
        var onlinePages = 0
            private set
        private val terminalListener = browserEventListener { event ->
            if (!event.isTrusted || event.target !== frame) eventFailure = AssertionError("Non-native offline terminal event")
            terminalEvents++
            if (event.type == "error") nativeErrors++
        }
        private val messageListener = browserEventListener { event ->
            val message = event as? MessageEvent ?: return@browserEventListener
            if (message.source === frame?.contentWindow && message.origin == fixture.destinationOrigin &&
                message.data.toString() == "online|${fixture.token}|${fixture.port}") {
                if (!message.isTrusted) eventFailure = AssertionError("Synthetic offline destination page witness")
                onlinePages++
            }
        }
        private val viewport = Viewport {
            WebView(state, Modifier.size(160.dp), navigator = navigator, onCreated = {
                frame = assertNotNull(state.iframe)
                frame!!.addEventListener("load", terminalListener)
                frame!!.addEventListener("error", terminalListener)
                window.addEventListener("message", messageListener)
            })
        }
        fun checkEvents() { eventFailure?.let { throw it } }
        suspend fun awaitOnlinePage() { awaitCondition { checkEvents(); onlinePages == 1 && frame?.isConnected == true } }
        suspend fun awaitDocument(stage: String): HTMLIFrameElement {
            awaitCondition {
                checkEvents()
                val ready = try {
                    frame?.isConnected == true && frame?.contentDocument?.title == stage &&
                        frame?.contentDocument?.documentElement?.getAttribute("data-nativecmpkit-offline-ready") == "yes" &&
                        frame?.contentDocument?.getElementById("nativecmpkit-offline-stage")?.textContent == stage &&
                        state.pageTitle == stage && state.loadingState == LoadingState.Finished
                } catch (_: Throwable) { false }
                ready
            }
            return assertNotNull(frame)
        }
        fun close() = runWebViewCleanup(null, { viewport.close() },
            { frame?.removeEventListener("load", terminalListener) },
            { frame?.removeEventListener("error", terminalListener) },
            { window.removeEventListener("message", messageListener) })
    }

    private data class Receipt(val pages: Int, val completed: Int, val connections: Int, val responses: Int,
        val listening: Boolean, val addressAbsent: Boolean, val closeObserved: Boolean, val probe: String,
        val controls: Int, val expired: Int) {
        fun assertAbsent() {
            assertFalse(listening); assertTrue(addressAbsent); assertTrue(closeObserved)
            assertEquals(0, connections); assertEquals(0, responses); assertEquals(0, expired)
            assertEquals("ECONNREFUSED", probe, "Actual connect error for the exact previously leased port")
        }
    }
    private class Fixture {
        val token = "ncko" + Random.nextInt(1_000_000_000).toString()
        private val controlOrigin = window.location.origin
        var port: Int = 0
            private set
        val destinationOrigin get() = "http://127.0.0.1:$port"
        val destination get() = "$destinationOrigin/nativecmpkit-offline-destination/$token/page"
        private var leaseAcquired = false
        init {
            check(window.location.protocol == "http:" && window.location.hostname in listOf("localhost", "127.0.0.1") &&
                window.location.port.isNotEmpty()) { "Use only Karma's actual owned HTTP control origin" }
        }
        suspend fun open() {
            val fields = roundTrip("open").split('|')
            assertEquals(5, fields.size); assertEquals("opened", fields[0]); assertEquals(token, fields[1])
            val actualPort = fields[2].toInt()
            assertTrue(actualPort in 1..65535); assertNotEquals(window.location.port.toInt(), actualPort)
            assertEquals("127.0.0.1", fields[3]); assertEquals("1", fields[4])
            port = actualPort
            leaseAcquired = true // Only an exact successful observed lease grants cleanup authority.
        }
        suspend fun close() {
            if (!leaseAcquired) return
            assertEquals("closed|$token|$port|0", roundTrip("close"))
            leaseAcquired = false
        }
        suspend fun offline() = parseReceipt(roundTrip("offline"), "offline")
        suspend fun receipt() = parseReceipt(roundTrip("receipt"), "receipt")
        suspend fun awaitOnlineReceipt(): Receipt = withTimeout(15_000) {
            repeat(16) {
                val current = receipt()
                if (current.pages == 1 && current.completed == 1 && current.connections == 0 && current.responses == 0 &&
                    current.listening && current.expired == 0) return@withTimeout current
                delay(500)
            }
            error("The owned destination did not settle before the finite observation cap")
        }
        private fun parseReceipt(message: String, kind: String): Receipt {
            val fields = message.split('|')
            assertEquals(13, fields.size); assertEquals(kind, fields[0]); assertEquals(token, fields[1])
            assertEquals(port.toString(), fields[2])
            fun count(index: Int) = fields[index].toInt().also { assertTrue(it >= 0) }
            fun flag(index: Int): Boolean { assertTrue(fields[index] in listOf("0", "1")); return fields[index] == "1" }
            return Receipt(count(3), count(4), count(5), count(6), flag(7), flag(8), flag(9), fields[10], count(11), count(12))
        }
        private suspend fun roundTrip(action: String): String {
            val native = (document.createElement("iframe") as HTMLIFrameElement).apply { style.display = "none" }
            val result = CompletableDeferred<String>()
            val listener = browserEventListener { event ->
                val message = event as? MessageEvent ?: return@browserEventListener
                if (message.source === native.contentWindow && message.origin == controlOrigin) {
                    if (message.isTrusted) result.complete(message.data.toString())
                    else result.completeExceptionally(AssertionError("Synthetic offline control receipt"))
                }
            }
            window.addEventListener("message", listener)
            var primary: Throwable? = null
            try {
                val ownedPort = if (action == "open") "" else "&port=$port"
                native.src = "$controlOrigin/nativecmpkit-offline-fixture/$action?token=$token$ownedPort"
                document.body!!.appendChild(native)
                return withTimeout(15_000) { result.await() }
            } catch (error: Throwable) { primary = error; throw error }
            finally { runWebViewCleanup(primary, { window.removeEventListener("message", listener) }, { native.remove() }) }
        }
    }

    /** Reuses the accepted dependency-owned viewport disposal pattern, without changing an accepted test. */
    private class Viewport(content: @Composable () -> Unit) {
        private val container = (document.createElement("div") as HTMLElement).apply { style.width = "320px"; style.height = "240px" }
        private var releaseWindow: (() -> Unit)? = null
        private var closed = false
        init {
            try {
                document.body!!.appendChild(container)
                ComposeViewport(container) {
                    val composeWindow = checkNotNull(LocalComposeWindow.current)
                    SideEffect {
                        releaseWindow = { composeWindow.dispose() }
                        if (closed) window.setTimeout({ releaseOnce(); null }, 0)
                    }
                    if (!closed) content()
                }
            } catch (error: Throwable) {
                try { close() } catch (cleanup: Throwable) { if (cleanup !== error) error.addSuppressed(cleanup) }
                throw error
            }
        }
        private fun releaseOnce() { val release = releaseWindow ?: return; releaseWindow = null; release() }
        fun close() { closed = true; try { releaseOnce() } finally { container.remove() } }
    }
}
