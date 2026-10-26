// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.io

import org.khronos.webgl.ArrayBuffer
import org.khronos.webgl.Uint8Array
import org.khronos.webgl.get
import org.w3c.files.File
import org.w3c.files.FileReader
import kotlinx.io.IOException

internal actual suspend fun readFileAsBytes(file: File): ByteArray = readBrowserFile(file)

internal actual fun browserReaderBytes(reader: FileReader): ByteArray {
    val result = reader.result ?: throw IOException("Browser returned no file-read result")
    val array = Uint8Array(result as ArrayBuffer)
    return ByteArray(array.length) { array[it] }
}

internal actual fun browserReaderErrorName(reader: FileReader): String? = js(
    """(function () {
        var error = reader.error;
        var name = error == null ? null : error.name;
        return typeof name === 'string' ? name : null;
    })()""",
)
