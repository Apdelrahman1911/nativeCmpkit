package com.mohamedrejeb.calf.ui.controls

import androidx.compose.foundation.background
import androidx.compose.foundation.interaction.Interaction
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.PressInteraction
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.IconButtonDefaults
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.SwitchDefaults
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.graphics.toPixelMap
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.assertHeightIsEqualTo
import androidx.compose.ui.test.assertWidthIsEqualTo
import androidx.compose.ui.test.captureToImage
import androidx.compose.ui.test.click
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.dp
import com.mohamedrejeb.calf.ui.button.AdaptiveButton
import com.mohamedrejeb.calf.ui.button.AdaptiveIconButton
import com.mohamedrejeb.calf.ui.slider.AdaptiveSlider
import com.mohamedrejeb.calf.ui.toggle.AdaptiveSwitch
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/** Tests the actual iOS adaptive APIs. The executed OS version determines their selected branch. */
@OptIn(ExperimentalTestApi::class)
class AdaptiveControlForwardingTest {
    @Test fun buttonForwardsShapePaddingEnabledAndDisabledColorsAndInteractionSource() = runComposeUiTest {
        val enabled = mutableStateOf(true)
        val source = MutableInteractionSource()
        val interactions = mutableListOf<Interaction>()
        var contentColor = Color.Unspecified
        var clicks = 0
        setContent {
            LaunchedEffect(source) { source.interactions.collect { interactions += it } }
            Box(Modifier.background(Color.White)) {
                AdaptiveButton(
                    onClick = { clicks++ }, modifier = Modifier.testTag("button"), enabled = enabled.value,
                    shape = RectangleShape,
                    contentPadding = PaddingValues(start = 23.dp, top = 31.dp, end = 27.dp, bottom = 37.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color.Red, contentColor = Color.Green,
                        disabledContainerColor = Color.Blue, disabledContentColor = Color.Magenta),
                    interactionSource = source,
                ) {
                    val current = LocalContentColor.current
                    SideEffect { contentColor = current }
                    Spacer(Modifier.size(8.dp, 10.dp))
                }
            }
        }
        onNodeWithTag("button").assertWidthIsEqualTo(58.dp).assertHeightIsEqualTo(78.dp)
        assertEquals(Color.Green, contentColor)
        val enabledPixels = onNodeWithTag("button").captureToImage().toPixelMap()
        val corner = enabledPixels[2, 2]
        assertTrue(corner.red > .8f && corner.green < .2f && corner.blue < .2f,
            "Rectangle shape and red surface must reach the corner, got $corner")
        onNodeWithTag("button").performTouchInput { click() }
        waitForIdle()
        assertEquals(1, clicks)
        val press = interactions.filterIsInstance<PressInteraction.Press>().single()
        assertEquals(1, interactions.filterIsInstance<PressInteraction.Release>().count { it.press === press })
        runOnIdle { enabled.value = false }
        assertEquals(Color.Magenta, contentColor)
        onNodeWithTag("button").performTouchInput { click() }
        assertEquals(1, clicks)
        val disabledPixels = onNodeWithTag("button").captureToImage().toPixelMap()
        val disabled = disabledPixels[disabledPixels.width / 2, 12]
        assertTrue(disabled.blue > .8f && disabled.red < .2f && disabled.green < .2f,
            "Explicit disabled blue must not be multiplied by another global disabled alpha, got $disabled")
    }

