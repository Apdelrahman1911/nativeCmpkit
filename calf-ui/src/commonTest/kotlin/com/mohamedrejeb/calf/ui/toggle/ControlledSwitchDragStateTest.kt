package com.mohamedrejeb.calf.ui.toggle

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull

class ControlledSwitchDragStateTest {
    @Test fun finishingReturnsAProposalAndClearsThePreviewEvenIfOwnerRejectsIt() {
        val state = ControlledSwitchDragState()
        state.start(false)
        state.dragBy(.8f)
        assertEquals(true, state.finish())
        assertNull(state.previewFraction)
        assertNull(state.finish())
    }

    @Test fun cancellingDoesNotProposeAValue() {
        val state = ControlledSwitchDragState()
        state.start(false)
        state.dragBy(1f)
        state.cancel()
        assertNull(state.previewFraction)
        assertNull(state.finish())
    }

    @Test fun draggingAcrossThresholdThenBackKeepsOriginalState() {
        val state = ControlledSwitchDragState()
        state.start(false)
        state.dragBy(.7f)
        state.dragBy(-.4f)
        assertEquals(false, state.finish())
    }

    @Test fun boundsAndNonFiniteDeltasCannotEscapeTheUnitInterval() {
        val state = ControlledSwitchDragState()
        state.start(true)
        state.dragBy(10f)
        assertEquals(1f, state.previewFraction)
        state.dragBy(Float.NaN)
        assertEquals(1f, state.previewFraction)
        state.dragBy(-10f)
        assertEquals(0f, state.previewFraction)
    }
}
