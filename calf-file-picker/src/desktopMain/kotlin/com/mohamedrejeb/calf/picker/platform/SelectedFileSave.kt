package com.mohamedrejeb.calf.picker.platform

import java.io.File
import java.io.IOException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.runInterruptible

/** The native selector owns the dialog; this owns only copying to its selected path. */
internal suspend fun saveSelectedDesktopFile(
    path: String?,
    source: File?,
    bytes: ByteArray?,
    operations: AtomicSaveOperations = FileSystemAtomicSaveOperations,
): File? {
    if (path == null) return null // Cancellation must not touch even an unreadable source.
    val context = currentCoroutineContext()
    val destination = File(path)
    return try {
        // NIO file streams own interruptible channels. Cancellation interrupts a
        // blocked copy, not the preceding platform modal/JNI invocation.
        runInterruptible(Dispatchers.IO) {
            context.ensureActive()
            if (source != null) saveFileCopy(source, destination, operations) { context.ensureActive() }
            else saveBytes(destination, bytes, operations) { context.ensureActive() }
        }
    } catch (failure: IOException) {
        // An interrupted channel can report IOException rather than
        // InterruptedException. Do not deliver that as an application error if
        // the owning coroutine was cancelled. All streams/staging have unwound.
        context.ensureActive()
        throw failure
    }
}
