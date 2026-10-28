package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.v2.runComposeUiTest
import kotlinx.coroutines.test.TestResult
import kotlin.test.Test

@OptIn(ExperimentalTestApi::class)
class CompactDateTransactionAcceptanceTest {
    @Test fun capturedConfirmRevalidatesTheLatestRules(): TestResult = runComposeUiTest {
        rejectCapturedConfirmAfterRulesTighten()
    }
    @Test fun replacementOwnerYearRangeAndRuleStartAnIndependentTransaction(): TestResult = runComposeUiTest {
        replaceOwnerAndYearRangeWithoutTransplantingScratchState()
    }
    @Test fun nullInputClearCancelReopenAndConfirmRemainTransactional(): TestResult = runComposeUiTest {
        clearActualInputThenCancelReopenAndCommitNull()
    }
    @Test fun noSelectableDateRejectsCommitAndCancelReopenRecovers(): TestResult = runComposeUiTest {
        rejectAllDaysThenCancelAndReopenWithRecoveredRules()
    }
}
