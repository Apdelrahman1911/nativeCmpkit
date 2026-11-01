package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.material3.DatePickerDefaults
import androidx.compose.material3.DisplayMode
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.click
import androidx.compose.ui.test.v2.runComposeUiTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Private proposal: exactly two new Material companions, not old suite replay. */
@OptIn(ExperimentalMaterial3Api::class, ExperimentalTestApi::class)
class MaterialDateYearPolicyImportantTest {
    @Test fun materialRuleChangesNeverSnapBeyondYearRange() {
        assertImportantYearSnapPolicy(importantYearState())
    }

    @Test fun publicMaterialYearPredicateRejectsDateTruePicksAndRecovers() {
        for (isRange in listOf(false, true)) runComposeUiTest {
            val single = importantYearState()
            val range = AdaptiveDateRangePickerState(
                initialSelectedStartDateMillis = MAR_15_2026,
                initialSelectedEndDateMillis = MAR_16_2026,
                initialDisplayedMonthMillis = MAR_1_2026,
                yearRange = 2026..2026,
                initialMaterialDisplayMode = DisplayMode.Picker,
            )
            setContent {
                if (isRange) AdaptiveDateRangePicker(range, title = null, headline = null, showModeToggle = false)
                else AdaptiveDatePicker(single, title = null, headline = null, showModeToggle = false)
            }
            waitForIdle()
            runOnIdle {
                if (isRange) range.selectableDates = RejectEveryYearAllowEveryDate
                else single.selectableDates = RejectEveryYearAllowEveryDate
            }
            waitForIdle()
            runOnIdle {
                val rule = if (isRange) range.dateRangePickerState.selectableDates else single.datePickerState.selectableDates
                assertFalse(rule.isSelectableYear(2026))
                assertTrue(rule.isSelectableDate(IMPORTANT_MAR_17_2026))
                if (isRange) {
                    assertEquals(MAR_15_2026, range.selectedStartDateMillis)
                    assertEquals(MAR_16_2026, range.selectedEndDateMillis)
                } else {
                    assertEquals(MAR_15_2026, single.selectedDateMillis)
                    assertFalse(single.isSelectionSelectable)
                }
            }
            dayCell(IMPORTANT_MAR_17_2026).assertIsNotEnabled().performTouchInput { click() }
            runOnIdle {
                if (isRange) {
                    assertEquals(MAR_15_2026, range.selectedStartDateMillis)
                    assertEquals(MAR_16_2026, range.selectedEndDateMillis)
                } else assertEquals(MAR_15_2026, single.selectedDateMillis)
                if (isRange) range.selectableDates = DatePickerDefaults.AllDates
                else single.selectableDates = DatePickerDefaults.AllDates
            }
            waitForIdle()
            dayCell(IMPORTANT_MAR_17_2026).assertIsEnabled().performClick()
            runOnIdle {
                if (isRange) {
                    assertEquals(IMPORTANT_MAR_17_2026, range.selectedStartDateMillis)
                    assertNull(range.selectedEndDateMillis)
                } else {
                    assertEquals(IMPORTANT_MAR_17_2026, single.selectedDateMillis)
                    assertTrue(single.isSelectionSelectable)
                }
            }
        }
    }
}
