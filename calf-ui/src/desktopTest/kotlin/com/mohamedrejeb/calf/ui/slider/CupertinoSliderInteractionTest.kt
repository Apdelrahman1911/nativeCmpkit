package com.mohamedrejeb.calf.ui.slider

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.interaction.DragInteraction
import androidx.compose.foundation.interaction.Interaction
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.PressInteraction
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.input.key.Key
import androidx.compose.ui.input.pointer.PointerEventPass
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.assertHeightIsAtLeast
import androidx.compose.ui.test.click
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onRoot
import androidx.compose.ui.test.performKeyInput
import androidx.compose.ui.test.performSemanticsAction
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.swipe
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import com.mohamedrejeb.calf.ui.internal.cancelScenePointerInput
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Real Compose rendering/input of the same Cupertino implementation called by the iOS actual. */
@OptIn(ExperimentalTestApi::class)
class CupertinoSliderInteractionTest {
    @Test fun negativeSetProgressUsesDiscreteStepsAndFinishesOnce() = runComposeUiTest {
        val value = mutableStateOf(-1f)
        var finished = 0
        setContent {
            CupertinoSlider(value.value, { value.value = it }, Modifier.width(240.dp).testTag("slider"),
                valueRange = -1f..1f, steps = 3, onValueChangeFinished = { finished++ })
        }
        onNodeWithTag("slider").performSemanticsAction(SemanticsActions.SetProgress) {
            assertTrue(it(-0.7f))
        }
        assertEquals(-0.5f, value.value)
        assertEquals(1, finished)
        onNodeWithTag("slider").performSemanticsAction(SemanticsActions.SetProgress) {
            assertFalse(it(-0.7f))
            assertFalse(it(Float.NaN))
        }
        assertEquals(1, finished)
    }

    @Test fun disabledSemanticAndPointerRequestsDoNotCallTheOwner() = runComposeUiTest {
        var changes = 0
        var finished = 0
        setContent {
            CupertinoSlider(0f, { changes++ }, Modifier.width(240.dp).testTag("slider"),
                enabled = false, onValueChangeFinished = { finished++ })
        }
        onNodeWithTag("slider").performSemanticsAction(SemanticsActions.SetProgress) {
            assertFalse(it(1f))
        }
        onNodeWithTag("slider").performTouchInput { click() }
        assertEquals(0, changes)
        assertEquals(0, finished)
    }

    @Test fun rangeStepsDirectionWidthAndCallbackReplacementAffectPointerInput() = runComposeUiTest {
        val range = mutableStateOf(0f..1f)
        val steps = mutableStateOf(0)
        val rtl = mutableStateOf(false)
        val width = mutableStateOf(240.dp)
        val useNewCallback = mutableStateOf(false)
        val value = mutableStateOf(0f)
        var oldCalls = 0
        var newCalls = 0
        setContent {
            CompositionLocalProvider(LocalLayoutDirection provides if (rtl.value) LayoutDirection.Rtl else LayoutDirection.Ltr) {
                val callback: (Float) -> Unit = if (useNewCallback.value) {
                    { value.value = it; newCalls++ }
                } else {
                    { value.value = it; oldCalls++ }
                }
                CupertinoSlider(value.value, callback, Modifier.width(width.value).testTag("slider"),
                    valueRange = range.value, steps = steps.value)
            }
        }
        onNodeWithTag("slider").performTouchInput { click(center) }
        assertEquals(0.5f, value.value)
        runOnIdle {
            range.value = -2f..2f
            steps.value = 3
            rtl.value = true
            width.value = 360.dp
            useNewCallback.value = true
        }
        onNodeWithTag("slider").performTouchInput { click(Offset(0f, centerY)) }
        assertEquals(2f, value.value)
        onNodeWithTag("slider").performTouchInput { click(center) }
        assertEquals(0f, value.value)
        assertEquals(1, oldCalls)
        assertEquals(2, newCalls)
        assertEquals(3, onNodeWithTag("slider").fetchSemanticsNode().config[SemanticsProperties.ProgressBarRangeInfo].steps)
    }

    @Test fun dragThenTapHasNoCompetingAnimationCallbacks() = runComposeUiTest {
        val value = mutableStateOf(0f)
        val requested = mutableListOf<Float>()
        var finished = 0
        setContent {
            CupertinoSlider(value.value, { value.value = it; requested += it }, Modifier.width(240.dp).testTag("slider"),
                steps = 3, onValueChangeFinished = { finished++ })
        }
        onNodeWithTag("slider").performTouchInput {
            swipe(Offset(0f, centerY), Offset(width.toFloat(), centerY), 200)
        }
        assertEquals(1f, value.value)
        onNodeWithTag("slider").performTouchInput { click(Offset(0f, centerY)) }
        waitForIdle()
        assertEquals(0f, value.value)
        assertEquals(2, finished)
        assertTrue(requested.all { it in setOf(0f, .25f, .5f, .75f, 1f) })
    }

