package com.mohamedrejeb.calf.ui.controls

import androidx.compose.foundation.interaction.DragInteraction
import androidx.compose.foundation.interaction.Interaction
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.state.ToggleableState
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.assertHeightIsAtLeast
import androidx.compose.ui.test.click
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performSemanticsAction
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.swipe
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import com.mohamedrejeb.calf.ui.ExperimentalCalfUiApi
import com.mohamedrejeb.calf.ui.internal.cancelScenePointerInput
import com.mohamedrejeb.calf.ui.slider.LiquidGlassSliderDefaults
import com.mohamedrejeb.calf.ui.slider.LiquidGlassSliderImpl
import com.mohamedrejeb.calf.ui.toggle.LiquidGlassSwitch
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Direct library control tests on the iOS Compose runtime, not a sample or replacement widget. */
@OptIn(ExperimentalTestApi::class, ExperimentalCalfUiApi::class)
class LiquidGlassControlTest {
    @Test fun sliderNegativeStepsAccessibilityAndCallbackReplacement() = runComposeUiTest {
        val value = mutableStateOf(-1f)
        val useNewCallback = mutableStateOf(false)
        var oldCalls = 0
        var newCalls = 0
        var finished = 0
        val source = MutableInteractionSource()
        setContent {
            LiquidGlassSliderImpl(
                value = value.value,
                onValueChange = if (useNewCallback.value) {
                    { value.value = it; newCalls++ }
                } else {
                    { value.value = it; oldCalls++ }
                },
                modifier = Modifier.width(240.dp).testTag("slider"), enabled = true,
                valueRange = -1f..1f, steps = 3, onValueChangeFinished = { finished++ },
                colors = LiquidGlassSliderDefaults.colors(), interactionSource = source,
            )
        }
        onNodeWithTag("slider").assertHeightIsAtLeast(44.dp)
        onNodeWithTag("slider").performSemanticsAction(SemanticsActions.SetProgress) { assertTrue(it(-.7f)) }
        assertEquals(-.5f, value.value)
        runOnIdle { useNewCallback.value = true }
        onNodeWithTag("slider").performSemanticsAction(SemanticsActions.SetProgress) { assertTrue(it(.7f)) }
        assertEquals(.5f, value.value)
        assertEquals(1, oldCalls)
        assertEquals(1, newCalls)
        assertEquals(2, finished)
    }

    @Test fun sliderRekeysRangeStepsDirectionGeometryAndEnabled() = runComposeUiTest {
        val value = mutableStateOf(0f)
        val range = mutableStateOf(0f..1f)
        val steps = mutableStateOf(0)
        val rtl = mutableStateOf(false)
        val width = mutableStateOf(240.dp)
        val enabled = mutableStateOf(true)
        var finished = 0
        val source = MutableInteractionSource()
        setContent {
            CompositionLocalProvider(LocalLayoutDirection provides if (rtl.value) LayoutDirection.Rtl else LayoutDirection.Ltr) {
                LiquidGlassSliderImpl(value.value, { value.value = it }, Modifier.width(width.value).testTag("slider"),
                    enabled.value, range.value, steps.value, { finished++ }, LiquidGlassSliderDefaults.colors(), source)
            }
        }
        onNodeWithTag("slider").performTouchInput { click() }
        assertEquals(.5f, value.value)
        runOnIdle { range.value = -2f..2f; steps.value = 3; rtl.value = true; width.value = 360.dp }
        onNodeWithTag("slider").performTouchInput { click(Offset(0f, centerY)) }
        assertEquals(2f, value.value)
        onNodeWithTag("slider").performTouchInput { down(center); moveBy(Offset(-60f, 0f)) }
        runOnIdle { enabled.value = false }
        val atDisable = value.value
        onNodeWithTag("slider").performTouchInput { moveBy(Offset(-30f, 0f)); up() }
        onNodeWithTag("slider").performSemanticsAction(SemanticsActions.SetProgress) { assertFalse(it(0f)) }
        assertEquals(atDisable, value.value)
        assertEquals(2, finished)
    }

