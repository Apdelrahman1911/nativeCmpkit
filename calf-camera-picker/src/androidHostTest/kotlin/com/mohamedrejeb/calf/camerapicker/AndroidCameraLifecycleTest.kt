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
    val disposals = mutableListOf<CameraDisposalObservation>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            CompositionLocalProvider(LocalContext provides if (useWrappedContext) wrappedContext else this) {
                if (showPicker) {
                    val current = rememberCameraPickerResultLauncher { results += it }
                    SideEffect { launcher = current }
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
