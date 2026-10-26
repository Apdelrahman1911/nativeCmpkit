package com.mohamedrejeb.calf.sample.utils

import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.yield
import kotlinx.io.Buffer
import kotlinx.io.IOException
import kotlinx.io.RawSource

internal const val SAMPLE_STREAM_CHUNK_SIZE = 64L * 1024

/** Consumes and closes this source, including cancellation/error paths. */
internal suspend fun RawSource.consumeByteCount(): Long = use { source ->
    val chunk = Buffer()
    var total = 0L
    while (true) {
        currentCoroutineContext().ensureActive()
        val read = source.readAtMostTo(chunk, SAMPLE_STREAM_CHUNK_SIZE)
        if (read == -1L) return@use total
        if (read <= 0 || read > SAMPLE_STREAM_CHUNK_SIZE) throw IOException("File source made invalid progress")
        if (total > Long.MAX_VALUE - read) throw IOException("File byte count exceeds Long range")
        total += read
        chunk.clear()
        // Ensure cancellation and UI work can run even on single-threaded browser dispatchers.
        yield()
    }
    @Suppress("UNREACHABLE_CODE")
    error("Unreachable")
}
