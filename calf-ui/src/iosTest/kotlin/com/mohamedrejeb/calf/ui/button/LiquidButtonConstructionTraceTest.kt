// SPDX-License-Identifier: Apache-2.0
@file:OptIn(androidx.compose.ui.test.ExperimentalTestApi::class,
    com.mohamedrejeb.calf.ui.ExperimentalCalfUiApi::class)

package com.mohamedrejeb.calf.ui.button

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.click
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.dp
import com.mohamedrejeb.calf.ui.internal.cancelScenePointerInput
import com.mohamedrejeb.calf.ui.utils.InteractiveHighlight
import com.mohamedrejeb.calf.ui.utils.LocalInteractiveHighlightConstructionObserver
import com.mohamedrejeb.calf.ui.utils.closeOwnedUiDragShaderResources
import com.mohamedrejeb.calf.ui.utils.requireUiDragShaderApplication
import kotlinx.coroutines.Job
import kotlinx.coroutines.isActive
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotSame
import kotlin.test.assertTrue
import kotlin.time.TimeSource

/** Observe actual public button instances, not100 standalone helpers or substituted factories. */
class LiquidButtonConstructionTraceTest {
    @Test fun hundredActualPublicButtonsKeepOptionalShaderConstructionAtZeroThroughInputDisableAndRecreation() {
        requireUiDragShaderApplication()
        runComposeUiTest {
            val created = mutableListOf<InteractiveHighlight>()
            val constructionTimes = mutableListOf<Long>()
            val shown = mutableStateOf(true)
            val enabled = mutableStateOf(true)
            val started = TimeSource.Monotonic.markNow()
            val observer: (InteractiveHighlight) -> Unit = { actual ->
                created += actual
                constructionTimes += started.elapsedNow().inWholeNanoseconds
            }
            var clicks = 0
            var primary: Throwable? = null
            try {
                setContent {
                    MaterialTheme {
                        CompositionLocalProvider(LocalInteractiveHighlightConstructionObserver provides observer) {
                            if (shown.value) {
                                // Eager composition guarantees100 actual buttons. A lazy list with only
                                // visible items would not measure the original100-construction criterion.
                                Column(Modifier.width(240.dp).height(400.dp)
                                    .verticalScroll(rememberScrollState()).testTag("buttons")) {
                                    repeat(100) { index ->
                                        LiquidGlassButton({ clicks++ },
                                            Modifier.fillMaxWidth().testTag("button-$index"), enabled = enabled.value,
                                            colors = LiquidGlassButtonDefaults.filledButtonColors(surfaceColor = Color.Red)) {
                                            Text("Button $index")
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                waitForIdle()
                val initial = created.toList()
                assertEquals(100, initial.size); assertEquals(100, initial.toSet().size)
                assertTrue(initial.all { !it.hasAttemptedShader && it.ownedDrawingShader == null && !it.isDisposed })
                assertTrue(initial.all { it.animationScope.isActive })

                onNodeWithTag("button-0").performTouchInput { click() }; waitForIdle()
                onNodeWithTag("button-99").performScrollTo()
                onNodeWithTag("button-99").performTouchInput { click() }; waitForIdle()
                assertEquals(2, clicks)
                assertEquals(100, created.size, "Interaction/recomposition must not reconstruct existing helpers")
                assertTrue(initial.none { it.hasAttemptedShader || it.ownedDrawingShader != null })

                onNodeWithTag("button-99").performTouchInput { down(center) }
                runOnIdle { enabled.value = false }
                onNodeWithTag("buttons").performTouchInput { cancel() }
                cancelScenePointerInput(); waitForIdle()
                assertEquals(2, clicks, "Disabling a held real button must cancel, not invoke the business callback")
                assertEquals(100, created.size)
                assertTrue(initial.all { !it.hasAttemptedShader && it.ownedDrawingShader == null })
                assertTrue(initial.all { it.pressProgress < .001f && !it.isDisposed })
                assertTrue(initial.all { it.animationScope.coroutineContext[Job]!!.children.none { job -> job.isActive } })

                runOnIdle { shown.value = false }; waitForIdle()
                assertTrue(initial.all { it.isDisposed && it.ownedDrawingShader == null })
                assertTrue(initial.none { it.animationScope.isActive })
                val firstGenerationElapsed = started.elapsedNow().inWholeNanoseconds
                runOnIdle { enabled.value = true; shown.value = true }; waitForIdle()
                assertEquals(200, created.size)
                val fresh = created.drop(100)
                assertEquals(100, fresh.toSet().size)
                for (index in 0 until 100) assertNotSame(initial[index], fresh[index])
                assertTrue(fresh.all { !it.isDisposed && it.animationScope.isActive })
                assertFalse(created.any { it.hasAttemptedShader || it.ownedDrawingShader != null })
                runOnIdle { shown.value = false }; waitForIdle()
                assertTrue(created.all { it.isDisposed && it.ownedDrawingShader == null })
                assertTrue(created.none { it.animationScope.isActive })
                assertEquals(200, constructionTimes.size)
                assertTrue(constructionTimes.zipWithNext().all { (before, after) -> before <= after })
                println("NATIVECMPKIT_LIQUID_BUTTON_CONSTRUCTION_TRACE firstGenerationButtons=100 " +
                    "actualHelperConstructions=200 generations=2 optionalShaderAttempts=0 ownedHighlightBuilders=0 " +
                    "disposedHelpers=200 callerClicks=$clicks firstGenerationElapsedNs=$firstGenerationElapsed " +
                    "elapsedNs=${started.elapsedNow().inWholeNanoseconds} " +
                    "instrumentsAllocationTrace=false hardwareGpuFrameBudgetMeasured=false")
            } catch (error: Throwable) {
                primary = error; throw error
            } finally {
                closeOwnedUiDragShaderResources(primary, *created.map { current -> { current.dispose() } }.toTypedArray())
            }
        }
    }
}
