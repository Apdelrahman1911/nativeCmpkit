// SPDX-License-Identifier: Apache-2.0
@file:OptIn(ExperimentalWasmJsInterop::class)
package com.mohamedrejeb.calf.share

import kotlin.js.ExperimentalWasmJsInterop
import org.w3c.dom.events.Event
import org.w3c.dom.events.EventListener

internal actual fun clipboardEventListener(handler: (Event) -> Unit): EventListener =
    js("({ handleEvent: handler })")
@JsFun("function() { return window.__nativecmpkitClipboardNative ? window.__nativecmpkitClipboardNative.mode : ''; }")
private external fun nativeMode(): String
@JsFun("function(name) { var h = window.__nativecmpkitClipboardNative; if (!h) throw new Error('No owned clipboard child'); return String(h[name]); }")
private external fun nativeValue(name: String): String
@JsFun("function() { return window.isSecureContext === true; }")
private external fun nativeSecureContext(): Boolean
@JsFun("function() { return navigator.userActivation != null && navigator.userActivation.isActive === true; }")
private external fun nativeActivation(): Boolean
@JsFun("function() { return navigator.clipboard != null && typeof navigator.clipboard.writeText === 'function'; }")
private external fun nativeApiAvailable(): Boolean
@JsFun("function() { window.__nativecmpkitClipboardNative.maskApi(); }")
private external fun nativeMaskApi()
@JsFun("function() { window.__nativecmpkitClipboardNative.observeNativeWrites(); }")
private external fun nativeObserveWrites()
@JsFun("function(done) { navigator.permissions.query({name:'clipboard-write'}).then(function(p) { done(p.state); }, function() { done('permission-query-rejected'); }); }")
private external fun nativePermission(onResult: (String) -> Unit)
@JsFun("function() { window.__nativecmpkitClipboardNative.arm(); }")
private external fun nativeArm()
@JsFun("function() { return window.__nativecmpkitClipboardNative.restore(); }")
private external fun nativeCleanup(): Boolean

internal actual fun clipboardFixtureMode(): String = nativeMode()
internal actual fun clipboardFixtureValue(name: String): String = nativeValue(name)
internal actual fun clipboardFixtureSecureContext(): Boolean = nativeSecureContext()
internal actual fun clipboardFixtureActivation(): Boolean = nativeActivation()
internal actual fun clipboardFixtureApiAvailable(): Boolean = nativeApiAvailable()
internal actual fun clipboardFixtureMaskApi() = nativeMaskApi()
internal actual fun clipboardFixtureObserveNativeWrites() = nativeObserveWrites()
internal actual fun clipboardFixturePermission(onResult: (String) -> Unit) = nativePermission(onResult)
internal actual fun clipboardFixtureArm() = nativeArm()
internal actual fun clipboardFixtureCleanup(): Boolean = nativeCleanup()
