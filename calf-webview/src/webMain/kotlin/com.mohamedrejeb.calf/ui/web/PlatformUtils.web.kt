// Modified for nativeCmpkit (2026-10-25): preserve native listener identity across JS/Wasm.
package com.mohamedrejeb.calf.ui.web

import org.w3c.dom.Window
import org.w3c.dom.events.Event
import org.w3c.dom.events.EventListener

/**
 * Evaluates a JavaScript expression in the given window context.
 * This requires an expect/actual because the eval API differs between JS and WasmJS.
 */
internal expect fun Window.evaluateScript(script: String): Any?

/**
 * Creates one native listener object. Retain it for both addEventListener and removeEventListener;
 * passing a Kotlin function through two interop calls must not decide native callback identity.
 */
internal expect fun browserEventListener(handler: (Event) -> Unit): EventListener
