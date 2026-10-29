// Modified for NativeCmpKit (2026-10-29): related native rendering/theme integration.
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class,
    androidx.compose.ui.ExperimentalComposeUiApi::class,
    androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.mohamedrejeb.calf.ui.utils

import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.text.BasicText
import androidx.compose.material3.SheetValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.PathParser
import androidx.compose.ui.uikit.LocalUIViewController
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.UIKitView
import androidx.compose.ui.window.ComposeUIViewController
import com.mohamedrejeb.calf.ui.internal.requireOwnedApplicationWindow
import com.mohamedrejeb.calf.ui.internal.runApplicationUiTest
import com.mohamedrejeb.calf.ui.internal.sameNativeObject
import com.mohamedrejeb.calf.ui.internal.waitForNative
import com.mohamedrejeb.calf.ui.sheet.BottomSheetManager
import com.mohamedrejeb.calf.ui.datepicker.CalendarViewHost
import com.mohamedrejeb.calf.ui.uikit.UIKitImage
import kotlinx.cinterop.UByteVar
import kotlinx.cinterop.convert
import kotlinx.cinterop.get
import kotlinx.cinterop.reinterpret
import platform.Foundation.NSThread
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import platform.CoreGraphics.*
import platform.UIKit.*
import kotlin.math.abs
import kotlin.math.roundToInt
import kotlin.test.*

/** Genuine UIKit views/traits/sheet and pixel rendering, not platform or image mocks.
 * Simulator-wide system appearance is changed by the finite, restoring simctl
 * driver. This is simulator behavior, not physical OS Settings or VoiceOver.
 */
