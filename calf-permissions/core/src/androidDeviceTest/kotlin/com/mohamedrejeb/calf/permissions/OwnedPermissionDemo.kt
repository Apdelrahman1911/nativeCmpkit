// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.permissions

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.os.Build
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
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import kotlin.test.*

/** The separate consumer owns all runtime requests. The -g-installed reporter only observes. */
internal class OwnedPermissionDemo : AutoCloseable {
    companion object {
        const val PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.permissiondemo"
        const val REPORTER = "com.mohamedrejeb.calf.calfpermissions.calfpermissionscore.test"
        const val PERMISSION = "$PACKAGE.BIND_DEMO"
        val FORBIDDEN = listOf("MANAGE_EXTERNAL_STORAGE", "READ_SMS", "SEND_SMS", "RECEIVE_SMS")
    }
    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private val owner = context.packageManager.getApplicationInfo(PACKAGE, 0).also {
        assertEquals(REPORTER, context.packageName)
        assertEquals("true", InstrumentationRegistry.getArguments().getString("nativecmpkitOwnedPermissionDemo"))
        assertNotEquals(Process.myUid(), it.uid)
        assertTrue(it.flags and ApplicationInfo.FLAG_DEBUGGABLE != 0)
        assertEquals(37, it.targetSdkVersion)
        assertEquals(PackageManager.SIGNATURE_MATCH, context.packageManager.checkSignatures(context.packageName, PACKAGE))
        assertEquals(PackageManager.PERMISSION_GRANTED, context.checkSelfPermission(PERMISSION))
    }
    private val thread = HandlerThread("owned-permission-demo-reporter").apply { start() }
    private class Reply { val ready = CountDownLatch(1); @Volatile var data: Bundle? = null }
    private val pending = ConcurrentHashMap<String, Reply>()
    @Volatile private var protocolError: String? = null
    @Volatile private var endpoint: Messenger? = null
    private var bound = false
    private var binder: IBinder? = null
    private var generation: String? = null
    private var nativePid: Int? = null
    private val death = IBinder.DeathRecipient { endpoint = null; protocolError = "Owned consumer Binder died" }
    private val admission = CountDownLatch(1)
    private val responses = Messenger(Handler(thread.looper) { message ->
        val data = Bundle(message.data)
        val reply = pending.remove(data.getString("nonce", ""))
        if (message.sendingUid != owner.uid || reply == null) protocolError = "Foreign, late or duplicate native response"
        else { reply.data = data; reply.ready.countDown() }
        true
    })
    private val connection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName, service: IBinder) {
            try {
                assertEquals(ComponentName(PACKAGE, "$PACKAGE.PermissionDemoService"), name)
                service.linkToDeath(death, 0)
                binder = service
                endpoint = Messenger(service)
            } catch (failure: Exception) { protocolError = "Invalid actual consumer admission" }
            finally { admission.countDown() }
        }
        override fun onServiceDisconnected(name: ComponentName) {
            endpoint = null
            protocolError = "Owned consumer disconnected"
        }
        override fun onBindingDied(name: ComponentName) = onServiceDisconnected(name)
        override fun onNullBinding(name: ComponentName) {
            protocolError = "Null native consumer binding"
            admission.countDown()
        }
    }

    fun connect() {
        assertFalse(bound)
        bound = context.bindService(Intent().setComponent(ComponentName(PACKAGE, "$PACKAGE.PermissionDemoService")),
            connection, Context.BIND_AUTO_CREATE)
        assertTrue(bound)
        assertTrue(admission.await(15, TimeUnit.SECONDS))
        val native = request("observe")
        assertNotEquals(Process.myPid(), native.getInt("pid"))
        assertEquals(Build.VERSION.SDK_INT, native.getInt("apiLevel"))
        assertEquals(37, native.getInt("targetSdk"))
        assertTrue(native.getLong("firstInstallTime") > 0)
        assertEquals(native.getLong("firstInstallTime"), native.getLong("lastUpdateTime"))
        val declarations = assertNotNull(native.getStringArray("declaredPermissions")).toSet()
        for (permission in FORBIDDEN) assertFalse("android.permission.$permission" in declarations,
            "Forbidden permission android.permission.$permission is declared: $declarations")
        for (permission in listOf("CALL_PHONE", "RECORD_AUDIO", "READ_MEDIA_IMAGES", "READ_MEDIA_VIDEO",
            "READ_MEDIA_VISUAL_USER_SELECTED")) assertContains(declarations, "android.permission.$permission")
    }

    fun foreground() {
        context.startActivity(Intent().setComponent(ComponentName(PACKAGE, "$PACKAGE.PermissionDemoActivity"))
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK))
        await { it.getBoolean("mounted") && it.getBoolean("resumed") && it.getBoolean("focused") }
    }

    fun request(operation: String): Bundle = request(operation, observationDeadline = null)

    // Only the third-request observation opts into the caller's existing absolute deadline.
    // Ordinary Call/picker/teardown operations retain their original 20-second wait.
    fun observeBefore(deadline: Long): Bundle = request("observe", observationDeadline = deadline)

    private fun request(operation: String, observationDeadline: Long?): Bundle {
        assertNotEquals(Looper.getMainLooper(), Looper.myLooper())
        assertNull(protocolError)
        val remote = assertNotNull(endpoint)
        if (observationDeadline != null) {
            check(operation == "observe") { "The bounded absence read must not perform a native operation" }
            check(SystemClock.elapsedRealtime() < observationDeadline) { "The original no-dialog deadline expired before native observation" }
        }
        val nonce = UUID.randomUUID().toString().replace("-", "")
        val reply = Reply()
        check(pending.put(nonce, reply) == null)
        val message = Message.obtain().apply {
            replyTo = responses
            data = Bundle().apply { putString("nonce", nonce); putString("operation", operation) }
        }
        try {
            if (observationDeadline != null) check(SystemClock.elapsedRealtime() < observationDeadline) {
                "The original no-dialog deadline expired before native send"
            }
            remote.send(message)
            val responseReady = if (observationDeadline == null) reply.ready.await(20, TimeUnit.SECONDS)
            else {
                val remaining = observationDeadline - SystemClock.elapsedRealtime()
                check(remaining > 0) { "A late native send cannot certify the no-dialog observation" }
                reply.ready.await(remaining, TimeUnit.MILLISECONDS)
            }
            assertTrue(responseReady, "Actual consumer response timed out")
            if (observationDeadline != null) check(SystemClock.elapsedRealtime() < observationDeadline) {
                "A late native response cannot certify the no-dialog observation"
            }
            assertNull(protocolError)
            return assertNotNull(reply.data).also {
                assertEquals(nonce, it.getString("nonce"))
                assertEquals(owner.uid, it.getInt("uid"))
                val pid = it.getInt("pid")
                assertTrue(pid > 0 && pid != Process.myPid())
                if (nativePid == null) nativePid = pid else assertEquals(nativePid, pid)
                assertNull(it.getString("probeError"), "A native refusal is not a successful test result")
                val actual = assertNotNull(it.getString("generation"))
                assertTrue(actual.matches(Regex("[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}")))
                if (generation == null) generation = actual else assertEquals(generation, actual)
                assertIs<Boolean>(it.get("activityActive"))
                assertEquals(Build.VERSION.SDK_INT, it.getInt("apiLevel"))
                if (it.getBoolean("activityActive")) {
                    assertNotNull(it.getString("activityGeneration"))
                    for (key in listOf("mounted", "resumed", "focused")) assertIs<Boolean>(it.get(key))
                    if (it.getBoolean("mounted")) {
                        // A missing/wrong-typed native read is unknown, never
                        // a false default accepted as denial or no rationale.
                        for (permission in listOf("CALL_PHONE", "RECORD_AUDIO", "READ_MEDIA_IMAGES",
                            "READ_MEDIA_VIDEO", "READ_MEDIA_VISUAL_USER_SELECTED")) {
                            assertIs<Boolean>(it.get("android.permission.$permission"))
                            assertIs<Boolean>(it.get("android.permission.$permission.rationale"))
                        }
                        for (name in listOf("Call", "RecordAudio", "ReadImage", "ReadVideo")) {
                            val state = assertNotNull(it.getBundle(name))
                            for (key in listOf("granted", "rationale")) assertIs<Boolean>(state.get(key))
                            for (key in listOf("availability", "access", "requestability")) assertIs<String>(state.get(key))
                            val count = assertIs<Int>(state.get("callbacks"))
                            assertTrue(count >= 0)
                            if (count > 0) assertIs<Boolean>(state.get("callbackResult"))
                            else assertFalse(state.containsKey("callbackResult"))
                        }
                    }
                }
                if (observationDeadline != null) check(SystemClock.elapsedRealtime() < observationDeadline) {
                    "Late native validation cannot certify the no-dialog observation"
                }
            }
        } finally { pending.remove(nonce); message.recycle() }
    }

    fun await(predicate: (Bundle) -> Boolean): Bundle {
        val deadline = SystemClock.elapsedRealtime() + 20000
        while (true) {
            val native = request("observe")
            if (predicate(native)) return native
            check(SystemClock.elapsedRealtime() < deadline) { "Actual native state did not reach the required value" }
            Thread.sleep(40)
        }
    }

    fun ready() = await { it.getBoolean("resumed") && it.getBoolean("focused") }

    override fun close() {
        try {
            if (bound) {
                assertNull(protocolError)
                assertNotNull(endpoint, "Native teardown cannot infer Activity cleanup from a lost endpoint")
                if (request("observe").getBoolean("activityActive")) request("finish")
                await { !it.getBoolean("activityActive") }
            }
        } finally {
            try {
                if (bound) { context.unbindService(connection); bound = false }
                binder?.takeIf { it.isBinderAlive }?.let { assertTrue(it.unlinkToDeath(death, 0) || !it.isBinderAlive) }
                binder = null
                endpoint = null
            } finally {
                thread.quitSafely()
                thread.join(10000)
                check(!thread.isAlive)
            }
        }
    }
}
