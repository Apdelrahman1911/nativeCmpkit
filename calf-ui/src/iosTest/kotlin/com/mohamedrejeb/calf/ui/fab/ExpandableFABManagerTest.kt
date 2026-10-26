@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.fab

import androidx.compose.ui.unit.LayoutDirection
import com.mohamedrejeb.calf.ui.internal.runNativeUiTest
import kotlinx.cinterop.useContents
import platform.CoreGraphics.CGPointMake
import platform.CoreGraphics.CGRectMake
import platform.UIKit.UIAccessibilityTraitButton
import platform.UIKit.UIAccessibilityTraitSelected
import platform.UIKit.UIButton
import platform.UIKit.UIControlEventTouchUpInside
import platform.UIKit.UIView
import platform.UIKit.accessibilityElementsHidden
import platform.UIKit.accessibilityLabel
import platform.UIKit.accessibilityTraits
import platform.UIKit.isAccessibilityElement
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

/** Exercises the internal manager with actual UIButton targets, hierarchy, layout and hit testing. */
class ExpandableFABManagerTest {
    @Test fun rebuildingExpandedOrCollapsedItemsReappliesTheCurrentAppearance() = runNativeUiTest {
        val parent = parent()
        val manager = ExpandableFABManager({}, {})
        manager.attachTo(parent)
        manager.updateItems(item("Main"), listOf(item("First")), 1f)
        UIView.performWithoutAnimation { manager.setExpanded(true) }
        manager.updateItems(item("Changed main"), listOf(item("Second"), item("Third")), 2f)
        val overlay = parent.overlay()
        val buttons = overlay.buttons()
        assertEquals(3, buttons.size)
        assertEquals(listOf("Second", "Third", "Changed main"), buttons.map { it.accessibilityLabel })
        buttons.dropLast(1).forEach {
            assertEquals(1.0, it.alpha)
            assertTrue(it.userInteractionEnabled)
            assertFalse(it.accessibilityElementsHidden)
            assertEquals(1.0, it.transform.useContents { a })
            assertEquals(1.0, it.transform.useContents { d })
        }
        assertTrue(buttons.last().accessibilityTraits and UIAccessibilityTraitSelected != 0uL)
        UIView.performWithoutAnimation { manager.setExpanded(false) }
        manager.updateItems(item("Collapsed"), listOf(item("New")), 3f)
        val collapsed = overlay.buttons().first()
        assertEquals(0.0, collapsed.alpha)
        assertFalse(collapsed.userInteractionEnabled)
        assertTrue(collapsed.accessibilityElementsHidden)
        manager.updateItems(item("Empty"), emptyList(), 1f)
        assertEquals(listOf("Empty"), overlay.buttons().map { it.accessibilityLabel })
        manager.detach()
        assertTrue(parent.subviews.isEmpty())
    }

    @Test fun emptyOverlayAreaPassesThroughButVisibleButtonsRemainHittable() = runNativeUiTest {
        val parent = parent()
        val behind = UIView(frame = parent.bounds)
        parent.addSubview(behind)
        val manager = ExpandableFABManager({}, {})
        manager.attachTo(parent)
        manager.updateItems(item("Main"), listOf(item("Child")), 1f)
        val overlay = parent.overlay()
        val main = overlay.buttons().last()
        val child = overlay.buttons().first()
        val emptyPoint = CGPointMake(2.0, 2.0)
        assertNull(overlay.hitTest(emptyPoint, null))
        assertSame(behind, parent.hitTest(emptyPoint, null))
        assertTrue(assertNotNull(overlay.hitTest(main.center, null)).isDescendantOfView(main))
        assertNull(overlay.hitTest(child.center, null))
        UIView.performWithoutAnimation { manager.setExpanded(true) }
        assertTrue(assertNotNull(overlay.hitTest(child.center, null)).isDescendantOfView(child))
        manager.detach()
        assertNull(overlay.onLayout)
    }

    @Test fun actualButtonActionsUseLatestItemsAndIgnoreCollapsedOrDetachedButtons() = runNativeUiTest {
        val expanded = mutableListOf<Boolean>()
        val selected = mutableListOf<Int>()
        val parent = parent()
        val manager = ExpandableFABManager(expanded::add, selected::add)
        manager.attachTo(parent)
        manager.updateItems(item("Open actions"), listOf(item("Archive")), 1f)
        val overlay = parent.overlay()
        val oldButtons = overlay.buttons()
        oldButtons.last().sendActionsForControlEvents(UIControlEventTouchUpInside)
        assertEquals(listOf(true), expanded)
        oldButtons.first().sendActionsForControlEvents(UIControlEventTouchUpInside)
        assertTrue(selected.isEmpty())
        UIView.performWithoutAnimation { manager.setExpanded(true) }
        manager.updateItems(item("New actions"), listOf(item("Copy"), item("Move")), 1f)
        val current = overlay.buttons()
        current.forEach {
            assertTrue(it.isAccessibilityElement)
            assertTrue(it.accessibilityTraits and UIAccessibilityTraitButton != 0uL)
        }
        oldButtons.first().sendActionsForControlEvents(UIControlEventTouchUpInside)
        assertTrue(selected.isEmpty())
        current[1].sendActionsForControlEvents(UIControlEventTouchUpInside)
        assertEquals(listOf(1), selected)
        assertEquals(listOf(true, false), expanded)
        manager.detach()
        current.last().sendActionsForControlEvents(UIControlEventTouchUpInside)
        current.first().sendActionsForControlEvents(UIControlEventTouchUpInside)
        assertEquals(listOf(1), selected)
        assertEquals(listOf(true, false), expanded)
    }

    @Test fun placementUsesParentBoundsAndTrailingDirectionRatherThanFixedScreenGeometry() = runNativeUiTest {
        val parent = parent()
        val manager = ExpandableFABManager({}, {})
        manager.attachTo(parent)
        manager.updateItems(item("Main"), listOf(item("Child")), 1f)
        val overlay = parent.overlay()
        val main = overlay.buttons().last()
        assertEquals(334.0, main.frame.useContents { origin.x })
        assertEquals(734.0, main.frame.useContents { origin.y })
        manager.applyLayoutDirection(LayoutDirection.Rtl)
        assertEquals(16.0, main.frame.useContents { origin.x })
        parent.setFrame(CGRectMake(0.0, 0.0, 600.0, 500.0))
        parent.layoutIfNeeded()
        overlay.layoutIfNeeded()
        assertEquals(600.0, overlay.bounds.useContents { size.width })
        assertEquals(500.0, overlay.bounds.useContents { size.height })
        assertEquals(434.0, main.frame.useContents { origin.y })
        manager.applyLayoutDirection(LayoutDirection.Ltr)
        assertEquals(534.0, main.frame.useContents { origin.x })
        manager.detach()
        val replacementParent = parent()
        manager.attachTo(replacementParent)
        manager.updateItems(item("Reattached"), emptyList(), 1f)
        assertEquals("Reattached", replacementParent.overlay().buttons().single().accessibilityLabel)
        assertTrue(parent.subviews.isEmpty())
        manager.detach()
    }

    private fun item(title: String) = UIKitExpandableFABItem(title)
    private fun parent() = UIView(frame = CGRectMake(0.0, 0.0, 400.0, 800.0))
    private fun UIView.overlay() = subviews.filterIsInstance<FABContainerView>().single()
    private fun FABContainerView.buttons() = subviews.filterIsInstance<UIButton>()
}
