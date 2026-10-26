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
    return remember(owner) { ShareLauncher(owner::launch) }
}

@ExperimentalCalfApi
@Stable
actual class ShareLauncher actual constructor(private val onLaunch: (ShareContent) -> Unit) {
    actual fun launch(content: ShareContent) { onLaunch(content.snapshot()) }
}

internal class IosShareOwner(private val presenter: UIViewController, private val onResult: (ShareOutcome) -> Unit) {
    private class Request(val controller: UIActivityViewController, val leases: List<SecurityScopedAccess>) {
        private var released = false
        fun release() {
            if (released) return
            released = true
            controller.completionWithItemsHandler = null
            leases.forEach { it.close() }
        }
    }
    private var active: Request? = null
    private var disposed = false

    fun launch(content: ShareContent) = onIosShareMain {
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
        active = request
        controller.completionWithItemsHandler = { _, completed, _, error ->
            if (active === request && !disposed) {
                active = null
                request.release()
                val result = when {
                    error != null -> ShareOutcome.Failed(ShareFailureReason.Platform, error.localizedDescription)
                    completed -> ShareOutcome.Completed
                    else -> ShareOutcome.Dismissed
                }
                onResult(result) // Cleanup precedes application code and cannot be skipped by it.
            }
        }
        controller.popoverPresentationController?.let { popover ->
            popover.sourceView = presenter.view
            popover.sourceRect = presenter.view.bounds.useContents {
                CGRectMake(origin.x + size.width / 2.0, origin.y + size.height / 2.0, 0.0, 0.0)
            }
            popover.permittedArrowDirections = 0uL
        }
        presenter.presentViewController(controller, true, null)
    }

    fun dispose() = onIosShareMain {
        if (disposed) return@onIosShareMain
        disposed = true
        val request = active
        active = null
        if (request != null) {
            request.controller.completionWithItemsHandler = null
            if (request.controller.presentingViewController != null) {
                request.controller.dismissViewControllerAnimated(false) { request.release() }
            } else request.release()
        }
    }
}

private fun onIosShareMain(action: () -> Unit) {
    if (NSThread.isMainThread) action() else dispatch_async(dispatch_get_main_queue()) { action() }
}
