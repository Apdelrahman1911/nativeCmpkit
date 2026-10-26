// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.geo

import android.content.Context
import android.os.Handler
import android.os.Looper
import androidx.compose.runtime.State
import androidx.fragment.app.FragmentManager
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.Priority
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Android foreground tracker. Bind/stop/close are main-thread operations. Start
 * may be called from any coroutine dispatcher and is marshalled to main. The
 * bound owner stopping stops tracking; callers explicitly restart on returning
 * to foreground. No background service or permission prompt is created.
 */
actual class LocationTracker(
    interval: Long = 1000,
    priority: Int = Priority.PRIORITY_HIGH_ACCURACY,
) : LocationCallback() {
    private val controller = LocationTrackingController(LocationTrackingCapability.Foreground)
    private val mainHandler = Handler(Looper.getMainLooper())
    private val request = LocationRequest.Builder(priority, interval.also {
        require(it > 0) { "Location interval must be positive" }
    }).build()
    private var backendFactory: (Context) -> LocationTrackingBackend = { AndroidLocationTrackingBackend(it, request) }
    private var boundOwner: BoundOwner? = null

    internal constructor(factory: (Context) -> LocationTrackingBackend) : this() {
        backendFactory = factory
    }

    private class BoundOwner(
        val lifecycle: Lifecycle,
        val context: Context,
        val observer: LifecycleEventObserver,
    )

    actual val capability: LocationTrackingCapability = LocationTrackingCapability.Foreground
    actual val snapshotState: State<LocationTrackingSnapshot> = controller.snapshotState
    actual val fixState: State<LocationFix?> = controller.fixState
    actual val locationState: State<LatLng> = controller.locationState
    actual val extendedLocationState: State<ExtendedLocation> = controller.extendedLocationState

    /** Kept for source/binary signature compatibility; fragments are not used for foreground tracking. */
    @Deprecated("FragmentManager is not used. Use bind(lifecycle, context).")
    @Suppress("UNUSED_PARAMETER")
    fun bind(lifecycle: Lifecycle, context: Context, fragmentManager: FragmentManager) = bind(lifecycle, context)

    fun bind(lifecycle: Lifecycle, context: Context) {
        requireMainThread()
        check(lifecycle.currentState != Lifecycle.State.DESTROYED) { "Cannot bind a destroyed lifecycle" }
        check(snapshotState.value.phase != LocationTrackingPhase.Closed) { "A closed LocationTracker cannot be rebound" }
        val applicationContext = context.applicationContext ?: context
        val oldOwner = boundOwner
        if (oldOwner?.lifecycle === lifecycle && oldOwner.context === applicationContext) return
        // Construct before replacing the current owner: a failing factory cannot orphan its observer.
        val backend = backendFactory(applicationContext)
        var owner: BoundOwner? = null
        val observer = LifecycleEventObserver { _, event ->
            if (boundOwner !== owner) return@LifecycleEventObserver
            when (event) {
                Lifecycle.Event.ON_RESUME -> controller.refreshPermission()
                Lifecycle.Event.ON_STOP -> controller.stop()
                Lifecycle.Event.ON_DESTROY -> unbind()
                else -> Unit
            }
        }
        owner = BoundOwner(lifecycle, applicationContext, observer)
        oldOwner?.lifecycle?.removeObserver(oldOwner.observer)
        boundOwner = owner
        controller.bind(backend, restartAllowed = lifecycle.currentState.isAtLeast(Lifecycle.State.STARTED))
        // Resuming an old pending start may reentrantly close/rebind the tracker.
        if (boundOwner === owner) lifecycle.addObserver(observer)
    }

    /** Detaches this owner and invalidates pending callbacks; a later bind is permitted. */
    fun unbind() {
        requireMainThread()
        val owner = boundOwner
        boundOwner = null
        owner?.lifecycle?.removeObserver(owner.observer)
        controller.unbind()
    }

    actual suspend fun startTracking() { startTrackingWithResult() }

    actual suspend fun startTrackingWithResult(): LocationStartResult = withContext(Dispatchers.Main.immediate) {
        val owner = boundOwner
        if (owner != null && !owner.lifecycle.currentState.isAtLeast(Lifecycle.State.STARTED)) {
            controller.rejectStart(LocationTrackingError(LocationTrackingFailure.OwnerInactive))
        } else controller.awaitStart(::onMainThread)
    }

    actual fun stopTracking() {
        requireMainThread()
        controller.stop()
    }

    actual fun close() {
        requireMainThread()
        val owner = boundOwner
        boundOwner = null
        owner?.lifecycle?.removeObserver(owner.observer)
        controller.close()
    }

    /**
     * Legacy callback signature remains available. Library subscriptions use
     * distinct callbacks per generation, never this shared callback identity.
     */
    override fun onLocationResult(locationResult: LocationResult) {
        val fix = locationResult.lastLocation?.toLocationFix() ?: return
        onMainThread { controller.acceptCurrent(fix) }
    }

    private fun onMainThread(action: () -> Unit) {
        if (Looper.myLooper() == Looper.getMainLooper()) action() else mainHandler.post { action() }
    }

    private fun requireMainThread() {
        check(Looper.myLooper() == Looper.getMainLooper()) { "LocationTracker bind/stop/close must run on the Android main thread" }
    }
}

actual fun createLocationTracker(): LocationTracker = LocationTracker()
