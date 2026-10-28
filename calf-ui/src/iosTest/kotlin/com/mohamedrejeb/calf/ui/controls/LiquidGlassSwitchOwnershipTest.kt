package com.mohamedrejeb.calf.ui.controls

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.state.ToggleableState
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.click
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.swipe
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import com.mohamedrejeb.calf.ui.ExperimentalCalfUiApi
import com.mohamedrejeb.calf.ui.toggle.LiquidGlassSwitch
import com.mohamedrejeb.calf.ui.toggle.LiquidGlassSwitchDefaults
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Public library controls on the real iOS Compose/UIKit host, not a sample or substitute. */
@OptIn(ExperimentalTestApi::class, ExperimentalCalfUiApi::class)
class LiquidGlassSwitchOwnershipTest {
    @Test fun delayedOwnerUpdateRestoresAuthoritativeThumbBeforeApplyingTheProposal() = runComposeUiTest {
        val checked = mutableStateOf(false)
        var pending: Boolean? = null
        var calls = 0
        setContent {
            CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Ltr) {
                LiquidGlassSwitch(checked.value, { pending = it; calls++ }, Modifier.testTag("switch"),
                    thumbContent = { Box(Modifier.size(3.dp).testTag("thumb")) })
            }
        }
        val before = onNodeWithTag("thumb", useUnmergedTree = true).fetchSemanticsNode().boundsInRoot.center.x
        onNodeWithTag("switch").performTouchInput { swipe(center, center + Offset(60f, 0f), 150) }
        waitForIdle()
        assertEquals(1, calls)
        assertEquals(true, pending)
        assertFalse(checked.value, "The owner deliberately delays acceptance; the library is not the owner")
        assertEquals(ToggleableState.Off, onNodeWithTag("switch").fetchSemanticsNode().config[SemanticsProperties.ToggleableState])
        assertEquals(before, onNodeWithTag("thumb", useUnmergedTree = true).fetchSemanticsNode().boundsInRoot.center.x, .5f)

        runOnIdle { checked.value = pending!! }
        waitForIdle()
        val distance = with(density) { LiquidGlassSwitchDefaults.DragWidth.toPx() }
        assertTrue(checked.value)
        assertEquals(ToggleableState.On, onNodeWithTag("switch").fetchSemanticsNode().config[SemanticsProperties.ToggleableState])
        assertEquals(before + distance, onNodeWithTag("thumb", useUnmergedTree = true).fetchSemanticsNode().boundsInRoot.center.x, .5f)
        assertEquals(1, calls, "Applying the owner proposal must not emit another proposal")
    }

    @Test fun thumbAndBothTrackEndsProposeOnceAndThresholdReturnDoesNotCommit() = runComposeUiTest {
        val checked = mutableStateOf(false)
        var calls = 0
        setContent {
            CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Ltr) {
                LiquidGlassSwitch(checked.value, { checked.value = it; calls++ }, Modifier.testTag("switch"),
                    thumbContent = { Box(Modifier.size(3.dp).testTag("thumb")) })
            }
        }
        onNodeWithTag("thumb", useUnmergedTree = true).performTouchInput { click() }
        waitForIdle()
        assertTrue(checked.value)
        assertEquals(1, calls)
        onNodeWithTag("switch").performTouchInput { click(Offset(1f, centerY)) }
        waitForIdle()
        assertFalse(checked.value)
        assertEquals(2, calls)
        onNodeWithTag("switch").performTouchInput { click(Offset(width - 1f, centerY)) }
        waitForIdle()
        assertTrue(checked.value)
        assertEquals(3, calls)

        val onPosition = onNodeWithTag("thumb", useUnmergedTree = true).fetchSemanticsNode().boundsInRoot.center.x
        val distance = with(density) { LiquidGlassSwitchDefaults.DragWidth.toPx() }
        onNodeWithTag("switch").performTouchInput { down(center); moveBy(Offset(-width * 2f, 0f)) }
        waitForIdle()
        val crossed = onNodeWithTag("thumb", useUnmergedTree = true).fetchSemanticsNode().boundsInRoot.center.x
        assertTrue(crossed < onPosition - distance * .5f, "The actual thumb must cross the threshold; a no-op drag is not coverage")
        assertEquals(3, calls, "A live preview is not a committed owner update")
        assertTrue(checked.value)
        assertEquals(ToggleableState.On, onNodeWithTag("switch").fetchSemanticsNode().config[SemanticsProperties.ToggleableState])
        onNodeWithTag("switch").performTouchInput { moveBy(Offset(width * 2f, 0f)); up() }
        waitForIdle()
        assertEquals(3, calls, "Crossing then returning to the authoritative state must not propose a toggle")
        assertTrue(checked.value)
        assertEquals(ToggleableState.On, onNodeWithTag("switch").fetchSemanticsNode().config[SemanticsProperties.ToggleableState])
        assertEquals(onPosition, onNodeWithTag("thumb", useUnmergedTree = true).fetchSemanticsNode().boundsInRoot.center.x, .5f)
    }

    @Test fun disabledTapAndDragLeaveThumbAndToggleSemanticsUnchanged() = runComposeUiTest {
        var calls = 0
        setContent {
            CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Ltr) {
                LiquidGlassSwitch(true, { calls++ }, Modifier.testTag("switch"), enabled = false,
                    thumbContent = { Box(Modifier.size(3.dp).testTag("thumb")) })
            }
        }
        val before = onNodeWithTag("thumb", useUnmergedTree = true).fetchSemanticsNode().boundsInRoot.center.x
        assertTrue(onNodeWithTag("switch").fetchSemanticsNode().config.contains(SemanticsProperties.Disabled))
        onNodeWithTag("switch").performTouchInput {
            click(Offset(1f, centerY))
            swipe(center, center + Offset(-60f, 0f), 150)
        }
        waitForIdle()
        assertEquals(0, calls)
        val node = onNodeWithTag("switch").fetchSemanticsNode()
        assertTrue(node.config.contains(SemanticsProperties.Disabled))
        assertEquals(ToggleableState.On, node.config[SemanticsProperties.ToggleableState])
        assertEquals(before, onNodeWithTag("thumb", useUnmergedTree = true).fetchSemanticsNode().boundsInRoot.center.x, .5f)
    }
}
