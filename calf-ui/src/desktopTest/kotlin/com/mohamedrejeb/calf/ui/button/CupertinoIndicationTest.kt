package com.mohamedrejeb.calf.ui.button

import androidx.compose.foundation.background
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.PressInteraction
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.size
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toPixelMap
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.captureToImage
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.dp
import kotlin.test.Test
import kotlin.test.assertTrue

@OptIn(ExperimentalTestApi::class)
class CupertinoIndicationTest {
    @Test fun releaseThenRepressKeepsTheNewPressHighlighted() = runComposeUiTest {
        val source = MutableInteractionSource()
        setContent {
            Box(Modifier.background(Color.White)) {
                CupertinoButton({}, Modifier.testTag("button"),
                    colors = CupertinoButtonDefaults.filledButtonColors(containerColor = Color.Red), interactionSource = source) {
                    Spacer(Modifier.size(32.dp))
                }
            }
        }
        mainClock.autoAdvance = false
        val first = PressInteraction.Press(Offset.Zero)
        val second = PressInteraction.Press(Offset.Zero)
        runOnIdle { source.tryEmit(first) }
        mainClock.advanceTimeBy(20)
        runOnIdle { source.tryEmit(PressInteraction.Release(first)) }
        mainClock.advanceTimeBy(20)
        runOnIdle { source.tryEmit(second) }
        mainClock.advanceTimeBy(500)
        val held = onNodeWithTag("button").captureToImage().toPixelMap()
        assertTrue(held[held.width / 2, held.height / 2].green > .5f, "the held red button must retain its translucent pressed appearance")
        runOnIdle { source.tryEmit(PressInteraction.Release(second)) }
        mainClock.advanceTimeBy(700)
        val released = onNodeWithTag("button").captureToImage().toPixelMap()
        assertTrue(released[released.width / 2, released.height / 2].green < .1f)
    }

    @Test fun cancellingOneOfTwoPressesDoesNotClearTheOther() = runComposeUiTest {
        val source = MutableInteractionSource()
        setContent {
            Box(Modifier.background(Color.White)) {
                CupertinoButton({}, Modifier.testTag("button"),
                    colors = CupertinoButtonDefaults.filledButtonColors(containerColor = Color.Red), interactionSource = source) {
                    Spacer(Modifier.size(32.dp))
                }
            }
        }
        mainClock.autoAdvance = false
        val first = PressInteraction.Press(Offset.Zero)
        val second = PressInteraction.Press(Offset.Zero)
        runOnIdle { source.tryEmit(first); source.tryEmit(second) }
        mainClock.advanceTimeBy(20)
        runOnIdle { source.tryEmit(PressInteraction.Cancel(first)) }
        mainClock.advanceTimeBy(500)
        val held = onNodeWithTag("button").captureToImage().toPixelMap()
        assertTrue(held[held.width / 2, held.height / 2].green > .5f)
    }
}
