@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

internal enum class MicrophoneAuthorization { Unknown, NotDetermined, Denied, Restricted, Authorized }
internal fun microphoneSnapshot(authorization: MicrophoneAuthorization): PermissionSnapshot =
    PermissionSnapshot(if (authorization == MicrophoneAuthorization.Authorized) PermissionStatus.Granted
        else PermissionStatus.Denied(authorization == MicrophoneAuthorization.Denied || authorization == MicrophoneAuthorization.Restricted),
        PermissionDetails(PermissionAvailability.Available, when (authorization) {
            MicrophoneAuthorization.Authorized -> PermissionAccess.Full
            MicrophoneAuthorization.Denied, MicrophoneAuthorization.Restricted -> PermissionAccess.None
            else -> PermissionAccess.Unknown
        }, when (authorization) {
            MicrophoneAuthorization.Authorized -> PermissionRequestability.NotRequired
            MicrophoneAuthorization.NotDetermined -> PermissionRequestability.Requestable
            MicrophoneAuthorization.Denied -> PermissionRequestability.SettingsOnly
            MicrophoneAuthorization.Restricted -> PermissionRequestability.Restricted
            MicrophoneAuthorization.Unknown -> PermissionRequestability.Unknown
        }, capability = "microphone"))
