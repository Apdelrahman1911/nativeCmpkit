package com.mohamedrejeb.calf.picker.platform

import kotlin.coroutines.CoroutineContext
import kotlinx.coroutines.ensureActive

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

/**
 * Cancellation can happen during synchronous JNI creation, after the IO dispatcher
 * admitted this worker. Recheck inside the owning try/finally before entering a
 * native modal, rejecting cancellation already observed at that boundary. Cancellation
 * racing after the check may still enter show; an active OS modal is not claimed to
 * be interruptible, and native-parent lifetime needs its own ownership contract.
 */
internal inline fun <T> withActiveDialogHandle(
    context: CoroutineContext,
    create: () -> Long,
    destroy: (Long) -> Unit,
    use: (Long) -> T,
): T {
    context.ensureActive()
    return withDialogHandle(create, destroy) { handle ->
        context.ensureActive()
        val result = use(handle)
        context.ensureActive()
        result
    }
}
