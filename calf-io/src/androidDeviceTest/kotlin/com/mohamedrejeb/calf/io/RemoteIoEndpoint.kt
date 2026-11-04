// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.io

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
import android.os.Parcel
import android.os.Process
import androidx.test.platform.app.InstrumentationRegistry
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import kotlin.test.*

/** NEW helper identities only. Existing accepted OwnedIoEndpoint remains byte-identical. */
internal object RemoteIoContract {
    const val PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.ioremotedocuments"
    const val AUTHORITY = "$PACKAGE.documents"
    const val PERMISSION = "$PACKAGE.CONTROL_REMOTE_IO"
    const val PROVIDER_PROCESS = "$PACKAGE:nativecmpkit_io_remote_provider"
    const val PAYLOAD_BYTES = 4097
    const val HELD_BYTES = 131073
    fun nonce(): String = UUID.randomUUID().toString().replace("-", "")
    fun folder(session: String) = "remote-folder-${checked(session)}"
    fun folderName(session: String) = "NativeCmpKitIo55-${checked(session)}"
    fun root(session: String) = "remote-root-${checked(session)}"
    fun home(session: String) = "remote-home-${checked(session)}"
    fun payload(session: String) = "remote-payload-${checked(session)}"
    fun held(session: String) = "remote-held-${checked(session)}"
    fun checked(value: String): String = value.also { check(it.matches(Regex("[a-f0-9]{32}"))) }
}

