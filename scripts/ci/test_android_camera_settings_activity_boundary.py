"""New Activity-boundary adversaries only; no SDK/native/build or accepted-suite run."""
from __future__ import annotations

import ast
from contextlib import ExitStack
import hashlib
if __package__:
    from .test_android_camera_settings_activity_refusal_diagnostics import historical_helper_source
else:
    from test_android_camera_settings_activity_refusal_diagnostics import historical_helper_source
import importlib.util
import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

TREE = Path(os.environ.get("CAMERA_SETTINGS_ACTIVITY_MODEL_TREE", Path(__file__).resolve().parents[2])).resolve()
PRIVATE = Path(os.environ.get("CAMERA_SETTINGS_ACTIVITY_MODEL_TMP", tempfile.gettempdir())).resolve()
HELPER = TREE / "scripts/ci/android_camera_developer_prerequisite.py"
SPEC = importlib.util.spec_from_file_location("camera_settings_activity_fixture_helpers",
                                            TREE / "scripts/ci/test_android_camera_developer_prerequisite.py")
fixtures = importlib.util.module_from_spec(SPEC)
with patch.dict(os.environ, {"CAMERA_PREREQUISITE_MODEL_TREE": str(TREE), "CAMERA_PREREQUISITE_MODEL_TMP": str(PRIVATE)}):
    with patch.dict(sys.modules, {SPEC.name: fixtures}):
        SPEC.loader.exec_module(fixtures)
camera = fixtures.camera
COMMAND = ("shell", "dumpsys", "activity", "-p", "com.android.settings", "activities")
BASE_HELPER_AST_SHA256 = "a15f841951909384da6893c6d66fd5d850a5d1c60d918ad0d5b9cc703f6f4ac2"
READER_AST_SHA256 = "97cb9c3d5c33b9676560c0952e061720247a6f91cfa2768b5b75ed66c18dd7b6"


def forbidden(*args, **kwargs):
    raise AssertionError("No SDK, subprocess, build, network, signal or native action is allowed")


class NoNativeActions:
    def setUp(self):
        self.guards = ExitStack()
        self.addCleanup(self.guards.close)
        for name in ("Popen", "run", "check_output", "check_call"):
            self.guards.enter_context(patch.object(camera.subprocess, name, forbidden))
        for name in ("kill", "killpg", "system"):
            self.guards.enter_context(patch.object(camera.os, name, forbidden))
        self.guards.enter_context(patch.object(socket, "socket", forbidden))
        super().setUp()


def activities(displays=(0,), extra=(), *, final=True):
    rows = [camera.ACTIVITIES_HEADER]
    rows.extend("Display #" + str(number) + " (activities from top to bottom):" for number in displays)
    rows.extend(extra)
    if final:
        rows.append("  (nothing)")
    return ("\n".join(rows) + "\n").encode()


