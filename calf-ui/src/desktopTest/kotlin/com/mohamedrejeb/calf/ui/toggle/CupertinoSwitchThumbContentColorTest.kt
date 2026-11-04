// NativeCmpKit (2026-11-04): owning common implementation regression, real Compose on Desktop.
@file:OptIn(androidx.compose.ui.test.ExperimentalTestApi::class)

package com.mohamedrejeb.calf.ui.toggle

import androidx.compose.foundation.layout.Column
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toPixelMap
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.captureToImage
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.sp
import kotlin.math.abs
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class CupertinoSwitchThumbContentColorTest {
    @Test fun currentCallerIconColorsFollowEveryStateAndDoNotLeakToSiblingContent() = runComposeUiTest {
        val checked = mutableStateOf(false)
        val enabled = mutableStateOf(true)
        val replaced = mutableStateOf(false)
        val inherited = Color(0xFF8A5731)
        var thumbColor = Color.Unspecified
        var siblingColor = Color.Unspecified
        setContent {
            MaterialTheme {
                CompositionLocalProvider(LocalContentColor provides inherited) {
                    Column {
                        CupertinoSwitch(checked.value, {}, enabled = enabled.value,
                            colors = SwitchDefaults.colors(
                                uncheckedIconColor = if (replaced.value) Color.Yellow else Color.Red,
                                checkedIconColor = if (replaced.value) Color.Cyan else Color.Green,
                                disabledUncheckedIconColor = if (replaced.value) Color.White else Color.Blue,
                                disabledCheckedIconColor = if (replaced.value) Color.Black else Color.Magenta,
                            ), thumbContent = {
                                val current = LocalContentColor.current
                                SideEffect { thumbColor = current }
                                Text("T", Modifier.testTag("thumb"), fontSize = 8.sp)
                            })
                        val current = LocalContentColor.current
                        SideEffect { siblingColor = current }
                        Text("Sibling")
                    }
                }
            }
        }
        for (replacement in listOf(false, true)) {
            for ((isEnabled, isChecked, expected) in listOf(
                Triple(true, false, if (replacement) Color.Yellow else Color.Red),
                Triple(true, true, if (replacement) Color.Cyan else Color.Green),
                Triple(false, true, if (replacement) Color.Black else Color.Magenta),
                Triple(false, false, if (replacement) Color.White else Color.Blue),
            )) {
                runOnIdle { replaced.value = replacement; enabled.value = isEnabled; checked.value = isChecked }
                waitForIdle()
                onNodeWithTag("thumb", useUnmergedTree = true).fetchSemanticsNode()
                assertEquals(expected, thumbColor, "current caller colors enabled=$isEnabled checked=$isChecked replaced=$replacement")
                assertEquals(inherited, siblingColor, "Thumb content must not rewrite its parent's local")
            }
        }
    }

    @Test fun disabledCustomThumbInDarkLargeTextActuallyDrawsTheSuppliedIconColor() = runComposeUiTest {
        var observedFontScale = 0f
        var observedColor = Color.Unspecified
        setContent {
            MaterialTheme(colorScheme = darkColorScheme()) {
                val nativeDensity = LocalDensity.current.density
                CompositionLocalProvider(LocalDensity provides Density(nativeDensity, fontScale = 2f)) {
                    CupertinoSwitch(true, {}, enabled = false,
                        colors = SwitchDefaults.colors(disabledCheckedIconColor = Color.Magenta,
                            disabledCheckedThumbColor = Color.White), thumbContent = {
                            val fontScale = LocalDensity.current.fontScale
                            val color = LocalContentColor.current
                            SideEffect { observedFontScale = fontScale; observedColor = color }
                            Text("T", Modifier.testTag("thumb"), fontSize = 8.sp)
                        })
                }
            }
        }
        assertEquals(2f, observedFontScale)
        assertEquals(Color.Magenta, observedColor)
        val pixels = onNodeWithTag("thumb", useUnmergedTree = true).captureToImage().toPixelMap()
        assertTrue((0 until pixels.width).any { x -> (0 until pixels.height).any { y ->
            val pixel = pixels[x, y]
            abs(pixel.red - 1f) < .1f && pixel.green < .1f && abs(pixel.blue - 1f) < .1f
        } }, "The real glyph snapshot must contain the supplied disabled magenta, not inherited dark-theme text")
    }
}
