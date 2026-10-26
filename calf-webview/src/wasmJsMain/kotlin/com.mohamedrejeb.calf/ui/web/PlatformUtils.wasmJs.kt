// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.web

import kotlin.js.ExperimentalWasmJsInterop
import org.w3c.dom.Window
import org.w3c.dom.events.Event
import org.w3c.dom.events.EventListener

@OptIn(ExperimentalWasmJsInterop::class)
private fun windowEval(window: Window, script: String): JsAny? =
    js("window.eval(script)")

@OptIn(ExperimentalWasmJsInterop::class)
internal actual fun Window.evaluateScript(script: String): Any? =
    windowEval(this, script)

@OptIn(ExperimentalWasmJsInterop::class)
@JsFun("function(epochMillis) { return new Date(epochMillis).toUTCString(); }")
private external fun formatCookieHttpDate(epochMillis: Double): String

internal actual fun cookieHttpDate(epochMillis: Double): String = formatCookieHttpDate(epochMillis)

@OptIn(ExperimentalWasmJsInterop::class)
internal actual fun browserEventListener(handler: (Event) -> Unit): EventListener =
    js("({ handleEvent: handler })")
