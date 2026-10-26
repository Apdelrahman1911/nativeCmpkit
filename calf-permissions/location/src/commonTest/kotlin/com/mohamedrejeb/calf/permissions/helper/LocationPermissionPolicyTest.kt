@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*
import kotlin.test.*

class LocationPermissionPolicyTest {
    @Test fun coarseAcceptsApproximateButFineDoesNotClaimPrecision() {
        val coarse = foregroundLocationSnapshot(ForegroundLocationAuthorization.WhenInUse, false, false)
        val fine = foregroundLocationSnapshot(ForegroundLocationAuthorization.WhenInUse, false, true)
        assertTrue(coarse.status.isGranted); assertFalse(fine.status.isGranted)
        assertEquals(PermissionAccess.Approximate, coarse.details.access)
        assertEquals(PermissionAccess.Approximate, fine.details.access)
        assertEquals(PermissionRequestability.SettingsOnly, fine.details.requestability)
    }
    @Test fun preciseForegroundOrAlwaysSatisfiesFine() {
        listOf(ForegroundLocationAuthorization.WhenInUse, ForegroundLocationAuthorization.Always).forEach {
            assertTrue(foregroundLocationSnapshot(it, true, true).status.isGranted)
        }
    }
    @Test fun initialDelegateEventsAreNotTerminal() {
        assertFalse(foregroundLocationIsTerminal(ForegroundLocationAuthorization.NotDetermined))
        assertFalse(foregroundLocationIsTerminal(ForegroundLocationAuthorization.Unknown))
        assertTrue(foregroundLocationIsTerminal(ForegroundLocationAuthorization.Denied))
        assertTrue(foregroundLocationIsTerminal(ForegroundLocationAuthorization.WhenInUse))
    }
    @Test fun restrictedNeverOffersAnotherPrompt() {
        val state = foregroundLocationSnapshot(ForegroundLocationAuthorization.Restricted, false, false)
        assertFalse(state.status.isGranted)
        assertEquals(PermissionRequestability.Restricted, state.details.requestability)
    }
}
