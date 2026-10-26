// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
package com.mohamedrejeb.calf.permissions.helper

/** Permission authorization plus an APNs registration attempt, never a token-delivery promise. */
internal class RemoteNotificationPermissionHelper : LocalNotificationPermissionHelper(remote = true)
