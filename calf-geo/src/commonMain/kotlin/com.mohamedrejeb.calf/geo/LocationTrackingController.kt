package com.mohamedrejeb.calf.geo

import androidx.compose.runtime.State
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.mutableStateOf
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume

/** Platform adapter boundary, not replacement Android/iOS classes in a test probe. */
internal interface LocationTrackingBackend {
    fun permissionAccuracy(): LocationPermissionAccuracy?
    fun createSubscription(): LocationSubscription
}

internal interface LocationSubscription {
    fun start(callbacks: LocationSubscriptionCallbacks)
    /** Must observe asynchronous removal and clean up even if registration is pending. */
    fun stop(onComplete: (LocationTrackingError?) -> Unit)
}

internal interface LocationSubscriptionCallbacks {
    fun onRegistered(error: LocationTrackingError?)
    fun onLocation(fix: LocationFix)
    fun onAvailability(available: Boolean)
    fun onFailure(error: LocationTrackingError)
}

/**
 * Main-thread-confined session/owner state machine. Android dispatches all public
 * operations and provider callbacks to main. There is no unowned coroutine scope,
 * channel, Activity, or native object here. Tests exercise this production class.
 */
internal class LocationTrackingController(val capability: LocationTrackingCapability) {
    private val state = mutableStateOf(
        LocationTrackingSnapshot(
            if (capability == LocationTrackingCapability.Unsupported) LocationTrackingPhase.Unsupported
            else LocationTrackingPhase.Unbound
        )
    )
    val snapshotState: State<LocationTrackingSnapshot> = state
    val fixState: State<LocationFix?> = derivedStateOf { state.value.fix }
    val locationState: State<LatLng> = derivedStateOf { state.value.fix?.coordinates ?: UnknownCoordinates }
    val extendedLocationState: State<ExtendedLocation> = derivedStateOf { state.value.fix.toLegacyLocation() }

    private var backend: LocationTrackingBackend? = null
    private var session: Session? = null
    private var version = 0L
    private var wantsTracking = false
    private var closed = false
    private val pendingRemovals = mutableSetOf<Session>()

    private class Session(
        val backend: LocationTrackingBackend,
        val subscription: LocationSubscription,
        var completion: ((LocationStartResult) -> Unit)?,
    ) {
        var registered = false
        var fix: LocationFix? = null
        var removed = false

        fun complete(result: LocationStartResult) {
            val callback = completion
            completion = null
            callback?.invoke(result)
        }
    }

    fun bind(newBackend: LocationTrackingBackend, restartAllowed: Boolean = true) {
        check(!closed) { "A closed LocationTracker cannot be rebound" }
        check(capability == LocationTrackingCapability.Foreground)
        val previous = session
        val wasRequested = wantsTracking
        val restart = wasRequested && restartAllowed
        wantsTracking = restart
        version++
        session = null
        backend = newBackend
        if (wasRequested && !restartAllowed) reset(
            LocationTrackingPhase.Failed, error = LocationTrackingError(LocationTrackingFailure.OwnerInactive)
        ) else reset(LocationTrackingPhase.Idle)
        if (previous != null) {
            remove(previous)
            previous.complete(LocationStartResult.Cancelled)
        }
        // A completion callback may have explicitly stopped or rebound the tracker.
        if (restart && wantsTracking && backend === newBackend && session == null && !closed) start { }
    }

    fun unbind() {
        if (closed) return
        val previous = session
        version++
        session = null
        backend = null
        wantsTracking = false
        reset(LocationTrackingPhase.Unbound)
        if (previous != null) {
            remove(previous)
            previous.complete(LocationStartResult.Cancelled)
        }
    }

