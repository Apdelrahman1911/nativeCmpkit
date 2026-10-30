// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.camerapicker

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
import androidx.test.platform.app.InstrumentationRegistry
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import kotlin.test.*

/** Actual separate-UID camera receiver; observes native writes, not real camera hardware or chooser UX. */
internal class OwnedCameraReceiver : AutoCloseable {
    companion object {
        const val PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.camerareceiver"
        const val PERMISSION = "$PACKAGE.BIND_RECEIVER"
    }
    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private val owner = context.packageManager.getApplicationInfo(PACKAGE, 0).also {
        assertNotEquals(Process.myUid(), it.uid)
        assertTrue(it.flags and ApplicationInfo.FLAG_DEBUGGABLE != 0)
        assertEquals(37, it.targetSdkVersion)
        assertEquals(PackageManager.SIGNATURE_MATCH, context.packageManager.checkSignatures(context.packageName, PACKAGE))
        assertEquals(PackageManager.PERMISSION_GRANTED, context.checkSelfPermission(PERMISSION))
    }
    val recipientUid: Int get() = owner.uid
    private class Reply { val latch = CountDownLatch(1); @Volatile var data: Bundle? = null }
    private val pending = ConcurrentHashMap<String, Reply>()
    @Volatile private var protocolError: String? = null
    @Volatile private var endpoint: Messenger? = null
    private val connected = CountDownLatch(1)
    private val thread = HandlerThread("owned-camera-receiver-reporter").apply { start() }
    private val replies = Messenger(Handler(thread.looper) { message ->
        if (closed) return@Handler true
        if (message.sendingUid != owner.uid) {
            protocolError = "Foreign native recipient UID"
            return@Handler true
        }
        val data = Bundle(message.data)
        val entry = pending.remove(data.getString("nonce", ""))
        if (entry == null) protocolError = "Unexpected or duplicate native recipient response"
        else { entry.data = data; entry.latch.countDown() }
        true
    })
    private val connection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName, binder: IBinder) {
            if (closed) return
            if (name != ComponentName(PACKAGE, "$PACKAGE.CameraReceiverService")) protocolError = "Foreign component"
            else endpoint = Messenger(binder)
            connected.countDown()
        }
        override fun onServiceDisconnected(name: ComponentName) { if (!closed) endpoint = null }
        override fun onNullBinding(name: ComponentName) { if (!closed) { protocolError = "Null native binding"; connected.countDown() } }
        override fun onBindingDied(name: ComponentName) { if (!closed) { endpoint = null; protocolError = "Native binding died" } }
    }
    private var bound = false
    @Volatile private var closed = false

    fun connect() {
        check(!bound && !closed)
        bound = context.bindService(Intent().setComponent(ComponentName(PACKAGE, "$PACKAGE.CameraReceiverService")),
            connection, Context.BIND_AUTO_CREATE)
        assertTrue(bound); assertTrue(connected.await(15, TimeUnit.SECONDS)); assertNotNull(endpoint)
        request("snapshot")
    }

    fun request(operation: String): Bundle {
        assertNotEquals(Looper.getMainLooper(), Looper.myLooper(), "Never block the native grant callback Looper")
        assertNull(protocolError); check(!closed)
        val remote = assertNotNull(endpoint)
        val nonce = UUID.randomUUID().toString().replace("-", "")
        val reply = Reply(); check(pending.put(nonce, reply) == null)
        val message = Message.obtain().apply {
            replyTo = replies; data = Bundle().apply { putString("nonce", nonce); putString("operation", operation) }
        }
        try {
            remote.send(message)
            assertTrue(reply.latch.await(20, TimeUnit.SECONDS), "Actual native recipient reply timed out")
            assertNull(protocolError)
            return assertNotNull(reply.data).also {
                assertEquals(nonce, it.getString("nonce")); assertEquals(owner.uid, it.getInt("uid"))
                assertNotEquals(Process.myPid(), it.getInt("pid"))
                assertNull(it.getString("protocolError"))
                assertTrue(it.getString("generation", "").matches(Regex("[a-f0-9-]{36}")))
            }
        } finally { pending.remove(nonce); message.recycle() }
    }

    fun received(packet: String): Bundle {
        var snapshot = request("snapshot")
        val started = System.nanoTime()
        while (snapshot.getString("packet") != packet) {
            check(System.nanoTime() - started < 20_000_000_000L) { "Native recipient did not receive the actual intent" }
            Thread.sleep(20); snapshot = request("snapshot")
        }
        assertTrue(snapshot.getBoolean("received")); assertEquals(context.packageName, snapshot.getString("caller"))
        return snapshot
    }

    override fun close() {
        if (closed) return
        try { if (endpoint != null) request("clear") }
        finally {
            closed = true; endpoint = null
            try { if (bound) { bound = false; context.unbindService(connection) } }
            finally { thread.quitSafely(); thread.join(10_000); check(!thread.isAlive); check(pending.isEmpty()) }
        }
    }
}
