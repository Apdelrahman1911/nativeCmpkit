// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.geo

/**
 * Legacy non-null measurement model. Tracker views use NaN for an absent numeric
 * value and timestamp 0 for absent time. Prefer [LocationFix], whose independent
 * native measurement/accuracy flags remain nullable. [azimuth] is course of travel,
 * not a measured device compass heading.
 */
data class ExtendedLocation(
    val location: Location,
    val azimuth: Azimuth,
    val speed: Speed,
    val altitude: Altitude,
    val timestampMs: Long
)
