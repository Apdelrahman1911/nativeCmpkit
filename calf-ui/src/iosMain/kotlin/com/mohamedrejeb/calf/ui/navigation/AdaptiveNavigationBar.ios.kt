// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.navigation

import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.mohamedrejeb.calf.ui.ExperimentalCalfUiApi
import com.mohamedrejeb.calf.ui.utils.applyLayoutDirection
import platform.UIKit.UITabBar

@ExperimentalCalfUiApi
@Composable
actual fun AdaptiveNavigationBar(
    modifier: Modifier,
    containerColor: Color,
    contentColor: Color,
    tonalElevation: Dp,
    windowInsets: WindowInsets,
    iosItems: List<UIKitUITabBarItem>,
    iosSelectedIndex: Int,
    iosOnItemSelected: (Int) -> Unit,
    iosConfiguration: UIKitTabBarConfiguration,
    content: @Composable RowScope.() -> Unit,
) {
    val density = LocalDensity.current
    val direction = LocalLayoutDirection.current
    val onSelected by rememberUpdatedState(iosOnItemSelected)
    val bar = remember { UITabBar() }
    val manager = remember(bar) { TabBarManager(bar) { onSelected(it) } }
    SideEffect {
        bar.applyLayoutDirection(direction)
        manager.setItems(iosItems, iosSelectedIndex, density.density, direction)
        manager.updateConfiguration(iosConfiguration)
    }
    NativeBar(bar, 49.dp, modifier.windowInsetsPadding(windowInsets))
}
