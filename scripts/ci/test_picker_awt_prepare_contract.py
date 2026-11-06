"""NEW8 source controls for passive preparation-postcondition diagnostics.

Synthetic in-memory traces only. No Gradle/native/consumer acceptance and no
replay of previously accepted failed-PREPARE diagnostic test populations.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import unittest
from unittest import mock

import picker_awt_generation as target
import picker_awt_prepare_failure as diagnostic

D1_EXPECTED_SOURCES = {'.github/workflows/picker-awt-preparation.yml': {'bytes': 1839,
                                                  'sha256': '236205c4b61b1f36fd86f81eb5f11b037bc3187b714f3ef2806aed8e58e78344'},
 'scripts/ci/library_tests.py': {'bytes': 412990,
                                 'sha256': '6fdc0947617c41b199f13e63b13056de6c76bb215698e259109c324f219c2127'},
 'scripts/ci/picker_awt_generation.py': {'bytes': 42048,
                                         'sha256': '11c843b65a6f534721e092c564cc7000d279ddd4e9c9c597d08d3041e43865ef'},
 'scripts/ci/picker_awt_preparation.py': {'bytes': 9612,
                                          'sha256': 'ef1da77624d63437041e93cc2e57f52bc2a3dc96ca3e17a73eb634f7828b1818'},
 'scripts/ci/picker_awt_prepare_failure.py': {'bytes': 29263,
                                              'sha256': '1ac0d39cf07310d5ee9ef8c0b93777baccb9f914c6b6a893e5731b5c7b4190d6'},
 'scripts/ci/picker_jni_actual_jvm2.py': {'bytes': 28352,
                                          'sha256': 'dba05feb854eddc09babf1da6b2038094c330928e22f9752795ddeeca4ff4f8b'}}
# Accepted D1/D2 pins remain literal; each uses the same six owning sources.
D2_EXPECTED_SOURCES = {'.github/workflows/picker-awt-preparation.yml': {'bytes': 1839,
                                                  'sha256': '236205c4b61b1f36fd86f81eb5f11b037bc3187b714f3ef2806aed8e58e78344'},
 'scripts/ci/library_tests.py': {'bytes': 412990,
                                 'sha256': '6fdc0947617c41b199f13e63b13056de6c76bb215698e259109c324f219c2127'},
 'scripts/ci/picker_awt_generation.py': {'bytes': 42398,
                                         'sha256': 'ca3e8bfd82ef4a2ba021a70c3949209c80bab0cffdb44855dd8438247145c797'},
 'scripts/ci/picker_awt_preparation.py': {'bytes': 9612,
                                          'sha256': 'ef1da77624d63437041e93cc2e57f52bc2a3dc96ca3e17a73eb634f7828b1818'},
 'scripts/ci/picker_awt_prepare_failure.py': {'bytes': 31104,
                                              'sha256': '78ecc9f06f385c36210799e180f0b62a55e3e9dd48b76d0a99815076d02e0e80'},
 'scripts/ci/picker_jni_actual_jvm2.py': {'bytes': 28352,
                                          'sha256': 'dba05feb854eddc09babf1da6b2038094c330928e22f9752795ddeeca4ff4f8b'}}
# D3 is only an additive diagnostic owner; no historical pin is rewritten.
EXPECTED_SOURCES = {**D2_EXPECTED_SOURCES,
    "scripts/ci/picker_awt_prepare_failure.py": {"bytes": 36874,
        "sha256": "543af524c43acfb0f25ad3ed6236767dd14c869ba9b6eb5832180e889f429bae"}}
EXPECTED_PREDICATE_AST = "BoolOp(op=Or(), values=[Call(func=Name(id='any', ctx=Load()), args=[GeneratorExp(elt=Compare(left=Call(func=Name(id='len', ctx=Load()), args=[Call(func=Attribute(value=Name(id='re', ctx=Load()), attr='findall', ctx=Load()), args=[BinOp(left=BinOp(left=Constant(value='(?m)^> Task '), op=Add(), right=Call(func=Attribute(value=Name(id='re', ctx=Load()), attr='escape', ctx=Load()), args=[Name(id='task', ctx=Load())], keywords=[])), op=Add(), right=Constant(value='$')), Name(id='body', ctx=Load())], keywords=[])], keywords=[]), ops=[NotEq()], comparators=[Constant(value=1)]), generators=[comprehension(target=Name(id='task', ctx=Store()), iter=Name(id='tasks', ctx=Load()), ifs=[], is_async=0)])], keywords=[]), Compare(left=Call(func=Name(id='len', ctx=Load()), args=[Call(func=Attribute(value=Name(id='re', ctx=Load()), attr='findall', ctx=Load()), args=[Constant(value='(?m)^BUILD SUCCESSFUL in .+$'), Name(id='body', ctx=Load())], keywords=[])], keywords=[]), ops=[NotEq()], comparators=[Constant(value=1)]), Call(func=Attribute(value=Name(id='re', ctx=Load()), attr='search', ctx=Load()), args=[Constant(value='(?m)^> Task \\\\S*(?:desktopTest|connectedAndroidDeviceTest|Test)(?:\\\\s|$)|BUILD FAILED'), Name(id='body', ctx=Load())], keywords=[])])"
UNCHANGED_GENERATION_FUNCTION_SHA256 = {'_jvm_properties': 'd69f4d1def1412b6bc5b99bec407eab0aa894733ff381f768afabdb3073816d8',
 'exact_command': 'e4b7a23fb536cdc8998d26086df9c1c697fe235127381aee6af060c98a6056a7',
 'phase': '783bcc0919b1f3891653186dd4fa7750e6457c2efbdab8f54b6ffcf94f275311',
 'prepare_command': 'dc677340a98243beeecbea4b8e1a98347d1fec5983154212ca1d416e922d6917',
 'prepare_failure_diagnostic': '6ea428b36f7f19352221d4fa1feb1f2f65594c266629189611caecd861adc3d4'}
STAT_FIELDS = ("st_dev", "st_ino", "st_mode", "st_nlink", "st_uid", "st_gid", "st_size",
               "st_atime_ns", "st_mtime_ns", "st_ctime_ns")
TASKS = {
    "host_native_build": ":calf-file-picker:buildNativeLib",
    "desktop_resources": ":calf-file-picker:desktopProcessResources",
    "runtime_classpath": ":calf-file-picker:writeNativeTestRuntimeClasspath",
    "native_resources": ":calf-file-picker:verifyNativeResources",
}
GOOD = "".join("> Task " + task + "\n" for task in TASKS.values()) + "BUILD SUCCESSFUL in 1s\n"
REASON = "standard-fresh-host-preparation-task-or-zero-test-contract-refused"
PRIVATE_SENTINEL = "DO_NOT_EXPORT_contract_private_operand"


class NativePreparationContractDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Once per NEW cohort: only six finite artifact-bound owning sources.
        root = Path(__file__).resolve().parents[2]
        cls.sources = {}
        for relative, expected in EXPECTED_SOURCES.items():
            fd = os.open(root / relative, os.O_RDONLY | os.O_NOATIME | os.O_NOFOLLOW)
            try:
                before = os.fstat(fd)
                if not stat.S_ISREG(before.st_mode) or before.st_size != expected["bytes"]:
                    raise AssertionError("named-owning-source-shape-refused")
                parts, remaining = [], expected["bytes"]
                while remaining:
                    chunk = os.read(fd, min(65536, remaining))
                    if not chunk:
                        raise AssertionError("named-owning-source-early-EOF-refused")
                    parts.append(chunk)
                    remaining -= len(chunk)
                if os.read(fd, 1):
                    raise AssertionError("named-owning-source-extra-EOF-refused")
                after = os.fstat(fd)
                if tuple(getattr(before, key) for key in STAT_FIELDS) != tuple(getattr(after, key) for key in STAT_FIELDS):
                    raise AssertionError("named-owning-source-full10-refused")
                data = b"".join(parts)
                if hashlib.sha256(data).hexdigest() != expected["sha256"]:
                    raise AssertionError("named-owning-source-SHA256-refused")
                cls.sources[relative] = data.decode("utf-8")
            finally:
                os.close(fd)

    def setUp(self):
        self.guards = []
        for owner, name in ((target.shared, "owned_phase"), (target.shared.subprocess, "Popen"),
                            (target.library, "execute"), (target.shared, "read_private_log")):
            patcher = mock.patch.object(owner, name, side_effect=AssertionError("source-control-native-or-private-request-refused"))
            guard = patcher.start()
            self.addCleanup(patcher.stop)
            self.guards.append(guard)

    def tearDown(self):
        for guard in self.guards:
            guard.assert_not_called()

    def refused(self, body, receipt=None):
        receipt = {} if receipt is None else receipt
        with self.assertRaises(target.Refusal) as caught:
            target.review_prepare(body, receipt)
        self.assertEqual(str(caught.exception), REASON)
        return receipt.get("prepare_contract_diagnostic")

    def unavailable(self, value, code):
        self.assertEqual(value, diagnostic.prepare_contract_unavailable(code))
        self.assertFalse(value["cause_established"])
        self.assertLessEqual(len(json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii")), 4096)

    def test_new01_literal_predicate_native_commands_and_two_callsites_hold(self):
        source = self.sources["scripts/ci/picker_awt_generation.py"]
        tree = ast.parse(source)
        review = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "review_prepare")
        predicate = next(node.test for node in review.body if isinstance(node, ast.If))
        self.assertEqual(ast.dump(predicate, include_attributes=False), EXPECTED_PREDICATE_AST)
        for name, expected in UNCHANGED_GENERATION_FUNCTION_SHA256.items():
            node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
            self.assertEqual(hashlib.sha256(ast.get_source_segment(source, node).encode()).hexdigest(), expected)
        for relative, qualified in (("scripts/ci/picker_awt_generation.py", "review_prepare"),
                                    ("scripts/ci/picker_awt_preparation.py", "r.review_prepare")):
            parsed = ast.parse(self.sources[relative])
            calls = [node for node in ast.walk(parsed) if isinstance(node, ast.Call) and ast.unparse(node.func) == qualified]
            self.assertEqual(len(calls), 1)
            self.assertEqual([ast.unparse(arg) for arg in calls[0].args], ["prepared", "receipt"])
        self.assertEqual((diagnostic.MAX_PRIVATE_BYTES, diagnostic.MAX_PUBLIC_BYTES, diagnostic.MAX_LINES,
                          diagnostic.MAX_LINE_BYTES, target.shared.NATIVE_BUDGET_SECONDS), (65536, 4096, 4096, 4096, 600))
        self.assertEqual(diagnostic.PREPARE_CONTRACT_TASK_IDS, tuple(TASKS))
        self.assertEqual({key: diagnostic.TASKS[key] for key in TASKS}, TASKS)

    def test_new02_success_one_argument_and_original_extra_annotation_compatibility(self):
        expected = {"required_resource_tasks": list(TASKS.values())[1:], "host_native_build_task_returned": True,
                    "executed_tests": 0}
        self.assertEqual(target.review_prepare(GOOD), expected)
        receipt = {"held": True}
        self.assertEqual(target.review_prepare(GOOD, receipt), expected)
        self.assertEqual(receipt, {"held": True})
        # Original regex accepts one exact line plus an extra annotated line.
        # Passive diagnostics must not add a new success requirement here.
        self.assertEqual(target.review_prepare(GOOD + "> Task " + TASKS["host_native_build"] + " UP-TO-DATE\n", receipt), expected)
        self.assertEqual(receipt, {"held": True})
        with mock.patch.object(diagnostic, "observe_prepare_contract") as observer:
            with self.assertRaises(target.Refusal) as caught:
                target.review_prepare(GOOD.replace("> Task " + TASKS["host_native_build"] + "\n", ""))
            self.assertEqual(str(caught.exception), REASON)
            observer.assert_not_called()

    def test_new03_each_missing_duplicate_and_annotated_task_stays_refused(self):
        suffixes = {" UP-TO-DATE": "up_to_date_line", " FROM-CACHE": "from_cache_line", " NO-SOURCE": "no_source_line",
                    " SKIPPED": "skipped_line", " FAILED": "failed_line", " " + PRIVATE_SENTINEL: "unrecognized",
                    "\tUP-TO-DATE": "unrecognized"}
        for key, task in TASKS.items():
            line = "> Task " + task + "\n"
            with self.subTest(task_id=key, case="absent"):
                value = self.refused(GOOD.replace(line, ""))
                self.assertEqual(value["task_exact_line_counts"][key], "absent")
                self.assertEqual(value["task_banner_states"][key], "unobserved")
            with self.subTest(task_id=key, case="duplicate"):
                value = self.refused(GOOD + line)
                self.assertEqual(value["task_exact_line_counts"][key], "multiple")
                self.assertEqual(value["task_banner_states"][key], "multiple")
            for suffix, state in suffixes.items():
                with self.subTest(task_id=key, case=state):
                    value = self.refused(GOOD.replace(line, "> Task " + task + suffix + "\n"))
                    self.assertEqual(value["status"], "observed")
                    self.assertEqual(value["task_exact_line_counts"][key], "absent")
                    self.assertEqual(value["task_banner_states"][key], state)
                    self.assertEqual(value["successful_footer_count"], "one")
                    self.assertFalse(value["forbidden_test_task_banner_observed"])
                    self.assertFalse(value["build_failed_text_observed"])
                    self.assertFalse(value["cause_established"])
                    self.assertNotIn(PRIVATE_SENTINEL, json.dumps(value))
            with self.subTest(task_id=key, case="different_prefix_task"):
                value = self.refused(GOOD.replace(line, "> Task " + task + "Unrelated UP-TO-DATE\n"))
                self.assertEqual(value["task_banner_states"][key], "unobserved")

    def test_new04_footer_test_and_unanchored_failed_operands_stay_refused(self):
        for body, count in ((GOOD.replace("BUILD SUCCESSFUL in 1s\n", ""), "absent"),
                            (GOOD + "BUILD SUCCESSFUL in 2s\n", "multiple")):
            with self.subTest(footer_count=count):
                value = self.refused(body)
                self.assertEqual(value["successful_footer_count"], count)
                self.assertFalse(value["forbidden_test_task_banner_observed"])
                self.assertFalse(value["build_failed_text_observed"])
        for name in ("desktopTest", "connectedAndroidDeviceTest", "customTest"):
            with self.subTest(forbidden_task=name):
                value = self.refused(GOOD + "> Task :calf-file-picker:" + name + " NO-SOURCE\n")
                self.assertTrue(value["forbidden_test_task_banner_observed"])
                self.assertFalse(value["build_failed_text_observed"])
        value = self.refused(GOOD + "wrapper operand: BUILD FAILED text\n")
        self.assertTrue(value["build_failed_text_observed"])
        self.assertFalse(value["forbidden_test_task_banner_observed"])

    def test_new05_private_utf8_line_input_public_caps_and_privacy(self):
        for body, code in ((None, "classifier_error"), (b"trace", "classifier_error"), (True, "classifier_error"),
                           ("\ud800", "UTF8_refused"), ("p" * 65537, "diagnostic_limit"),
                           ("p" * 4097, "diagnostic_limit"), ("\n" * 4097, "diagnostic_limit"),
                           (GOOD + "\x01", "diagnostic_limit")):
            with self.subTest(unavailable_code=code):
                self.unavailable(diagnostic.observe_prepare_contract(body), code)
        boundary = ("p" * 1023 + "\n") * 64
        self.assertEqual(len(boundary.encode()), 65536)
        self.assertEqual(diagnostic.observe_prepare_contract(boundary)["status"], "observed")
        body = GOOD.replace("> Task " + TASKS["desktop_resources"] + "\n", "") + "/owned/private/" + PRIVATE_SENTINEL + " token=not-a-real-secret\n"
        value = self.refused(body)
        encoded = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        self.assertNotIn(PRIVATE_SENTINEL.encode(), encoded)
        self.assertNotIn(b"/owned/private/", encoded)
        self.assertNotIn(b"not-a-real-secret", encoded)
        self.assertLessEqual(len(encoded), 4096)
        self.unavailable(self.refused(GOOD.replace("> Task " + TASKS["desktop_resources"] + "\n", "") + "p" * 65537), "diagnostic_limit")
        with mock.patch.object(diagnostic, "MAX_PUBLIC_BYTES", 1):
            self.unavailable(self.refused(GOOD.replace("> Task " + TASKS["desktop_resources"] + "\n", "")), "diagnostic_limit")

    def test_new06_fixed_schema_blocks_untrusted_keys_values_and_false_causes(self):
        observed = diagnostic.observe_prepare_contract(GOOD)
        bad_values = []
        value = copy.deepcopy(observed); value[PRIVATE_SENTINEL] = PRIVATE_SENTINEL; bad_values.append(value)
        for name, value_to_set in (("schema_version", True), ("cause_established", True), ("status", PRIVATE_SENTINEL),
                                   ("unavailable_code", PRIVATE_SENTINEL), ("successful_footer_count", PRIVATE_SENTINEL),
                                   ("forbidden_test_task_banner_observed", PRIVATE_SENTINEL), ("build_failed_text_observed", 0)):
            value = copy.deepcopy(observed); value[name] = value_to_set; bad_values.append(value)
        for name in ("task_exact_line_counts", "task_banner_states"):
            value = copy.deepcopy(observed); value[name]["host_native_build"] = PRIVATE_SENTINEL; bad_values.append(value)
            value = copy.deepcopy(observed); value[name][PRIVATE_SENTINEL] = value[name].pop("host_native_build"); bad_values.append(value)
        value = diagnostic.prepare_contract_unavailable("diagnostic_limit"); value["build_failed_text_observed"] = False; bad_values.append(value)
        for index, value in enumerate(bad_values):
            with self.subTest(schema_case=index):
                self.unavailable(diagnostic.bounded_prepare_contract_public(value), "classifier_error")
        self.unavailable(diagnostic.prepare_contract_unavailable([PRIVATE_SENTINEL]), "classifier_error")
        self.unavailable(diagnostic.prepare_contract_unavailable(PRIVATE_SENTINEL), "classifier_error")

    def test_new07_secondary_classifier_assignment_errors_keep_exact_primary(self):
        body = GOOD.replace("> Task " + TASKS["desktop_resources"] + "\n", "")
        for name in ("observe_prepare_contract", "bounded_prepare_contract_public"):
            with self.subTest(secondary_owner=name), mock.patch.object(diagnostic, name, side_effect=RuntimeError(PRIVATE_SENTINEL)):
                receipt = {}
                self.assertIsNone(self.refused(body, receipt))
                self.assertEqual(receipt, {})
        class FailingReceipt(dict):
            def __setitem__(self, key, value):
                raise RuntimeError(PRIVATE_SENTINEL)
        with self.assertRaises(target.Refusal) as caught:
            target.review_prepare(body, FailingReceipt())
        self.assertEqual(str(caught.exception), REASON)
        with self.assertRaises(target.Refusal) as caught:
            target.review_prepare(body, 0)
        self.assertEqual(str(caught.exception), REASON)
        with mock.patch.object(diagnostic, "observe_prepare_contract", return_value={"private": PRIVATE_SENTINEL}):
            self.unavailable(self.refused(body), "classifier_error")

    def test_new08_postcondition_route_does_not_reopen_logs_or_enter_native_phase(self):
        body = GOOD.replace("> Task " + TASKS["native_resources"] + "\n", "")
        with mock.patch.object(target, "phase", side_effect=AssertionError("phase-must-not-be-requested")) as phase, \
                mock.patch.object(target, "prepare_failure_diagnostic", side_effect=AssertionError("nonzero-classifier-must-not-be-requested")) as nonzero:
            value = self.refused(body)
            self.assertEqual(value["status"], "observed")
            self.assertFalse(value["cause_established"])
            phase.assert_not_called()
            nonzero.assert_not_called()


    # NEW4 only: incidental-limit raw operands, not a replay of accepted NEW8.
    def test_new09_incidental_limits_preserve_strict_API_and_raw_operands(self):
        missing = GOOD.replace("> Task " + TASKS["desktop_resources"] + "\n", "")
        payloads = (PRIVATE_SENTINEL + "p" * 4097 + "\n",
                    PRIVATE_SENTINEL + "\n" * 4097,
                    PRIVATE_SENTINEL + "\x01\n")
        for payload in payloads:
            with self.subTest(incidental_bytes=len(payload.encode("utf-8"))):
                body = missing + payload
                self.assertLessEqual(len(body.encode("utf-8")), diagnostic.MAX_PRIVATE_BYTES)
                self.unavailable(diagnostic.observe_prepare_contract(body), "diagnostic_limit")
                value = diagnostic._observe_refused_prepare_contract_raw(body)
                self.assertEqual(value["status"], "observed")
                self.assertEqual(value["task_exact_line_counts"],
                                 {key: "absent" if key == "desktop_resources" else "one" for key in TASKS})
                self.assertEqual(value["successful_footer_count"], "one")
                self.assertFalse(value["forbidden_test_task_banner_observed"])
                self.assertFalse(value["build_failed_text_observed"])
                self.assertEqual(value["task_banner_states"], {key: "unobserved" for key in TASKS})
                self.assertFalse(value["cause_established"])
                encoded = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii")
                self.assertNotIn(PRIVATE_SENTINEL.encode(), encoded)
                self.assertLessEqual(len(encoded), 4096)

    def test_new10_raw_original_regex_equality_without_normalization(self):
        host_line = "> Task " + TASKS["host_native_build"] + "\n"
        cases = {
            "raw_ANSI": GOOD.replace("> Task ", "\x1b[32m> Task ") + "\x01",
            "raw_CRLF": GOOD.replace("\n", "\r\n") + "\x01",
            "annotation": GOOD.replace(host_line, host_line.rstrip("\n") + " UP-TO-DATE\n") + "\x01",
            "duplicate_task": GOOD + host_line + "\x01",
            "missing_footer": GOOD.replace("BUILD SUCCESSFUL in 1s\n", "") + "\x01",
            "duplicate_footer": GOOD + "BUILD SUCCESSFUL in 2s\n\x01",
            "test_banner": GOOD + "> Task :calf-file-picker:customTest NO-SOURCE\n\x01",
            "unanchored_failed": GOOD + PRIVATE_SENTINEL + " wrapper BUILD FAILED suffix\n\x01",
        }
        for case, body in cases.items():
            with self.subTest(raw_case=case):
                value = diagnostic._observe_refused_prepare_contract_raw(body)
                counts = {}
                for key, task in TASKS.items():
                    count = len(target.re.findall(r"(?m)^> Task " + target.re.escape(task) + r"$", body))
                    counts[key] = "absent" if count == 0 else "one" if count == 1 else "multiple"
                footer_count = len(target.re.findall(r"(?m)^BUILD SUCCESSFUL in .+$", body))
                footer = "absent" if footer_count == 0 else "one" if footer_count == 1 else "multiple"
                test_flag = target.re.search(
                    r"(?m)^> Task \S*(?:desktopTest|connectedAndroidDeviceTest|Test)(?:\s|$)", body) is not None
                failed_flag = "BUILD FAILED" in body
                self.assertEqual(value["task_exact_line_counts"], counts)
                self.assertEqual(value["successful_footer_count"], footer)
                self.assertEqual(value["forbidden_test_task_banner_observed"], test_flag)
                self.assertEqual(value["build_failed_text_observed"], failed_flag)
                self.assertTrue(any(count != "one" for count in counts.values()) or footer != "one" or test_flag or failed_flag)
                self.assertEqual(value["task_banner_states"], {key: "unobserved" for key in TASKS})
                self.assertFalse(value["cause_established"])
                self.assertNotIn(PRIVATE_SENTINEL, json.dumps(value))
                if case in ("raw_ANSI", "raw_CRLF"):
                    self.assertEqual(counts, {key: "absent" for key in TASKS})

    def test_new11_private_raw_fallback_independent_UTF8_byte_schema_and_public_caps(self):
        class UntrustedStr(str):
            def encode(self, *args, **kwargs):
                raise AssertionError("subclass-encoding-must-not-run")
        bad = ((None, "classifier_error"), (b"trace", "classifier_error"), (True, "classifier_error"),
               (UntrustedStr("trace"), "classifier_error"), ("\ud800", "UTF8_refused"),
               ("p" * 65537, "diagnostic_limit"), ("\u00e9" * 32769, "diagnostic_limit"))
        for body, code in bad:
            with self.subTest(unavailable_code=code):
                self.unavailable(diagnostic._observe_refused_prepare_contract_raw(body), code)
        prefix = PRIVATE_SENTINEL + "\x01\n"
        for body in (prefix + "p" * (65536 - len(prefix.encode("utf-8"))), "\U0001f642" * 16384):
            with self.subTest(boundary_codepoints=len(body)):
                self.assertEqual(len(body.encode("utf-8")), 65536)
                value = diagnostic._observe_refused_prepare_contract_raw(body)
                self.assertEqual(value["status"], "observed")
                self.assertEqual(set(value), set(diagnostic.prepare_contract_unavailable("classifier_error")))
                self.assertEqual(value["task_exact_line_counts"], {key: "absent" for key in TASKS})
                self.assertEqual(value["task_banner_states"], {key: "unobserved" for key in TASKS})
                self.assertEqual(value["successful_footer_count"], "absent")
                self.assertFalse(value["forbidden_test_task_banner_observed"])
                self.assertFalse(value["build_failed_text_observed"])
                self.assertFalse(value["cause_established"])
                encoded = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii")
                self.assertNotIn(PRIVATE_SENTINEL.encode(), encoded)
                self.assertLessEqual(len(encoded), 4096)
        with mock.patch.object(diagnostic, "MAX_PUBLIC_BYTES", 1):
            self.unavailable(diagnostic._observe_refused_prepare_contract_raw(GOOD), "diagnostic_limit")

    def test_new12_fallback_route_scope_secondary_failures_and_native_guards(self):
        body = GOOD.replace("> Task " + TASKS["desktop_resources"] + "\n", "")
        limit = diagnostic.prepare_contract_unavailable("diagnostic_limit")
        with mock.patch.object(diagnostic, "observe_prepare_contract", return_value=limit) as strict, \
                mock.patch.object(diagnostic, "_observe_refused_prepare_contract_raw",
                                  wraps=diagnostic._observe_refused_prepare_contract_raw) as fallback:
            value = self.refused(body)
            strict.assert_called_once_with(body)
            fallback.assert_called_once_with(body)
            self.assertEqual(value["task_exact_line_counts"]["desktop_resources"], "absent")
            self.assertEqual(value["task_banner_states"], {key: "unobserved" for key in TASKS})
            self.assertFalse(value["cause_established"])
        with mock.patch.object(diagnostic, "observe_prepare_contract") as strict, \
                mock.patch.object(diagnostic, "_observe_refused_prepare_contract_raw") as fallback:
            receipt = {"held": True}
            self.assertEqual(target.review_prepare(GOOD, receipt),
                             {"required_resource_tasks": list(TASKS.values())[1:],
                              "host_native_build_task_returned": True, "executed_tests": 0})
            self.assertEqual(receipt, {"held": True})
            with self.assertRaises(target.Refusal) as caught:
                target.review_prepare(body)
            self.assertEqual(str(caught.exception), REASON)
            strict.assert_not_called()
            fallback.assert_not_called()
        for code in ("UTF8_refused", "remaining_budget_refused", "classifier_error"):
            with self.subTest(nonfallback_code=code), \
                    mock.patch.object(diagnostic, "observe_prepare_contract",
                                      return_value=diagnostic.prepare_contract_unavailable(code)), \
                    mock.patch.object(diagnostic, "_observe_refused_prepare_contract_raw") as fallback:
                self.unavailable(self.refused(body), code)
                fallback.assert_not_called()
        with mock.patch.object(diagnostic, "observe_prepare_contract", return_value={"private": PRIVATE_SENTINEL}), \
                mock.patch.object(diagnostic, "_observe_refused_prepare_contract_raw") as fallback:
            self.unavailable(self.refused(body), "classifier_error")
            fallback.assert_not_called()
        with mock.patch.object(diagnostic, "observe_prepare_contract", return_value=limit), \
                mock.patch.object(diagnostic, "_observe_refused_prepare_contract_raw", side_effect=RuntimeError(PRIVATE_SENTINEL)):
            value = self.refused(body)
            self.unavailable(value, "diagnostic_limit")
            self.assertNotIn(PRIVATE_SENTINEL, json.dumps(value))
        with mock.patch.object(diagnostic, "observe_prepare_contract", return_value=limit), \
                mock.patch.object(diagnostic, "_observe_refused_prepare_contract_raw", return_value={"private": PRIVATE_SENTINEL}):
            self.unavailable(self.refused(body), "classifier_error")
        class SecondAssignmentFails(dict):
            def __init__(self):
                super().__init__()
                self.assignments = 0
            def __setitem__(self, key, value):
                self.assignments += 1
                if self.assignments == 2:
                    raise RuntimeError(PRIVATE_SENTINEL)
                return super().__setitem__(key, value)
        receipt = SecondAssignmentFails()
        with mock.patch.object(diagnostic, "observe_prepare_contract", return_value=limit):
            self.unavailable(self.refused(body, receipt), "diagnostic_limit")
        self.assertEqual(receipt.assignments, 2)


    # NEW2 only: fixed name/marker observations, no accepted population replay.
    def test_new13_fixed_leaf_names_and_task_frame_order_never_change_acceptance(self):
        expected = {"desktopTest": "test_task_name", "connectedAndroidDeviceTest": "test_task_name"}
        expected.update({prefix + source_set: "resource_preparation_name"
                         for prefix in ("convertXmlValueResourcesFor", "copyNonXmlValueResourcesFor",
                                        "prepareComposeResourcesTaskFor", "generateResourceAccessorsFor")
                         for source_set in ("CommonTest", "DesktopTest")})
        task_order = ["host_native_build", "desktop_resources", "runtime_classpath", "native_resources"]
        reason = "^standard-fresh-host-preparation-task-or-zero-test-contract-refused$"
        for leaf, kind in expected.items():
            with self.subTest(leaf=leaf):
                body = GOOD.replace("BUILD SUCCESSFUL", "> Task :private-" + PRIVATE_SENTINEL + ":" +
                                             leaf + " SKIPPED\nBUILD SUCCESSFUL")
                value = diagnostic.observe_prepare_contract(body)
                self.assertEqual("observed", value["status"])
                self.assertEqual([{"leaf_id": leaf, "name_kind": kind, "count": "one"}], value["refused_task_names"])
                self.assertEqual(task_order + ["refused:" + leaf, "successful_footer"], value["task_build_frame_order"])
                self.assertEqual("complete_projection", value["task_build_frame_order_status"])
                raw = diagnostic._observe_refused_prepare_contract_raw(body)
                for key in ("refused_task_names", "task_build_frame_order", "task_build_frame_order_status"):
                    self.assertEqual(value[key], raw[key])
                self.assertEqual({"unobserved"}, set(raw["task_banner_states"].values()))
                receipt = {}
                with self.assertRaisesRegex(target.Refusal, reason):
                    target.review_prepare(body, receipt)
                self.assertEqual(value, receipt["prepare_contract_diagnostic"])
                self.assertIs(False, value["cause_established"])
                self.assertNotIn(PRIVATE_SENTINEL, json.dumps(value))
        nonbare = GOOD.replace("buildNativeLib\n", "buildNativeLib UP-TO-DATE\n")
        value = diagnostic._observe_refused_prepare_contract_raw(nonbare)
        self.assertEqual("host_native_build:nonbare", value["task_build_frame_order"][0])
        self.assertEqual("absent", value["task_exact_line_counts"]["host_native_build"])
        with self.assertRaisesRegex(target.Refusal, reason):
            target.review_prepare(nonbare, {})
        # Neither an ANSI prefix nor a Unicode line separator creates a raw LF
        # task boundary. These diagnostics must not normalize original operands.
        for noise in ("\x1b[31m> Task :private:desktopTest\x1b[0m", "private\u2028> Task :private:desktopTest"):
            value = diagnostic._observe_refused_prepare_contract_raw(GOOD + noise + "\n")
            self.assertEqual([], value["refused_task_names"])
            self.assertIs(False, value["forbidden_test_task_banner_observed"])
        # These mixed frames/control bytes are synthetic, not the missing capture.
        body = ("\x1b[31m" + PRIVATE_SENTINEL + "\x1b[0m\n> Task :calf-file-picker:buildNativeLib\n"
                "> Task :private:first\n> Task :private:second\n> Task :calf-file-picker:buildNativeLib\n" +
                ("> Task :private:" + PRIVATE_SENTINEL + "Test\n") * 2 +
                "\n".join("> Task " + task for task in target.PREPARE_TASKS) +
                "\nFAILURE: Build failed with an exception.\n* What went wrong:\n* Exception is:\n"
                "BUILD FAILED in 1s\nBUILD SUCCESSFUL in 1s\n")
        self.assertEqual("diagnostic_limit", diagnostic.observe_prepare_contract(body)["unavailable_code"])
        value = diagnostic._observe_refused_prepare_contract_raw(body)
        self.assertEqual([{"leaf_id": "unrecognized", "name_kind": "unrecognized_name", "count": "multiple"}],
                         value["refused_task_names"])
        self.assertEqual(["host_native_build", "other_task_banner", "host_native_build", "refused:unrecognized",
                          "refused:unrecognized", *task_order[1:], "failure_frame", "what_frame", "exception_frame",
                          "failed_footer", "successful_footer"], value["task_build_frame_order"])
        self.assertEqual("multiple", value["task_exact_line_counts"]["host_native_build"])
        receipt = {}
        with self.assertRaisesRegex(target.Refusal, reason):
            target.review_prepare(body, receipt)
        self.assertEqual(value, receipt["prepare_contract_diagnostic"])
        self.assertNotIn(PRIVATE_SENTINEL, json.dumps(value))
        self.assertIs(False, value["cause_established"])
        # No diagnostics on the unchanged accepted synthetic preparation contract.
        receipt = {}
        self.assertEqual({"required_resource_tasks": list(target.PREPARE_TASKS), "host_native_build_task_returned": True,
                          "executed_tests": 0}, target.review_prepare(GOOD, receipt))
        self.assertEqual({}, receipt)

    def test_new14_detail_caps_schema_and_secondary_errors_preserve_primary(self):
        self.assertEqual((65536, 4096, 4096, 4096, 32),
                         (diagnostic.MAX_PRIVATE_BYTES, diagnostic.MAX_PUBLIC_BYTES, diagnostic.MAX_LINES, diagnostic.MAX_LINE_BYTES,
                          diagnostic.PREPARE_CONTRACT_ORDER_LIMIT))
        tail = GOOD.replace("BUILD SUCCESSFUL", "> Task :private:" + PRIVATE_SENTINEL + "Test\nBUILD SUCCESSFUL")
        body = "\x00\n" + ("> Task :calf-file-picker:buildNativeLib\n> Task :private:other\n") * 40 + tail
        full_order = ["host_native_build", "other_task_banner"] * 40 + [
            "host_native_build", "desktop_resources", "runtime_classpath", "native_resources",
            "refused:unrecognized", "successful_footer"]
        value = diagnostic._observe_refused_prepare_contract_raw(body)
        self.assertEqual("observed", value["status"])
        self.assertEqual(full_order[:16] + ["omitted_middle"] + full_order[-15:], value["task_build_frame_order"])
        self.assertEqual("middle_omitted", value["task_build_frame_order_status"])
        self.assertEqual("multiple", value["task_exact_line_counts"]["host_native_build"])
        self.assertNotIn(PRIVATE_SENTINEL, json.dumps(value))
        maximal = copy.deepcopy(value)
        maximal["refused_task_names"] = [{"leaf_id": key, "name_kind": kind, "count": "multiple"}
                                          for key, kind in diagnostic.PREPARE_CONTRACT_LEAF_KINDS.items()]
        maximal["task_build_frame_order"] = [max(diagnostic.PREPARE_CONTRACT_ORDER_EVENTS, key=len)] * 32
        maximal["task_build_frame_order_status"] = "complete_projection"
        self.assertIs(maximal, diagnostic.bounded_prepare_contract_public(maximal))
        self.assertLessEqual(len(json.dumps(maximal, ensure_ascii=True, separators=(",", ":")).encode("ascii")), 4096)
        for change in (
                {"refused_task_names": [{"leaf_id": PRIVATE_SENTINEL, "name_kind": "unrecognized_name", "count": "one"}]},
                {"refused_task_names": [{"leaf_id": "desktopTest", "name_kind": "resource_preparation_name", "count": "one"}]},
                {"refused_task_names": [{"leaf_id": "desktopTest", "name_kind": "test_task_name", "count": True}]},
                {"refused_task_names": value["refused_task_names"] * 2},
                {"task_build_frame_order": [PRIVATE_SENTINEL]},
                {"task_build_frame_order": ["host_native_build"] * 33},
                {"task_build_frame_order": ["omitted_middle"]},
                {"task_build_frame_order_status": PRIVATE_SENTINEL},
                {"forbidden_test_task_banner_observed": False}):
            changed = copy.deepcopy(value)
            changed.update(change)
            refused = diagnostic.bounded_prepare_contract_public(changed)
            self.assertEqual(("unavailable", "classifier_error"), (refused["status"], refused["unavailable_code"]))
            self.assertEqual(([], [], "unobserved"), (refused["refused_task_names"], refused["task_build_frame_order"],
                                                     refused["task_build_frame_order_status"]))
            self.assertNotIn(PRIVATE_SENTINEL, json.dumps(refused))
        for observer in (diagnostic.observe_prepare_contract, diagnostic._observe_refused_prepare_contract_raw):
            for bad, code in ((None, "classifier_error"), ("\ud800", "UTF8_refused"), ("x" * 65537, "diagnostic_limit")):
                self.assertEqual(code, observer(bad)["unavailable_code"])
        # The caller's existing secondary-error catch must retain its refusal.
        receipt = {"kept": True}
        with mock.patch.object(diagnostic, "_observe_prepare_contract_details", side_effect=RuntimeError(PRIVATE_SENTINEL)):
            with self.assertRaisesRegex(target.Refusal, "^standard-fresh-host-preparation-task-or-zero-test-contract-refused$"):
                target.review_prepare(tail, receipt)
        self.assertEqual({"kept": True}, receipt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
