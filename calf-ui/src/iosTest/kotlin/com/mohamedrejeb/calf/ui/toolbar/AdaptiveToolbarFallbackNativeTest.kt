// NativeCmpKit (2026-11-04): real OS-selected public Material fallback, no native-slot absence proxy.
@file:OptIn(androidx.compose.ui.test.ExperimentalTestApi::class,
    com.mohamedrejeb.calf.ui.ExperimentalCalfUiApi::class)

package com.mohamedrejeb.calf.ui.toolbar

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.assertWidthIsEqualTo
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.dp
import com.mohamedrejeb.calf.ui.controls.AdaptiveControlBranch
import com.mohamedrejeb.calf.ui.controls.requireAdaptiveControlHost
import com.mohamedrejeb.calf.ui.navigation.UIKitUIBarButtonItem
import kotlin.test.Test
import kotlin.test.assertTrue

class AdaptiveToolbarFallbackNativeTest {
    @Test fun pre26EmptyAndPopulatedItemsRenderMaterialSlotsAndCallerPlacement() =
        fallback(AdaptiveControlBranch.Pre26, includePopulatedItems = true)

    @Test fun ios26EmptyItemsRenderMaterialSlotsAndCallerPlacement() =
        fallback(AdaptiveControlBranch.IOS26Plus, includePopulatedItems = false)

    private fun fallback(branch: AdaptiveControlBranch, includePopulatedItems: Boolean) {
        requireAdaptiveControlHost(branch)
        runComposeUiTest {
            val expanded = mutableStateOf(true)
            val revision = mutableStateOf(0)
            val items = mutableStateOf(emptyList<UIKitUIBarButtonItem>())
            var mainCompositions = 0; var leadingCompositions = 0; var trailingCompositions = 0
            setContent {
                MaterialTheme {
                    Column {
                        AdaptiveToolbar(expanded.value,
                            modifier = Modifier.testTag("toolbar")
                                .padding(start = 11.dp, top = 5.dp, end = 17.dp, bottom = 7.dp).width(240.dp),
                            iosItems = items.value,
                            leadingContent = { Text("Leading ${revision.value}", Modifier.testTag("leading"))
                                SideEffect { leadingCompositions++ } },
                            trailingContent = { Text("Trailing ${revision.value}", Modifier.testTag("trailing"))
                                SideEffect { trailingCompositions++ } },
                            content = { Text("Main ${revision.value}", Modifier.testTag("main"))
                                SideEffect { mainCompositions++ } })
                        // A separately allocated caller bottom row, not a root-level native overlay.
                        Box(Modifier.width(240.dp).height(32.dp).testTag("callerBottom"))
                    }
                }
            }
            for (populated in if (includePopulatedItems) listOf(false, true) else listOf(false)) {
                runOnIdle {
                    items.value = if (populated) listOf(UIKitUIBarButtonItem.title("Native fixture item")) else emptyList()
                    expanded.value = true
                    revision.value++
                }
                waitForIdle()
                onNodeWithTag("toolbar").assertWidthIsEqualTo(268.dp)
                onNodeWithTag("main").assertIsDisplayed().assertTextEquals("Main ${revision.value}")
                onNodeWithTag("leading").assertIsDisplayed().assertTextEquals("Leading ${revision.value}")
                onNodeWithTag("trailing").assertIsDisplayed().assertTextEquals("Trailing ${revision.value}")
                assertTrue(mainCompositions > 0 && leadingCompositions > 0 && trailingCompositions > 0,
                    "The real public fallback must compose all three supplied slots")
                val toolbarBounds = onNodeWithTag("toolbar").fetchSemanticsNode().boundsInRoot
                val bottomBounds = onNodeWithTag("callerBottom").fetchSemanticsNode().boundsInRoot
                assertTrue(toolbarBounds.bottom <= bottomBounds.top,
                    "Public modifier/insets must allocate space, not overlap the separately owned bottom row")
                val beforeCollapsed = mainCompositions
                runOnIdle { expanded.value = false; revision.value++ }
                waitForIdle()
                onNodeWithTag("main").assertIsDisplayed().assertTextEquals("Main ${revision.value}")
                assertTrue(mainCompositions > beforeCollapsed, "Collapsed fallback must keep current main content")
                runOnIdle { expanded.value = true; revision.value++ }
                waitForIdle()
                onNodeWithTag("leading").assertIsDisplayed().assertTextEquals("Leading ${revision.value}")
                onNodeWithTag("trailing").assertIsDisplayed().assertTextEquals("Trailing ${revision.value}")
                println("NATIVECMPKIT_ADAPTIVE_TOOLBAR_FALLBACK branch=${branch.label} populated=$populated " +
                    "mainCompositions=$mainCompositions leadingCompositions=$leadingCompositions " +
                    "trailingCompositions=$trailingCompositions callerPlacementVerified=true")
            }
        }
    }
}
