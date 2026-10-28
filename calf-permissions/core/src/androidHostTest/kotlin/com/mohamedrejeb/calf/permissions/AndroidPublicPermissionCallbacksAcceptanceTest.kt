@file:OptIn(ExperimentalPermissionsApi::class, kotlinx.coroutines.ExperimentalCoroutinesApi::class)

package com.mohamedrejeb.calf.permissions

import android.Manifest
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import kotlinx.coroutines.test.runTest
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.LooperMode
import kotlin.test.*

/** Public Android singles, including the original constructor-callback fast path; controlled grants. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [29, 33], manifest = Config.NONE)
@LooperMode(LooperMode.Mode.PAUSED)
class AndroidPublicPermissionCallbacksAcceptanceTest {
    @Test fun singleRuntimeAndNoGateKeepTheirOwnersAndUseLatestCallbacks() = runTest {
        val host = AndroidPermissionCompositionTest.PermissionComposition(this)
        val camera = Permission("android-important-callback-camera").also {
            AndroidPermissionRegistry.register(it, AndroidPermissionMapping(Manifest.permission.CAMERA))
        }
        val noGate = Permission("android-important-callback-no-gate").also {
            AndroidPermissionRegistry.register(it, AndroidPermissionMapping("", alwaysGranted = true))
        }
        var version by mutableStateOf(0)
        lateinit var runtime: PermissionState
        lateinit var fast: PermissionState
        val runtimeResults = mutableListOf<Pair<Int, Boolean>>()
        val fastResults = mutableListOf<Pair<Int, Boolean>>()
        try {
            host.deny(Manifest.permission.CAMERA)
            host.setContent {
                val current = version
                runtime = rememberPermissionState(camera) {
                    assertTrue(runtime.status.isGranted)
                    assertEquals(PermissionRequestOutcome.Granted, runtime.details.lastRequest)
                    runtimeResults += current to it
                }
                fast = rememberPermissionState(noGate) {
                    assertEquals(PermissionAvailability.NotRequired, fast.details.availability)
                    assertEquals(PermissionRequestOutcome.NotRequired, fast.details.lastRequest)
                    fastResults += current to it
                }
            }
            val runtimeOwner = runtime
            val fastOwner = fast
            runtime.launchPermissionRequest()
            fast.launchPermissionRequest()
            assertEquals(listOf(0 to true), fastResults)
            assertTrue(runtimeResults.isEmpty())
            assertEquals(listOf(Manifest.permission.CAMERA), host.registry.launches.single().permissions)

            version = 1
            host.recompose()
            assertSame(runtimeOwner, runtime)
            assertSame(fastOwner, fast)
            fast.launchPermissionRequest()
            host.grant(Manifest.permission.CAMERA)
            host.registry.deliver(0, setOf(Manifest.permission.CAMERA))
            host.registry.deliver(0, setOf(Manifest.permission.CAMERA))
            assertEquals(listOf(1 to true), runtimeResults)
            assertEquals(listOf(0 to true, 1 to true), fastResults)

            version = 2
            host.recompose()
            assertSame(runtimeOwner, runtime)
            assertSame(fastOwner, fast)
            runtime.launchPermissionRequest() // The now-granted runtime member also takes its synchronous path.
            fast.launchPermissionRequest()
            assertEquals(listOf(1 to true, 2 to true), runtimeResults)
            assertEquals(listOf(0 to true, 1 to true, 2 to true), fastResults)
            assertEquals(1, host.registry.launches.size, "Recomposition/no-gate/already-granted requests must not churn native launchers")
            host.disposeComposition()
            runtime.launchPermissionRequest()
            fast.launchPermissionRequest()
            assertEquals(2, runtimeResults.size)
            assertEquals(3, fastResults.size)
            assertEquals(0, host.owner.registry.observerCount)
        } finally { host.close() }
    }
}
