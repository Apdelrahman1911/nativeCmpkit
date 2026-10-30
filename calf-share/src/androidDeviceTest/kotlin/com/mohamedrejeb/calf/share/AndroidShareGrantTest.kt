// SPDX-License-Identifier: Apache-2.0
@file:OptIn(com.mohamedrejeb.calf.core.ExperimentalCalfApi::class)
@file:Suppress("DEPRECATION")

package com.mohamedrejeb.calf.share

import android.app.Activity
import android.content.ComponentName
import android.content.ContextWrapper
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Process
import android.provider.DocumentsContract
import android.widget.TextView
import androidx.core.content.FileProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.io.toKmpFile
import java.io.File
import java.security.MessageDigest
import java.util.UUID
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.*

class ShareVerificationActivity : Activity() {
    @Volatile var documentResult: Intent? = null
    @Volatile var documentResultCode: Int? = null
    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        setContentView(TextView(this).apply { text = "NativeCmpKit source share verification" })
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == 4801) { documentResult = data?.let(::Intent); documentResultCode = resultCode }
    }
}

/**
 * Real library intents/providers, source foreground Activity and another UID's native reads.
 * Only chooser selection is redirected to our signature-protected, finite recipient;
 * Android itself grants/enforces URI permissions. No manual grant or fabricated reader.
 * Not DocumentsUI/cloud/photo-picker, chooser UX, physical/minimum-device or ABI evidence.
 */
@RunWith(AndroidJUnit4::class)
class AndroidShareGrantTest {
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val filesAuthority get() = "${context.packageName}.share-device-files"
    private val documentPackage = "io.github.apdelrahman1911.nativecmpkit.verification.sharedocuments"
    private val documentsAuthority get() = "$documentPackage.documents"
    private val options get() = ShareOptions(androidFileProviderAuthority = filesAuthority)
    private val grants = mutableListOf<Uri>()

    @Test fun nativeLocalFileConversionIsReadableAfterPresentationAndRevocationIsEnforced() = owned { activity, recipient, root ->
        val bytes = "NativeCmpKit synthetic delayed recipient bytes".encodeToByteArray()
        val file = File(root, "files/${UUID.randomUUID()}.txt").apply { parentFile!!.mkdirs(); writeBytes(bytes) }
        val local = file.toKmpFile()
        assertEquals("file", local.uri.scheme)
        val transport = ChooserRedirect(activity)
        val results = mutableListOf<ShareOutcome>()
        onMain { deliverAndroidShareResult(transport, ShareContent.File(local, "text/plain", "synthetic subject"), options, results::add) }
        assertEquals(listOf<ShareOutcome>(ShareOutcome.Presented), results, "Presentation is not recipient completion")
        val received = recipient.received(transport.packet)
        assertEquals(0, received.getInt("reads"), "Do not silently substitute an eager same-UID read")
        assertEquals("text/plain", received.getString("mime")); assertEquals("synthetic subject", received.getString("subject"))
        val value = assertNotNull(received.getStringArrayList("streams")).single()
        val uri = Uri.parse(value).also { grants += it }
        assertEquals("content", uri.scheme); assertEquals(filesAuthority, uri.authority)
        assertEquals(listOf(value), assertNotNull(received.getStringArrayList("clips")).toList())
        assertReadOnlyFlags(received)
        val read = reports(recipient.request("read")).single()
        assertRead(read, bytes); assertWriteDenied(read)
        assertTrue(file.exists()); assertContentEquals(bytes, file.readBytes())
        context.revokeUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
        val revoked = reports(recipient.request("read")).single()
        assertFalse(revoked.getBoolean("readGranted")); assertEquals("SecurityException", revoked.getString("readError"))
        assertWriteDenied(revoked)
        assertEquals(1, results.size); assertEquals(ShareOutcome.Presented, results.single())
        assertContentEquals(bytes, file.readBytes())
    }

