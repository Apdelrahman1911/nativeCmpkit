// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.permissions

import android.os.Build
import androidx.test.platform.app.InstrumentationRegistry
import kotlin.test.*

/** Actual API/target/focus must match the predeclared finite profile; no latest-runtime proxy. */
internal object PermissionCompatibilityProfiles {
    const val BASE = "io.github.apdelrahman1911.nativecmpkit.verification.permissioncompat"
    const val REPORTER = "$BASE.reporter"
    data class Spec(val api: Int, val target: Int, val roles: Set<String>, val method: String)
    val profiles = mapOf(
        "android-permission-compat-api23-target23" to Spec(23, 23, setOf("fine", "coarse", "pair", "batch"), "freshFineCoarsePairAndBackgroundUseRealApiTargetDialogs"),
        "android-permission-compat-api23-target37" to Spec(23, 37, setOf("fine", "coarse", "pair", "batch"), "freshFineCoarsePairAndBackgroundUseRealApiTargetDialogs"),
        "android-permission-compat-api29-target28" to Spec(29, 28, setOf("fine", "coarse", "pair", "batch"), "freshFineCoarsePairAndBackgroundUseRealApiTargetDialogs"),
        "android-permission-compat-api29-target37" to Spec(29, 37, setOf("fine", "coarse", "pair", "batch"), "freshFineCoarsePairAndBackgroundUseRealApiTargetDialogs"),
        "android-permission-compat-api30-target29" to Spec(30, 29, setOf("fine", "coarse", "pair", "batch"), "freshFineCoarsePairAndBackgroundUseRealApiTargetDialogs"),
        "android-permission-compat-api30-target37" to Spec(30, 37, setOf("fine", "coarse", "pair", "batch"), "freshFineCoarsePairAndBackgroundUseRealApiTargetDialogs"),
        "android-permission-compat-api31-target30" to Spec(31, 30, setOf("fine", "coarse", "pair", "batch"), "freshFineCoarsePairAndBackgroundUseRealApiTargetDialogs"),
        "android-permission-compat-api31-target37" to Spec(31, 37, setOf("fine", "coarse", "pair", "batch"), "freshFineCoarsePairAndBackgroundUseRealApiTargetDialogs"),
        "android-permission-compat-api33-target32" to Spec(33, 32, setOf("fine", "coarse", "pair", "batch"), "freshFineCoarsePairAndBackgroundUseRealApiTargetDialogs"),
        "android-permission-compat-api33-target37" to Spec(33, 37, setOf("fine", "coarse", "pair", "batch"), "freshFineCoarsePairAndBackgroundUseRealApiTargetDialogs"),
        "android-permission-manifest-services-api35" to Spec(35, 37, setOf("omitted", "batch"), "manifestOmissionAndServicesOffKeepDifferentNativeAndPermissionSemantics"),
        "android-permission-camera-revoke-api35" to Spec(35, 37, setOf("camera"), "cameraSettingsRevocationRefreshesSingleBatchAtSameIdentity"),
        "android-permission-location-revoke-api35" to Spec(35, 37, setOf("fine"), "locationSettingsRevocationRefreshesSingleBatchAtSameIdentity"),
        "android-permission-pending-disposal-api35" to Spec(35, 37, setOf("camera"), "pendingNativeCameraDialogDisposalSuppressesRealLateResult"),
    )
    val allPermissions = setOf("android.permission.ACCESS_FINE_LOCATION", "android.permission.ACCESS_COARSE_LOCATION",
        "android.permission.ACCESS_BACKGROUND_LOCATION", "android.permission.CAMERA")
    val declarations = mapOf(
        "fine" to setOf("android.permission.ACCESS_FINE_LOCATION", "android.permission.ACCESS_COARSE_LOCATION"),
        "coarse" to setOf("android.permission.ACCESS_COARSE_LOCATION"),
        "pair" to setOf("android.permission.ACCESS_FINE_LOCATION", "android.permission.ACCESS_COARSE_LOCATION"),
        "batch" to setOf("android.permission.ACCESS_FINE_LOCATION", "android.permission.ACCESS_COARSE_LOCATION", "android.permission.ACCESS_BACKGROUND_LOCATION"),
        "omitted" to emptySet(), "camera" to setOf("android.permission.CAMERA"),
    )
    fun selected(): Pair<String, Spec> {
        val arguments = InstrumentationRegistry.getArguments()
        assertEquals("true", arguments.getString("nativecmpkitOwnedPermissionCompatibility"))
        val focus = assertNotNull(arguments.getString("nativecmpkitPermissionCompatibilityFocus"))
        val spec = assertNotNull(profiles[focus], "No broad/default/one-time-expiry profile is implemented")
        assertEquals(spec.api, Build.VERSION.SDK_INT)
        assertEquals(REPORTER, InstrumentationRegistry.getInstrumentation().targetContext.packageName)
        return focus to spec
    }
    fun requireMethod(method: String) { assertEquals(method, selected().second.method) }
}
