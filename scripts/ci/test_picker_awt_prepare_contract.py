"""NEW8 source controls for passive preparation-postcondition diagnostics.

Synthetic in-memory traces only. No Gradle/native/consumer acceptance and no
replay of previously accepted failed-PREPARE diagnostic test populations.
"""
from __future__ import annotations

import ast
from contextlib import ExitStack, redirect_stdout
import io
import tempfile
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
import picker_awt_preparation as preparation_target

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
# P5 current ingress is exact; D1/D2/D3 literal pins above remain historical.
P5_EXPECTED_SOURCES = {**EXPECTED_SOURCES, **{'scripts/ci/picker_awt_generation.py': {'bytes': 47548, 'sha256': 'ae2ecfbbcfc3bc422a2639527eccbb7b8fcd39cddf7cbd46f77cadec025d01ee'}, 'scripts/ci/picker_awt_preparation.py': {'bytes': 9686, 'sha256': '9f2f0bdd8a7dca5d2c828821ac5c721713371b86e33ea49ddd64f892b547842f'}}}
P5_HELPER_MARKER = '# P5: logical native-build completion, never a rendered task-header count.\n'
P5_HELPER_SHA256 = 'a90100d5e794eeaf6e3b0cc0493fe55cc023d8d502bcd4042fb2e26916e39843'
P5_SOURCE_INVERSES = {'scripts/ci/picker_awt_generation.py': [('    completion = _prepare_native_completion(body)\n    tasks = PREPARE_TASKS\n    if (completion is None or not re.search(r"(?m)^> Task :calf-file-picker:buildNativeLib$", body) or\n            any(len(re.findall(r"(?m)^> Task " + re.escape(task) + r"$", body)) != 1 for task in tasks) or\n            len(re.findall(r"(?m)^BUILD SUCCESSFUL in .+$", body)) != 1 or\n            _prepare_forbidden_test_task(body) or "BUILD FAILED" in body):\n', '    tasks = (":calf-file-picker:buildNativeLib", *PREPARE_TASKS)\n    if (any(len(re.findall(r"(?m)^> Task " + re.escape(task) + r"$", body)) != 1 for task in tasks) or\n            len(re.findall(r"(?m)^BUILD SUCCESSFUL in .+$", body)) != 1 or\n            re.search(r"(?m)^> Task \\S*(?:desktopTest|connectedAndroidDeviceTest|Test)(?:\\s|$)|BUILD FAILED", body)):\n'), ('    return {"required_resource_tasks": list(PREPARE_TASKS), "host_native_build_task_returned": True, "executed_tests": 0,\n            "native_build_completion": completion}\n', '    return {"required_resource_tasks": list(PREPARE_TASKS), "host_native_build_task_returned": True, "executed_tests": 0}\n'), ('        native = native_identity(root, revision, version, budget)\n        require_prepare_native_identity(receipt["preparation"], native)\n', '        native = native_identity(root, revision, version, budget)\n')], 'scripts/ci/picker_awt_preparation.py': [('        native = r.native_identity(root, revision, version, budget)\n        r.require_prepare_native_identity(receipt["preparation"], native)\n', '        native = r.native_identity(root, revision, version, budget)\n')]}
P5_PROOF_SOURCES = {'.github/workflows/build-native-libs.yml': {'bytes': 13992, 'sha256': '26edb07e55079f72f8637b3d69f56ab4b202df2baa143b1d8a133c3cc187a838'}, 'calf-file-picker/build.gradle.kts': {'bytes': 4707, 'sha256': 'c89af41eef7ff43de667d2bbd090feab559a6d18d349a9d8510d91986f940044'}, 'convention-plugins/src/main/kotlin/Hirearchy.kt': {'bytes': 2256, 'sha256': '7e021c98adada58ebadef61bc8eb1392cda712019ea947e42cb1df1956cefee7'}, 'convention-plugins/src/main/kotlin/LibraryTests.kt': {'bytes': 552, 'sha256': 'a40e5681410071d6d5c33270e40ec11b520f82765f5a3c54ef434f132da3845c'}, 'convention-plugins/src/main/kotlin/NativeLibraries.kt': {'bytes': 9741, 'sha256': '45556959ab2a17e1742f6718d13358d3dbd354fd7aa1acdcbec3d36c7169115d'}, 'convention-plugins/src/main/kotlin/Targets.kt': {'bytes': 1545, 'sha256': 'e3a962fdcd0c2fd2b22201be6ccb0cad9917ef5edb1149e4933684b67b1bffaa'}, 'convention-plugins/src/main/kotlin/compose.multiplatform.gradle.kts': {'bytes': 274, 'sha256': 'f51f60afffb2d0b3350c255e89c18ab9dbfe13829a3617219bd6d21a07919e39'}, 'convention-plugins/src/main/kotlin/kotlin.multiplatform.gradle.kts': {'bytes': 330, 'sha256': '00c4938fa93c982d16e1b880b2c9de317df0b4280597ba99f4942050cc629330'}, 'scripts/ci/picker_awt_generation.py': {'bytes': 47548, 'sha256': 'ae2ecfbbcfc3bc422a2639527eccbb7b8fcd39cddf7cbd46f77cadec025d01ee'}, 'scripts/ci/picker_awt_preparation.py': {'bytes': 9686, 'sha256': '9f2f0bdd8a7dca5d2c828821ac5c721713371b86e33ea49ddd64f892b547842f'}, 'scripts/ci/picker_awt_prepare_failure.py': {'bytes': 36874, 'sha256': '543af524c43acfb0f25ad3ed6236767dd14c869ba9b6eb5832180e889f429bae'}, 'scripts/ci/picker_jni_actual_jvm2.py': {'bytes': 28352, 'sha256': 'dba05feb854eddc09babf1da6b2038094c330928e22f9752795ddeeca4ff4f8b'}, 'scripts/ci/test_picker_awt_generation.py': {'bytes': 28622, 'sha256': '5a684f050eac78ccfd42a61837180a3f897e5b50b5f92e921c38eab3b2ed9501'}, 'scripts/ci/test_picker_awt_prepare_failure_diagnostics.py': {'bytes': 53121, 'sha256': '0ba041ee973f036cda822546b99a2057993f70620fefdd17f1e0d4e76c461c24'}, 'scripts/native/artifacts.py': {'bytes': 25961, 'sha256': 'd8b4f7ba5924cc2087d5d46068f6d017baa8765e4f70ccc0284a7ab2169d8a00'}}


