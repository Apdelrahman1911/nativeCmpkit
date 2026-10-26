package com.mohamedrejeb.calf.geo

import kotlin.math.PI
import kotlin.math.abs
import kotlin.random.Random
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class LatLngTest {
    @Test fun uncheckedConstructorAndDataClassCopyRemainCompatible() {
        val value = LatLng(100.0, 400.0)
        assertFalse(value.isValid)
        assertEquals(100.0, value.latitude)
        assertEquals(LatLng(100.0, 3.0), value.copy(longitude = 3.0))
    }

    @Test fun validatedFactoryRejectsInvalidDomains() {
        for (point in listOf(LatLng(Double.NaN, 0.0), LatLng(0.0, Double.POSITIVE_INFINITY), LatLng(90.1, 0.0), LatLng(0.0, -180.1))) {
            assertFailsWith<IllegalArgumentException> { LatLng.validated(point.latitude, point.longitude) }
            assertNull(point.distanceToOrNull(LatLng(0.0, 0.0)))
            assertTrue(point.distanceTo(LatLng(0.0, 0.0)).isNaN())
            assertNull(point.initialBearingToOrNull(LatLng(0.0, 0.0)))
        }
        assertEquals(LatLng(90.0, 180.0), LatLng.validated(90.0, 180.0))
    }

    @Test fun longitudeNormalizationIsExplicitAndDoesNotFoldInvalidLatitude() {
        assertEquals(LatLng(1.0, -180.0), LatLng.normalized(1.0, 540.0))
        assertEquals(LatLng(1.0, 179.0), LatLng.normalized(1.0, -181.0))
        assertEquals(LatLng(1.0, 0.0), LatLng.normalized(1.0, 360.0))
        assertTrue(LatLng.normalized(0.0, Double.MAX_VALUE).isValid)
        assertFailsWith<IllegalArgumentException> { LatLng.normalized(91.0, 0.0) }
        assertFailsWith<IllegalArgumentException> { LatLng.normalized(0.0, Double.NaN) }
    }

    @Test fun sphericalDistanceUnitsAndIdenticalPoints() {
        assertEquals(0.0, LatLng(1.0, 2.0).distanceTo(LatLng(1.0, 2.0)))
        assertEquals(6371.0 * PI / 2, LatLng(0.0, 0.0).distanceTo(LatLng(0.0, 90.0)), 1e-8)
    }

    @Test fun datelineUsesShortArc() {
        assertEquals(6371.0 * PI / 90, LatLng(0.0, 179.0).distanceTo(LatLng(0.0, -179.0)), 1e-8)
        assertEquals(0.0, LatLng(0.0, -180.0).distanceTo(LatLng(0.0, 180.0)))
    }

    @Test fun identicalPolesDoNotDependOnLongitude() {
        assertEquals(0.0, LatLng(90.0, 30.0).distanceTo(LatLng(90.0, -150.0)))
        assertNull(LatLng(90.0, 30.0).initialBearingToOrNull(LatLng(80.0, 30.0)))
        assertEquals(0.0, LatLng(80.0, 0.0).initialBearingToOrNull(LatLng(90.0, 0.0)))
    }

    @Test fun antipodalDistanceIsFiniteAndUndefinedBearingIsExplicit() {
        val start = LatLng(32.0, 50.0)
        val end = LatLng(-32.0, -130.0)
        assertEquals(6371.0 * PI, start.distanceTo(end), 1e-3)
        assertNull(start.initialBearingToOrNull(end))
        assertTrue(start.getAngleTo(end).isNaN())
        assertNull(start.initialBearingToOrNull(start))
    }

    @Test fun cardinalBearingsUseTrueNorthClockwiseConvention() {
        val origin = LatLng(0.0, 0.0)
        assertEquals(0.0, origin.initialBearingToOrNull(LatLng(1.0, 0.0)))
        assertEquals(90.0, origin.initialBearingToOrNull(LatLng(0.0, 1.0)))
        assertEquals(180.0, origin.initialBearingToOrNull(LatLng(-1.0, 0.0)))
        assertEquals(270.0, origin.initialBearingToOrNull(LatLng(0.0, -1.0)))
    }

    @Test fun tinyDistinctCoordinatesAreNotRoundedIntoIdenticalPoints() {
        val start = LatLng(0.0, 0.0)
        val end = LatLng(0.0, 1e-12)
        assertTrue(start.distanceTo(end) > 0)
        assertEquals(90.0, start.initialBearingToOrNull(end))
    }

    @Test fun compatibilityBearingDefaultRoundsAndWrapsToZeroNot360() {
        val start = LatLng(0.0, 0.0)
        val end = LatLng(1.0, -0.001)
        assertEquals(0.0, start.getAngleTo(end))
        val raw = start.getAngleTo(end, rounded = false)
        assertTrue(raw > 350 && raw < 360)
    }

    @Test fun seededDistancesAreSymmetricBoundedAndFiniteAcrossTargets() {
        val random = Random(483)
        repeat(500) {
            val first = LatLng(random.nextDouble(-90.0, 90.0), random.nextDouble(-180.0, 180.0))
            val second = LatLng(random.nextDouble(-90.0, 90.0), random.nextDouble(-180.0, 180.0))
            val forward = first.distanceTo(second)
            assertTrue(forward.isFinite() && forward >= 0 && forward <= 6371.0 * PI)
            assertTrue(abs(forward - second.distanceTo(first)) < 1e-7)
            val raw = assertNotNull(first.initialBearingToOrNull(second))
            val rounded = assertNotNull(first.initialBearingToOrNull(second, rounded = true))
            assertTrue(raw in 0.0..<360.0)
            assertTrue(rounded in 0.0..<360.0 && rounded % 10 == 0.0)
        }
    }
}
