package com.mohamedrejeb.calf.ui.internal

import kotlin.test.*

class NativePresentationStateTest {
    @Test fun hideDuringPresentationIsNotDropped() {
        val state = NativePresentationState()
        state.request(true)
        val show = requireNotNull(state.nextTransition())
        state.request(false)
        assertNull(state.nextTransition())
        assertTrue(state.complete(show))
        val hide = requireNotNull(state.nextTransition())
        assertFalse(hide.visible)
        assertTrue(state.complete(hide))
        assertEquals(NativePresentationState.Phase.Hidden, state.phase)
    }

    @Test fun disposalIsTerminalEvenWhenPresentationCompletesLater() {
        val state = NativePresentationState()
        state.request(true)
        val show = requireNotNull(state.nextTransition())
        state.dispose()
        state.request(true)
        state.complete(show)
        val hide = requireNotNull(state.nextTransition())
        state.complete(hide)
        assertTrue(state.disposed)
        assertFalse(state.requestedVisible)
        assertNull(state.nextTransition())
    }

    @Test fun repeatedRequestsCoalesceAndOldCompletionsCannotWin() {
        val state = NativePresentationState()
        state.request(true)
        val first = requireNotNull(state.nextTransition())
        state.request(true)
        assertNull(state.nextTransition())
        state.dismissedInteractively()
        assertFalse(state.complete(first))
        state.request(true)
        val second = requireNotNull(state.nextTransition())
        assertFalse(state.complete(first))
        assertTrue(state.complete(second))
    }

    @Test fun reopenWaitsForDismissCompletion() {
        val state = NativePresentationState()
        state.request(true)
        state.complete(requireNotNull(state.nextTransition()))
        state.request(false)
        val hide = requireNotNull(state.nextTransition())
        state.request(true)
        assertNull(state.nextTransition())
        state.complete(hide)
        assertTrue(requireNotNull(state.nextTransition()).visible)
    }
}
