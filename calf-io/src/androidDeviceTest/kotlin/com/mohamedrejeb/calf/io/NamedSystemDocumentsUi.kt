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
    private var unavailableGate: GateFailureTarget? = null
    private data class ResourceContract(val resources: android.content.res.Resources, val namespace: String)
    private var admittedResourceContract: ResourceContract? = null

    init {
        check(packageName in AndroidIoSystemTreeGrantActivity.SYSTEM_DOCUMENTS_UI)
        val app = instrumentation.targetContext.packageManager.getApplicationInfo(packageName, 0)
        check(app.flags and (ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0)
        automation.serviceInfo = automation.serviceInfo.apply {
            flags = flags or AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS
        }
    }

    fun selectOwnedFolder(folder: String) {
        check(folder.matches(Regex("NativeCmpKitIo55-[a-f0-9]{32}")))
        // The caller has already assigned this constructed UI to its finally owner.
        // Qualify the complete literal app contract before any accessibility query or click.
        qualifyResourceContract()
        // Android15 ListDocumentHolder/GridDirectoryHolder bind the row display name to android:id/title.
        // Only the exact owned row inside DirectoryFragment's dir_list is admissible, not arbitrary text.
        withGateFailureObservation(GateFailureRole.OWNED_FOLDER_ROW, folder) {
        click({ root -> textIn(root, resource("dir_list"), folder) }, {
            it.viewIdResourceName == "android:id/title" && it.text?.toString() == folder
        }, enclosingContainer = resource("dir_list"))
        } // End OWNED_FOLDER_ROW failure-only scope; original native body is unchanged.
        // NavigationViewManager sets the toolbar title for this non-Recents directory.
        // A search bar, breadcrumb, generic root title or unavailable variant is not a substitute.
        observe({ root -> textIn(root, resource("toolbar"), folder) }) {
            it.text?.toString() == folder
        }
        // ACTION_OPEN_TREE installs PickFragment, not the document action-mode select menu.
        // PickFragment binds button1/open_tree_button and disables it while its blocking overlay is visible.
        val pickLabel = stringResource("open_tree_button")
        // TextView allCaps changes accessibility text, not the installed resource string.
        // This fixture requires English; accept only the exact resource or its exact rendering.
        val renderedPickLabel = pickLabel.uppercase(java.util.Locale.ENGLISH)
        withGateFailureObservation(GateFailureRole.OPEN_TREE_BUTTON, pickLabel) {
        click({ root -> root.findAccessibilityNodeInfosByViewId("android:id/button1") }, {
            (it.text?.toString() == pickLabel || it.text?.toString() == renderedPickLabel) &&
                it.isEnabled && it.isClickable
        })
        } // End OPEN_TREE_BUTTON failure-only scope; original native body is unchanged.
        val context = instrumentation.targetContext
        val callerLabel = context.packageManager.getApplicationLabel(context.applicationInfo).toString()
        check(callerLabel.isNotBlank() && callerLabel.length <= 128)
        // ConfirmFragment uses current directory title and the actual calling application's label.
        val dialogTitle = stringResource("open_tree_dialog_title", callerLabel, folder)
        val dialogMessage = stringResource("open_tree_dialog_message", callerLabel, folder)
        check(dialogTitle.contains(folder) && dialogTitle.contains(callerLabel) &&
            dialogMessage.contains(folder) && dialogMessage.contains(callerLabel))
        val allowLabel = stringResource("allow")
        val renderedAllowLabel = allowLabel.uppercase(java.util.Locale.ENGLISH)
        // Both exact strings must belong to the same refreshed active root as the positive-button query.
        click({ root ->
            if (hasExactText(root, dialogTitle) && hasExactText(root, dialogMessage)) {
                root.findAccessibilityNodeInfosByViewId("android:id/button1")
            } else emptyList()
        }, {
            (it.text?.toString() == allowLabel || it.text?.toString() == renderedAllowLabel) &&
                it.isEnabled && it.isClickable
        })
    }

    private fun qualifyResourceContract() {
        check(admittedResourceContract == null) { "DocumentsUI resource contract was already qualified" }
        // Application identity chooses one complete contract; no label-derived namespace or fallback.
        val namespace = when (packageName) {
            "com.android.documentsui" -> "com.android.documentsui"
            "com.google.android.documentsui" -> "com.google.android.documentsui"
            else -> error("DocumentsUI resource application refused;application=OTHER_REFUSED")
        }
        val resources = try {
            instrumentation.targetContext.packageManager.getResourcesForApplication(packageName)
        } catch (_: Throwable) {
            error(resourceAdmissionRefusal("RESOURCE_TABLE", namespace, null, null))
        }
        // All six original154 candidate roles were nonzero/exact; every execution must requalify.
        val contracts = arrayOf(
            Triple("DIR_LIST", "id", "dir_list"),
            Triple("TOOLBAR", "id", "toolbar"),
            Triple("OPEN_TREE_BUTTON", "string", "open_tree_button"),
            Triple("OPEN_TREE_DIALOG_TITLE", "string", "open_tree_dialog_title"),
            Triple("OPEN_TREE_DIALOG_MESSAGE", "string", "open_tree_dialog_message"),
            Triple("ALLOW", "string", "allow"),
        )
        for ((request, type, entry) in contracts) {
            readQualifiedResource(resources, namespace, request, type, entry)
        }
        // No partial contract, zero/wrong readback or per-role namespace hybrid can be published.
        admittedResourceContract = ResourceContract(resources, namespace)
    }

    private fun resource(id: String): String = qualifiedResource("id", id).second

    private fun stringResource(name: String, vararg arguments: Any): String {
        val (value, _) = qualifiedResource("string", name)
        val resources = checkNotNull(admittedResourceContract).resources
        val text = try {
            resources.getString(value, *arguments)
        } catch (_: Throwable) {
            error("Exact admitted DocumentsUI string unavailable;request=STRING_VALUE")
        }
        return text.also {
            check(it.isNotBlank() && it.length <= 1024) { "Exact admitted DocumentsUI string value refused" }
        }
    }

    private fun qualifiedResource(type: String, entry: String): Pair<Int, String> {
        val contract = checkNotNull(admittedResourceContract) { "DocumentsUI resource contract is unqualified" }
        val request = when ("$type/$entry") {
            "id/dir_list" -> "DIR_LIST"
            "id/toolbar" -> "TOOLBAR"
            "string/open_tree_button" -> "OPEN_TREE_BUTTON"
            "string/open_tree_dialog_title" -> "OPEN_TREE_DIALOG_TITLE"
            "string/open_tree_dialog_message" -> "OPEN_TREE_DIALOG_MESSAGE"
            "string/allow" -> "ALLOW"
            else -> error("DocumentsUI resource role refused;request=OTHER_REFUSED")
        }
        // Recheck consumed IDs/strings against the same fully qualified Resources object.
        return readQualifiedResource(contract.resources, contract.namespace, request, type, entry)
    }

    private fun readQualifiedResource(resources: android.content.res.Resources, namespace: String,
        request: String, type: String, entry: String): Pair<Int, String> {
        val value: Int? = try {
            resources.getIdentifier(entry, type, namespace)
        } catch (_: Throwable) {
            null
        }
        val nonzero: Boolean? = value?.let { it != 0 }
        val fullName: String? = if (nonzero == true) try {
            resources.getResourceName(checkNotNull(value))
        } catch (_: Throwable) {
            null
        } else null
        val exactFullNameMatch: Boolean? = fullName?.let { it == "$namespace:$type/$entry" }
        check(nonzero == true && exactFullNameMatch == true) {
            resourceAdmissionRefusal(request, namespace, nonzero, exactFullNameMatch)
        }
        return checkNotNull(value) to checkNotNull(fullName)
    }

    private fun resourceAdmissionRefusal(request: String, namespace: String,
        nonzero: Boolean?, exactFullNameMatch: Boolean?): String {
        val application = when (packageName) {
            "com.android.documentsui" -> "AOSP_DOCUMENTS_UI"
            "com.google.android.documentsui" -> "GOOGLE_DOCUMENTS_UI"
            else -> "OTHER_REFUSED"
        }
        val declaredNamespace = when (namespace) {
            "com.android.documentsui" -> "AOSP_DOCUMENTS_UI"
            "com.google.android.documentsui" -> "GOOGLE_DOCUMENTS_UI"
            else -> "OTHER_REFUSED"
        }
        // Only fixed categories and nullable booleans leave a refusal, never raw IDs/names/bodies.
        return "The exact application-specific DocumentsUI resource is unavailable;" +
            "documentsUiResourceAdmissionSchema=1,request=$request,application=$application," +
            "declaredNamespace=$declaredNamespace,identifierNonzero=$nonzero," +
            "exactFullNameMatch=$exactFullNameMatch"
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
        error("Exact owned DocumentsUI control unavailable; samplesCapped512=$samples,maxVisibleMatches=$maxVisibleMatches" + unavailableGateObservation())
    }

    private enum class GateFailureRole { OWNED_FOLDER_ROW, OPEN_TREE_BUTTON }
    private data class GateFailureTarget(val role: GateFailureRole, val expectedText: String)
    private class GateProbeStop(val category: String) : RuntimeException()
    private class GateProbeCounts {
        var visited = 0
        var refreshed = 0
        var visible = 0
        var packageExact = 0
        var idExact = 0
        var textExact = 0
        var idAndText = 0
        var textAndEnabled = 0
        var textEnabledClickable = 0
        var originalPredicate = 0
    }
    private class GateProbeFacts(val role: GateFailureRole, val application: String, val namespace: String) {
        var status = "UNAVAILABLE"
        var rootPresent: Boolean? = null
        var rootRefreshed: Boolean? = null
        var rootVisible: Boolean? = null
        var rootPackageExact: Boolean? = null
        var rawContainersCapped65: Int? = null
        var rawNodesCapped65: Int? = null
        var containers: GateProbeCounts? = null
        var nodes: GateProbeCounts? = null
        fun render(): String = "documentsUiGateFailureSchema=1,observation=AFTER_TIMEOUT_ONLY," +
            "role=$role,application=$application,admittedNamespace=$namespace,status=$status," +
            "probeBudgetMillis=1000,rootPresent=$rootPresent,rootRefreshed=$rootRefreshed," +
            "rootVisible=$rootVisible,rootPackageExact=$rootPackageExact," +
            "rawContainersCapped65=$rawContainersCapped65,containerVisited=${containers?.visited}," +
            "containerRefreshed=${containers?.refreshed},containerVisible=${containers?.visible}," +
            "containerPackageExact=${containers?.packageExact},rawNodesCapped65=$rawNodesCapped65," +
            "nodeVisited=${nodes?.visited},nodeRefreshed=${nodes?.refreshed},nodeVisible=${nodes?.visible}," +
            "nodePackageExact=${nodes?.packageExact},nodeIdExact=${nodes?.idExact}," +
            "nodeTextExact=${nodes?.textExact},nodeIdAndText=${nodes?.idAndText}," +
            "nodeTextAndEnabled=${nodes?.textAndEnabled},nodeTextEnabledClickable=${nodes?.textEnabledClickable}," +
            "originalPredicateAtProbe=${nodes?.originalPredicate}"
    }

    private inline fun withGateFailureObservation(role: GateFailureRole, expectedText: String, action: () -> Unit) {
        val previous = unavailableGate
        unavailableGate = GateFailureTarget(role, expectedText)
        try { action() } finally { unavailableGate = previous }
    }

    // Called only while constructing the original timeout error; it can never admit a late candidate.
    private fun unavailableGateObservation(): String {
        val target = unavailableGate ?: return ""
        return try {
            ";" + gateFailureObservation(target)
        } catch (_: Throwable) {
            // No diagnostic exception or raw label/body may replace the original gate failure.
            ";documentsUiGateFailureSchema=1,observation=AFTER_TIMEOUT_ONLY,role=${target.role},status=UNAVAILABLE"
        }
    }

    private fun gateProbeTime(deadline: Long) {
        if (SystemClock.elapsedRealtime() >= deadline) throw GateProbeStop("TIME_BOUND")
    }

    private fun gateFailureObservation(target: GateFailureTarget): String {
        val application = when (packageName) {
            "com.android.documentsui" -> "AOSP_DOCUMENTS_UI"
            "com.google.android.documentsui" -> "GOOGLE_DOCUMENTS_UI"
            else -> "OTHER_REFUSED"
        }
        val namespace = when (admittedResourceContract?.namespace) {
            "com.android.documentsui" -> "AOSP_DOCUMENTS_UI"
            "com.google.android.documentsui" -> "GOOGLE_DOCUMENTS_UI"
            null -> "UNQUALIFIED"
            else -> "OTHER_REFUSED"
        }
        val facts = GateProbeFacts(target.role, application, namespace)
        val deadline = SystemClock.elapsedRealtime() + 1_000
        try {
            gateProbeTime(deadline)
            val probeRoot = automation.rootInActiveWindow
            facts.rootPresent = probeRoot != null
            if (probeRoot == null) {
                gateProbeTime(deadline)
                throw GateProbeStop("ROOT_UNAVAILABLE")
            }
            try {
                gateProbeTime(deadline)
                facts.rootRefreshed = probeRoot.refresh()
                gateProbeTime(deadline)
                if (facts.rootRefreshed != true) throw GateProbeStop("ROOT_REFUSED")
                facts.rootVisible = probeRoot.isVisibleToUser
                gateProbeTime(deadline)
                if (facts.rootVisible != true) throw GateProbeStop("ROOT_REFUSED")
                facts.rootPackageExact = probeRoot.packageName?.toString() == packageName
                gateProbeTime(deadline)
                if (facts.rootPackageExact != true) throw GateProbeStop("ROOT_REFUSED")
                when (target.role) {
                    GateFailureRole.OWNED_FOLDER_ROW -> {
                        // Same mandatory resource recheck, exact dir_list scope and owned-text query.
                        val scopes = probeRoot.findAccessibilityNodeInfosByViewId(resource("dir_list"))
                        try {
                            facts.rawContainersCapped65 = minOf(scopes.size, 65)
                            gateProbeTime(deadline)
                            if (scopes.size > 64) throw GateProbeStop("QUERY_BOUND")
                            val counts = GateProbeCounts().also { facts.containers = it }
                            val eligibleScopes = mutableListOf<AccessibilityNodeInfo>()
                            for (scope in scopes) {
                                gateProbeTime(deadline)
                                val refreshed = scope.refresh()
                                val visible = if (refreshed) scope.isVisibleToUser else null
                                val packageExact = if (visible == true) scope.packageName?.toString() == packageName else null
                                gateProbeTime(deadline)
                                counts.visited += 1
                                if (refreshed) counts.refreshed += 1
                                if (visible == true) counts.visible += 1
                                if (packageExact == true) {
                                    counts.packageExact += 1
                                    eligibleScopes += scope
                                }
                            }
                            if (eligibleScopes.size != 1) throw GateProbeStop(
                                if (eligibleScopes.isEmpty()) "NO_ELIGIBLE_CONTAINER" else "AMBIGUOUS_CONTAINER")
                            gateProbeTime(deadline)
                            val raw = eligibleScopes.single().findAccessibilityNodeInfosByText(target.expectedText)
                            gateFailureNodes(raw, target, facts, deadline)
                        } finally { scopes.forEach { it.recycle() } }
                    }
                    GateFailureRole.OPEN_TREE_BUTTON -> {
                        gateProbeTime(deadline)
                        val raw = probeRoot.findAccessibilityNodeInfosByViewId("android:id/button1")
                        gateFailureNodes(raw, target, facts, deadline)
                    }
                }
                gateProbeTime(deadline)
                facts.status = "COMPLETE"
            } finally { probeRoot.recycle() }
        } catch (stop: GateProbeStop) {
            facts.status = stop.category
        } catch (_: Throwable) {
            facts.status = "UNAVAILABLE"
        }
        return facts.render() + gateDetailObservation(target)
    }

    private fun gateFailureNodes(raw: List<AccessibilityNodeInfo>, target: GateFailureTarget,
        facts: GateProbeFacts, deadline: Long) {
        try {
            facts.rawNodesCapped65 = minOf(raw.size, 65)
            gateProbeTime(deadline)
            if (raw.size > 64) throw GateProbeStop("QUERY_BOUND")
            val counts = GateProbeCounts().also { facts.nodes = it }
            val expectedId = when (target.role) {
                GateFailureRole.OWNED_FOLDER_ROW -> "android:id/title"
                GateFailureRole.OPEN_TREE_BUTTON -> "android:id/button1"
            }
            for (probeNode in raw) {
                gateProbeTime(deadline)
                val refreshed = probeNode.refresh()
                val visible = if (refreshed) probeNode.isVisibleToUser else null
                val packageExact = if (visible == true) probeNode.packageName?.toString() == packageName else null
                val idExact = if (packageExact == true) probeNode.viewIdResourceName == expectedId else null
                val textExact = if (packageExact == true) probeNode.text?.toString() == target.expectedText else null
                val enabled = if (packageExact == true) probeNode.isEnabled else null
                val clickable = if (packageExact == true) probeNode.isClickable else null
                // Commit only fully observed nodes within the separate probe budget; late/partial is not zero.
                gateProbeTime(deadline)
                counts.visited += 1
                if (refreshed) counts.refreshed += 1
                if (visible == true) counts.visible += 1
                if (packageExact == true) counts.packageExact += 1
                if (idExact == true) counts.idExact += 1
                if (textExact == true) counts.textExact += 1
                if (idExact == true && textExact == true) counts.idAndText += 1
                if (textExact == true && enabled == true) counts.textAndEnabled += 1
                if (textExact == true && enabled == true && clickable == true) counts.textEnabledClickable += 1
                val originalPredicate = when (target.role) {
                    GateFailureRole.OWNED_FOLDER_ROW -> idExact == true && textExact == true
                    GateFailureRole.OPEN_TREE_BUTTON -> textExact == true && enabled == true && clickable == true
                }
                if (originalPredicate) counts.originalPredicate += 1
            }
        } finally { raw.forEach { it.recycle() } }
    }

    // Separate after-timeout snapshot. Never a native selector, result or historical poll.
    private class GateDetailFacts(val role: GateFailureRole) {
        var status = "UNAVAILABLE"
        var rootPresent: Boolean? = null
        var rootRefreshed: Boolean? = null
        var rootVisible: Boolean? = null
        var rootPackageExact: Boolean? = null
        var rawButtonNodesCapped65: Int? = null
        var qualifiedButtonIds: Int? = null
        var enabledButtonIds: Int? = null
        var clickableButtonIds: Int? = null
        var buttonTextPresent: Int? = null
        var buttonTextExact: Int? = null
        var buttonTextUppercaseOnly: Int? = null
        var rootOwnedTextQueryCapped65: Int? = null
        var rootOwnedTextExact: Int? = null
        var dirListChildCountCapped65: Int? = null
        var dirListScrollable: Boolean? = null
        var downloadsTitleQualified: Boolean? = null
        var toolbarDownloadsTitleExact: Int? = null
        fun render(): String = ";documentsUiGateDetailSchema=1,detailObservation=AFTER_TIMEOUT_SEPARATE_SNAPSHOT," +
            "detailRole=$role,detailStatus=$status,detailProbeBudgetMillis=1000," +
            "detailRootPresent=$rootPresent,detailRootRefreshed=$rootRefreshed," +
            "detailRootVisible=$rootVisible,detailRootPackageExact=$rootPackageExact," +
            "detailRawButtonNodesCapped65=$rawButtonNodesCapped65,detailQualifiedButtonIds=$qualifiedButtonIds," +
            "detailEnabledButtonIds=$enabledButtonIds,detailClickableButtonIds=$clickableButtonIds," +
            "detailButtonTextPresent=$buttonTextPresent,detailButtonTextExact=$buttonTextExact," +
            "detailButtonTextUppercaseOnly=$buttonTextUppercaseOnly," +
            "detailRootOwnedTextQueryCapped65=$rootOwnedTextQueryCapped65,detailRootOwnedTextExact=$rootOwnedTextExact," +
            "detailDirListChildCountCapped65=$dirListChildCountCapped65,detailDirListScrollable=$dirListScrollable," +
            "detailDownloadsTitleQualified=$downloadsTitleQualified,detailToolbarDownloadsTitleExact=$toolbarDownloadsTitleExact"
    }

    private fun gateDetailObservation(target: GateFailureTarget): String {
        val facts = GateDetailFacts(target.role)
        val deadline = SystemClock.elapsedRealtime() + 1_000
        try {
            gateProbeTime(deadline)
            val root = automation.rootInActiveWindow
            facts.rootPresent = root != null
            if (root == null) throw GateProbeStop("ROOT_UNAVAILABLE")
            try {
                gateProbeTime(deadline)
                facts.rootRefreshed = root.refresh()
                gateProbeTime(deadline)
                if (facts.rootRefreshed != true) throw GateProbeStop("ROOT_REFUSED")
                facts.rootVisible = root.isVisibleToUser
                facts.rootPackageExact = root.packageName?.toString() == packageName
                gateProbeTime(deadline)
                if (facts.rootVisible != true || facts.rootPackageExact != true) throw GateProbeStop("ROOT_REFUSED")
                when (target.role) {
                    GateFailureRole.OPEN_TREE_BUTTON -> {
                        val raw = root.findAccessibilityNodeInfosByViewId("android:id/button1")
                        try {
                            facts.rawButtonNodesCapped65 = minOf(raw.size, 65)
                            gateProbeTime(deadline)
                            if (raw.size > 64) throw GateProbeStop("QUERY_BOUND")
                            facts.qualifiedButtonIds = 0; facts.enabledButtonIds = 0; facts.clickableButtonIds = 0
                            facts.buttonTextPresent = 0; facts.buttonTextExact = 0; facts.buttonTextUppercaseOnly = 0
                            val uppercase = target.expectedText.uppercase(java.util.Locale.ROOT)
                            for (node in raw) {
                                gateProbeTime(deadline)
                                if (!node.refresh() || !node.isVisibleToUser || node.packageName?.toString() != packageName ||
                                    node.viewIdResourceName != "android:id/button1") continue
                                val nativeText = node.text
                                if (nativeText != null && nativeText.length > 1024) throw GateProbeStop("TEXT_BOUND")
                                val text = nativeText?.toString()
                                val enabled = node.isEnabled
                                val clickable = node.isClickable
                                gateProbeTime(deadline)
                                facts.qualifiedButtonIds = facts.qualifiedButtonIds!! + 1
                                if (enabled) facts.enabledButtonIds = facts.enabledButtonIds!! + 1
                                if (clickable) facts.clickableButtonIds = facts.clickableButtonIds!! + 1
                                if (text != null) facts.buttonTextPresent = facts.buttonTextPresent!! + 1
                                if (text == target.expectedText) facts.buttonTextExact = facts.buttonTextExact!! + 1
                                // Evidence of one exact transformation only, NOT input normalization or admission.
                                if (text == uppercase && text != target.expectedText) {
                                    facts.buttonTextUppercaseOnly = facts.buttonTextUppercaseOnly!! + 1
                                }
                            }
                        } finally { raw.forEach { it.recycle() } }
                    }
                    GateFailureRole.OWNED_FOLDER_ROW -> {
                        val global = root.findAccessibilityNodeInfosByText(target.expectedText)
                        try {
                            facts.rootOwnedTextQueryCapped65 = minOf(global.size, 65)
                            facts.rootOwnedTextExact = gateDetailExactTextCount(global, target.expectedText, deadline)
                        } finally { global.forEach { it.recycle() } }
                        val scopes = root.findAccessibilityNodeInfosByViewId(resource("dir_list"))
                        try {
                            gateProbeTime(deadline)
                            if (scopes.size > 64) throw GateProbeStop("QUERY_BOUND")
                            val admitted = scopes.filter { scope ->
                                gateProbeTime(deadline)
                                val eligible = scope.refresh() && scope.isVisibleToUser &&
                                    scope.packageName?.toString() == packageName &&
                                    scope.viewIdResourceName == resource("dir_list")
                                gateProbeTime(deadline)
                                eligible
                            }
                            gateProbeTime(deadline)
                            if (admitted.size != 1) throw GateProbeStop("CONTAINER_REFUSED")
                            val scope = admitted.single()
                            facts.dirListChildCountCapped65 = minOf(scope.childCount, 65)
                            facts.dirListScrollable = scope.isScrollable
                        } finally { scopes.forEach { it.recycle() } }
                        // DownloadStorageProvider.queryRoots binds Root.COLUMN_TITLE to root_downloads.
                        // Read this exact installed resource as data; never query protected provider contents.
                        val providerPackage = "com.android.providers.downloads"
                        val resources = instrumentation.targetContext.packageManager.getResourcesForApplication(providerPackage)
                        gateProbeTime(deadline)
                        val titleId = resources.getIdentifier("root_downloads", "string", providerPackage)
                        if (titleId == 0 || resources.getResourceName(titleId) != "$providerPackage:string/root_downloads") {
                            facts.downloadsTitleQualified = false
                            throw GateProbeStop("RESOURCE_REFUSED")
                        }
                        val title = resources.getString(titleId)
                        if (title.isBlank() || title.length > 1024) throw GateProbeStop("TEXT_BOUND")
                        gateProbeTime(deadline)
                        facts.downloadsTitleQualified = true
                        val toolbars = root.findAccessibilityNodeInfosByViewId(resource("toolbar"))
                        try {
                            gateProbeTime(deadline)
                            if (toolbars.size > 64) throw GateProbeStop("QUERY_BOUND")
                            val admitted = toolbars.filter { toolbar ->
                                gateProbeTime(deadline)
                                val eligible = toolbar.refresh() && toolbar.isVisibleToUser &&
                                    toolbar.packageName?.toString() == packageName &&
                                    toolbar.viewIdResourceName == resource("toolbar")
                                gateProbeTime(deadline)
                                eligible
                            }
                            gateProbeTime(deadline)
                            if (admitted.size != 1) throw GateProbeStop("TOOLBAR_REFUSED")
                            val labels = admitted.single().findAccessibilityNodeInfosByText(title)
                            try { facts.toolbarDownloadsTitleExact = gateDetailExactTextCount(labels, title, deadline) }
                            finally { labels.forEach { it.recycle() } }
                        } finally { toolbars.forEach { it.recycle() } }
                    }
                }
                gateProbeTime(deadline)
                facts.status = "COMPLETE"
            } finally { root.recycle() }
        } catch (stop: GateProbeStop) {
            facts.status = stop.category
        } catch (_: Throwable) {
            facts.status = "UNAVAILABLE"
        }
        return facts.render()
    }

    private fun gateDetailExactTextCount(raw: List<AccessibilityNodeInfo>, expected: String, deadline: Long): Int {
        gateProbeTime(deadline)
        if (raw.size > 64) throw GateProbeStop("QUERY_BOUND")
        var exact = 0
        for (node in raw) {
            gateProbeTime(deadline)
            if (!node.refresh() || !node.isVisibleToUser || node.packageName?.toString() != packageName) continue
            val nativeText = node.text
            if (nativeText != null && nativeText.length > 1024) throw GateProbeStop("TEXT_BOUND")
            val matches = nativeText?.toString() == expected
            gateProbeTime(deadline)
            if (matches) exact++
        }
        return exact
    }

    override fun close() {
        automation.serviceInfo = automation.serviceInfo.apply { flags = originalFlags }
    }
}
