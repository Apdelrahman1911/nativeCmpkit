// SPDX-License-Identifier: Apache-2.0
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)
package io.github.apdelrahman1911.nativecmpkit.verification.permissiondemo

import android.Manifest
import android.content.ContentValues
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.MediaStore
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.SideEffect
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.io.readByteArray
import com.mohamedrejeb.calf.permissions.Call
import com.mohamedrejeb.calf.permissions.MultiplePermissionsState
import com.mohamedrejeb.calf.permissions.Permission
import com.mohamedrejeb.calf.permissions.PermissionState
import com.mohamedrejeb.calf.permissions.ReadImage
import com.mohamedrejeb.calf.permissions.ReadVideo
import com.mohamedrejeb.calf.permissions.RecordAudio
import com.mohamedrejeb.calf.permissions.details
import com.mohamedrejeb.calf.permissions.isGranted
import com.mohamedrejeb.calf.permissions.rememberMultiplePermissionsState
import com.mohamedrejeb.calf.permissions.rememberPermissionState
import com.mohamedrejeb.calf.permissions.shouldShowRationale
import com.mohamedrejeb.calf.picker.FilePickerFileType
import com.mohamedrejeb.calf.picker.FilePickerLauncher
import com.mohamedrejeb.calf.picker.FilePickerSelectionMode
import com.mohamedrejeb.calf.picker.rememberFilePickerLauncher
import java.io.ByteArrayOutputStream
import java.security.MessageDigest
import java.util.UUID
import kotlinx.coroutines.launch

