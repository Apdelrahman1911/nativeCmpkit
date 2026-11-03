# SPDX-License-Identifier: Apache-2.0
"""NEW controls for the seven actual CI337 fixture failures, not native passes.

Select only changed digest/boundary helpers, not historical test methods or model
classes. Source admission, synthetic config hashing and exact inverse composition
remain different contracts. No compiler, SDK, Git, process or network operation.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import android_external328_source_projection as bridge
import terminal_awt240_source_projection as terminal

ROOT = Path(__file__).resolve().parents[2]
FF = "scripts/ci/test_android_camera_pre_reporter_fail_fast.py"
CA = "scripts/ci/test_android_camera205_owning_admission.py"
TERMINAL = "scripts/ci/terminal_awt240_source_projection.py"
SCALAR = "scripts/ci/test_android_camera_scalar_control_refusal.py"
PRIOR_BINDINGS_SHA256 = "1df5350f49c01e5e048c22ca4f841c6616d4112eea54dbc870c7771965f6a76c"
PRIOR_AFTER_SHA256 = {
    FF: "e0c157e8870d73d887824299356cd1dc9463f268a39514e7d012bfbd3840603f",
    CA: "9293145eef7eb888f72b22dd445a0adf63f45c423bcc439975939bb2f9e81423",
    TERMINAL: "7403411fb994a0a3cd8812cfa07f07f28f38553873dbd9e6c742505b9e77afa1",
}


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def assignment(source, name):
    nodes = [node for node in ast.parse(source).body if isinstance(node, ast.Assign)
             and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    if len(nodes) != 1:
        raise AssertionError("One exact inert source declaration is required")
    return nodes[0]


def literal(source, name):
    return ast.literal_eval(assignment(source, name).value)


def function(source, name):
    nodes = [node for node in ast.walk(ast.parse(source))
             if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(nodes) != 1:
        raise AssertionError("One exact inert helper definition is required")
    return nodes[0]


def selected_digest(source_tree):
    source = (ROOT / FF).read_text()
    node = function(source, "digest")
    namespace = {"TREE": source_tree, "hashlib": hashlib}
    exec(compile(ast.Module(body=[node], type_ignores=[]),
                 "<ci337-changed-digest-only>", "exec"), namespace)
    return namespace["digest"]


class External337FixtureRecoveryControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bindings = bridge._bindings()
        cls.raw_spec = bridge.SPEC_PATH.read_bytes()
        cls.current = {relative: (ROOT / relative).read_bytes() for relative in cls.bindings}

    @classmethod
    def tearDownClass(cls):
        if bridge.SPEC_PATH.read_bytes() != cls.raw_spec or any(
                (ROOT / relative).read_bytes() != payload for relative, payload in cls.current.items()):
            raise AssertionError("The exact source and manifest bytes changed during CI337 controls")

    def test_private_synthetic_config_hash_is_raw_and_changes_without_source_projection(self):
        changed_digest = selected_digest(ROOT)
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-ci337-raw-config-") as name:
            path = Path(name) / "avd/synthetic-config"
            self.assertFalse(path.is_relative_to(ROOT))
            path.parent.mkdir()
            path.write_bytes(b"synthetic-owned-config")
            self.assertEqual(digest(path.read_bytes()), changed_digest(path))
            first = changed_digest(path)
            path.write_bytes(b"changed-synthetic-config")
            self.assertEqual(digest(path.read_bytes()), changed_digest(path))
            self.assertNotEqual(first, changed_digest(path))

    def test_source_digest_admits_exact_current_identity_but_not_old_or_changed_images(self):
        relative = "scripts/ci/android_device_tests.py"
        current = self.current[relative]
        previous = bridge.current_source_for_history(relative, current)
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-ci337-source-digest-") as name:
            root = Path(name)
            path = root / relative
            path.parent.mkdir(parents=True)
            changed_digest = selected_digest(root)
            path.write_bytes(current)
            self.assertEqual(digest(previous), changed_digest(path))
            for payload in (previous, current + b"\n", current[:-1], b"foreign", b""):
                path.write_bytes(payload)
                with self.assertRaisesRegex(ValueError, "exact current source"):
                    changed_digest(path)
            outside = root.parent / (root.name + "-ordinary-config")
            try:
                outside.write_bytes(current)
                self.assertEqual(digest(current), changed_digest(outside))
            finally:
                outside.unlink()

    def test_preimport_boundary_separates_actual_current_and_private_historical_inputs(self):
        source = self.current[CA].decode()
        names = ("HELPER", "SCALAR", "IMPORT_BOUNDARY_SHA256")
        namespace = {name: literal(source, name) for name in names}
        namespace.update(TREE=ROOT, ast=ast, digest=digest,
                         assignment=assignment, literal=literal, function=function)
        node = function(source, "boundary")
        exec(compile(ast.Module(body=[node], type_ignores=[]),
                     "<ci337-changed-preimport-reader-only>", "exec"), namespace)
        self.sources = {
            FF: bridge.current_source_for_history(FF, self.current[FF]).decode(),
            SCALAR: (ROOT / SCALAR).read_text(),
        }
        inputs = literal(self.sources[FF], "EXPECTED_INPUT_SHA256")
        boundary = namespace["boundary"]
        boundary(self, FF, ROOT)
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-ci337-preimport-") as name:
            root = Path(name)
            for relative in inputs:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                payload = (ROOT / relative).read_bytes()
                path.write_bytes(bridge.current_source_for_history(relative, payload))
            # Explicit private fixture: old exact literals and raw historical bytes.
            boundary(self, FF, root)
            for relative in inputs:
                (root / relative).write_bytes((ROOT / relative).read_bytes())
            # Model the actual current-source branch without touching live files.
            namespace["TREE"] = root
            boundary(self, FF, root)
            relative = "scripts/ci/camera_scalar_failfast_source_projection.py"
            path = root / relative
            current = path.read_bytes()
            for payload in (bridge.current_source_for_history(relative, current), current + b"\n"):
                path.write_bytes(payload)
                with self.assertRaisesRegex(ValueError, "exact current source"):
                    boundary(self, FF, root)
            path.write_bytes(current)

    def test_terminal_preimage_is_idempotent_without_admitting_mutated_intermediate_bytes(self):
        relative = "scripts/ci/library_tests.py"
        current = self.current[relative]
        previous = terminal.source_before_terminal_awt240(relative, current)
        binding = json.loads(terminal.SPEC_PATH.read_text())["bindings"][relative]
        self.assertEqual(binding["before_sha256"], digest(previous))
        with self.assertRaises(ValueError):
            bridge.source_before_android_external328(relative, previous)
        self.assertIs(previous, terminal.source_before_terminal_awt240(relative, previous))
        self.assertEqual(previous, terminal.source_before_terminal_awt240(
            relative, terminal.source_before_terminal_awt240(relative, current)))
        for payload in (previous + b"\n", previous[:-1], current + b"\n", b"", None, bytearray(previous)):
            with self.assertRaises(ValueError):
                terminal.source_before_terminal_awt240(relative, payload)

    def test_manifest_adds_only_three_repairs_and_retains_every_prior_binding_and_fragment(self):
        from arm64_stop_candidate_source_projection import current_source_before_arm64_stop_candidate

        previous = copy.deepcopy(self.bindings)
        self.assertEqual(16, len(previous))
        self.assertEqual(49, sum(len(binding["fragments"]) for binding in previous.values()))
        for relative, expected in PRIOR_AFTER_SHA256.items():
            binding = previous[relative]
            repair = binding["fragments"].pop()
            restored = self.current[relative]
            before, after = repair["before"].encode(), repair["after"].encode()
            self.assertEqual(1, restored.count(after))
            restored = restored.replace(after, before, 1)
            self.assertEqual(expected, digest(restored))
            binding["after_sha256"] = expected
        canonical = json.dumps(previous, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(PRIOR_BINDINGS_SHA256, digest(canonical))
        self.assertEqual(46, sum(len(binding["fragments"]) for binding in previous.values()))
        for relative, binding in self.bindings.items():
            current = self.current[relative]
            # The prior manifest binds its own stage, not the newer Stop-only stage.
            prior_current = current_source_before_arm64_stop_candidate(relative, current)
            self.assertEqual(binding["after_sha256"], digest(prior_current))
            original = bridge.current_source_for_history(relative, current)
            self.assertEqual(binding["before_sha256"], digest(original))

    def test_owning_manifest_check_refuses_old_or_changed_live_source_before_historical_digest(self):
        from arm64_stop_candidate_source_projection import source_before_arm64_stop_candidate
        from unittest.mock import patch

        relative = "scripts/ci/library_tests.py"
        current = self.current[relative]
        variants = (
            source_before_arm64_stop_candidate(relative, current),
            bridge.current_source_for_history(relative, current),
            current + b"\n",
            current[:-1],
            b"foreign",
            b"",
        )
        for number, payload in enumerate(variants):
            mutated = dict(self.current)
            mutated[relative] = payload
            with self.subTest(mutation=number), patch.object(self, "current", mutated), \
                    self.assertRaisesRegex(ValueError, "exact current iOS modal lifecycle source"):
                self.test_manifest_adds_only_three_repairs_and_retains_every_prior_binding_and_fragment()


if __name__ == "__main__":
    unittest.main()
