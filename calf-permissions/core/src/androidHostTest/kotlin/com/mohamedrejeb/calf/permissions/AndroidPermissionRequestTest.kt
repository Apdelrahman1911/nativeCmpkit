@file:OptIn(ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions

import kotlin.test.*

class AndroidPermissionRequestTest {
    private val gallery = Permission("test-gallery")
    private val storage = Permission("test-storage")
    private val fine = Permission("test-fine")
    private val coarse = Permission("test-coarse")
    private val background = Permission("test-background")
    private val unknown = Permission("test-unknown")
    private val notRequired = Permission("test-notRequired")
    private val mappings = mapOf(
        gallery to AndroidPermissionMapping("storage", maxSdkVersion = 32),
        storage to AndroidPermissionMapping("storage", maxSdkVersion = 32),
        fine to AndroidPermissionMapping(AndroidPermissionRequestPlan.FINE),
        coarse to AndroidPermissionMapping(AndroidPermissionRequestPlan.COARSE),
        background to AndroidPermissionMapping(AndroidPermissionRequestPlan.BACKGROUND, minSdkVersion = 29),
        notRequired to AndroidPermissionMapping("", alwaysGranted = true),
    )
    private fun plan(permissions: List<Permission>, sdk: Int) = AndroidPermissionRequestPlan(permissions, sdk, mappings::get)

    @Test fun unknownIsDeniedButExplicitOrVersionedNoGateIsNotRequired() {
        val plan = plan(listOf(unknown, notRequired, storage), 33)
        assertEquals(mapOf(unknown to false, notRequired to true, storage to true), plan.results { false })
        assertEquals(PermissionAvailability.Unsupported, plan.snapshot(unknown, { false }, { false }).details.availability)
        assertEquals(PermissionAvailability.NotRequired, plan.snapshot(storage, { false }, { false }).details.availability)
    }

    @Test fun aliasesDeduplicateNativeRequestAndFanOutToExactRequestedNames() {
        val plan = plan(listOf(storage, gallery, storage), 32)
        assertEquals(listOf("storage"), plan.foregroundPermissions { false })
        assertEquals(mapOf(storage to true, gallery to true), plan.results { it == "storage" })
        assertEquals(mapOf(gallery to true), plan(listOf(gallery), 32).results { true })
    }

    @Test fun fineIncludesCoarseOnAndroid12AndDoesNotTreatApproximateAsPrecise() {
        val plan = plan(listOf(fine, coarse), 31)
        assertEquals(listOf(AndroidPermissionRequestPlan.COARSE, AndroidPermissionRequestPlan.FINE), plan.foregroundPermissions { false })
        val result = plan.results { it == AndroidPermissionRequestPlan.COARSE }
        assertEquals(mapOf(fine to false, coarse to true), result)
        assertEquals(PermissionAccess.Approximate, plan.snapshot(fine, { it == AndroidPermissionRequestPlan.COARSE }, { false }).details.access)
        assertEquals(PermissionAccess.Approximate, plan.snapshot(coarse, { it == AndroidPermissionRequestPlan.COARSE }, { false }).details.access)
    }

    @Test fun selectedPhotosExposeLimitedScopeWithoutPretendingToGrantFullRead() {
        val image = Permission("test-images")
        val plan = AndroidPermissionRequestPlan(listOf(image), 34) {
            AndroidPermissionMapping(android.Manifest.permission.READ_MEDIA_IMAGES)
        }
        val snapshot = plan.snapshot(image, { it == android.Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED }, { false })
        assertFalse(snapshot.status.isGranted)
        assertEquals(PermissionAccess.Limited, snapshot.details.access)
    }

    @Test fun android29BackgroundIsSeparateAndRequiresForeground() {
        val plan = plan(listOf(background, fine), 29)
        assertEquals(listOf(AndroidPermissionRequestPlan.FINE), plan.foregroundPermissions { false })
        assertTrue(plan.backgroundPermissions { false }.isEmpty())
        assertEquals(listOf(AndroidPermissionRequestPlan.BACKGROUND), plan.backgroundPermissions { it == AndroidPermissionRequestPlan.FINE })
    }

    @Test fun android30BackgroundIsSettingsOnlyWithoutImplicitEscalation() {
        val plan = plan(listOf(background), 30)
        assertTrue(plan.foregroundPermissions { false }.isEmpty())
        assertTrue(plan.backgroundPermissions { true }.isEmpty())
        assertEquals(PermissionRequestability.PrerequisiteRequired, plan.snapshot(background, { false }, { false }).details.requestability)
        assertEquals(PermissionRequestability.SettingsOnly, plan.snapshot(background, { it == AndroidPermissionRequestPlan.COARSE }, { false }).details.requestability)
    }

    @Test fun sdkBoundariesAndConstructorCompatibility() {
        val mapping = AndroidPermissionMapping("x", 23, 28, false)
        assertEquals("x", mapping.permissionString)
        fun result(sdk: Int) = AndroidPermissionRequestPlan(listOf(storage), sdk) { mapping }.results { false }.getValue(storage)
        assertTrue(result(22)); assertFalse(result(23)); assertFalse(result(28)); assertTrue(result(29))
    }

    @Test fun registryRejectsAmbiguousBlankButAllowsExplicitNoGate() {
        assertFailsWith<IllegalArgumentException> { AndroidPermissionRegistry.register(unknown, AndroidPermissionMapping("")) }
        assertFailsWith<IllegalArgumentException> { AndroidPermissionRegistry.register(unknown, AndroidPermissionMapping("x", 30, 20)) }
        AndroidPermissionRegistry.register(notRequired, AndroidPermissionMapping("", alwaysGranted = true))
        assertTrue(AndroidPermissionRegistry.getMapping(notRequired)!!.alwaysGranted)
    }

    @Test fun runnerCompletesEmptyAndAllFilteredWithoutNativeLaunch() {
        for (permissions in listOf(emptyList(), listOf(notRequired, unknown, storage))) {
            var result: Map<Permission, Boolean>? = null; var refreshes = 0
            val runner = AndroidPermissionRequestRunner({ plan(permissions, 33) }, { false }, { fail("native launch") }, { refreshes++ })
            runner.launch { assertEquals(1, refreshes); result = it }
            assertEquals(permissions.associateWith { it != unknown }, result)
        }
    }

    @Test fun runnerStagesNativeRequestsAndCompletesFullMapAfterRefresh() {
        val grants = mutableSetOf<String>(); val launches = mutableListOf<List<String>>()
        var result: Map<Permission, Boolean>? = null; var refreshed = false
        val runner = AndroidPermissionRequestRunner({ plan(listOf(gallery, storage, fine, background, unknown), 29) },
            grants::contains, { launches += it.toList() }, { refreshed = true })
        runner.launch { assertTrue(refreshed); result = it }
        assertEquals(listOf("storage", AndroidPermissionRequestPlan.FINE), launches.single())
        grants += launches.single()
        runner.onNativeResult(launches.single().associateWith { true })
        assertNull(result)
        assertEquals(listOf(AndroidPermissionRequestPlan.BACKGROUND), launches[1])
        grants += AndroidPermissionRequestPlan.BACKGROUND
        runner.onNativeResult(mapOf(AndroidPermissionRequestPlan.BACKGROUND to true))
        assertEquals(mapOf(gallery to true, storage to true, fine to true, background to true, unknown to false), result)
    }

    @Test fun cancelledNativeRequestStillCompletesEveryIdentityAndCanRelaunch() {
        var launches = 0; val results = mutableListOf<Map<Permission, Boolean>>()
        val runner = AndroidPermissionRequestRunner({ plan(listOf(gallery, storage, notRequired), 32) },
            { false }, { launches++ }, {})
        runner.launch { results += it }; runner.onNativeResult(emptyMap())
        runner.launch { results += it }; runner.onNativeResult(mapOf("storage" to false))
        assertEquals(2, launches)
        assertEquals(List(2) { mapOf(gallery to false, storage to false, notRequired to true) }, results)
    }

    @Test fun disposingRunnerSuppressesOldResults() {
        val runner = AndroidPermissionRequestRunner({ plan(listOf(fine), 31) }, { false }, {}, {})
        runner.launch { fail("disposed owner callback") }
        runner.dispose()
        runner.onNativeResult(emptyMap())
    }
}
