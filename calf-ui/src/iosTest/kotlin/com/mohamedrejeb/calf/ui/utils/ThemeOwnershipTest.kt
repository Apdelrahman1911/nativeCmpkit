@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.utils

import com.mohamedrejeb.calf.ui.internal.runNativeUiTest
import platform.CoreGraphics.CGRectMake
import platform.UIKit.UIUserInterfaceStyle
import platform.UIKit.UIView
import platform.UIKit.UIViewController
import platform.UIKit.addChildViewController
import platform.UIKit.didMoveToParentViewController
import platform.UIKit.removeFromParentViewController
import platform.UIKit.willMoveToParentViewController
import kotlin.test.Test
import kotlin.test.assertEquals

class ThemeOwnershipTest {
    @Test fun siblingNativeControlsCanHaveOppositeThemesWithoutChangingTheirParent() = runNativeUiTest {
        val parent = UIView(frame = CGRectMake(0.0, 0.0, 320.0, 480.0))
        val first = UIView(frame = CGRectMake(0.0, 0.0, 160.0, 40.0))
        val second = UIView(frame = CGRectMake(160.0, 0.0, 160.0, 40.0))
        parent.addSubview(first)
        parent.addSubview(second)
        first.applyTheme(dark = true)
        second.applyTheme(dark = false)
        assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleUnspecified, parent.overrideUserInterfaceStyle)
        assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleDark, first.overrideUserInterfaceStyle)
        assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleLight, second.overrideUserInterfaceStyle)
        first.applyTheme(dark = false)
        second.removeFromSuperview()
        assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleUnspecified, parent.overrideUserInterfaceStyle)
        assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleLight, first.overrideUserInterfaceStyle)
    }

    @Test fun explicitParentStyleSurvivesChildUpdatesAndRemoval() = runNativeUiTest {
        val parent = UIView(frame = CGRectMake(0.0, 0.0, 320.0, 480.0))
        val child = UIView(frame = CGRectMake(0.0, 0.0, 320.0, 40.0))
        parent.overrideUserInterfaceStyle = UIUserInterfaceStyle.UIUserInterfaceStyleLight
        parent.addSubview(child)
        child.applyTheme(dark = true)
        assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleLight, parent.overrideUserInterfaceStyle)
        child.removeFromSuperview()
        assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleLight, parent.overrideUserInterfaceStyle)
        assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleDark, child.overrideUserInterfaceStyle)
    }

    @Test fun controllerStylingIsExplicitAndDoesNotMutateItsParentController() = runNativeUiTest {
        val parent = UIViewController()
        val child = UIViewController()
        parent.addChildViewController(child)
        parent.view.addSubview(child.view)
        child.didMoveToParentViewController(parent)
        child.applyTheme(dark = true)
        assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleUnspecified, parent.overrideUserInterfaceStyle)
        assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleDark, child.overrideUserInterfaceStyle)
        child.willMoveToParentViewController(null)
        child.view.removeFromSuperview()
        child.removeFromParentViewController()
        assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleUnspecified, parent.overrideUserInterfaceStyle)
    }
}
