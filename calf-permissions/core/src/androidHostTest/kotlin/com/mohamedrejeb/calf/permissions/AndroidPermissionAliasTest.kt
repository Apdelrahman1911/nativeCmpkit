@file:OptIn(ExperimentalPermissionsApi::class, kotlinx.coroutines.ExperimentalCoroutinesApi::class)

package com.mohamedrejeb.calf.permissions

import android.Manifest
import android.os.Build
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.runTest
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.LooperMode
import kotlin.test.*

/**
 * Different instrumentation configurations select different Robolectric sandboxes.
 * Explicit fresh-registry assertions below prove each actual singleton initialization
 * order, rather than repeatedly accessing already-initialized objects. No production
 * registry reset/reflection or substituted builtin mappings are used.
 * Real public Compose/ActivityResult factories; grants and OS dialogs are controlled
 * by the existing host fixture, not physical-device authorization evidence.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28, 32, 33], manifest = Config.NONE,
    instrumentedPackages = ["com.mohamedrejeb.calf.permissions", "nativecmpkit.alias.storagefirst"])
@LooperMode(LooperMode.Mode.PAUSED)
class AndroidStorageFirstAliasTest {
    @Test fun coldReadStorageThenGalleryReturnsOnlyRequestedLogicalIdentities() = runTest {
        exerciseColdBuiltinAliases(readStorageFirst = true)
    }
}

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28, 32, 33], manifest = Config.NONE,
    instrumentedPackages = ["com.mohamedrejeb.calf.permissions", "nativecmpkit.alias.galleryfirst"])
@LooperMode(LooperMode.Mode.PAUSED)
class AndroidGalleryFirstAliasTest {
    @Test fun coldGalleryThenReadStorageReturnsOnlyRequestedLogicalIdentities() = runTest {
        exerciseColdBuiltinAliases(readStorageFirst = false)
    }
}

private suspend fun TestScope.exerciseColdBuiltinAliases(readStorageFirst: Boolean) {
    val sdk = Build.VERSION.SDK_INT
    assertTrue(sdk in listOf(28, 32, 33), "This regression must really execute its required SDK matrix")
    val storageIdentity = Permission("ReadStorage")
    val galleryIdentity = Permission("Gallery")
    assertNull(AndroidPermissionRegistry.getMapping(storageIdentity), "ReadStorage must not be initialized before this cold-order test")
    assertNull(AndroidPermissionRegistry.getMapping(galleryIdentity), "Gallery must not be initialized before this cold-order test")

    val first = if (readStorageFirst) Permission.ReadStorage else Permission.Gallery
    assertEquals(Manifest.permission.READ_EXTERNAL_STORAGE,
        assertNotNull(AndroidPermissionRegistry.getMapping(first)).permissionString)
    assertNull(AndroidPermissionRegistry.getMapping(if (readStorageFirst) galleryIdentity else storageIdentity),
        "Initializing the first builtin must not accidentally initialize the other one")
    val second = if (readStorageFirst) Permission.Gallery else Permission.ReadStorage
    val storage = if (readStorageFirst) first else second
    val gallery = if (readStorageFirst) second else first
    assertSame(Permission.ReadStorage, storage)
    assertSame(Permission.Gallery, gallery)
    for (permission in listOf(storage, gallery)) {
        val mapping = assertNotNull(AndroidPermissionRegistry.getMapping(permission))
        assertEquals(Manifest.permission.READ_EXTERNAL_STORAGE, mapping.permissionString)
        assertEquals(32, mapping.maxSdkVersion)
    }
    if (sdk <= 32) {
        // The legacy reverse lookup really sees the first builtin. A Gallery-only
        // request must still use Gallery, and a both-alias request must update both.
        assertSame(first, AndroidPermissionRegistry.findByAndroidString(Manifest.permission.READ_EXTERNAL_STORAGE, sdk))
    }

    exerciseAliasRequest(listOf(gallery), Manifest.permission.READ_EXTERNAL_STORAGE, notRequired = sdk > 32)
    exerciseAliasRequest(listOf(storage, gallery), Manifest.permission.READ_EXTERNAL_STORAGE, notRequired = sdk > 32)

    val foreign = Permission("unrequested-custom-$sdk-$readStorageFirst")
    val customFirst = Permission("requested-custom-first-$sdk-$readStorageFirst")
    val customSecond = Permission("requested-custom-second-$sdk-$readStorageFirst")
    for (permission in listOf(foreign, customFirst, customSecond)) {
        AndroidPermissionRegistry.register(permission, AndroidPermissionMapping(Manifest.permission.CAMERA))
    }
    assertSame(foreign, AndroidPermissionRegistry.findByAndroidString(Manifest.permission.CAMERA, sdk))
    exerciseAliasRequest(listOf(customFirst, customSecond, customFirst), Manifest.permission.CAMERA, notRequired = false)
}

private suspend fun TestScope.exerciseAliasRequest(requested: List<Permission>, native: String, notRequired: Boolean) {
    val expected = requested.distinct()
    val host = AndroidPermissionCompositionTest.PermissionComposition(this)
    lateinit var state: MultiplePermissionsState
    val results = mutableListOf<Map<Permission, Boolean>>()
    host.deny(native)
    try {
        host.setContent {
            state = rememberMultiplePermissionsState(requested) { result ->
                assertEquals(expected.toSet(), result.keys, "Never include an unrequested global alias")
                for (permission in expected) {
                    assertSame(permission, result.keys.single { it == permission }, "Callback must retain the requested object identity")
                    val member = state.permissions.single { it.permission == permission }
                    assertSame(permission, member.permission)
                    assertEquals(result.getValue(permission), member.status.isGranted,
                        "Every requested alias must be refreshed before delivering the callback")
                }
                results += result
            }
        }
        assertEquals(expected, state.permissions.map { it.permission })
        if (expected.size == 2) assertNotSame(state.permissions[0], state.permissions[1])
        assertEquals(List(expected.size) { notRequired }, state.permissions.map { it.status.isGranted })
        if (notRequired) assertTrue(state.permissions.all { it.details.availability == PermissionAvailability.NotRequired })

        for (index in 0..1) {
            host.deny(native)
            state.launchMultiplePermissionRequest()
            if (!notRequired) {
                assertEquals(index, results.size, "Actual delayed results must not be invented before native delivery")
                assertEquals(index + 1, host.registry.launches.size)
                assertEquals(listOf(native), host.registry.launches[index].permissions, "Deduplicate the native permission, not logical aliases")
                if (index == 0) host.grant(native)
                host.registry.deliver(index, if (index == 0) setOf(native) else emptySet())
            }
            val granted = notRequired || index == 0
            assertEquals(index + 1, results.size)
            assertEquals(expected.associateWith { granted }, results.last())
            assertEquals(List(expected.size) { granted }, state.permissions.map { it.status.isGranted })
        }
        assertEquals(if (notRequired) 0 else 2, host.registry.launches.size)
    } finally {
        host.close()
    }
}
