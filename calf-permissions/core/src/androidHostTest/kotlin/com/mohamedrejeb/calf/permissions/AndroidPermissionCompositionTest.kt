@file:OptIn(ExperimentalPermissionsApi::class, kotlinx.coroutines.ExperimentalCoroutinesApi::class)

package com.mohamedrejeb.calf.permissions

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import androidx.activity.compose.LocalActivityResultRegistryOwner
import androidx.activity.result.ActivityResultRegistry
import androidx.activity.result.ActivityResultRegistryOwner
import androidx.activity.result.contract.ActivityResultContract
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.ui.platform.LocalContext
import androidx.core.app.ActivityOptionsCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.LifecycleRegistry
import androidx.lifecycle.compose.LocalLifecycleOwner
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config
import org.robolectric.annotation.LooperMode
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNotSame
import kotlin.test.assertSame
import kotlin.test.assertTrue

/**
 * Public factories, real Android Compose/ActivityResult contracts and lifecycle observers under
 * Robolectric. The registry deliberately records requests instead of showing system privacy UI.
 * Permission observations are Robolectric application grants, not real device authorization.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34], manifest = Config.NONE)
@LooperMode(LooperMode.Mode.PAUSED)
class AndroidPermissionCompositionTest {
    @Test fun delayedSingleResultUsesLatestCallbackAndRefreshesBeforeDelivery() = runTest {
        val host = PermissionComposition(this)
        val permission = mapped("single", Manifest.permission.CAMERA)
        host.deny(Manifest.permission.CAMERA)
        var version by mutableStateOf(0)
        lateinit var state: PermissionState
        val results = mutableListOf<Pair<Int, Boolean>>()
        try {
            host.setContent {
                val current = version
                state = rememberPermissionState(permission) { granted ->
                    assertEquals(PermissionStatus.Granted, state.status)
                    assertEquals(PermissionRequestOutcome.Granted, state.details.lastRequest)
                    results += current to granted
                }
            }
            val original = state
            assertFalse(state.status.isGranted)
            state.launchPermissionRequest()
            assertEquals(listOf(Manifest.permission.CAMERA), host.registry.launches.single().permissions)
            assertTrue(results.isEmpty())
            version = 1
            host.recompose()
            assertSame(original, state)
            host.grant(Manifest.permission.CAMERA)
            host.registry.deliver(0, setOf(Manifest.permission.CAMERA))
            assertEquals(listOf(1 to true), results)
            assertEquals(1, host.registry.launches.size)
        } finally {
            host.close()
        }
    }

    @Test fun batchFansOutAliasesAndSyntheticMembersThroughTheActualRegistry() = runTest {
        val host = PermissionComposition(this)
        val first = mapped("batch-first", Manifest.permission.CAMERA)
        val alias = mapped("batch-alias", Manifest.permission.CAMERA)
        val noGate = Permission("android-composition-no-gate").also {
            AndroidPermissionRegistry.register(it, AndroidPermissionMapping("", alwaysGranted = true))
        }
        val unsupported = Permission("android-composition-unregistered")
        host.deny(Manifest.permission.CAMERA)
        var version by mutableStateOf(0)
        lateinit var state: MultiplePermissionsState
        val results = mutableListOf<Pair<Int, Map<Permission, Boolean>>>()
        try {
            host.setContent {
                val current = version
                state = rememberMultiplePermissionsState(listOf(first, first, alias, noGate, unsupported)) {
                    results += current to it
                }
            }
            val original = state
            assertEquals(listOf(first, alias, noGate, unsupported), state.permissions.map { it.permission })
            state.launchMultiplePermissionRequest()
            assertEquals(listOf(Manifest.permission.CAMERA), host.registry.launches.single().permissions)
            version = 1
            host.recompose()
            assertSame(original, state)
            host.grant(Manifest.permission.CAMERA)
            host.registry.deliver(0, setOf(Manifest.permission.CAMERA))
            val expected = mapOf(first to true, alias to true, noGate to true, unsupported to false)
            assertEquals(listOf(1 to expected), results)
            assertEquals(expected, state.permissions.associate { it.permission to it.status.isGranted })
            assertEquals(PermissionRequestOutcome.NotRequired, state.permissions[2].details.lastRequest)
            assertEquals(PermissionRequestOutcome.Unsupported, state.permissions[3].details.lastRequest)
            state.permissions.first().launchPermissionRequest()
            assertEquals(listOf(1 to expected, 1 to mapOf(first to true)), results)
            assertEquals(1, host.registry.launches.size)
        } finally {
            host.close()
        }
    }

    @Test fun emptyAndroidBatchCompletesEachLaunchWithTheLatestCallbackWithoutNativeWork() = runTest {
        val host = PermissionComposition(this)
        var version by mutableStateOf(0)
        lateinit var state: MultiplePermissionsState
        val results = mutableListOf<Pair<Int, Map<Permission, Boolean>>>()
        try {
            host.setContent {
                val current = version
                state = rememberMultiplePermissionsState(emptyList()) { results += current to it }
            }
            state.launchMultiplePermissionRequest()
            version = 1
            host.recompose()
            state.launchMultiplePermissionRequest()
            assertEquals(listOf(0 to emptyMap<Permission, Boolean>(), 1 to emptyMap<Permission, Boolean>()), results)
            assertTrue(state.permissions.isEmpty())
            assertTrue(host.registry.launches.isEmpty())
        } finally {
            host.close()
        }
    }

    @Test fun resumeRefreshesRevocationAndDisposalUnregistersObserversAndPendingDelivery() = runTest {
        val host = PermissionComposition(this)
        val permission = mapped("resume", Manifest.permission.CAMERA)
        host.grant(Manifest.permission.CAMERA)
        lateinit var state: PermissionState
        val results = mutableListOf<Boolean>()
        try {
            assertEquals(0, host.owner.registry.observerCount)
            host.setContent { state = rememberPermissionState(permission) { results += it } }
            assertTrue(state.status.isGranted)
            assertEquals(1, host.owner.registry.observerCount)
            host.owner.registry.handleLifecycleEvent(Lifecycle.Event.ON_PAUSE)
            host.deny(Manifest.permission.CAMERA)
            host.owner.registry.handleLifecycleEvent(Lifecycle.Event.ON_RESUME)
            assertFalse(state.status.isGranted)
            assertTrue(results.isEmpty())
            state.launchPermissionRequest()
            assertEquals(1, host.registry.launches.size)
            host.disposeComposition()
            assertEquals(0, host.owner.registry.observerCount)
            host.grant(Manifest.permission.CAMERA)
            host.registry.deliver(0, setOf(Manifest.permission.CAMERA))
            assertTrue(results.isEmpty())
            assertFalse(state.status.isGranted)
            state.launchPermissionRequest()
            assertEquals(1, host.registry.launches.size)
        } finally {
            host.close()
        }
    }

    @Test fun changedPermissionRebindsTheLauncherAndDropsThePreviousOwnersResult() = runTest {
        val host = PermissionComposition(this)
        val camera = mapped("replace-camera", Manifest.permission.CAMERA)
        val microphone = mapped("replace-microphone", Manifest.permission.RECORD_AUDIO)
        host.deny(Manifest.permission.CAMERA, Manifest.permission.RECORD_AUDIO)
        var selected by mutableStateOf(camera)
        lateinit var state: PermissionState
        val results = mutableListOf<Pair<Permission, Boolean>>()
        try {
            host.setContent {
                val current = selected
                state = rememberPermissionState(current) { results += current to it }
            }
            val old = state
            state.launchPermissionRequest()
            selected = microphone
            host.recompose()
            assertNotSame(old, state)
            assertEquals(microphone, state.permission)
            assertEquals(1, host.owner.registry.observerCount)
            host.grant(Manifest.permission.CAMERA)
            host.registry.deliver(0, setOf(Manifest.permission.CAMERA))
            assertTrue(results.isEmpty())
            assertFalse(state.status.isGranted)
            state.launchPermissionRequest()
            assertEquals(listOf(Manifest.permission.RECORD_AUDIO), host.registry.launches[1].permissions)
            host.grant(Manifest.permission.RECORD_AUDIO)
            host.registry.deliver(1, setOf(Manifest.permission.RECORD_AUDIO))
            assertEquals(listOf(microphone to true), results)
            assertTrue(state.status.isGranted)
        } finally {
            host.close()
        }
    }

    private fun mapped(name: String, native: String) = Permission("android-composition-$name").also {
        AndroidPermissionRegistry.register(it, AndroidPermissionMapping(native))
    }

    private class Owner : LifecycleOwner {
        val registry = LifecycleRegistry(this).apply { currentState = Lifecycle.State.RESUMED }
        override val lifecycle: Lifecycle get() = registry
    }

    private class PermissionComposition(private val scope: TestScope) {
        private val activityController = Robolectric.buildActivity(Activity::class.java).setup()
        private val activity = activityController.get()
        val owner = Owner()
        val registry = RecordingPermissionRegistry(activity)
        private val clock = BroadcastFrameClock()
        private val recomposer = Recomposer(scope.coroutineContext + clock)
        private val composition = Composition(NoNodes(), recomposer)
        private val work = scope.launch(clock) { recomposer.runRecomposeAndApplyChanges() }
        private var disposed = false
        private var frame = 0L

        fun setContent(content: @Composable () -> Unit) {
            composition.setContent {
                CompositionLocalProvider(
                    LocalContext provides activity,
                    LocalLifecycleOwner provides owner,
                    LocalActivityResultRegistryOwner provides registry,
                    content = content,
                )
            }
            scope.runCurrent()
        }

        fun recompose() {
            Snapshot.sendApplyNotifications()
            scope.runCurrent()
            clock.sendFrame(++frame)
            scope.runCurrent()
        }

        fun grant(vararg permissions: String) = shadowOf(activity.application).grantPermissions(*permissions)
        fun deny(vararg permissions: String) = shadowOf(activity.application).denyPermissions(*permissions)

        suspend fun disposeComposition() {
            if (disposed) return
            disposed = true
            try {
                composition.dispose()
            } finally {
                recomposer.close()
                work.cancelAndJoin()
            }
        }

        suspend fun close() {
            try {
                disposeComposition()
            } finally {
                owner.registry.currentState = Lifecycle.State.DESTROYED
                activityController.pause().stop().destroy()
            }
        }
    }

    private class RecordingPermissionRegistry(private val activity: Activity) :
        ActivityResultRegistry(), ActivityResultRegistryOwner {
        data class Launch(val requestCode: Int, val permissions: List<String>)
        val launches = mutableListOf<Launch>()
        override val activityResultRegistry: ActivityResultRegistry get() = this

        override fun <I, O> onLaunch(
            requestCode: Int,
            contract: ActivityResultContract<I, O>,
            input: I,
            options: ActivityOptionsCompat?,
        ) {
            val intent = contract.createIntent(activity, input)
            assertIs<ActivityResultContracts.RequestMultiplePermissions>(contract)
            val permissions = intent.getStringArrayExtra(ActivityResultContracts.RequestMultiplePermissions.EXTRA_PERMISSIONS)
            launches += Launch(requestCode, requireNotNull(permissions).toList())
        }

        fun deliver(index: Int, granted: Set<String>) {
            val launch = launches[index]
            val intent = Intent(ActivityResultContracts.RequestMultiplePermissions.ACTION_REQUEST_PERMISSIONS)
                .putExtra(ActivityResultContracts.RequestMultiplePermissions.EXTRA_PERMISSIONS, launch.permissions.toTypedArray())
                .putExtra(ActivityResultContracts.RequestMultiplePermissions.EXTRA_PERMISSION_GRANT_RESULTS,
                    launch.permissions.map {
                        if (it in granted) PackageManager.PERMISSION_GRANTED else PackageManager.PERMISSION_DENIED
                    }.toIntArray())
            dispatchResult(launch.requestCode, Activity.RESULT_OK, intent)
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
