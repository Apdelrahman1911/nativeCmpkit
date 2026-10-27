// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.navigation

import androidx.compose.ui.graphics.isSpecified
import androidx.compose.ui.unit.LayoutDirection
import com.mohamedrejeb.calf.ui.utils.toUIColor
import com.mohamedrejeb.calf.ui.utils.toUIImage
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.objcPtr
import platform.UIKit.UIColor
import platform.UIKit.UITabBar
import platform.UIKit.UITabBarDelegateProtocol
import platform.UIKit.UITabBarItem
import platform.darwin.NSObject

/**
 * A helper class that manages a native iOS UITabBar, handling item setup and selection.
 *
 * @param tabBar The native UITabBar instance to manage.
 * @param onItemSelected Callback invoked when a tab bar item is selected, with the item index.
 */
@OptIn(ExperimentalForeignApi::class)
internal class TabBarManager(
    private val tabBar: UITabBar,
    onItemSelected: (Int) -> Unit,
) {
    private val uiTabBarDelegate = UITabBarDelegate(
        onItemSelected = onItemSelected,
    )

    // Capture the original tint colors so we can restore iOS defaults when the user
    // switches back to Color.Unspecified.
    private val defaultTintColor: UIColor = tabBar.tintColor
    private val defaultUnselectedItemTintColor: UIColor? = tabBar.unselectedItemTintColor

    private var currentItems = emptyList<UIKitUITabBarItem>()
    private var currentConfiguration: UIKitTabBarConfiguration? = null
    private var currentDensity = Float.NaN
    private var currentLayoutDirection = LayoutDirection.Ltr

    init {
        tabBar.delegate = uiTabBarDelegate
    }

    fun setItems(
        items: List<UIKitUITabBarItem>,
        selectedIndex: Int,
        density: Float,
        layoutDirection: LayoutDirection = LayoutDirection.Ltr,
    ) {
        if (items.isEmpty()) {
            tabBar.selectedItem = null
            tabBar.setItems(emptyList<UITabBarItem>())
            currentItems = emptyList()
            return
        }

        if (items != currentItems || density != currentDensity || layoutDirection != currentLayoutDirection) {
            val uiKitItems = items.mapIndexed { index, item ->
                item.toUITabBarItem(index.toLong(), density, layoutDirection)
            }
            tabBar.setItems(uiKitItems)
            currentItems = items
            currentDensity = density
            currentLayoutDirection = layoutDirection
            val safeSelectedIndex = selectedIndex.coerceIn(uiKitItems.indices)
            tabBar.selectedItem = uiKitItems[safeSelectedIndex]
        } else {
            val uiKitItems = tabBar.items?.filterIsInstance<UITabBarItem>() ?: return
            val safeSelectedIndex = selectedIndex.coerceIn(uiKitItems.indices)
            tabBar.selectedItem = uiKitItems[safeSelectedIndex]
        }
    }

    fun updateConfiguration(
        configuration: UIKitTabBarConfiguration,
    ) {
        if (configuration == currentConfiguration) return

        tabBar.translucent = configuration.isTranslucent

        // Selected item tint — UITabBar.tintColor controls the selected icon+label color
        tabBar.tintColor =
            if (configuration.selectedItemColor.isSpecified)
                configuration.selectedItemColor.toUIColor()
            else
                defaultTintColor

        // Unselected item color works on pre-Liquid Glass iOS via unselectedItemTintColor.
        // Note: Liquid Glass (iOS 26+) ignores this property; not yet supported.
        tabBar.unselectedItemTintColor =
            if (configuration.unselectedItemColor.isSpecified)
                configuration.unselectedItemColor.toUIColor()
            else
                defaultUnselectedItemTintColor

        currentConfiguration = configuration
    }
}

private fun UIKitUITabBarItem.toUITabBarItem(tag: Long, density: Float, layoutDirection: LayoutDirection): UITabBarItem {
    val item = UITabBarItem(
        title = title,
        image = image?.toUIImage(density, layoutDirection),
        tag = tag,
    )
    selectedImage?.toUIImage(density, layoutDirection)?.let { item.selectedImage = it }
    return item
}

@OptIn(ExperimentalForeignApi::class)
internal class UITabBarDelegate(
    private val onItemSelected: (Int) -> Unit,
) : NSObject(), UITabBarDelegateProtocol {
    override fun tabBar(tabBar: UITabBar, didSelectItem: UITabBarItem) {
        // UIKit callbacks may arrive after a caller cleared/reordered the items
        // or replaced the manager. A tag is mutable metadata, not ownership or
        // a safe current index. Compare the real native identities, not Kotlin
        // wrapper identity, and never resurrect a detached/foreign selection.
        if (tabBar.delegate?.objcPtr() != objcPtr()) return
        val index = tabBar.items.orEmpty().indexOfFirst { item ->
            item is UITabBarItem && item.objcPtr() == didSelectItem.objcPtr()
        }
        if (index < 0) return
        tabBar.selectedItem = didSelectItem
        onItemSelected(index)
    }
}
