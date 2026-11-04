// SPDX-License-Identifier: Apache-2.0
@file:Suppress("INVISIBLE_MEMBER", "INVISIBLE_REFERENCE")
@file:OptIn(androidx.compose.ui.ExperimentalComposeUiApi::class)
package com.mohamedrejeb.calf.ui.web

import androidx.compose.runtime.*
import androidx.compose.ui.window.ComposeViewport
import androidx.compose.ui.window.LocalComposeWindow
import kotlinx.browser.document
import kotlinx.browser.window
import kotlinx.coroutines.*
import org.w3c.dom.HTMLElement
import org.w3c.dom.HTMLIFrameElement
import org.w3c.dom.MessageEvent
import kotlin.random.Random
import kotlin.test.*

/** Real Karma HTTP control receipts via trusted messages from exact owned native control frames. */
internal class BrowserContentPolicyFixture(val method: String) {
    companion object {
        const val unicode = "Ελληνικά العربية 漢字 café 🙂"
        fun inline(title: String, relativeResources: Boolean = false) =
            "<!doctype html><meta charset='utf-8'><link rel='icon' href='data:,'><title>$title</title>" +
                "<p id='policy-document'>$unicode</p>" +
                if (relativeResources) "<script src='probe.js'></script><link rel='stylesheet' href='probe.css'><img src='probe.svg'>" else ""
    }
    private val token = Random.nextBytes(16).joinToString("") { (it.toInt() and 255).toString(16).padStart(2, '0') }
    private val origin = window.location.origin.also {
        assertEquals("http:", window.location.protocol)
        assertTrue(window.location.hostname in listOf("localhost", "127.0.0.1"), "No guessed external fixture origin")
        assertTrue(window.location.port.isNotEmpty())
    }
    private var completed = false
    private fun route(kind: String, stage: String) = "$origin/nativecmpkit-content-policy/$token/$kind/$method/$stage"
    fun url(stage: String) = route("page", stage)
    fun baseUrl(stage: String) = route("base", stage) + "/"
    val initialHeaders get() = mapOf("X-NativeCmpKit-Initial" to "fixture-only-$token", "Authorization" to "NativeCmpKitFixture $token")
    fun title(stage: String, count: Int) = "$method-$stage-$count"
    suspend fun open() { assertEquals(1, control("open").getValue("opened")) }
    suspend fun stats(stage: String): Map<String, Int> = control("stats/$stage").also { assertEquals(0, it.getValue("fixture_error")) }
    suspend fun complete() { assertEquals(1, control("done").getValue("done")); completed = true }
    suspend fun close() { if (!completed) { assertEquals(1, control("close").getValue("closed")); completed = true } }
    private suspend fun control(action: String): Map<String, Int> {
        assertTrue(Regex("[a-z0-9/-]{1,80}").matches(action))
        val native = (document.createElement("iframe") as HTMLIFrameElement).apply { style.display = "none" }
        val received = CompletableDeferred<String>()
        val listener = browserEventListener { event ->
            val message = event as? MessageEvent ?: return@browserEventListener
            if (message.source === native.contentWindow && message.origin == origin) {
                if (message.isTrusted) received.complete(message.data.toString())
                else received.completeExceptionally(AssertionError("Synthetic content-policy receipt"))
            }
        }
        window.addEventListener("message", listener)
        var primary: Throwable? = null
        try {
            native.src = route("control", action)
            document.body!!.appendChild(native)
            val text = withTimeout(10_000) { received.await() }
            assertTrue(text.length <= 2300, "Owned content receipt exceeds finite protocol")
            val parts = text.split('|')
            assertEquals(4, parts.size); assertEquals("policy", parts[0]); assertEquals(token, parts[1]); assertEquals(method, parts[2])
            val values = mutableMapOf<String, Int>()
            parts[3].trimEnd('\n').split('\n').forEach { row ->
                assertTrue(Regex("[a-z_]+=[0-9]{1,10}").matches(row), "Unreviewed content receipt")
                val (name, value) = row.split('=')
                assertTrue(name !in values); values[name] = assertNotNull(value.toIntOrNull())
            }
            return values
        } catch (error: Throwable) { primary = error; throw error }
        finally { runWebViewCleanup(primary, { window.removeEventListener("message", listener) }, { native.remove() }) }
    }
}

/** New host reuses the accepted real ComposeWindow disposal mechanism, not a fake DOM teardown. */
internal class BrowserContentPolicyViewport(content: @Composable () -> Unit) {
    private val container = (document.createElement("div") as HTMLElement).apply { style.width = "360px"; style.height = "260px" }
    private var releaseWindow: (() -> Unit)? = null
    private var closed = false
    init {
        try {
            document.body!!.appendChild(container)
            ComposeViewport(container) {
                val own = checkNotNull(LocalComposeWindow.current)
                SideEffect {
                    releaseWindow = { own.dispose() }
                    if (closed) window.setTimeout({ releaseOnce(); null }, 0)
                }
                if (!closed) content()
            }
        } catch (primary: Throwable) { runWebViewCleanup(primary, { close() }) }
    }
    private fun releaseOnce() { val release = releaseWindow ?: return; releaseWindow = null; release() }
    fun close() { closed = true; runWebViewCleanup(null, { releaseOnce() }, { container.remove() }) }
}
