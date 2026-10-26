// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.web

import org.w3c.dom.Window
import org.w3c.dom.events.Event
import org.w3c.dom.events.EventListener

internal actual fun Window.evaluateScript(script: String): Any? =
    asDynamic().eval(script)

internal actual fun cookieHttpDate(epochMillis: Double): String = kotlin.js.Date(epochMillis).toUTCString()

internal actual fun browserEventListener(handler: (Event) -> Unit): EventListener =
    js("({ handleEvent: handler })")
