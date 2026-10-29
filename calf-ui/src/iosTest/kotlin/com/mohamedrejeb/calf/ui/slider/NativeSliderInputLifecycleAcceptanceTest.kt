// Modified for NativeCmpKit (2026-10-29): shared real native slider input/ownership acceptance.
@file:OptIn(androidx.compose.ui.test.ExperimentalTestApi::class)

package com.mohamedrejeb.calf.ui.slider

import androidx.compose.foundation.interaction.DragInteraction
import androidx.compose.foundation.interaction.Interaction
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsDraggedAsState
import androidx.compose.foundation.layout.width
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.click
import androidx.compose.ui.test.ComposeUiTest
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performSemanticsAction
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.swipe
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import com.mohamedrejeb.calf.ui.internal.cancelScenePointerInput
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Both production renderers, real Compose input and interaction flows on the UIKit host.
 * Direct Cupertino execution does not certify adaptive pre-26 OS selection or physical input.
 */
class NativeSliderInputLifecycleAcceptanceTest {
    @Test fun liquidEnabledAndLiveCallbacksFollowOnlyTheCurrentGestureOwner() = enabledAndCallbacks(Renderer.Liquid)
    @Test fun cupertinoEnabledAndLiveCallbacksFollowOnlyTheCurrentGestureOwner() = enabledAndCallbacks(Renderer.Cupertino)
    @Test fun liquidEveryStructuralInputChangeCancelsOnlyTheOldInteraction() = structuralReplacement(Renderer.Liquid)
    @Test fun cupertinoEveryStructuralInputChangeCancelsOnlyTheOldInteraction() = structuralReplacement(Renderer.Cupertino)
    @Test fun liquidTapDragOppositeTapAndCancellationHaveNoPendingWriter() = tapDragCancellation(Renderer.Liquid)
    @Test fun cupertinoTapDragOppositeTapAndCancellationHaveNoPendingWriter() = tapDragCancellation(Renderer.Cupertino)

    private fun enabledAndCallbacks(renderer: Renderer) = runComposeUiTest {
        var enabled by mutableStateOf(false)
        var value by mutableStateOf(.25f)
        var useCurrentCallback by mutableStateOf(false)
        val source = MutableInteractionSource()
        val interactions = mutableListOf<Interaction>()
        var oldChanges = 0; var currentChanges = 0
        var oldFinished = 0; var currentFinished = 0
        setContent {
            LaunchedEffect(source) { source.interactions.collect { interactions += it } }
            renderer.control(value, if (useCurrentCallback) {
                { value = it; currentChanges++ }
            } else { { value = it; oldChanges++ } }, enabled = enabled,
                finished = if (useCurrentCallback) { { currentFinished++ } } else { { oldFinished++ } },
                source = source)
        }
        onNodeWithTag("slider").performTouchInput { click() }
        onNodeWithTag("slider").performSemanticsAction(SemanticsActions.SetProgress) { assertFalse(it(1f)) }
        assertEquals(.25f, value); assertEquals(0, oldChanges); assertEquals(0, oldFinished)
        runOnIdle { enabled = true }
        onNodeWithTag("slider").performTouchInput { click(Offset(width - 2f, centerY)) }
        assertEquals(1f, value); assertEquals(1, oldChanges); assertEquals(1, oldFinished)
        runOnIdle { enabled = false }
        onNodeWithTag("slider").performTouchInput { click(Offset(2f, centerY)) }
        assertEquals(1f, value); assertEquals(1, oldChanges); assertEquals(1, oldFinished)

        runOnIdle { enabled = true }
        onNodeWithTag("slider").performTouchInput {
            down(Offset(width - 2f, centerY)); moveBy(Offset(-width * .55f, 0f))
        }
        waitForIdle()
        val start = interactions.filterIsInstance<DragInteraction.Start>().single()
        assertTrue(oldChanges > 1, "A live drag must actually publish before ownership checks")
        val oldChangesAtReplacement = oldChanges
        runOnIdle { useCurrentCallback = true }
        onNodeWithTag("slider").performTouchInput { moveBy(Offset(-width * .1f, 0f)) }
        waitForIdle()
        assertEquals(oldChangesAtReplacement, oldChanges)
        assertTrue(currentChanges > 0, "An unchanged active gesture must use its current callback")
        assertTrue(interactions.none { it is DragInteraction.Cancel || it is DragInteraction.Stop })
        runOnIdle { enabled = false }
        val changesAtDisable = currentChanges
        val valueAtDisable = value
        onNodeWithTag("slider").performTouchInput { moveBy(Offset(25f, 0f)); up() }
        waitForIdle()
        assertEquals(valueAtDisable, value); assertEquals(changesAtDisable, currentChanges)
        assertEquals(1, oldFinished); assertEquals(0, currentFinished)
        assertEquals(1, interactions.filterIsInstance<DragInteraction.Cancel>().count { it.start === start })
        assertTrue(interactions.none { it is DragInteraction.Stop })

        runOnIdle { enabled = true }
        onNodeWithTag("slider").performTouchInput { click(Offset(2f, centerY)) }
        waitForIdle()
        assertEquals(0f, value); assertEquals(changesAtDisable + 1, currentChanges)
        assertEquals(1, currentFinished); assertEquals(1, oldFinished)
        assertEquals(oldChangesAtReplacement, oldChanges)
    }

