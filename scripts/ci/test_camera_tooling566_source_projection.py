# SPDX-License-Identifier: Apache-2.0
"""Important shared ingress/ancestor controls; zero compiler or native work."""
import ast
import hashlib
import importlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import android_external328_source_projection as bridge
import camera_tooling562_source_projection as older
import camera_tooling566_source_projection as history

ROOT = Path(__file__).resolve().parents[2]
MODULES = (
    "scripts/ci/test_android_camera_scalar_control_refusal.py",
    "scripts/ci/test_android_camera_settings_activity_reference_prefix_diagnostics.py",
)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


class CameraTooling566Controls(unittest.TestCase):
    def test_six_complete_own_git_bindings_roundtrip_without_old_pin_changes(self):
        bindings = history._bindings()
        self.assertEqual(6, len(bindings))
        for name, binding in bindings.items():
            current = (ROOT / name).read_bytes()
            previous = history.current_source_before_tooling566(name, current)
            self.assertEqual(binding["before_sha256"], sha(previous))
            self.assertEqual(binding["before_bytes"], len(previous))
            forward = previous
            for fragment in binding["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(1, forward.count(before))
                forward = forward.replace(before, after, 1)
            self.assertEqual(current, forward)
            self.assertEqual(previous, history.source_before_tooling566(name, previous))
        self.assertEqual("e91e9f3ccbf98238d7fcb7f82a6cedce492451fb15bfcb381ace6616cd43dfdc",
                         sha(older.SPEC_PATH.read_bytes()))

    def test_latest_raw_ingress_occurs_once_and_nested_stages_do_not_readmit_it(self):
        for name in MODULES:
            current = (ROOT / name).read_bytes()
            expected = older.source_before_tooling(name, current)
            with (patch.object(history, "current_source_before_tooling566", wraps=history.current_source_before_tooling566) as latest,
                  patch.object(older, "current_source_before_tooling", wraps=older.current_source_before_tooling) as prior):
                self.assertEqual(expected, bridge.current_source_for_history(name, current))
                self.assertEqual(1, latest.call_count)
                self.assertEqual(1, prior.call_count)
                latest.assert_called_once_with(name, current)
                prior.assert_called_once_with(name, current)

    def test_original_and_tooling562_preimages_never_replace_raw_current_sources(self):
        for name in history._bindings():
            current = (ROOT / name).read_bytes()
            previous = history.source_before_tooling566(name, current)
            bad_images = (previous, current[:-1], current + b"\n", b"", bytearray(current), None)
            for bad in bad_images:
                with self.subTest(name=name, type=type(bad).__name__), self.assertRaises(ValueError):
                    bridge.current_source_for_history(name, bad)
        for name in MODULES:
            current = (ROOT / name).read_bytes()
            previous = older.source_before_tooling(name, current)
            with self.assertRaises(ValueError):
                bridge.current_source_for_history(name, previous)

    def test_three_formerly_blocked_owning_source_admissions_without_old_test_execution(self):
        camera205 = importlib.import_module("test_android_camera205_owning_admission")
        owner = camera205.Camera205OwningAdmissionNewOnlyTests
        owner.setUpClass()  # Exact original setup only; no accepted method replay.
        self.assertEqual(camera205.EXPECTED_SHA256, {name: sha(raw) for name, raw in owner.payloads.items()})
        ci213 = importlib.import_module("test_camera_ci213_source_projection")
        owner = ci213.CameraCI213ProjectionTests
        owner.setUpClass()
        self.assertEqual(ci213.EXPECTED, {name: sha(raw) for name, raw in owner.payloads.items()})
        owner.tearDownClass()
        console = importlib.import_module("test_android_camera_owned_avd_console_name")
        # Qualify the original failing first assignment; do not execute its
        # subsequent action-guard/helper setup, native parser or old methods.
        admitted = {name: console.read_bound_source(name) for name in console.BOUND_SOURCE_AFTER47}
        self.assertEqual(console.BOUND_SOURCE_AFTER47, {name: sha(raw) for name, raw in admitted.items()})

    def test_busy_stage_is_distinct_from_actual_current_tooling_image(self):
        import camera_boot_busy_source_projection as busy
        name = "scripts/ci/camera_recents_fixture_source_projection.py"
        current = (ROOT / name).read_bytes()
        tooling562_stage = history.current_source_before_tooling566(name, current)
        busy_stage = older.current_source_before_tooling(name, tooling562_stage)
        self.assertNotEqual(current, busy_stage)
        previous = busy.current_source_before_boot_busy(name, current)
        binding = busy._bindings()[name]
        self.assertEqual(binding["before_sha256"], sha(previous))
        forward = previous
        for fragment in binding["fragments"]:
            forward = forward.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
        self.assertEqual(busy_stage, forward)
        with self.assertRaises(ValueError):
            busy.current_source_before_boot_busy(name, previous)

    def test_nested_current_readers_keep_only_exact_ancestor_peeling(self):
        for filename, function in (
            ("arm64_stop_candidate_source_projection.py", "current_source_before_arm64_stop_candidate"),
            ("camera_recents_fixture_source_projection.py", "current_source_before_recents_fixture"),
            ("camera_boot_busy_source_projection.py", "current_source_before_boot_busy"),
        ):
            source = (ROOT / "scripts/ci" / filename).read_text()
            node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == function)
            calls = {n.func.id for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
            self.assertNotIn("current_source_before_tooling", calls)
            self.assertNotIn("current_source_before_tooling566", calls)
            self.assertIn("peel_current_tooling_for_older_history", calls)
            self.assertIn("peel_current_tooling566_for_older_history", calls)

    def test_changed_manifest_aliases_and_nonordinary_images_fail_before_projection(self):
        original = history.SPEC_PATH.read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            with patch.object(history, "SPEC_PATH", path):
                for bad in (original + b"\n", b"{}", b"", b"x" * (history.MAX_SPEC_BYTES + 1)):
                    path.write_bytes(bad)
                    with self.assertRaises(ValueError):
                        history._bindings()
                path.unlink(); path.symlink_to(history.__file__)
                with self.assertRaises(ValueError):
                    history._bindings()
                path.unlink()
                backing = path.with_name("backing.json"); backing.write_bytes(original)
                path.hardlink_to(backing)
                with self.assertRaises(ValueError):
                    history._bindings()

    def test_unchanged_native_helper_controller_kotlin_and_workflow_inputs(self):
        spec = json.loads(history.SPEC_PATH.read_bytes())
        for name, expected in spec["unchanged_owning_inputs"].items():
            self.assertEqual(expected, sha((ROOT / name).read_bytes()), name)
        for name in MODULES:
            # Observer bodies/raw digest logic are not touched by this repair.
            self.assertNotIn(name, history._bindings())


if __name__ == "__main__":
    unittest.main()
