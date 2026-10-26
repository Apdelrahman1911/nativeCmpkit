@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

import kotlin.test.*

class MicrophonePermissionPolicyTest {
    @Test fun onlyAuthorizedGrantsAccess() {
        MicrophoneAuthorization.entries.forEach {
            assertEquals(it == MicrophoneAuthorization.Authorized, microphoneSnapshot(it).status.isGranted)
        }
    }
    @Test fun restrictedAndNotDeterminedAreNotConflated() {
        val unknown = microphoneSnapshot(MicrophoneAuthorization.NotDetermined)
        assertFalse(unknown.status.shouldShowRationale)
        assertEquals(PermissionRequestability.Requestable, unknown.details.requestability)
        assertEquals(PermissionRequestability.Restricted, microphoneSnapshot(MicrophoneAuthorization.Restricted).details.requestability)
    }
}
