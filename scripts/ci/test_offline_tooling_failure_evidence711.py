"""NEW711 pure synthetic/source controls; no real scope, child, Git or network.

Qualification must select these NEW methods only. No prior accepted TestCase
methods, producer scopes, native tests or provenance acquisition are replayed.
"""
import ast
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import offline_tooling_failure_evidence711 as progress

SOURCE = Path(__file__).with_name("offline_tooling_reuse.py")
BASE_OWNER_SHA256 = "6a4c6509ce1c205f590456789c63fe99b475dc0e83242e751aef08e274fa087c"
OLD_WIRING = (b'        emit_scope_failure_inventory(output)\n'
              b'    except BaseException:\n        pass\n\n\ndef emit_scope_refusal')
NEW_WIRING = (b'        emit_scope_failure_inventory(output)\n'
              b'        emit_scope_failure_progress(scope, output, phase=phase,\n'
              b'                                    sampled_after_refusal=sampled_after_refusal)\n'
              b'    except BaseException:\n        pass\n\n\ndef emit_scope_refusal')
SCOPES = tuple((directory, "test_*.py") for directory in (
    "scripts/audit", "scripts/migration", "scripts/development", "scripts/ci",
    "scripts/native", "scripts/dependencies", "scripts/dependencies/yarn",
    "scripts/docs", "tests/consumer")) + (("scripts/development", "upstream_sync_tests.py"),)
SCOPE = SCOPES[3]
PREFIX = "[offline-scope-progress] "


def original711_source():
    # Strict exact658 data inverse; original711 assertions stay unchanged.
    # Import no scope owner, planner or restored executable.
    from macos_share_ci668_composition import source_before_failure_parent658
    return source_before_failure_parent658(
        "scripts/ci/offline_tooling_reuse.py", SOURCE.read_bytes(),
        SOURCE.resolve().parents[2])


def parent(method="test_active", token="", newline=True, suffix=None):
    suffix = (" " + token) if suffix is None else suffix
    return (f"{method} (test_fixture.Control.{method}) ...{suffix}" + ("\n" if newline else "")).encode()


def emitter(stream=None):
    # Execute only the actual secondary emitter + original pure canonical/require.
    # Do not import or execute the scope owner, planners, scopes or subprocesses.
    tree = ast.parse(original711_source())
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name in {"canonical", "require", "emit_scope_failure_progress"}]
    if len(selected) != 3:
        raise AssertionError("Actual fixed emitter and two pure helpers are required")
    stream = io.StringIO() if stream is None else stream
    namespace = {"SCOPES": SCOPES, "MAX_LOG_BYTES": 16 * 1024**2, "MAX_SCOPE_EVENT_BYTES": 4096,
                 "sys": SimpleNamespace(stderr=stream), "re": re, "json": json}
    code = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
    exec(compile(code, "<actual-secondary-progress711-functions-only>", "exec"), namespace)
    return namespace["emit_scope_failure_progress"], stream


def decode(stream):
    lines = stream.getvalue().splitlines()
    if len(lines) != 1 or not lines[0].startswith(PREFIX):
        raise AssertionError("One bounded secondary progress record is required")
    return json.loads(lines[0][len(PREFIX):])


