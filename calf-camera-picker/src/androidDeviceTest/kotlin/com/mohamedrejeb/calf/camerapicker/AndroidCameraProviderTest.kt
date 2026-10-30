// SPDX-License-Identifier: Apache-2.0
@file:Suppress("DEPRECATION")
package com.mohamedrejeb.calf.camerapicker

import android.content.ComponentName
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.MediaStore
import androidx.activity.ComponentActivity
import androidx.activity.compose.LocalActivityResultRegistryOwner
import androidx.activity.compose.setContent
import androidx.activity.result.ActivityResultRegistry
import androidx.activity.result.ActivityResultRegistryOwner
import androidx.activity.result.contract.ActivityResultContract
import androidx.compose.runtime.*
import androidx.core.app.ActivityOptionsCompat
import androidx.core.content.FileProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.UUID
import java.util.concurrent.CopyOnWriteArrayList
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.*

/** Minimal public Compose consumer. Only installed recipient selection is redirected. */
class CameraProviderVerificationActivity : ComponentActivity() {
    var options by mutableStateOf(CameraPickerOptions())
    @Volatile var launcher: CameraPickerLauncher? = null
    @Volatile var appliedOptions: CameraPickerOptions? = null
    val results = CopyOnWriteArrayList<CameraPickerResult>()
    @Volatile var outputUri: Uri? = null
    @Volatile var packet: String? = null
    var missingHandler = false
    var cancel = false
    var externalLaunches = 0
    private val platformBridge = object : ActivityResultRegistry() {
        override fun <I, O> onLaunch(requestCode: Int, contract: ActivityResultContract<I, O>, input: I, options: ActivityOptionsCompat?) {
            val intent = contract.createIntent(this@CameraProviderVerificationActivity, input)
            assertEquals(MediaStore.ACTION_IMAGE_CAPTURE, intent.action)
            outputUri = assertNotNull(intent.getParcelableExtra<Uri>(MediaStore.EXTRA_OUTPUT))
            packet = UUID.randomUUID().toString().replace("-", "")
            intent.component = ComponentName(OwnedCameraReceiver.PACKAGE,
                "${OwnedCameraReceiver.PACKAGE}.${if (missingHandler) "NonexistentCameraActivity" else "CameraReceiverActivity"}")
            intent.putExtra("nativecmpkit.packet", packet); intent.putExtra("nativecmpkit.cancel", cancel)
            externalLaunches++
            // No manually added ClipData/URI grants: Android owns EXTRA_OUTPUT grant migration
            // and the real foreign-UID Activity result. A missing component fails in Android.
            startActivityForResult(intent, requestCode, options?.toBundle())
        }
    }
    private val registryOwner = object : ActivityResultRegistryOwner { override val activityResultRegistry = platformBridge }
    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        options = CameraPickerOptions(androidFileProviderAuthority = "$packageName.camera-files")
        setContent {
            CompositionLocalProvider(LocalActivityResultRegistryOwner provides registryOwner) {
                val current = rememberCameraPickerResultLauncher(options, results::add)
                SideEffect { launcher = current; appliedOptions = options }
                DisposableEffect(current) { onDispose { if (launcher === current) launcher = null } }
            }
        }
    }
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        assertTrue(platformBridge.dispatchResult(requestCode, resultCode, data))
    }
}

/**
 * Actual API23/35 Activity/Compose consumer, manifest/path parsing, foreign native UID,
 * system-created grants, ContentResolver output and Android platform no-handler failure.
 * Synthetic output/recipient selection are explicit: no camera/vendor UI, real photo,
 * process-death/restoration, physical device, packaged Maven, API/ABI or release claim.
 */
@RunWith(AndroidJUnit4::class)
class AndroidCameraNativeProviderTest {
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val bytes = "NativeCmpKit synthetic native camera output".encodeToByteArray()

    @Test fun nativeCustomAndLegacyProvidersGrantForeignUidOutputAndRetainExactlyOneSuccess() = owned { activity, receiver ->
        for (authority in listOf("${context.packageName}.camera-files", null)) {
            setOptions(activity, CameraPickerOptions(androidFileProviderAuthority = authority))
            val previous = activity.results.size
            onMain { assertNotNull(activity.launcher).launch() }
            waitUntil { activity.results.size == previous + 1 }
            val captured = assertIs<CameraPickerResult.Captured>(activity.results.last())
            val uri = assertNotNull(activity.outputUri)
            assertEquals("content", uri.scheme)
            assertEquals(authority ?: "${context.packageName}.provider", uri.authority)
            assertEquals(uri, captured.file.uri)
            val report = receiver.received(assertNotNull(activity.packet))
            assertEquals(uri.toString(), report.getString("uri")); assertEquals(MediaStore.ACTION_IMAGE_CAPTURE, report.getString("action"))
            assertTrue(report.getBoolean("readGranted")); assertTrue(report.getBoolean("writeGranted")); assertTrue(report.getBoolean("clipMatches"))
            assertEquals(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION,
                report.getInt("flags") and (Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION))
            assertNull(report.getString("writeError")); assertEquals(1, report.getInt("opens")); assertEquals(1, report.getInt("closes"))
            assertContentEquals(bytes, context.contentResolver.openInputStream(captured.file.uri)!!.use { it.readBytes() })
            instrumentation.waitForIdleSync()
            assertEquals(previous + 1, activity.results.size)
        }
    }

