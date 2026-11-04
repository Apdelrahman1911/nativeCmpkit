# SPDX-License-Identifier: Apache-2.0
"""Important real-parser and controller models; zero Android/Settings/camera IO."""
from __future__ import annotations

from pathlib import Path
import unittest

import android_camera_home_baseline as home
import test_android_camera_developer_prerequisite as fixtures

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedDeveloperSettingsUi.kt"


def canonical() -> list[str]:
    # Synthetic source-template rows, NOT a reconstruction of an actual task.
    return [
        "  * Recent #0: Task{abcdef #17 type=home A=1000:com.android.settings}",
        "    userId=0 effectiveUid=1000 mCallingUid=0 mUserSetupComplete=false mCallingPackage=null mCallingFeatureId=null",
        "    affinity=1000:com.android.settings",
        "    intent={act=android.intent.action.MAIN cat=[android.intent.category.HOME] flg=0x10000100 cmp=com.android.settings/.FallbackHome}",
        "    mActivityComponent=com.android.settings/.FallbackHome",
        "    autoRemoveRecents=false isPersistable=false activityType=2",
        "    rootWasReset=false mNeverRelinquishIdentity=true mReuseTask=false mLockTaskAuth=LOCK_TASK_AUTH_DONT_LOCK",
        "    Activities=[]", "    taskId=17 rootTaskId=17", "    hasChildPipActivity=false",
        "    mHasBeenVisible=false",
        "    mResizeMode=RESIZE_MODE_UNRESIZEABLE mSupportsPictureInPicture=false isResizeable=false",
        "    lastActiveTime=1 (inactive for 2s)",
    ]


def changed(index, old, new):
    rows = canonical()
    assert old in rows[index]
    rows[index] = rows[index].replace(old, new)
    return rows


def envelope(rows=None):
    frame = fixtures.RECENTS.decode().removesuffix("\n").split("\n")
    assert frame[-1] == "  (nothing)"
    frame = frame[:-1]
    return ("\n".join(frame + (["  Recent tasks:"] + (canonical() if rows is None else rows))) + "\n").encode()