    @Test fun sliderCancelPairsItsInteractionWithoutCompletion() = runComposeUiTest {
        val source = MutableInteractionSource()
        val interactions = mutableListOf<Interaction>()
        var finished = 0
        setContent {
            LaunchedEffect(source) { source.interactions.collect { interactions += it } }
            LiquidGlassSliderImpl(0f, {}, Modifier.width(240.dp).testTag("slider"), true, 0f..1f, 0,
                { finished++ }, LiquidGlassSliderDefaults.colors(), source)
        }
        onNodeWithTag("slider").performTouchInput { down(center); moveBy(Offset(60f, 0f)); cancel() }
        cancelScenePointerInput()
        waitForIdle()
        assertEquals(0, finished)
        val start = interactions.filterIsInstance<DragInteraction.Start>().single()
        assertEquals(1, interactions.filterIsInstance<DragInteraction.Cancel>().count { it.start === start },
            "A scene-cancelled drag must pair exactly once: $interactions")
        assertTrue(interactions.none { it is DragInteraction.Stop }, "Cancelled interaction sequence: $interactions")
    }

    @Test fun switchReadOnlyHasStateButNoToggleActionOrEnglishDescription() = runComposeUiTest {
        setContent { LiquidGlassSwitch(false, null, Modifier.testTag("switch")) }
        val node = onNodeWithTag("switch").fetchSemanticsNode()
        assertEquals(ToggleableState.Off, node.config[SemanticsProperties.ToggleableState])
        assertFalse(node.config.contains(SemanticsActions.OnClick))
        assertFalse(node.config.contains(SemanticsProperties.StateDescription))
        onNodeWithTag("switch").assertHeightIsAtLeast(44.dp)
        onNodeWithTag("switch").performTouchInput { click(); swipe(center, center + Offset(60f, 0f), 150) }
        assertEquals(ToggleableState.Off, onNodeWithTag("switch").fetchSemanticsNode().config[SemanticsProperties.ToggleableState])
    }

    @Test fun switchFullTrackTapAndSemanticActionEachProposeOnce() = runComposeUiTest {
        val checked = mutableStateOf(false)
        var calls = 0
        setContent {
            LiquidGlassSwitch(checked.value, { checked.value = it; calls++ }, Modifier.testTag("switch"),
                thumbContent = { Box(Modifier.size(3.dp).testTag("thumbContent")) })
        }
        onNodeWithTag("thumbContent", useUnmergedTree = true).fetchSemanticsNode()
        onNodeWithTag("switch").performTouchInput { click(Offset(width - 2f, centerY)) }
        assertTrue(checked.value)
        onNodeWithTag("switch").performClick()
        assertFalse(checked.value)
        assertEquals(2, calls)
    }

    @Test fun rejectingSwitchOwnerRetainsVisualAndSemanticStateAfterDrag() = runComposeUiTest {
        var calls = 0
        setContent {
            LiquidGlassSwitch(false, { calls++ }, Modifier.testTag("switch"),
                thumbContent = { Box(Modifier.size(3.dp).testTag("thumb")) })
        }
        val before = onNodeWithTag("thumb", useUnmergedTree = true).fetchSemanticsNode().boundsInRoot.center.x
        onNodeWithTag("switch").performTouchInput { swipe(center, center + Offset(60f, 0f), 150) }
        waitForIdle()
        assertEquals(1, calls)
        assertEquals(ToggleableState.Off, onNodeWithTag("switch").fetchSemanticsNode().config[SemanticsProperties.ToggleableState])
        val after = onNodeWithTag("thumb", useUnmergedTree = true).fetchSemanticsNode().boundsInRoot.center.x
        assertEquals(before, after, absoluteTolerance = .5f)
    }

    @Test fun switchPointerCancelAndVerticalScrollCannotCommit() = runComposeUiTest {
        var calls = 0
        setContent {
            Column(Modifier.height(250.dp).verticalScroll(rememberScrollState())) {
                LiquidGlassSwitch(false, { calls++ }, Modifier.testTag("switch"))
                Box(Modifier.height(1_000.dp))
            }
        }
        onNodeWithTag("switch").performTouchInput { down(center); moveBy(Offset(45f, 0f)); cancel() }
        cancelScenePointerInput()
        onNodeWithTag("switch").performTouchInput { swipe(center, center + Offset(0f, -150f), 150) }
        assertEquals(0, calls)
    }

