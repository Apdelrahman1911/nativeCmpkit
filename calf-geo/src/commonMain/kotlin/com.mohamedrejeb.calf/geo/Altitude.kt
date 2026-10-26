// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.geo

/** Android altitude is meters above the WGS84 ellipsoid; null accuracy means not supplied. */
data class Altitude(
    val altitudeMeters: Double,
    val altitudeAccuracyMeters: Double?
)
