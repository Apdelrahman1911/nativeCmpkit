// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.geo

import kotlin.math.*

/**
 * A class representing a pair of latitude and longitude coordinates, stored as degrees.
 *
 * The constructor deliberately remains unchecked for source/data-class
 * compatibility. Use [validated] or [normalized] at trust boundaries and [isValid]
 * before interpreting a value as a position. No constructor silently changes
 * coordinates or their equality.
 *
 * @property latitude Latitude in degrees, valid in [-90, 90].
 * @property longitude Longitude in degrees, valid in [-180, 180].
 */
data class LatLng(
    val latitude: Double,
    val longitude: Double
) {
    val isValid: Boolean
        get() = latitude.isFinite() && longitude.isFinite() &&
            latitude in -90.0..90.0 && longitude in -180.0..180.0

    /**
     * Spherical great-circle distance in kilometers using radius 6371 km, not a
     * WGS84 ellipsoidal/geodesic solution. Location measurement accuracy is in
     * meters; do not mix those units. Invalid inputs return NaN.
     *
     * @param latLng The [LatLng] to calculate the distance to.
     * @return The distance to the given [LatLng] in kilometers.
     */
    fun distanceTo(latLng: LatLng): Double = distanceToOrNull(latLng) ?: Double.NaN

    /** Nullable counterpart of [distanceTo], with an explicit invalid-input result. */
    fun distanceToOrNull(latLng: LatLng): Double? {
        if (!isValid || !latLng.isValid) return null
        if (latitude == latLng.latitude && abs(latitude) == 90.0) return 0.0
        val lat1 = latitude
        val lon1 = longitude
        val lat2 = latLng.latitude
        val lon2 = latLng.longitude

        val r = EarthRadius
        val dLat = toRadians(lat2 - lat1)
        val dLon = toRadians(normalizeLongitude(lon2 - lon1))
        val a = sin(dLat / 2) * sin(dLat / 2) +
                cos(toRadians(lat1)) * cos(toRadians(lat2)) * sin(dLon / 2) * sin(dLon / 2)
        // Floating-point roundoff must not take a valid haversine outside its domain.
        val c = 2 * asin(sqrt(a.coerceIn(0.0, 1.0)))
        return r * c
    }

    /**
     * Initial course of the spherical shortest arc, clockwise from true north,
     * not the device heading. Invalid or undefined bearings return NaN. Bearings
     * are undefined for coincident points, exact antipodes, and a start at a pole.
     * Use [initialBearingToOrNull] to represent these cases without a NaN sentinel.
     *
     * @param latLng The [LatLng] to calculate the angle to.
     * @param rounded Whether the angle should be rounded to the nearest 10 degrees.
     * @return The angle to the given [LatLng] in degrees.
     */
    fun getAngleTo(latLng: LatLng, rounded: Boolean = true): Double =
        initialBearingToOrNull(latLng, rounded) ?: Double.NaN

    /**
     * Returns null for invalid coordinates or a non-unique initial bearing.
     * Valid unrounded results are in [0, 360); rounded results are 0, 10, ..., 350.
     * Near-antipodal courses can be ill-conditioned even when mathematically unique.
     */
    fun initialBearingToOrNull(latLng: LatLng, rounded: Boolean = false): Double? {
        if (!isValid || !latLng.isValid || abs(latitude) == 90.0) return null
        val longitudeDelta = normalizeLongitude(latLng.longitude - longitude)
        if (latitude == latLng.latitude && longitudeDelta == 0.0) return null
        if (latitude == -latLng.latitude && abs(longitudeDelta) == 180.0) return null
        val lat1 = toRadians(this.latitude)
        val lat2 = toRadians(latLng.latitude)
        val dLon = toRadians(longitudeDelta)

        val y = sin(dLon) * cos(lat2)
        val x = cos(lat1) * sin(lat2) -
                (sin(lat1) * cos(lat2) * cos(dLon))

        if (x == 0.0 && y == 0.0) return null
        var brng = atan2(y, x)

        brng = toDegree(brng)
        brng = (brng + 360) % 360

        var angle = brng
        if (rounded) {
            angle = (round(brng / 10) * 10)
        }
        if (angle == 360.0) angle = 0.0

        return angle
    }

    private fun toRadians(angle: Double): Double {
        return angle * PI / 180.0
    }

    private fun toDegree(angle: Double): Double {
        return angle * 180.0 / PI
    }

    companion object {
        /**
         * Legacy spherical radius in kilometers, retained for JVM field compatibility.
         * The original private companion still emitted this as a public JVM constant;
         * keep its name, value and Java visibility for existing source and reflection.
         */
        @Deprecated(
            message = "Legacy spherical radius; retained for JVM compatibility.",
            level = DeprecationLevel.WARNING,
        )
        const val EarthRadius = 6371.00

        /** Rejects nonfinite and out-of-range coordinates without changing them. */
        fun validated(latitude: Double, longitude: Double): LatLng =
            LatLng(latitude, longitude).also { require(it.isValid) { "Coordinates must be finite, latitude [-90,90], longitude [-180,180]" } }

        /**
         * Normalizes only longitude to [-180,180). Latitude must already be finite
         * and in [-90,90]; pole-crossing latitude folding is deliberately not guessed.
         */
        fun normalized(latitude: Double, longitude: Double): LatLng {
            require(latitude.isFinite() && latitude in -90.0..90.0 && longitude.isFinite()) {
                "Latitude must be finite in [-90,90] and longitude must be finite"
            }
            return LatLng(latitude, normalizeLongitude(longitude))
        }

        private fun normalizeLongitude(longitude: Double): Double {
            val wrapped = longitude % 360.0
            // Avoid adding a large constant, which would erase very small deltas.
            return when {
                wrapped < -180.0 -> wrapped + 360.0
                wrapped >= 180.0 -> wrapped - 360.0
                else -> wrapped
            }
        }
    }
}
