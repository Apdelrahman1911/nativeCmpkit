// SPDX-License-Identifier: Apache-2.0
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package io.github.apdelrahman1911.nativecmpkit.verification.storageprobe

import android.Manifest
import android.app.Activity
import android.app.AppOpsManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.Message
import android.os.Messenger
import android.os.ParcelFileDescriptor
import android.os.Process
import android.provider.DocumentsContract
import android.system.ErrnoException
import android.system.Os
import android.system.OsConstants
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.SideEffect
import androidx.lifecycle.Lifecycle
import com.mohamedrejeb.calf.permissions.Permission
import com.mohamedrejeb.calf.permissions.PermissionState
import com.mohamedrejeb.calf.permissions.WriteStorage
import com.mohamedrejeb.calf.permissions.details
import com.mohamedrejeb.calf.permissions.isGranted
import com.mohamedrejeb.calf.permissions.rememberPermissionState
import java.io.File
import java.security.MessageDigest

private const val REPORTER = "com.mohamedrejeb.calf.calfpermissions.calfpermissionscore.test"
private const val AUTHORITY = REPORTER + ".storage-documents"

/** Real public library factory in the UID whose file operations are measured. */
class StorageProbeActivity : ComponentActivity() {
    companion object { @Volatile var active: StorageProbeActivity? = null }
    private val document = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        val session = checkNotNull(StorageSession.current)
        check(result.resultCode == Activity.RESULT_OK)
        val data = checkNotNull(result.data)
        val uri = checkNotNull(data.data)
        check(uri == session.documentUri)
        check(data.flags and Intent.FLAG_GRANT_READ_URI_PERMISSION != 0)
        contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
        check(contentResolver.persistedUriPermissions.any { it.uri == uri && it.isReadPermission })
        session.frameworkResult = true
        session.resultFlags = data.flags
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        active = this
        val session = checkNotNull(StorageSession.current)
        setContent {
            val state = rememberPermissionState(Permission.WriteStorage) { granted ->
                session.callbackCount++
                session.lastResult = granted
            }
            SideEffect { session.writeState = state }
        }
    }

    fun selectDocument(session: StorageSession) {
        check(lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED))
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "application/octet-stream"
            putExtra(DocumentsContract.EXTRA_INITIAL_URI, DocumentsContract.buildRootUri(AUTHORITY, "storage-root"))
        }
        val resolved = checkNotNull(packageManager.resolveActivity(intent, PackageManager.MATCH_DEFAULT_ONLY))
        check(resolved.activityInfo.packageName in setOf("com.android.documentsui", "com.google.android.documentsui"))
        check(resolved.activityInfo.applicationInfo.flags and ApplicationInfo.FLAG_SYSTEM != 0)
        check(resolved.activityInfo.applicationInfo.uid != Process.myUid())
        session.documentsUiPackage = resolved.activityInfo.packageName
        document.launch(intent)
    }

    override fun onDestroy() {
        if (active === this) active = null
        StorageSession.current?.writeState = null
        super.onDestroy()
    }
}

