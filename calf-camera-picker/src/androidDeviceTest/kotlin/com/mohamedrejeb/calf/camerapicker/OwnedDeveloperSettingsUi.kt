// SPDX-License-Identifier: Apache-2.0
@file:Suppress("DEPRECATION")
package com.mohamedrejeb.calf.camerapicker

import android.accessibilityservice.AccessibilityServiceInfo
import android.app.UiAutomation
import android.content.ComponentName
import android.content.Intent
import android.content.pm.ActivityInfo
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.graphics.Rect
import android.view.accessibility.AccessibilityNodeInfo
import android.view.accessibility.AccessibilityWindowInfo
import java.util.UUID

/**
 * Test-only public Settings UI lease, not reflection/Binder-policy bypass. The
 * installed platform Settings identity, native nonce-bound task/top Activity,
 * exact installed preference resources and actual AMS/scalar readback are all
 * required. Developer Options must already be enabled and is never toggled.
 * Every partial launch/action is owned before IPC; unknown cleanup stays failed.
 * Trees/task bodies remain in memory: no screenshots, dumps or UI text exports.
 */
internal class OwnedDeveloperSettingsUi(
    private val pm: PackageManager,
    private val ui: UiAutomation,
    private val shell: (String, Int) -> String,
) {
    private val component = ComponentName(SETTINGS_PACKAGE, "com.android.settings.Settings\$DevelopmentSettingsActivity")
    private val resources = pm.getResourcesForApplication(SETTINGS_PACKAGE)
    private val title = resources.getString(resource("immediately_destroy_activities", "string"))
    private val summary = resources.getString(resource("immediately_destroy_activities_summary", "string"))
    private val switchId = resources.getResourceName(resource("switchWidget", "id"))
    private val recyclerId = resources.getResourceName(resource("recycler_view", "id"))
    private val originalFlags = checkNotNull(ui.serviceInfo).flags
    private val expectedFlags = originalFlags or AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
        AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS or AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS
    private var flagsAttempted = false
    private var flagsConfigured = false
    private var flagsRestorationAttempted = false
    private var flagsRestored = true
    private var activeLease: Lease? = null
    private var mutationAttempted = false

    private class Lease(val nonce: String, val intent: Intent) {
        var taskId: Int? = null
        var removalAttempted = false
    }
    private data class RecentTask(val id: Int, val user: String, val uid: String, val callerUid: String,
        val setup: String, val callerPackage: String, val callerFeature: String, val intentRow: String, val componentRow: String)
    private data class LiveTasks(val ids: Set<Int>, val settings: Set<Int>)
    private data class Tree(val nodes: List<AccessibilityNodeInfo>, val parents: List<Int>)
    private data class Selection(val row: AccessibilityNodeInfo, val widget: AccessibilityNodeInfo)

    init {
        val info = pm.getActivityInfo(component, PackageManager.GET_META_DATA)
        check(info.packageName == SETTINGS_PACKAGE && info.name == component.className)
        check(info.enabled && info.exported && info.permission == null && info.launchMode == ActivityInfo.LAUNCH_MULTIPLE)
        val applicationInfo = checkNotNull(info.applicationInfo)
        check(applicationInfo.uid == 1000 && applicationInfo.enabled)
        check(applicationInfo.flags and ApplicationInfo.FLAG_SYSTEM != 0)
        check(info.processName == SETTINGS_PACKAGE)
        check(pm.checkSignatures("android", SETTINGS_PACKAGE) == PackageManager.SIGNATURE_MATCH)
        check(pm.getComponentEnabledSetting(component) == PackageManager.COMPONENT_ENABLED_STATE_DEFAULT)
        check(pm.getApplicationEnabledSetting(SETTINGS_PACKAGE) == PackageManager.COMPONENT_ENABLED_STATE_DEFAULT)
        check(checkNotNull(info.metaData).getString("com.android.settings.FRAGMENT_CLASS") ==
            "com.android.settings.development.DevelopmentSettingsDashboardFragment")
        check(pm.checkPermission("android.permission.DUMP", "com.android.shell") == PackageManager.PERMISSION_GRANTED)
        check(pm.checkPermission("android.permission.MANAGE_ACTIVITY_TASKS", "com.android.shell") == PackageManager.PERMISSION_GRANTED)
        check(pm.checkPermission("android.permission.REMOVE_TASKS", "com.android.shell") == PackageManager.PERMISSION_GRANTED)
        check(title.isNotBlank() && summary.isNotBlank() && title != summary)
        requireMaster()
    }

    fun requireMaster() {
        check(shell("settings get global development_settings_enabled", CONTROL_BYTES) == "1") {
            "Developer Options master must already be enabled and remain unchanged"
        }
    }

    /** One needed genuine preference click, or a verified no-op; never double-toggle. */
    fun setNative(enabled: Boolean, expectedChecked: Boolean, verifyNative: (Boolean) -> Unit): Boolean {
        check(activeLease == null && flagsRestored)
        var primary: Throwable? = null
        var clicked = false
        try {
            val lease = openSettings()
            withPreference(lease, navigate = true) { selected ->
                val switchChecked = selected.widget.isChecked
                check(switchChecked == expectedChecked) { "Refuse a changed Settings preference before mutation" }
                requireMaster()
                if (switchChecked != enabled) {
                    mutationAttempted = true // Retain the exact owned UI action before uncertain acceptance.
                    check(selected.row.performAction(AccessibilityNodeInfo.ACTION_CLICK)) { "Owned Settings preference click was not accepted" }
                    clicked = true
                }
            }
            waitUntil {
                var ready = false
                withPreference(lease, navigate = false) { selected -> ready = selected.widget.isChecked == enabled }
                ready
            }
            withPreference(lease, navigate = false) { selected ->
                check(selected.widget.isChecked == enabled)
                verifyNative(clicked) // Settings catches RemoteException: UI checked alone is not AMS acceptance.
                requireMaster()
            }
        } catch (failure: Throwable) {
            primary = failure
            throw failure
        } finally {
            var cleanupFailure: Throwable? = null
            fun cleanup(action: () -> Unit) {
                try { action() } catch (failure: Throwable) {
                    val initial = primary
                    if (initial != null) { if (failure !== initial) initial.addSuppressed(failure) }
                    else { val prior = cleanupFailure; if (prior == null) cleanupFailure = failure else prior.addSuppressed(failure) }
                }
            }
            cleanup { closeSettings() }
            cleanup { restoreFlags() }
            cleanupFailure?.let { throw it }
        }
        return clicked
    }

    private fun openSettings(): Lease {
        requireMaster()
        check(readRecentTasks().isEmpty()) { "Refuse pre-existing or competing Settings tasks" }
        check(readLiveTasks().settings.isEmpty())
        check(serviceFlags() == originalFlags && flagsRestored)
        flagsAttempted = false; flagsConfigured = false; flagsRestorationAttempted = false
        val requested = checkNotNull(ui.serviceInfo).apply { flags = expectedFlags }
        flagsAttempted = true; flagsRestored = false // Own before uncertain accessibility configuration.
        ui.serviceInfo = requested
        check(serviceFlags() == expectedFlags)
        flagsConfigured = true
        val nonce = UUID.randomUUID().toString().replace("-", "")
        val intent = Intent(SETTINGS_ACTION).setComponent(component).setIdentifier(nonce)
            .setFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_MULTIPLE_TASK)
        val uri = intent.toUri(Intent.URI_INTENT_SCHEME)
        check(Regex("[A-Za-z0-9._:/#%;=+\\-]+").matches(uri)) // Safe URI grammar: no embedded whitespace or quote.
        val lease = Lease(nonce, intent)
        activeLease = lease // Own before launch can succeed with an uncertain reply.
        val reply = runComplete("am start -W --user 0 '$uri'")
        check(reply.firstOrNull() == "Starting: $intent")
        check(reply.filter { it.startsWith("Status:") } == listOf("Status: ok"))
        check(reply.filter { it.startsWith("Activity:") } == listOf("Activity: ${component.flattenToShortString()}"))
        check(reply.lastOrNull() == "Complete" && reply.none { it.startsWith("Warning:") || it.startsWith("Error:") })
        val rows = readRecentTasks()
        check(rows.size == 1)
        assertOwned(rows.single(), lease)
        lease.taskId = rows.single().id
        assertTop(lease)
        requireMaster()
        return lease
    }

    private fun restoreFlags() {
        if (!flagsAttempted) { check(serviceFlags() == originalFlags); return }
        check(!flagsRestorationAttempted)
        val flags = serviceFlags()
        if (flagsConfigured) check(flags == expectedFlags)
        else check(flags in setOf(originalFlags, expectedFlags))
        val restored = checkNotNull(ui.serviceInfo).apply { this.flags = originalFlags }
        flagsRestorationAttempted = true // Do not automatically retry an uncertain restoration.
        ui.serviceInfo = restored
        check(serviceFlags() == originalFlags)
        flagsRestored = true
    }

    private fun closeSettings() {
        val lease = activeLease ?: return
        val rows = readRecentTasks()
        if (rows.isEmpty()) {
            val live = readLiveTasks()
            check(live.settings.isEmpty() && (lease.taskId == null || lease.taskId !in live.ids))
            activeLease = null; return
        } // Exact completed recent AND live native queries, not missing output.
        check(rows.size == 1)
        assertOwned(rows.single(), lease)
        val taskId = rows.single().id
        check(lease.taskId == null || lease.taskId == taskId)
        check(!lease.removalAttempted)
        lease.removalAttempted = true
        check(runComplete("am stack remove $taskId").isEmpty())
        waitUntil {
            val remaining = readRecentTasks()
            val live = readLiveTasks()
            if (remaining.isEmpty()) live.settings.isEmpty() && taskId !in live.ids else {
                check(remaining.size == 1); assertOwned(remaining.single(), lease)
                check(remaining.single().id == taskId); false
            }
        }
        activeLease = null
    }

    private fun assertOwned(task: RecentTask, lease: Lease) {
        check(task.user == "0" && task.uid == "1000" && task.callerUid == "2000" && task.setup == "true")
        check(task.callerPackage == "com.android.shell" && task.callerFeature == "null")
        check(task.intentRow == "    intent={act=$SETTINGS_ACTION id=${lease.nonce} flg=0x18000000 cmp=${component.flattenToShortString()}}")
        check(task.componentRow == "    mActivityComponent=${component.flattenToShortString()}")
    }

    private fun readRecentTasks(): List<RecentTask> {
        // -p is parsed BEFORE recents. A trailing package argument would not filter this dispatch.
        val lines = runComplete("dumpsys activity -p com.android.settings recents")
        check(lines.size >= 5 && lines.first() == RECENTS_HEADER && lines.count { it == RECENTS_HEADER } == 1)
        check(Regex("mRecentsUid=[0-9]+").matches(lines[1]))
        check(Regex("mRecentsComponent=ComponentInfo\\{[^{}]+}").matches(lines[2]))
        check(Regex("mFreezeTaskListReordering=(true|false)").matches(lines[3]))
        check(Regex("mFreezeTaskListReorderingPendingTimeout=(true|false)").matches(lines[4]))
        val remainder = lines.drop(5)
        if (remainder.isEmpty() || remainder == listOf("  (nothing)")) return emptyList()
        check(remainder.first() == "  Recent tasks:" && remainder.count { it == "  Recent tasks:" } == 1)
        check(remainder.count { it == RECENTS_VISIBLE } <= 1)
        val visible = remainder.indexOf(RECENTS_VISIBLE).let { if (it < 0) remainder.size else it }
        val raw = remainder.subList(1, visible).dropLastWhile { it.isEmpty() }
        val starts = raw.indices.filter { raw[it].startsWith("  * Recent #") }
        check(starts.isNotEmpty() && starts.first() == 0)
        val tasks = starts.mapIndexed { index, start ->
            val end = starts.getOrElse(index + 1) { raw.size }
            val block = raw.subList(start, end)
            val header = checkNotNull(Regex("""  \* Recent #[0-9]+: Task\{[a-f0-9]+ #([1-9][0-9]*) type=standard[^{}]*}""").matchEntire(block.first()))
            check(Regex("""    lastActiveTime=[0-9]+ \(inactive for [0-9]+s\)""").matches(block.last()))
            check(block.drop(1).all { it.startsWith("    ") })
            val identity = checkNotNull(Regex("""    userId=([0-9]+) effectiveUid=(\S+) mCallingUid=(\S+) mUserSetupComplete=(true|false) mCallingPackage=(\S+) mCallingFeatureId=(\S+)""")
                .matchEntire(oneRow(block, "    userId="))).groupValues
            val ids = checkNotNull(Regex("    taskId=([1-9][0-9]*) rootTaskId=([1-9][0-9]*)").matchEntire(oneRow(block, "    taskId="))).groupValues
            check(ids[1] == header.groupValues[1])
            RecentTask(ids[1].toInt(), identity[1], identity[2], identity[3], identity[4], identity[5], identity[6],
                oneRow(block, "    intent="), oneRow(block, "    mActivityComponent="))
        }
        check(tasks.map { it.id }.distinct().size == tasks.size)
        return tasks
    }

    private fun assertTop(lease: Lease) {
        val taskId = checkNotNull(lease.taskId)
        val lines = runComplete("dumpsys activity top-resumed")
        check(lines.firstOrNull() == TOP_HEADER && lines.count { it == TOP_HEADER } == 1)
        check(oneRow(lines, "packageName=") == "packageName=com.android.settings processName=com.android.settings")
        check(oneRow(lines, "launchedFromUid=") == "launchedFromUid=2000 launchedFromPackage=com.android.shell launchedFromFeature=null userId=0")
        check(lines.count { it == lease.intent.toString() } == 1)
        check(oneRow(lines, "mActivityComponent=") == "mActivityComponent=${component.flattenToShortString()}")
        check(Regex("""rootOfTask=true task=Task\{[a-f0-9]+ #$taskId type=standard[^{}]*}""").matches(oneRow(lines, "rootOfTask=")))
        check(oneRow(lines, "state=") == "state=RESUMED delayedResume=false finishing=false")
    }

    private fun readLiveTasks(): LiveTasks {
        // Native getAllRootTaskInfos includes all leaf task IDs/names, even a
        // background task. Require complete successful shell output and every
        // source-backed root/configuration/child row; never infer an unknown
        // name, silent error or absent recents entry is a removed live task.
        val lines = runComplete("am stack list").filter { it.isNotEmpty() }
        check(lines.isNotEmpty())
        val roots = lines.indices.filter { lines[it].startsWith("RootTask id=") }
        check(roots.isNotEmpty() && roots.first() == 0)
        val ids = mutableSetOf<Int>()
        val settings = mutableSetOf<Int>()
        val children = mutableSetOf<Int>()
        val bounds = "\\[-?[0-9]+,-?[0-9]+]\\[-?[0-9]+,-?[0-9]+]"
        roots.forEachIndexed { index, start ->
            val end = roots.getOrElse(index + 1) { lines.size }
            val block = lines.subList(start, end)
            check(block.size >= 2)
            val root = checkNotNull(Regex("RootTask id=([0-9]+) bounds=$bounds displayId=[0-9]+ userId=[0-9]+").matchEntire(block[0]))
            check(block[1].startsWith(" configuration={") && block[1].endsWith("}"))
            ids += root.groupValues[1].toInt()
            for (line in block.drop(2)) {
                val child = checkNotNull(Regex("  taskId=([0-9]+): ([^\\s]+)(?: bounds=$bounds)? userId=[0-9]+ visible=(true|false)(?: topActivity=ComponentInfo\\{([^{}]+)})?").matchEntire(line))
                val id = child.groupValues[1].toInt()
                check(children.add(id))
                ids += id
                val name = child.groupValues[2]
                check(name != "unknown")
                val top = child.groupValues[4]
                if (name == SETTINGS_PACKAGE || name.startsWith("$SETTINGS_PACKAGE/") || top.startsWith("$SETTINGS_PACKAGE/")) settings += id
            }
        }
        return LiveTasks(ids, settings)
    }

    private fun oneRow(lines: List<String>, prefix: String): String {
        val rows = lines.filter { it.startsWith(prefix) }
        check(rows.size == 1)
        return rows.single()
    }

    private fun runComplete(command: String): List<String> {
        check(command in setOf("dumpsys activity -p com.android.settings recents", "dumpsys activity top-resumed", "am stack list") ||
            Regex("am stack remove [1-9][0-9]*").matches(command) ||
            Regex("am start -W --user 0 '[A-Za-z0-9._:/#%;=+\\-]+'").matches(command))
        val marker = "nativecmpkit-settings-" + UUID.randomUUID().toString().replace("-", "")
        // UiAutomationConnection uses Runtime.exec(String), NOT a shell tokenizer.
        // Pass one whitespace-free -c argument to the explicit shell. Only the
        // validated URI is quoted INSIDE that argument; ${IFS} supplies argv
        // separators there. The final marker includes the actual command status.
        val encoded = command.replace(" ", "\${IFS}")
        val text = shell("sh -c $encoded;echo\${IFS}$marker-\$?", CONTROL_BYTES)
        check(text.none { it == '\r' || it == '\u0000' || it == '\u001b' })
        val lines = text.lines()
        check(lines.lastOrNull() == "$marker-0" && lines.count { it.contains(marker) } == 1)
        return lines.dropLast(1)
    }

    private fun withPreference(lease: Lease, navigate: Boolean, action: (Selection) -> Unit) {
        var scrolls = 0
        while (true) {
            requireMaster(); assertTop(lease)
            val tree = readTree()
            val nodes = tree.nodes
            try {
                val selected = selection(tree)
                if (selected != null) { action(selected); return }
                check(navigate && scrolls++ < MAX_SCROLLS) { "Exact installed Settings preference unavailable" }
                val recyclers = nodes.filter { it.viewIdResourceName == recyclerId && it.className?.toString() == "androidx.recyclerview.widget.RecyclerView" }
                check(recyclers.size == 1)
                val recycler = recyclers.single()
                check(recycler.isVisibleToUser && recycler.isEnabled && recycler.isScrollable)
                check(recycler.performAction(AccessibilityNodeInfo.ACTION_SCROLL_FORWARD)) { "Owned preference scrolling refused" }
            } finally {
                nodes.forEach { it.recycle() }
            }
            Thread.sleep(100)
        }
    }

    private fun readTree(): Tree {
        val windows = checkNotNull(ui.windows)
        try {
            val active = windows.filter { it.type == AccessibilityWindowInfo.TYPE_APPLICATION && it.isActive && it.isFocused }
            check(active.size == 1)
            val root = checkNotNull(ui.rootInActiveWindow)
            val nodes = mutableListOf(root)
            val parents = mutableListOf(-1)
            val depths = mutableListOf(0)
            var index = 0
            try {
                check(root.windowId == active.single().id && root.packageName?.toString() == SETTINGS_PACKAGE)
                while (index < nodes.size) {
                    val node = nodes[index]
                    check(depths[index] <= MAX_DEPTH && node.childCount <= 128)
                    for (child in 0 until node.childCount) {
                        check(nodes.size < MAX_NODES)
                        nodes += checkNotNull(node.getChild(child)); parents += index; depths += depths[index] + 1
                    }
                    index++
                }
                return Tree(nodes, parents)
            } catch (failure: Throwable) {
                nodes.forEach { it.recycle() }
                throw failure
            }
        } finally { windows.forEach { it.recycle() } }
    }

    private fun selection(tree: Tree): Selection? {
        val nodes = tree.nodes
        val titles = nodes.indices.filter { nodes[it].text?.toString() == title }
        if (titles.isEmpty()) return null
        check(titles.size == 1 && nodes[titles.single()].viewIdResourceName == "android:id/title")
        val summaries = nodes.indices.filter { nodes[it].text?.toString() == summary }
        if (summaries.isEmpty()) return null
        check(summaries.size == 1 && nodes[summaries.single()].viewIdResourceName == "android:id/summary")
        fun below(child: Int, parent: Int): Boolean {
            var at = child
            while (at >= 0) { if (at == parent) return true; at = tree.parents[at] }
            return false
        }
        var parent = tree.parents[titles.single()]
        while (parent >= 0) {
            val row = nodes[parent]
            if (row.isClickable && below(summaries.single(), parent)) {
                val children = nodes.indices.filter { below(it, parent) }
                check(children.count { nodes[it].viewIdResourceName == "android:id/title" } == 1)
                val switches = children.map { nodes[it] }.filter { it.viewIdResourceName == switchId }
                check(switches.size == 1)
                val widget = switches.single()
                check(widget.className?.toString() in setOf("android.widget.Switch", "androidx.appcompat.widget.SwitchCompat"))
                check(widget.isCheckable && widget.isEnabled && widget.isVisibleToUser)
                check(row.isEnabled && row.isVisibleToUser && row.packageName?.toString() == SETTINGS_PACKAGE)
                check(widget.packageName?.toString() == SETTINGS_PACKAGE)
                check(row.actionList.any { it.id == AccessibilityNodeInfo.ACTION_CLICK })
                val bounds = Rect(); row.getBoundsInScreen(bounds); check(!bounds.isEmpty)
                return Selection(row, widget)
            }
            parent = tree.parents[parent]
        }
        error("Exact installed Settings preference row was not uniquely actionable")
    }

    private fun serviceFlags() = checkNotNull(ui.serviceInfo).flags
    private fun resource(name: String, type: String) = resources.getIdentifier(name, type, SETTINGS_PACKAGE).also { check(it != 0) }
    private fun waitUntil(condition: () -> Boolean) {
        val deadline = System.nanoTime() + 10_000_000_000L
        while (!condition()) { check(System.nanoTime() < deadline) { "Owned Settings readback timed out" }; Thread.sleep(30) }
    }

    private companion object {
        const val SETTINGS_PACKAGE = "com.android.settings"
        const val SETTINGS_ACTION = "android.settings.APPLICATION_DEVELOPMENT_SETTINGS"
        const val RECENTS_HEADER = "ACTIVITY MANAGER RECENT TASKS (dumpsys activity recents)"
        const val RECENTS_VISIBLE = "  Visible recent tasks (most recent first):"
        const val TOP_HEADER = "ACTIVITY MANAGER TOP-RESUMED (dumpsys activity top-resumed)"
        const val CONTROL_BYTES = 65536
        const val MAX_SCROLLS = 40
        const val MAX_NODES = 2048
        const val MAX_DEPTH = 32
    }
}
