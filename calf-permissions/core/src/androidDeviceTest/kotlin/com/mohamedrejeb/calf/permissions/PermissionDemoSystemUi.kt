// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.permissions

import android.Manifest
import android.os.Bundle
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
    fun permissionButtonAfterRequest(request: Bundle, permission: String, vararg ids: String) =
        clickId(PERMISSION, *ids, requestFacts = requestReplyFacts(request, permission))
    fun selectedPhoto() = clickId(MEDIA, "icon_thumbnail")
    fun confirmSelectedPhoto() = clickId(MEDIA, "button_add")
    fun document(name: String) {
        assertTrue(name.matches(Regex("nav015-[a-f0-9]{32}\\.txt")))
        click(DOCUMENTS, { root -> root.findAccessibilityNodeInfosByText(name) }, { it.text?.toString() == name })
    }

    // This is the already validated reply immediately after the public method returned,
    // not proof of native dispatch, a later callback, a visible dialog or a grant.
    private fun requestReplyFacts(request: Bundle, permission: String): String {
        val kind = when (permission) {
            Manifest.permission.CALL_PHONE -> 1
            Manifest.permission.RECORD_AUDIO -> 2
            else -> error("Only the two owned permission request observations are allowed")
        }
        val state = request.get(if (kind == 1) "Call" else "RecordAudio") as? Bundle
        val callbacks = (state?.get("callbacks") as? Int)?.let {
            if (it >= 0) minOf(it, 4) else -1
        } ?: -1
        return "requestReplyKind=$kind,requestReplyReturned=1," +
            "requestReplyGrant=${diagnosticBoolean(request.get(permission))}," +
            "requestReplyRationale=${diagnosticBoolean(request.get(permission + ".rationale"))}," +
            "requestReplyCallbacksCapped4=$callbacks," +
            "requestReplyResumed=${diagnosticBoolean(request.get("resumed"))}," +
            "requestReplyFocused=${diagnosticBoolean(request.get("focused"))}"
    }
    private fun diagnosticBoolean(value: Any?): Int = when (value as? Boolean) {
        true -> 1
        false -> 0
        null -> -1
    }

    enum class PermissionDialogKind { UNKNOWN, PRESENT, OWNED_VISIBLE_HOST }
    data class PermissionDialogObservation(
        val kind: PermissionDialogKind,
        // 1 null; 2 missing package; 4 owned host; 8 allowed OS; 16 foreign; 32 unrefreshed.
        val windowKind: Int,
        // -1 unobserved; 0 observed false; 1 observed true. Never a no-dialog Boolean.
        val refreshed: Int,
        val visible: Int,
    )

    fun permissionDialogObservation(deadline: Long): PermissionDialogObservation {
        requireObservationDeadline(deadline)
        // Reacquire the active root each time; do not enumerate windows or clear the OS cache.
        val root = automation.rootInActiveWindow
        try {
            requireObservationDeadline(deadline)
            if (root == null) return PermissionDialogObservation(PermissionDialogKind.UNKNOWN, 1, -1, -1)
            val refreshed = root.refresh()
            // A failed refresh leaves visibility unobserved, not a false absence result.
            val visible = if (refreshed) root.isVisibleToUser else null
            requireObservationDeadline(deadline, if (refreshed) 1 else 0, diagnosticBoolean(visible))
            if (!refreshed) return PermissionDialogObservation(PermissionDialogKind.UNKNOWN, 32, 0, -1)
            // Read identity only after the cache-bypassing refresh succeeded.
            val packageName = root.packageName?.toString()
            val windowKind = when {
                packageName == null -> 2
                packageName == OwnedPermissionDemo.PACKAGE -> 4
                packageName in PERMISSION -> 8
                else -> 16
            }
            val unknown = PermissionDialogObservation(PermissionDialogKind.UNKNOWN, windowKind, 1,
                diagnosticBoolean(visible))
            if (visible != true) return unknown
            if (packageName in PERMISSION) {
                val app = instrumentation.targetContext.packageManager.getApplicationInfo(checkNotNull(packageName), 0)
                assertTrue(app.flags and (ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0,
                    "A non-system permission package cannot prove the current native window")
                requireObservationDeadline(deadline, 1, 1)
                return unknown.copy(kind = PermissionDialogKind.PRESENT)
            }
            requireObservationDeadline(deadline, 1, 1)
            return if (packageName == OwnedPermissionDemo.PACKAGE)
                unknown.copy(kind = PermissionDialogKind.OWNED_VISIBLE_HOST) else unknown
        } finally { root?.recycle() }
    }

    private fun requireObservationDeadline(deadline: Long, refreshed: Int = -1, visible: Int = -1) {
        check(SystemClock.elapsedRealtime() < deadline) {
            "A late native window read cannot certify the original no-dialog deadline; " +
                "refresh=$refreshed,visible=$visible"
        }
    }

    private fun clickId(packages: Set<String>, vararg ids: String,
        requestFacts: String = "requestReplyReturned=-1") = click(packages, { root ->
        val packageName = assertNotNull(root.packageName).toString()
        if (packages == PERMISSION) {
            // Android 15 PermissionController retains its R namespace, not the window app package.
            val resources = instrumentation.targetContext.packageManager.getResourcesForApplication(packageName)
            val resourcePackage = "com.android.permissioncontroller"
            val resourceNames = ids.map { id ->
                val expected = "$resourcePackage:id/$id"
                val resourceId = resources.getIdentifier(id, "id", resourcePackage)
                assertTrue(resourceId != 0, "The original permission control resource is unavailable")
                assertTrue(resources.getResourceName(resourceId) == expected,
                    "The permission control resource namespace is not exact")
                expected
            }
            resourceNames.flatMap { root.findAccessibilityNodeInfosByViewId(it) }
        } else {
            ids.flatMap { root.findAccessibilityNodeInfosByViewId("$packageName:id/$it") }
        }
    }, requestFacts = requestFacts)

    private fun click(packages: Set<String>, nodes: (AccessibilityNodeInfo) -> List<AccessibilityNodeInfo>,
        selected: (AccessibilityNodeInfo) -> Boolean = { true },
        requestFacts: String = "requestReplyReturned=-1") {
        val deadline = SystemClock.elapsedRealtime() + 20000
        var samples = 0
        var windowKinds = 0 // 1 null root; 2 missing package; 4 owned app; 8 allowed OS; 16 other.
        var exactQueries = 0
        var maxExactQueryNodes = -1 // Unknown is not an observed empty query.
        var maxVisibleMatches = -1
        while (SystemClock.elapsedRealtime() < deadline) {
            samples = minOf(samples + 1, 512)
            val root = automation.rootInActiveWindow
            if (root != null) {
                try {
                    val packageName = root.packageName?.toString()
                    windowKinds = windowKinds or when {
                        packageName == null -> 2
                        packageName in packages -> 8
                        packageName == OwnedPermissionDemo.PACKAGE -> 4
                        else -> 16
                    }
                    if (packageName in packages) {
                        val app = instrumentation.targetContext.packageManager.getApplicationInfo(checkNotNull(packageName), 0)
                        assertTrue(app.flags and (ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0)
                        val acquired = nodes(root)
                        try {
                            assertTrue(acquired.size <= 128, "The exact bounded node query returned an unexpected inventory")
                            exactQueries = minOf(exactQueries + 1, 512)
                            maxExactQueryNodes = maxOf(maxExactQueryNodes, acquired.size)
                            val matches = acquired.filter { it.isVisibleToUser && selected(it) }
                            assertTrue(matches.size <= 1, "An ambiguous visible OS control must not be clicked")
                            maxVisibleMatches = maxOf(maxVisibleMatches, matches.size)
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
            } else {
                windowKinds = windowKinds or 1
            }
            Thread.sleep(40)
        }
        fail("The exact required native OS control was not observed within the bound; " +
            "samplesCapped512=$samples,windowKindsMask=$windowKinds,exactQueriesCapped512=$exactQueries," +
            "maxExactQueryNodes=$maxExactQueryNodes,maxVisibleMatches=$maxVisibleMatches;$requestFacts")
    }
    override fun close() { automation.serviceInfo = automation.serviceInfo.apply { flags = originalFlags } }
}
