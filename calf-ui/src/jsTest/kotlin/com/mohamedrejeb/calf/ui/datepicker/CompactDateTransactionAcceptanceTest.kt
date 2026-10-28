package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.ComposeUiTest
import androidx.compose.ui.test.v2.runComposeUiTest
import kotlinx.coroutines.test.TestResult
import org.jetbrains.skiko.InternalSkikoApi
import org.jetbrains.skiko.wasm.awaitSkiko
import kotlin.js.unsafeCast
import kotlin.test.Test

/** Import the real Skiko exports and await initialization before creating its raster surface. */
@OptIn(ExperimentalTestApi::class, InternalSkikoApi::class)
private fun runReadyBrowserTransaction(block: suspend ComposeUiTest.() -> Unit): TestResult =
    // Native Promise.then assimilates the returned test Promise, so assertions
    // and Compose cleanup complete before the outer test settles. The cast
    // describes that standard flattening; it does not drop or catch failures.
    awaitSkiko.then { runComposeUiTest(block = block) }.unsafeCast<TestResult>()

/** Returns the actual browser Promise; no runBlocking or unawaited assertions. */
@OptIn(ExperimentalTestApi::class)
class CompactDateTransactionAcceptanceTest {
    @Test fun capturedConfirmRevalidatesTheLatestRules(): TestResult = runReadyBrowserTransaction {
        rejectCapturedConfirmAfterRulesTighten()
    }
    @Test fun replacementOwnerYearRangeAndRuleStartAnIndependentTransaction(): TestResult = runReadyBrowserTransaction {
        replaceOwnerAndYearRangeWithoutTransplantingScratchState()
    }
    @Test fun nullInputClearCancelReopenAndConfirmRemainTransactional(): TestResult = runReadyBrowserTransaction {
        clearActualInputThenCancelReopenAndCommitNull()
    }
    @Test fun noSelectableDateRejectsCommitAndCancelReopenRecovers(): TestResult = runReadyBrowserTransaction {
        rejectAllDaysThenCancelAndReopenWithRecoveredRules()
    }
}
