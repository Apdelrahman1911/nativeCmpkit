# SPDX-License-Identifier: Apache-2.0
"""Essential NEW final659 binding/ingress controls; no accepted-population replay."""
from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import camera_ios_ownership_source_projection as camera
import platform_recovery659_source_projection as newest
import webview_content_policy_source_projection as content_history

ROOT = Path(__file__).resolve().parents[2]
IMAGE_CONTROL = "scripts/ci/test_apple_image_launcher_source_projection.py"
CAMERA4697_GUARD_SHA256 = "3b1d14ca28edcca507a645b301f577ce845161172bd9f28f6d354e5ccc9eebdc"
WEBVIEW4697_GUARD_SHA256 = "cc3f7cb7099e744d08db6273194c6bcf586613521d0c8fae7757d3defa4af878"
WEBVIEW659_GUARD_SHA256 = "bb0b63b32a41667c0c33401f44873bd20426524ece52caaa3cfa41ffd880f60d"
CAMERA651_SPEC_SHA256 = "90844a99910a622024f769dd16ffe504308e1a94324d9192e406cda681e680bd"
WEBVIEW874_SPEC_SHA256 = "c44400087570740d3248704c2165c3222229f2c05ff1a2a3840dbda9aa04b916"


def function(tree, name):
    matches = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(matches) != 1:
        raise AssertionError("One exact top-level source function is required")
    return matches[0]


def copy_fixture(root):
    for name in content_history.fixture_inputs():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())