    @Test fun nativeMissingAuthorityWrongRootAndAbsentCameraHandlerFailWithoutOrphanOrDelivery() = owned { activity, receiver ->
        val beforeFiles = outputs(); val beforeIntents = receiver.request("snapshot").getInt("intents")
        for (authority in listOf("${context.packageName}.missing-camera-provider", "${context.packageName}.wrong-camera-root")) {
            setOptions(activity, CameraPickerOptions(androidFileProviderAuthority = authority))
            val count = activity.results.size; val launches = activity.externalLaunches
            onMain { assertNotNull(activity.launcher).launch() }
            waitUntil { activity.results.size == count + 1 }
            assertEquals(CameraFailureReason.Configuration, assertIs<CameraPickerResult.Failed>(activity.results.last()).reason)
            assertEquals(launches, activity.externalLaunches); assertEquals(beforeFiles, outputs())
        }
        setOptions(activity, CameraPickerOptions(androidFileProviderAuthority = "${context.packageName}.camera-files"))
        val count = activity.results.size
        onMain { activity.missingHandler = true; assertNotNull(activity.launcher).launch() }
        waitUntil { activity.results.size == count + 1 }
        assertEquals(CameraFailureReason.Launch, assertIs<CameraPickerResult.Failed>(activity.results.last()).reason)
        assertEquals(1, activity.externalLaunches); assertEquals(beforeFiles, outputs())
        assertEquals(beforeIntents, receiver.request("snapshot").getInt("intents"))
        assertTrue(activity.results.none { it is CameraPickerResult.Captured })
    }

    @Test fun nativeNarrowProviderExcludesSiblingCacheAndCancellationCleansOnlyItsOutput() = owned { activity, receiver ->
        val sibling = File.createTempFile("nativecmpkit-private-", ".txt", context.cacheDir).apply { writeText("unrelated cache bytes") }
        try {
            assertFailsWith<IllegalArgumentException> { FileProvider.getUriForFile(context, "${context.packageName}.camera-files", sibling) }
            val beforeFiles = outputs(); val count = activity.results.size
            onMain { activity.cancel = true; assertNotNull(activity.launcher).launch() }
            waitUntil { activity.results.size == count + 1 }
            assertEquals(CameraPickerResult.Cancelled, activity.results.last())
            val report = receiver.received(assertNotNull(activity.packet))
            assertTrue(report.getBoolean("cancelled")); assertTrue(report.getBoolean("writeGranted")); assertEquals(0, report.getInt("opens"))
            assertEquals(beforeFiles, outputs()); assertEquals("unrelated cache bytes", sibling.readText())
            assertFailsWith<java.io.FileNotFoundException> { context.contentResolver.openInputStream(assertNotNull(activity.outputUri))!!.use { it.read() } }
            assertEquals(count + 1, activity.results.size)
        } finally { assertTrue(sibling.delete()) }
    }

    private fun owned(body: (CameraProviderVerificationActivity, OwnedCameraReceiver) -> Unit) {
        assertEquals("true", InstrumentationRegistry.getArguments().getString("nativecmpkitOwnedCameraReceiver"))
        assertTrue(Build.VERSION.SDK_INT in setOf(23, 35)); assertTrue(Build.HARDWARE in setOf("ranchu", "goldfish"))
        assertTrue(context.packageManager.hasSystemFeature(PackageManager.FEATURE_CAMERA_ANY), "Use the selected real emulated-camera configuration")
        val beforeFiles = outputs()
        val receiver = OwnedCameraReceiver()
        try {
            receiver.connect()
            ActivityScenario.launch(CameraProviderVerificationActivity::class.java).use { scenario ->
                var current: CameraProviderVerificationActivity? = null
                scenario.onActivity { current = it }
                val activity = assertNotNull(current)
                waitUntil { activity.launcher != null }
                body(activity, receiver)
            }
        } finally {
            try { receiver.close() }
            finally { (outputs() - beforeFiles).forEach { assertTrue(File(it).delete()) } }
        }
    }
    private fun outputs(): Set<String> = File(context.cacheDir, "nativecmpkit-camera").listFiles()?.map { it.canonicalPath }?.toSet() ?: emptySet()
    private fun setOptions(activity: CameraProviderVerificationActivity, options: CameraPickerOptions) {
        onMain { activity.options = options }
        waitUntil { activity.appliedOptions == options }
        instrumentation.waitForIdleSync()
    }
    private fun waitUntil(predicate: () -> Boolean) {
        val start = System.nanoTime()
        while (!predicate()) { check(System.nanoTime() - start < 20_000_000_000L) { "Actual camera provider native result timed out" }; Thread.sleep(20) }
    }
    private fun <T> onMain(action: () -> T): T {
        var result: Result<T>? = null
        instrumentation.runOnMainSync { result = runCatching(action) }
        return checkNotNull(result).getOrThrow()
    }
}