class CompleteHomeParserTests(unittest.TestCase):
    def test_complete_record_is_preserved_never_claimed_owned_or_exported(self):
        original = canonical()
        baseline = home.parse_home_task(original)
        self.assertEqual(17, baseline.task_id)
        self.assertEqual(17, baseline.root_task_id)
        self.assertEqual("SettingsHomeTaskBaseline(preserved, not owned)", repr(baseline))
        self.assertEqual({"preserved_home_task_count", "stable_record_sha256", "owned_or_removable"}, set(baseline.safe()))
        self.assertIs(baseline.safe()["owned_or_removable"], False)
        self.assertNotIn("abcdef", repr(baseline.safe()))
        original[1] = "foreign mutation"
        self.assertEqual(home.parse_home_task(canonical()), baseline)

    def test_only_rank_and_elapsed_clock_can_change_in_an_unchanged_baseline(self):
        later = canonical()
        later[0] = later[0].replace("Recent #0", "Recent #2")
        later[12] = later[12].replace("inactive for 2s", "inactive for 300s")
        first, second = home.parse_home_task(canonical()), home.parse_home_task(later)
        self.assertEqual(first, second)
        self.assertEqual(first.safe(), second.safe())

    def test_every_immutable_identity_policy_root_and_original_clock_change_is_detected(self):
        before = home.parse_home_task(canonical())
        variants = [changed(0, "abcdef", "abcde1"), changed(6, "mReuseTask=false", "mReuseTask=true"),
                    changed(8, "rootTaskId=17", "rootTaskId=1"), changed(10, "false", "true"),
                    changed(12, "lastActiveTime=1", "lastActiveTime=2"), changed(3, "0x10000100", "0x10000000")]
        for rows in variants:
            with self.subTest(row=variants.index(rows)):
                self.assertNotEqual(before, home.parse_home_task(rows))

    def test_live_foreign_standard_and_shell_caller_records_cannot_be_preserved(self):
        variants = [changed(0, "type=home", "type=standard"), changed(1, "userId=0", "userId=10"),
                    changed(1, "effectiveUid=1000", "effectiveUid=10001"), changed(1, "mCallingUid=0", "mCallingUid=2000"),
                    changed(1, "mUserSetupComplete=false", "mUserSetupComplete=true"),
                    changed(1, "mCallingPackage=null", "mCallingPackage=com.android.shell"),
                    changed(4, ".FallbackHome", ".Settings$DevelopmentSettingsActivity"),
                    changed(7, "[]", "[ActivityRecord{abcdef u0 com.android.settings/.FallbackHome t17}]"),
                    changed(9, "false", "true")]
        for rows in variants:
            with self.subTest(row=variants.index(rows)), self.assertRaises(ValueError):
                home.parse_home_task(rows)

    def test_missing_duplicate_out_of_order_and_unknown_rows_are_not_ignored(self):
        for i in range(13):
            for rows in (canonical()[:i] + canonical()[i + 1:],
                         canonical()[:i] + [canonical()[(i + 1) % 13]] + canonical()[i + 1:]):
                with self.subTest(index=i), self.assertRaises(ValueError):
                    home.parse_home_task(rows)
        with self.assertRaises(ValueError):
            home.parse_home_task(canonical() + ["    unknownPolicy=true"])

    def test_identity_clock_enum_and_source_print_condition_bounds_remain_strict(self):
        variants = [changed(0, "#17", "#2147483648"), changed(0, "Recent #0", "Recent #2147483648"),
                    changed(8, "taskId=17", "taskId=18"), changed(8, "rootTaskId=17", "rootTaskId=2147483648"),
                    changed(12, "lastActiveTime=1", "lastActiveTime=9223372036854775808"),
                    changed(12, "inactive for 2s", "inactive for 02s"), changed(3, "0x10000100", "0x010000100"),
                    changed(6, "LOCK_TASK_AUTH_DONT_LOCK", "LOCK_TASK_AUTH_UNKNOWN"),
                    changed(11, "RESIZE_MODE_UNRESIZEABLE", "RESIZE_MODE_UNKNOWN"),
                    changed(6, "mNeverRelinquishIdentity=true", "mNeverRelinquishIdentity=false")]
        variants[-1][6] = variants[-1][6].replace("LOCK_TASK_AUTH_DONT_LOCK", "LOCK_TASK_AUTH_PINNABLE")
        for rows in variants:
            with self.subTest(row=variants.index(rows)), self.assertRaises(ValueError):
                home.parse_home_task(rows)

    def test_unsafe_oversized_or_nonordinary_values_are_not_normalized(self):
        for value in (None, {}, "not rows", canonical() + [" "], ["x" * 2049] + canonical()[1:]):
            with self.subTest(kind=type(value).__name__), self.assertRaises(ValueError):
                home.parse_home_task(value)
        for suffix in ("\r", "\0", "\x1b", "é", "\t"):
            rows = canonical(); rows[7] += suffix
            with self.subTest(suffix=repr(suffix)), self.assertRaises(ValueError):
                home.parse_home_task(rows)

    def test_complete_empty_and_one_home_envelopes_are_distinguished(self):
        self.assertIsNone(home.parse_recent_home_baseline(fixtures.RECENTS))
        self.assertIsNone(home.parse_recent_home_baseline(fixtures.RECENTS.removesuffix(b"  (nothing)\n")))
        self.assertEqual(home.parse_home_task(canonical()), home.parse_recent_home_baseline(envelope()))

    def test_hidden_visible_only_competing_failed_truncated_and_extra_sections_refuse(self):
        good = envelope()
        variants = [b"", good[:-20], good + b"\n", good + b"  unknownSection=true\n", good.replace(b"  Recent tasks:", b"  Visible recent tasks (most recent first):"),
                    good.replace(b"  Recent tasks:", b"mHiddenTasks=[Task{abcdef}]\n  Recent tasks:"),
                    envelope(canonical() + canonical()), good.replace(b"type=home", b"type=standard"),
                    good.replace(b"mRecentsUid=1000", b"mRecentsUid=2147483648"), good + b"\r", good + b"\0"]
        for i, payload in enumerate(variants):
            with self.subTest(index=i), self.assertRaises(ValueError):
                home.parse_recent_home_baseline(payload)


