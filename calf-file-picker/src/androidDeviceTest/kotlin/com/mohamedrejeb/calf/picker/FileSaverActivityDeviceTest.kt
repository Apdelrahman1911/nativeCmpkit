package com.mohamedrejeb.calf.picker

import android.app.Instrumentation
import android.content.Intent
import android.net.Uri
import android.os.SystemClock
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import androidx.test.platform.app.InstrumentationRegistry
import com.mohamedrejeb.calf.core.ExperimentalCalfApi
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.picker.instrumentation.SaveDestinationActivity
import com.mohamedrejeb.calf.picker.instrumentation.SaverDeviceContent
import com.mohamedrejeb.calf.picker.instrumentation.SaverHostActivity
import java.util.concurrent.CopyOnWriteArrayList
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNotNull
import kotlin.test.assertNotSame
import kotlin.test.assertNull
import kotlin.test.assertTrue

/**
 * Public composable/launcher -> actual ComponentActivity registry -> actual child Activity result
 * -> real ContentResolver/descriptor integration. Only destination UI selection is deterministic.
 * API26 is needed for the non-blocking ActivityMonitor routing hook, not by the library itself.
 */
@OptIn(ExperimentalCalfApi::class)
@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 26)
class FileSaverActivityDeviceTest {
    @get:Rule val compose = createAndroidComposeRule<SaverHostActivity>()
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private lateinit var fixture: DeviceSaveFixture
    private lateinit var route: SaveActivityRoute
    private lateinit var activityMonitor: Instrumentation.ActivityMonitor
    private var destinationActivity: SaveDestinationActivity? = null
    private lateinit var launcher: FileSaverLauncher
    private val outcomes = CopyOnWriteArrayList<Outcome>()

    @Before fun setUp() {
        fixture = DeviceSaveFixture()
        route = SaveActivityRoute(fixture.context.packageName)
        instrumentation.addMonitor(route)
        compose.runOnIdle {
            SaverDeviceContent.body = {
                launcher = rememberFileSaverLauncher(
                    onError = { outcomes += Outcome.Failed(it) },
                    onResult = { outcomes += Outcome.Returned(it) },
                )
            }
        }
        compose.waitForIdle()
    }

    @After fun tearDown() {
        instrumentation.runOnMainSync {
            destinationActivity?.takeUnless { it.isFinishing || it.isDestroyed }?.complete(null)
            SaverDeviceContent.body = { }
        }
        if (::activityMonitor.isInitialized) instrumentation.removeMonitor(activityMonitor)
        if (::route.isInitialized) instrumentation.removeMonitor(route)
        instrumentation.waitForIdleSync()
        if (::fixture.isInitialized) fixture.close()
    }

    @Test fun byteRequestSurvivesAnActualActivityResultRoundTrip() {
        val bytes = ByteArray(131_079) { (it % 251).toByte() }
        val (destination, uri) = fixture.createDocument("Report.bin")
        val child = launchAndAwait { launch(bytes, "Report", "bin") }
        val intent = route.intents.single()
        assertEquals(Intent.ACTION_CREATE_DOCUMENT, intent.action)
        assertEquals("Report.bin", intent.getStringExtra(Intent.EXTRA_TITLE))
        assertEquals("application/octet-stream", intent.type)
        val defaultIntent = ActivityResultContracts.CreateDocument("application/octet-stream")
            .createIntent(fixture.context, "Report.bin")
        assertEquals(defaultIntent.categories, intent.categories)
        complete(child, uri)
        awaitOutcomes(1)

        assertEquals(uri, assertIs<Outcome.Returned>(outcomes.single()).file?.uri)
        assertContentEquals(bytes, destination.readBytes())
        fixture.assertClosed(uri, reads = 0, writes = 1)
        assertNoDeviceFileDescriptors(destination)
    }

