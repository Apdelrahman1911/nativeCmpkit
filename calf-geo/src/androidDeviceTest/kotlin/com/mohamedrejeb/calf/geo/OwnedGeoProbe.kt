// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.geo

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

/** Actual separate-UID native library consumer; its runtime revocation cannot kill this reporter. */
internal class OwnedGeoProbe : AutoCloseable {
    companion object {
        const val PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.geoprobe"
        const val PERMISSION = "$PACKAGE.BIND_PROBE"
    }
    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private val owner = context.packageManager.getApplicationInfo(PACKAGE, 0).also {
        assertNotEquals(Process.myUid(), it.uid)
        assertTrue(it.flags and ApplicationInfo.FLAG_DEBUGGABLE != 0)
        assertEquals(37, it.targetSdkVersion)
        assertEquals(PackageManager.SIGNATURE_MATCH, context.packageManager.checkSignatures(context.packageName, PACKAGE))
        assertEquals(PackageManager.PERMISSION_GRANTED, context.checkSelfPermission(PERMISSION))
    }
    private val thread = HandlerThread("owned-geo-probe-reporter").apply { start() }
    private class Reply { val latch = CountDownLatch(1); @Volatile var data: Bundle? = null }
    private val pending = ConcurrentHashMap<String, Reply>()
    @Volatile private var protocolError: String? = null
    @Volatile private var endpoint: Messenger? = null
    private var bound = false
    private var connected = CountDownLatch(1)
    private var death = CountDownLatch(1)
    @Volatile private var binder: IBinder? = null
    private var recipient: IBinder.DeathRecipient? = null
    @Volatile private var connection: ServiceConnection? = null
    private val responses = Messenger(Handler(thread.looper) { message ->
        val data = Bundle(message.data)
        val entry = pending.remove(data.getString("nonce", ""))
        if (entry == null) protocolError = "Unexpected/duplicate owned probe response"
        else { entry.data = data; entry.latch.countDown() }
        true
    })
    fun connect() {
        check(!bound)
        connected = CountDownLatch(1); death = CountDownLatch(1)
        val admission = connected
        val observedDeath = death
        val current = object : ServiceConnection {
            override fun onServiceConnected(name: ComponentName, service: IBinder) {
                if (connection !== this) return
                try {
                    if (name != ComponentName(PACKAGE, "$PACKAGE.GeoProbeService")) {
                        protocolError = "Unexpected bound component"
                    } else {
                        val lease = this
                        val dying = IBinder.DeathRecipient {
                            observedDeath.countDown()
                            if (connection === lease && binder === service) endpoint = null
                        }
                        service.linkToDeath(dying, 0)
                        binder = service; recipient = dying; endpoint = Messenger(service)
                    }
                } catch (failure: android.os.RemoteException) { protocolError = "Owned binding died before admission" }
                finally { admission.countDown() }
            }
            override fun onServiceDisconnected(name: ComponentName) {
                if (connection === this) { endpoint = null; observedDeath.countDown() }
            }
            override fun onBindingDied(name: ComponentName) {
                if (connection === this) { endpoint = null; observedDeath.countDown() }
            }
            override fun onNullBinding(name: ComponentName) {
                if (connection === this) { protocolError = "Null owned binding"; admission.countDown() }
            }
        }
        connection = current
        bound = context.bindService(Intent().setComponent(ComponentName(PACKAGE, "$PACKAGE.GeoProbeService")),
            current, Context.BIND_AUTO_CREATE)
        assertTrue(bound, "Exact signature-protected probe binding must succeed")
        assertTrue(connected.await(15, TimeUnit.SECONDS), "Actual probe did not bind")
        assertNotNull(endpoint)
        val actual = request("snapshot")
        assertEquals(owner.uid, actual.getInt("uid"))
        assertNotEquals(Process.myPid(), actual.getInt("pid"))
    }

    fun foreground() {
        context.startActivity(Intent().setComponent(ComponentName(PACKAGE, "$PACKAGE.GeoProbeActivity"))
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK))
        waitFor { request("snapshot").getBoolean("foreground") }
    }

    fun request(operation: String): Bundle {
        assertNotEquals(Looper.getMainLooper(), Looper.myLooper(), "Never block the native callback Looper")
        assertNull(protocolError)
        val remote = assertNotNull(endpoint)
        val nonce = UUID.randomUUID().toString().replace("-", "")
        val reply = Reply(); check(pending.put(nonce, reply) == null)
        val message = Message.obtain().apply {
            replyTo = responses
            data = Bundle().apply { putString("nonce", nonce); putString("operation", operation) }
        }
        try {
            remote.send(message)
            assertTrue(reply.latch.await(20, TimeUnit.SECONDS), "Actual owned probe reply timed out")
            assertNull(protocolError)
            return assertNotNull(reply.data).also {
                assertEquals(nonce, it.getString("nonce")); assertEquals(owner.uid, it.getInt("uid"))
                assertNull(it.getString("probeError"), "Native probe failure is not success")
                assertTrue(it.getString("generation", "").matches(Regex("[a-f0-9-]{36}")))
            }
        } finally { pending.remove(nonce); message.recycle() }
    }

    fun awaitDeath() { assertTrue(death.await(15, TimeUnit.SECONDS), "Revocation must be actually observed, not assumed") }
    fun disconnect() {
        val current = connection; val native = binder; val dying = recipient; val wasBound = bound
        connection = null; bound = false; binder = null; recipient = null; endpoint = null
        if (wasBound) context.unbindService(checkNotNull(current))
        if (native != null && dying != null && native.isBinderAlive) {
            val removed = native.unlinkToDeath(dying, 0)
            assertTrue(removed || !native.isBinderAlive, "Missing live owned death observer is not clean removal")
        }
    }

    fun stopped() { waitFor { request("snapshot").getString("phase") == "Stopped" } }

    private fun waitFor(predicate: () -> Boolean) {
        val started = System.nanoTime()
        while (!predicate()) {
            check(System.nanoTime() - started < 20_000_000_000L) { "Actual remote predicate did not finish" }
            Thread.sleep(20)
        }
    }

    override fun close() {
        try { if (endpoint != null) request("close") }
        finally {
            try { disconnect() }
            finally { thread.quitSafely(); thread.join(10_000); check(!thread.isAlive) }
        }
    }
}
