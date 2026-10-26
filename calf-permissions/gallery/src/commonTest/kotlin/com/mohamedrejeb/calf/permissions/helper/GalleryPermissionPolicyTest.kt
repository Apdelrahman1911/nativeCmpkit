@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*
import kotlin.test.*

class GalleryPermissionPolicyTest {
    @Test fun limitedAccessIsUsableButNeverReportedFull() {
        val snapshot = gallerySnapshot(GalleryAuthorization.Limited)
        assertTrue(snapshot.status.isGranted)
        assertEquals(PermissionAccess.Limited, snapshot.details.access)
        assertEquals(PermissionRequestability.NotRequired, snapshot.details.requestability)
    }
    @Test fun unknownAndNotDeterminedAreNotPermanentDenials() {
        listOf(GalleryAuthorization.Unknown, GalleryAuthorization.NotDetermined).forEach {
            assertFalse(gallerySnapshot(it).status.shouldShowRationale)
            assertEquals(PermissionAccess.Unknown, gallerySnapshot(it).details.access)
        }
    }
    @Test fun restrictedAndDeniedAreDistinct() {
        assertEquals(PermissionRequestability.Restricted, gallerySnapshot(GalleryAuthorization.Restricted).details.requestability)
        assertEquals(PermissionRequestability.SettingsOnly, gallerySnapshot(GalleryAuthorization.Denied).details.requestability)
    }
    @Test fun onlyFullAndLimitedStatesGrantLegacyAccess() {
        GalleryAuthorization.entries.forEach {
            assertEquals(it == GalleryAuthorization.Full || it == GalleryAuthorization.Limited, gallerySnapshot(it).status.isGranted)
        }
    }
}