/** Finite signature admission; no arbitrary path, operation, package or grant API. */
class StorageProbeService : Service() {
    private val endpoint = Messenger(Handler(Looper.getMainLooper()) { request ->
        val packages = packageManager.getPackagesForUid(request.sendingUid)
        if (request.replyTo == null || packages?.toSet() != setOf(REPORTER) ||
            packageManager.checkSignatures(packageName, REPORTER) != PackageManager.SIGNATURE_MATCH) return@Handler true
        val input = request.data
        val nonce = input.getString("nonce", "")
        if (!nonce.matches(Regex("[a-f0-9]{32}"))) return@Handler true
        val response = Bundle()
        try {
            when (input.getString("operation")) {
                "begin" -> {
                    check(StorageSession.current == null)
                    val caseNonce = input.getString("case_nonce", "")
                    check(caseNonce.matches(Regex("[a-f0-9]{32}")))
                    val uri = Uri.parse(input.getString("document_uri", ""))
                    check(uri == DocumentsContract.buildDocumentUri(AUTHORITY, caseNonce + ".bin"))
                    val session = StorageSession(this, caseNonce, uri)
                    StorageControlRecord.begin(this, caseNonce, uri)
                    StorageSession.current = session
                }
                "snapshot" -> Unit
                "request-write" -> checkNotNull(StorageSession.current?.writeState).launchPermissionRequest()
                "app-scoped" -> response.putAll(checkNotNull(StorageSession.current).appScoped())
                "shared-root" -> response.putAll(checkNotNull(StorageSession.current).sharedRoot())
                "saf-denied" -> response.putBoolean("saf.denied", checkNotNull(StorageSession.current).documentDenied())
                "saf-select" -> checkNotNull(StorageProbeActivity.active).selectDocument(checkNotNull(StorageSession.current))
                "saf-read" -> response.putAll(checkNotNull(StorageSession.current).readSelectedDocument())
                "saf-release-finish" -> {
                    val session = checkNotNull(StorageSession.current)
                    check(session.frameworkResult)
                    session.releaseOwnedPersistedRead(requirePresent = true)
                    checkNotNull(StorageProbeActivity.active).finishAndRemoveTask()
                }
                "saf-cleanup" -> {
                    checkNotNull(StorageSession.current).releaseOwnedPersistedRead(requirePresent = false)
                    StorageProbeActivity.active?.finishAndRemoveTask()
                }
                "saf-permission" -> {
                    val uri = checkNotNull(StorageSession.current).documentUri
                    response.putBoolean("saf.nativeReadGrant", checkUriPermission(uri, Process.myPid(), Process.myUid(),
                        Intent.FLAG_GRANT_READ_URI_PERMISSION) == PackageManager.PERMISSION_GRANTED)
                }
                "close" -> {
                    StorageSession.current?.releaseOwnedPersistedRead(requirePresent = false)
                    StorageProbeActivity.active?.finishAndRemoveTask()
                    StorageSession.current?.writeState = null
                    StorageSession.current = null
                }
                else -> error("Unknown storage operation")
            }
            StorageSession.current?.snapshot()?.let(response::putAll)
        } catch (failure: Exception) {
            response.putString("probeError", "owned-storage-operation-failed")
        }
        response.putAll(StorageProbeIdentity.read(this))
        response.putString("nonce", nonce)
        response.putString("package", packageName)
        response.putInt("uid", Process.myUid()); response.putInt("pid", Process.myPid())
        response.putInt("sdk", Build.VERSION.SDK_INT)
        response.putInt("target", applicationInfo.targetSdkVersion)
        response.putString("mode", BuildConfig.STORAGE_MODE)
        val message = Message.obtain().apply { data = response }
        try { request.replyTo.send(message) } finally { message.recycle() }
        true
    })
    override fun onBind(intent: Intent?): IBinder = endpoint.binder
}

/** Synthetic bytes only. Every protected operation runs in this application's normal UID. */
class StorageSession(private val context: Context, private val nonce: String, val documentUri: Uri) {
    companion object { @Volatile var current: StorageSession? = null }
    init { check(context.contentResolver.persistedUriPermissions.isEmpty()) }
    var writeState: PermissionState? = null
    var callbackCount = 0
    var lastResult: Boolean? = null
    var frameworkResult = false
    var persistedReleased = false
    var resultFlags = 0
    var documentsUiPackage: String? = null
    private val payload = ByteArray(257) { (it % 256).toByte() }

