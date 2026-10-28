package com.mohamedrejeb.calf.picker.coil

import org.w3c.files.File
import org.w3c.files.FileReader

internal actual fun browserCoilFile(name: String, size: Int): File = js(
    """(function () {
        var bytes = new Uint8Array(size);
        for (var i = 0; i < size; ++i) bytes[i] = i & 255;
        return new File([bytes], name, { type: 'application/octet-stream' });
    })()""",
)

internal actual class BrowserReaderProbe actual constructor(failureName: String) {
    init { installReaderProbe(failureName) }
    actual val createdCount: Int get() = probeCreatedCount()
    actual val readCount: Int get() = probeReadCount()
    actual val lastReader: FileReader? get() = probeLastReader()
    actual fun close() = closeReaderProbe()
}

private fun installReaderProbe(failureName: String): Unit = js(
    """(function () {
        var key = '__nativeCmpKitCoilReaderProbe';
        if (Object.prototype.hasOwnProperty.call(globalThis, key)) throw new Error('Reader probe already installed');
        var descriptor = Object.getOwnPropertyDescriptor(globalThis, 'FileReader');
        if (!descriptor || !descriptor.configurable) throw new Error('Actual FileReader constructor is unavailable');
        var Original = globalThis.FileReader;
        var state = { descriptor: descriptor, original: Original, readers: [], reads: 0 };
        function ObservedReader() {
            var reader = new Original();
            state.readers.push(reader);
            var originalRead = reader.readAsArrayBuffer;
            reader.readAsArrayBuffer = function (file) {
                ++state.reads;
                // Start the actual native read, not a fake promise or a fake fetcher.
                originalRead.call(reader, file);
                if (failureName) {
                    if (Object.prototype.hasOwnProperty.call(reader, 'error')) throw new Error('Fresh reader has an own error');
                    var error = new DOMException('Private message must not enter diagnostics', failureName);
                    Object.defineProperty(reader, 'error', { configurable: true, get: function () { return error; } });
                    // Deterministic error-event injection; no OS access-denial claim.
                    reader.dispatchEvent(new Event('error'));
                }
            };
            return reader;
        }
        ObservedReader.prototype = Original.prototype;
        Object.setPrototypeOf(ObservedReader, Original);
        state.wrapper = ObservedReader;
        Object.defineProperty(globalThis, 'FileReader', { configurable: true, enumerable: descriptor.enumerable,
            writable: true, value: ObservedReader });
        globalThis[key] = state;
    })()""",
)

private fun probeCreatedCount(): Int = js("globalThis.__nativeCmpKitCoilReaderProbe.readers.length")
private fun probeReadCount(): Int = js("globalThis.__nativeCmpKitCoilReaderProbe.reads")
private fun probeLastReader(): FileReader? = js(
    "(function () { var readers = globalThis.__nativeCmpKitCoilReaderProbe.readers; return readers.length ? readers[readers.length - 1] : null; })()",
)

private fun closeReaderProbe(): Unit = js(
    """(function () {
        var state = globalThis.__nativeCmpKitCoilReaderProbe;
        if (!state || globalThis.FileReader !== state.wrapper) throw new Error('Reader probe no longer owns the constructor');
        // Restore the exact original descriptor even if a failed test left native work alive.
        Object.defineProperty(globalThis, 'FileReader', state.descriptor);
        delete globalThis.__nativeCmpKitCoilReaderProbe;
        state.readers.forEach(function (reader) {
            if (reader.readyState === state.original.LOADING) reader.abort();
            if (Object.prototype.hasOwnProperty.call(reader, 'error')) delete reader.error;
            delete reader.readAsArrayBuffer;
        });
    })()""",
)
