package com.mohamedrejeb.calf.io

import android.content.ContentProvider
import android.content.ContentValues
import android.content.pm.ProviderInfo
import android.database.Cursor
import android.net.Uri
import android.os.ParcelFileDescriptor
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.shadows.ShadowContentResolver
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Real AndroidX/resolver calls with controlled denial; not Binder/OS-grant enforcement. */
@RunWith(RobolectricTestRunner::class)
class DeniedProviderMetadataAcceptanceTest {
    @Test fun deniedQueriesCannotInventExistenceSizeOrNamesAndBothOverloadsAgree() {
        val context = RuntimeEnvironment.getApplication()
        AndroidContextHolder.initialize(context)
        assertTrue(AndroidContextHolder.context === context)
        val authority = "nativecmpkit.io.test.denied-metadata"
        val provider = DeniedProvider().apply {
            attachInfo(context, ProviderInfo().apply { this.authority = authority })
        }
        ShadowContentResolver.registerProviderInternal(authority, provider)
        val file = KmpFile(Uri.parse("content://$authority/openable/private"))
        for (denyType in listOf(false, true)) {
            provider.denyType = denyType
            val previousQueries = provider.queryAttempts
            val previousTypes = provider.typeAttempts
            assertFalse(file.exists(context))
            assertFalse(file.exists())
            assertFalse(file.isFile(context))
            assertFalse(file.isFile())
            assertEquals(previousTypes, provider.typeAttempts,
                "a denied existence query must short-circuit isFile before native MIME work")
            assertFalse(file.isDirectory(context))
            assertFalse(file.isDirectory())
            assertNull(file.getSize(context))
            assertNull(file.getSize())
            assertNull(file.getName(context))
            assertNull(file.getName())
            val expectedType = if (denyType) null else "application/octet-stream"
            assertEquals(expectedType, file.getMimeType(context))
            assertEquals(expectedType, file.getMimeType())
            assertTrue(provider.queryAttempts - previousQueries >= 8,
                "the actual registered provider must have thrown the controlled query denials")
            assertTrue(provider.typeAttempts > previousTypes)
            assertEquals(0, provider.openAttempts, "metadata must not acquire a native stream")
        }
    }

    class DeniedProvider : ContentProvider() {
        var denyType = false
        var queryAttempts = 0
        var typeAttempts = 0
        var openAttempts = 0

        override fun onCreate(): Boolean = true
        override fun query(uri: Uri, projection: Array<out String>?, selection: String?,
                           selectionArgs: Array<out String>?, sortOrder: String?): Cursor? {
            queryAttempts++
            throw SecurityException("Controlled fixture query denial")
        }
        override fun getType(uri: Uri): String? {
            typeAttempts++
            if (denyType) throw SecurityException("Controlled fixture MIME denial")
            return "application/octet-stream"
        }
        override fun openFile(uri: Uri, mode: String): ParcelFileDescriptor? {
            openAttempts++
            error("Metadata must not open the owned provider")
        }
        override fun insert(uri: Uri, values: ContentValues?): Uri? = error("unused")
        override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?): Int = error("unused")
        override fun update(uri: Uri, values: ContentValues?, selection: String?, selectionArgs: Array<out String>?): Int = error("unused")
    }
}