    /** Returns a cancellation handle for this request only, never for a later generation. */
    fun start(completion: (LocationStartResult) -> Unit): () -> Unit {
        if (closed) {
            completion(LocationStartResult.Failed(LocationTrackingError(LocationTrackingFailure.Closed)))
            return { }
        }
        if (capability == LocationTrackingCapability.Unsupported) {
            completion(LocationStartResult.Unsupported)
            return { }
        }
        session?.let {
            completion(if (it.registered) LocationStartResult.AlreadyStarted else LocationStartResult.InProgress)
            return { }
        }
        val activeBackend = backend
        if (activeBackend == null) {
            val error = LocationTrackingError(LocationTrackingFailure.NotBound)
            reset(LocationTrackingPhase.Unbound, error = error)
            completion(LocationStartResult.Failed(error))
            return { }
        }
        val accuracy: LocationPermissionAccuracy?
        val subscription: LocationSubscription
        try {
            accuracy = activeBackend.permissionAccuracy()
            if (accuracy == null) {
                wantsTracking = false
                val error = LocationTrackingError(LocationTrackingFailure.PermissionDenied)
                reset(LocationTrackingPhase.Failed, error = error)
                completion(LocationStartResult.Failed(error))
                return { }
            }
            subscription = activeBackend.createSubscription()
        } catch (failure: Exception) {
            wantsTracking = false
            val error = LocationTrackingError(LocationTrackingFailure.ProviderError, failure)
            reset(LocationTrackingPhase.Failed, error = error)
            completion(LocationStartResult.Failed(error))
            return { }
        }
        val current = Session(activeBackend, subscription, completion)
        version++
        session = current
        wantsTracking = true
        reset(LocationTrackingPhase.Starting, permissionAccuracy = accuracy)
        try {
            subscription.start(object : LocationSubscriptionCallbacks {
                override fun onRegistered(error: LocationTrackingError?) {
                    if (session !== current || current.registered) return
                    if (error != null) {
                        fail(current, error)
                        return
                    }
                    if (!refreshPermission(current)) return
                    current.registered = true
                    state.value = state.value.copy(phase = LocationTrackingPhase.Tracking, fix = current.fix)
                    current.complete(LocationStartResult.Started)
                }

                override fun onLocation(fix: LocationFix) = accept(current, fix)

                override fun onAvailability(available: Boolean) {
                    if (session === current) state.value = state.value.copy(isProviderAvailable = available)
                }

                override fun onFailure(error: LocationTrackingError) = fail(current, error)
            })
        } catch (failure: Exception) {
            fail(current, LocationTrackingError(LocationTrackingFailure.ProviderError, failure))
        }
        return { if (session === current) stop() }
    }

    suspend fun awaitStart(dispatchCancellation: (() -> Unit) -> Unit = { it() }): LocationStartResult =
        suspendCancellableCoroutine { continuation ->
            if (!continuation.isActive) return@suspendCancellableCoroutine
            var cancel: (() -> Unit)? = null
            continuation.invokeOnCancellation { dispatchCancellation { cancel?.invoke() } }
            val requestCancellation = start { result -> if (continuation.isActive) continuation.resume(result) }
            cancel = requestCancellation
            // Handles cancellation before the handle was installed (including synchronous adapters).
            if (continuation.isCancelled) requestCancellation()
        }

    fun refreshPermission() {
        val current = session ?: return
        refreshPermission(current)
    }

    fun rejectStart(error: LocationTrackingError): LocationStartResult.Failed {
        val current = session
        if (current != null) fail(current, error)
        else if (!closed) {
            wantsTracking = false
            version++
            state.value = state.value.copy(phase = LocationTrackingPhase.Failed, error = error)
        }
        return LocationStartResult.Failed(error)
    }

    /** Compatibility callback bridge; the library itself uses per-generation callbacks. */
    fun acceptCurrent(fix: LocationFix) {
        session?.let { accept(it, fix) }
    }

    private fun refreshPermission(current: Session): Boolean {
        if (session !== current) return false
        val accuracy = try {
            current.backend.permissionAccuracy()
        } catch (failure: Exception) {
            fail(current, LocationTrackingError(LocationTrackingFailure.ProviderError, failure))
            return false
        }
        if (accuracy == null) {
            fail(current, LocationTrackingError(LocationTrackingFailure.PermissionDenied))
            return false
        }
        state.value = state.value.copy(permissionAccuracy = accuracy)
        return true
    }

    private fun accept(current: Session, fix: LocationFix) {
        if (session !== current) return
        if (!fix.coordinates.isValid) {
            fail(current, LocationTrackingError(LocationTrackingFailure.InvalidLocation))
            return
        }
        if (!refreshPermission(current) || fix.isOlderThan(current.fix)) return
        current.fix = fix
        // A fix delivered before the registration Task succeeds is not a successful start.
        if (current.registered) state.value = state.value.copy(fix = fix)
    }

    private fun fail(current: Session, error: LocationTrackingError) {
        if (session !== current) return
        version++
        session = null
        wantsTracking = false
        state.value = state.value.copy(phase = LocationTrackingPhase.Failed, error = error)
        remove(current)
        current.complete(LocationStartResult.Failed(error))
    }

