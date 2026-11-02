// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class, com.mohamedrejeb.calf.core.InternalCalfApi::class)

package com.mohamedrejeb.calf.share

import androidx.compose.runtime.*
import androidx.compose.ui.uikit.LocalUIViewController
import com.mohamedrejeb.calf.core.ExperimentalCalfApi
import com.mohamedrejeb.calf.io.SecurityScopedAccess
import com.mohamedrejeb.calf.io.acquireSecurityScopedAccess
import kotlinx.cinterop.useContents
import platform.CoreGraphics.CGRectMake
import platform.Foundation.NSThread
import platform.UIKit.*
import platform.darwin.dispatch_async
import platform.darwin.dispatch_get_main_queue

@ExperimentalCalfApi
@Composable
actual fun rememberShareLauncher(onResult: (ShareResult) -> Unit): ShareLauncher =
    rememberShareOutcomeLauncher { onResult(it.toLegacyResult()) }

@ExperimentalCalfApi
@Composable
actual fun rememberShareOutcomeLauncher(options: ShareOptions, onResult: (ShareOutcome) -> Unit): ShareLauncher {
    val viewController = LocalUIViewController.current
    val currentResult by rememberUpdatedState(onResult)
    val owner = remember(viewController) { IosShareOwner(viewController) { currentResult(it) } }
    DisposableEffect(owner) { onDispose { owner.dispose() } }
    return remember(owner) { ShareLauncher(owner) }
}

@ExperimentalCalfApi
@Stable
actual class ShareLauncher actual constructor(private val onLaunch: (ShareContent) -> Unit) {
    private var observedIosOwner: IosShareOwner? = null
    internal constructor(owner: IosShareOwner) : this(owner::launch) { observedIosOwner = owner }
    /** Read-only native-test ownership observation; the public constructor/launch remain exact. */
    internal val currentIosOwner: IosShareOwner?
        get() { check(NSThread.isMainThread); return observedIosOwner }
    actual fun launch(content: ShareContent) { onLaunch(content.snapshot()) }
}

internal class IosShareOwner(private val presenter: UIViewController, private val onResult: (ShareOutcome) -> Unit) {
    /** Immutable native presenter identity for a test's exact root-local cleanup obligation. */
    internal val nativePresenter: UIViewController
        get() { check(NSThread.isMainThread); return presenter }
    /** One main-thread-owned native presentation; a void present return is not a barrier. */
    internal class Request(val controller: UIActivityViewController, val leases: List<SecurityScopedAccess>) {
        var phase = IosShareRequestPhase.Prepared
            private set
        var presentationCompletionObserved = false
            private set
        var dismissalCompletionObserved = false
            private set
        var onReleased: () -> Unit = {}
        private var disposalRequested = false
        private var dismissNative: ((() -> Unit) -> Unit)? = null
        private var terminalResult: (() -> Unit)? = null

        fun beginPresentation(dismiss: (() -> Unit) -> Unit) {
            check(phase == IosShareRequestPhase.Prepared && !disposalRequested)
            dismissNative = dismiss
            phase = IosShareRequestPhase.Presenting
        }

        /** Called by UIKit's real presentation completion, never from a nil native link. */
        fun presentationCompleted() {
            if (phase != IosShareRequestPhase.Presenting) return
            presentationCompletionObserved = true
            phase = IosShareRequestPhase.Presented
            advanceDisposal()
        }

        fun dispose() {
            terminalResult = null // Real owner disposal also suppresses an already pending result.
            disposalRequested = true
            controller.completionWithItemsHandler = null
            advanceDisposal()
        }

        /**
         * Accept only the first terminal input. UIKit's activity result is not our
         * presentation/dismissal completion: keep the controller and file scopes
         * owned until those real barriers, then notify application code.
         */
        fun complete(deliver: () -> Unit) {
            if (disposalRequested || phase == IosShareRequestPhase.Released) return
            terminalResult = deliver
            disposalRequested = true
            controller.completionWithItemsHandler = null
            advanceDisposal()
        }

        private fun advanceDisposal() {
            if (!disposalRequested) return
            when (phase) {
                // No native presentation call has been entered in this phase.
                IosShareRequestPhase.Prepared -> release()
                IosShareRequestPhase.Presented -> {
                    // Set the phase before entering UIKit: dismissal can complete synchronously.
                    phase = IosShareRequestPhase.Dismissing
                    checkNotNull(dismissNative).invoke {
                        if (phase == IosShareRequestPhase.Dismissing) {
                            dismissalCompletionObserved = true
                            release()
                        }
                    }
                }
                // Do not dismiss during presentation or release during either transition.
                IosShareRequestPhase.Presenting, IosShareRequestPhase.Dismissing,
                IosShareRequestPhase.Released -> Unit
            }
        }

