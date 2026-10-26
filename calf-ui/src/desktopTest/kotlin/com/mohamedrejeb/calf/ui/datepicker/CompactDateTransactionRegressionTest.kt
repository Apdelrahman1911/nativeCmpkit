package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.material3.DatePickerDefaults
import androidx.compose.material3.DisplayMode
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.*
import androidx.compose.ui.test.v2.runComposeUiTest
import kotlin.test.*

@OptIn(ExperimentalMaterial3Api::class, ExperimentalTestApi::class)
class CompactDateTransactionRegressionTest {
    private fun state(selected: Long? = MAR_15_2026) = AdaptiveDatePickerState(selected, MAR_1_2026,
        2020..2030, DisplayMode.Picker, UIKitDisplayMode.Picker)
    private fun label() = requireNotNull(DatePickerDefaults.dateFormatter().formatDate(MAR_15_2026, getCalendarLocalDefault()))

    @Test fun tighteningRulesRejectsTheOutstandingScratchSelection() = runComposeUiTest {
        val owner = state()
        setContent { AdaptiveCompactDatePicker(owner, materialConfirmText = "Commit", materialDismissText = "Discard") }
        onNodeWithText(label()).performClick()
        dayCell(MAR_16_2026).performClick()
        runOnIdle { owner.selectableDates = DateBounds(maxDateMillis = MAR_15_2026) }
        onNodeWithText("Commit").assertIsNotEnabled()
        assertEquals(MAR_15_2026, owner.selectedDateMillis)
        onNodeWithText("Discard").performClick()
        onAllNodesWithText("Commit").assertCountEquals(0)
    }

    @Test fun replacingOwnerCancelsRatherThanTransplantsAnOpenEdit() = runComposeUiTest {
        val first = state()
        val replacement = state(MAR_1_2026)
        var owner by mutableStateOf(first)
        setContent { AdaptiveCompactDatePicker(owner, materialConfirmText = "Commit") }
        onNodeWithText(label()).performClick()
        dayCell(MAR_16_2026).performClick()
        runOnIdle { owner = replacement }
        onAllNodesWithText("Commit").assertCountEquals(0)
        assertEquals(MAR_1_2026, replacement.selectedDateMillis)
        assertEquals(MAR_15_2026, first.selectedDateMillis)
    }

    @Test fun allDaysRejectedDisablesConfirmation() = runComposeUiTest {
        val owner = state()
        setContent { AdaptiveCompactDatePicker(owner, materialConfirmText = "Commit") }
        onNodeWithText(label()).performClick()
        runOnIdle { owner.selectableDates = NoDates }
        onNodeWithText("Commit").assertIsNotEnabled()
    }
}
