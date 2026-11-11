// Modified for NativeCmpKit (2026-11-08): iOS-only action-sheet popover anchors for UI-013.
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.dialog.uikit

import androidx.compose.runtime.staticCompositionLocalOf
import kotlinx.cinterop.CValue
import kotlinx.cinterop.objcPtr
import kotlinx.cinterop.useContents
import platform.CoreGraphics.CGRect
import platform.CoreGraphics.CGRectMake
import platform.Foundation.NSThread
import platform.UIKit.UIBarButtonItem
import platform.UIKit.UIPopoverArrowDirectionAny
import platform.UIKit.UIView
import platform.UIKit.UIViewController

/**
 * Optional iOS ActionSheet anchor for [LocalAlertDialogIosPopoverAnchor].
 *
 * UIKit requires an anchor for a regular-width (for example, iPad) action-sheet
 * popover before it is presented. Passing `null` to the composition local keeps the
 * previous public dialog signatures and resolves to a documented one-point
 * presenter-center fallback, so existing callers no longer present an anchorless
 * action sheet on regular-width layouts.
 *
 * Anchors are native, main-thread-confined UI objects. They are not saveable state;
 * provide a new value when an explicit anchor changes. Alert-style dialogs ignore
 * the composition local.
 */
sealed class AlertDialogIosPopoverAnchor {
    /**
     * Anchors the popover to a rectangle inside [sourceView].
     *
     * [sourceRect] is in [sourceView]'s local coordinate space, never screen or
     * window coordinates. When it is `null`, the source view's current bounds are
     * read at presentation and whenever UIKit requests a reposition. A detached,
     * foreign-window or missing source view, or a rectangle that is not finite,
     * non-empty and fully inside those bounds, uses the documented presenter-center
     * fallback instead of passing invalid geometry to UIKit.
     *
     * @param sourceView The view whose bounds localize [sourceRect]. It must belong
     * to the presenter's current window at presentation time.
     * @param sourceRect The anchor rectangle in [sourceView]'s local coordinates, or
     * `null` to track its current bounds.
     * @param permittedArrowDirections A mask of `UIPopoverArrowDirection` values.
     */
    class ViewRect(
        val sourceView: UIView?,
        val sourceRect: CValue<CGRect>? = null,
        val permittedArrowDirections: ULong = UIPopoverArrowDirectionAny,
    ) : AlertDialogIosPopoverAnchor() {
        init {
            require(
                (permittedArrowDirections and UIPopoverArrowDirectionAny) == permittedArrowDirections
            ) {
                "permittedArrowDirections must contain only UIPopoverArrowDirection flags"
            }
        }
    }

    /**
     * Anchors the popover to an installed bar button item.
     *
     * [barButtonItem] must be installed in the presenter's current navigation bar,
     * toolbar or other bar when the sheet is presented. UIKit owns the system item's
     * geometry; its private backing view is deliberately not inspected. A `null`
     * item or a detached custom view uses the documented presenter-center fallback.
     * Public UIKit APIs cannot prove that an item is installed: a system item with
     * no custom view, or a custom view elsewhere in the window, is accepted on the
     * caller's installation precondition. Use [ViewRect] when that precondition
     * cannot be guaranteed. Ownership ends after dismissal cleanup.
     *
     * @param barButtonItem The installed bar button item, or `null` for the fallback.
     * @param permittedArrowDirections A mask of `UIPopoverArrowDirection` values.
     */
    class BarButton(
        val barButtonItem: UIBarButtonItem?,
        val permittedArrowDirections: ULong = UIPopoverArrowDirectionAny,
    ) : AlertDialogIosPopoverAnchor() {
        init {
            require(
                (permittedArrowDirections and UIPopoverArrowDirectionAny) == permittedArrowDirections
            ) {
                "permittedArrowDirections must contain only UIPopoverArrowDirection flags"
            }
        }
    }
}

