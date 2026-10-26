package com.mohamedrejeb.calf.geo

/** A backend capability, not a permission grant, provider-health check, or fix guarantee. */
enum class LocationTrackingCapability { Foreground, Unsupported }

enum class LocationTrackingPhase { Unsupported, Unbound, Idle, Starting, Tracking, Stopping, Stopped, Failed, Closed }

/** Android permission granularity, not a promise about a particular fix's accuracy. */
enum class LocationPermissionAccuracy { Approximate, Precise }

enum class LocationTrackingFailure {
    NotBound, Closed, OwnerInactive, PermissionDenied, ProviderUnavailable, ProviderError, RemovalFailed, InvalidLocation
}

/** Platform failures are retained for the caller, never logged or persisted by the library. */
data class LocationTrackingError(
    val reason: LocationTrackingFailure,
    val cause: Throwable? = null,
    val platformCode: Int? = null,
)

sealed interface LocationStartResult {
    data object Started : LocationStartResult
    data object AlreadyStarted : LocationStartResult
    data object InProgress : LocationStartResult
    data object Cancelled : LocationStartResult
    data object Unsupported : LocationStartResult
    data class Failed(val error: LocationTrackingError) : LocationStartResult
}

/**
 * An observed fix, with absence distinct from a genuine zero measurement.
 *
 * Coordinates are degrees; horizontal/vertical accuracy and altitude are meters;
 * speed is meters/second. [courseDegrees] is direction of travel clockwise from true
 * north, NOT the device's compass heading. Android altitude is above the WGS84
 * reference ellipsoid, not necessarily mean sea level. Native uncertainty values
 * retain the provider's meaning (Android's approximately 68% confidence).
 *
 * [timestampMs] is a positive UTC epoch millisecond timestamp when supplied.
 * [elapsedRealtimeNanos] is Android's monotonic time since boot, not an epoch or
 * a value comparable across boots/devices. Neither clock is synthesized. Cached,
 * coarse, and mock fixes are permitted and identified, not silently represented
 * as fresh/precise. Applications must choose their own age/accuracy/mock policy.
 */
data class LocationFix(
    val coordinates: LatLng,
    val coordinatesAccuracyMeters: Double? = null,
    val speedMps: Double? = null,
    val speedAccuracyMps: Double? = null,
    val courseDegrees: Double? = null,
    val courseAccuracyDegrees: Double? = null,
    val altitudeMeters: Double? = null,
    val altitudeAccuracyMeters: Double? = null,
    val timestampMs: Long? = null,
    val elapsedRealtimeNanos: Long? = null,
    val isMock: Boolean? = null,
) {
    /** Convenience views; the raw fields above retain independently supplied accuracy flags. */
    val speed: Speed? get() = speedMps?.let { Speed(it, speedAccuracyMps) }
    val course: Azimuth? get() = courseDegrees?.let { Azimuth(it, courseAccuracyDegrees) }
    val altitude: Altitude? get() = altitudeMeters?.let { Altitude(it, altitudeAccuracyMeters) }
}

/**
 * The single observable source of truth. [fix] remains the last accepted fix when
 * stopped; a new start/rebind clears it. Registration success does not guarantee
 * a fix. A false [isProviderAvailable] is a transient native availability signal,
 * not evidence that permissions were denied. [cleanupError] reports failed
 * removal, including an old subscription's failure during a safe rebind, without
 * stopping a different current subscription.
 */
data class LocationTrackingSnapshot(
    val phase: LocationTrackingPhase,
    val fix: LocationFix? = null,
    val permissionAccuracy: LocationPermissionAccuracy? = null,
    val isProviderAvailable: Boolean? = null,
    val error: LocationTrackingError? = null,
    val cleanupError: LocationTrackingError? = null,
)
