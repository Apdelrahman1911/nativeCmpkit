package com.mohamedrejeb.calf.io

import org.w3c.files.File
import org.w3c.files.FileReader

internal actual fun browserFixtureFile(name: String, content: String): File = js("new File([content], name)")

internal actual fun installBrowserReaderErrorFixture(reader: FileReader, nonStringName: Boolean): Unit = js(
    """(function () {
        if (Object.prototype.hasOwnProperty.call(reader, 'error')) {
            throw new Error('Expected a fresh FileReader without an own error property');
        }
        var error = nonStringName ? { name: 17 } : new DOMException('ignored native message', 'NotReadableError');
        var accessed = false;
        Object.defineProperty(reader, 'error', {
            configurable: true,
            get: function () {
                if (accessed) throw new Error('FileReader.error was read more than once');
                accessed = true;
                return error;
            }
        });
    })()""",
)

internal actual fun removeBrowserReaderErrorFixture(reader: FileReader): Boolean = js("delete reader.error")
