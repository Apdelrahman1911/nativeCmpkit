@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

internal enum class NotificationAuthorization { Unknown, NotDetermined, Denied, Authorized, Provisional, Ephemeral }
internal fun notificationSnapshot(authorization: NotificationAuthorization): PermissionSnapshot {
    val granted = authorization in setOf(NotificationAuthorization.Authorized, NotificationAuthorization.Provisional, NotificationAuthorization.Ephemeral)
    return PermissionSnapshot(if (granted) PermissionStatus.Granted else PermissionStatus.Denied(authorization == NotificationAuthorization.Denied),
        PermissionDetails(PermissionAvailability.Available, when (authorization) {
            NotificationAuthorization.Authorized -> PermissionAccess.Full
            NotificationAuthorization.Provisional -> PermissionAccess.Provisional
            NotificationAuthorization.Ephemeral -> PermissionAccess.Ephemeral
            NotificationAuthorization.Denied -> PermissionAccess.None
            else -> PermissionAccess.Unknown
        }, when {
            granted -> PermissionRequestability.NotRequired
            authorization == NotificationAuthorization.NotDetermined -> PermissionRequestability.Requestable
            authorization == NotificationAuthorization.Denied -> PermissionRequestability.SettingsOnly
            else -> PermissionRequestability.Unknown
        }, capability = "notifications"))
}

/** Used for fresh and existing authorization alike. Registration is NOT token delivery. */
internal fun finishNotificationRequest(
    granted: Boolean, remote: Boolean, register: () -> Unit, callback: (Boolean) -> Unit,
) {
    if (granted && remote) register()
    callback(granted)
}
