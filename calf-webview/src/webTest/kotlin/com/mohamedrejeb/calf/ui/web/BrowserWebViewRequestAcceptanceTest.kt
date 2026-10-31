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

/** Only missing #64 browser contracts. Owned TCP refusal is not system-offline certification. */
class BrowserWebViewRequestAcceptanceTest {
    @Test fun rejectedOptionsRetryAndNativeReloadResetErrorsAndRequestedMetadata() = runTest {
        withContext(Dispatchers.Default) { withFixture { fixture ->
            val original = fixture.url("hold", "reload-source")
            val rejected = fixture.url("page", "rejected-headers")
            val state = trustedState(WebContent.Url(original))
            val navigator = WebViewNavigator(this)
            withMounted(fixture, state, navigator) { mounted ->
                mounted.awaitMessage("held", "reload-source", 1)
                assertLoading(state, original)
                assertEquals(1, fixture.receipt()["reload-source"].pending)
                fixture.release("reload-source")
                val native = mounted.awaitDocument("reload-source")
                assertEquals(original, state.lastLoadedUrl)

                // Genuine public API rejection: no unsupported header request is sent.
                state.content = WebContent.Url(rejected, mapOf("X-NativeCmpKit-Reject" to "value"))
                awaitCondition { state.errorsForCurrentRequest.singleOrNull()?.description?.contains("additionalHttpHeaders") == true }
                assertRejected(state, rejected, "additionalHttpHeaders")
                assertEquals("reload-source", native.contentDocument?.title)
                assertEquals(0, fixture.receipt()["rejected-headers"].page)

                navigator.loadHtml(html("rejected-encoding"), encoding = "iso-8859-1")
                awaitCondition { state.errorsForCurrentRequest.singleOrNull()?.description?.contains("encoding") == true }
                assertRejected(state, null, "encoding")
                assertFalse(state.errorsForCurrentRequest.single().description.contains("additionalHttpHeaders"))
                assertEquals("reload-source", native.contentDocument?.title)

                navigator.loadUrl(rejected, mapOf("X-NativeCmpKit-Reject" to "value"))
                awaitCondition { state.requestedUrl == rejected && state.errorsForCurrentRequest.singleOrNull()?.description?.contains("additionalHttpHeaders") == true }
                assertRejected(state, rejected, "additionalHttpHeaders")
                // The rejected request changed common state, NOT the mounted native document.
                assertEquals(original, native.contentWindow?.location?.href)
                navigator.reload()
                mounted.awaitMessage("held", "reload-source", 2)
                assertLoading(state, original, "Native reload must start the actually readable URL, not the last rejected URL")
                val held = fixture.receipt()
                assertEquals(2, held["reload-source"].hold)
                assertEquals(0, held["rejected-headers"].page)
                fixture.release("reload-source")
                assertSame(native, mounted.awaitDocument("reload-source"))
                assertEquals(original, state.requestedUrl)
                assertEquals(original, state.lastLoadedUrl)
                assertTrue(state.errorsForCurrentRequest.isEmpty())

                val retry = fixture.url("page", "retry-success")
                navigator.loadUrl(retry)
                assertSame(native, mounted.awaitDocument("retry-success"))
                assertEquals(retry, state.requestedUrl)
                assertEquals(retry, state.lastLoadedUrl)
                assertTrue(state.errorsForCurrentRequest.isEmpty())
                val receipt = fixture.receipt()
                assertEquals(1, receipt["retry-success"].page)
                assertEquals(2, receipt["reload-source"].holdCompleted)
                receipt.assertIdle()
            }
        } }
    }

