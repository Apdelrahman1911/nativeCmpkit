# SPDX-License-Identifier: Apache-2.0
"""Important CI491 source-stage regressions, not Android/library executions."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import camera_handoff_fixture_source_projection as older
import camera_recents_fixture_source_projection as recovery
import camera_recents_source_projection as recents

ROOT = Path(__file__).resolve().parents[2]
PATHS = {
    "scripts/ci/camera_recents_source_projection.py",
    "scripts/ci/test_android_camera_boot_handoff.py",
    "scripts/ci/test_android_external337_fixture_recovery.py",
    "scripts/ci/test_camera_handoff_fixture_recovery.py",
}
OLD_SPECS = {
    "camera-boot-handoff-source-inverse.json": "525f7f43222f92ab5730d0154e817dbfc60858e21b1daaa60d5203d954535367",
    "camera-handoff-fixture-source-inverse.json": "29da5ee28cd1aa1c1859c076895c0d62080743d2ab4bd447983dddd15684b565",
    "camera-recents-observation-source-inverse.json": "0329eb385d26e9ef90e6c3f92604672e1e76215c9513bbf88c06498eb5f1e028",
}


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


class CameraRecentsFixtureRecoveryControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = recovery.SPEC_PATH.read_bytes()
        cls.bindings = recovery._bindings()
        cls.current = {relative: (ROOT / relative).read_bytes() for relative in PATHS}

    @classmethod
    def tearDownClass(cls):
        if recovery.SPEC_PATH.read_bytes() != cls.spec or any(
                (ROOT / relative).read_bytes() != payload for relative, payload in cls.current.items()):
            raise AssertionError("Exact CI491 fixture source or manifest changed during controls")

    def test_four_paths_eight_fragments_retain_every_original_manifest_and_pin(self):
        document = json.loads(self.spec)
        self.assertEqual("d63e57f1d3ac7b0a297a1d39f2641292fea71bd3", document["before_revision"])
        self.assertEqual(PATHS, set(self.bindings))
        self.assertEqual(8, sum(len(binding["fragments"]) for binding in self.bindings.values()))
        self.assertEqual(recovery.SPEC_SHA256, sha(self.spec))
        for name, expected in OLD_SPECS.items():
            self.assertEqual(expected, sha((ROOT / "scripts/ci/fixtures" / name).read_bytes()))
        for relative, current in self.current.items():
            before = recovery.source_before_recents_fixture(relative, current)
            def pins(payload):
                source = payload.decode()
                return {ast.get_source_segment(source, node) for node in ast.parse(source).body
                        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and
                           "SHA256" in target.id for target in node.targets)}
            self.assertEqual(pins(before), pins(current), relative)
        self.assertFalse(any(path.startswith("calf-") for path in self.bindings))

    def test_exact_current_inverse_and_forward_composition_keep_older_stage_separate(self):
        for relative, binding in self.bindings.items():
            current = self.current[relative]
            previous = recovery.current_source_before_recents_fixture(relative, current)
            self.assertEqual(binding["after_sha256"], sha(current))
            self.assertEqual(binding["before_sha256"], sha(previous))
            self.assertEqual(binding["before_bytes"], len(previous))
            self.assertEqual(previous, recents.current_source_before_recents_observation(relative, current))
            self.assertIs(previous, recovery.source_before_recents_fixture(relative, previous))
            forward = previous
            for fragment in binding["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(fragment["before_fragment_sha256"], sha(before))
                self.assertEqual(fragment["after_fragment_sha256"], sha(after))
                self.assertEqual(1, forward.count(before))
                forward = forward.replace(before, after, 1)
            self.assertEqual(current, forward)
        relative = "scripts/ci/test_android_external337_fixture_recovery.py"
        oldest = older.current_source_before_handoff_fixture(relative, self.current[relative])
        original = older._bindings()[relative]["before_sha256"]
        self.assertEqual([original], self.bindings[relative]["historical_composition_sha256"])
        self.assertEqual(original, sha(oldest))
        self.assertIs(oldest, recovery.source_before_recents_fixture(relative, oldest))
        self.assertEqual(oldest, older.source_before_handoff_fixture(relative, oldest))
        with self.assertRaises(ValueError):
            recovery.current_source_before_recents_fixture(relative, oldest)

    def test_old_drifting_wrong_type_or_tampered_source_never_satisfies_current_admission(self):
        for relative, current in self.current.items():
            previous = recovery.source_before_recents_fixture(relative, current)
            for payload in (previous, current + b"\n", current[:-1], b"foreign", b"", None, bytearray(current)):
                with self.subTest(relative=relative, kind=type(payload).__name__), self.assertRaises(ValueError):
                    recovery.current_source_before_recents_fixture(relative, payload)
            for identity in (None, Path(relative), [], 1):
                with self.assertRaises(ValueError):
                    recovery.current_source_before_recents_fixture(identity, current)
            mutated = copy.deepcopy(self.bindings)
            mutated[relative]["fragments"][0]["after_fragment_sha256"] = "0" * 64
            with patch.object(recovery, "_bindings", return_value=mutated), self.assertRaises(ValueError):
                recovery.source_before_recents_fixture(relative, current)
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-recents-fixture-manifest-") as name:
            path = Path(name) / "manifest.json"
            for raw in (self.spec + b"\n", b"{}", b"", b"x" * (recovery.MAX_SPEC_BYTES + 1)):
                path.write_bytes(raw)
                with patch.object(recovery, "SPEC_PATH", path), self.assertRaises(ValueError):
                    recovery._bindings()
            path.write_bytes(self.spec)
            link = path.with_name("linked.json")
            link.symlink_to(path)
            with patch.object(recovery, "SPEC_PATH", link), self.assertRaises(ValueError):
                recovery._bindings()
            link.unlink()
            link.hardlink_to(path)
            with patch.object(recovery, "SPEC_PATH", link), self.assertRaises(ValueError):
                recovery._bindings()

    def test_current_callers_admit_actual_bytes_before_older_roundtrip_or_message_checks(self):
        source = self.current["scripts/ci/test_android_camera_boot_handoff.py"].decode()
        tree = ast.parse(source)
        node = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and
                    node.name == "test_new_stage_exact_inverse_preserves_old_pins_sources_and_roundtrip")
        method = ast.get_source_segment(source, node)
        self.assertIn("current_source_before_handoff_fixture(relative, actual_current)", method)
        self.assertIn("history.current_source_before_boot_handoff(relative, actual_current)", method)
        self.assertIn('binding["after_sha256"]', method)
        self.assertIn("self.assertEqual(current, previous)", method)
        source = self.current["scripts/ci/test_android_external337_fixture_recovery.py"].decode()
        self.assertIn('"^A historical image cannot replace exact current recents-observation source$"', source)
        self.assertIn("for payload in (previous, current +", source)
        source = self.current["scripts/ci/test_camera_handoff_fixture_recovery.py"].decode()
        self.assertIn("cls.actual_current =", source)
        self.assertIn("current_source_before_recents_fixture(relative, payload)", source)
        self.assertIn("for relative, payload in cls.actual_current.items()):", source)
        self.assertIn("recovery.current_source_before_handoff_fixture(relative, self.actual_current[relative])", source)
        self.assertIn("boot.current_source_before_boot_handoff(relative, self.actual_current[relative])", source)
        # These are prior-stage controls, not authority for the new boundary.
        prior = recovery.source_before_recents_fixture(
            "scripts/ci/test_android_external337_fixture_recovery.py",
            self.current["scripts/ci/test_android_external337_fixture_recovery.py"])
        self.assertIn(b"exact current boot-handoff source$", prior)


if __name__ == "__main__":
    unittest.main()
