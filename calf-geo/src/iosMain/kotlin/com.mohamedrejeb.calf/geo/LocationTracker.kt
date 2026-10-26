// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.geo

import androidx.compose.runtime.State

/** This target has no location backend; no coordinates are fabricated and nothing is logged. */
actual class LocationTracker {
    private val controller = LocationTrackingController(LocationTrackingCapability.Unsupported)

    actual val capability: LocationTrackingCapability = LocationTrackingCapability.Unsupported
    actual val snapshotState: State<LocationTrackingSnapshot> = controller.snapshotState
    actual val fixState: State<LocationFix?> = controller.fixState
    actual val locationState: State<LatLng> = controller.locationState
    actual val extendedLocationState: State<ExtendedLocation> = controller.extendedLocationState

    actual suspend fun startTracking() { startTrackingWithResult() }
    actual suspend fun startTrackingWithResult(): LocationStartResult = controller.awaitStart()
    actual fun stopTracking() = controller.stop()
    actual fun close() = controller.close()
}

actual fun createLocationTracker(): LocationTracker = LocationTracker()
