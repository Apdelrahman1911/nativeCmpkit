// Modified for NativeCmpKit (2026-11-08): real UIKit geometry tests for UI-013 action-sheet anchors.
@file:OptIn(
    kotlinx.cinterop.ExperimentalForeignApi::class,
    kotlinx.cinterop.BetaInteropApi::class,
    com.mohamedrejeb.calf.core.InternalCalfApi::class,
)

package com.mohamedrejeb.calf.ui.dialog

import androidx.compose.ui.window.DialogProperties
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosAction
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosActionStyle
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosPopoverAnchor
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosProperties
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosStyle
import kotlinx.cinterop.*
import platform.CoreGraphics.CGRect
import platform.CoreGraphics.CGRectMake
import platform.Foundation.NSThread
import platform.UIKit.UIAlertController
import platform.UIKit.UIAlertControllerStyleActionSheet
import platform.UIKit.UIAlertControllerStyleAlert
import platform.UIKit.UIBarButtonSystemItem.UIBarButtonSystemItemDone
import platform.UIKit.UIPresentationController
import platform.UIKit.UIBarButtonItem
import platform.UIKit.UIButton
import platform.UIKit.UIPopoverArrowDirectionAny
import platform.UIKit.UIPopoverPresentationController
import platform.UIKit.UIPopoverPresentationControllerDelegateProtocol
import platform.UIKit.UIToolbar
import platform.UIKit.UIView
import platform.UIKit.UIViewController
import platform.UIKit.UIWindow
import platform.UIKit.modalInPresentation
import platform.darwin.NSObject
import kotlin.math.abs
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertFailsWith
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

/**
 * Real UIKit/library anchor-geometry tests for UI-013.
 *
 * These construct genuine `UIWindow`, `UIView`, `UIBarButtonItem`, `UIAlertController` and
 * `UIPopoverPresentationController` objects and exercise the exact anchor-resolution and
 * reposition code paths through explicitly constructed presentation controllers on either
 * compact or regular-width test hosts. The window has a root controller but no application
 * window scene. They do not present an alert, so an iOS test host still requires the
 * manual iPad/iPhone exercise in `docs/testing/ios-action-sheet-anchor.md`. In particular, a
 * directly invoked reposition callback is not an operating-system rotation, split-view or
 * physical-device result.
 */
class NativePopoverAnchorGeometryTest {

    @Test
    fun viewRectAnchorUsesFiniteLocalGeometryAndTracksUpdatedRectangles() = onMain {
        withFixture { fixture ->
            val source = UIView(frame = CGRectMake(20.0, 30.0, 120.0, 80.0))
            fixture.parent.view.addSubview(source)
            fixture.window.layoutIfNeeded()

            val manager = actionSheetManager(fixture.parent)
            manager.popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(source)
            val popover = manager.configureControlledPopover(fixture.parent)

            assertTrue(sameNativeObject(source, popover.sourceView))
            assertRect(popover.sourceRect, 0.0, 0.0, 120.0, 80.0)
            assertNull(popover.barButtonItem)
            assertEquals(UIPopoverArrowDirectionAny, popover.permittedArrowDirections)
            assertNotNull(popover.delegate)

            manager.popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(
                sourceView = source,
                sourceRect = CGRectMake(10.0, 12.0, 20.0, 24.0),
            )
            manager.updateDialogProperties()

            assertTrue(sameNativeObject(source, popover.sourceView))
            assertRect(popover.sourceRect, 10.0, 12.0, 20.0, 24.0)
            assertNull(popover.barButtonItem)
            assertEquals(UIPopoverArrowDirectionAny, popover.permittedArrowDirections)
        }
    }

