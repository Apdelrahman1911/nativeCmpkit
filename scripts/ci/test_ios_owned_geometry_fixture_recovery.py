# SPDX-License-Identifier: Apache-2.0
"""NEW important shared-fixture controls; no platform, compiler or network."""
import ast
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import ios_owned_geometry_fixture_recovery as recovery
import ios_geometry_simulator_source_projection as owned

ROOT = Path(__file__).resolve().parents[2]
HOME = "scripts/ci/test_camera_home_baseline_source_projection.py"
PATHS = {HOME, "scripts/ci/test_camera_home571_fixture_recovery.py",
         "scripts/ci/ios_geometry_simulator_source_projection.py",
         "scripts/ci/test_ios_geometry_simulator_source_projection.py"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class SharedGeometryFixtureRecoveryControls(unittest.TestCase):
    def test_four_complete_owning_images_roundtrip_without_any_dated_pin_change(self):
        document = recovery._document()
        self.assertEqual(PATHS, set(document["bindings"]))
        for name, binding in document["bindings"].items():
            actual = (ROOT / name).read_bytes()
            previous = recovery.current_source_before_recovery(name, actual)
            self.assertEqual(binding["before_sha256"], sha(previous), name)
            self.assertEqual(binding["before_bytes"], len(previous), name)
            forward = previous
            for fragment in binding["fragments"]:
                self.assertEqual(1, forward.count(fragment["before"].encode()))
                forward = forward.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
            self.assertEqual(actual, forward)
        for name, digest in document["unchanged_inputs"].items():
            self.assertEqual(digest, sha((ROOT / name).read_bytes()), name)

    def test_old_partial_displaced_unknown_and_nonordinary_images_never_admit(self):
        for name, binding in recovery._document()["bindings"].items():
            current = (ROOT / name).read_bytes()
            old = recovery.source_before_recovery(name, current)
            fragment = binding["fragments"][0]["after"].encode()
            displaced = current.replace(fragment, b"", 1) + fragment
            self.assertNotEqual(current, displaced)
            for bad in (old, current[:-1], current + b"\n", displaced, b"", None, bytearray(current)):
                with self.subTest(name=name, kind=type(bad).__name__), self.assertRaises(ValueError):
                    recovery.current_source_before_recovery(name, bad)
            self.assertEqual(old, recovery.peel_current_recovery_for_history(name, current))
            self.assertEqual(old, recovery.peel_current_recovery_for_history(name, old))
            unknown = current + b"\n# synthetic unreviewed fixture\n"
            self.assertEqual(unknown, recovery.peel_current_recovery_for_history(name, unknown))

    def test_original_home_assertions_only_qualify_exact_workflow_stage_and_keep_all_methods(self):
        current = (ROOT / HOME).read_bytes()
        original = recovery.source_before_recovery(HOME, current)
        class QualificationOnly(ast.NodeTransformer):
            def visit_Call(self, node):
                node = self.generic_visit(node)
                if (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and
                        node.func.value.id == "owned_history" and node.func.attr == "current_source_before_owned_geometry" and
                        len(node.args) == 2 and not node.keywords):
                    return node.args[1]
                return node
        def obligations(raw):
            tree = QualificationOnly().visit(ast.parse(raw))
            return ([node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")],
                    [ast.dump(node, include_attributes=False) for node in ast.walk(tree)
                     if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
                     isinstance(node.func.value, ast.Name) and node.func.value.id == "self" and node.func.attr.startswith("assert")])
        self.assertEqual(obligations(original), obligations(current))
        self.assertEqual(8, len(obligations(current)[0]))
        workflow = ".github/workflows/gradle.yml"
        stage = owned.current_source_before_owned_geometry(workflow, (ROOT / workflow).read_bytes())
        self.assertEqual("3d5d2ea0313055366bf6bc83550f7e2f40c50438c450508588db778fb6bb75f7", sha(stage))
        with self.assertRaises(ValueError):
            owned.current_source_before_owned_geometry(workflow, (ROOT / workflow).read_bytes() + b"\n")

    def test_live_raw_source_and_manifest_drift_or_aliases_refuse_before_historical_admission(self):
        document = recovery._document()
        paths = set(document["bindings"]) | set(document["added_inputs"])
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-fixture581-") as directory:
            root = Path(directory)
            for name in paths:
                target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / name).read_bytes())
            self.assertTrue(recovery.validate_current_sources(root))
            target = root / HOME
            target.write_bytes(recovery.source_before_recovery(HOME, target.read_bytes()))
            with self.assertRaises(ValueError): recovery.validate_current_sources(root)
            target.unlink(); target.symlink_to(ROOT / HOME)
            with self.assertRaises(ValueError): recovery.validate_current_sources(root)
            raw = recovery.SPEC_PATH.read_bytes()
            manifest = root / "manifest.json"
            with patch.object(recovery, "SPEC_PATH", manifest):
                for bad in (raw + b"\n", b"{}", b"", b"x" * (recovery.MAX_SPEC_BYTES + 1)):
                    manifest.write_bytes(bad)
                    with self.assertRaises(ValueError): recovery._document()
                manifest.unlink(); manifest.symlink_to(ROOT / HOME)
                with self.assertRaises(ValueError): recovery._document()
                manifest.unlink(); backing = root / "backing.json"; backing.write_bytes(raw)
                manifest.hardlink_to(backing)
                with self.assertRaises(ValueError): recovery._document()


if __name__ == "__main__":
    unittest.main()
