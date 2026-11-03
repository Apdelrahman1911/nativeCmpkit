// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class, kotlinx.cinterop.BetaInteropApi::class,
    com.mohamedrejeb.calf.core.InternalCalfApi::class)

package com.mohamedrejeb.calf.ui.dialog

import androidx.compose.ui.uikit.LocalUIViewController
import androidx.compose.ui.window.DialogProperties
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosAction
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosActionStyle
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosPopoverAnchor
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosProperties
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosStyle
import com.mohamedrejeb.calf.ui.internal.NativeApplicationUiTest
import com.mohamedrejeb.calf.ui.internal.requireOwnedApplicationWindow
import com.mohamedrejeb.calf.ui.internal.runApplicationUiTest
import com.mohamedrejeb.calf.ui.internal.sameNativeObject
import com.mohamedrejeb.calf.ui.internal.waitForNative
import kotlinx.cinterop.CValue
import kotlinx.cinterop.useContents
import platform.CoreGraphics.CGRect
import platform.CoreGraphics.CGRectMake
import platform.Foundation.NSError
import platform.Foundation.NSProcessInfo
import platform.UIKit.*
import kotlin.math.abs
import kotlin.test.*

/** Public OS geometry requests, never bounds/traits overrides or manufactured reposition callbacks. */
class NativePopoverGeometryTest {
    @Test fun nativePortraitTraitsAndViewLocalAnchorUseTheOwnedScene() = runApplicationUiTest {
        exerciseOwnedGeometry(rotateWhilePresented = false)
    }

    @Test fun nativeOSRotationRefreshesOwnedAnchorsAndRestoresTheOriginalOrientation() = runApplicationUiTest {
        exerciseOwnedGeometry(rotateWhilePresented = true)
    }