class ActivityAbsenceGrammarModels(NoNativeActions, unittest.TestCase):
    def refused(self, payload):
        with self.assertRaises(ValueError):
            camera.parse_settings_activity_absence(fixtures.cp(payload))

    def test_single_native_display_requires_no_extra_rows(self):
        for payload in (activities(), activities().removesuffix(b"\n")):
            camera.parse_settings_activity_absence(fixtures.cp(payload))

    def test_multiple_unique_native_nonnegative_integer_displays_admitted(self):
        for ids in ((2, 0), (2147483647, 7, 0)):
            camera.parse_settings_activity_absence(fixtures.cp(activities(ids)))

    def test_header_and_sentinel_without_complete_traversal_are_not_absence_proof(self):
        for payload in (b"", (camera.ACTIVITIES_HEADER + "\n  (nothing)\n").encode(),
                        activities(final=False), b"Display #0 (activities from top to bottom):\n  (nothing)\n",
                        activities().replace(camera.ACTIVITIES_HEADER.encode(), camera.RECENTS_HEADER.encode())):
            with self.subTest(variant=hashlib.sha256(payload).hexdigest()):
                self.refused(payload)

    def test_duplicate_headers_sentinels_or_displays_refused(self):
        for payload in (activities((0, 0)), activities(extra=(camera.ACTIVITIES_HEADER,)),
                        activities(extra=("  (nothing)",)), activities() + b"  (nothing)\n"):
            with self.subTest(variant=hashlib.sha256(payload).hexdigest()):
                self.refused(payload)

    def test_noncanonical_negative_or_overflow_display_ids_refused(self):
        for value in ("-1", "+0", "00", "01", "2147483648", "9999999999", "1" * 11, "0.0", " 0", "0 user=0"):
            with self.subTest(display=value):
                self.refused(activities().replace(b"Display #0 ", ("Display #" + value + " ").encode()))

    def test_nonbinary_failed_stderr_or_unbounded_control_results_refused(self):
        for result in (fixtures.cp(activities(), code=1), fixtures.cp(activities(), stderr=b"permission denied\n"),
                       fixtures.cp(activities().decode()), fixtures.cp(activities(), stderr=""),
                       fixtures.cp(b"x" * (camera.CONTROL_BYTES + 1))):
            with self.assertRaises(ValueError):
                camera.parse_settings_activity_absence(result)

    def test_controls_invalid_utf8_blank_console_and_client_rows_refused(self):
        payloads = [activities().replace(b"\n", b"\r\n"), activities() + b"\0", activities() + b"\x1b",
                    activities() + b"\xff", b"\n" + activities(), activities() + b"\n"]
        payloads += [activities(extra=(row,)) for row in ("", " ", "Error: unknown option -p", "Warning: partial dump",
                     "java.lang.Exception", "    Failed to dump client: timeout", "  private console output")]
        for payload in payloads:
            with self.subTest(variant=hashlib.sha256(payload).hexdigest()):
                self.refused(payload)

    def test_nested_started_or_resumed_activity_rows_refused_even_with_terminal_nothing(self):
        for rows in (("  * Task{root com.example.root/.RootActivity}", "    * TaskFragment{middle}",
                      "      * Hist #1: ActivityRecord{aa u0 com.android.settings/.Settings$DevelopmentSettingsDashboardActivity t2}",
                      "        state=STARTED"),
                     ("  ResumedActivity: ActivityRecord{aa u0 com.android.settings/.Settings t2}",),
                     ("  Resumed activities in task display areas (from top to bottom):",
                      "    Resumed: ActivityRecord{aa u0 com.android.settings/.Settings t2}")):
            self.refused(activities(extra=rows))

    def test_global_stopping_and_finishing_rows_refused_even_with_terminal_nothing(self):
        for label in ("  Activities waiting to stop:", "  Activities waiting to finish:"):
            self.refused(activities(extra=(label,
                "    * Stop #0: ActivityRecord{aa u0 com.android.settings/.Settings$DevelopmentSettingsDashboardActivity t2}")))


