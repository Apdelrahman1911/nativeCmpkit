// Modified for NativeCmpKit (2026-10-29): actual native state/calendar/action ownership acceptance.
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class,
    androidx.compose.material3.ExperimentalMaterial3Api::class,
    androidx.compose.ui.test.ExperimentalTestApi::class)

package com.mohamedrejeb.calf.ui.timepicker

import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.uikit.LocalUIViewController
import com.mohamedrejeb.calf.ui.internal.datePickers
import com.mohamedrejeb.calf.ui.internal.runApplicationUiTest
import com.mohamedrejeb.calf.ui.internal.sameNativeObject
import com.mohamedrejeb.calf.ui.internal.waitForNative
import platform.Foundation.*
import platform.UIKit.*
import kotlin.test.*

/** Real UIKit calendars/actions and Compose roots, not locale screenshots or physical input. */
class NativeTimeStateLifecycleAcceptanceTest {
    @Test fun identicalStateAndLiveNativeZoneLocaleChangesKeepTheCurrentOwner() = runApplicationUiTest {
        val first = AdaptiveTimePickerState(1, 2, true)
        val second = AdaptiveTimePickerState(14, 35, false)
        var current by mutableStateOf(first)
        var epoch by mutableStateOf(0)
        var committed = -1
        lateinit var parent: UIViewController
        setContent {
            parent = LocalUIViewController.current
            AdaptiveTimePicker(current)
            SideEffect { committed = epoch }
        }
        waitForIdle()
        waitForNative { parent.view.datePickers().singleOrNull()?.window != null }
        lateinit var original: UIDatePicker
        runOnIdle { original = parent.view.datePickers().single() }
        repeat(3) { round ->
            runOnIdle { epoch = round + 1 }
            waitForIdle()
            runOnIdle {
                assertEquals(round + 1, committed)
                assertTrue(sameNativeObject(original, parent.view.datePickers().single()),
                    "Identical hoisted state must not accumulate new views or actions")
            }
        }
        // Real runtime native settings, including a 45-minute offset and a DST zone.
        // This is not a claim that is24hour overrides UIKit or an OS Settings locale change.
        for ((zoneName, localeName, hour, minute) in listOf(
            Settings("Asia/Kathmandu", "ar_SA", 23, 54),
            Settings("America/New_York", "ja_JP", 7, 5),
        )) {
            runOnIdle {
                val zone = assertNotNull(NSTimeZone.timeZoneWithName(zoneName))
                val calendar = NSCalendar(NSCalendarIdentifierGregorian).apply {
                    timeZone = NSTimeZone.timeZoneForSecondsFromGMT(0)
                }
                original.calendar = calendar
                original.timeZone = zone
                original.locale = NSLocale(localeIdentifier = localeName)
                val nativeCalendarBefore = assertNotNull(original.calendar)
                val originalZone = nativeCalendarBefore.timeZone.name
                val displayCalendar = NSCalendar(NSCalendarIdentifierGregorian).apply { timeZone = zone }
                val picked = assertNotNull(displayCalendar.dateFromComponents(NSDateComponents().apply {
                    year = 2026; month = 3; day = 15; this.hour = hour.toLong(); this.minute = minute.toLong(); this.second = 0
                }))
                original.setDate(picked, animated = false)
                original.sendActionsForControlEvents(UIControlEventValueChanged)
                assertEquals(hour, first.hour)
                assertEquals(minute, first.minute)
                assertEquals(14, second.hour)
                assertEquals(35, second.minute)
                assertEquals(localeName, original.locale?.localeIdentifier)
                assertEquals(originalZone, nativeCalendarBefore.timeZone.name,
                    "Decoding must not mutate UIKit's or a caller's calendar")
            }
            waitForIdle() // Actual public effect writes using the same effective native zone.
            runOnIdle {
                val zone = assertNotNull(original.timeZone)
                val calendar = NSCalendar(NSCalendarIdentifierGregorian).apply { timeZone = zone }
                val visible = calendar.components(NSCalendarUnitHour or NSCalendarUnitMinute, original.date)
                assertEquals(hour.toLong(), visible.hour)
                assertEquals(minute.toLong(), visible.minute)
            }
        }
        val priorDefaultZone = runOnIdle { NSTimeZone.defaultTimeZone }
        try {
            // A nil UIDatePicker zone follows Foundation's live default, not
            // the previously installed calendar snapshot. Restore this process
            // setting on every exit; this is not a physical OS Settings change.
            for ((zoneName, hour, minute) in listOf(
                Triple("Pacific/Auckland", 22, 11), Triple("America/Los_Angeles", 6, 37),
            )) {
                runOnIdle {
                    val zone = assertNotNull(NSTimeZone.timeZoneWithName(zoneName))
                    NSTimeZone.defaultTimeZone = zone
                    original.timeZone = null
                    setNativeTime(original, hour, minute)
                    original.sendActionsForControlEvents(UIControlEventValueChanged)
                    assertEquals(hour, first.hour)
                    assertEquals(minute, first.minute)
                    assertEquals(14, second.hour)
                    assertEquals(35, second.minute)
                }
                waitForIdle()
                runOnIdle { assertTime(original, hour, minute) }
            }
        } finally { runOnIdle { NSTimeZone.defaultTimeZone = priorDefaultZone } }
        val previousHour = first.hour
        val previousMinute = first.minute
        runOnIdle { current = second }
        waitForIdle()
        waitForNative {
            val picker = parent.view.datePickers().singleOrNull()
            picker != null && !sameNativeObject(original, picker) && original.window == null
        }
        runOnIdle {
            original.sendActionsForControlEvents(UIControlEventValueChanged)
            assertEquals(previousHour, first.hour)
            assertEquals(previousMinute, first.minute)
            assertEquals(14, second.hour)
            assertEquals(35, second.minute)
            val picker = parent.view.datePickers().single()
            picker.sendActionsForControlEvents(UIControlEventValueChanged)
            assertEquals(14, second.hour)
            assertEquals(35, second.minute)
        }
    }

