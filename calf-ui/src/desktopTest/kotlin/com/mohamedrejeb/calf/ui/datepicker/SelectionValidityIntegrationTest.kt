// NativeCmpKit library-level acceptance: real state/public predicate and an actual Compose consumer.
package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.foundation.layout.Column
import androidx.compose.material3.Button
import androidx.compose.material3.DatePickerDefaults
import androidx.compose.material3.DisplayMode
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.SelectableDates
import androidx.compose.material3.Text
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.test.*
import androidx.compose.ui.test.v2.runComposeUiTest
import kotlin.test.*

@OptIn(ExperimentalMaterial3Api::class, ExperimentalTestApi::class)
class SelectionValidityIntegrationTest {
    private fun state() = AdaptiveDatePickerState(MAR_15_2026, MAR_1_2026, 2020..2030,
        DisplayMode.Picker, UIKitDisplayMode.Picker)

    @Test fun noDatesRetainsTheSelectionButExplicitlyReportsInvalidAndNullIsNotValid() {
        val owner = state()
        assertTrue(owner.isSelectionSelectable)
        owner.selectableDates = NoDates
        assertEquals(MAR_15_2026, owner.selectedDateMillis,
            "NoDates must retain the established selection, not silently clear or accept it")
        assertFalse(owner.isSelectionSelectable)
        owner.selectedDateMillis = null
        assertNull(owner.selectedDateMillis)
        assertFalse(owner.isSelectionSelectable, "An empty selection is not a validated non-null date")
    }

    @Test fun aValidDayBeyondTheDefault366DaySearchDoesNotSilentlyValidateTheRetainedDate() {
        val distant = MAR_15_2026 + 367 * MILLIS_PER_DAY
        val sparse = object : SelectableDates {
            override fun isSelectableDate(utcTimeMillis: Long) = utcTimeMillis == distant
        }
        assertEquals(366, DEFAULT_SNAP_SEARCH_DAYS)
        assertNull(nearestSelectableDay(MAR_15_2026, null, null, sparse))
        assertEquals(distant, nearestSelectableDay(MAR_15_2026, null, null, sparse, maxDistanceDays = 367))
        val owner = state()
        owner.selectableDates = sparse
        assertEquals(MAR_15_2026, owner.selectedDateMillis)
        assertFalse(owner.isSelectionSelectable)
        owner.selectedDateMillis = distant // Explicit caller assignment can reach a distant valid date.
        assertTrue(owner.isSelectionSelectable)
    }

    @Test fun laterDayWinsTiesAndChangingEffectiveBoundsRecomputesTheExplicitValidity() {
        val neighbors = object : SelectableDates {
            override fun isSelectableDate(utcTimeMillis: Long) =
                utcTimeMillis == MAR_14_2026 || utcTimeMillis == MAR_16_2026
        }
        assertEquals(MAR_16_2026, nearestSelectableDay(MAR_15_2026, null, null, neighbors))
        val owner = state()
        owner.selectableDates = neighbors
        assertEquals(MAR_16_2026, owner.selectedDateMillis)
        assertTrue(owner.isSelectionSelectable)
        owner.selectableDates = DateBounds(maxDateMillis = MAR_15_2026) and neighbors
        assertEquals(MAR_14_2026, owner.selectedDateMillis)
        assertTrue(owner.isSelectionSelectable)
        owner.selectableDates = DateBounds(MAR_15_2026, MAR_15_2026) and neighbors
        assertEquals(MAR_14_2026, owner.selectedDateMillis,
            "A window rejecting every candidate must retain the prior value explicitly as invalid")
        assertFalse(owner.isSelectionSelectable)
        owner.selectableDates = DateBounds(MAR_15_2026, MAR_16_2026) and neighbors
        assertEquals(MAR_16_2026, owner.selectedDateMillis)
        assertTrue(owner.isSelectionSelectable)
    }

    @Test fun actualConsumerUsesLocalizedLiveRegionAndBlocksInvalidOrEmptySubmission() = runComposeUiTest {
        val owner = state()
        var submitted = 0
        val valid = "التاريخ متاح"
        val invalid = "التاريخ غير متاح"
        val empty = "لم يتم تحديد تاريخ"
        setContent {
            // This is a library consumer fixture, not a sample application or a claimed
            // built-in localized announcement. The library supplies the observable predicate;
            // business validation/text and accessibility announcement policy are host-owned.
            val accepted = owner.isSelectionSelectable
            val status = if (owner.selectedDateMillis == null) empty else if (accepted) valid else invalid
            Column {
                AdaptiveCompactDatePicker(owner, modifier = Modifier.testTag("actual-picker"))
                Text(status, modifier = Modifier.testTag("date-validity").semantics {
                    liveRegion = LiveRegionMode.Polite
                    stateDescription = status
                })
                Button(enabled = accepted, modifier = Modifier.testTag("validated-submit"),
                    onClick = { if (owner.isSelectionSelectable) submitted++ }) { Text("Submit") }
            }
        }
        fun assertStatus(expected: String) {
            onNodeWithTag("date-validity")
                .assertTextEquals(expected)
                .assert(SemanticsMatcher.expectValue(SemanticsProperties.StateDescription, expected))
                .assert(SemanticsMatcher.expectValue(SemanticsProperties.LiveRegion, LiveRegionMode.Polite))
        }
        onNodeWithTag("actual-picker").assertIsDisplayed()
        assertStatus(valid)
        onNodeWithTag("validated-submit").assertIsEnabled().performClick()
        assertEquals(1, submitted)
        runOnIdle { owner.selectableDates = NoDates }
        assertStatus(invalid)
        onNodeWithTag("validated-submit").assertIsNotEnabled().performTouchInput { click() }
        assertEquals(1, submitted)
        assertEquals(MAR_15_2026, owner.selectedDateMillis)
        runOnIdle { owner.selectedDateMillis = null }
        assertStatus(empty)
        onNodeWithTag("validated-submit").assertIsNotEnabled().performTouchInput { click() }
        assertEquals(1, submitted)
        runOnIdle {
            owner.selectableDates = DatePickerDefaults.AllDates
            owner.selectedDateMillis = MAR_15_2026
        }
        assertStatus(valid)
        onNodeWithTag("validated-submit").assertIsEnabled().performClick()
        assertEquals(2, submitted)
    }
}
