// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.permissioncompat

import android.app.Service
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.Message
import android.os.Messenger
import android.os.Process
import android.os.RemoteException
import java.util.UUID

/** Actual signed Binder sender plus exact finite operation and fresh request nonce. */
class PermissionCompatibilityService : Service() {
    private val generation = UUID.randomUUID().toString()
    private val endpoint = Messenger(Handler(Looper.getMainLooper()) { request ->
        val names = packageManager.getPackagesForUid(request.sendingUid)?.toList()
        if (request.replyTo != null && names == listOf(REPORTER) &&
            packageManager.checkSignatures(packageName, REPORTER) == PackageManager.SIGNATURE_MATCH) {
            val nonce = request.data.getString("nonce", "")
            val operation = request.data.getString("operation", "")
            if (nonce.matches(Regex("[a-f0-9]{32}")) && operation in OPERATIONS) {
                val native = Bundle()
                try {
                    if (operation != "observe") checkNotNull(PermissionCompatibilityActivity.active).perform(operation)
                    PermissionCompatibilityActivity.active?.snapshot()?.let { native.putAll(it) }
                    native.putBoolean("activityActive", PermissionCompatibilityActivity.active != null)
                    if (PermissionCompatibilityActivity.cleanupFailed) native.putString("probeError", "owned-cleanup-failed")
                    val info = packageManager.getPackageInfo(packageName, PackageManager.GET_PERMISSIONS)
                    native.putStringArray("declaredPermissions", info.requestedPermissions ?: emptyArray())
                    native.putLong("firstInstallTime", info.firstInstallTime)
                    native.putLong("lastUpdateTime", info.lastUpdateTime)
                    native.putInt("targetSdk", applicationInfo.targetSdkVersion)
                    native.putString("profile", BuildConfig.VERIFICATION_PROFILE)
                    native.putString("role", BuildConfig.VERIFICATION_ROLE)
                } catch (failure: Exception) { native.putString("probeError", "finite-native-operation-failed") }
                native.putString("nonce", nonce)
                native.putString("generation", generation)
                native.putInt("uid", Process.myUid())
                native.putInt("pid", Process.myPid())
                native.putInt("apiLevel", Build.VERSION.SDK_INT)
                val response = Message.obtain().apply { data = native }
                try { request.replyTo.send(response) }
                catch (disconnected: RemoteException) { /* Independent reporter retains its bounded failure. */ }
                finally { response.recycle() }
            }
        }
        true
    })
    override fun onBind(intent: Intent): IBinder = endpoint.binder
    companion object {
        private const val REPORTER = "io.github.apdelrahman1911.nativecmpkit.verification.permissioncompat.reporter"
        private val OPERATIONS = setOf("observe", "request-fine", "request-coarse", "request-background", "request-camera",
            "request-batch", "request-batch-retained", "open-fine-settings", "open-background-settings", "open-camera-settings",
            "open-location-services", "dispose-content", "finish")
    }
}