    @Test fun realRedirectReloadAndOwnedNativeStopHaveDistinctRequestAndTerminalMetadata() = runTest {
        withContext(Dispatchers.Default) { withFixture { fixture ->
            val state = trustedState(WebContent.Data(html("before-redirect")))
            val navigator = WebViewNavigator(this)
            withMounted(fixture, state, navigator) { mounted ->
                val native = mounted.awaitDocument("before-redirect")
                val redirect = fixture.url("redirect", "redirect-one")
                val terminal = fixture.url("hold", "redirect-one-final")
                state.content = WebContent.Url(redirect)
                mounted.awaitMessage("held", "redirect-one-final", 1)
                assertLoading(state, redirect)
                assertEquals(terminal, native.contentWindow?.location?.href)
                val redirected = fixture.receipt()
                assertEquals(1, redirected["redirect-one"].redirect)
                assertEquals(fixture.path("hold", "redirect-one-final"), redirected.location,
                    "Receipt records the actual emitted Location response header")
                assertEquals(1, redirected["redirect-one-final"].pending)
                fixture.release("redirect-one-final")
                mounted.awaitDocument("redirect-one-final")
                assertEquals(redirect, state.requestedUrl)
                assertEquals(terminal, state.lastLoadedUrl)

                navigator.reload()
                mounted.awaitMessage("held", "redirect-one-final", 2)
                assertLoading(state, terminal)
                fixture.release("redirect-one-final")
                mounted.awaitDocument("redirect-one-final")
                assertEquals(terminal, state.requestedUrl)
                assertEquals(terminal, state.lastLoadedUrl)
                assertEquals(1, fixture.receipt()["redirect-one"].redirect, "Reload is not a replay of the original redirect request")

                val slow = fixture.url("hold", "owned-stop")
                navigator.loadUrl(slow)
                mounted.awaitMessage("held", "owned-stop", 1)
                assertLoading(state, slow)
                assertEquals(1, fixture.receipt()["owned-stop"].pending)
                navigator.stopLoading() // Actual accessible native window.stop(), not a mocked queue acknowledgement.
                awaitCondition { state.loadingState == LoadingState.Finished }
                val stopped = fixture.awaitReceipt { it["owned-stop"].pending == 0 && it["owned-stop"].holdCancelled == 1 }
                assertEquals(0, stopped["owned-stop"].holdCompleted, "The server did not release/complete the stopped response")
                assertEquals(slow, state.requestedUrl)
                assertTrue(state.errorsForCurrentRequest.isEmpty())
                // A native browser may expose its genuinely committed partial title/URL after stop.
                // Finished is not fabricated HTTP/fully-loaded success.
                val recovered = fixture.url("page", "after-stop")
                navigator.loadUrl(recovered)
                assertSame(native, mounted.awaitDocument("after-stop"))
                assertEquals(recovered, state.lastLoadedUrl)
                assertTrue(state.errorsForCurrentRequest.isEmpty())
                fixture.receipt().assertIdle()
            }
        } }
    }

    @Test fun repeatedActualTransportRefusalsCannotRetainOldMetadataOrErrorsDuringRecovery() = runTest {
        withContext(Dispatchers.Default) { withFixture { fixture ->
            val state = trustedState(WebContent.Data(html("before-transport-refusal")))
            val navigator = WebViewNavigator(this)
            withMounted(fixture, state, navigator) { mounted ->
                val native = mounted.awaitDocument("before-transport-refusal")
                val oldUrl = assertNotNull(state.lastLoadedUrl)
                navigator.loadHtml(html("unsupported-before-transport"), encoding = "iso-8859-1")
                awaitCondition { state.errorsForCurrentRequest.singleOrNull()?.code == -2 }
                for ((index, stage) in listOf("abort-one", "abort-two").withIndex()) {
                    val before = mounted.terminalEvents
                    val target = fixture.url("abort", stage)
                    if (index == 0) state.content = WebContent.Url(target) else navigator.loadUrl(target)
                    awaitCondition {
                        mounted.checkEvents()
                        state.requestedUrl == target && mounted.terminalEvents > before &&
                            state.loadingState == LoadingState.Finished && native.contentDocument == null
                    }
                    val refusal = fixture.awaitReceipt { it[stage].abort > 0 && it[stage].abortClosed == it[stage].abort }
                    assertFalse(native.hasAttribute("srcdoc"))
                    assertEquals(target, native.getAttribute("src"))
                    assertNull(native.contentDocument, "The old readable document is not a transport-failure witness")
                    assertTrue(state.pageTitle.isNullOrEmpty())
                    assertNull(state.lastLoadedUrl)
                    assertNotEquals(oldUrl, state.lastLoadedUrl)
                    assertFalse(mounted.hasMessage("page", stage), "An aborted transport never received executable page bytes")
                    assertEquals(0, refusal[stage].page)
                    assertEquals(0, refusal[stage].pending)
                    // Chromium deliberately may fire load rather than error for failed framing/network.
                    // Only errors actually reported by the native iframe may populate this request.
                    assertTrue(state.errorsForCurrentRequest.all { it.code == -1 })
                    assertTrue(state.errorsForCurrentRequest.size <= 1, "A previous request's errors must not accumulate")
                }
                navigator.loadHtml(html("after-transport-refusal"))
                assertSame(native, mounted.awaitDocument("after-transport-refusal"))
                assertNull(state.requestedUrl)
                assertTrue(state.errorsForCurrentRequest.isEmpty())
                assertEquals("after-transport-refusal", state.pageTitle)
                fixture.receipt().assertIdle()
            }
        } }
    }