    private fun reset(
        phase: LocationTrackingPhase,
        error: LocationTrackingError? = null,
        permissionAccuracy: LocationPermissionAccuracy? = null,
    ) {
        state.value = LocationTrackingSnapshot(
            phase = phase, error = error, permissionAccuracy = permissionAccuracy,
            cleanupError = state.value.cleanupError,
        )
    }

    fun stop() {
        if (closed || capability == LocationTrackingCapability.Unsupported) return
        wantsTracking = false
        val current = session
        if (current == null) {
            retryFailedRemovals()
            return
        }
        session = null // Invalidate callbacks BEFORE invoking provider removal or caller completion.
        val stopVersion = ++version
        state.value = state.value.copy(phase = LocationTrackingPhase.Stopping)
        remove(current) { error ->
            if (!closed && version == stopVersion && session == null) {
                state.value = state.value.copy(
                    phase = if (error == null) LocationTrackingPhase.Stopped else LocationTrackingPhase.Failed,
                    error = error,
                )
            }
        }
        current.complete(LocationStartResult.Cancelled)
    }

    private fun remove(current: Session, completion: (LocationTrackingError?) -> Unit = { }) {
        if (current.removed) return
        current.removed = true
        pendingRemovals += current
        var completed = false
        val finish: (LocationTrackingError?) -> Unit = { error ->
            if (!completed) {
                completed = true
                if (error == null) pendingRemovals -= current else current.removed = false
                if (!closed) {
                    if (error != null) state.value = state.value.copy(cleanupError = error)
                    else if (pendingRemovals.isEmpty()) state.value = state.value.copy(cleanupError = null)
                }
                completion(error)
            }
        }
        try {
            current.subscription.stop(finish)
        } catch (failure: Exception) {
            finish(LocationTrackingError(LocationTrackingFailure.RemovalFailed, failure))
        }
    }

    /** Explicit repeated stop/close retries failed removals; never an unbounded automatic retry loop. */
    private fun retryFailedRemovals() {
        val failed = pendingRemovals.filter { !it.removed }
        if (failed.isEmpty()) return
        val retryVersion = ++version
        var remaining = failed.size
        if (!closed) state.value = state.value.copy(phase = LocationTrackingPhase.Stopping)
        for (previous in failed) remove(previous) {
            remaining--
            if (!closed && remaining == 0 && session == null && version == retryVersion) {
                state.value = state.value.copy(
                    phase = when {
                        pendingRemovals.isEmpty() -> LocationTrackingPhase.Stopped
                        state.value.cleanupError != null -> LocationTrackingPhase.Failed
                        else -> LocationTrackingPhase.Stopping
                    },
                    error = state.value.cleanupError,
                )
            }
        }
    }

    fun close() {
        if (closed) {
            retryFailedRemovals()
            return
        }
        retryFailedRemovals()
        val previous = session
        closed = true
        version++
        session = null
        backend = null
        wantsTracking = false
        state.value = LocationTrackingSnapshot(LocationTrackingPhase.Closed)
        if (previous != null) {
            remove(previous)
            previous.complete(LocationStartResult.Cancelled)
        }
    }
}

private val UnknownCoordinates = LatLng(Double.NaN, Double.NaN)

private fun LocationFix?.toLegacyLocation(): ExtendedLocation = ExtendedLocation(
    location = Location(this?.coordinates ?: UnknownCoordinates, this?.coordinatesAccuracyMeters ?: Double.NaN),
    azimuth = Azimuth(this?.courseDegrees ?: Double.NaN, this?.courseAccuracyDegrees),
    speed = Speed(this?.speedMps ?: Double.NaN, this?.speedAccuracyMps),
    altitude = Altitude(this?.altitudeMeters ?: Double.NaN, this?.altitudeAccuracyMeters),
    timestampMs = this?.timestampMs ?: 0L,
)

private fun LocationFix.isOlderThan(previous: LocationFix?): Boolean {
    if (previous == null) return false
    val monotonic = elapsedRealtimeNanos
    val previousMonotonic = previous.elapsedRealtimeNanos
    if (monotonic != null && previousMonotonic != null) return monotonic < previousMonotonic
    val epoch = timestampMs
    val previousEpoch = previous.timestampMs
    return epoch != null && previousEpoch != null && epoch < previousEpoch
}
