// SPDX-License-Identifier: Apache-2.0
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)
package io.github.apdelrahman1911.nativecmpkit.verification.permissionlifecycle

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
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

/** A real owned ComponentActivity mounting the public permission API. */
class PermissionLifecycleActivity : ComponentActivity() {
    private val activityGeneration = UUID.randomUUID().toString()
    private lateinit var content: ComposeView
    private var contentVisible by mutableStateOf(true)
    private var mounted = false
    private var pauseCount = 0
    private var resumeCount = 0
    private var disposalCount = 0
    private var settingsOpens = 0
    private var lastSettingsAction: String? = null
    private var lastSettingsPackage: String? = null
    private var states: Map<String, PermissionState> = emptyMap()
    private var locationBatch: MultiplePermissionsState? = null
    private var lifecycleBatch: MultiplePermissionsState? = null
    private data class Callback(var count: Int = 0, var result: Boolean? = null)
    private val callbacks = mutableMapOf<String, Callback>()
    private var locationCallbacks = 0
    private var locationResult: Map<Permission, Boolean>? = null
    private var lifecycleCallbacks = 0
    private var lifecycleResult: Map<Permission, Boolean>? = null
    private val nativePermissionResults = mutableListOf<Bundle>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        check(active == null)
        active = this
        content = ComposeView(this).apply {
            setContent {
                if (contentVisible) {
                    val fine = rememberPermissionState(Permission.FineLocation) { record("FineLocation", it) }
                    val coarse = rememberPermissionState(Permission.CoarseLocation) { record("CoarseLocation", it) }
                    val background = rememberPermissionState(Permission.BackgroundLocation) { record("BackgroundLocation", it) }
                    val camera = rememberPermissionState(Permission.Camera) { record("Camera", it) }
                    val notification = rememberPermissionState(Permission.Notification) { record("Notification", it) }
                    val locations = rememberMultiplePermissionsState(
                        listOf(Permission.FineLocation, Permission.CoarseLocation, Permission.BackgroundLocation)
                    ) { locationCallbacks++; locationResult = it.toMap() }
                    val lifecycle = rememberMultiplePermissionsState(
                        listOf(Permission.Camera, Permission.Notification)
                    ) { lifecycleCallbacks++; lifecycleResult = it.toMap() }
                    SideEffect {
                        states = mapOf("FineLocation" to fine, "CoarseLocation" to coarse,
                            "BackgroundLocation" to background, "Camera" to camera, "Notification" to notification)
                        locationBatch = locations
                        lifecycleBatch = lifecycle
                        mounted = true
                    }
                    DisposableEffect(Unit) {
                        onDispose { mounted = false; disposalCount++ }
                    }
                    BasicText("NativeCmpKit permission lifecycle verification")
                } else {
                    BasicText("Owned library permission composition disposed")
                }
            }
        }
        setContentView(content)
    }

    private fun record(name: String, value: Boolean) {
        callbacks.getOrPut(name) { Callback() }.apply { count++; result = value }
    }

    override fun onPause() {
        pauseCount++
        super.onPause()
    }

    override fun onResume() {
        super.onResume()
        resumeCount++
    }

    override fun startActivity(intent: Intent) {
        if (intent.action in setOf(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Settings.ACTION_APP_NOTIFICATION_SETTINGS)) {
            settingsOpens++
            lastSettingsAction = intent.action
            lastSettingsPackage = if (intent.action == Settings.ACTION_APP_NOTIFICATION_SETTINGS)
                intent.getStringExtra(Settings.EXTRA_APP_PACKAGE) else intent.data?.schemeSpecificPart
        }
        super.startActivity(intent)
    }

    @Deprecated("Observe and delegate the genuine framework callback only")
    override fun onRequestPermissionsResult(
        requestCode: Int, permissions: Array<out String>, grantResults: IntArray,
    ) {
        check(permissions.size == grantResults.size && permissions.size <= 5 && nativePermissionResults.size < 8)
        check(permissions.toSet().size == permissions.size && permissions.all { it in NATIVE_PERMISSIONS })
        nativePermissionResults.add(Bundle().apply {
            putStringArray("permissions", permissions.toList().toTypedArray())
            putIntArray("results", grantResults.toList().toIntArray())
        })
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
    }

    fun perform(operation: String) {
        check(operation == "finish" || states.size == 5)
        when (operation) {
            "request-fine" -> states.getValue("FineLocation").launchPermissionRequest()
            "request-coarse" -> states.getValue("CoarseLocation").launchPermissionRequest()
            "request-background" -> states.getValue("BackgroundLocation").launchPermissionRequest()
            "request-location-batch" -> checkNotNull(locationBatch).launchMultiplePermissionRequest()
            "request-notification" -> states.getValue("Notification").launchPermissionRequest()
            "open-camera-settings" -> states.getValue("Camera").openAppSettings()
            "open-notification-settings" -> states.getValue("Notification").openAppSettings()
            "dispose-content" -> { check(mounted && contentVisible); contentVisible = false }
            "finish" -> { content.disposeComposition(); finish() }
            else -> error("Unregistered native operation")
        }
    }

    private fun stateSnapshot(state: PermissionState, name: String, callback: Callback?): Bundle = Bundle().apply {
        putString("name", name)
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
        for ((name, state) in states) {
            putBundle(if (mounted) name else "retained.$name", stateSnapshot(state, name, callbacks[name]))
        }
        for (batch in listOfNotNull(locationBatch, lifecycleBatch)) {
            for (state in batch.permissions) putBundle("batch." + state.permission.name,
                stateSnapshot(state, state.permission.name, null))
        }
        putInt("locationCallbacks", locationCallbacks)
        locationResult?.let { result -> putBundle("locationResult", Bundle().apply {
            for ((permission, granted) in result) putBoolean(permission.name, granted)
        }) }
        putInt("lifecycleCallbacks", lifecycleCallbacks)
        lifecycleResult?.let { result -> putBundle("lifecycleResult", Bundle().apply {
            for ((permission, granted) in result) putBoolean(permission.name, granted)
        }) }
        putParcelableArrayList("nativePermissionResults", ArrayList(nativePermissionResults.map(::Bundle)))
    }

    override fun onDestroy() {
        try { if (::content.isInitialized) content.disposeComposition() }
        catch (failure: Exception) { cleanupFailed = true; throw failure }
        finally {
            states = emptyMap()
            locationBatch = null
            lifecycleBatch = null
            active = null
            super.onDestroy()
        }
    }

    companion object {
        var active: PermissionLifecycleActivity? = null
            private set
        var cleanupFailed = false
            private set
        val NATIVE_PERMISSIONS = listOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION,
            Manifest.permission.ACCESS_BACKGROUND_LOCATION, Manifest.permission.CAMERA, Manifest.permission.POST_NOTIFICATIONS)
    }
}
