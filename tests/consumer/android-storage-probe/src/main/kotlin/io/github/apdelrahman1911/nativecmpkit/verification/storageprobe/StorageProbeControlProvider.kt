// SPDX-License-Identifier: Apache-2.0
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package io.github.apdelrahman1911.nativecmpkit.verification.storageprobe

import android.Manifest
import android.app.AppOpsManager
import android.content.ContentProvider
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.database.Cursor
import android.net.Uri
import android.os.Binder
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.os.Handler
import android.os.Looper
import android.os.Process
import android.os.SystemClock
import android.provider.DocumentsContract
import android.util.AtomicFile
import java.io.File
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import org.json.JSONObject

/** Only a fixed reporter-authority nonce URI; persisted before any grant can exist. */
internal object StorageControlRecord {
    private const val AUTHORITY = "com.mohamedrejeb.calf.calfpermissions.calfpermissionscore.test.storage-documents"
    private const val PREFERENCES = "owned-storage-record"
    private fun preferences(context: Context) = context.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE)
    fun ownedUri(nonce: String): Uri {
        check(nonce.matches(Regex("[a-f0-9]{32}")))
        return DocumentsContract.buildDocumentUri(AUTHORITY, nonce + ".bin")
    }
    @Synchronized fun begin(context: Context, nonce: String, uri: Uri) {
        check(uri == ownedUri(nonce))
        val stored = preferences(context)
        check(stored.all.isEmpty())
        check(context.contentResolver.persistedUriPermissions.isEmpty())
        check(stored.edit().putString("nonce", nonce).putString("uri", uri.toString()).commit())
    }
    @Synchronized fun hasRecord(context: Context, nonce: String): Boolean {
        val stored = preferences(context)
        if (stored.all.isEmpty()) return false
        check(stored.all.keys == setOf("nonce", "uri"))
        check(stored.getString("nonce", null) == nonce && stored.getString("uri", null) == ownedUri(nonce).toString())
        return true
    }
    @Synchronized fun clear(context: Context, nonce: String) {
        check(hasRecord(context, nonce) || preferences(context).all.isEmpty())
        check(preferences(context).edit().clear().commit())
    }
}

/** DUMP plus exact Shell UID, finite status/cleanup only; protected I/O stays app UID. */
class StorageProbeControlProvider : ContentProvider() {
    override fun onCreate() = true
    override fun call(method: String, arg: String?, extras: Bundle?): Bundle {
        val context = checkNotNull(context)
        check(Binder.getCallingUid() == 2000)
        context.enforceCallingPermission("android.permission.DUMP", "Owned storage control requires Shell DUMP")
        check(method in setOf("status", "cleanup"))
        val nonce = checkNotNull(arg)
        check(nonce.matches(Regex("[a-f0-9]{32}")))
        check(extras?.keySet() == setOf("request_nonce"))
        val requestNonce = checkNotNull(extras?.getString("request_nonce"))
        check(requestNonce.matches(Regex("[a-f0-9]{32}")))
        // Clear only the Binder identity, never adopt Shell for protected work.
        // Package, grant and descriptor operations below execute in Process.myUid().
        val token = Binder.clearCallingIdentity()
        try {
            val status = try { observe(context, method, nonce, requestNonce) }
            catch (failure: Exception) {
                JSONObject().put("schema", "nativecmpkit-storage-control-v1").put("operation", method)
                    .put("case_nonce", nonce).put("request_nonce", requestNonce).put("status", "failed")
            }
            publish(context, nonce, status)
            return Bundle().apply { putBoolean("published", true) }
        } finally { Binder.restoreCallingIdentity(token) }
    }

