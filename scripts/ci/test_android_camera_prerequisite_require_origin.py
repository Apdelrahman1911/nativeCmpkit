"""New failure-origin controls only; no SDK, builds or native outcome models.

Every traceback/result below is synthetic. It cannot identify the unseen actual
016 refusing condition. Only the held owning source is imported; the controller
origin function is compiled alone with standard-library names.
"""
from __future__ import annotations

import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

TREE = Path(os.environ.get("CAMERA_REQUIRE_ORIGIN_MODEL_TREE", Path(__file__).resolve().parents[2])).resolve()
HELPER = TREE / "scripts/ci/android_camera_developer_prerequisite.py"
CONTROLLER = TREE / "scripts/ci/android_device_tests.py"
SPEC = importlib.util.spec_from_file_location("camera_prerequisite_require_origin_under_test", HELPER)
camera = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {SPEC.name: camera}):
    SPEC.loader.exec_module(camera)

SOURCE = "android_camera_developer_prerequisite.py"
MARKER = "SYNTHETIC_UNPUBLISHED_FAILURE_DATA"
UNAVAILABLE = {"source": "unavailable", "symbol": "unavailable", "line": 0}
SYNTAX = ast.parse(HELPER.read_bytes())
ORIGIN_NODE = next(node for node in ast.parse(CONTROLLER.read_bytes()).body
                   if isinstance(node, ast.FunctionDef) and node.name == "preflight_error_origin")
GENERIC = {"Path": Path, "re": camera.re, "__file__": str(CONTROLLER)}
exec(compile(ast.Module(body=[ORIGIN_NODE], type_ignores=[]), str(CONTROLLER), "exec"), GENERIC)


def forbidden(*args, **kwargs):
    raise AssertionError("No unstubbed SDK, build, process, signal or native action is admitted")


def function_node(name):
    if "." in name:
        owner, symbol = name.split(".")
        container = next(node for node in SYNTAX.body if isinstance(node, ast.ClassDef) and node.name == owner)
        return next(node for node in container.body if isinstance(node, ast.FunctionDef) and node.name == symbol)
    return next(node for node in SYNTAX.body if isinstance(node, ast.FunctionDef) and node.name == name)


def guard_line(name, index=0):
    calls = sorted((node for node in ast.walk(function_node(name)) if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name) and node.func.id == "require"), key=lambda node: node.lineno)
    return calls[index].lineno


def captured(call):
    try:
        call()
    except BaseException as error:
        return error
    raise AssertionError("The synthetic source/refusal control unexpectedly passed")


def trace_for(error, code):
    node = error.__traceback__
    while node is not None:
        if node.tb_frame.f_code is code:
            return node
        node = node.tb_next
    raise AssertionError("The synthetic traceback lacks its held source frame")


def bare_owner():
    """Only the real prepare/close failure boundaries, with all actions inert."""
    owner = object.__new__(camera.OwnedDeveloperPrerequisite)
    owner.closed = False
    owner.original = None
    owner.new_boot = None
    owner.enable_attempted = owner.enable_completed = False
    owner.reboot_attempted = owner.restore_attempted = False
    owner.receiver_prepare_attempted = False
    owner.receiver_cleanup = None
    owner.receipt = {"schema": "nativecmpkit.camera-developer-prerequisite.v1", "focus": camera.FOCUS,
                     "api_level": 35, "prepare_status": "not-started", "cleanup_status": "not-started", "errors": [],
                     "master_enable_attempts": 0, "normal_reboot_attempts": 0, "master_restore_attempts": 0,
                     "reporter_dispatch_attempted": False, "reporter_removed": False, "receiver_removed": False,
                     "raw_boot_ids_dumps_paths_or_environment_exported": False, "native_acceptance_inferred": False}
    owner.events, owner.published = [], []

    def publish():
        owner.events.append("publish")
        owner.published.append(copy.deepcopy(owner.receipt))

    owner.publish = publish
    owner.devices = owner.run = owner.control = owner.action_guard = owner.stable = forbidden
    owner.reporter = types.SimpleNamespace(freeze=forbidden, observe=forbidden,
                                          cleanup=lambda: owner.events.append("inert-reporter-cleanup"))
    return owner


def prepare_refusal(owner):
    def refuse_devices():
        try:
            camera.result_bytes(subprocess.CompletedProcess([MARKER], 1, MARKER.encode(), MARKER.encode()), 512)
        except ValueError as error:
            error.args = (MARKER,)
            owner.primary = error
            raise

    owner.devices = refuse_devices
    return captured(owner.prepare)


