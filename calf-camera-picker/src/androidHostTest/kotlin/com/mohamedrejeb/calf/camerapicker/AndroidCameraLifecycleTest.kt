package com.mohamedrejeb.calf.camerapicker

import android.app.Activity
import android.content.ContextWrapper
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.provider.MediaStore
import android.provider.OpenableColumns
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.Lifecycle
import org.junit.After
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.Shadows.shadowOf
import org.robolectric.android.controller.ActivityController
import org.robolectric.annotation.Config
import org.robolectric.annotation.LooperMode
import org.robolectric.shadows.ShadowActivity
import java.io.File
import kotlin.test.*

/** A real ComponentActivity/Android composition, with the production ActivityResultRegistry. */
class CameraLifecycleTestActivity : ComponentActivity() {
    var showPicker by mutableStateOf(true)
    var useWrappedContext by mutableStateOf(false)
    private val wrappedContext = ContextWrapper(this)
    var launcher: CameraPickerLauncher? = null
    val results = mutableListOf<CameraPickerResult>()
    var resultCallback by mutableStateOf<(CameraPickerResult) -> Unit>({ results += it })
    var appliedCallback: ((CameraPickerResult) -> Unit)? = null
    val disposals = mutableListOf<CameraDisposalObservation>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            CompositionLocalProvider(LocalContext provides if (useWrappedContext) wrappedContext else this) {
                if (showPicker) {
                    val callback = resultCallback
                    val current = rememberCameraPickerResultLauncher(onResult = callback)
                    SideEffect { launcher = current; appliedCallback = callback }
                    DisposableEffect(Unit) {
                        onDispose {
                            disposals += CameraDisposalObservation(
                                isChangingConfigurations, isDestroyed, isFinishing,
                                lifecycle.currentState, retainCameraRequestForActivityRestoration(),
                            )
                            launcher = null
                        }
                    }
                }
            }
        }
    }
}

data class CameraDisposalObservation(
    val changingConfigurations: Boolean,
    val destroyed: Boolean,
    val finishing: Boolean,
    val lifecycleState: Lifecycle.State,
    val retainForRestoration: Boolean,
)

