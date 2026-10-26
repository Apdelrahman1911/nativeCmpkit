@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*
import kotlin.test.*

class BluetoothPermissionPolicyTest {
    @Test fun permissionGrantDoesNotDependOnPoweredOnHardware() {
        assertTrue(bluetoothSnapshot(BluetoothAuthorization.Allowed).status.isGranted)
        assertEquals("bluetooth-authorization", bluetoothSnapshot(BluetoothAuthorization.Allowed).details.capability)
    }
    @Test fun undeterminedTimeoutIsNotPermanentDenial() {
        val snapshot = bluetoothSnapshot(BluetoothAuthorization.NotDetermined, PermissionRequestOutcome.TimedOut)
        assertFalse(snapshot.status.isGranted)
        assertFalse(snapshot.status.shouldShowRationale)
        assertEquals(PermissionRequestOutcome.TimedOut, snapshot.details.lastRequest)
        assertEquals(PermissionRequestability.Requestable, snapshot.details.requestability)
    }
    @Test fun restrictedAndDeniedAreDistinct() {
        assertEquals(PermissionRequestability.Restricted, bluetoothSnapshot(BluetoothAuthorization.Restricted).details.requestability)
        assertEquals(PermissionRequestability.SettingsOnly, bluetoothSnapshot(BluetoothAuthorization.Denied).details.requestability)
    }
    @Test fun oldUnsupportedQueryDoesNotPretendToGrant() {
        val snapshot = bluetoothSnapshot(BluetoothAuthorization.Unsupported)
        assertFalse(snapshot.status.isGranted)
        assertEquals(PermissionAvailability.Unsupported, snapshot.details.availability)
    }
}