    @Test fun iconButtonForwardsBothContainerAndContentColorStates() = runComposeUiTest {
        val enabled = mutableStateOf(true)
        var contentColor = Color.Unspecified
        setContent {
            Box(Modifier.background(Color.White)) {
                AdaptiveIconButton({}, Modifier.testTag("icon"), enabled = enabled.value,
                    colors = IconButtonDefaults.iconButtonColors(containerColor = Color.Red, contentColor = Color.Green,
                        disabledContainerColor = Color.Blue, disabledContentColor = Color.Magenta)) {
                    val current = LocalContentColor.current
                    SideEffect { contentColor = current }
                    Spacer(Modifier.size(8.dp))
                }
            }
        }
        assertEquals(Color.Green, contentColor)
        val enabledPixels = onNodeWithTag("icon").captureToImage().toPixelMap()
        val enabledColor = enabledPixels[enabledPixels.width / 2, enabledPixels.height / 2]
        assertTrue(enabledColor.red > .8f && enabledColor.blue < .2f)
        runOnIdle { enabled.value = false }
        assertEquals(Color.Magenta, contentColor)
        val disabledPixels = onNodeWithTag("icon").captureToImage().toPixelMap()
        val disabledColor = disabledPixels[disabledPixels.width / 2, disabledPixels.height / 2]
        assertTrue(disabledColor.blue > .8f && disabledColor.red < .2f && disabledColor.green < .2f)
    }

    @Test fun sliderForwardsTrackAndDisabledTrackColors() = runComposeUiTest {
        val enabled = mutableStateOf(true)
        setContent {
            Box(Modifier.background(Color.White)) {
                AdaptiveSlider(.5f, {}, Modifier.width(240.dp).testTag("slider"), enabled = enabled.value,
                    colors = SliderDefaults.colors(
                        activeTrackColor = Color.Red, inactiveTrackColor = Color.Blue, thumbColor = Color.Yellow,
                        disabledActiveTrackColor = Color.Green, disabledInactiveTrackColor = Color.Magenta,
                        disabledThumbColor = Color.Cyan,
                    ))
            }
        }
        val enabledPixels = onNodeWithTag("slider").captureToImage().toPixelMap()
        val active = enabledPixels[enabledPixels.width / 4, enabledPixels.height / 2]
        val inactive = enabledPixels[enabledPixels.width * 3 / 4, enabledPixels.height / 2]
        assertTrue(active.red > .9f && active.green < .1f && active.blue < .1f)
        assertTrue(inactive.blue > .9f && inactive.red < .1f && inactive.green < .1f)
        runOnIdle { enabled.value = false }
        val disabledPixels = onNodeWithTag("slider").captureToImage().toPixelMap()
        val disabledActive = disabledPixels[disabledPixels.width / 4, disabledPixels.height / 2]
        val disabledInactive = disabledPixels[disabledPixels.width * 3 / 4, disabledPixels.height / 2]
        assertTrue(disabledActive.green > .9f && disabledActive.red < .1f && disabledActive.blue < .1f)
        assertTrue(disabledInactive.red > .9f && disabledInactive.blue > .9f && disabledInactive.green < .1f)
    }

    @Test fun switchForwardsThumbContentAndItsIconColorForAllStates() = runComposeUiTest {
        val enabled = mutableStateOf(true)
        val checked = mutableStateOf(false)
        var contentColor = Color.Unspecified
        setContent {
            AdaptiveSwitch(checked.value, { checked.value = it }, Modifier.testTag("switch"), enabled = enabled.value,
                colors = SwitchDefaults.colors(
                    uncheckedIconColor = Color.Red, checkedIconColor = Color.Green,
                    disabledUncheckedIconColor = Color.Blue, disabledCheckedIconColor = Color.Magenta,
                ), thumbContent = {
                    val current = LocalContentColor.current
                    SideEffect { contentColor = current }
                    Box(Modifier.size(4.dp).testTag("customThumb"))
                })
        }
        onNodeWithTag("customThumb", useUnmergedTree = true).fetchSemanticsNode()
        assertEquals(Color.Red, contentColor)
        runOnIdle { checked.value = true }
        assertEquals(Color.Green, contentColor)
        runOnIdle { enabled.value = false }
        assertEquals(Color.Magenta, contentColor)
        runOnIdle { checked.value = false }
        assertEquals(Color.Blue, contentColor)
    }
}
