// NativeCmpKit (2026-10-27): checked Foundation copying extracted from the derived Calf read path.
package com.mohamedrejeb.calf.io

import kotlinx.cinterop.COpaquePointer
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.addressOf
import kotlinx.cinterop.usePinned
import kotlinx.io.IOException
import platform.Foundation.NSData
import platform.Foundation.getBytes

/**
 * Validate before allocating/pinning. Foundation's copying method keeps the NSData receiver
 * alive for the native call; no borrowed `bytes` pointer escapes its owning object. The
 * file-reading path provides immutable NSData; concurrent mutation of NSMutableData is not
 * supported. Large content should use the streaming API, not a whole-file allocation.
 */
@OptIn(ExperimentalForeignApi::class)
internal fun NSData.toCheckedByteArray(): ByteArray {
    val size = checkedByteArraySize(length)
    if (size == 0) return ByteArray(0)
    return ByteArray(size).apply {
        usePinned { copyToCheckedNativeBuffer(it.addressOf(0), size) }
    }
}

/**
 * The caller owns a destination of [capacity] bytes. This internal boundary is shared by the
 * actual pinned-array read and native guard-page integration tests. Validate length and
 * capacity before the Foundation call; empty data requires no pointer at all.
 */
@OptIn(ExperimentalForeignApi::class)
internal fun NSData.copyToCheckedNativeBuffer(destination: COpaquePointer?, capacity: Int) {
    require(capacity >= 0) { "Native buffer capacity must not be negative" }
    val count = checkedByteArraySize(length)
    if (count > capacity) throw IOException("File data exceeds the native destination capacity")
    if (count == 0) return
    if (destination == null) throw IOException("Nonempty file data requires a native destination")
    getBytes(destination, length = count.toULong())
}
