@file:OptIn(ExperimentalPermissionsApi::class, kotlinx.coroutines.ExperimentalCoroutinesApi::class)

package com.mohamedrejeb.calf.permissions

import androidx.compose.runtime.*
import androidx.compose.runtime.snapshots.Snapshot
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlin.test.*

/** Shared, unchanged Compose-runtime scenarios; Android runs them with a real Robolectric runner. */
internal class RememberPermissionCallbacksFixture {
    private class NoNodes : AbstractApplier<Unit>(Unit) {
        override fun insertBottomUp(index: Int, instance: Unit) = Unit
        override fun insertTopDown(index: Int, instance: Unit) = Unit
        override fun move(from: Int, to: Int, count: Int) = Unit
        override fun remove(index: Int, count: Int) = Unit
        override fun onClear() = Unit
    }

    fun rememberedSingleUsesLatestCallbackWithoutReplacingState() = runTest {
        val clock = BroadcastFrameClock()
        val recomposer = Recomposer(coroutineContext + clock)
        val composition = Composition(NoNodes(), recomposer)
        val work = launch(clock) { recomposer.runRecomposeAndApplyChanges() }
        var version by mutableStateOf(0)
        lateinit var state: MutablePermissionState
        val results = mutableListOf<Int>()
        try {
            composition.setContent {
                val current = version
                state = rememberUnsupportedPermissionState(Permission("Camera")) { results += current }
            }
            runCurrent()
            val original = state
            state.launchPermissionRequest()
            version = 1
            Snapshot.sendApplyNotifications(); runCurrent(); clock.sendFrame(1L); runCurrent()
            assertSame(original, state)
            state.launchPermissionRequest()
            assertEquals(listOf(0, 1), results)
        } finally {
            composition.dispose(); recomposer.close(); work.cancelAndJoin()
        }
    }

    fun rememberedEmptyBatchStillCallsLatestCallbackExactlyOnce() = runTest {
        val clock = BroadcastFrameClock()
        val recomposer = Recomposer(coroutineContext + clock)
        val composition = Composition(NoNodes(), recomposer)
        val work = launch(clock) { recomposer.runRecomposeAndApplyChanges() }
        var version by mutableStateOf(0)
        lateinit var state: MultiplePermissionsState
        val results = mutableListOf<Int>()
        try {
            composition.setContent {
                val current = version
                state = rememberUnsupportedMultiplePermissionsState(emptyList()) {
                    assertTrue(it.isEmpty()); results += current
                }
            }
            runCurrent(); state.launchMultiplePermissionRequest()
            version = 1
            Snapshot.sendApplyNotifications(); runCurrent(); clock.sendFrame(1L); runCurrent()
            state.launchMultiplePermissionRequest()
            assertEquals(listOf(0, 1), results)
        } finally {
            composition.dispose(); recomposer.close(); work.cancelAndJoin()
        }
    }

    fun unsupportedBatchReportsAllDistinctMembersWithOneCallback() = runTest {
        val clock = BroadcastFrameClock()
        val recomposer = Recomposer(coroutineContext + clock)
        val composition = Composition(NoNodes(), recomposer)
        val work = launch(clock) { recomposer.runRecomposeAndApplyChanges() }
        val a = Permission("A"); val b = Permission("B")
        lateinit var state: MultiplePermissionsState
        val results = mutableListOf<Map<Permission, Boolean>>()
        try {
            composition.setContent {
                state = rememberUnsupportedMultiplePermissionsState(listOf(a, a, b)) { results += it }
            }
            runCurrent(); state.launchMultiplePermissionRequest()
            assertEquals(listOf(mapOf(a to false, b to false)), results)
            assertEquals(2, state.permissions.size)
            assertTrue(state.permissions.all { it.details.lastRequest == PermissionRequestOutcome.Unsupported })
        } finally {
            composition.dispose(); recomposer.close(); work.cancelAndJoin()
        }
    }
}