    @Test
    fun barButtonAnchorAndDetachedOrMissingSourcesUseTheDocumentedFallback() = onMain {
        withFixture { fixture ->
            val toolbar = UIToolbar(frame = CGRectMake(10.0, 90.0, 260.0, 50.0))
            val customView = UIButton(frame = CGRectMake(0.0, 0.0, 40.0, 40.0))
            val barButton = UIBarButtonItem(customView = customView)
            toolbar.setItems(listOf(barButton), animated = false)
            fixture.parent.view.addSubview(toolbar)
            fixture.window.layoutIfNeeded()

            val manager = actionSheetManager(fixture.parent)
            manager.popoverAnchor = AlertDialogIosPopoverAnchor.BarButton(barButton)
            val popover = manager.configureControlledPopover(fixture.parent)

            assertTrue(sameNativeObject(barButton, popover.barButtonItem))
            assertNull(popover.sourceView)
            assertEquals(UIPopoverArrowDirectionAny, popover.permittedArrowDirections)

            toolbar.removeFromSuperview()
            manager.popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(
                sourceView = customView,
                sourceRect = CGRectMake(0.0, 0.0, 1.0, 1.0),
            )
            manager.updateDialogProperties()

            assertTrue(sameNativeObject(fixture.parent.view, popover.sourceView))
            assertNull(popover.barButtonItem)
            assertEquals(0uL, popover.permittedArrowDirections)
            assertFallbackCenter(popover, fixture.parent.view)

            manager.popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(null)
            manager.updateDialogProperties()
            assertTrue(sameNativeObject(fixture.parent.view, popover.sourceView))

            manager.popoverAnchor = AlertDialogIosPopoverAnchor.BarButton(null)
            manager.updateDialogProperties()
            assertTrue(sameNativeObject(fixture.parent.view, popover.sourceView))
            assertNull(popover.barButtonItem)
        }
    }

    @Test
    fun invalidBoundedOrDetachedGeometryIsRejectedBeforeUIKit() = onMain {
        withFixture { fixture ->
            val source = UIView(frame = CGRectMake(10.0, 80.0, 120.0, 80.0))
            fixture.parent.view.addSubview(source)
            fixture.window.layoutIfNeeded()

            val manager = actionSheetManager(fixture.parent)
            val popover = manager.configureControlledPopover(fixture.parent)

            // Existing callers that never provide the new local still get a safe,
            // finite anchor instead of an anchorless regular-width action sheet.
            assertTrue(sameNativeObject(fixture.parent.view, popover.sourceView))
            assertNull(popover.barButtonItem)
            assertEquals(0uL, popover.permittedArrowDirections)
            assertFallbackCenter(popover, fixture.parent.view)

            val invalidRectangles = listOf(
                CGRectMake(Double.NaN, 0.0, 1.0, 1.0),
                CGRectMake(0.0, Double.POSITIVE_INFINITY, 1.0, 1.0),
                CGRectMake(-1.0, 0.0, 1.0, 1.0),
                CGRectMake(0.0, 0.0, -2.0, 1.0),
                CGRectMake(0.0, 0.0, 0.0, 1.0),
                CGRectMake(100.0, 0.0, 30.0, 1.0),
            )
            for (rect in invalidRectangles) {
                manager.popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(source, rect)
                manager.updateDialogProperties()

                assertTrue(sameNativeObject(fixture.parent.view, popover.sourceView), "rect=$rect")
                assertNull(popover.barButtonItem)
                assertEquals(0uL, popover.permittedArrowDirections)
                assertFallbackCenter(popover, fixture.parent.view)
            }

            source.removeFromSuperview()
            manager.popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(source)
            manager.updateDialogProperties()
            assertTrue(sameNativeObject(fixture.parent.view, popover.sourceView))
            assertFallbackCenter(popover, fixture.parent.view)

            assertFailsWith<IllegalArgumentException> {
                AlertDialogIosPopoverAnchor.ViewRect(
                    sourceView = source,
                    permittedArrowDirections = 16uL,
                )
            }
            assertFailsWith<IllegalArgumentException> {
                AlertDialogIosPopoverAnchor.BarButton(
                    barButtonItem = null,
                    permittedArrowDirections = 16uL,
                )
            }
        }
    }

