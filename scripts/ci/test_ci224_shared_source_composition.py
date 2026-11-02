"""Regression controls for the two shared-source CI224 failures.

Select inert source functions only; never import historical test classes, model
fixtures or native/build/network drivers. Current Share188 bytes must qualify
before the retained alert/Share153/Wasm chain or FF16 source assertions run.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
ALERT = "scripts/ci/test_ui_alert_container_timeout_observation.py"
HISTORY = "scripts/ci/test_ui_alert_important_recovery.py"
FF = "scripts/ci/test_android_camera_pre_reporter_fail_fast.py"
CONSOLE = "scripts/ci/test_android_camera_owned_avd_console_name.py"
OWNING = "scripts/ci/test_android_camera205_owning_admission.py"
EXPECTED = {
    ALERT: "fc761b20a2d5a78e275dc1e5965402a0c284c7a61b3d97c17098b7b209cc9884",
    HISTORY: "d49f5a2d27cc302c8da38522f84ae8d5d27a9b84a05fafab727f1488a677cbb8",
    FF: "afab5f37a89e0e94af7480ac7aac7023d88ffd2c85a4215e770697cb4d59f39c",
    CONSOLE: "71709ee20947d4f97df38a75c4c591bf12db319f327840b51440c07c3e2c0f33",
    OWNING: "172f39bf8c9af2a7827107bb64a0184cf8f14bf26e9913218dda37e16151b81d",
    "scripts/ci/library_tests.py": "93dfe1a301d861f091016de2dcf45ec7d7ed437f8284f90220f3971ecacabf88",
    "scripts/ci/workflow_matrix.py": "c4ad217aaf7d1c5586fe57edba3214b7c8d7bd383661df2b55a70ce4d9be3f45",
    ".github/workflows/gradle.yml": "ac55aee1f485f78914de5405c517f4a9f8a5a6fed2f7ba88650e2a4fb8401561",
}


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def assignment(source, name):
    matches = [n for n in ast.parse(source).body if isinstance(n, ast.Assign) and
               len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == name]
    if len(matches) != 1:
        raise AssertionError("An exact unique inert declaration is required")
    return matches[0]


def literal(source, name):
    return ast.literal_eval(assignment(source, name).value)


class CI224SharedSourceCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payloads = {}
        for relative, expected in EXPECTED.items():
            path = ROOT / relative
            if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
                raise AssertionError("An ordinary unshared current source file is required")
            payload = path.read_bytes()
            if not 0 < len(payload) <= 4 * 1024 * 1024 or digest(payload) != expected:
                raise AssertionError("An exact bounded current source image is required")
            cls.payloads[relative] = payload
        cls.sources = {r: b.decode() for r, b in cls.payloads.items()}

    @classmethod
    def tearDownClass(cls):
        if any((ROOT / r).read_bytes() != b for r, b in cls.payloads.items()):
            raise AssertionError("The admitted source changed during these controls")

    def alert_guard(self):
        source = self.sources[ALERT]
        names = ("RETAINED_ASSIGNMENTS", "OBSERVATION_DECLARATION", "INERT_FUNCTION_PINS",
                 "SHARE188_OUTER_GUARD_PINS")
        namespace = {n: literal(source, n) for n in names}
        namespace.update(ast=ast, hashlib=hashlib, json=json, ROOT=ROOT, HISTORICAL=HISTORY)
        function_names = {"digest", "portable_ast", "ast_digest", "raw_node",
                          "compose_share188_outer_guard", "authored_guard_namespace"}
        functions = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name in function_names]
        self.assertEqual(len(functions), len(function_names))
        self.assertFalse(any(isinstance(n, (ast.ClassDef, ast.Import, ast.ImportFrom))
                             for n in ast.walk(ast.Module(body=functions, type_ignores=[]))))
        exec(compile(ast.Module(body=functions, type_ignores=[]), "<ci224-inert-alert-byte-guards>", "exec"), namespace)
        return namespace

    def test_ci224_01_current_share_images_reverse_before_the_intact_alert_and_wasm_chain(self):
        guard = self.alert_guard()
        _, _, namespace = guard["authored_guard_namespace"](self.sources[HISTORY])
        outer = namespace["source_before_share188_failed_only_rebase"]
        combined = namespace["source_before_share_alert153_rebase"]
        self.assertEqual(set(namespace["SHARE188_FAILED_ONLY_REBASE"]), {
            "scripts/ci/library_tests.py", "scripts/ci/workflow_matrix.py", ".github/workflows/gradle.yml"})
        for relative, binding in namespace["SHARE188_FAILED_ONLY_REBASE"].items():
            with self.subTest(relative=relative):
                payload = self.payloads[relative]
                restored = outer(relative, payload)
                self.assertEqual(digest(restored), binding["before_sha256"])
                self.assertEqual(digest(combined(relative, payload)),
                                 namespace["SHARE_ALERT153_REBASE"][relative]["original153_sha256"])
                for fragment in binding["fragments"]:
                    old, new = fragment["before"].encode(), fragment["after"].encode()
                    self.assertEqual(restored.count(old), 1)
                    restored = restored.replace(old, new, 1)
                self.assertEqual(restored, payload)

    def test_ci224_02_missing_duplicate_or_modified_outer_symbols_refuse_before_compilation(self):
        guard = self.alert_guard()
        source = self.sources[HISTORY]
        declaration = assignment(source, "SHARE188_FAILED_ONLY_REBASE")
        function = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and
                        n.name == "source_before_share188_failed_only_rebase")
        raws = [guard["raw_node"](source, n).decode() for n in (declaration, function)]
        for raw in raws:
            self.assertEqual(source.count(raw), 1)
            candidates = (source.replace(raw, "", 1), source + "\n" + raw,
                          source.replace(raw, raw.rstrip("\n") + " \n", 1))
            for candidate in candidates:
                with self.subTest(symbol_bytes=len(raw), candidate_bytes=len(candidate)):
                    with patch.dict(guard, {"exec": lambda *a, **k: self.fail("Changed guard reached compilation")}):
                        with self.assertRaises(ValueError):
                            guard["compose_share188_outer_guard"](candidate, ast.parse(candidate), {})

    def test_ci224_03_old_partial_wrong_type_and_mutated_share_images_remain_refused(self):
        guard = self.alert_guard()
        _, _, namespace = guard["authored_guard_namespace"](self.sources[HISTORY])
        outer = namespace["source_before_share188_failed_only_rebase"]
        combined = namespace["source_before_share_alert153_rebase"]
        for relative in namespace["SHARE188_FAILED_ONLY_REBASE"]:
            payload = self.payloads[relative]
            old = outer(relative, payload)
            for candidate in (old, payload + b"\n", payload[:-1], b"", None, bytearray(payload), payload.decode()):
                with self.subTest(relative=relative, candidate_type=type(candidate).__name__):
                    with self.assertRaises(ValueError):
                        outer(relative, candidate)
                    with self.assertRaises(ValueError):
                        combined(relative, candidate)
        sentinel = b"unrelated synthetic bytes"
        self.assertIs(outer("synthetic-unrelated-source", sentinel), sentinel)
        self.assertEqual(digest(sentinel), digest(b"unrelated synthetic bytes"))

    def test_ci224_04_ff_overlay_is_exactly_two_current_shared_leaves_and_retains_all_18_bodies(self):
        source = self.sources[FF]
        original = literal(source, "UNCHANGED_NATIVE_SOURCE_SHA256")
        overlay = literal(source, "CAMERA224_SHARE188_SHARED_SOURCE_SHA256")
        self.assertEqual(overlay, {r: EXPECTED[r] for r in (".github/workflows/gradle.yml", "scripts/ci/library_tests.py")})
        self.assertEqual(digest(ast.get_source_segment(source, assignment(source, "UNCHANGED_NATIVE_SOURCE_SHA256")).encode()),
                         "230c0097294e1905e657158d897541da29a582fafb5457248f9dfcd1572e5b4a")
        updates = [n for n in ast.parse(source).body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and
                   isinstance(n.value.func, ast.Attribute) and isinstance(n.value.func.value, ast.Name) and
                   n.value.func.value.id == "UNCHANGED_NATIVE_SOURCE_SHA256"]
        self.assertEqual(len(updates), 1)
        expected = ast.parse("UNCHANGED_NATIVE_SOURCE_SHA256.update(CAMERA224_SHARE188_SHARED_SOURCE_SHA256)").body[0]
        self.assertEqual(ast.dump(updates[0], include_attributes=False), ast.dump(expected, include_attributes=False))
        namespace = {"UNCHANGED_NATIVE_SOURCE_SHA256": dict(original), "CAMERA224_SHARE188_SHARED_SOURCE_SHA256": overlay}
        exec(compile(ast.Module(body=updates, type_ignores=[]), "<ci224-finite-current-two-leaf-overlay>", "exec"), namespace)
        current = namespace["UNCHANGED_NATIVE_SOURCE_SHA256"]
        self.assertEqual(set(current), set(original))
        self.assertEqual({r for r in original if original[r] != current[r]}, set(overlay))
        self.assertTrue(all(digest((ROOT / r).read_bytes()) == expected for r, expected in current.items()))
        functions = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "digest"]
        self.assertEqual(len(functions), 1)
        self.assertEqual(ast.get_source_segment(source, functions[0]),
                         "def digest(path):\n    return hashlib.sha256(path.read_bytes()).hexdigest()")
        methods = {c.name + "." + n.name: ast.get_source_segment(source, n)
                   for c in ast.parse(source).body if isinstance(c, ast.ClassDef)
                   for n in c.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}
        self.assertEqual(len(methods), 18)
        self.assertEqual(digest(canonical(methods)), "4a75e3d7b9a5abc427a871a554a64804e5079393a9c1433f248f5478c9f50ef1")

    def test_ci224_05_one_leaf_current_ff_closure_refuses_stale_extra_or_missing_overlays(self):
        console, owning = self.sources[CONSOLE], self.sources[OWNING]
        before, after = (literal(console, n) for n in ("BOUND_SOURCE_BEFORE47", "BOUND_SOURCE_AFTER47"))
        self.assertEqual(literal(console, "CAMERA224_DERIVATIVE_SOURCE_SHA256"), {FF: EXPECTED[FF]})
        names = ("DERIVATIVE_SHA256", "EXPECTED_SHA256", "CAMERA205_SHARE188_SHARED_SOURCE_SHA256",
                 "CAMERA213_DERIVATIVE_SOURCE_SHA256", "CAMERA224_DERIVATIVE_SOURCE_SHA256",
                 "BEFORE47_MAPPING_SHA256", "HELPER", "FAILFAST")
        namespace = {n: literal(owning, n) for n in names}
        namespace.update(digest=digest, canonical=canonical)
        utilities = [n for n in ast.walk(ast.parse(owning)) if isinstance(n, ast.FunctionDef) and n.name == "assert_closure"]
        self.assertEqual(len(utilities), 1)
        exec(compile(ast.Module(body=utilities, type_ignores=[]), "<ci224-current-closure-utility-only>", "exec"), namespace)
        declared = literal(console, "CAMERA205_DERIVATIVE_SOURCE_SHA256")
        namespace["assert_closure"](self, before, after, declared)
        for candidate in ({}, {FF: declared[FF]}, {FF: "0" * 64}, {FF: EXPECTED[FF], "synthetic-extra": "0" * 64}):
            with patch.dict(namespace, {"CAMERA224_DERIVATIVE_SOURCE_SHA256": candidate}):
                with self.assertRaises(AssertionError):
                    namespace["assert_closure"](self, before, after, declared)
        for candidate in ({**after, FF: declared[FF]}, {**after, FF: "0" * 64}):
            with self.assertRaises(AssertionError):
                namespace["assert_closure"](self, before, candidate, declared)


if __name__ == "__main__":
    unittest.main()
