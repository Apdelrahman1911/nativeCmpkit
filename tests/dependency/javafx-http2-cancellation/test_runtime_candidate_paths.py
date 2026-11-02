"""Exact candidate inventory/guard expressions under controlled path semantics."""
from __future__ import annotations

import ast
from pathlib import Path, PurePosixPath, PureWindowsPath
import tempfile
import unittest

import build_runtime_candidate as candidate


class CompiledFile:
    def __init__(self, path, root, path_type):
        self.path, self.root, self.path_type = path, root, path_type

    def relative_to(self, root):
        if root is not self.root:
            raise AssertionError("Only the exact synthetic class root is allowed")
        return self.path_type(self.path.relative_to(root.directory).as_posix())

    def read_bytes(self):
        return self.path.read_bytes()


class CompiledRoot:
    def __init__(self, directory, path_type):
        self.directory, self.path_type = directory, path_type

    def rglob(self, pattern):
        if pattern != "*.class":
            raise AssertionError("Only the original compiled class inventory is allowed")
        return [CompiledFile(path, self, self.path_type)
                for path in sorted(self.directory.rglob(pattern))]


class RuntimeCandidatePathTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-candidate-paths-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.members = {}
        for name in candidate.CLASS_SHA256:
            relative = candidate.CLASS_PREFIX + name
            payload = b"synthetic-not-JVM-class:" + name.encode()
            path = self.directory / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            self.members[relative] = payload
        source = (candidate.HERE / "build_runtime_candidate.py").read_bytes()
        parsed = ast.parse(source)
        inventories = [node.value for node in ast.walk(parsed) if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id == "actual_classes"
                               for target in node.targets)]
        self.assertEqual(len(inventories), 1)
        self.assertIsInstance(inventories[0], ast.DictComp)
        guards = [node for node in ast.walk(parsed) if isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Attribute) and node.func.attr == "need"
                  and len(node.args) == 2 and isinstance(node.args[1], ast.Constant)
                  and str(node.args[1].value).startswith("Compiler emits changed/extra owning classes;")]
        self.assertEqual(len(guards), 1)
        # Execute only the two exact reviewed local expressions, not archived CI
        # code, compiler/JVM commands, the candidate builder or native libraries.
        self.inventory_expression = compile(ast.Expression(inventories[0]), "<candidate-inventory>", "eval")
        self.guard_expression = compile(ast.Expression(guards[0]), "<candidate-class-guard>", "eval")

    def inventory(self, path_type):
        return eval(self.inventory_expression, {"classes": CompiledRoot(self.directory, path_type)})

    def guard(self, actual):
        expected = {name: candidate.probe.digest(payload) for name, payload in self.members.items()}
        return eval(self.guard_expression, {"actual_classes": actual, "expected_classes": expected,
                                           "probe": candidate.probe})

    def test_windows_class_keys_are_canonical_jar_member_names_without_changing_payloads(self):
        self.assertEqual(self.inventory(PureWindowsPath), self.members)

    def test_posix_and_windows_class_inventories_are_identical_on_the_same_actual_fixture_bytes(self):
        self.assertEqual(self.inventory(PurePosixPath), self.inventory(PureWindowsPath))
        self.assertEqual(self.inventory(PurePosixPath), self.members)

    def test_original_exact_hash_guard_still_refuses_extra_missing_or_changed_classes(self):
        self.assertIsNone(self.guard(dict(self.members)))
        changed = dict(self.members)
        changed[next(iter(changed))] = b"changed-synthetic-class"
        missing = dict(self.members)
        missing.pop(next(iter(missing)))
        for actual in (changed, missing, self.members | {"extra.class": b"unexpected"}):
            with self.subTest(kind=len(actual)), self.assertRaisesRegex(ValueError, "Compiler emits"):
                self.guard(actual)


if __name__ == "__main__":
    unittest.main()
