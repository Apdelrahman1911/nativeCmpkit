# SPDX-License-Identifier: Apache-2.0
"""New important CI476 recovery guards; no SDK, Gradle or native execution."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import camera_boot_handoff_source_projection as boot
import camera_handoff_fixture_source_projection as recovery

ROOT = Path(__file__).resolve().parents[2]
PATHS = {
    "scripts/ci/test_android_external328_source_projection.py",
    "scripts/ci/test_android_external337_fixture_recovery.py",
    "scripts/ci/camera_boot_handoff_source_projection.py",
}
ORIGINAL_BOOT_SPEC_SHA256 = "525f7f43222f92ab5730d0154e817dbfc60858e21b1daaa60d5203d954535367"


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


class CameraHandoffFixtureRecoveryControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec_bytes = recovery.SPEC_PATH.read_bytes()
        cls.bindings = recovery._bindings()
        cls.actual_current = {relative: (ROOT / relative).read_bytes() for relative in PATHS}
        from camera_recents_fixture_source_projection import current_source_before_recents_fixture
        cls.current = {relative: current_source_before_recents_fixture(relative, payload)
                       for relative, payload in cls.actual_current.items()}

    @classmethod
    def tearDownClass(cls):
        if recovery.SPEC_PATH.read_bytes() != cls.spec_bytes or any(
                (ROOT / relative).read_bytes() != payload for relative, payload in cls.actual_current.items()):
            raise AssertionError("Owning fixture source or manifest changed during the controls")

    def test_exact_three_paths_five_fragments_keep_original_boot_manifest_and_endpoints(self):
        document = json.loads(self.spec_bytes)
        self.assertEqual("d4d17f868eadf501e10baa50613388a84200971e", document["before_revision"])
        self.assertEqual(PATHS, set(self.bindings))
        self.assertEqual(5, sum(len(binding["fragments"]) for binding in self.bindings.values()))
        self.assertEqual(recovery.SPEC_SHA256, sha(self.spec_bytes))
        self.assertEqual(ORIGINAL_BOOT_SPEC_SHA256, boot.SPEC_SHA256)
        self.assertEqual(ORIGINAL_BOOT_SPEC_SHA256, sha(boot.SPEC_PATH.read_bytes()))
        self.assertFalse(any(path.startswith("calf-") for path in self.bindings))

    def test_every_current_source_restores_full_prior_bytes_and_forward_roundtrip(self):
        for relative, binding in self.bindings.items():
            current = self.current[relative]
            self.assertEqual(binding["after_sha256"], sha(current))
            previous = recovery.current_source_before_handoff_fixture(relative, self.actual_current[relative])
            self.assertEqual(binding["before_sha256"], sha(previous))
            self.assertEqual(binding["before_bytes"], len(previous))
            self.assertIs(previous, recovery.source_before_handoff_fixture(relative, previous))
            self.assertEqual(previous, boot.current_source_before_boot_handoff(relative, self.actual_current[relative]))
            forward = previous
            for fragment in binding["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(fragment["before_fragment_sha256"], sha(before))
                self.assertEqual(fragment["after_fragment_sha256"], sha(after))
                self.assertEqual(1, forward.count(before))
                forward = forward.replace(before, after, 1)
            self.assertEqual(current, forward)

    def test_current_admission_refuses_historical_mutated_wrong_identity_and_manifest_inputs(self):
        for relative, current in self.current.items():
            previous = recovery.source_before_handoff_fixture(relative, current)
            for payload in (previous, current[:-1], current + b"\n", b"foreign", b"", None, bytearray(current)):
                with self.subTest(relative=relative, kind=type(payload).__name__):
                    with self.assertRaises(ValueError):
                        recovery.current_source_before_handoff_fixture(relative, payload)
            for identity in (None, Path(relative), [], 1):
                with self.assertRaises(ValueError):
                    recovery.current_source_before_handoff_fixture(identity, current)
            altered = copy.deepcopy(self.bindings)
            altered[relative]["fragments"][0]["after_fragment_sha256"] = "0" * 64
            with patch.object(recovery, "_bindings", return_value=altered), self.assertRaises(ValueError):
                recovery.source_before_handoff_fixture(relative, current)
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-handoff-fixture-manifest-") as name:
            path = Path(name) / "manifest.json"
            for raw in (self.spec_bytes + b"\n", b"{}", b"", b"x" * (recovery.MAX_SPEC_BYTES + 1)):
                path.write_bytes(raw)
                with patch.object(recovery, "SPEC_PATH", path), self.assertRaises(ValueError):
                    recovery._bindings()
            path.write_bytes(self.spec_bytes)
            linked = path.with_name("linked.json")
            linked.symlink_to(path)
            with patch.object(recovery, "SPEC_PATH", linked), self.assertRaises(ValueError):
                recovery._bindings()
            linked.unlink()
            linked.hardlink_to(path)
            with patch.object(recovery, "SPEC_PATH", linked), self.assertRaises(ValueError):
                recovery._bindings()

    def test_owning_fixture_changes_admit_actual_current_before_history_and_keep_pins(self):
        relative = "scripts/ci/test_android_external328_source_projection.py"
        current = self.current[relative].decode()
        self.assertIn("path.write_bytes(self.actual_current[relative])", current)
        self.assertIn("bridge.read_current_source_for_history(path, root)", current)
        relative = "scripts/ci/test_android_external337_fixture_recovery.py"
        current = self.current[relative].decode()
        self.assertIn("restored = current_source_before_arm64_stop_candidate(relative, self.current[relative])", current)
        self.assertIn('"^A historical image cannot replace exact current boot-handoff source$"', current)
        for relative in PATHS:
            current = self.current[relative]
            previous = recovery.source_before_handoff_fixture(relative, current)
            def pins(payload):
                source = payload.decode()
                return {ast.get_source_segment(source, node) for node in ast.parse(source).body
                        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and
                           "SHA256" in target.id for target in node.targets)}
            self.assertEqual(pins(previous), pins(current), relative)


if __name__ == "__main__":
    unittest.main()
