package com.mohamedrejeb.calf.geo

import android.location.Location as AndroidLocation
import android.os.Build

/** Preserve every independent native has* flag. Never use default zero as evidence of a measurement. */
internal fun AndroidLocation.toLocationFix(): LocationFix? {
    val coordinates = LatLng(latitude, longitude)
    if (!coordinates.isValid) return null
    val horizontalAccuracy = if (hasAccuracy()) accuracy.toDouble().uncertaintyOrNull() else null
    val speedValue = if (hasSpeed()) speed.toDouble().uncertaintyOrNull() else null
    val courseValue = if (hasBearing()) bearing.toDouble().takeIf { it.isFinite() && it in 0.0..<360.0 } else null
    val altitudeValue = if (hasAltitude()) altitude.takeIf { it.isFinite() } else null
    val speedAccuracy = if (Build.VERSION.SDK_INT >= 26 && hasSpeedAccuracy()) speedAccuracyMetersPerSecond.toDouble().uncertaintyOrNull() else null
    val bearingAccuracy = if (Build.VERSION.SDK_INT >= 26 && hasBearingAccuracy()) bearingAccuracyDegrees.toDouble().uncertaintyOrNull() else null
    val altitudeAccuracy = if (Build.VERSION.SDK_INT >= 26 && hasVerticalAccuracy()) verticalAccuracyMeters.toDouble().uncertaintyOrNull() else null
    @Suppress("DEPRECATION")
    val mock = if (Build.VERSION.SDK_INT >= 31) isMock else isFromMockProvider
    return LocationFix(
        coordinates = coordinates,
        coordinatesAccuracyMeters = horizontalAccuracy,
        speedMps = speedValue,
        speedAccuracyMps = speedAccuracy,
        courseDegrees = courseValue,
        courseAccuracyDegrees = bearingAccuracy,
        altitudeMeters = altitudeValue,
        altitudeAccuracyMeters = altitudeAccuracy,
        timestampMs = time.takeIf { it > 0L },
        elapsedRealtimeNanos = elapsedRealtimeNanos.takeIf { it > 0L },
        isMock = mock,
    )
}

private fun Double.uncertaintyOrNull(): Double? = takeIf { it.isFinite() && it >= 0.0 }
