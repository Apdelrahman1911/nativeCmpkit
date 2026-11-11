@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class, kotlinx.cinterop.BetaInteropApi::class)

package com.mohamedrejeb.calf.ui.dialog

import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.window.*
import com.mohamedrejeb.calf.core.*
import com.mohamedrejeb.calf.ui.dialog.uikit.*
import com.mohamedrejeb.calf.ui.utils.*
import kotlinx.cinterop.*
import platform.CoreGraphics.CGRect
import platform.Foundation.NSThread
import platform.UIKit.*
import platform.darwin.NSObject
import platform.objc.sel_registerName

/**
 * Manages the [UIAlertController] and its actions.
 *
 * ActionSheet presentations configure a UIKit popover anchor before presentation.
 * An optional [AlertDialogIosPopoverAnchor] can be supplied through the iOS
 * `LocalAlertDialogIosPopoverAnchor`; `null` uses the documented presenter-center
 * fallback so existing callers remain source-compatible.
 *
 * @param onDismissRequest Lambda that is invoked when the dialog is dismissed.
 * @param iosProperties The iOS properties of the dialog.
 * @param properties The properties of the dialog.
 * @param parentUIViewController The [UIViewController] that will present the dialog.
 * @constructor Creates an [AlertDialogManager] instance.
 * @see [UIAlertController]
 */