class FailureProgress711Controls(unittest.TestCase):
    def test_unterminated_last_parent_is_lexical_not_a_current_method_or_cause(self):
        output = parent(newline=False)
        observed = progress.observe_progress(output)
        last = observed["last_qualified_parent_progress"]
        self.assertEqual("test_fixture.Control.test_active", last["testcase_id"])
        self.assertEqual("unresolved-or-interleaved", last["result_token"])
        self.assertIs(False, last["line_terminated"])
        self.assertEqual((1, 0), (last["line_number"], last["byte_offset"]))
        emit, stream = emitter()
        emit(SCOPE, output, phase="wait-guard", sampled_after_refusal=True)
        public = decode(stream)
        self.assertIs(False, public["complete_output"])
        self.assertIs(True, public["last_progress_is_not_current_test_or_failure_cause"])
        self.assertIs(True, public["sample_is_after_refusal"])
        self.assertIs(False, public["reusable_certificate"])
        self.assertNotIn("reported_tests", public)
        self.assertNotIn("time_admitted", public)
        self.assertNotIn("output_admitted", public)

    def test_terminal_tokens_count_progress_observations_not_successful_test_population(self):
        first = parent("test_first", "ok")
        output = first + parent("test_red", "FAIL") + parent("test_broken", "ERROR") + parent("test_last")
        observed = progress.observe_progress(output)
        self.assertEqual(4, observed["qualified_parent_progress_observations"])
        self.assertEqual({"ok": 1, "FAIL": 1, "ERROR": 1}, observed["terminal_token_observations"])
        self.assertEqual(1, observed["unresolved_or_interleaved_progress_observations"])
        last = observed["last_qualified_parent_progress"]
        self.assertEqual("test_fixture.Control.test_last", last["testcase_id"])
        self.assertEqual(4, last["line_number"])
        self.assertEqual(output.index(parent("test_last")), last["byte_offset"])
        emit, stream = emitter()
        emit(SCOPE, output, phase="retain-child", sampled_after_refusal=True)
        self.assertIs(True, decode(stream)["counts_are_progress_observations_not_tests"])

    def test_raw_values_signed_urls_and_subtest_parameters_are_never_exported(self):
        private = "RAW_PRIVATE_VALUE"
        subtest = f"test_sub (test_fixture.Control.test_sub) (token='{private}') ... FAIL\n".encode()
        url = f"https://storage.invalid/actions-results/blob?sig={private}&token={private}"
        output = (f"Authorization: Bearer {private}\npassword={private}\n".encode() + subtest
                  + parent(suffix=f" {url} credential={private}")
                  + parent("test_last", suffix=f" [token='{private}']"))
        observed = progress.observe_progress(output)
        public = json.dumps(observed, sort_keys=True)
        for value in (private, "https://", "Authorization", "password=", "sig=", "credential=", "token='"):
            self.assertNotIn(value, public)
        self.assertIs(True, observed["limits_observed"]["unqualified_progress"])
        self.assertEqual(2, observed["qualified_parent_progress_observations"])
        self.assertEqual(2, observed["unresolved_or_interleaved_progress_observations"])
        self.assertEqual("test_fixture.Control.test_last", observed["last_qualified_parent_progress"]["testcase_id"])

    def test_credential_shaped_malformed_and_decorated_identifiers_are_not_qualified(self):
        output = (b"test_ghp_PRIVATE (test_fixture.Control.test_ghp_PRIVATE) ... ok\n"
                  b"test_case (test_fixture.github_pat_PRIVATE.test_case) ... FAIL\n"
                  b"test_wrong (test_fixture.Control.test_other) ... ok\n"
                  b"  test_case (test_fixture.Control.test_case) ... ok\n"
                  b"\x1b[31mtest_case (test_fixture.Control.test_case) ... ok\n"
                  b"test_case (https://private.invalid/token) ... ok\n")
        observed = progress.observe_progress(output)
        self.assertIsNone(observed["last_qualified_parent_progress"])
        self.assertEqual(0, observed["qualified_parent_progress_observations"])
        self.assertIs(True, observed["limits_observed"]["credential_shaped_id"])
        self.assertIs(True, observed["limits_observed"]["unqualified_progress"])
        self.assertNotIn("PRIVATE", json.dumps(observed))

    def test_input_line_count_and_line_size_caps_are_explicit_not_a_false_full_last_test(self):
        first, second = parent("test_first", "ok"), parent("test_second", "FAIL")
        with patch.object(progress, "MAX_INPUT_BYTES", len(first)):
            observed = progress.observe_progress(first + second)
        self.assertIs(True, observed["limits_observed"]["input_byte_cap"])
        self.assertEqual(len(first), observed["parsed_prefix_bytes"])
        self.assertEqual("test_fixture.Control.test_first", observed["last_qualified_parent_progress"]["testcase_id"])
        with patch.object(progress, "MAX_LINES", 1):
            observed = progress.observe_progress(first + second)
        self.assertIs(True, observed["limits_observed"]["line_cap"])
        self.assertEqual(1, observed["qualified_parent_progress_observations"])
        with patch.object(progress, "MAX_LINE_BYTES", 8):
            observed = progress.observe_progress(first)
        self.assertIs(True, observed["limits_observed"]["line_byte_cap"])
        self.assertIsNone(observed["last_qualified_parent_progress"])
        self.assertEqual(0, observed["qualified_parent_progress_observations"])

    def test_non_utf8_control_lines_and_unknown_input_cannot_export_private_data(self):
        output = b"\xffPRIVATE_NON_UTF8\n" + parent("test_wrong", suffix=" \x00PRIVATE_CONTROL") + parent()
        observed = progress.observe_progress(output)
        self.assertIs(True, observed["limits_observed"]["non_utf8_line"])
        self.assertIs(True, observed["limits_observed"]["unqualified_progress"])
        self.assertEqual(3, observed["last_qualified_parent_progress"]["line_number"])
        self.assertNotIn("PRIVATE", json.dumps(observed))
        with self.assertRaises(ValueError):
            progress.observe_progress("PRIVATE_NON_BYTE_INPUT")

    def test_unknown_helper_and_secondary_io_refusals_cannot_replace_the_primary(self):
        emit, stream = emitter()
        with patch.object(progress, "observe_progress", side_effect=RuntimeError("token=PRIVATE_HELPER")):
            emit(SCOPE, parent(), phase="cleanup", sampled_after_refusal=True)
        public = decode(stream)
        self.assertIs(False, public["progress_observation_available"])
        self.assertIsNone(public["progress"])
        self.assertNotIn("PRIVATE_HELPER", stream.getvalue())
        primary = ValueError("original primary")
        class RefusingStream:
            def write(self, _data):
                raise RuntimeError("token=PRIVATE_IO")
            def flush(self):
                raise RuntimeError("token=PRIVATE_IO")
        emit, _stream = emitter(RefusingStream())
        with self.assertRaises(ValueError) as caught:
            try:
                raise primary
            finally:
                emit(SCOPE, parent(), phase="wait-guard", sampled_after_refusal=True)
        self.assertIs(primary, caught.exception)

    def test_unknown_context_or_miswired_private_metadata_is_silent_or_fixed_unknown(self):
        emit, stream = emitter()
        with patch.object(progress, "observe_progress", side_effect=AssertionError("must not observe unknown context")) as observe:
            for scope, phase, sampled, output in (
                (("token=PRIVATE_SCOPE", "test_*.py"), "wait-guard", True, parent()),
                (list(SCOPE), "wait-guard", True, parent()),
                (SCOPE, "token=PRIVATE_PHASE", True, parent()),
                (SCOPE, "wait-guard", "PRIVATE_BOOL", parent()),
                (SCOPE, "wait-guard", True, "PRIVATE_NON_BYTES"),
            ):
                emit(scope, output, phase=phase, sampled_after_refusal=sampled)
            observe.assert_not_called()
        self.assertEqual("", stream.getvalue())
        valid = progress.observe_progress(parent())
        models = []
        model = json.loads(json.dumps(valid)); model["raw_private"] = "PRIVATE_FIELD"; models.append(model)
        model = json.loads(json.dumps(valid)); model["last_qualified_parent_progress"]["testcase_id"] = "https://private.invalid?token=PRIVATE_ID"; models.append(model)
        model = json.loads(json.dumps(valid)); model["last_qualified_parent_progress"]["result_token"] = "PRIVATE_STATUS"; models.append(model)
        model = json.loads(json.dumps(valid)); model["qualified_parent_progress_observations"] = True; models.append(model)
        for model in models:
            emit, stream = emitter()
            with patch.object(progress, "observe_progress", return_value=model):
                emit(SCOPE, parent(), phase="wait-guard", sampled_after_refusal=True)
            public = decode(stream)
            self.assertIsNone(public["progress"])
            self.assertNotIn("PRIVATE", stream.getvalue())
            self.assertLessEqual(len(stream.getvalue().encode("ascii")), 4097)

    def test_exact_two_fragment_delta_preserves_primary_cleanup_eligibility_and_all_other_source(self):
        after = original711_source()
        self.assertEqual(1, after.count(NEW_WIRING))
        without_wiring = after.replace(NEW_WIRING, OLD_WIRING)
        start = without_wiring.index(b"def emit_scope_failure_progress(")
        end = without_wiring.index(b"def emit_scope_buffer_metadata(", start)
        before = without_wiring[:start] + without_wiring[end:]
        self.assertEqual(BASE_OWNER_SHA256, hashlib.sha256(before).hexdigest())
        old_nodes = {node.name: node for node in ast.parse(before).body if isinstance(node, ast.FunctionDef)}
        new_nodes = {node.name: node for node in ast.parse(after).body if isinstance(node, ast.FunctionDef)}
        changed = {name for name in old_nodes if ast.dump(old_nodes[name], include_attributes=False)
                   != ast.dump(new_nodes[name], include_attributes=False)}
        self.assertEqual({"emit_scope_buffer_metadata"}, changed)
        self.assertEqual({"emit_scope_failure_progress"}, set(new_nodes) - set(old_nodes))
        for name in ("execute_scope", "run_scopes", "scope_summary", "check", "tooling_actions",
                     "capture_source", "capture_runtime", "scope_environment", "producer_context"):
            self.assertEqual(ast.dump(old_nodes[name], include_attributes=False), ast.dump(new_nodes[name], include_attributes=False))

    def test_only_failure_buffer_wiring_keeps_inventory_first_and_adds_no_heartbeat_or_child_read(self):
        tree = ast.parse(original711_source())
        owners = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        calls = [(name, node) for name, owner in owners.items() for node in ast.walk(owner)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                 and node.func.id == "emit_scope_failure_progress"]
        self.assertEqual(["emit_scope_buffer_metadata"], [name for name, _node in calls])
        body = owners["emit_scope_buffer_metadata"].body[1].body
        names = [node.value.func.id for node in body if isinstance(node, ast.Expr)
                 and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)]
        self.assertEqual(["emit_scope_failure_inventory", "emit_scope_failure_progress"], names[-2:])
        emitter_source = ast.get_source_segment(original711_source().decode(), owners["emit_scope_failure_progress"])
        for forbidden in ("os.pread", "os.fstat", "time.", "subprocess", "log.", "open(", "heartbeat_count"):
            self.assertNotIn(forbidden, emitter_source)
        helper_tree = ast.parse(Path(progress.__file__).read_bytes())
        imports = {alias.name for node in helper_tree.body if isinstance(node, ast.Import) for alias in node.names}
        self.assertEqual({"io", "re"}, imports)
        self.assertFalse(any(isinstance(node, ast.ImportFrom) for node in helper_tree.body))
        self.assertEqual((16 * 1024**2, 200000, 4096, 384),
                         (progress.MAX_INPUT_BYTES, progress.MAX_LINES, progress.MAX_LINE_BYTES, progress.MAX_ID_BYTES))


if __name__ == "__main__":
    unittest.main()
