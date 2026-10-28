@file:OptIn(ExperimentalPermissionsApi::class, kotlinx.coroutines.ExperimentalCoroutinesApi::class)

package com.mohamedrejeb.calf.permissions

import androidx.compose.runtime.AbstractApplier
import androidx.compose.runtime.BroadcastFrameClock
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Composition
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Recomposer
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshots.Snapshot
import androidx.compose.ui.platform.LocalInspectionMode
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.TestResult
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlin.test.*

/** Public factory + real platform actuals; the applier only omits unrelated rendered UI. */
internal class UnsupportedPublicFactoryFixture {
    private class NoNodes : AbstractApplier<Unit>(Unit) {
        override fun insertBottomUp(index: Int, instance: Unit) = Unit
        override fun insertTopDown(index: Int, instance: Unit) = Unit
        override fun move(from: Int, to: Int, count: Int) = Unit
        override fun remove(index: Int, count: Int) = Unit
        override fun onClear() = Unit
    }

    private class PublicComposition(val composition: Composition, val clock: BroadcastFrameClock) {
        private var frame = 0L
        fun TestScope.recompose() {
            Snapshot.sendApplyNotifications()
            runCurrent()
            clock.sendFrame(++frame)
            runCurrent()
        }
    }

    private suspend fun TestScope.withPublicComposition(block: suspend PublicComposition.() -> Unit) {
        val clock = BroadcastFrameClock()
        val recomposer = Recomposer(coroutineContext + clock)
        val composition = Composition(NoNodes(), recomposer)
        val work = launch(clock) { recomposer.runRecomposeAndApplyChanges() }
        try {
            PublicComposition(composition, clock).block()
        } finally {
            composition.dispose()
            recomposer.close()
            work.cancelAndJoin()
        }
    }

    private fun namedPermissions() = listOf(
        Permission("Camera"), Permission("Microphone"), Permission("CoarseLocation"),
        Permission("FineLocation"), Permission("Notification"), Permission("RemoteNotification"),
        Permission("Bluetooth"), Permission("Gallery"), Permission("ReadImage"),
        Permission("ReadCalendar"), Permission("WriteCalendar"), Permission("ReadContacts"),
        Permission.ReadSms, Permission.ReceiveSms, Permission.SendSms,
        Permission.ReadStorage, Permission.WriteStorage, Permission.ReadAudio, Permission.Call,
        Permission("CustomNativeCmpKitCapability"),
    )

    private fun assertUnsupported(state: PermissionState, requested: Boolean = false) {
        assertEquals(PermissionStatus.Denied(false), state.status)
        assertEquals(PermissionAvailability.Unsupported, state.details.availability)
        assertEquals(PermissionRequestability.Unsupported, state.details.requestability)
        assertEquals(PermissionAccess.None, state.details.access)
        assertEquals(if (requested) PermissionRequestOutcome.Unsupported else null, state.details.lastRequest)
    }

    /** Explicit false inspection mode prevents a preview helper from replacing the real actual. */
    @Composable private fun realContent(content: @Composable () -> Unit) {
        CompositionLocalProvider(LocalInspectionMode provides false, content = content)
    }

    fun allNamedSingleRequestsCompleteOnceWithoutImplyingAuthorization(): TestResult = runTest {
        withPublicComposition {
            val permissions = namedPermissions()
            val results = mutableListOf<Pair<Permission, Boolean>>()
            var states = emptyList<PermissionState>()
            composition.setContent {
                realContent { states = permissions.map { p -> rememberPermissionState(p) { results += p to it } } }
            }
            runCurrent()
            assertEquals(permissions, states.map { it.permission })
            states.forEachIndexed { index, state ->
                assertUnsupported(state)
                state.launchPermissionRequest()
                assertEquals(index + 1, results.size, "Each public request completes synchronously once")
                assertEquals(state.permission to false, results.last())
                assertUnsupported(state, requested = true)
            }
            runCurrent()
            assertEquals(permissions.map { it to false }, results, "No late/duplicate callbacks")
        }
    }

    fun publicBatchChildAndEmptyRequestsReturnExactUnsupportedMaps(): TestResult = runTest {
        withPublicComposition {
            val a = Permission("Camera")
            val b = Permission("Microphone")
            val results = mutableListOf<Map<Permission, Boolean>>()
            val empty = mutableListOf<Map<Permission, Boolean>>()
            lateinit var state: MultiplePermissionsState
            lateinit var emptyState: MultiplePermissionsState
            composition.setContent { realContent {
                state = rememberMultiplePermissionsState(listOf(a, a, b)) { results += it }
                emptyState = rememberMultiplePermissionsState(emptyList()) { empty += it }
            } }
            runCurrent()
            assertEquals(listOf(a, b), state.permissions.map { it.permission })
            assertFalse(state.allPermissionsGranted)
            assertFalse(state.shouldShowRationale)
            state.permissions.forEach { assertUnsupported(it) }
            state.launchMultiplePermissionRequest()
            assertEquals(listOf(mapOf(a to false, b to false)), results)
            state.permissions.forEach { assertUnsupported(it, requested = true) }
            state.permissions[1].launchPermissionRequest()
            assertEquals(listOf(mapOf(a to false, b to false), mapOf(b to false)), results)
            emptyState.launchMultiplePermissionRequest()
            assertEquals(listOf(emptyMap()), empty)
            assertEquals(emptyList(), emptyState.permissions)
            runCurrent()
            assertEquals(2, results.size)
            assertEquals(1, empty.size)
        }
    }

