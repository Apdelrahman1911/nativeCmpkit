// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.geo

/** Tracker values are course of travel in degrees clockwise from true north, not device heading. */
data class Azimuth(
    val azimuthDegrees: Double,
    val azimuthAccuracyDegrees: Double?
)