    @Test
    fun prepareRevalidatesChangedBoundsAndDetachedSourcesBeforePresentation() = onMain {
        withFixture { fixture ->
            val source = UIView(frame = CGRectMake(10.0, 80.0, 120.0, 80.0))
            fixture.parent.view.addSubview(source)
            fixture.window.layoutIfNeeded()
            val manager = actionSheetManager(fixture.parent)
            manager.popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(source)
            val popover = manager.configureControlledPopover(fixture.parent)
            val delegate = assertNotNull(
                popover.delegate as? UIPopoverPresentationControllerDelegateProtocol
            )

            source.setBounds(CGRectMake(4.0, 8.0, 240.0, 120.0))
            delegate.prepareForPopoverPresentation(popover)

            assertTrue(sameNativeObject(source, popover.sourceView))
            assertRect(popover.sourceRect, 4.0, 8.0, 240.0, 120.0)

            source.removeFromSuperview()
            fixture.parent.view.setBounds(CGRectMake(2.0, 4.0, 480.0, 320.0))
            delegate.prepareForPopoverPresentation(popover)

            assertTrue(sameNativeObject(fixture.parent.view, popover.sourceView))
            assertNull(popover.barButtonItem)
            assertEquals(0uL, popover.permittedArrowDirections)
            assertRect(popover.sourceRect, 242.0, 164.0, 1.0, 1.0)
        }
    }

    @Test
    fun prepareIgnoresForeignPopoversWithoutChangingEitherAnchor() = onMain {
        withFixture { fixture ->
            val manager = actionSheetManager(fixture.parent)
            val popover = manager.configureControlledPopover(fixture.parent)
            val delegate = assertNotNull(
                popover.delegate as? UIPopoverPresentationControllerDelegateProtocol
            )
            val originalRect = popover.sourceRect
            val foreignController = UIAlertController.alertControllerWithTitle(
                title = "Foreign",
                message = null,
                preferredStyle = UIAlertControllerStyleActionSheet,
            )
            val foreignPopover = UIPopoverPresentationController(foreignController, fixture.parent)
            foreignPopover.sourceView = fixture.parent.view
            foreignPopover.sourceRect = CGRectMake(7.0, 9.0, 11.0, 13.0)
            fixture.parent.view.setBounds(CGRectMake(0.0, 0.0, 400.0, 300.0))

            delegate.prepareForPopoverPresentation(foreignPopover)

            originalRect.useContents {
                assertRect(popover.sourceRect, origin.x, origin.y, size.width, size.height)
            }
            assertTrue(sameNativeObject(fixture.parent.view, popover.sourceView))
            assertRect(foreignPopover.sourceRect, 7.0, 9.0, 11.0, 13.0)
            assertNull(foreignPopover.delegate)
        }
    }

    @Test
    fun foreignWindowSourceUsesTheCurrentPresentersFallback() = onMain {
        withFixture { fixture ->
            withFixture { foreign ->
                val source = UIView(frame = CGRectMake(10.0, 20.0, 30.0, 40.0))
                foreign.parent.view.addSubview(source)
                foreign.window.layoutIfNeeded()
                assertTrue(sameNativeObject(foreign.window, source.window))
                val manager = actionSheetManager(fixture.parent)
                manager.popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(source)

                val popover = manager.configureControlledPopover(fixture.parent)

                assertTrue(sameNativeObject(fixture.parent.view, popover.sourceView))
                assertNull(popover.barButtonItem)
                assertEquals(0uL, popover.permittedArrowDirections)
                assertFallbackCenter(popover, fixture.parent.view)
            }
        }
    }

