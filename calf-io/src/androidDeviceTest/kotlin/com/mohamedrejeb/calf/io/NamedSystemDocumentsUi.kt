// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.io

import android.accessibilityservice.AccessibilityServiceInfo
import android.content.pm.ApplicationInfo
import android.os.SystemClock
import android.view.accessibility.AccessibilityNodeInfo
import androidx.test.platform.app.InstrumentationRegistry

/** Only exact visible controls in the resolved system app; missing/ambiguous controls fail. */
internal class NamedSystemDocumentsUi(private val packageName: String) : AutoCloseable {
    private val instrumentation = InstrumentationRegistry.getInstrumentation()
    private val automation = instrumentation.uiAutomation
    private val originalFlags = automation.serviceInfo.flags
    private var admittedLabelResource: Int? = null

    init {
        check(packageName in AndroidIoSystemTreeGrantActivity.SYSTEM_DOCUMENTS_UI)
        val app = instrumentation.targetContext.packageManager.getApplicationInfo(packageName, 0)
        check(app.flags and (ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0)
        admittedLabelResource = app.labelRes
        automation.serviceInfo = automation.serviceInfo.apply {
            flags = flags or AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS
        }
    }

    fun selectOwnedFolder(folder: String) {
        check(folder.matches(Regex("NativeCmpKitIo55-[a-f0-9]{32}")))
        // Android15 ListDocumentHolder/GridDirectoryHolder bind the row display name to android:id/title.
        // Only the exact owned row inside DirectoryFragment's dir_list is admissible, not arbitrary text.
        click({ root -> textIn(root, resource("dir_list"), folder) }, {
            it.viewIdResourceName == "android:id/title" && it.text?.toString() == folder
        }, enclosingContainer = resource("dir_list"))
        // NavigationViewManager sets the toolbar title for this non-Recents directory.
        // A search bar, breadcrumb, generic root title or unavailable variant is not a substitute.
        observe({ root -> textIn(root, resource("toolbar"), folder) }) {
            it.text?.toString() == folder
        }
        // ACTION_OPEN_TREE installs PickFragment, not the document action-mode select menu.
        // PickFragment binds button1/open_tree_button and disables it while its blocking overlay is visible.
        val pickLabel = stringResource("open_tree_button")
        click({ root -> root.findAccessibilityNodeInfosByViewId("android:id/button1") }, {
            it.text?.toString() == pickLabel && it.isEnabled && it.isClickable
        })
        val context = instrumentation.targetContext
        val callerLabel = context.packageManager.getApplicationLabel(context.applicationInfo).toString()
        check(callerLabel.isNotBlank() && callerLabel.length <= 128)
        // ConfirmFragment uses current directory title and the actual calling application's label.
        val dialogTitle = stringResource("open_tree_dialog_title", callerLabel, folder)
        val dialogMessage = stringResource("open_tree_dialog_message", callerLabel, folder)
        check(dialogTitle.contains(folder) && dialogTitle.contains(callerLabel) &&
            dialogMessage.contains(folder) && dialogMessage.contains(callerLabel))
        val allowLabel = stringResource("allow")
        // Both exact strings must belong to the same refreshed active root as the positive-button query.
        click({ root ->
            if (hasExactText(root, dialogTitle) && hasExactText(root, dialogMessage)) {
                root.findAccessibilityNodeInfosByViewId("android:id/button1")
            } else emptyList()
        }, {
            it.text?.toString() == allowLabel && it.isEnabled && it.isClickable
        })
    }

    private fun resource(id: String): String {
        // The R namespace need not be the package name of a Google-repackaged system application.
        val namespace = "com.android.documentsui"
        val resources = instrumentation.targetContext.packageManager.getResourcesForApplication(packageName)
        val value = resources.getIdentifier(id, "id", namespace)
        check(value != 0 && resources.getResourceName(value) == "$namespace:id/$id") {
            resourceRefusal("The exact stock DocumentsUI control resource is unavailable",
                resources, value, "id/$id")
        }
        return resources.getResourceName(value)
    }

    private fun stringResource(name: String, vararg arguments: Any): String {
        val namespace = "com.android.documentsui"
        val resources = instrumentation.targetContext.packageManager.getResourcesForApplication(packageName)
        val value = resources.getIdentifier(name, "string", namespace)
        check(value != 0 && resources.getResourceName(value) == "$namespace:string/$name") {
            resourceRefusal("The exact stock DocumentsUI string resource is unavailable",
                resources, value, "string/$name")
        }
        return resources.getString(value, *arguments).also { check(it.isNotBlank() && it.length <= 1024) }
    }

    // Failure-only metadata observations never select or authorize a replacement resource.
    private fun resourceRefusal(message: String, resources: android.content.res.Resources,
        value: Int, requested: String): String {
        val application = when (packageName) {
            "com.android.documentsui" -> "AOSP_DOCUMENTS_UI"
            "com.google.android.documentsui" -> "GOOGLE_DOCUMENTS_UI"
            else -> "OTHER_REFUSED"
        }
        val request = when (requested) {
            "id/dir_list" -> "DIR_LIST"
            "id/toolbar" -> "TOOLBAR"
            "string/open_tree_button" -> "OPEN_TREE_BUTTON"
            "string/open_tree_dialog_title" -> "OPEN_TREE_DIALOG_TITLE"
            "string/open_tree_dialog_message" -> "OPEN_TREE_DIALOG_MESSAGE"
            "string/allow" -> "ALLOW"
            else -> "OTHER_REFUSED"
        }
        // Only the original check's lazy false branch calls this function.
        // Nonzero means its exact-name comparison completed false, not a new lookup.
        val nonzero = value != 0
        val nameMatchFromRefusal: Boolean? = if (nonzero) false else null
        val label = admittedLabelResource
        return "$message;documentsUiResourceRefusalSchema=1,request=$request,application=$application," +
            "canonicalIdentifierNonzero=$nonzero,canonicalNameMatchFromRefusal=$nameMatchFromRefusal," +
            "canonicalPostRefusalNamespace=${resourceNamespaceCategory(resources, value)}," +
            "applicationLabelIdentifierNonzero=${label?.let { it != 0 }}," +
            "applicationLabelPostRefusalNamespace=${if (label == null) "UNOBSERVED" else resourceNamespaceCategory(resources, label)}"
    }

    private fun resourceNamespaceCategory(resources: android.content.res.Resources, value: Int): String {
        if (value == 0) return "ZERO_IDENTIFIER"
        // Additional post-refusal readback only. A label resource is not whole-table ownership.
        // Neither a resource name nor a diagnostic exception may escape into the failure report.
        return try {
            val name = resources.getResourceName(value)
            when {
                name.startsWith("com.android.documentsui:") -> "AOSP_DOCUMENTS_UI"
                name.startsWith("com.google.android.documentsui:") -> "GOOGLE_DOCUMENTS_UI"
                name.startsWith("android:") -> "ANDROID_FRAMEWORK"
                ':' in name -> "OTHER_NAMESPACE"
                else -> "UNAVAILABLE"
            }
        } catch (_: Throwable) {
            "UNAVAILABLE" // Preserve the original IllegalStateException and its fixed message prefix.
        }
    }

    private fun textIn(root: AccessibilityNodeInfo, containerId: String, expected: String): List<AccessibilityNodeInfo> {
        val containers = root.findAccessibilityNodeInfosByViewId(containerId)
        try {
            check(containers.size <= 64) { "Exact DocumentsUI container query exceeded its bound" }
            val selectedContainers = containers.filter {
                it.refresh() && it.isVisibleToUser && it.packageName?.toString() == packageName
            }
            check(selectedContainers.size <= 1) { "An ambiguous DocumentsUI container must not be used" }
            return if (selectedContainers.size == 1) {
                selectedContainers.single().findAccessibilityNodeInfosByText(expected)
            } else emptyList()
        } finally { containers.forEach { it.recycle() } }
    }

    private fun hasExactText(root: AccessibilityNodeInfo, expected: String): Boolean {
        val texts = root.findAccessibilityNodeInfosByText(expected)
        try {
            check(texts.size <= 64) { "Exact DocumentsUI confirmation query exceeded its bound" }
            val exactTexts = texts.filter {
                it.refresh() && it.isVisibleToUser && it.packageName?.toString() == packageName &&
                    it.text?.toString() == expected
            }
            check(exactTexts.size <= 1) { "An ambiguous DocumentsUI confirmation must not be used" }
            return exactTexts.size == 1
        } finally { texts.forEach { it.recycle() } }
    }

    private fun observe(nodes: (AccessibilityNodeInfo) -> List<AccessibilityNodeInfo>,
        matches: (AccessibilityNodeInfo) -> Boolean) = find(nodes, matches, click = false)

    private fun click(nodes: (AccessibilityNodeInfo) -> List<AccessibilityNodeInfo>,
        matches: (AccessibilityNodeInfo) -> Boolean, enclosingContainer: String? = null) =
        find(nodes, matches, click = true, enclosingContainer = enclosingContainer)

    private fun find(nodes: (AccessibilityNodeInfo) -> List<AccessibilityNodeInfo>,
        matches: (AccessibilityNodeInfo) -> Boolean, click: Boolean, enclosingContainer: String? = null) {
        val deadline = SystemClock.elapsedRealtime() + 20_000
        var samples = 0
        var maxVisibleMatches = -1 // Unobserved is not an observed empty query.
        while (SystemClock.elapsedRealtime() < deadline) {
            samples = minOf(samples + 1, 512)
            val root = automation.rootInActiveWindow
            if (root != null) try {
                if (root.refresh() && root.isVisibleToUser && root.packageName?.toString() == packageName) {
                    val acquired = nodes(root)
                    try {
                        check(acquired.size <= 64) { "Exact DocumentsUI query exceeded its bound" }
                        val selected = acquired.filter {
                            it.refresh() && it.isVisibleToUser && it.packageName?.toString() == packageName && matches(it)
                        }
                        maxVisibleMatches = maxOf(maxVisibleMatches, selected.size)
                        check(selected.size <= 1) { "An ambiguous system DocumentsUI control must not be used" }
                        if (selected.size == 1) {
                            check(SystemClock.elapsedRealtime() < deadline) { "A late DocumentsUI observation is not acceptance" }
                            if (!click) return
                            var candidate = selected.single()
                            val parents = mutableListOf<AccessibilityNodeInfo>()
                            try {
                                while (!candidate.isClickable && parents.size < 6) {
                                    candidate = checkNotNull(candidate.parent).also { parents += it }
                                    check(candidate.refresh() && candidate.isVisibleToUser && candidate.packageName?.toString() == packageName)
                                    check(enclosingContainer == null || candidate.viewIdResourceName != enclosingContainer) {
                                        "An owned DocumentsUI row ascent must not reach dir_list or higher"
                                    }
                                }
                                check(candidate.refresh() && candidate.isVisibleToUser && candidate.isEnabled && candidate.isClickable)
                                check(enclosingContainer == null || candidate.viewIdResourceName != enclosingContainer) {
                                    "The refreshed DocumentsUI container is not an owned row action"
                                }
                                check(SystemClock.elapsedRealtime() < deadline) { "A late DocumentsUI action is refused" }
                                check(candidate.performAction(AccessibilityNodeInfo.ACTION_CLICK))
                                return
                            } finally { parents.forEach { it.recycle() } }
                        }
                    } finally { acquired.forEach { it.recycle() } }
                }
            } finally { root.recycle() }
            Thread.sleep(40)
        }
        error("Exact owned DocumentsUI control unavailable; samplesCapped512=$samples,maxVisibleMatches=$maxVisibleMatches")
    }

    override fun close() {
        automation.serviceInfo = automation.serviceInfo.apply { flags = originalFlags }
    }
}
