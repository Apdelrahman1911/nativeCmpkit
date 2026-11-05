// SPDX-License-Identifier: Apache-2.0
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)
package io.github.apdelrahman1911.nativecmpkit.verification.permissioncompat

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.location.LocationManager
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.ComposeView
import com.mohamedrejeb.calf.permissions.*
import java.util.UUID

/** Selected fresh helper role mounts real public library states, never a sample. */
class PermissionCompatibilityActivity : ComponentActivity() {
    private val activityGeneration = UUID.randomUUID().toString()
    private lateinit var content: ComposeView
    private var visible by mutableStateOf(true)
    private var mounted = false
    private var pauseCount = 0
    private var resumeCount = 0
    private var disposalCount = 0
    private var settingsOpens = 0
    private var lastSettingsAction: String? = null
    private var lastSettingsPackage: String? = null
    private var states: Map<String, PermissionState> = emptyMap()
    private var batch: MultiplePermissionsState? = null
    private data class Callback(var count: Int = 0, var result: Boolean? = null)
    private val callbacks = mutableMapOf<String, Callback>()
    private var batchCallbacks = 0
    private var batchResult: Map<Permission, Boolean>? = null
    private val frameworkResults = mutableListOf<Bundle>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        check(active == null && BuildConfig.VERIFICATION_ROLE in ROLES)
        check(packageName == BASE + "." + BuildConfig.VERIFICATION_ROLE)
        active = this
        content = ComposeView(this).apply {
            setContent {
                if (visible) {
                    val permissions = when (BuildConfig.VERIFICATION_ROLE) {
                        "fine" -> listOf(Permission.FineLocation)
                        "coarse" -> listOf(Permission.CoarseLocation)
                        "pair" -> listOf(Permission.FineLocation, Permission.CoarseLocation)
                        "batch", "omitted" -> listOf(Permission.FineLocation, Permission.CoarseLocation, Permission.BackgroundLocation)
                        "camera" -> listOf(Permission.Camera)
                        else -> error("Unknown exact verification role")
                    }
                    val singles = permissions.associate { permission ->
                        permission.name to rememberPermissionState(permission) { record(permission.name, it) }
                    }
                    val multiple = rememberMultiplePermissionsState(permissions) {
                        batchCallbacks++
                        batchResult = it.toMap()
                    }
                    SideEffect { states = singles; batch = multiple; mounted = true }
                    DisposableEffect(Unit) { onDispose { mounted = false; disposalCount++ } }
                    BasicText("NativeCmpKit public permission compatibility verification")
                } else BasicText("Owned permission composition disposed")
            }
        }
        setContentView(content)
    }

    private fun record(name: String, value: Boolean) {
        callbacks.getOrPut(name) { Callback() }.apply { count++; result = value }
    }

    override fun onPause() { pauseCount++; super.onPause() }
    override fun onResume() { super.onResume(); resumeCount++ }

    override fun startActivity(intent: Intent) {
        if (intent.action in setOf(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Settings.ACTION_LOCATION_SOURCE_SETTINGS)) {
            settingsOpens++
            lastSettingsAction = intent.action
            lastSettingsPackage = intent.data?.schemeSpecificPart
        }
        super.startActivity(intent)
    }

    @Deprecated("Observe the actual framework result before delegating; never manufacture it")
    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        check(permissions.size == grantResults.size && permissions.size <= 4 && frameworkResults.size < 8)
        check(permissions.toSet().size == permissions.size && permissions.all { it in NATIVE_PERMISSIONS })
        frameworkResults.add(Bundle().apply {
            putStringArray("permissions", permissions.toList().toTypedArray())
            putIntArray("results", grantResults.toList().toIntArray())
        })
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
    }

    fun perform(operation: String) {
        check(operation == "finish" || states.isNotEmpty())
        when (operation) {
            "request-fine" -> states.getValue("FineLocation").launchPermissionRequest()
            "request-coarse" -> states.getValue("CoarseLocation").launchPermissionRequest()
            "request-background" -> states.getValue("BackgroundLocation").launchPermissionRequest()
            "request-camera" -> states.getValue("Camera").launchPermissionRequest()
            "request-batch" -> { check(mounted); checkNotNull(batch).launchMultiplePermissionRequest() }
            "request-batch-retained" -> { check(!mounted && !visible); checkNotNull(batch).launchMultiplePermissionRequest() }
            "open-fine-settings" -> states.getValue("FineLocation").openAppSettings()
            "open-background-settings" -> states.getValue("BackgroundLocation").openAppSettings()
            "open-camera-settings" -> states.getValue("Camera").openAppSettings()
            "open-location-services" -> startActivity(Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS))
            "dispose-content" -> {
                check(mounted && visible)
                visible = false
                // Dispose the actual Compose view even while the permission dialog pauses
                // the host; never rely on a future frame or manufacture onDispose/state.
                content.disposeComposition()
            }
            "finish" -> { content.disposeComposition(); finish() }
            else -> error("Unknown finite native operation")
        }
    }

    private fun observation(state: PermissionState, callback: Callback?): Bundle = Bundle().apply {
        putBoolean("granted", state.status is PermissionStatus.Granted)
        putBoolean("rationale", (state.status as? PermissionStatus.Denied)?.shouldShowRationale ?: false)
        putString("availability", state.details.availability.name)
        putString("access", state.details.access.name)
        putString("requestability", state.details.requestability.name)
        state.details.lastRequest?.let { putString("lastRequest", it.name) }
        putInt("callbacks", callback?.count ?: 0)
        callback?.result?.let { putBoolean("callbackResult", it) }
    }

    fun snapshot(): Bundle = Bundle().apply {
        putString("activityGeneration", activityGeneration)
        putBoolean("mounted", mounted)
        putBoolean("resumed", lifecycle.currentState.isAtLeast(androidx.lifecycle.Lifecycle.State.RESUMED))
        putBoolean("focused", hasWindowFocus())
        putInt("pauseCount", pauseCount)
        putInt("resumeCount", resumeCount)
        putInt("disposalCount", disposalCount)
        putInt("settingsOpens", settingsOpens)
        putString("lastSettingsAction", lastSettingsAction)
        putString("lastSettingsPackage", lastSettingsPackage)
        for (permission in NATIVE_PERMISSIONS) {
            putBoolean(permission, checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED)
            putBoolean(permission + ".rationale", shouldShowRequestPermissionRationale(permission))
        }
        val manager = getSystemService(Context.LOCATION_SERVICE) as LocationManager
        putBoolean("locationServicesEnabled", if (Build.VERSION.SDK_INT >= 28) manager.isLocationEnabled
            else manager.isProviderEnabled(LocationManager.GPS_PROVIDER) || manager.isProviderEnabled(LocationManager.NETWORK_PROVIDER))
        putString("locationServiceObservation", if (Build.VERSION.SDK_INT >= 28) "isLocationEnabled" else "providerEnabled")
        for ((name, state) in states) putBundle(if (mounted) name else "retained.$name", observation(state, callbacks[name]))
        batch?.permissions?.forEach { putBundle("batch." + it.permission.name, observation(it, null)) }
        putInt("batchCallbacks", batchCallbacks)
        batchResult?.let { result -> putBundle("batchResult", Bundle().apply {
            for ((permission, granted) in result) putBoolean(permission.name, granted)
        }) }
        putParcelableArrayList("frameworkResults", ArrayList(frameworkResults.map(::Bundle)))
    }

    override fun onDestroy() {
        try { if (::content.isInitialized) content.disposeComposition() }
        catch (failure: Exception) { cleanupFailed = true; throw failure }
        finally { states = emptyMap(); batch = null; active = null; super.onDestroy() }
    }

    companion object {
        const val BASE = "io.github.apdelrahman1911.nativecmpkit.verification.permissioncompat"
        val ROLES = setOf("fine", "coarse", "pair", "batch", "omitted", "camera")
        val NATIVE_PERMISSIONS = setOf("android.permission.ACCESS_FINE_LOCATION", "android.permission.ACCESS_COARSE_LOCATION",
            "android.permission.ACCESS_BACKGROUND_LOCATION", "android.permission.CAMERA")
        var active: PermissionCompatibilityActivity? = null
            private set
        var cleanupFailed = false
            private set
    }
}
