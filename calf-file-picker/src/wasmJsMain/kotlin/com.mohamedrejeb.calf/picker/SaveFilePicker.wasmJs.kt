@file:OptIn(ExperimentalWasmJsInterop::class)

package com.mohamedrejeb.calf.picker

import org.w3c.files.Blob
import org.w3c.files.File

internal actual fun isSaveFilePickerSupported(): Boolean =
    js("typeof window !== 'undefined' && window.isSecureContext === true && typeof window.showSaveFilePicker === 'function'")

internal actual class BrowserSaveOperation internal constructor(private val operation: JsAny) {
    actual fun cancel() { cancelOperation(operation) }
}

private fun cancelOperation(operation: JsAny): Unit = js("{ operation.cancel(); }")

internal actual fun showSaveFilePicker(
    blob: Blob, suggestedName: String, mimeType: String, extension: String,
    onSaved: (File) -> Unit, onCancelled: () -> Unit, onPickerFailed: () -> Unit, onWriteFailed: () -> Unit,
): BrowserSaveOperation = BrowserSaveOperation(createSaveOperation(blob, suggestedName, mimeType, extension, onSaved, onCancelled, onPickerFailed, onWriteFailed))

private fun createSaveOperation(
    blob: Blob, suggestedName: String, mimeType: String, extension: String,
    onSaved: (File) -> Unit, onCancelled: () -> Unit, onPickerFailed: () -> Unit, onWriteFailed: () -> Unit,
): JsAny = js(
    """{

var cancelled = false;
var finished = false;
var writable = null;
function abortWritable() {
    var stream = writable;
    writable = null;
    if (stream) {
        try { Promise.resolve(stream.abort()).catch(function () {}); } catch (ignored) {}
    }
}
var options = { suggestedName: suggestedName };
if (extension && mimeType !== 'application/octet-stream') {
    var accept = {}; accept[mimeType] = ['.' + extension]; options.types = [{ accept: accept }];
}
var promise;
try { promise = window.showSaveFilePicker(options); }
catch (error) { promise = Promise.reject(error); }
promise.then(function (handle) {
    if (cancelled) return;
    // Put createWritable inside a promise handler so even synchronous failures reach onWriteFailed.
    Promise.resolve().then(function () {
        return cancelled ? null : handle.createWritable();
    }).then(function (stream) {
        if (!stream) return null;
        writable = stream;
        if (cancelled) { abortWritable(); return null; }
        return stream.write(blob).then(function () {
            if (cancelled) { abortWritable(); return null; }
            return stream.close().then(function () {
                writable = null;
                return cancelled ? null : handle.getFile();
            });
        });
    }).then(function (file) {
        if (cancelled || finished) return;
        finished = true;
        if (file) onSaved(file); else onWriteFailed();
    }, function () {
        abortWritable();
        if (cancelled || finished) return;
        finished = true;
        onWriteFailed();
    });
}, function (error) {
    if (cancelled || finished) return;
    finished = true;
    if (error && error.name === 'AbortError') onCancelled(); else onPickerFailed();
});
return { cancel: function () { if (cancelled || finished) return; cancelled = true; abortWritable(); } };
}""",
)
