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
import platform.Foundation.NSDate
import platform.Foundation.NSLock
import platform.Foundation.NSProcessInfo
import platform.Foundation.NSRunLoop
import platform.Foundation.NSThread
import platform.Foundation.dateWithTimeIntervalSinceNow
import platform.Foundation.runUntilDate
import platform.darwin.dispatch_async
import platform.darwin.dispatch_get_global_queue
import platform.darwin.dispatch_get_main_queue
import kotlin.test.*

/**
 * Actual public expect/actual factories, Compose Runtime, Darwin Main/background queues,
 * Foundation NSLock and LifecycleRegistry. No Dispatchers.setMain or state/backend substitute.
 * Registered application helpers control native completions: this is not OS privacy UI,
 * a UIKit presentation test, physical-device authority or a heap/leak certification.
 */
class IOSPublicPermissionFactoryTest {
    @Test fun unknownAndExplicitNoGateHaveDifferentCoherentOutcomes() = withHost { host ->
        val unknown = Permission("ios-important-unregistered")
        val noGate = register("no-gate") { GrantedPermissionHelper() }
        // Retain the existing diagnostic of the public registry lookup API.
        val error = assertFailsWith<IllegalStateException> { PermissionDelegateRegistry.getDelegate(unknown) }
        assertTrue(error.message.orEmpty().contains(unknown.name))
        lateinit var state: MultiplePermissionsState
        val results = mutableListOf<Map<Permission, Boolean>>()
        host.setContent { state = rememberMultiplePermissionsState(listOf(unknown, noGate)) { results += it } }
        host.await("coherent unknown and explicit no-gate observation") {
            state.permissions[0].details.availability == PermissionAvailability.Unsupported &&
                state.permissions[1].details.availability == PermissionAvailability.NotRequired
        }
        assertFalse(state.permissions[0].status.isGranted)
        assertEquals(PermissionAccess.None, state.permissions[0].details.access)
        state.launchMultiplePermissionRequest()
        host.await("one complete mixed result") { results.size == 1 }
        assertEquals(listOf(mapOf(unknown to false, noGate to true)), results)
        assertEquals(PermissionRequestOutcome.Unsupported, state.permissions[0].details.lastRequest)
        assertEquals(PermissionRequestOutcome.NotRequired, state.permissions[1].details.lastRequest)
    }

    @Test fun delayedSingleUsesLatestCallbackAndRealMainQueueWithoutReplacingOwner() = withHost { host ->
        val helper = DelayedHelper()
        val permission = register("delayed-single") { helper }
        var version by mutableStateOf(0)
        lateinit var state: PermissionState
        val results = mutableListOf<Pair<Int, Boolean>>()
        host.setContent {
            val current = version
            state = rememberPermissionState(permission) {
                assertTrue(NSThread.isMainThread)
                assertTrue(state.status.isGranted)
                assertEquals(PermissionRequestOutcome.Granted, state.details.lastRequest)
                results += current to it
            }
        }
        val owner = state
        state.launchPermissionRequest()
        assertEquals(1, helper.requests.size)
        assertTrue(results.isEmpty())
        version = 1
        host.recompose()
        assertSame(owner, state)
        assertEquals(1, helper.factories)
        helper.deliverFromBackground(0, true, duplicate = true)
        host.await("latest single callback after a real background completion") { helper.mainDeliveries == 1 }
        assertEquals(listOf(1 to true), results)
        assertTrue(helper.observedBackgroundDelivery())
        assertEquals(1, helper.requests.size)
        host.dispose()
        assertEquals(1, helper.disposals)
        assertEquals(0, host.owner.registry.observerCount)
    }

