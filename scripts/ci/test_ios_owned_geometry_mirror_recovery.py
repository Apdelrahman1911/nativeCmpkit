# SPDX-License-Identifier: Apache-2.0
"""NEW important mirror587 checks; zero platform/compiler/network executions."""
import ast
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import ios_owned_geometry_fixture_recovery as recovery
import ios_geometry_simulator_source_projection as owned
import ios_popover_geometry_source_projection as geometry

ROOT = Path(__file__).resolve().parents[2]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class OwnedGeometryMirrorRecoveryControls(unittest.TestCase):
    def test_only_complete_current_mirror_roundtrips_and_retains_every_original_assertion(self):
        binding = recovery.MIRROR_BINDING
        current = (ROOT / binding["path"]).read_bytes()
        old = recovery.current_source_before_recovery(binding["path"], current)
        self.assertEqual(binding["before_sha256"], sha(old))
        self.assertEqual(binding["after_sha256"], sha(current))
        def obligations(raw):
            tree = ast.parse(raw)
            return ([n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")],
                    [ast.dump(n, include_attributes=False) for n in ast.walk(tree)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and
                     isinstance(n.func.value, ast.Name) and n.func.value.id == "self" and n.func.attr.startswith("assert")])
        self.assertEqual(obligations(old), obligations(current))
        fragment = binding["after_fragment"].encode()
        displaced = current.replace(fragment, b"", 1) + fragment
        self.assertNotEqual(displaced, current)
        for bad in (old, current[:-1], current + b"\n", displaced, b"", None, bytearray(current)):
            with self.subTest(kind=type(bad).__name__), self.assertRaises(ValueError):
                recovery.current_source_before_recovery(binding["path"], bad)
        self.assertEqual(old, recovery.peel_current_recovery_for_history(binding["path"], current))
        unknown = current + b"\n# synthetic unknown fixture\n"
        self.assertEqual(unknown, recovery.peel_current_recovery_for_history(binding["path"], unknown))

    def test_full_live_mirror_requires_latest_inputs_without_missing_file_or_symlink_waiver(self):
        documents = (geometry._bindings(), owned._document(), recovery._document())
        paths = set(documents[0])
        paths |= set(json.loads(geometry.SPEC_PATH.read_bytes())["added_inputs"])
        for document in documents[1:]:
            paths |= set(document["bindings"]) | set(document["added_inputs"])
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-mirror587-") as directory:
            root = Path(directory)
            for name in paths:
                target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / name).read_bytes())
            self.assertTrue(geometry.validate_current_sources(root))
            target = root / "scripts/ci/ios_geometry_simulator_source_projection.py"
            raw = target.read_bytes(); target.unlink()
            with self.assertRaises(FileNotFoundError): geometry.validate_current_sources(root)
            target.symlink_to(ROOT / target.relative_to(root))
            with self.assertRaises(ValueError): geometry.validate_current_sources(root)
            target.unlink(); target.write_bytes(raw + b"\n")
            with self.assertRaises(ValueError): geometry.validate_current_sources(root)


if __name__ == "__main__":
    unittest.main()
