// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

import platform.Photos.*
import platform.UIKit.UIDevice

internal class GalleryPermissionHelper : PermissionSnapshotHelper {
    private fun modern() = (UIDevice.currentDevice.systemVersion.substringBefore('.').toIntOrNull() ?: 0) >= 14
    override fun launchPermissionRequest(onPermissionResult: (Boolean) -> Unit) {
        handleLaunchPermissionRequest(onPermissionResult) {
            val completion: (PHAuthorizationStatus) -> Unit = { onPermissionResult(gallerySnapshot(authorization(it)).status.isGranted) }
            if (modern()) PHPhotoLibrary.requestAuthorizationForAccessLevel(PHAccessLevelReadWrite, completion)
            else PHPhotoLibrary.requestAuthorization(completion)
        }
    }
    override fun getPermissionSnapshot(onResult: (PermissionSnapshot) -> Unit) {
        val current = if (modern()) PHPhotoLibrary.authorizationStatusForAccessLevel(PHAccessLevelReadWrite)
            else PHPhotoLibrary.authorizationStatus()
        onResult(gallerySnapshot(authorization(current)))
    }
    private fun authorization(status: PHAuthorizationStatus) = when (status) {
        PHAuthorizationStatusAuthorized -> GalleryAuthorization.Full
        PHAuthorizationStatusLimited -> GalleryAuthorization.Limited
        PHAuthorizationStatusNotDetermined -> GalleryAuthorization.NotDetermined
        PHAuthorizationStatusDenied -> GalleryAuthorization.Denied
        PHAuthorizationStatusRestricted -> GalleryAuthorization.Restricted
        else -> GalleryAuthorization.Unknown
    }
}
