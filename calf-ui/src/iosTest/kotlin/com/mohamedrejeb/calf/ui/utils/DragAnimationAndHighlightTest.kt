package com.mohamedrejeb.calf.ui.utils

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.dp
import com.mohamedrejeb.calf.ui.internal.cancelScenePointerInput
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.isActive
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Actual library helpers, composition-owned jobs and the Compose frame clock; no animation stub. */
@OptIn(ExperimentalTestApi::class)
class DragAnimationAndHighlightTest {
    @Test fun rapidReleaseRepressCannotReleaseTheNewPress() = runComposeUiTest {
        lateinit var animation: DampedDragAnimation
        setContent {
            val scope = rememberCoroutineScope()
            animation = remember { newAnimation(scope) }
            DisposableEffect(animation) { onDispose { animation.cancel() } }
        }
        waitForIdle()
        mainClock.autoAdvance = false
        runOnIdle { animation.press() }
        mainClock.advanceTimeBy(32)
        runOnIdle { animation.release(); animation.press() }
        mainClock.advanceTimeBy(2_000)
        assertEquals(1f, animation.pressProgress, .001f)
        assertEquals(1.5f, animation.scaleX, .001f)
        assertEquals(1.5f, animation.scaleY, .001f)
        runOnIdle { animation.release() }
        mainClock.advanceTimeBy(2_000)
        assertEquals(0f, animation.pressProgress, .001f)
        assertEquals(1f, animation.scaleX, .001f)
        assertEquals(0f, animation.velocity)
    }

    @Test fun highFrequencyValueUpdatesKeepOnlyTwoOwnedJobLanes() = runComposeUiTest {
        lateinit var animation: DampedDragAnimation
        lateinit var scope: CoroutineScope
        setContent {
            scope = rememberCoroutineScope()
            animation = remember { newAnimation(scope) }
            DisposableEffect(animation) { onDispose { animation.cancel() } }
        }
        waitForIdle()
        mainClock.autoAdvance = false
        runOnIdle {
            animation.press()
            repeat(1_000) { animation.updateValue(it / 1_000f) }
            assertTrue(animation.activeOwnedJobCount <= 2)
            assertTrue(scope.coroutineContext[Job]!!.children.count { it.isActive } <= 2)
        }
        mainClock.advanceTimeBy(2_000)
        assertEquals(.999f, animation.value, .001f)
        assertTrue(animation.value.isFinite() && animation.progress.isFinite() && animation.velocity.isFinite())
        runOnIdle { animation.cancel() }
        assertEquals(0, animation.activeOwnedJobCount)
        assertTrue(scope.isActive, "The helper must not cancel its caller's coroutine scope")
    }

    @Test fun newPressInterruptsProgrammaticValueAnimationWithoutAStaleRelease() = runComposeUiTest {
        lateinit var animation: DampedDragAnimation
        setContent {
            val scope = rememberCoroutineScope()
            animation = remember { newAnimation(scope) }
            DisposableEffect(animation) { onDispose { animation.cancel() } }
        }
        waitForIdle()
        mainClock.autoAdvance = false
        runOnIdle { animation.animateToValue(1f) }
        mainClock.advanceTimeBy(48)
        runOnIdle { animation.press() }
        val atInterruption = animation.value
        mainClock.advanceTimeBy(2_000)
        assertEquals(atInterruption, animation.value, .001f)
        assertEquals(1f, animation.pressProgress, .001f)
        runOnIdle { animation.updateValue(.25f) }
        mainClock.advanceTimeBy(2_000)
        assertEquals(.25f, animation.value, .001f)
        assertEquals(1f, animation.pressProgress, .001f)
    }

    @Test fun constantAndExtremeFiniteRangesNeverGenerateNonFiniteValues() = runComposeUiTest {
        lateinit var constant: DampedDragAnimation
        lateinit var wide: DampedDragAnimation
        setContent {
            val scope = rememberCoroutineScope()
            constant = remember { newAnimation(scope, initial = 9f, range = 2f..2f) }
            wide = remember { newAnimation(scope, initial = -Float.MAX_VALUE, range = -Float.MAX_VALUE..Float.MAX_VALUE) }
            DisposableEffect(constant, wide) { onDispose { constant.cancel(); wide.cancel() } }
        }
        waitForIdle()
        mainClock.autoAdvance = false
        assertEquals(2f, constant.value)
        assertEquals(0f, constant.progress)
        runOnIdle { constant.animateToValue(100f); wide.press(); wide.updateValue(Float.MAX_VALUE) }
        repeat(80) {
            mainClock.advanceTimeBy(16)
            for (animation in listOf(constant, wide)) {
                assertTrue(animation.value.isFinite())
                assertTrue(animation.progress.isFinite() && animation.progress in 0f..1f)
                assertTrue(animation.velocity.isFinite())
                assertTrue(animation.scaleX.isFinite() && animation.scaleY.isFinite())
            }
        }
        assertEquals(2f, constant.value)
        assertEquals(1f, wide.progress, .001f)
        runOnIdle { constant.cancel(); wide.cancel() }
        assertEquals(0, constant.activeOwnedJobCount)
        assertEquals(0, wide.activeOwnedJobCount)
    }

