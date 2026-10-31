// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.camerapicker

import android.content.pm.PackageManager
import android.os.Build
import android.os.IBinder
import android.os.IInterface
import android.os.Process
import java.lang.reflect.Modifier

/**
 * Test-only API35 developer-mode lease. Android15 Settings uses the native
 * IActivityManager.setAlwaysFinish(boolean) operation, not a scalar-only write.
 * The running ABI and complete AMS dump are verified; unavailable reflection,
 * ambiguous/native state, foreign changes and uncertain cleanup remain failures.
 * No hidden-API policy/permission bypass or forced Activity destruction is used.
 */
internal class OwnedAlwaysFinish(
    pm: PackageManager,
    expectedOriginalScalar: String,
    private val shell: (String, Int) -> String,
) {
    private data class State(val native: Boolean, val scalar: String)

    private val transaction: Int
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
        transaction = runningTransaction()
        original = readStableState()
        check(original.scalar == expectedOriginalScalar) { "Refuse a changed original developer setting" }
        // Refuse an inconsistent pre-existing scalar/cache pair rather than
        // overwrite or claim ownership of an unknown outside mutation.
        check(original.native == (original.scalar == "1")) { "Refuse an inconsistent original native developer mode" }
    }

    fun arm() {
        check(!closed && !mutationAttempted && !restorationStarted)
        check(readStableState() == original) { "Refuse a foreign developer-mode change before arming" }
        mutationAttempted = true // Retain ownership before an uncertain shell/Binder reply.
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
        setNative(original.native)
        val setterRestored = State(original.native, if (original.native) "1" else "0")
        check(readStableState() == setterRestored) { "Native developer-mode restoration was not verified" }
        if (original.scalar == "null") {
            check(!original.native)
            // The setter creates a 0 row. Delete only that verified owned row to
            // restore original absence, without changing the restored cache.
            check(shell("settings delete global always_finish_activities", CONTROL_BYTES) == "Deleted 1 rows")
        }
        check(readStableState() == original) { "Exact original native/scalar developer mode was not restored" }
        closed = true
    }

    private fun runningTransaction(): Int {
        // Ordinary reflective access may be unavailable on a running API35
        // build. Any refusal occurs before mutation; never change hidden-API
        // policy or substitute a guessed/version-derived transaction number.
        val contract = Class.forName("android.app.IActivityManager")
        check(contract.isInterface && IInterface::class.java.isAssignableFrom(contract))
        val method = contract.getDeclaredMethod("setAlwaysFinish", Boolean::class.javaPrimitiveType)
        check(method.returnType == Void.TYPE && !Modifier.isStatic(method.modifiers))
        val stub = Class.forName("android.app.IActivityManager\$Stub")
        check(contract.isAssignableFrom(stub) && IBinder::class.java.isAssignableFrom(stub))
        val field = stub.getDeclaredField("TRANSACTION_setAlwaysFinish")
        check(field.type == Int::class.javaPrimitiveType && Modifier.isStatic(field.modifiers) && Modifier.isFinal(field.modifiers))
        field.isAccessible = true
        val transaction = field.getInt(null).also { check(it in 1..4096) }
        val name = stub.getDeclaredMethod("getDefaultTransactionName", Int::class.javaPrimitiveType)
        check(name.returnType == String::class.java && Modifier.isStatic(name.modifiers) && Modifier.isPublic(name.modifiers))
        check(name.invoke(null, transaction) == "setAlwaysFinish")

        // service.cpp obtains the live service descriptor and writes that token
        // for `service call`. Verify the complete native list's unique activity
        // identity, not a local class-name assumption or substring match.
        val lines = shell("service list", CONTROL_BYTES).lines()
        val count = checkNotNull(Regex("Found ([0-9]+) services:").matchEntire(lines.firstOrNull().orEmpty()))
            .groupValues[1].toInt().also { check(it in 1..2048) }
        check(lines.size == count + 1)
        val entries = lines.drop(1).mapIndexed { index, line ->
            val entry = checkNotNull(Regex("""([0-9]+)\t([^\s]+): \[([^\[\]\r\n]*)]""").matchEntire(line))
            check(entry.groupValues[1].toInt() == index)
            Triple(index, entry.groupValues[2], entry.groupValues[3])
        }
        check(entries.count { it.second == "activity" } == 1)
        check(entries.single { it.second == "activity" }.third == SERVICE_DESCRIPTOR)
        return transaction
    }

    private fun setNative(enabled: Boolean) {
        val reply = shell("service call activity $transaction i32 ${if (enabled) 1 else 0}", CONTROL_BYTES)
        check(Regex("""Result: Parcel\(\s*00000000\s+'\.\.\.\.'\s*\)""").matches(reply)) {
            "Expected the exact API35 void Binder no-exception reply"
        }
    }

    private fun readScalar(): String {
        val value = shell("settings get global always_finish_activities", CONTROL_BYTES)
        check(value in setOf("null", "0", "1")) { "Unknown native developer setting" }
        return value
    }

    private fun readState(): State {
        val scalar = readScalar()
        val native = readNative()
        check(readScalar() == scalar) { "Developer setting changed during native readback" }
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
        const val SERVICE_DESCRIPTOR = "android.app.IActivityManager"
        const val PROCESS_HEADER = "ACTIVITY MANAGER RUNNING PROCESSES (dumpsys activity processes)"
        const val READINESS_ROW = "  mProcessesReady=true mSystemReady=true mBooted=true mFactoryTest=0"
        const val ALWAYS_FINISH_ROW = "  mAlwaysFinishActivities=true"
        const val CONTROL_BYTES = 65536
        const val DUMP_BYTES = 1_048_576
    }
}
