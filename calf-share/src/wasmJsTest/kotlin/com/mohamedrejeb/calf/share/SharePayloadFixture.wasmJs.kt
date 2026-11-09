@file:OptIn(ExperimentalWasmJsInterop::class)

package com.mohamedrejeb.calf.share

import org.w3c.files.File
import kotlin.js.ExperimentalWasmJsInterop

internal actual fun installShareCapture(): WebShareCapture {
    val state = jsInstallShareCapture()
    return try {
        WasmShareCapture(state)
    } catch (failure: Throwable) {
        jsRestoreShareDescriptor(state)
        throw failure
    }
}

internal actual fun snapshotNavigatorShareDescriptor(): () -> Boolean {
    val snapshot = jsSnapshotShareDescriptor()
    return { jsShareDescriptorUnchanged(snapshot) }
}

internal actual fun browserFile(name: String, contents: String, mimeType: String): File =
    jsBrowserFile(name, contents, mimeType)

private class WasmShareCapture(private val state: JsAny) : WebShareCapture {
    override val callCount: Int
        get() = jsCaptureCalls(state)

    override fun fieldNames(): String = jsCaptureFields(state)

    override fun hasOwnField(field: String): Boolean = jsCaptureHasOwnField(state, field)

    override fun stringField(field: String): String? = jsCaptureString(state, field)?.toString()

    override fun fileCount(): Int = jsCaptureFileCount(state)

    override fun fileAt(index: Int): File = jsCaptureFileAt(state, index)

    override fun isSameFile(index: Int, original: File): Boolean = jsCaptureIsSameFile(state, index, original)

    override fun restore() = jsRestoreShareDescriptor(state)
}

@JsFun("""
function() {
    var target = navigator;
    var previous = Object.getOwnPropertyDescriptor(target, 'share');
    var state = { payload: null, calls: 0 };
    state.restore = function() {
        if (previous === undefined) {
            if (!Reflect.deleteProperty(target, 'share')) {
                throw new Error('Could not restore navigator.share');
            }
        } else {
            Object.defineProperty(target, 'share', previous);
        }
    };
    try {
        Object.defineProperty(target, 'share', {
            configurable: true,
            enumerable: false,
            writable: true,
            value: function(data) {
                state.payload = data;
                state.calls += 1;
                return new Promise(function() {});
            }
        });
        return state;
    } catch (failure) {
        state.restore();
        throw failure;
    }
}
""")
private external fun jsInstallShareCapture(): JsAny

@JsFun("function(state) { state.restore(); }")
private external fun jsRestoreShareDescriptor(state: JsAny)

@JsFun("function(state) { return state.calls; }")
private external fun jsCaptureCalls(state: JsAny): Int

@JsFun("function(state) { return Object.keys(state.payload).sort().join(','); }")
private external fun jsCaptureFields(state: JsAny): String

@JsFun("function(state, field) { return Object.prototype.hasOwnProperty.call(state.payload, field); }")
private external fun jsCaptureHasOwnField(state: JsAny, field: String): Boolean

@JsFun("function(state, field) { var value = state.payload[field]; return typeof value === 'string' ? value : null; }")
private external fun jsCaptureString(state: JsAny, field: String): JsString?

@JsFun("function(state) { return state.payload.files.length; }")
private external fun jsCaptureFileCount(state: JsAny): Int

@JsFun("function(state, index) { return state.payload.files[index]; }")
private external fun jsCaptureFileAt(state: JsAny, index: Int): File

@JsFun("function(state, index, original) { return state.payload.files[index] === original; }")
private external fun jsCaptureIsSameFile(state: JsAny, index: Int, original: File): Boolean

@JsFun("function(name, contents, mimeType) { return new File([contents], name, { type: mimeType }); }")
private external fun jsBrowserFile(name: String, contents: String, mimeType: String): File

@JsFun("function() { return { target: navigator, descriptor: Object.getOwnPropertyDescriptor(navigator, 'share') }; }")
private external fun jsSnapshotShareDescriptor(): JsAny

@JsFun("""
function(snapshot) {
    var previous = snapshot.descriptor;
    var current = Object.getOwnPropertyDescriptor(snapshot.target, 'share');
    if (previous === undefined || current === undefined) return previous === current;
    return previous.value === current.value && previous.get === current.get &&
        previous.set === current.set && previous.writable === current.writable &&
        previous.enumerable === current.enumerable && previous.configurable === current.configurable;
}
""")
private external fun jsShareDescriptorUnchanged(snapshot: JsAny): Boolean