    private fun NativeApplicationUiTest.exerciseOwnedGeometry(rotateWhilePresented: Boolean) {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        lateinit var scene: UIWindowScene
        lateinit var window: UIWindow
        var originalOrientation: Long? = null
        var attemptedGeometry = false
        var source: UIView? = null
        var manager: AlertDialogManager? = null
        var primary: Throwable? = null
        var geometryError: NSError? = null // Main-confined; checked by every awaited predicate.
        assertTrue(NSProcessInfo.processInfo.operatingSystemVersion.useContents { majorVersion >= 16 })
        val expectedIdiom = NSProcessInfo.processInfo.environment["NATIVECMPKIT_POPOVER_GEOMETRY_IDIOM"] as? String
        assertTrue(expectedIdiom in setOf("iphone", "ipad"))
        if (rotateWhilePresented) assertEquals("ipad", expectedIdiom)

        fun geometry(target: Long) {
            runOnIdle {
                assertTrue(sameNativeObject(requireOwnedApplicationWindow(), window))
                assertTrue(sameNativeObject(window.windowScene, scene))
                assertEquals(UISceneActivationStateForegroundActive, scene.activationState)
                geometryError = null
                attemptedGeometry = true // Own restoration before an uncertain native request.
                scene.requestGeometryUpdateWithPreferences(
                    UIWindowSceneGeometryPreferencesIOS(interfaceOrientations = orientationMask(target)),
                    errorHandler = { error -> geometryError = checkNotNull(error) },
                )
            }
            waitForNative {
                geometryError?.let { failure -> error("Owned public OS geometry request failed: code=${failure.code}") }
                sameNativeObject(requireOwnedApplicationWindow(), window) && sameNativeObject(window.windowScene, scene) &&
                    scene.activationState == UISceneActivationStateForegroundActive && scene.interfaceOrientation == target &&
                    window.bounds.useContents { validGeometry(size.width, size.height, target) } &&
                    parent.view.bounds.useContents { validGeometry(size.width, size.height, target) }
            }
        }

        try {
            runOnIdle {
                window = requireOwnedApplicationWindow()
                scene = checkNotNull(window.windowScene) { "This profile requires a genuine connected UIWindowScene" }
                assertEquals(UISceneActivationStateForegroundActive, scene.activationState)
                assertTrue(sameNativeObject(parent.view.window, window))
                assertEquals(if (expectedIdiom == "ipad") UIUserInterfaceIdiomPad else UIUserInterfaceIdiomPhone,
                    UIDevice.currentDevice.userInterfaceIdiom)
                originalOrientation = scene.interfaceOrientation.also { orientationMask(it) }
            }
            geometry(UIInterfaceOrientationPortrait)
            runOnIdle {
                assertEquals(if (expectedIdiom == "ipad") UIUserInterfaceSizeClassRegular else UIUserInterfaceSizeClassCompact,
                    parent.traitCollection.horizontalSizeClass)
                source = UIView(frame = parent.view.bounds).apply {
                    autoresizingMask = UIViewAutoresizingFlexibleWidth or UIViewAutoresizingFlexibleHeight
                    parent.view.addSubview(this)
                }
                manager = AlertDialogManager(parent, {}, AlertDialogIosProperties(title = "Native OS geometry", animated = false,
                    style = AlertDialogIosStyle.ActionSheet,
                    actions = listOf(AlertDialogIosAction("Close", AlertDialogIosActionStyle.Default, {}))), DialogProperties()).apply {
                    popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(checkNotNull(source))
                    showAlertDialog()
                }
            }
            waitForNative { parent.presentedViewController is UIAlertController }
            lateinit var alert: UIAlertController
            lateinit var popover: UIPopoverPresentationController
            runOnIdle {
                alert = parent.presentedViewController as UIAlertController
                popover = checkNotNull(alert.popoverPresentationController)
                assertTrue(sameNativeObject(source, popover.sourceView))
                assertSameRect(checkNotNull(source).bounds, popover.sourceRect)
                assertNull(popover.barButtonItem)
            }
            if (rotateWhilePresented) {
                // Genuine WindowScene geometry input; no manager/property/delegate update after rotation.
                geometry(UIInterfaceOrientationLandscapeLeft)
                waitForNative {
                    sameNativeObject(alert, parent.presentedViewController) && sameNativeObject(source, popover.sourceView) &&
                        sameRect(checkNotNull(source).bounds, popover.sourceRect)
                }
                runOnIdle {
                    assertEquals(UIUserInterfaceSizeClassRegular, parent.traitCollection.horizontalSizeClass)
                    assertTrue(sameNativeObject(alert, parent.presentedViewController))
                    assertTrue(sameNativeObject(source, popover.sourceView))
                    assertSameRect(checkNotNull(source).bounds, popover.sourceRect)
                    manager!!.popoverAnchor = AlertDialogIosPopoverAnchor.ViewRect(null)
                    manager!!.updateDialogProperties() // Change requested anchor only BEFORE the next OS event.
                    assertTrue(sameNativeObject(parent.view, popover.sourceView))
                    assertEquals(0uL, popover.permittedArrowDirections)
                }
                geometry(UIInterfaceOrientationPortrait)
                waitForNative {
                    sameNativeObject(alert, parent.presentedViewController) && sameNativeObject(parent.view, popover.sourceView) &&
                        isFallbackCenter(parent.view.bounds, popover.sourceRect)
                }
                runOnIdle {
                    assertEquals(UIUserInterfaceSizeClassRegular, parent.traitCollection.horizontalSizeClass)
                    assertTrue(sameNativeObject(alert, parent.presentedViewController))
                    assertTrue(isFallbackCenter(parent.view.bounds, popover.sourceRect))
                    assertNull(popover.barButtonItem)
                }
            }
        } catch (failure: Throwable) {
            primary = failure
            throw failure
        } finally {
            var cleanupFailure: Throwable? = null
            fun cleanup(action: () -> Unit) {
                try { action() } catch (failure: Throwable) {
                    val prior = primary ?: cleanupFailure
                    if (prior == null) cleanupFailure = failure else if (prior !== failure) prior.addSuppressed(failure)
                }
            }
            cleanup { runOnIdle { manager?.dispose(); source?.removeFromSuperview() } }
            cleanup { waitForNative { parent.presentedViewController == null } }
            if (attemptedGeometry) cleanup { geometry(checkNotNull(originalOrientation)) }
            cleanupFailure?.let { throw it }
        }
    }

    private fun orientationMask(orientation: Long): ULong = when (orientation) {
        UIInterfaceOrientationPortrait -> UIInterfaceOrientationMaskPortrait
        UIInterfaceOrientationLandscapeLeft -> UIInterfaceOrientationMaskLandscapeLeft
        UIInterfaceOrientationLandscapeRight -> UIInterfaceOrientationMaskLandscapeRight
        UIInterfaceOrientationPortraitUpsideDown -> UIInterfaceOrientationMaskPortraitUpsideDown
        else -> error("An unknown original interface orientation cannot be restored")
    }

    private fun validGeometry(width: Double, height: Double, orientation: Long): Boolean =
        width.isFinite() && height.isFinite() && width > 0.0 && height > 0.0 &&
            if (orientation in setOf(UIInterfaceOrientationPortrait, UIInterfaceOrientationPortraitUpsideDown)) height > width else width > height

    private fun sameRect(a: CValue<CGRect>, b: CValue<CGRect>): Boolean = a.useContents {
        val ax = origin.x; val ay = origin.y; val aw = size.width; val ah = size.height
        b.useContents { abs(ax - origin.x) < 0.001 && abs(ay - origin.y) < 0.001 &&
            abs(aw - size.width) < 0.001 && abs(ah - size.height) < 0.001 }
    }

    private fun assertSameRect(a: CValue<CGRect>, b: CValue<CGRect>) = assertTrue(sameRect(a, b))

    private fun isFallbackCenter(bounds: CValue<CGRect>, rect: CValue<CGRect>): Boolean = bounds.useContents {
        sameRect(CGRectMake(origin.x + size.width / 2.0, origin.y + size.height / 2.0, 1.0, 1.0), rect)
    }
}
