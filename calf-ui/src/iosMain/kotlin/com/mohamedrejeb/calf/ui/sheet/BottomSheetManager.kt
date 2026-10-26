// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.sheet

import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.SheetValue
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.window.ComposeUIViewController
import com.mohamedrejeb.calf.ui.internal.NativePresentationState
import com.mohamedrejeb.calf.ui.internal.NativePresentationQueue
import com.mohamedrejeb.calf.ui.utils.applyLayoutDirection
import com.mohamedrejeb.calf.ui.utils.applyTheme
import com.mohamedrejeb.calf.ui.utils.toUIColor
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import platform.Foundation.NSThread
import platform.UIKit.*
import platform.darwin.NSObject

/** Main-confined UIKit owner. Cancellation detaches a waiter, not a native animation. */
@OptIn(ExperimentalMaterial3Api::class)
internal class BottomSheetManager(
    private val parentUIViewController: UIViewController,
    private var isDark: Boolean,
    private var containerColor: Color,
    private var onDismiss: () -> Unit,
    private val confirmValueChange: (SheetValue) -> Boolean,
    private var onStateChanged: (SheetValue, SheetValue) -> Unit,
    content: @Composable () -> Unit,
    internal var layoutDirection: LayoutDirection = LayoutDirection.Ltr,
) {
    private val presentation = NativePresentationState()
    private var content: (@Composable () -> Unit)? = content
    private var controller: UIViewController? = null
    private var currentValue = SheetValue.Hidden
    private var shownValue = SheetValue.Expanded
    private var skipPartial = false
    private var showHandle = true
    var allowInteractiveDismiss = true
    private val waiters = mutableMapOf<CompletableDeferred<Unit>, Boolean>()

    private val delegate = BottomSheetControllerDelegate(
        onDismiss = {
            presentation.dismissedInteractively()
            currentValue = SheetValue.Hidden
            publishState()
            finishWaiters(false)
            NativePresentationQueue.release(parentUIViewController, this@BottomSheetManager)
            onDismiss()
        },
        confirmValueChange = { allowInteractiveDismiss && confirmValueChange(it) },
    ).apply {
        onDetentChanged = { value ->
            if (confirmValueChange(value)) {
                shownValue = value
                currentValue = value
                publishState()
            } else {
                controller?.sheetPresentationController?.selectedDetentIdentifier = shownValue.detentIdentifier()
            }
        }
    }

    private fun requireMain() = check(NSThread.isMainThread) { "UIKit sheet operations must run on Main" }

    private fun getController(): UIViewController = controller ?: ComposeUIViewController {
        content?.invoke()
    }.apply {
        modalPresentationStyle = UIModalPresentationPageSheet
        modalTransitionStyle = UIModalTransitionStyleCoverVertical
        sheetPresentationController?.delegate = delegate
        presentationController?.delegate = delegate
    }.also { controller = it }

    fun applyTheme(dark: Boolean) {
        requireMain()
        isDark = dark
        controller?.applyTheme(dark)
    }

    fun applyContainerColor(color: Color) {
        requireMain()
        containerColor = color
        controller?.view?.backgroundColor = color.toUIColor()
    }

    suspend fun show(skipPartiallyExpanded: Boolean, showDragHandle: Boolean, initialValue: SheetValue) {
        requireMain()
        skipPartial = skipPartiallyExpanded
        showHandle = showDragHandle
        if (currentValue == SheetValue.Hidden) shownValue = initialValue
        awaitVisibility(true)
    }

    suspend fun hide() {
        requireMain()
        awaitVisibility(false)
    }

    private suspend fun awaitVisibility(visible: Boolean) {
        check(!presentation.disposed) { "The native sheet owner has been disposed" }
        val completion = CompletableDeferred<Unit>() // one token per invocation; never reused
        waiters[completion] = visible
        presentation.request(visible)
        publishState()
        pump()
        if (presentation.phase == if (visible) NativePresentationState.Phase.Presented else NativePresentationState.Phase.Hidden) {
            finishWaiters(visible)
        }
        try {
            completion.await()
        } finally {
            waiters.remove(completion)
        }
    }

    private fun publishState() {
        onStateChanged(currentValue, if (presentation.requestedVisible) shownValue else SheetValue.Hidden)
    }

    private fun finishWaiters(visible: Boolean) {
        waiters.filterValues { it == visible }.keys.toList().forEach {
            waiters.remove(it)
            it.complete(Unit)
        }
    }

    private fun pump() {
        requireMain()
        val transition = presentation.nextTransition()
        if (transition == null) {
            releaseIfDisposed()
            return
        }
        val viewController = getController()
        val completion = {
            if (presentation.complete(transition)) {
                currentValue = if (transition.visible) shownValue else SheetValue.Hidden
                publishState()
                finishWaiters(transition.visible)
                if (!transition.visible) NativePresentationQueue.release(parentUIViewController, this)
                pump()
            }
        }
        if (transition.visible) {
            viewController.sheetPresentationController?.apply {
                detents = if (skipPartial) listOf(UISheetPresentationControllerDetent.largeDetent()) else listOf(
                    UISheetPresentationControllerDetent.mediumDetent(),
                    UISheetPresentationControllerDetent.largeDetent(),
                )
                selectedDetentIdentifier = shownValue.detentIdentifier()
                prefersGrabberVisible = showHandle
            }
            viewController.applyTheme(isDark)
            viewController.view.backgroundColor = containerColor.toUIColor()
            viewController.applyLayoutDirection(layoutDirection)
            NativePresentationQueue.acquire(parentUIViewController, this) {
                parentUIViewController.presentViewController(viewController, animated = true, completion = completion)
            }
        } else {
            viewController.dismissViewControllerAnimated(flag = true, completion = completion)
        }
    }

    /** Forced ownership cleanup deliberately bypasses application transition vetoes. */
    fun dispose() {
        requireMain()
        presentation.dispose()
        onDismiss = {}
        onStateChanged = { _, _ -> }
        waiters.keys.toList().forEach { it.cancel(CancellationException("Sheet owner disposed")) }
        waiters.clear()
        if (NativePresentationQueue.cancelWaiting(parentUIViewController, this)) {
            presentation.dismissedInteractively()
        }
        pump() // a pending presentation completion will pump the queued terminal hide
    }

    private fun releaseIfDisposed() {
        if (!presentation.disposed || presentation.phase != NativePresentationState.Phase.Hidden) return
        controller?.presentationController?.delegate = null
        controller?.sheetPresentationController?.delegate = null
        controller = null
        content = null
    }
}

