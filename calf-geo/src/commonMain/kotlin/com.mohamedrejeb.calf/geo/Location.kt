// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.geo

/**
 * A class representing the coordinates of a location, stored as a [LatLng] and an accuracy in meters.
 *
 * @property coordinates The coordinates of the location.
 * @property coordinatesAccuracyMeters The accuracy of the coordinates in meters.
 * The legacy tracker view uses NaN when horizontal accuracy is absent; prefer
 * [LocationFix.coordinatesAccuracyMeters] for explicit nullable absence.
 */
data class Location(
    val coordinates: LatLng,
    val coordinatesAccuracyMeters: Double
)
