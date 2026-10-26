package com.mohamedrejeb.calf.io

import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.io.IOException
import org.w3c.files.File
import org.w3c.files.FileReader
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

/** Shared JS/Wasm event lifetime. The injected real reader is useful for browser abort tests. */
internal suspend fun readBrowserFile(file: File, reader: FileReader = FileReader()): ByteArray {
    checkedByteArraySize(file.size.toDouble().toULong())
    return suspendCancellableCoroutine { continuation ->
        var finished = false
        fun cleanup() {
            reader.onload = null
            reader.onerror = null
            reader.onabort = null
        }
        fun fail(failure: Throwable) {
            if (finished) return
            finished = true
            cleanup()
            continuation.resumeWithException(failure)
        }
        reader.onload = {
            if (!finished) {
                val result = try {
                    browserReaderBytes(reader)
                } catch (failure: Throwable) {
                    fail(failure)
                    null
                }
                if (result != null) {
                    finished = true
                    cleanup()
                    continuation.resume(result)
                }
            }
        }
        reader.onerror = { fail(IOException("Browser file read failed: ${browserReaderErrorName(reader) ?: "unknown error"}")) }
        reader.onabort = { fail(IOException("Browser file read was aborted")) }
        continuation.invokeOnCancellation {
            if (!finished) {
                finished = true
                cleanup()
                if (reader.readyState == FileReader.LOADING) reader.abort()
            }
        }
        if (!finished) {
            try {
                reader.readAsArrayBuffer(file)
            } catch (failure: Throwable) {
                fail(failure)
            }
        }
    }
}

internal expect fun browserReaderBytes(reader: FileReader): ByteArray

// Wasm exposes FileReader.error as JsAny, unlike the dynamic JS DOM binding.
internal expect fun browserReaderErrorName(reader: FileReader): String?
