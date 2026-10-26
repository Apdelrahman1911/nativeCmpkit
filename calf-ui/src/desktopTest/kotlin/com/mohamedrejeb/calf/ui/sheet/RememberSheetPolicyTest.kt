package com.mohamedrejeb.calf.ui.sheet

import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.SheetValue
import androidx.compose.runtime.*
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.v2.runComposeUiTest
import kotlinx.coroutines.runBlocking
import kotlin.test.*

@OptIn(ExperimentalMaterial3Api::class, ExperimentalTestApi::class)
class RememberSheetPolicyTest {
    @Test fun callbackReplacementPreservesStateButUsesLatestPolicy() = runComposeUiTest {
        var callsA = 0
        var callsB = 0
        var confirm by mutableStateOf<(SheetValue) -> Boolean>({ callsA++; false })
        lateinit var state: AdaptiveSheetState
        setContent { state = rememberAdaptiveSheetState(confirmValueChange = confirm) }
        waitForIdle()
        val first = state
        runOnIdle { confirm = { callsB++; false } }
        waitForIdle()
        assertSame(first, state)
        runOnIdle { runBlocking { state.hide() } }
        assertEquals(0, callsA)
        assertEquals(1, callsB)
        assertEquals(SheetValue.Hidden, state.currentValue)
    }
}