    @Test fun pointerCancellationNeverFinishesAndPairsTheInteraction() = runComposeUiTest {
        val value = mutableStateOf(0f)
        val source = MutableInteractionSource()
        val interactions = mutableListOf<Interaction>()
        var finished = 0
        setContent {
            LaunchedEffect(source) { source.interactions.collect { interactions += it } }
            CupertinoSlider(value.value, { value.value = it }, Modifier.width(240.dp).testTag("slider"),
                interactionSource = source, onValueChangeFinished = { finished++ })
        }
        onNodeWithTag("slider").performTouchInput {
            down(center)
            moveBy(Offset(70f, 0f))
            cancel()
        }
        cancelScenePointerInput()
        waitForIdle()
        assertEquals(0, finished)
        val starts = interactions.filterIsInstance<DragInteraction.Start>()
        assertEquals(1, starts.size)
        assertEquals(1, interactions.filterIsInstance<DragInteraction.Cancel>().count { it.start === starts.single() },
            "A scene-cancelled drag must pair exactly once: $interactions")
        assertTrue(interactions.none { it is DragInteraction.Stop }, "Cancelled interaction sequence: $interactions")
    }

    @Test fun disablingDuringDragCancelsBeforePointerUp() = runComposeUiTest {
        val enabled = mutableStateOf(true)
        val value = mutableStateOf(0f)
        val source = MutableInteractionSource()
        val interactions = mutableListOf<Interaction>()
        var finished = 0
        setContent {
            LaunchedEffect(source) { source.interactions.collect { interactions += it } }
            CupertinoSlider(value.value, { value.value = it }, Modifier.width(240.dp).testTag("slider"),
                enabled = enabled.value, interactionSource = source, onValueChangeFinished = { finished++ })
        }
        onNodeWithTag("slider").performTouchInput { down(center); moveBy(Offset(60f, 0f)) }
        runOnIdle { enabled.value = false }
        val atDisable = value.value
        onNodeWithTag("slider").performTouchInput { moveBy(Offset(20f, 0f)); up() }
        waitForIdle()
        assertEquals(atDisable, value.value)
        assertEquals(0, finished)
        val start = interactions.filterIsInstance<DragInteraction.Start>().single()
        assertEquals(1, interactions.filterIsInstance<DragInteraction.Cancel>().count { it.start === start },
            "Disabling must cancel the active drag: $interactions")
        assertTrue(interactions.none { it is DragInteraction.Stop })
        runOnIdle { enabled.value = true }
        onNodeWithTag("slider").performTouchInput { click(Offset(0f, centerY)) }
        assertEquals(0f, value.value)
        assertEquals(1, finished)
    }

    @Test fun disposingAnActiveSliderPairsCancellationWithoutCompletion() = runComposeUiTest {
        val shown = mutableStateOf(true)
        val source = MutableInteractionSource()
        val interactions = mutableListOf<Interaction>()
        var finished = 0
        setContent {
            LaunchedEffect(source) { source.interactions.collect { interactions += it } }
            if (shown.value) {
                CupertinoSlider(0f, {}, Modifier.width(240.dp).testTag("slider"),
                    interactionSource = source, onValueChangeFinished = { finished++ })
            }
        }
        onNodeWithTag("slider").performTouchInput { down(center); moveBy(Offset(70f, 0f)) }
        runOnIdle { shown.value = false }
        onRoot().performTouchInput { up() }
        waitForIdle()
        val start = interactions.filterIsInstance<DragInteraction.Start>().single()
        assertEquals(1, interactions.filterIsInstance<DragInteraction.Cancel>().count { it.start === start },
            "Disposal must cancel the active drag: $interactions")
        assertTrue(interactions.none { it is DragInteraction.Stop })
        assertEquals(0, finished)
    }

    @Test fun parentConsumptionCancelsAnAlreadyStartedDrag() = runComposeUiTest {
        val consume = mutableStateOf(false)
        val source = MutableInteractionSource()
        val interactions = mutableListOf<Interaction>()
        var finished = 0
        setContent {
            LaunchedEffect(source) { source.interactions.collect { interactions += it } }
            Box(Modifier.pointerInput(Unit) {
                awaitPointerEventScope {
                    while (true) {
                        val event = awaitPointerEvent(PointerEventPass.Initial)
                        if (consume.value) event.changes.forEach { it.consume() }
                    }
                }
            }) {
                CupertinoSlider(0f, {}, Modifier.width(240.dp).testTag("slider"),
                    interactionSource = source, onValueChangeFinished = { finished++ })
            }
        }
        onNodeWithTag("slider").performTouchInput { down(center); moveBy(Offset(70f, 0f)) }
        runOnIdle { consume.value = true }
        onNodeWithTag("slider").performTouchInput { moveBy(Offset(-30f, 0f)); up() }
        waitForIdle()
        val start = interactions.filterIsInstance<DragInteraction.Start>().single()
        assertEquals(1, interactions.filterIsInstance<DragInteraction.Cancel>().count { it.start === start },
            "Consumed input must cancel the active drag: $interactions")
        assertTrue(interactions.none { it is DragInteraction.Stop })
        assertEquals(0, finished)
    }

