@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*
import kotlin.test.*

class BackgroundLocationPermissionPolicyTest {
    @Test fun whenInUseIsAnExplicitlyRequestableAlwaysUpgrade() {
        val state = backgroundLocationSnapshot(BackgroundLocationAuthorization.WhenInUse)
        assertFalse(state.status.isGranted)
        assertFalse(state.status.shouldShowRationale)
        assertEquals(PermissionRequestability.Requestable, state.details.requestability)
        assertEquals(PermissionAccess.Limited, state.details.access)
    }
    @Test fun onlyAlwaysIsGranted() {
        BackgroundLocationAuthorization.entries.forEach {
            assertEquals(it == BackgroundLocationAuthorization.Always, backgroundLocationSnapshot(it).status.isGranted)
        }
    }
    @Test fun initialAndUnchangedUpgradeDelegateEventsAreNotTerminal() {
        assertFalse(backgroundLocationIsTerminal(BackgroundLocationAuthorization.NotDetermined, BackgroundLocationAuthorization.NotDetermined))
        assertFalse(backgroundLocationIsTerminal(BackgroundLocationAuthorization.WhenInUse, BackgroundLocationAuthorization.WhenInUse))
        assertTrue(backgroundLocationIsTerminal(BackgroundLocationAuthorization.WhenInUse, BackgroundLocationAuthorization.Always))
        assertTrue(backgroundLocationIsTerminal(BackgroundLocationAuthorization.WhenInUse, BackgroundLocationAuthorization.Denied))
    }
    @Test fun deniedAndRestrictedRemainNonrequestable() {
        assertEquals(PermissionRequestability.SettingsOnly, backgroundLocationSnapshot(BackgroundLocationAuthorization.Denied).details.requestability)
        assertEquals(PermissionRequestability.Restricted, backgroundLocationSnapshot(BackgroundLocationAuthorization.Restricted).details.requestability)
    }
}
