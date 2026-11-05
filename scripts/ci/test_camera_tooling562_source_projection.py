# SPDX-License-Identifier: Apache-2.0
"""CI562 source ingress/old-pin regressions; zero compiler or native actions."""
import ast
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import camera_tooling562_source_projection as history
import android_external328_source_projection as bridge
import ios_geometry_simulator_source_projection as owned_history
import webview_content_policy_source_projection as content_history

ROOT = Path(__file__).resolve().parents[2]
HELPER = "scripts/ci/android_camera_developer_prerequisite.py"
MODULES = (
    "scripts/ci/test_android_camera_scalar_control_refusal.py",
    "scripts/ci/test_android_camera_settings_activity_reference_prefix_diagnostics.py",
)
OLD_HELPER = "0e47097d10f1886bec0ee8eebc280b29afb704dc47d09df1bbdb41ddaa651b26"


def digest(data):
    return hashlib.sha256(data).hexdigest()


class CameraTooling562Controls(unittest.TestCase):
    def test_six_full_source_bindings_and_nine_fragments_roundtrip(self):
        bindings = history._bindings()
        self.assertEqual(6, len(bindings))
        self.assertEqual(9, sum(len(b["fragments"]) for b in bindings.values()))
        for path, binding in bindings.items():
            from camera_tooling566_source_projection import current_source_before_tooling566
            current = current_source_before_tooling566(path,
                owned_history.current_source_before_owned_geometry(path, (ROOT / path).read_bytes()))
            old = history.current_source_before_tooling(path, current)
            self.assertEqual(binding["before_sha256"], digest(old))
            rebuilt = old
            for fragment in binding["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(1, rebuilt.count(before))
                rebuilt = rebuilt.replace(before, after, 1)
            self.assertEqual(current, rebuilt)
            self.assertEqual(old, history.source_before_tooling(path, old))

    def test_current_refuses_old_partial_unknown_and_nonordinary_payloads(self):
        for path in history._bindings():
            from camera_tooling566_source_projection import current_source_before_tooling566
            current = current_source_before_tooling566(path,
                owned_history.current_source_before_owned_geometry(path, (ROOT / path).read_bytes()))
            old = history.source_before_tooling(path, current)
            for bad in (old, current[:-1], current + b"\n", b"", b"foreign", None, bytearray(current)):
                with self.subTest(path=path, kind=type(bad).__name__), self.assertRaises(ValueError):
                    history.current_source_before_tooling(path, bad)
        with self.assertRaises(ValueError):
            history.current_source_before_tooling(Path(MODULES[0]), b"x")

    def test_ancestor_and_latest_admission_keep_the_preserved_stage_separate(self):
        for path in MODULES:
            current = (ROOT / path).read_bytes()
            old = history.current_source_before_tooling(path, current)
            self.assertEqual(old, bridge.current_source_for_history(path, current))
            self.assertEqual(old, history.peel_current_tooling_for_older_history(path, old))
            with self.assertRaises(ValueError):
                bridge.current_source_for_history(path, old)
        path = "unlisted-source-is-not-certified"
        self.assertEqual(b"unqualified", history.peel_current_tooling_for_older_history(path, b"unqualified"))

    def test_new_ingress_qualifies_current_helper_but_retains_raw_custody_hash(self):
        import camera_home_baseline_source_projection as home
        payload = (ROOT / HELPER).read_bytes()
        prior = home.source_before_home_baseline(HELPER,
            owned_history.current_source_before_owned_geometry(HELPER, payload))
        for path in MODULES:
            source = (ROOT / path).read_text()
            tree = ast.parse(source)
            functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                         and n.name in {"digest", "source_binding_digest"}]
            self.assertEqual(2, len(functions))
            before = history.source_before_tooling(path, source.encode()).decode()
            old_digest = next(n for n in ast.parse(before).body if isinstance(n, ast.FunctionDef) and n.name == "digest")
            new_digest = next(n for n in functions if n.name == "digest")
            self.assertEqual(ast.dump(old_digest), ast.dump(new_digest))
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                helper = root / HELPER
                helper.parent.mkdir(parents=True)
                helper.write_bytes(payload)
                namespace = {"Path": Path, "hashlib": hashlib, "TREE": root,
                             "HELPER_PATH": helper, "__file__": str(root / path)}
                exec(compile(ast.Module(body=functions, type_ignores=[]), "<only-source-ingress>", "exec"), namespace)
                self.assertEqual(OLD_HELPER, namespace["source_binding_digest"](helper))
                self.assertEqual(digest(payload), namespace["digest"](helper))
                for bad in (prior, payload + b"\n", b"foreign"):
                    helper.write_bytes(bad)
                    with self.assertRaises(ValueError):
                        namespace["source_binding_digest"](helper)
                namespace["__file__"] = str(ROOT / path)  # Explicit private historical tree.
                helper.write_bytes(bridge.current_source_for_history(HELPER, payload))
                self.assertEqual(OLD_HELPER, namespace["source_binding_digest"](helper))

    def test_manifest_drift_symlink_and_hardlink_fail_before_projection(self):
        raw = history.SPEC_PATH.read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fixture.json"
            with patch.object(history, "SPEC_PATH", path):
                for bad in (raw + b"\n", b"{}", b"", b"x" * (history.MAX_SPEC_BYTES + 1)):
                    path.write_bytes(bad)
                    with self.assertRaises(ValueError):
                        history._bindings()
                path.unlink()
                path.symlink_to(history.__file__)
                with self.assertRaises(ValueError):
                    history._bindings()
                path.unlink()
                backing = path.with_name("backing.json")
                backing.write_bytes(raw)
                path.hardlink_to(backing)
                with self.assertRaises(ValueError):
                    history._bindings()

    def test_original_home_native_controller_and_workflow_inputs_unchanged(self):
        archive = ROOT / "docs/development/evidence/current-platform-recovery-20261101/camera-home-baseline556-559/final-inputs.json"
        inputs = json.loads(archive.read_text())
        for path in (HELPER, "scripts/ci/android_device_tests.py",
                     "calf-camera-picker/build.gradle.kts",
                     "calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedDeveloperSettingsUi.kt",
                     "calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraRestorationTest.kt"):
            self.assertEqual(inputs[path], digest(content_history.current_source_before_content_policy(
                path, (ROOT / path).read_bytes())))
        # Workflow is separately held own-Git provenance, not a library input map.
        self.assertEqual("3d5d2ea0313055366bf6bc83550f7e2f40c50438c450508588db778fb6bb75f7",
                         digest(owned_history.current_source_before_owned_geometry(
                             ".github/workflows/gradle.yml", (ROOT / ".github/workflows/gradle.yml").read_bytes())))


if __name__ == "__main__":
    unittest.main()
