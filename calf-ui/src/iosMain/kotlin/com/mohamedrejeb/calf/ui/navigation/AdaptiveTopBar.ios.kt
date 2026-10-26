// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.navigation

import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.TopAppBarColors
import androidx.compose.material3.TopAppBarScrollBehavior
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.mohamedrejeb.calf.ui.ExperimentalCalfUiApi
import com.mohamedrejeb.calf.ui.utils.applyLayoutDirection
import com.mohamedrejeb.calf.ui.utils.isIOS26OrAbove
import platform.UIKit.UINavigationBar

/** Native content uses ios* arguments, but ownership, modifiers and insets belong to Compose. */
@OptIn(ExperimentalMaterial3Api::class)
@ExperimentalCalfUiApi
@Composable
actual fun AdaptiveTopBar(
    modifier: Modifier,
    title: @Composable () -> Unit,
    navigationIcon: @Composable () -> Unit,
    actions: @Composable RowScope.() -> Unit,
    expandedHeight: Dp,
    windowInsets: WindowInsets,
    colors: TopAppBarColors,
    scrollBehavior: TopAppBarScrollBehavior?,
    iosTitle: String,
    iosLeadingItems: List<UIKitUIBarButtonItem>,
    iosTrailingItems: List<UIKitUIBarButtonItem>,
    iosConfiguration: UIKitNavigationBarConfiguration,
) {
    val density = LocalDensity.current
    val direction = LocalLayoutDirection.current
    val bar = remember { UINavigationBar() }
    val manager = remember(bar) { TopBarManager(bar) }
    SideEffect {
        bar.applyLayoutDirection(direction)
        manager.update(iosTitle, iosLeadingItems, iosTrailingItems, iosConfiguration,
            isIOS26OrAbove(), density.density, direction)
    }
    NativeBar(bar, if (iosConfiguration.prefersLargeTitles) 96.dp else 44.dp,
        modifier.windowInsetsPadding(windowInsets))
}