    @Test fun delayedChildAndSerialBatchUseLatestCallbacksAndExactRequestedMap() = withHost { host ->
        val firstHelper = DelayedHelper()
        val secondHelper = DelayedHelper()
        val first = register("batch-first") { firstHelper }
        val second = register("batch-second") { secondHelper }
        val noGate = register("batch-no-gate") { GrantedPermissionHelper() }
        var version by mutableStateOf(0)
        lateinit var state: MultiplePermissionsState
        val results = mutableListOf<Pair<Int, Map<Permission, Boolean>>>()
        host.setContent {
            val current = version
            state = rememberMultiplePermissionsState(listOf(first, noGate, second, first)) {
                assertTrue(NSThread.isMainThread)
                results += current to it
            }
        }
        val owner = state
        assertEquals(listOf(first, noGate, second), state.permissions.map { it.permission })
        state.permissions.first().launchPermissionRequest()
        version = 1
        host.recompose()
        assertSame(owner, state)
        firstHelper.deliverFromBackground(0, true, duplicate = true)
        host.await("one latest child result") { firstHelper.mainDeliveries == 1 }
        assertEquals(listOf(1 to mapOf(first to true)), results)

        state.launchMultiplePermissionRequest()
        assertEquals(2, firstHelper.requests.size)
        assertTrue(secondHelper.requests.isEmpty(), "The second native request must wait for the first")
        version = 2
        host.recompose()
        firstHelper.deliverFromBackground(1, false)
        host.await("serial second request after the first result") {
            firstHelper.mainDeliveries == 2 && secondHelper.requests.size == 1
        }
        assertEquals(1, results.size, "No premature partial batch completion")
        secondHelper.deliverFromBackground(0, true, duplicate = true)
        host.await("complete latest batch map") { secondHelper.mainDeliveries == 1 }
        val batch = mapOf(first to false, noGate to true, second to true)
        assertEquals(listOf(1 to mapOf(first to true), 2 to batch), results)
        assertEquals(batch, state.permissions.associate { it.permission to it.status.isGranted })
        state.permissions[1].launchPermissionRequest()
        host.await("latest explicit no-gate child result") { results.size == 3 }
        assertEquals(2 to mapOf(noGate to true), results.last())
        assertEquals(1, firstHelper.factories)
        assertEquals(1, secondHelper.factories)
        host.dispose()
        assertEquals(1, firstHelper.disposals)
        assertEquals(1, secondHelper.disposals)
        assertEquals(0, host.owner.registry.observerCount)
    }

    @Test fun emptyAndNotRequiredPublicRequestsUseLatestCallbackWithoutNativeWork() = withHost { host ->
        val noGate = register("fast-single") { GrantedPermissionHelper() }
        var version by mutableStateOf(0)
        lateinit var single: PermissionState
        lateinit var empty: MultiplePermissionsState
        val singles = mutableListOf<Pair<Int, Boolean>>()
        val batches = mutableListOf<Pair<Int, Map<Permission, Boolean>>>()
        host.setContent {
            val current = version
            single = rememberPermissionState(noGate) { singles += current to it }
            empty = rememberMultiplePermissionsState(emptyList()) { batches += current to it }
        }
        val singleOwner = single
        val batchOwner = empty
        single.launchPermissionRequest()
        empty.launchMultiplePermissionRequest()
        host.await("first fast-path callbacks") { singles.size == 1 && batches.size == 1 }
        version = 1
        host.recompose()
        assertSame(singleOwner, single)
        assertSame(batchOwner, empty)
        single.launchPermissionRequest()
        empty.launchMultiplePermissionRequest()
        host.await("latest fast-path callbacks") { singles.size == 2 && batches.size == 2 }
        assertEquals(listOf(0 to true, 1 to true), singles)
        assertEquals(listOf(0 to emptyMap<Permission, Boolean>(), 1 to emptyMap()), batches)
        assertEquals(PermissionAvailability.NotRequired, single.details.availability)
        assertEquals(PermissionRequestOutcome.NotRequired, single.details.lastRequest)
        assertTrue(empty.permissions.isEmpty())
    }

