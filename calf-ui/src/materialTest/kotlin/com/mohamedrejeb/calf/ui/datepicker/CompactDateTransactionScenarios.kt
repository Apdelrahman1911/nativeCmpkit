// NativeCmpKit library regression: the actual public Material dialog and its event boundaries.
package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.material3.DatePickerDefaults
import androidx.compose.material3.DisplayMode
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.*
import kotlin.test.*

private const val COMMIT = "Commit transaction"
private const val DISCARD = "Discard transaction"
private const val EMPTY = "No date selected"

@OptIn(ExperimentalMaterial3Api::class)
private fun transactionState(selected: Long? = MAR_15_2026, range: IntRange = 2020..2030,
                             mode: DisplayMode = DisplayMode.Picker) =
    AdaptiveDatePickerState(selected, MAR_1_2026, range, mode, UIKitDisplayMode.Picker)

@OptIn(ExperimentalMaterial3Api::class)
private fun transactionLabel(selected: Long) = requireNotNull(
    DatePickerDefaults.dateFormatter().formatDate(selected, getCalendarLocalDefault()),
)

@OptIn(ExperimentalMaterial3Api::class, ExperimentalTestApi::class)
private fun ComposeUiTest.transactionDay(selected: Long): SemanticsNodeInteraction {
    val description = requireNotNull(DatePickerDefaults.dateFormatter()
        .formatDate(selected, getCalendarLocalDefault(), forContentDescription = true))
    return onNode((hasText(description, substring = true) or
        hasContentDescription(description, substring = true)) and hasClickAction())
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalTestApi::class)
internal fun ComposeUiTest.rejectCapturedConfirmAfterRulesTighten() {
    val owner = transactionState()
    setContent { AdaptiveCompactDatePicker(owner, materialConfirmText = COMMIT, materialDismissText = DISCARD) }
    onNodeWithText(transactionLabel(MAR_15_2026)).performClick()
    transactionDay(MAR_16_2026).performClick()
    onNodeWithText(COMMIT).assertIsEnabled()
    val enabledAction = assertNotNull(onNodeWithText(COMMIT).fetchSemanticsNode()
        .config[SemanticsActions.OnClick].action)

    // Deliver the previously enabled real event before recomposition can disable
    // its button. A disabled-only test would miss unconditional stale callbacks.
    runOnIdle {
        owner.selectableDates = DateBounds(maxDateMillis = MAR_15_2026)
        assertTrue(enabledAction())
        assertEquals(MAR_15_2026, owner.selectedDateMillis)
        assertEquals(MAR_1_2026, owner.displayedMonthMillis)
    }
    onNodeWithText(COMMIT).assertIsNotEnabled()
    transactionDay(MAR_16_2026).assertIsNotEnabled()
    onNodeWithText(DISCARD).assertIsDisplayed()
    runOnIdle { owner.selectableDates = DatePickerDefaults.AllDates }
    onNodeWithText(COMMIT).assertIsEnabled().performClick()
    assertEquals(MAR_16_2026, runOnIdle { owner.selectedDateMillis })
    onAllNodesWithText(COMMIT).assertCountEquals(0)
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalTestApi::class)
internal fun ComposeUiTest.replaceOwnerAndYearRangeWithoutTransplantingScratchState() {
    val first = transactionState()
    val replacement = transactionState(MAR_1_2026, range = 2026..2026).apply {
        selectableDates = DateBounds(maxDateMillis = MAR_15_2026)
    }
    var owner by mutableStateOf(first)
    setContent { AdaptiveCompactDatePicker(owner, materialConfirmText = COMMIT, materialDismissText = DISCARD) }
    onNodeWithText(transactionLabel(MAR_15_2026)).performClick()
    transactionDay(MAR_16_2026).performClick()
    runOnIdle { owner = replacement }
    onAllNodesWithText(COMMIT).assertCountEquals(0)
    runOnIdle {
        assertEquals(MAR_15_2026, first.selectedDateMillis)
        assertEquals(MAR_1_2026, replacement.selectedDateMillis)
        assertEquals(2026..2026, replacement.yearRange)
    }
    onNodeWithText(transactionLabel(MAR_1_2026)).performClick()
    transactionDay(MAR_16_2026).assertIsNotEnabled()
    transactionDay(MAR_15_2026).performClick()
    onNodeWithText(DISCARD).performClick()
    assertEquals(MAR_1_2026, runOnIdle { replacement.selectedDateMillis })
    onNodeWithText(transactionLabel(MAR_1_2026)).performClick()
    transactionDay(MAR_1_2026).assertIsSelected()
    transactionDay(MAR_15_2026).performClick()
    onNodeWithText(COMMIT).performClick()
    runOnIdle {
        assertEquals(MAR_15_2026, replacement.selectedDateMillis)
        assertEquals(MAR_15_2026, first.selectedDateMillis)
    }
    onAllNodesWithText(COMMIT).assertCountEquals(0)
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalTestApi::class)
internal fun ComposeUiTest.clearActualInputThenCancelReopenAndCommitNull() {
    val owner = transactionState(mode = DisplayMode.Input)
    setContent { AdaptiveCompactDatePicker(owner, materialPlaceholder = EMPTY,
        materialConfirmText = COMMIT, materialDismissText = DISCARD) }
    onNodeWithText(transactionLabel(MAR_15_2026)).performClick()
    val seed = onNode(hasSetTextAction()).fetchSemanticsNode()
        .config[SemanticsProperties.EditableText].text
    assertTrue(seed.isNotEmpty(), "The real input must start with the owner's non-null date")
    onNode(hasSetTextAction()).performTextClearance()
    // The merged Material field still contains its visible "Date" label. Check
    // the actual editable value, not Text + EditableText (label plus input).
    assertEquals("", onNode(hasSetTextAction()).fetchSemanticsNode()
        .config[SemanticsProperties.EditableText].text)
    assertEquals(MAR_15_2026, runOnIdle { owner.selectedDateMillis })
    onNodeWithText(DISCARD).performClick()
    onNodeWithText(transactionLabel(MAR_15_2026)).performClick()
    assertEquals(seed, onNode(hasSetTextAction()).fetchSemanticsNode()
        .config[SemanticsProperties.EditableText].text)
    onNode(hasSetTextAction()).performTextClearance()
    onNodeWithText(COMMIT).assertIsEnabled().performClick()
    assertNull(runOnIdle { owner.selectedDateMillis })
    onAllNodesWithText(COMMIT).assertCountEquals(0)
    onNodeWithText(EMPTY).performClick()
    assertEquals("", onNode(hasSetTextAction()).fetchSemanticsNode()
        .config[SemanticsProperties.EditableText].text)
    onNodeWithText(COMMIT).assertIsEnabled().performClick()
    assertNull(runOnIdle { owner.selectedDateMillis })
    onNodeWithText(EMPTY).assertIsDisplayed()
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalTestApi::class)
internal fun ComposeUiTest.rejectAllDaysThenCancelAndReopenWithRecoveredRules() {
    val owner = transactionState()
    setContent { AdaptiveCompactDatePicker(owner, materialConfirmText = COMMIT, materialDismissText = DISCARD) }
    onNodeWithText(transactionLabel(MAR_15_2026)).performClick()
    transactionDay(MAR_16_2026).performClick()
    runOnIdle { owner.selectableDates = NoDates }
    onNodeWithText(COMMIT).assertIsNotEnabled()
    onNodeWithText(COMMIT).performTouchInput { click() }
    assertEquals(MAR_15_2026, runOnIdle { owner.selectedDateMillis })
    onNodeWithText(DISCARD).performClick()
    onAllNodesWithText(COMMIT).assertCountEquals(0)
    runOnIdle { owner.selectableDates = DatePickerDefaults.AllDates }
    onNodeWithText(transactionLabel(MAR_15_2026)).performClick()
    transactionDay(MAR_15_2026).assertIsSelected()
    transactionDay(MAR_16_2026).assertIsNotSelected()
    onNodeWithText(COMMIT).assertIsEnabled().performClick()
    assertEquals(MAR_15_2026, runOnIdle { owner.selectedDateMillis })
    onAllNodesWithText(COMMIT).assertCountEquals(0)
}