    @Test fun nativeSafDocumentsAndMixedMimeClipDataRetainReadOnlyAccessAndCloseRealDescriptors() = owned { activity, recipient, _ ->
        val firstBytes = "NativeCmpKit synthetic SAF document".encodeToByteArray()
        val secondBytes = android.util.Base64.decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==", android.util.Base64.DEFAULT)
        val owner = context.packageManager.getApplicationInfo(documentPackage, 0)
        assertNotEquals(Process.myUid(), owner.uid)
        assertNotEquals(recipient.recipientUid, owner.uid, "Document provider, library caller and recipient must have three distinct native UIDs")
        assertTrue(owner.flags and ApplicationInfo.FLAG_DEBUGGABLE != 0)
        assertEquals(37, owner.targetSdkVersion)
        assertEquals(PackageManager.SIGNATURE_MATCH, context.packageManager.checkSignatures(context.packageName, documentPackage))
        assertEquals(PackageManager.PERMISSION_GRANTED, context.checkSelfPermission("$documentPackage.SELECT_DOCUMENTS"))
        onMain { activity.startActivityForResult(Intent().setComponent(ComponentName(documentPackage, "$documentPackage.ShareDocumentGrantActivity")), 4801) }
        val source = activity as ShareVerificationActivity
        waitUntil { source.documentResultCode != null }
        assertEquals(Activity.RESULT_OK, source.documentResultCode)
        val selected = assertNotNull(source.documentResult)
        val uris = assertNotNull(selected.getParcelableArrayListExtra<Uri>(Intent.EXTRA_STREAM))
        assertEquals(Intent.FLAG_GRANT_READ_URI_PERMISSION, selected.flags and
            (Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION or Intent.FLAG_GRANT_PREFIX_URI_PERMISSION))
        val ids = listOf("nativecmpkit-owned.txt", "nativecmpkit-owned.png")
        assertEquals(ids, uris.map { DocumentsContract.getDocumentId(it) })
        assertEquals(uris.map(Uri::toString), (0 until assertNotNull(selected.clipData).itemCount).map { selected.clipData!!.getItemAt(it).uri.toString() })
        assertTrue(uris.all { DocumentsContract.isDocumentUri(context, it) })
        uris.forEach {
            assertEquals(PackageManager.PERMISSION_GRANTED, context.checkUriPermission(it, Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_READ_URI_PERMISSION))
            assertEquals(PackageManager.PERMISSION_DENIED, context.checkUriPermission(it, Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_WRITE_URI_PERMISSION))
        }
        assertEquals(listOf("text/plain", "image/png"), uris.map { context.contentResolver.getType(it) })
        assertTrue(ids.all { stats(it).getInt("opens") == 0 })
        val transport = ChooserRedirect(activity)
        val results = mutableListOf<ShareOutcome>()
        onMain { deliverAndroidShareResult(transport, ShareContent.Files(uris.map(::KmpFile), "*/*", "mixed synthetic files"), options, results::add) }
        assertEquals(listOf<ShareOutcome>(ShareOutcome.Presented), results)
        val received = recipient.received(transport.packet)
        assertEquals(Intent.ACTION_SEND_MULTIPLE, received.getString("action")); assertEquals("*/*", received.getString("mime"))
        assertEquals(uris.map(Uri::toString), assertNotNull(received.getStringArrayList("streams")).toList())
        assertEquals(uris.map(Uri::toString), assertNotNull(received.getStringArrayList("clips")).toList()); assertReadOnlyFlags(received)
        assertEquals(0, received.getInt("reads")); assertTrue(ids.all { stats(it).getInt("opens") == 0 })
        val reads = reports(recipient.request("read")); assertEquals(2, reads.size)
        listOf(firstBytes, secondBytes).forEachIndexed { index, bytes -> assertRead(reads[index], bytes); assertWriteDenied(reads[index]) }
        waitUntil { ids.all { stats(it).getInt("closes") == 1 } }
        ids.forEach {
            val state = stats(it)
            assertNotEquals(Process.myPid(), state.getInt("pid"), "The provider must be a real different native process")
            assertEquals(owner.uid, state.getInt("uid"))
            assertEquals(1, state.getInt("opens")); assertEquals(1, state.getInt("closes"))
            assertEquals(0, state.getInt("closeErrors")); assertEquals(0, state.getInt("writes"))
        }
        // Closing the recipient Activity/source Activity owns their nonpersistent
        // grant lifetime. The explicit local FileProvider revocation is tested above;
        // a nonowner must not invent authority to revoke the third app's source URI.
        assertTrue(ids.all { stats(it).getInt("opens") == 1 && stats(it).getInt("closes") == 1 })
        assertEquals(1, results.size)
    }