class PreservedHomeControllerTests(fixtures.ModelFixture):
    """Inherited setup only, explicit new methods; no inherited accepted methods."""
    def baseline_owner(self):
        owner = self.model(fixtures.camera.Row(True, "1"))
        self.device.recent_tasks = envelope()
        return owner

    def test_real_snapshot_admits_only_fully_parsed_preserved_empty_home_without_writes(self):
        owner = self.baseline_owner()
        snapshot = owner.stable(fresh=True)
        self.assertEqual(home.parse_home_task(canonical()), snapshot.settings_home)
        self.assertEqual([], self.device.actions)

    def test_same_epoch_baseline_drift_or_disappearance_refuses_before_any_mutation(self):
        owner = self.baseline_owner()
        owner.original = owner.stable(fresh=True)
        for payload in (envelope(changed(12, "lastActiveTime=1", "lastActiveTime=2")), fixtures.RECENTS):
            self.device.recent_tasks = payload
            with self.assertRaises(ValueError):
                owner.snapshot(fresh=True)
            self.assertEqual([], self.device.actions)

    def test_same_epoch_rank_clock_progress_is_not_a_baseline_mutation(self):
        owner = self.baseline_owner(); owner.original = owner.stable(fresh=True)
        later = canonical(); later[0] = later[0].replace("Recent #0", "Recent #1"); later[12] = later[12].replace("2s", "25s")
        self.device.recent_tasks = envelope(later)
        self.assertEqual(owner.original, owner.stable(fresh=True))
        self.assertEqual([], self.device.actions)

    def test_a_new_task_is_never_substituted_under_an_unrequested_kernel_epoch(self):
        owner = self.baseline_owner(); owner.original = owner.stable(fresh=True)
        self.device.boot = fixtures.NEW
        with self.assertRaises(ValueError):
            owner.snapshot(fresh=True)
        self.assertEqual([], self.device.actions)

    def test_unchanged_old_strict_empty_parser_still_refuses_a_home_record(self):
        with self.assertRaises(ValueError):
            fixtures.camera.parse_recents(fixtures.cp(envelope()))

    def test_native_gate_distinguishes_nonowned_home_and_nonce_owned_standard_cleanup(self):
        source = NATIVE.read_text()
        for token in ("SettingsHomeTaskBaselineParser.parse(block)", "homeBaselineCaptured", "check(home == preservedHomeBaseline)",
                      "check(task.id != preservedHomeBaseline?.taskId)", "lease.removalAttempted = true",
                      'runComplete("am stack remove $taskId")'):
            self.assertIn(token, source)
        self.assertNotIn("am task remove", source)
        self.assertNotIn("force-stop", source)


