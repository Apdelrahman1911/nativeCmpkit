// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.permissions

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.pm.ApplicationInfo
import android.os.SystemClock
import android.view.accessibility.AccessibilityNodeInfo
import androidx.test.platform.app.InstrumentationRegistry
import java.util.Locale
import kotlin.test.*

/** Exact, fresh native API35/en controls; unknown/foreign/stale/ambiguous is not success. */
internal class PermissionLifecycleSystemUi : AutoCloseable {
    private val instrumentation = InstrumentationRegistry.getInstrumentation()
    private val automation = instrumentation.uiAutomation
    private val originalFlags = automation.serviceInfo.flags
    private val permissionPackages = setOf("com.android.permissioncontroller", "com.google.android.permissioncontroller")
    private val settingsPackages = permissionPackages + "com.android.settings"
    init {
        assertEquals("en", Locale.getDefault().language, "This finite Settings selector has only an English native contract")
        automation.serviceInfo = automation.serviceInfo.apply {
            flags = flags or AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS
        }
    }

    fun locationGrant(precise: Boolean) {
        val deadline = SystemClock.elapsedRealtime() + 15000
        clickIds(permissionPackages, deadline,
            if (precise) "permission_location_accuracy_radio_fine" else "permission_location_accuracy_radio_coarse")
        clickIds(permissionPackages, deadline, "permission_allow_foreground_only_button")
    }

    fun notificationGrant() = clickIds(permissionPackages, SystemClock.elapsedRealtime() + 15000, "permission_allow_button")

    fun cameraGrant() {
        val deadline = SystemClock.elapsedRealtime() + 15000
        clickText(setOf("com.android.settings"), deadline, "Permissions")
        val camera = instrumentation.targetContext.packageManager
            .getPermissionGroupInfo("android.permission-group.CAMERA", 0)
            .loadLabel(instrumentation.targetContext.packageManager).toString()
        clickText(settingsPackages, deadline, camera)
        clickIds(permissionPackages, deadline, "allow_foreground_only_radio_button", "foreground_only_radio_button")
    }

    fun notificationToggle(enabled: Boolean) {
        val deadline = SystemClock.elapsedRealtime() + 15000
        click(setOf("com.android.settings"), deadline, { root, _ ->
            root.findAccessibilityNodeInfosByViewId("com.android.settings:id/switch_widget") +
                root.findAccessibilityNodeInfosByViewId("android:id/switch_widget")
        }, { node -> node.isCheckable && node.isChecked != enabled }, requireChecked = !enabled)
        // Reacquire/read the actual OS switch after the click; the library/native permission
        // and same-process observations are separate mandatory assertions in the test.
        awaitRoot(setOf("com.android.settings"), deadline) { root, _ ->
            val acquired = root.findAccessibilityNodeInfosByViewId("com.android.settings:id/switch_widget") +
                root.findAccessibilityNodeInfosByViewId("android:id/switch_widget")
            try {
                val matches = acquired.filter { node -> node.refresh() && node.isVisibleToUser && node.isEnabled && node.isCheckable }
                assertTrue(matches.size <= 1, "An ambiguous native notification switch is unverified")
                matches.size == 1 && matches.single().isChecked == enabled
            } finally { acquired.forEach { it.recycle() } }
        }
    }

    fun assertSettingsVisible() {
        awaitRoot(settingsPackages, SystemClock.elapsedRealtime() + 15000) { _, _ -> true }
    }

    fun assertOwnedHost() {
        awaitRoot(setOf(OwnedPermissionLifecycle.PACKAGE), SystemClock.elapsedRealtime() + 10000) { _, _ -> true }
    }

    fun backToOwned() {
        val deadline = SystemClock.elapsedRealtime() + 15000
        var backs = 0
        while (SystemClock.elapsedRealtime() < deadline) {
            val root = automation.rootInActiveWindow
            try {
                if (root != null && root.refresh() && root.isVisibleToUser) {
                    val packageName = assertNotNull(root.packageName).toString()
                    if (packageName == OwnedPermissionLifecycle.PACKAGE) return
                    assertTrue(packageName in settingsPackages, "A foreign window cannot be navigated as the owned Settings round trip")
                    assertSystem(packageName)
                    check(backs++ < 5) { "The original Activity did not return after the bounded native Back sequence" }
                    check(SystemClock.elapsedRealtime() < deadline)
                    assertTrue(automation.performGlobalAction(AccessibilityService.GLOBAL_ACTION_BACK))
                    val remaining = deadline - SystemClock.elapsedRealtime()
                    check(remaining > 0) { "Native Back exceeded its original deadline" }
                    // Observe actual OS idleness before another fresh root/Back. Never spam
                    // Back against a stale in-flight Settings transition and close the host.
                    automation.waitForIdle(250, minOf(4000L, remaining))
                }
            } finally { root?.recycle() }
            sleepBefore(deadline, 40)
        }
        fail("The original owned Activity was not observed after native Settings Back")
    }