    @Test fun invalidValuesAreRejectedBeforeCreatingAnimationWork() = runComposeUiTest {
        lateinit var scope: CoroutineScope
        setContent { scope = rememberCoroutineScope() }
        waitForIdle()
        runOnIdle {
            assertFailsWith<IllegalArgumentException> { newAnimation(scope, initial = Float.NaN) }
            assertFailsWith<IllegalArgumentException> { newAnimation(scope, range = 1f..0f) }
            assertFailsWith<IllegalArgumentException> { newAnimation(scope, range = Float.NEGATIVE_INFINITY..1f) }
            assertFailsWith<IllegalArgumentException> { newAnimation(scope, threshold = 0f) }
            assertFailsWith<IllegalArgumentException> { newAnimation(scope, threshold = Float.NaN) }
            val valid = newAnimation(scope, initial = 3f, range = -2f..-1f)
            assertEquals(-1f, valid.value)
            assertFailsWith<IllegalArgumentException> { valid.updateValue(Float.POSITIVE_INFINITY) }
            assertFailsWith<IllegalArgumentException> { valid.animateToValue(Float.NaN) }
            assertEquals(0, valid.activeOwnedJobCount)
        }
    }

    @Test fun cancellingTheActualDragModifierDoesNotInvokeDragStopped() = runComposeUiTest {
        lateinit var animation: DampedDragAnimation
        var starts = 0
        var stops = 0
        setContent {
            val scope = rememberCoroutineScope()
            animation = remember {
                DampedDragAnimation(scope, 0f, 0f..1f, .001f, 1f, 1.5f,
                    onDragStarted = { starts++ }, onDragStopped = { stops++ }, onDrag = { _, _ -> })
            }
            DisposableEffect(animation) { onDispose { animation.cancel() } }
            Box(Modifier.size(100.dp).then(animation.modifier).testTag("target"))
        }
        onNodeWithTag("target").performTouchInput { down(center); moveBy(Offset(20f, 0f)); cancel() }
        cancelScenePointerInput()
        waitForIdle()
        assertEquals(1, starts)
        assertEquals(0, stops)
        assertEquals(0f, animation.pressProgress, .001f)
        assertEquals(0f, animation.velocity)
        onNodeWithTag("target").performTouchInput { down(center); moveBy(Offset(20f, 0f)); up() }
        waitForIdle()
        assertEquals(2, starts)
        assertEquals(1, stops)
    }

    @Test fun hundredGestureOnlyHighlightsDoNotConstructRuntimeShaders() = runComposeUiTest {
        lateinit var highlights: List<InteractiveHighlight>
        setContent {
            val scope = rememberCoroutineScope()
            highlights = remember { List(100) { InteractiveHighlight(scope) } }
            DisposableEffect(highlights) { onDispose { highlights.forEach { it.dispose() } } }
            // This is the production button's gesture-only path, not the optional drawing modifier.
            Box(Modifier.size(100.dp).then(highlights.first().gestureModifier).testTag("target"))
        }
        waitForIdle()
        assertTrue(highlights.none { it.hasAttemptedShader })
        onNodeWithTag("target").performTouchInput { down(center); moveBy(Offset(20f, 0f)) }
        waitForIdle()
        assertTrue(highlights.first().pressProgress > .9f)
        assertTrue(highlights.none { it.hasAttemptedShader })
        onNodeWithTag("target").performTouchInput { cancel() }
        cancelScenePointerInput()
        waitForIdle()
        assertEquals(0f, highlights.first().pressProgress, .001f)
        assertTrue(highlights.none { it.hasAttemptedShader })
    }

    @Test fun drawingHighlightCompilesLazilyAndDisposesOnlyItsOwnWork() = runComposeUiTest {
        lateinit var highlight: InteractiveHighlight
        lateinit var scope: CoroutineScope
        setContent {
            scope = rememberCoroutineScope()
            highlight = remember { InteractiveHighlight(scope) }
            DisposableEffect(highlight) { onDispose { highlight.dispose() } }
            Box(Modifier.size(100.dp).then(highlight.gestureModifier).then(highlight.modifier).testTag("target"))
        }
        waitForIdle()
        assertFalse(highlight.hasAttemptedShader)
        onNodeWithTag("target").performTouchInput { down(center) }
        waitForIdle()
        assertTrue(highlight.hasAttemptedShader)
        onNodeWithTag("target").performTouchInput { cancel() }
        cancelScenePointerInput()
        waitForIdle()
        runOnIdle { highlight.dispose(); highlight.dispose() }
        assertTrue(scope.isActive)
        assertTrue(scope.coroutineContext[Job]!!.children.none { it.isActive })
    }

    private fun newAnimation(
        scope: CoroutineScope,
        initial: Float = 0f,
        range: ClosedRange<Float> = 0f..1f,
        threshold: Float = .001f,
    ) = DampedDragAnimation(scope, initial, range, threshold, 1f, 1.5f, {}, {}, { _, _ -> })
}
