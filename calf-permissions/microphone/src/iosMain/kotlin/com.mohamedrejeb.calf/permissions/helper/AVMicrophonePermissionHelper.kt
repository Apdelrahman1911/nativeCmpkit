// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

import platform.AVFoundation.*

internal class AVMicrophonePermissionHelper(private val type: AVMediaType) : PermissionSnapshotHelper {
    override fun launchPermissionRequest(onPermissionResult: (Boolean) -> Unit) {
        handleLaunchPermissionRequest(onPermissionResult) {
            AVCaptureDevice.requestAccessForMediaType(type) { granted -> onPermissionResult(granted) }
        }
    }
    override fun getPermissionSnapshot(onResult: (PermissionSnapshot) -> Unit) {
        val authorization = when (AVCaptureDevice.authorizationStatusForMediaType(type)) {
            AVAuthorizationStatusAuthorized -> MicrophoneAuthorization.Authorized
            AVAuthorizationStatusNotDetermined -> MicrophoneAuthorization.NotDetermined
            AVAuthorizationStatusDenied -> MicrophoneAuthorization.Denied
            AVAuthorizationStatusRestricted -> MicrophoneAuthorization.Restricted
            else -> MicrophoneAuthorization.Unknown
        }
        onResult(microphoneSnapshot(authorization))
    }
}
