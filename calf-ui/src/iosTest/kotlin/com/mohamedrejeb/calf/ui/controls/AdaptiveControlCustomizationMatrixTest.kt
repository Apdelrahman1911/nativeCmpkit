// NativeCmpKit (2026-11-04): new public adaptive dark/large-text customization matrix.
@file:OptIn(androidx.compose.ui.test.ExperimentalTestApi::class)

package com.mohamedrejeb.calf.ui.controls

import androidx.compose.foundation.background
import androidx.compose.foundation.interaction.DragInteraction
import androidx.compose.foundation.interaction.Interaction
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.PressInteraction
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.IconButtonDefaults
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.graphics.asSkiaBitmap
import androidx.compose.ui.graphics.toPixelMap
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.ComposeUiTest
import androidx.compose.ui.test.captureToImage
import androidx.compose.ui.test.click
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.swipe
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.mohamedrejeb.calf.ui.button.AdaptiveButton
import com.mohamedrejeb.calf.ui.button.AdaptiveIconButton
import com.mohamedrejeb.calf.ui.slider.AdaptiveSlider
import com.mohamedrejeb.calf.ui.toggle.AdaptiveSwitch
import kotlin.math.abs
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/** Compose snapshots and actual supplied interaction flows, not OS Settings or spoken assistive tests. */
class AdaptiveControlCustomizationMatrixTest {
    @Test fun pre26CustomColorsContentAndInteractionsSurviveDarkAndLargeText() = matrix(AdaptiveControlBranch.Pre26)
    @Test fun ios26CustomColorsContentAndInteractionsSurviveDarkAndLargeText() = matrix(AdaptiveControlBranch.IOS26Plus)

    private fun matrix(branch: AdaptiveControlBranch) {
        requireAdaptiveControlHost(branch)
        for (dark in listOf(false, true)) {
            val normal = row(branch, dark, 1f)
            val large = row(branch, dark, 2f)
            assertTrue(large > normal * 1.6f, "Actual custom button text layout must grow at fontScale2; normal=$normal large=$large")
        }
    }