    @Test
    fun controlledRepositionWritesOnlyCompleteOwnedPointerPairs() = onMain {
        withFixture { fixture ->
            val source = UIView(frame = CGRectMake(10.0, 80.0, 120.0, 80.0))
            fixture.parent.view.addSubview(source)
            fixture.window.layoutIfNeeded()

            val manager = actionSheetManager(fixture.parent)
            manager.popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(source)
            val popover = manager.configureControlledPopover(fixture.parent)
            val delegate = assertNotNull(
                popover.delegate as? UIPopoverPresentationControllerDelegateProtocol
            )

            source.setBounds(CGRectMake(0.0, 0.0, 240.0, 120.0))

            memScoped {
                val rect = alloc<CGRect>()
                val inView = alloc<ObjCObjectVar<UIView?>>()
                rect.origin.x = -17.0
                rect.origin.y = -19.0
                rect.size.width = 2.0
                rect.size.height = 3.0
                inView.value = fixture.parent.view

                delegate.popoverPresentationController(
                    popoverPresentationController = popover,
                    willRepositionPopoverToRect = rect.ptr,
                    inView = inView.ptr,
                )

                assertRect(rect.readValue(), 0.0, 0.0, 240.0, 120.0)
                assertTrue(sameNativeObject(source, inView.value))
                assertRect(popover.sourceRect, 0.0, 0.0, 240.0, 120.0)
                assertTrue(sameNativeObject(source, popover.sourceView))

                rect.origin.x = -17.0
                inView.value = fixture.parent.view
                delegate.popoverPresentationController(
                    popoverPresentationController = popover,
                    willRepositionPopoverToRect = null,
                    inView = inView.ptr,
                )
                assertEquals(-17.0, rect.origin.x)
                assertTrue(sameNativeObject(fixture.parent.view, inView.value))

                delegate.popoverPresentationController(
                    popoverPresentationController = popover,
                    willRepositionPopoverToRect = rect.ptr,
                    inView = null,
                )
                assertEquals(-17.0, rect.origin.x)

                val foreign = UIAlertController.alertControllerWithTitle(
                    title = "Foreign",
                    message = null,
                    preferredStyle = UIAlertControllerStyleActionSheet,
                )
                val foreignPopover = UIPopoverPresentationController(foreign, fixture.parent)
                rect.origin.x = -17.0
                inView.value = fixture.parent.view
                delegate.popoverPresentationController(
                    popoverPresentationController = foreignPopover,
                    willRepositionPopoverToRect = rect.ptr,
                    inView = inView.ptr,
                )
                assertEquals(-17.0, rect.origin.x)
                assertTrue(sameNativeObject(fixture.parent.view, inView.value))
                assertNull(foreignPopover.delegate)
            }
        }
    }

    @Test
    fun defaultFallbackRecentersAfterPresenterBoundsChange() = onMain {
        withFixture { fixture ->
            val manager = actionSheetManager(fixture.parent)
            val popover = manager.configureControlledPopover(fixture.parent)
            val delegate = assertNotNull(
                popover.delegate as? UIPopoverPresentationControllerDelegateProtocol
            )

            fixture.parent.view.setBounds(CGRectMake(0.0, 0.0, 400.0, 300.0))

            memScoped {
                val rect = alloc<CGRect>()
                val inView = alloc<ObjCObjectVar<UIView?>>()
                rect.origin.x = -17.0
                rect.origin.y = -19.0
                rect.size.width = 2.0
                rect.size.height = 3.0
                inView.value = fixture.parent.view

                delegate.popoverPresentationController(
                    popoverPresentationController = popover,
                    willRepositionPopoverToRect = rect.ptr,
                    inView = inView.ptr,
                )

                assertRect(rect.readValue(), 200.0, 150.0, 1.0, 1.0)
                assertTrue(sameNativeObject(fixture.parent.view, inView.value))
                assertTrue(sameNativeObject(fixture.parent.view, popover.sourceView))
                assertNull(popover.barButtonItem)
                assertEquals(0uL, popover.permittedArrowDirections)
            }
        }
    }

    @Test
    fun barButtonRepositionDoesNotFabricatePrivateViewGeometry() = onMain {
        withFixture { fixture ->
            val toolbar = UIToolbar(frame = CGRectMake(10.0, 90.0, 260.0, 50.0))
            val barButton = UIBarButtonItem(customView = UIButton(frame = CGRectMake(0.0, 0.0, 40.0, 40.0)))
            toolbar.setItems(listOf(barButton), animated = false)
            fixture.parent.view.addSubview(toolbar)
            fixture.window.layoutIfNeeded()

            val manager = actionSheetManager(fixture.parent)
            manager.popoverAnchor = AlertDialogIosPopoverAnchor.BarButton(barButton)
            val popover = manager.configureControlledPopover(fixture.parent)
            val delegate = assertNotNull(
                popover.delegate as? UIPopoverPresentationControllerDelegateProtocol
            )

            memScoped {
                val rect = alloc<CGRect>()
                val inView = alloc<ObjCObjectVar<UIView?>>()
                rect.origin.x = -17.0
                rect.origin.y = -19.0
                rect.size.width = 2.0
                rect.size.height = 3.0
                inView.value = fixture.parent.view

                delegate.popoverPresentationController(
                    popoverPresentationController = popover,
                    willRepositionPopoverToRect = rect.ptr,
                    inView = inView.ptr,
                )

                assertEquals(-17.0, rect.origin.x)
                assertEquals(-19.0, rect.origin.y)
                assertEquals(2.0, rect.size.width)
                assertEquals(3.0, rect.size.height)
                assertTrue(sameNativeObject(fixture.parent.view, inView.value))
                assertTrue(sameNativeObject(barButton, popover.barButtonItem))
                assertNull(popover.sourceView)
            }
        }
    }

