// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.camerapicker

import android.app.UiAutomation
import android.content.pm.PackageManager
import android.os.Build
import android.os.Process

/**
 * Test-only API35 developer-mode lease. Genuine platform Settings UI invokes
 * IActivityManager.setAlwaysFinish(boolean); no inaccessible reflection, guessed
 * Binder transaction, scalar-only toggle or permission/policy bypass is used.
 * Full native/scalar snapshots, the existing Developer Options master and exact
 * owned Settings UI/task cleanup are required. Unknown state remains failed.
 */
internal class OwnedAlwaysFinish(
    pm: PackageManager,
    ui: UiAutomation,
    expectedOriginalScalar: String,
    private val shell: (String, Int) -> String,
) {
    private data class State(val native: Boolean, val scalar: String)

    private val settingsUi = OwnedDeveloperSettingsUi(pm, ui, shell)
    private val original: State
    private var mutationAttempted = false
    private var armCompleted = false
    private var restorationStarted = false
    private var closed = false

    init {
        check(Build.VERSION.SDK_INT == 35 && Build.HARDWARE in setOf("ranchu", "goldfish"))
        check(Process.myUid() / 100_000 == 0)
        check(pm.getApplicationInfo("com.android.shell", 0).uid == 2000)
        check(pm.checkPermission("android.permission.SET_ALWAYS_FINISH", "com.android.shell") == PackageManager.PERMISSION_GRANTED)
        check(expectedOriginalScalar in setOf("null", "0", "1"))
        original = readStableState()
        check(original.scalar == expectedOriginalScalar) { "Refuse a changed original developer setting" }
        // Refuse an inconsistent pre-existing scalar/cache pair rather than
        // overwrite or claim ownership of an unknown outside mutation.
        check(original.native == (original.scalar == "1")) { "Refuse an inconsistent original native developer mode" }
    }

    fun arm() {
        check(!closed && !mutationAttempted && !restorationStarted)
        check(readStableState() == original) { "Refuse a foreign developer-mode change before arming" }
        mutationAttempted = true // Retain ownership before an uncertain public Settings UI action.
        setNative(true)
        check(readStableState() == State(true, "1")) { "Native developer-mode arming was not verified" }
        armCompleted = true
    }

    fun restore() {
        check(!closed && !restorationStarted)
        if (!mutationAttempted) {
            check(readStableState() == original)
            closed = true
            return
        }
        val current = readStableState()
        val target = State(true, "1")
        // AMS writes the scalar before its synchronized cache assignment. Only
        // the exact original, owned target or source-backed partial arm is valid
        // after an unconfirmed attempt; a completed arm requires the target.
        val permitted = if (armCompleted) setOf(target)
            else setOf(original, State(original.native, "1"), target)
        check(current in permitted) { "Refuse a foreign or unverified native developer mode during restoration" }
        restorationStarted = true // Never hide or automatically retry uncertain restoration.
        val clicked = setNative(original.native)
        val setterRestored = State(original.native, if (original.native) "1" else "0")
        if (clicked || original.scalar != "null") {
            check(readStableState() == setterRestored) { "Native developer-mode restoration was not verified" }
        }
        if (original.scalar == "null") {
            if (clicked) {
                check(!original.native)
                // Only a real restoration click creates this verified owned 0.
                // A verified no-op preserves original absence without any delete.
                check(shell("settings delete global always_finish_activities", CONTROL_BYTES) == "Deleted 1 rows")
            }
        }
        check(readStableState() == original) { "Exact original native/scalar developer mode was not restored" }
        closed = true
    }

    private fun setNative(enabled: Boolean): Boolean {
        val before = readStableState()
        return settingsUi.setNative(enabled, before.scalar == "1") { clicked ->
            val expected = if (clicked) State(enabled, if (enabled) "1" else "0") else before
            check(expected.native == enabled) { "Refuse UI-only native mode acceptance" }
            check(readStableState() == expected) { "Native Settings operation was not verified" }
        }
    }

    private fun readScalar(): String {
        val value = shell("settings get global always_finish_activities", CONTROL_BYTES)
        check(value in setOf("null", "0", "1")) { "Unknown native developer setting" }
        return value
    }

    private fun readState(): State {
        settingsUi.requireMaster()
        val scalar = readScalar()
        val native = readNative()
        check(readScalar() == scalar) { "Developer setting changed during native readback" }
        settingsUi.requireMaster()
        return State(native, scalar)
    }

    private fun readStableState(): State {
        val first = readState()
        val second = readState()
        check(first == second) { "Developer mode changed across native snapshots" }
        return second
    }

    private fun readNative(): Boolean {
        // Exact no-package `processes` dispatch sets dumpAll=true. ProcessList
        // prints the header, AMS always prints readiness and the final footer.
        // Only within that complete source-backed branch is a missing true-only
        // mAlwaysFinishActivities row evidence of false; arbitrary omission is not.
        // Inspect in memory only: never log/export unrelated process dump bodies.
        val text = shell("dumpsys activity processes", DUMP_BYTES)
        check(text.none { it == '\r' || it == '\u0000' || it == '\u001b' })
        val lines = text.lines()
        check(lines.firstOrNull() == PROCESS_HEADER && lines.count { it == PROCESS_HEADER } == 1)
        val readiness = lines.withIndex().filter { it.value.contains("mProcessesReady") }
        val footer = lines.withIndex().filter { it.value.contains("mForceBackgroundCheck") }
        check(readiness.size == 1 && readiness.single().value == READINESS_ROW)
        check(footer.size == 1 && footer.single().index == lines.lastIndex)
        check(Regex("  mForceBackgroundCheck=(true|false)").matches(footer.single().value))
        check(readiness.single().index < footer.single().index)
        val fields = lines.withIndex().filter { it.value.contains("mAlwaysFinishActivities") }
        check(fields.size <= 1)
        if (fields.isEmpty()) return false
        check(fields.single().value == ALWAYS_FINISH_ROW)
        check(fields.single().index in 1 until readiness.single().index)
        return true
    }

    private companion object {
        const val PROCESS_HEADER = "ACTIVITY MANAGER RUNNING PROCESSES (dumpsys activity processes)"
        const val READINESS_ROW = "  mProcessesReady=true mSystemReady=true mBooted=true mFactoryTest=0"
        const val ALWAYS_FINISH_ROW = "  mAlwaysFinishActivities=true"
        const val CONTROL_BYTES = 65536
        const val DUMP_BYTES = 1_048_576
    }
}
