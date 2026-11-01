// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.share

import kotlinx.browser.document
import kotlinx.browser.window
import kotlinx.coroutines.*
import kotlinx.coroutines.selects.select
import kotlinx.coroutines.test.runTest
import org.w3c.dom.HTMLButtonElement
import org.w3c.dom.HTMLIFrameElement
import org.w3c.dom.MessageEvent
import org.w3c.dom.events.Event
import org.w3c.dom.events.EventListener
import kotlin.coroutines.resume
import kotlin.random.Random
import kotlin.test.*

/** Four missing literal #82 C3 paths, not a replay of the accepted controlled-Promise methods.
 *
 * Every child loads the SAME emitted JS/Wasm library test bundle. Its test adapter invokes only
 * the exact selected new method; original accepted test bodies never execute in that child.
 * No clipboard reads, fabricated event dispatch or Runtime.evaluate(userGesture=true).
 */
class WebClipboardEnvironmentAcceptanceTest {
    @Test fun secureContextWithAbsentClipboardApiReportsUnavailableWithoutPlatformCalls() =
        scenario("missing", "secureContextWithAbsentClipboardApiReportsUnavailableWithoutPlatformCalls") {
            assertTrue(clipboardFixtureSecureContext())
            assertTrue(clipboardFixtureApiAvailable(), "The fresh secure child starts with the real browser API")
            clipboardFixtureMaskApi() // Capability-absence branch only; not a native permission claim.
            assertFalse(clipboardFixtureApiAvailable())
            assertFalse(isClipboardSupported())
            assertUnavailableWithoutWrite()
        }

    @Test fun genuinelyInsecureHttpContextHasNoClipboardApiAndReportsUnavailable() =
        scenario("insecure", "genuinelyInsecureHttpContextHasNoClipboardApiAndReportsUnavailable") {
            assertEquals("http:", window.location.protocol)
            assertEquals("nativecmpkit-clipboard-insecure.invalid", window.location.hostname)
            assertFalse(clipboardFixtureSecureContext(), "Actual HTTP non-trustworthy origin, not a shadowed property")
            assertFalse(clipboardFixtureApiAvailable(), "Actual unavailable browser capability in that realm")
            assertFalse(isClipboardSupported())
            assertUnavailableWithoutWrite()
        }

    @Test fun actualDeniedClipboardPermissionRejectsOneTrustedGestureWriteWithoutSuccess() =
        scenario("denied", "actualDeniedClipboardPermissionRejectsOneTrustedGestureWriteWithoutSuccess") {
            assertEquals("denied", permissionState(), "Real PermissionStatus under this document's policy")
            val results = trustedWrite()
            val failed = assertIs<ShareOutcome.Failed>(results.single())
            assertEquals(ShareFailureReason.Platform, failed.reason)
            assertEquals(1, clipboardFixtureValue("calls").toInt())
            assertEquals(0, clipboardFixtureValue("resolved").toInt())
            assertEquals(1, clipboardFixtureValue("rejected").toInt())
            assertEquals("NotAllowedError", clipboardFixtureValue("errorName"))
            assertEquals("DOMException", clipboardFixtureValue("errorType"))
        }

    @Test fun directTrustedGesturePreservesActivationAndCompletesOneActualOwnedTextWrite() =
        scenario("gesture", "directTrustedGesturePreservesActivationAndCompletesOneActualOwnedTextWrite") {
            assertTrue(permissionState() in setOf("prompt", "granted"))
            val results = trustedWrite()
            assertEquals(listOf<ShareOutcome>(ShareOutcome.CopiedToClipboard), results)
            assertEquals(1, clipboardFixtureValue("calls").toInt())
            assertEquals(1, clipboardFixtureValue("resolved").toInt())
            assertEquals(0, clipboardFixtureValue("rejected").toInt())
            assertEquals("", clipboardFixtureValue("errorName"))
        }

