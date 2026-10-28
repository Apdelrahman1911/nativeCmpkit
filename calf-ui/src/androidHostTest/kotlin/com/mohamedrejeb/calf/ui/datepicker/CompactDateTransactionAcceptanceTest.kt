package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.v2.runComposeUiTest
import kotlinx.coroutines.test.TestResult
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/** Real production Android/Compose code in Robolectric, not a device result. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
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