    @Test fun publicFileOverloadStreamsFromARealFileProviderWithoutMovingTheSource() {
        val bytes = ByteArray(65_537) { it.toByte() }
        val source = fixture.file("original.bin", bytes)
        val (destination, uri) = fixture.createDocument("Copy.bin")
        val child = launchAndAwait { launch(KmpFile(fixture.fileProviderUri(source)), "Copy", "bin") }
        complete(child, uri)
        awaitOutcomes(1)

        assertEquals(uri, assertIs<Outcome.Returned>(outcomes.single()).file?.uri)
        assertContentEquals(bytes, source.readBytes())
        assertContentEquals(bytes, destination.readBytes())
        fixture.assertClosed(uri, reads = 0, writes = 1)
        assertNoDeviceFileDescriptors(source)
        assertNoDeviceFileDescriptors(destination)
    }

    @Test fun nullBytesDeliberatelyProduceARealEmptyDocument() {
        val (destination, uri) = fixture.createDocument("Empty.bin")
        val child = launchAndAwait { launch(bytes = null, baseName = "Empty", extension = "bin") }
        complete(child, uri)
        awaitOutcomes(1)

        assertEquals(uri, assertIs<Outcome.Returned>(outcomes.single()).file?.uri)
        assertTrue(destination.isFile)
        assertEquals(0L, destination.length())
        fixture.assertClosed(uri, reads = 0, writes = 1)
        assertNoDeviceFileDescriptors(destination)
    }

    @Test fun frameworkCancellationDeliversOneNullResultAndReleasesTheNextLaunch() {
        val first = launchAndAwait { launch(byteArrayOf(1), "Cancel", "bin") }
        complete(first, null)
        awaitOutcomes(1)
        assertNull(assertIs<Outcome.Returned>(outcomes.single()).file)

        val (destination, uri) = fixture.createDocument("Next.bin")
        val next = launchAndAwait { launch(byteArrayOf(9, 8), "Next", "bin") }
        complete(next, uri)
        awaitOutcomes(2)
        assertEquals(2, outcomes.size)
        assertEquals(uri, assertIs<Outcome.Returned>(outcomes.last()).file?.uri)
        assertEquals(2, route.intents.size)
        assertContentEquals(byteArrayOf(9, 8), destination.readBytes())
        fixture.assertClosed(uri, reads = 0, writes = 1)
    }

    @Test fun overlapReportsOneErrorWithoutReplacingTheAcceptedNativeRequest() {
        val firstBytes = byteArrayOf(1, 0, -1, 4)
        val (destination, uri) = fixture.createDocument("First.bin")
        val first = launchAndAwait { launch(firstBytes, "First", "bin") }
        // Invoke on the actual UI thread while the real child Activity owns the foreground.
        instrumentation.runOnMainSync { launcher.launch(byteArrayOf(99), "Second", "bin") }
        waitForSystemCondition { outcomes.size == 1 }
        assertIs<Outcome.Failed>(outcomes.single())
        assertEquals(1, route.intents.size, "a rejected overlap must not launch another Activity")
        complete(first, uri)
        awaitOutcomes(2)

        assertEquals(2, outcomes.size)
        assertEquals(uri, assertIs<Outcome.Returned>(outcomes.last()).file?.uri)
        assertContentEquals(firstBytes, destination.readBytes())
        fixture.assertClosed(uri, reads = 0, writes = 1)
    }

    @Test fun originalReturnedUnderATreeAliasIsNeverOpenedForWriteOrDeleted() {
        val bytes = byteArrayOf(4, 0, -1, 9)
        val source = fixture.file("self.bin", bytes)
        val original = fixture.treeDocumentUri(source)
        val destination = fixture.documentUri(source)
        val child = launchAndAwait { launch(KmpFile(original), "self", "bin") }
        complete(child, destination)
        awaitOutcomes(1)

        assertEquals(destination, assertIs<Outcome.Returned>(outcomes.single()).file?.uri)
        assertContentEquals(bytes, source.readBytes())
        fixture.assertClosed(destination, reads = 1, writes = 0)
        assertEquals(0, fixture.stats(destination).getInt("writeAttempts"))
        assertEquals(0, fixture.stats(destination).getInt("deletes"))
        assertNoDeviceFileDescriptors(source)
    }

