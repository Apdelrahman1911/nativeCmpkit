// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.dropdown

import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.ComposeUiTest
import androidx.compose.ui.test.v2.runComposeUiTest
import kotlinx.coroutines.test.TestResult
import kotlin.test.Test
import org.jetbrains.skiko.InternalSkikoApi
import org.jetbrains.skiko.wasm.awaitSkiko
import kotlin.js.unsafeCast

@OptIn(ExperimentalTestApi::class, InternalSkikoApi::class)
private fun runReadyDropdown(block: suspend ComposeUiTest.() -> Unit): TestResult =
    awaitSkiko.then { runComposeUiTest(block = block) }.unsafeCast<TestResult>()

/** Real Material scene raster/input APIs, not an OS accessibility or native window certificate. */
@OptIn(ExperimentalTestApi::class)
class MaterialDropdownAcceptanceTest {
    @Test fun offsetAndRtlMutationsMoveTheActualPopup(): TestResult = runReadyDropdown {
        dropdownOffsetTracksLiveLtrAndRtlInputs()
    }
    @Test fun callerScrollStateReachesBothEndsOfTheActualLongMenu(): TestResult = runReadyDropdown {
        dropdownCallerScrollControlsActualLongContents()
    }
    @Test fun shapeColorBothElevationsAndBorderMatchActualMaterialPixels(): TestResult = runReadyDropdown {
        dropdownStylePixelsMatchTheIndependentMaterialCall()
    }
    @Test fun focusAndDismissalPropertiesControlActualBackAndPointerEvents(): TestResult = runReadyDropdown {
        dropdownFocusBackAndOutsidePoliciesControlRealEvents()
    }
}
