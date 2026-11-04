// NativeCmpKit (2026-11-04): public adaptive slider contracts on both real OS branches.
@file:OptIn(androidx.compose.ui.test.ExperimentalTestApi::class)

package com.mohamedrejeb.calf.ui.slider

import androidx.compose.foundation.interaction.DragInteraction
import androidx.compose.foundation.interaction.Interaction
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.PressInteraction
import androidx.compose.foundation.layout.width
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.ComposeUiTest
import androidx.compose.ui.test.click
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performSemanticsAction
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.swipe
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import com.mohamedrejeb.calf.ui.controls.AdaptiveControlBranch
import com.mohamedrejeb.calf.ui.controls.requireAdaptiveControlHost
import kotlin.math.abs
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Real public AdaptiveSlider calls; selecting Cupertino directly on iOS26 is not pre26 coverage. */
class AdaptiveSliderNativeMatrixTest {
    @Test fun pre26PublicStepsTapDragAndAccessibilityMatrix() = matrix(AdaptiveControlBranch.Pre26)
    @Test fun ios26PublicStepsTapDragAndAccessibilityMatrix() = matrix(AdaptiveControlBranch.IOS26Plus)
    @Test fun pre26PublicNegativeStepsAreRejected() = rejectsNegativeSteps(AdaptiveControlBranch.Pre26)
    @Test fun ios26PublicNegativeStepsAreRejected() = rejectsNegativeSteps(AdaptiveControlBranch.IOS26Plus)

    private fun matrix(branch: AdaptiveControlBranch) {
        requireAdaptiveControlHost(branch)
        for (steps in listOf(0, 1, 3)) {
            for (range in listOf(-2f..2f, 4f..12f)) {
                for (direction in listOf(LayoutDirection.Ltr, LayoutDirection.Rtl)) {
                    row(branch, steps, range, direction)
                }
            }
        }
    }

