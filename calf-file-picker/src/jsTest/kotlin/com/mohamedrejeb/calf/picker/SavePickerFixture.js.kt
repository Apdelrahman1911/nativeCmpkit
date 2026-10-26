package com.mohamedrejeb.calf.picker

internal actual class SavePickerFixture actual constructor(mode: String) {
    private val token = createFixture(mode)
    actual val aborts: Int get() = fixtureAborts(token)
    actual fun completeWrite() { finishFixtureWrite(token) }
    actual fun close() { closeFixture(token) }
}

private fun fixtureAborts(token: dynamic): Int = js("token.aborts()")
private fun finishFixtureWrite(token: dynamic): Unit = js("{ token.completeWrite(); }")
private fun closeFixture(token: dynamic): Unit = js("{ token.close(); }")
private fun createFixture(mode: String): dynamic = js(
    """(function () {
var previous = Object.getOwnPropertyDescriptor(window, 'showSaveFilePicker');
var aborts = 0;
var completeWrite = null;
window.showSaveFilePicker = function () {
    if (mode === 'cancel') return Promise.reject(new DOMException('Cancelled', 'AbortError'));
    if (mode === 'picker-failure') return Promise.reject(new DOMException('Permission refused', 'SecurityError'));
    return Promise.resolve({
        createWritable: function () {
            if (mode === 'sync-create-failure') throw new Error('Synchronous createWritable failure');
            return Promise.resolve({
                write: function () {
                    if (mode === 'write-failure') return Promise.reject(new Error('Write failure'));
                    if (mode === 'pending-write') return new Promise(function (resolve) { completeWrite = resolve; });
                    return Promise.resolve();
                },
                close: function () { return Promise.resolve(); },
                abort: function () { aborts++; return Promise.resolve(); }
            });
        },
        getFile: function () { return Promise.resolve(new File(['written'], 'fixture.txt')); }
    });
};
return {
    aborts: function () { return aborts; },
    completeWrite: function () { if (completeWrite) completeWrite(); },
    close: function () {
        if (previous) Object.defineProperty(window, 'showSaveFilePicker', previous);
        else delete window.showSaveFilePicker;
    }
};
})()""",
)
