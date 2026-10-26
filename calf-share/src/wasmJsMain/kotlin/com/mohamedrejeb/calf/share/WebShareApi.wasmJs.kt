// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
@file:OptIn(ExperimentalWasmJsInterop::class)

package com.mohamedrejeb.calf.share

import kotlin.js.ExperimentalWasmJsInterop

@JsFun("function() { return window.isSecureContext === true && typeof navigator.share === 'function'; }")
private external fun jsIsShareSupported(): Boolean
@JsFun("function() { return window.isSecureContext === true && !!navigator.clipboard && typeof navigator.clipboard.writeText === 'function'; }")
private external fun jsIsClipboardSupported(): Boolean

@JsFun("""
function(text, url, files, title, completed, dismissed, unavailable, failed) {
    var data = {};
    if (text !== null) data.text = text;
    if (url !== null) data.url = url;
    if (files !== null) data.files = Array.from(files);
    if (title !== null) data.title = title;
    var supported = false;
    try {
        supported = window.isSecureContext === true && typeof navigator.share === 'function' &&
            (files === null || (typeof navigator.canShare === 'function' && navigator.canShare(data)));
    } catch (_) { supported = false; }
    if (!supported) { unavailable(); return; }
    var promise;
    try { promise = navigator.share(data); } catch (_) { promise = null; }
    if (!promise) { failed(); return; }
    promise.then(function() { completed(); }, function(e) {
        if (e && e.name === 'AbortError') dismissed(); else failed();
    });
}
""")
private external fun jsShare(
    text: JsString?, url: JsString?, files: JsArray<JsAny>?, title: JsString?,
    completed: () -> Unit, dismissed: () -> Unit, unavailable: () -> Unit, failed: () -> Unit,
)

@JsFun("""
function(text, completed, failed) {
    var promise;
    try {
        promise = window.isSecureContext === true && navigator.clipboard && typeof navigator.clipboard.writeText === 'function'
            ? navigator.clipboard.writeText(text) : null;
    } catch (_) { promise = null; }
    if (!promise) { failed(); return; }
    promise.then(function() { completed(); }, function() { failed(); });
}
""")
private external fun jsCopyToClipboard(text: String, completed: () -> Unit, failed: () -> Unit)

internal actual fun isWebShareSupported(): Boolean = jsIsShareSupported()
internal actual fun isClipboardSupported(): Boolean = jsIsClipboardSupported()
internal actual fun webShareText(text: String, title: String?, onResult: (WebShareResult) -> Unit) =
    share(text = text, title = title, onResult = onResult)
internal actual fun webShareUrl(url: String, title: String?, onResult: (WebShareResult) -> Unit) =
    share(url = url, title = title, onResult = onResult)
internal actual fun webShareFile(file: org.w3c.files.File, title: String?, onResult: (WebShareResult) -> Unit) =
    webShareFiles(listOf(file), title, onResult)
internal actual fun webShareFiles(files: List<org.w3c.files.File>, title: String?, onResult: (WebShareResult) -> Unit) {
    val array = JsArray<JsAny>()
    files.forEach { jsArrayPush(array, it as JsAny) }
    share(files = array, title = title, onResult = onResult)
}
private fun share(text: String? = null, url: String? = null, files: JsArray<JsAny>? = null, title: String?, onResult: (WebShareResult) -> Unit) {
    jsShare(text?.toJsString(), url?.toJsString(), files, title?.toJsString(),
        { onResult(WebShareResult.Completed) }, { onResult(WebShareResult.Dismissed) },
        { onResult(WebShareResult.Unavailable) }, { onResult(WebShareResult.Failed) })
}
internal actual fun copyToClipboard(text: String, onResult: (Boolean) -> Unit) =
    jsCopyToClipboard(text, { onResult(true) }, { onResult(false) })
@JsFun("function(array, item) { array.push(item); }")
private external fun jsArrayPush(array: JsArray<JsAny>, item: JsAny)
