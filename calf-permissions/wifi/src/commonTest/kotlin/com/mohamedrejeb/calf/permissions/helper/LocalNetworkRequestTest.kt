package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.PermissionRequestOutcome
import kotlin.test.*

/** The production request owner is tested; NSNetService itself still requires iOS integration. */
class LocalNetworkRequestTest {
    private class Probe : LocalNetworkProbe {
        lateinit var result: (PermissionRequestOutcome) -> Unit
        var starts = 0
        var stops = 0
        override fun start(onResult: (PermissionRequestOutcome) -> Unit) { starts++; result = onResult }
        override fun stop() { stops++ }
    }
    @Test fun successCleansNativeServiceAndTimerBeforeCallback() {
        val probe = Probe(); var cancelled = 0; var callbacks = 0
        val request = LocalNetworkRequest(probe, { { cancelled++ } }) { _, result ->
            callbacks++; assertEquals(PermissionRequestOutcome.Granted, result)
            assertEquals(1, cancelled); assertEquals(1, probe.stops)
        }
        request.start(); request.start()
        assertEquals(1, probe.starts)
        probe.result(PermissionRequestOutcome.Granted)
        probe.result(PermissionRequestOutcome.Failed)
        assertEquals(1, callbacks)
    }
    @Test fun timeoutIsDistinctAndStillCleans() {
        val probe = Probe(); lateinit var timeout: () -> Unit
        var result: PermissionRequestOutcome? = null
        val request = LocalNetworkRequest(probe, { expired -> timeout = expired; {} }) { _, value -> result = value }
        request.start(); timeout()
        assertEquals(PermissionRequestOutcome.TimedOut, result)
        assertEquals(1, probe.stops)
    }
    @Test fun disposalSuppressesBothLateDelegateAndTimeoutCallbacks() {
        val probe = Probe(); lateinit var timeout: () -> Unit
        val request = LocalNetworkRequest(probe, { expired -> timeout = expired; {} }) { _, _ -> fail("disposed") }
        request.start(); request.cancel(); request.cancel()
        probe.result(PermissionRequestOutcome.Granted); timeout()
        assertEquals(1, probe.stops)
    }
    @Test fun throwingApplicationCallbackCannotSkipCleanup() {
        val probe = Probe(); var cancelled = false
        val request = LocalNetworkRequest(probe, { { cancelled = true } }) { _, _ -> error("callback") }
        request.start()
        assertFailsWith<IllegalStateException> { probe.result(PermissionRequestOutcome.Granted) }
        assertTrue(cancelled); assertEquals(1, probe.stops)
    }
    @Test fun reentrantNewRequestIsNotCleanedByTheOldRequest() {
        val old = Probe(); val next = Probe()
        val second = LocalNetworkRequest(next, { {} }) { _, _ -> }
        val first = LocalNetworkRequest(old, { {} }) { _, _ -> second.start() }
        first.start(); old.result(PermissionRequestOutcome.Granted)
        old.result(PermissionRequestOutcome.Failed)
        assertEquals(1, old.stops); assertEquals(1, next.starts); assertEquals(0, next.stops)
        second.cancel()
    }
}