class ActivityBoundaryModels(NoNativeActions, fixtures.ModelFixture):
    def cached(self, master=None, *, scalar=None, native=False):
        self.model(master, scalar=scalar, native=native)
        self.device.settings_process = True
        self.device.new_settings_process = True
        self.assertEqual(camera.parse_native(fixtures.cp(fixtures.native_payload(native, True))), (native, True))
        return self.owner

    def successful_close(self):
        self.dispatch()
        receipt = self.close_model()
        self.assertTrue(camera.accepted(receipt, self.disposal()))
        self.assertIs(receipt["native_acceptance_inferred"], False)
        return receipt

    def sticky_close(self, receipt):
        before = list(self.device.actions)
        self.assertEqual(self.owner.close(), receipt)
        self.assertEqual(self.device.actions, before)

    def test_cached_settings_process_without_activities_admitted_before_enable(self):
        self.cached().prepare()
        self.assertEqual(self.owner.original.pair(), (False, camera.Row(False, None)))
        receipt = self.successful_close()
        self.assertEqual([tuple(call[3:]) for call in self.device.calls if tuple(call[3:]) == COMMAND].count(COMMAND), 8)
        self.assertEqual((receipt["master_enable_attempts"], receipt["normal_reboot_attempts"],
                          receipt["master_restore_attempts"]), (1, 1, 1))

    def test_dependency_only_token_without_activities_is_not_a_live_ui_proof(self):
        self.model()
        def dependency(args, device):
            if args == ("shell", "dumpsys", "activity", "processes"):
                return fixtures.cp(fixtures.native_payload(device.native).replace(camera.READINESS.encode(),
                    b"    packageDependencies={com.android.settings}\n" + camera.READINESS.encode()))
        self.device.hook = dependency
        observation = dependency(("shell", "dumpsys", "activity", "processes"), self.device)
        self.assertTrue(camera.parse_native(observation)[1])
        self.owner.prepare()
        self.successful_close()

    def test_changed_boot_cached_process_with_zero_activities_keeps_exact_native_scalar_and_restores_once(self):
        self.cached(camera.Row(True, "0"), scalar=camera.Row(True, "1"), native=True).prepare()
        receipt = self.successful_close()
        self.assertTrue(receipt["kernel_barrier_verified"])
        self.assertNotEqual(self.device.boot, fixtures.OLD)
        self.assertEqual(self.device.master, camera.Row(True, "0"))
        self.assertEqual((self.device.native, self.device.scalar), (True, camera.Row(True, "1")))
        self.assertEqual(receipt["master_restore_attempts"], 1)
        self.sticky_close(receipt)

    def test_middle_settings_activity_behind_foreign_root_and_translucent_top_refused(self):
        self.cached()
        # These old readers have no interior Activity identity; this is a
        # source-backed adversarial model, not the attributed actual-run cause.
        camera.parse_recents(fixtures.cp(self.device.recent_tasks))
        camera.parse_live_tasks(fixtures.cp(self.device.live_tasks))
        self.device.settings_activities = activities(extra=(
            "  * Task{root com.example.root/.RootActivity}", "    * TaskFragment{middle}",
            "      * Hist #1: ActivityRecord{aa u0 com.android.settings/.Settings$DevelopmentSettingsDashboardActivity t2}",
            "        state=STARTED", "      * Hist #0: ActivityRecord{bb u0 com.example.overlay/.TranslucentTopActivity t2}"))
        with self.assertRaises(ValueError):
            self.owner.prepare()
        self.assertIsNone(self.owner.original)
        self.assertEqual(self.device.actions, [])
        receipt = self.close_model()
        self.assertFalse(camera.accepted(receipt, self.disposal()))
        self.assertEqual(receipt["master_restore_attempts"], 0)
        self.sticky_close(receipt)

    def test_existing_settings_recent_task_refusal_is_not_weakened(self):
        self.cached()
        self.device.recent_tasks += b"  Recent tasks:\n  * Recent #0: Task{com.android.settings/.Settings}\n"
        with self.assertRaises(ValueError):
            self.owner.prepare()
        self.assertEqual(self.device.actions, [])

    def test_existing_settings_live_task_refusal_is_not_weakened(self):
        self.cached()
        self.device.live_tasks = self.device.live_tasks.replace(b"com.google.android.apps.nexuslauncher", b"com.android.settings")
        with self.assertRaises(ValueError):
            self.owner.prepare()
        self.assertEqual(self.device.actions, [])

    def test_changed_boot_stopping_settings_activity_refuses_before_any_restoring_write(self):
        self.cached().prepare()
        self.dispatch()
        self.device.new_settings_activities = activities(extra=("  Activities waiting to stop:",
            "    * Stop #0: ActivityRecord{aa u0 com.android.settings/.Settings t2}"))
        receipt = self.close_model()
        self.assertEqual(self.device.boot, fixtures.NEW)
        self.assertFalse(receipt.get("kernel_barrier_verified", False))
        self.assertEqual(receipt["master_restore_attempts"], 0)
        self.assertFalse(camera.accepted(receipt, self.disposal()))
        self.sticky_close(receipt)

    def test_empty_activity_dump_never_substitutes_for_changed_kernel_lifetime(self):
        self.cached().prepare()
        self.dispatch()
        self.device.reboot_effect = False
        receipt = self.close_model()
        self.assertFalse(receipt.get("kernel_barrier_verified", False))
        self.assertEqual(receipt["master_restore_attempts"], 0)
        self.assertEqual(self.device.actions.count(("reboot",)), 1)
        self.assertGreaterEqual(self.clock.now, 360)
        self.assertFalse(camera.accepted(receipt, self.disposal()))
        self.sticky_close(receipt)

    def test_cached_empty_activities_do_not_waive_inconsistent_original_native_scalar_pair(self):
        self.cached(scalar=camera.Row(True, "1"), native=False)
        with self.assertRaises(ValueError):
            self.owner.prepare()
        self.assertIsNone(self.owner.original)
        self.assertEqual(self.device.actions, [])

    def test_cached_empty_activities_do_not_waive_foreign_master_before_cleanup(self):
        self.cached(camera.Row(True, "0")).prepare()
        self.dispatch()
        self.device.master = camera.Row(False, None)
        receipt = self.close_model()
        self.assertEqual((receipt["normal_reboot_attempts"], receipt["master_restore_attempts"]), (0, 0))
        self.assertFalse(camera.accepted(receipt, self.disposal()))
        self.sticky_close(receipt)

    def test_cached_empty_activities_keep_uncertain_enable_failure_and_sole_action_latches(self):
        self.cached(camera.Row(True, "0"))
        self.device.enable_timeout = True
        with self.assertRaises(TimeoutError):
            self.owner.prepare()
        receipt = self.close_model()
        self.assertEqual(receipt["prepare_status"], "failed")
        self.assertEqual((receipt["master_enable_attempts"], receipt["normal_reboot_attempts"],
                          receipt["master_restore_attempts"]), (1, 1, 1))
        self.assertTrue(receipt["master_original_restored"])
        self.assertFalse(camera.accepted(receipt, self.disposal()))
        self.sticky_close(receipt)

    def test_cached_empty_activities_keep_uncertain_reboot_failure_even_after_exact_restore(self):
        self.cached().prepare()
        self.dispatch()
        self.device.reboot_timeout = True
        receipt = self.close_model()
        self.assertTrue(receipt["kernel_barrier_verified"])
        self.assertTrue(receipt["master_original_restored"])
        self.assertEqual(receipt["cleanup_status"], "failed")
        self.assertEqual((receipt["normal_reboot_attempts"], receipt["master_restore_attempts"]), (1, 1))
        self.assertFalse(camera.accepted(receipt, self.disposal()))
        self.sticky_close(receipt)

    def test_cached_empty_activities_keep_uncertain_restore_failure_without_write_retry(self):
        self.cached(camera.Row(True, "0")).prepare()
        self.dispatch()
        self.device.restore_timeout = True
        receipt = self.close_model()
        self.assertTrue(receipt["master_original_restored"])
        self.assertEqual(receipt["cleanup_status"], "failed")
        self.assertEqual(receipt["master_restore_attempts"], 1)
        self.assertFalse(camera.accepted(receipt, self.disposal()))
        self.sticky_close(receipt)

    def test_cached_empty_activities_keep_already_enabled_master1_native1_scalar1_true_noop(self):
        self.cached(camera.Row(True, "1"), scalar=camera.Row(True, "1"), native=True).prepare()
        receipt = self.successful_close()
        self.assertEqual(self.setting_actions(), [])
        self.assertEqual((receipt["master_enable_attempts"], receipt["normal_reboot_attempts"],
                          receipt["master_restore_attempts"]), (0, 0, 0))
        self.assertNotIn(("reboot",), self.device.actions)

    def test_cached_empty_activities_do_not_green_prebarrier_native_cleanup_red_after_reboot_match(self):
        self.cached().prepare()
        self.dispatch()
        self.device.native = True
        receipt = self.close_model()
        self.assertFalse(receipt["pre_barrier_native_scalar_restored"])
        self.assertTrue(receipt["final_native_scalar_restored"])
        self.assertFalse(camera.accepted(receipt, self.disposal()))
        self.assertTrue(all(action[6] == camera.MASTER for action in self.setting_actions()))
        self.sticky_close(receipt)