class CameraPrerequisiteRequireOriginTests(unittest.TestCase):
    def setUp(self):
        # The private helper's import is inert. No control can start a process.
        for module, names in ((camera.subprocess, ("Popen", "run", "check_call", "check_output")),
                              (camera.os, ("kill", "killpg"))):
            for name in names:
                guard = patch.object(module, name, forbidden)
                guard.start()
                self.addCleanup(guard.stop)

    def assert_safe(self, origin, *, symbol, line):
        self.assertEqual(origin, {"source": SOURCE, "symbol": symbol, "line": line})
        self.assertEqual(set(origin), {"source", "symbol", "line"})
        self.assertIs(type(origin["line"]), int)
        self.assertLess(len(json.dumps(origin)), 256)
        self.assertNotIn(MARKER, json.dumps(origin))
        self.assertNotIn(str(TREE), json.dumps(origin))

    def assert_unavailable(self, error):
        self.assertEqual(camera.require_call_origin(error), UNAVAILABLE)

    def assert_no_action(self, owner):
        self.assertFalse(owner.enable_attempted or owner.reboot_attempted or owner.restore_attempted)
        self.assertEqual([owner.receipt[name] for name in ("master_enable_attempts", "normal_reboot_attempts",
                                                          "master_restore_attempts")], [0, 0, 0])
        self.assertIs(owner.receipt["reporter_dispatch_attempted"], False)
        self.assertIs(owner.receipt["native_acceptance_inferred"], False)

    def test_prepare_records_direct_require_call_not_generic_origin(self):
        owner = bare_owner()
        error = prepare_refusal(owner)
        self.assertIs(type(error), ValueError)
        self.assertIs(error, owner.primary)
        self.assertEqual(error.args, (MARKER,))
        self.assertEqual(owner.receipt["prepare_status"], "failed")
        self.assertEqual(len(owner.receipt["errors"]), 1)
        entry = owner.receipt["errors"][0]
        self.assertEqual((entry["phase"], entry["class"]), ("prepare", "ValueError"))
        self.assertIn("require_call_origin", entry)
        self.assert_safe(entry["require_call_origin"], symbol="result_bytes", line=guard_line("result_bytes"))
        raise_line = function_node("require").body[0].body[0].lineno
        self.assertEqual(GENERIC["preflight_error_origin"](error),
                         {"source": SOURCE, "symbol": "require", "line": raise_line})
        self.assertEqual(owner.published[-1], owner.receipt)
        self.assertEqual(owner.events, ["publish", "publish"])
        self.assertNotIn(MARKER, json.dumps(owner.receipt))
        self.assert_no_action(owner)

    def test_two_real_same_function_guards_have_distinct_callsite_lines(self):
        good = subprocess.CompletedProcess([], 0, b"null\n", b"")
        absent = subprocess.CompletedProcess([], 0, b"No result found.\n", b"")
        wrong = subprocess.CompletedProcess([], 0, b"0\n", b"")
        errors = [captured(lambda: camera.parse_row(good, absent, "not-an-admitted-key")),
                  captured(lambda: camera.parse_row(wrong, absent, camera.MASTER))]
        origins = [camera.require_call_origin(error) for error in errors]
        for origin, index in zip(origins, (0, 1)):
            self.assert_safe(origin, symbol="parse_row", line=guard_line("parse_row", index))
        self.assertNotEqual(origins[0]["line"], origins[1]["line"])

    def test_cleanup_retains_separate_prior_failure_and_sticky_refusal(self):
        owner = bare_owner()
        prepare_refusal(owner)
        prior = copy.deepcopy(owner.receipt["errors"][0])
        receipt = owner.close()
        self.assertEqual(receipt["errors"][0], prior)
        self.assertEqual(len(receipt["errors"]), 2)
        entry = receipt["errors"][1]
        self.assertEqual((entry["phase"], entry["class"]), ("cleanup", "ValueError"))
        self.assert_safe(entry["require_call_origin"], symbol="close", line=guard_line("OwnedDeveloperPrerequisite.close", 0))
        self.assertEqual(receipt["cleanup_status"], "failed")
        self.assertTrue(owner.closed)
        self.assertEqual(owner.events.count("inert-reporter-cleanup"), 1)
        checkpoint = copy.deepcopy(owner.published)
        events = owner.events.copy()
        self.assertEqual(owner.close(), receipt)
        self.assertEqual(owner.published, checkpoint)
        self.assertEqual(owner.events, events)
        self.assert_no_action(owner)

    def test_unraised_valueerror_is_unavailable_without_exporting_message(self):
        owner = bare_owner()
        owner.failure("receiver-cleanup", ValueError(MARKER))
        self.assertEqual(owner.receipt["errors"], [{"phase": "receiver-cleanup", "class": "ValueError",
                                                  "require_call_origin": UNAVAILABLE}])
        self.assertNotIn(MARKER, json.dumps(owner.receipt))

    def test_external_lookalike_basename_is_not_an_owning_callsite(self):
        space = {"require": camera.require, "MARKER": MARKER}
        exec(compile("def pretend():\n    require(False, MARKER)\n", "/synthetic-unpublished/" + SOURCE, "exec"), space)
        self.assert_unavailable(captured(space["pretend"]))

    def test_exact_filename_spoof_is_refused_without_registered_code_identity(self):
        space = {"require": camera.require, "MARKER": MARKER}
        exec(compile("def line():\n    require(False, MARKER)\n", str(HELPER), "exec"), space)
        self.assert_unavailable(captured(space["line"]))

    def test_lookalike_require_name_and_filename_cannot_supply_the_terminal_guard(self):
        space = {"MARKER": MARKER}
        exec(compile("def require():\n    raise ValueError(MARKER)\n", str(HELPER), "exec"), space)
        self.assert_unavailable(captured(space["require"]))

    def test_non_valueerror_cannot_reuse_a_real_require_traceback(self):
        original = captured(lambda: camera.line(subprocess.CompletedProcess([], 0, b"wrong", b""), 512, rb"0"))
        substituted = RuntimeError(MARKER).with_traceback(original.__traceback__)
        self.assert_unavailable(substituted)
        self.assertIs(type(substituted), RuntimeError)
        self.assertEqual(substituted.args, (MARKER,))

    def test_valueerror_subclass_does_not_masquerade_as_the_original_guard_class(self):
        original = captured(lambda: camera.parse_properties(b"\xff"))
        self.assertIs(type(original), UnicodeDecodeError)
        self.assert_unavailable(original)

    def test_over_bound_traceback_stays_unavailable(self):
        original = captured(lambda: camera.line(subprocess.CompletedProcess([], 0, b"wrong", b""), 512, rb"0"))
        head = original.__traceback__
        frame = sys._getframe()
        for _ in range(65):
            head = types.TracebackType(head, frame, frame.f_lasti, frame.f_lineno)
        self.assert_unavailable(ValueError(MARKER).with_traceback(head))

    def test_require_without_owning_caller_or_with_later_frame_is_unavailable(self):
        original = captured(lambda: camera.line(subprocess.CompletedProcess([], 0, b"wrong", b""), 512, rb"0"))
        terminal = trace_for(original, camera.require.__code__)
        self.assert_unavailable(ValueError(MARKER).with_traceback(terminal))
        caller = trace_for(original, camera.line.__code__)
        frame = sys._getframe()
        tail = types.TracebackType(None, frame, frame.f_lasti, frame.f_lineno)
        nonterminal = types.TracebackType(tail, terminal.tb_frame, terminal.tb_lasti, terminal.tb_lineno)
        head = types.TracebackType(nonterminal, caller.tb_frame, caller.tb_lasti, caller.tb_lineno)
        self.assert_unavailable(ValueError(MARKER).with_traceback(head))

    def test_unbounded_or_non_instruction_caller_line_is_unavailable(self):
        original = captured(lambda: camera.line(subprocess.CompletedProcess([], 0, b"wrong", b""), 512, rb"0"))
        terminal = trace_for(original, camera.require.__code__)
        caller = trace_for(original, camera.line.__code__)
        for line in (0, 20000, guard_line("line") + 1000):
            with self.subTest(line=line):
                head = types.TracebackType(terminal, caller.tb_frame, caller.tb_lasti, line)
                self.assert_unavailable(ValueError(MARKER).with_traceback(head))

    def test_observer_error_cannot_replace_the_prepare_primary_valueerror(self):
        owner = bare_owner()
        with patch.object(camera, "require_call_origin", side_effect=RuntimeError(MARKER)):
            error = prepare_refusal(owner)
        self.assertIs(error, owner.primary)
        self.assertIs(type(error), ValueError)
        self.assertEqual(error.args, (MARKER,))
        self.assertEqual(owner.receipt["errors"], [{"phase": "prepare", "class": "ValueError"}])
        self.assertEqual(owner.events, ["publish", "publish"])
        self.assert_no_action(owner)

    def test_observer_interrupt_cannot_replace_an_already_recorded_primary_refusal(self):
        owner = bare_owner()
        with patch.object(camera, "require_call_origin", side_effect=KeyboardInterrupt(MARKER)):
            error = prepare_refusal(owner)
        self.assertIs(error, owner.primary)
        self.assertIs(type(error), ValueError)
        self.assertEqual(owner.receipt["errors"], [{"phase": "prepare", "class": "ValueError"}])
        self.assertEqual(owner.events, ["publish", "publish"])
        self.assert_no_action(owner)

    def test_nonrefusing_require_never_invokes_failure_only_observer(self):
        owner = bare_owner()
        before = copy.deepcopy(owner.receipt)
        with patch.object(camera, "require_call_origin", side_effect=forbidden) as observe:
            camera.require(True, MARKER)
        observe.assert_not_called()
        self.assertEqual(owner.receipt, before)
        self.assertEqual(owner.published, [])


if __name__ == "__main__":
    unittest.main()