    @Test fun hoistedTimeSurvivesRealControllerReplacementAndOldActionsAreDetached() {
        val state = AdaptiveTimePickerState(3, 4, true)
        lateinit var oldParent: UIViewController
        lateinit var oldPicker: UIDatePicker
        runApplicationUiTest {
            setContent { oldParent = LocalUIViewController.current; AdaptiveTimePicker(state) }
            waitForIdle()
            waitForNative { oldParent.view.datePickers().singleOrNull()?.window != null }
            runOnIdle {
                oldPicker = oldParent.view.datePickers().single()
                setNativeTime(oldPicker, 18, 42)
                oldPicker.sendActionsForControlEvents(UIControlEventValueChanged)
                assertEquals(18, state.hour)
                assertEquals(42, state.minute)
            }
        }
        runApplicationUiTest {
            lateinit var parent: UIViewController
            setContent { parent = LocalUIViewController.current; AdaptiveTimePicker(state) }
            waitForIdle()
            waitForNative { parent.view.datePickers().singleOrNull()?.window != null }
            runOnIdle {
                val picker = parent.view.datePickers().single()
                assertFalse(sameNativeObject(oldParent, parent))
                assertFalse(sameNativeObject(oldPicker, picker))
                assertNull(oldParent.view.window)
                assertNull(oldPicker.window)
                assertTime(picker, 18, 42)
                // Keep the old UIKit object alive deliberately: GC is not action cleanup.
                setNativeTime(oldPicker, 1, 9)
                oldPicker.sendActionsForControlEvents(UIControlEventValueChanged)
                assertEquals(18, state.hour)
                assertEquals(42, state.minute)
                setNativeTime(picker, 7, 5)
                picker.sendActionsForControlEvents(UIControlEventValueChanged)
                assertEquals(7, state.hour)
                assertEquals(5, state.minute)
            }
        }
    }

    private fun setNativeTime(picker: UIDatePicker, hour: Int, minute: Int) {
        val calendar = (assertNotNull(picker.calendar).copyWithZone(null) as NSCalendar).apply {
            timeZone = picker.timeZone ?: NSTimeZone.localTimeZone
        }
        val components = calendar.components(NSCalendarUnitYear or NSCalendarUnitMonth or NSCalendarUnitDay, picker.date)
        components.hour = hour.toLong(); components.minute = minute.toLong(); components.second = 0
        picker.setDate(assertNotNull(calendar.dateFromComponents(components)), animated = false)
    }

    private fun assertTime(picker: UIDatePicker, hour: Int, minute: Int) {
        val calendar = (assertNotNull(picker.calendar).copyWithZone(null) as NSCalendar).apply {
            timeZone = picker.timeZone ?: NSTimeZone.localTimeZone
        }
        val components = calendar.components(NSCalendarUnitHour or NSCalendarUnitMinute, picker.date)
        assertEquals(hour.toLong(), components.hour)
        assertEquals(minute.toLong(), components.minute)
    }

    private data class Settings(val zone: String, val locale: String, val hour: Int, val minute: Int)
}
