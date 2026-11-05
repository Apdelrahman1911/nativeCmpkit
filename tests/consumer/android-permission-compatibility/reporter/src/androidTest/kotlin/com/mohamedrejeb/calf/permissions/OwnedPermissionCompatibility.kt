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
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import kotlin.test.*

/** One selected fresh helper and one binding. Process/Binder/Activity replacement fails. */
internal class OwnedPermissionCompatibility(val role: String) : AutoCloseable {
    private val selected = PermissionCompatibilityProfiles.selected()
    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    val packageName = PermissionCompatibilityProfiles.BASE + "." + role
    private val component = ComponentName(packageName, PermissionCompatibilityProfiles.BASE + ".PermissionCompatibilityService")
    private val owner = context.packageManager.getApplicationInfo(packageName, 0).also {
        assertTrue(role in selected.second.roles)
        assertTrue(it.uid >= 10000 && it.uid != Process.myUid())
        assertTrue(it.flags and ApplicationInfo.FLAG_DEBUGGABLE != 0)
        assertEquals(selected.second.target, it.targetSdkVersion)
        assertEquals(listOf(packageName), context.packageManager.getPackagesForUid(it.uid)?.toList())
        assertEquals(PackageManager.SIGNATURE_MATCH, context.packageManager.checkSignatures(context.packageName, packageName))
        assertEquals(PackageManager.PERMISSION_GRANTED, context.checkSelfPermission(packageName + ".CONTROL_COMPATIBILITY"))
    }
    private val thread = HandlerThread("owned-permission-compatibility-reporter-$role").apply { start() }
    private class Reply { val ready = CountDownLatch(1); @Volatile var data: Bundle? = null }
    private val pending = ConcurrentHashMap<String, Reply>()
    @Volatile private var protocolError: String? = null
    @Volatile private var endpoint: Messenger? = null
    private var binder: IBinder? = null
    private var bound = false
    private var closed = false
    private var generation: String? = null
    private var pid: Int? = null
    private var activityGeneration: String? = null
    private val admission = CountDownLatch(1)
    private val death = IBinder.DeathRecipient {
        protocolError = "Owned compatibility Binder died; process death is not a lifecycle pass"
        endpoint = null
        pending.values.forEach { it.ready.countDown() }
    }
    private val responses = Messenger(Handler(thread.looper) { message ->
        val data = Bundle(message.data)
        val reply = pending.remove(data.getString("nonce", ""))
        if (message.sendingUid != owner.uid || reply == null) {
            protocolError = "Foreign, late or duplicate compatibility response"
            pending.values.forEach { it.ready.countDown() }
        } else { reply.data = data; reply.ready.countDown() }
        true
    })
    private val connection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName, service: IBinder) {
            try {
                assertEquals(component, name)
                assertNull(binder, "A second compatibility Binder is not admitted")
                service.linkToDeath(death, 0)
                binder = service
                endpoint = Messenger(service)
            } catch (failure: Throwable) { protocolError = "Invalid compatibility service admission" }
            finally { admission.countDown() }
        }
        override fun onServiceDisconnected(name: ComponentName) {
            protocolError = "Owned compatibility service disconnected"
            endpoint = null
            admission.countDown()
            pending.values.forEach { it.ready.countDown() }
        }
        override fun onBindingDied(name: ComponentName) = onServiceDisconnected(name)
        override fun onNullBinding(name: ComponentName) {
            protocolError = "Null compatibility service binding"
            admission.countDown()
        }
    }

    fun connect(): Bundle {
        check(!bound && !closed)
        bound = context.bindService(Intent().setComponent(component), connection, Context.BIND_AUTO_CREATE)
        assertTrue(bound)
        assertTrue(admission.await(15, TimeUnit.SECONDS), "Fresh compatibility service admission timed out")
        val native = request("observe")
        assertFalse(native.getBoolean("activityActive"))
        assertTrue(native.getLong("firstInstallTime") > 0)
        assertEquals(native.getLong("firstInstallTime"), native.getLong("lastUpdateTime"))
        val declared = assertNotNull(native.getStringArray("declaredPermissions")).toList()
        val dynamic = packageName + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
        assertEquals(declared.size, declared.toSet().size)
        assertEquals(PermissionCompatibilityProfiles.declarations.getValue(role), declared.toSet() - dynamic)
        return native
    }

    fun foreground(): Bundle {
        check(bound && !closed)
        context.startActivity(Intent().setComponent(ComponentName(packageName,
            PermissionCompatibilityProfiles.BASE + ".PermissionCompatibilityActivity")).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        return await { it.getBoolean("activityActive") && it.getBoolean("mounted") && it.getBoolean("resumed") && it.getBoolean("focused") }
    }

    fun request(operation: String): Bundle = requestBefore(operation, SystemClock.elapsedRealtime() + 20000)

    private fun requestBefore(operation: String, deadline: Long): Bundle {
        assertNotEquals(Looper.getMainLooper(), Looper.myLooper())
        assertNull(protocolError, "Native death/replacement cannot pass as same-process resume")
        check(!closed && SystemClock.elapsedRealtime() < deadline)
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
            check(remaining > 0)
            assertTrue(reply.ready.await(remaining, TimeUnit.MILLISECONDS), "Actual compatibility response timed out")
            assertNull(protocolError)
            check(SystemClock.elapsedRealtime() < deadline) { "Late native reply is not a result" }
            return assertNotNull(reply.data).also {
                assertEquals(nonce, it.getString("nonce"))
                assertEquals(owner.uid, assertIs<Int>(it.get("uid")))
                val actualPid = assertIs<Int>(it.get("pid"))
                assertTrue(actualPid > 0 && actualPid != Process.myPid())
                if (pid == null) pid = actualPid else assertEquals(pid, actualPid)
                val actualGeneration = assertNotNull(it.getString("generation"))
                assertTrue(actualGeneration.matches(UUID_PATTERN))
                if (generation == null) generation = actualGeneration else assertEquals(generation, actualGeneration)
                assertNull(it.getString("probeError"))
                assertEquals(selected.first, it.getString("profile"))
                assertEquals(role, it.getString("role"))
                assertEquals(selected.second.api, assertIs<Int>(it.get("apiLevel")))
                assertEquals(selected.second.target, assertIs<Int>(it.get("targetSdk")))
                assertIs<Boolean>(it.get("activityActive"))
                assertIs<Long>(it.get("firstInstallTime")); assertIs<Long>(it.get("lastUpdateTime"))
                if (it.getBoolean("activityActive")) validateActive(it)
            }
        } finally { pending.remove(nonce); message.recycle() }
    }

    private fun validateActive(native: Bundle) {
        val actual = assertNotNull(native.getString("activityGeneration"))
        assertTrue(actual.matches(UUID_PATTERN))
        if (activityGeneration == null) activityGeneration = actual else assertEquals(activityGeneration, actual)
        for (key in listOf("mounted", "resumed", "focused", "locationServicesEnabled")) assertIs<Boolean>(native.get(key))
        for (key in listOf("pauseCount", "resumeCount", "disposalCount", "settingsOpens", "batchCallbacks")) assertTrue(assertIs<Int>(native.get(key)) >= 0)
        for (permission in PermissionCompatibilityProfiles.allPermissions) {
            assertIs<Boolean>(native.get(permission)); assertIs<Boolean>(native.get(permission + ".rationale"))
        }
        val names = when (role) {
            "fine" -> listOf("FineLocation")
            "coarse" -> listOf("CoarseLocation")
            "pair" -> listOf("FineLocation", "CoarseLocation")
            "batch", "omitted" -> listOf("FineLocation", "CoarseLocation", "BackgroundLocation")
            "camera" -> listOf("Camera")
            else -> error("Unregistered compatibility role")
        }
        for (name in names) {
            validateState(assertNotNull(native.getBundle(if (native.getBoolean("mounted")) name else "retained.$name")))
            validateState(assertNotNull(native.getBundle("batch.$name")))
        }
        val callbacks = assertIs<Int>(native.get("batchCallbacks"))
        if (callbacks > 0) {
            val result = assertNotNull(native.getBundle("batchResult"))
            assertTrue(result.keySet().all { it in names })
            for (key in result.keySet()) assertIs<Boolean>(result.get(key))
        } else assertFalse(native.containsKey("batchResult"))
        framework(native).forEach { result ->
            val permissions = assertNotNull(result.getStringArray("permissions"))
            val values = assertNotNull(result.getIntArray("results"))
            assertEquals(permissions.size, values.size)
            assertTrue(permissions.size <= 4 && permissions.toSet().size == permissions.size)
            assertTrue(permissions.all { it in PermissionCompatibilityProfiles.allPermissions })
            assertTrue(values.all { it in setOf(PackageManager.PERMISSION_GRANTED, PackageManager.PERMISSION_DENIED) })
        }
    }

    private fun validateState(state: Bundle) {
        for (key in listOf("granted", "rationale")) assertIs<Boolean>(state.get(key))
        for (key in listOf("availability", "access", "requestability")) assertIs<String>(state.get(key))
        val callbacks = assertIs<Int>(state.get("callbacks"))
        assertTrue(callbacks >= 0)
        if (callbacks > 0) assertIs<Boolean>(state.get("callbackResult")) else assertFalse(state.containsKey("callbackResult"))
    }

    @Suppress("DEPRECATION")
    fun framework(native: Bundle): List<Bundle> = assertNotNull(native.getParcelableArrayList<Bundle>("frameworkResults")).also { assertTrue(it.size <= 8) }

    fun await(predicate: (Bundle) -> Boolean): Bundle {
        val deadline = SystemClock.elapsedRealtime() + 20000
        while (true) {
            val native = requestBefore("observe", deadline)
            if (predicate(native)) return native
            val remaining = deadline - SystemClock.elapsedRealtime()
            check(remaining > 0)
            Thread.sleep(minOf(20L, remaining))
        }
    }

    fun assertSameIdentity(before: Bundle, after: Bundle) {
        assertTrue(before.getBoolean("activityActive") && after.getBoolean("activityActive"))
        for (key in listOf("uid", "pid")) assertEquals(assertIs<Int>(before.get(key)), assertIs<Int>(after.get(key)))
        for (key in listOf("generation", "activityGeneration")) assertEquals(assertNotNull(before.getString(key)), after.getString(key))
    }

    fun returnFromSettings(before: Bundle, ui: PermissionCompatibilitySystemUi): Bundle {
        ui.backToOwned(packageName)
        val after = await { it.getBoolean("resumed") && it.getBoolean("focused") && it.getInt("resumeCount") > before.getInt("resumeCount") }
        assertSameIdentity(before, after)
        assertTrue(after.getInt("pauseCount") > before.getInt("pauseCount"))
        return after
    }

    override fun close() {
        if (closed) return
        var failure: Throwable? = null
        try {
            assertNull(protocolError, "A dead helper cannot have successful native disposal")
            if (bound && endpoint != null && request("observe").getBoolean("activityActive")) {
                request("finish"); await { !it.getBoolean("activityActive") }
            }
        } catch (error: Throwable) { failure = error }
        finally {
            closed = true
            try { binder?.unlinkToDeath(death, 0) }
            catch (error: Throwable) { if (failure == null) failure = error else failure!!.addSuppressed(error) }
            try { if (bound) context.unbindService(connection) }
            catch (error: Throwable) { if (failure == null) failure = error else failure!!.addSuppressed(error) }
            finally {
                bound = false; endpoint = null; binder = null; pending.clear()
                try { thread.quitSafely(); thread.join(5000); assertFalse(thread.isAlive, "Owned compatibility reply thread remains alive") }
                catch (error: Throwable) { if (failure == null) failure = error else failure!!.addSuppressed(error) }
            }
        }
        failure?.let { throw it }
    }

    companion object { private val UUID_PATTERN = Regex("[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}") }
}
