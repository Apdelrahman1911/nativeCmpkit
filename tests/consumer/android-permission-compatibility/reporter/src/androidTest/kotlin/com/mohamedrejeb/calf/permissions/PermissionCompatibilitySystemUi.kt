// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.permissions

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.pm.ApplicationInfo
import android.os.Build
import android.os.SystemClock
import android.view.accessibility.AccessibilityNodeInfo
import androidx.test.platform.app.InstrumentationRegistry
import java.util.Locale
import kotlin.test.*

/** Finite SDK/en native selectors. Unknown/stale/foreign/ambiguous never means success. */
internal class PermissionCompatibilitySystemUi : AutoCloseable {
    private val instrumentation = InstrumentationRegistry.getInstrumentation()
    private val automation = instrumentation.uiAutomation
    private val originalFlags = automation.serviceInfo.flags
    private val permissions = if (Build.VERSION.SDK_INT == 23)
        setOf("com.android.packageinstaller", "com.google.android.packageinstaller")
        else setOf("com.android.permissioncontroller", "com.google.android.permissioncontroller")
    private val settings = permissions + "com.android.settings"
    init {
        PermissionCompatibilityProfiles.selected()
        assertEquals("en", Locale.getDefault().language)
        automation.serviceInfo = automation.serviceInfo.apply {
            flags = flags or AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS
        }
    }

    fun locationGrant(preciseChoice: Boolean?) {
        val deadline = SystemClock.elapsedRealtime() + 15000
        if (preciseChoice != null) {
            assertTrue(Build.VERSION.SDK_INT >= 31)
            clickIds(permissions, deadline, if (preciseChoice) "permission_location_accuracy_radio_fine" else "permission_location_accuracy_radio_coarse")
        }
        clickIds(permissions, deadline, if (Build.VERSION.SDK_INT >= 29) "permission_allow_foreground_only_button" else "permission_allow_button")
    }

    fun cameraGrant() = clickIds(permissions, SystemClock.elapsedRealtime() + 15000,
        if (Build.VERSION.SDK_INT >= 30) "permission_allow_foreground_only_button" else "permission_allow_button")

    fun denyRuntime() = clickIds(permissions, SystemClock.elapsedRealtime() + 15000, "permission_deny_button")

    fun assertPermissionDialog() {
        awaitRoot(permissions, SystemClock.elapsedRealtime() + 15000) { root, pkg ->
            val acquired = root.findAccessibilityNodeInfosByViewId("$pkg:id/permission_deny_button")
            try {
                val matches = acquired.filter { it.refresh() && it.isVisibleToUser && it.isEnabled }
                assertTrue(matches.size <= 1)
                matches.size == 1
            } finally { acquired.forEach { it.recycle() } }
        }
    }

    fun permissionSetting(group: String, decision: String) {
        val deadline = SystemClock.elapsedRealtime() + 15000
        val manager = instrumentation.targetContext.packageManager
        val label = manager.getPermissionGroupInfo(group, 0).loadLabel(manager).toString()
        clickText(setOf("com.android.settings"), deadline, "Permissions")
        clickText(settings, deadline, label)
        when (decision) {
            "background-grant" -> {
                assertTrue(Build.VERSION.SDK_INT >= 29)
                clickIds(permissions, deadline, "allow_always_radio_button", "always_radio_button")
            }
            "foreground-only" -> {
                assertTrue(Build.VERSION.SDK_INT >= 29)
                clickIds(permissions, deadline, "allow_foreground_only_radio_button", "foreground_only_radio_button")
            }
            "deny" -> {
                assertEquals(35, Build.VERSION.SDK_INT)
                clickIds(permissions, deadline, "deny_radio_button", "no_access_radio_button")
            }
            "camera-grant" -> {
                assertEquals(35, Build.VERSION.SDK_INT)
                clickIds(permissions, deadline, "allow_foreground_only_radio_button", "foreground_only_radio_button")
            }
            else -> fail("Unregistered finite native Settings decision")
        }
    }

    fun setLocationServices(enabled: Boolean) {
        assertEquals(35, Build.VERSION.SDK_INT)
        val deadline = SystemClock.elapsedRealtime() + 15000
        var observed: Boolean? = null
        awaitRoot(setOf("com.android.settings"), deadline) { root, _ ->
            val acquired = switchNodes(root)
            try {
                check(acquired.size <= 256)
                val matches = acquired.filter { it.refresh() && it.isVisibleToUser && it.isEnabled && it.isCheckable }
                assertTrue(matches.size <= 1, "Ambiguous location-services switch")
                if (matches.size != 1) return@awaitRoot false
                observed = matches.single().isChecked
                true
            } finally { acquired.forEach { it.recycle() } }
        }
        if (assertNotNull(observed) != enabled) {
            click(setOf("com.android.settings"), deadline, { root, _ -> switchNodes(root) },
                { it.isCheckable && it.isChecked != enabled }, requireChecked = !enabled)
        }
        awaitRoot(setOf("com.android.settings"), deadline) { root, _ ->
            val acquired = switchNodes(root)
            try {
                check(acquired.size <= 256)
                val matches = acquired.filter { it.refresh() && it.isVisibleToUser && it.isEnabled && it.isCheckable }
                assertTrue(matches.size <= 1)
                matches.size == 1 && matches.single().isChecked == enabled
            } finally { acquired.forEach { it.recycle() } }
        }
    }

