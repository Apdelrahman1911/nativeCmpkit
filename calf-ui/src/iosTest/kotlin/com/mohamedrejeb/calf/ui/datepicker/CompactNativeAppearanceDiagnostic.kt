@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.ui.graphics.Color
import com.mohamedrejeb.calf.ui.internal.requireOwnedApplicationWindow
import com.mohamedrejeb.calf.ui.internal.runApplicationUiTest
import com.mohamedrejeb.calf.ui.internal.sameNativeObject
import com.mohamedrejeb.calf.ui.utils.toUIColor
import platform.CoreGraphics.CGRectMake
import platform.Foundation.NSThread
import platform.UIKit.*
import kotlin.test.assertNull
import kotlin.test.assertTrue

/**
 * Observes real UIDatePicker setters/layout independently of the public Compose
 * picker. It never writes to the public control or changes its failed assertion.
 * Diagnostic booleans are evidence, not a successful appearance-test verdict.
 */
internal fun traceCompactNativeAppearance() = runApplicationUiTest {
    setContent {}
    runOnIdle {
        val root = requireNotNull(requireOwnedApplicationWindow().rootViewController).view
        val background = Color(0xff143859).toUIColor()
        val tint = Color(0xffcf37a2).toUIColor()
        // Keep this raw UIKit witness independent of the repaired, decorated
        // production owner. It must not become a manufactured passing control.
        val picker = UIDatePicker().apply {
            setDate(localStartOfDay(MAR_15_2026), animated = false)
            datePickerMode = UIDatePickerMode.UIDatePickerModeDate
            preferredDatePickerStyle = UIDatePickerStyle.UIDatePickerStyleCompact
            sizeToFit()
        }
        fun applyColors() {
            picker.tintColor = tint
            picker.backgroundColor = background
        }
        fun observe(phase: String) {
            // No native object pointers, private values or unbounded transcripts.
            println("NATIVECMPKIT_COMPACT_APPEARANCE phase=$phase " +
                "backgroundMatches=${picker.backgroundColor == background} " +
                "tintMatches=${picker.tintColor == tint} attached=${picker.window != null} " +
                "enabled=${picker.enabled} rtl=${picker.semanticContentAttribute == UISemanticContentAttributeForceRightToLeft} " +
                "dark=${picker.overrideUserInterfaceStyle == UIUserInterfaceStyle.UIUserInterfaceStyleDark} " +
                "mainThread=${NSThread.isMainThread}")
        }
        observe("created")
        picker.semanticContentAttribute = UISemanticContentAttributeForceRightToLeft
        picker.minimumDate = localStartOfDay(MAR_1_2026)
        picker.maximumDate = localEndOfDay(MAR_31_2026)
        picker.enabled = false
        picker.overrideUserInterfaceStyle = UIUserInterfaceStyle.UIUserInterfaceStyleDark
        applyColors()
        observe("configured-before-attachment")
        picker.setFrame(CGRectMake(0.0, 0.0, 320.0, 72.0))
        try {
            root.addSubview(picker)
            assertTrue(sameNativeObject(picker.window, root.window))
            picker.setNeedsLayout()
            picker.layoutIfNeeded()
            observe("attached-laid-out")
            applyColors()
            observe("colors-reapplied-after-attachment")
            picker.sizeToFit()
            picker.setNeedsLayout()
            picker.layoutIfNeeded()
            observe("after-size-to-fit")
            picker.enabled = true
            picker.setNeedsLayout()
            picker.layoutIfNeeded()
            observe("after-enabled-change")
            picker.overrideUserInterfaceStyle = UIUserInterfaceStyle.UIUserInterfaceStyleLight
            picker.setNeedsLayout()
            picker.layoutIfNeeded()
            observe("after-theme-change")
        } finally {
            picker.removeFromSuperview()
            assertNull(picker.window, "The diagnostic must detach only its own native control")
            observe("detached")
        }
    }
}
