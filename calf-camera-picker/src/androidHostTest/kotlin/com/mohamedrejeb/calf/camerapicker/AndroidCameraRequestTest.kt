package com.mohamedrejeb.calf.camerapicker

import android.app.Application
import android.content.pm.PackageManager
import android.net.Uri
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContract
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.saveable.SaverScope
import androidx.core.app.ActivityOptionsCompat
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config
import java.io.File
import kotlin.test.*

/** Real library code, Android host services and cache files, with an external-camera result driver.
 * This does not claim the system camera, process recreation, or grant delivery was device-tested. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [23])
class AndroidCameraRequestTest {
    private class ResultDriver(private val onLaunch: (Uri) -> Unit = {}) : ActivityResultLauncher<Uri>() {
        val launched = mutableListOf<Uri>()
        override fun launch(input: Uri, options: ActivityOptionsCompat?) { launched += input; onLaunch(input) }
        override fun unregister() = Unit
        override val contract: ActivityResultContract<Uri, *> = ActivityResultContracts.TakePicture()
    }
    private val application: Application get() = RuntimeEnvironment.getApplication()
    private fun cameraAvailable(installProvider: Boolean = true) {
        shadowOf(application.packageManager).setSystemFeature(PackageManager.FEATURE_CAMERA_ANY, true)
        if (installProvider) installCameraHostFileProvider(application, "${application.packageName}.provider")
    }
    private fun owner(state: CameraRequestState, driver: ResultDriver, callback: (CameraPickerResult) -> Unit) =
        CameraPickerLauncherAndroidImpl(application, driver, state, { CameraPickerOptions() }, callback)

    @Test fun restoredSuccessUsesSavedUriAndIsDeliveredOnceToNewOwner() {
        cameraAvailable()
        val state = CameraRequestState()
        val oldResults = mutableListOf<CameraPickerResult>()
        val old = owner(state, ResultDriver(), oldResults::add)
        old.launch()
        val pending = state.pending!!
        File(pending.ownedPath).writeBytes(byteArrayOf(1, 2, 3))
        val saver = CameraRequestState.Saver
        val scope = object : SaverScope { override fun canBeSaved(value: Any) = true }
        val saved = with(saver) { scope.save(state) }!!
        old.dispose(retainPendingForSuccessor = true)
        val restored = saver.restore(saved)!!
        val results = mutableListOf<CameraPickerResult>()
        val replacement = owner(restored, ResultDriver(), results::add)
        replacement.handleResult(true)
        replacement.handleResult(true)
        assertTrue(oldResults.isEmpty())
        assertEquals(pending.uri, (results.single() as CameraPickerResult.Captured).file.uri.toString())
        assertNull(restored.pending)
        assertTrue(File(pending.ownedPath).exists(), "Successful output must survive callback delivery")
        File(pending.ownedPath).delete()
        replacement.dispose(false)
    }

    @Test fun busyDoesNotOverwriteRequestAndCancelDeletesOnlyItsOutput() {
        cameraAvailable()
        val state = CameraRequestState()
        val driver = ResultDriver()
        val results = mutableListOf<CameraPickerResult>()
        val owner = owner(state, driver, results::add)
        owner.launch()
        val pending = state.pending!!
        owner.launch()
        assertSame(pending, state.pending)
        assertEquals(CameraPickerResult.Busy, results.single())
        assertEquals(1, driver.launched.size)
        owner.handleResult(false)
        assertEquals(CameraPickerResult.Cancelled, results.last())
        assertFalse(File(pending.ownedPath).exists())
        owner.dispose(false)
    }

    @Test fun cancellationCannotDeleteArbitrarySavedPath() {
        val unrelated = File.createTempFile("unrelated-", ".jpg", application.cacheDir)
        try {
            val state = CameraRequestState(PendingCameraCapture(Uri.fromFile(unrelated).toString(), unrelated.absolutePath))
            owner(state, ResultDriver()) {}.handleResult(false)
            assertTrue(unrelated.exists())
        } finally { unrelated.delete() }
    }

    @Test @Config(sdk = [34]) fun missingFileProviderIsAConfigurationFailureNotACrash() {
        cameraAvailable(installProvider = false)
        val results = mutableListOf<CameraPickerResult>()
        val state = CameraRequestState()
        val driver = ResultDriver()
        owner(state, driver, results::add).launch()
        assertEquals(CameraFailureReason.Configuration, assertIs<CameraPickerResult.Failed>(results.single()).reason)
        assertNull(state.pending)
        assertTrue(driver.launched.isEmpty())
    }

    @Test fun callbackFailureCannotBeRemappedOrDeliveredTwice() {
        cameraAvailable()
        val state = CameraRequestState()
        var calls = 0
        val owner = owner(state, ResultDriver()) { calls++; error("application callback") }
        owner.launch()
        assertFailsWith<IllegalStateException> { owner.handleResult(false) }
        owner.handleResult(false)
        assertEquals(1, calls)
        assertNull(state.pending)
    }

    @Test fun synchronousReentrantCallbackFailureCannotClearTheNextRequestOrDeleteSuccess() {
        cameraAvailable()
        val state = CameraRequestState()
        val results = mutableListOf<CameraPickerResult>()
        val expected = IllegalStateException("application callback after launching the next capture")
        lateinit var owner: CameraPickerLauncherAndroidImpl
        var firstFile: File? = null
        var nextRequest: PendingCameraCapture? = null
        val driver = ResultDriver { uri ->
            if (firstFile == null) {
                firstFile = File(assertNotNull(state.pending).ownedPath)
                assertEquals("content", uri.scheme)
                application.contentResolver.openOutputStream(uri)!!.use { it.write(byteArrayOf(9, 8, 7)) }
                owner.handleResult(true) // Explicitly synchronous custom-registry behavior.
            }
        }
        owner = owner(state, driver) { result ->
            results += result
            if (result is CameraPickerResult.Captured) {
                owner.launch()
                nextRequest = state.pending
                throw expected
            }
        }
        try {
            assertSame(expected, assertFailsWith<IllegalStateException> { owner.launch() })
            assertIs<CameraPickerResult.Captured>(results.single())
            assertEquals(2, driver.launched.size)
            assertNotNull(nextRequest)
            assertSame(nextRequest, state.pending, "The old launch must not consume the replacement request")
            assertContentEquals(byteArrayOf(9, 8, 7), assertNotNull(firstFile).readBytes())
            owner.handleResult(false)
            assertEquals(CameraPickerResult.Cancelled, results.last())
            assertEquals(2, results.size, "No reclassified failure callback may be emitted")
            assertFalse(File(assertNotNull(nextRequest).ownedPath).exists())
            assertTrue(assertNotNull(firstFile).exists(), "Successful output is caller-owned")
        } finally {
            owner.dispose(false)
            firstFile?.delete()
            nextRequest?.let { File(it.ownedPath).delete() }
        }
    }
}
