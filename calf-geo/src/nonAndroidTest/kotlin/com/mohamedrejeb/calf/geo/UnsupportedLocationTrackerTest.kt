package com.mohamedrejeb.calf.geo

import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertTrue

class UnsupportedLocationTrackerTest {
    @Test fun commonFactoryExposesActualUnsupportedTargetWithoutFakeFix() = runTest {
        val tracker = createLocationTracker()
        assertEquals(LocationTrackingCapability.Unsupported, tracker.capability)
        assertEquals(LocationStartResult.Unsupported, tracker.startTrackingWithResult())
        tracker.startTracking()
        tracker.stopTracking()
        assertEquals(LocationTrackingPhase.Unsupported, tracker.snapshotState.value.phase)
        assertNull(tracker.fixState.value)
        assertTrue(tracker.locationState.value.latitude.isNaN())
        assertTrue(tracker.extendedLocationState.value.location.coordinatesAccuracyMeters.isNaN())
    }

    @Test fun actualUnsupportedTrackerCanBeClosedWithoutNativeWork() = runTest {
        val tracker = createLocationTracker()
        tracker.close()
        tracker.close()
        val result = assertIs<LocationStartResult.Failed>(tracker.startTrackingWithResult())
        assertEquals(LocationTrackingFailure.Closed, result.error.reason)
        assertEquals(LocationTrackingPhase.Closed, tracker.snapshotState.value.phase)
        assertNull(tracker.fixState.value)
    }
}
