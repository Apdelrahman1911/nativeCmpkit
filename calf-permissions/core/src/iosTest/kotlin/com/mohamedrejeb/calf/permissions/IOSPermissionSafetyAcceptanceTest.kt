@file:OptIn(ExperimentalPermissionsApi::class, kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.permissions

import androidx.compose.runtime.*
import androidx.compose.runtime.snapshots.Snapshot
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.LifecycleRegistry
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.mohamedrejeb.calf.permissions.helper.*
import kotlinx.coroutines.*
import platform.Foundation.*
import platform.Foundation.dateWithTimeIntervalSinceNow
import platform.Foundation.runUntilDate
import platform.darwin.dispatch_async
import platform.darwin.dispatch_get_global_queue
import platform.darwin.dispatch_get_main_queue
import kotlin.test.*

/** Actual public iOS factories/Compose/Darwin queues/NSLock/lifecycle; no replacement backend/Main dispatcher.
 * Application helpers control pending native-interface completions, not OS privacy dialogs or heap/ABI proof.
 */
class IOSPermissionSafetyAcceptanceTest {
    @Test fun throwingBackgroundCompletionKeepsThePublicOwnerRecoverableAndStatusCurrent() {
        val failure = IllegalStateException("Deliberate iOS application callback failure")
        val host = Host(failure)
        val helper = PendingHelper()
        val permission = Permission("ios-safety-callback-recovery")
        PermissionDelegateRegistry.register(permission) { helper.also { it.factories++ } }
        lateinit var state: PermissionState
        val results = mutableListOf<Boolean>()
        try {
            host.setContent {
                state = rememberPermissionState(permission) {
                    assertTrue(NSThread.isMainThread)
                    results += it
                    if (results.size == 1) {
                        assertTrue(state.status.isGranted)
                        assertEquals(PermissionRequestOutcome.Granted, state.details.lastRequest)
                        throw failure
                    }
                    assertFalse(it)
                    assertFalse(state.status.isGranted)
                    assertEquals(PermissionRequestOutcome.Denied, state.details.lastRequest)
                }
            }
            val owner = state
            state.launchPermissionRequest()
            assertEquals(1, helper.requests.size)
            helper.deliverRequest(0, true, duplicate = true)
            host.await("one surfaced callback error and real background barrier") {
                helper.mainDeliveries == 1 && host.errors.size == 1
            }
            assertSame(failure, host.errors.single())
            assertEquals(listOf(true), results)
            host.recompose()
            assertSame(owner, state)
            assertEquals(1, helper.factories)
            state.launchPermissionRequest()
            assertEquals(2, helper.requests.size, "A throwing callback cannot cancel the remembered request scope")
            helper.deliverRequest(1, false, duplicate = true)
            host.await("the same owner recovers without helper replacement") { helper.mainDeliveries == 2 }
            assertEquals(listOf(true, false), results)
            assertEquals(1, host.errors.size)
            assertTrue(helper.backgroundObserved())
            host.dispose()
            assertEquals(1, helper.disposals)
            assertEquals(0, host.owner.registry.observerCount)
            state.launchPermissionRequest()
            assertEquals(2, helper.requests.size)
        } finally {
            try { host.close() } finally {
                PermissionDelegateRegistry.register(permission) { NotGrantedPermissionHelper() }
                helper.releaseCapturedCallbacks()
            }
        }
    }

    @Test fun racedRealBackgroundQueriesAndPendingDisposalNeverPublishObsoleteState() {
        val host = Host()
        val helper = PendingHelper()
        val permission = Permission("ios-safety-observation-race")
        PermissionDelegateRegistry.register(permission) { helper.also { it.factories++ } }
        lateinit var state: PermissionState
        val results = mutableListOf<Boolean>()
        try {
            host.setContent { state = rememberPermissionState(permission) { results += it } }
            assertFalse(state.status.isGranted)
            helper.delayQueries = true
            val mutable = state as MutablePermissionState
            mutable.refreshPermissionStatus()
            mutable.refreshPermissionStatus()
            assertEquals(2, helper.queries.size)
            helper.deliverQuery(1, true, duplicate = true)
            host.await("newer actual asynchronous observation") { helper.mainDeliveries == 1 }
            assertTrue(state.status.isGranted)
            assertEquals(PermissionAccess.Full, state.details.access)
            helper.deliverQuery(0, false)
            host.await("older actual asynchronous observation was processed") { helper.mainDeliveries == 2 }
            assertTrue(state.status.isGranted, "The older denied query must not overwrite the newer grant")
            assertEquals(PermissionAccess.Full, state.details.access)
            assertTrue(results.isEmpty())

            helper.delayQueries = false
            state.launchPermissionRequest()
            helper.deliverRequest(0, false)
            host.await("fresh request supersedes earlier observations") { helper.mainDeliveries == 3 }
            assertEquals(listOf(false), results)
            assertFalse(state.status.isGranted)
            assertEquals(PermissionRequestOutcome.Denied, state.details.lastRequest)
            helper.delayQueries = true
            mutable.refreshPermissionStatus()
            assertEquals(3, helper.queries.size)
            state.launchPermissionRequest()
            assertEquals(2, helper.requests.size)
            // Both a native-interface request and an asynchronous status query are outstanding.
            val before = state.details
            host.dispose()
            assertEquals(1, helper.disposals)
            assertEquals(0, host.owner.registry.observerCount)
            val nativeQueriesAtDisposal = helper.nativeQueries
            helper.deliverQuery(2, true)
            helper.deliverRequest(1, true, duplicate = true)
            host.await("late query/request processed after disposal") { helper.mainDeliveries == 5 }
            assertEquals(listOf(false), results)
            assertFalse(state.status.isGranted)
            assertEquals(before, state.details)
            assertEquals(nativeQueriesAtDisposal, helper.nativeQueries, "No native query may start after disposal")
            assertTrue(helper.backgroundObserved())
            state.launchPermissionRequest()
            assertEquals(2, helper.requests.size)
        } finally {
            try { host.close() } finally {
                PermissionDelegateRegistry.register(permission) { NotGrantedPermissionHelper() }
                helper.releaseCapturedCallbacks()
            }
        }
    }

    private class PendingHelper : PermissionSnapshotHelper, PermissionLifecycleHelper {
        var factories = 0
        var disposals = 0
        var nativeQueries = 0
        var delayQueries = false
        var mainDeliveries = 0
            private set
        val requests = mutableListOf<(Boolean) -> Unit>()
        val queries = mutableListOf<(PermissionSnapshot) -> Unit>()
        private var granted = false
        private val lock = NSLock()
        private var background = false
        override fun getPermissionSnapshot(onResult: (PermissionSnapshot) -> Unit) {
            assertTrue(NSThread.isMainThread)
            assertEquals(0, disposals)
            nativeQueries++
            if (delayQueries) queries += onResult else onResult(snapshot(granted))
        }
        override fun launchPermissionRequest(onPermissionResult: (Boolean) -> Unit) {
            assertTrue(NSThread.isMainThread)
            assertEquals(0, disposals)
            requests += onPermissionResult
        }
        private fun snapshot(value: Boolean) = PermissionSnapshot(
            if (value) PermissionStatus.Granted else PermissionStatus.Denied(false),
            PermissionDetails(PermissionAvailability.Available,
                if (value) PermissionAccess.Full else PermissionAccess.None, PermissionRequestability.Requestable))
        fun deliverRequest(index: Int, value: Boolean, duplicate: Boolean = false) {
            assertTrue(NSThread.isMainThread)
            granted = value // Only completion crosses queues; backend observation remains Main-confined.
            val callback = requests[index]
            dispatch { callback(value); if (duplicate) callback(value) }
        }
        fun deliverQuery(index: Int, value: Boolean, duplicate: Boolean = false) {
            assertTrue(NSThread.isMainThread)
            val callback = queries[index]
            val observed = snapshot(value)
            dispatch { callback(observed); if (duplicate) callback(observed) }
        }
        private fun dispatch(callback: () -> Unit) {
            dispatch_async(dispatch_get_global_queue(0, 0u)) {
                lock.lock()
                try { background = !NSThread.isMainThread } finally { lock.unlock() }
                callback()
                dispatch_async(dispatch_get_main_queue()) { mainDeliveries++ }
            }
        }
        fun backgroundObserved(): Boolean {
            lock.lock()
            return try { background } finally { lock.unlock() }
        }
        override fun dispose() { assertTrue(NSThread.isMainThread); disposals++ }
        fun releaseCapturedCallbacks() { requests.clear(); queries.clear() }
    }

    private class Owner : LifecycleOwner {
        val registry = LifecycleRegistry(this).apply { currentState = Lifecycle.State.RESUMED }
        override val lifecycle: Lifecycle get() = registry
    }

    private class Host(private val allowedFailure: Throwable? = null) {
        val owner = Owner()
        val errors = mutableListOf<Throwable>()
        private val clock = BroadcastFrameClock()
        private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate + clock +
            CoroutineExceptionHandler { _, error -> errors += error })
        private val recomposer = Recomposer(scope.coroutineContext)
        private val composition = Composition(NoNodes(), recomposer)
        private val work = scope.launch { recomposer.runRecomposeAndApplyChanges() }
        private var generation by mutableStateOf(0)
        private var committed = -1
        private var frame = 0L
        private var disposed = false
        init { assertTrue(NSThread.isMainThread, "The real Foundation main run loop must own these tests") }
        fun setContent(content: @Composable () -> Unit) {
            composition.setContent {
                val current = generation
                CompositionLocalProvider(LocalLifecycleOwner provides owner, content = content)
                SideEffect { committed = current }
            }
            await("actual initial composition") { committed == generation && !recomposer.hasPendingWork }
        }
        fun recompose() {
            generation++
            Snapshot.sendApplyNotifications()
            await("actual owner-preserving recomposition") { committed == generation && !recomposer.hasPendingWork }
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
            await("owned recomposer cancellation") { work.isCompleted }
        }
        fun close() { dispose(); assertEquals(0, owner.registry.observerCount) }
    }
    private class NoNodes : AbstractApplier<Unit>(Unit) {
        override fun insertBottomUp(index: Int, instance: Unit) = Unit
        override fun insertTopDown(index: Int, instance: Unit) = Unit
        override fun move(from: Int, to: Int, count: Int) = Unit
        override fun remove(index: Int, count: Int) = Unit
        override fun onClear() = Unit
    }
}
