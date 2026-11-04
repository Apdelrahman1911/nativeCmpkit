# SPDX-License-Identifier: Apache-2.0
"""NEW finite manifest-affinity regressions; no Android or native executions."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import android_camera_home_baseline as home
import android_camera_home_refusal_observation as observation
import test_android_camera_home_baseline as fixture
import test_android_camera_developer_prerequisite as model

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_AFFINITY = "1000:com.android.settings.FallbackHome"


def manifest_rows():
    # Explicit synthetic producer-template rows, never actual hosted identifiers.
    rows = fixture.canonical()
    rows[0] = rows[0].replace("A=1000:com.android.settings}", "A=" + MANIFEST_AFFINITY + "}")
    rows[2] = "    affinity=" + MANIFEST_AFFINITY
    return rows


def refusal(rows):
    try:
        home.parse_recent_home_baseline(fixture.envelope(rows))
    except ValueError as error:
        return error
    raise AssertionError("The synthetic invalid candidate must actually refuse")


class ManifestHomeAffinityParserControls(unittest.TestCase):
    def setUp(self):
        for name in ("run", "Popen", "check_call", "check_output"):
            guard = patch.object(subprocess, name, side_effect=AssertionError("No process allowed by parser controls"))
            guard.start()
            self.addCleanup(guard.stop)

    def test_manifest_specific_and_previous_exact_forms_remain_complete_nonowned_baselines(self):
        rows = manifest_rows()
        before = rows.copy()
        baseline = home.parse_recent_home_baseline(fixture.envelope(rows))
        self.assertEqual(before, rows)
        self.assertEqual((17, 17), (baseline.task_id, baseline.root_task_id))
        self.assertEqual("SettingsHomeTaskBaseline(preserved, not owned)", repr(baseline))
        self.assertFalse(baseline.safe()["owned_or_removable"])
        self.assertNotEqual(home.parse_home_task(fixture.canonical()), baseline)
        self.assertNotIn(MANIFEST_AFFINITY, json.dumps(baseline.safe()))

    def test_both_header_body_affinity_hybrids_refuse_and_observe_exact_failed_equality(self):
        old_header = fixture.canonical()
        old_header[2] = manifest_rows()[2]
        new_header = manifest_rows()
        new_header[2] = fixture.canonical()[2]
        for rows in (old_header, new_header):
            with self.subTest(manifest_header=rows is new_header):
                before = rows.copy()
                error = refusal(rows)
                facts = observation.home_refusal(error)
                self.assertEqual("home-component", facts["guard"])
                self.assertTrue(facts["task_operand_facts"]["matches"]["home_header"])
                self.assertFalse(facts["task_operand_facts"]["matches"]["home_affinity"])
                self.assertTrue(facts["task_operand_facts"]["matches"]["task_id_matches_header"])
                self.assertEqual(before, rows)

    def test_unknown_case_uid_suffix_or_root_affinities_are_not_generic_admission(self):
        values = (MANIFEST_AFFINITY + ".extra", "1000:com.android.settings.root",
                  "1000:com.android.settings.fallbackhome", "2000:com.android.settings.FallbackHome",
                  "01000:com.android.settings.FallbackHome", "com.android.settings.FallbackHome")
        for value in values:
            rows = manifest_rows()
            rows[0] = rows[0].replace(MANIFEST_AFFINITY, value)
            rows[2] = "    affinity=" + value
            with self.subTest(kind=values.index(value)):
                self.assertEqual(("Exact fallback HOME header required",), refusal(rows).args)
        for suffix in (" root=1000:com.android.settings", " ", "\t", "\r", "é"):
            rows = manifest_rows()
            rows[2] += suffix
            with self.subTest(suffix=repr(suffix)), self.assertRaises(ValueError):
                home.parse_home_task(rows)

    def test_manifest_affinity_never_waives_unchanged_caller_component_live_or_identity_bounds(self):
        mutations = ((0, "#17", "#2147483648"), (0, "Recent #0", "Recent #2147483648"),
                     (0, "type=home", "type=standard"), (1, "mCallingUid=0", "mCallingUid=2000"),
                     (1, "effectiveUid=1000", "effectiveUid=10001"),
                     (1, "mUserSetupComplete=false", "mUserSetupComplete=true"),
                     (3, "/.FallbackHome", "/.Settings$DevelopmentSettingsActivity"),
                     (4, "/.FallbackHome", "/.Settings$DevelopmentSettingsActivity"),
                     (7, "[]", "[ActivityRecord{abcdef u0 com.android.settings/.FallbackHome t17}]"),
                     (8, "taskId=17", "taskId=18"), (8, "rootTaskId=17", "rootTaskId=2147483648"),
                     (9, "false", "true"), (12, "lastActiveTime=1", "lastActiveTime=9223372036854775808"))
        for index, old, new in mutations:
            rows = manifest_rows()
            self.assertIn(old, rows[index])
            rows[index] = rows[index].replace(old, new)
            with self.subTest(row=index, mutation=old), self.assertRaises(ValueError):
                home.parse_home_task(rows)

    def test_manifest_record_requires_every_role_once_and_rejects_unknown_or_unsafe_bytes(self):
        rows = manifest_rows()
        for index in range(13):
            for candidate in (rows[:index] + rows[index + 1:],
                              rows[:index] + [rows[(index + 1) % 13]] + rows[index + 1:]):
                with self.subTest(row=index), self.assertRaises(ValueError):
                    home.parse_home_task(candidate)
        for payload in (fixture.envelope(rows + ["    unknownPolicy=true"]), fixture.envelope(rows) + b"\n",
                        fixture.envelope(rows) + b"\r", fixture.envelope(rows) + b"\0"):
            with self.assertRaises(ValueError):
                home.parse_recent_home_baseline(payload)

    def test_manifest_baseline_only_normalizes_rank_elapsed_time_not_affinity_or_identity(self):
        before = home.parse_home_task(manifest_rows())
        later = manifest_rows()
        later[0] = later[0].replace("Recent #0", "Recent #3")
        later[12] = later[12].replace("inactive for 2s", "inactive for 999s")
        self.assertEqual(before, home.parse_home_task(later))
        for index, old, new in ((0, "abcdef", "abcde1"), (8, "rootTaskId=17", "rootTaskId=1"),
                                (12, "lastActiveTime=1", "lastActiveTime=2")):
            changed = manifest_rows()
            changed[index] = changed[index].replace(old, new)
            self.assertNotEqual(before, home.parse_home_task(changed))
        self.assertNotEqual(before, home.parse_home_task(fixture.canonical()))

    def test_failure_only_observer_uses_new_equality_without_retry_export_or_native_inference(self):
        rows = manifest_rows()
        rows[12] = rows[12].replace("lastActiveTime=1", "lastActiveTime=9223372036854775808")
        error = refusal(rows)
        args, trace = error.args, error.__traceback__
        parser_calls = []
        previous_profile = sys.getprofile()
        parser_codes = (home.parse_home_task.__code__, home.parse_recent_home_baseline.__code__)
        def profile(frame, event, argument):
            if event == "call" and frame.f_code in parser_codes:
                parser_calls.append(frame.f_code.co_name)
        try:
            sys.setprofile(profile)
            facts = observation.home_refusal(error)
        finally:
            sys.setprofile(previous_profile)
        self.assertEqual("home-clock", facts["guard"])
        self.assertTrue(facts["task_operand_facts"]["matches"]["home_affinity"])
        self.assertEqual(args, error.args)
        self.assertIs(trace, error.__traceback__)
        self.assertFalse(facts["parser_retried"])
        self.assertFalse(facts["recents_absence_verified"])
        self.assertFalse(facts["query_exit_or_owner_inferred"])
        self.assertEqual(0, facts["new_queries_or_native_operations"])
        for private in (MANIFEST_AFFINITY, "abcdef", str(ROOT)):
            self.assertNotIn(private, json.dumps(facts))
        self.assertEqual([], parser_calls)

    def test_python_kotlin_header_affinity_and_stable_row_contracts_have_exact_parity(self):
        kotlin = (ROOT / "calf-camera-picker/src/commonTest/kotlin/com/mohamedrejeb/calf/camerapicker/SettingsHomeTaskBaseline.kt").read_text()
        heading = kotlin.split('private val header = Regex("""', 1)[1].split('""")', 1)[0]
        self.assertEqual(home.HEADER.pattern, heading.replace("$positiveInt", home.POSITIVE_INT))
        self.assertIn('check(rows[2] == "    affinity=" + heading.groupValues[4])', kotlin)
        self.assertIn('check(identifiers.groupValues[1].toIntOrNull() == taskId)', kotlin)
        self.assertIn('heading.groupValues[2]', kotlin)
        tree = ast.parse((ROOT / "scripts/ci/android_camera_home_baseline.py").read_bytes())
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
                             node.func.attr in {"run", "Popen", "control", "read_bytes", "write_bytes", "open"}
                             for node in ast.walk(tree)))


class ManifestHomeAffinityControllerControls(model.ModelFixture):
    """Only NEW methods on existing inert fixtures; not Android execution."""

    def test_real_controller_snapshots_preserve_manifest_baseline_and_refuse_branch_drift_before_actions(self):
        owner = self.model(model.camera.Row(True, "1"))
        self.device.recent_tasks = fixture.envelope(manifest_rows())
        owner.original = owner.stable(fresh=True)
        self.assertEqual(home.parse_home_task(manifest_rows()), owner.original.settings_home)
        self.assertEqual([], self.device.actions)
        self.device.recent_tasks = fixture.envelope(fixture.canonical())
        with self.assertRaisesRegex(ValueError, "Original same-epoch HOME baseline changed"):
            owner.snapshot(fresh=True)
        self.assertEqual([], self.device.actions)

    def test_action_boundary_manifest_drift_refuses_before_any_allowed_mutating_ipc(self):
        owner = self.model(model.camera.Row(True, "1"))
        self.device.recent_tasks = fixture.envelope(manifest_rows())
        owner.original = owner.stable(fresh=True)
        rows = manifest_rows()
        rows[12] = rows[12].replace("lastActiveTime=1", "lastActiveTime=2")
        self.device.recent_tasks = fixture.envelope(rows)
        with self.assertRaisesRegex(ValueError, "Original same-epoch HOME baseline changed"):
            owner.action_guard()
        self.assertEqual([], self.device.actions)


if __name__ == "__main__":
    unittest.main()
