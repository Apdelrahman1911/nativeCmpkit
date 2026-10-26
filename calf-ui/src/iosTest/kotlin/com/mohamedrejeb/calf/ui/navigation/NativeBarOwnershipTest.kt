@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.navigation

import com.mohamedrejeb.calf.ui.internal.runNativeUiTest
import platform.CoreGraphics.CGRectMake
import platform.UIKit.*
import kotlin.test.*

class NativeBarOwnershipTest {
    @Test fun emptyTabsClearSelectionAndRepopulationClampsIndex() = runNativeUiTest {
        val bar = UITabBar()
        var clicks = 0
        val manager = TabBarManager(bar) { clicks++ }
        val items = listOf(UIKitUITabBarItem("One"), UIKitUITabBarItem("Two"))
        manager.setItems(items, 99, 1f)
        assertEquals(1L, bar.selectedItem?.tag)
        manager.setItems(emptyList(), 0, 1f)
        assertTrue(bar.items.isNullOrEmpty())
        assertNull(bar.selectedItem)
        manager.setItems(items, -1, 1f)
        assertEquals(0L, bar.selectedItem?.tag)
        assertEquals(0, clicks)
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
