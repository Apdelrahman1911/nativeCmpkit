"""NEW658 lexical/model/source controls, never a producer or full owner run.

Only these NEW methods may be selected. The external frozen runner supplies exact
finite backing bytes; ordinary discovery uses only the named sibling sources.
The owner is never imported. Three actual AST functions are extracted solely to
model the existing failure-buffer hook with stubbed old secondary endpoints.
"""
import ast
import hashlib
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import offline_tooling_failure_evidence711 as progress711
import offline_tooling_failure_parent_ids658 as parent_ids

SOURCE = Path(__file__).with_name("offline_tooling_reuse.py")
BEFORE_OWNER_SHA256 = "58f08f3fcda1e490743a8d28f7881473a28f5fcd1a3127abfffce35d6e7b2cb5"
PRESERVED_SHA256 = {
    "progress711": "3bcb54e114807b6ffd4c2337367407354412312b1adecaba356ad57cdb5ccd28",
    "progress711_control": "c82a70f4890b4a7d2bddfa60ef2273dfb4a41c9005871234282363e745fed14f",
    "inventory": "2df6e8e67fe614b189b5109ddf0a9272cf140372f2236e9b985926200ce1693d",
}
OLD_HOOK = (b'        emit_scope_failure_progress(scope, output, phase=phase,\n'
            b'                                    sampled_after_refusal=sampled_after_refusal)\n')
NEW_HOOK = OLD_HOOK + (
    b'        try:\n'
    b'            from offline_tooling_failure_parent_ids658 import emit_failure_parent_ids\n'
    b'            emit_failure_parent_ids(output, scope_index=SCOPES.index(scope) + 1,\n'
    b'                                    phase=phase, sampled_after_refusal=sampled_after_refusal,\n'
    b'                                    stream=sys.stderr)\n'
    b'        except BaseException:\n'
    b'            pass\n')
SCOPES = (
    ("scripts/audit", "test_*.py"), ("scripts/migration", "test_*.py"),
    ("scripts/development", "test_*.py"), ("scripts/ci", "test_*.py"),
    ("scripts/native", "test_*.py"), ("scripts/dependencies", "test_*.py"),
    ("scripts/dependencies/yarn", "test_*.py"), ("scripts/docs", "test_*.py"),
    ("tests/consumer", "test_*.py"), ("scripts/development", "upstream_sync_tests.py"),
)
SCOPE = SCOPES[3]
EXTRACTED_FUNCTIONS = ("canonical", "digest", "emit_scope_buffer_metadata")


def backing(name):
    if "_FROZEN_BACKING" in globals():
        return _FROZEN_BACKING[name]
    if name == "owner_after":
        return SOURCE.read_bytes()
    if name == "owner_before":
        after = backing("owner_after")
        if after.count(NEW_HOOK) != 1:
            raise AssertionError("One exact owning diagnostic hook is required")
        return after.replace(NEW_HOOK, OLD_HOOK)
    paths = {"progress711": "offline_tooling_failure_evidence711.py",
             "progress711_control": "test_offline_tooling_failure_evidence711.py",
             "inventory": "offline_tooling_failure_inventory.py",
             "parent_ids": "offline_tooling_failure_parent_ids658.py"}
    return SOURCE.with_name(paths[name]).read_bytes()


def parent(method="test_case", token="FAIL", *, identifier=None, suffix=None, newline=True):
    identifier = f"fixture.Control.{method}" if identifier is None else identifier
    suffix = " " + token if suffix is None else suffix
    return (f"{method} ({identifier}) ...{suffix}" + ("\n" if newline else "")).encode("utf-8")


def public(output, **context):
    stream = io.StringIO()
    options = {"scope_index": 4, "phase": "wait-guard", "sampled_after_refusal": True}
    options.update(context)
    emitted = parent_ids.emit_failure_parent_ids(output, stream=stream, **options)
    return emitted, stream.getvalue()


