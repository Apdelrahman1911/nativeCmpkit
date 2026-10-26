// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.geo

/** Speed and its optional uncertainty are both meters per second. */
data class Speed(
    val speedMps: Double,
    val speedAccuracyMps: Double?
)
