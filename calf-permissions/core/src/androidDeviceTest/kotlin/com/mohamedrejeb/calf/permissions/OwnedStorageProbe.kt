// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.permissions

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Handler
import android.os.HandlerThread
import android.os.IBinder
import android.os.Looper
import android.os.Message
import android.os.Messenger
import android.os.Process
import android.os.SystemClock
import androidx.test.platform.app.InstrumentationRegistry
import java.util.UUID
import java.io.File
import java.security.MessageDigest
import android.system.Os
import android.system.OsConstants
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import kotlin.test.*


private data class StorageInvocation(val profile: String, val api: Int, val flavor: String, val target: Int,
    val installedUid: Int, val apkSha256: String, val reporterApkSha256: String, val certificateSha256: String)

private fun storageInvocation(mode: String, target: Int): StorageInvocation {
    val args = InstrumentationRegistry.getArguments()
    assertEquals("true", args.getString("nativecmpkitOwnedStorageProbe"), "Only exact prepared controller dispatch is admitted")
    val profile = assertNotNull(args.getString("nativecmpkitStorageProfile"))
    val rows = mapOf(
        "android-storage-api28" to Triple(28, "legacy28", 28),
        "android-storage-api29-target28" to Triple(29, "legacyTarget28", 28),
        "android-storage-api29-legacy" to Triple(29, "legacy29", 29),
        "android-storage-api29-scoped" to Triple(29, "scoped29", 29),
        "android-storage-api30-normal" to Triple(30, "modern", 35),
        "android-storage-api30-all-files" to Triple(30, "allFiles", 35),
        "android-storage-api35-normal" to Triple(35, "modern", 35),
        "android-storage-api35-all-files" to Triple(35, "allFiles", 35),
    )
    val row = assertNotNull(rows[profile])
    assertEquals(row.first.toString(), args.getString("nativecmpkitStorageApi"))
    assertEquals(row.second, args.getString("nativecmpkitStorageFlavor")); assertEquals(mode, row.second)
    assertEquals(row.third.toString(), args.getString("nativecmpkitStorageTarget")); assertEquals(target, row.third)
    assertEquals(row.first, android.os.Build.VERSION.SDK_INT)
    fun hash(key: String) = assertNotNull(args.getString(key)).also { assertTrue(it.matches(Regex("[a-f0-9]{64}"))) }
    val uid = assertNotNull(args.getString("nativecmpkitStorageInstalledUid")).also {
        assertTrue(it.matches(Regex("[0-9]{5,7}")))
    }.toInt()
    assertTrue(uid >= 10000); assertNotEquals(Process.myUid(), uid)
    return StorageInvocation(profile, row.first, row.second, row.third, uid,
        hash("nativecmpkitStorageApkSha256"), hash("nativecmpkitStorageReporterApkSha256"),
        hash("nativecmpkitStorageCertificateSha256"))
}

private fun certificate(context: Context, packageName: String): String {
    val info = context.packageManager.getPackageInfo(packageName, PackageManager.GET_SIGNING_CERTIFICATES)
    val signing = assertNotNull(info.signingInfo)
    assertFalse(signing.hasMultipleSigners()); assertEquals(1, signing.signingCertificateHistory?.size)
    val bytes = signing.apkContentsSigners.single().toByteArray()
    return MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it.toInt() and 255) }
}

