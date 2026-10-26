@file:OptIn(kotlin.js.ExperimentalWasmJsInterop::class)

// Test-only native DOM instrumentation. The registered callback object is never substituted.
package com.mohamedrejeb.calf.ui.web

import org.w3c.dom.HTMLIFrameElement

@JsFun("""function() {
    var key = '__nativecmpkitWebViewListenerProbe';
    if (Object.prototype.hasOwnProperty.call(window, key)) throw new Error('Listener probe was not restored');
    var proto = HTMLIFrameElement.prototype;
    var addDescriptor = Object.getOwnPropertyDescriptor(proto, 'addEventListener');
    var removeDescriptor = Object.getOwnPropertyDescriptor(proto, 'removeEventListener');
    var nativeAdd = proto.addEventListener;
    var nativeRemove = proto.removeEventListener;
    var h = {frame: null, entries: [], registrations: 0, deliveries: 0, matchedRemovals: 0, unmatchedRemovals: 0};
    function restoreDescriptor(target, name, descriptor) {
        if (descriptor) Object.defineProperty(target, name, descriptor);
        else delete target[name];
    }
    function capture(options) {
        return typeof options === 'boolean' ? options : !!(options && options.capture);
    }
    function relevant(type) { return type === 'load' || type === 'error'; }
    h.restore = function() {
        var failures = [];
        function attempt(action) { try { action(); } catch (error) { failures.push(error); } }
        h.entries.forEach(function(entry) {
            attempt(function() { nativeRemove.call(entry.frame, entry.type, entry.listener, entry.capture); });
            attempt(function() { restoreDescriptor(entry.listener, 'handleEvent', entry.handleDescriptor); });
        });
        attempt(function() { restoreDescriptor(proto, 'addEventListener', addDescriptor); });
        attempt(function() { restoreDescriptor(proto, 'removeEventListener', removeDescriptor); });
        attempt(function() { delete window[key]; });
        h.entries.length = 0;
        h.frame = null;
        if (failures.length) throw failures[0];
    };
    window[key] = h;
    try {
        Object.defineProperty(proto, 'addEventListener', {configurable: true, writable: true, value: function(type, listener, options) {
            if (!relevant(type)) return nativeAdd.call(this, type, listener, options);
            if (h.frame === null) h.frame = this;
            if (this !== h.frame) return nativeAdd.call(this, type, listener, options);
            if (!listener || typeof listener !== 'object' || typeof listener.handleEvent !== 'function') {
                throw new Error('Owner must retain a native listener object, not independently converted functions');
            }
            var originalHandler = listener.handleEvent;
            var entry = {frame: this, type: type, listener: listener, capture: capture(options),
                handleDescriptor: Object.getOwnPropertyDescriptor(listener, 'handleEvent')};
            h.entries.push(entry);
            Object.defineProperty(listener, 'handleEvent', {configurable: true, writable: true,
                enumerable: entry.handleDescriptor ? entry.handleDescriptor.enumerable : true,
                value: function(event) {
                    h.deliveries++;
                    return originalHandler.call(this, event);
                }});
            h.registrations++;
            // The actual native callback object is passed unchanged, never replaced by the observer.
            return nativeAdd.call(this, type, listener, options);
        }});
        Object.defineProperty(proto, 'removeEventListener', {configurable: true, writable: true, value: function(type, listener, options) {
            if (this === h.frame && relevant(type)) {
                var target = this;
                var matched = h.entries.some(function(entry) {
                    return entry.frame === target && entry.type === type &&
                        entry.listener === listener && entry.capture === capture(options);
                });
                if (matched) h.matchedRemovals++;
                else h.unmatchedRemovals++;
            }
            return nativeRemove.call(this, type, listener, options);
        }});
    } catch (error) {
        try { h.restore(); } finally { throw error; }
    }
}""")
private external fun install()

@JsFun("""function() { var h = window.__nativecmpkitWebViewListenerProbe; if (!h) throw new Error('Listener probe is not installed'); h.restore(); }""")
private external fun restore()

@JsFun("""function(frame) { var h = window.__nativecmpkitWebViewListenerProbe; return !!h && h.frame === frame; }""")
private external fun owns(frame: HTMLIFrameElement): Boolean

@JsFun("""function(name) { var h = window.__nativecmpkitWebViewListenerProbe; if (!h || typeof h[name] !== 'number') throw new Error('Unknown listener probe counter'); return h[name]; }""")
private external fun count(name: String): Int

internal actual fun installBrowserListenerProbe() = install()
internal actual fun restoreBrowserListenerProbe() = restore()
internal actual fun browserListenerProbeOwns(frame: HTMLIFrameElement): Boolean = owns(frame)
internal actual fun browserListenerProbeCount(name: String): Int = count(name)