    @Test fun externalCheckedOrDisabledChangeCancelsAnActiveSwitchDrag() = runComposeUiTest {
        val checked = mutableStateOf(false)
        val enabled = mutableStateOf(true)
        var calls = 0
        setContent { LiquidGlassSwitch(checked.value, { calls++ }, Modifier.testTag("switch"), enabled = enabled.value) }
        onNodeWithTag("switch").performTouchInput { down(center); moveBy(Offset(40f, 0f)) }
        runOnIdle { checked.value = true }
        onNodeWithTag("switch").performTouchInput { up() }
        assertEquals(0, calls)
        assertEquals(ToggleableState.On, onNodeWithTag("switch").fetchSemanticsNode().config[SemanticsProperties.ToggleableState])
        onNodeWithTag("switch").performTouchInput { down(center); moveBy(Offset(-40f, 0f)) }
        runOnIdle { enabled.value = false }
        onNodeWithTag("switch").performTouchInput { up() }
        assertEquals(0, calls)
    }

    @Test fun cancellationAcceptanceSecondPointerHandoffCommitsOnlyAtTheFinalUp() = runComposeUiTest {
        val checked = mutableStateOf(false)
        val interactions = mutableListOf<Interaction>()
        val source = MutableInteractionSource()
        var calls = 0
        setContent {
            LaunchedEffect(source) { source.interactions.collect { interactions += it } }
            LiquidGlassSwitch(checked.value, { checked.value = it; calls++ }, Modifier.testTag("switch"),
                interactionSource = source)
        }
        onNodeWithTag("switch").performTouchInput {
            down(pointerId = 0, position = center)
            moveBy(Offset(60f, 0f))
            down(pointerId = 1, position = center)
            up(pointerId = 0)
        }
        waitForIdle()
        assertEquals(0, calls, "Removing the primary pointer must not finish while its replacement is down")
        assertFalse(checked.value)
        val start = interactions.filterIsInstance<DragInteraction.Start>().single()
        assertTrue(interactions.none { it is DragInteraction.Stop || it is DragInteraction.Cancel })

        onNodeWithTag("switch").performTouchInput { up(pointerId = 1) }
        waitForIdle()

        assertEquals(1, calls, "The successful handoff must commit exactly once, not once per pointer")
        assertTrue(checked.value)
        assertEquals(1, interactions.filterIsInstance<DragInteraction.Stop>().count { it.start === start })
        assertTrue(interactions.none { it is DragInteraction.Cancel })
    }

    @Test fun cancellationAcceptanceDisposalCancelsTheDragAndCannotToggleTheReplacement() = runComposeUiTest {
        val visible = mutableStateOf(true)
        val checked = mutableStateOf(false)
        val source = MutableInteractionSource()
        val interactions = mutableListOf<Interaction>()
        var calls = 0
        setContent {
            LaunchedEffect(source) { source.interactions.collect { interactions += it } }
            Box(Modifier.size(200.dp).testTag("container")) {
                if (visible.value) {
                    LiquidGlassSwitch(checked.value, { checked.value = it; calls++ }, Modifier.testTag("switch"),
                        interactionSource = source)
                }
            }
        }
        onNodeWithTag("switch").performTouchInput { down(center); moveBy(Offset(60f, 0f)) }
        waitForIdle()
        val start = interactions.filterIsInstance<DragInteraction.Start>().single()
        runOnIdle { visible.value = false }
        waitForIdle()
        assertEquals(0, calls)
        assertFalse(checked.value)
        assertEquals(1, interactions.filterIsInstance<DragInteraction.Cancel>().count { it.start === start })
        assertTrue(interactions.none { it is DragInteraction.Stop })

        runOnIdle { visible.value = true }
        onNodeWithTag("container").performTouchInput { up() }
        waitForIdle()
        assertEquals(0, calls, "A stale up after disposal cannot activate the new switch owner")
        assertFalse(checked.value)

        onNodeWithTag("switch").performTouchInput { click() }
        waitForIdle()
        assertEquals(1, calls, "The replacement still accepts one fresh tap after stale input is drained")
        assertTrue(checked.value)
        assertEquals(1, interactions.filterIsInstance<DragInteraction.Cancel>().count { it.start === start })
    }
}
