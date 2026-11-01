// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.permissiondemo

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

/** Only the exact independently signed reporter can drive these finite public-library operations. */
class PermissionDemoService : Service() {
    private val generation = UUID.randomUUID().toString()
    private val endpoint = Messenger(Handler(Looper.getMainLooper()) { request ->
        val names = packageManager.getPackagesForUid(request.sendingUid)?.toList()
        if (request.replyTo != null && names == listOf(REPORTER) &&
            packageManager.checkSignatures(packageName, REPORTER) == PackageManager.SIGNATURE_MATCH) {
            val nonce = request.data.getString("nonce", "")
            val operation = request.data.getString("operation", "")
            if (nonce.matches(Regex("[a-f0-9]{32}"))) {
                val observation = Bundle()
                try {
                    if (operation != "observe") checkNotNull(PermissionDemoActivity.active).perform(operation)
                    PermissionDemoActivity.active?.snapshot()?.let { observation.putAll(it) }
                    observation.putBoolean("activityActive", PermissionDemoActivity.active != null)
                    if (PermissionDemoActivity.cleanupFailed) observation.putString("probeError", "owned-source-cleanup-failed")
                    val info = packageManager.getPackageInfo(packageName, PackageManager.GET_PERMISSIONS)
                    observation.putStringArray("declaredPermissions", info.requestedPermissions ?: emptyArray())
                    observation.putLong("firstInstallTime", info.firstInstallTime)
                    observation.putLong("lastUpdateTime", info.lastUpdateTime)
                    observation.putInt("targetSdk", applicationInfo.targetSdkVersion)
                } catch (failure: Exception) {
                    observation.putString("probeError", "finite-native-operation-failed")
                }
                observation.putString("nonce", nonce)
                observation.putString("generation", generation)
                observation.putInt("uid", Process.myUid())
                observation.putInt("pid", Process.myPid())
                observation.putInt("apiLevel", Build.VERSION.SDK_INT)
                val response = Message.obtain().apply { data = observation }
                try { request.replyTo.send(response) }
                catch (disconnected: RemoteException) { /* Reporter observes its own bounded failure. */ }
                finally { response.recycle() }
            }
        }
        true
    })
    override fun onBind(intent: Intent): IBinder = endpoint.binder
    companion object {
        private const val REPORTER = "com.mohamedrejeb.calf.calfpermissions.calfpermissionscore.test"
    }
}