/**
 * These exercise actual Activity/Compose save, destruction, recreation and registry delivery.
 * Robolectric does not run an external camera or kill the OS process: fixture bytes and result
 * codes explicitly simulate that boundary. Non-finishing destruction models don't-keep-activities
 * without claiming that a device's developer-option lifecycle or URI grants were exercised.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [23])
@LooperMode(LooperMode.Mode.PAUSED)
class AndroidCameraLifecycleTest {
    @get:Rule val compose = createEmptyComposeRule()
    private val controllers = mutableListOf<ActivityController<CameraLifecycleTestActivity>>()
    private val outputs = mutableListOf<File>()

    @After fun releaseFixtures() {
        // No actual camera was launched in this host test; close its synthetic writers first.
        compose.runOnUiThread {
            controllers.asReversed().forEach { if (!it.get().isDestroyed) it.close() }
        }
        outputs.forEach { it.delete() }
    }

    @Test fun nonFinishingDestructionRetainsAnActiveOutputAndSavedRequestForRestoration() {
        val originalController = createActivity()
        val original = originalController.get()
        val launched = launch(original)
        val output = output(launched)
        val saved = Bundle()
        original.contentResolver.openOutputStream(launchUri(launched))!!.use { externalWriter ->
            compose.runOnUiThread {
                originalController.pause().saveInstanceState(saved).stop().destroy()
            }
            assertTrue(original.isDestroyed)
            assertFalse(original.isFinishing)
            assertFalse(original.isChangingConfigurations, "This is not the config-only fixture")
            val disposal = original.disposals.single()
            assertEquals(Lifecycle.State.DESTROYED, disposal.lifecycleState)
            assertTrue(disposal.retainForRestoration)
            assertTrue(output.exists(), "The camera can still be writing after Activity destruction")
            externalWriter.write(byteArrayOf(1, 3, 5, 7))
        }

        val restored = createActivity(saved).get()
        assertNotSame(original, restored)
        compose.runOnIdle { assertNotNull(restored.launcher).launch() }
        assertEquals(CameraPickerResult.Busy, restored.results.single(), "The saved request is still active")
        assertNull(shadowOf(restored).nextStartedActivityForResult)
        deliver(restored, launched, Activity.RESULT_OK)
        val captured = assertIs<CameraPickerResult.Captured>(restored.results.last())
        assertEquals(launchUri(launched), captured.file.uri)
        assertContentEquals(byteArrayOf(1, 3, 5, 7), output.readBytes())
        assertEquals(2, restored.results.size)
        assertTrue(original.results.isEmpty(), "The destroyed owner receives no late callback")
    }

    @Test fun realActivityRecreationRetainsPendingOutputAndCancellationCleansIt() {
        val controller = createActivity()
        val original = controller.get()
        val launched = launch(original)
        val output = output(launched)
        compose.runOnUiThread { controller.recreate() }
        val restored = controller.get()
        awaitComposition(restored)
        assertNotSame(original, restored)
        assertTrue(original.isChangingConfigurations, "Robolectric recreation must take the real config-destroy path")
        assertTrue(original.disposals.single().retainForRestoration)
        assertTrue(output.exists())
        deliver(restored, launched, Activity.RESULT_CANCELED)
        assertEquals(CameraPickerResult.Cancelled, restored.results.single())
        assertFalse(output.exists(), "A terminal camera result, unlike unregister, permits cleanup")
        assertTrue(original.results.isEmpty())
    }

    @Test fun liveCompositionRemovalAbandonsCallbacksWithoutUnlinkingTheExternalOutput() {
        val activity = createActivity().get()
        val oldLauncher = assertNotNull(activity.launcher)
        val first = launch(activity)
        val firstOutput = output(first)
        activity.contentResolver.openOutputStream(launchUri(first))!!.use { externalWriter ->
            compose.runOnIdle { activity.showPicker = false }
            compose.waitForIdle()
            assertFalse(activity.isDestroyed)
            assertFalse(activity.disposals.single().retainForRestoration)
            assertTrue(firstOutput.exists(), "Unregister cannot revoke a camera's open output")
            externalWriter.write(byteArrayOf(2, 4, 6))
        }
        deliver(activity, first, Activity.RESULT_OK)
        assertTrue(activity.results.isEmpty(), "Unregistered/disposed requests cannot deliver to the app")
        compose.runOnIdle { activity.showPicker = true }
        awaitComposition(activity)
        assertNotSame(oldLauncher, activity.launcher)
        val second = launch(activity)
        val secondOutput = output(second)
        assertNotEquals(launchUri(first), launchUri(second))
        assertTrue(activity.results.isEmpty(), "The new composition must not inherit an abandoned Busy request")
        deliver(activity, second, Activity.RESULT_CANCELED)
        assertEquals(CameraPickerResult.Cancelled, activity.results.single())
        assertFalse(secondOutput.exists())
        assertContentEquals(byteArrayOf(2, 4, 6), firstOutput.readBytes())
    }

    @Test fun finishingActivityAbandonsResultButDoesNotDeleteAnInFlightOutput() {
        val controller = createActivity()
        val activity = controller.get()
        val launched = launch(activity)
        val output = output(launched)
        activity.contentResolver.openOutputStream(launchUri(launched))!!.use { externalWriter ->
            compose.runOnUiThread {
                activity.finish()
                controller.pause().stop().destroy()
            }
            assertTrue(activity.isFinishing)
            assertTrue(activity.isDestroyed)
            assertFalse(activity.disposals.single().retainForRestoration)
            assertTrue(output.exists())
            externalWriter.write(byteArrayOf(8, 9))
        }
        deliver(activity, launched, Activity.RESULT_OK)
        assertTrue(activity.results.isEmpty())
        assertContentEquals(byteArrayOf(8, 9), output.readBytes())
    }

    @Test fun liveContextWrapperReplacementTransfersPendingOwnershipWithoutClearingIt() {
        val activity = createActivity().get()
        val originalLauncher = assertNotNull(activity.launcher)
        val launched = launch(activity)
        val output = output(launched)
        activity.contentResolver.openOutputStream(launchUri(launched))!!.use { it.write(byteArrayOf(4, 3, 2, 1)) }
        compose.runOnIdle { activity.useWrappedContext = true }
        compose.waitForIdle()
        assertNotSame(originalLauncher, activity.launcher)
        assertFalse(activity.isDestroyed)
        assertTrue(activity.disposals.isEmpty(), "Only the context-dependent owner changed, not composition identity")
        compose.runOnIdle { assertNotNull(activity.launcher).launch() }
        assertEquals(CameraPickerResult.Busy, activity.results.single())
        assertNull(shadowOf(activity).nextStartedActivityForResult)
        deliver(activity, launched, Activity.RESULT_OK)
        assertEquals(launchUri(launched), assertIs<CameraPickerResult.Captured>(activity.results.last()).file.uri)
        assertContentEquals(byteArrayOf(4, 3, 2, 1), output.readBytes())
        assertEquals(2, activity.results.size)
    }

    // NEW2: genuine host Activity/Compose/registry regressions, not device C1 acceptance.
    @Test fun nonFinishingRestorationThenCallbackSwapDeliversOneReadableResultToCurrentOwner() {
        val callbackAResults = mutableListOf<CameraPickerResult>()
        val callbackBResults = mutableListOf<CameraPickerResult>()
        val callbackA: (CameraPickerResult) -> Unit = { callbackAResults += it }
        val callbackB: (CameraPickerResult) -> Unit = { callbackBResults += it }
        val originalController = createActivity()
        val original = originalController.get()
        val originalOwner = assertNotNull(original.launcher)
        compose.runOnIdle { original.resultCallback = callbackA }
        awaitCallback(original, callbackA)
        assertSame(originalOwner, original.launcher)
        val launched = launch(original)
        val uri = launchUri(launched)
        val output = output(launched)
        val expected = byteArrayOf(12, 34, 56, 78)
        val saved = Bundle()
        original.contentResolver.openOutputStream(uri)!!.use { externalWriter ->
            compose.runOnUiThread {
                originalController.pause().saveInstanceState(saved).stop().destroy()
            }
            compose.waitForIdle()
            assertTrue(original.isDestroyed)
            assertFalse(original.isFinishing)
            assertFalse(original.isChangingConfigurations, "This must be non-finishing, not config-only recreation")
            val disposal = original.disposals.single()
            assertEquals(Lifecycle.State.DESTROYED, disposal.lifecycleState)
            assertFalse(disposal.finishing)
            assertFalse(disposal.changingConfigurations)
            assertTrue(disposal.retainForRestoration)
            assertTrue(output.isFile, "The external writer still owns an open output after destruction")
            externalWriter.write(expected)
        }

        val restored = createActivity(saved).get()
        assertNotSame(original, restored)
        val restoredOwner = assertNotNull(restored.launcher)
        assertNotSame(originalOwner, restoredOwner)
        compose.runOnIdle { restored.resultCallback = callbackA }
        awaitCallback(restored, callbackA)
        compose.runOnIdle { restored.resultCallback = callbackB }
        awaitCallback(restored, callbackB)
        assertSame(restoredOwner, restored.launcher, "A callback update must not replace the saved request owner")
        assertTrue(output.isFile)
        assertTrue(callbackAResults.isEmpty())
        assertTrue(callbackBResults.isEmpty())
        compose.runOnIdle { originalOwner.launch() }
        assertNull(shadowOf(original).nextStartedActivityForResult, "A disposed owner cannot launch another camera")
        assertNull(shadowOf(restored).nextStartedActivityForResult, "Restoration/callback swap must not relaunch")

        // The synthetic writer is closed before actual registry success delivery.
        deliver(restored, launched, Activity.RESULT_OK)
        val captured = assertIs<CameraPickerResult.Captured>(callbackBResults.single())
        assertEquals(uri, captured.file.uri)
        assertContentEquals(expected, output.readBytes())
        restored.contentResolver.openInputStream(captured.file.uri)!!.use {
            assertContentEquals(expected, it.readBytes())
        }
        deliver(restored, launched, Activity.RESULT_OK) // Duplicate host registry delivery; no device/native claim.
        assertEquals(1, callbackBResults.size, "Exactly one terminal result goes to the current callback")
        assertTrue(callbackAResults.isEmpty(), "Neither the destroyed nor replaced callback receives a result")
        assertTrue(original.results.isEmpty(), "The old fixture's default callback remains silent")
        assertTrue(restored.results.isEmpty(), "The restored fixture's replaced default callback remains silent")
        assertNull(shadowOf(restored).nextStartedActivityForResult)
    }

    @Test fun nonFinishingRestorationThenCallbackSwapCancelsOnlyOwnedOutputAndSuppressesOldCallbacks() {
        val callbackAResults = mutableListOf<CameraPickerResult>()
        val callbackBResults = mutableListOf<CameraPickerResult>()
        val callbackA: (CameraPickerResult) -> Unit = { callbackAResults += it }
        val callbackB: (CameraPickerResult) -> Unit = { callbackBResults += it }
        val originalController = createActivity()
        val original = originalController.get()
        val originalOwner = assertNotNull(original.launcher)
        compose.runOnIdle { original.resultCallback = callbackA }
        awaitCallback(original, callbackA)
        assertSame(originalOwner, original.launcher)
        val launched = launch(original)
        val uri = launchUri(launched)
        val output = output(launched)
        val unrelatedBytes = byteArrayOf(9, 7, 5, 3)
        val unrelated = File.createTempFile("capture-unrelated-", ".jpg", assertNotNull(output.parentFile)).also {
            outputs += it // Register exact teardown ownership before the first write/assertion can fail.
            it.writeBytes(unrelatedBytes)
        }
        assertNotEquals(output.canonicalFile, unrelated.canonicalFile)
        val saved = Bundle()
        original.contentResolver.openOutputStream(uri)!!.use { externalWriter ->
            compose.runOnUiThread {
                originalController.pause().saveInstanceState(saved).stop().destroy()
            }
            compose.waitForIdle()
            assertTrue(original.isDestroyed)
            assertFalse(original.isFinishing)
            assertFalse(original.isChangingConfigurations, "This must be non-finishing, not config-only recreation")
            val disposal = original.disposals.single()
            assertEquals(Lifecycle.State.DESTROYED, disposal.lifecycleState)
            assertFalse(disposal.finishing)
            assertFalse(disposal.changingConfigurations)
            assertTrue(disposal.retainForRestoration)
            assertTrue(output.isFile, "Unregister cannot unlink an output with an external writer")
            externalWriter.write(byteArrayOf(1, 2, 3, 4))
        }

        val restored = createActivity(saved).get()
        assertNotSame(original, restored)
        val restoredOwner = assertNotNull(restored.launcher)
        assertNotSame(originalOwner, restoredOwner)
        compose.runOnIdle { restored.resultCallback = callbackA }
        awaitCallback(restored, callbackA)
        compose.runOnIdle { restored.resultCallback = callbackB }
        awaitCallback(restored, callbackB)
        assertSame(restoredOwner, restored.launcher, "A callback update must not replace the saved request owner")
        assertTrue(output.isFile, "The restored pending output remains until terminal cancellation")
        assertTrue(callbackAResults.isEmpty())
        assertTrue(callbackBResults.isEmpty())
        compose.runOnIdle { originalOwner.launch() }
        assertNull(shadowOf(original).nextStartedActivityForResult, "A disposed owner cannot launch another camera")
        assertNull(shadowOf(restored).nextStartedActivityForResult, "Restoration/callback swap must not relaunch")

        // The synthetic writer is closed before actual registry cancellation delivery.
        deliver(restored, launched, Activity.RESULT_CANCELED)
        assertEquals(CameraPickerResult.Cancelled, callbackBResults.single())
        assertFalse(output.exists(), "A terminal cancellation deletes only the saved pending output")
        assertContentEquals(unrelatedBytes, unrelated.readBytes(), "An unrelated owned-pattern sibling must survive")
        deliver(restored, launched, Activity.RESULT_CANCELED) // Duplicate host registry delivery; no device/native claim.
        assertEquals(1, callbackBResults.size, "A duplicate result cannot call the current callback twice")
        assertTrue(callbackAResults.isEmpty(), "Neither the destroyed nor replaced callback receives cancellation")
        assertTrue(original.results.isEmpty(), "The old fixture's default callback remains silent")
        assertTrue(restored.results.isEmpty(), "The restored fixture's replaced default callback remains silent")
        assertFalse(output.exists())
        assertContentEquals(unrelatedBytes, unrelated.readBytes())
        assertNull(shadowOf(restored).nextStartedActivityForResult)
    }

    private fun createActivity(saved: Bundle? = null): ActivityController<CameraLifecycleTestActivity> {
        val app = RuntimeEnvironment.getApplication()
        shadowOf(app.packageManager)
            .setSystemFeature(PackageManager.FEATURE_CAMERA_ANY, true)
        installCameraHostFileProvider(app, "${app.packageName}.provider")
        val controller = Robolectric.buildActivity(CameraLifecycleTestActivity::class.java)
        controllers += controller
        compose.runOnUiThread { if (saved == null) controller.setup() else controller.setup(saved) }
        awaitComposition(controller.get())
        return controller
    }

    private fun awaitComposition(activity: CameraLifecycleTestActivity) {
        // A state write also needs Robolectric's paused framework looper drained. Advancing
        // only the Compose test clock in waitUntil cannot replace this post-mutation idle.
        compose.waitForIdle()
        compose.waitUntil(timeoutMillis = 5_000) { compose.runOnUiThread { activity.launcher != null } }
        compose.waitForIdle()
    }

    private fun awaitCallback(activity: CameraLifecycleTestActivity, callback: (CameraPickerResult) -> Unit) {
        // As for composition readiness, drain Robolectric's paused looper after the state write.
        compose.waitForIdle()
        compose.waitUntil(timeoutMillis = 5_000) {
            compose.runOnUiThread { activity.appliedCallback === callback }
        }
        compose.waitForIdle()
    }

    private fun launch(activity: CameraLifecycleTestActivity): ShadowActivity.IntentForResult {
        compose.runOnIdle { assertNotNull(activity.launcher).launch() }
        val launched = assertNotNull(shadowOf(activity).nextStartedActivityForResult)
        assertEquals(MediaStore.ACTION_IMAGE_CAPTURE, launched.intent.action)
        assertEquals("content", launchUri(launched).scheme) // Private outputs must be grantable on SDK23 too.
        return launched
    }

    private fun launchUri(launched: ShadowActivity.IntentForResult): Uri =
        assertNotNull(launched.intent.getParcelableExtra<Uri>(MediaStore.EXTRA_OUTPUT))

    private fun output(launched: ShadowActivity.IntentForResult): File {
        val app = RuntimeEnvironment.getApplication()
        val name = app.contentResolver.query(launchUri(launched), arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)!!.use {
            assertTrue(it.moveToFirst())
            it.getString(it.getColumnIndexOrThrow(OpenableColumns.DISPLAY_NAME))
        }
        return File(File(app.cacheDir, "nativecmpkit-camera"), name).also {
            outputs += it
            assertTrue(it.exists())
        }
    }

    private fun deliver(activity: CameraLifecycleTestActivity, launched: ShadowActivity.IntentForResult, result: Int) {
        compose.runOnUiThread {
            assertTrue(activity.activityResultRegistry.dispatchResult(launched.requestCode, result, Intent()))
        }
        compose.waitForIdle()
    }
}
