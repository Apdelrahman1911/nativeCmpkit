// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
@file:OptIn(BetaInteropApi::class, ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.fab

import androidx.compose.ui.unit.LayoutDirection
import com.mohamedrejeb.calf.ui.utils.applyLayoutDirection
import com.mohamedrejeb.calf.ui.utils.isIOS26OrAbove
import com.mohamedrejeb.calf.ui.utils.toUIImage
import kotlinx.cinterop.BetaInteropApi
import kotlinx.cinterop.CValue
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.ObjCAction
import kotlinx.cinterop.useContents
import platform.CoreGraphics.CGAffineTransformMakeRotation
import platform.CoreGraphics.CGAffineTransformMakeScale
import platform.CoreGraphics.CGPoint
import platform.CoreGraphics.CGRectMake
import platform.UIKit.UIAccessibilityTraitButton
import platform.UIKit.UIAccessibilityTraitSelected
import platform.UIKit.UIButton
import platform.UIKit.UIButtonConfiguration
import platform.UIKit.UIControlEventTouchUpInside
import platform.UIKit.UIEvent
import platform.UIKit.UIImageSymbolConfiguration
import platform.UIKit.UIView
import platform.UIKit.UIViewAutoresizingFlexibleHeight
import platform.UIKit.UIViewAutoresizingFlexibleWidth
import platform.UIKit.accessibilityElementsHidden
import platform.UIKit.accessibilityLabel
import platform.UIKit.accessibilityTraits
import platform.UIKit.isAccessibilityElement
import platform.darwin.NSObject
import platform.darwin.sel_registerName
import kotlin.math.PI

private const val FAB_SIZE = 50.0
private const val FAB_MARGIN = 16.0
private const val ITEM_SPACING = 12.0

/** Internal prototype, not a public supported component. Its overlay passes empty-area hits through. */
internal class ExpandableFABManager(
    private val onExpandedChange: (Boolean) -> Unit,
    private val onItemSelected: (Int) -> Unit,
) {
    private var containerView: FABContainerView? = null
    private var parentView: UIView? = null
    private var mainButton: UIButton? = null
    private var itemButtons: List<UIButton> = emptyList()
    private var isExpanded = false
    private var modelGeneration = 0L
    private var layoutDirection = LayoutDirection.Ltr
    private var mainActionHandler: MainFABActionHandler? = null
    private var itemActionHandlers: List<ItemFABActionHandler> = emptyList()
    private val useGlass = isIOS26OrAbove()

    fun attachTo(view: UIView) {
        if (parentView === view && containerView != null) return
        detach()
        parentView = view
        val container = FABContainerView().apply {
            setFrame(view.bounds)
            autoresizingMask = UIViewAutoresizingFlexibleWidth or UIViewAutoresizingFlexibleHeight
            clipsToBounds = false
            onLayout = { layoutButtons() }
            applyLayoutDirection(layoutDirection)
        }
        containerView = container
        view.addSubview(container)
    }

    fun detach() {
        modelGeneration++
        containerView?.onLayout = null
        mainButton?.layer?.removeAllAnimations()
        itemButtons.forEach { it.layer.removeAllAnimations() }
        containerView?.removeFromSuperview()
        containerView = null
        parentView = null
        mainButton = null
        itemButtons = emptyList()
        mainActionHandler = null
        itemActionHandlers = emptyList()
    }

    fun updateItems(mainImage: UIKitExpandableFABItem, items: List<UIKitExpandableFABItem>, density: Float) {
        val container = containerView ?: return
        mainButton?.layer?.removeAllAnimations()
        mainButton?.removeFromSuperview()
        itemButtons.forEach { it.layer.removeAllAnimations(); it.removeFromSuperview() }
        modelGeneration++
        mainActionHandler = MainFABActionHandler(this, modelGeneration)
        itemActionHandlers = items.indices.map { ItemFABActionHandler(this, it, modelGeneration) }
        itemButtons = items.mapIndexed { index, item ->
            createItemButton(item, index, density).also(container::addSubview)
        }
        mainButton = createMainButton(mainImage, density).also(container::addSubview)
        layoutButtons()
        // Rebuilding while already expanded must not leave newly created buttons hidden/scaled.
        applyExpansion(animated = false)
    }

    fun applyLayoutDirection(layoutDirection: LayoutDirection) {
        this.layoutDirection = layoutDirection
        containerView?.applyLayoutDirection(layoutDirection)
        containerView?.setNeedsLayout()
        layoutButtons()
    }

    fun setExpanded(expanded: Boolean) {
        if (isExpanded == expanded) return
        isExpanded = expanded
        applyExpansion(animated = true)
    }

    internal fun handleMainButtonTap(generation: Long) {
        if (generation != modelGeneration || mainButton == null) return
        onExpandedChange(!isExpanded)
    }

    internal fun handleItemButtonTap(index: Int, generation: Long) {
        if (generation != modelGeneration || !isExpanded || index !in itemButtons.indices) return
        onItemSelected(index)
        onExpandedChange(false)
    }

    private fun createMainButton(item: UIKitExpandableFABItem, density: Float): UIButton {
        val config = if (useGlass) UIButtonConfiguration.prominentGlassButtonConfiguration()
        else UIButtonConfiguration.filledButtonConfiguration()
        config.setPreferredSymbolConfigurationForImage(UIImageSymbolConfiguration.configurationWithPointSize(20.0))
        config.setImage(item.image?.toUIImage(density, layoutDirection))
        return UIButton.buttonWithConfiguration(config, primaryAction = null).apply {
            accessibilityLabel = item.title
            isAccessibilityElement = true
            addTarget(mainActionHandler, sel_registerName("mainButtonTapped"), UIControlEventTouchUpInside)
        }
    }

    private fun createItemButton(item: UIKitExpandableFABItem, index: Int, density: Float): UIButton {
        val config = if (useGlass) UIButtonConfiguration.glassButtonConfiguration()
        else UIButtonConfiguration.filledButtonConfiguration()
        config.setPreferredSymbolConfigurationForImage(UIImageSymbolConfiguration.configurationWithPointSize(18.0))
        config.setImage(item.image?.toUIImage(density, layoutDirection))
        return UIButton.buttonWithConfiguration(config, primaryAction = null).apply {
            tag = index.toLong()
            accessibilityLabel = item.title
            isAccessibilityElement = true
            accessibilityTraits = UIAccessibilityTraitButton
            addTarget(itemActionHandlers[index], sel_registerName("itemButtonTapped"), UIControlEventTouchUpInside)
        }
    }

    private fun layoutButtons() {
        val container = containerView ?: return
        val main = mainButton ?: return
        val width = container.bounds.useContents { size.width }
        val height = container.bounds.useContents { size.height }
        val insets = container.safeAreaInsets
        val left = insets.useContents { left }
        val right = insets.useContents { right }
        val bottom = insets.useContents { bottom }
        val top = insets.useContents { top }
        val x = if (layoutDirection == LayoutDirection.Rtl) left + FAB_MARGIN
        else (width - right - FAB_MARGIN - FAB_SIZE).coerceAtLeast(left + FAB_MARGIN)
        val mainY = (height - bottom - FAB_MARGIN - FAB_SIZE).coerceAtLeast(top + FAB_MARGIN)
        // Bounds/frame layout belongs to UIKit; safe-area changes and parent resizing re-enter here.
        // Reset transforms before assigning frames, then reapply the current expansion appearance.
        main.setTransform(CGAffineTransformMakeScale(1.0, 1.0))
        main.setFrame(CGRectMake(x, mainY, FAB_SIZE, FAB_SIZE))
        itemButtons.forEachIndexed { index, button ->
            button.setTransform(CGAffineTransformMakeScale(1.0, 1.0))
            button.setFrame(CGRectMake(x, mainY - (index + 1) * (FAB_SIZE + ITEM_SPACING), FAB_SIZE, FAB_SIZE))
        }
        applyExpansion(animated = false)
    }

    private fun applyExpansion(animated: Boolean) {
        val main = mainButton ?: return
        val expanded = isExpanded
        val buttons = itemButtons
        buttons.forEach {
            it.userInteractionEnabled = expanded
            it.accessibilityElementsHidden = !expanded
        }
        main.accessibilityTraits = UIAccessibilityTraitButton or if (expanded) UIAccessibilityTraitSelected else 0uL
        val changes = {
            buttons.forEach {
                it.alpha = if (expanded) 1.0 else 0.0
                val scale = if (expanded) 1.0 else .3
                it.setTransform(CGAffineTransformMakeScale(scale, scale))
            }
            main.setTransform(if (expanded) CGAffineTransformMakeRotation(PI / 4.0) else CGAffineTransformMakeScale(1.0, 1.0))
        }
        if (animated) {
            UIView.animateWithDuration(.35, 0.0, .8, .5, 0u, changes, null)
        } else {
            UIView.performWithoutAnimation(changes)
        }
    }
}

/** A full-parent layout observer that is not itself a hit-test target. */
internal class FABContainerView : UIView(frame = CGRectMake(0.0, 0.0, 0.0, 0.0)) {
    var onLayout: (() -> Unit)? = null

    override fun layoutSubviews() {
        super.layoutSubviews()
        onLayout?.invoke()
    }

    override fun safeAreaInsetsDidChange() {
        super.safeAreaInsetsDidChange()
        setNeedsLayout()
    }

    override fun hitTest(point: CValue<CGPoint>, withEvent: UIEvent?): UIView? {
        val hit = super.hitTest(point, withEvent)
        return if (hit === this) null else hit
    }
}

internal class MainFABActionHandler(private val manager: ExpandableFABManager, private val generation: Long) : NSObject() {
    @Suppress("unused")
    @ObjCAction
    fun mainButtonTapped() = manager.handleMainButtonTap(generation)
}

internal class ItemFABActionHandler(
    private val manager: ExpandableFABManager,
    private val index: Int,
    private val generation: Long,
) : NSObject() {
    @Suppress("unused")
    @ObjCAction
    fun itemButtonTapped() = manager.handleItemButtonTap(index, generation)
}
