// SPDX-License-Identifier: Apache-2.0
// Modified for NativeCmpKit (2026-11-03): supported, lifecycle-aware iOS action-sheet anchors.
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
 * Existing dialog functions and common property constructors are unchanged.
 * Anchors are native, Main-confined UI objects, not saveable state. Replace the
 * provided value when an explicit rectangle changes; a null rectangle reads
 * the source view's current bounds at presentation and native repositioning.
 */
sealed class AlertDialogIosPopoverAnchor {
    /**
     * [sourceRect] is in [sourceView]'s LOCAL coordinates, never screen coordinates.
     * A detached/foreign-window/missing view or nonfinite/out-of-bounds rectangle
     * uses the documented presenter-center fallback instead of invalid UIKit input.
     */
    class ViewRect(
        val sourceView: UIView?,
        val sourceRect: CValue<CGRect>? = null,
        val permittedArrowDirections: ULong = UIPopoverArrowDirectionAny,
    ) : AlertDialogIosPopoverAnchor() {
        init { require((permittedArrowDirections and UIPopoverArrowDirectionAny) == permittedArrowDirections) }
    }

    /**
     * [barButtonItem] must be installed in the presenter's current navigation bar
     * or toolbar. UIKit positions system items; their private backing view is
     * deliberately not inspected. A missing item or detached custom view falls
     * back to the presenter. Ownership ends with the dialog composition.
     */
    class BarButton(
        val barButtonItem: UIBarButtonItem?,
        val permittedArrowDirections: ULong = UIPopoverArrowDirectionAny,
    ) : AlertDialogIosPopoverAnchor() {
        init { require((permittedArrowDirections and UIPopoverArrowDirectionAny) == permittedArrowDirections) }
    }
}

/**
 * Provide an [AlertDialogIosPopoverAnchor] around either adaptive alert function
 * when using ActionSheet style. Defaults to a one-point presenter-center anchor
 * with no arrow. Alert style ignores this local. No Android/Desktop/web API changes.
 */
val LocalAlertDialogIosPopoverAnchor = staticCompositionLocalOf<AlertDialogIosPopoverAnchor?> { null }

internal sealed class ResolvedAlertPopoverAnchor {
    class ViewRect(val view: UIView, val rect: CValue<CGRect>, val arrows: ULong) : ResolvedAlertPopoverAnchor()
    class BarButton(val item: UIBarButtonItem, val arrows: ULong) : ResolvedAlertPopoverAnchor()
}

internal fun AlertDialogIosPopoverAnchor?.resolveFor(parent: UIViewController): ResolvedAlertPopoverAnchor {
    check(NSThread.isMainThread) { "UIKit popover anchors must be resolved on Main" }
    val presenter = parent.view
    val window = presenter.window
    fun inCurrentWindow(view: UIView): Boolean = window != null && view.window?.objcPtr() == window.objcPtr()
    when (this) {
        is AlertDialogIosPopoverAnchor.ViewRect -> {
            val view = sourceView
            if (view != null && inCurrentWindow(view)) {
                val bounds = view.bounds
                val rect = sourceRect ?: bounds
                if (validRectInBounds(rect, bounds)) {
                    return ResolvedAlertPopoverAnchor.ViewRect(view, rect, permittedArrowDirections)
                }
            }
        }
        is AlertDialogIosPopoverAnchor.BarButton -> {
            val item = barButtonItem
            if (item != null && window != null && (item.customView?.let(::inCurrentWindow) != false)) {
                return ResolvedAlertPopoverAnchor.BarButton(item, permittedArrowDirections)
            }
        }
        null -> Unit
    }
    val rect = presenter.bounds.useContents {
        val x = (origin.x + size.width / 2).takeIf { it.isFinite() } ?: 0.0
        val y = (origin.y + size.height / 2).takeIf { it.isFinite() } ?: 0.0
        CGRectMake(x, y, 1.0, 1.0)
    }
    return ResolvedAlertPopoverAnchor.ViewRect(presenter, rect, 0u)
}

private fun validRectInBounds(rect: CValue<CGRect>, bounds: CValue<CGRect>): Boolean = bounds.useContents {
    val left = origin.x
    val top = origin.y
    val right = left + size.width
    val bottom = top + size.height
    if (!left.isFinite() || !top.isFinite() || !right.isFinite() || !bottom.isFinite() ||
        !size.width.isFinite() || !size.height.isFinite() || size.width <= 0.0 || size.height <= 0.0) return@useContents false
    rect.useContents {
        origin.x.isFinite() && origin.y.isFinite() && size.width.isFinite() && size.height.isFinite() &&
            size.width >= 0.0 && size.height >= 0.0 && (origin.x + size.width).isFinite() &&
            (origin.y + size.height).isFinite() && origin.x >= left && origin.y >= top &&
            origin.x + size.width <= right && origin.y + size.height <= bottom
    }
}