/** Fresh separate UID mounts the public libraries; no sample screen or permission-result injection. */
class PermissionDemoActivity : ComponentActivity() {
    val generation: String = UUID.randomUUID().toString()
    private var states: List<PermissionState> = emptyList()
    private var media: MultiplePermissionsState? = null
    private var filePicker: FilePickerLauncher? = null
    private var imagePicker: FilePickerLauncher? = null
    private val callbacks = mutableMapOf<String, Int>()
    private val results = mutableMapOf<String, Boolean>()
    private val reads = mutableMapOf<String, Bundle>()
    private val seeds = mutableMapOf<String, Seed>()
    private var platformCallbacks = 0
    private var platformResult: Map<String, Boolean> = emptyMap()
    private var activeReads = 0
    private var nativeError: String? = null
    private val platformSelection = registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) {
        platformCallbacks++
        platformResult = it.toMap()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        check(Build.VERSION.SDK_INT in 33..35)
        check(active == null)
        check(!cleanupFailed && cleanupFailure == null)
        active = this
        setContent {
            val call = rememberPermissionState(Permission.Call) { completed("Call", it) }
            val microphone = rememberPermissionState(Permission.RecordAudio) { completed("RecordAudio", it) }
            val visualMedia = rememberMultiplePermissionsState(listOf(Permission.ReadImage, Permission.ReadVideo)) {
                check(it.keys == setOf(Permission.ReadImage, Permission.ReadVideo))
                it.forEach { (permission, granted) -> completed(permission.name, granted) }
            }
            val document = rememberFilePickerLauncher(
                type = FilePickerFileType.Extension(listOf("txt")),
                selectionMode = FilePickerSelectionMode.Single,
                onError = { nativeError = "public-document-picker-error" },
                onResult = { received("document", it) },
            )
            val image = rememberFilePickerLauncher(
                type = FilePickerFileType.Image,
                selectionMode = FilePickerSelectionMode.Single,
                onError = { nativeError = "public-image-picker-error" },
                onResult = { received("image", it) },
            )
            SideEffect {
                states = listOf(call, microphone) + visualMedia.permissions
                media = visualMedia
                filePicker = document
                imagePicker = image
            }
            BasicText("NativeCmpKit approved Call permission test variant")
        }
    }

    private fun completed(name: String, granted: Boolean) {
        callbacks[name] = (callbacks[name] ?: 0) + 1
        results[name] = granted
    }

    fun perform(operation: String) {
        check(android.os.Looper.myLooper() == android.os.Looper.getMainLooper())
        if (operation == "finish") {
            try {
                closeOwnedActivity()
            } catch (failure: Throwable) {
                recordCleanupFailure(failure)
            } finally {
                try { finish() }
                catch (failure: Throwable) { recordCleanupFailure(failure) }
            }
            cleanupFailure?.let { throw it }
            return
        }
        check(states.size == 4 && hasWindowFocus() && lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED))
        when (operation) {
            "request-call" -> states.single { it.permission == Permission.Call }.launchPermissionRequest()
            "request-microphone" -> states.single { it.permission == Permission.RecordAudio }.launchPermissionRequest()
            "request-media" -> checkNotNull(media).launchMultiplePermissionRequest()
            "platform-selected" -> {
                check(Build.VERSION.SDK_INT >= 34)
                // Establish real explicit selected access, then observe public library states.
                // The library currently requests images/video only; this is not that request path.
                platformSelection.launch(arrayOf(Manifest.permission.READ_MEDIA_IMAGES,
                    Manifest.permission.READ_MEDIA_VIDEO, Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED))
            }
            "seed" -> seedOwnedContent()
            "file-picker" -> { check("document" in seeds); checkNotNull(filePicker).launch() }
            "image-picker" -> { check("image" in seeds); checkNotNull(imagePicker).launch() }
            else -> error("Unknown finite operation")
        }
    }

    fun snapshot(): Bundle = Bundle().apply {
        putString("activityGeneration", generation)
        putBoolean("mounted", states.size == 4 && filePicker != null && imagePicker != null)
        putBoolean("resumed", lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED))
        putBoolean("focused", hasWindowFocus())
        putInt("activeReads", activeReads)
        putInt("ownedSeedCount", seeds.size)
        nativeError?.let { putString("probeError", it) }
        states.forEach { state ->
            val name = state.permission.name
            putBundle(name, Bundle().apply {
                putBoolean("granted", state.status.isGranted)
                putBoolean("rationale", state.status.shouldShowRationale)
                putString("availability", state.details.availability.name)
                putString("access", state.details.access.name)
                putString("requestability", state.details.requestability.name)
                state.details.lastRequest?.let { putString("lastRequest", it.name) }
                putInt("callbacks", callbacks[name] ?: 0)
                results[name]?.let { putBoolean("callbackResult", it) }
            })
        }
        NATIVE_PERMISSIONS.forEach { permission ->
            putBoolean(permission, checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED)
            putBoolean(permission + ".rationale", shouldShowRequestPermissionRationale(permission))
        }
        putInt("platformCallbacks", platformCallbacks)
        putBundle("platformResult", Bundle().apply { platformResult.forEach { (name, value) -> putBoolean(name, value) } })
        seeds.forEach { (kind, seed) ->
            putBundle("seed." + kind, Bundle().apply {
                putString("name", seed.name)
                putString("sha256", seed.sha256)
                putInt("bytes", seed.bytes)
            })
        }
        reads.forEach { (kind, read) -> putBundle("read." + kind, Bundle(read)) }
    }

    private fun received(kind: String, files: List<KmpFile>) {
        activeReads++
        lifecycleScope.launch {
            try {
                val file = files.single()
                val source = checkNotNull(seeds[kind])
                check(file.uri.scheme == "content")
                val bytes = file.readByteArray(maxBytes = 65536)
                check(bytes.size == source.bytes && sha256(bytes) == source.sha256)
                assertOwnedAndUnchanged(source)
                check(kind !in reads)
                reads[kind] = Bundle().apply {
                    putInt("results", files.size)
                    putBoolean("realContentUri", true)
                    putBoolean("sourcePreserved", true)
                    putString("sha256", sha256(bytes))
                    putInt("bytes", bytes.size)
                }
            } catch (failure: Exception) {
                nativeError = "native-picker-read-or-identity-failed"
            } finally {
                activeReads--
            }
        }
    }

    private fun seedOwnedContent() {
        check(seeds.isEmpty())
        val suffix = generation.replace("-", "")
        val text = "NativeCmpKit NAV015 synthetic document $suffix\n".repeat(32).toByteArray(Charsets.UTF_8)
        insertOwned("document", "nav015-$suffix.txt", "text/plain", text,
            MediaStore.Downloads.EXTERNAL_CONTENT_URI, "Download/NativeCmpKitNav015")
        val bitmap = Bitmap.createBitmap(2, 2, Bitmap.Config.ARGB_8888)
        val png = try {
            bitmap.eraseColor(Color.rgb(37, 83, 149))
            bitmap.setPixel(0, 0, suffix.take(6).toInt(16) or (0xff shl 24))
            ByteArrayOutputStream().use { out ->
                check(bitmap.compress(Bitmap.CompressFormat.PNG, 100, out))
                out.toByteArray()
            }
        } finally { bitmap.recycle() }
        insertOwned("image", "nav015-$suffix.png", "image/png", png,
            MediaStore.Images.Media.EXTERNAL_CONTENT_URI, "Pictures/NativeCmpKitNav015")
    }

    private fun insertOwned(kind: String, name: String, mime: String, bytes: ByteArray, collection: Uri, directory: String) {
        check(bytes.size in 1..65536)
        val values = ContentValues().apply {
            put(MediaStore.MediaColumns.DISPLAY_NAME, name)
            put(MediaStore.MediaColumns.MIME_TYPE, mime)
            put(MediaStore.MediaColumns.RELATIVE_PATH, directory)
            put(MediaStore.MediaColumns.IS_PENDING, 1)
        }
        val uri = checkNotNull(contentResolver.insert(collection, values))
        val seed = Seed(uri, name, sha256(bytes), bytes.size)
        seeds[kind] = seed // Retain ownership before any potentially failing write.
        checkNotNull(contentResolver.openOutputStream(uri, "w")).use { it.write(bytes) }
        check(contentResolver.update(uri, ContentValues().apply { put(MediaStore.MediaColumns.IS_PENDING, 0) }, null, null) == 1)
        assertOwnedAndUnchanged(seed)
        seed.published = true
    }

    private fun assertOwnedIdentity(seed: Seed) {
        checkNotNull(contentResolver.query(seed.uri, arrayOf(MediaStore.MediaColumns.OWNER_PACKAGE_NAME,
            MediaStore.MediaColumns.DISPLAY_NAME), null, null, null)).use { cursor ->
            check(cursor.count == 1 && cursor.moveToFirst())
            check(cursor.getString(0) == packageName && cursor.getString(1) == seed.name)
        }
    }

    private fun assertOwnedAndUnchanged(seed: Seed) {
        assertOwnedIdentity(seed)
        val bytes = checkNotNull(contentResolver.openInputStream(seed.uri)).use { input ->
            val value = input.readNBytes(65537)
            check(value.size <= 65536)
            value
        }
        check(bytes.size == seed.bytes && sha256(bytes) == seed.sha256)
    }

    private fun appendFailure(firstFailure: Throwable?, failure: Throwable): Throwable {
        if (firstFailure == null) return failure
        if (firstFailure !== failure) firstFailure.addSuppressed(failure)
        return firstFailure
    }

    private fun recordCleanupFailure(failure: Throwable) {
        cleanupFailed = true
        cleanupFailure = appendFailure(cleanupFailure, failure)
    }

    private fun closeOwnedActivity() {
        // A live-read refusal is recorded before cleanup; it cannot skip owned
        // row attempts or become successful after later lifecycle cancellation.
        try { check(activeReads == 0) }
        catch (failure: Throwable) { recordCleanupFailure(failure) }
        try { closeOwnedSeeds() }
        catch (failure: Throwable) { recordCleanupFailure(failure) }
    }

    private fun closeOwnedSeeds() {
        var firstFailure: Throwable? = null
        for ((kind, seed) in seeds.toMap()) {
            try {
                // An insert can succeed before a write/update fails. Exact row
                // ownership, not a successful content hash, admits its cleanup.
                assertOwnedIdentity(seed)
            } catch (failure: Throwable) {
                firstFailure = appendFailure(firstFailure, failure)
                continue
            }
            if (seed.published) {
                try { assertOwnedAndUnchanged(seed) }
                catch (failure: Throwable) { firstFailure = appendFailure(firstFailure, failure) }
            }
            try {
                // Content validation can fail after the initial identity query.
                // Only a fresh exact identity check admits this deletion.
                assertOwnedIdentity(seed)
                check(contentResolver.delete(seed.uri, null, null) == 1)
                seeds.remove(kind)
            } catch (failure: Throwable) {
                firstFailure = appendFailure(firstFailure, failure)
            }
        }
        firstFailure?.let { throw it }
    }

    override fun onDestroy() {
        try {
            closeOwnedActivity()
        } catch (failure: Throwable) {
            recordCleanupFailure(failure)
        } finally {
            if (active === this) active = null
            try { super.onDestroy() }
            catch (failure: Throwable) { recordCleanupFailure(failure) }
        }
        cleanupFailure?.let { throw it }
    }

    private data class Seed(val uri: Uri, val name: String, val sha256: String, val bytes: Int, var published: Boolean = false)
    companion object {
        @Volatile var active: PermissionDemoActivity? = null
            private set
        @Volatile var cleanupFailed = false
            private set
        @Volatile private var cleanupFailure: Throwable? = null
        val NATIVE_PERMISSIONS = listOf(Manifest.permission.CALL_PHONE, Manifest.permission.RECORD_AUDIO,
            Manifest.permission.READ_MEDIA_IMAGES, Manifest.permission.READ_MEDIA_VIDEO,
            Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED)
        private fun sha256(bytes: ByteArray) = MessageDigest.getInstance("SHA-256").digest(bytes)
            .joinToString("") { "%02x".format(it) }
    }
}