class HomeEpochAndActionBoundaryTests(fixtures.ModelFixture):
    """NEW models for the later IPC boundary, never native execution or retries."""

    def captured_owner(self, *, empty=False):
        owner = self.model(fixtures.camera.Row(True, "1"))
        self.device.recent_tasks = fixtures.RECENTS if empty else envelope()
        owner.original = owner.stable(fresh=True)
        return owner

    def test_requested_new_epoch_has_its_own_stable_baseline_and_cannot_later_drift(self):
        owner = self.model()
        self.device.recent_tasks = envelope()
        owner.prepare()
        old = owner.original.settings_home
        after_reboot = changed(0, "abcdef", "abcde1")
        after_reboot[8] = after_reboot[8].replace("rootTaskId=17", "rootTaskId=1")
        later = envelope(after_reboot)

        def reboot_changes_home(args, device):
            if args == ("reboot",):
                device.recent_tasks = later

        self.device.hook = reboot_changes_home
        result = self.close_model()
        self.assertEqual("passed", result["cleanup_status"])
        self.assertEqual(fixtures.NEW, owner.new_boot)
        self.assertNotEqual(old, owner.new_epoch_settings_home)
        self.assertEqual(home.parse_home_task(after_reboot), owner.new_epoch_settings_home)
        actions = list(self.device.actions)
        for boot, payload in ((fixtures.NEW, envelope()), (fixtures.OLD, later),
                              (fixtures.NEW, fixtures.RECENTS)):
            with self.subTest(boot_is_new=boot == fixtures.NEW):
                self.device.boot, self.device.recent_tasks = boot, payload
                with self.assertRaises(ValueError):
                    owner.snapshot(fresh=True)
                self.assertEqual(actions, self.device.actions)

    def test_two_requested_new_epoch_snapshots_cannot_accept_different_home_records(self):
        owner = self.captured_owner()
        owner.enable_attempted = owner.reboot_attempted = True  # Synthetic owned request latch.
        self.device.boot = fixtures.NEW
        count = 0

        def different_completed_recents(args, device):
            nonlocal count
            if args == ("shell", "dumpsys", "activity", "-p", "com.android.settings", "recents"):
                count += 1
                return fixtures.cp(envelope() if count == 1 else envelope(changed(0, "abcdef", "abcde1")))

        self.device.hook = different_completed_recents
        with self.assertRaisesRegex(ValueError, "across complete snapshots"):
            owner.wait_new_epoch()
        self.assertEqual(2, count)
        self.assertIsNone(owner.new_boot)
        self.assertIsNone(owner.new_epoch_settings_home)
        self.assertIsNone(owner.deadline)
        self.assertEqual([], self.device.actions)

    def test_an_original_empty_home_baseline_cannot_acquire_a_task_in_the_same_epoch(self):
        owner = self.captured_owner(empty=True)
        self.device.recent_tasks = envelope()
        with self.assertRaises(ValueError):
            owner.snapshot(fresh=True)
        with self.assertRaises(ValueError):
            owner.control("reboot")
        self.assertEqual([], self.device.actions)

    def test_command_failure_stderr_and_partial_recent_records_refuse_before_baseline_admission(self):
        owner = self.captured_owner()
        for reply in (fixtures.cp(envelope(), code=1), fixtures.cp(envelope(), stderr=b"warning\n"),
                      fixtures.cp(envelope()[:-20])):
            def failing_recents(args, device):
                if args == ("shell", "dumpsys", "activity", "-p", "com.android.settings", "recents"):
                    return reply
            self.device.hook = failing_recents
            with self.subTest(code=reply.returncode, stderr=bool(reply.stderr)), self.assertRaises(ValueError):
                owner.snapshot(fresh=True)
            self.assertEqual([], self.device.actions)

    def test_every_existing_mutating_control_rechecks_home_at_its_own_ipc_boundary(self):
        owner = self.captured_owner()
        for payload in (envelope(changed(12, "lastActiveTime=1", "lastActiveTime=2")), fixtures.RECENTS):
            self.device.recent_tasks = payload
            for args in (("shell", "settings", "--user", "0", "put", "global", fixtures.camera.MASTER, "1"),
                         ("shell", "settings", "--user", "0", "put", "global", fixtures.camera.MASTER, "0"),
                         ("shell", "settings", "--user", "0", "delete", "global", fixtures.camera.MASTER),
                         ("uninstall", fixtures.camera.REPORTER), ("reboot",)):
                with self.subTest(payload_is_empty=payload == fixtures.RECENTS, action=args[0]), self.assertRaises(ValueError):
                    owner.control(*args)
                self.assertEqual([], self.device.actions)

    def test_epoch_is_rechecked_after_the_action_boundary_home_query_before_any_write(self):
        owner = self.captured_owner()
        def reboot_during_recents(args, device):
            if args == ("shell", "dumpsys", "activity", "-p", "com.android.settings", "recents"):
                device.boot = fixtures.NEW
                return fixtures.cp(envelope())
        self.device.hook = reboot_during_recents
        with self.assertRaises(ValueError):
            owner.control("shell", "settings", "--user", "0", "put", "global", fixtures.camera.MASTER, "0")
        self.assertEqual([], self.device.actions)

    def test_native_owned_leaf_and_root_both_exclude_both_preserved_home_identities(self):
        source = NATIVE.read_text()
        for comparison in ("task.id != preservedHomeBaseline?.taskId", "task.id != preservedHomeBaseline?.rootTaskId",
                           "task.rootId != preservedHomeBaseline?.taskId", "task.rootId != preservedHomeBaseline?.rootTaskId"):
            self.assertIn(comparison, source)
        self.assertLess(source.index("assertOwned(rows.single(), lease)", source.index("private fun closeSettings")),
                        source.index('runComplete("am stack remove $taskId")'))


if __name__ == "__main__":
    unittest.main()
