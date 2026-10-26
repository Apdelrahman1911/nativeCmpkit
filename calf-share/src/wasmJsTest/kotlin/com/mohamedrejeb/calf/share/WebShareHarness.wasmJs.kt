@file:OptIn(kotlin.js.ExperimentalWasmJsInterop::class)

package com.mohamedrejeb.calf.share

import org.w3c.files.File

@JsFun("""function(mode) {
    if (window.__nativecmpkitShareHarness) throw new Error('Share harness was not restored');
    if (window.isSecureContext !== true) throw new Error('Tests require the localhost/HTTPS browser runner');
    var saved = {};
    ['share', 'canShare', 'clipboard'].forEach(function(key) {
        saved[key] = Object.getOwnPropertyDescriptor(navigator, key);
    });
    var h = {calls: 0, data: {}, callbackErrors: [], resolve: null, reject: null};
    h.restore = function() {
        ['share', 'canShare', 'clipboard'].forEach(function(key) {
            if (saved[key]) Object.defineProperty(navigator, key, saved[key]);
            else delete navigator[key];
        });
        delete window.__nativecmpkitShareHarness;
    };
    function set(key, value) { Object.defineProperty(navigator, key, {configurable: true, value: value}); }
    function pending(data) {
        h.calls++;
        h.data = data;
        if (mode === 'clipboard-throws') throw new DOMException('Denied fixture', 'NotAllowedError');
        var promise = new Promise(function(resolve, reject) { h.resolve = resolve; h.reject = reject; });
        // Observe the downstream application exception so the runner can assert propagation.
        // This does not catch it inside production code or turn it into another platform result.
        var then = promise.then.bind(promise);
        promise.then = function(fulfilled, rejected) {
            var child = then(fulfilled, rejected);
            child.catch(function(error) { h.callbackErrors.push(String(error)); });
            return child;
        };
        return promise;
    }
    window.__nativecmpkitShareHarness = h;
    set('share', mode === 'share' || mode === 'files-unavailable' ? function(data) { return pending(data); } : undefined);
    set('canShare', function(data) { return mode !== 'files-unavailable'; });
    set('clipboard', {writeText: function(text) { return pending({text: text}); }});
}""")
private external fun install(mode: String)
@JsFun("function() { window.__nativecmpkitShareHarness.restore(); }")
private external fun restore()
@JsFun("function(success, abort) { var h = window.__nativecmpkitShareHarness; if (!h.resolve) throw new Error('No pending request'); if (success) h.resolve(); else h.reject(new DOMException('Fixture rejection', abort ? 'AbortError' : 'NotAllowedError')); }")
private external fun settle(success: Boolean, abort: Boolean)
@JsFun("function() { return window.__nativecmpkitShareHarness.calls; }")
private external fun calls(): Int
@JsFun("function() { return window.__nativecmpkitShareHarness.callbackErrors.length; }")
private external fun callbackErrors(): Int
@JsFun("function(name) { var data = window.__nativecmpkitShareHarness.data; return name === 'fileNames' ? (data.files || []).map(function(file) { return file.name; }).join(',') : String(data[name] || ''); }")
private external fun field(name: String): String
@JsFun("function() { return new File(['fixture'], 'fixture.txt', {type:'text/plain'}); }")
private external fun file(): File

internal actual fun installShareHarness(mode: String) = install(mode)
internal actual fun restoreShareHarness() = restore()
internal actual fun shareHarnessSettle(success: Boolean, abort: Boolean) = settle(success, abort)
internal actual fun shareHarnessCalls(): Int = calls()
internal actual fun shareHarnessCallbackErrors(): Int = callbackErrors()
internal actual fun shareHarnessField(name: String): String = field(name)
internal actual fun shareHarnessFile(): File = file()
