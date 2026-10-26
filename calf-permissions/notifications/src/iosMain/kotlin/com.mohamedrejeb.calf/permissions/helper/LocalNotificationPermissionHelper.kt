// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

import platform.UIKit.UIApplication
import platform.UIKit.registerForRemoteNotifications
import platform.UserNotifications.*

internal open class LocalNotificationPermissionHelper(private val remote: Boolean = false) : PermissionSnapshotHelper, PermissionLifecycleHelper {
    private val center = UNUserNotificationCenter.currentNotificationCenter()
    private var disposed = false
    private var outcome: PermissionRequestOutcome? = null

    override fun launchPermissionRequest(onPermissionResult: (Boolean) -> Unit) {
        outcome = null
        getPermissionSnapshot { snapshot ->
            if (disposed) return@getPermissionSnapshot
            if (snapshot.status.isGranted) finish(true, onPermissionResult)
            else if (snapshot.details.requestability == PermissionRequestability.Requestable) {
                center.requestAuthorizationWithOptions(UNAuthorizationOptionSound.or(UNAuthorizationOptionAlert).or(UNAuthorizationOptionBadge)) { granted, error ->
                    runOnPermissionMainThread {
                        if (!disposed) {
                            outcome = if (error != null) PermissionRequestOutcome.Failed
                                else if (granted) PermissionRequestOutcome.Granted else PermissionRequestOutcome.Denied
                            finish(granted && error == null, onPermissionResult)
                        }
                    }
                }
            } else finish(false, onPermissionResult)
        }
    }
    private fun finish(granted: Boolean, callback: (Boolean) -> Unit) {
        // Both already-authorized and fresh-grant branches run here, on Main.
        finishNotificationRequest(granted, remote, {
            UIApplication.sharedApplication.registerForRemoteNotifications()
        }, callback)
    }
    override fun getPermissionSnapshot(onResult: (PermissionSnapshot) -> Unit) {
        center.getNotificationSettingsWithCompletionHandler { settings ->
            runOnPermissionMainThread {
                if (!disposed) {
                    val authorization = when (settings?.authorizationStatus) {
                        UNAuthorizationStatusAuthorized -> NotificationAuthorization.Authorized
                        UNAuthorizationStatusProvisional -> NotificationAuthorization.Provisional
                        UNAuthorizationStatusEphemeral -> NotificationAuthorization.Ephemeral
                        UNAuthorizationStatusNotDetermined -> NotificationAuthorization.NotDetermined
                        UNAuthorizationStatusDenied -> NotificationAuthorization.Denied
                        else -> NotificationAuthorization.Unknown
                    }
                    val snapshot = notificationSnapshot(authorization)
                    onResult(snapshot.copy(details = snapshot.details.copy(lastRequest = outcome)))
                }
            }
        }
    }
    override fun dispose() { disposed = true }
}
