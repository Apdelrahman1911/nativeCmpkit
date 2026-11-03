package com.mohamedrejeb.calf.ui.internal

/**
 * Requested/actual visibility for asynchronous native presentations. All calls belong to Main.
 * Drivers execute one returned transition, then complete that exact token. A hide/dispose during
 * presentation is retained; stale completions cannot resurrect a dismissed owner.
 */
internal class NativePresentationState {
    enum class Phase { Hidden, Presenting, Presented, Dismissing }
    data class Transition(val generation: Long, val visible: Boolean)

    var phase = Phase.Hidden
        private set
    var requestedVisible = false
        private set
    var disposed = false
        private set
    private var generation = 0L

    fun request(visible: Boolean) {
        if (!disposed) requestedVisible = visible
    }

    fun dispose() {
        disposed = true
        requestedVisible = false
    }

    fun nextTransition(): Transition? = when {
        phase == Phase.Hidden && requestedVisible -> {
            phase = Phase.Presenting
            Transition(++generation, true)
        }
        phase == Phase.Presented && !requestedVisible -> {
            phase = Phase.Dismissing
            Transition(++generation, false)
        }
        else -> null
    }

    fun complete(transition: Transition): Boolean {
        if (transition.generation != generation ||
            phase != if (transition.visible) Phase.Presenting else Phase.Dismissing) return false
        phase = if (transition.visible) Phase.Presented else Phase.Hidden
        return true
    }

    /**
     * The driver removed this owner from its admission queue before UIKit started presenting.
     * Never call this for an admitted animation: that animation must complete its own token.
     */
    fun cancelQueuedPresentation(): Boolean {
        if (phase != Phase.Presenting || requestedVisible) return false
        generation++
        phase = Phase.Hidden
        return true
    }

    /** UIKit completed an interactive dismissal, not a completion belonging to a driver token. */
    fun dismissedInteractively() {
        generation++
        requestedVisible = false
        phase = Phase.Hidden
    }
}
