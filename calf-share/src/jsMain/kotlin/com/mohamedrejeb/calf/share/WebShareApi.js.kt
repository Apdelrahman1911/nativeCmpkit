// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.share

import kotlinx.browser.window

internal actual fun isWebShareSupported(): Boolean =
    js("window.isSecureContext === true && typeof navigator.share === 'function'").unsafeCast<Boolean>()
internal actual fun isClipboardSupported(): Boolean =
    js("window.isSecureContext === true && navigator.clipboard != null && typeof navigator.clipboard.writeText === 'function'").unsafeCast<Boolean>()

internal actual fun webShareText(text: String, title: String?, onResult: (WebShareResult) -> Unit) {
    val data = js("({})")
    data.text = text
    if (title != null) data.title = title
    performShare(data, false, onResult)
}
internal actual fun webShareUrl(url: String, title: String?, onResult: (WebShareResult) -> Unit) {
    val data = js("({})")
    data.url = url
    if (title != null) data.title = title
    performShare(data, false, onResult)
}
internal actual fun webShareFile(file: org.w3c.files.File, title: String?, onResult: (WebShareResult) -> Unit) =
    webShareFiles(listOf(file), title, onResult)
internal actual fun webShareFiles(files: List<org.w3c.files.File>, title: String?, onResult: (WebShareResult) -> Unit) {
    val data = js("({})")
    data.files = files.toTypedArray()
    if (title != null) data.title = title
    performShare(data, true, onResult)
}

private fun performShare(data: dynamic, files: Boolean, onResult: (WebShareResult) -> Unit) {
    val navigator = window.navigator.asDynamic()
    val available = try {
        isWebShareSupported() && (!files || (js("typeof navigator.canShare === 'function'").unsafeCast<Boolean>() && navigator.canShare(data) == true))
    } catch (_: Throwable) { false }
    if (!available) { onResult(WebShareResult.Unavailable); return }
    val promise = try { navigator.share(data) } catch (_: Throwable) { null }
    if (promise == null) { onResult(WebShareResult.Failed); return }
    // Two settlement handlers, not then(callback).catch(callback): application exceptions must
    // never be caught as a second platform result.
    promise.then(
        { _: dynamic -> onResult(WebShareResult.Completed) },
        { error: dynamic -> onResult(if (error?.name == "AbortError") WebShareResult.Dismissed else WebShareResult.Failed) },
    )
}

internal actual fun copyToClipboard(text: String, onResult: (Boolean) -> Unit) {
    val promise = try {
        if (isClipboardSupported()) window.navigator.asDynamic().clipboard.writeText(text) else null
    } catch (_: Throwable) { null }
    if (promise == null) { onResult(false); return }
    promise.then({ _: dynamic -> onResult(true) }, { _: dynamic -> onResult(false) })
}