class PlatformRecovery659SourceProjectionControls(unittest.TestCase):
    def setUp(self):
        def forbidden(*args, **kwargs):
            raise AssertionError("An outer source control cannot execute external processes")
        for name in ("run", "Popen"):
            control = patch.object(subprocess, name, forbidden)
            control.start()
            self.addCleanup(control.stop)

    def test_one_complete_outer_inverse_restores4697_and_rejects_old_partial_displaced_foreign_and_type_drift(self):
        document = newest._document()
        self.assertEqual("4697c3ec65427a12e53645ecffac5e2b52821dd5", document["predecessor"])
        self.assertEqual(20, len(document["bindings"]))
        self.assertEqual(newest.BOUND_PATHS, set(document["bindings"]))
        for name, row in document["bindings"].items():
            raw = (ROOT / name).read_bytes()
            before = newest.current_source_before_platform_recovery659(name, raw)
            self.assertEqual((row["after_sha256"], row["after_bytes"]), (newest.sha(raw), len(raw)), name)
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (newest.sha(before), len(before)), name)
            self.assertIs(before, newest.source_before_platform_recovery659(name, before))
            self.assertEqual(before, newest.peel_platform_recovery659_for_history(name, raw))
            self.assertIs(before, newest.peel_platform_recovery659_for_history(name, before))
            forward = before
            for fragment in row["fragments"]:
                old, new = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual((newest.sha(old), newest.sha(new)),
                                 (fragment["before_fragment_sha256"], fragment["after_fragment_sha256"]))
                self.assertEqual(1, forward.count(old))
                forward = forward.replace(old, new, 1)
            self.assertEqual(raw, forward)
            fragment = row["fragments"][0]["after"].encode()
            displaced = raw.replace(fragment, b"", 1) + fragment
            self.assertNotEqual(raw, displaced)
            foreign = (ROOT / next(path for path in newest.BOUND_PATHS if path != name)).read_bytes()
            for bad in (before, raw[:-1], raw + b"\n", displaced, foreign, b"", b"unknown", None,
                        bytearray(raw), raw.decode(), b"x" * (newest.MAX_SOURCE_BYTES + 1)):
                with self.subTest(relative=name, kind=type(bad).__name__), self.assertRaises(ValueError):
                    newest.current_source_before_platform_recovery659(name, bad)
            unknown = before + b"\n# uncertified source\n"
            self.assertIs(unknown, newest.peel_platform_recovery659_for_history(name, unknown))
            with self.assertRaises(ValueError):
                newest.source_before_platform_recovery659(name, unknown)
        unlisted = b"pass-through never certifies a current source"
        for reader in (newest.source_before_platform_recovery659, newest.current_source_before_platform_recovery659,
                       newest.peel_platform_recovery659_for_history):
            self.assertIs(unlisted, reader("unlisted-source", unlisted))
            with self.assertRaises(ValueError):
                reader(Path("unlisted-source"), unlisted)
        self.assertEqual(CAMERA4697_GUARD_SHA256, document["bindings"][camera.SOURCE_RELATIVE]["before_sha256"])
        self.assertEqual(WEBVIEW4697_GUARD_SHA256, document["bindings"][content_history.SOURCE_RELATIVE]["before_sha256"])
        self.assertEqual(WEBVIEW659_GUARD_SHA256, newest.sha((ROOT / content_history.SOURCE_RELATIVE).read_bytes()))

    def test_nonrecursive_camera_hooks_peel_actual_raw_guards_before_original_validation_without_rewriting_pins(self):
        raw = (ROOT / camera.SOURCE_RELATIVE).read_bytes()
        before = newest.source_before_platform_recovery659(camera.SOURCE_RELATIVE, raw)
        class TransparentOuterHooks(ast.NodeTransformer):
            def visit_ImportFrom(self, node):
                return None if node.module == "platform_recovery659_source_projection" else node
            def visit_Import(self, node):
                return None if ast.unparse(node) == "import platform_recovery659_source_projection as newest" else node
            def visit_Expr(self, node):
                return None if ast.unparse(node) == "newest.validate_current_sources(root)" else self.generic_visit(node)
            def visit_Assign(self, node):
                if (len(node.targets) == 1 and ast.unparse(node.targets[0]) == "payload" and isinstance(node.value, ast.Call) and
                        ast.unparse(node.value.func) in {"peel_platform_recovery659_for_history", "current_source_before_platform_recovery659"}):
                    if [ast.unparse(arg) for arg in node.value.args] != ["relative", "payload"] or node.value.keywords:
                        raise AssertionError("Only the exact binary outer source hook is allowed")
                    return None
                return self.generic_visit(node)
            def visit_Call(self, node):
                node = self.generic_visit(node)
                if ast.unparse(node.func) == "newest.source_before_platform_recovery659":
                    if len(node.args) != 2 or node.keywords or ast.unparse(node.args[0]) != "name":
                        raise AssertionError("Only the exact owning validator source operand changes")
                    return node.args[1]
                return node
            def visit_BinOp(self, node):
                node = self.generic_visit(node)
                if (isinstance(node.op, ast.BitOr) and isinstance(node.right, ast.Call) and
                        ast.unparse(node.right.func) == "newest_fixture_inputs"):
                    if node.right.args or node.right.keywords:
                        raise AssertionError("Only the finite outer fixture union is allowed")
                    return node.left
                return node
        self.assertEqual(ast.dump(ast.parse(before), include_attributes=False),
                         ast.dump(TransparentOuterHooks().visit(ast.parse(raw)), include_attributes=False))
        guard_tree = ast.parse((ROOT / newest.SOURCE_RELATIVE).read_bytes())
        self.assertFalse(any(isinstance(node, (ast.Import, ast.ImportFrom)) and
                             any(name in ast.unparse(node) for name in ("camera_ios_ownership", "webview_content_policy"))
                             for node in ast.walk(guard_tree)))
        prohibited = {"exec", "eval", "compile", "__import__", "run", "Popen", "write_bytes", "write_text"}
        guarded = [node for node in ast.walk(guard_tree) if isinstance(node, ast.Call) and
                   ast.unparse(node.func).rsplit(".", 1)[-1] in prohibited]
        self.assertEqual(["re.compile"], [ast.unparse(node.func) for node in guarded])
        self.assertEqual([r"[0-9a-f]{64}\Z"], [ast.literal_eval(node.args[0]) for node in guarded])
        self.assertTrue(all(len(node.args) == 1 and not node.keywords for node in guarded))
        for name in newest.BOUND_PATHS:
            raw_current = (ROOT / name).read_bytes()
            with patch.object(newest, "current_source_before_platform_recovery659",
                              wraps=newest.current_source_before_platform_recovery659) as raw_ingress:
                content_history.current_source_before_content_policy(name, raw_current)
                raw_ingress.assert_called_once_with(name, raw_current)
        self.assertEqual(CAMERA651_SPEC_SHA256, camera.SPEC_SHA256)
        self.assertEqual(WEBVIEW874_SPEC_SHA256, content_history.SPEC_SHA256)
        self.assertEqual(CAMERA651_SPEC_SHA256, newest.sha((ROOT / camera.SPEC_RELATIVE).read_bytes()))
        self.assertEqual(WEBVIEW874_SPEC_SHA256, newest.sha((ROOT / content_history.SPEC_RELATIVE).read_bytes()))
        with patch.object(newest, "validate_current_sources", wraps=newest.validate_current_sources) as raw_validator:
            self.assertTrue(camera.validate_current_sources(ROOT))
            raw_validator.assert_called_once_with(ROOT)

    def test_raw_finite_inputs_own_guard_singleton_template_and_new_controls_refuse_missing_drift_links_and_old_images(self):
        document = newest._document()
        self.assertEqual(2, len(document["added_inputs"]))
        self.assertNotIn("AGENTS.md", newest.fixture_inputs())
        self.assertTrue(newest.fixture_inputs() <= camera.fixture_inputs())
        self.assertTrue(newest.fixture_inputs() <= content_history.fixture_inputs())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            copy_fixture(root)
            self.assertTrue(newest.validate_current_sources(root))
            self.assertTrue(camera.validate_current_sources(root))
            self.assertTrue(content_history.validate_current_sources(root))
            (root / "AGENTS.md").write_bytes(b"unrelated maintainer bytes\x00\xff")
            self.assertTrue(newest.validate_current_sources(root))
            for name in sorted(newest.fixture_inputs()):
                with self.subTest(owned_input=name):
                    target = root / name
                    raw = target.read_bytes()
                    target.write_bytes(raw + b"\n")
                    with self.assertRaises(ValueError):
                        camera.validate_current_sources(root)
                    target.unlink()
                    with self.assertRaises(FileNotFoundError):
                        camera.validate_current_sources(root)
                    target.symlink_to(ROOT / name)
                    with self.assertRaises(ValueError):
                        camera.validate_current_sources(root)
                    target.unlink()
                    backing = target.with_name(target.name + ".backing")
                    backing.write_bytes(raw)
                    target.hardlink_to(backing)
                    with self.assertRaises(ValueError):
                        camera.validate_current_sources(root)
                    target.unlink()
                    backing.unlink()
                    target.write_bytes(raw)
            for name in sorted(newest.BOUND_PATHS):
                target = root / name
                raw = target.read_bytes()
                target.write_bytes(newest.source_before_platform_recovery659(name, raw))
                with self.assertRaises(ValueError):
                    camera.validate_current_sources(root)
                with self.assertRaises(ValueError):
                    content_history.validate_current_sources(root)
                target.write_bytes(raw)
            guard = root / newest.SOURCE_RELATIVE
            raw_guard = guard.read_bytes()
            needle = ('SPEC_SHA256 = "' + newest.SPEC_SHA256 + '"\n').encode()
            self.assertEqual(1, raw_guard.count(needle))
            normalized = raw_guard.replace(needle, ('SPEC_SHA256 = "' + "0" * 64 + '"\n').encode(), 1)
            self.assertEqual((document["own_guard"]["template_sha256"], document["own_guard"]["bytes"]),
                             (newest.sha(normalized), len(raw_guard)))
            for bad in (raw_guard.replace(needle, needle + needle, 1), raw_guard.replace(needle, b"", 1),
                        raw_guard.replace(needle, ('SPEC_SHA256 = "' + "a" * 64 + '"\n').encode(), 1),
                        raw_guard.replace(b"return True", b"return None", 1)):
                guard.write_bytes(bad)
                with self.assertRaises(ValueError):
                    newest.validate_current_sources(root)
            guard.write_bytes(raw_guard)
            self.assertTrue(content_history.validate_current_sources(root))

    def test_manifest_exact_schema_and_raw_image_fixture_operand_do_not_double_peel_or_certify_pass_through(self):
        raw = (ROOT / newest.SPEC_RELATIVE).read_bytes()
        document = newest._document()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            path.write_bytes(raw + b"\n")
            with patch.object(newest, "SPEC_PATH", path), self.assertRaises(ValueError):
                newest._document()
            for candidate in (b'{"schema_version":1,"schema_version":1}', b'{"schema_version":NaN}', b"{}", b"[]"):
                path.write_bytes(candidate)
                with patch.object(newest, "SPEC_PATH", path), patch.object(newest, "SPEC_SHA256", newest.sha(candidate)), self.assertRaises(ValueError):
                    newest._document()
            mutations = (
                lambda d: d.update(schema_version=True),
                lambda d: d.update(scope="native acceptance"),
                lambda d: d.update(predecessor="unknown"),
                lambda d: d["bindings"].pop(next(iter(d["bindings"]))),
                lambda d: d["added_inputs"].update({"foreign.py": "a" * 64}),
                lambda d: d["unchanged_inputs"].update({"AGENTS.md": "a" * 64}),
                lambda d: d["own_guard"].update(bytes=True),
                lambda d: d["own_guard"].update(template_sha256="A" * 64),
                lambda d: d["bindings"][camera.SOURCE_RELATIVE].update(after_bytes=True),
                lambda d: d["bindings"][camera.SOURCE_RELATIVE].update(after_sha256="A" * 64),
            )
            for mutate in mutations:
                bad = deepcopy(document)
                mutate(bad)
                candidate = json.dumps(bad).encode()
                path.write_bytes(candidate)
                with patch.object(newest, "SPEC_PATH", path), patch.object(newest, "SPEC_SHA256", newest.sha(candidate)), self.assertRaises(ValueError):
                    newest._document()
        name = camera.SOURCE_RELATIVE
        bad = deepcopy(document)
        bad["bindings"][name]["fragments"][0]["after_fragment_sha256"] = "a" * 64
        with patch.object(newest, "_document", return_value=bad), self.assertRaises(ValueError):
            newest.source_before_platform_recovery659(name, (ROOT / name).read_bytes())
        image = (ROOT / IMAGE_CONTROL).read_bytes()
        old_image = newest.source_before_platform_recovery659(IMAGE_CONTROL, image)
        self.assertEqual(old_image, content_history._current_tooling656_control_source(IMAGE_CONTROL, image))
        self.assertEqual("9d7870ffcd1cf584c7e2914143d93066defba889638df05f0f91781ab5dd2fa9", newest.sha(old_image))
        with self.assertRaises(ValueError):
            content_history._current_tooling656_control_source(IMAGE_CONTROL, old_image)
        with self.assertRaises(ValueError):
            content_history.current_source_before_content_policy(IMAGE_CONTROL, old_image)
        with patch.object(newest, "validate_current_sources", wraps=newest.validate_current_sources) as raw_gate, \
                patch.object(content_history, "_current_tooling656_control_source",
                             wraps=content_history._current_tooling656_control_source) as fixture_operand:
            self.assertTrue(content_history.validate_current_sources(ROOT))
            raw_gate.assert_called_once_with(ROOT)
            actual = [call for call in fixture_operand.call_args_list if call.args[0] == IMAGE_CONTROL]
            self.assertEqual(1, len(actual))
            self.assertEqual((IMAGE_CONTROL, image), actual[0].args)
        owner = function(ast.parse((ROOT / content_history.SOURCE_RELATIVE).read_bytes()), "validate_current_sources")
        operands = [node for node in ast.walk(owner) if isinstance(node, ast.Call) and
                    ast.unparse(node.func) == "_current_tooling656_control_source"]
        self.assertEqual(1, len(operands))
        self.assertEqual("_ordinary_bytes(root, name)[0]", ast.unparse(operands[0].args[1]))


if __name__ == "__main__":
    unittest.main()
