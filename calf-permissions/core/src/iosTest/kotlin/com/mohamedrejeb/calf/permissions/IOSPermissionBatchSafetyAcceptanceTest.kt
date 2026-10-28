@file:OptIn(ExperimentalPermissionsApi::class, kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.permissions

import androidx.compose.runtime.*
import androidx.compose.runtime.snapshots.Snapshot
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.LifecycleRegistry
import androidx.lifecycle.compose.LocalLifecycleOwner
import kotlinx.coroutines.*
import platform.Foundation.*
import platform.Foundation.dateWithTimeIntervalSinceNow
import platform.Foundation.runUntilDate
import kotlin.test.*

/** Real public iOS/Compose/Main run-loop ownership. No helper, dispatcher, privacy UI or heap stand-in. */
class IOSPermissionBatchSafetyAcceptanceTest {
    @Test fun emptyCallbackFailurePreservesRecompositionLaterRequestsAndDisposal() {
        val failure = IllegalStateException("Deliberate empty iOS batch application callback failure")
        val host = Host(failure)
        val permission = Permission("ios-batch-failure-next")
        var requested by mutableStateOf(emptyList<Permission>())
        var version by mutableStateOf(0)
        lateinit var batch: MultiplePermissionsState
        val results = mutableListOf<Pair<Int, Map<Permission, Boolean>>>()
        try {
            host.setContent {
                val current = version
                batch = rememberMultiplePermissionsState(requested) {
                    assertTrue(NSThread.isMainThread)
                    results += current to it
                    if (current == 0) throw failure
                    if (current == 2) host.dispose()
                }
            }
            val original = batch
            batch.launchMultiplePermissionRequest()
            host.await("one empty result and surfaced application error") { results.size == 1 && host.errors.size == 1 }
            assertSame(failure, host.errors.single())
            assertEquals(listOf(0 to emptyMap()), results)

            version = 1
            host.recompose() // A cancelled composition scope would prevent this real commit.
            assertSame(original, batch)
            batch.launchMultiplePermissionRequest()
            host.await("same empty owner recovers with the latest callback") { results.size == 2 }
            assertEquals(listOf(0 to emptyMap(), 1 to emptyMap()), results)

            requested = listOf(permission, permission)
            host.recompose()
            assertNotSame(original, batch)
            assertEquals(listOf(permission), batch.permissions.map { it.permission })
            original.launchMultiplePermissionRequest()
            assertEquals(2, results.size, "The replaced empty owner cannot emit another callback")
            batch.launchMultiplePermissionRequest()
            host.await("one complete truthful unsupported map after replacement") { results.size == 3 }
            assertEquals(1 to mapOf(permission to false), results[2])
            assertEquals(PermissionAvailability.Unsupported, batch.permissions.single().details.availability)
            batch.permissions.single().launchPermissionRequest()
            host.await("individual child still uses the current group callback") { results.size == 4 }
            assertEquals(1 to mapOf(permission to false), results[3])

            version = 2
            host.recompose()
            val last = batch
            last.launchMultiplePermissionRequest()
            host.await("callback can dispose the real composition and its owned recomposer") {
                results.size == 5 && host.workCompleted
            }
            assertEquals(2 to mapOf(permission to false), results[4])
            assertEquals(0, host.owner.registry.observerCount)
            last.launchMultiplePermissionRequest()
            last.permissions.single().launchPermissionRequest()
            original.launchMultiplePermissionRequest()
            assertEquals(5, results.size)
            assertEquals(listOf(failure), host.errors)
        } finally { host.close() }
    }

    private class Owner : LifecycleOwner {
        val registry = LifecycleRegistry(this).apply { currentState = Lifecycle.State.RESUMED }
        override val lifecycle: Lifecycle get() = registry
    }

    private class Host(private val allowedFailure: Throwable) {
        val owner = Owner()
        val errors = mutableListOf<Throwable>()
        private val clock = BroadcastFrameClock()
        private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate + clock +
            CoroutineExceptionHandler { _, error -> errors += error })
        private val recomposer = Recomposer(scope.coroutineContext)
        private val composition = Composition(NoNodes(), recomposer)
        private val work = scope.launch { recomposer.runRecomposeAndApplyChanges() }
        val workCompleted: Boolean get() = work.isCompleted
        private var generation by mutableStateOf(0)
        private var committed = -1
        private var frame = 0L
        private var disposed = false
        init { assertTrue(NSThread.isMainThread) }
        fun setContent(content: @Composable () -> Unit) {
            composition.setContent {
                val current = generation
                CompositionLocalProvider(LocalLifecycleOwner provides owner, content = content)
                SideEffect { committed = current }
            }
            await("initial actual composition") { committed == generation && !recomposer.hasPendingWork }
        }
        fun recompose() {
            generation++
            Snapshot.sendApplyNotifications()
            await("owner-preserving recomposition") { committed == generation && !recomposer.hasPendingWork }
        }
        fun await(phase: String, predicate: () -> Boolean) {
            val deadline = NSProcessInfo.processInfo.systemUptime + 10.0
            do {
                Snapshot.sendApplyNotifications()
                if (clock.hasAwaiters) clock.sendFrame(++frame)
                NSRunLoop.mainRunLoop.runUntilDate(NSDate.dateWithTimeIntervalSinceNow(0.002))
                errors.firstOrNull { it !== allowedFailure }?.let { throw it }
                if (predicate()) return
            } while (NSProcessInfo.processInfo.systemUptime < deadline)
            error("Timed out awaiting $phase")
        }
        fun dispose() {
            if (disposed) return
            disposed = true
            try { composition.dispose() } finally {
                owner.registry.currentState = Lifecycle.State.DESTROYED
                recomposer.close()
                scope.cancel()
            }
        }
        fun close() {
            dispose()
            await("owned recomposer cancellation") { work.isCompleted }
            assertEquals(0, owner.registry.observerCount)
        }
    }

    private class NoNodes : AbstractApplier<Unit>(Unit) {
        override fun insertBottomUp(index: Int, instance: Unit) = Unit
        override fun insertTopDown(index: Int, instance: Unit) = Unit
        override fun move(from: Int, to: Int, count: Int) = Unit
        override fun remove(index: Int, count: Int) = Unit
        override fun onClear() = Unit
    }
}
