package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.PermissionRequestOutcome
import kotlin.test.*

/** The production request owner is tested with controlled native delegate/timer adapters. */
class BluetoothRequestTest {
    private class Probe : BluetoothProbe {
        lateinit var changed: () -> Unit
        var starts = 0
        var stops = 0
        override fun start(onChange: () -> Unit) { starts++; changed = onChange }
        override fun stop() { stops++ }
    }
    private class Timers {
        val callbacks = mutableListOf<() -> Unit>()
        var cancelled = 0
        fun schedule(seconds: Double, repeats: Boolean, callback: () -> Unit): () -> Unit {
            assertEquals(if (repeats) 0.5 else 60.0, seconds)
            callbacks += callback
            return { cancelled++ }
        }
    }
    @Test fun slowAuthorizationContinuesPollingAndCleansBeforeCallback() {
        val probe = Probe(); val timers = Timers()
        var authorization = BluetoothAuthorization.NotDetermined; var calls = 0
        val request = BluetoothRequest(probe, { authorization }, timers::schedule) { _, result ->
            calls++; assertEquals(PermissionRequestOutcome.Granted, result)
            assertEquals(1, probe.stops); assertEquals(2, timers.cancelled)
        }
        request.start(); request.start()
        repeat(10) { timers.callbacks[1]() }
        assertEquals(0, calls); assertEquals(1, probe.starts)
        authorization = BluetoothAuthorization.Allowed
        timers.callbacks[1](); probe.changed(); timers.callbacks[0]()
        assertEquals(1, calls)
    }
    @Test fun deadlineIsTimeoutNotUserDenial() {
        val probe = Probe(); val timers = Timers(); var result: PermissionRequestOutcome? = null
        val request = BluetoothRequest(probe, { BluetoothAuthorization.NotDetermined }, timers::schedule) { _, value -> result = value }
        request.start(); timers.callbacks[0]()
        assertEquals(PermissionRequestOutcome.TimedOut, result)
        assertEquals(1, probe.stops); assertEquals(2, timers.cancelled)
    }
    @Test fun disposalDropsAllLateNativeAndTimerDeliveries() {
        val probe = Probe(); val timers = Timers()
        val request = BluetoothRequest(probe, { BluetoothAuthorization.NotDetermined }, timers::schedule) { _, _ -> fail("disposed") }
        request.start(); request.cancel(); request.cancel()
        probe.changed(); timers.callbacks.forEach { it() }
        assertEquals(1, probe.stops); assertEquals(2, timers.cancelled)
    }
    @Test fun deniedAndRestrictedAuthorizationAreTerminalOnce() {
        for (authorization in listOf(BluetoothAuthorization.Denied, BluetoothAuthorization.Restricted)) {
            val probe = Probe(); val timers = Timers(); var calls = 0
            val request = BluetoothRequest(probe, { authorization }, timers::schedule) { _, result ->
                calls++; assertEquals(if (authorization == BluetoothAuthorization.Denied) PermissionRequestOutcome.Denied else PermissionRequestOutcome.Restricted, result)
            }
            request.start(); probe.changed()
            assertEquals(1, calls); assertEquals(1, probe.stops)
        }
    }
    @Test fun callbackExceptionStillReleasesManagerDelegateAndTimers() {
        val probe = Probe(); val timers = Timers()
        var authorization = BluetoothAuthorization.NotDetermined
        val request = BluetoothRequest(probe, { authorization }, timers::schedule) { _, _ -> error("callback") }
        request.start(); authorization = BluetoothAuthorization.Allowed
        assertFailsWith<IllegalStateException> { probe.changed() }
        assertEquals(1, probe.stops); assertEquals(2, timers.cancelled)
    }
}
