@file:OptIn(ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions

import kotlin.test.*

class PermissionRequestTest {
    @Test fun gateCoalescesAndCompletesEachCallerExactlyOnce() {
        val gate = PermissionRequestGate<Boolean>()
        val results = mutableListOf<Boolean>()
        val token = gate.begin { results += it }!!
        assertNull(gate.begin { results += it })
        gate.complete(token, true)
        gate.complete(token, false)
        assertEquals(listOf(true, true), results)
        assertFalse(gate.isActive)
    }

    @Test fun completionClearsBeforeReentrantLaunch() {
        val gate = PermissionRequestGate<Int>()
        val results = mutableListOf<Int>()
        var next: Long? = null
        val token = gate.begin { results += it; next = gate.begin { results += it } }!!
        gate.complete(token, 1)
        gate.complete(token, 99)
        gate.complete(next!!, 2)
        assertEquals(listOf(1, 2), results)
    }

    @Test fun throwingCallbackDoesNotLoseOtherWaitersOrOwnership() {
        val gate = PermissionRequestGate<Int>()
        var delivered = false
        val token = gate.begin { error("application callback") }!!
        gate.begin { delivered = true }
        assertFailsWith<IllegalStateException> { gate.complete(token, 1) }
        assertTrue(delivered)
        assertFalse(gate.isActive)
    }

    @Test fun disposalSuppressesLateNativeCompletion() {
        val gate = PermissionRequestGate<Boolean>()
        val token = gate.begin { fail("disposed owner callback") }!!
        gate.dispose()
        gate.complete(token, true)
        assertNull(gate.begin { fail("new request after disposal") })
    }

    @Test fun disposalDuringDeliverySuppressesRemainingOwnedCallbacks() {
        val gate = PermissionRequestGate<Boolean>()
        val token = gate.begin { gate.dispose() }!!
        gate.begin { fail("owner was disposed by the first callback") }
        gate.complete(token, true)
    }

    @Test fun emptyBatchCompletesWithEmptyMap() {
        var result: Map<Permission, Boolean>? = null
        PermissionBatchRequest(emptyList()) { _, _ -> fail("native launch") }.launch { result = it }
        assertEquals(emptyMap(), result)
    }

    @Test fun batchSerializesAndReturnsEveryRequestedIdentityOnce() {
        val a = Permission("A"); val b = Permission("B")
        val native = mutableListOf<Pair<Permission, (Boolean) -> Unit>>()
        val results = mutableListOf<Map<Permission, Boolean>>()
        val batch = PermissionBatchRequest(listOf(a, a, b)) { p, cb -> native += p to cb }
        batch.launch { results += it }
        assertEquals(listOf(a), native.map { it.first })
        native[0].second(true)
        assertEquals(listOf(a, b), native.map { it.first })
        assertTrue(results.isEmpty())
        native[0].second(false) // Duplicate old callback cannot finish the next stage.
        native[1].second(false)
        native[1].second(true)
        assertEquals(listOf(mapOf(a to true, b to false)), results)
    }

    @Test fun overlappingBatchSharesNativeWorkButCompletesEachLaunch() {
        val p = Permission("A")
        var native: ((Boolean) -> Unit)? = null
        var launches = 0
        var callbacks = 0
        val batch = PermissionBatchRequest(listOf(p)) { _, cb -> launches++; native = cb }
        batch.launch { callbacks++ }
        batch.launch { callbacks++ }
        native!!(false)
        assertEquals(1, launches)
        assertEquals(2, callbacks)
    }

    @Test fun batchDisposalDoesNotStartNextPrompt() {
        var finish: ((Boolean) -> Unit)? = null
        var calls = 0
        val batch = PermissionBatchRequest(listOf(Permission("A"), Permission("B"))) { _, cb -> calls++; finish = cb }
        batch.launch { fail("disposed batch") }
        batch.dispose()
        finish!!(true)
        assertEquals(1, calls)
    }

    @Test fun synchronousBatchDoesNotGrowTheStack() {
        val permissions = List(10_000) { Permission("p$it") }
        var result: Map<Permission, Boolean>? = null
        PermissionBatchRequest(permissions) { _, cb -> cb(true) }.launch { result = it }
        assertEquals(10_000, result!!.size)
        assertTrue(result!!.values.all { it })
    }

    @Test fun aggregateRefreshesEveryDuplicateAndDetectsRevocation() {
        class State(override val permission: Permission) : MutablePermissionState {
            override var status: PermissionStatus = PermissionStatus.Granted
            var refreshes = 0
            override fun refreshPermissionStatus() { refreshes++; status = PermissionStatus.Denied(true) }
            override fun launchPermissionRequest() = Unit
            override fun openAppSettings() = Unit
        }
        val a = State(Permission("A")); val alias = State(Permission("A"))
        val group = MutableMultiplePermissionsState(listOf(a, alias))
        assertTrue(group.allPermissionsGranted)
        group.updatePermissionsStatus(mapOf(a.permission to false))
        assertEquals(1, a.refreshes)
        assertEquals(1, alias.refreshes)
        assertEquals(2, group.revokedPermissions.size)
        assertTrue(group.shouldShowRationale)
    }

    @Test fun unsupportedRequestCompletesFalseAndRefreshRejectsSyntheticGrant() {
        var calls = 0
        val state = UnsupportedPermissionState(Permission("Camera")) { assertFalse(it); calls++ }
        assertNull(state.details.lastRequest)
        state.status = PermissionStatus.Granted // Legacy mutable property remains available.
        state.launchPermissionRequest()
        state.launchPermissionRequest()
        assertEquals(2, calls)
        assertFalse(state.status.isGranted)
        assertEquals(PermissionAvailability.Unsupported, state.details.availability)
        assertEquals(PermissionRequestability.Unsupported, state.details.requestability)
        assertEquals(PermissionRequestOutcome.Unsupported, state.details.lastRequest)
    }

    @Test fun legacyStatusRemainsTwoCaseAndPermissionNamesRemainIdentities() {
        fun describe(status: PermissionStatus) = when (status) {
            PermissionStatus.Granted -> "yes"
            is PermissionStatus.Denied -> "no"
        }
        assertEquals("yes", describe(PermissionStatus.Granted))
        assertEquals("no", describe(PermissionStatus.Denied(false)))
        assertEquals(Permission("Camera"), Permission("Camera"))
        assertNotEquals(Permission("camera"), Permission("Camera"))
    }
}
