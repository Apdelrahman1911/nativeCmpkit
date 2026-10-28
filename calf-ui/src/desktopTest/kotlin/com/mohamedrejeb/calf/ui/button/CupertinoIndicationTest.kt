package com.mohamedrejeb.calf.ui.button

import androidx.compose.foundation.background
import androidx.compose.foundation.IndicationNodeFactory
import androidx.compose.foundation.indication
import androidx.compose.foundation.interaction.InteractionSource
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.PressInteraction
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.ReusableContentHost
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toPixelMap
import androidx.compose.ui.node.DelegatableNode
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.captureToImage
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.dp
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertSame
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

    @Test fun actualIndicationNodeDetachesWithPendingReleaseAndReattachesWithoutStaleWork() = runComposeUiTest {
        val source = MutableInteractionSource()
        // Only observe the factory output. Every attached/drawn/collected node is
        // the actual production indication, not an adapter or a test renderer.
        val nodes = mutableListOf<DelegatableNode>()
        val actual = CupertinoIndication()
        val observed = object : IndicationNodeFactory {
            override fun create(interactionSource: InteractionSource): DelegatableNode =
                actual.create(interactionSource).also(nodes::add)
        }
        var active by mutableStateOf(true)
        mainClock.autoAdvance = false
        setContent {
            Box(Modifier.size(80.dp).background(Color.White)) {
                ReusableContentHost(active) {
                    Box(Modifier.size(80.dp).testTag("feedback")
                        .indication(source, observed).background(Color.Red))
                }
            }
        }
        assertEquals(1, nodes.size)
        val original = nodes.single().node
        assertTrue(original.isAttached)
        val first = PressInteraction.Press(Offset.Zero)
        runOnIdle { assertTrue(source.tryEmit(first)) }
        mainClock.advanceTimeBy(20)
        val pressed = onNodeWithTag("feedback").captureToImage().toPixelMap()
        assertTrue(pressed[pressed.width / 2, pressed.height / 2].green > .5f)
        runOnIdle { assertTrue(source.tryEmit(PressInteraction.Release(first))); active = false }
        mainClock.advanceTimeByFrame()
        onNodeWithTag("feedback").assertDoesNotExist()
        assertFalse(original.isAttached, "Deactivation must actually detach the production node")
        // A terminal event emitted while detached cannot become a remembered
        // press/release in the new collector. Do not recreate the observed node.
        runOnIdle { assertTrue(source.tryEmit(PressInteraction.Cancel(first))); active = true }
        mainClock.advanceTimeByFrame()
        assertEquals(1, nodes.size, "This test must exercise reattachment, not a new factory node")
        assertSame(original, nodes.single().node)
        assertTrue(original.isAttached)
        val reset = onNodeWithTag("feedback").captureToImage().toPixelMap()
        assertTrue(reset[reset.width / 2, reset.height / 2].green < .1f)
        val second = PressInteraction.Press(Offset.Zero)
        runOnIdle { assertTrue(source.tryEmit(second)) }
        mainClock.advanceTimeBy(700)
        val held = onNodeWithTag("feedback").captureToImage().toPixelMap()
        assertTrue(held[held.width / 2, held.height / 2].green > .5f,
            "Detached release work cannot clear the reattached node's current press")
        runOnIdle { assertTrue(source.tryEmit(PressInteraction.Cancel(second))) }
        mainClock.advanceTimeBy(700)
        val cancelled = onNodeWithTag("feedback").captureToImage().toPixelMap()
        assertTrue(cancelled[cancelled.width / 2, cancelled.height / 2].green < .1f)
        runOnIdle { active = false }
        mainClock.advanceTimeByFrame()
        assertFalse(original.isAttached)
    }
}