    private fun structuralReplacement(renderer: Renderer) = runComposeUiTest {
        var value by mutableStateOf(0f)
        var range by mutableStateOf(0f..1f)
        var steps by mutableStateOf(0)
        var widthDp by mutableStateOf(240.dp)
        var density by mutableStateOf(Density(1f))
        var direction by mutableStateOf(LayoutDirection.Ltr)
        val first = MutableInteractionSource(); val second = MutableInteractionSource()
        var source by mutableStateOf(first)
        val firstEvents = mutableListOf<Interaction>(); val secondEvents = mutableListOf<Interaction>()
        var changes = 0; var finished = 0; var observedDragging = false
        structuralPhase(renderer, 0, "before-content")
        setContent {
            LaunchedEffect(first) { first.interactions.collect { firstEvents += it } }
            LaunchedEffect(second) { second.interactions.collect { secondEvents += it } }
            val dragging by source.collectIsDraggedAsState()
            SideEffect { observedDragging = dragging }
            CompositionLocalProvider(LocalDensity provides density, LocalLayoutDirection provides direction) {
                renderer.control(value, { value = it; changes++ }, range = range, steps = steps,
                    width = widthDp, source = source, finished = { finished++ })
            }
        }
        structuralPhase(renderer, 0, "content-installed")
        val changesToContract = listOf<Pair<String, () -> Unit>>(
            "measured width" to { widthDp = 360.dp },
            "density and thumb geometry" to { density = Density(2f, 1.5f) },
            "RTL direction" to { direction = LayoutDirection.Rtl },
            "range" to { range = -2f..2f },
            "steps" to { steps = 3 },
            "interaction source" to { source = second },
        )
        for ((axisIndex, contractChange) in changesToContract.withIndex()) {
            val (name, replace) = contractChange
            val axis = axisIndex + 1
            structuralPhase(renderer, axis, "before-reset")
            runOnIdle { value = (range.start + range.endInclusive) / 2f }
            structuralPhase(renderer, axis, "reset")
            val events = if (source === first) firstEvents else secondEvents
            val changesBeforeDrag = changes
            var pointerOutstanding = false
            try {
                structuralPhase(renderer, axis, "before-drag")
                onNodeWithTag("slider").performTouchInput {
                    down(center); pointerOutstanding = true; moveBy(Offset(width * .4f, 0f))
                }
                waitForIdle()
                // Scene idle alone does not flush an asynchronously collected
                // interaction and its SideEffect. Require the actual live
                // observer; timing cannot substitute for this positive witness.
                waitUntil(timeoutMillis = 5_000) {
                    observedDragging && changes > changesBeforeDrag &&
                        events.any { it is DragInteraction.Start }
                }
                structuralPhase(renderer, axis, "dragged")
                val starts = events.filterIsInstance<DragInteraction.Start>()
                // Observe before assertions: an assertion with a held pointer must
                // remain visible even when Compose's subsequent teardown is stuck.
                println("NATIVECMPKIT_SLIDER_DRAG renderer=${renderer.name} axis=$axis " +
                    "started=${starts.isNotEmpty()} changed=${changes > changesBeforeDrag} observed=$observedDragging")
                val start = starts.last()
                assertTrue(changes > changesBeforeDrag, "$name must replace an actual live input session")
                assertTrue(observedDragging)
                val changesBeforeReplacement = changes; val finishesBeforeReplacement = finished
                structuralPhase(renderer, axis, "before-replace")
                runOnIdle { replace() }
                waitForIdle()
                structuralPhase(renderer, axis, "replaced")
                onNodeWithTag("slider").performTouchInput {
                    moveBy(Offset(-15f, 0f)); up(); pointerOutstanding = false
                }
                waitForIdle()
                waitUntil(timeoutMillis = 5_000) {
                    !observedDragging && events.filterIsInstance<DragInteraction.Cancel>()
                        .count { it.start === start } == 1
                }
                structuralPhase(renderer, axis, "stale-released")
                assertEquals(changesBeforeReplacement, changes, "$name cannot leave an obsolete writer")
                assertEquals(finishesBeforeReplacement, finished, "$name cancellation is not completion")
                assertEquals(1, events.filterIsInstance<DragInteraction.Cancel>().count { it.start === start }, name)
                assertTrue(events.filterIsInstance<DragInteraction.Stop>().none { it.start === start }, name)
                assertFalse(observedDragging, "$name must clear the actual dragged-state observer")
                structuralPhase(renderer, axis, "cancellation-verified")
                // A discrete RTL drag can already reach range.start. Reset only after proving
                // stale-input rejection, so the fresh tap must genuinely change current state.
                runOnIdle { value = (range.start + range.endInclusive) / 2f }
                waitForIdle()
                structuralPhase(renderer, axis, "fresh-reset")
                assertEquals(changesBeforeReplacement, changes, "$name hoisted reset is not an input callback")
                assertEquals(finishesBeforeReplacement, finished, "$name hoisted reset is not input completion")
                onNodeWithTag("slider").performTouchInput {
                    click(Offset(if (direction == LayoutDirection.Rtl) width - 2f else 2f, centerY))
                }
                waitForIdle()
                assertEquals(range.start, value, "$name replacement must accept a fresh current-domain tap")
                assertEquals(changesBeforeReplacement + 1, changes)
                assertEquals(finishesBeforeReplacement + 1, finished)
                val progress = onNodeWithTag("slider").fetchSemanticsNode().config[SemanticsProperties.ProgressBarRangeInfo]
                assertEquals(steps, progress.steps)
                assertEquals(range, progress.range, "$name semantics must use the replacement range")
                assertEquals(value, progress.current, "$name semantics must expose the current tap value")
                val midpoint = (range.start + range.endInclusive) / 2f
                onNodeWithTag("slider").performSemanticsAction(SemanticsActions.SetProgress) { assertTrue(it(midpoint)) }
                waitForIdle()
                assertEquals(midpoint, value, "$name current-domain semantics and touch must agree")
                assertEquals(changesBeforeReplacement + 2, changes)
                assertEquals(finishesBeforeReplacement + 2, finished)
                structuralPhase(renderer, axis, "fresh-input-verified")
            } catch (failure: Throwable) {
                if (pointerOutstanding) cleanFailedStructuralPointer(renderer, axis, failure)
                throw failure // Never turn an assertion or cleanup failure into success.
            }
        }
    }

