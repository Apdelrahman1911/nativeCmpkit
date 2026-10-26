@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*
import kotlin.test.*

class ContactPermissionPolicyTest {
    @Test fun limitedAccessIsUsableButNeverReportedFull() {
        val snapshot = contactSnapshot(ContactAuthorization.Limited)
        assertTrue(snapshot.status.isGranted)
        assertEquals(PermissionAccess.Limited, snapshot.details.access)
        assertEquals(PermissionRequestability.NotRequired, snapshot.details.requestability)
    }
    @Test fun unknownAndNotDeterminedAreNotPermanentDenials() {
        listOf(ContactAuthorization.Unknown, ContactAuthorization.NotDetermined).forEach {
            assertFalse(contactSnapshot(it).status.shouldShowRationale)
            assertEquals(PermissionAccess.Unknown, contactSnapshot(it).details.access)
        }
    }
    @Test fun restrictedAndDeniedAreDistinct() {
        assertEquals(PermissionRequestability.Restricted, contactSnapshot(ContactAuthorization.Restricted).details.requestability)
        assertEquals(PermissionRequestability.SettingsOnly, contactSnapshot(ContactAuthorization.Denied).details.requestability)
    }
    @Test fun onlyFullAndLimitedStatesGrantLegacyAccess() {
        ContactAuthorization.entries.forEach {
            assertEquals(it == ContactAuthorization.Full || it == ContactAuthorization.Limited, contactSnapshot(it).status.isGranted)
        }
    }
}
