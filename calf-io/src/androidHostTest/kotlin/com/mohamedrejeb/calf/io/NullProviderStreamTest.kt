package com.mohamedrejeb.calf.io

import android.content.ContentProvider
import android.content.ContentValues
import android.content.pm.ProviderInfo
import android.content.res.AssetFileDescriptor
import android.database.Cursor
import android.net.Uri
import java.io.FileNotFoundException
import kotlinx.coroutines.runBlocking
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import org.robolectric.shadows.ShadowContentResolver
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNull

/** Actual Android ContentResolver null-provider path under Robolectric, not a device/binder claim. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], manifest = Config.NONE)
class NullProviderStreamTest {
    @Test fun nullProviderInputStreamStillReportsNotFound() = runBlocking {
        val context = RuntimeEnvironment.getApplication()
        val providerAuthority = "nativecmpkit.io.nullstream"
        val provider = NullStreamProvider().apply {
            attachInfo(context, ProviderInfo().apply { authority = providerAuthority })
        }
        ShadowContentResolver.registerProviderInternal(providerAuthority, provider)
        val uri = Uri.parse("content://$providerAuthority/file.bin")
        assertNull(context.contentResolver.openInputStream(uri), "The fixture must actually return null, not an unregistered mock stream")
        assertFailsWith<FileNotFoundException> { KmpFile(uri).readByteArray(context) }
        assertEquals(2, provider.opens)
    }

    class NullStreamProvider : ContentProvider() {
        var opens = 0
        override fun onCreate(): Boolean = true
        override fun openAssetFile(uri: Uri, mode: String): AssetFileDescriptor? { opens++; return null }
        override fun getType(uri: Uri): String = "application/octet-stream"
        override fun query(uri: Uri, projection: Array<out String>?, selection: String?, selectionArgs: Array<out String>?, sortOrder: String?): Cursor? = null
        override fun insert(uri: Uri, values: ContentValues?): Uri? = error("unused")
        override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?): Int = error("unused")
        override fun update(uri: Uri, values: ContentValues?, selection: String?, selectionArgs: Array<out String>?): Int = error("unused")
    }
}