@OptIn(ExperimentalMaterial3Api::class)
private fun SheetValue.detentIdentifier(): String? = when (this) {
    SheetValue.PartiallyExpanded -> UISheetPresentationControllerDetentIdentifierMedium
    else -> UISheetPresentationControllerDetentIdentifierLarge
}

/** Retained delegate; the historical two-argument constructor remains available. */
@OptIn(ExperimentalMaterial3Api::class)
class BottomSheetControllerDelegate(
    private val onDismiss: () -> Unit,
    private val confirmValueChange: (SheetValue) -> Boolean,
) : NSObject(), UISheetPresentationControllerDelegateProtocol {
    internal var onDetentChanged: (SheetValue) -> Unit = {}

    override fun presentationControllerShouldDismiss(presentationController: UIPresentationController): Boolean =
        confirmValueChange(SheetValue.Hidden)

    override fun presentationControllerDidDismiss(presentationController: UIPresentationController) = onDismiss()

    override fun sheetPresentationControllerDidChangeSelectedDetentIdentifier(sheetPresentationController: UISheetPresentationController) {
        onDetentChanged(if (sheetPresentationController.selectedDetentIdentifier == UISheetPresentationControllerDetentIdentifierMedium)
            SheetValue.PartiallyExpanded else SheetValue.Expanded)
    }
}
