package com.mohamedrejeb.calf.picker

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Job
import platform.UIKit.UIViewController
import kotlin.concurrent.AtomicInt

/**
 * One UI-thread-confined presentation, never reused for another callback generation.
 * A result, finished provider work, and completed UIKit dismissal are different events.
 */
internal class IosDialogSession {
    private val terminal = AtomicInt(0)
    private val finished = CompletableDeferred<Unit>()
    private var finishRequested = false
    private var dismissalRequested = false
    private var dismissNative: ((() -> Unit) -> Unit)? = null
    var phase = IosDialogPhase.Prepared
        private set
    var cancelled = false
        private set
    var controller: UIViewController? = null
    var retainedDelegate: Any? = null
    var detachDelegate: () -> Unit = {}
    var job: Job? = null
    var cleanup: () -> Unit = {}
    var onFinished: () -> Unit = {}

    fun claimResult(): Boolean = !cancelled && terminal.compareAndSet(0, 1)

    /** Called immediately before the native present call, after presenter admission. */
    fun beginPresentation(dismiss: (() -> Unit) -> Unit) {
        check(phase == IosDialogPhase.Prepared && !finishRequested && !cancelled)
        dismissNative = dismiss
        phase = IosDialogPhase.Presenting
    }

    /** UIKit's presentation completion, not merely the return from presentViewController. */
    fun presentationCompleted() {
        if (phase != IosDialogPhase.Presenting) return
        phase = IosDialogPhase.Presented
        advance()
    }

    /** Only for a call that did not attach or begin presenting our controller. */
    fun presentationRejected() {
        if (phase != IosDialogPhase.Presenting) return
        phase = IosDialogPhase.Dismissed
        finish()
    }

    /** Photo picking may dismiss its sheet while the separately owned provider copies run. */
    fun requestDismissal() {
        dismissalRequested = true
        advance()
    }

    /** A successful dismissal completion/delegate event, never an interactive rollback. */
    fun dismissalCompleted() {
        if (phase == IosDialogPhase.Prepared || phase == IosDialogPhase.Finished) return
        phase = IosDialogPhase.Dismissed
        dismissNative = null
        advance()
    }

    fun finish() {
        terminal.compareAndSet(0, 1)
        finishRequested = true
        dismissalRequested = true
        advance()
    }

    suspend fun awaitFinished() = finished.await()

    private fun advance() {
        when (phase) {
            IosDialogPhase.Prepared, IosDialogPhase.Dismissed -> if (finishRequested) releaseResources()
            IosDialogPhase.Presented -> if (dismissalRequested) {
                phase = IosDialogPhase.Dismissing
                // Set the phase before invoking native code: completion may be synchronous.
                checkNotNull(dismissNative).invoke(::dismissalCompleted)
            }
            // During presentation, defer dismissal until UIKit's completion. During dismissal,
            // keep the controller, delegate and export file alive until native completion.
            IosDialogPhase.Presenting, IosDialogPhase.Dismissing, IosDialogPhase.Finished -> Unit
        }
    }

    private fun releaseResources() {
        phase = IosDialogPhase.Finished
        val detach = detachDelegate
        detachDelegate = {}
        val clean = cleanup
        cleanup = {}
        val notifyOwner = onFinished
        onFinished = {}
        dismissNative = null
        retainedDelegate = null
        controller = null
        job = null
        // Invalidate ownership before cleanup: callbacks/reentry/throws cannot clean twice.
        val result = runCatching { try { detach() } finally { clean() } }
        try { notifyOwner() } finally {
            result.fold(finished::complete, finished::completeExceptionally)
        }
        result.getOrThrow()
    }

    fun cancel() {
        cancelled = true
        terminal.compareAndSet(0, 1)
        job?.cancel()
        finish()
    }
}

internal enum class IosDialogPhase { Prepared, Presenting, Presented, Dismissing, Dismissed, Finished }

internal class IosDialogOwner {
    var current: IosDialogSession? = null
        private set
    private var disposed = false

    fun begin(): IosDialogSession {
        check(!disposed) { "The picker composition was disposed" }
        check(current == null) { "A picker/save operation is already in progress" }
        return IosDialogSession().also { session ->
            current = session
            session.onFinished = { if (current === session) current = null }
        }
    }

    fun end(session: IosDialogSession) {
        session.finish()
    }

    fun close() {
        disposed = true
        current?.cancel()
    }
}
