package com.mohamedrejeb.calf.ui.slider

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.interaction.DragInteraction
import androidx.compose.foundation.interaction.Interaction
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.assertWidthIsEqualTo
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performSemanticsAction
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.swipe
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import com.mohamedrejeb.calf.ui.ExperimentalCalfUiApi
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Public Liquid controls on the actual UIKit/Compose host; no layout or frame-clock substitute. */
@OptIn(ExperimentalTestApi::class, ExperimentalCalfUiApi::class)
class LiquidGlassSliderNumericTest {
    @Test fun constantZeroNarrowAndUnboundedControlsRenderFiniteAndStayInert() = runComposeUiTest {
        var changes = 0
        var finished = 0
        setContent {
            CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
                Column {
                    Box(Modifier.width(0.dp)) {
                        LiquidGlassSlider(9f, { changes++ }, Modifier.fillMaxWidth().testTag("zero"),
                            valueRange = 0f..0f, onValueChangeFinished = { finished++ })
                    }
                    Box(Modifier.width(1.dp)) {
                        LiquidGlassSlider(9f, { changes++ }, Modifier.fillMaxWidth().testTag("narrow"),
                            valueRange = 0f..0f, onValueChangeFinished = { finished++ })
                    }
                    Box(Modifier.width(200.dp).horizontalScroll(rememberScrollState())) {
                        LiquidGlassSlider(9f, { changes++ }, Modifier.testTag("unbounded"),
                            valueRange = 0f..0f, onValueChangeFinished = { finished++ })
                    }
                }
            }
        }
        for (tag in listOf("zero", "narrow", "unbounded")) {
            val node = onNodeWithTag(tag).fetchSemanticsNode()
            val bounds = node.boundsInRoot
            assertTrue(listOf(bounds.left, bounds.top, bounds.right, bounds.bottom).all { it.isFinite() })
            val progress = node.config[SemanticsProperties.ProgressBarRangeInfo]
            assertEquals(0f, progress.current)
            assertEquals(0f..0f, progress.range)
            onNodeWithTag(tag).performSemanticsAction(SemanticsActions.SetProgress) {
                assertFalse(it(1f))
                assertFalse(it(Float.NaN))
            }
        }
        onNodeWithTag("zero").assertWidthIsEqualTo(0.dp)
        onNodeWithTag("narrow").assertWidthIsEqualTo(1.dp)
        onNodeWithTag("unbounded").assertWidthIsEqualTo(144.dp)
        onNodeWithTag("unbounded").performTouchInput { swipe(center, center + Offset(120f, 0f), 150) }
        waitForIdle()
        assertEquals(0, changes)
        assertEquals(0, finished)
    }

    @Test fun rangeGeometryAndRtlReplacementDuringLiveInputKeepsEveryFrameFinite() = runComposeUiTest {
        val value = mutableStateOf(0f)
        val range = mutableStateOf(-1f..1f)
        val width = mutableStateOf(240.dp)
        val direction = mutableStateOf(LayoutDirection.Ltr)
        val source = MutableInteractionSource()
        val interactions = mutableListOf<Interaction>()
        var changes = 0
        var finished = 0
        setContent {
            LaunchedEffect(source) { source.interactions.collect { interactions += it } }
            CompositionLocalProvider(LocalLayoutDirection provides direction.value) {
                LiquidGlassSlider(value.value, { value.value = it; changes++ },
                    Modifier.width(width.value).testTag("slider"), valueRange = range.value,
                    interactionSource = source, onValueChangeFinished = { finished++ })
            }
        }
        waitForIdle()
        mainClock.autoAdvance = false
        onNodeWithTag("slider").performTouchInput { down(center); moveBy(Offset(this.width * 2f, 0f)) }
        mainClock.advanceTimeBy(32)
        assertTrue(changes > 0, "A no-op pointer injection does not cover live range/geometry replacement")
        val start = interactions.filterIsInstance<DragInteraction.Start>().single()
        assertTrue(interactions.none { it is DragInteraction.Stop || it is DragInteraction.Cancel })
        assertEquals(0, finished)
        val beforeReplacement = changes
        runOnIdle {
            range.value = -10f..-2f
            value.value = -6f
            width.value = 1.dp
            direction.value = LayoutDirection.Rtl
        }
        mainClock.advanceTimeBy(32)
        onNodeWithTag("slider").performTouchInput { up() }
        repeat(80) {
            mainClock.advanceTimeBy(16)
            val node = onNodeWithTag("slider").fetchSemanticsNode()
            val progress = node.config[SemanticsProperties.ProgressBarRangeInfo]
            assertTrue(progress.current.isFinite() && progress.current in -10f..-2f)
            val bounds = node.boundsInRoot
            assertTrue(listOf(bounds.left, bounds.top, bounds.right, bounds.bottom).all { it.isFinite() })
        }
        assertEquals(beforeReplacement, changes, "The disposed input session cannot publish to the new domain")
        assertEquals(0, finished, "Re-keying/cancellation is not a successful gesture")
        assertEquals(1, interactions.filterIsInstance<DragInteraction.Cancel>().count { it.start === start })
        assertTrue(interactions.none { it is DragInteraction.Stop })
        assertEquals(-6f, value.value)
        runOnIdle { width.value = 240.dp }
        mainClock.autoAdvance = true
        waitForIdle()
        onNodeWithTag("slider").performSemanticsAction(SemanticsActions.SetProgress) {
            assertTrue(it(-5.5f))
            assertFalse(it(Float.NaN))
            assertFalse(it(Float.POSITIVE_INFINITY))
        }
        waitForIdle()
        assertEquals(-5.5f, value.value)
        assertEquals(beforeReplacement + 1, changes)
        assertEquals(1, finished)
    }
}
