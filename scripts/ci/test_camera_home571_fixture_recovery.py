# SPDX-License-Identifier: Apache-2.0
"""Only affected HOME source-stage admission; zero library/native executions."""
import ast
import hashlib
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

import test_camera_home_baseline_source_projection as fixture
import camera_home_baseline_source_projection as home
import camera_tooling566_source_projection as latest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = "scripts/ci/test_camera_home_baseline_source_projection.py"
SPEC = ROOT / "scripts/ci/fixtures/camera-home571-fixture-recovery.json"
SPEC_SHA256 = "681d4eb39370cfff45de265f9baf0913e9e60f04a29f3a331e6fe1b61de9923b"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def original_fixture(payload):
    info = SPEC.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= 256 * 1024:
        raise ValueError("One ordinary bounded HOME571 fixture manifest is required")
    raw = SPEC.read_bytes()
    if sha(raw) != SPEC_SHA256:
        raise ValueError("The exact HOME571 fixture manifest changed")
    binding = json.loads(raw)["bindings"][FIXTURE]
    if type(payload) is not bytes or sha(payload) != binding["after_sha256"]:
        raise ValueError("Only the exact current HOME571 fixture image is required")
    original = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if sha(before) != fragment["before_fragment_sha256"] or sha(after) != fragment["after_fragment_sha256"] or original.count(after) != 1:
            raise ValueError("Exact unique HOME571 inverse fragments are required")
        original = original.replace(after, before, 1)
    if sha(original) != binding["before_sha256"]:
        raise ValueError("The complete original HOME571 fixture must be restored")
    forward = original
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique HOME571 forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("HOME571 round trip differs from actual current fixture bytes")
    return original


class Home571FixtureRecoveryControls(unittest.TestCase):
    def test_complete_original_fixture_and_every_assertion_remain_bound(self):
        current = (ROOT / FIXTURE).read_bytes()
        old = original_fixture(current)
        def assertions(raw):
            return [ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(raw))
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and
                    isinstance(n.func.value, ast.Name) and n.func.value.id == "self" and
                    n.func.attr.startswith("assert")]
        self.assertEqual(assertions(old), assertions(current))
        for raw in (old, current):
            body = next(n for n in ast.parse(raw).body if isinstance(n, ast.ClassDef) and n.name == "HomeBaselineHistoryTests")
            self.assertEqual(8, sum(isinstance(n, ast.FunctionDef) and n.name.startswith("test_") for n in body.body))
        self.assertEqual("b968373d8de34a53525efd291055ad61f8d034a17236f663d8c58ba4c0716dcb", sha(home.SPEC_PATH.read_bytes()))

    def test_only_three_changed_current_files_precede_the_unchanged_six_home_stage_pins(self):
        changed = set(latest._bindings()) & fixture.OWNING
        self.assertEqual({"scripts/ci/android_external328_source_projection.py",
                          "scripts/ci/camera_boot_busy_source_projection.py",
                          "scripts/ci/test_android_camera_boot_busy.py"}, changed)
        for relative, binding in home._bindings().items():
            actual = (ROOT / relative).read_bytes()
            stage = fixture.preserved_home_stage(relative, actual)
            self.assertEqual(binding["after_sha256"], sha(stage), relative)
            self.assertEqual(relative in changed, stage != actual)
            self.assertEqual(binding["before_sha256"], sha(home.current_source_before_home_baseline(relative, stage)))
            if relative in changed:
                for bad in (stage, actual[:-1], actual + b"\n", bytearray(actual), None):
                    with self.subTest(relative=relative), self.assertRaises(ValueError):
                        fixture.preserved_home_stage(relative, bad)

    def test_old_partial_unknown_and_displaced_fixture_images_cannot_admit(self):
        current = (ROOT / FIXTURE).read_bytes()
        old = original_fixture(current)
        for bad in (old, current[:-1], current + b"\n", b"", None, bytearray(current)):
            with self.subTest(kind=type(bad).__name__), self.assertRaises(ValueError):
                original_fixture(bad)
        source = (ROOT / FIXTURE).read_text()
        function = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "preserved_home_stage")
        calls = [n.func.id for n in ast.walk(function) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        self.assertEqual(["current_source_before_tooling566"], calls)

    def test_new_manifest_drift_symlink_hardlink_and_empty_receipts_refuse(self):
        current = (ROOT / FIXTURE).read_bytes()
        raw = SPEC.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            with patch.dict(original_fixture.__globals__, {"SPEC": path}):
                for bad in (raw + b"\n", b"{}", b"", b"x" * (256 * 1024 + 1)):
                    path.write_bytes(bad)
                    with self.assertRaises(ValueError):
                        original_fixture(current)
                path.unlink(); path.symlink_to(ROOT / FIXTURE)
                with self.assertRaises(ValueError):
                    original_fixture(current)
                path.unlink()
                backing = path.with_name("backing.json"); backing.write_bytes(raw)
                path.hardlink_to(backing)
                with self.assertRaises(ValueError):
                    original_fixture(current)


if __name__ == "__main__":
    unittest.main()