def decode(raw):
    if not raw.endswith("\n") or raw.count("\n") != 1 or not raw.startswith(parent_ids.PREFIX):
        raise AssertionError("One complete prefixed JSON line is required")
    return json.loads(raw[len(parent_ids.PREFIX):])


def modeled_emitter(stream=None):
    source = backing("owner_after")
    nodes = {node.name: node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}
    selected = [nodes[name] for name in EXTRACTED_FUNCTIONS]
    stream = io.StringIO() if stream is None else stream
    endpoints = []
    namespace = {"SCOPES": SCOPES, "MAX_LOG_BYTES": 16 * 1024**2,
                 "sys": SimpleNamespace(stderr=stream), "json": json, "hashlib": hashlib,
                 "emit_scope_failure_inventory": lambda output: endpoints.append(("inventory", output)),
                 "emit_scope_failure_progress": lambda scope, output, **context:
                     endpoints.append(("progress", scope, output, context))}
    code = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
    exec(compile(code, "<frozen-actual-three-functions-hook-model658>", "exec"), namespace)
    return namespace["emit_scope_buffer_metadata"], stream, endpoints


def copied(value):
    return json.loads(json.dumps(value))


class FailureParentIds658Controls(unittest.TestCase):
    def test_exact_fail_error_terminals_only_ignore_ok_interleaved_and_unresolved(self):
        output = (parent("test_red") + parent("test_error", "ERROR") + parent("test_ok", "ok")
                  + parent("test_active", suffix="") + parent("test_note", suffix=" FAIL extra")
                  + parent("test_space", suffix="  FAIL") + parent("test_lower", "fail"))
        found = parent_ids.observe_failure_parent_ids(output)
        self.assertEqual({"FAIL": 1, "ERROR": 1}, found["observed_parent_token_counts"])
        self.assertEqual(5, found["line_omission_counts"]["non_fail_error_progress"])
        self.assertEqual(["fixture.Control.test_red", "fixture.Control.test_error"],
                         [row["parent_id"] for row in found["records"]])
        emitted, raw = public(output)
        self.assertIs(True, emitted)
        self.assertNotIn("test_note", raw)
        self.assertNotIn("test_active", raw)
        self.assertIs(True, decode(raw)["counts_are_parent_token_observations_not_tests"])

    def test_duplicate_ids_coalesce_occurrences_across_both_kinds(self):
        output = parent() + parent(token="ERROR") + parent() + parent("test_other", "ERROR")
        found = parent_ids.observe_failure_parent_ids(output)
        self.assertEqual(2, found["retained_unique_parent_ids"])
        self.assertEqual({"parent_id": "fixture.Control.test_case", "FAIL": 2, "ERROR": 1}, found["records"][0])
        self.assertEqual({"FAIL": 2, "ERROR": 2}, found["retained_parent_token_counts"])
        self.assertEqual({"FAIL": 0, "ERROR": 0}, found["omitted_parent_token_counts"])
        self.assertEqual(0, found["unique_ids_omitted_at_id_cap"])

    def test_identifier_grammar_display_leaf_match_and_ascii_boundaries_are_strict(self):
        output = (parent(identifier="fixture.Control.test_other")
                  + parent(identifier="https://private.invalid/token")
                  + parent(identifier="fixture.Control.test_é")
                  + parent(identifier="single_identifier")
                  + parent(identifier="fixture..test_case")
                  + parent(identifier="fixture.Control.9test_case"))
        found = parent_ids.observe_failure_parent_ids(output)
        self.assertEqual([], found["records"])
        self.assertEqual(6, found["line_omission_counts"]["unqualified_progress"])
        self.assertIs(True, found["limits_observed"]["unqualified_progress"])

    def test_credential_shaped_module_class_and_method_ids_are_omitted(self):
        output = (parent(identifier="fixture.github_pat_PRIVATE.test_case")
                  + parent(identifier="fixture.ghp_PRIVATE.test_case")
                  + parent(identifier="fixture.sk_PRIVATE.test_case")
                  + parent("test_ghs_PRIVATE") + parent("test_gho_PRIVATE")
                  + parent("test_ghu_PRIVATE") + parent("test_ghr_PRIVATE"))
        emitted, raw = public(output)
        self.assertIs(True, emitted)
        found = decode(raw)["inventory"]
        self.assertEqual(7, found["line_omission_counts"]["credential_shaped_id"])
        self.assertEqual([], found["records"])
        self.assertNotIn("PRIVATE", raw)
        self.assertIs(True, found["limits_observed"]["credential_shaped_id"])

    def test_ansi_indent_headers_subtests_messages_and_tracebacks_are_not_id_sources(self):
        line = parent()
        output = (b"  " + line + b"\x1b[31m" + line
                  + b"FAIL: test_case (fixture.Control.test_case)\n"
                  + b"ERROR: test_case (fixture.Control.test_case)\n"
                  + b"test_sub (fixture.Control.test_sub) (token='PRIVATE_SUB') ... FAIL\n"
                  + parent("test_message", suffix=" ERROR password=PRIVATE_MESSAGE")
                  + b"Traceback (most recent call last):\npassword=PRIVATE_TRACE\n")
        emitted, raw = public(output)
        self.assertIs(True, emitted)
        self.assertEqual([], decode(raw)["inventory"]["records"])
        for value in ("PRIVATE", "password=", "Traceback", "token=", "test_sub", "test_message"):
            self.assertNotIn(value, raw)

    def test_384_byte_ascii_id_is_qualified_and_385_byte_id_is_omitted(self):
        tail = ".Control.test_case"
        identifier = "m" * (384 - len(tail)) + tail
        found = parent_ids.observe_failure_parent_ids(parent(identifier=identifier)
                                                     + parent(identifier="m" + identifier))
        self.assertEqual(384, len(found["records"][0]["parent_id"].encode("ascii")))
        self.assertEqual(1, found["retained_unique_parent_ids"])
        self.assertEqual(1, found["line_omission_counts"]["unqualified_progress"])

    def test_empty_and_all_omitted_prefixes_emit_bounded_diagnostic_zero_observations(self):
        for output in (b"", b"PRIVATE_MESSAGE\n", parent(token="ok")):
            emitted, raw = public(output)
            self.assertIs(True, emitted)
            record = decode(raw)
            self.assertEqual({"FAIL": 0, "ERROR": 0}, record["inventory"]["observed_parent_token_counts"])
            self.assertEqual([], record["inventory"]["records"])
            self.assertIs(True, record["incomplete"])
            self.assertIs(False, record["complete_output"])
            self.assertIs(False, record["identities_authenticated"])
            self.assertIs(False, record["identities_current_or_completed_tests"])
            self.assertIs(False, record["identities_failure_causes"])
            self.assertIs(False, record["reusable_certificate"])
            self.assertNotIn("PRIVATE", raw)

    def test_nonbytes_and_unknown_context_are_silent_without_observing(self):
        for value in ("PRIVATE_STRING", bytearray(b"PRIVATE_BYTES"), memoryview(b"PRIVATE_VIEW"), None):
            with self.assertRaises(ValueError):
                parent_ids.observe_failure_parent_ids(value)
        with patch.object(parent_ids, "observe_failure_parent_ids", side_effect=AssertionError("PRIVATE_CONTEXT")) as observe:
            for context in ({"scope_index": True}, {"scope_index": 0}, {"scope_index": 11},
                            {"scope_index": "PRIVATE_INDEX"}, {"phase": "PRIVATE_PHASE"},
                            {"sampled_after_refusal": 1}):
                emitted, raw = public(parent(), **context)
                self.assertIs(False, emitted)
                self.assertEqual("", raw)
            emitted, raw = public("PRIVATE_OUTPUT")
            self.assertIs(False, emitted)
            self.assertEqual("", raw)
            emitted, raw = public(b"x" * (parent_ids.MAX_INPUT_BYTES + 2))
            self.assertIs(False, emitted)
            self.assertEqual("", raw)
            observe.assert_not_called()

    def test_input_byte_cap_counts_only_the_inspected_prefix_and_omitted_bytes(self):
        first, second = parent("test_first"), parent("test_second", "ERROR")
        with patch.object(parent_ids, "MAX_INPUT_BYTES", len(first)):
            found = parent_ids.observe_failure_parent_ids(first + second)
        self.assertEqual(len(first), found["sample_prefix_bytes"])
        self.assertEqual(len(second), found["input_bytes_omitted"])
        self.assertEqual(len(first), found["scanned_prefix_bytes"])
        self.assertEqual(0, found["prefix_bytes_uninspected"])
        self.assertEqual({"FAIL": 1, "ERROR": 0}, found["observed_parent_token_counts"])
        self.assertIs(True, found["limits_observed"]["input_byte_cap"])
        self.assertNotIn("test_second", json.dumps(found))

    def test_line_count_cap_counts_uninspected_bytes_without_scanning_more_ids(self):
        first, second = parent("test_first"), parent("test_second", "ERROR")
        with patch.object(parent_ids, "MAX_LINES", 1):
            emitted, raw = public(first + second)
        self.assertIs(True, emitted)
        found = decode(raw)["inventory"]
        self.assertEqual(1, found["scanned_lines"])
        self.assertEqual(len(first), found["scanned_prefix_bytes"])
        self.assertEqual(len(second), found["prefix_bytes_uninspected"])
        self.assertEqual(0, found["input_bytes_omitted"])
        self.assertIs(True, found["limits_observed"]["line_cap"])
        self.assertNotIn("test_second", raw)

    def test_physical_line_byte_cap_includes_the_terminator_and_omits_whole_lines(self):
        accepted = b"x" * 4095 + b"\n"
        omitted = b"x" * 4096 + b"\n"
        found = parent_ids.observe_failure_parent_ids(accepted + omitted + parent())
        self.assertEqual(3, found["scanned_lines"])
        self.assertEqual(1, found["line_omission_counts"]["line_byte_cap"])
        self.assertEqual(1, found["line_omission_counts"]["not_parent_progress"])
        self.assertEqual({"FAIL": 1, "ERROR": 0}, found["observed_parent_token_counts"])
        self.assertIs(True, found["limits_observed"]["line_byte_cap"])
        with patch.object(parent_ids, "MAX_LINE_BYTES", len(parent()) - 1):
            emitted, raw = public(parent())
        self.assertIs(True, emitted)
        self.assertEqual([], decode(raw)["inventory"]["records"])

    def test_nonutf8_and_control_lines_cannot_export_private_payloads(self):
        output = b"\xffPRIVATE_NONUTF8\n" + parent(suffix=" FAIL\x00PRIVATE_CONTROL") + parent("test_valid", "ERROR")
        emitted, raw = public(output)
        self.assertIs(True, emitted)
        found = decode(raw)["inventory"]
        self.assertEqual(1, found["line_omission_counts"]["non_utf8_line"])
        self.assertEqual(1, found["line_omission_counts"]["unqualified_progress"])
        self.assertEqual({"FAIL": 0, "ERROR": 1}, found["observed_parent_token_counts"])
        self.assertNotIn("PRIVATE", raw)
        self.assertIs(True, found["limits_observed"]["non_utf8_line"])

    def test_real_256_id_cap_keeps_later_retained_duplicates_and_exact_omitted_tokens(self):
        methods = [f"test_case_{index:03d}" for index in range(257)]
        output = b"".join(parent(method) for method in methods) + parent(methods[0], "ERROR") + parent(methods[-1], "ERROR")
        found = parent_ids.observe_failure_parent_ids(output)
        self.assertEqual(256, found["retained_unique_parent_ids"])
        self.assertEqual({"FAIL": 257, "ERROR": 2}, found["observed_parent_token_counts"])
        self.assertEqual({"FAIL": 256, "ERROR": 1}, found["retained_parent_token_counts"])
        self.assertEqual({"FAIL": 1, "ERROR": 1}, found["omitted_for_unique_id_cap"])
        self.assertEqual(found["omitted_for_unique_id_cap"], found["omitted_parent_token_counts"])
        self.assertIsNone(found["unique_ids_omitted_at_id_cap"])
        self.assertIs(True, found["limits_observed"]["unique_id_cap"])
        self.assertNotIn("fixture.Control.test_case_256", json.dumps(found))

    def test_real_256_long_ids_prune_whole_records_into_one_64k_json_with_exact_counts(self):
        lines = []
        for index in range(256):
            method = f"test_long_{index:03d}"
            tail = ".Control." + method
            identifier = "m" * (384 - len(tail)) + tail
            lines.append(parent(method, "ERROR" if index % 2 else "FAIL", identifier=identifier))
        output = b"".join(lines)
        emitted, raw = public(output)
        self.assertIs(True, emitted)
        self.assertLessEqual(len(raw.encode("ascii")), 65536)
        found = decode(raw)["inventory"]
        kept = found["retained_unique_parent_ids"]
        self.assertGreater(kept, 0)
        self.assertLess(kept, 256)
        self.assertEqual(256 - kept, found["unique_ids_omitted_for_public_byte_cap"])
        self.assertEqual({"FAIL": 128, "ERROR": 128}, found["observed_parent_token_counts"])
        self.assertEqual({"FAIL": (kept + 1) // 2, "ERROR": kept // 2}, found["retained_parent_token_counts"])
        omitted = {"FAIL": 128 - (kept + 1) // 2, "ERROR": 128 - kept // 2}
        self.assertEqual(omitted, found["omitted_for_public_byte_cap"])
        self.assertEqual(omitted, found["omitted_parent_token_counts"])
        self.assertEqual({"FAIL": 0, "ERROR": 0}, found["omitted_for_unique_id_cap"])
        self.assertEqual(0, found["unique_ids_omitted_at_id_cap"])
        self.assertIs(True, found["limits_observed"]["public_byte_cap"])
        self.assertEqual(kept, len(found["records"]))

    def test_insufficient_public_budget_is_silent_not_truncated_or_retried_json(self):
        with patch.object(parent_ids, "MAX_PUBLIC_BYTES", 1):
            emitted, raw = public(parent())
        self.assertIs(False, emitted)
        self.assertEqual("", raw)

    def test_unterminated_and_byte_capped_terminal_mimics_are_omitted_without_parent_ids(self):
        emitted, raw = public(parent() + parent("test_last", "ERROR", newline=False))
        self.assertIs(True, emitted)
        record = decode(raw)
        self.assertEqual({"FAIL": 0, "ERROR": 1}, record["inventory"]["omitted_unterminated_suffix_candidate_counts"])
        self.assertEqual({"FAIL": 1, "ERROR": 0}, record["inventory"]["observed_parent_token_counts"])
        self.assertEqual(1, record["inventory"]["line_omission_counts"]["unterminated_fail_error_progress"])
        self.assertNotIn("fixture.Control.test_last", raw)
        self.assertIs(True, record["only_newline_terminated_parent_ids_retained"])
        self.assertIs(True, record["unterminated_suffix_counts_are_omitted_unqualified_candidates"])
        self.assertIs(False, record["identities_current_or_completed_tests"])
        truncated = parent(newline=False)
        with patch.object(parent_ids, "MAX_INPUT_BYTES", len(truncated)):
            emitted, raw = public(truncated + b"\n")
        self.assertIs(True, emitted)
        record = decode(raw)
        self.assertEqual({"FAIL": 1, "ERROR": 0}, record["inventory"]["omitted_unterminated_suffix_candidate_counts"])
        self.assertEqual({"FAIL": 0, "ERROR": 0}, record["inventory"]["observed_parent_token_counts"])
        self.assertEqual([], record["inventory"]["records"])
        self.assertIs(True, record["inventory"]["limits_observed"]["unterminated_fail_error_progress"])
        self.assertEqual(1, record["inventory"]["input_bytes_omitted"])
        self.assertIs(True, record["capped"])
        self.assertIs(False, record["identities_failure_causes"])
        emitted, raw = public(parent(newline=False) + b"\r")
        self.assertIs(True, emitted)
        found = decode(raw)["inventory"]
        self.assertEqual([], found["records"])
        self.assertEqual({"FAIL": 1, "ERROR": 0}, found["omitted_unterminated_suffix_candidate_counts"])

    def test_helper_baseexceptions_are_secondary_and_never_replace_the_primary(self):
        primary = ValueError("synthetic primary")
        for secondary in (RuntimeError("PRIVATE_HELPER"), SystemExit("PRIVATE_EXIT"), KeyboardInterrupt("PRIVATE_INTERRUPT")):
            stream = io.StringIO()
            with self.assertRaises(ValueError) as caught:
                try:
                    raise primary
                finally:
                    with patch.object(parent_ids, "observe_failure_parent_ids", side_effect=secondary):
                        emitted = parent_ids.emit_failure_parent_ids(parent(), scope_index=4, phase="cleanup",
                                                                     sampled_after_refusal=True, stream=stream)
            self.assertIs(primary, caught.exception)
            self.assertIs(False, emitted)
            self.assertEqual("", stream.getvalue())

    def test_miswired_metadata_shapes_ids_counters_and_flags_are_silent(self):
        valid = parent_ids.observe_failure_parent_ids(parent())
        models = []
        def changed(edit):
            model = copied(valid)
            edit(model)
            models.append(model)
        changed(lambda model: model.update(raw_private="PRIVATE_FIELD"))
        changed(lambda model: model["records"][0].update(parent_id="https://private.invalid?token=PRIVATE_ID"))
        changed(lambda model: model["records"][0].update(FAIL=True))
        changed(lambda model: model["observed_parent_token_counts"].update(FAIL=True))
        changed(lambda model: model.update(scanned_prefix_bytes=0))
        changed(lambda model: model.update(scanned_lines=2))
        changed(lambda model: model["limits_observed"].update(credential_shaped_id=True))
        changed(lambda model: model.update(unique_ids_omitted_at_id_cap=True))
        changed(lambda model: model["limits_observed"].update(public_byte_cap=True))
        changed(lambda model: model["records"].append(copied(model["records"][0])))
        for model in models:
            with patch.object(parent_ids, "observe_failure_parent_ids", return_value=model):
                emitted, raw = public(parent())
            self.assertIs(False, emitted)
            self.assertEqual("", raw)

    def test_secondary_write_short_write_and_flush_refusals_preserve_primary_identity(self):
        primary = ValueError("synthetic primary")
        class RefusingWrite:
            def write(self, _value):
                raise RuntimeError("PRIVATE_WRITE")
            def flush(self):
                raise AssertionError("not reached")
        class ShortWrite:
            def write(self, _value):
                return 0
            def flush(self):
                raise AssertionError("not reached")
        class RefusingFlush:
            def write(self, value):
                return len(value)
            def flush(self):
                raise RuntimeError("PRIVATE_FLUSH")
        for stream in (RefusingWrite(), ShortWrite(), RefusingFlush()):
            with self.assertRaises(ValueError) as caught:
                try:
                    raise primary
                finally:
                    emitted = parent_ids.emit_failure_parent_ids(parent(), scope_index=4, phase="cleanup",
                                                                 sampled_after_refusal=True, stream=stream)
            self.assertIs(primary, caught.exception)
            self.assertIs(False, emitted)

    def test_all_finite_phases_and_scope_indexes_remain_diagnostic_context_only(self):
        expected = ("startup", "retain-child", "wait-clock", "wait-output", "wait-guard",
                    "wait-sleep", "cleanup", "post-cleanup-summary")
        self.assertEqual(expected, parent_ids.PHASES)
        for phase in expected:
            for scope_index in (1, 10):
                for sampled in (True, False):
                    emitted, raw = public(parent(), scope_index=scope_index, phase=phase, sampled_after_refusal=sampled)
                    self.assertIs(True, emitted)
                    record = decode(raw)
                    self.assertEqual((scope_index, phase, sampled),
                                     (record["scope_index"], record["phase"], record["sample_is_after_refusal"]))
                    self.assertIs(False, record["complete_output"])

    def test_extracted_hook_hands_identical_existing_buffer_to_all_three_endpoints_once(self):
        emit, stream, endpoints = modeled_emitter()
        output = parent() + b"PRIVATE_IGNORED\n"
        calls = []
        def observe(received, **context):
            calls.append((received, context))
            return False
        with patch.object(parent_ids, "emit_failure_parent_ids", side_effect=observe):
            emit(SCOPE, output, phase="wait-guard", sampled_after_refusal=True)
        self.assertEqual(["inventory", "progress"], [row[0] for row in endpoints])
        self.assertIs(output, endpoints[0][1])
        self.assertIs(output, endpoints[1][2])
        self.assertEqual(1, len(calls))
        self.assertIs(output, calls[0][0])
        self.assertEqual({"scope_index": 4, "phase": "wait-guard", "sampled_after_refusal": True, "stream": stream}, calls[0][1])
        self.assertNotIn("PRIVATE_IGNORED", stream.getvalue())
        self.assertEqual(1, stream.getvalue().count("[offline-scope-buffer] "))

    def test_extracted_hook_context_and_secondary_refusals_do_not_replace_primary(self):
        emit, stream, endpoints = modeled_emitter()
        with patch.object(parent_ids, "emit_failure_parent_ids", side_effect=AssertionError("PRIVATE_NOT_CALLED")) as hook:
            for scope, phase, sampled, output in ((list(SCOPE), "wait-guard", True, parent()),
                                                   (("PRIVATE_SCOPE", "test_*.py"), "wait-guard", True, parent()),
                                                   (SCOPE, "PRIVATE_PHASE", True, parent()),
                                                   (SCOPE, "wait-guard", 1, parent()),
                                                   (SCOPE, "wait-guard", True, "PRIVATE_OUTPUT")):
                emit(scope, output, phase=phase, sampled_after_refusal=sampled)
            hook.assert_not_called()
        self.assertEqual([], endpoints)
        self.assertEqual("", stream.getvalue())
        primary = ValueError("synthetic primary")
        with self.assertRaises(ValueError) as caught:
            try:
                raise primary
            finally:
                with patch.object(parent_ids, "emit_failure_parent_ids", side_effect=KeyboardInterrupt("PRIVATE_SECONDARY")):
                    emit(SCOPE, parent(), phase="cleanup", sampled_after_refusal=True)
        self.assertIs(primary, caught.exception)
        self.assertNotIn("PRIVATE", stream.getvalue())

    def test_exact_one_fragment_inverse_preserves_all_old_functions_and_top_level_source(self):
        before, after = backing("owner_before"), backing("owner_after")
        self.assertEqual(BEFORE_OWNER_SHA256, hashlib.sha256(before).hexdigest())
        self.assertEqual(1, before.count(OLD_HOOK))
        self.assertEqual(1, after.count(NEW_HOOK))
        self.assertEqual(after, before.replace(OLD_HOOK, NEW_HOOK))
        self.assertEqual(before, after.replace(NEW_HOOK, OLD_HOOK))
        old_tree, new_tree = ast.parse(before), ast.parse(after)
        old_nodes = {node.name: node for node in old_tree.body if isinstance(node, ast.FunctionDef)}
        new_nodes = {node.name: node for node in new_tree.body if isinstance(node, ast.FunctionDef)}
        self.assertEqual(set(old_nodes), set(new_nodes))
        changed = {name for name in old_nodes if ast.dump(old_nodes[name], include_attributes=False)
                   != ast.dump(new_nodes[name], include_attributes=False)}
        self.assertEqual({"emit_scope_buffer_metadata"}, changed)
        self.assertEqual([ast.dump(node, include_attributes=False) for node in old_tree.body if not isinstance(node, ast.FunctionDef)],
                         [ast.dump(node, include_attributes=False) for node in new_tree.body if not isinstance(node, ast.FunctionDef)])
        for name in ("execute_scope", "emit_scope_refusal", "emit_scope_event", "emit_scope_failure_progress",
                     "emit_scope_failure_inventory", "run_scopes", "scope_summary", "check", "tooling_actions",
                     "capture_source", "capture_runtime", "scope_environment", "producer_context"):
            self.assertEqual(ast.dump(old_nodes[name], include_attributes=False), ast.dump(new_nodes[name], include_attributes=False))

    def test_one_buffer_only_hook_preserves_711_endpoints_and_adds_no_reads_or_budget_change(self):
        tree = ast.parse(backing("owner_after"))
        owners = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        calls = [(name, node) for name, owner in owners.items() for node in ast.walk(owner)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                 and node.func.id == "emit_failure_parent_ids"]
        self.assertEqual(["emit_scope_buffer_metadata"], [name for name, _node in calls])
        imports = [(name, node) for name, owner in owners.items() for node in ast.walk(owner)
                   if isinstance(node, ast.ImportFrom) and node.module == "offline_tooling_failure_parent_ids658"]
        self.assertEqual(["emit_scope_buffer_metadata"], [name for name, _node in imports])
        hook_body = ast.get_source_segment(backing("owner_after").decode("utf-8"), imports[0][1])
        self.assertEqual("from offline_tooling_failure_parent_ids658 import emit_failure_parent_ids", hook_body)
        for key, expected in PRESERVED_SHA256.items():
            self.assertEqual(expected, hashlib.sha256(backing(key)).hexdigest())
        helper_tree = ast.parse(backing("parent_ids"))
        helper_imports = {alias.name for node in helper_tree.body if isinstance(node, ast.Import) for alias in node.names}
        self.assertEqual({"io", "json", "re", "offline_tooling_failure_evidence711"}, helper_imports)
        self.assertFalse(any(isinstance(node, ast.ImportFrom) for node in helper_tree.body))
        self.assertIs(progress711, parent_ids.qualified)
        self.assertEqual((16 * 1024**2, 200000, 4096, 384, 256, 65536),
                         (parent_ids.MAX_INPUT_BYTES, parent_ids.MAX_LINES, parent_ids.MAX_LINE_BYTES,
                          parent_ids.MAX_ID_BYTES, parent_ids.MAX_UNIQUE_IDS, parent_ids.MAX_PUBLIC_BYTES))
        helper_source = backing("parent_ids").decode("utf-8")
        for forbidden in ("os.", "subprocess.", "Path(", "open(", "getenv(", "observe_progress("):
            self.assertNotIn(forbidden, helper_source)
        assignments = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
                       if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                       and node.targets[0].id in {"TOTAL_SCOPE_SECONDS", "SCOPE_HEARTBEAT_SECONDS", "MAX_SCOPE_HEARTBEATS",
                                                "MAX_SCOPE_EVENT_BYTES", "MAX_FAILURE_METADATA_BYTES"}}
        self.assertEqual({"TOTAL_SCOPE_SECONDS": 1500, "SCOPE_HEARTBEAT_SECONDS": 60, "MAX_SCOPE_HEARTBEATS": 32,
                          "MAX_SCOPE_EVENT_BYTES": 4096, "MAX_FAILURE_METADATA_BYTES": 65536}, assignments)


if __name__ == "__main__":
    unittest.main()
