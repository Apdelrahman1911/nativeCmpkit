# SPDX-License-Identifier: Apache-2.0
"""NEW finite source-custody controls only; never execute reconstructed/native code."""
import ast
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import android_external328_source_projection as bridge
import camera_home_affinity_source_projection as camera
import ios_ui_related_source_projection as ui
import macos_share_missing_source_projection as history
import webview_content_policy_source_projection as content_history

ROOT = Path(__file__).resolve().parents[2]
GUARD = "scripts/ci/macos_share_missing_source_projection.py"
GUARD_SHA256 = "0b1f39f890df7cdb68db70d027b23340c2da1dd234b4387f68f2c8be41d8d3ad"
SHARED = (".github/workflows/gradle.yml", "scripts/ci/library_tests.py", "scripts/ci/workflow_matrix.py")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class MissingShare630SourceControls(unittest.TestCase):
    def test_exact_six_path_inverse_roundtrip_and_one_newest_raw_ingress(self):
        document = history._document()
        self.assertEqual(6, len(document["bindings"]))
        self.assertEqual(GUARD_SHA256, sha(content_history.source_before_content_policy(GUARD, (ROOT / GUARD).read_bytes())))
        for name, binding in document["bindings"].items():
            raw_current = (ROOT / name).read_bytes()
            current = content_history.source_before_content_policy(name, raw_current)
            old = history.current_source_before_share_missing_ci(name, raw_current)
            self.assertEqual((binding["before_sha256"], binding["before_bytes"]), (sha(old), len(old)))
            self.assertIs(old, history.source_before_share_missing_ci(name, old))
            self.assertIs(old, history.peel_share_missing_ci_for_history(name, old))
            forward = old
            for fragment in binding["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(fragment["before_fragment_sha256"], sha(before))
                self.assertEqual(fragment["after_fragment_sha256"], sha(after))
                self.assertEqual(1, forward.count(before)); forward = forward.replace(before, after, 1)
            self.assertEqual(current, forward)
        for name in SHARED:
            current = (ROOT / name).read_bytes()
            with patch.object(history, "current_source_before_share_missing_ci",
                              wraps=history.current_source_before_share_missing_ci) as raw:
                self.assertIsInstance(bridge.current_source_for_history(name, current), bytes)
                raw.assert_called_once_with(name, current)

    def test_prior_partial_unknown_displaced_foreign_and_identity_domains_are_not_current(self):
        for name, binding in history._document()["bindings"].items():
            current = (ROOT / name).read_bytes(); old = history.source_before_share_missing_ci(name, current)
            fragment = binding["fragments"][0]["after"].encode()
            displaced = current.replace(fragment, b"", 1) + fragment
            self.assertNotEqual(current, displaced)
            for bad in (old, current[:-1], current + b"\n", displaced,
                        (ROOT / next(other for other in history.BOUND_PATHS if other != name)).read_bytes(),
                        b"", None, current.decode(), bytearray(current), b"x" * (history.MAX_SOURCE_BYTES + 1)):
                with self.subTest(name=name, kind=type(bad).__name__), self.assertRaises(ValueError):
                    history.current_source_before_share_missing_ci(name, bad)
            unknown = old + b"\n# unreviewed synthetic ancestor\n"
            self.assertIs(unknown, history.peel_share_missing_ci_for_history(name, unknown))
            with self.assertRaises(ValueError): history.source_before_share_missing_ci(name, unknown)
            if name in SHARED:
                with patch.object(camera, "_bindings", side_effect=AssertionError("Invalid newest source crossed ingress")) as older:
                    with self.assertRaises(ValueError): bridge.current_source_for_history(name, old)
                    older.assert_not_called()
        for reader in (history.source_before_share_missing_ci, history.current_source_before_share_missing_ci,
                       history.peel_share_missing_ci_for_history):
            raw = b"unlisted bytes are not certified"
            self.assertIs(raw, reader("unlisted", raw))
            with self.assertRaises(ValueError): reader(Path("unlisted"), raw)

    def test_owning_validator_fixture_union_exact_manifest_and_unchanged_pins_are_required(self):
        from test_ios_ui_related_source_projection import fixture_inputs
        document = history._document()
        self.assertTrue(history.validate_current_sources(ROOT))
        self.assertEqual(history.ADDED_PATHS, set(document["added_inputs"]))
        self.assertEqual("5511b49eb4e164735508ccb596013a7ac59a3dadfe8adf2ce2acac710a2393f8", ui.SPEC_SHA256)
        self.assertEqual("175c69071fa0bf8bbf106b6cc127ae6cd90344512d70f960b5447a4d2b9dc3c4",
                         sha((ROOT / "scripts/ci/ios_owned_geometry_fixture_recovery.py").read_bytes()))
        with tempfile.TemporaryDirectory(prefix="share630-fixture-only-") as temporary:
            root = Path(temporary)
            for name in fixture_inputs():
                target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / name).read_bytes())
            self.assertTrue(ui.validate_current_sources(root))
            name = "scripts/ci/macos_share_missing_ci.py"; target = root / name; original = target.read_bytes()
            target.unlink()
            with self.assertRaises(FileNotFoundError): ui.validate_current_sources(root)
            target.symlink_to(ROOT / name)
            with self.assertRaises(ValueError): ui.validate_current_sources(root)
            target.unlink(); target.write_bytes(original)
            name = SHARED[1]; target = root / name; original = target.read_bytes()
            target.write_bytes(history.source_before_share_missing_ci(name, original))
            with self.assertRaises(ValueError): ui.validate_current_sources(root)
        raw = history.SPEC_PATH.read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "manifest.json"
            with patch.object(history, "SPEC_PATH", target):
                target.write_bytes(raw + b"\n")
                with self.assertRaises(ValueError): history._document()
                target.unlink(); target.symlink_to(ROOT / history.SPEC_RELATIVE)
                with self.assertRaises(ValueError): history._document()
                target.unlink(); backing = target.with_name("backing.json"); backing.write_bytes(raw); target.hardlink_to(backing)
                with self.assertRaises(ValueError): history._document()

    def test_only_transparent_ui_history_hooks_and_narrow_fixture_operands_change(self):
        name = "scripts/ci/ios_ui_related_source_projection.py"; current = (ROOT / name).read_bytes()
        old = history.source_before_share_missing_ci(name, current)
        class TransparentShareHooks(ast.NodeTransformer):
            def visit_ImportFrom(self, node):
                return None if node.module == "macos_share_missing_source_projection" else node
            def visit_Import(self, node):
                return None if ast.unparse(node) == "import macos_share_missing_source_projection as share_history" else node
            def visit_Expr(self, node):
                return None if ast.unparse(node) == "share_history.validate_current_sources(root)" else self.generic_visit(node)
            def visit_Assign(self, node):
                if (len(node.targets) == 1 and ast.unparse(node.targets[0]) == "payload" and
                        isinstance(node.value, ast.Call) and ast.unparse(node.value.func) in {
                            "peel_share_missing_ci_for_history", "current_source_before_share_missing_ci"}):
                    if [ast.unparse(arg) for arg in node.value.args] != ["relative", "payload"] or node.value.keywords:
                        raise AssertionError("Only exact binary source ingress hooks are allowed")
                    return None
                return self.generic_visit(node)
            def visit_Call(self, node):
                node = self.generic_visit(node)
                if ast.unparse(node.func) == "share_history.source_before_share_missing_ci":
                    if len(node.args) != 2 or node.keywords or ast.unparse(node.args[0]) != "name":
                        raise AssertionError("Only the owning current hash operand changes")
                    return node.args[1]
                return node
        self.assertEqual(ast.dump(ast.parse(old), include_attributes=False),
                         ast.dump(TransparentShareHooks().visit(ast.parse(current)), include_attributes=False))
        affected = {
            "scripts/ci/test_ios_ui_related_source_projection.py": {
                "fixture_inputs", "test_complete_ui_inverses_restore_all_exact_parent_images_and_forward_bytes",
                "test_retained_image_calendar_assertions_and_all_dated_pins_have_exact_ancestor_operands"},
            "scripts/ci/test_calendar_share_selector_source_projection.py": {
                "test_owning_validator_requires_all_four_added_inputs_and_ordinary_current_images"},
        }
        for name, changed in affected.items():
            current = content_history.source_before_content_policy(name, (ROOT / name).read_bytes())
            old = history.source_before_share_missing_ci(name, current)
            before = {node.name: node for node in ast.walk(ast.parse(old)) if isinstance(node, ast.FunctionDef)}
            after = {node.name: node for node in ast.walk(ast.parse(current)) if isinstance(node, ast.FunctionDef)}
            self.assertEqual(set(before), set(after))
            for method in set(before) - changed:
                self.assertEqual(ast.dump(before[method], include_attributes=False), ast.dump(after[method], include_attributes=False))
            for method in changed:
                def assertions(node):
                    return [child.func.attr for child in ast.walk(node) if isinstance(child, ast.Call) and
                            isinstance(child.func, ast.Attribute) and child.func.attr.startswith("assert")]
                self.assertEqual(assertions(before[method]), assertions(after[method]))


if __name__ == "__main__":
    unittest.main()
