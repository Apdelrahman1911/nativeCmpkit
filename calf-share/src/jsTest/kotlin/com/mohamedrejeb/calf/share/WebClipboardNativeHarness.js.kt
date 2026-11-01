// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.share

import org.w3c.dom.events.Event
import org.w3c.dom.events.EventListener

internal actual fun clipboardEventListener(handler: (Event) -> Unit): EventListener =
    js("({ handleEvent: handler })")
internal actual fun clipboardFixtureMode(): String =
    js("window.__nativecmpkitClipboardNative ? window.__nativecmpkitClipboardNative.mode : ''").unsafeCast<String>()
internal actual fun clipboardFixtureValue(name: String): String {
    val read = js("(function(name) { var h = window.__nativecmpkitClipboardNative; if (!h) throw new Error('No owned clipboard child'); return String(h[name]); })")
    return read(name).unsafeCast<String>()
}
internal actual fun clipboardFixtureSecureContext(): Boolean =
    js("window.isSecureContext === true").unsafeCast<Boolean>()
internal actual fun clipboardFixtureActivation(): Boolean =
    js("navigator.userActivation != null && navigator.userActivation.isActive === true").unsafeCast<Boolean>()
internal actual fun clipboardFixtureApiAvailable(): Boolean =
    js("navigator.clipboard != null && typeof navigator.clipboard.writeText === 'function'").unsafeCast<Boolean>()
internal actual fun clipboardFixtureMaskApi() { js("window.__nativecmpkitClipboardNative.maskApi()") }
internal actual fun clipboardFixtureObserveNativeWrites() { js("window.__nativecmpkitClipboardNative.observeNativeWrites()") }
internal actual fun clipboardFixturePermission(onResult: (String) -> Unit) {
    val read = js("(function(done) { navigator.permissions.query({name:'clipboard-write'}).then(function(p) { done(p.state); }, function() { done('permission-query-rejected'); }); })")
    read(onResult)
}
internal actual fun clipboardFixtureArm() { js("window.__nativecmpkitClipboardNative.arm()") }
internal actual fun clipboardFixtureCleanup(): Boolean =
    js("window.__nativecmpkitClipboardNative.restore()").unsafeCast<Boolean>()
