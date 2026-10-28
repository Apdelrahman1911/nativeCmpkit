package com.mohamedrejeb.calf.picker

import android.content.ContentProvider
import android.content.ContentValues
import android.content.pm.ProviderInfo
import android.content.res.AssetFileDescriptor
import android.database.Cursor
import android.net.Uri
import android.os.Bundle
import android.os.Looper
import android.provider.DocumentsContract
import androidx.activity.compose.LocalActivityResultRegistryOwner
import androidx.activity.result.ActivityResultRegistryOwner
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.test.junit4.v2.createComposeRule
import com.mohamedrejeb.calf.core.ExperimentalCalfApi
import com.mohamedrejeb.calf.io.KmpFile
import java.io.File
import java.io.FileNotFoundException
import java.io.FileOutputStream
import java.io.IOException
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config
import org.robolectric.shadows.ShadowContentResolver
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertTrue

/**
 * Public Compose saver -> real host ActivityResult registry -> production coroutine writer.
 * The result registry and resolver stream registration are controlled host boundaries, not a
 * real documents UI, Android kernel/grant, full-filesystem or process-death certification.
 */
@OptIn(ExperimentalCalfApi::class)
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class SaveTerminalEventAcceptanceTest {
    // v1's UnconfinedTestDispatcher resumes an IO handoff on the worker itself.
    // Use the current queued test dispatcher; retain the actual Main-looper assertions.
    @get:Rule val compose = createComposeRule()
    @get:Rule val folder = TemporaryFolder()
    private val registry = RecordingActivityResultRegistry()
    private val generation = mutableIntStateOf(0)
    private val mounted = mutableStateOf(true)
    private val outcomes = CopyOnWriteArrayList<Outcome>()
    private lateinit var launcher: FileSaverLauncher

    @Test fun successIsOneLatestCallbackEvenWithDuplicateResultsDuringAndAfterWriting() {
        val provider = provider()
        val output = BlockingFileOutput(provider.destination)
        shadowOf(resolver).registerOutputStream(provider.uri, output)
        mount()
        try {
            launchAndReplaceCallbacks()
            dispatch(provider.uri)
            assertTrue(output.entered.await(10, TimeUnit.SECONDS), "The real production IO copy must reach the owned stream")
            dispatch(provider.uri)
            dispatch(null)
            assertTrue(outcomes.isEmpty(), "No success precedes write/close and no duplicate cancels the owned copy")
            output.release.countDown()
            awaitOutcomes(1)
            dispatch(provider.uri)
            dispatch(null)

            val returned = assertIs<Outcome.Returned>(outcomes.single())
            assertEquals(1, returned.generation)
            assertEquals(provider.uri, returned.file?.uri)
            assertContentEquals(CONTENT, provider.destination.readBytes())
            assertEquals(1, output.writes.get())
            assertEquals(1, output.closes.get())
            assertEquals(0, provider.deletes.get())
            assertContentEquals(CONTENT, provider.source.readBytes())
        } finally { output.release.countDown(); output.closeIfNeeded() }
    }

    @Test fun userCancellationIsOneNullResultNotAnErrorDespiteDuplicateResults() {
        val provider = provider()
        mount()
        launchAndReplaceCallbacks()
        dispatch(null)
        awaitOutcomes(1)
        dispatch(null)
        dispatch(provider.uri)

        val returned = assertIs<Outcome.Returned>(outcomes.single())
        assertEquals(1, returned.generation)
        assertNull(returned.file)
        assertTrue(provider.openModes.isEmpty())
        assertEquals(0, provider.deletes.get(), "Cancellation with no returned destination transfers no cleanup ownership")
    }

    @Test fun nullWriteIsOneLatestErrorNeverAResultAndCleansOnlyTheNewDocument() {
        val provider = provider()
        mount()
        launchAndReplaceCallbacks()
        dispatch(provider.uri)
        awaitOutcomes(1)
        dispatch(provider.uri)
        dispatch(null)

        val failed = assertIs<Outcome.Failed>(outcomes.single())
        assertEquals(1, failed.generation)
        assertIs<FileNotFoundException>(failed.error.cause)
        assertEquals(listOf("wt"), provider.openModes.toList())
        assertEquals(1, provider.deletes.get())
        assertFalse(provider.destination.exists())
        assertContentEquals(CONTENT, provider.source.readBytes())
    }

    @Test fun legacyWriteFailureMapsToOneNullResultWithoutADuplicateTerminalEvent() {
        val provider = provider()
        mount(legacy = true)
        launchAndReplaceCallbacks()
        dispatch(provider.uri)
        awaitOutcomes(1)
        dispatch(provider.uri)
        dispatch(null)

        val returned = assertIs<Outcome.Returned>(outcomes.single())
        assertEquals(1, returned.generation)
        assertNull(returned.file)
        assertEquals(1, provider.deletes.get())
        assertFalse(provider.destination.exists())
    }

    @Test fun launchFailureDeliversOneErrorAndReleasesTheNextRequest() {
        mount()
        registry.hasDocumentsApp = false
        compose.runOnIdle { launcher.launch(CONTENT, "failed-launch", "bin") }
        awaitOutcomes(1)
        assertIs<Outcome.Failed>(outcomes.single())
        registry.hasDocumentsApp = true
        launchAndReplaceCallbacks()
        dispatch(null)
        awaitOutcomes(2)
        dispatch(null)

        assertEquals(2, outcomes.size, "Each of the two accepted attempts has one terminal callback")
        assertEquals(0, outcomes.first().generation)
        val returned = assertIs<Outcome.Returned>(outcomes.last())
        assertEquals(1, returned.generation)
        assertNull(returned.file)
    }

    @Test fun disposalDuringCopyClosesAndCleansWithoutSendingAStaleTerminalCallback() {
        val provider = provider()
        val output = BlockingFileOutput(provider.destination)
        shadowOf(resolver).registerOutputStream(provider.uri, output)
        mount()
        try {
            launchAndReplaceCallbacks()
            dispatch(provider.uri)
            assertTrue(output.entered.await(10, TimeUnit.SECONDS))
            compose.runOnIdle { mounted.value = false }
            compose.waitForIdle()
            output.release.countDown()
            compose.waitUntil(timeoutMillis = 10_000) { provider.deletes.get() == 1 }
            compose.waitForIdle()
            compose.runOnIdle { launcher.launch(CONTENT, "disposed-owner", "bin") }

            assertTrue(outcomes.isEmpty(), "A cancelled/disposed composition is not a live callback owner")
            assertEquals(1, output.closes.get())
            assertFalse(provider.destination.exists())
            assertContentEquals(CONTENT, provider.source.readBytes())
        } finally { output.release.countDown(); output.closeIfNeeded() }
    }

    private fun mount(legacy: Boolean = false) {
        val owner = object : ActivityResultRegistryOwner {
            override val activityResultRegistry = registry
        }
        compose.setContent {
            if (mounted.value) CompositionLocalProvider(LocalActivityResultRegistryOwner provides owner) {
                val current = generation.intValue
                val onResult: (KmpFile?) -> Unit = {
                    assertEquals(Looper.getMainLooper(), Looper.myLooper(), "Public callbacks belong to Android Main")
                    outcomes += Outcome.Returned(it, current)
                }
                launcher = if (legacy) rememberFileSaverLauncher(onResult = onResult) else
                    rememberFileSaverLauncher(onError = {
                        assertEquals(Looper.getMainLooper(), Looper.myLooper(), "Public errors belong to Android Main")
                        outcomes += Outcome.Failed(it, current)
                    }, onResult = onResult)
            }
        }
    }

    private fun launchAndReplaceCallbacks() {
        compose.runOnIdle { launcher.launch(CONTENT, "saved", "bin") }
        compose.runOnIdle { generation.intValue++ }
        compose.waitForIdle()
    }

    private fun dispatch(uri: Uri?) = compose.runOnIdle { registry.dispatchLast(uri) }

    private fun awaitOutcomes(count: Int) {
        compose.waitUntil(timeoutMillis = 10_000) { outcomes.size >= count }
        compose.waitForIdle()
        assertEquals(count, outcomes.size)
    }

    private val resolver get() = RuntimeEnvironment.getApplication().contentResolver

    private fun provider(): TerminalProvider = TerminalProvider(
        folder.newFile().apply { writeBytes(CONTENT) }, folder.newFile(),
    ).also {
        it.attachInfo(RuntimeEnvironment.getApplication(), ProviderInfo().apply { authority = AUTHORITY })
        ShadowContentResolver.registerProviderInternal(AUTHORITY, it)
    }

    private sealed interface Outcome {
        val generation: Int
        data class Returned(val file: KmpFile?, override val generation: Int) : Outcome
        data class Failed(val error: FilePickerException, override val generation: Int) : Outcome
    }

    class TerminalProvider(val source: File, val destination: File) : ContentProvider() {
        val uri: Uri = DocumentsContract.buildDocumentUri(AUTHORITY, destination.name)
        val openModes = CopyOnWriteArrayList<String>()
        val deletes = AtomicInteger()
        override fun onCreate(): Boolean = true
        override fun openAssetFile(uri: Uri, mode: String): AssetFileDescriptor? { openModes += mode; return null }
        override fun call(method: String, arg: String?, extras: Bundle?): Bundle? {
            check(method == "android:deleteDocument")
            check(extras?.getParcelable<Uri>("uri") == uri)
            check(destination.delete())
            deletes.incrementAndGet()
            return Bundle()
        }
        override fun query(uri: Uri, projection: Array<out String>?, selection: String?, selectionArgs: Array<out String>?, sortOrder: String?): Cursor? = null
        override fun getType(uri: Uri): String = "application/octet-stream"
        override fun insert(uri: Uri, values: ContentValues?): Uri? = error("unused")
        override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?): Int = error("unused")
        override fun update(uri: Uri, values: ContentValues?, selection: String?, selectionArgs: Array<out String>?): Int = error("unused")
    }

    private class BlockingFileOutput(file: File) : FileOutputStream(file) {
        val entered = CountDownLatch(1)
        val release = CountDownLatch(1)
        val writes = AtomicInteger()
        val closes = AtomicInteger()
        override fun write(bytes: ByteArray, offset: Int, length: Int) {
            if (writes.incrementAndGet() == 1) {
                entered.countDown()
                if (!release.await(10, TimeUnit.SECONDS)) throw IOException("The owning test did not release its IO stream")
            }
            super.write(bytes, offset, length)
        }
        override fun close() { closes.incrementAndGet(); super.close() }
        fun closeIfNeeded() { if (closes.get() == 0) close() }
    }

    companion object {
        private const val AUTHORITY = "nativecmpkit.picker.test.terminal-events"
        private val CONTENT = byteArrayOf(1, 0, -1, 4, 7, 9)
    }
}
