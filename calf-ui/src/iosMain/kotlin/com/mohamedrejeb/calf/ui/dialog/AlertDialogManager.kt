// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
// Modified for nativeCmpkit (2026-10-27): preserve UIKit-owned alert delegation.
// Modified for NativeCmpKit (2026-11-03): refresh owned action-sheet anchors and release native references.
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class, kotlinx.cinterop.BetaInteropApi::class)

package com.mohamedrejeb.calf.ui.dialog

import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.window.DialogProperties
import com.mohamedrejeb.calf.core.InternalCalfApi
import com.mohamedrejeb.calf.ui.dialog.uikit.*
import com.mohamedrejeb.calf.ui.internal.NativePresentationQueue
import com.mohamedrejeb.calf.ui.internal.NativePresentationState
import com.mohamedrejeb.calf.ui.utils.*
import kotlinx.cinterop.ObjCAction
import kotlinx.cinterop.CPointer
import kotlinx.cinterop.ObjCObjectVar
import kotlinx.cinterop.objcPtr
import kotlinx.cinterop.pointed
import kotlinx.cinterop.useContents
import kotlinx.cinterop.value
import platform.CoreGraphics.CGRect
import platform.CoreGraphics.CGRectContainsPoint
import platform.CoreGraphics.CGRectMake
import platform.Foundation.NSThread
import platform.UIKit.*
import platform.darwin.NSObject
import platform.objc.sel_registerName