def _p5_previous_source(relative: str, data: bytes) -> str:
    """Exact current qualification precedes the literal diagnostic-history view."""
    source = data.decode("utf-8")
    if relative == "scripts/ci/picker_awt_generation.py":
        if source.count(P5_HELPER_MARKER) != 1:
            raise AssertionError("P5-helper-boundary-refused")
        start = source.index(P5_HELPER_MARKER)
        end = source.index("def review_prepare(", start)
        if hashlib.sha256(source[start:end].encode()).hexdigest() != P5_HELPER_SHA256:
            raise AssertionError("P5-helper-inverse-SHA256-refused")
        source = source[:start] + source[end:]
    for current, previous in reversed(P5_SOURCE_INVERSES.get(relative, ())):
        if source.count(current) != 1:
            raise AssertionError("P5-history-exact-inverse-count-refused")
        source = source.replace(current, previous, 1)
    expected = EXPECTED_SOURCES[relative]
    payload = source.encode("utf-8")
    if len(payload) != expected["bytes"] or hashlib.sha256(payload).hexdigest() != expected["sha256"]:
        raise AssertionError("P5-history-original-bytes-or-SHA256-refused")
    return source


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
NATIVE_BUILD_COMPLETION = {"module": "calf-file-picker", "platform": "macos-arm64", "sha256": "d" * 64,
                           "sourceSha256": "c" * 64, "sourceTreeDirty": False}
NATIVE_BUILD_LINE = json.dumps(NATIVE_BUILD_COMPLETION) + "\n"
GOOD = "".join("> Task " + task + "\n" for task in TASKS.values()) + NATIVE_BUILD_LINE + "BUILD SUCCESSFUL in 1s\n"
REASON = "standard-fresh-host-preparation-task-or-zero-test-contract-refused"
PRIVATE_SENTINEL = "DO_NOT_EXPORT_contract_private_operand"


class NativePreparationContractDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Once per NEW cohort: only six finite artifact-bound owning sources.
        root = Path(__file__).resolve().parents[2]
        cls.sources, cls.current_sources = {}, {}
        for relative, expected in P5_EXPECTED_SOURCES.items():
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
                cls.current_sources[relative] = data.decode("utf-8")
                cls.sources[relative] = _p5_previous_source(relative, data)
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
                    "executed_tests": 0, "native_build_completion": NATIVE_BUILD_COMPLETION}
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
                # Native rendering may repeat; duplicate logical returns still refuse.
                value = self.refused(GOOD + line + (NATIVE_BUILD_LINE if key == "host_native_build" else ""))
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
                              "host_native_build_task_returned": True, "executed_tests": 0,
                              "native_build_completion": NATIVE_BUILD_COMPLETION})
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
                          "executed_tests": 0, "native_build_completion": NATIVE_BUILD_COMPLETION},
                         target.review_prepare(GOOD, receipt))
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


class NativePreparationLogicalCompletionTests(unittest.TestCase):
    """P5 NEW6 only: source and synthetic data, never a hosted/native rerun."""
    setUp = NativePreparationContractDiagnosticTests.setUp
    tearDown = NativePreparationContractDiagnosticTests.tearDown
    refused = NativePreparationContractDiagnosticTests.refused

    @classmethod
    def setUpClass(cls):
        # Reuse only finite source custody/history checks, not any accepted method.
        NativePreparationContractDiagnosticTests.setUpClass.__func__(cls)
        root = Path(__file__).resolve().parents[2]
        for relative, expected in P5_PROOF_SOURCES.items():
            if relative in cls.current_sources:
                data = cls.current_sources[relative].encode("utf-8")
            else:
                fd = os.open(root / relative, os.O_RDONLY | os.O_NOATIME | os.O_NOFOLLOW)
                try:
                    before = os.fstat(fd)
                    if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or
                            before.st_size != expected["bytes"]):
                        raise AssertionError("P5-named-proof-source-shape-refused")
                    parts, remaining = [], expected["bytes"]
                    while remaining:
                        part = os.read(fd, min(65536, remaining))
                        if not part:
                            raise AssertionError("P5-named-proof-source-early-EOF-refused")
                        parts.append(part)
                        remaining -= len(part)
                    if os.read(fd, 1):
                        raise AssertionError("P5-named-proof-source-extra-EOF-refused")
                    after = os.fstat(fd)
                    if tuple(getattr(before, key) for key in STAT_FIELDS) != tuple(getattr(after, key) for key in STAT_FIELDS):
                        raise AssertionError("P5-named-proof-source-full10-refused")
                    data = b"".join(parts)
                finally:
                    os.close(fd)
            if len(data) != expected["bytes"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
                raise AssertionError("P5-named-proof-source-SHA256-refused")
            cls.current_sources[relative] = data.decode("utf-8")

    def test_p5_01_source_owners_history_commands_and_caps_hold(self):
        generation = self.current_sources["scripts/ci/picker_awt_generation.py"]
        tree = ast.parse(generation)
        for name, expected in UNCHANGED_GENERATION_FUNCTION_SHA256.items():
            node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
            self.assertEqual(expected, hashlib.sha256(ast.get_source_segment(generation, node).encode()).hexdigest())
        self.assertEqual(EXPECTED_SOURCES["scripts/ci/picker_awt_generation.py"]["sha256"],
                         hashlib.sha256(self.sources["scripts/ci/picker_awt_generation.py"].encode()).hexdigest())
        original = ast.parse(self.sources["scripts/ci/picker_awt_generation.py"])
        review = next(node for node in original.body if isinstance(node, ast.FunctionDef) and node.name == "review_prepare")
        self.assertEqual(EXPECTED_PREDICATE_AST,
                         ast.dump(next(node.test for node in review.body if isinstance(node, ast.If)), include_attributes=False))
        native = self.current_sources["convention-plugins/src/main/kotlin/NativeLibraries.kt"]
        self.assertEqual(1, native.count('tasks.register<Exec>("buildNativeLib")'))
        self.assertIn('tasks.register("writeNativeTestRuntimeClasspath")', native)
        section = native.split('tasks.register("writeNativeTestRuntimeClasspath")', 1)[1].split(
            'tasks.withType(Copy::class.java)', 1)[0]
        self.assertIn('dependsOn("desktopTestClasses")', section)
        self.assertIn('(tasks.getByName("desktopTest") as Test).classpath.files', section)
        self.assertNotIn('dependsOn("desktopTest")', section)
        artifact = self.current_sources["scripts/native/artifacts.py"]
        self.assertEqual(1, artifact.count('subprocess.run([*prefix, "cargo", "build", "--locked", "--release", "--target", target,'))
        self.assertIn('print(json.dumps({"module": args.module, "platform": result["platform"], "sha256": result["sha256"],', artifact)
        self.assertIn('"sourceSha256": result["sourceSha256"], "sourceTreeDirty": result["sourceTreeDirty"]}))', artifact)
        self.assertNotIn("gradlew", artifact)
        self.assertIn('print(json.dumps({"verified": True, "module": args.module, "platforms": [m["platform"] for m in result],', artifact)
        self.assertIn('"sourceRevision": revision, "require_clean": args.require_clean}))', artifact)
        self.assertEqual(2, native.count('val matrixArguments = if (mode == "release") listOf("--full-matrix", "--require-clean")'))
        self.assertEqual(2, native.count('else listOf("--platform", platform)'))
        hierarchy = self.current_sources["convention-plugins/src/main/kotlin/Hirearchy.kt"]
        self.assertIn('group("material")', hierarchy)
        self.assertIn('group("nonAndroid")', hierarchy)
        self.assertEqual(2, hierarchy.count("withJvm()"))
        self.assertIn('jvm("desktop")', self.current_sources["convention-plugins/src/main/kotlin/Targets.kt"])
        self.assertIn('id("org.jetbrains.compose")',
                      self.current_sources["convention-plugins/src/main/kotlin/compose.multiplatform.gradle.kts"])
        for relative, prefix in (("scripts/ci/picker_awt_generation.py", ""),
                                 ("scripts/ci/picker_awt_preparation.py", "r.")):
            body = self.current_sources[relative]
            binding = prefix + 'require_prepare_native_identity(receipt["preparation"], native)'
            self.assertEqual(1, body.count(binding))
            self.assertLess(body.index("native = " + prefix + "native_identity("), body.index(binding))
            self.assertLess(body.index(binding), body.index("= " + prefix + "classpath_identity(", body.index(binding)))
        self.assertEqual((600, 8 * 1024 * 1024, 65536, 4096, 4096, 4096),
                         (target.shared.NATIVE_BUDGET_SECONDS, target.shared.MAX_LOG_BYTES, diagnostic.MAX_PRIVATE_BYTES,
                          diagnostic.MAX_PUBLIC_BYTES, diagnostic.MAX_LINES, diagnostic.MAX_LINE_BYTES))
        self.assertEqual(5, len(target.PUBLIC_FILES))

    def test_p5_02_only_exact_owning_resource_names_bypass_test_suffix_refusal(self):
        allowed = {":calf-file-picker:" + prefix + source_set
                   for prefix in ("convertXmlValueResourcesFor", "copyNonXmlValueResourcesFor",
                                  "prepareComposeResourcesTaskFor", "generateResourceAccessorsFor")
                   for source_set in ("CommonTest", "DesktopTest", "MaterialTest", "NonAndroidTest")}
        self.assertEqual(16, len(allowed))
        self.assertEqual(allowed, target.PREPARE_RESOURCE_TASKS)
        for task in sorted(allowed):
            for suffix in ("", " NO-SOURCE", " UP-TO-DATE", " FROM-CACHE", " SKIPPED"):
                with self.subTest(task=task, suffix=suffix):
                    body = GOOD.replace("BUILD SUCCESSFUL", "> Task " + task + suffix + "\nBUILD SUCCESSFUL")
                    self.assertEqual(0, target.review_prepare(body)["executed_tests"])
        refused_tasks = (":calf-file-picker:desktopTest", ":calf-file-picker:connectedAndroidDeviceTest",
                         ":calf-file-picker:customTest", ":calf-share:desktopTest",
                         ":calf-share:convertXmlValueResourcesForCommonTest",
                         ":nested:calf-file-picker:convertXmlValueResourcesForCommonTest",
                         ":calf-file-picker:convertXmlValueResourcesForIosTest",
                         ":calf-file-picker:convertXmlValueResourcesForWebTest",
                         ":calf-file-picker:convertXmlValueResourcesForCommonTestTest",
                         ":calf-file-picker:fakeprepareComposeResourcesTaskForCommonTest")
        for task in refused_tasks:
            with self.subTest(refused_task=task):
                value = self.refused(GOOD + "> Task " + task + " NO-SOURCE\n")
                self.assertFalse(value["cause_established"])
        for suffix in (" FAILED", " " + PRIVATE_SENTINEL, "\tNO-SOURCE", " NO-SOURCE "):
            with self.subTest(resource_status=suffix):
                self.refused(GOOD + "> Task :calf-file-picker:prepareComposeResourcesTaskForCommonTest" + suffix + "\n")

    def test_p5_03_one_logical_completion_not_repeated_task_rendering_owns_native_return(self):
        host_line = "> Task " + TASKS["host_native_build"] + "\n"
        for rendered in (1, 2, 4, 9):
            with self.subTest(rendered_headers=rendered):
                body = GOOD.replace(host_line, (host_line + "> Task :synthetic:other\n") * rendered)
                value = target.review_prepare(body)
                self.assertEqual(NATIVE_BUILD_COMPLETION, value["native_build_completion"])
                self.assertEqual(0, value["executed_tests"])
                diagnostic_value = diagnostic.observe_prepare_contract(body)
                self.assertEqual("one" if rendered == 1 else "multiple",
                                 diagnostic_value["task_exact_line_counts"]["host_native_build"])
                self.assertFalse(diagnostic_value["cause_established"])
        for body in (GOOD.replace(NATIVE_BUILD_LINE, ""), GOOD + NATIVE_BUILD_LINE,
                     GOOD.replace(host_line, ""), GOOD.replace(host_line, host_line.rstrip() + " UP-TO-DATE\n"),
                     GOOD.replace("BUILD SUCCESSFUL in 1s\n", ""), GOOD + "BUILD SUCCESSFUL in 2s\n",
                     GOOD + "wrapper BUILD FAILED suffix\n"):
            self.refused(body)
        for task in target.PREPARE_TASKS:
            line = "> Task " + task + "\n"
            for body in (GOOD.replace(line, ""), GOOD + line,
                         GOOD.replace(line, line.rstrip() + " UP-TO-DATE\n")):
                self.refused(body)
        # The inherited one-bare-plus-annotated compatibility case is unchanged.
        self.assertEqual(0, target.review_prepare(GOOD + host_line.rstrip() + " UP-TO-DATE\n")["executed_tests"])
        for ordinary in (
                "[Incubating] Problems report is available at: file:///synthetic/problems.html\n",
                "[INFO] Ordinary Gradle wrapper message\n",
                'warning: the "module" property is deprecated; use "platform" instead\n',
                'warning: "module": ordinary quoted-field discussion\n',
                '[warning] "sourceTreeDirty" is a quoted field name, not JSON\n'):
            with self.subTest(ordinary_log=ordinary):
                value = target.review_prepare(GOOD + ordinary)
                self.assertEqual(NATIVE_BUILD_COMPLETION, value["native_build_completion"])
                self.assertEqual(0, value["executed_tests"])

    def test_p5_04_missing_duplicate_malformed_unknown_or_dirty_build_records_refuse(self):
        malformed = []
        for key in NATIVE_BUILD_COMPLETION:
            value = dict(NATIVE_BUILD_COMPLETION)
            del value[key]
            malformed.append(json.dumps(value) + "\n")
        for key, wrong in (("module", "calf-share"), ("platform", "macos-x64"),
                           ("sha256", "A" * 64), ("sha256", "d" * 63), ("sha256", True),
                           ("sourceSha256", "C" * 64), ("sourceSha256", None),
                           ("sourceTreeDirty", True), ("sourceTreeDirty", 0), ("sourceTreeDirty", "false"),
                           (PRIVATE_SENTINEL, "private")):
            malformed.append(json.dumps({**NATIVE_BUILD_COMPLETION, key: wrong}) + "\n")
        line = NATIVE_BUILD_LINE.rstrip("\n")
        malformed += [line[:-1] + ', "sha256": "' + "d" * 64 + '"}\n',
                      line[:-1] + ', "\\u0073ha256": "' + "d" * 64 + '"}\n',
                      line[:-1] + "\n", "[ " + line + " ]\n", "null\n", "{}\n",
                      " " + NATIVE_BUILD_LINE, "\x1b[32m" + NATIVE_BUILD_LINE,
                      NATIVE_BUILD_LINE + NATIVE_BUILD_LINE,
                      NATIVE_BUILD_LINE + '{"module":"unknown-build"}\n',
                      NATIVE_BUILD_LINE + '{"unexpected":"' + PRIVATE_SENTINEL + '"}\n',
                      NATIVE_BUILD_LINE + '{"module":\n',
                      NATIVE_BUILD_LINE + "\x1b[32m" + NATIVE_BUILD_LINE,
                      NATIVE_BUILD_LINE + "[]\n", NATIVE_BUILD_LINE + "[ 1,\n",
                      NATIVE_BUILD_LINE + "[ true,\n", NATIVE_BUILD_LINE + "[\n",
                      NATIVE_BUILD_LINE + "wrapper-prefix " + NATIVE_BUILD_LINE,
                      NATIVE_BUILD_LINE + '[INFO] {"module":\n',
                      NATIVE_BUILD_LINE + NATIVE_BUILD_LINE[1:]]
        for index, record in enumerate(malformed):
            with self.subTest(record_case=index):
                value = self.refused(GOOD.replace(NATIVE_BUILD_LINE, record))
                self.assertNotIn(PRIVATE_SENTINEL, json.dumps(value))
        verified = {"verified": True, "module": target.MODULE, "platforms": [target.PLATFORM],
                    "sourceRevision": "a" * 40, "require_clean": False}
        body = GOOD.replace(NATIVE_BUILD_LINE, NATIVE_BUILD_LINE + (json.dumps(verified) + "\n") * 2)
        self.assertEqual(NATIVE_BUILD_COMPLETION, target.review_prepare(body)["native_build_completion"])
        self.refused(body.replace(NATIVE_BUILD_LINE, ""))
        self.refused(GOOD + json.dumps({**verified, "unexpected": True}) + "\n")
        with self.assertRaisesRegex(target.Refusal, "^native-diagnostic-review-limit$"):
            target.review_prepare(GOOD + "x" * target.shared.MAX_LOG_BYTES)

    def test_p5_05_build_binary_source_and_platform_bind_to_validated_native_identity(self):
        preparation = target.review_prepare(GOOD)
        native = {"platform": target.PLATFORM, "source_sha256": "c" * 64,
                  "files": {target.NATIVE_RESOURCE: {"sha256": "d" * 64, "size": 1}}}
        before = copy.deepcopy((preparation, native))
        target.require_prepare_native_identity(preparation, native)
        self.assertEqual(before, (preparation, native))
        bad_native = []
        for key, value in (("platform", "macos-x64"), ("source_sha256", "e" * 64)):
            changed = copy.deepcopy(native); changed[key] = value; bad_native.append(changed)
        changed = copy.deepcopy(native)
        changed["files"][target.NATIVE_RESOURCE]["sha256"] = "e" * 64
        bad_native += [changed, {}, {"platform": target.PLATFORM}, None]
        for candidate in bad_native:
            with self.assertRaisesRegex(target.Refusal, "^preparation-build-completion-or-validated-native-identity-mismatch$"):
                target.require_prepare_native_identity(preparation, candidate)
        for candidate in ({}, {"native_build_completion": {**NATIVE_BUILD_COMPLETION, "sourceTreeDirty": 0}}, None):
            with self.assertRaisesRegex(target.Refusal, "^preparation-build-completion-or-validated-native-identity-mismatch$"):
                target.require_prepare_native_identity(candidate, native)

    def test_p5_06_both_controllers_bind_before_any_inventory_or_JUnit_and_prep_stays_zero(self):
        for controller in (target, preparation_target):
            modes = ("bad-binary", "bad-source", "bad-platform") + (("positive",) if controller is preparation_target else ())
            for mode in modes:
                with self.subTest(controller=controller.FOCUS, mode=mode), \
                        tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                    root, revision = Path(directory).resolve(), "a" * 40
                    selected_budget = target.shared.NativeBudget(clock=lambda: 0)
                    runtime = {"source_revision": revision, "source_tree_dirty": False,
                               "host": {"system": "Darwin", "architecture": "arm64"},
                               "java": {"major": 17, "version": "17.0.20"},
                               "rust": {"release": "1.98.0", "host": target.shared.TARGET},
                               "compiler_runtime_fingerprint": "b" * 64}
                    native = {"platform": target.PLATFORM, "source_sha256": "c" * 64,
                              "files": {name: {"sha256": "d" * 64, "size": 1}
                                        for name in (target.NATIVE_RESOURCE, target.MANIFEST_RESOURCE)}}
                    if mode == "bad-binary":
                        native["files"][target.NATIVE_RESOURCE]["sha256"] = "e" * 64
                    elif mode == "bad-source":
                        native["source_sha256"] = "e" * 64
                    elif mode == "bad-platform":
                        native["platform"] = "macos-x64"
                    cp = {"resources": {name: [{"entry_index": 0, "sha256": "d" * 64, "size": 1}]
                                        for name in target.REQUIRED_RESOURCES}}
                    calls = []
                    body = GOOD.replace("> Task " + TASKS["host_native_build"] + "\n",
                                        ("> Task " + TASKS["host_native_build"] + "\n> Task :synthetic:other\n") * 4)
                    body = body.replace("BUILD SUCCESSFUL", "".join("> Task " + task + " NO-SOURCE\n"
                                        for task in sorted(target.PREPARE_RESOURCE_TASKS)) + "BUILD SUCCESSFUL")
                    def phase(actual_root, private, stage, command, budget, receipt):
                        self.assertEqual(root, actual_root)
                        self.assertIs(selected_budget, budget)
                        self.assertEqual("prepare", stage)
                        expected = target.prepare_command(root, private)
                        if controller is preparation_target:
                            expected = [*expected, "--stacktrace"]
                        self.assertEqual(expected, command)
                        calls.append(stage)
                        receipt["phases"][stage] = {"started": True, "exit_code": 0, "capture_complete": True,
                                                   "captured_bytes": len(body.encode()),
                                                   "private_capture_sha256": hashlib.sha256(body.encode()).hexdigest(),
                                                   "post_exit_group_state": "absent", "stop_reason": None,
                                                   "elapsed_seconds": 0.1}
                        return body
                    stack.enter_context(mock.patch.dict(os.environ, {}, clear=True))
                    stack.enter_context(mock.patch.object(target.library, "ROOT", root))
                    stack.enter_context(mock.patch.object(target.library, "git_revision", return_value=revision))
                    stack.enter_context(mock.patch.object(target.library.runtime_context, "capture", return_value=runtime))
                    stack.enter_context(mock.patch.object(controller, "source_snapshot", return_value={"synthetic-source": "c" * 64}))
                    stack.enter_context(mock.patch.object(target, "qualify_jdk", return_value=(Path("/synthetic-jdk"), {"synthetic": "jdk"})))
                    stack.enter_context(mock.patch.object(target, "default_version", return_value="0.1.0-SNAPSHOT"))
                    stack.enter_context(mock.patch.object(target, "native_identity", return_value=native))
                    if mode == "positive":
                        classpath = stack.enter_context(mock.patch.object(target, "classpath_identity", return_value=("synthetic-cp", cp)))
                    else:
                        classpath = stack.enter_context(mock.patch.object(target, "classpath_identity",
                                                                         side_effect=AssertionError("must-bind-before-classpath-or-native-phase")))
                    stack.enter_context(mock.patch.object(target, "phase", side_effect=phase))
                    stack.enter_context(mock.patch.object(target.shared, "NativeBudget", return_value=selected_budget))
                    with redirect_stdout(io.StringIO()):
                        result = controller.run(Path("build/ci-verification/synthetic"))
                    output = root / "build/ci-verification/synthetic"
                    receipt = json.loads((output / "receipt.json").read_text())
                    self.assertEqual(["prepare"], calls)
                    self.assertEqual(mode == "positive", receipt["passed"])
                    self.assertEqual(0 if mode == "positive" else 1, result)
                    self.assertEqual(0, receipt["tests"])
                    self.assertTrue(receipt["owned_java_descriptors_closed"])
                    self.assertLessEqual({path.name for path in output.glob("*.json")}, set(target.PUBLIC_FILES))
                    if mode != "positive":
                        classpath.assert_not_called()
                        self.assertEqual("prepare", receipt["failed_stage"])
                        self.assertEqual("preparation-build-completion-or-validated-native-identity-mismatch", receipt["reason_code"])
                    if controller is preparation_target:
                        self.assertEqual(0, receipt["native_processes_requested"])
                        self.assertEqual(0, receipt["inventory_processes_requested"])
                        self.assertEqual(0, receipt["native_JUnit_requested"])
                        self.assertEqual(mode == "positive", receipt["preparation_passed"])
                        self.assertFalse(receipt["native_reuse_certificate"])
                    if mode == "positive":
                        self.assertTrue(receipt["held_inputs"])
                        self.assertTrue(receipt["held_native_bundle"])
                        self.assertEqual(NATIVE_BUILD_COMPLETION, receipt["preparation"]["native_build_completion"])



if __name__ == "__main__":
    unittest.main(verbosity=2)