    private fun ComposeUiTest.cleanFailedStructuralPointer(renderer: Renderer, axis: Int, failure: Throwable) {
        println("NATIVECMPKIT_SLIDER_FAILURE_CLEANUP renderer=${renderer.name} axis=$axis phase=request")
        try {
            onNodeWithTag("slider").performTouchInput { cancel() }
            cancelScenePointerInput() // Reset the real scene, not just Skiko's no-op cancel injector.
            waitForIdle()
            println("NATIVECMPKIT_SLIDER_FAILURE_CLEANUP renderer=${renderer.name} axis=$axis phase=verified")
        } catch (cleanup: Throwable) {
            if (cleanup !== failure) failure.addSuppressed(cleanup)
            println("NATIVECMPKIT_SLIDER_FAILURE_CLEANUP renderer=${renderer.name} axis=$axis phase=failed")
        }
    }

    // Finite public fixture identities only. Progress never replaces any assertion or completion.
    private fun structuralPhase(renderer: Renderer, axis: Int, phase: String) {
        println("NATIVECMPKIT_SLIDER_STRUCTURE renderer=${renderer.name} axis=$axis phase=$phase")
    }

    private fun tapDragCancellation(renderer: Renderer) = runComposeUiTest {
        var value by mutableStateOf(0f)
        val source = MutableInteractionSource()
        val events = mutableListOf<Interaction>(); val values = mutableListOf<Float>()
        var finished = 0; var observedDragging = false
        tapPhase(renderer, "before-content")
        setContent {
            LaunchedEffect(source) { source.interactions.collect { events += it } }
            val dragging by source.collectIsDraggedAsState()
            SideEffect { observedDragging = dragging }
            renderer.control(value, { value = it; values += it }, range = -1f..1f, steps = 3,
                source = source, finished = { finished++ })
        }
        tapPhase(renderer, "content-installed")
        tapPhase(renderer, "before-tap")
        onNodeWithTag("slider").performTouchInput { click(Offset(width - 2f, centerY)) }
        tapPhase(renderer, "tapped")
        tapPhase(renderer, "before-drag")
        onNodeWithTag("slider").performTouchInput {
            swipe(Offset(width - 2f, centerY), Offset(2f, centerY), 150)
        }
        tapPhase(renderer, "dragged")
        assertEquals(-1f, value); assertEquals(2, finished)
        tapPhase(renderer, "first-input-verified")
        tapPhase(renderer, "before-opposite-taps")
        onNodeWithTag("slider").performTouchInput { click(Offset(width - 2f, centerY)); click(Offset(2f, centerY)) }
        tapPhase(renderer, "opposite-taps")
        waitForIdle()
        assertEquals(-1f, value); assertEquals(4, finished)
        tapPhase(renderer, "successful-input-verified")
        val countAfterSuccessfulInput = values.size
        tapPhase(renderer, "before-writer-clock")
        mainClock.advanceTimeBy(512)
        tapPhase(renderer, "writer-clock-advanced")
        waitForIdle()
        assertEquals(countAfterSuccessfulInput, values.size, "Tap/drag cannot retain a delayed caller-state writer")
        assertEquals(-1f, value)
        tapPhase(renderer, "writer-cleared")

        tapPhase(renderer, "before-cancelled-drag")
        onNodeWithTag("slider").performTouchInput { down(center); moveBy(Offset(width * .35f, 0f)); cancel() }
        tapPhase(renderer, "cancelled-injector")
        cancelScenePointerInput() // Real scene cancellation; test input cancel alone was historically a no-op.
        tapPhase(renderer, "scene-cancelled")
        waitForIdle()
        tapPhase(renderer, "cancellation-idle")
        val cancelled = events.filterIsInstance<DragInteraction.Start>().last()
        assertEquals(1, events.filterIsInstance<DragInteraction.Cancel>().count { it.start === cancelled })
        assertTrue(events.filterIsInstance<DragInteraction.Stop>().none { it.start === cancelled })
        assertFalse(observedDragging)
        assertEquals(4, finished)
        tapPhase(renderer, "cancellation-verified")
        val countAtCancellation = values.size
        tapPhase(renderer, "before-cancelled-writer-clock")
        mainClock.advanceTimeBy(512)
        tapPhase(renderer, "cancelled-writer-clock-advanced")
        waitForIdle()
        assertEquals(countAtCancellation, values.size)
        assertTrue(values.all { it in setOf(-1f, -.5f, 0f, .5f, 1f) })
        tapPhase(renderer, "cancelled-writer-cleared")
        tapPhase(renderer, "before-semantic")
        onNodeWithTag("slider").performSemanticsAction(SemanticsActions.SetProgress) { assertTrue(it(-.7f)) }
        tapPhase(renderer, "semantic")
        waitForIdle()
        assertEquals(-.5f, value); assertEquals(5, finished)
        tapPhase(renderer, "complete")
    }

    private fun tapPhase(renderer: Renderer, phase: String) {
        println("NATIVECMPKIT_SLIDER_TAP renderer=${renderer.name} phase=$phase")
    }

    private enum class Renderer {
        Liquid, Cupertino;

        @Composable fun control(value: Float, change: (Float) -> Unit, enabled: Boolean = true,
                                range: ClosedFloatingPointRange<Float> = 0f..1f, steps: Int = 0,
                                width: Dp = 240.dp, source: MutableInteractionSource, finished: () -> Unit) {
            val modifier = Modifier.width(width).testTag("slider")
            when (this) {
                Liquid -> LiquidGlassSliderImpl(value, change, modifier, enabled, range, steps, finished,
                    LiquidGlassSliderDefaults.colors(), source)
                Cupertino -> CupertinoSlider(value, change, modifier, enabled, range, steps, finished,
                    interactionSource = source)
            }
        }
    }
}
