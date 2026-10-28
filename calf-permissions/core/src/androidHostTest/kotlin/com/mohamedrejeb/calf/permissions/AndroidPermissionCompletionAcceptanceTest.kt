@file:OptIn(ExperimentalPermissionsApi::class, kotlinx.coroutines.ExperimentalCoroutinesApi::class)

package com.mohamedrejeb.calf.permissions

import android.Manifest
import android.os.Build
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import kotlinx.coroutines.test.runTest
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.LooperMode
import kotlin.test.*

/** Actual public Compose/ActivityResult/lifecycle routes on API29/33; controlled OS grants. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [29, 33], manifest = Config.NONE)
@LooperMode(LooperMode.Mode.PAUSED)
class AndroidPermissionCompletionAcceptanceTest {
    @Test fun emptyFilteredAndMixedBatchesReturnCompleteMapsIncludingRealNotificationBoundaries() = runTest {
        val host = AndroidPermissionCompositionTest.PermissionComposition(this)
        val camera = mapped("mixed-camera")
        val unknown = Permission("android-completion-unregistered")
        var input by mutableStateOf(emptyList<Permission>())
        var version by mutableStateOf(0)
        lateinit var state: MultiplePermissionsState
        val results = mutableListOf<Pair<Int, Map<Permission, Boolean>>>()
        try {
            host.deny(Manifest.permission.CAMERA, Manifest.permission.POST_NOTIFICATIONS)
            host.setContent {
                val current = version
                state = rememberMultiplePermissionsState(input) { results += current to it }
            }
            state.launchMultiplePermissionRequest()
            assertEquals(listOf(0 to emptyMap<Permission, Boolean>()), results)
            assertTrue(host.registry.launches.isEmpty())

            input = listOf(Permission.WriteStorage, Permission.RemoteNotification)
            version = 1
            host.recompose()
            state.launchMultiplePermissionRequest()
            assertEquals(1 to input.associateWith { true }, results.last())
            assertEquals(2, results.size)
            assertTrue(host.registry.launches.isEmpty())
            assertTrue(state.permissions.all { it.details.availability == PermissionAvailability.NotRequired })

            input = listOf(camera, Permission.Notification, Permission.WriteStorage, unknown, camera)
            version = 2
            host.recompose()
            state.launchMultiplePermissionRequest()
            val expectedNative = if (Build.VERSION.SDK_INT >= 33)
                listOf(Manifest.permission.CAMERA, Manifest.permission.POST_NOTIFICATIONS)
            else listOf(Manifest.permission.CAMERA)
            assertEquals(expectedNative, host.registry.launches.single().permissions)
            assertEquals(2, results.size, "No premature/partial mixed callback")
            version = 3
            host.recompose()
            host.grant(*expectedNative.toTypedArray())
            host.registry.deliver(0, expectedNative.toSet())
            host.registry.deliver(0, expectedNative.toSet())
            val expected = input.distinct().associateWith { it != unknown }
            assertEquals(3, results.size, "A duplicate native result must not duplicate completion")
            assertEquals(3 to expected, results.last())
            assertEquals(expected, state.permissions.associate { it.permission to it.status.isGranted })
            assertEquals(PermissionAvailability.Unsupported,
                state.permissions.single { it.permission == unknown }.details.availability)
            val notification = state.permissions.single { it.permission == Permission.Notification }
            assertEquals(if (Build.VERSION.SDK_INT < 33) PermissionAvailability.NotRequired else PermissionAvailability.Available,
                notification.details.availability)
        } finally { host.close() }
    }

    @Test fun runtimeNotRequiredAndUnknownChildrenUseLatestCallbacksExactlyOnce() = runTest {
        val host = AndroidPermissionCompositionTest.PermissionComposition(this)
        val camera = mapped("child-camera")
        val unknown = Permission("android-completion-child-unregistered")
        var version by mutableStateOf(0)
        lateinit var state: MultiplePermissionsState
        val results = mutableListOf<Pair<Int, Map<Permission, Boolean>>>()
        try {
            host.deny(Manifest.permission.CAMERA)
            host.setContent {
                val current = version
                state = rememberMultiplePermissionsState(listOf(camera, Permission.WriteStorage, unknown)) {
                    results += current to it
                }
            }
            val owner = state
            state.permissions[0].launchPermissionRequest()
            assertEquals(listOf(Manifest.permission.CAMERA), host.registry.launches.single().permissions)
            assertTrue(results.isEmpty())
            version = 1
            host.recompose()
            assertSame(owner, state)
            host.registry.deliver(0, emptySet())
            host.registry.deliver(0, emptySet())
            assertEquals(listOf(1 to mapOf(camera to false)), results)
            state.permissions[1].launchPermissionRequest()
            state.permissions[2].launchPermissionRequest()
            assertEquals(listOf(1 to mapOf(camera to false), 1 to mapOf(Permission.WriteStorage to true),
                1 to mapOf(unknown to false)), results)
            assertEquals(1, host.registry.launches.size, "Synthetic members must not launch an OS request")
            assertEquals(PermissionRequestOutcome.NotRequired, state.permissions[1].details.lastRequest)
            assertEquals(PermissionRequestOutcome.Unsupported, state.permissions[2].details.lastRequest)
        } finally { host.close() }
    }

    @Test fun destroyedAndRecreatedActivityOwnersCannotDeliverOldOrDuplicateChildResults() = runTest {
        val old = AndroidPermissionCompositionTest.PermissionComposition(this)
        val camera = mapped("recreated-camera")
        val results = mutableListOf<Pair<Int, Map<Permission, Boolean>>>()
        lateinit var previous: MultiplePermissionsState
        var oldClosed = false
        try {
            old.deny(Manifest.permission.CAMERA)
            old.setContent { previous = rememberMultiplePermissionsState(listOf(camera)) { results += 0 to it } }
            previous.permissions.single().launchPermissionRequest()
            assertEquals(1, old.registry.launches.size)
            old.close()
            oldClosed = true
            assertEquals(0, old.owner.registry.observerCount)
            val replacement = AndroidPermissionCompositionTest.PermissionComposition(this)
            try {
                replacement.deny(Manifest.permission.CAMERA)
                lateinit var current: MultiplePermissionsState
                replacement.setContent { current = rememberMultiplePermissionsState(listOf(camera)) { results += 1 to it } }
                assertNotSame(previous, current)
                old.registry.deliver(0, setOf(Manifest.permission.CAMERA))
                assertTrue(results.isEmpty(), "A destroyed owner's pending callback must not reach its successor")
                assertFalse(current.permissions.single().status.isGranted)
                current.permissions.single().launchPermissionRequest()
                replacement.grant(Manifest.permission.CAMERA)
                replacement.registry.deliver(0, setOf(Manifest.permission.CAMERA))
                replacement.registry.deliver(0, setOf(Manifest.permission.CAMERA))
                assertEquals(listOf(1 to mapOf(camera to true)), results)
                replacement.disposeComposition()
                current.permissions.single().launchPermissionRequest()
                previous.permissions.single().launchPermissionRequest()
                assertEquals(1, old.registry.launches.size)
                assertEquals(1, replacement.registry.launches.size)
                assertEquals(0, replacement.owner.registry.observerCount)
            } finally { replacement.close() }
        } finally { if (!oldClosed) old.close() }
    }

    private fun mapped(name: String) = Permission("android-completion-$name").also {
        AndroidPermissionRegistry.register(it, AndroidPermissionMapping(Manifest.permission.CAMERA))
    }
}
