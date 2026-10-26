@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

internal enum class ForegroundLocationAuthorization { Unknown, NotDetermined, Denied, Restricted, WhenInUse, Always }

internal fun foregroundLocationSnapshot(
    authorization: ForegroundLocationAuthorization, precise: Boolean, requirePrecise: Boolean,
): PermissionSnapshot {
    val authorized = authorization == ForegroundLocationAuthorization.WhenInUse || authorization == ForegroundLocationAuthorization.Always
    val granted = authorized && (!requirePrecise || precise)
    val requestability = when {
        granted -> PermissionRequestability.NotRequired
        authorization == ForegroundLocationAuthorization.NotDetermined -> PermissionRequestability.Requestable
        authorization == ForegroundLocationAuthorization.Restricted -> PermissionRequestability.Restricted
        authorization == ForegroundLocationAuthorization.Denied || authorized -> PermissionRequestability.SettingsOnly
        else -> PermissionRequestability.Unknown
    }
    return PermissionSnapshot(if (granted) PermissionStatus.Granted else PermissionStatus.Denied(
        requestability == PermissionRequestability.SettingsOnly || requestability == PermissionRequestability.Restricted),
        PermissionDetails(PermissionAvailability.Available, when {
            authorized && precise -> PermissionAccess.Full
            authorized -> PermissionAccess.Approximate
            authorization == ForegroundLocationAuthorization.NotDetermined || authorization == ForegroundLocationAuthorization.Unknown -> PermissionAccess.Unknown
            else -> PermissionAccess.None
        }, requestability, capability = "foreground-location"))
}

internal fun foregroundLocationIsTerminal(authorization: ForegroundLocationAuthorization): Boolean =
    authorization != ForegroundLocationAuthorization.NotDetermined && authorization != ForegroundLocationAuthorization.Unknown