class NativeVectorThemeAcceptanceTest {
    @Test fun convertedVectorsKeepOriginalPixelsAndSupportActualNativeTemplateTint() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current; BasicText("Native vector fixture") }
        val vector = ImageVector.Builder("Template ownership", 24.dp, 16.dp, 24f, 16f).apply {
            addPath(PathParser().parsePathString("M2,2 H10 V14 H2 Z").toNodes(),
                fill = SolidColor(Color.Red), fillAlpha = .75f)
            addPath(PathParser().parsePathString("M14,2 H22 V14 H14 Z").toNodes(),
                fill = SolidColor(Color.Blue), fillAlpha = .5f)
        }.build()
        val tint = Color(0xFF3399CC)
        for (density in listOf(2f, 3f)) {
            lateinit var view: UIImageView
            lateinit var raster: UIImage
            runOnIdle {
                raster = assertNotNull(UIKitImage.Vector(vector, 24.dp, 16.dp).toUIImage(density))
                view = UIImageView(frame = CGRectMake(0.0, 0.0, 24.0, 16.0)).apply {
                    tintColor = tint.toUIColor()
                    contentMode = UIViewContentMode.UIViewContentModeScaleToFill
                    image = raster.imageWithRenderingMode(UIImageRenderingMode.UIImageRenderingModeAlwaysOriginal)
                }
                parent.view.addSubview(view)
            }
            try {
                runOnIdle {
                    assertTrue(sameNativeObject(view.window, parent.view.window))
                    val original = snapshot(view, density).rgba()
                    val source = raster.rgba()
                    assertEquals(source.size, original.size)
                    // UIKit may round premultiplied sRGB channels during drawing.
                    // Inspect every channel with the same narrow tolerance used
                    // by the native-vs-Compose painter comparison; never skip edges.
                    source.indices.forEach { channel ->
                        assertTrue(abs((source[channel].toInt() and 255) -
                            (original[channel].toInt() and 255)) <= 3,
                            "AlwaysOriginal raster mismatch at pixel ${channel / 4}, channel ${channel % 4}")
                    }
                    val width = (24 * density).toInt()
                    val red = ((8 * density).toInt() * width + (6 * density).toInt()) * 4
                    val blue = ((8 * density).toInt() * width + (18 * density).toInt()) * 4
                    assertTrue((original[red].toInt() and 255) > 180)
                    assertEquals(0, original[red + 2].toInt() and 255)
                    assertTrue((original[blue + 2].toInt() and 255) > 120)
                    assertEquals(0, original[blue].toInt() and 255)
                    view.image = raster.imageWithRenderingMode(UIImageRenderingMode.UIImageRenderingModeAlwaysTemplate)
                }
                runOnIdle {
                    val actual = snapshot(view, density).rgba()
                    val source = raster.rgba()
                    assertEquals(source.size, actual.size)
                    var coloredPixels = 0
                    for (offset in source.indices step 4) {
                        val alpha = source[offset + 3].toInt() and 255
                        if (alpha > 0) coloredPixels++
                        val expected = listOf((tint.red * alpha).roundToInt(), (tint.green * alpha).roundToInt(),
                            (tint.blue * alpha).roundToInt(), alpha)
                        expected.indices.forEach { channel ->
                            assertTrue(abs(expected[channel] - (actual[offset + channel].toInt() and 255)) <= 3,
                                "Actual UIImageView template mismatch at pixel ${offset / 4}, channel $channel")
                        }
                    }
                    assertTrue(coloredPixels > (24 * 16 * density * density / 4).toInt())
                }
            } finally { runOnIdle { view.removeFromSuperview() } }
        }
    }

    @Test fun attachedOppositeAndInheritedThemesFollowOnlyTheirOwnNativeAppearanceOwner() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current; BasicText("Theme owners") }
        lateinit var dark: UIView; lateinit var light: UIView; lateinit var inherited: UIView
        lateinit var window: UIWindow
        var prior = UIUserInterfaceStyle.UIUserInterfaceStyleUnspecified
        runOnIdle {
            window = requireOwnedApplicationWindow()
            prior = window.overrideUserInterfaceStyle
            dark = UIView(frame = CGRectMake(0.0, 0.0, 80.0, 44.0))
            light = UIView(frame = CGRectMake(80.0, 0.0, 80.0, 44.0))
            inherited = UIView(frame = CGRectMake(160.0, 0.0, 80.0, 44.0))
            parent.view.addSubview(dark); parent.view.addSubview(light); parent.view.addSubview(inherited)
        }
        try {
            runOnIdle { dark.applyTheme(true); light.applyTheme(false) }
            for (style in listOf(UIUserInterfaceStyle.UIUserInterfaceStyleLight, UIUserInterfaceStyle.UIUserInterfaceStyleDark)) {
                runOnIdle { window.overrideUserInterfaceStyle = style }
                awaitMain("actual inherited native trait propagation") {
                    inherited.traitCollection.userInterfaceStyle == style &&
                        dark.traitCollection.userInterfaceStyle == UIUserInterfaceStyle.UIUserInterfaceStyleDark &&
                        light.traitCollection.userInterfaceStyle == UIUserInterfaceStyle.UIUserInterfaceStyleLight
                }
                runOnIdle {
                    assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleUnspecified, parent.overrideUserInterfaceStyle)
                    assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleUnspecified, parent.view.overrideUserInterfaceStyle)
                    assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleUnspecified, inherited.overrideUserInterfaceStyle)
                }
            }
            runOnIdle { dark.applyTheme(false); light.removeFromSuperview() }
            awaitMain("updated child trait without rewriting the native ancestor") {
                dark.traitCollection.userInterfaceStyle == UIUserInterfaceStyle.UIUserInterfaceStyleLight &&
                    inherited.traitCollection.userInterfaceStyle == UIUserInterfaceStyle.UIUserInterfaceStyleDark
            }
            runOnIdle { assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleDark, window.overrideUserInterfaceStyle) }
        } finally {
            runOnIdle {
                dark.removeFromSuperview(); light.removeFromSuperview(); inherited.removeFromSuperview()
                window.overrideUserInterfaceStyle = prior
            }
        }
    }

    @Test fun transparentDayControlInsideRealComposeNativeSheetNeverRewritesAnyAncestorTheme() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current; BasicText("Light native presenter") }
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
        var manager: BottomSheetManager? = null
        var day: UICalendarView? = null
        var calendarHost: CalendarViewHost? = null
        lateinit var showing: Job
        var prior = UIUserInterfaceStyle.UIUserInterfaceStyleUnspecified
        // CalendarViewHost chooses the background style from inverse text
        // luminance. Transparent black day text deliberately selects a light
        // calendar inside a dark native sheet, exercising the actual callsite.
        val dayColor = Color.Black.copy(alpha = .1f)
        runOnIdle {
            prior = parent.overrideUserInterfaceStyle
            parent.applyTheme(false)
            manager = BottomSheetManager(parent, true, dayColor, {}, { true }, { _, _ -> }, {
                BasicText("Transparent light child in dark sheet")
                UIKitView(factory = {
                    CalendarViewHost().also { calendarHost = it; day = it.calendarView }.calendarView
                }, modifier = Modifier.width(320.dp).height(380.dp))
            })
            showing = scope.launch { manager!!.show(true, false, SheetValue.Expanded) }
        }
        try {
            waitForNative { showing.isCompleted && parent.presentedViewController != null && day?.window != null }
            runOnIdle {
                val sheet = assertNotNull(parent.presentedViewController)
                val child = assertNotNull(day)
                val ancestors = generateSequence(child.superview) { it.superview }.map { it to it.overrideUserInterfaceStyle }.toList()
                assertTrue(ancestors.isNotEmpty())
                assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleDark, sheet.overrideUserInterfaceStyle)
                calendarHost!!.applyColors(Color.Transparent, dayColor, Color.Cyan)
                assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleLight, child.overrideUserInterfaceStyle)
                ancestors.forEach { (view, original) -> assertEquals(original, view.overrideUserInterfaceStyle) }
                assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleLight, parent.overrideUserInterfaceStyle)
            }
            for (dark in listOf(false, true)) {
                runOnIdle { manager!!.applyTheme(dark) }
                val expected = if (dark) UIUserInterfaceStyle.UIUserInterfaceStyleDark else UIUserInterfaceStyle.UIUserInterfaceStyleLight
                awaitMain("real native sheet traits while an explicit day child stays isolated") {
                    parent.presentedViewController?.traitCollection?.userInterfaceStyle == expected &&
                        day?.traitCollection?.userInterfaceStyle == UIUserInterfaceStyle.UIUserInterfaceStyleLight
                }
                runOnIdle { assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleLight, parent.overrideUserInterfaceStyle) }
            }
        } finally { runOnIdle { manager?.dispose(); scope.cancel(); parent.overrideUserInterfaceStyle = prior } }
        waitForNative { parent.presentedViewController == null }
    }

    @Test fun realComposeNativePopoverRetainsItsExplicitThemeAndTransparentChildOwnership() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current; BasicText("Popover owner") }
        lateinit var controller: UIViewController
        var day: UICalendarView? = null
        var calendarHost: CalendarViewHost? = null
        var shown = false
        val dayColor = Color.Black.copy(alpha = .1f)
        var prior = UIUserInterfaceStyle.UIUserInterfaceStyleUnspecified
        runOnIdle {
            prior = parent.overrideUserInterfaceStyle
            parent.applyTheme(false)
            controller = ComposeUIViewController {
                BasicText("Transparent day control in a native popover")
                UIKitView(factory = {
                    CalendarViewHost().also { calendarHost = it; day = it.calendarView }.calendarView
                }, modifier = Modifier.width(320.dp).height(380.dp))
            }
            controller.applyTheme(true)
            controller.modalPresentationStyle = UIModalPresentationPopover
            controller.preferredContentSize = CGSizeMake(380.0, 480.0)
            val popover = assertNotNull(controller.popoverPresentationController)
            popover.sourceView = parent.view
            popover.sourceRect = CGRectMake(100.0, 100.0, 1.0, 1.0)
            parent.presentViewController(controller, animated = false) { shown = true }
        }
        try {
            waitForNative { shown && day?.window != null && sameNativeObject(parent.presentedViewController, controller) }
            runOnIdle {
                // iPhone can adapt this requested popover. The dedicated iPad
                // profile must additionally establish a real popover controller.
                if (UIDevice.currentDevice.userInterfaceIdiom == UIUserInterfaceIdiomPad) {
                    assertTrue(controller.presentationController is UIPopoverPresentationController)
                }
                assertTrue(sameNativeObject(controller.popoverPresentationController?.sourceView, parent.view))
                val child = assertNotNull(day)
                val ancestors = generateSequence(child.superview) { it.superview }.map { it to it.overrideUserInterfaceStyle }.toList()
                assertTrue(ancestors.isNotEmpty())
                calendarHost!!.applyColors(Color.Transparent, dayColor, Color.Cyan)
                ancestors.forEach { (view, style) -> assertEquals(style, view.overrideUserInterfaceStyle) }
                assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleDark, controller.overrideUserInterfaceStyle)
                assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleLight, parent.overrideUserInterfaceStyle)
            }
            for (dark in listOf(false, true)) {
                runOnIdle { controller.applyTheme(dark) }
                val expected = if (dark) UIUserInterfaceStyle.UIUserInterfaceStyleDark else UIUserInterfaceStyle.UIUserInterfaceStyleLight
                awaitMain("real popover/native child appearance isolation") {
                    controller.traitCollection.userInterfaceStyle == expected &&
                        day?.traitCollection?.userInterfaceStyle == UIUserInterfaceStyle.UIUserInterfaceStyleLight
                }
                runOnIdle { assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleLight, parent.overrideUserInterfaceStyle) }
            }
        } finally {
            runOnIdle {
                assertTrue(sameNativeObject(parent.presentedViewController, controller))
                parent.dismissViewControllerAnimated(false, null)
                parent.overrideUserInterfaceStyle = prior
            }
        }
        waitForNative { parent.presentedViewController == null && day?.window == null }
    }

    @Test fun actualSimulatorSystemAppearanceChangesLeaveExplicitNativeOverridesIsolated() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current; BasicText("Actual system appearance") }
        lateinit var dark: UIView; lateinit var inherited: UIView
        runOnIdle {
            val window = requireOwnedApplicationWindow()
            assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleUnspecified, window.overrideUserInterfaceStyle)
            assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleUnspecified, parent.overrideUserInterfaceStyle)
            assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleUnspecified, parent.view.overrideUserInterfaceStyle)
            dark = UIView(frame = CGRectMake(0.0, 0.0, 100.0, 44.0)).apply { applyTheme(true) }
            inherited = UIView(frame = CGRectMake(100.0, 0.0, 100.0, 44.0))
            parent.view.addSubview(dark); parent.view.addSubview(inherited)
        }
        try {
            awaitMain("driver-established actual initial light system appearance") {
                inherited.traitCollection.userInterfaceStyle == UIUserInterfaceStyle.UIUserInterfaceStyleLight
            }
            for ((index, style) in listOf("dark", "light").withIndex()) {
                // Exact finite requests only, handled outside the app by simctl.
                println("NATIVECMPKIT_SYSTEM_APPEARANCE phase=request step=${index + 1} style=$style")
                val expected = if (style == "dark") UIUserInterfaceStyle.UIUserInterfaceStyleDark else UIUserInterfaceStyle.UIUserInterfaceStyleLight
                awaitMain("actual simulator-wide appearance propagated to inherited views") {
                    inherited.traitCollection.userInterfaceStyle == expected &&
                        dark.traitCollection.userInterfaceStyle == UIUserInterfaceStyle.UIUserInterfaceStyleDark
                }
                runOnIdle {
                    assertTrue(NSThread.isMainThread)
                    assertEquals(expected, parent.traitCollection.userInterfaceStyle)
                    assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleUnspecified, inherited.overrideUserInterfaceStyle)
                    assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleUnspecified, parent.overrideUserInterfaceStyle)
                    assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleUnspecified, parent.view.overrideUserInterfaceStyle)
                    assertEquals(UIUserInterfaceStyle.UIUserInterfaceStyleUnspecified, requireOwnedApplicationWindow().overrideUserInterfaceStyle)
                }
                println("NATIVECMPKIT_SYSTEM_APPEARANCE phase=verified step=${index + 1} style=$style")
            }
        } finally { runOnIdle { dark.removeFromSuperview(); inherited.removeFromSuperview() } }
    }

    private fun snapshot(view: UIImageView, density: Float): UIImage {
        UIGraphicsBeginImageContextWithOptions(CGSizeMake(24.0, 16.0), false, density.toDouble())
        try {
            assertNotNull(UIGraphicsGetCurrentContext())
            view.layoutIfNeeded()
            // Actual UIKit drawing; do not wait synchronously for another main-loop update.
            assertTrue(view.drawViewHierarchyInRect(view.bounds, afterScreenUpdates = false))
            return assertNotNull(UIGraphicsGetImageFromCurrentImageContext())
        } finally { UIGraphicsEndImageContext() }
    }

    private fun UIImage.rgba(): ByteArray {
        val image = assertNotNull(CGImage)
        val width = CGImageGetWidth(image).toInt(); val height = CGImageGetHeight(image).toInt()
        val space = assertNotNull(CGColorSpaceCreateWithName(kCGColorSpaceSRGB))
        try {
            val context = assertNotNull(CGBitmapContextCreate(null, width.convert(), height.convert(), 8u,
                (width * 4).convert(), space, CGImageAlphaInfo.kCGImageAlphaPremultipliedLast.value or kCGBitmapByteOrder32Big))
            try {
                val rect = CGRectMake(0.0, 0.0, width.toDouble(), height.toDouble())
                CGContextSetBlendMode(context, CGBlendMode.kCGBlendModeCopy)
                CGContextSetRGBFillColor(context, 0.0, 0.0, 0.0, 0.0)
                CGContextFillRect(context, rect)
                CGContextSetBlendMode(context, CGBlendMode.kCGBlendModeNormal)
                CGContextDrawImage(context, rect, image)
                val data = assertNotNull(CGBitmapContextGetData(context)).reinterpret<UByteVar>()
                return ByteArray(width * height * 4) { data[it].toByte() }
            } finally { CGContextRelease(context) }
        } finally { CGColorSpaceRelease(space) }
    }
}