    private fun observe(context: Context, method: String, nonce: String, requestNonce: String): JSONObject {
        val uri = StorageControlRecord.ownedUri(nonce)
        val record = StorageControlRecord.hasRecord(context, nonce)
        val before = context.contentResolver.persistedUriPermissions
        check(before.all { it.uri == uri && it.isReadPermission && !it.isWritePermission })
        check(before.size <= 1 && (record || before.isEmpty()))
        check(StorageSession.current == null || StorageControlRecord.hasRecord(context, nonce))
        var released = false
        var cleared = false
        if (method == "cleanup") {
            // Unknown/foreign persisted grants or private records were refused
            // above. Release only the original fixed URI in this ordinary UID.
            if (before.isNotEmpty()) context.contentResolver.releasePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
            check(context.contentResolver.persistedUriPermissions.isEmpty())
            val removed = CountDownLatch(1)
            check(Handler(Looper.getMainLooper()).post {
                StorageProbeActivity.active?.finishAndRemoveTask()
                StorageSession.current?.writeState = null
                removed.countDown()
            })
            check(removed.await(10, TimeUnit.SECONDS))
            val deadline = SystemClock.elapsedRealtime() + 10000
            while (StorageProbeActivity.active != null && SystemClock.elapsedRealtime() < deadline) Thread.sleep(25)
            check(StorageProbeActivity.active == null)
            check(context.checkUriPermission(uri, Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_READ_URI_PERMISSION) ==
                PackageManager.PERMISSION_DENIED)
            check(context.contentResolver.persistedUriPermissions.isEmpty())
            StorageControlRecord.clear(context, nonce)
            StorageSession.current = null
            released = true; cleared = true
        }
        val actual = context.contentResolver.persistedUriPermissions
        check(actual.all { it.uri == uri && it.isReadPermission && !it.isWritePermission } && actual.size <= 1)
        val nativeIdentity = StorageProbeIdentity.read(context)
        val status = JSONObject().put("schema", "nativecmpkit-storage-control-v1").put("operation", method)
            .put("case_nonce", nonce).put("request_nonce", requestNonce).put("status", "passed")
            .put("package", context.packageName).put("uid", Process.myUid()).put("pid", Process.myPid())
            .put("sdk", Build.VERSION.SDK_INT).put("target", context.applicationInfo.targetSdkVersion).put("mode", BuildConfig.STORAGE_MODE)
            .put("apk_sha256", nativeIdentity.getString("apkSha256")).put("certificate_sha256", nativeIdentity.getString("certificateSha256"))
            .put("splits_absent", nativeIdentity.getBoolean("splitsAbsent"))
            .put("record_present", StorageControlRecord.hasRecord(context, nonce)).put("activity_active", StorageProbeActivity.active != null)
            .put("persisted_read_count", actual.size).put("foreign_persisted_count", 0)
            .put("native_read_grant", context.checkUriPermission(uri, Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_READ_URI_PERMISSION) ==
                PackageManager.PERMISSION_GRANTED)
            .put("write_granted", context.checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE) == PackageManager.PERMISSION_GRANTED)
            .put("release_verified", released).put("record_cleared", cleared)
        if (Build.VERSION.SDK_INT >= 30) {
            val appops = checkNotNull(context.getSystemService(AppOpsManager::class.java))
            val managerOp = checkNotNull(AppOpsManager.permissionToOp(Manifest.permission.MANAGE_EXTERNAL_STORAGE))
            status.put("manager", Environment.isExternalStorageManager()).put("manager_mode",
                appops.unsafeCheckOpNoThrow(managerOp, Process.myUid(), context.packageName))
        } else { status.put("manager", JSONObject.NULL).put("manager_mode", JSONObject.NULL) }
        return status
    }

    private fun publish(context: Context, nonce: String, status: JSONObject) {
        val bytes = status.toString().toByteArray(Charsets.UTF_8)
        check(bytes.size in 1..65536)
        val atomic = AtomicFile(File(context.filesDir, "storage-control-" + nonce + ".json"))
        val stream = atomic.startWrite()
        try { stream.write(bytes); atomic.finishWrite(stream) }
        catch (failure: Throwable) {
            try { atomic.failWrite(stream) } catch (cleanup: Throwable) { failure.addSuppressed(cleanup) }
            throw failure
        }
    }

    override fun query(uri: Uri, projection: Array<out String>?, selection: String?, selectionArgs: Array<out String>?, sortOrder: String?): Cursor =
        throw SecurityException("No generic storage-control query")
    override fun getType(uri: Uri): String = throw SecurityException("No generic storage-control type")
    override fun insert(uri: Uri, values: ContentValues?): Uri = throw SecurityException("No generic storage-control insert")
    override fun update(uri: Uri, values: ContentValues?, selection: String?, selectionArgs: Array<out String>?): Int =
        throw SecurityException("No generic storage-control update")
    override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?): Int =
        throw SecurityException("No generic storage-control delete")
}
