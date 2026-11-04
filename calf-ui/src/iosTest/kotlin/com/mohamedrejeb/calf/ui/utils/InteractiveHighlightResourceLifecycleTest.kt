// SPDX-License-Identifier: Apache-2.0
@file:OptIn(androidx.compose.ui.test.ExperimentalTestApi::class)

package com.mohamedrejeb.calf.ui.utils

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.dp
import com.kyant.backdrop.asSkikoRuntimeShader
import com.mohamedrejeb.calf.ui.internal.cancelScenePointerInput
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Job
import kotlinx.coroutines.awaitCancellation
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNotSame
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

/** Actual Skia builder identities/pixels and actual input, not a replacement shader or fixture bitmap. */
class InteractiveHighlightResourceLifecycleTest {
    @Test fun disposingAPressedRetainedModifierClosesItsRealBuilderStopsPixelsAndNeverRestartsItsJobs() {
        requireUiDragShaderApplication()
        runComposeUiTest {
            lateinit var firstScope: CoroutineScope; lateinit var secondScope: CoroutineScope
            lateinit var first: InteractiveHighlight; lateinit var second: InteractiveHighlight
            lateinit var sibling: Job
            var cleanupFirst: InteractiveHighlight? = null; var cleanupSecond: InteractiveHighlight? = null
            var cleanupFirstScope: CoroutineScope? = null; var cleanupSecondScope: CoroutineScope? = null
            var primary: Throwable? = null
            try {
                setContent {
                    firstScope = rememberCallerOwnedAnimationScope(); cleanupFirstScope = firstScope
                    secondScope = rememberCallerOwnedAnimationScope(); cleanupSecondScope = secondScope
                    first = remember(firstScope) { InteractiveHighlight(firstScope) }; cleanupFirst = first
                    second = remember(secondScope) { InteractiveHighlight(secondScope) }; cleanupSecond = second
                    DisposableEffect(first, second) { onDispose { first.dispose(); second.dispose() } }
                    Row {
                        Box(Modifier.size(100.dp).background(Color.Red).then(first.gestureModifier)
                            .then(first.modifier).testTag("first"))
                        Box(Modifier.size(100.dp).background(Color.Red).then(second.gestureModifier)
                            .then(second.modifier).testTag("second"))
                    }
                }
                waitForIdle()
                runOnIdle { sibling = firstScope.launch(start = CoroutineStart.UNDISPATCHED) { awaitCancellation() } }
                assertFalse(first.hasAttemptedShader); assertFalse(second.hasAttemptedShader)

                // Capture observations while held; finish each injection before any assertions.
                onNodeWithTag("first").performTouchInput { down(center) }
                val pressedFirstColor = captureOwnedCenterColor("first")
                val firstBuilderObservation = runOnIdle { first.ownedDrawingShader?.asSkikoRuntimeShader() }
                onNodeWithTag("first").performTouchInput { up() }; waitForIdle()
                onNodeWithTag("second").performTouchInput { down(center) }
                val pressedSecondColor = captureOwnedCenterColor("second")
                val secondBuilderObservation = runOnIdle { second.ownedDrawingShader?.asSkikoRuntimeShader() }
                onNodeWithTag("second").performTouchInput { up() }; waitForIdle()
                val firstBuilder = assertNotNull(firstBuilderObservation, "A real SkSL builder must be created, not fallback-only coverage")
                val secondBuilder = assertNotNull(secondBuilderObservation)
                assertNotSame(firstBuilder, secondBuilder)
                assertFalse(firstBuilder.isClosed); assertFalse(secondBuilder.isClosed)
                assertTrue(pressedFirstColor.green > .05f && pressedSecondColor.green > .05f)

                onNodeWithTag("first").performTouchInput { down(center); moveBy(Offset(15f, 5f)) }
                val beforeDisposalColor = captureOwnedCenterColor("first")
                runOnIdle { first.dispose(); first.dispose() }
                val afterDisposalColor = captureOwnedCenterColor("first")
                onNodeWithTag("first").performTouchInput { up() }; waitForIdle()
                assertTrue(beforeDisposalColor.green > .05f)
                assertEquals(Color.Red, afterDisposalColor, "A disposed shader must not become an opaque/flat fallback draw")
                assertTrue(firstBuilder.isClosed)
                assertFalse(secondBuilder.isClosed, "Disposal cannot close a sibling helper's actual native builder")
                assertNull(first.ownedDrawingShader); assertTrue(first.isDisposed)
                assertEquals(0f, first.pressProgress); assertEquals(Offset.Zero, first.offset)
                runOnIdle {
                    assertSame(sibling, firstScope.coroutineContext[Job]!!.children.filter { it.isActive }.single())
                    assertTrue(firstScope.isActive && sibling.isActive)
                }

                // Retained pointer/drawing nodes really receive another gesture AFTER terminal disposal.
                onNodeWithTag("first").performTouchInput { down(center); moveBy(Offset(20f, 0f)) }
                val repressedColor = captureOwnedCenterColor("first")
                val repressedProgress = runOnIdle { first.pressProgress }
                onNodeWithTag("first").performTouchInput { up() }; waitForIdle()
                assertEquals(Color.Red, repressedColor); assertEquals(0f, repressedProgress)
                assertNull(first.ownedDrawingShader); assertTrue(firstBuilder.isClosed)
                runOnIdle {
                    assertSame(sibling, firstScope.coroutineContext[Job]!!.children.filter { it.isActive }.single())
                    second.dispose()
                    assertTrue(secondBuilder.isClosed)
                    assertTrue(secondScope.isActive)
                    assertTrue(secondScope.coroutineContext[Job]!!.children.none { it.isActive })
                }
                println("NATIVECMPKIT_HIGHLIGHT_NATIVE_CUSTODY actualBuilders=2 closedOwned=2 " +
                    "retainedRepressJobs=0 disposedPixelsAreBackdrop=true siblingPreserved=true")
            } catch (error: Throwable) {
                primary = error; throw error
            } finally {
                closeOwnedUiDragShaderResources(primary,
                    { cleanupFirst?.dispose() }, { cleanupSecond?.dispose() },
                    { cleanupFirstScope?.coroutineContext?.get(Job)?.cancel() },
                    { cleanupSecondScope?.coroutineContext?.get(Job)?.cancel() })
            }
        }
    }

