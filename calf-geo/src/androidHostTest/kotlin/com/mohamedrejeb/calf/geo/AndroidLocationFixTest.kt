package com.mohamedrejeb.calf.geo

import android.location.Location as AndroidLocation
import android.os.Build
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull

/** Real Android Location implementation under Robolectric, not a fake Android class. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [23, 26, 34])
class AndroidLocationFixTest {
    @Test fun nativeMissingFieldsRemainIndependentlyAbsent() {
        val fix = assertNotNull(location().toLocationFix())
        assertEquals(LatLng(1.0, 2.0), fix.coordinates)
        assertNull(fix.coordinatesAccuracyMeters)
        assertNull(fix.speedMps)
        assertNull(fix.courseDegrees)
        assertNull(fix.altitudeMeters)
        assertNull(fix.speedAccuracyMps)
        assertNull(fix.courseAccuracyDegrees)
        assertNull(fix.altitudeAccuracyMeters)
        assertNull(fix.timestampMs)
        assertNull(fix.elapsedRealtimeNanos)
    }

    @Test fun realZeroMeasurementsAreNotConfusedWithMissingFlags() {
        val native = location().apply {
            latitude = 0.0
            longitude = 0.0
            accuracy = 0f
            speed = 0f
            bearing = 0f
            altitude = 0.0
            if (Build.VERSION.SDK_INT >= 26) {
                speedAccuracyMetersPerSecond = 0f
                bearingAccuracyDegrees = 0f
                verticalAccuracyMeters = 0f
            }
        }
        val fix = assertNotNull(native.toLocationFix())
        assertEquals(LatLng(0.0, 0.0), fix.coordinates)
        assertEquals(0.0, fix.coordinatesAccuracyMeters)
        assertEquals(0.0, fix.speedMps)
        assertEquals(0.0, fix.courseDegrees)
        assertEquals(0.0, fix.altitudeMeters)
        val expectedAccuracy = if (Build.VERSION.SDK_INT >= 26) 0.0 else null
        assertEquals(expectedAccuracy, fix.speedAccuracyMps)
        assertEquals(expectedAccuracy, fix.courseAccuracyDegrees)
        assertEquals(expectedAccuracy, fix.altitudeAccuracyMeters)
    }

    @Test fun measurementPresenceDoesNotInventAccuracyOnNewerApis() {
        val fix = assertNotNull(location().apply {
            speed = 1f
            bearing = 2f
            altitude = 3.0
        }.toLocationFix())
        assertEquals(1.0, fix.speedMps)
        assertEquals(2.0, fix.courseDegrees)
        assertEquals(3.0, fix.altitudeMeters)
        assertNull(fix.speedAccuracyMps)
        assertNull(fix.courseAccuracyDegrees)
        assertNull(fix.altitudeAccuracyMeters)
    }

    @Test fun nativeAccuracyFlagCanExistWithoutItsMeasurementFlag() {
        val native = location()
        if (Build.VERSION.SDK_INT >= 26) {
            native.speedAccuracyMetersPerSecond = 1f
            native.bearingAccuracyDegrees = 2f
            native.verticalAccuracyMeters = 3f
        }
        val fix = assertNotNull(native.toLocationFix())
        assertNull(fix.speedMps)
        assertNull(fix.courseDegrees)
        assertNull(fix.altitudeMeters)
        assertEquals(if (Build.VERSION.SDK_INT >= 26) 1.0 else null, fix.speedAccuracyMps)
        assertEquals(if (Build.VERSION.SDK_INT >= 26) 2.0 else null, fix.courseAccuracyDegrees)
        assertEquals(if (Build.VERSION.SDK_INT >= 26) 3.0 else null, fix.altitudeAccuracyMeters)
    }

    @Test fun clearingNativeFlagsDoesNotPublishTheirDefaultZeros() {
        val native = location().apply {
            accuracy = 5f
            speed = 6f
            bearing = 7f
            altitude = 8.0
            removeAccuracy()
            removeSpeed()
            removeBearing()
            removeAltitude()
        }
        val fix = assertNotNull(native.toLocationFix())
        assertNull(fix.coordinatesAccuracyMeters)
        assertNull(fix.speedMps)
        assertNull(fix.courseDegrees)
        assertNull(fix.altitudeMeters)
    }

    @Test fun unitsTimesAndNegativeAltitudeAreRetainedWithoutConversions() {
        val fix = assertNotNull(location().apply {
            accuracy = 12.5f
            speed = 3.5f
            bearing = 180f
            altitude = -430.0
            time = 1_700_000_000_123L
            elapsedRealtimeNanos = 900_000_000L
        }.toLocationFix())
        assertEquals(12.5, fix.coordinatesAccuracyMeters)
        assertEquals(3.5, fix.speedMps)
        assertEquals(180.0, fix.courseDegrees)
        assertEquals(-430.0, fix.altitudeMeters)
        assertEquals(1_700_000_000_123L, fix.timestampMs)
        assertEquals(900_000_000L, fix.elapsedRealtimeNanos)
    }

    @Test fun invalidCoordinatesDoNotBecomeAnObservedFix() {
        assertNull(location().apply { latitude = Double.NaN }.toLocationFix())
        assertNull(location().apply { longitude = 181.0 }.toLocationFix())
    }

    @Test @Config(sdk = [34]) fun nativeMockFlagRemainsVisibleToConsumers() {
        val native = location().apply { setMock(true) }
        assertEquals(true, native.toLocationFix()?.isMock)
    }

    private fun location() = AndroidLocation("test-provider").apply {
        latitude = 1.0
        longitude = 2.0
    }
}
