@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

internal enum class ContactAuthorization { Unknown, NotDetermined, Denied, Restricted, Full, Limited }
internal fun contactSnapshot(authorization: ContactAuthorization): PermissionSnapshot {
    val granted = authorization == ContactAuthorization.Full || authorization == ContactAuthorization.Limited
    return PermissionSnapshot(if (granted) PermissionStatus.Granted else PermissionStatus.Denied(
        authorization == ContactAuthorization.Denied || authorization == ContactAuthorization.Restricted),
        PermissionDetails(PermissionAvailability.Available, when (authorization) {
            ContactAuthorization.Full -> PermissionAccess.Full
            ContactAuthorization.Limited -> PermissionAccess.Limited
            ContactAuthorization.Unknown, ContactAuthorization.NotDetermined -> PermissionAccess.Unknown
            else -> PermissionAccess.None
        }, when (authorization) {
            ContactAuthorization.Full, ContactAuthorization.Limited -> PermissionRequestability.NotRequired
            ContactAuthorization.NotDetermined -> PermissionRequestability.Requestable
            ContactAuthorization.Restricted -> PermissionRequestability.Restricted
            ContactAuthorization.Denied -> PermissionRequestability.SettingsOnly
            ContactAuthorization.Unknown -> PermissionRequestability.Unknown
        }, capability = "contacts"))
}