    private fun scenario(mode: String, method: String, body: suspend () -> Unit) = runTest {
        withContext(Dispatchers.Default) {
            if (clipboardFixtureMode() == mode) {
                var primary: Throwable? = null
                try {
                    assertEquals(method, clipboardFixtureValue("method"))
                    body()
                    // Real browser jobs, not virtual scheduler advancement; observe unhandled rejections.
                    browserTurn()
                    browserTurn()
                    assertEquals(0, clipboardFixtureValue("unhandled").toInt())
                } catch (error: Throwable) { primary = error; throw error }
                finally {
                    try { assertTrue(clipboardFixtureCleanup(), "Exact native descriptor/listener restoration") }
                    catch (cleanup: Throwable) {
                        val original = primary
                        if (original == null) throw cleanup
                        if (cleanup !== original) original.addSuppressed(cleanup)
                    }
                }
            } else {
                assertEquals("", clipboardFixtureMode(), "A child may not recursively open another realm")
                val child = OwnedChild(mode, method)
                var primary: Throwable? = null
                try { child.execute() } catch (error: Throwable) { primary = error; throw error }
                finally {
                    withContext(NonCancellable) {
                        try { child.close() } catch (cleanup: Throwable) {
                            val original = primary
                            if (original == null) throw cleanup
                            if (cleanup !== original) original.addSuppressed(cleanup)
                        }
                    }
                }
            }
        }
    }

    private fun ownedText() = "NativeCmpKit clipboard " + clipboardFixtureValue("token")

    private fun assertUnavailableWithoutWrite() {
        assertFalse(isWebShareSupported(), "The native Chrome profile must reach the real clipboard fallback")
        val results = mutableListOf<ShareOutcome>()
        val owner = BrowserShareOwner({ ShareOptions() }) { results += it }
        try {
            owner.launch(ShareContent.Text(ownedText()))
            assertIs<ShareOutcome.Unavailable>(results.single())
            assertEquals(0, clipboardFixtureValue("calls").toInt())
            assertEquals(0, clipboardFixtureValue("resolved").toInt())
            assertEquals(0, clipboardFixtureValue("rejected").toInt())
        } finally { owner.dispose() }
    }

    private suspend fun permissionState(): String = suspendCancellableCoroutine { continuation ->
        clipboardFixturePermission { state -> if (continuation.isActive) continuation.resume(state) }
    }

    private suspend fun trustedWrite(): List<ShareOutcome> {
        assertTrue(clipboardFixtureSecureContext())
        assertTrue(clipboardFixtureApiAvailable())
        assertTrue(isClipboardSupported())
        assertFalse(isWebShareSupported(), "Do not substitute/mask navigator.share for native clipboard acceptance")
        assertFalse(clipboardFixtureActivation(), "Fresh document has no prior transient activation")
        clipboardFixtureObserveNativeWrites() // Calls the saved native method and returns the exact original Promise.
        val completed = CompletableDeferred<ShareOutcome>()
        val clicked = CompletableDeferred<Unit>()
        val results = mutableListOf<ShareOutcome>()
        val owner = BrowserShareOwner({ ShareOptions() }) { result ->
            results += result
            completed.complete(result)
        }
        val button = assertNotNull(document.getElementById("nativecmpkit-clipboard-action")) as HTMLButtonElement
        val listener = clipboardEventListener { event ->
            try {
                assertTrue(event.isTrusted, "Only browser-delivered input may trigger the library")
                assertTrue(clipboardFixtureActivation(), "Transient activation must be active at the callsite")
                assertTrue(document.hasFocus(), "The actual native document must be focused")
                assertFalse(clicked.isCompleted, "The native gesture occurs exactly once")
                owner.launch(ShareContent.Text(ownedText())) // No dispatch/suspension before the native write.
                assertTrue(results.isEmpty(), "Even a native Promise must settle before success/failure")
                assertEquals(1, clipboardFixtureValue("calls").toInt())
                clicked.complete(Unit)
            } catch (error: Throwable) {
                clicked.completeExceptionally(error)
                completed.completeExceptionally(error)
            }
        }
        button.addEventListener("click", listener)
        try {
            clipboardFixtureArm()
            withTimeout(15_000) { clicked.await(); completed.await() }
            assertEquals(1, results.size)
            return results.toList()
        } finally {
            owner.dispose()
            button.removeEventListener("click", listener)
        }
    }

    private suspend fun browserTurn() = suspendCancellableCoroutine { continuation ->
        val timer = window.setTimeout({ if (continuation.isActive) continuation.resume(Unit); null }, 0)
        continuation.invokeOnCancellation { window.clearTimeout(timer) }
    }

