// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class, kotlinx.cinterop.BetaInteropApi::class,
    com.mohamedrejeb.calf.core.InternalCalfApi::class)

package com.mohamedrejeb.calf.ui.dialog

import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.uikit.LocalUIViewController
import androidx.compose.ui.window.DialogProperties
import com.mohamedrejeb.calf.ui.dialog.uikit.*
import com.mohamedrejeb.calf.ui.internal.runApplicationUiTest
import com.mohamedrejeb.calf.ui.internal.sameNativeObject
import com.mohamedrejeb.calf.ui.internal.waitForNative
import kotlinx.cinterop.*
import platform.CoreGraphics.CGRect
import platform.CoreGraphics.CGRectMake
import platform.UIKit.*
import platform.darwin.NSObject
import kotlin.test.*

/** Real UIKit/library ownership tests; controlled bounds/delegate input is NOT OS rotation/split view. */
class NativePopoverAnchorTest {
    @Test fun publicCompositionAnchorUsesLocalRectAndUpdatesWithoutRebuilding() = runApplicationUiTest {
        lateinit var parent: UIViewController
        var visible by mutableStateOf(false)
        var anchor by mutableStateOf<AlertDialogIosPopoverAnchor?>(null)
        var dismissals = 0
        val properties = AlertDialogIosProperties(title = "Public anchor", animated = false,
            style = AlertDialogIosStyle.ActionSheet,
            actions = listOf(AlertDialogIosAction("Close", AlertDialogIosActionStyle.Default, {})))
        setContent {
            parent = LocalUIViewController.current
            if (visible) CompositionLocalProvider(LocalAlertDialogIosPopoverAnchor provides anchor) {
                AdaptiveBasicAlertDialog(onDismissRequest = { dismissals++ }, iosProperties = properties, materialContent = {})
            }
        }
        lateinit var source: UIView
        var sourceReady = false
        var popover: UIPopoverPresentationController? = null
        try {
            runOnIdle {
                source = UIView(frame = CGRectMake(30.0, 80.0, 120.0, 80.0))
                sourceReady = true
                parent.view.addSubview(source)
                anchor = AlertDialogIosPopoverAnchor.ViewRect(source, CGRectMake(10.0, 12.0, 20.0, 24.0))
                visible = true
            }
            waitForNative { parent.presentedViewController is UIAlertController }
            lateinit var original: UIAlertController
            runOnIdle {
                original = parent.presentedViewController as UIAlertController
                popover = requireNotNull(original.popoverPresentationController)
                assertTrue(sameNativeObject(source, popover?.sourceView))
                assertRect(requireNotNull(popover).sourceRect, 10.0, 12.0, 20.0, 24.0)
                assertNull(popover?.barButtonItem)
                anchor = AlertDialogIosPopoverAnchor.ViewRect(source, CGRectMake(40.0, 30.0, 25.0, 25.0))
            }
            waitForNative { popover?.sourceRect?.useContents { origin.x == 40.0 } == true }
            runOnIdle {
                assertTrue(sameNativeObject(original, parent.presentedViewController))
                assertRect(requireNotNull(popover).sourceRect, 40.0, 30.0, 25.0, 25.0)
                visible = false
            }
            waitForNative { parent.presentedViewController == null }
            runOnIdle {
                assertNull(popover?.sourceView); assertNull(popover?.barButtonItem); assertNull(popover?.delegate)
                assertEquals(0, dismissals)
            }
        } finally {
            runOnIdle { visible = false; anchor = null; if (sourceReady) source.removeFromSuperview() }
        }
    }

