package com.mohamedrejeb.calf.picker.platform

/** Allocation, use and close stay in one worker block; no cancellable raw-handle handoff. */
internal inline fun <T> withDialogHandle(create: () -> Long, destroy: (Long) -> Unit, use: (Long) -> T): T {
    val handle = create()
    check(handle != 0L) { "Native dialog creation returned an invalid handle" }
    try {
        return use(handle)
    } finally {
        destroy(handle)
    }
}