    private fun trustedState(content: WebContent) = WebViewState(content).apply {
        // Test pages are exclusively host-controlled. No weakening of Isolated/CORS/CSP.
        settings.browserSandboxPolicy = BrowserSandboxPolicy.Trusted
        settings.javaScriptEnabled = true
    }
    private fun assertLoading(state: WebViewState, url: String?, message: String = "") {
        assertEquals(url, state.requestedUrl, message)
        assertTrue(state.loadingState is LoadingState.Loading)
        assertNull(state.pageTitle)
        assertNull(state.lastLoadedUrl)
        assertTrue(state.errorsForCurrentRequest.isEmpty())
    }
    private fun assertRejected(state: WebViewState, url: String?, option: String) {
        assertEquals(url, state.requestedUrl)
        assertEquals(LoadingState.Finished, state.loadingState)
        assertNull(state.pageTitle); assertNull(state.lastLoadedUrl)
        val error = state.errorsForCurrentRequest.single()
        assertEquals(-2, error.code); assertTrue(error.description.contains(option))
    }
    private fun html(stage: String) = "<!doctype html><title>$stage</title><p id='nativecmpkit-request-stage'>$stage</p>" +
        "<script>document.documentElement.setAttribute('data-nativecmpkit-request-ready','yes')</script>"
    private suspend fun awaitCondition(check: () -> Boolean) = withTimeout(15_000) { while (!check()) delay(10) }

    private suspend fun withFixture(block: suspend (Fixture) -> Unit) {
        val fixture = Fixture()
        var primary: Throwable? = null
        try { fixture.open(); block(fixture) } catch (error: Throwable) { primary = error; throw error }
        finally { withContext(NonCancellable) { preserveCleanupFailure(primary) { fixture.close() } } }
    }
    private suspend fun withMounted(fixture: Fixture, state: WebViewState, navigator: WebViewNavigator, block: suspend (Mounted) -> Unit) {
        val mounted = Mounted(fixture, state, navigator)
        var primary: Throwable? = null
        try { block(mounted) } catch (error: Throwable) { primary = error; throw error }
        finally { withContext(NonCancellable) { preserveCleanupFailure(primary) {
            mounted.close()
            awaitCondition { state.iframe == null && mounted.frame?.isConnected != true }
        } } }
    }
    private suspend fun preserveCleanupFailure(primary: Throwable?, cleanup: suspend () -> Unit) {
        try { cleanup() } catch (error: Throwable) {
            if (primary == null) throw error
            if (error !== primary) primary.addSuppressed(error)
        }
    }

