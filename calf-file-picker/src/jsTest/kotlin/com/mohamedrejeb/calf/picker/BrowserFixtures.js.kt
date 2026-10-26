package com.mohamedrejeb.calf.picker

import org.w3c.files.File

internal actual fun pickerFixtureFile(name: String): File = js("new File(['fixture'], name)")

internal actual class BrowserTimeoutSpy actual constructor() {
    private val token = createBrowserTimeoutSpy()
    actual val timerCount: Int get() = timeoutSpyCount(token)
    actual fun delayAt(index: Int): Int = timeoutSpyDelay(token, index)
    actual fun fireCallback(index: Int): Boolean = timeoutSpyFire(token, index)
    actual fun close() { closeBrowserTimeoutSpy(token) }
}

private fun timeoutSpyCount(token: dynamic): Int = js("token.count()")
private fun timeoutSpyDelay(token: dynamic, index: Int): Int = js("token.delayAt(index)")
private fun timeoutSpyFire(token: dynamic, index: Int): Boolean = js("token.fire(index)")
private fun closeBrowserTimeoutSpy(token: dynamic): Unit = js("{ token.close(); }")
private fun createBrowserTimeoutSpy(): dynamic = js(
    """(function () {
        var previous = Object.getOwnPropertyDescriptor(window, 'setTimeout');
        var originalSetTimeout = window.setTimeout;
        var originalClearTimeout = window.clearTimeout;
        var records = [];
        var closed = false;
        if (typeof originalSetTimeout !== 'function' || typeof originalClearTimeout !== 'function') {
            throw new Error('Expected native browser timer functions');
        }
        Object.defineProperty(window, 'setTimeout', {
            configurable: true,
            enumerable: previous ? previous.enumerable : true,
            writable: true,
            value: function (handler, timeout) {
                if (this !== window) throw new Error('Expected the window timer receiver');
                var record = {
                    callback: handler,
                    delay: timeout,
                    args: Array.prototype.slice.call(arguments, 2),
                    handle: null
                };
                records.push(record);
                record.handle = originalSetTimeout.apply(this, arguments);
                return record.handle;
            }
        });
        return {
            count: function () { return records.length; },
            delayAt: function (index) { return records[index].delay; },
            fire: function (index) {
                var record = records[index];
                return record.callback.apply(window, record.args) === null;
            },
            close: function () {
                if (closed) return;
                closed = true;
                var failed = false;
                var firstFailure;
                function attempt(action) {
                    try { action(); }
                    catch (failure) {
                        if (!failed) { failed = true; firstFailure = failure; }
                    }
                }
                attempt(function () {
                    if (previous) Object.defineProperty(window, 'setTimeout', previous);
                    else if (!delete window.setTimeout) throw new Error('Could not restore window.setTimeout');
                });
                records.forEach(function (record) {
                    if (record.handle !== null) {
                        attempt(function () { originalClearTimeout.call(window, record.handle); });
                    }
                });
                records.forEach(function (record) {
                    attempt(function () { record.callback.apply(window, record.args); });
                });
                if (failed) throw firstFailure;
            }
        };
    })()""",
)