    private fun row(branch: AdaptiveControlBranch, dark: Boolean, fontScale: Float): Float {
        var labelHeight = 0f
        // Fixed first-row caller phases only; no pixels, private runtime state or inferred success.
        fun firstRowPhase(phase: String) {
            if (!dark && fontScale == 1f) {
                println("NATIVECMPKIT_ADAPTIVE_CUSTOM_PHASE branch=${branch.label} dark=$dark fontScale=$fontScale phase=$phase")
            }
        }
        firstRowPhase("compose-enter")
        runComposeUiTest {
            firstRowPhase("compose-body-entered")
            val enabled = mutableStateOf(true)
            val checked = mutableStateOf(false)
            val sliderValue = mutableStateOf(.5f)
            val names = listOf("button", "icon", "slider", "switch")
            val sources = names.associateWith { MutableInteractionSource() }
            val interactions = names.associateWith { mutableListOf<Interaction>() }
            val observedColors = mutableMapOf<String, Color>()
            var observedFontScale = 0f
            var density = 0f
            var buttonCalls = 0; var iconCalls = 0; var switchCalls = 0; var sliderCalls = 0
            var sliderFinished = 0
            firstRowPhase("set-content-enter")
            setContent {
                MaterialTheme(colorScheme = if (dark) darkColorScheme() else lightColorScheme()) {
                    val originalDensity = LocalDensity.current.density
                    CompositionLocalProvider(LocalDensity provides Density(originalDensity, fontScale)) {
                        for (name in names) {
                            val source = sources.getValue(name)
                            LaunchedEffect(source) { source.interactions.collect { interactions.getValue(name) += it } }
                        }
                        val currentDensity = LocalDensity.current
                        SideEffect { observedFontScale = currentDensity.fontScale; density = currentDensity.density }
                        Column(Modifier.background(MaterialTheme.colorScheme.surface)) {
                            AdaptiveButton({ buttonCalls++ }, Modifier.testTag("button"), enabled = enabled.value,
                                shape = RectangleShape,
                                contentPadding = PaddingValues(start = 23.dp, top = 31.dp, end = 27.dp, bottom = 37.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = Color.Red, contentColor = Color.Green,
                                    disabledContainerColor = Color.Blue, disabledContentColor = Color.Magenta),
                                interactionSource = sources.getValue("button")) {
                                val color = LocalContentColor.current
                                SideEffect { observedColors["button"] = color }
                                Text("Aa", Modifier.testTag("label"), fontSize = 10.sp)
                            }
                            AdaptiveIconButton({ iconCalls++ }, Modifier.testTag("icon"), enabled = enabled.value,
                                colors = IconButtonDefaults.iconButtonColors(containerColor = Color.Yellow, contentColor = Color.Blue,
                                    disabledContainerColor = Color.Cyan, disabledContentColor = Color.Red),
                                interactionSource = sources.getValue("icon")) {
                                val color = LocalContentColor.current
                                SideEffect { observedColors["icon"] = color }
                                Spacer(Modifier.size(8.dp))
                            }
                            AdaptiveSlider(sliderValue.value, { sliderValue.value = it; sliderCalls++ },
                                Modifier.width(240.dp).testTag("slider"), enabled = enabled.value,
                                colors = SliderDefaults.colors(activeTrackColor = Color.Red, inactiveTrackColor = Color.Blue,
                                    thumbColor = Color.Yellow, disabledActiveTrackColor = Color.Green,
                                    disabledInactiveTrackColor = Color.Magenta, disabledThumbColor = Color.Cyan),
                                interactionSource = sources.getValue("slider"), onValueChangeFinished = { sliderFinished++ })
                            AdaptiveSwitch(checked.value, { checked.value = it; switchCalls++ }, Modifier.testTag("switch"),
                                enabled = enabled.value, colors = SwitchDefaults.colors(
                                    checkedTrackColor = Color.Red, uncheckedTrackColor = Color.Blue,
                                    checkedThumbColor = Color.Yellow, uncheckedThumbColor = Color.White,
                                    disabledCheckedTrackColor = Color.Green, disabledUncheckedTrackColor = Color.Magenta,
                                    disabledCheckedThumbColor = Color.White, disabledUncheckedThumbColor = Color.Cyan,
                                    uncheckedIconColor = Color.Red, checkedIconColor = Color.Green,
                                    disabledUncheckedIconColor = Color.Blue, disabledCheckedIconColor = Color.Magenta),
                                interactionSource = sources.getValue("switch"), thumbContent = {
                                    val color = LocalContentColor.current
                                    SideEffect { observedColors["switch"] = color }
                                    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                                        Text("T", Modifier.testTag("thumb"), fontSize = 8.sp)
                                    }
                                })
                        }
                    }
                }
            }
            firstRowPhase("set-content-returned")
            assertEquals(fontScale, observedFontScale)
            val button = onNodeWithTag("button").fetchSemanticsNode().boundsInRoot
            val label = onNodeWithTag("label", useUnmergedTree = true).fetchSemanticsNode().boundsInRoot
            labelHeight = label.height
            assertTrue(abs(label.left - button.left - 23f * density) <= 1f, "Supplied start padding")
            assertTrue(abs(label.top - button.top - 31f * density) <= 1f, "Supplied top padding")
            assertTrue(abs(button.width - label.width - 50f * density) <= 1f, "Supplied horizontal padding")
            assertTrue(abs(button.height - label.height - 68f * density) <= 1f, "Supplied vertical padding")
            assertEquals(Color.Green, observedColors["button"])
            assertEquals(Color.Blue, observedColors["icon"])
            firstRowPhase("enabled-captures-enter")
            assertOpaqueSurface("button", Color.Red, corner = true)
            assertOpaqueSurface("icon", Color.Yellow)
            assertSliderTracks(Color.Red, Color.Blue)
            assertThumbGlyph(Color.Red, observedColors)
            firstRowPhase("enabled-captures-returned")

            firstRowPhase("paired-taps-enter")
            for (name in listOf("button", "icon", "switch")) {
                onNodeWithTag(name).performTouchInput { click() }
                waitForIdle()
                val events = interactions.getValue(name)
                waitUntil(timeoutMillis = 5_000) {
                    events.filterIsInstance<PressInteraction.Press>().size == 1 &&
                        events.filterIsInstance<PressInteraction.Release>().size == 1
                }
                val press = events.filterIsInstance<PressInteraction.Press>().single()
                assertEquals(1, events.filterIsInstance<PressInteraction.Release>().count { it.press === press }, name)
            }
            assertEquals(1, buttonCalls); assertEquals(1, iconCalls); assertEquals(1, switchCalls)
            firstRowPhase("paired-taps-returned")
            assertTrue(checked.value)
            assertThumbGlyph(Color.Green, observedColors)
            firstRowPhase("slider-drag-enter")
            onNodeWithTag("slider").performTouchInput {
                swipe(Offset(1f, centerY), Offset(width - 1f, centerY), durationMillis = 240)
            }
            waitForIdle()
            val sliderEvents = interactions.getValue("slider")
            waitUntil(timeoutMillis = 5_000) {
                sliderEvents.filterIsInstance<DragInteraction.Start>().size == 1 &&
                    sliderEvents.filterIsInstance<DragInteraction.Stop>().size == 1
            }
            val drag = sliderEvents.filterIsInstance<DragInteraction.Start>().single()
            assertEquals(1, sliderEvents.filterIsInstance<DragInteraction.Stop>().count { it.start === drag })
            assertTrue(sliderEvents.filterIsInstance<DragInteraction.Cancel>().none { it.start === drag })
            assertTrue(sliderCalls > 0, "Actual drag must reach the caller through its supplied interaction source")
            assertEquals(1, sliderFinished)
            assertEquals(1f, sliderValue.value)
            firstRowPhase("slider-drag-returned")

            runOnIdle { enabled.value = false; sliderValue.value = .5f }
            waitForIdle()
            assertEquals(Color.Magenta, observedColors["button"])
            assertEquals(Color.Red, observedColors["icon"])
            firstRowPhase("disabled-captures-enter")
            assertOpaqueSurface("button", Color.Blue, corner = true)
            assertOpaqueSurface("icon", Color.Cyan)
            assertSliderTracks(Color.Green, Color.Magenta)
            assertThumbGlyph(Color.Magenta, observedColors)
            runOnIdle { checked.value = false }
            waitForIdle()
            assertThumbGlyph(Color.Blue, observedColors)
            firstRowPhase("disabled-captures-returned")
            val sliderCallsAtDisable = sliderCalls
            val eventCountsAtDisable = interactions.mapValues { it.value.size }
            firstRowPhase("disabled-input-enter")
            for (name in names) onNodeWithTag(name).performTouchInput { click() }
            waitForIdle()
            assertEquals(1, buttonCalls); assertEquals(1, iconCalls); assertEquals(1, switchCalls)
            assertEquals(sliderCallsAtDisable, sliderCalls); assertEquals(1, sliderFinished)
            assertEquals(eventCountsAtDisable, interactions.mapValues { it.value.size },
                "Disabled custom controls cannot emit an enabled press/drag")
            firstRowPhase("disabled-input-returned")
            println("NATIVECMPKIT_ADAPTIVE_CUSTOM_ROW branch=${branch.label} dark=$dark fontScale=$fontScale " +
                "labelHeight=$labelHeight colorsVerified=true interactionsPaired=true disabledInert=true")
        }
        firstRowPhase("compose-returned")
        return labelHeight
    }

    private fun ComposeUiTest.assertOpaqueSurface(tag: String, expected: Color, corner: Boolean = false) {
        val screenshot = onNodeWithTag(tag).captureToImage()
        try {
            val pixels = screenshot.toPixelMap()
            val actual = if (corner) pixels[2, 2] else pixels[pixels.width / 2, pixels.height / 2]
            assertColor(expected, actual, "$tag actual surface")
        } finally {
            screenshot.asSkiaBitmap().close()
        }
    }

    private fun ComposeUiTest.assertSliderTracks(active: Color, inactive: Color) {
        val screenshot = onNodeWithTag("slider").captureToImage()
        try {
            val pixels = screenshot.toPixelMap()
            assertColor(active, pixels[pixels.width / 4, pixels.height / 2], "Actual active track")
            assertColor(inactive, pixels[pixels.width * 3 / 4, pixels.height / 2], "Actual inactive track")
        } finally {
            screenshot.asSkiaBitmap().close()
        }
    }

    private fun ComposeUiTest.assertThumbGlyph(expected: Color, observed: Map<String, Color>) {
        assertEquals(expected, observed["switch"], "Actual supplied custom thumb local")
        val screenshot = onNodeWithTag("thumb", useUnmergedTree = true).captureToImage()
        try {
            val pixels = screenshot.toPixelMap()
            assertTrue((0 until pixels.width).any { x -> (0 until pixels.height).any { y ->
                val actual = pixels[x, y]
                abs(actual.red - expected.red) < .1f && abs(actual.green - expected.green) < .1f &&
                    abs(actual.blue - expected.blue) < .1f && actual.alpha > .9f
            } }, "The actual custom thumb glyph must draw $expected")
        } finally {
            screenshot.asSkiaBitmap().close()
        }
    }

    private fun assertColor(expected: Color, actual: Color, label: String) {
        assertTrue(abs(expected.red - actual.red) < .1f && abs(expected.green - actual.green) < .1f &&
            abs(expected.blue - actual.blue) < .1f && actual.alpha > .9f, "$label expected=$expected actual=$actual")
    }
}
