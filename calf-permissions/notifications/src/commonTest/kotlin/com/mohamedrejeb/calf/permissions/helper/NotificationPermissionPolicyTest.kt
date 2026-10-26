@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*
import kotlin.test.*

class NotificationPermissionPolicyTest {
    @Test fun provisionalAndEphemeralAreVisibleWithoutBreakingLegacyGrant() {
        val provisional = notificationSnapshot(NotificationAuthorization.Provisional)
        val ephemeral = notificationSnapshot(NotificationAuthorization.Ephemeral)
        assertTrue(provisional.status.isGranted); assertTrue(ephemeral.status.isGranted)
        assertEquals(PermissionAccess.Provisional, provisional.details.access)
        assertEquals(PermissionAccess.Ephemeral, ephemeral.details.access)
    }
    @Test fun remoteRegistrationPrecedesSuccessForAllEligibleAuthorizationScopes() {
        listOf(NotificationAuthorization.Authorized, NotificationAuthorization.Provisional, NotificationAuthorization.Ephemeral).forEach {
            val events = mutableListOf<String>()
            finishNotificationRequest(notificationSnapshot(it).status.isGranted, true, { events += "register" }) { granted ->
                assertTrue(granted); events += "callback"
            }
            assertEquals(listOf("register", "callback"), events)
        }
    }
    @Test fun deniedRequestsDoNotRegisterAPNs() {
        var calls = 0
        finishNotificationRequest(false, true, { fail("register") }) { assertFalse(it); calls++ }
        assertEquals(1, calls)
    }
    @Test fun localNotificationAuthorizationDoesNotRegisterAPNs() {
        finishNotificationRequest(true, false, { fail("register") }) { assertTrue(it) }
    }
    @Test fun notDeterminedIsRequestableButDeniedRequiresSettings() {
        assertEquals(PermissionRequestability.Requestable, notificationSnapshot(NotificationAuthorization.NotDetermined).details.requestability)
        assertEquals(PermissionRequestability.SettingsOnly, notificationSnapshot(NotificationAuthorization.Denied).details.requestability)
    }
}