    @Test
    fun alertStyleNeverAssignsTheOwnedPopoverDelegate() = onMain {
        withFixture { fixture ->
            val manager = AlertDialogManager(
                parentUIViewController = fixture.parent,
                onDismissRequest = {},
                iosProperties = AlertDialogIosProperties(
                    title = "UIKit alert",
                    animated = false,
                    style = AlertDialogIosStyle.Alert,
                    actions = listOf(
                        AlertDialogIosAction(
                            title = "OK",
                            style = AlertDialogIosActionStyle.Default,
                            onClick = {},
                        )
                    ),
                ),
                properties = DialogProperties(),
            )
            manager.popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(fixture.parent.view)
            val alert = manager.dialogUIViewController as UIAlertController
            val controlledPopover = UIPopoverPresentationController(alert, fixture.parent)
            manager.configurePopoverPresentation(controlledPopover)
            manager.configureActionSheetDismissal(controlledPopover)
            assertEquals(UIAlertControllerStyleAlert, alert.preferredStyle)
            assertNull(controlledPopover.delegate)
            assertNull(controlledPopover.sourceView)
            assertNull(controlledPopover.barButtonItem)
        }
    }

    @Test
    fun installedSystemBarButtonUsesThePublicItemWithoutInventingAView() = onMain {
        withFixture { fixture ->
            val toolbar = UIToolbar(frame = CGRectMake(0.0, 0.0, 300.0, 44.0))
            val item = UIBarButtonItem(UIBarButtonSystemItemDone, target = null, action = null)
            toolbar.setItems(listOf(item), animated = false)
            fixture.parent.view.addSubview(toolbar)
            fixture.window.layoutIfNeeded()
            val manager = actionSheetManager(fixture.parent)
            manager.popoverAnchor = AlertDialogIosPopoverAnchor.BarButton(item)
            val popover = manager.configureControlledPopover(fixture.parent)
            assertTrue(sameNativeObject(item, popover.barButtonItem))
            assertNull(popover.sourceView)
            // Setup installs the item; the resolver cannot verify that through UIKit.
        }
    }

    @Test
    fun compactPresentationDelegateTracksOutsideDismissalPolicy() = onMain {
        withFixture { fixture ->
            val manager = actionSheetManager(fixture.parent)
            val presentation = UIPresentationController(manager.dialogUIViewController, fixture.parent)
            manager.properties = DialogProperties(dismissOnClickOutside = false)
            manager.configureActionSheetDismissal(presentation)
            manager.presentationCompleted(presentation)
            val delegate = assertNotNull(presentation.delegate)
            assertFalse(delegate.presentationControllerShouldDismiss(presentation))
            assertTrue(manager.dialogUIViewController.modalInPresentation)
            manager.properties = DialogProperties(dismissOnClickOutside = true)
            manager.configureActionSheetDismissal(presentation)
            assertTrue(delegate.presentationControllerShouldDismiss(presentation))
            assertFalse(manager.dialogUIViewController.modalInPresentation)
        }
    }

    @Test
    fun controlledNativeDismissalNotifiesOnceAndReleasesOwnedAnchors() = onMain {
        withFixture { fixture ->
            var dismissals = 0
            val manager = actionSheetManager(fixture.parent)
            manager.onDismissRequest = { dismissals++ }
            val popover = manager.configureControlledPopover(fixture.parent)
            manager.presentationCompleted(popover)
            val delegate = assertNotNull(popover.delegate as? UIPopoverPresentationControllerDelegateProtocol)
            delegate.popoverPresentationControllerDidDismissPopover(popover)
            delegate.presentationControllerDidDismiss(popover)
            manager.dismissalCompleted()
            assertEquals(1, dismissals)
            assertNull(popover.delegate)
            assertNull(popover.sourceView)
            assertNull(popover.barButtonItem)
        }
    }