    private fun row(branch: AdaptiveControlBranch, steps: Int,
        range: ClosedFloatingPointRange<Float>, direction: LayoutDirection) = runComposeUiTest {
        val label = "${branch.label}/steps=$steps/range=${range.start}..${range.endInclusive}/$direction"
        val span = range.endInclusive - range.start
        val midpoint = range.start + span / 2f
        val value = mutableStateOf(midpoint)
        val requested = mutableListOf<Float>()
        val source = MutableInteractionSource()
        val events = mutableListOf<Interaction>()
        var finished = 0
        setContent {
            LaunchedEffect(source) { source.interactions.collect { events += it } }
            CompositionLocalProvider(LocalLayoutDirection provides direction) {
                AdaptiveSlider(value.value, { value.value = it; requested += it },
                    Modifier.width(240.dp).testTag("slider"), valueRange = range, steps = steps,
                    onValueChangeFinished = { finished++ }, interactionSource = source)
            }
        }
        assertProgress(range, steps, midpoint, label)

        // Clamped physical ends and the actual center are shared by both thumb geometries.
        tapEnd(direction, minimum = true)
        assertEquals(range.start, value.value, label)
        assertEquals(1, requested.size, label); assertEquals(1, finished, label)
        waitUntil(timeoutMillis = 5_000) {
            events.filterIsInstance<PressInteraction.Press>().size == 1 &&
                events.filterIsInstance<PressInteraction.Release>().size == 1
        }
        val tapPress = events.filterIsInstance<PressInteraction.Press>().single()
        assertEquals(1, events.filterIsInstance<PressInteraction.Release>().count { it.press === tapPress }, label)
        tapEnd(direction, minimum = false)
        assertEquals(range.endInclusive, value.value, label)
        assertEquals(2, requested.size, label); assertEquals(2, finished, label)
        onNodeWithTag("slider").performTouchInput { click(center) }
        waitForIdle()
        assertTrue(abs(midpoint - value.value) <= .00001f, "$label center tap")
        assertEquals(3, requested.size, label); assertEquals(3, finished, label)
        tapEnd(direction, minimum = true)
        assertEquals(range.start, value.value, label)

        // Exact first-interval ties choose the greater grid point; continuous input stays continuous.
        val target = range.start + span * if (steps == 0) .375f else .5f / (steps + 1)
        val expected = range.start + span * if (steps == 0) .375f else 1f / (steps + 1)
        val beforeSemantic = requested.size
        val finishesBeforeSemantic = finished
        onNodeWithTag("slider").performSemanticsAction(SemanticsActions.SetProgress) { assertTrue(it(target), label) }
        waitForIdle()
        assertEquals(expected, value.value, label)
        assertEquals(beforeSemantic + 1, requested.size, label)
        assertEquals(finishesBeforeSemantic + 1, finished, label)
        assertProgress(range, steps, expected, label)
        onNodeWithTag("slider").performSemanticsAction(SemanticsActions.SetProgress) {
            assertFalse(it(target), "$label unchanged proposal")
            assertFalse(it(Float.NaN), "$label NaN")
            assertFalse(it(Float.POSITIVE_INFINITY), "$label infinity")
        }
        assertEquals(beforeSemantic + 1, requested.size, label)
        assertEquals(finishesBeforeSemantic + 1, finished, label)
        onNodeWithTag("slider").performSemanticsAction(SemanticsActions.SetProgress) {
            assertTrue(it(range.start - span), "$label lower clamp")
        }
        waitForIdle()
        assertEquals(range.start, value.value, label)
        onNodeWithTag("slider").performSemanticsAction(SemanticsActions.SetProgress) {
            assertTrue(it(range.endInclusive + span), "$label upper clamp")
        }
        waitForIdle()
        assertEquals(range.endInclusive, value.value, label)
        assertEquals(beforeSemantic + 3, requested.size, label)
        assertEquals(finishesBeforeSemantic + 3, finished, label)

        tapEnd(direction, minimum = true)
        val beforeDrag = requested.size
        val finishesBeforeDrag = finished
        // Always finish injected gestures before assertions; no held-pointer teardown workaround.
        onNodeWithTag("slider").performTouchInput {
            val left = Offset(1f, centerY)
            val right = Offset(width - 1f, centerY)
            swipe(if (direction == LayoutDirection.Rtl) right else left,
                if (direction == LayoutDirection.Rtl) left else right, durationMillis = 240)
        }
        waitForIdle()
        waitUntil(timeoutMillis = 5_000) {
            events.filterIsInstance<DragInteraction.Start>().size == 1 &&
                events.filterIsInstance<DragInteraction.Stop>().size == 1
        }
        assertTrue(requested.size > beforeDrag, "$label drag must publish real input")
        assertEquals(range.endInclusive, value.value, "$label drag endpoint")
        assertEquals(finishesBeforeDrag + 1, finished, "$label drag completion")
        val drag = events.filterIsInstance<DragInteraction.Start>().single()
        assertEquals(1, events.filterIsInstance<DragInteraction.Stop>().count { it.start === drag }, label)
        assertTrue(events.filterIsInstance<DragInteraction.Cancel>().none { it.start === drag }, label)
        assertTrue(requested.all { it.isFinite() && it in range }, "$label every actual callback is bounded")
        if (steps > 0) {
            val allowed = (0..steps + 1).map { range.start + span * it.toFloat() / (steps + 1) }
            assertTrue(requested.all { it in allowed }, "$label every tap/drag/semantic callback snaps: $requested")
        }
        assertProgress(range, steps, range.endInclusive, label)
        println("NATIVECMPKIT_ADAPTIVE_SLIDER_ROW branch=${branch.label} steps=$steps " +
            "negative=${range.start < 0f} rtl=${direction == LayoutDirection.Rtl} " +
            "callbacks=${requested.size} finished=$finished dragPaired=true")
    }

    private fun ComposeUiTest.tapEnd(direction: LayoutDirection, minimum: Boolean) {
        onNodeWithTag("slider").performTouchInput {
            val right = minimum == (direction == LayoutDirection.Rtl)
            click(Offset(if (right) width - 1f else 1f, centerY))
        }
        waitForIdle()
    }

    private fun ComposeUiTest.assertProgress(range: ClosedFloatingPointRange<Float>, steps: Int,
        value: Float, label: String) {
        val info = onNodeWithTag("slider").fetchSemanticsNode().config[SemanticsProperties.ProgressBarRangeInfo]
        assertEquals(range, info.range, label); assertEquals(steps, info.steps, label)
        assertTrue(abs(value - info.current) <= .00001f, "$label actual progress value")
    }

    private fun rejectsNegativeSteps(branch: AdaptiveControlBranch) {
        requireAdaptiveControlHost(branch)
        val failure = assertFailsWith<IllegalArgumentException> {
            runComposeUiTest {
                setContent { AdaptiveSlider(.5f, {}, Modifier.width(240.dp), steps = -1) }
                waitForIdle()
            }
        }
        assertEquals("steps should be >= 0", failure.message,
            "Only the public invalid-steps contract, not a host/setup error, satisfies this test")
    }
}