    private fun clickIds(packages: Set<String>, deadline: Long, vararg ids: String) =
        click(packages, deadline, { root, packageName ->
            ids.flatMap { root.findAccessibilityNodeInfosByViewId("$packageName:id/$it") }
        }, { node -> ids.any { node.viewIdResourceName?.endsWith(":id/$it") == true } })

    private fun clickText(packages: Set<String>, deadline: Long, label: String) =
        click(packages, deadline, { root, _ -> root.findAccessibilityNodeInfosByText(label) }, { node -> node.text?.toString() == label })

    private fun click(
        packages: Set<String>, deadline: Long,
        query: (AccessibilityNodeInfo, String) -> List<AccessibilityNodeInfo>,
        selected: (AccessibilityNodeInfo) -> Boolean, requireChecked: Boolean? = null,
    ) {
        awaitRoot(packages, deadline) { root, packageName ->
            val acquired = query(root, packageName)
            try {
                check(acquired.size <= 256) { "Unbounded native OS control query" }
                val matches = acquired.filter { node -> node.refresh() && node.isVisibleToUser && selected(node) }
                assertTrue(matches.size <= 1, "An ambiguous native control must not be clicked")
                if (matches.isEmpty()) return@awaitRoot false
                assertEquals(1, matches.size)
                var node = matches.single()
                assertEquals(packageName, node.packageName?.toString())
                assertTrue(node.refresh() && node.isVisibleToUser && selected(node))
                if (requireChecked != null) assertEquals(requireChecked, node.isChecked)
                val ancestors = mutableListOf<AccessibilityNodeInfo>()
                try {
                    while (!node.isClickable && ancestors.size < 6) {
                        node = assertNotNull(node.parent).also { ancestors += it }
                        assertEquals(packageName, node.packageName?.toString())
                    }
                    assertTrue(node.refresh() && node.isVisibleToUser && node.isEnabled && node.isClickable)
                    check(SystemClock.elapsedRealtime() < deadline) { "Late native control cannot meet its original deadline" }
                    assertTrue(node.performAction(AccessibilityNodeInfo.ACTION_CLICK))
                    true
                } finally { ancestors.forEach { it.recycle() } }
            } finally { acquired.forEach { it.recycle() } }
        }
    }

    private fun awaitRoot(packages: Set<String>, deadline: Long, action: (AccessibilityNodeInfo, String) -> Boolean) {
        while (SystemClock.elapsedRealtime() < deadline) {
            val root = automation.rootInActiveWindow
            try {
                if (root != null && root.refresh() && root.isVisibleToUser) {
                    val packageName = root.packageName?.toString()
                    if (packageName in packages) {
                        if (packageName != OwnedPermissionLifecycle.PACKAGE) assertSystem(assertNotNull(packageName))
                        check(SystemClock.elapsedRealtime() < deadline)
                        if (action(root, assertNotNull(packageName))) {
                            check(SystemClock.elapsedRealtime() < deadline) { "Late native window/action is unverified" }
                            return
                        }
                    }
                }
            } finally { root?.recycle() }
            sleepBefore(deadline, 40)
        }
        fail("The exact fresh required OS control was not observed before the absolute deadline")
    }

    private fun assertSystem(packageName: String) {
        val app = instrumentation.targetContext.packageManager.getApplicationInfo(packageName, 0)
        assertTrue(app.flags and (ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0)
    }

    private fun sleepBefore(deadline: Long, millis: Long) {
        val remaining = deadline - SystemClock.elapsedRealtime()
        check(remaining > 0) { "Original native UI deadline expired" }
        Thread.sleep(minOf(millis, remaining))
    }

    override fun close() { automation.serviceInfo = automation.serviceInfo.apply { flags = originalFlags } }
}
