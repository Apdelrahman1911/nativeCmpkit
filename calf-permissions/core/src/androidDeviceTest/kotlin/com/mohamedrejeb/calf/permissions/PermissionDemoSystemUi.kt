// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.permissions

import android.accessibilityservice.AccessibilityServiceInfo
import android.content.pm.ApplicationInfo
import android.os.SystemClock
import android.view.accessibility.AccessibilityNodeInfo
import androidx.test.platform.app.InstrumentationRegistry
import kotlin.test.*

/** Exact visible OS controls only: no Activity monitor, registry dispatch, coordinates or grants. */
internal class PermissionDemoSystemUi : AutoCloseable {
    companion object {
        val PERMISSION = setOf("com.android.permissioncontroller", "com.google.android.permissioncontroller")
        val DOCUMENTS = setOf("com.android.documentsui", "com.google.android.documentsui")
        val MEDIA = setOf("com.android.providers.media.module", "com.google.android.providers.media.module")
    }
    private val instrumentation = InstrumentationRegistry.getInstrumentation()
    private val automation = instrumentation.uiAutomation
    private val originalFlags = automation.serviceInfo.flags
    init {
        automation.serviceInfo = automation.serviceInfo.apply {
            flags = flags or AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS
        }
    }

    fun permissionButton(vararg ids: String) = clickId(PERMISSION, *ids)
    fun selectedPhoto() = clickId(MEDIA, "icon_thumbnail")
    fun confirmSelectedPhoto() = clickId(MEDIA, "button_add")
    fun document(name: String) {
        assertTrue(name.matches(Regex("nav015-[a-f0-9]{32}\\.txt")))
        click(DOCUMENTS, { root -> root.findAccessibilityNodeInfosByText(name) }, { it.text?.toString() == name })
    }

    fun permissionDialogVisible(): Boolean {
        val root = assertNotNull(automation.rootInActiveWindow, "An unavailable native window is not no dialog")
        try {
            val packageName = assertNotNull(root.packageName).toString()
            assertTrue(packageName == OwnedPermissionDemo.PACKAGE || packageName in PERMISSION,
                "A foreign active window cannot prove the owned request showed no dialog")
            assertTrue(root.refresh() && root.isVisibleToUser)
            return packageName in PERMISSION
        } finally { root.recycle() }
    }

    private fun clickId(packages: Set<String>, vararg ids: String) = click(packages, { root ->
        val packageName = assertNotNull(root.packageName).toString()
        ids.flatMap { root.findAccessibilityNodeInfosByViewId("$packageName:id/$it") }
    })

    private fun click(packages: Set<String>, nodes: (AccessibilityNodeInfo) -> List<AccessibilityNodeInfo>,
        selected: (AccessibilityNodeInfo) -> Boolean = { true }) {
        val deadline = SystemClock.elapsedRealtime() + 20000
        while (SystemClock.elapsedRealtime() < deadline) {
            val root = automation.rootInActiveWindow
            if (root != null) {
                try {
                    val packageName = root.packageName?.toString()
                    if (packageName in packages) {
                        val app = instrumentation.targetContext.packageManager.getApplicationInfo(checkNotNull(packageName), 0)
                        assertTrue(app.flags and (ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0)
                        val acquired = nodes(root)
                        try {
                            assertTrue(acquired.size <= 128, "The exact bounded node query returned an unexpected inventory")
                            val matches = acquired.filter { it.isVisibleToUser && selected(it) }
                            assertTrue(matches.size <= 1, "An ambiguous visible OS control must not be clicked")
                            if (matches.size == 1) {
                                var node = matches.single()
                                assertEquals(packageName, node.packageName?.toString())
                                assertTrue(node.refresh() && node.isVisibleToUser && selected(node))
                                val ancestors = mutableListOf<AccessibilityNodeInfo>()
                                try {
                                    while (!node.isClickable && ancestors.size < 6) {
                                        node = assertNotNull(node.parent).also { ancestors += it }
                                        assertEquals(packageName, node.packageName?.toString())
                                    }
                                    assertTrue(node.refresh() && node.isClickable && node.isEnabled && node.isVisibleToUser)
                                    assertTrue(node.performAction(AccessibilityNodeInfo.ACTION_CLICK))
                                    return
                                } finally { ancestors.forEach { it.recycle() } }
                            }
                        } finally { acquired.forEach { it.recycle() } }
                    }
                } finally { root.recycle() }
            }
            Thread.sleep(40)
        }
        fail("The exact required native OS control was not observed within the bound")
    }
    override fun close() { automation.serviceInfo = automation.serviceInfo.apply { flags = originalFlags } }
}
