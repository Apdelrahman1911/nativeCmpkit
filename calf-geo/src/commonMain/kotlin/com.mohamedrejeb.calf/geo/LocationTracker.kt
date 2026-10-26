// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.geo

import androidx.compose.runtime.State

/**
 * Foreground location tracking. Android must be [bound][LocationTracker] to a
 * platform lifecycle before starting; other targets explicitly report unsupported.
 * No method requests permissions or silently escalates to background access.
 *
 * Read [snapshotState] for both availability and a nullable, attributed fix. The
 * legacy non-null views use documented NaN sentinels until a fix is available.
 */
expect class LocationTracker {
    /** Compatibility entry point. Inspect [snapshotState] for failures. */
    suspend fun startTracking()
    /** Waits for provider registration, not the first fix. Cancellation stops that request. */
    suspend fun startTrackingWithResult(): LocationStartResult
    /** Stops delivery; provider-removal failures are exposed in [snapshotState]. */
    fun stopTracking()
    /** Permanently releases this tracker. A closed tracker cannot be rebound or restarted. */
    fun close()

    val capability: LocationTrackingCapability
    val snapshotState: State<LocationTrackingSnapshot>
    /** Latest accepted fix; null before a fix. Check the snapshot phase before treating it as live. */
    val fixState: State<LocationFix?>

    /**
     * Compatibility view. Both coordinates are NaN when no fix exists, never a
     * fabricated position at (0, 0). Prefer [fixState] for explicit absence.
     */
    val locationState: State<LatLng>

    /**
     * Compatibility view. Missing numeric measurements are NaN, missing accuracy
     * is null (or NaN for the legacy non-null horizontal accuracy), and missing
     * time is 0. Prefer [fixState], whose measurement objects and time are nullable.
     */
    val extendedLocationState: State<ExtendedLocation>
}

/** Creates an unbound Android tracker, or an explicitly unsupported tracker elsewhere. */
expect fun createLocationTracker(): LocationTracker
