@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

internal enum class CalendarAccessMode { Read, Write }
internal enum class CalendarAuthorization { Unknown, NotDetermined, Denied, Restricted, Full, WriteOnly }
internal enum class CalendarRequestKind { Legacy, FullAccess, WriteOnly }

internal fun calendarRequestKind(majorIOSVersion: Int, mode: CalendarAccessMode): CalendarRequestKind =
    if (majorIOSVersion < 17) CalendarRequestKind.Legacy
    else if (mode == CalendarAccessMode.Write) CalendarRequestKind.WriteOnly else CalendarRequestKind.FullAccess

internal fun calendarSnapshot(authorization: CalendarAuthorization, mode: CalendarAccessMode): PermissionSnapshot {
    val granted = authorization == CalendarAuthorization.Full ||
        (authorization == CalendarAuthorization.WriteOnly && mode == CalendarAccessMode.Write)
    val requestability = when {
        granted -> PermissionRequestability.NotRequired
        authorization == CalendarAuthorization.NotDetermined || authorization == CalendarAuthorization.WriteOnly -> PermissionRequestability.Requestable
        authorization == CalendarAuthorization.Restricted -> PermissionRequestability.Restricted
        authorization == CalendarAuthorization.Denied -> PermissionRequestability.SettingsOnly
        else -> PermissionRequestability.Unknown
    }
    return PermissionSnapshot(if (granted) PermissionStatus.Granted else PermissionStatus.Denied(
        requestability == PermissionRequestability.SettingsOnly || requestability == PermissionRequestability.Restricted),
        PermissionDetails(PermissionAvailability.Available, when (authorization) {
            CalendarAuthorization.Full -> PermissionAccess.Full
            CalendarAuthorization.WriteOnly -> PermissionAccess.WriteOnly
            CalendarAuthorization.Unknown, CalendarAuthorization.NotDetermined -> PermissionAccess.Unknown
            else -> PermissionAccess.None
        }, requestability, capability = "calendar-events"))
}
