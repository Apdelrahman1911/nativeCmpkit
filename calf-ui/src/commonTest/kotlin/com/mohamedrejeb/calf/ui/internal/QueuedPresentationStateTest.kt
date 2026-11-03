// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.internal

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class QueuedPresentationStateTest {
    @Test fun queuedHideInvalidatesItsUnstartedShowAndCanImmediatelyReopen() {
        val state = NativePresentationState()
        state.request(true)
        val oldShow = assertNotNull(state.nextTransition())
        state.request(false)
        assertTrue(state.cancelQueuedPresentation())
        assertEquals(NativePresentationState.Phase.Hidden, state.phase)
        assertFalse(state.complete(oldShow))
        assertNull(state.nextTransition())
        state.request(true)
        val replacement = assertNotNull(state.nextTransition())
        assertFalse(state.complete(oldShow))
        assertTrue(state.complete(replacement))
        assertEquals(NativePresentationState.Phase.Presented, state.phase)
    }

    @Test fun cancellationRequiresAPendingShowAndAHiddenIntent() {
        val state = NativePresentationState()
        assertFalse(state.cancelQueuedPresentation())
        state.request(true)
        val show = assertNotNull(state.nextTransition())
        assertFalse(state.cancelQueuedPresentation())
        assertTrue(state.complete(show))
        state.request(false)
        assertFalse(state.cancelQueuedPresentation())
        val hide = assertNotNull(state.nextTransition())
        assertFalse(state.cancelQueuedPresentation())
        assertTrue(state.complete(hide))
        assertFalse(state.cancelQueuedPresentation())
    }

    @Test fun disposalOfAQueuedPresentationStaysTerminal() {
        val state = NativePresentationState()
        state.request(true)
        val show = assertNotNull(state.nextTransition())
        state.dispose()
        assertTrue(state.cancelQueuedPresentation())
        state.request(true)
        assertFalse(state.complete(show))
        assertFalse(state.cancelQueuedPresentation())
        assertFalse(state.requestedVisible)
        assertTrue(state.disposed)
        assertNull(state.nextTransition())
    }

    @Test fun repeatedQueuedCancellationsCannotCompleteAReplacementToken() {
        val state = NativePresentationState()
        val oldShows = mutableListOf<NativePresentationState.Transition>()
        repeat(32) {
            state.request(true)
            val pending = assertNotNull(state.nextTransition())
            oldShows.forEach { assertFalse(state.complete(it)) }
            oldShows += pending
            state.request(false)
            assertTrue(state.cancelQueuedPresentation())
            assertFalse(state.complete(pending))
            assertNull(state.nextTransition())
        }
        state.request(true)
        val last = assertNotNull(state.nextTransition())
        oldShows.forEach { assertFalse(state.complete(it)) }
        assertTrue(state.complete(last))
        oldShows.forEach { assertFalse(state.complete(it)) }
        assertEquals(NativePresentationState.Phase.Presented, state.phase)
    }
}