/**
 * Provides an [AlertDialogIosPopoverAnchor] around `AdaptiveAlertDialog` or
 * `AdaptiveBasicAlertDialog` when using [AlertDialogIosStyle.ActionSheet].
 *
 * Defaults to `null`, which resolves to a one-point presenter-center anchor with no
 * arrow. Alert-style dialogs ignore this local. This API is iOS-only and additive;
 * the common dialog signatures and data-class constructors are unchanged.
 */
val LocalAlertDialogIosPopoverAnchor =
    staticCompositionLocalOf<AlertDialogIosPopoverAnchor?> { null }

/** A validated anchor in a coordinate space UIKit accepts. */
internal sealed class ResolvedAlertPopoverAnchor {
    class ViewRect(
        val view: UIView,
        val rect: CValue<CGRect>,
        val arrows: ULong,
    ) : ResolvedAlertPopoverAnchor()

    class BarButton(
        val item: UIBarButtonItem,
        val arrows: ULong,
    ) : ResolvedAlertPopoverAnchor()
}

/**
 * Resolves the requested anchor against the presenter's current window.
 *
 * This must run on Main because it reads UIKit view/window state and is used
 * immediately before configuring a [platform.UIKit.UIPopoverPresentationController].
 * Missing bar items and detached/invalid view anchors resolve to a finite fallback
 * instead of being forwarded to UIKit.
 */
internal fun AlertDialogIosPopoverAnchor?.resolveFor(
    parent: UIViewController,
): ResolvedAlertPopoverAnchor {
    check(NSThread.isMainThread) { "UIKit popover anchors must be resolved on Main" }

    val presenter = parent.view
    val window = presenter.window

    fun inCurrentWindow(view: UIView?): Boolean =
        view != null && window != null && view.window?.objcPtr() == window.objcPtr()

    when (this) {
        is AlertDialogIosPopoverAnchor.ViewRect -> {
            val view = sourceView
            if (view != null && inCurrentWindow(view)) {
                val bounds = view.bounds()
                val rect = sourceRect ?: bounds
                if (validRectInBounds(rect, bounds)) {
                    return ResolvedAlertPopoverAnchor.ViewRect(
                        view = view,
                        rect = rect,
                        arrows = permittedArrowDirections,
                    )
                }
            }
        }

        is AlertDialogIosPopoverAnchor.BarButton -> {
            val item = barButtonItem
            if (item != null && window != null &&
                (item.customView == null || inCurrentWindow(item.customView))
            ) {
                return ResolvedAlertPopoverAnchor.BarButton(
                    item = item,
                    arrows = permittedArrowDirections,
                )
            }
        }

        null -> Unit
    }

    return ResolvedAlertPopoverAnchor.ViewRect(
        view = presenter,
        rect = fallbackCenterRect(presenter.bounds()),
        arrows = 0uL,
    )
}

private fun fallbackCenterRect(bounds: CValue<CGRect>): CValue<CGRect> = bounds.useContents {
    val x = origin.x + size.width / 2.0
    val y = origin.y + size.height / 2.0
    CGRectMake(
        x.takeIf { it.isFinite() } ?: 0.0,
        y.takeIf { it.isFinite() } ?: 0.0,
        1.0,
        1.0,
    )
}

private fun validRectInBounds(
    rect: CValue<CGRect>,
    bounds: CValue<CGRect>,
): Boolean = bounds.useContents {
    val left = origin.x
    val top = origin.y
    val right = left + size.width
    val bottom = top + size.height

    if (!left.isFinite() || !top.isFinite() || !right.isFinite() || !bottom.isFinite() ||
        !size.width.isFinite() || !size.height.isFinite() ||
        size.width <= 0.0 || size.height <= 0.0
    ) {
        return@useContents false
    }

    rect.useContents {
        origin.x.isFinite() && origin.y.isFinite() &&
            size.width.isFinite() && size.height.isFinite() &&
            size.width > 0.0 && size.height > 0.0 &&
            (origin.x + size.width).isFinite() &&
            (origin.y + size.height).isFinite() &&
            origin.x >= left && origin.y >= top &&
            origin.x + size.width <= right &&
            origin.y + size.height <= bottom
    }
}
