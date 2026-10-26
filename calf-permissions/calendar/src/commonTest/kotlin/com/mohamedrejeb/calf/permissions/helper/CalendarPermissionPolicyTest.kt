@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*
import kotlin.test.*

class CalendarPermissionPolicyTest {
    @Test fun onlyModernWriteRequestsWriteOnlyAccess() {
        assertEquals(CalendarRequestKind.Legacy, calendarRequestKind(16, CalendarAccessMode.Write))
        assertEquals(CalendarRequestKind.Legacy, calendarRequestKind(16, CalendarAccessMode.Read))
        assertEquals(CalendarRequestKind.WriteOnly, calendarRequestKind(17, CalendarAccessMode.Write))
        assertEquals(CalendarRequestKind.FullAccess, calendarRequestKind(17, CalendarAccessMode.Read))
        assertEquals(CalendarRequestKind.WriteOnly, calendarRequestKind(26, CalendarAccessMode.Write))
    }
    @Test fun writeOnlyGrantsWritesButReadCanRequestUpgrade() {
        val write = calendarSnapshot(CalendarAuthorization.WriteOnly, CalendarAccessMode.Write)
        val read = calendarSnapshot(CalendarAuthorization.WriteOnly, CalendarAccessMode.Read)
        assertTrue(write.status.isGranted); assertFalse(read.status.isGranted)
        assertEquals(PermissionAccess.WriteOnly, write.details.access)
        assertEquals(PermissionRequestability.Requestable, read.details.requestability)
        assertFalse(read.status.shouldShowRationale)
    }
    @Test fun fullAccessSatisfiesBothModes() {
        CalendarAccessMode.entries.forEach { assertTrue(calendarSnapshot(CalendarAuthorization.Full, it).status.isGranted) }
    }
    @Test fun restrictedAndDeniedHaveDifferentRequestability() {
        assertEquals(PermissionRequestability.Restricted, calendarSnapshot(CalendarAuthorization.Restricted, CalendarAccessMode.Read).details.requestability)
        assertEquals(PermissionRequestability.SettingsOnly, calendarSnapshot(CalendarAuthorization.Denied, CalendarAccessMode.Write).details.requestability)
    }
    @Test fun undeterminedIsNotAPermanentDenial() {
        val state = calendarSnapshot(CalendarAuthorization.NotDetermined, CalendarAccessMode.Read)
        assertFalse(state.status.shouldShowRationale)
        assertEquals(PermissionAccess.Unknown, state.details.access)
        assertEquals(PermissionRequestability.Requestable, state.details.requestability)
    }
}