private fun ownReporterApkHash(context: Context): String {
    val info = context.packageManager.getPackageInfo(context.packageName, 0)
    val app = assertNotNull(info.applicationInfo)
    assertTrue(app.uid >= 10000); assertEquals(Process.myUid(), app.uid)
    assertEquals("com.mohamedrejeb.calf.calfpermissions.calfpermissionscore.test", context.packageName)
    assertEquals(37, app.targetSdkVersion)
    assertTrue(app.flags and ApplicationInfo.FLAG_DEBUGGABLE != 0)
    assertTrue(info.splitNames.isNullOrEmpty() && app.splitSourceDirs.isNullOrEmpty())
    val file = File(app.sourceDir); val before = Os.lstat(file.absolutePath)
    val limit = 256L * 1024 * 1024
    assertTrue(OsConstants.S_ISREG(before.st_mode) && before.st_size in 1 until limit)
    val digest = MessageDigest.getInstance("SHA-256"); var total = 0L
    file.inputStream().use { stream ->
        val bytes = ByteArray(16384)
        while (true) {
            val count = stream.read(bytes)
            if (count < 0) break
            assertTrue(count > 0); total += count; assertTrue(total < limit); digest.update(bytes, 0, count)
        }
    }
    val after = Os.lstat(file.absolutePath)
    assertEquals(before.st_size, total); assertEquals(before.st_size, after.st_size)
    assertEquals(before.st_ino, after.st_ino); assertEquals(before.st_dev, after.st_dev); assertEquals(before.st_mtime, after.st_mtime)
    return digest.digest().joinToString("") { "%02x".format(it.toInt() and 255) }
}

