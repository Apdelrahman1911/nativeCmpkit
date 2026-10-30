// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.dropdown

import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.ComposeUiTest
import androidx.compose.ui.test.v2.runComposeUiTest
import kotlinx.coroutines.test.TestResult
import kotlin.test.Test

/** Real Material scene raster/input APIs, not an OS accessibility or native window certificate. */
@OptIn(ExperimentalTestApi::class)
class MaterialDropdownAcceptanceTest {
    @Test fun offsetAndRtlMutationsMoveTheActualPopup(): TestResult = runComposeUiTest {
        dropdownOffsetTracksLiveLtrAndRtlInputs()
    }
    @Test fun callerScrollStateReachesBothEndsOfTheActualLongMenu(): TestResult = runComposeUiTest {
        dropdownCallerScrollControlsActualLongContents()
    }
    @Test fun shapeColorBothElevationsAndBorderMatchActualMaterialPixels(): TestResult = runComposeUiTest {
        dropdownStylePixelsMatchTheIndependentMaterialCall()
    }
    @Test fun focusAndDismissalPropertiesControlActualBackAndPointerEvents(): TestResult = runComposeUiTest {
        dropdownFocusBackAndOutsidePoliciesControlRealEvents()
    }
}
