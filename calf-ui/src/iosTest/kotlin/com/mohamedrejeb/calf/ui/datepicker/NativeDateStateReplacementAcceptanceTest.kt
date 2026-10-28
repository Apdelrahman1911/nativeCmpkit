@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class,
    androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.material3.DatePickerColors
import androidx.compose.material3.DatePickerDefaults
import androidx.compose.material3.DisplayMode
import androidx.compose.runtime.*
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.uikit.LocalUIViewController
import androidx.compose.ui.unit.LayoutDirection
import com.mohamedrejeb.calf.ui.internal.runApplicationUiTest
import com.mohamedrejeb.calf.ui.internal.sameNativeObject
import com.mohamedrejeb.calf.ui.internal.waitForNative
import com.mohamedrejeb.calf.ui.utils.toUIColor
import platform.UIKit.*
import kotlin.test.*

/** Actual public Compose/UIKit identity boundaries; no replacement native view or physical input claim. */
class NativeDateStateReplacementAcceptanceTest {
    @Test fun inlineStateReplacementInitializesAllEqualSettings() = replacement("inline")
    @Test fun compactDisabledReplacementInitializesAllEqualSettings() = replacement("compact")
    @Test fun rangeStateReplacementInitializesAllEqualSettings() = replacement("range")
}

private fun replacement(kind: String) = runApplicationUiTest {
    val rules = DateBounds(MAR_1_2026, MAR_31_2026)
    fun single() = AdaptiveDatePickerState(MAR_15_2026, MAR_1_2026, 2026..2026,
        DisplayMode.Picker, UIKitDisplayMode.Picker, rules)
    fun range() = AdaptiveDateRangePickerState(MAR_15_2026, MAR_16_2026, MAR_1_2026,
        2026..2026, DisplayMode.Picker, rules)
    var state by mutableStateOf(single())
    var rangeState by mutableStateOf(range())
    var generation by mutableStateOf(0)
    var committed = -1
    lateinit var parent: UIViewController
    lateinit var colors: DatePickerColors
    setContent {
        parent = LocalUIViewController.current
        val configured = DatePickerDefaults.colors(containerColor = Color(0xff143859),
            dayContentColor = Color.White, selectedDayContainerColor = Color(0xffcf37a2))
        // Keep exactly the same object: a new colors key must not accidentally hide
        // missing manager keys in the replacement's synchronization effects.
        colors = remember { configured }
        val currentGeneration = generation
        CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
            when (kind) {
                "inline" -> AdaptiveDatePicker(state, colors = colors)
                "compact" -> AdaptiveCompactDatePicker(state, enabled = false, colors = colors)
                else -> AdaptiveDateRangePicker(rangeState, colors = colors)
            }
        }
        SideEffect { committed = currentGeneration }
    }
    fun attachedControl(): UIView? = parent.view.dateControls().singleOrNull()?.takeIf {
        it.window != null && sameNativeObject(it.window, parent.view.window)
    }
    waitForIdle() // Do not read parent before the asynchronous real composition commits.
    waitForNative { attachedControl() != null && committed == 0 }
    lateinit var first: UIView
    runOnIdle {
        first = requireNotNull(attachedControl())
        assertInitialized(first, colors, enabled = kind != "compact")
        generation++ // A genuine ordinary parent recomposition with the same owner.
    }
    waitForNative { committed == 1 }
    runOnIdle {
        assertTrue(sameNativeObject(first, requireNotNull(attachedControl())),
            "Ordinary recomposition must not create a new native $kind view")
        if (kind == "range") rangeState = range() else state = single()
        generation++
    }
    waitForNative {
        committed == 2 && attachedControl()?.let { !sameNativeObject(first, it) } == true
    }
    lateinit var second: UIView
    runOnIdle {
        second = requireNotNull(attachedControl())
        assertNull(first.window, "The old native owner must actually detach")
        assertInitialized(second, colors, enabled = kind != "compact")
        generation++
    }
    waitForNative { committed == 3 }
    runOnIdle {
        assertTrue(sameNativeObject(second, requireNotNull(attachedControl())))
        assertInitialized(second, colors, enabled = kind != "compact")
    }
}

private fun assertInitialized(view: UIView, colors: DatePickerColors, enabled: Boolean) {
    assertEquals(UISemanticContentAttributeForceRightToLeft, view.semanticContentAttribute)
    assertEquals(colors.containerColor.toUIColor(), view.backgroundColor)
    assertEquals(colors.selectedDayContainerColor.toUIColor(), view.tintColor)
    when (view) {
        is UIDatePicker -> {
            assertEquals(UIDatePickerStyle.UIDatePickerStyleCompact, view.preferredDatePickerStyle)
            assertEquals(enabled, view.enabled)
            assertEquals(MAR_1_2026, requireNotNull(view.minimumDate).toUtcDayMillis())
            assertEquals(MAR_31_2026, requireNotNull(view.maximumDate).toUtcDayMillis())
            assertEquals(MAR_15_2026, view.date.toUtcDayMillis())
        }
        is UICalendarView -> {
            assertEquals(enabled, view.userInteractionEnabled)
            assertEquals(MAR_1_2026, view.availableDateRange.startDate.toUtcDayMillis())
            assertEquals(MAR_31_2026, view.availableDateRange.endDate.toUtcDayMillis())
        }
        else -> fail("A real UIDatePicker/UICalendarView is required")
    }
}

private fun UIView.dateControls(): List<UIView> = if (this is UIDatePicker || this is UICalendarView)
    listOf(this) else subviews.filterIsInstance<UIView>().flatMap { it.dateControls() }