    @Test
    fun chosenActionSheetActionDoesNotEmitAnAdditionalDismissCallback() = onMain {
        withFixture { fixture ->
            var actions = 0
            var dismissals = 0
            val manager = actionSheetManager(fixture.parent)
            manager.onDismissRequest = { dismissals++ }
            val presentation = assertNotNull(manager.dialogUIViewController.presentationController)
            manager.properties = DialogProperties(dismissOnClickOutside = false)
            manager.presentationCompleted(presentation)
            val delegate = assertNotNull(presentation.delegate)
            assertFalse(delegate.presentationControllerShouldDismiss(presentation))
            assertTrue(manager.dialogUIViewController.modalInPresentation)
            manager.actionInvoked(
                AlertDialogIosAction(
                    title = "Confirm",
                    style = AlertDialogIosActionStyle.Default,
                    onClick = {
                        actions++
                        assertTrue(delegate.presentationControllerShouldDismiss(presentation))
                        assertFalse(manager.dialogUIViewController.modalInPresentation)
                    },
                )
            )
            assertTrue(sameNativeObject(presentation, manager.dialogUIViewController.presentationController))
            assertTrue(delegate.presentationControllerShouldDismiss(presentation))
            assertFalse(manager.dialogUIViewController.modalInPresentation)
            manager.configureActionSheetDismissal(presentation)
            assertFalse(manager.dialogUIViewController.modalInPresentation)
            delegate.presentationControllerDidDismiss(presentation)
            manager.dismissalCompleted()
            assertEquals(1, actions)
            assertEquals(0, dismissals)
        }
    }

    @Test
    fun replacedAndForeignPresentationControllersCannotDismissTheCurrentActionSheet() = onMain {
        withFixture { fixture ->
            var actions = 0
            var dismissals = 0
            val manager = actionSheetManager(fixture.parent)
            manager.onDismissRequest = { dismissals++ }
            manager.properties = DialogProperties(dismissOnClickOutside = false)
            val retired = UIPresentationController(manager.dialogUIViewController, fixture.parent)
            manager.presentationCompleted(retired)
            val delegate = assertNotNull(retired.delegate)
            assertFalse(delegate.presentationControllerShouldDismiss(retired))
            val presentation = assertNotNull(manager.dialogUIViewController.presentationController)
            assertFalse(sameNativeObject(retired, presentation))
            manager.presentationCompleted(presentation)
            assertNull(retired.delegate)
            val foreign = UIPresentationController(UIViewController(), fixture.parent)
            manager.configureActionSheetDismissal(foreign)
            assertNull(foreign.delegate)
            assertFalse(delegate.presentationControllerShouldDismiss(retired))
            assertFalse(delegate.presentationControllerShouldDismiss(foreign))
            delegate.presentationControllerDidDismiss(retired)
            delegate.presentationControllerDidDismiss(foreign)
            assertTrue(sameNativeObject(delegate as? NSObject, presentation.delegate as? NSObject))
            assertTrue(manager.dialogUIViewController.modalInPresentation)
            assertEquals(0, dismissals)
            manager.actionInvoked(
                AlertDialogIosAction(
                    title = "Confirm",
                    style = AlertDialogIosActionStyle.Default,
                    onClick = { actions++ },
                )
            )
            assertFalse(delegate.presentationControllerShouldDismiss(retired))
            assertFalse(delegate.presentationControllerShouldDismiss(foreign))
            assertTrue(delegate.presentationControllerShouldDismiss(presentation))
            assertFalse(manager.dialogUIViewController.modalInPresentation)
            delegate.presentationControllerDidDismiss(retired)
            delegate.presentationControllerDidDismiss(foreign)
            assertTrue(delegate.presentationControllerShouldDismiss(presentation))
            assertEquals(0, dismissals)
            delegate.presentationControllerDidDismiss(presentation)
            manager.dismissalCompleted()
            assertNull(presentation.delegate)
            assertEquals(1, actions)
            assertEquals(0, dismissals)
        }
    }

    @Test
    fun controlledAlertActionAndCompletionNotifyEachCallbackOnce() = onMain {
        withFixture { fixture ->
            var actions = 0
            var dismissals = 0
            val manager = actionSheetManager(fixture.parent)
            manager.iosProperties = manager.iosProperties.copy(style = AlertDialogIosStyle.Alert)
            manager.onDismissRequest = { dismissals++ }
            manager.presentationCompleted()
            manager.actionInvoked(
                AlertDialogIosAction(
                    title = "Confirm",
                    style = AlertDialogIosActionStyle.Default,
                    onClick = { actions++ },
                )
            )
            manager.dismissalCompleted()
            manager.dismissalCompleted()
            assertEquals(1, actions)
            assertEquals(1, dismissals)
        }
    }

