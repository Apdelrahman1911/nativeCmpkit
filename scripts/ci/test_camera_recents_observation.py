# SPDX-License-Identifier: Apache-2.0
"""Important synthetic returned-query/source controls, zero Android executions."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import android_camera_developer_prerequisite as camera
import android_camera_recents_observation as observation
import camera_boot_handoff_source_projection as boot
import camera_handoff_fixture_source_projection as fixture
import camera_recents_source_projection as history
import webview_content_policy_source_projection as content_history

ROOT = Path(__file__).resolve().parents[2]
OLD_REVISION = "dd614a75bba7dda1678f7a0cfcf97943697db92f"
PREFIX = (camera.RECENTS_HEADER + "\nmRecentsUid=1000\n"
          "mRecentsComponent=ComponentInfo{com.android.launcher3/.QuickstepService}\n"
          "mFreezeTaskListReordering=false\nmFreezeTaskListReorderingPendingTimeout=false\n").encode()
VALID = PREFIX + b"  (nothing)\n"
REFUSED = VALID + b"\n"
ARGS = ["/synthetic-sdk/platform-tools/adb", *observation.QUERY_ARGUMENTS]


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def refused(payload=REFUSED, *, args=None, stderr=b"", code=0):
    result = subprocess.CompletedProcess(ARGS.copy() if args is None else args, code, payload, stderr)
    try:
        camera.parse_recents(result)
    except BaseException as error:
        return error, result
    raise AssertionError("Synthetic precondition must actually refuse the original reader")


class CameraRecentsObservationControls(unittest.TestCase):
    def test_original_compound_refusal_stays_failed_without_input_or_trace_replacement(self):
        error, result = refused()
        trace, args, stdout = error.__traceback__, error.args, result.stdout
        facts = observation.recents_refusal(error)
        self.assertIs(error.__traceback__, trace)
        self.assertEqual(args, error.args)
        self.assertIs(stdout, result.stdout)
        self.assertEqual("parse_recents", facts["require_call_origin"]["symbol"])
        self.assertEqual(324, facts["require_call_origin"]["line"])
        self.assertEqual(7, facts["row_count"])
        self.assertEqual(2, facts["tail_rows"])
        self.assertEqual(1, facts["tail_empty_rows"])
        self.assertFalse(facts["original_operand_matches"]["exact_tail"])
        self.assertEqual(["exact_tail"], [key for key, value in facts["original_operand_matches"].items() if not value])
        self.assertEqual(0, facts["new_queries_or_native_operations"])
        self.assertTrue(facts["original_reader_still_refused"])
        for key in ("parser_retried", "recents_absence_verified", "original_scalar_or_cause_inferred",
                    "raw_rows_identifiers_paths_or_environment_exported"):
            self.assertFalse(facts[key])

    def test_uid_component_flags_and_header_operands_are_independent_booleans_not_values(self):
        variants = (
            (VALID.replace(b"mRecentsUid=1000", b"mRecentsUid=-1"), "unsigned_uid"),
            (VALID.replace(b"ComponentInfo{com.android.launcher3/.QuickstepService}", b"null"), "component_info"),
            (VALID.replace(b"mFreezeTaskListReordering=false", b"mFreezeTaskListReordering=unknown"), "freeze_flag"),
            (VALID.replace(b"mFreezeTaskListReorderingPendingTimeout=false", b"mFreezeTaskListReorderingPendingTimeout=unknown"), "pending_timeout_flag"),
            (VALID.replace(camera.RECENTS_HEADER.encode(), b"Unknown private header"), "header"),
        )
        for payload, key in variants:
            with self.subTest(key=key):
                error, _ = refused(payload)
                facts = observation.recents_refusal(error)
                self.assertFalse(facts["original_operand_matches"][key])
                self.assertTrue(facts["original_operand_matches"]["exact_tail"])
                self.assertTrue(all(type(value) is bool for value in facts["original_operand_matches"].values()))

    def test_short_and_unknown_tail_are_observed_not_normalized_or_admitted(self):
        for payload in (PREFIX.split(b"\n", 3)[0] + b"\n", PREFIX + b"  Recent tasks:\n",
                        PREFIX + b"  (nothing)\n \n", PREFIX + b"mHiddenTasks=[untrusted]\n"):
            with self.subTest(bytes=len(payload)):
                error, result = refused(payload)
                facts = observation.recents_refusal(error)
                self.assertIsNotNone(facts)
                self.assertEqual(len(payload), facts["payload_bytes"])
                self.assertEqual(sha(payload), facts["payload_sha256"])
                self.assertEqual(payload, result.stdout)
                self.assertFalse(facts["recents_absence_verified"])

    def test_fact_output_is_bounded_and_never_contains_raw_rows_tools_or_identifiers(self):
        payload = PREFIX + b"private-output-must-not-leak\n" + b"\n" * 1000
        error, _ = refused(payload)
        facts = observation.recents_refusal(error)
        self.assertLessEqual(len(facts["observed_rows"]), 8)
        self.assertLess(len(json.dumps(facts).encode()), 8192)
        exported = json.dumps(facts)
        for private in ("private-output-must-not-leak", "synthetic-sdk", "QuickstepService",
                        "com.android.launcher3", "mRecentsUid=1000", "mFreezeTaskListReordering=false"):
            self.assertNotIn(private, exported)
        self.assertEqual(1001, facts["tail_rows"])

    def test_foreign_incomplete_or_unsafe_query_identity_is_unavailable(self):
        variants = ([], tuple(ARGS), [*ARGS[:-1], "activities"], [*ARGS[:2], "foreign", *ARGS[3:]],
                    ["relative/platform-tools/adb", *ARGS[1:]], ["/sdk/../platform-tools/adb", *ARGS[1:]],
                    ["/sdk/platform-tools/adb\n", *ARGS[1:]], [None, *ARGS[1:]])
        for args in variants:
            with self.subTest(kind=type(args).__name__):
                error, _ = refused(args=args)
                self.assertIsNone(observation.recents_refusal(error))

    def test_empty_unsafe_unbounded_nonbinary_or_nonzero_results_are_not_absence(self):
        variants = ((b"", b"", 0), (REFUSED + b"\r", b"", 0), (REFUSED + b"\0", b"", 0),
                    (REFUSED + b"\x1b", b"", 0), (b"\xff", b"", 0),
                    (REFUSED * 400, b"", 0), ("not bytes", b"", 0),
                    (REFUSED, b"warning", 0), (REFUSED, b"", 1))
        for payload, stderr, code in variants:
            with self.subTest(kind=type(payload).__name__, code=code):
                error, _ = refused(payload, stderr=stderr, code=code)
                self.assertIsNone(observation.recents_refusal(error))

    def test_forged_message_origin_or_foreign_trace_never_supplies_facts(self):
        self.assertIsNone(observation.recents_refusal(ValueError("Settings recent task absence is unproved")))
        try:
            camera.require(False, "Settings recent task absence is unproved")
        except ValueError as error:
            self.assertIsNone(observation.recents_refusal(error))
        error, _ = refused()
        error.args = ("Different refusal",)
        self.assertIsNone(observation.recents_refusal(error))
        error, _ = refused()
        with patch.object(camera, "require_call_origin", return_value={"source": "foreign.py", "symbol": "parse_recents", "line": 324}):
            self.assertIsNone(observation.recents_refusal(error))

    def test_trace_rows_or_returned_payload_drift_is_unavailable_not_partial_metadata(self):
        error, _ = refused()
        trace = error.__traceback__
        while trace.tb_frame.f_code is not camera.parse_recents.__code__:
            trace = trace.tb_next
        trace.tb_frame.f_locals["rows"].append("changed after refusal")
        self.assertIsNone(observation.recents_refusal(error))
        error, result = refused()
        result.stdout = VALID
        self.assertIsNone(observation.recents_refusal(error))

    def test_exhausted_trace_budget_is_unavailable_and_observer_has_no_execution_calls(self):
        error, _ = refused()
        with patch.object(observation, "MAX_FRAMES", 0):
            self.assertIsNone(observation.recents_refusal(error))
        tree = ast.parse((ROOT / "scripts/ci/android_camera_recents_observation.py").read_text())
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        self.assertFalse(any(isinstance(node.func, ast.Attribute) and node.func.attr in
                             {"parse_recents", "control", "run", "Popen", "open", "read_bytes", "write_bytes"}
                             for node in calls))
        self.assertFalse(any(isinstance(node, ast.Import) and any(alias.name in {"os", "socket", "urllib", "time"}
                             for alias in node.names) for node in ast.walk(tree)))


class CameraRecentsSourceControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec_bytes = history.SPEC_PATH.read_bytes()
        cls.bindings = history._bindings()
        cls.current = {
            relative: content_history.current_source_before_content_policy(
                relative, (ROOT / relative).read_bytes())
            for relative in cls.bindings
        }

    def test_exact_two_paths_three_fragments_restore_prior_full_source_and_forward_roundtrip(self):
        document = json.loads(self.spec_bytes)
        self.assertEqual(OLD_REVISION, document["before_revision"])
        self.assertEqual({"scripts/ci/android_device_tests.py", "scripts/ci/camera_handoff_fixture_source_projection.py"}, set(self.bindings))
        self.assertEqual(3, sum(len(binding["fragments"]) for binding in self.bindings.values()))
        self.assertEqual(history.SPEC_SHA256, sha(self.spec_bytes))
        for relative, binding in self.bindings.items():
            after = self.current[relative]
            self.assertEqual(binding["after_sha256"], sha(after))
            before = history.current_source_before_recents_observation(relative, after)
            self.assertEqual(binding["before_sha256"], sha(before))
            forward = before
            for fragment in binding["fragments"]:
                self.assertEqual(1, forward.count(fragment["before"].encode()))
                forward = forward.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
            self.assertEqual(after, forward)
            self.assertIs(before, history.source_before_recents_observation(relative, before))

    def test_current_history_refuses_old_drift_and_tampered_fragments_without_generic_repins(self):
        for relative, after in self.current.items():
            before = history.source_before_recents_observation(relative, after)
            for payload in (before, after + b"\n", after[:-1], b"", None, bytearray(after)):
                with self.subTest(relative=relative, kind=type(payload).__name__), self.assertRaises(ValueError):
                    history.current_source_before_recents_observation(relative, payload)
            changed = copy.deepcopy(self.bindings)
            changed[relative]["fragments"][0]["after_fragment_sha256"] = "0" * 64
            with patch.object(history, "_bindings", return_value=changed), self.assertRaises(ValueError):
                history.source_before_recents_observation(relative, after)

    def test_latest_controller_composes_older_boot_and_fixture_without_native_parser_change(self):
        path = "scripts/ci/android_device_tests.py"
        current = self.current[path]
        prior = history.current_source_before_recents_observation(path, current)
        self.assertEqual(boot.current_source_before_boot_handoff(path, current),
                         boot.source_before_boot_handoff(path, prior))
        self.assertEqual(prior, fixture.current_source_before_handoff_fixture(path, current))
        self.assertEqual("525f7f43222f92ab5730d0154e817dbfc60858e21b1daaa60d5203d954535367", sha(boot.SPEC_PATH.read_bytes()))
        self.assertEqual("29da5ee28cd1aa1c1859c076895c0d62080743d2ab4bd447983dddd15684b565", sha(fixture.SPEC_PATH.read_bytes()))
        helper = (ROOT / "scripts/ci/android_camera_developer_prerequisite.py").read_bytes()
        # The owning helper is outside this new inverse: every reader, action,
        # original324/1375 callsite and cleanup body stays byte-identical.
        self.assertNotIn("scripts/ci/android_camera_developer_prerequisite.py", self.bindings)
        self.assertIn(b'rows[5:] in ([], ["  (nothing)"])', helper)
        controller = current.decode()
        self.assertEqual(1, controller.count('result["camera_recents_refusal"] = observation'))
        self.assertLess(controller.index('result["controller_error"] = type(error).__name__'),
                        controller.index('result["camera_recents_refusal"] = observation'))
        self.assertIn('except BaseException:\n                pass  # Optional returned-query facts', controller)

    def test_manifest_changes_and_nonordinary_sources_refuse(self):
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-recents-manifest-") as directory:
            root = Path(directory)
            changed = root / "changed.json"
            changed.write_bytes(self.spec_bytes + b"\n")
            link = root / "link.json"
            link.symlink_to(changed)
            for path in (changed, link):
                with patch.object(history, "SPEC_PATH", path), self.assertRaises(ValueError):
                    history._bindings()


class CameraRecentsControllerControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Compile only the actual returned-error handler and its bounded source
        # origin function. Do not run _run, a mocked device, or any prerequisites.
        path = ROOT / "scripts/ci/android_device_tests.py"
        tree = ast.parse(path.read_text())
        owner = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_run")
        handler = next(node for node in ast.walk(owner) if isinstance(node, ast.ExceptHandler) and
                       any(isinstance(child, ast.Constant) and child.value == "controller_error"
                           for child in ast.walk(node)))
        function = ast.parse("def handle(result, error, diagnostics, camera_developer_required):\n    return result\n").body[0]
        function.body = copy.deepcopy(handler.body) + function.body
        origin = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "preflight_error_origin")
        selected = ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(origin), function], type_ignores=[]))
        namespace = {"Path": Path, "re": __import__("re"), "__file__": str(path)}
        exec(compile(selected, str(path), "exec"), namespace)
        cls.handler = staticmethod(namespace["handle"])

    def test_actual_owned_exception_handler_records_facts_after_unchanged_primary_origin(self):
        error, _ = refused()
        result = {"passed": False, "test_suite_passed": False}
        returned = self.handler(result, error, True, True)
        self.assertIs(result, returned)
        self.assertEqual("ValueError", result["controller_error"])
        self.assertEqual({"source": "android_camera_developer_prerequisite.py", "symbol": "require", "line": 48},
                         result["controller_error_origin"])
        self.assertEqual("parse_recents", result["camera_recents_refusal"]["require_call_origin"]["symbol"])
        self.assertFalse(result["passed"])
        self.assertFalse(result["test_suite_passed"])

    def test_non_camera_routes_never_call_the_observer_or_add_recents_metadata(self):
        error, _ = refused()
        with patch.object(observation, "recents_refusal", side_effect=AssertionError("must not observe")) as observer:
            result = self.handler({}, error, False, False)
            observer.assert_not_called()
        self.assertEqual({"controller_error": "ValueError"}, result)

    def test_observer_exception_or_interruption_does_not_replace_the_primary_failure(self):
        for failure in (RuntimeError("synthetic observation failure"), KeyboardInterrupt()):
            with self.subTest(kind=type(failure).__name__):
                error, _ = refused()
                with patch.object(observation, "recents_refusal", side_effect=failure):
                    result = self.handler({}, error, True, True)
                self.assertEqual("ValueError", result["controller_error"])
                self.assertEqual("require", result["controller_error_origin"]["symbol"])
                self.assertNotIn("camera_recents_refusal", result)


class CameraRecentsHistoricalCompositionControls(unittest.TestCase):
    def test_only_exact_original_pre_boot_controller_is_idempotent_history_not_current(self):
        path = "scripts/ci/android_device_tests.py"
        binding = history._bindings()[path]
        prior = history.current_source_before_recents_observation(path, (ROOT / path).read_bytes())
        older = boot.source_before_boot_handoff(path, prior)
        original = boot._bindings()[path]
        self.assertEqual([original["before_sha256"]], binding["historical_composition_sha256"])
        self.assertEqual(original["before_sha256"], sha(older))
        self.assertIs(older, history.source_before_recents_observation(path, older))
        with self.assertRaises(ValueError):
            history.current_source_before_recents_observation(path, older)
        self.assertEqual(boot.source_before_boot_handoff(path, prior),
                         boot.source_before_boot_handoff(path, older))

    def test_old_image_drift_or_cross_binding_still_refuses_with_full_byte_pins(self):
        path = "scripts/ci/android_device_tests.py"
        prior = history.source_before_recents_observation(path, (ROOT / path).read_bytes())
        older = boot.source_before_boot_handoff(path, prior)
        for drift in (older + b"\n", older[:-1], b"unknown old image"):
            with self.subTest(bytes=len(drift)), self.assertRaises(ValueError):
                history.source_before_recents_observation(path, drift)
        with self.assertRaises(ValueError):
            history.source_before_recents_observation("scripts/ci/camera_handoff_fixture_source_projection.py", older)
        self.assertNotIn("historical_composition_sha256", history._bindings()["scripts/ci/camera_handoff_fixture_source_projection.py"])

    def test_current_controller_qualifies_the_actual_previously_refused_shared_endpoint(self):
        import android_external328_source_projection as external
        path = "scripts/ci/android_device_tests.py"
        current = (ROOT / path).read_bytes()
        projected = external.current_source_for_history(path, current)
        self.assertEqual(external._bindings()[path]["before_sha256"], sha(projected))
        with self.assertRaises(ValueError):
            external.current_source_for_history(path, current + b"\n")


if __name__ == "__main__":
    unittest.main()