    private fun switchNodes(root: AccessibilityNodeInfo): List<AccessibilityNodeInfo> =
        root.findAccessibilityNodeInfosByViewId("com.android.settings:id/switch_widget") + root.findAccessibilityNodeInfosByViewId("android:id/switch_widget")

    fun assertOwnedHost(packageName: String) {
        requireOwned(packageName)
        awaitRoot(setOf(packageName), SystemClock.elapsedRealtime() + 10000) { _, _ -> true }
    }

    fun backToOwned(packageName: String) {
        requireOwned(packageName)
        val deadline = SystemClock.elapsedRealtime() + 15000
        var backs = 0
        while (SystemClock.elapsedRealtime() < deadline) {
            val root = automation.rootInActiveWindow
            try {
                if (root != null && root.refresh() && root.isVisibleToUser) {
                    val pkg = assertNotNull(root.packageName).toString()
                    if (pkg == packageName) return
                    assertTrue(pkg in settings, "Foreign window is not an owned Settings return")
                    assertSystem(pkg)
                    check(backs++ < 5)
                    check(SystemClock.elapsedRealtime() < deadline)
                    assertTrue(automation.performGlobalAction(AccessibilityService.GLOBAL_ACTION_BACK))
                    val remaining = deadline - SystemClock.elapsedRealtime()
                    check(remaining > 0)
                    automation.waitForIdle(250, minOf(4000L, remaining))
                }
            } finally { root?.recycle() }
            sleepBefore(deadline)
        }
        fail("Exact owned Activity did not return after bounded native Back")
    }

    private fun requireOwned(packageName: String) {
        val selected = PermissionCompatibilityProfiles.selected().second
        assertTrue(selected.roles.any { packageName == PermissionCompatibilityProfiles.BASE + "." + it })
    }

    private fun clickIds(packages: Set<String>, deadline: Long, vararg ids: String) =
        click(packages, deadline, { root, pkg -> ids.flatMap { root.findAccessibilityNodeInfosByViewId("$pkg:id/$it") } },
            { node -> ids.any { node.viewIdResourceName?.endsWith(":id/$it") == true } })

    private fun clickText(packages: Set<String>, deadline: Long, label: String) =
        click(packages, deadline, { root, _ -> root.findAccessibilityNodeInfosByText(label) }, { it.text?.toString() == label })

    private fun click(packages: Set<String>, deadline: Long,
                      query: (AccessibilityNodeInfo, String) -> List<AccessibilityNodeInfo>,
                      selected: (AccessibilityNodeInfo) -> Boolean, requireChecked: Boolean? = null) {
        awaitRoot(packages, deadline) { root, pkg ->
            val acquired = query(root, pkg)
            try {
                check(acquired.size <= 256)
                val matches = acquired.filter { it.refresh() && it.isVisibleToUser && selected(it) }
                assertTrue(matches.size <= 1, "Ambiguous native OS control")
                if (matches.isEmpty()) return@awaitRoot false
                var node = matches.single()
                assertEquals(pkg, node.packageName?.toString())
                assertTrue(node.refresh() && node.isVisibleToUser && selected(node))
                if (requireChecked != null) assertEquals(requireChecked, node.isChecked)
                val ancestors = mutableListOf<AccessibilityNodeInfo>()
                try {
                    while (!node.isClickable && ancestors.size < 6) {
                        node = assertNotNull(node.parent).also { ancestors += it }
                        assertEquals(pkg, node.packageName?.toString())
                    }
                    assertTrue(node.refresh() && node.isVisibleToUser && node.isEnabled && node.isClickable)
                    check(SystemClock.elapsedRealtime() < deadline)
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
                    val pkg = root.packageName?.toString()
                    if (pkg in packages) {
                        val actualPackage = assertNotNull(pkg)
                        if (!actualPackage.startsWith(PermissionCompatibilityProfiles.BASE + ".")) assertSystem(actualPackage)
                        check(SystemClock.elapsedRealtime() < deadline)
                        if (action(root, actualPackage)) {
                            check(SystemClock.elapsedRealtime() < deadline)
                            return
                        }
                    }
                }
            } finally { root?.recycle() }
            sleepBefore(deadline)
        }
        fail("Exact fresh required OS window/control not observed before its absolute deadline")
    }

    private fun assertSystem(pkg: String) {
        val info = instrumentation.targetContext.packageManager.getApplicationInfo(pkg, 0)
        assertTrue(info.flags and (ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0)
    }

    private fun sleepBefore(deadline: Long) {
        val remaining = deadline - SystemClock.elapsedRealtime()
        check(remaining > 0)
        Thread.sleep(minOf(40L, remaining))
    }

    override fun close() { automation.serviceInfo = automation.serviceInfo.apply { flags = originalFlags } }
}
