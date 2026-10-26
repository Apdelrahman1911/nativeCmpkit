@file:OptIn(com.mohamedrejeb.calf.core.ExperimentalCalfApi::class)

package com.mohamedrejeb.calf.share

import android.app.Application
import android.content.ActivityNotFoundException
import android.content.ContextWrapper
import android.content.Intent
import android.content.pm.ProviderInfo
import android.net.Uri
import android.os.Bundle
import androidx.core.content.FileProvider
import com.mohamedrejeb.calf.io.KmpFile
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config
import org.robolectric.shadows.ShadowContentResolver
import java.io.File
import kotlin.test.*

/** Real library intents/FileProvider/cache files under Robolectric, not recipient-device grants. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
class AndroidShareTest {
    private val providerId = java.util.UUID.randomUUID().toString().replace("-", "")
    private val application: Application get() = RuntimeEnvironment.getApplication()
    private val authority: String get() = "${application.packageName}.nativecmpkit.test.$providerId"
    private val options: ShareOptions get() = ShareOptions(androidFileProviderAuthority = authority)

    private fun installProvider() {
        val resources = application.resources
        val xml = sequenceOf(application.packageName, "com.mohamedrejeb.calf.calfshare")
            .map { resources.getIdentifier("nativecmpkit_share_test_paths", "xml", it) }.firstOrNull { it != 0 }
        assertNotNull(xml, "Android host test resources must be merged for the real FileProvider test")
        val info = ProviderInfo().apply {
            name = FileProvider::class.java.name
            packageName = application.packageName
            authority = this@AndroidShareTest.authority
            exported = false
            grantUriPermissions = true
            metaData = Bundle().apply { putInt("android.support.FILE_PROVIDER_PATHS", xml) }
        }
        shadowOf(application.packageManager).addOrUpdateProvider(info)
        val provider = FileProvider()
        provider.attachInfo(application, info)
        ShadowContentResolver.registerProviderInternal(authority, provider)
    }

    private fun withFile(action: (File) -> Unit) {
        val directory = File(application.cacheDir, "nativecmpkit-share-test").apply { mkdirs() }
        val file = File.createTempFile("share-", ".txt", directory).apply { writeText("recipient fixture") }
        try { action(file) } finally { file.delete() }
    }

    @Test fun localFileIsConvertedToAReadableContentUriWithReadGrant() {
        installProvider()
        withFile { file ->
            val intent = ShareContent.File(KmpFile(Uri.fromFile(file)), "text/plain", "subject").toShareIntent(application, options)
            val uri = intent.getParcelableExtra<Uri>(Intent.EXTRA_STREAM)!!
            assertEquals("content", uri.scheme)
            assertEquals(authority, uri.authority)
            assertEquals(uri, intent.clipData!!.getItemAt(0).uri)
            assertTrue(intent.flags and Intent.FLAG_GRANT_READ_URI_PERMISSION != 0)
            assertEquals("subject", intent.getStringExtra(Intent.EXTRA_SUBJECT))
            assertEquals("recipient fixture", application.contentResolver.openInputStream(uri)!!.bufferedReader().use { it.readText() })
        }
    }

    @Test @Config(sdk = [23]) fun api23AlsoUsesTheConfiguredFileProvider() = localFileIsConvertedToAReadableContentUriWithReadGrant()

    @Test fun existingContentUrisArePreservedInAllMultiFileGrants() {
        installProvider()
        withFile { first -> withFile { second ->
            val uris = listOf(first, second).map { FileProvider.getUriForFile(application, authority, it) }
            val intent = ShareContent.Files(uris.map(::KmpFile), "text/plain").toShareIntent(application, options)
            assertEquals(Intent.ACTION_SEND_MULTIPLE, intent.action)
            assertEquals(uris, assertNotNull(intent.getParcelableArrayListExtra<Uri>(Intent.EXTRA_STREAM)).toList())
            assertEquals(uris, (0 until intent.clipData!!.itemCount).map { intent.clipData!!.getItemAt(it).uri })
            assertTrue(intent.flags and Intent.FLAG_GRANT_READ_URI_PERMISSION != 0)
        } }
    }

    @Test fun missingProviderAndOutsideConfiguredRootAreExplicitFailures() {
        withFile { file ->
            val content = ShareContent.File(KmpFile(Uri.fromFile(file)), "text/plain")
            val absent = launchAndroidShare(application, content, ShareOptions(androidFileProviderAuthority = "missing.provider"))
            assertEquals(ShareFailureReason.Configuration, assertIs<ShareOutcome.Failed>(absent).reason)
        }
        installProvider()
        val outside = File.createTempFile("not-shared-", ".txt", application.cacheDir)
        try {
            val result = launchAndroidShare(application, ShareContent.File(KmpFile(Uri.fromFile(outside)), "text/plain"), options)
            assertEquals(ShareFailureReason.Configuration, assertIs<ShareOutcome.Failed>(result).reason)
            assertTrue(outside.exists())
        } finally { outside.delete() }
    }

    @Test fun presentedStageAndApplicationContextFlagsAreTruthful() {
        assertEquals(ShareOutcome.Presented, launchAndroidShare(application, ShareContent.Text("fixture"), options))
        val chooser = shadowOf(application).nextStartedActivity
        assertEquals(Intent.ACTION_CHOOSER, chooser.action)
        assertTrue(chooser.flags and Intent.FLAG_ACTIVITY_NEW_TASK != 0)
    }

    @Test fun throwingApplicationResultCallbackIsNotReclassifiedOrInvokedTwice() {
        var calls = 0
        val expected = IllegalStateException("application result")
        val thrown = assertFailsWith<IllegalStateException> {
            deliverAndroidShareResult(application, ShareContent.Text("fixture"), options) {
                calls++
                assertEquals(ShareOutcome.Presented, it)
                throw expected
            }
        }
        assertSame(expected, thrown)
        assertEquals(1, calls)
    }

    @Test fun platformLaunchFailureIsOneFailureInsteadOfACompletedShare() {
        val context = object : ContextWrapper(application) {
            override fun startActivity(intent: Intent) { throw ActivityNotFoundException("no chooser") }
        }
        val results = mutableListOf<ShareOutcome>()
        deliverAndroidShareResult(context, ShareContent.Text("fixture"), options, results::add)
        assertEquals(ShareFailureReason.Platform, assertIs<ShareOutcome.Failed>(results.single()).reason)
    }

    @Test fun invalidSchemesAndEmptyCollectionsNeverStartAnActivity() {
        val invalid = ShareContent.File(KmpFile(Uri.parse("https://example.invalid/file")), "text/plain")
        assertIs<ShareOutcome.Failed>(launchAndroidShare(application, invalid, options))
        assertIs<ShareOutcome.Failed>(launchAndroidShare(application, ShareContent.Files(emptyList(), "text/plain"), options))
        assertNull(shadowOf(application).nextStartedActivity)
    }
}
