@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

internal enum class CameraAuthorization { Unknown, NotDetermined, Denied, Restricted, Authorized }
internal fun cameraSnapshot(authorization: CameraAuthorization): PermissionSnapshot =
    PermissionSnapshot(if (authorization == CameraAuthorization.Authorized) PermissionStatus.Granted
        else PermissionStatus.Denied(authorization == CameraAuthorization.Denied || authorization == CameraAuthorization.Restricted),
        PermissionDetails(PermissionAvailability.Available, when (authorization) {
            CameraAuthorization.Authorized -> PermissionAccess.Full
            CameraAuthorization.Denied, CameraAuthorization.Restricted -> PermissionAccess.None
            else -> PermissionAccess.Unknown
        }, when (authorization) {
            CameraAuthorization.Authorized -> PermissionRequestability.NotRequired
            CameraAuthorization.NotDetermined -> PermissionRequestability.Requestable
            CameraAuthorization.Denied -> PermissionRequestability.SettingsOnly
            CameraAuthorization.Restricted -> PermissionRequestability.Restricted
            CameraAuthorization.Unknown -> PermissionRequestability.Unknown
        }, capability = "camera"))
