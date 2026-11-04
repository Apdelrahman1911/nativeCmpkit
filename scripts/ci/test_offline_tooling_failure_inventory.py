"""NEW synthetic controls only: no project imports or execute_scope child."""
import ast
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

import offline_tooling_failure_inventory as inventory

AFTER = Path(__file__).with_name("offline_tooling_reuse.py")
OLD_OWNER_SHA256 = "9bd6b6d8daa7d8e6270fc874c28a8b7692f815334d4d77130fb3d81c35d7897b"
OLD_FAILED_PATH = b'    if not summary["passed"]:\n        # Bounded failure tail from the same refusing execution, never a retry.\n'
NEW_FAILED_PATH = b'    if not summary["passed"]:\n        # Metadata-only inventory supplements this same output, never eligibility.\n        try:\n            from offline_tooling_failure_inventory import failure_inventory_line\n            inventory = failure_inventory_line(output)\n        except BaseException:\n            inventory = (\'[offline-failure-inventory] {"schema":"nativecmpkit-offline-failure-inventory-v1",\'\n                         \'"diagnostic_only":true,"status":"unknown",\'\n                         \'"reason_codes":["inventory-helper-unavailable"],"records":[]}\')\n        try:\n            print(inventory, file=sys.stderr)\n        except BaseException:\n            pass  # Secondary inventory I/O never replaces the known failed outcome.\n        # Bounded failure tail from the same refusing execution, never a retry.\n'


def _record(kind, method="test_case", suffix="", source="scripts/ci/test_inventory_fixture.py",
            error="AssertionError", identifier=None, display=None):
    identifier = identifier or "test_inventory_fixture.Fixture." + method
    display = display or method
    return (f"{kind}: {display} ({identifier}){suffix}\n"
            "----------------------------------------------------------------------\n"
            "Traceback (most recent call last):\n"
            f'  File "/private/local/prefix/{source}", line 42, in {method}\n'
            "    raise RuntimeError('token=PRIVATE_MESSAGE')\n"
            f"{error}: token=PRIVATE_MESSAGE\n\n")


def _output(*records, failures=1, errors=0, decoration=""):
    fields = []
    if failures:
        fields.append("failures=" + str(failures))
    if errors:
        fields.append("errors=" + str(errors))
    return ("".join(records) + "Ran 2 tests in 0.003s\n\nFAILED (" + ", ".join(fields)
            + decoration + ")\n").encode()


def _owner_sources():
    # Portable repository control: only its sibling, no external proposal files.
    after = AFTER.read_bytes()
    if after.count(NEW_FAILED_PATH) != 1:
        raise AssertionError("One exact new failed-observation span is required")
    return after.replace(NEW_FAILED_PATH, OLD_FAILED_PATH), after


def _branch_source(source):
    module = ast.parse(source)
    function = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "execute_scope")
    failed = next(node for node in function.body if isinstance(node, ast.If)
                  and ast.dump(node.test, include_attributes=False)
                  == "UnaryOp(op=Not(), operand=Subscript(value=Name(id='summary', ctx=Load()), slice=Constant(value='passed'), ctx=Load()))")
    return module, function, failed


def _branch(path):
    module = ast.parse(path.read_bytes())
    function = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "execute_scope")
    failed = next(node for node in function.body if isinstance(node, ast.If)
                  and ast.dump(node.test, include_attributes=False)
                  == "UnaryOp(op=Not(), operand=Subscript(value=Name(id='summary', ctx=Load()), slice=Constant(value='passed'), ctx=Load()))")
    return module, function, failed


def _run_failed_block(output, passed=False, stream=None):
    # Compile only the observation/tail branch, never execute_scope or its child.
    _, _, failed = _branch(AFTER)
    summary = {"passed": passed, "returncode": 9, "tests": 2, "output_sha256": "unchanged"}
    stream = io.StringIO() if stream is None else stream
    namespace = {"summary": summary, "output": output, "sys": SimpleNamespace(stderr=stream), "re": re}
    executable = ast.fix_missing_locations(ast.Module(body=[failed], type_ignores=[]))
    exec(compile(executable, "<new-failed-observation-block-only>", "exec"), namespace)
    return namespace["summary"], summary, stream