    fun snapshot() = Bundle().apply {
        putBoolean("nativeWrite", context.checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE) == PackageManager.PERMISSION_GRANTED)
        putBoolean("legacy", Build.VERSION.SDK_INT < 29 || Environment.isExternalStorageLegacy())
        if (Build.VERSION.SDK_INT >= 30) {
            putBoolean("manager", Environment.isExternalStorageManager())
            val appops = checkNotNull(context.getSystemService(AppOpsManager::class.java))
            val managerOp = checkNotNull(AppOpsManager.permissionToOp(Manifest.permission.MANAGE_EXTERNAL_STORAGE))
            putInt("managerMode", appops.unsafeCheckOpNoThrow(managerOp,
                Process.myUid(), context.packageName))
        }
        putBoolean("resumed", StorageProbeActivity.active?.lifecycle?.currentState?.isAtLeast(Lifecycle.State.RESUMED) == true)
        putBoolean("activityActive", StorageProbeActivity.active != null)
        putBoolean("writeReady", writeState != null)
        writeState?.let {
            putBoolean("write.granted", it.status.isGranted)
            putString("write.availability", it.details.availability.name)
            putString("write.access", it.details.access.name)
            putString("write.lastRequest", it.details.lastRequest?.name)
        }
        putInt("callbackCount", callbackCount)
        lastResult?.let { putBoolean("lastResult", it) }
        putBoolean("saf.frameworkResult", frameworkResult)
        putBoolean("saf.persistedReleased", persistedReleased)
        putString("documentsUiPackage", documentsUiPackage)
    }

    fun appScoped(): Bundle {
        check(Environment.getExternalStorageState() == Environment.MEDIA_MOUNTED)
        return probeOwnedFile(checkNotNull(context.getExternalFilesDir(null)), "app", denialAllowed = false)
    }

    @Suppress("DEPRECATION")
    fun sharedRoot(): Bundle {
        check(Environment.getExternalStorageState() == Environment.MEDIA_MOUNTED)
        return probeOwnedFile(Environment.getExternalStorageDirectory(), "shared", denialAllowed = true)
    }

    private fun probeOwnedFile(directory: File, prefix: String, denialAllowed: Boolean): Bundle {
        check(directory.isDirectory)
        val file = File(directory, "nativecmpkit-storage-" + nonce + ".bin")
        var created = false
        var closed = false
        var primary: Throwable? = null
        val response = Bundle()
        try {
            val descriptor = Os.open(file.absolutePath, OsConstants.O_RDWR or OsConstants.O_CREAT or OsConstants.O_EXCL, 384)
            created = true
            var operationFailure: Throwable? = null
            try {
                var offset = 0
                while (offset < payload.size) {
                    val count = Os.write(descriptor, payload, offset, payload.size - offset)
                    check(count > 0); offset += count
                }
                check(Os.lseek(descriptor, 0L, OsConstants.SEEK_SET) == 0L)
                val actual = ByteArray(payload.size)
                offset = 0
                while (offset < actual.size) {
                    val count = Os.read(descriptor, actual, offset, actual.size - offset)
                    check(count > 0); offset += count
                }
                check(Os.read(descriptor, ByteArray(1), 0, 1) == 0)
                check(actual.contentEquals(payload))
                response.putString(prefix + ".sha256", sha256(actual))
            } catch (failure: Throwable) { operationFailure = failure; throw failure }
            finally {
                preserveCleanup(operationFailure) {
                    Os.close(descriptor); check(!descriptor.valid()); closed = true
                }
            }
            response.putBoolean(prefix + ".allowed", true)
            response.putInt(prefix + ".errno", 0)
        } catch (failure: ErrnoException) {
            if (!denialAllowed || created || failure.errno !in setOf(OsConstants.EACCES, OsConstants.EPERM)) {
                primary = failure; throw failure
            }
            response.putBoolean(prefix + ".allowed", false)
            response.putInt(prefix + ".errno", failure.errno)
        } catch (failure: Throwable) { primary = failure; throw failure }
        finally {
            preserveCleanup(primary) {
                if (created) {
                    Os.remove(file.absolutePath)
                    try { Os.lstat(file.absolutePath); error("Owned file still exists after unlink") }
                    catch (failure: ErrnoException) { check(failure.errno == OsConstants.ENOENT) }
                }
            }
        }
        response.putBoolean(prefix + ".opened", created)
        response.putBoolean(prefix + ".closed", closed)
        response.putBoolean(prefix + ".cleanup", true)
        return response
    }

    private fun preserveCleanup(primary: Throwable?, action: () -> Unit) {
        try { action() }
        catch (failure: Throwable) { if (primary == null) throw failure else primary.addSuppressed(failure) }
    }

    fun releaseOwnedPersistedRead(requirePresent: Boolean) {
        val persisted = context.contentResolver.persistedUriPermissions
        check(persisted.all { it.uri == documentUri && it.isReadPermission && !it.isWritePermission })
        val owned = persisted.singleOrNull()
        check(!requirePresent || owned != null)
        if (owned != null) context.contentResolver.releasePersistableUriPermission(documentUri,
            Intent.FLAG_GRANT_READ_URI_PERMISSION)
        check(context.contentResolver.persistedUriPermissions.isEmpty())
        persistedReleased = true
    }

    fun documentDenied(): Boolean {
        try {
            checkNotNull(context.contentResolver.openFileDescriptor(documentUri, "r")).use { }
            return false
        } catch (failure: SecurityException) { return true }
    }

    fun readSelectedDocument(): Bundle {
        check(frameworkResult)
        check(context.contentResolver.persistedUriPermissions.any { it.uri == documentUri && it.isReadPermission })
        val opened = checkNotNull(context.contentResolver.openFileDescriptor(documentUri, "r"))
        val descriptor = opened.fileDescriptor
        val actual = ParcelFileDescriptor.AutoCloseInputStream(opened).use { it.readBytes() }
        check(actual.contentEquals(payload)); check(!descriptor.valid())
        return Bundle().apply {
            putString("saf.sha256", sha256(actual)); putBoolean("saf.descriptorClosed", true)
            putBoolean("saf.persistedRead", true); putInt("saf.resultFlags", resultFlags)
        }
    }

    private fun sha256(bytes: ByteArray) = MessageDigest.getInstance("SHA-256").digest(bytes)
        .joinToString("") { "%02x".format(it.toInt() and 255) }
}