    fun publicCallbacksFollowRecompositionAndPreserveTheState(): TestResult = runTest {
        withPublicComposition {
            var version by mutableStateOf(0)
            lateinit var single: PermissionState
            lateinit var batch: MultiplePermissionsState
            val singleResults = mutableListOf<Int>()
            val batchResults = mutableListOf<Pair<Int, Map<Permission, Boolean>>>()
            val a = Permission("Camera")
            val b = Permission("Microphone")
            composition.setContent { realContent {
                val current = version
                single = rememberPermissionState(a) { assertFalse(it); singleResults += current }
                batch = rememberMultiplePermissionsState(listOf(a, b)) { batchResults += current to it }
            } }
            runCurrent()
            val originalSingle = single
            val originalBatch = batch
            single.launchPermissionRequest()
            batch.launchMultiplePermissionRequest()
            version = 1
            recompose()
            assertSame(originalSingle, single)
            assertSame(originalBatch, batch)
            single.launchPermissionRequest()
            batch.permissions[0].launchPermissionRequest()
            batch.launchMultiplePermissionRequest()
            assertEquals(listOf(0, 1), singleResults)
            assertEquals(listOf(0 to mapOf(a to false, b to false), 1 to mapOf(a to false),
                1 to mapOf(a to false, b to false)), batchResults)
        }
    }

    fun publicPermissionChangesCannotLeakThePreviousSelection(): TestResult = runTest {
        withPublicComposition {
            val a = Permission("Camera")
            val b = Permission("Microphone")
            var chosen by mutableStateOf(a)
            var list by mutableStateOf(listOf(a, a))
            lateinit var single: PermissionState
            lateinit var batch: MultiplePermissionsState
            val results = mutableListOf<Pair<Permission, Boolean>>()
            val batches = mutableListOf<Map<Permission, Boolean>>()
            composition.setContent { realContent {
                val current = chosen
                single = rememberPermissionState(current) { results += current to it }
                batch = rememberMultiplePermissionsState(list) { batches += it }
            } }
            runCurrent()
            val old = single
            chosen = b
            list = listOf(b, a, b)
            recompose()
            assertNotSame(old, single)
            assertEquals(b, single.permission)
            assertEquals(listOf(b, a), batch.permissions.map { it.permission })
            single.launchPermissionRequest()
            batch.launchMultiplePermissionRequest()
            assertEquals(listOf(b to false), results)
            assertEquals(listOf(mapOf(b to false, a to false)), batches)
            list = emptyList()
            recompose()
            batch.launchMultiplePermissionRequest()
            assertEquals(listOf(mapOf(b to false, a to false), emptyMap()), batches)
        }
    }

    fun throwingAndReentrantCallbacksHaveExactlyOneSynchronousResult(): TestResult = runTest {
        withPublicComposition {
            var mode by mutableStateOf(0)
            lateinit var state: PermissionState
            lateinit var batch: MultiplePermissionsState
            var callbacks = 0
            var batchCallbacks = 0
            composition.setContent { realContent {
                val current = mode
                state = rememberPermissionState(Permission("Camera")) {
                    assertFalse(it)
                    assertUnsupported(state, requested = true)
                    callbacks++
                    if (current == 0) error("Synthetic application callback")
                    if (callbacks == 2) state.launchPermissionRequest()
                }
                batch = rememberMultiplePermissionsState(listOf(Permission("Camera"), Permission("Microphone"))) {
                    assertTrue(it.values.all { granted -> !granted })
                    batchCallbacks++
                    if (current == 0) error("Synthetic batch callback")
                }
            } }
            runCurrent()
            assertFailsWith<IllegalStateException> { state.launchPermissionRequest() }
            assertFailsWith<IllegalStateException> { batch.launchMultiplePermissionRequest() }
            assertEquals(1, callbacks)
            assertEquals(1, batchCallbacks)
            assertUnsupported(state, requested = true)
            mode = 1
            recompose()
            state.launchPermissionRequest()
            batch.launchMultiplePermissionRequest()
            assertEquals(3, callbacks, "One result per explicit outer/reentrant request")
            assertEquals(2, batchCallbacks, "The failed callback does not poison the next launch")
            runCurrent()
            assertEquals(3, callbacks)
            assertEquals(2, batchCallbacks)
        }
    }

    /** Browser wrappers guard real global service properties; desktop uses its actual no-service policy. */
    fun environmentAndLegacyFlagsCannotManufactureAuthorization(
        installServiceGuard: (String) -> (() -> Unit) = { {} },
    ): TestResult = runTest {
        for (mode in listOf("missing", "denied")) {
            val restore = installServiceGuard(mode)
            try {
                withPublicComposition {
                    var states = emptyList<PermissionState>()
                    val results = mutableListOf<Boolean>()
                    composition.setContent { realContent {
                        states = namedPermissions().map { p -> rememberPermissionState(p) { results += it } }
                    } }
                    runCurrent()
                    states.forEachIndexed { index, state ->
                        assertUnsupported(state)
                        // The legacy setter is not an OS enforcement boundary. A request
                        // must never report this synthetic value as a native authorization.
                        state.status = PermissionStatus.Granted
                        state.openAppSettings() // Explicitly unsupported/no portable route.
                        assertEquals(index, results.size, "Opening unsupported settings produces no result")
                        state.launchPermissionRequest()
                        assertUnsupported(state, requested = true)
                    }
                    assertEquals(List(states.size) { false }, results)
                }
            } finally {
                restore()
            }
        }
    }
}