        fun release() {
            if (phase == IosShareRequestPhase.Released) return
            phase = IosShareRequestPhase.Released
            dismissNative = null
            val notifyOwner = onReleased
            onReleased = {}
            val deliver = terminalResult
            terminalResult = null
            // Invalidate before cleanup/notification so reentry or a throw cannot close twice.
            try {
                controller.completionWithItemsHandler = null
                leases.forEach { it.close() }
            } finally { notifyOwner() }
            deliver?.invoke() // Owner cleanup precedes reentry; cleanup failure cannot report success.
        }
    }
    private var active: Request? = null
    private var disposed = false
    /** Read-only owning observation; native/controller state is confined to UIKit's main thread. */
    internal val currentRequest: Request?
        get() { check(NSThread.isMainThread); return active }

    fun launch(content: ShareContent) = launch(content) { controller, completed ->
        presenter.presentViewController(controller, true, completed)
    }

    /** Per-call scheduling boundary, as in the picker; no global native hook or fake OS result. */
    internal fun launch(
        content: ShareContent,
        present: (UIActivityViewController, () -> Unit) -> Unit,
    ) = onIosShareMain {
        if (disposed) return@onIosShareMain
        if (active != null) { onResult(ShareOutcome.Busy); return@onIosShareMain }
        content.validationFailure()?.let { onResult(it); return@onIosShareMain }
        if (presenter.presentedViewController != null || presenter.view.window == null) {
            onResult(ShareOutcome.Unavailable("The share presenter is detached or already presenting"))
            return@onIosShareMain
        }
        val files = when (content) { is ShareContent.File -> listOf(content.file); is ShareContent.Files -> content.files; else -> emptyList() }
        val leases = mutableListOf<SecurityScopedAccess>()
        val controller = try {
            files.forEach { leases += it.url.acquireSecurityScopedAccess() }
            UIActivityViewController(activityItems = content.toActivityItems(), applicationActivities = null)
        } catch (error: Exception) {
            leases.forEach { it.close() }
            null
        }
        if (controller == null) {
            onResult(ShareOutcome.Failed(ShareFailureReason.Platform, "Could not prepare activity items"))
            return@onIosShareMain
        }
        val request = Request(controller, leases)
        request.onReleased = { if (active === request) active = null }
        active = request
        controller.completionWithItemsHandler = { _, completed, _, error ->
            onIosShareMain {
                if (active === request && !disposed) {
                    val result = when {
                        error != null -> ShareOutcome.Failed(ShareFailureReason.Platform, error.localizedDescription)
                        completed -> ShareOutcome.Completed
                        else -> ShareOutcome.Dismissed
                    }
                    request.complete { if (!disposed) onResult(result) }
                }
            }
        }
        controller.popoverPresentationController?.let { popover ->
            popover.sourceView = presenter.view
            popover.sourceRect = presenter.view.bounds.useContents {
                CGRectMake(origin.x + size.width / 2.0, origin.y + size.height / 2.0, 0.0, 0.0)
            }
            popover.permittedArrowDirections = 0uL
        }
        request.beginPresentation { completed -> dismissOwnedIosShare(controller, completed) }
        present(controller, request::presentationCompleted)
    }

    fun dispose() = onIosShareMain {
        if (disposed) return@onIosShareMain
        disposed = true
        // Keep the exact request and its scopes owned until UIKit crosses both barriers.
        // A missing backlink during a queued/animated present cannot authorize cleanup.
        active?.dispose()
    }
}

internal enum class IosShareRequestPhase { Prepared, Presenting, Presented, Dismissing, Released }

/** Dismiss only this request's controller, never another owner's modal from the presenter. */
private fun dismissOwnedIosShare(controller: UIActivityViewController, completed: () -> Unit) {
    check(NSThread.isMainThread)
    if (controller.isBeingDismissed()) {
        // A native/interactive dismissal may already be running. A cancelled transition is a
        // rollback, not a cleanup barrier: allow UIKit to finish it, then dismiss our controller.
        val registered = controller.transitionCoordinator?.animateAlongsideTransition(null) { context ->
            if (context != null && !context.isCancelled()) completed()
            else dispatch_async(dispatch_get_main_queue()) { dismissOwnedIosShare(controller, completed) }
        } == true
        if (registered) return
    }
    controller.dismissViewControllerAnimated(false, completed)
    // No nil-link or timer fallback. If UIKit never acknowledges completion, retaining the
    // scopes/controller is safer than releasing a resource still reachable by native work.
}

private fun onIosShareMain(action: () -> Unit) {
    if (NSThread.isMainThread) action() else dispatch_async(dispatch_get_main_queue()) { action() }
}
