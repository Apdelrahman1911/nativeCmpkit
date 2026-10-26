@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

internal enum class BackgroundLocationAuthorization { Unknown, NotDetermined, Denied, Restricted, WhenInUse, Always }
internal fun backgroundLocationSnapshot(authorization: BackgroundLocationAuthorization): PermissionSnapshot {
    val requestability = when (authorization) {
        BackgroundLocationAuthorization.Always -> PermissionRequestability.NotRequired
        BackgroundLocationAuthorization.WhenInUse, BackgroundLocationAuthorization.NotDetermined -> PermissionRequestability.Requestable
        BackgroundLocationAuthorization.Denied -> PermissionRequestability.SettingsOnly
        BackgroundLocationAuthorization.Restricted -> PermissionRequestability.Restricted
        BackgroundLocationAuthorization.Unknown -> PermissionRequestability.Unknown
    }
    return PermissionSnapshot(if (authorization == BackgroundLocationAuthorization.Always) PermissionStatus.Granted
        else PermissionStatus.Denied(requestability == PermissionRequestability.SettingsOnly || requestability == PermissionRequestability.Restricted),
        PermissionDetails(PermissionAvailability.Available, when (authorization) {
            BackgroundLocationAuthorization.Always -> PermissionAccess.Full
            BackgroundLocationAuthorization.WhenInUse -> PermissionAccess.Limited
            BackgroundLocationAuthorization.Unknown, BackgroundLocationAuthorization.NotDetermined -> PermissionAccess.Unknown
            else -> PermissionAccess.None
        }, requestability, capability = "background-location"))
}
internal fun backgroundLocationIsTerminal(initial: BackgroundLocationAuthorization, current: BackgroundLocationAuthorization): Boolean =
    current != BackgroundLocationAuthorization.NotDetermined && current != BackgroundLocationAuthorization.Unknown &&
        !(initial == BackgroundLocationAuthorization.WhenInUse && current == initial)
