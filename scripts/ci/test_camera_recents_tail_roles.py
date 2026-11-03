# SPDX-License-Identifier: Apache-2.0
"""Returned-query grammar observations only; zero devices or absence admissions."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import android_camera_developer_prerequisite as camera
import android_camera_recents_observation as observation

PREFIX = (camera.RECENTS_HEADER + "\nmRecentsUid=1000\n"
          "mRecentsComponent=ComponentInfo{com.android.launcher3/.QuickstepService}\n"
          "mFreezeTaskListReordering=false\nmFreezeTaskListReorderingPendingTimeout=false\n").encode()
HOME = [
    "  Recent tasks:",
    "  * Recent #0: Task{abcdef #17 type=home A=1000:com.android.settings}",
    "    userId=0 effectiveUid=1000 mCallingUid=1000 mUserSetupComplete=true mCallingPackage=com.android.settings mCallingFeatureId=null",
    "    affinity=1000:com.android.settings",
    "    intent={act=android.intent.action.MAIN cat=[android.intent.category.HOME] flg=0x10000100 cmp=com.android.settings/.FallbackHome}",
    "    mActivityComponent=com.android.settings/.FallbackHome",
    "    autoRemoveRecents=false isPersistable=false activityType=2",
    "    Activities=[]",
    "    taskId=17 rootTaskId=17",
    "    hasChildPipActivity=false",
    "    mHasBeenVisible=true",
    "    mResizeMode=RESIZE_MODE_RESIZEABLE mSupportsPictureInPicture=false isResizeable=true",
    "    lastActiveTime=1 (inactive for 2s)",
]


def observe(rows):
    payload = PREFIX + ("\n".join(rows) + "\n").encode()
    result = subprocess.CompletedProcess(
        ["/synthetic-sdk/platform-tools/adb", *observation.QUERY_ARGUMENTS], 0, payload, b"")
    try:
        camera.parse_recents(result)
    except ValueError as error:
        trace, args = error.__traceback__, error.args
        facts = observation.recents_refusal(error)
        if error.__traceback__ is not trace or error.args != args or result.stdout != payload:
            raise AssertionError("The observer changed the held original refusal")
        return facts, facts["tail_structure"]
    raise AssertionError("The owning parser must still refuse these synthetic tasks")


class CameraRecentsTailRoleControls(unittest.TestCase):
    def test_home_shape_is_observed_but_never_certifies_absence_or_ownership(self):
        facts, shape = observe(HOME)
        self.assertTrue(shape["available"])
        self.assertEqual(1, shape["task_type_rows"]["home"])
        self.assertEqual(0, shape["task_type_rows"]["standard"])
        self.assertEqual(1, shape["fixed_component_rows"]["settings_fallback_home"])
        self.assertEqual(1, shape["empty_activities_rows"])
        self.assertTrue(shape["single_task_header_dump_ids_match"])
        self.assertEqual(0, shape["unknown_rows"])
        for key in ("task_ownership_verified", "system_image_provenance_verified", "admission_changed"):
            self.assertFalse(shape[key])
        self.assertFalse(facts["original_operand_matches"]["exact_tail"])
        self.assertTrue(facts["original_reader_still_refused"])
        self.assertFalse(facts["recents_absence_verified"])

    def test_standard_foreign_multiple_and_mismatched_ids_remain_distinct_observations(self):
        standard = [row.replace("type=home", "type=standard").replace("/.FallbackHome", "/.Settings$DevelopmentSettingsActivity")
                    for row in HOME]
        _, shape = observe(standard)
        self.assertEqual(1, shape["task_type_rows"]["standard"])
        self.assertEqual(1, shape["fixed_component_rows"]["settings_development"])
        _, shape = observe(HOME + standard[1:])
        self.assertEqual(1, shape["task_type_rows"]["home"])
        self.assertEqual(1, shape["task_type_rows"]["standard"])
        self.assertIsNone(shape["single_task_header_dump_ids_match"])
        _, shape = observe([row.replace("taskId=17", "taskId=18") for row in HOME])
        self.assertFalse(shape["single_task_header_dump_ids_match"])
        _, shape = observe([row.replace("type=home", "type=private-unknown") for row in HOME])
        self.assertEqual(1, shape["unknown_rows"])
        self.assertEqual(0, sum(shape["task_type_rows"].values()))

    def test_identity_matches_export_only_fixed_field_booleans_not_caller_values(self):
        _, shape = observe(HOME)
        self.assertEqual(1, shape["identity_matches"]["user_zero"])
        self.assertEqual(1, shape["identity_matches"]["effective_uid_1000"])
        self.assertEqual(1, shape["identity_matches"]["caller_uid_1000"])
        self.assertEqual(1, shape["identity_matches"]["caller_settings"])
        changed = [row.replace("mCallingUid=1000", "mCallingUid=2000")
                   .replace("mCallingPackage=com.android.settings", "mCallingPackage=com.android.shell") for row in HOME]
        _, shape = observe(changed)
        self.assertEqual(1, shape["identity_matches"]["caller_uid_2000"])
        self.assertEqual(1, shape["identity_matches"]["caller_shell"])
        self.assertEqual(0, shape["identity_matches"]["caller_settings"])

    def test_missing_duplicate_overflow_or_incomplete_fields_never_supply_id_identity(self):
        variants = (
            [row for row in HOME if not row.startswith("    taskId=")],
            HOME + ["    taskId=17 rootTaskId=17"],
            [row.replace("#17", "#9999999999").replace("taskId=17", "taskId=9999999999") for row in HOME],
            [row.replace(" mCallingFeatureId=null", "") for row in HOME],
        )
        for rows in variants:
            with self.subTest(rows=len(rows)):
                _, shape = observe(rows)
                self.assertTrue(shape["available"])
                self.assertFalse(shape["task_ownership_verified"])
                if not any("mCallingFeatureId=" in row for row in rows):
                    self.assertEqual(0, shape["identity_rows"])
                else:
                    self.assertIsNone(shape["single_task_header_dump_ids_match"])

    def test_unknown_body_bytes_are_counted_without_export_or_normalization(self):
        private = "private-body-should-never-export-user-or-environment"
        _, shape = observe(HOME + ["    " + private, " \t", ""])
        self.assertEqual(3, shape["unknown_rows"])
        self.assertNotIn(private, json.dumps(shape))
        self.assertNotIn("abcdef", json.dumps(shape))
        self.assertNotIn("com.android.settings", json.dumps(shape))
        self.assertEqual(len(HOME) + 3, shape["tail_rows_observed"])

    def test_tail_and_row_budgets_are_unavailable_not_partial_or_zero(self):
        for rows, reason in ((["private"] * 65, "tail-row-budget"), (["x" * 2049], "row-byte-budget")):
            with self.subTest(reason=reason):
                facts, shape = observe(rows)
                self.assertFalse(shape["available"])
                self.assertEqual(reason, shape["reason"])
                self.assertNotIn("task_type_rows", shape)
                self.assertFalse(facts["recents_absence_verified"])
                self.assertLess(len(json.dumps(facts).encode()), 8192)

    def test_short_or_nothing_like_refusals_stay_non_admissions(self):
        for rows in (["  (nothing)", "private"], ["  Recent tasks:"], [""], ["  Visible recent tasks (most recent first):"]):
            with self.subTest(rows=len(rows)):
                facts, shape = observe(rows)
                self.assertTrue(shape["available"])
                self.assertIsNone(shape["single_task_header_dump_ids_match"])
                self.assertFalse(facts["recents_absence_verified"])
                self.assertFalse(shape["task_ownership_verified"])
                self.assertLess(len(json.dumps(facts).encode()), 8192)

    def test_role_reader_has_no_execution_or_original_parser_calls_and_does_not_mask_failure(self):
        # This helper is observational only. The controller's original optional
        # observer guard preserves any error; no new device/IO/parser operation.
        source = Path(observation.__file__).read_text()
        tree = ast.parse(source)
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "tail_structure")
        calls = [node for node in ast.walk(function) if isinstance(node, ast.Call)]
        self.assertFalse(any(isinstance(node.func, ast.Attribute) and node.func.attr in
                             {"parse_recents", "control", "run", "Popen", "open", "read_bytes", "write_bytes"}
                             for node in calls))
        self.assertFalse(any(isinstance(node.func, ast.Name) and node.func.id in {"exec", "eval", "open", "compile"}
                             for node in calls))
        with patch.object(observation, "tail_structure", wraps=observation.tail_structure) as reader:
            facts, _ = observe(HOME)
        self.assertEqual(1, reader.call_count)
        self.assertEqual(0, facts["new_queries_or_native_operations"])
        self.assertFalse(facts["parser_retried"])


if __name__ == "__main__":
    unittest.main()
