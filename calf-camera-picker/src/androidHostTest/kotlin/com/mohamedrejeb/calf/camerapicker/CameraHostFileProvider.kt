package com.mohamedrejeb.calf.camerapicker

import android.app.Application
import android.content.pm.ProviderInfo
import android.os.Bundle
import androidx.core.content.FileProvider
import org.robolectric.Shadows.shadowOf
import org.robolectric.shadows.ShadowContentResolver
import kotlin.test.assertNotNull

/** Real AndroidX path parsing/resolver; no external-UID grant claim on Robolectric. */
internal fun installCameraHostFileProvider(
    application: Application,
    authority: String,
    paths: String = "nativecmpkit_camera_test_paths",
) {
    val xml = sequenceOf(application.packageName, "com.mohamedrejeb.calf.calfcamerapicker")
        .map { application.resources.getIdentifier(paths, "xml", it) }.firstOrNull { it != 0 }
    assertNotNull(xml, "The real FileProvider requires merged host XML resources")
    val info = ProviderInfo().apply {
        name = FileProvider::class.java.name
        packageName = application.packageName
        this.authority = authority
        exported = false
        grantUriPermissions = true
        metaData = Bundle().apply { putInt("android.support.FILE_PROVIDER_PATHS", xml) }
    }
    shadowOf(application.packageManager).addOrUpdateProvider(info)
    val provider = FileProvider()
    provider.attachInfo(application, info)
    ShadowContentResolver.registerProviderInternal(authority, provider)
}
