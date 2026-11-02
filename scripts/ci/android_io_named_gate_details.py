"""Exact diagnostic-only derivative; no native selector or source-receipt waiver.

The original Local2 observer and every native action are retained. This second
snapshot reports fixed scalar text/eligibility/location facts after the timeout.
It does not use case conversion to select a control or grant a URI.
"""
from __future__ import annotations

REFUSAL = "Failure-only DocumentsUI gate observation changed"
RETURN_BEFORE = "        return facts.render()\n    }\n"
RETURN_AFTER = "        return facts.render() + gateDetailObservation(target)\n    }\n"
CLOSE_ANCHOR = "    override fun close() {\n"

KOTLIN_DETAIL = '''    // Separate after-timeout snapshot. Never a native selector, result or historical poll.
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

'''


def require(condition: bool) -> None:
    if not condition:
        raise ValueError(REFUSAL)


def detail_images(additions: tuple[str, ...], deltas: tuple[tuple[str, str], ...]):
    """Advance just the owning observer block; all historic/native fragments stay.

    The complete authored derivative is checked by the original forward round
    trip. Partial/hybrid/edited derivatives cannot return a source receipt.
    """
    require(type(additions) is tuple and type(deltas) is tuple)
    require(len(additions) == 6 and len(deltas) == 5)
    require(all(type(value) is str for value in additions))
    require(all(type(value) is tuple and len(value) == 2 and
                all(type(part) is str for part in value) for value in deltas))
    block = additions[-1]
    require(block.count(RETURN_BEFORE) == 1)
    require(deltas[-1] == (CLOSE_ANCHOR, block + CLOSE_ANCHOR))
    current = block.replace(RETURN_BEFORE, RETURN_AFTER, 1) + KOTLIN_DETAIL
    return additions[:-1] + (current,), deltas[:-1] + ((CLOSE_ANCHOR, current + CLOSE_ANCHOR),)


def detail_preimage(current: str) -> str:
    """Read-only exact current-detail inverse, not a native/root admission."""
    require(type(current) is str)
    require(current.count(KOTLIN_DETAIL) == 1 and current.count(RETURN_AFTER) == 1)
    original = current.replace(KOTLIN_DETAIL, "", 1).replace(RETURN_AFTER, RETURN_BEFORE, 1)
    require("gateDetail" not in original and "GateDetail" not in original)
    return original


def detail_fixture_postimage(original: str) -> str:
    """Exact fixture-only overlay, including deliberately malformed old guards.

    Preserve every supplied legacy byte. This never admits source or runs UI;
    the unchanged full source contract must still reject a mutated native guard.
    """
    require(type(original) is str)
    require(original.count(RETURN_BEFORE) == 1 and original.count(CLOSE_ANCHOR) == 1)
    require("gateDetail" not in original and "GateDetail" not in original)
    current = original.replace(RETURN_BEFORE, RETURN_AFTER, 1)
    current = current.replace(CLOSE_ANCHOR, KOTLIN_DETAIL + CLOSE_ANCHOR, 1)
    require(detail_preimage(current) == original)
    return current