    @Test fun replacementAndDisposalDropOldNativeResultsAndReleaseLifecycleObservers() = withHost { host ->
        val firstHelper = DelayedHelper()
        val secondHelper = DelayedHelper()
        val first = register("dispose-first") { firstHelper }
        val second = register("dispose-second") { secondHelper }
        var selected by mutableStateOf(first)
        lateinit var state: PermissionState
        val results = mutableListOf<Pair<Permission, Boolean>>()
        host.setContent {
            val current = selected
            state = rememberPermissionState(current) { results += current to it }
        }
        val previous = state
        state.launchPermissionRequest()
        selected = second
        host.recompose()
        assertNotSame(previous, state)
        assertEquals(1, firstHelper.disposals)
        assertEquals(1, host.owner.registry.observerCount)
        val oldQueries = firstHelper.queries
        firstHelper.deliverFromBackground(0, true)
        host.await("actual old background callback processed on main") { firstHelper.mainDeliveries == 1 }
        assertTrue(results.isEmpty())
        assertFalse(state.status.isGranted)
        assertEquals(oldQueries, firstHelper.queries)
        state.launchPermissionRequest()
        secondHelper.deliverFromBackground(0, true)
        host.await("replacement result") { secondHelper.mainDeliveries == 1 }
        assertEquals(listOf(second to true), results)
        state.launchPermissionRequest()
        host.dispose()
        assertEquals(1, secondHelper.disposals)
        assertEquals(0, host.owner.registry.observerCount)
        secondHelper.deliverFromBackground(1, false)
        host.await("actual late callback processed after disposal") { secondHelper.mainDeliveries == 2 }
        assertEquals(listOf(second to true), results)
        previous.launchPermissionRequest()
        state.launchPermissionRequest()
        assertEquals(1, firstHelper.requests.size)
        assertEquals(2, secondHelper.requests.size)
    }

    @Test fun nativeRegistryHandlesNameCollisionsConcurrentLookupsAndReentrantFactories() {
        val permission = Permission("ios-important-registry-collision")
        val first = NotGrantedPermissionHelper()
        val second = GrantedPermissionHelper()
        PermissionDelegateRegistry.register(permission) { first }
        assertSame(first, PermissionDelegateRegistry.getDelegate(Permission(permission.name)))
        PermissionDelegateRegistry.register(Permission(permission.name)) { second }
        assertSame(second, PermissionDelegateRegistry.getDelegate(permission))
        val nested = Permission("ios-important-registry-reentrant")
        PermissionDelegateRegistry.register(nested) {
            PermissionDelegateRegistry.register(permission) { first }
            PermissionDelegateRegistry.getDelegate(permission)
        }
        assertSame(first, PermissionDelegateRegistry.getDelegate(nested))
        runBlocking {
            withTimeout(10_000) {
                List(16) { index ->
                    async(Dispatchers.Default) {
                        val key = Permission("ios-important-registry-concurrent-$index")
                        repeat(200) {
                            PermissionDelegateRegistry.register(key) { GrantedPermissionHelper() }
                            assertIs<GrantedPermissionHelper>(PermissionDelegateRegistry.getDelegate(Permission(key.name)))
                        }
                    }
                }.awaitAll()
            }
        }
        PermissionDelegateRegistry.register(permission) { NotGrantedPermissionHelper() }
        PermissionDelegateRegistry.register(nested) { NotGrantedPermissionHelper() }
    }

    @Test fun throwingRegisteredFactoryRemainsFailedRatherThanMasqueradingAsUnsupported() = withHost { host ->
        val permission = register("factory-failure") { error("Deliberate application helper failure") }
        lateinit var state: PermissionState
        val results = mutableListOf<Boolean>()
        host.setContent { state = rememberPermissionState(permission) { results += it } }
        host.await("explicit registered-helper failure") { state.details.lastRequest == PermissionRequestOutcome.Failed }
        assertEquals(PermissionAvailability.Unknown, state.details.availability)
        assertFalse(state.status.isGranted)
        state.launchPermissionRequest()
        host.await("one failed request result") { results.size == 1 }
        assertEquals(listOf(false), results)
        assertEquals(PermissionRequestOutcome.Failed, state.details.lastRequest)
        assertEquals(PermissionAvailability.Unknown, state.details.availability)
    }

    private val registered = mutableListOf<Permission>()
    private fun register(name: String, factory: () -> PermissionHelper): Permission =
        Permission("ios-important-$name").also { permission ->
            registered += permission
            PermissionDelegateRegistry.register(permission) {
                factory().also { if (it is DelayedHelper) it.factories++ }
            }
        }

