# SPDX-License-Identifier: Apache-2.0
"""NEW16 synthetic live-frame/controller/source controls, zero device/native IO.

Only NEW tiny synthetic fixtures call the original pure reader once to obtain
genuine refusal frames. No original payload, parser result, accepted test method,
controller run, query, APK, Gradle or native execution is replayed.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest
from unittest.mock import patch

import android_camera_developer_prerequisite as camera
import android_camera_live_task_refusal_observation as leaf
import android_camera_recents_observation as observation
import webview_content_policy_source_projection as content_history

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = "private-synthetic-live-task-label-not-for-export"
QUERY = ["/private-synthetic-sdk/platform-tools/adb", *leaf.QUERY_ARGUMENTS]
ROOT_ROW = "RootTask id=314159 bounds=[0,0][1080,1920] displayId=0 userId=0"
CONFIG = " configuration={" + PRIVATE + "}"
KNOWN = "  taskId=314160: " + PRIVATE + " userId=0 visible=false"
MALFORMED = "  taskId=314161: " + PRIVATE + " userId=0 visible=unrecognized"
DISPATCH = ('    if error.args == ("Unknown live leaf task",):\n'
            '        from android_camera_live_task_refusal_observation import live_task_refusal\n'
            '        return live_task_refusal(error)\n')
BASE_OBSERVER_SHA256 = "0fba4e83307511dada22ed28f5ad98e9e97fb15f5fc0521af858ca954901d304"
UNCHANGED = {
    "scripts/ci/android_camera_developer_prerequisite.py": "92f8d79d3a0871f1abb619a0a17b36c87568e11151fb3dbefa4f12773de78bdb",
    "scripts/ci/android_device_tests.py": "f096609a3731628c02966b7f6edd40641d7c0ff8119d0922605f6c7e6e99d7d8",
    "scripts/ci/android_camera_home_baseline.py": "e710e5f1c7d048b0b32e00f2a261443f6dcbd24aa51ec1fc46bfbe27ab47e3b5",
    "scripts/ci/android_camera_home_refusal_observation.py": "1ad4888609d470e591d212cf5a370bc5ed900aa80c181e84d0277f6c9095287c",
}


def sha(body):
    return hashlib.sha256(body).hexdigest()


def payload(*children, root=ROOT_ROW, configuration=CONFIG):
    return ("\n".join((root, configuration, *children)) + "\n").encode()


def refused(body=None, *, args=None, code=0, stderr=b""):
    """One NEW fixture invocation, never an original/cached parser replay."""
    result = subprocess.CompletedProcess(QUERY.copy() if args is None else args, code,
                                         payload(MALFORMED) if body is None else body, stderr)
    try:
        camera.parse_live_tasks(result)
    except BaseException as error:
        return error, result
    raise AssertionError("NEW synthetic fixture must actually refuse")


def live_values(error):
    trace = error.__traceback__
    while trace is not None:
        if trace.tb_frame.f_code is camera.parse_live_tasks.__code__:
            return trace.tb_frame.f_locals
        trace = trace.tb_next
    raise AssertionError("NEW synthetic error must contain its actual reader frame")


class LiveLeafReturnedFrameControls(unittest.TestCase):
    def assert_not_admitted(self, facts):
        self.assertEqual("nativecmpkit.camera-live-leaf-refusal.v1", facts["schema"])
        self.assertIs(facts["original_require_condition"], False)
        self.assertIs(facts["original_reader_still_refused"], True)
        self.assertEqual(0, facts["new_queries_or_native_operations"])
        for key in ("parser_retried", "instruction_trace_or_atomic_freeze_verified", "live_task_absence_verified",
                    "task_ownership_verified", "installed_image_or_HOME_provenance_verified",
                    "original_scalar_or_cause_inferred", "native_acceptance_inferred", "admission_changed",
                    "raw_rows_identifiers_leaf_labels_components_affinity_paths_or_environment_exported"):
            self.assertIs(facts[key], False, key)

    def test_captured_nonmatch_refusal_preserves_primary_error_query_and_unevaluated_terms(self):
        error, result = refused()
        original_trace, original_args, original_stdout = error.__traceback__, error.args, result.stdout
        facts = observation.recents_refusal(error)
        self.assertIs(original_trace, error.__traceback__)
        self.assertEqual(original_args, error.args)
        self.assertIs(original_stdout, result.stdout)
        self.assertEqual({"child_grammar_match": False, "child_id_not_previously_seen": None,
                          "leaf_label_not_literal_unknown": None}, facts["captured_state_operand_matches"])
        self.assertEqual({"child_grammar_match": True, "child_id_not_previously_seen": False,
                          "leaf_label_not_literal_unknown": False}, facts["source_short_circuit_evaluated"])
        self.assertEqual("child_grammar_match", facts["captured_state_first_false_operand"])
        self.assertEqual({"source": "android_camera_developer_prerequisite.py", "symbol": "parse_live_tasks", "line": 349},
                         facts["require_call_origin"])
        self.assert_not_admitted(facts)

    def test_duplicate_child_id_keeps_later_leaf_predicate_unexecuted_and_does_not_export_id(self):
        duplicate = KNOWN.replace(PRIVATE, "another-" + PRIVATE)
        error, _ = refused(payload(KNOWN, duplicate))
        facts = leaf.live_task_refusal(error)
        self.assertEqual({"child_grammar_match": True, "child_id_not_previously_seen": False,
                          "leaf_label_not_literal_unknown": None}, facts["captured_state_operand_matches"])
        self.assertEqual("child_id_not_previously_seen", facts["captured_state_first_false_operand"])
        self.assertEqual(1, facts["captured_seen_child_id_count"])
        self.assertEqual(3, facts["rejected_row"]["nonempty_index"])
        self.assertNotIn("314160", json.dumps(facts))
        self.assert_not_admitted(facts)

    def test_literal_unknown_leaf_is_observed_only_after_both_prior_predicates_were_reached(self):
        unknown = "  taskId=314162: unknown userId=0 visible=false"
        error, _ = refused(payload(unknown))
        facts = leaf.live_task_refusal(error)
        self.assertEqual({"child_grammar_match": True, "child_id_not_previously_seen": True,
                          "leaf_label_not_literal_unknown": False}, facts["captured_state_operand_matches"])
        self.assertTrue(all(facts["source_short_circuit_evaluated"].values()))
        self.assertEqual("leaf_label_not_literal_unknown", facts["captured_state_first_false_operand"])
        self.assert_not_admitted(facts)

    def test_exact_original_query_return_identity_is_required_not_a_similar_foreign_command(self):
        variants = ([], tuple(QUERY), [*QUERY[:-1], "recents"], [QUERY[0], "-s", "foreign", *QUERY[3:]],
                    ["relative/platform-tools/adb", *QUERY[1:]], ["/sdk/../platform-tools/adb", *QUERY[1:]],
                    ["/sdk/platform-tools/adb\n", *QUERY[1:]], [None, *QUERY[1:]])
        for args in variants:
            with self.subTest(query_type=type(args).__name__):
                error, _ = refused(args=args)
                self.assertIsNone(leaf.live_task_refusal(error))
        for code, stderr in ((False, b""), (1, b""), (0, PRIVATE.encode())):
            error, _ = refused(code=code, stderr=stderr)
            self.assertIsNone(leaf.live_task_refusal(error))

    def test_foreign_literal_errors_wrong_guard_and_nonterminal_code_supply_no_frame_facts(self):
        for error in (ValueError(leaf.GUARD), RuntimeError(leaf.GUARD), ValueError("Different guard"),
                      ValueError(object()), ValueError(leaf.GUARD, "extra")):
            self.assertIsNone(leaf.live_task_refusal(error))
        try:
            camera.require(False, leaf.GUARD)
        except ValueError as error:
            self.assertIsNone(leaf.live_task_refusal(error))
        error, _ = refused()
        error.args = ("Changed refusal",)
        self.assertIsNone(leaf.live_task_refusal(error))
        error, _ = refused(payload(MALFORMED, root="RootTask invalid"))
        self.assertIsNone(observation.recents_refusal(error))

    def test_payload_row_block_and_captured_seen_state_changes_are_unavailable_not_new_operands(self):
        changes = (lambda values, result: values["rows"].append(PRIVATE),
                   lambda values, result: values["rows"].__setitem__(2, "\ud800"),
                   lambda values, result: values["block"].reverse(),
                   lambda values, result: values["roots"].clear(),
                   lambda values, result: values["children"].add("900001"),
                   lambda values, result: setattr(result, "stdout", payload(KNOWN)),
                   lambda values, result: setattr(result, "stderr", PRIVATE.encode()))
        for index, change in enumerate(changes):
            with self.subTest(change=index):
                error, result = refused()
                change(live_values(error), result)
                self.assertIsNone(leaf.live_task_refusal(error))

    def test_trace_row_payload_and_byte_budgets_do_not_fabricate_partial_or_zero_results(self):
        for name, limit in (("MAX_FRAMES", 0), ("MAX_ROWS", 2), ("MAX_ROW_BYTES", 8)):
            error, _ = refused()
            with patch.object(leaf, name, limit):
                self.assertIsNone(leaf.live_task_refusal(error))
        for body in (b"", payload(MALFORMED) + b"\r", payload(MALFORMED) + b"\0",
                     payload(MALFORMED) + b"\x1b", b"\xff", payload("x" * 2049),
                     payload(MALFORMED) + b"\n" * 129, payload(MALFORMED) * 1000):
            error, _ = refused(body)
            self.assertIsNone(leaf.live_task_refusal(error))

    def test_bounded_fixed_row_metrics_never_contain_sensitive_labels_ids_components_or_paths(self):
        body = payload(MALFORMED + " topActivity=ComponentInfo{" + PRIVATE + "/PrivateComponent}")
        error, _ = refused(body)
        facts = leaf.live_task_refusal(error)
        row = facts["rejected_row"]
        self.assertEqual(2, row["leading_ascii_spaces"])
        self.assertEqual(1, row["fixed_marker_counts"][" topActivity=ComponentInfo{"])
        self.assertEqual(sha(body), facts["payload_sha256"])
        self.assertLess(len(json.dumps(facts).encode()), 8192)
        exported = json.dumps(facts)
        for private in (PRIVATE, "PrivateComponent", "314159", "314161", QUERY[0], ROOT_ROW, CONFIG):
            self.assertNotIn(private, exported)
        self.assert_not_admitted(facts)

    def test_root_block_and_nonempty_coordinates_are_source_conditionals_not_task_ownership(self):
        second_root = ROOT_ROW.replace("314159", "314163")
        body = ("\n" + "\n".join((ROOT_ROW, CONFIG, KNOWN, second_root, CONFIG, "", MALFORMED)) + "\n").encode()
        error, _ = refused(body)
        facts = leaf.live_task_refusal(error)
        self.assertEqual(2, facts["root_block_count"])
        self.assertEqual(1, facts["rejected_block_index"])
        self.assertEqual(5, facts["rejected_row"]["nonempty_index"])
        self.assertEqual(1, facts["source_conditional_prior_leaf_rows"])
        self.assertEqual(3, facts["omitted_empty_rows"])
        self.assert_not_admitted(facts)
        error, _ = refused(payload(MALFORMED, MALFORMED))
        values = live_values(error)
        values["rows"][3] = values["rows"][2]
        values["block"][3] = values["block"][2]
        self.assertIsNone(leaf.live_task_refusal(error), "Ambiguous references cannot guess an iteration")

    def test_other_root_configuration_and_settings_guards_keep_their_original_refusal(self):
        settings = "  taskId=314164: com.android.settings/.PrivateSettings userId=0 visible=true"
        for body, message in ((payload(MALFORMED, configuration="foreign-config"), "Incomplete root/configuration"),
                              (payload(settings), "Settings live task remains")):
            error, result = refused(body)
            self.assertEqual((message,), error.args)
            self.assertIsNone(observation.recents_refusal(error))
            self.assertEqual(body, result.stdout)


class LiveLeafControllerHandlerControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Compile only this unchanged exception handler and metadata-origin
        # function as a NEW synthetic model. Never import/run the controller.
        path = ROOT / "scripts/ci/android_device_tests.py"
        tree = ast.parse(path.read_text())
        owner = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_run")
        handler = next(node for node in ast.walk(owner) if isinstance(node, ast.ExceptHandler) and
                       any(isinstance(child, ast.Constant) and child.value == "controller_error" for child in ast.walk(node)))
        function = ast.parse("def handle(result, error, diagnostics, camera_developer_required):\n    return result\n").body[0]
        function.body = copy.deepcopy(handler.body) + function.body
        origin = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "preflight_error_origin")
        module = ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(origin), function], type_ignores=[]))
        namespace = {"Path": Path, "re": re, "__file__": str(path)}
        exec(compile(module, str(path), "exec"), namespace)
        cls.handler = staticmethod(namespace["handle"])

    def test_actual_handler_keeps_opaque_primary_error_origin_before_optional_bound_leaf_facts(self):
        error, _ = refused()
        result = {"passed": False, "test_suite_passed": False}
        original_trace = error.__traceback__
        self.assertIs(result, self.handler(result, error, True, True))
        self.assertEqual("ValueError", result["controller_error"])
        self.assertEqual({"source": "android_camera_developer_prerequisite.py", "symbol": "require", "line": 48},
                         result["controller_error_origin"])
        self.assertEqual("nativecmpkit.camera-live-leaf-refusal.v1", result["camera_recents_refusal"]["schema"])
        self.assertLess(list(result).index("controller_error_origin"), list(result).index("camera_recents_refusal"))
        self.assertIs(original_trace, error.__traceback__)
        self.assertFalse(result["passed"])
        self.assertFalse(result["test_suite_passed"])

    def test_optional_observer_exception_preserves_primary_refusal_and_existing_cleanup_data(self):
        error, _ = refused()
        result = {"passed": False, "cleanup": {"synthetic_existing_ownership_refusal": True}}
        prior = copy.deepcopy(result)
        with patch.object(observation, "recents_refusal", side_effect=KeyboardInterrupt("private exception")):
            self.handler(result, error, True, True)
        self.assertEqual("ValueError", result["controller_error"])
        self.assertNotIn("camera_recents_refusal", result)
        self.assertEqual(prior["cleanup"], result["cleanup"])
        self.assertEqual((leaf.GUARD,), error.args)
        self.assertNotIn("private exception", json.dumps(result))

    def test_non_camera_route_unavailable_or_foreign_error_cannot_publish_new_leaf_evidence(self):
        error, _ = refused()
        result = {"passed": False}
        with patch.object(observation, "recents_refusal", side_effect=AssertionError("Wrong route")) as optional:
            self.handler(result, error, True, False)
            optional.assert_not_called()
        for foreign in (ValueError(leaf.GUARD), RuntimeError(leaf.GUARD)):
            result = {"passed": False}
            self.handler(result, foreign, True, True)
            self.assertNotIn("camera_recents_refusal", result)
            self.assertFalse(result["passed"])


class LiveLeafSourceScopeControls(unittest.TestCase):
    def test_exact_three_line_dispatch_restores_the_entire_original_observer(self):
        current = (ROOT / "scripts/ci/android_camera_recents_observation.py").read_text()
        self.assertEqual(3, len(DISPATCH.splitlines()))
        self.assertEqual(1, current.count(DISPATCH))
        self.assertEqual(BASE_OBSERVER_SHA256, sha(current.replace(DISPATCH, "", 1).encode()))
        tree = ast.parse(current)
        owner = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "recents_refusal")
        self.assertEqual('if type(error) is not ValueError:\n    return None', ast.unparse(owner.body[1]))
        self.assertLess(current.index(DISPATCH), current.index('if error.args != ("Settings recent task absence is unproved",):'))

    def test_new_helper_reads_captured_match_state_without_execution_or_parser_regex_calls(self):
        tree = ast.parse((ROOT / "scripts/ci/android_camera_live_task_refusal_observation.py").read_text())
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        forbidden = {"parse_live_tasks", "parse_recents", "require", "control", "run", "Popen", "open",
                     "read_bytes", "write_bytes", "fullmatch", "match", "search", "finditer", "chmod", "unlink"}
        self.assertFalse(any(isinstance(node.func, ast.Attribute) and node.func.attr in forbidden for node in calls))
        self.assertFalse(any(isinstance(node.func, ast.Name) and node.func.id in forbidden for node in calls))
        self.assertFalse(any(isinstance(node, ast.Import) and any(alias.name in {"os", "socket", "urllib", "time"}
                             for alias in node.names) for node in ast.walk(tree)))

    def test_dispatch_leaf_is_unlisted_by_all_existing_source_bindings_and_original_actions_are_unchanged(self):
        bindings = set()
        manifests = list((ROOT / "scripts/ci/fixtures").glob("*source-inverse.json"))
        self.assertGreater(len(manifests), 10)
        for path in manifests:
            document = json.loads(path.read_bytes())
            if type(document) is dict and type(document.get("bindings")) is dict:
                bindings.update(document["bindings"])
        self.assertNotIn("scripts/ci/android_camera_recents_observation.py", bindings)
        self.assertNotIn("scripts/ci/android_camera_live_task_refusal_observation.py", bindings)
        for name, expected in UNCHANGED.items():
            self.assertEqual(expected, sha(content_history.current_source_before_content_policy(
                name, (ROOT / name).read_bytes())), name)


if __name__ == "__main__":
    unittest.main()
