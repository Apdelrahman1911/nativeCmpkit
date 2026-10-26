// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

import platform.AVFoundation.*

internal class AVCameraPermissionHelper(private val type: AVMediaType) : PermissionSnapshotHelper {
    override fun launchPermissionRequest(onPermissionResult: (Boolean) -> Unit) {
        handleLaunchPermissionRequest(onPermissionResult) {
            AVCaptureDevice.requestAccessForMediaType(type) { granted -> onPermissionResult(granted) }
        }
    }
    override fun getPermissionSnapshot(onResult: (PermissionSnapshot) -> Unit) {
        val authorization = when (AVCaptureDevice.authorizationStatusForMediaType(type)) {
            AVAuthorizationStatusAuthorized -> CameraAuthorization.Authorized
            AVAuthorizationStatusNotDetermined -> CameraAuthorization.NotDetermined
            AVAuthorizationStatusDenied -> CameraAuthorization.Denied
            AVAuthorizationStatusRestricted -> CameraAuthorization.Restricted
            else -> CameraAuthorization.Unknown
        }
        onResult(cameraSnapshot(authorization))
    }
}