/** Main-confined UIAlertController owner; disposal is not a semantic user dismissal. */
@InternalCalfApi
class AlertDialogManager internal constructor(
    private val parentUIViewController: UIViewController,
    internal var onDismissRequest: () -> Unit,
    internal var iosProperties: AlertDialogIosProperties,
    internal var properties: DialogProperties,
    internal var layoutDirection: LayoutDirection = LayoutDirection.Ltr,
) : NSObject() {
    private val presentation = NativePresentationState()
    private var controller: UIAlertController? = null
    private var controllerStructure: List<Any>? = null
    private var rebuild = false
    private var notifyDismiss = false
    private var actionChosen = false
    private val textFieldDelegates = mutableListOf<NSObject>()
    private var outsideTap: UITapGestureRecognizer? = null
    private var ownedPopover: UIPopoverPresentationController? = null
    internal var popoverAnchor: AlertDialogIosPopoverAnchor? = null
    private var ownedAnchorView: UIView? = null
    private var ownedAnchorBarButton: UIBarButtonItem? = null

    // UIAlertController's Alert presentation delegate belongs to UIKit: even
    // assigning null throws on current iOS. Only ActionSheet's public popover
    // delegate is ours, including its adapted compact presentation callbacks.
    private val presentationDelegate = object : NSObject(), UIPopoverPresentationControllerDelegateProtocol {
        override fun presentationControllerShouldDismiss(presentationController: UIPresentationController): Boolean =
            canDismissNatively(presentationController)

        override fun presentationControllerDidDismiss(presentationController: UIPresentationController) =
            dismissedNatively(presentationController)

        override fun popoverPresentationControllerShouldDismissPopover(
            popoverPresentationController: UIPopoverPresentationController,
        ): Boolean = canDismissNatively(popoverPresentationController)

        override fun popoverPresentationControllerDidDismissPopover(
            popoverPresentationController: UIPopoverPresentationController,
        ) = dismissedNatively(popoverPresentationController)

        override fun popoverPresentationController(
            popoverPresentationController: UIPopoverPresentationController,
            willRepositionPopoverToRect: CPointer<CGRect>?,
            inView: CPointer<ObjCObjectVar<UIView?>>?,
        ) {
            requireMain()
            if (!ownsPopover(popoverPresentationController) || presentation.disposed ||
                presentation.phase == NativePresentationState.Phase.Dismissing) return
            when (val anchor = popoverAnchor.resolveFor(parentUIViewController)) {
                is ResolvedAlertPopoverAnchor.BarButton -> {
                    // UIKit owns system bar-item geometry; never guess its private view.
                    applyPopoverAnchor(popoverPresentationController, anchor)
                }
                is ResolvedAlertPopoverAnchor.ViewRect -> {
                    // Both are UIKit-owned in/out pointers valid only for this callback.
                    // A partial pointer pair is not permission to change one coordinate space.
                    if (willRepositionPopoverToRect == null || inView == null) return
                    anchor.rect.useContents {
                        val target = willRepositionPopoverToRect.pointed
                        target.origin.x = origin.x
                        target.origin.y = origin.y
                        target.size.width = size.width
                        target.size.height = size.height
                    }
                    inView.pointed.value = anchor.view
                    applyPopoverAnchor(popoverPresentationController, anchor)
                }
            }
        }
    }

    private fun requireMain() = check(NSThread.isMainThread) { "UIKit alert operations must run on Main" }

    private fun ownsNativeController(native: UIPresentationController): Boolean {
        val current = controller ?: return false
        return native.presentedViewController.objcPtr() == current.objcPtr()
    }

    private fun canDismissNatively(native: UIPresentationController): Boolean {
        requireMain()
        return ownsNativeController(native) && !presentation.disposed && properties.dismissOnClickOutside
    }

    private fun dismissedNatively(native: UIPresentationController) {
        requireMain()
        // Popover/adaptation may report the same dismissal twice; a stale
        // controller must not dismiss or release a newly rebuilt presentation.
        if (!ownsNativeController(native) || presentation.phase == NativePresentationState.Phase.Hidden) return
        val notify = !presentation.disposed && !actionChosen
        presentation.dismissedInteractively()
        notifyDismiss = false
        rebuild = false
        clearController()
        NativePresentationQueue.release(parentUIViewController, this)
        if (notify) onDismissRequest()
    }

    private fun getController(): UIAlertController = controller ?: createController().also { controller = it }

    private fun createController(): UIAlertController {
        val structure = iosProperties.structure()
        controllerStructure = structure
        actionChosen = false
        return UIAlertController.alertControllerWithTitle(iosProperties.title, iosProperties.text,
            iosProperties.style.toUIAlertControllerStyle()).apply {
            iosProperties.actions.forEachIndexed { index, descriptor ->
                addAction(UIAlertAction.actionWithTitle(descriptor.title, descriptor.style.toUIAlertActionStyle()) {
                    activateAction(index, structure)
                })
            }
            if (iosProperties.style == AlertDialogIosStyle.Alert) {
                iosProperties.textFields.forEachIndexed { index, descriptor ->
                    addTextFieldWithConfigurationHandler { field ->
                        if (field != null) {
                            val target = object : NSObject() {
                                @ObjCAction fun textFieldDidChange(sender: UITextField) {
                                    if (!presentation.disposed && iosProperties.structure() == structure) {
                                        iosProperties.textFields.getOrNull(index)?.onValueChange?.invoke(sender.text.orEmpty())
                                    }
                                }
                            }
                            textFieldDelegates.add(target)
                            field.text = descriptor.initialValue
                            field.placeholder = descriptor.placeholder
                            field.keyboardType = descriptor.keyboardType.toUIKeyboardType()
                            field.setSecureTextEntry(descriptor.isSecure)
                            field.addTarget(target, sel_registerName("textFieldDidChange:"), UIControlEventEditingChanged)
                        }
                    }
                }
            }
            if (iosProperties.severity == AlertDialogIosSeverity.Critical) setSeverity(UIAlertControllerSeverityCritical)
            // Action sheets require an anchor on iPad. The fallback is explicitly in the
            // presenter's local coordinate space, not a fabricated global screen rectangle.
            if (iosProperties.style == AlertDialogIosStyle.ActionSheet) {
                popoverPresentationController?.apply {
                    delegate = presentationDelegate
                    ownedPopover = this
                    sourceView = parentUIViewController.view
                    ownedAnchorView = parentUIViewController.view
                    sourceRect = parentUIViewController.view.bounds.useContents {
                        CGRectMake(origin.x + size.width / 2, origin.y + size.height / 2, 1.0, 1.0)
                    }
                    permittedArrowDirections = 0u
                }
            }
        }
    }

    /** Fetch callbacks from the latest descriptor only if native structure still matches. */
    internal fun activateAction(index: Int, expectedStructure: List<Any>? = controllerStructure) {
        requireMain()
        if (presentation.disposed || actionChosen || expectedStructure != iosProperties.structure()) return
        val action = iosProperties.actions.getOrNull(index)?.takeIf { it.enabled } ?: return
        actionChosen = true
        notifyDismiss = false
        presentation.request(false)
        pump()
        action.onClick()
    }

    internal fun updateDialogProperties() {
        requireMain()
        val viewController = controller ?: return
        if (controllerStructure != iosProperties.structure()) {
            rebuild = true
            presentation.request(false)
            pump()
            return
        }
        viewController.title = iosProperties.title
        viewController.message = iosProperties.text
        viewController.applyLayoutDirection(layoutDirection)
        viewController.modalInPresentation = !properties.dismissOnClickOutside
        viewController.setPreferredAction(null)
        iosProperties.actions.forEachIndexed { index, descriptor ->
            (viewController.actions.getOrNull(index) as? UIAlertAction)?.let {
                it.enabled = descriptor.enabled
                if (descriptor.isPreferred) viewController.setPreferredAction(it)
            }
        }
        refreshPopoverAnchor()
    }

    /** User/outside dismissal request, unlike [dispose]. */
    @ObjCAction
    fun dismiss() {
        requireMain()
        if (presentation.disposed || actionChosen || presentation.phase == NativePresentationState.Phase.Hidden) return
        notifyDismiss = true
        presentation.request(false)
        pump()
    }

    @ObjCAction
    fun onOutsideTap(sender: UITapGestureRecognizer) {
        requireMain()
        if (!properties.dismissOnClickOutside) return
        val view = controller?.view ?: return
        if (!CGRectContainsPoint(view.bounds, sender.locationInView(view))) dismiss()
    }

    fun showAlertDialog() {
        requireMain()
        presentation.request(true)
        pump()
    }

    /** Retains a terminal hide request even if UIKit is still presenting. */
    internal fun dispose() {
        requireMain()
        notifyDismiss = false
        rebuild = false
        onDismissRequest = {}
        popoverAnchor = null
        presentation.dispose()
        if (NativePresentationQueue.cancelWaiting(parentUIViewController, this)) {
            check(presentation.cancelQueuedPresentation())
            clearController()
        }
        pump()
    }

    private fun pump() {
        if (!presentation.requestedVisible &&
            presentation.phase == NativePresentationState.Phase.Presenting &&
            NativePresentationQueue.cancelWaiting(parentUIViewController, this)) {
            check(presentation.cancelQueuedPresentation())
            val shouldNotify = notifyDismiss && !presentation.disposed && !actionChosen
            notifyDismiss = false
            clearController()
            if (rebuild && !presentation.disposed) {
                rebuild = false
                presentation.request(true)
            }
            if (shouldNotify) onDismissRequest()
        }
        val transition = presentation.nextTransition() ?: return
        val viewController = getController()
        if (transition.visible) {
            updateDialogProperties()
            NativePresentationQueue.acquire(parentUIViewController, this) {
                // A queued owner's original bounds/anchor may have changed before admission.
                refreshPopoverAnchor()
                parentUIViewController.presentViewController(viewController, iosProperties.animated) {
                    if (presentation.complete(transition)) {
                        if (viewController.preferredStyle == UIAlertControllerStyleAlert) {
                            outsideTap = UITapGestureRecognizer(this, sel_registerName("onOutsideTap:")).also {
                                it.cancelsTouchesInView = false
                                viewController.view.superview?.addGestureRecognizer(it)
                            }
                        }
                        pump()
                    }
                }
            }
        } else {
            viewController.dismissViewControllerAnimated(iosProperties.animated) {
                if (presentation.complete(transition)) {
                    val shouldNotify = notifyDismiss && !presentation.disposed && !actionChosen
                    notifyDismiss = false
                    clearController()
                    NativePresentationQueue.release(parentUIViewController, this)
                    if (rebuild && !presentation.disposed) {
                        rebuild = false
                        presentation.request(true)
                    }
                    if (shouldNotify) onDismissRequest()
                    pump()
                }
            }
        }
    }

    private fun clearController() {
        outsideTap?.let { it.view?.removeGestureRecognizer(it) }
        outsideTap = null
        ownedPopover?.let { popover ->
            val delegate = popover.delegate as? NSObject
            if (delegate != null && delegate.objcPtr() == presentationDelegate.objcPtr()) {
                if (ownedAnchorView?.objcPtr() == popover.sourceView?.objcPtr()) popover.sourceView = null
                if (ownedAnchorBarButton?.objcPtr() == popover.barButtonItem?.objcPtr()) popover.barButtonItem = null
                popover.delegate = null
            }
        }
        ownedPopover = null
        ownedAnchorView = null
        ownedAnchorBarButton = null
        controller = null
        controllerStructure = null
        textFieldDelegates.clear()
    }

    private fun ownsPopover(popover: UIPopoverPresentationController): Boolean {
        val owned = ownedPopover ?: return false
        val delegate = popover.delegate as? NSObject ?: return false
        return owned.objcPtr() == popover.objcPtr() && ownsNativeController(popover) &&
            delegate.objcPtr() == presentationDelegate.objcPtr()
    }

    private fun refreshPopoverAnchor() {
        val popover = ownedPopover ?: return
        if (!ownsPopover(popover) || presentation.disposed) return
        applyPopoverAnchor(popover, popoverAnchor.resolveFor(parentUIViewController))
    }

    private fun applyPopoverAnchor(popover: UIPopoverPresentationController, anchor: ResolvedAlertPopoverAnchor) {
        when (anchor) {
            is ResolvedAlertPopoverAnchor.ViewRect -> {
                popover.barButtonItem = null
                popover.sourceView = anchor.view
                popover.sourceRect = anchor.rect
                popover.permittedArrowDirections = anchor.arrows
                ownedAnchorView = anchor.view
                ownedAnchorBarButton = null
            }
            is ResolvedAlertPopoverAnchor.BarButton -> {
                popover.sourceView = null
                popover.barButtonItem = anchor.item
                popover.permittedArrowDirections = anchor.arrows
                ownedAnchorView = null
                ownedAnchorBarButton = anchor.item
            }
        }
    }

    companion object {
        fun AlertDialogIosActionStyle.toUIAlertActionStyle(): UIAlertActionStyle = when (this) {
            AlertDialogIosActionStyle.Default -> UIAlertActionStyleDefault
            AlertDialogIosActionStyle.Cancel -> UIAlertActionStyleCancel
            AlertDialogIosActionStyle.Destructive -> UIAlertActionStyleDestructive
        }
        fun AlertDialogIosStyle.toUIAlertControllerStyle(): UIAlertControllerStyle = when (this) {
            AlertDialogIosStyle.ActionSheet -> UIAlertControllerStyleActionSheet
            AlertDialogIosStyle.Alert -> UIAlertControllerStyleAlert
        }
        fun AlertDialogIosAction.toUIAlertAction(): UIAlertAction = UIAlertAction.actionWithTitle(
            title, style.toUIAlertActionStyle(), handler = { onClick() },
        )
    }
}