    private class OwnedChild(private val mode: String, private val method: String) {
        private val token = (1..30).joinToString("") { "abcdefghijklmnopqrstuvwxyz0123456789"[Random.nextInt(36)].toString() }
        private val controlOrigin = window.location.origin
        private val childOrigin = if (mode == "insecure")
            "http://nativecmpkit-clipboard-insecure.invalid:" + window.location.port else controlOrigin
        private val native = (document.createElement("iframe") as HTMLIFrameElement).apply {
            id = "nativecmpkit-clipboard-child-$token"
            style.position = "fixed"; style.left = "0px"; style.top = "0px"
            style.width = "420px"; style.height = "180px"; style.border = "0"
            style.zIndex = "2147483647"
        }
        private val ready = CompletableDeferred<Unit>()
        private val armed = CompletableDeferred<Unit>()
        private val completed = CompletableDeferred<Unit>()
        private var openAttempted = false
        private var listening = false
        private val listener = clipboardEventListener { event ->
            val message = event as? MessageEvent ?: return@clipboardEventListener
            if (message.source !== native.contentWindow || message.origin != childOrigin) return@clipboardEventListener
            val text = message.data.toString()
            val identity = "$token|$mode|$method"
            if (!message.isTrusted) {
                completed.completeExceptionally(AssertionError("Synthetic native clipboard child receipt"))
            } else when {
                text == "ready|$identity" -> ready.complete(Unit)
                text == "armed|$identity" && ready.isCompleted -> armed.complete(Unit)
                text == "done|$identity|passed|0|1" && ready.isCompleted -> completed.complete(Unit)
                text.startsWith("failed|$identity|") -> completed.completeExceptionally(AssertionError(text))
                else -> completed.completeExceptionally(AssertionError("Unknown native clipboard child receipt"))
            }
        }

        suspend fun execute() {
            assertEquals("http://localhost:" + window.location.port, controlOrigin)
            openAttempted = true // The exact token also owns cleanup if an original open reply is lost.
            assertEquals("opened|$token|$mode|$method", roundTrip("open"))
            window.addEventListener("message", listener)
            listening = true
            native.src = "$childOrigin/nativecmpkit-clipboard-fixture/child?token=$token"
            document.body!!.appendChild(native)
            withTimeout(30_000) {
                select<Unit> { ready.onAwait { }; completed.onAwait { error("Child completed before native readiness") } }
                if (mode in setOf("denied", "gesture")) {
                    select<Unit> { armed.onAwait { }; completed.onAwait { error("Child completed without the required native gesture") } }
                    assertEquals("clicked|$token|1", roundTrip("click"))
                }
                completed.await()
            }
        }

        suspend fun close() {
            var failure: Throwable? = null
            try {
                if (openAttempted) {
                    assertEquals("closed|$token|0|0", roundTrip("close"))
                    openAttempted = false
                }
            } catch (error: Throwable) { failure = error }
            finally {
                if (listening) { window.removeEventListener("message", listener); listening = false }
                native.remove()
            }
            if (failure != null) throw failure
        }

        private suspend fun roundTrip(action: String): String {
            val control = (document.createElement("iframe") as HTMLIFrameElement).apply { style.display = "none" }
            val result = CompletableDeferred<String>()
            val received = clipboardEventListener { event ->
                val message = event as? MessageEvent ?: return@clipboardEventListener
                if (message.source === control.contentWindow && message.origin == controlOrigin) {
                    if (message.isTrusted) result.complete(message.data.toString())
                    else result.completeExceptionally(AssertionError("Synthetic clipboard control receipt"))
                }
            }
            window.addEventListener("message", received)
            try {
                val selected = if (action == "open") "&mode=$mode&method=$method" else ""
                control.src = "$controlOrigin/nativecmpkit-clipboard-fixture/$action?token=$token$selected"
                document.body!!.appendChild(control)
                return withTimeout(10_000) { result.await() }
            } finally {
                window.removeEventListener("message", received)
                control.remove()
            }
        }
    }
}

internal expect fun clipboardEventListener(handler: (Event) -> Unit): EventListener
internal expect fun clipboardFixtureMode(): String
internal expect fun clipboardFixtureValue(name: String): String
internal expect fun clipboardFixtureSecureContext(): Boolean
internal expect fun clipboardFixtureActivation(): Boolean
internal expect fun clipboardFixtureApiAvailable(): Boolean
internal expect fun clipboardFixtureMaskApi()
internal expect fun clipboardFixtureObserveNativeWrites()
internal expect fun clipboardFixturePermission(onResult: (String) -> Unit)
internal expect fun clipboardFixtureArm()
internal expect fun clipboardFixtureCleanup(): Boolean
