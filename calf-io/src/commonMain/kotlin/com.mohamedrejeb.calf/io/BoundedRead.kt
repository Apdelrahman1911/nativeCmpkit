package com.mohamedrejeb.calf.io

import com.mohamedrejeb.calf.core.PlatformContext
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.yield
import kotlinx.io.Buffer
import kotlinx.io.IOException
import kotlinx.io.RawSource
import kotlinx.io.readByteArray

/** Checks the allocation/copy boundary without allocating an oversized array. */
internal fun checkedByteArraySize(length: ULong): Int {
    if (length > Int.MAX_VALUE.toULong()) {
        throw IOException("File is too large for a ByteArray; use source() for streaming reads")
    }
    return length.toInt()
}

/**
 * Reads at most [maxBytes] bytes, throwing [IOException] instead of returning truncated data.
 * Metadata is only a precheck: the limit is enforced while reading as well. The source is
 * always closed, including on cancellation/failure. Reads are blocking on native/JVM targets;
 * choose a background dispatcher, or use [source] when buffering is not needed.
 */
suspend fun KmpFile.readByteArray(context: PlatformContext, maxBytes: Int): ByteArray {
    require(maxBytes >= 0) { "maxBytes must not be negative" }
    currentCoroutineContext().ensureActive()
    val size = getSize(context)
    if (size != null && size > maxBytes) throw IOException("File exceeds the $maxBytes byte limit")
    return source(context).readBounded(maxBytes)
}

/** Context-free version of [readByteArray] with an explicit in-memory size limit. */
suspend fun KmpFile.readByteArray(maxBytes: Int): ByteArray = readByteArray(resolveContext(), maxBytes)

internal suspend fun RawSource.readBounded(maxBytes: Int): ByteArray = use { source ->
    require(maxBytes >= 0) { "maxBytes must not be negative" }
    val buffer = Buffer()
    while (true) {
        currentCoroutineContext().ensureActive()
        // One extra byte distinguishes exactly-at-limit from truncated content.
        val count = minOf(64 * 1024L, maxBytes.toLong() + 1 - buffer.size)
        val read = source.readAtMostTo(buffer, count)
        if (buffer.size > maxBytes) throw IOException("File exceeds the $maxBytes byte limit")
        if (read == -1L) return@use buffer.readByteArray()
        if (read == 0L) throw IOException("File source made no progress")
        yield()
    }
    @Suppress("UNREACHABLE_CODE")
    error("Unreachable")
}