    @Test fun nativeInvalidProviderAndUngrantableUrisFailWithoutReceivingOrDeletingData() = owned { activity, recipient, root ->
        val transport = ChooserRedirect(activity)
        val before = recipient.request("snapshot").getInt("intents")
        val bytes = "NativeCmpKit owning configuration-failure data".encodeToByteArray()
        val outside = File(root, "outside.txt").apply { parentFile!!.mkdirs(); writeBytes(bytes) }
        fun launch(content: ShareContent, selected: ShareOptions = options): ShareOutcome = onMain { launchAndroidShare(transport, content, selected) }
        assertEquals(ShareFailureReason.InvalidContent, assertIs<ShareOutcome.Failed>(launch(ShareContent.Files(emptyList(), "*/*"))).reason)
        assertEquals(ShareFailureReason.Configuration, assertIs<ShareOutcome.Failed>(launch(ShareContent.File(KmpFile(Uri.parse("https://example.invalid/owned-fixture")), "text/plain"))).reason)
        assertEquals(ShareFailureReason.Configuration, assertIs<ShareOutcome.Failed>(launch(ShareContent.File(outside.toKmpFile(), "text/plain"))).reason)
        assertEquals(ShareFailureReason.Configuration, assertIs<ShareOutcome.Failed>(launch(ShareContent.File(outside.toKmpFile(), "text/plain"),
            ShareOptions(androidFileProviderAuthority = "missing.nativecmpkit.synthetic.provider"))).reason)
        assertEquals(0, transport.attempts)
        val ungrantable = Uri.parse("content://${context.packageName}.share-device-grantless/file")
        assertEquals("application/octet-stream", context.contentResolver.getType(ungrantable))
        val refused = launch(ShareContent.File(KmpFile(ungrantable), "application/octet-stream"))
        assertEquals(ShareFailureReason.Permission, assertIs<ShareOutcome.Failed>(refused).reason)
        val providerError = launch(ShareContent.File(KmpFile(Uri.parse("content://${context.packageName}.share-device-grantless/throw")), "application/octet-stream"))
        assertEquals(ShareFailureReason.Permission, assertIs<ShareOutcome.Failed>(providerError).reason)
        assertEquals(before, recipient.request("snapshot").getInt("intents"))
        assertContentEquals(bytes, outside.readBytes())
    }

    private inner class ChooserRedirect(private val activity: Activity) : ContextWrapper(activity) {
        val packet = UUID.randomUUID().toString().replace("-", "")
        var attempts = 0; private set
        override fun startActivity(intent: Intent) {
            attempts++
            assertEquals(Intent.ACTION_CHOOSER, intent.action)
            val target = Intent(assertNotNull(intent.getParcelableExtra<Intent>(Intent.EXTRA_INTENT)))
            assertTrue(intent.flags and Intent.FLAG_GRANT_READ_URI_PERMISSION != 0)
            assertNotNull(intent.clipData)
            target.component = ComponentName(OwnedShareRecipient.PACKAGE, "${OwnedShareRecipient.PACKAGE}.ShareRecipientActivity")
            target.putExtra("nativecmpkit.packet", packet)
            // Android owns the actual outgoing grant. Only UX recipient selection is deterministic.
            activity.startActivityForResult(target, 4817)
        }
    }

    private fun owned(body: (Activity, OwnedShareRecipient, File) -> Unit) {
        assertEquals("true", InstrumentationRegistry.getArguments().getString("nativecmpkitOwnedShareRecipient"))
        assertEquals(35, Build.VERSION.SDK_INT); assertTrue(Build.HARDWARE in setOf("ranchu", "goldfish"))
        val root = File(context.cacheDir, "nativecmpkit-share-device")
        val recipient = OwnedShareRecipient()
        try {
            recipient.connect()
            ActivityScenario.launch(ShareVerificationActivity::class.java).use { scenario ->
                var activity: Activity? = null; scenario.onActivity { activity = it }
                body(assertNotNull(activity), recipient, root)
            }
        } finally {
            try { recipient.close() }
            finally {
                try { grants.forEach { context.revokeUriPermission(it, Intent.FLAG_GRANT_READ_URI_PERMISSION) } }
                finally { grants.clear(); if (root.exists()) assertTrue(root.deleteRecursively()) }
            }
        }
    }

    private fun assertReadOnlyFlags(received: Bundle) {
        val flags = received.getInt("flags")
        assertTrue(flags and Intent.FLAG_GRANT_READ_URI_PERMISSION != 0)
        assertEquals(0, flags and (Intent.FLAG_GRANT_WRITE_URI_PERMISSION or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION or Intent.FLAG_GRANT_PREFIX_URI_PERMISSION))
    }

    private fun reports(bundle: Bundle): List<Bundle> = assertNotNull(bundle.getParcelableArrayList<Bundle>("reports"))
    private fun assertRead(report: Bundle, bytes: ByteArray) {
        assertTrue(report.getBoolean("readGranted")); assertFalse(report.getBoolean("writeGranted"))
        assertNull(report.getString("readError")); assertEquals(bytes.size, report.getInt("bytes"))
        assertEquals(MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it.toInt() and 255) }, report.getString("sha256"))
    }
    private fun assertWriteDenied(report: Bundle) { assertFalse(report.getBoolean("writeGranted")); assertEquals("SecurityException", report.getString("writeError")) }
    private fun stats(id: String): Bundle = assertNotNull(context.contentResolver.call(Uri.parse("content://$documentsAuthority"), "nativecmpkit-share-document-stats", id, null))
    private fun waitUntil(predicate: () -> Boolean) {
        val start = System.nanoTime()
        while (!predicate()) { check(System.nanoTime() - start < 20_000_000_000L); Thread.sleep(20) }
    }
    private fun <T> onMain(action: () -> T): T {
        var result: Result<T>? = null
        instrumentation.runOnMainSync { result = runCatching(action) }
        return checkNotNull(result).getOrThrow()
    }
}