/** UID/signature/component/process/generation-bound native Messenger witnesses, not HTTP PID headers. */
internal class RemoteIoEndpoint private constructor(private val provider: Boolean) : AutoCloseable {
    companion object {
        fun control() = RemoteIoEndpoint(false)
        fun providerWitness() = RemoteIoEndpoint(true)
    }
    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private val component = ComponentName(RemoteIoContract.PACKAGE, RemoteIoContract.PACKAGE +
        if (provider) ".RemoteIoProviderWitnessService" else ".RemoteIoControlService")
    private val processName = if (provider) RemoteIoContract.PROVIDER_PROCESS else RemoteIoContract.PACKAGE
    private val owner = context.packageManager.getApplicationInfo(component.packageName, 0).also { app ->
        assertNotEquals(Process.myUid(), app.uid)
        assertTrue(app.flags and ApplicationInfo.FLAG_DEBUGGABLE != 0)
        assertEquals(37, app.targetSdkVersion)
        assertEquals(listOf(RemoteIoContract.PACKAGE), context.packageManager.getPackagesForUid(app.uid)?.toList())
        assertEquals(PackageManager.SIGNATURE_MATCH, context.packageManager.checkSignatures(context.packageName, component.packageName))
        assertEquals(PackageManager.PERMISSION_GRANTED, context.checkSelfPermission(RemoteIoContract.PERMISSION))
        assertEquals(PackageManager.PERMISSION_GRANTED, context.packageManager.checkPermission("android.permission.INTERNET", component.packageName))
        val service = context.packageManager.getServiceInfo(component, 0)
        assertEquals(processName, service.processName); assertEquals(app.uid, service.applicationInfo.uid)
        assertTrue(service.exported); assertEquals(RemoteIoContract.PERMISSION, service.permission)
    }
    private class Reply { val latch = CountDownLatch(1); @Volatile var data: Bundle? = null }
    private val pending = ConcurrentHashMap<String, Reply>()
    private val connected = CountDownLatch(1)
    private val death = CountDownLatch(1)
    private val thread = HandlerThread("nativecmpkit-remote-io-replies") // Starts only after the test assigns this owner.
    private var threadStarted = false
    private var replies: Messenger? = null
    @Volatile private var endpoint: Messenger? = null
    @Volatile private var protocolError: String? = null
    @Volatile private var expectedDeath = false
    @Volatile private var closed = false
    private var bound = false
    private var generation: String? = null
    private var pid: Int? = null
    private var deathBinder: IBinder? = null
    private val deathRecipient = IBinder.DeathRecipient { death.countDown() }
    private val connection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName, binder: IBinder) {
            if (closed || expectedDeath) return
            if (name != component || endpoint != null) protocolError = "Foreign or duplicate controlled-remote binding"
            else endpoint = Messenger(binder)
            connected.countDown()
        }
        override fun onServiceDisconnected(name: ComponentName) {
            if (!closed) { endpoint = null; if (!expectedDeath) protocolError = "Unexpected controlled-remote disconnect" }
        }
        override fun onNullBinding(name: ComponentName) {
            if (!closed) { protocolError = "Null controlled-remote binding"; connected.countDown() }
        }
        override fun onBindingDied(name: ComponentName) {
            if (!closed && !expectedDeath) protocolError = "Unexpected controlled-remote binding death"
        }
    }
    fun connect(): Bundle {
        check(!closed && !bound && !threadStarted)
        threadStarted = true; thread.start()
        replies = Messenger(Handler(thread.looper) { message ->
            if (closed) return@Handler true
            if (message.sendingUid != owner.uid) protocolError = "Foreign controlled-remote reply UID"
            else {
                val data = Bundle(message.data)
                val parcel = Parcel.obtain()
                try { parcel.writeBundle(data); check(parcel.dataSize() <= 524288) { "Native reply body bound exceeded" } }
                catch (_: Throwable) { protocolError = "Native controlled-remote reply body refused" }
                finally { parcel.recycle() }
                val entry = pending.remove(data.getString("nonce", ""))
                if (entry == null) protocolError = "Unexpected or duplicate controlled-remote reply"
                else { entry.data = data; entry.latch.countDown() }
            }
            true
        })
        bound = context.bindService(Intent().setComponent(component), connection, Context.BIND_AUTO_CREATE)
        assertTrue(bound); assertTrue(connected.await(15, TimeUnit.SECONDS)); assertNotNull(endpoint)
        return request("snapshot")
    }
    @Suppress("DEPRECATION")
    fun request(operation: String, session: String? = null, token: String? = null, port: Int? = null): Bundle {
        assertNotEquals(Looper.getMainLooper(), Looper.myLooper(), "Never block a genuine system grant callback")
        check(!closed); assertNull(protocolError)
        check(operation in setOf("snapshot", "prepare", "stats", "stop", "die") || !provider && operation == "revoke")
        if (operation == "snapshot") check(session == null && token == null && port == null)
        else {
            RemoteIoContract.checked(assertNotNull(session))
            if (operation == "prepare") {
                RemoteIoContract.checked(assertNotNull(token))
                if (provider) check(assertNotNull(port) in 1024..65535) else check(port == null)
            } else check(token == null && port == null)
        }
        val nonce = RemoteIoContract.nonce(); val reply = Reply()
        check(pending.put(nonce, reply) == null)
        val message = Message.obtain().apply {
            replyTo = assertNotNull(replies)
            data = Bundle().apply {
                putString("nonce", nonce); putString("operation", operation)
                if (session != null) putString("session", session)
                if (token != null) putString("token", token)
                if (port != null) putInt("port", port)
            }
        }
        try {
            assertNotNull(endpoint).send(message)
            assertTrue(reply.latch.await(20, TimeUnit.SECONDS), "Controlled-remote native reply timed out")
            assertNull(protocolError)
            return assertNotNull(reply.data).also { result ->
                for (key in listOf("uid", "pid")) { assertTrue(result.containsKey(key)); assertIs<Int>(result.get(key)) }
                for (key in listOf("nonce", "process", "generation")) { assertTrue(result.containsKey(key)); assertIs<String>(result.get(key)) }
                assertEquals(nonce, result.getString("nonce")); assertEquals(owner.uid, result.getInt("uid"))
                assertTrue(result.getInt("pid") > 0); assertNotEquals(Process.myPid(), result.getInt("pid"))
                assertEquals(processName, result.getString("process")); assertNull(result.getString("protocolError"))
                val observed = assertNotNull(result.getString("generation")); check(observed.matches(Regex("[a-f0-9-]{36}")))
                if (generation == null) { generation = observed; pid = result.getInt("pid") }
                else { assertEquals(generation, observed); assertEquals(pid, result.getInt("pid")) }
                if (session != null && operation in setOf("prepare", "stats", "stop")) {
                    val native = assertNotNull(result.getBundle(if (provider) "provider" else "backend"))
                    assertEquals(session, native.getString("session"))
                }
            }
        } finally { pending.remove(nonce); message.recycle() }
    }
    fun dieAndObserveBinderDeath(session: String): Bundle {
        val binder = assertNotNull(endpoint).binder
        binder.linkToDeath(deathRecipient, 0); deathBinder = binder; expectedDeath = true
        val receipt = request("die", session)
        assertEquals(pid, receipt.getInt("terminationSelfPid")); assertTrue(receipt.getBoolean("quiescentBeforeDeath"))
        // Remove BIND_AUTO_CREATE before the acknowledged self kill, avoiding a silent helper restart.
        if (bound) { bound = false; context.unbindService(connection) }
        assertTrue(death.await(15, TimeUnit.SECONDS), "The acknowledged own native process must actually die")
        assertFalse(binder.isBinderAlive, "A simulated disconnect is not process death")
        close(); return receipt
    }
    override fun close() {
        if (closed) return
        closed = true; endpoint = null
        var primary: Throwable? = null
        fun attempt(action: () -> Unit) {
            try { action() } catch (failure: Throwable) { if (primary == null) primary = failure else primary!!.addSuppressed(failure) }
        }
        attempt { deathBinder?.takeIf { it.isBinderAlive }?.unlinkToDeath(deathRecipient, 0) }
        attempt { if (bound) { bound = false; context.unbindService(connection) } }
        attempt { if (threadStarted) { thread.quitSafely(); thread.join(10_000); check(!thread.isAlive) } }
        attempt { check(pending.isEmpty()); assertNull(protocolError) }
        primary?.let { throw it }
    }
}
