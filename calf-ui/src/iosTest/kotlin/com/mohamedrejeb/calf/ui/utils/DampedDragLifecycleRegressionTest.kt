// SPDX-License-Identifier: Apache-2.0
@file:OptIn(androidx.compose.ui.test.ExperimentalTestApi::class)

package com.mohamedrejeb.calf.ui.utils

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.dp
import com.mohamedrejeb.calf.ui.internal.cancelScenePointerInput
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Job
import kotlinx.coroutines.awaitCancellation
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotSame
import kotlin.test.assertSame
import kotlin.test.assertTrue
import kotlin.time.TimeSource

/** New callback/disposal/actual job-custody boundaries; the older accepted eight bodies stay intact. */
class DampedDragLifecycleRegressionTest {
    @Test fun cancellationFromActualStartAndStopCallbacksCannotRecreateFeedbackAndNextGestureRecovers() {
        requireUiDragShaderApplication()
        runComposeUiTest {
            lateinit var scope: CoroutineScope
            lateinit var animation: DampedDragAnimation
            lateinit var sibling: Job
            var cleanupScope: CoroutineScope? = null
            var cleanupAnimation: DampedDragAnimation? = null
            var cancelOnStart = true; var cancelOnStop = false
            var starts = 0; var stops = 0; var drags = 0
            try {
                setContent {
                    scope = rememberCallerOwnedAnimationScope()
                    cleanupScope = scope
                    animation = remember {
                        DampedDragAnimation(scope, 0f, 0f..1f, .001f, 1f, 1.5f,
                            onDragStarted = { starts++; if (cancelOnStart) cancel() },
                            onDragStopped = { stops++; if (cancelOnStop) cancel() },
                            onDrag = { _, _ -> drags++; updateValue(.75f) })
                    }
                    cleanupAnimation = animation
                    DisposableEffect(animation) { onDispose { animation.cancel() } }
                    Box(Modifier.size(100.dp).then(animation.modifier).testTag("drag"))
                }
                waitForIdle(); mainClock.autoAdvance = false
                runOnIdle { sibling = scope.launch(start = CoroutineStart.UNDISPATCHED) { awaitCancellation() } }

                // Complete the injected session BEFORE assertions, even when the owner cancels at start.
                onNodeWithTag("drag").performTouchInput { down(center); moveBy(Offset(20f, 0f)); up() }
                runOnIdle {
                    assertEquals(1, starts); assertEquals(0, stops); assertEquals(0, drags)
                    assertEquals(0, animation.activeOwnedJobCount)
                    assertSame(sibling, scope.coroutineContext[Job]!!.children.filter { it.isActive }.single())
                    cancelOnStart = false; cancelOnStop = true
                }

                onNodeWithTag("drag").performTouchInput { down(center); moveBy(Offset(20f, 0f)); up() }
                runOnIdle {
                    assertEquals(2, starts); assertEquals(1, stops); assertTrue(drags > 0)
                    // No delayed release may be launched AFTER the owner's stop callback cancelled it.
                    assertEquals(0, animation.activeOwnedJobCount)
                    assertSame(sibling, scope.coroutineContext[Job]!!.children.filter { it.isActive }.single())
                    cancelOnStop = false
                }
                onNodeWithTag("drag").performTouchInput { down(center); moveBy(Offset(20f, 0f)); up() }
                mainClock.advanceTimeBy(2_000)
                runOnIdle {
                    assertEquals(3, starts); assertEquals(2, stops)
                    assertEquals(.75f, animation.value, .001f)
                    animation.cancel()
                    assertEquals(0, animation.activeOwnedJobCount)
                    assertTrue(scope.isActive && sibling.isActive)
                }
                println("NATIVECMPKIT_DAMPED_CALLBACK_CUSTODY starts=$starts stops=$stops " +
                    "cancelledStartDrags=0 ownedAfterCancel=0 siblingPreserved=true")
            } finally {
                cleanupAnimation?.cancel()
                cleanupScope?.coroutineContext?.get(Job)?.cancel()
            }
        }
    }