    @Test fun uriPayloadSurvivesActualHostActivityRecreationBeforeTheResult() {
        val bytes = byteArrayOf(5, 0, -1, 1)
        val source = fixture.file("restored-source.bin", bytes)
        val (destination, uri) = fixture.createDocument("Restored.bin")
        val child = launchAndAwait { launch(KmpFile(fixture.fileProviderUri(source)), "Restored", "bin") }
        recreateHostBelowTheChild()
        complete(child, uri)
        awaitOutcomes(1)

        assertEquals(uri, assertIs<Outcome.Returned>(outcomes.single()).file?.uri)
        assertContentEquals(bytes, source.readBytes())
        assertContentEquals(bytes, destination.readBytes())
        fixture.assertClosed(uri, reads = 0, writes = 1)
        assertNoDeviceFileDescriptors(source)
        assertNoDeviceFileDescriptors(destination)
    }

    @Test fun lostBytePayloadAfterActualRecreationIsAnErrorNotEmptySuccess() {
        val (destination, uri) = fixture.createDocument("Lost.bin")
        val child = launchAndAwait { launch(byteArrayOf(1, 2, 3), "Lost", "bin") }
        recreateHostBelowTheChild()
        complete(child, uri)
        awaitOutcomes(1)

        val failure = assertIs<Outcome.Failed>(outcomes.single())
        assertNotNull(failure.error.cause)
        assertFalse(destination.exists(), "failure must clean only the newly created document")
        assertEquals(0, fixture.stats(uri).getInt("writeAttempts"))
        assertEquals(1, fixture.stats(uri).getInt("deletes"))
    }

    private fun launchAndAwait(launch: FileSaverLauncher.() -> Unit): SaveDestinationActivity {
        // Creation and resume can both match; never reuse a prior launch's observation state.
        val monitor = instrumentation.addMonitor(SaveDestinationActivity::class.java.name, null, false)
        activityMonitor = monitor
        return try {
            compose.runOnIdle { launcher.launch() }
            val activity = monitor.waitForActivityWithTimeout(TIMEOUT_MS)
            assertIs<SaveDestinationActivity>(activity).also {
                destinationActivity = it
                assertFalse(it.isFinishing)
            }
        } finally {
            instrumentation.removeMonitor(monitor)
        }
    }

    private fun complete(activity: SaveDestinationActivity, uri: Uri?) {
        instrumentation.runOnMainSync { activity.complete(uri) }
        destinationActivity = null
    }

    private fun recreateHostBelowTheChild() {
        val before = assertNotNull(SaverHostActivity.latest.get())
        val count = SaverHostActivity.creations.get()
        instrumentation.runOnMainSync { before.recreate() }
        // ActivityScenario.recreate() waits for RESUMED and would deadlock behind the child.
        waitForSystemCondition { SaverHostActivity.creations.get() > count }
        assertNotSame(before, assertNotNull(SaverHostActivity.latest.get()))
    }

    private fun awaitOutcomes(count: Int) {
        waitForSystemCondition { outcomes.size >= count }
        compose.waitForIdle()
        assertEquals(count, outcomes.size, "an actual Activity result must not deliver two library outcomes")
    }

    private fun waitForSystemCondition(condition: () -> Boolean) {
        val deadline = SystemClock.elapsedRealtime() + TIMEOUT_MS
        while (!condition() && SystemClock.elapsedRealtime() < deadline) SystemClock.sleep(10)
        assertTrue(condition(), "Timed out waiting for a real Android lifecycle/result transition")
    }

    private sealed interface Outcome {
        class Returned(val file: KmpFile?) : Outcome
        class Failed(val error: FilePickerException) : Outcome
    }

    /**
     * A non-blocking monitor changes only the chosen Activity component. It returns null, so
     * Android really launches an Activity and delivers its result through the production registry.
     * It never returns a synthetic Instrumentation.ActivityResult or calls dispatchResult.
     */
    private class SaveActivityRoute(private val packageName: String) : Instrumentation.ActivityMonitor() {
        val intents = CopyOnWriteArrayList<Intent>()
        override fun onStartActivity(intent: Intent): Instrumentation.ActivityResult? {
            if (intent.action == Intent.ACTION_CREATE_DOCUMENT) {
                intents += Intent(intent)
                intent.setClassName(packageName, SaveDestinationActivity::class.java.name)
            }
            return null
        }
    }

    companion object { private const val TIMEOUT_MS = 30_000L }
}