    @Test
    fun repositionAfterSourceRemovalUsesTheFallback() = onMain {
        withFixture { fixture ->
            val source = UIView(frame = CGRectMake(1.0, 2.0, 30.0, 40.0))
            fixture.parent.view.addSubview(source)
            val manager = actionSheetManager(fixture.parent)
            manager.popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(source)
            val popover = manager.configureControlledPopover(fixture.parent)
            val delegate = assertNotNull(popover.delegate as? UIPopoverPresentationControllerDelegateProtocol)
            source.removeFromSuperview()
            memScoped {
                val rect = alloc<CGRect>()
                val view = alloc<ObjCObjectVar<UIView?>>()
                view.value = source
                delegate.popoverPresentationController(popover, rect.ptr, view.ptr)
                assertTrue(sameNativeObject(fixture.parent.view, view.value))
                assertFallbackCenter(popover, fixture.parent.view)
            }
        }
    }

    private fun actionSheetManager(parent: UIViewController): AlertDialogManager =
        AlertDialogManager(
            parentUIViewController = parent,
            onDismissRequest = {},
            iosProperties = AlertDialogIosProperties(
                title = "Public anchor geometry",
                animated = false,
                style = AlertDialogIosStyle.ActionSheet,
                actions = listOf(
                    AlertDialogIosAction(
                        title = "Close",
                        style = AlertDialogIosActionStyle.Cancel,
                        onClick = {},
                    )
                ),
            ),
            properties = DialogProperties(),
        )

    private fun AlertDialogManager.configureControlledPopover(
        parent: UIViewController,
    ): UIPopoverPresentationController {
        // Controlled public UIKit object: independent of the test device's idiom.
        // This does not prove which controller UIKit creates during presentation.
        return UIPopoverPresentationController(dialogUIViewController, parent).also {
            configurePopoverPresentation(it)
        }
    }

    private fun assertFallbackCenter(
        popover: UIPopoverPresentationController,
        presenter: UIView,
    ) {
        presenter.bounds().useContents {
            assertRect(
                popover.sourceRect,
                origin.x + size.width / 2.0,
                origin.y + size.height / 2.0,
                1.0,
                1.0,
            )
        }
    }

    private fun assertRect(
        actual: CValue<CGRect>,
        x: Double,
        y: Double,
        width: Double,
        height: Double,
    ) = actual.useContents {
        assertNear(x, origin.x, "origin.x")
        assertNear(y, origin.y, "origin.y")
        assertNear(width, size.width, "size.width")
        assertNear(height, size.height, "size.height")
    }

    private fun assertNear(expected: Double, actual: Double, name: String) {
        assertTrue(abs(expected - actual) < 0.001, "$name: expected $expected, got $actual")
    }

    private fun sameNativeObject(first: NSObject?, second: NSObject?): Boolean =
        first != null && second != null && first.objcPtr() == second.objcPtr()

    private fun onMain(block: () -> Unit) {
        // XCTest runs these synchronous library tests on the main thread. Failing
        // fast here is safer than dispatching to a main run loop that the caller
        // may already be blocking while waiting for this test.
        check(NSThread.isMainThread) { "UIKit popover geometry tests must run on Main" }
        block()
    }

    private fun withFixture(block: (WindowFixture) -> Unit) {
        val fixture = WindowFixture()
        try {
            fixture.attach()
            block(fixture)
        } finally {
            fixture.dispose()
        }
    }

    private class WindowFixture {
        val window = UIWindow(frame = CGRectMake(0.0, 0.0, 800.0, 600.0))
        val parent = UIViewController()

        fun attach() {
            parent.view.setFrame(window.bounds())
            window.rootViewController = parent
            window.hidden = false
            window.layoutIfNeeded()
            parent.view.layoutIfNeeded()
        }

        fun dispose() {
            parent.presentedViewController?.dismissViewControllerAnimated(
                flag = false,
                completion = null,
            )
            window.hidden = true
            window.rootViewController = null
        }
    }
}