class ActivityBoundarySourceGuard(NoNativeActions, unittest.TestCase):
    def test_only_new_header_reader_and_fresh_boundary_differ_in_full_helper_ast(self):
        source = ast.parse(historical_helper_source(HELPER.read_text()))
        headers = [node for node in source.body if isinstance(node, ast.Assign) and
                   any(isinstance(target, ast.Name) and target.id == "ACTIVITIES_HEADER" for target in node.targets)]
        self.assertEqual(len(headers), 1)
        self.assertEqual(ast.dump(headers[0], include_attributes=False), ast.dump(ast.parse(
            'ACTIVITIES_HEADER = "ACTIVITY MANAGER ACTIVITIES (dumpsys activity activities)"').body[0], include_attributes=False))
        source.body.remove(headers[0])
        readers = [node for node in source.body if isinstance(node, ast.FunctionDef) and node.name == "parse_settings_activity_absence"]
        self.assertEqual(len(readers), 1)
        self.assertEqual(hashlib.sha256(ast.dump(readers[0], include_attributes=False).encode()).hexdigest(), READER_AST_SHA256)
        source.body.remove(readers[0])
        owner = next(node for node in source.body if isinstance(node, ast.ClassDef) and node.name == "OwnedDeveloperPrerequisite")
        snapshot = next(node for node in owner.body if isinstance(node, ast.FunctionDef) and node.name == "snapshot")
        expected = ast.parse('if fresh:\n    parse_settings_activity_absence(self.control("shell", "dumpsys", "activity", "-p", "com.android.settings", "activities"))\n').body[0]
        branches = [node for node in snapshot.body if isinstance(node, ast.If) and
                    ast.dump(node, include_attributes=False) == ast.dump(expected, include_attributes=False)]
        self.assertEqual(len(branches), 1)
        index = snapshot.body.index(branches[0])
        snapshot.body[index] = ast.parse('require(not fresh or not settings, "Settings process/package/dependency record present in fresh epoch")').body[0]
        # This hashes the WHOLE restored helper: no native/action/boot/write or
        # cleanup method is stripped to evade an owning preservation guard.
        self.assertEqual(hashlib.sha256(ast.dump(source, include_attributes=False).encode()).hexdigest(), BASE_HELPER_AST_SHA256)

    def test_reused_fixture_base_has_no_inherited_accepted_test_methods(self):
        self.assertFalse(any(name.startswith("test_") for name in fixtures.ModelFixture.__dict__))
        self.assertEqual(ActivityBoundaryModels.__bases__, (NoNativeActions, fixtures.ModelFixture))


if __name__ == "__main__":
    unittest.main()
