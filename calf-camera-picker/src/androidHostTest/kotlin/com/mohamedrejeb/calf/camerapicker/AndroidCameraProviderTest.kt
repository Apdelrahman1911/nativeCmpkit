package com.mohamedrejeb.calf.camerapicker

import android.app.Application
import android.content.ActivityNotFoundException
import android.content.pm.PackageManager
import android.net.Uri
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContract
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.app.ActivityOptionsCompat
import androidx.core.content.FileProvider
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config
import java.io.File
import java.util.UUID
import kotlin.test.*

/** Real provider XML, resolver, cache bytes and owning launcher; the camera boundary is driven. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [23])
class AndroidCameraProviderTest {
    private val app: Application get() = RuntimeEnvironment.getApplication()
    private val authority = "nativecmpkit.camera.host.${UUID.randomUUID().toString().replace("-", "") }"
    private class Driver(val action: (Uri) -> Unit = {}) : ActivityResultLauncher<Uri>() {
        val uris = mutableListOf<Uri>()
        override fun launch(input: Uri, options: ActivityOptionsCompat?) { uris += input; action(input) }
        override fun unregister() = Unit
        override val contract: ActivityResultContract<Uri, *> = ActivityResultContracts.TakePicture()
    }
    private fun owner(state: CameraRequestState, driver: Driver, results: MutableList<CameraPickerResult>) =
        CameraPickerLauncherAndroidImpl(app, driver, state, { CameraPickerOptions(androidFileProviderAuthority = authority) }, results::add)
    private fun cameraAvailable() { shadowOf(app.packageManager).setSystemFeature(PackageManager.FEATURE_CAMERA_ANY, true) }
    private fun outputs() = File(app.cacheDir, "nativecmpkit-camera").listFiles()?.map { it.canonicalPath }?.toSet() ?: emptySet()

    @Test fun api23ConfiguredProviderUsesContentUriAndResolverBytesSurviveSuccess() {
        cameraAvailable(); installCameraHostFileProvider(app, authority)
        val state = CameraRequestState(); val driver = Driver(); val results = mutableListOf<CameraPickerResult>()
        val owner = owner(state, driver, results)
        owner.launch()
        val pending = assertNotNull(state.pending)
        try {
            val uri = driver.uris.single()
            assertEquals("content", uri.scheme, "Private cache file URIs are not grantable to the external camera UID")
            assertEquals(authority, uri.authority)
            app.contentResolver.openOutputStream(uri)!!.use { it.write(byteArrayOf(5, 4, 3, 2)) }
            owner.handleResult(true); owner.handleResult(true)
            val captured = assertIs<CameraPickerResult.Captured>(results.single())
            assertEquals(uri, captured.file.uri)
            assertContentEquals(byteArrayOf(5, 4, 3, 2), app.contentResolver.openInputStream(captured.file.uri)!!.use { it.readBytes() })
            assertNull(state.pending)
            assertTrue(File(pending.ownedPath).exists(), "Success transfers ownership rather than deleting the file")
        } finally { owner.dispose(false); File(pending.ownedPath).delete() }
    }

    @Test @Config(sdk = [34]) fun api24PlusConfiguredProviderUsesContentUriAndResolverBytesSurviveSuccess() =
        api23ConfiguredProviderUsesContentUriAndResolverBytesSurviveSuccess()

    @Test fun api23MissingProviderReturnsConfigurationAndLeavesNoOrphanOrLaunch() {
        cameraAvailable()
        assertConfigurationFailureWithNoOutput()
    }

    @Test @Config(sdk = [34]) fun api24PlusMissingProviderReturnsConfigurationAndLeavesNoOrphanOrLaunch() =
        api23MissingProviderReturnsConfigurationAndLeavesNoOrphanOrLaunch()

    @Test fun api23WrongProviderPathReturnsConfigurationAndDoesNotDeleteUnrelatedCache() {
        cameraAvailable(); installCameraHostFileProvider(app, authority, "nativecmpkit_camera_wrong_paths")
        val unrelated = File.createTempFile("unrelated-", ".txt", app.cacheDir).apply { writeText("preserve me") }
        try { assertConfigurationFailureWithNoOutput(); assertEquals("preserve me", unrelated.readText()) }
        finally { unrelated.delete() }
    }

    @Test @Config(sdk = [34]) fun api24PlusWrongProviderPathReturnsConfigurationAndDoesNotDeleteUnrelatedCache() =
        api23WrongProviderPathReturnsConfigurationAndDoesNotDeleteUnrelatedCache()

    @Test fun recommendedProviderCannotGrantSiblingCacheFilesAndCancellationCleansOnlyItsOutput() {
        cameraAvailable(); installCameraHostFileProvider(app, authority)
        val sibling = File.createTempFile("private-", ".txt", app.cacheDir).apply { writeText("not a photo") }
        val state = CameraRequestState(); val driver = Driver(); val results = mutableListOf<CameraPickerResult>()
        val owner = owner(state, driver, results)
        try {
            assertFailsWith<IllegalArgumentException> { FileProvider.getUriForFile(app, authority, sibling) }
            owner.launch()
            val pending = assertNotNull(state.pending)
            assertEquals("content", driver.uris.single().scheme)
            owner.handleResult(false); owner.handleResult(false)
            assertEquals(CameraPickerResult.Cancelled, results.single())
            assertFalse(File(pending.ownedPath).exists())
            assertEquals("not a photo", sibling.readText())
        } finally { owner.dispose(false); sibling.delete() }
    }

    @Test fun missingCameraIntentHandlerIsOneLaunchFailureAndCleansOnlyNewOutput() {
        cameraAvailable(); installCameraHostFileProvider(app, authority)
        val before = outputs(); val state = CameraRequestState(); val results = mutableListOf<CameraPickerResult>()
        val driver = Driver { throw ActivityNotFoundException("Controlled host has no external camera handler") }
        owner(state, driver, results).launch()
        assertEquals(CameraFailureReason.Launch, assertIs<CameraPickerResult.Failed>(results.single()).reason)
        assertEquals(1, driver.uris.size); assertNull(state.pending); assertEquals(before, outputs())
    }

    private fun assertConfigurationFailureWithNoOutput() {
        val before = outputs(); val state = CameraRequestState(); val driver = Driver(); val results = mutableListOf<CameraPickerResult>()
        owner(state, driver, results).launch()
        assertEquals(1, results.size, "Invalid provider setup must report one failure instead of starting the external camera")
        assertEquals(CameraFailureReason.Configuration, assertIs<CameraPickerResult.Failed>(results.single()).reason)
        assertNull(state.pending); assertTrue(driver.uris.isEmpty()); assertEquals(before, outputs())
    }
}
