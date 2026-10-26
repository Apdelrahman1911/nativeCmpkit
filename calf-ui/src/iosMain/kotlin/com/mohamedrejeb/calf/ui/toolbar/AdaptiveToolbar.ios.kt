// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.toolbar

import androidx.compose.foundation.layout.RowScope
import androidx.compose.material3.ExperimentalMaterial3ExpressiveApi
import androidx.compose.material3.FloatingToolbarDefaults
import androidx.compose.material3.HorizontalFloatingToolbar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.unit.dp
import com.mohamedrejeb.calf.ui.ExperimentalCalfUiApi
import com.mohamedrejeb.calf.ui.navigation.NativeBar
import com.mohamedrejeb.calf.ui.navigation.UIKitUIBarButtonItem
import com.mohamedrejeb.calf.ui.utils.isIOS26OrAbove

@OptIn(ExperimentalMaterial3ExpressiveApi::class)
@ExperimentalCalfUiApi
@Composable
actual fun AdaptiveToolbar(
    expanded: Boolean,
    modifier: Modifier,
    leadingContent: @Composable (RowScope.() -> Unit)?,
    trailingContent: @Composable (RowScope.() -> Unit)?,
    content: @Composable RowScope.() -> Unit,
    iosItems: List<UIKitUIBarButtonItem>,
) {
    if (!isIOS26OrAbove() || iosItems.isEmpty()) {
        HorizontalFloatingToolbar(expanded = expanded, modifier = modifier,
            colors = FloatingToolbarDefaults.standardFloatingToolbarColors(),
            leadingContent = leadingContent, trailingContent = trailingContent, content = content)
        return
    }
    val density = LocalDensity.current
    val direction = LocalLayoutDirection.current
    val manager = remember { ToolbarManager() }
    SideEffect {
        manager.applyLayoutDirection(direction)
        manager.update(iosItems, density.density, direction)
    }
    // Native items have no Material expanded/leading/trailing slot analogue. Placement and
    // insets are now chosen by the caller, rather than an implicit root-bottom overlay.
    NativeBar(manager.toolbar, 44.dp, modifier)
}
