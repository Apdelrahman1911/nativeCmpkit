@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

internal enum class BluetoothAuthorization { Unknown, NotDetermined, Allowed, Denied, Restricted, Unsupported }
internal fun bluetoothSnapshot(authorization: BluetoothAuthorization, outcome: PermissionRequestOutcome? = null): PermissionSnapshot =
    PermissionSnapshot(if (authorization == BluetoothAuthorization.Allowed) PermissionStatus.Granted
        else PermissionStatus.Denied(authorization == BluetoothAuthorization.Denied || authorization == BluetoothAuthorization.Restricted),
        PermissionDetails(if (authorization == BluetoothAuthorization.Unsupported) PermissionAvailability.Unsupported else PermissionAvailability.Available,
            when (authorization) {
                BluetoothAuthorization.Allowed -> PermissionAccess.Full
                BluetoothAuthorization.Denied, BluetoothAuthorization.Restricted -> PermissionAccess.None
                else -> PermissionAccess.Unknown
            }, when (authorization) {
                BluetoothAuthorization.Allowed -> PermissionRequestability.NotRequired
                BluetoothAuthorization.NotDetermined -> PermissionRequestability.Requestable
                BluetoothAuthorization.Denied -> PermissionRequestability.SettingsOnly
                BluetoothAuthorization.Restricted -> PermissionRequestability.Restricted
                BluetoothAuthorization.Unsupported -> PermissionRequestability.Unsupported
                BluetoothAuthorization.Unknown -> PermissionRequestability.Unknown
            }, lastRequest = outcome, capability = "bluetooth-authorization"))