class NewFailureInventoryControls(unittest.TestCase):
    def test_complete_inventory_keeps_earliest_id_hidden_by_old_tail(self):
        first = _record("FAIL", "test_earliest")
        spacer = "\n".join("ordinary assertion diff line " + str(i) for i in range(220)) + "\n"
        output = _output(first + spacer, _record("ERROR", "test_latest", error="ValueError"), failures=1, errors=1)
        self.assertNotIn("test_earliest", "\n".join(output.decode().splitlines()[-100:]))
        result = inventory.failure_inventory(output)
        self.assertEqual("complete", result["status"])
        self.assertEqual(["test_inventory_fixture.Fixture.test_earliest", "test_inventory_fixture.Fixture.test_latest"],
                         [item["testcase_id"] for item in result["records"]])
        self.assertEqual({"FAIL": 1, "ERROR": 1}, result["declared_counts"])
        self.assertEqual({"file": "scripts/ci/test_inventory_fixture.py", "line": 42}, result["records"][0]["source"])
        self.assertEqual("AssertionError", result["records"][0]["error_class"])

    def test_subtests_omit_values_and_aggregate_parent_occurrences(self):
        output = _output(_record("FAIL", suffix=" (password='SUBTEST_PRIVATE_ONE')"),
                         _record("FAIL", suffix=" [SUBTEST_PRIVATE_MESSAGE] (token='SUBTEST_PRIVATE_TWO')"), failures=2)
        result = inventory.failure_inventory(output)
        self.assertEqual("complete", result["status"])
        self.assertEqual(1, len(result["records"]))
        self.assertEqual(2, result["records"][0]["occurrences"])
        self.assertIs(True, result["records"][0]["subtest"])
        public = inventory.failure_inventory_line(output)
        self.assertNotIn("SUBTEST_PRIVATE", public)
        self.assertNotIn("password=", public)
        self.assertNotIn("token=", public)

    def test_setup_and_loader_ids_have_safe_fixed_phases(self):
        records = [
            _record("ERROR", display="setUpClass", identifier="test_inventory_fixture.Fixture"),
            _record("ERROR", display="tearDownClass", identifier="test_inventory_fixture.Fixture"),
            _record("ERROR", display="setUpModule", identifier="test_inventory_fixture"),
            _record("ERROR", display="tearDownModule", identifier="test_inventory_fixture"),
            _record("ERROR", display="broken_module", identifier="unittest.loader._FailedTest.broken_module"),
        ]
        result = inventory.failure_inventory(_output(*records, failures=0, errors=5))
        self.assertEqual("complete", result["status"])
        self.assertEqual(["setUpClass", "tearDownClass", "setUpModule", "tearDownModule", "loader"],
                         [item["phase"] for item in result["records"]])
        self.assertEqual(5, result["header_counts"]["ERROR"])

    def test_optional_source_frames_and_error_classes_are_conservative(self):
        for source in ("scripts/ci/../../private.py", "scripts/ci/test.unsafe.py", "tests/ghp_credential/file.py"):
            with self.subTest(source=source):
                result = inventory.failure_inventory(_output(_record("FAIL", source=source)))
                self.assertIsNone(result["records"][0]["source"])
        text = _record("FAIL") + '  File "/usr/lib/python3/unittest/case.py", line 1, in assertEqual\n'
        result = inventory.failure_inventory(_output(text))
        self.assertIsNone(result["records"][0]["source"])
        ambiguous = _record("FAIL") + "ValueError: another private message\n"
        result = inventory.failure_inventory(_output(ambiguous))
        self.assertIsNone(result["records"][0]["error_class"])
        unknown = inventory.failure_inventory(_output(_record("FAIL", error="PrivateOpaqueSignal")))
        self.assertIsNone(unknown["records"][0]["error_class"])

    def test_messages_params_prefixes_and_credential_shaped_ids_never_export(self):
        output = _output(_record("FAIL", suffix=" (token='SENSITIVE_VALUE', url='https://example.invalid/?sig=PRIVATE_SIG')"))
        public = inventory.failure_inventory_line(output)
        for private in ("SENSITIVE_VALUE", "PRIVATE_MESSAGE", "PRIVATE_SIG", "private/local/prefix", "https://", "raise RuntimeError"):
            self.assertNotIn(private, public)
        token_id = "test_inventory_fixture.Fixture.test_ghp_SENSITIVE_VALUE"
        result = inventory.failure_inventory(_output(_record("FAIL", method="test_ghp_SENSITIVE_VALUE", identifier=token_id)))
        self.assertEqual("unknown", result["status"])
        self.assertNotIn("SENSITIVE_VALUE", inventory.failure_inventory_line(_output(_record("FAIL", method="test_ghp_SENSITIVE_VALUE", identifier=token_id))))

    def test_missing_mismatched_and_ambiguous_summaries_are_explicit(self):
        cases = (
            _record("FAIL").encode(),
            _output(_record("FAIL"), failures=2),
            _output(_record("FAIL")) + b"Ran 1 test in 0.001s\nFAILED (failures=1)\n",
            b"Ran 1 test in 0.001s\nFAILED (errors=1)\n",
        )
        for output in cases:
            with self.subTest(case=cases.index(output)):
                result = inventory.failure_inventory(output)
                self.assertIn(result["status"], ("partial", "unknown"))
                self.assertTrue(result["reason_codes"])

    def test_duplicate_normal_headers_are_partial_not_complete(self):
        result = inventory.failure_inventory(_output(_record("FAIL"), _record("FAIL"), failures=2))
        self.assertEqual("partial", result["status"])
        self.assertIn("duplicate-header", result["reason_codes"])
        self.assertEqual(2, result["records"][0]["occurrences"])
        self.assertEqual({"FAIL": 2, "ERROR": 0}, result["header_counts"])

    def test_malformed_ids_headers_controls_and_non_utf8_are_unknown(self):
        cases = (
            b"FAIL: password=SENSITIVE_VALUE\nRan 1 test in 0.001s\nFAILED (failures=1)\n",
            _output(_record("FAIL", identifier="https://example.invalid/?sig=SENSITIVE_VALUE")),
            _output(_record("FAIL", identifier="test_inventory_fixture.Fixture.test_mismatch")),
            _output(_record("FAIL", suffix=" (token='SENSITIVE_VALUE'\x00)")),
            b"FAIL: \xff\nRan 1 test in 0.001s\nFAILED (failures=1)\n",
        )
        for index, output in enumerate(cases):
            with self.subTest(case=index):
                result = inventory.failure_inventory(output)
                self.assertEqual("unknown", result["status"])
                self.assertNotIn("SENSITIVE_VALUE", inventory.failure_inventory_line(output))
        long_method = "test_" + "x" * inventory.MAX_ID_BYTES
        self.assertEqual("unknown", inventory.failure_inventory(_output(_record("FAIL", method=long_method)))["status"])

    def test_decorated_headers_and_summaries_never_certify_complete(self):
        ordinary = _output(_record("FAIL"))
        cases = (
            ordinary.replace(b"FAIL: test_case", b"\x1b[31mFAIL: test_case"),
            ordinary.replace(b"FAILED (", b"  FAILED ("),
            ordinary.replace(b"Ran 2", b"\x1b[33mRan 2"),
            _output(_record("FAIL"), decoration=", skipped=1"),
            _output(_record("FAIL"), decoration=", failures=1"),
        )
        for index, output in enumerate(cases):
            with self.subTest(case=index):
                self.assertIn(inventory.failure_inventory(output)["status"], ("partial", "unknown"))

    def test_record_byte_line_input_and_public_caps_are_explicit(self):
        two = _output(_record("FAIL", "test_first"), _record("ERROR", "test_second", error="ValueError"), failures=1, errors=1)
        with mock.patch.object(inventory, "MAX_RECORDS", 1):
            result = inventory.failure_inventory(two)
            self.assertEqual("partial", result["status"])
            self.assertIn("record-cap", result["reason_codes"])
            self.assertEqual(1, len(result["records"]))
        with mock.patch.object(inventory, "MAX_INPUT_BYTES", 250):
            result = inventory.failure_inventory(two)
            self.assertIn(result["status"], ("partial", "unknown"))
            self.assertIn("input-byte-cap", result["reason_codes"])
        with mock.patch.object(inventory, "MAX_LINES", 5):
            result = inventory.failure_inventory(two)
            self.assertEqual("partial", result["status"])
            self.assertIn("line-cap", result["reason_codes"])
        oversized_line = _output(_record("FAIL") + "x" * 1024 + "\n")
        with mock.patch.object(inventory, "MAX_LINE_BYTES", 512):
            result = inventory.failure_inventory(oversized_line)
            self.assertEqual("partial", result["status"])
            self.assertIn("line-byte-cap", result["reason_codes"])
        many = _output(*[_record("FAIL", "test_case_" + str(i)) for i in range(20)], failures=20)
        with mock.patch.object(inventory, "MAX_PUBLIC_BYTES", 1024):
            line = inventory.failure_inventory_line(many)
            result = json.loads(line[len(inventory.PREFIX):])
            self.assertLessEqual(len(line.encode("ascii")), 1024)
            self.assertIn("public-byte-cap", result["reason_codes"])
            self.assertIn(result["status"], ("partial", "unknown"))

    def test_line_and_inventory_are_bounded_canonical_metadata_only(self):
        output = _output(_record("FAIL"))
        first = inventory.failure_inventory_line(output)
        self.assertEqual(first, inventory.failure_inventory_line(output))
        self.assertLessEqual(len(first.encode("ascii")), inventory.MAX_PUBLIC_BYTES)
        result = json.loads(first[len(inventory.PREFIX):])
        self.assertIs(True, result["diagnostic_only"])
        self.assertIs(True, result["subtest_parameters_omitted"])
        self.assertNotIn("passed", result)
        self.assertNotIn("returncode", result)
        self.assertEqual({"kind", "testcase_id", "phase", "subtest", "occurrences", "source", "error_class"}, set(result["records"][0]))

    def test_single_fragment_keeps_all_other_owner_ast_and_tail_exact(self):
        before, after = _owner_sources()
        old, new = OLD_FAILED_PATH, NEW_FAILED_PATH
        self.assertEqual(OLD_OWNER_SHA256, hashlib.sha256(before).hexdigest())
        self.assertEqual(1, before.count(old))
        self.assertEqual(1, after.count(new))
        self.assertEqual(after, before.replace(old, new))
        self.assertEqual(before, after.replace(new, old))
        old_module, old_function, old_failed = _branch_source(before)
        new_module, new_function, new_failed = _branch_source(after)
        self.assertEqual(ast.dump(old_failed.test, include_attributes=False), ast.dump(new_failed.test, include_attributes=False))
        self.assertEqual([ast.dump(node, include_attributes=False) for node in old_failed.body],
                         [ast.dump(node, include_attributes=False) for node in new_failed.body[-len(old_failed.body):]])
        old_function.body.remove(old_failed)
        new_function.body.remove(new_failed)
        self.assertEqual(ast.dump(old_module, include_attributes=False), ast.dump(new_module, include_attributes=False))

    def test_success_branch_never_observes_or_mutates_summary(self):
        with mock.patch.object(inventory, "failure_inventory_line") as observed:
            returned, original, stream = _run_failed_block(b"private body", passed=True)
        observed.assert_not_called()
        self.assertIs(returned, original)
        self.assertEqual("", stream.getvalue())

    def test_helper_exception_keeps_original_failed_summary_and_tail(self):
        output = b"original bounded tail\npassword=TAIL_PRIVATE_VALUE\n"
        with mock.patch.object(inventory, "failure_inventory_line", side_effect=RuntimeError("token=PRIMARY_PRIVATE_VALUE")):
            returned, original, stream = _run_failed_block(output)
        self.assertIs(returned, original)
        self.assertEqual({"passed": False, "returncode": 9, "tests": 2, "output_sha256": "unchanged"}, returned)
        self.assertIn('"status":"unknown"', stream.getvalue())
        self.assertIn("original bounded tail", stream.getvalue())
        self.assertNotIn("PRIMARY_PRIVATE_VALUE", stream.getvalue())
        self.assertNotIn("TAIL_PRIVATE_VALUE", stream.getvalue())

    def test_inventory_write_exception_does_not_replace_primary_outcome(self):
        class FirstWriteRefuses(io.StringIO):
            def __init__(self):
                super().__init__()
                self.calls = 0

            def write(self, value):
                self.calls += 1
                if self.calls == 1:
                    raise RuntimeError("token=SECONDARY_PRIVATE_VALUE")
                return super().write(value)

        returned, original, stream = _run_failed_block(b"original tail still reached\n", stream=FirstWriteRefuses())
        self.assertIs(returned, original)
        self.assertIn("original tail still reached", stream.getvalue())
        self.assertNotIn("SECONDARY_PRIVATE_VALUE", stream.getvalue())

    def test_normal_failed_branch_prints_inventory_before_same_tail_once(self):
        output = _output(_record("FAIL"))
        returned, original, stream = _run_failed_block(output)
        self.assertIs(returned, original)
        actual = stream.getvalue().splitlines()
        self.assertTrue(actual[0].startswith(inventory.PREFIX))
        expected = ["[redacted diagnostic]" if re.search(r"(?i)password|secret|token|credential|authorization|PRIVATE KEY", line)
                    else line[:2000] for line in output.decode().splitlines()[-100:]]
        self.assertEqual(expected, actual[1:])
        self.assertEqual(1, sum(line.startswith(inventory.PREFIX) for line in actual))

    def test_invalid_type_has_unknown_constant_surface(self):
        for value in ("token=PRIVATE_INPUT", None, bytearray(b"password=PRIVATE_INPUT"), 7):
            with self.subTest(type=type(value).__name__):
                line = inventory.failure_inventory_line(value)
                result = json.loads(line[len(inventory.PREFIX):])
                self.assertEqual("unknown", result["status"])
                self.assertIn("invalid-input-type", result["reason_codes"])
                self.assertNotIn("PRIVATE_INPUT", line)


    def test_repository_controls_need_only_sibling_source_not_external_proposal(self):
        original_read = Path.read_bytes
        observed = []

        def sibling_only(path):
            self.assertEqual(AFTER, path)
            observed.append(path)
            return original_read(path)

        with mock.patch.object(Path, "read_bytes", sibling_only):
            before, after = _owner_sources()
        self.assertEqual([AFTER], observed)
        self.assertEqual(OLD_OWNER_SHA256, hashlib.sha256(before).hexdigest())
        self.assertEqual(after, before.replace(OLD_FAILED_PATH, NEW_FAILED_PATH))
        self.assertEqual("offline_tooling_reuse.py", AFTER.name)



if __name__ == "__main__":
    unittest.main()
