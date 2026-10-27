@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.navigation

import com.mohamedrejeb.calf.ui.internal.runNativeUiTest
import platform.CoreGraphics.CGRectMake
import platform.UIKit.*
import kotlin.test.*

class NativeBarOwnershipTest {
    @Test fun emptyTabsClearSelectionAndRepopulationClampsIndex() = runNativeUiTest {
        val bar = UITabBar()
        val selections = mutableListOf<Int>()
        val manager = TabBarManager(bar) { selections += it }
        val items = listOf(UIKitUITabBarItem("One"), UIKitUITabBarItem("Two"))
        manager.setItems(items, 99, 1f)
        assertEquals(1L, bar.selectedItem?.tag)
        val originalItems = bar.items.orEmpty().filterIsInstance<UITabBarItem>()
        assertEquals(listOf("One", "Two"), originalItems.map { it.title })
        val delegate = assertIs<UITabBarDelegate>(bar.delegate)
        delegate.tabBar(bar, originalItems[0]) // Real production native entrypoint, not a touch injection.
        assertEquals(listOf(0), selections)
        assertEquals(0L, bar.selectedItem?.tag)
        manager.setItems(emptyList(), 0, 1f)
        assertTrue(bar.items.isNullOrEmpty())
        assertNull(bar.selectedItem)
        delegate.tabBar(bar, originalItems[1]) // Late callback cannot resurrect a cleared selection.
        assertNull(bar.selectedItem)
        assertEquals(listOf(0), selections)
        manager.setItems(items, -1, 1f)
        assertEquals(0L, bar.selectedItem?.tag)
        val repopulated = bar.items.orEmpty().filterIsInstance<UITabBarItem>()
        assertEquals(listOf("One", "Two"), repopulated.map { it.title })
        assertEquals(listOf(0), selections) // Programmatic setup never fabricates a callback.
        delegate.tabBar(bar, repopulated[1])
        assertEquals(listOf(0, 1), selections)
        assertEquals(1L, bar.selectedItem?.tag)
    }

    @Test fun selectionUsesCurrentNativeMembershipInsteadOfStaleOrMutableTags() = runNativeUiTest {
        val bar = UITabBar()
        val selections = mutableListOf<Int>()
        val manager = TabBarManager(bar) { selections += it }
        val items = listOf(UIKitUITabBarItem("One"), UIKitUITabBarItem("Two"))
        manager.setItems(items, 0, 1f)
        val oldItems = bar.items.orEmpty().filterIsInstance<UITabBarItem>()
        val delegate = assertIs<UITabBarDelegate>(bar.delegate)

        manager.setItems(items.reversed(), 99, 1f)
        val current = bar.items.orEmpty().filterIsInstance<UITabBarItem>()
        assertEquals(listOf("Two", "One"), current.map { it.title })
        assertEquals(1L, bar.selectedItem?.tag)
        delegate.tabBar(bar, oldItems[0])
        delegate.tabBar(bar, UITabBarItem("Foreign", null, 0))
        assertTrue(selections.isEmpty())
        assertEquals(1L, bar.selectedItem?.tag)

        current[0].tag = Long.MAX_VALUE
        delegate.tabBar(bar, current[0])
        assertEquals(listOf(0), selections) // Index derives from current native items, not a narrowing Long tag.
        assertEquals("Two", bar.selectedItem?.title)

        val foreignBar = UITabBar()
        delegate.tabBar(foreignBar, current[1])
        assertNull(foreignBar.selectedItem)
        assertEquals(listOf(0), selections)
        bar.delegate = UITabBarDelegate { selections += 99 }
        delegate.tabBar(bar, current[1]) // Replaced delegate cannot deliver an obsolete callback.
        assertEquals(listOf(0), selections)
        assertEquals("Two", bar.selectedItem?.title)
    }

    @Test fun barLivesInsideItsHostAndContinuesMeasuringAfterLayoutChanges() = runNativeUiTest {
        val bar = UINavigationBar()
        val host = NativeBarHost(bar)
        var callbacks = 0
        host.onMeasuredHeight = { callbacks++ }
        host.setFrame(CGRectMake(0.0, 0.0, 320.0, 44.0))
        host.layoutIfNeeded()
        assertSame(host, bar.superview)
        assertTrue(callbacks > 0)
        host.setFrame(CGRectMake(0.0, 0.0, 640.0, 44.0))
        host.invalidateMeasurement()
        host.layoutIfNeeded()
        assertSame(host, bar.superview)
        // This asserts persistent ownership/layout only, not a physical orientation/trait change.
    }
}