    @Test fun interactionSourceReplacementCancelsTheOldPress() = runComposeUiTest {
        val first = MutableInteractionSource()
        val second = MutableInteractionSource()
        val source = mutableStateOf(first)
        val oldInteractions = mutableListOf<Interaction>()
        val newInteractions = mutableListOf<Interaction>()
        var finished = 0
        setContent {
            LaunchedEffect(Unit) { first.interactions.collect { oldInteractions += it } }
            LaunchedEffect(Unit) { second.interactions.collect { newInteractions += it } }
            CupertinoSlider(0f, {}, Modifier.width(240.dp).testTag("slider"),
                interactionSource = source.value, onValueChangeFinished = { finished++ })
        }
        onNodeWithTag("slider").performTouchInput { down(center) }
        runOnIdle { source.value = second }
        onNodeWithTag("slider").performTouchInput { up() }
        waitForIdle()
        assertEquals(0, finished)
        val press = oldInteractions.filterIsInstance<PressInteraction.Press>().single()
        assertTrue(oldInteractions.filterIsInstance<PressInteraction.Cancel>().any { it.press === press })
        onNodeWithTag("slider").performTouchInput { click() }
        waitForIdle()
        assertEquals(1, finished)
        assertEquals(1, newInteractions.filterIsInstance<PressInteraction.Press>().size)
        assertEquals(1, newInteractions.filterIsInstance<PressInteraction.Release>().size)
    }

    @Test fun verticalParentScrollDoesNotAdjustOrFinishTheSlider() = runComposeUiTest {
        var changes = 0
        var finished = 0
        setContent {
            Column(Modifier.height(250.dp).verticalScroll(rememberScrollState())) {
                CupertinoSlider(0f, { changes++ }, Modifier.width(240.dp).testTag("slider"),
                    onValueChangeFinished = { finished++ })
                Box(Modifier.height(1_000.dp))
            }
        }
        onNodeWithTag("slider").performTouchInput { swipe(center, center + Offset(0f, -180f), 200) }
        assertEquals(0, changes)
        assertEquals(0, finished)
    }

    @Test fun keyboardUsesDiscreteStepsAndOneCompletionPerKey() = runComposeUiTest {
        val value = mutableStateOf(0f)
        var finished = 0
        setContent {
            CupertinoSlider(value.value, { value.value = it }, Modifier.width(240.dp).testTag("slider"),
                valueRange = -1f..1f, steps = 3, onValueChangeFinished = { finished++ })
        }
        onNodeWithTag("slider").performSemanticsAction(SemanticsActions.RequestFocus) { it() }
        onNodeWithTag("slider").performKeyInput { keyDown(Key.DirectionRight); keyUp(Key.DirectionRight) }
        assertEquals(.5f, value.value)
        assertEquals(1, finished)
        onNodeWithTag("slider").performKeyInput { keyDown(Key.MoveHome); keyUp(Key.MoveHome) }
        assertEquals(-1f, value.value)
        assertEquals(2, finished)
    }

    @Test fun constantRangeNarrowAndUnboundedLayoutsAreFinite() = runComposeUiTest {
        var calls = 0
        setContent {
            Column {
                CupertinoSlider(2f, { calls++ }, Modifier.width(240.dp).testTag("constant"), valueRange = 2f..2f)
                CupertinoSlider(0f, { calls++ }, Modifier.width(8.dp).testTag("narrow"))
                Row(Modifier.horizontalScroll(rememberScrollState())) {
                    CupertinoSlider(0f, { calls++ }, Modifier.testTag("unbounded"))
                }
            }
        }
        onNodeWithTag("constant").assertHeightIsAtLeast(44.dp)
        onNodeWithTag("constant").performSemanticsAction(SemanticsActions.SetProgress) { assertFalse(it(9f)) }
        onNodeWithTag("narrow").performTouchInput { click() }
        assertTrue(onNodeWithTag("unbounded").fetchSemanticsNode().boundsInRoot.width in 1f..1_000f)
        assertEquals(0, calls)
    }
}