    @Test fun removingAnActiveActualModifierLeavesNoReleaseWorkInTheCallerScopeAndRangeReplacementRecovers() {
        requireUiDragShaderApplication()
        runComposeUiTest {
            lateinit var scope: CoroutineScope
            lateinit var animation: DampedDragAnimation
            lateinit var retired: DampedDragAnimation
            lateinit var sibling: Job
            var cleanupScope: CoroutineScope? = null
            var cleanupAnimation: DampedDragAnimation? = null
            var cleanupRetired: DampedDragAnimation? = null
            val shown = mutableStateOf(true)
            val range = mutableStateOf(0f..1f)
            var starts = 0; var stops = 0; var disposals = 0
            try {
                setContent {
                    scope = rememberCallerOwnedAnimationScope()
                    cleanupScope = scope
                    Box(Modifier.size(160.dp).testTag("root")) {
                        if (shown.value) {
                            animation = remember(range.value) {
                                DampedDragAnimation(scope, range.value.start, range.value, .001f, 1f, 1.5f,
                                    onDragStarted = { starts++ }, onDragStopped = { stops++ },
                                    onDrag = { _, _ -> updateValue(range.value.endInclusive) })
                            }
                            cleanupAnimation = animation
                            val current = animation
                            DisposableEffect(current) { onDispose { current.cancel(); disposals++ } }
                            Box(Modifier.size(100.dp).then(current.modifier).testTag("drag"))
                        }
                    }
                }
                waitForIdle(); mainClock.autoAdvance = false
                runOnIdle { sibling = scope.launch(start = CoroutineStart.UNDISPATCHED) { awaitCancellation() } }
                onNodeWithTag("drag").performTouchInput { down(center); moveBy(Offset(20f, 0f)) }
                mainClock.advanceTimeBy(48)
                runOnIdle { retired = animation; cleanupRetired = retired; shown.value = false }
                // Reset injector AND the actual scene. The no-op injector alone is not native cancellation.
                onNodeWithTag("root").performTouchInput { cancel() }
                cancelScenePointerInput()
                mainClock.advanceTimeBy(64)
                runOnIdle {
                    assertEquals(1, starts); assertEquals(0, stops); assertEquals(1, disposals)
                    assertEquals(0, retired.activeOwnedJobCount)
                    assertSame(sibling, scope.coroutineContext[Job]!!.children.filter { it.isActive }.single())
                    assertTrue(scope.isActive && sibling.isActive)
                    range.value = -2f..2f; shown.value = true
                }
                waitForIdle()
                onNodeWithTag("drag").performTouchInput { down(center); moveBy(Offset(20f, 0f)); up() }
                mainClock.advanceTimeBy(2_000)
                runOnIdle {
                    assertNotSame(retired, animation)
                    assertEquals(-2f..2f, animation.valueRange)
                    assertEquals(2f, animation.value, .001f)
                    assertEquals(2, starts); assertEquals(1, stops)
                    assertEquals(0, retired.activeOwnedJobCount)
                    animation.cancel()
                    assertTrue(scope.isActive && sibling.isActive)
                }
                println("NATIVECMPKIT_DAMPED_REMOVAL retiredOwned=0 cancelledStops=0 " +
                    "newRangeRecovered=true siblingPreserved=true")
            } finally {
                cleanupAnimation?.cancel()
                cleanupRetired?.cancel()
                cleanupScope?.coroutineContext?.get(Job)?.cancel()
            }
        }
    }

    @Test fun thousandSustainedUpdatesTraceActualJobTreesAcrossFramesAndRepressWithoutCancellingSiblingWork() {
        requireUiDragShaderApplication()
        runComposeUiTest {
            lateinit var scope: CoroutineScope
            lateinit var animation: DampedDragAnimation
            lateinit var sibling: Job
            var cleanupScope: CoroutineScope? = null
            var cleanupAnimation: DampedDragAnimation? = null
            val observedJobs = mutableSetOf<Job>()
            var maxRoot = 0; var maxActive = 0; var maxTotal = 0; var updates = 0
            val started = TimeSource.Monotonic.markNow()
            try {
                setContent {
                    scope = rememberCallerOwnedAnimationScope()
                    cleanupScope = scope
                    animation = remember {
                        DampedDragAnimation(scope, 0f, 0f..1f, .001f, 1f, 1.5f, {}, {}, { _, _ -> })
                    }
                    cleanupAnimation = animation
                    DisposableEffect(animation) { onDispose { animation.cancel() } }
                }
                waitForIdle(); mainClock.autoAdvance = false
                runOnIdle {
                    sibling = scope.launch(start = CoroutineStart.UNDISPATCHED) { awaitCancellation() }
                    animation.press()
                }
                repeat(50) { frame ->
                    runOnIdle {
                        if (frame > 0 && frame % 10 == 0) { animation.release(); animation.press() }
                        repeat(20) { index -> animation.updateValue((frame * 20 + index) / 999f); updates++ }
                    }
                    mainClock.advanceTimeBy(16)
                    runOnIdle {
                        val owner = scope.coroutineContext[Job]!!
                        val roots = owner.children.toList()
                        val descendants = ownedDescendants(owner)
                        observedJobs += descendants
                        maxRoot = maxOf(maxRoot, roots.size)
                        maxActive = maxOf(maxActive, descendants.count { it.isActive })
                        maxTotal = maxOf(maxTotal, descendants.size)
                        assertTrue(roots.count { it.isActive && it !== sibling } <= 2)
                        // Value lane + feedback owner/three animations, plus the independent sibling.
                        assertTrue(descendants.count { it.isActive } <= 6)
                        assertTrue(animation.value.isFinite() && animation.progress in 0f..1f)
                        assertTrue(animation.velocity.isFinite())
                        assertTrue(sibling.isActive)
                    }
                }
                mainClock.advanceTimeBy(2_000)
                runOnIdle {
                    assertEquals(1_000, updates); assertEquals(1f, animation.value, .001f)
                    assertEquals(1f, animation.pressProgress, .001f)
                    assertTrue(observedJobs.size > 10, "The trace must observe real animation jobs, not only a source counter")
                    animation.cancel()
                    assertEquals(0, animation.activeOwnedJobCount)
                    assertSame(sibling, scope.coroutineContext[Job]!!.children.filter { it.isActive }.single())
                    assertTrue(scope.isActive && sibling.isActive)
                }
                println("NATIVECMPKIT_DAMPED_JOB_TRACE updates=$updates frames=50 maxRootChildren=$maxRoot " +
                    "maxActiveDescendants=$maxActive maxTotalDescendants=$maxTotal " +
                    "distinctObservedJobs=${observedJobs.size} elapsedNs=${started.elapsedNow().inWholeNanoseconds} " +
                    "virtualFrameClock=true hardwareFrameBudgetMeasured=false")
            } finally {
                cleanupAnimation?.cancel()
                cleanupScope?.coroutineContext?.get(Job)?.cancel()
            }
        }
    }
}