    private fun withHost(body: (Host) -> Unit) {
        val host = Host()
        try { body(host) } finally {
            try { host.close() } finally {
                // The public registry intentionally retains application factories. Drop
                // the test's captured helpers without adding a production unregister API.
                registered.forEach { PermissionDelegateRegistry.register(it) { NotGrantedPermissionHelper() } }
                registered.clear()
            }
        }
    }

    private class DelayedHelper : PermissionSnapshotHelper, PermissionLifecycleHelper {
        var factories = 0
        var queries = 0
        var disposals = 0
        var mainDeliveries = 0
            private set
        val requests = mutableListOf<(Boolean) -> Unit>()
        private var granted = false
        private val lock = NSLock()
        private var background = false
        override fun getPermissionSnapshot(onResult: (PermissionSnapshot) -> Unit) {
            assertTrue(NSThread.isMainThread)
            assertEquals(0, disposals)
            queries++
            onResult(PermissionSnapshot(if (granted) PermissionStatus.Granted else PermissionStatus.Denied(false),
                PermissionDetails(PermissionAvailability.Available,
                    if (granted) PermissionAccess.Full else PermissionAccess.None, PermissionRequestability.Requestable)))
        }
        override fun launchPermissionRequest(onPermissionResult: (Boolean) -> Unit) {
            assertTrue(NSThread.isMainThread)
            assertEquals(0, disposals)
            requests += onPermissionResult
        }
        fun deliverFromBackground(index: Int, value: Boolean, duplicate: Boolean = false) {
            assertTrue(NSThread.isMainThread)
            granted = value // The observation remains main-confined; only the callback crosses queues.
            val callback = requests[index]
            dispatch_async(dispatch_get_global_queue(0, 0u)) {
                lock.lock()
                try { background = !NSThread.isMainThread } finally { lock.unlock() }
                callback(value)
                if (duplicate) callback(value)
                // A real queue barrier follows both callbacks. Negative disposal/
                // duplicate assertions must not race an as-yet-undelivered event.
                dispatch_async(dispatch_get_main_queue()) { mainDeliveries++ }
            }
        }
        fun observedBackgroundDelivery(): Boolean {
            lock.lock()
            return try { background } finally { lock.unlock() }
        }
        override fun dispose() { assertTrue(NSThread.isMainThread); disposals++ }
    }

    private class Owner : LifecycleOwner {
        val registry = LifecycleRegistry(this).apply { currentState = Lifecycle.State.RESUMED }
        override val lifecycle: Lifecycle get() = registry
    }

    private class Host {
        val owner = Owner()
        private val failures = mutableListOf<Throwable>()
        private val clock = BroadcastFrameClock()
        private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate + clock +
            CoroutineExceptionHandler { _, error -> failures += error })
        private val recomposer = Recomposer(scope.coroutineContext)
        private val composition = Composition(NoNodes(), recomposer)
        private val work = scope.launch { recomposer.runRecomposeAndApplyChanges() }
        private var generation by mutableStateOf(0)
        private var committed = -1
        private var frame = 0L
        private var disposed = false
        init { assertTrue(NSThread.isMainThread, "These native tests must own the real Foundation main run loop") }

        fun setContent(content: @Composable () -> Unit) {
            composition.setContent {
                val current = generation
                CompositionLocalProvider(LocalLifecycleOwner provides owner, content = content)
                SideEffect { committed = current }
            }
            await("initial real composition") { committed == generation && !recomposer.hasPendingWork }
        }
        fun recompose() {
            generation++
            Snapshot.sendApplyNotifications()
            await("real callback-holder recomposition") { committed == generation && !recomposer.hasPendingWork }
        }
        fun await(phase: String, predicate: () -> Boolean) {
            val deadline = NSProcessInfo.processInfo.systemUptime + 10.0
            do {
                flushMain()
                failures.firstOrNull()?.let { throw it }
                if (predicate()) return
            } while (NSProcessInfo.processInfo.systemUptime < deadline)
            error("Timed out awaiting $phase")
        }
        fun flushMain() {
            Snapshot.sendApplyNotifications()
            if (clock.hasAwaiters) clock.sendFrame(++frame)
            NSRunLoop.mainRunLoop.runUntilDate(NSDate.dateWithTimeIntervalSinceNow(0.002))
            failures.firstOrNull()?.let { throw it }
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