@InternalCalfApi
class AlertDialogManager internal constructor(
    private val parentUIViewController: UIViewController,
    internal var onDismissRequest: () -> Unit,
    internal var iosProperties: AlertDialogIosProperties,
    internal var properties: DialogProperties,
    internal var layoutDirection: LayoutDirection = LayoutDirection.Ltr,
) : NSObject() {

    /**
     * Indicates whether the dialog is presented or not.
     */
    private var isPresented = false

    /**
     * Indicates whether the dialog is animating or not.
     */
    private var isAnimating = false

    /**
     * Set before an ActionSheet action runs so a subsequent UIKit dismissal callback
     * does not invoke the dialog-level dismiss callback a second time.
     */
    private var actionChosen = false

    /**
     * Strong references to text field delegate objects.
     * UIKit's addTarget holds targets weakly, so without these
     * the GC would collect the delegates and text change events
     * would stop firing.
     */
    private val textFieldDelegates = mutableListOf<NSObject>()

    /**
     * Optional action-sheet anchor supplied by the iOS composition local.
     * `null` resolves to the documented presenter-center fallback.
     */
    internal var popoverAnchor: AlertDialogIosPopoverAnchor? = null

    /**
     * The popover controller we configured for the current ActionSheet, if any.
     */
    private var ownedPopover: UIPopoverPresentationController? = null
    private var ownedPresentationController: UIPresentationController? = null
    private var ownedAnchorView: UIView? = null
    private var ownedAnchorBarButton: UIBarButtonItem? = null

    /**
     * Only public ActionSheet presentation delegation is ours. UIKit owns Alert
     * presentation delegation, so that path is never assigned here.
     */
    private val popoverDelegate = object : NSObject(), UIPopoverPresentationControllerDelegateProtocol {
        override fun prepareForPopoverPresentation(
            popoverPresentationController: UIPopoverPresentationController,
        ) {
            requireMain()
            if (!ownsPopover(popoverPresentationController)) return

            applyPopoverAnchor(
                popoverPresentationController,
                popoverAnchor.resolveFor(parentUIViewController),
            )
        }

        override fun popoverPresentationController(
            popoverPresentationController: UIPopoverPresentationController,
            willRepositionPopoverToRect: CPointer<CGRect>?,
            inView: CPointer<ObjCObjectVar<UIView?>>?,
        ) {
            requireMain()
            if (!ownsPopover(popoverPresentationController)) return

            when (val anchor = popoverAnchor.resolveFor(parentUIViewController)) {
                is ResolvedAlertPopoverAnchor.BarButton -> {
                    // UIKit owns system bar-item geometry; never guess its private view.
                    applyPopoverAnchor(popoverPresentationController, anchor)
                }

                is ResolvedAlertPopoverAnchor.ViewRect -> {
                    // Both pointers are UIKit-owned in/out values valid only for this
                    // callback. A partial pair is not permission to change one
                    // coordinate space.
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

        override fun presentationControllerShouldDismiss(
            presentationController: UIPresentationController,
        ): Boolean {
            requireMain()
            return ownsDismissalController(presentationController) &&
                (actionChosen || (!isAnimating && properties.dismissOnClickOutside))
        }

        override fun popoverPresentationControllerShouldDismissPopover(
            popoverPresentationController: UIPopoverPresentationController,
        ): Boolean = presentationControllerShouldDismiss(popoverPresentationController)

        override fun presentationControllerDidDismiss(
            presentationController: UIPresentationController,
        ) {
            dismissedNatively(presentationController)
        }

        override fun popoverPresentationControllerDidDismissPopover(
            popoverPresentationController: UIPopoverPresentationController,
        ) {
            dismissedNatively(popoverPresentationController)
        }
    }

    /**
     * The ui view controller that is used to present the dialog.
     */
    @OptIn(ExperimentalForeignApi::class, BetaInteropApi::class)
    internal val dialogUIViewController: UIViewController by lazy {
        UIAlertController.alertControllerWithTitle(
            title = iosProperties.title,
            message = iosProperties.text,
            preferredStyle = iosProperties.style.toUIAlertControllerStyle()
        ).apply {
            iosProperties.actions.forEach { action ->
                val uiAlertAction = UIAlertAction.actionWithTitle(
                    title = action.title,
                    style = action.style.toUIAlertActionStyle(),
                    handler = {
                        actionInvoked(action)
                    },
                )
                uiAlertAction.enabled = action.enabled
                addAction(uiAlertAction)

                if (action.isPreferred) {
                    setPreferredAction(uiAlertAction)
                }
            }

            if (iosProperties.style == AlertDialogIosStyle.Alert) {
                iosProperties.textFields.forEach { textFieldState ->
                    addTextFieldWithConfigurationHandler { textField ->
                        if (textField == null)
                            return@addTextFieldWithConfigurationHandler

                        val textChangedDelegate = object : NSObject() {
                            @ObjCAction
                            fun textFieldDidChange(sender: UITextField) {
                                textFieldState.onValueChange(sender.text.orEmpty())
                            }
                        }

                        // Keep a strong reference so GC doesn't collect the delegate
                        textFieldDelegates.add(textChangedDelegate)

                        textField.text = textFieldState.initialValue
                        textField.placeholder = textFieldState.placeholder
                        textField.keyboardType = textFieldState.keyboardType.toUIKeyboardType()
                        textField.setSecureTextEntry(textFieldState.isSecure)
                        textField.addTarget(
                            target = textChangedDelegate,
                            action = sel_registerName("textFieldDidChange:"),
                            forControlEvents = UIControlEventEditingChanged
                        )
                    }
                }
            }

            if (iosProperties.severity == AlertDialogIosSeverity.Critical)
                setSeverity(UIAlertControllerSeverityCritical)
        }
    }

    /**
     * Updates the properties of the already-presented [UIAlertController]
     * without dismissing and recreating it.
     *
     * Updatable properties:
     * - [UIAlertController.title] and [UIAlertController.message]
     * - [UIAlertAction.enabled] for each action
     */
    internal fun updateDialogProperties() {
        val controller = dialogUIViewController as? UIAlertController ?: return

        controller.title = iosProperties.title
        controller.message = iosProperties.text

        val actions = iosProperties.actions
        for (i in actions.indices) {
            if (i < controller.actions.size) {
                (controller.actions[i] as? UIAlertAction)?.enabled = actions[i].enabled
            }
        }

        configureActionSheetDismissal()
        refreshPopoverAnchor()
    }

    internal fun actionInvoked(action: AlertDialogIosAction) {
        requireMain()
        // Preserve Alert's existing dialog-level dismissal callback.
        actionChosen = iosProperties.style == AlertDialogIosStyle.ActionSheet
        configureActionSheetDismissal()
        action.onClick()
    }

    private fun requireMain() {
        check(NSThread.isMainThread) { "UIKit alert operations must run on Main" }
    }

    private fun ownsNativeController(native: UIPresentationController): Boolean {
        val controller = dialogUIViewController as? UIAlertController ?: return false
        return native.presentedViewController.objcPtr() == controller.objcPtr()
    }

    private fun ownsDismissalController(native: UIPresentationController): Boolean =
        ownsNativeController(native) &&
            (native.objcPtr() == ownedPresentationController?.objcPtr() ||
                native.objcPtr() == ownedPopover?.objcPtr()) &&
            (native.delegate as? NSObject)?.objcPtr() == popoverDelegate.objcPtr()

    /**
     * Notifies the dialog-level callback at most once for a UIKit-initiated
     * action-sheet dismissal. A chosen action already delivered its own callback.
     */
    private fun dismissedNatively(native: UIPresentationController) {
        requireMain()
        if (!ownsDismissalController(native) || !isPresented || isAnimating) return

        dismissalCompleted()
    }

    internal fun dismissalCompleted() {
        requireMain()
        if (!isPresented) return
        isPresented = false
        isAnimating = false
        clearPopoverReferences()
        val notifyDismiss = !actionChosen
        actionChosen = false
        if (notifyDismiss) onDismissRequest()
    }

    private fun ownsPopover(popover: UIPopoverPresentationController): Boolean {
        val owned = ownedPopover ?: return false
        val delegate = popover.delegate as? NSObject ?: return false
        return owned.objcPtr() == popover.objcPtr() &&
            delegate.objcPtr() == popoverDelegate.objcPtr()
    }

    /**
     * Configures only the ActionSheet popover before presentation.
     *
     * This is called before [UIViewController.presentViewController] so UIKit sees
     * a valid view/rect or bar-button anchor for regular-width layouts. Alert-style
     * dialogs never assign a presentation delegate here; UIKit owns that delegation.
     */
    internal fun configurePopoverPresentation(
        popover: UIPopoverPresentationController? =
            (dialogUIViewController as? UIAlertController)?.popoverPresentationController,
    ) {
        requireMain()
        if (iosProperties.style != AlertDialogIosStyle.ActionSheet) return

        configureActionSheetDismissal()
        if (popover == null) return
        ownedPopover = popover
        configureActionSheetDismissal(popover)
        applyPopoverAnchor(popover, popoverAnchor.resolveFor(parentUIViewController))
    }

    /** Also used for compact action sheets that have no popover controller. */
    internal fun configureActionSheetDismissal(
        presentation: UIPresentationController? = dialogUIViewController.presentationController,
    ) {
        requireMain()
        if (iosProperties.style != AlertDialogIosStyle.ActionSheet) return
        dialogUIViewController.modalInPresentation =
            !actionChosen && !properties.dismissOnClickOutside
        if (presentation == null || !ownsNativeController(presentation)) return
        ownedPresentationController?.let { previous ->
            if (previous.objcPtr() != presentation.objcPtr() &&
                previous.objcPtr() != ownedPopover?.objcPtr() &&
                (previous.delegate as? NSObject)?.objcPtr() == popoverDelegate.objcPtr()
            ) previous.delegate = null
        }
        ownedPresentationController = presentation
        presentation.delegate = popoverDelegate
    }

    internal fun presentationCompleted(
        presentation: UIPresentationController? = dialogUIViewController.presentationController,
    ) {
        requireMain()
        isPresented = true
        isAnimating = false
        // UIKit may create/adapt its presentation controller only during presentation.
        configureActionSheetDismissal(presentation)
    }

    private fun refreshPopoverAnchor() {
        val popover = ownedPopover ?: return
        if (!ownsPopover(popover)) return
        applyPopoverAnchor(popover, popoverAnchor.resolveFor(parentUIViewController))
    }

    private fun applyPopoverAnchor(
        popover: UIPopoverPresentationController,
        anchor: ResolvedAlertPopoverAnchor,
    ) {
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

    private fun clearPopoverReferences() {
        ownedPopover?.let { popover ->
            val delegate = popover.delegate as? NSObject
            if (delegate != null && delegate.objcPtr() == popoverDelegate.objcPtr()) {
                val view = ownedAnchorView
                if (view != null && view.objcPtr() == popover.sourceView?.objcPtr()) {
                    popover.sourceView = null
                }
                val barButton = ownedAnchorBarButton
                if (barButton != null && barButton.objcPtr() == popover.barButtonItem?.objcPtr()) {
                    popover.barButtonItem = null
                }
                popover.delegate = null
            }
        }
        ownedPresentationController?.let { presentation ->
            if ((presentation.delegate as? NSObject)?.objcPtr() == popoverDelegate.objcPtr()) {
                presentation.delegate = null
            }
        }
        ownedPresentationController = null
        ownedPopover = null
        ownedAnchorView = null
        ownedAnchorBarButton = null
    }

    /**
     * Lambda that dismisses the dialog.
     */
    private val onDismissLambda: (() -> Unit) = {
        dialogUIViewController.dismissViewControllerAnimated(
            flag = true,
            completion = {
                dismissalCompleted()
            }
        )
    }

    /**
     * Pointer to the [dismiss] method.
     */
    @OptIn(ExperimentalForeignApi::class)
    private val dismissPointer = sel_registerName("dismiss")

    /**
     * Dismisses the dialog.
     */
    @OptIn(BetaInteropApi::class)
    @ObjCAction
    fun dismiss() {
        if (!isPresented || isAnimating) return
        isAnimating = true
        onDismissLambda.invoke()
    }

    /**
     * Shows the dialog.
     */
    @OptIn(ExperimentalForeignApi::class)
    fun showAlertDialog() {
        if (isPresented || isAnimating) return
        isAnimating = true
        actionChosen = false

        dialogUIViewController.applyLayoutDirection(layoutDirection)
        configurePopoverPresentation()

        parentUIViewController.presentViewController(
            viewControllerToPresent = dialogUIViewController,
            animated = iosProperties.animated,
            completion = {
                presentationCompleted()

                // Alerts use the owned outside-tap gesture. Action sheets keep UIKit's
                // native popover dismissal; a tap recognizer on their container can
                // cancel action-button delivery.
                if (iosProperties.style == AlertDialogIosStyle.Alert &&
                    properties.dismissOnClickOutside
                ) {
                    dialogUIViewController.view.superview?.setUserInteractionEnabled(true)
                    dialogUIViewController.view.superview?.addGestureRecognizer(
                        UITapGestureRecognizer(
                            target = this,
                            action = dismissPointer
                        )
                    )
                }
            }
        )
    }

    companion object {
        fun AlertDialogIosActionStyle.toUIAlertActionStyle(): UIAlertActionStyle =
            when (this) {
                AlertDialogIosActionStyle.Default ->
                    UIAlertActionStyleDefault

                AlertDialogIosActionStyle.Cancel ->
                    UIAlertActionStyleCancel

                AlertDialogIosActionStyle.Destructive ->
                    UIAlertActionStyleDestructive
            }

        fun AlertDialogIosStyle.toUIAlertControllerStyle(): UIAlertControllerStyle =
            when (this) {
                AlertDialogIosStyle.ActionSheet ->
                    UIAlertControllerStyleActionSheet

                AlertDialogIosStyle.Alert ->
                    UIAlertControllerStyleAlert
            }

        fun AlertDialogIosAction.toUIAlertAction(): UIAlertAction {
            return UIAlertAction.actionWithTitle(
                title = title,
                style = style.toUIAlertActionStyle(),
                handler = {
                    onClick()
                }
            )
        }
    }
}
