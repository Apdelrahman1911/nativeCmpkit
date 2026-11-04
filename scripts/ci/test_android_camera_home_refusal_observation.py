# SPDX-License-Identifier: Apache-2.0
"""Important actual-parser/handler controls; no Android, process or native work."""
import ast
import json
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

import android_camera_developer_prerequisite as camera
import android_camera_home_baseline as home
import android_camera_home_refusal_observation as observation
import android_camera_recents_observation as route
import test_android_camera_home_baseline as fixture
import test_camera_recents_observation as old_fixture

ROOT = Path(__file__).resolve().parents[2]
MARKER = "private-HOME-row-or-path-must-not-export"


def refused(payload):
    try:
        home.parse_recent_home_baseline(payload)
    except ValueError as error:
        return error
    raise AssertionError("Original HOME parser must actually refuse the synthetic payload")


def bad_row_count():
    return fixture.envelope(fixture.canonical()[:6] + fixture.canonical()[7:])


class CameraHomeRefusalObservationControls(unittest.TestCase):
    def setUp(self):
        for name in ("run", "Popen", "check_call", "check_output"):
            guard = patch.object(subprocess, name, side_effect=AssertionError("No process is authorized by source controls"))
            guard.start(); self.addCleanup(guard.stop)

    def test_original_row_count_refusal_has_exact_inner_origin_and_never_changes_input_or_exception(self):
        payload = bad_row_count(); error = refused(payload); trace, args = error.__traceback__, error.args
        facts = observation.home_refusal(error)
        self.assertIs(error.__traceback__, trace)
        self.assertEqual(args, error.args)
        self.assertEqual("recent-row-count", facts["guard"])
        self.assertEqual({"source": "android_camera_home_baseline.py", "symbol": "parse_recent_home_baseline", "line": 101}, facts["require_call_origin"])
        self.assertEqual(18, facts["row_count"])
        self.assertEqual(12, facts["task_row_count"])
        self.assertFalse(facts["original_row_count_matches"])
        self.assertFalse(facts["task_operand_facts"]["available"])
        self.assertTrue(facts["original_reader_still_refused"])
        for key in ("parser_retried", "query_exit_or_owner_inferred", "recents_absence_verified", "original_scalar_or_cause_inferred"):
            self.assertFalse(facts[key])
        self.assertEqual(0, facts["new_queries_or_native_operations"])

    def test_complete_task_identity_component_root_policy_and_clock_operands_are_independent_facts(self):
        cases = ((1, "mCallingUid=0", "mCallingUid=2000", "bootstrap-identity", "bootstrap_identity"),
                 (3, "0x10000100", "0x010000100", "home-component", "home_intent"),
                 (6, "LOCK_TASK_AUTH_DONT_LOCK", "LOCK_TASK_AUTH_UNKNOWN", "home-policy", "root_policy"),
                 (8, "taskId=17", "taskId=18", "home-task-id-bounds", "task_id_matches_header"),
                 (11, "RESIZE_MODE_UNRESIZEABLE", "RESIZE_MODE_UNKNOWN", "home-child-policy", "resize_policy"),
                 (12, "lastActiveTime=1", "lastActiveTime=9223372036854775808", "home-clock", "clock_shape_and_bounds"))
        for index, old, new, guard, operand in cases:
            with self.subTest(guard=guard):
                rows = fixture.canonical(); rows[index] = rows[index].replace(old, new)
                facts = observation.home_refusal(refused(fixture.envelope(rows)))
                self.assertEqual(guard, facts["guard"])
                self.assertEqual("parse_home_task", facts["require_call_origin"]["symbol"])
                self.assertFalse(facts["task_operand_facts"]["matches"][operand])
                self.assertTrue(all(type(v) is bool for v in facts["task_operand_facts"]["matches"].values()))

    def test_framing_and_raw_list_refusals_never_export_private_rows_ids_or_paths(self):
        for payload, guard in ((fixture.envelope().replace(b"mFreezeTaskListReordering=false", b"mFreezeTaskListReordering=unknown"), "recent-framing"),
                               (fixture.envelope().replace(b"  Recent tasks:", b"  " + MARKER.encode()), "raw-task-header")):
            with self.subTest(guard=guard):
                facts = observation.home_refusal(refused(payload))
                self.assertEqual(guard, facts["guard"])
                output = json.dumps(facts)
                self.assertLess(len(output.encode()), 8192)
                for private in (MARKER, "abcdef", "com.android.settings", str(ROOT)):
                    self.assertNotIn(private, output)
                self.assertLessEqual(len(facts["observed_rows"]), 8)

    def test_unsafe_nonordinary_oversized_or_exhausted_inputs_are_unavailable_not_zero(self):
        for payload in (b"", None, bytearray(fixture.envelope()), fixture.envelope() + b"\r", b"x" * (home.MAX_REPLY_BYTES + 1),
                        fixture.envelope() + b"\n" * (observation.MAX_ROWS + 1)):
            with self.subTest(kind=type(payload).__name__):
                self.assertIsNone(observation.home_refusal(refused(payload)))
        error = refused(bad_row_count())
        with patch.object(observation, "MAX_FRAMES", 0): self.assertIsNone(observation.home_refusal(error))

    def test_unraised_foreign_spoofed_subclass_or_modified_guard_cannot_supply_a_live_origin(self):
        error = refused(bad_row_count())
        self.assertIsNone(observation.home_refusal(ValueError(*error.args)))
        self.assertIsNone(observation.home_refusal(RuntimeError(*error.args).with_traceback(error.__traceback__)))
        class Derived(ValueError):
            pass
        self.assertIsNone(observation.home_refusal(Derived(*error.args).with_traceback(error.__traceback__)))
        error.args = (MARKER,)
        self.assertIsNone(observation.home_refusal(error))
        namespace = {"require": home.require}
        exec(compile('def parse_recent_home_baseline():\n    require(False, "Exact complete recent-task row count required")\n',
                     home.parse_recent_home_baseline.__code__.co_filename, "exec"), namespace)
        try:
            namespace["parse_recent_home_baseline"]()
        except ValueError as foreign:
            self.assertIsNone(observation.home_refusal(foreign))

    def test_changed_live_parent_or_task_rows_never_supply_partial_metadata(self):
        for target in (home.parse_recent_home_baseline, home.parse_home_task):
            rows = fixture.canonical(); rows[1] = rows[1].replace("mCallingUid=0", "mCallingUid=2000")
            error = refused(fixture.envelope(rows)); node = error.__traceback__
            while node.tb_frame.f_code is not target.__code__: node = node.tb_next
            node.tb_frame.f_locals["rows"].append(MARKER)
            self.assertIsNone(observation.home_refusal(error))

    def test_over_budget_nonterminal_or_noninstruction_trace_remains_unavailable(self):
        original = refused(bad_row_count()); frame = sys._getframe(); head = original.__traceback__
        for _ in range(65): head = types.TracebackType(head, frame, frame.f_lasti, frame.f_lineno)
        self.assertIsNone(observation.home_refusal(ValueError(*original.args).with_traceback(head)))
        caller = original.__traceback__
        while caller.tb_frame.f_code is not home.parse_recent_home_baseline.__code__: caller = caller.tb_next
        terminal = caller.tb_next
        head = types.TracebackType(terminal, caller.tb_frame, caller.tb_lasti, 20000)
        self.assertIsNone(observation.home_refusal(ValueError(*original.args).with_traceback(head)))
        tail = types.TracebackType(None, frame, frame.f_lasti, frame.f_lineno)
        nonterminal = types.TracebackType(tail, terminal.tb_frame, terminal.tb_lasti, terminal.tb_lineno)
        head = types.TracebackType(nonterminal, caller.tb_frame, caller.tb_lasti, caller.tb_lineno)
        self.assertIsNone(observation.home_refusal(ValueError(*original.args).with_traceback(head)))

    def test_existing_controller_routes_new_facts_after_the_same_primary_failure_without_native_actions(self):
        old_fixture.CameraRecentsControllerControls.setUpClass()
        handler = old_fixture.CameraRecentsControllerControls.handler
        error = refused(bad_row_count()); original_args, trace = error.args, error.__traceback__
        result = {"passed": False, "test_suite_passed": False}
        returned = handler(result, error, True, True)
        self.assertIs(returned, result)
        self.assertEqual("ValueError", result["controller_error"])
        self.assertEqual("recent-row-count", result["camera_recents_refusal"]["guard"])
        self.assertFalse(result["passed"] or result["test_suite_passed"])
        self.assertEqual(original_args, error.args)
        self.assertIs(trace, error.__traceback__)
        with patch.object(observation, "home_refusal", side_effect=AssertionError("noncamera observer must not execute")) as observe:
            handler({}, error, True, False)
        observe.assert_not_called()

    def test_observer_exception_or_interrupt_preserves_primary_failure_and_legacy_recents_route(self):
        old_fixture.CameraRecentsControllerControls.setUpClass(); handler = old_fixture.CameraRecentsControllerControls.handler
        for secondary in (RuntimeError(MARKER), KeyboardInterrupt(MARKER)):
            with self.subTest(kind=type(secondary).__name__), patch.object(observation, "home_refusal", side_effect=secondary):
                result = handler({}, refused(bad_row_count()), True, True)
                self.assertEqual("ValueError", result["controller_error"])
                self.assertNotIn("camera_recents_refusal", result)
        legacy, _ = old_fixture.refused()
        with patch.object(observation, "home_refusal", side_effect=AssertionError("legacy route must not change")) as observe:
            facts = route.recents_refusal(legacy)
        observe.assert_not_called()
        self.assertEqual("nativecmpkit.camera-recents-refusal.v1", facts["schema"])

    def test_observation_has_no_parser_process_io_or_mutation_calls_and_retains_admission_source(self):
        source = (ROOT / "scripts/ci/android_camera_home_refusal_observation.py").read_bytes()
        tree = ast.parse(source)
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
        self.assertFalse(any(isinstance(n.func, ast.Attribute) and n.func.attr in
                             {"parse_recent_home_baseline", "parse_home_task", "require", "control", "run", "Popen", "open", "read_bytes", "write_bytes"}
                             for n in calls))
        self.assertFalse(any(isinstance(n.func, ast.Name) and n.func.id in {"exec", "eval", "open", "compile", "setattr"} for n in calls))
        targets = [target for n in ast.walk(tree) if isinstance(n, (ast.Assign, ast.AugAssign))
                   for target in (n.targets if isinstance(n, ast.Assign) else [n.target])]
        self.assertFalse(any(isinstance(child, ast.Attribute) and child.attr == "args"
                             for target in targets for child in ast.walk(target)))
        self.assertEqual(15, len(observation.GUARDS))


if __name__ == "__main__":
    unittest.main()