    @Test fun removingAnActualPressedHighlightClosesItsBuilderAndNewCompositionUsesANewOwnedResource() {
        requireUiDragShaderApplication()
        runComposeUiTest {
            lateinit var scope: CoroutineScope
            lateinit var highlight: InteractiveHighlight
            lateinit var sibling: Job
            var cleanupScope: CoroutineScope? = null
            val created = mutableListOf<InteractiveHighlight>()
            val shown = mutableStateOf(true)
            var primary: Throwable? = null
            try {
                setContent {
                    scope = rememberCallerOwnedAnimationScope(); cleanupScope = scope
                    Box(Modifier.size(160.dp).testTag("root")) {
                        if (shown.value) {
                            highlight = remember(scope) { InteractiveHighlight(scope).also { created += it } }
                            val current = highlight
                            DisposableEffect(current) { onDispose { current.dispose() } }
                            Box(Modifier.size(100.dp).background(Color.Red).then(current.gestureModifier)
                                .then(current.modifier).testTag("highlight"))
                        }
                    }
                }
                waitForIdle()
                runOnIdle { sibling = scope.launch(start = CoroutineStart.UNDISPATCHED) { awaitCancellation() } }
                onNodeWithTag("highlight").performTouchInput { down(center); moveBy(Offset(20f, 0f)) }
                val beforeRemovalColor = captureOwnedCenterColor("highlight")
                val retired = highlight
                val retiredBuilderObservation = runOnIdle { retired.ownedDrawingShader?.asSkikoRuntimeShader() }
                runOnIdle { shown.value = false }
                onNodeWithTag("root").performTouchInput { cancel() }
                cancelScenePointerInput(); waitForIdle()
                val retiredBuilder = assertNotNull(retiredBuilderObservation)
                assertTrue(beforeRemovalColor.green > .05f)
                assertTrue(retiredBuilder.isClosed && retired.isDisposed)
                assertNull(retired.ownedDrawingShader); assertEquals(0f, retired.pressProgress)
                runOnIdle {
                    assertSame(sibling, scope.coroutineContext[Job]!!.children.filter { it.isActive }.single())
                    assertTrue(scope.isActive && sibling.isActive)
                    shown.value = true
                }
                waitForIdle()
                onNodeWithTag("highlight").performTouchInput { down(center) }
                val freshColor = captureOwnedCenterColor("highlight")
                val fresh = highlight
                val freshBuilderObservation = runOnIdle { fresh.ownedDrawingShader?.asSkikoRuntimeShader() }
                onNodeWithTag("highlight").performTouchInput { up() }; waitForIdle()
                val freshBuilder = assertNotNull(freshBuilderObservation)
                assertNotSame(retired, fresh); assertNotSame(retiredBuilder, freshBuilder)
                assertEquals(2, created.size); assertTrue(freshColor.green > .05f)
                assertTrue(retiredBuilder.isClosed); assertFalse(freshBuilder.isClosed)
                runOnIdle {
                    fresh.dispose(); fresh.dispose()
                    assertTrue(freshBuilder.isClosed)
                    assertSame(sibling, scope.coroutineContext[Job]!!.children.filter { it.isActive }.single())
                    assertTrue(scope.isActive && sibling.isActive)
                }
                println("NATIVECMPKIT_HIGHLIGHT_ROOT_REMOVAL actualBuilders=2 closedOwned=2 " +
                    "actualSceneCancelled=true newNativeIdentity=true siblingPreserved=true")
            } catch (error: Throwable) {
                primary = error; throw error
            } finally {
                closeOwnedUiDragShaderResources(primary,
                    *created.map { current -> { current.dispose() } }.toTypedArray(),
                    { cleanupScope?.coroutineContext?.get(Job)?.cancel() })
            }
        }
    }
}
