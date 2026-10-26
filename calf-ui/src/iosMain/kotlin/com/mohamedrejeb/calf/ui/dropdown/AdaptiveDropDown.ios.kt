// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.dropdown

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.ScrollState
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.offset
import androidx.compose.material3.DropdownMenu
import androidx.compose.runtime.*
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.DpOffset
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.viewinterop.UIKitInteropProperties
import androidx.compose.ui.viewinterop.UIKitView
import androidx.compose.ui.window.PopupProperties
import com.mohamedrejeb.calf.ui.ExperimentalCalfUiApi
import com.mohamedrejeb.calf.ui.utils.applyLayoutDirection
import com.mohamedrejeb.calf.ui.utils.toUIImage
import kotlinx.cinterop.CValue
import kotlinx.cinterop.ObjCSignatureOverride
import kotlinx.cinterop.useContents
import platform.CoreGraphics.CGPoint
import platform.CoreGraphics.CGRectMake
import platform.UIKit.*

@OptIn(ExperimentalComposeUiApi::class)
@ExperimentalCalfUiApi
@Composable
actual fun BoxScope.AdaptiveDropDown(
    expanded: Boolean,
    onDismissRequest: () -> Unit,
    iosItems: List<AdaptiveDropDownItem>,
    modifier: Modifier,
    offset: DpOffset,
    scrollState: ScrollState,
    properties: PopupProperties,
    shape: Shape,
    containerColor: Color,
    tonalElevation: Dp,
    shadowElevation: Dp,
    border: BorderStroke?,
    iosSections: List<AdaptiveDropDownSection>,
    materialContent: @Composable ColumnScope.() -> Unit,
) {
    if (!supportsProgrammaticNativeMenu(UIDevice.currentDevice.systemVersion)) {
        DropdownMenu(expanded = expanded, onDismissRequest = onDismissRequest, modifier = modifier,
            offset = offset, scrollState = scrollState, properties = properties, shape = shape,
            containerColor = containerColor, tonalElevation = tonalElevation,
            shadowElevation = shadowElevation, border = border, content = materialContent)
        return
    }
    val density = LocalDensity.current
    val direction = LocalLayoutDirection.current
    val button = remember { DropDownMenuButton() }
    val delegate = remember(button) { DropDownMenuDelegate() }
    SideEffect {
        delegate.items = iosItems
        delegate.sections = iosSections
        delegate.density = density.density
        delegate.layoutDirection = direction
        button.onDismissRequest = onDismissRequest
        button.applyLayoutDirection(direction)
    }
    LaunchedEffect(button, iosItems, iosSections, density, direction) {
        button.menu = delegate.buildMenu()
        button.updatePresentation()
    }
    LaunchedEffect(button, expanded) { button.setExpanded(expanded) }
    DisposableEffect(button) { onDispose { button.dispose() } }
    // The transparent native anchor is measured/moved by Compose, not by screen coordinates.
    UIKitView(factory = { button }, modifier = modifier.matchParentSize().offset(offset.x, offset.y),
        properties = UIKitInteropProperties(interactionMode = null, isNativeAccessibilityEnabled = false))
}

/** Public UIKit lifecycle callbacks, rather than fabricated private gesture recognizers. */
internal class DropDownMenuButton : UIButton(frame = CGRectMake(0.0, 0.0, 0.0, 0.0)),
    UIContextMenuInteractionDelegateProtocol {
    var onDismissRequest: () -> Unit = {}
    private var requested = false
    private var opening = false
    private var showing = false
    private var closing = false
    private var disposed = false
    internal val isMenuPresented: Boolean get() = showing

    init {
        backgroundColor = UIColor.clearColor
        showsMenuAsPrimaryAction = true
        isAccessibilityElement = false
    }

    fun setExpanded(expanded: Boolean) {
        if (disposed) return
        requested = expanded
        updatePresentation()
    }

    fun updatePresentation() {
        if (disposed) return
        if (!requested) {
            if (showing || opening) contextMenuInteraction?.dismissMenu()
            return
        }
        if (showing || opening || closing || window == null || menu?.children?.isEmpty() != false) return
        if (!bounds.useContents { size.width > 0 && size.height > 0 }) return
        opening = true
        performPrimaryAction()
    }

    override fun didMoveToWindow() {
        super.didMoveToWindow()
        updatePresentation()
    }

    override fun layoutSubviews() {
        super.layoutSubviews()
        updatePresentation()
    }

    // UIControl's category methods are final extensions in Kotlin/Native, not
    // overridable class members. Adopt the public delegate protocol explicitly
    // and supply our menu configuration instead of inventing a category super call.
    @ObjCSignatureOverride
    override fun contextMenuInteraction(
        interaction: UIContextMenuInteraction,
        configurationForMenuAtLocation: CValue<CGPoint>,
    ): UIContextMenuConfiguration? {
        if (disposed || !requested) return null
        val requestedMenu = menu ?: return null
        return UIContextMenuConfiguration.configurationWithIdentifier(
            identifier = null, previewProvider = null, actionProvider = { requestedMenu })
    }

    @ObjCSignatureOverride
    override fun contextMenuInteraction(
        interaction: UIContextMenuInteraction,
        willDisplayMenuForConfiguration: UIContextMenuConfiguration,
        animator: UIContextMenuInteractionAnimatingProtocol?,
    ) {
        opening = false
        showing = true
        if (!requested || disposed) interaction.dismissMenu()
    }

    @ObjCSignatureOverride
    override fun contextMenuInteraction(
        interaction: UIContextMenuInteraction,
        willEndForConfiguration: UIContextMenuConfiguration,
        animator: UIContextMenuInteractionAnimatingProtocol?,
    ) {
        val notify = requested
        requested = false
        opening = false
        closing = true
        val finished = {
            showing = false
            closing = false
            if (!disposed && notify) onDismissRequest()
            updatePresentation()
        }
        if (animator != null) animator.addCompletion(finished) else finished()
    }

    fun dispose() {
        disposed = true
        requested = false
        onDismissRequest = {}
        contextMenuInteraction?.dismissMenu()
        menu = null
    }
}

internal class DropDownMenuDelegate {
    var items: List<AdaptiveDropDownItem> = emptyList()
    var sections: List<AdaptiveDropDownSection> = emptyList()
    var density = 1f
    var layoutDirection = LayoutDirection.Ltr

    fun buildMenu(): UIMenu = UIMenu.menuWithTitle("", children =
        items.mapIndexed { index, item -> action(item) { items.getOrNull(index) } } +
            sections.mapIndexed { sectionIndex, section ->
                UIMenu.menuWithTitle(section.title, image = null, identifier = null,
                    options = UIMenuOptionsDisplayInline,
                    children = section.items.mapIndexed { index, item ->
                        action(item) { sections.getOrNull(sectionIndex)?.items?.getOrNull(index) }
                    })
            })

    private fun action(item: AdaptiveDropDownItem, current: () -> AdaptiveDropDownItem?): UIAction =
        UIAction.actionWithTitle(item.title, image = item.iosIcon?.toUIImage(density, layoutDirection), identifier = null) {
            // A callback-only update follows the current descriptor. If its visible title or
            // position changed, don't apply a stale native menu action to a different item.
            current()?.takeIf { it.title == item.title && !it.isDisabled }?.onClick?.invoke()
        }.apply {
            var flags = 0uL
            if (item.isDestructive) flags = flags or UIMenuElementAttributesDestructive
            if (item.isDisabled) flags = flags or UIMenuElementAttributesDisabled
            attributes = flags
        }
}