    private class Mounted(private val fixture: Fixture, private val state: WebViewState, navigator: WebViewNavigator) {
        var frame: HTMLIFrameElement? = null
            private set
        private var eventFailure: Throwable? = null
        var terminalEvents = 0
            private set
        private val messages = mutableMapOf<String, Int>()
        private val terminalListener = browserEventListener { event ->
            if (!event.isTrusted) eventFailure = AssertionError("Synthetic request terminal event")
            terminalEvents++
        }
        private val messageListener = browserEventListener { event ->
            val message = event as? MessageEvent ?: return@browserEventListener
            if (message.source === frame?.contentWindow && message.origin == fixture.origin) {
                if (!message.isTrusted) eventFailure = AssertionError("Synthetic request page witness")
                val value = message.data.toString()
                if (value.startsWith("held|${fixture.token}|") || value.startsWith("page|${fixture.token}|")) {
                    messages[value] = (messages[value] ?: 0) + 1
                }
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
        fun hasMessage(phase: String, stage: String) = (messages["$phase|${fixture.token}|$stage"] ?: 0) > 0
        suspend fun awaitMessage(phase: String, stage: String, count: Int) = withTimeout(15_000) {
            while ((messages["$phase|${fixture.token}|$stage"] ?: 0) < count) { checkEvents(); delay(10) }
            checkEvents(); assertTrue(frame?.isConnected == true)
        }
        suspend fun awaitDocument(stage: String): HTMLIFrameElement {
            withTimeout(15_000) { while (true) {
                checkEvents()
                val ready = try {
                    frame?.isConnected == true && frame?.contentDocument?.title == stage &&
                        frame?.contentDocument?.documentElement?.getAttribute("data-nativecmpkit-request-ready") == "yes" &&
                        frame?.contentDocument?.getElementById("nativecmpkit-request-stage")?.textContent == stage &&
                        state.pageTitle == stage && state.loadingState == LoadingState.Finished
                } catch (_: Throwable) { false }
                if (ready) break
                delay(10)
            } }
            return assertNotNull(frame)
        }
        fun close() = runWebViewCleanup(null, { viewport.close() },
            { frame?.removeEventListener("load", terminalListener) },
            { frame?.removeEventListener("error", terminalListener) },
            { window.removeEventListener("message", messageListener) })
    }

    private data class Counts(val page: Int = 0, val hold: Int = 0, val redirect: Int = 0, val abort: Int = 0,
        val abortClosed: Int = 0, val holdCompleted: Int = 0, val holdCancelled: Int = 0, val expired: Int = 0, val pending: Int = 0)
    private data class Receipt(val stages: Map<String, Counts>, val location: String) {
        operator fun get(stage: String) = stages[stage] ?: Counts()
        fun assertIdle() { assertTrue(stages.values.all { it.pending == 0 && it.expired == 0 }) }
    }
    private class Fixture {
        val token = "nck" + Random.nextInt(1_000_000_000).toString()
        val origin = window.location.origin
        init {
            check(window.location.protocol == "http:" && window.location.hostname in listOf("localhost", "127.0.0.1") && window.location.port.isNotEmpty()) {
                "Use only Karma's actual owned HTTP origin; no guessed/external socket"
            }
        }
        fun path(action: String, stage: String) = "/nativecmpkit-request-fixture/$action?token=$token&stage=$stage"
        fun url(action: String, stage: String) = origin + path(action, stage)
        private var leaseAcquired = false
        suspend fun open() {
            assertEquals("opened|$token", roundTrip("open", "receipt"))
            leaseAcquired = true
        }
        suspend fun close() {
            // A rejected/colliding open never grants permission to close another session.
            if (!leaseAcquired) return
            assertEquals("closed|$token|0", roundTrip("close", "receipt"))
            leaseAcquired = false
        }
        suspend fun release(stage: String) { assertEquals("released|$token|$stage|1", roundTrip("release", stage)) }
        suspend fun receipt(): Receipt {
            val fields = roundTrip("receipt", "receipt").split('|')
            assertEquals(4, fields.size); assertEquals("receipt", fields[0]); assertEquals(token, fields[1])
            val rows = if (fields[2].isEmpty()) emptyList() else fields[2].split(';')
            val stages = rows.associate { row ->
                val values = row.split(','); assertEquals(10, values.size)
                val numbers = values.drop(1).map { it.toInt().also { count -> assertTrue(count >= 0) } }
                values[0] to Counts(numbers[0], numbers[1], numbers[2], numbers[3], numbers[4], numbers[5], numbers[6], numbers[7], numbers[8])
            }
            assertEquals(rows.size, stages.size, "No duplicate receipt stage")
            return Receipt(stages, fields[3])
        }
        suspend fun awaitReceipt(check: (Receipt) -> Boolean): Receipt = withTimeout(15_000) {
            // At most two waits per session: 64 polls plus fixed controls fit the 128-work budget.
            repeat(32) {
                val current = receipt()
                if (check(current)) return@withTimeout current
                delay(500)
            }
            error("The owned HTTP receipt did not settle within its bounded observation budget")
        }
        private suspend fun roundTrip(action: String, stage: String): String {
            val native = (document.createElement("iframe") as HTMLIFrameElement).apply { style.display = "none" }
            val result = CompletableDeferred<String>()
            val listener = browserEventListener { event ->
                val message = event as? MessageEvent ?: return@browserEventListener
                if (message.source === native.contentWindow && message.origin == origin) {
                    if (message.isTrusted) result.complete(message.data.toString())
                    else result.completeExceptionally(AssertionError("Synthetic request control receipt"))
                }
            }
            window.addEventListener("message", listener)
            var primary: Throwable? = null
            try {
                native.src = url(action, stage); document.body!!.appendChild(native)
                return withTimeout(15_000) { result.await() }
            } catch (error: Throwable) { primary = error; throw error }
            finally { runWebViewCleanup(primary, { window.removeEventListener("message", listener) }, { native.remove() }) }
        }
    }

    /** Same accepted dependency-owned viewport disposal pattern; no accepted test is modified. */
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
