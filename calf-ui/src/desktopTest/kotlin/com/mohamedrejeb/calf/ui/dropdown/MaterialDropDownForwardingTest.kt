package com.mohamedrejeb.calf.ui.dropdown

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.ScrollState
import androidx.compose.foundation.layout.Box
import androidx.compose.material3.Text
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.*
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.DpOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.PopupProperties
import com.mohamedrejeb.calf.ui.ExperimentalCalfUiApi
import kotlinx.coroutines.runBlocking
import kotlin.test.*

@OptIn(ExperimentalTestApi::class, ExperimentalCalfUiApi::class)
class MaterialDropDownForwardingTest {
    @Test fun callerScrollStateControlsTheMaterialMenu() = runComposeUiTest {
        val scroll = ScrollState(0)
        setContent {
            Box {
                AdaptiveDropDown(expanded = true, onDismissRequest = {}, iosItems = emptyList(),
                    offset = DpOffset(12.dp, 8.dp), scrollState = scroll,
                    properties = PopupProperties(focusable = true, dismissOnClickOutside = false),
                    containerColor = Color.Yellow, tonalElevation = 0.dp, shadowElevation = 0.dp,
                    border = BorderStroke(2.dp, Color.Red)) {
                    repeat(100) { Text("Item $it", Modifier.testTag("item-$it")) }
                }
            }
        }
        waitForIdle()
        assertTrue(scroll.maxValue > 0)
        runOnIdle { runBlocking { scroll.scrollTo(scroll.maxValue) } }
        onNodeWithTag("item-99").assertIsDisplayed()
    }
}
