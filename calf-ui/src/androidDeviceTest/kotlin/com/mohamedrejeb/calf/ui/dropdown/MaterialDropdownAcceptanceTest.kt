// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.dropdown

import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.ComposeUiTest
import androidx.compose.ui.test.v2.runComposeUiTest
import kotlinx.coroutines.test.TestResult
import org.junit.Test
import org.junit.runner.RunWith
import androidx.test.ext.junit.runners.AndroidJUnit4

/** Real instrumented library popup windows; no sample or Robolectric. */
@RunWith(AndroidJUnit4::class)
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
