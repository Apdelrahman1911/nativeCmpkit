# SPDX-License-Identifier: Apache-2.0
"""Owning workflow/history controls; no native, compiler or network execution."""
import ast
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import ios_geometry_simulator_source_projection as history
import ios_owned_geometry_fixture_recovery as recovery
import android_external328_source_projection as bridge

ROOT = Path(__file__).resolve().parents[2]
PATHS = {
    ".github/workflows/gradle.yml",
    "scripts/ci/android_external328_source_projection.py",
    "scripts/ci/ios_popover_geometry_source_projection.py",
    "scripts/ci/test_ios_popover_geometry.py",
    "scripts/ci/test_camera_tooling562_source_projection.py",
    "scripts/ci/test_camera_tooling566_source_projection.py",
    "scripts/ci/test_camera_home_baseline_source_projection.py",
    "scripts/ci/test_camera_home571_fixture_recovery.py",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class OwnedGeometrySourceControls(unittest.TestCase):
    def test_eight_complete_images_and_every_unique_fragment_roundtrip(self):
        self.assertEqual(PATHS, set(history._bindings()))
        for name, binding in history._bindings().items():
            actual = (ROOT / name).read_bytes()
            current = recovery.current_source_before_recovery(name, actual)
            old = history.current_source_before_owned_geometry(name, actual)
            self.assertEqual(binding["before_sha256"], sha(old), name)
            self.assertEqual(binding["before_bytes"], len(old), name)
            forward = old
            for fragment in binding["fragments"]:
                self.assertEqual(1, forward.count(fragment["before"].encode()))
                forward = forward.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
            self.assertEqual(current, forward)
            self.assertEqual(old, history.source_before_owned_geometry(name, old))

    def test_old_partial_displaced_nonordinary_or_unknown_images_cannot_be_current(self):
        for name, binding in history._bindings().items():
            current = (ROOT / name).read_bytes()
            old = history.source_before_owned_geometry(name, current)
            fragment = binding["fragments"][0]["after"].encode()
            displaced = current.replace(fragment, b"", 1) + fragment
            self.assertNotEqual(current, displaced)
            for bad in (old, current[:-1], current + b"\n", displaced, b"", None, bytearray(current)):
                with self.subTest(name=name, kind=type(bad).__name__), self.assertRaises(ValueError):
                    history.current_source_before_owned_geometry(name, bad)

    def test_outer_raw_ingress_once_and_dated_camera_pins_still_own_ancestors(self):
        name = "scripts/ci/android_external328_source_projection.py"
        current = (ROOT / name).read_bytes()
        original = history.current_source_before_owned_geometry(name, current)
        with patch.object(history, "current_source_before_owned_geometry", wraps=history.current_source_before_owned_geometry) as raw:
            ancestor = bridge.current_source_for_history(name, current)
            raw.assert_called_once_with(name, current)
        self.assertNotEqual(current, ancestor)
        self.assertEqual(ancestor, bridge.source_before_android_external328(name, original))
        with self.assertRaises(ValueError):
            bridge.current_source_for_history(name, original)
        self.assertEqual(original, history.peel_current_owned_geometry_for_older_history(name, original))
        unknown = current + b"\n# synthetic unknown source\n"
        self.assertEqual(unknown, history.peel_current_owned_geometry_for_older_history(name, unknown))

    def test_original_assertions_and_declared_method_names_are_not_weakened(self):
        class QualificationOnly(ast.NodeTransformer):
            def visit_Call(self, node):
                node = self.generic_visit(node)
                if (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and
                        node.func.value.id == "owned_history" and node.func.attr == "current_source_before_owned_geometry" and
                        len(node.args) == 2 and not node.keywords):
                    return node.args[1]  # Only exact source-stage qualification changes the operand.
                return node
        for name in PATHS:
            if not Path(name).name.startswith("test_"):
                continue
            current = (ROOT / name).read_bytes()
            old = history.source_before_owned_geometry(name, current)
            def obligations(raw):
                raw = recovery.peel_current_recovery_for_history(name, raw)
                tree = QualificationOnly().visit(ast.parse(raw))
                methods = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")]
                assertions = [ast.dump(node, include_attributes=False) for node in ast.walk(tree)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
                    isinstance(node.func.value, ast.Name) and node.func.value.id == "self" and node.func.attr.startswith("assert")]
                return methods, assertions
            self.assertEqual(obligations(old), obligations(current), name)

    def test_live_geometry_admission_checks_new_bytes_not_an_old_fixture_view(self):
        document = history._document()
        paths = set(document["bindings"]) | set(document["added_inputs"])
        latest = recovery._document()
        paths |= set(latest["bindings"]) | set(latest["added_inputs"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in paths:
                target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / name).read_bytes())
            self.assertTrue(history.validate_current_sources(root))
            for name in (".github/workflows/gradle.yml", "scripts/ci/ios_geometry_simulator.py"):
                target = root / name; original = target.read_bytes()
                target.write_bytes(original + b"\n")
                with self.assertRaises(ValueError): history.validate_current_sources(root)
                target.unlink(); target.symlink_to(ROOT / name)
                with self.assertRaises(ValueError): history.validate_current_sources(root)
                target.unlink(); target.write_bytes(original)

    def test_only_two_focuses_prepare_before_boot_and_always_dispose_known_owner(self):
        source = (ROOT / ".github/workflows/gradle.yml").read_text()
        runtime = source.split("      - name: Record actual architecture, compiler, SDK and selected simulator\n", 1)[1].split("      - name: Record exact configured dependency inputs", 1)[0]
        self.assertIn('if [[ "$TEST_FOCUS" == ui-native-popover-portrait-traits || "$TEST_FOCUS" == ui-native-popover-os-rotation ]]; then', runtime)
        self.assertLess(runtime.index("--output build/ci-runtime/selection.json"), runtime.index("ios_geometry_simulator.py prepare"))
        geometry = runtime.split('if [[ "$TEST_FOCUS"', 1)[1].split("            else\n", 1)[0]
        self.assertNotIn("simctl boot", geometry)
        self.assertIn('args+=(--apple --simulator "$device" --require-booted)', runtime)
        self.assertIn('--require-clean --android-platform android-37.0', runtime)
        self.assertIn('scripts/ci/runtime_context.py "${args[@]}" --output build/ci-runtime/actual.json', runtime)
        cleanup = source.split("      - name: Dispose only the acknowledged owned geometry simulator\n", 1)[1].split("      - name: Show bounded failure diagnostics", 1)[0]
        self.assertIn("always() && matrix.suite == 'ios'", cleanup)
        for focus in ("ui-native-popover-portrait-traits", "ui-native-popover-os-rotation"):
            self.assertIn("matrix.test-focus == '" + focus + "'", cleanup)
        self.assertIn('ios_geometry_simulator.py cleanup --focus "$TEST_FOCUS"', cleanup)
        self.assertNotIn("continue-on-error", cleanup)
        self.assertNotIn("simctl erase", source)
        self.assertLess(source.index("Dispose only the acknowledged owned geometry simulator"), source.index("Keep receipts and actual selected-task XML only"))

    def test_native_compiler_and_old_manifest_inputs_are_exactly_unchanged(self):
        document = history._document()
        self.assertGreaterEqual(len(document["unchanged_native_compiler_inputs"]), 7)
        self.assertEqual(3, len(document["unchanged_dated_manifests"]))
        from ios_ui_split664_source_projection import current_source_before_ui_split664
        for name, expected in (document["unchanged_native_compiler_inputs"] | document["unchanged_dated_manifests"]).items():
            current = (ROOT / name).read_bytes()
            if name == "calf-ui/build.gradle.kts":
                current = current_source_before_ui_split664(name, current)
            self.assertEqual(expected, sha(current), name)
        self.assertTrue(all(name not in PATHS for name in document["unchanged_native_compiler_inputs"]))

    def test_changed_or_aliased_manifest_fails_before_projection(self):
        original = history.SPEC_PATH.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            with patch.object(history, "SPEC_PATH", path):
                for bad in (original + b"\n", b"{}", b"", b"x" * (history.MAX_SPEC_BYTES + 1)):
                    path.write_bytes(bad)
                    with self.assertRaises(ValueError): history._bindings()
                path.unlink(); path.symlink_to(ROOT / "scripts/ci/ios_geometry_simulator.py")
                with self.assertRaises(ValueError): history._bindings()
                path.unlink(); backing = path.with_name("backing.json"); backing.write_bytes(original)
                path.hardlink_to(backing)
                with self.assertRaises(ValueError): history._bindings()


if __name__ == "__main__":
    unittest.main()