    @Test fun nativeBarButtonAndDetachedOrMissingViewUseTheDocumentedFallback() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        lateinit var toolbar: UIToolbar
        var toolbarReady = false
        lateinit var bar: UIBarButtonItem
        lateinit var manager: AlertDialogManager
        var managerReady = false
        try {
            runOnIdle {
                toolbar = UIToolbar(frame = CGRectMake(10.0, 90.0, 260.0, 50.0))
                toolbarReady = true
                bar = UIBarButtonItem(customView = UIButton(frame = CGRectMake(0.0, 0.0, 40.0, 40.0)))
                toolbar.setItems(listOf(bar), animated = false)
                parent.view.addSubview(toolbar)
                manager = manager(parent, "Bar anchor")
                managerReady = true
                manager.popoverAnchor = AlertDialogIosPopoverAnchor.BarButton(bar)
                manager.showAlertDialog()
            }
            waitForNative { parent.presentedViewController is UIAlertController }
            runOnIdle {
                val popover = requireNotNull((parent.presentedViewController as UIAlertController).popoverPresentationController)
                assertTrue(sameNativeObject(bar, popover.barButtonItem)); assertNull(popover.sourceView)
                toolbar.removeFromSuperview()
                manager.popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(bar.customView, CGRectMake(0.0, 0.0, 1.0, 1.0))
                manager.updateDialogProperties()
                assertTrue(sameNativeObject(parent.view, popover.sourceView)); assertNull(popover.barButtonItem)
                assertEquals(0uL, popover.permittedArrowDirections)
                manager.popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(null)
                manager.updateDialogProperties()
                assertTrue(sameNativeObject(parent.view, popover.sourceView))
                manager.popoverAnchor = AlertDialogIosPopoverAnchor.BarButton(null)
                manager.updateDialogProperties()
                assertTrue(sameNativeObject(parent.view, popover.sourceView)); assertNull(popover.barButtonItem)
            }
        } finally {
            runOnIdle {
                if (managerReady) manager.dispose()
                if (toolbarReady) toolbar.removeFromSuperview()
            }
        }
        waitForNative { parent.presentedViewController == null }
    }

    @Test fun queuedPresentationRefreshesBoundsAndDisposalReleasesOwnedAnchorReferences() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        lateinit var source: UIView
        var sourceReady = false
        lateinit var blocker: AlertDialogManager
        var blockerReady = false
        lateinit var queued: AlertDialogManager
        var queuedReady = false
        try {
            runOnIdle {
                source = UIView(frame = CGRectMake(10.0, 80.0, 100.0, 80.0)); sourceReady = true; parent.view.addSubview(source)
                blocker = AlertDialogManager(parent, {}, AlertDialogIosProperties(title = "Blocker", animated = false), DialogProperties())
                blockerReady = true
                blocker.showAlertDialog()
            }
            waitForNative { (parent.presentedViewController as? UIAlertController)?.title == "Blocker" }
            runOnIdle {
                queued = manager(parent, "Queued anchor")
                queuedReady = true
                queued.popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(source)
                queued.showAlertDialog()
                source.setBounds(CGRectMake(0.0, 0.0, 240.0, 120.0))
                blocker.dispose()
            }
            waitForNative { (parent.presentedViewController as? UIAlertController)?.title == "Queued anchor" }
            lateinit var popover: UIPopoverPresentationController
            runOnIdle {
                popover = requireNotNull((parent.presentedViewController as UIAlertController).popoverPresentationController)
                assertTrue(sameNativeObject(source, popover.sourceView))
                assertRect(popover.sourceRect, 0.0, 0.0, 240.0, 120.0)
                queued.dispose()
                assertNull(queued.popoverAnchor)
            }
            waitForNative { parent.presentedViewController == null }
            runOnIdle { assertNull(popover.sourceView); assertNull(popover.barButtonItem); assertNull(popover.delegate) }
        } finally {
            runOnIdle {
                if (blockerReady) blocker.dispose()
                if (queuedReady) queued.dispose()
                if (sourceReady) source.removeFromSuperview()
            }
        }
    }

    @Test fun controlledNativeRepositionWritesOnlyCompleteOwnedPointerPairs() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        lateinit var source: UIView
        var sourceReady = false
        lateinit var manager: AlertDialogManager
        var managerReady = false
        try {
            runOnIdle {
                source = UIView(frame = CGRectMake(10.0, 80.0, 120.0, 80.0)); sourceReady = true; parent.view.addSubview(source)
                manager = manager(parent, "Reposition anchor")
                managerReady = true
                manager.popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(source)
                manager.showAlertDialog()
            }
            waitForNative { parent.presentedViewController is UIAlertController }
            runOnIdle {
                val popover = requireNotNull((parent.presentedViewController as UIAlertController).popoverPresentationController)
                val delegate = requireNotNull(popover.delegate as? UIPopoverPresentationControllerDelegateProtocol)
                source.setBounds(CGRectMake(0.0, 0.0, 200.0, 100.0))
                memScoped {
                    val rect = alloc<CGRect>()
                    val view = alloc<ObjCObjectVar<UIView?>>()
                    rect.origin.x = -17.0; rect.origin.y = -19.0; rect.size.width = 2.0; rect.size.height = 3.0
                    view.value = parent.view
                    delegate.popoverPresentationController(popover, willRepositionPopoverToRect = rect.ptr, inView = null)
                    assertEquals(-17.0, rect.origin.x)
                    delegate.popoverPresentationController(popover, willRepositionPopoverToRect = null, inView = view.ptr)
                    assertTrue(sameNativeObject(parent.view, view.value))
                    delegate.popoverPresentationController(popover, willRepositionPopoverToRect = rect.ptr, inView = view.ptr)
                    assertTrue(sameNativeObject(source, view.value))
                    assertRect(rect.readValue(), 0.0, 0.0, 200.0, 100.0)
                    val foreign = requireNotNull(UIAlertController.alertControllerWithTitle("Foreign", null,
                        UIAlertControllerStyleActionSheet).popoverPresentationController)
                    rect.origin.x = -17.0; view.value = parent.view
                    delegate.popoverPresentationController(foreign, willRepositionPopoverToRect = rect.ptr, inView = view.ptr)
                    assertEquals(-17.0, rect.origin.x); assertTrue(sameNativeObject(parent.view, view.value))
                    assertNull(foreign.delegate)
                }
                // Controlled callback delivery above does not prove an OS orientation event.
                assertRect(popover.sourceRect, 0.0, 0.0, 200.0, 100.0)
            }
        } finally {
            runOnIdle { if (managerReady) manager.dispose(); if (sourceReady) source.removeFromSuperview() }
        }
        waitForNative { parent.presentedViewController == null }
    }

    @Test fun invalidRectanglesAreRejectedBeforeUIKitAndAlertDelegationIsUnchanged() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        lateinit var source: UIView
        var sourceReady = false
        lateinit var manager: AlertDialogManager
        var managerReady = false
        try {
            runOnIdle {
                source = UIView(frame = CGRectMake(10.0, 80.0, 120.0, 80.0)); sourceReady = true; parent.view.addSubview(source)
                manager = manager(parent, "Finite anchor")
                managerReady = true
                manager.showAlertDialog()
            }
            waitForNative { parent.presentedViewController is UIAlertController }
            runOnIdle {
                val popover = requireNotNull((parent.presentedViewController as UIAlertController).popoverPresentationController)
                for (rect in listOf(CGRectMake(Double.NaN, 0.0, 1.0, 1.0), CGRectMake(0.0, 0.0, Double.POSITIVE_INFINITY, 1.0),
                    CGRectMake(-1.0, 0.0, 1.0, 1.0), CGRectMake(0.0, 0.0, -2.0, 1.0), CGRectMake(100.0, 0.0, 30.0, 1.0))) {
                    manager.popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(source, rect)
                    manager.updateDialogProperties()
                    assertTrue(sameNativeObject(parent.view, popover.sourceView))
                    popover.sourceRect.useContents {
                        assertTrue(origin.x.isFinite() && origin.y.isFinite() && size.width.isFinite() && size.height.isFinite())
                    }
                }
                assertFailsWith<IllegalArgumentException> { AlertDialogIosPopoverAnchor.ViewRect(source, permittedArrowDirections = 16u) }
                manager.dispose()
            }
            waitForNative { parent.presentedViewController == null }
            runOnIdle {
                manager = AlertDialogManager(parent, {}, AlertDialogIosProperties(title = "UIKit alert", animated = false), DialogProperties())
                manager.popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(source)
                manager.showAlertDialog()
            }
            waitForNative { (parent.presentedViewController as? UIAlertController)?.title == "UIKit alert" }
            runOnIdle {
                val alert = parent.presentedViewController as UIAlertController
                val original = alert.presentationController?.delegate as? NSObject
                manager.popoverAnchor = AlertDialogIosPopoverAnchor.BarButton(null)
                manager.updateDialogProperties()
                val after = alert.presentationController?.delegate as? NSObject
                if (original == null) assertNull(after) else assertTrue(sameNativeObject(original, after))
                assertEquals(UIAlertControllerStyleAlert, alert.preferredStyle)
            }
        } finally {
            runOnIdle { if (managerReady) manager.dispose(); if (sourceReady) source.removeFromSuperview() }
        }
        waitForNative { parent.presentedViewController == null }
    }

    private fun manager(parent: UIViewController, title: String) = AlertDialogManager(parent, {},
        AlertDialogIosProperties(title = title, animated = false, style = AlertDialogIosStyle.ActionSheet,
            actions = listOf(AlertDialogIosAction("Close", AlertDialogIosActionStyle.Default, {}))), DialogProperties())

    private fun assertRect(rect: CValue<CGRect>, x: Double, y: Double, width: Double, height: Double) = rect.useContents {
        assertEquals(x, origin.x, 0.001); assertEquals(y, origin.y, 0.001)
        assertEquals(width, size.width, 0.001); assertEquals(height, size.height, 0.001)
    }
}
