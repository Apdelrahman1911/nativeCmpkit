@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

internal enum class GalleryAuthorization { Unknown, NotDetermined, Denied, Restricted, Full, Limited }
internal fun gallerySnapshot(authorization: GalleryAuthorization): PermissionSnapshot {
    val granted = authorization == GalleryAuthorization.Full || authorization == GalleryAuthorization.Limited
    return PermissionSnapshot(if (granted) PermissionStatus.Granted else PermissionStatus.Denied(
        authorization == GalleryAuthorization.Denied || authorization == GalleryAuthorization.Restricted),
        PermissionDetails(PermissionAvailability.Available, when (authorization) {
            GalleryAuthorization.Full -> PermissionAccess.Full
            GalleryAuthorization.Limited -> PermissionAccess.Limited
            GalleryAuthorization.Unknown, GalleryAuthorization.NotDetermined -> PermissionAccess.Unknown
            else -> PermissionAccess.None
        }, when (authorization) {
            GalleryAuthorization.Full, GalleryAuthorization.Limited -> PermissionRequestability.NotRequired
            GalleryAuthorization.NotDetermined -> PermissionRequestability.Requestable
            GalleryAuthorization.Restricted -> PermissionRequestability.Restricted
            GalleryAuthorization.Denied -> PermissionRequestability.SettingsOnly
            GalleryAuthorization.Unknown -> PermissionRequestability.Unknown
        }, capability = "photo-library"))
}
