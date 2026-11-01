// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.io

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Build
import android.os.Handler
import android.os.HandlerThread
import android.os.IBinder
import android.os.Looper
import android.os.Message
import android.os.Messenger
import android.os.Process
import android.os.UserHandle
import androidx.test.platform.app.InstrumentationRegistry
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import kotlin.test.*

/** Actual Messenger identities, nonce-bound requests and observed Binder death; no shell process guessing. */
internal class OwnedIoEndpoint private constructor(
    private val component: ComponentName,
    private val processName: String,
    private val remoteOwner: Boolean,
) : AutoCloseable {
    companion object {
        private val context get() = InstrumentationRegistry.getInstrumentation().targetContext
        fun control() = OwnedIoEndpoint(ComponentName(AndroidIoProviderContract.PACKAGE,
            "${AndroidIoProviderContract.PACKAGE}.IoControlService"), AndroidIoProviderContract.PACKAGE, true)
        fun providerWitness() = OwnedIoEndpoint(ComponentName(AndroidIoProviderContract.PACKAGE,
            "${AndroidIoProviderContract.PACKAGE}.IoProviderWitnessService"),
            "${AndroidIoProviderContract.PACKAGE}:nativecmpkit_io_provider", true)
        fun bookmarkClient() = OwnedIoEndpoint(ComponentName(context, IoBookmarkClientService::class.java),
            "${context.packageName}:nativecmpkit_io_client", false)
    }
    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private val owner = context.packageManager.getApplicationInfo(component.packageName, 0).also {
        if (remoteOwner) {
            assertNotEquals(Process.myUid(), it.uid)
            assertTrue(it.flags and ApplicationInfo.FLAG_DEBUGGABLE != 0)
            assertEquals(37, it.targetSdkVersion)
            assertEquals(PackageManager.SIGNATURE_MATCH, context.packageManager.checkSignatures(context.packageName, component.packageName))
            assertEquals(PackageManager.PERMISSION_GRANTED, context.checkSelfPermission(AndroidIoProviderContract.PERMISSION))
        } else assertEquals(Process.myUid(), it.uid)
        val service = context.packageManager.getServiceInfo(component, 0)
        assertEquals(processName, service.processName)
        assertEquals(it.uid, service.applicationInfo.uid)
        assertEquals(remoteOwner, service.exported)
        if (remoteOwner) assertEquals(AndroidIoProviderContract.PERMISSION, service.permission)
    }
    private class Reply { val latch = CountDownLatch(1); @Volatile var data: Bundle? = null }
    private val pending = ConcurrentHashMap<String, Reply>()
    private val connected = CountDownLatch(1)
    private val death = CountDownLatch(1)
    private val thread = HandlerThread("owned-io-native-replies").apply { start() }
    @Volatile private var endpoint: Messenger? = null
    @Volatile private var protocolError: String? = null
    @Volatile private var expectedDeath = false
    @Volatile private var closed = false
    private var bound = false
    private var generation: String? = null
    private var pid: Int? = null
    private var deathBinder: IBinder? = null
    private val deathRecipient = IBinder.DeathRecipient { death.countDown() }
    private val replies = Messenger(Handler(thread.looper) { message ->
        if (closed) return@Handler true
        if (message.sendingUid != owner.uid) protocolError = "Foreign native IO reply UID"
        else {
            val data = Bundle(message.data)
            val entry = pending.remove(data.getString("nonce", ""))
            if (entry == null) protocolError = "Unexpected or duplicate native IO reply"
            else { entry.data = data; entry.latch.countDown() }
        }
        true
    })
    private val connection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName, binder: IBinder) {
            if (closed || expectedDeath) return
            if (name != component || endpoint != null) protocolError = "Foreign or duplicate native IO binding"
            else endpoint = Messenger(binder)
            connected.countDown()
        }
        override fun onServiceDisconnected(name: ComponentName) {
            if (!closed) { endpoint = null; if (!expectedDeath) protocolError = "Unexpected native IO disconnect" }
        }
        override fun onNullBinding(name: ComponentName) { if (!closed) { protocolError = "Null native IO binding"; connected.countDown() } }
        override fun onBindingDied(name: ComponentName) { if (!closed && !expectedDeath) protocolError = "Unexpected native IO binding death" }
    }
    fun connect(): Bundle {
        check(!bound && !closed)
        bound = context.bindService(Intent().setComponent(component), connection, Context.BIND_AUTO_CREATE)
        assertTrue(bound); assertTrue(connected.await(15, TimeUnit.SECONDS)); assertNotNull(endpoint)
        return request("snapshot")
    }
    fun request(operation: String, id: String? = null): Bundle = transaction(operation, id)

    /** Only the own main control endpoint may mutate and exactly restore the fixed provider lease. */
    @Suppress("DEPRECATION")
    fun unavailable(operation: String, leaseToken: String): Bundle {
        check(remoteOwner && component == ComponentName(AndroidIoProviderContract.PACKAGE,
            "${AndroidIoProviderContract.PACKAGE}.IoControlService") && processName == AndroidIoProviderContract.PACKAGE)
        check(operation in setOf("acquire-unavailable", "restore-unavailable"))
        check(leaseToken.matches(Regex("[a-f0-9]{32}")))
        assertEquals(35, Build.VERSION.SDK_INT); assertEquals(UserHandle.getUserHandleForUid(0), Process.myUserHandle())
        val held = operation == "acquire-unavailable"
        return transaction(operation, leaseToken = leaseToken).also { data ->
            for (key in listOf("unavailableComponent", "unavailableAuthority", "unavailableLeaseToken")) {
                assertTrue(data.containsKey(key), "Missing exact unavailable-lease string field")
                assertIs<String>(data.get(key))
            }
            for (key in listOf("unavailableOwnerUid", "unavailableUserId", "unavailableOriginalSetting", "unavailableActualSetting")) {
                assertTrue(data.containsKey(key), "Missing exact unavailable-lease integer field")
                assertIs<Int>(data.get(key))
            }
            for (key in listOf("unavailableAuthorityPresent", "unavailableLeaseHeld")) {
                assertTrue(data.containsKey(key), "Missing exact unavailable-lease boolean field")
                assertIs<Boolean>(data.get(key))
            }
            assertEquals(ComponentName(AndroidIoProviderContract.PACKAGE,
                "${AndroidIoProviderContract.PACKAGE}.OwnedIoDocumentsProvider").flattenToString(), data.getString("unavailableComponent"))
            assertEquals(AndroidIoProviderContract.AUTHORITY, data.getString("unavailableAuthority"))
            assertEquals(owner.uid, data.getInt("unavailableOwnerUid")); assertEquals(0, data.getInt("unavailableUserId"))
            assertEquals(leaseToken, data.getString("unavailableLeaseToken"))
            assertEquals(PackageManager.COMPONENT_ENABLED_STATE_DEFAULT, data.getInt("unavailableOriginalSetting"))
            assertEquals(if (held) PackageManager.COMPONENT_ENABLED_STATE_DISABLED else PackageManager.COMPONENT_ENABLED_STATE_DEFAULT,
                data.getInt("unavailableActualSetting"))
            assertEquals(!held, data.getBoolean("unavailableAuthorityPresent")); assertEquals(held, data.getBoolean("unavailableLeaseHeld"))
        }
    }

    private fun transaction(operation: String, id: String? = null, leaseToken: String? = null): Bundle {
        assertNotEquals(Looper.getMainLooper(), Looper.myLooper(), "Never block the actual Activity grant callback")
        assertNull(protocolError); check(!closed)
        val remote = assertNotNull(endpoint)
        val nonce = UUID.randomUUID().toString().replace("-", "")
        val reply = Reply(); check(pending.put(nonce, reply) == null)
        val message = Message.obtain().apply {
            replyTo = replies
            data = Bundle().apply {
                putString("nonce", nonce); putString("operation", operation)
                if (id != null) putString("id", id)
                if (leaseToken != null) putString("leaseToken", leaseToken)
            }
        }
        try {
            remote.send(message)
            assertTrue(reply.latch.await(20, TimeUnit.SECONDS), "Native IO reply timed out")
            assertNull(protocolError)
            return assertNotNull(reply.data).also {
                for (key in listOf("uid", "pid", "process", "generation")) assertTrue(it.containsKey(key), "Missing native identity field")
                assertEquals(nonce, it.getString("nonce")); assertEquals(owner.uid, it.getInt("uid"))
                assertTrue(it.getInt("pid") > 0)
                assertNotEquals(Process.myPid(), it.getInt("pid")); assertEquals(processName, it.getString("process"))
                assertNull(it.getString("protocolError"))
                val observed = assertNotNull(it.getString("generation"))
                assertTrue(observed.matches(Regex("[a-f0-9-]{36}")))
                if (generation == null) { generation = observed; pid = it.getInt("pid") }
                else { assertEquals(generation, observed); assertEquals(pid, it.getInt("pid")) }
            }
        } finally { pending.remove(nonce); message.recycle() }
    }
    fun dieAndObserveBinderDeath(): Bundle {
        check(component.className.endsWith("IoProviderWitnessService") || component.className.endsWith("IoBookmarkClientService"))
        val binder = assertNotNull(endpoint).binder
        binder.linkToDeath(deathRecipient, 0); deathBinder = binder; expectedDeath = true
        val receipt = request("die")
        assertTrue(death.await(15, TimeUnit.SECONDS), "The acknowledged owned process must actually die")
        assertFalse(binder.isBinderAlive, "A simulated disconnect is not process death")
        close()
        return receipt
    }
    override fun close() {
        if (closed) return
        closed = true; endpoint = null
        try {
            deathBinder?.takeIf { it.isBinderAlive }?.unlinkToDeath(deathRecipient, 0)
            if (bound) { bound = false; context.unbindService(connection) }
        } finally {
            thread.quitSafely(); thread.join(10_000)
            check(!thread.isAlive); check(pending.isEmpty())
        }
    }
}
