// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.camerapicker

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotEquals

/** Synthetic source-template records, NOT receipts for an actual Android task. */
class SettingsHomeTaskBaselineTest {
    private fun canonical() = listOf(
        "  * Recent #0: Task{abcdef #17 type=home A=1000:com.android.settings}",
        "    userId=0 effectiveUid=1000 mCallingUid=0 mUserSetupComplete=false mCallingPackage=null mCallingFeatureId=null",
        "    affinity=1000:com.android.settings",
        "    intent={act=android.intent.action.MAIN cat=[android.intent.category.HOME] flg=0x10000100 cmp=com.android.settings/.FallbackHome}",
        "    mActivityComponent=com.android.settings/.FallbackHome",
        "    autoRemoveRecents=false isPersistable=false activityType=2",
        "    rootWasReset=false mNeverRelinquishIdentity=true mReuseTask=false mLockTaskAuth=LOCK_TASK_AUTH_DONT_LOCK",
        "    Activities=[]",
        "    taskId=17 rootTaskId=17",
        "    hasChildPipActivity=false",
        "    mHasBeenVisible=false",
        "    mResizeMode=RESIZE_MODE_UNRESIZEABLE mSupportsPictureInPicture=false isResizeable=false",
        "    lastActiveTime=1 (inactive for 2s)",
    )

    private fun changed(index: Int, action: (String) -> String) = canonical().toMutableList().apply {
        this[index] = action(this[index])
    }

    @Test fun completeBootstrapRecordIsPreservedNotAnOwnedStandardTask() {
        val baseline = SettingsHomeTaskBaselineParser.parse(canonical())
        assertEquals(17, baseline.taskId)
        assertEquals(17, baseline.rootTaskId)
        assertEquals("SettingsHomeTaskBaseline(preserved, not owned)", baseline.toString())
    }

    @Test fun onlyRecentRankAndElapsedInactivityMayChangeWithoutChangingTheBaseline() {
        val later = canonical().toMutableList().apply {
            this[0] = this[0].replace("Recent #0", "Recent #1")
            this[12] = this[12].replace("inactive for 2s", "inactive for 300s")
        }
        assertEquals(SettingsHomeTaskBaselineParser.parse(canonical()), SettingsHomeTaskBaselineParser.parse(later))
    }

    @Test fun changedTaskObjectIdentityPoliciesOrOriginalActiveTimeAreNotTheSameBaseline() {
        val baseline = SettingsHomeTaskBaselineParser.parse(canonical())
        for (candidate in listOf(changed(0) { it.replace("abcdef", "abcde1") },
                changed(6) { it.replace("mReuseTask=false", "mReuseTask=true") },
                changed(8) { it.replace("rootTaskId=17", "rootTaskId=1") },
                changed(10) { it.replace("false", "true") }, changed(12) { it.replace("lastActiveTime=1", "lastActiveTime=2") },
                canonical().map { it.replace("#17", "#18").replace("taskId=17", "taskId=18").replace("rootTaskId=17", "rootTaskId=18") })) {
            assertNotEquals(baseline, SettingsHomeTaskBaselineParser.parse(candidate))
        }
    }

    @Test fun liveForeignStandardAndShellCallerRecordsCannotBecomeAnEmptyHomeBaseline() {
        val variants = listOf(changed(0) { it.replace("type=home", "type=standard") },
            changed(1) { it.replace("userId=0", "userId=10") }, changed(1) { it.replace("effectiveUid=1000", "effectiveUid=10001") },
            changed(1) { it.replace("mCallingUid=0", "mCallingUid=2000") },
            changed(1) { it.replace("mCallingPackage=null", "mCallingPackage=com.android.shell") },
            changed(1) { it.replace("mUserSetupComplete=false", "mUserSetupComplete=true") },
            changed(3) { it.replace("/.FallbackHome", "/.Settings\$DevelopmentSettingsActivity") },
            changed(4) { it.replace("/.FallbackHome", "/.Settings\$DevelopmentSettingsActivity") },
            changed(7) { it.replace("[]", "[ActivityRecord{abcdef u0 com.android.settings/.FallbackHome t17}]") },
            changed(9) { it.replace("false", "true") })
        for (candidate in variants) assertFailsWith<IllegalStateException> { SettingsHomeTaskBaselineParser.parse(candidate) }
    }

    @Test fun everyRoleMustBePresentInOrderOnceWithNoUnknownTrailingRows() {
        for (index in canonical().indices) {
            assertFailsWith<IllegalStateException> { SettingsHomeTaskBaselineParser.parse(canonical().filterIndexed { i, _ -> i != index }) }
            val duplicate = canonical().toMutableList().apply { this[index] = this[(index + 1) % size] }
            assertFailsWith<IllegalStateException> { SettingsHomeTaskBaselineParser.parse(duplicate) }
        }
        assertFailsWith<IllegalStateException> { SettingsHomeTaskBaselineParser.parse(canonical() + "    unknownPolicy=true") }
    }

    @Test fun exactIdentityAndClockBoundsRejectOverflowLeadingZeroAndMismatchedRoots() {
        val variants = listOf(changed(0) { it.replace("#17", "#2147483648") }, changed(0) { it.replace("Recent #0", "Recent #2147483648") },
            changed(8) { it.replace("taskId=17", "taskId=017") }, changed(8) { it.replace("taskId=17", "taskId=18") },
            changed(8) { it.replace("rootTaskId=17", "rootTaskId=2147483648") },
            changed(12) { it.replace("lastActiveTime=1", "lastActiveTime=9223372036854775808") },
            changed(12) { it.replace("inactive for 2s", "inactive for -1s") }, changed(12) { it.replace("inactive for 2s", "inactive for 02s") })
        for (candidate in variants) assertFailsWith<IllegalStateException> { SettingsHomeTaskBaselineParser.parse(candidate) }
    }

    @Test fun malformedWhitespaceUnicodeUnknownPoliciesAndOversizedRowsAreNotNormalized() {
        for (candidate in listOf(changed(1) { "\t" + it }, changed(3) { it + " " }, changed(7) { it + "\r" },
                changed(7) { it + "\u0000" }, changed(7) { it + "\u001b" }, changed(2) { it + "é" },
                changed(6) { it.replace("LOCK_TASK_AUTH_DONT_LOCK", "LOCK_TASK_AUTH_UNKNOWN") },
                changed(6) { it.replace("mNeverRelinquishIdentity=true", "mNeverRelinquishIdentity=false").replace("LOCK_TASK_AUTH_DONT_LOCK", "LOCK_TASK_AUTH_PINNABLE") },
                changed(3) { it.replace("0x10000100", "0x010000100") },
                changed(11) { it.replace("RESIZE_MODE_UNRESIZEABLE", "RESIZE_MODE_UNKNOWN") }, changed(3) { "x".repeat(2049) })) {
            assertFailsWith<IllegalStateException> { SettingsHomeTaskBaselineParser.parse(candidate) }
        }
    }

    @Test fun inputListsAreNotMutatedOrRetainedAsMutableBaselineState() {
        val input = canonical().toMutableList()
        val copy = input.toList()
        val parsed = SettingsHomeTaskBaselineParser.parse(input)
        assertEquals(copy, input)
        input[1] = "foreign mutation"
        assertEquals(SettingsHomeTaskBaselineParser.parse(copy), parsed)
    }
}
