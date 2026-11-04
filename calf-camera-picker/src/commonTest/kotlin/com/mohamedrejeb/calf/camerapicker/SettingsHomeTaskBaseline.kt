// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.camerapicker

/**
 * Test-only preserved baseline, NOT a task owned or removable by the test.
 *
 * Callers must separately verify the fresh guest, installed platform Settings
 * identity, no live Settings Activity, and the unchanged baseline around their
 * nonce-bound standard Settings task. Parsing alone authorizes no UI operation.
 */
internal data class SettingsHomeTaskBaseline(
    val taskId: Int,
    val rootTaskId: Int,
    private val stableRows: List<String>,
) {
    // This owner is test-only, but error/report formatting must not export task bodies.
    override fun toString(): String = "SettingsHomeTaskBaseline(preserved, not owned)"
}

internal object SettingsHomeTaskBaselineParser {
    private const val MAX_ROW_LENGTH = 2048
    private val decimal = "(?:0|[1-9][0-9]{0,18})"
    private val positiveInt = "([1-9][0-9]{0,9})"
    private val header = Regex("""  \* Recent #(0|[1-9][0-9]{0,9}): (Task\{[a-f0-9]{1,8} #$positiveInt type=home A=1000:com\.android\.settings})""")
    private val intent = Regex("""    intent=\{act=android\.intent\.action\.MAIN cat=\[android\.intent\.category\.HOME] flg=0x[1-9a-f][0-9a-f]{0,7} cmp=com\.android\.settings/\.FallbackHome}""")
    private val policy = Regex("    autoRemoveRecents=(true|false) isPersistable=(true|false) activityType=2")
    private val rootPolicy = Regex("    rootWasReset=(true|false) mNeverRelinquishIdentity=(true|false) mReuseTask=(true|false) " +
        "mLockTaskAuth=LOCK_TASK_AUTH_(?:DONT_LOCK|PINNABLE|LAUNCHABLE|ALLOWLISTED|LAUNCHABLE_PRIV)")
    private val ids = Regex("    taskId=$positiveInt rootTaskId=$positiveInt")
    private val resizePolicy = Regex("    mResizeMode=RESIZE_MODE_(?:UNRESIZEABLE|RESIZEABLE|FORCE_RESIZEABLE|" +
        "RESIZEABLE_VIA_SDK_VERSION|FORCE_RESIZABLE_LANDSCAPE_ONLY|FORCE_RESIZABLE_PORTRAIT_ONLY|" +
        "FORCE_RESIZABLE_PRESERVE_ORIENTATION) mSupportsPictureInPicture=(true|false) isResizeable=(true|false)")
    private val lastActive = Regex("    lastActiveTime=($decimal) \\(inactive for ($decimal)s\\)")

    /** Exact complete thirteen-row task body; unknown/missing/duplicate rows fail. */
    fun parse(rows: List<String>): SettingsHomeTaskBaseline {
        check(rows.size == 13 && rows.all { row ->
            row.length in 1..MAX_ROW_LENGTH && row.all { it.code in 32..126 }
        }) { "Complete bounded ASCII fallback HOME task required" }
        val heading = checkNotNull(header.matchEntire(rows[0])) { "Exact fallback HOME header required" }
        check(heading.groupValues[1].toIntOrNull() != null)
        val taskId = checkNotNull(heading.groupValues[3].toIntOrNull()).also { check(it > 0) }
        check(rows[1] == "    userId=0 effectiveUid=1000 mCallingUid=0 mUserSetupComplete=false mCallingPackage=null mCallingFeatureId=null")
        check(rows[2] == "    affinity=1000:com.android.settings")
        check(intent.matches(rows[3]))
        check(rows[4] == "    mActivityComponent=com.android.settings/.FallbackHome")
        check(policy.matches(rows[5]) && rootPolicy.matches(rows[6]))
        check(rows[6] != "    rootWasReset=false mNeverRelinquishIdentity=false mReuseTask=false mLockTaskAuth=LOCK_TASK_AUTH_PINNABLE") {
            "An unprinted source-template default cannot be a complete observed policy row"
        }
        check(rows[7] == "    Activities=[]") { "A live or nested Activity cannot be a preserved empty HOME baseline" }
        val identifiers = checkNotNull(ids.matchEntire(rows[8]))
        check(identifiers.groupValues[1].toIntOrNull() == taskId)
        val rootTaskId = checkNotNull(identifiers.groupValues[2].toIntOrNull()).also { check(it > 0) }
        check(rows[9] == "    hasChildPipActivity=false")
        check(Regex("    mHasBeenVisible=(true|false)").matches(rows[10]))
        check(resizePolicy.matches(rows[11]))
        val clock = checkNotNull(lastActive.matchEntire(rows[12]))
        check(clock.groupValues[1].toLongOrNull() != null && clock.groupValues[2].toLongOrNull() != null)
        // Recent-list rank changes when OUR task is added/removed, and elapsed
        // inactivity is a clock, not task mutation. Preserve every other byte,
        // including object/task identity, original lastActiveTime and policies.
        val stable = listOf(heading.groupValues[2]) + rows.subList(1, 12).toList() +
            listOf("    lastActiveTime=" + clock.groupValues[1])
        return SettingsHomeTaskBaseline(taskId, rootTaskId, stable)
    }
}
