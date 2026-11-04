// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.permissions

import android.Manifest
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

/** One fresh signed native source app; any PID/Binder/Activity replacement is a refusal. */
internal class OwnedPermissionLifecycle : AutoCloseable {
    companion object {
        const val PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.permissionlifecycle"
        const val REPORTER = "com.mohamedrejeb.calf.calfpermissions.calfpermissionscore.test"
        const val PERMISSION = "$PACKAGE.CONTROL_LIFECYCLE"
        val NATIVE_PERMISSIONS = listOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION,
            Manifest.permission.ACCESS_BACKGROUND_LOCATION, Manifest.permission.CAMERA, Manifest.permission.POST_NOTIFICATIONS)
        val FOCUSES = setOf("android-permission-location-api35", "android-permission-lifecycle-grant-api35",
            "android-permission-lifecycle-revoke-api35")
    }
    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private val arguments = InstrumentationRegistry.getArguments()
    private val owner = context.packageManager.getApplicationInfo(PACKAGE, 0).also {
        assertEquals(35, Build.VERSION.SDK_INT)
        assertEquals(REPORTER, context.packageName)
        assertEquals("true", arguments.getString("nativecmpkitOwnedPermissionLifecycle"))
        assertTrue(arguments.getString("nativecmpkitPermissionLifecycleFocus") in FOCUSES)
        assertNotEquals(Process.myUid(), it.uid)
        assertTrue(it.flags and ApplicationInfo.FLAG_DEBUGGABLE != 0)
        assertEquals(37, it.targetSdkVersion)
        assertEquals(PackageManager.SIGNATURE_MATCH, context.packageManager.checkSignatures(context.packageName, PACKAGE))
        assertEquals(PackageManager.PERMISSION_GRANTED, context.checkSelfPermission(PERMISSION))
    }
    private val thread = HandlerThread("owned-permission-lifecycle-reporter").apply { start() }
    private class Reply { val ready = CountDownLatch(1); @Volatile var data: Bundle? = null }
    private val pending = ConcurrentHashMap<String, Reply>()
    @Volatile private var protocolError: String? = null
    @Volatile private var endpoint: Messenger? = null
    private var binder: IBinder? = null
    private var bound = false
    private var generation: String? = null
    private var nativePid: Int? = null
    private var activityGeneration: String? = null
    private val admission = CountDownLatch(1)
    private val death = IBinder.DeathRecipient {
        protocolError = "Owned lifecycle Binder died"
        endpoint = null
        pending.values.forEach { it.ready.countDown() }
    }
    private val responses = Messenger(Handler(thread.looper) { message ->
        val data = Bundle(message.data)
        val reply = pending.remove(data.getString("nonce", ""))
        if (message.sendingUid != owner.uid || reply == null) {
            protocolError = "Foreign, late or duplicate lifecycle response"
            pending.values.forEach { it.ready.countDown() }
        } else { reply.data = data; reply.ready.countDown() }
        true
    })
    private val connection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName, service: IBinder) {
            try {
                assertEquals(ComponentName(PACKAGE, "$PACKAGE.PermissionLifecycleService"), name)
                assertNull(binder, "A replacement lifecycle Binder cannot be admitted")
                service.linkToDeath(death, 0)
                binder = service
                endpoint = Messenger(service)
            } catch (failure: Throwable) { protocolError = "Invalid lifecycle service admission" }
            finally { admission.countDown() }
        }
        override fun onServiceDisconnected(name: ComponentName) {
            endpoint = null
            protocolError = "Owned lifecycle service disconnected"
            admission.countDown()
            pending.values.forEach { it.ready.countDown() }
        }
        override fun onBindingDied(name: ComponentName) = onServiceDisconnected(name)
        override fun onNullBinding(name: ComponentName) {
            protocolError = "Null lifecycle service binding"
            admission.countDown()
        }
    }

    fun requireFocus(focus: String) {
        assertEquals(focus, arguments.getString("nativecmpkitPermissionLifecycleFocus"))
    }

    fun connect() {
        assertFalse(bound)
        bound = context.bindService(Intent().setComponent(ComponentName(PACKAGE, "$PACKAGE.PermissionLifecycleService")),
            connection, Context.BIND_AUTO_CREATE)
        assertTrue(bound)
        assertTrue(admission.await(15, TimeUnit.SECONDS), "Owned lifecycle service admission timed out")
        val initial = request("observe")
        assertFalse(assertIs<Boolean>(initial.get("activityActive")))
        assertTrue(initial.getLong("firstInstallTime") > 0)
        assertEquals(initial.getLong("firstInstallTime"), initial.getLong("lastUpdateTime"))
        val declarations = assertNotNull(initial.getStringArray("declaredPermissions")).toSet()
        assertTrue(declarations.containsAll(NATIVE_PERMISSIONS))
        assertTrue(declarations.all { it in NATIVE_PERMISSIONS || it == "$PACKAGE.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION" })
    }

    fun foreground() {
        context.startActivity(Intent().setComponent(ComponentName(PACKAGE, "$PACKAGE.PermissionLifecycleActivity"))
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        await { it.getBoolean("activityActive") && it.getBoolean("mounted") && it.getBoolean("resumed") && it.getBoolean("focused") }
    }

    fun request(operation: String): Bundle = requestBefore(operation, SystemClock.elapsedRealtime() + 20000)

    private fun requestBefore(operation: String, deadline: Long): Bundle {
        assertNotEquals(Looper.getMainLooper(), Looper.myLooper())
        assertNull(protocolError, "A disconnected native process cannot be treated as a resume")
        check(SystemClock.elapsedRealtime() < deadline) { "Native request deadline expired" }
        val remote = assertNotNull(endpoint)
        val nonce = UUID.randomUUID().toString().replace("-", "")
        val reply = Reply()
        check(pending.put(nonce, reply) == null)
        val message = Message.obtain().apply {
            replyTo = responses
            data = Bundle().apply { putString("nonce", nonce); putString("operation", operation) }
        }
        try {
            remote.send(message)
            val remaining = deadline - SystemClock.elapsedRealtime()
            check(remaining > 0) { "Native send exceeded its absolute deadline" }
            assertTrue(reply.ready.await(remaining, TimeUnit.MILLISECONDS), "Actual lifecycle response timed out")
            assertNull(protocolError, "Binder death is not a no-process-death result")
            check(SystemClock.elapsedRealtime() < deadline) { "Late native response is unverified" }
            return assertNotNull(reply.data).also {
                assertEquals(nonce, it.getString("nonce"))
                assertEquals(owner.uid, assertIs<Int>(it.get("uid")))
                val pid = assertIs<Int>(it.get("pid"))
                assertTrue(pid > 0 && pid != Process.myPid())
                if (nativePid == null) nativePid = pid else assertEquals(nativePid, pid)
                val actual = assertNotNull(it.getString("generation"))
                assertTrue(actual.matches(Regex("[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}")))
                if (generation == null) generation = actual else assertEquals(generation, actual)
                assertNull(it.getString("probeError"), "A native refusal is not a successful result")
                assertEquals(35, assertIs<Int>(it.get("apiLevel")))
                assertEquals(37, assertIs<Int>(it.get("targetSdk")))
                if (assertIs<Boolean>(it.get("activityActive"))) {
                    val activeGeneration = assertNotNull(it.getString("activityGeneration"))
                    assertTrue(activeGeneration.matches(Regex("[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}")))
                    if (activityGeneration == null) activityGeneration = activeGeneration else assertEquals(activityGeneration, activeGeneration)
                    for (key in listOf("mounted", "resumed", "focused")) assertIs<Boolean>(it.get(key))
                    for (key in listOf("pauseCount", "resumeCount", "disposalCount")) assertTrue(assertIs<Int>(it.get(key)) >= 0)
                    for (permission in NATIVE_PERMISSIONS) {
                        assertIs<Boolean>(it.get(permission))
                        assertIs<Boolean>(it.get(permission + ".rationale"))
                    }
                    if (it.getBoolean("mounted")) for (name in listOf("FineLocation", "CoarseLocation", "BackgroundLocation", "Camera", "Notification")) {
                        val state = assertNotNull(it.getBundle(name))
                        for (key in listOf("granted", "rationale")) assertIs<Boolean>(state.get(key))
                        for (key in listOf("availability", "access", "requestability")) assertIs<String>(state.get(key))
                        val count = assertIs<Int>(state.get("callbacks"))
                        assertTrue(count >= 0)
                        if (count > 0) assertIs<Boolean>(state.get("callbackResult")) else assertFalse(state.containsKey("callbackResult"))
                    }
                }
            }
        } finally { pending.remove(nonce); message.recycle() }
    }

    fun await(predicate: (Bundle) -> Boolean): Bundle {
        val deadline = SystemClock.elapsedRealtime() + 20000
        while (true) {
            val native = requestBefore("observe", deadline)
            if (predicate(native)) return native
            val remaining = deadline - SystemClock.elapsedRealtime()
            check(remaining > 0) { "Actual lifecycle state did not meet its bounded condition" }
            Thread.sleep(minOf(20L, remaining))
        }
    }

    fun assertSameIdentity(before: Bundle, after: Bundle) {
        assertTrue(assertIs<Boolean>(before.get("activityActive")))
        assertTrue(assertIs<Boolean>(after.get("activityActive")))
        for (key in listOf("uid", "pid")) assertEquals(assertIs<Int>(before.get(key)), assertIs<Int>(after.get(key)))
        for (key in listOf("generation", "activityGeneration")) assertEquals(assertNotNull(before.getString(key)), after.getString(key))
    }

    fun returnFromSettings(before: Bundle, ui: PermissionLifecycleSystemUi): Bundle {
        ui.backToOwned()
        val after = await { it.getBoolean("resumed") && it.getBoolean("focused") && it.getInt("resumeCount") > before.getInt("resumeCount") }
        assertSameIdentity(before, after)
        assertTrue(after.getInt("pauseCount") > before.getInt("pauseCount"), "A fabricated resume is not a Settings round trip")
        return after
    }

    override fun close() {
        var failure: Throwable? = null
        try {
            assertNull(protocolError, "A lifecycle protocol/death failure cannot pass as clean native disposal")
            if (bound && endpoint != null) {
                request("finish")
                await { !it.getBoolean("activityActive") }
            }
        } catch (error: Throwable) { failure = error }
        finally {
            try { binder?.unlinkToDeath(death, 0) }
            catch (error: Throwable) { if (failure == null) failure = error else failure!!.addSuppressed(error) }
            try { if (bound) context.unbindService(connection) }
            catch (error: Throwable) { if (failure == null) failure = error else failure!!.addSuppressed(error) }
            finally {
                bound = false; endpoint = null; binder = null; pending.clear()
                try { thread.quitSafely(); thread.join(5000); assertFalse(thread.isAlive, "Owned reply thread remains alive") }
                catch (error: Throwable) { if (failure == null) failure = error else failure!!.addSuppressed(error) }
            }
        }
        failure?.let { throw it }
    }
}