/** Separate source-consumer UID; never evaluate a file operation as shell or reporter. */
internal class OwnedStorageProbe(private val mode: String, private val target: Int) : AutoCloseable {
    companion object {
        const val PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.storageprobe"
        const val CONTROL = PACKAGE + ".CONTROL_STORAGE"
    }
    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private val invocation = storageInvocation(mode, target).also {
        assertEquals(it.reporterApkSha256, ownReporterApkHash(context))
        assertEquals(it.certificateSha256, certificate(context, context.packageName))
        assertEquals(it.certificateSha256, certificate(context, PACKAGE))
    }
    private val owner = context.packageManager.getApplicationInfo(PACKAGE, 0).also {
        assertTrue(it.uid >= 10000); assertNotEquals(Process.myUid(), it.uid)
        assertEquals(invocation.installedUid, it.uid)
        assertEquals(setOf(PACKAGE), context.packageManager.getPackagesForUid(it.uid)?.toSet())
        assertEquals(target, it.targetSdkVersion)
        assertTrue(it.flags and ApplicationInfo.FLAG_DEBUGGABLE != 0)
        assertEquals(PackageManager.SIGNATURE_MATCH, context.packageManager.checkSignatures(context.packageName, PACKAGE))
        assertEquals(PackageManager.PERMISSION_GRANTED, context.checkSelfPermission(CONTROL))
    }
    private val thread = HandlerThread("owned-storage-replies").apply { start() }
    private class Reply(val nonce: String) { val latch = CountDownLatch(1); @Volatile var data: Bundle? = null }
    @Volatile private var pending: Reply? = null
    @Volatile private var protocolError: String? = null
    @Volatile private var endpoint: Messenger? = null
    private var binder: IBinder? = null
    private val connected = CountDownLatch(1)
    private val dead = CountDownLatch(1)
    private var bound = false
    private var sessionBegun = false
    private val deathRecipient = IBinder.DeathRecipient { endpoint = null; dead.countDown() }
    private val responses = Messenger(Handler(thread.looper) { message ->
        if (message.sendingUid != owner.uid) { protocolError = "Foreign storage response UID"; return@Handler true }
        val data = Bundle(message.data)
        val current = pending
        if (current == null || data.getString("nonce") != current.nonce || current.data != null) {
            protocolError = "Unexpected owned storage reply"
        } else { current.data = data; current.latch.countDown() }
        true
    })
    private val connection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName, service: IBinder) {
            if (name != ComponentName(PACKAGE, PACKAGE + ".StorageProbeService")) {
                protocolError = "Wrong storage component"
            } else {
                service.linkToDeath(deathRecipient, 0)
                binder = service; endpoint = Messenger(service)
            }
            connected.countDown()
        }
        override fun onServiceDisconnected(name: ComponentName) { endpoint = null; dead.countDown() }
        override fun onBindingDied(name: ComponentName) { endpoint = null; dead.countDown() }
        override fun onNullBinding(name: ComponentName) { protocolError = "Null storage binding"; connected.countDown() }
    }

    fun connect() {
        assertFalse(bound)
        bound = context.bindService(Intent().setComponent(ComponentName(PACKAGE, PACKAGE + ".StorageProbeService")),
            connection, Context.BIND_AUTO_CREATE)
        assertTrue(bound)
        assertTrue(connected.await(15, TimeUnit.SECONDS))
        assertNull(protocolError); assertNotNull(endpoint)
    }

    fun foreground() {
        context.startActivity(Intent().setComponent(ComponentName(PACKAGE, PACKAGE + ".StorageProbeActivity"))
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK))
        await { val state = request("snapshot"); state.getBoolean("resumed") && state.getBoolean("writeReady") }
    }

    fun request(operation: String, fields: Bundle = Bundle()): Bundle {
        assertNotEquals(Looper.getMainLooper(), Looper.myLooper())
        assertNull(protocolError); assertNull(pending)
        val reply = Reply(UUID.randomUUID().toString().replace("-", ""))
        pending = reply
        val message = Message.obtain().apply {
            replyTo = responses
            data = Bundle(fields).apply { putString("nonce", reply.nonce); putString("operation", operation) }
        }
        try {
            assertNotNull(endpoint).send(message)
            assertTrue(reply.latch.await(20, TimeUnit.SECONDS), "Owned storage response timed out")
            assertNull(protocolError)
            return assertNotNull(reply.data).also {
                assertEquals(reply.nonce, it.getString("nonce"))
                assertEquals(PACKAGE, it.getString("package"))
                assertEquals(owner.uid, it.getInt("uid")); assertNotEquals(Process.myUid(), it.getInt("uid"))
                assertTrue(it.getInt("pid") > 0); assertNotEquals(Process.myPid(), it.getInt("pid"))
                assertEquals(android.os.Build.VERSION.SDK_INT, it.getInt("sdk"))
                assertEquals(target, it.getInt("target")); assertEquals(mode, it.getString("mode"))
                assertEquals(invocation.apkSha256, it.getString("apkSha256"))
                assertEquals(invocation.certificateSha256, it.getString("certificateSha256"))
                assertTrue(it.getBoolean("splitsAbsent"))
                assertNull(it.getString("probeError"), "A probe operation error is not success")
                if (operation == "begin") sessionBegun = true
            }
        } finally { pending = null; message.recycle() }
    }

    fun awaitDeath() {
        assertTrue(dead.await(15, TimeUnit.SECONDS), "Owned permission restoration must be observed")
        assertFalse(assertNotNull(binder).isBinderAlive, "A connection callback alone is not process death")
        assertNull(endpoint)
    }

    fun stopRebindingBeforeRevocation() {
        // Keep the linked Binder witness, but do not restart the UID we are about to revoke.
        assertTrue(bound)
        context.unbindService(connection)
        bound = false
    }

    fun removeOwnedActivityAndSaf() {
        assertTrue(sessionBegun)
        request("saf-cleanup")
        await {
            val actual = request("snapshot")
            actual.containsKey("activityActive") && !actual.getBoolean("activityActive") &&
                actual.getBoolean("saf.persistedReleased") &&
                !request("saf-permission").getBoolean("saf.nativeReadGrant")
        }
        assertTrue(request("saf-denied").getBoolean("saf.denied"))
    }

    fun await(condition: () -> Boolean) {
        val deadline = SystemClock.elapsedRealtime() + 20000
        while (SystemClock.elapsedRealtime() < deadline) {
            if (condition()) return
            Thread.sleep(50)
        }
        fail("Owned storage condition was not observed")
    }

    override fun close() {
        var failure: Throwable? = null
        fun attempt(action: () -> Unit) {
            try { action() }
            catch (current: Throwable) {
                val prior = failure
                if (prior == null) failure = current else prior.addSuppressed(current)
            }
        }
        attempt { if (endpoint != null && sessionBegun) removeOwnedActivityAndSaf() }
        attempt { if (endpoint != null) { request("close"); sessionBegun = false } }
        attempt { binder?.let { if (it.isBinderAlive) assertTrue(it.unlinkToDeath(deathRecipient, 0)) } }
        attempt { if (bound) { context.unbindService(connection); bound = false } }
        attempt { endpoint = null; thread.quitSafely(); thread.join(10000); assertFalse(thread.isAlive) }
        failure?.let { throw it }
    }
}
