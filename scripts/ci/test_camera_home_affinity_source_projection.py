# SPDX-License-Identifier: Apache-2.0
"""NEW exact HOME-affinity source controls, not native/compiler acceptance."""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import camera_home_affinity_source_projection as history
import ios_owned_geometry_fixture_recovery as older

ROOT = Path(__file__).resolve().parents[2]
HOME_TEST = "scripts/ci/test_camera_home_baseline_source_projection.py"
KOTLIN_TEST = "calf-camera-picker/src/commonTest/kotlin/com/mohamedrejeb/calf/camerapicker/SettingsHomeTaskBaselineTest.kt"
EXPECTED = {
    "scripts/ci/android_camera_home_baseline.py",
    "scripts/ci/android_camera_home_refusal_observation.py",
    "calf-camera-picker/src/commonTest/kotlin/com/mohamedrejeb/calf/camerapicker/SettingsHomeTaskBaseline.kt",
    KOTLIN_TEST, HOME_TEST,
    "scripts/ci/ios_owned_geometry_fixture_recovery.py",
    "scripts/ci/test_ios_owned_geometry_fixture_recovery.py",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class HomeAffinitySourceProjectionControls(unittest.TestCase):
    def test_all_seven_complete_current_images_and_sixteen_fragments_roundtrip_exactly(self):
        bindings = history._bindings()
        self.assertEqual(EXPECTED, set(bindings))
        self.assertEqual(16, sum(len(row["fragments"]) for row in bindings.values()))
        for name, row in bindings.items():
            raw_current = (ROOT / name).read_bytes()
            from calendar_share_selector_source_projection import peel_calendar_share_selectors_for_history
            current = peel_calendar_share_selectors_for_history(name, raw_current)
            previous = history.current_source_before_home_affinity(name, raw_current)
            self.assertEqual((row["after_sha256"], row["after_bytes"]), (sha(current), len(current)), name)
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(previous), len(previous)), name)
            forward = previous
            for fragment in row["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(fragment["before_fragment_sha256"], sha(before))
                self.assertEqual(fragment["after_fragment_sha256"], sha(after))
                self.assertEqual(1, forward.count(before))
                forward = forward.replace(before, after, 1)
            self.assertEqual(current, forward)

    def test_old_partial_displaced_unknown_nonordinary_images_never_admit_as_current(self):
        for name, row in history._bindings().items():
            current = (ROOT / name).read_bytes()
            previous = history.source_before_home_affinity(name, current)
            fragment = row["fragments"][0]["after"].encode()
            self.assertEqual(1, current.count(fragment))
            remainder = current.replace(fragment, b"", 1)
            displaced = fragment + remainder if current.endswith(fragment) else remainder + fragment
            self.assertNotEqual(current, displaced)
            for bad in (previous, current[:-1], current + b"\n", displaced, b"", None, bytearray(current),
                        b"x" * (history.MAX_SOURCE_BYTES + 1)):
                with self.subTest(name=name, kind=type(bad).__name__), self.assertRaises(ValueError):
                    history.current_source_before_home_affinity(name, bad)

    def test_ancestor_peeling_is_finite_exact_idempotent_and_cannot_certify_unknown_bytes(self):
        for name in EXPECTED:
            current = (ROOT / name).read_bytes()
            previous = history.source_before_home_affinity(name, current)
            self.assertEqual(previous, history.peel_home_affinity_for_history(name, current))
            self.assertEqual(previous, history.peel_home_affinity_for_history(name, previous))
            unknown = current + b"\n# synthetic unknown source\n"
            self.assertEqual(unknown, history.peel_home_affinity_for_history(name, unknown))
            with self.assertRaises(ValueError):
                history.source_before_home_affinity(name, unknown)
        current = (ROOT / HOME_TEST).read_bytes()
        before_affinity = history.current_source_before_home_affinity(HOME_TEST, current)
        before_fixture581 = older.source_before_recovery(HOME_TEST, before_affinity)
        self.assertEqual(before_fixture581, older.current_source_before_recovery(HOME_TEST, current))
        with self.assertRaises(ValueError):
            older.current_source_before_recovery(HOME_TEST, before_affinity)
        self.assertEqual(before_fixture581, older.peel_current_recovery_for_history(HOME_TEST, current))
        self.assertEqual(before_fixture581, older.peel_current_recovery_for_history(HOME_TEST, before_fixture581))

    def test_old_manifests_original_eight_kotlin_methods_and_shared_assertions_are_unchanged(self):
        originals = {
            "scripts/ci/fixtures/camera-home-baseline-source-inverse.json": "b968373d8de34a53525efd291055ad61f8d034a17236f663d8c58ba4c0716dcb",
            "scripts/ci/fixtures/camera-home571-fixture-recovery.json": "681d4eb39370cfff45de265f9baf0913e9e60f04a29f3a331e6fe1b61de9923b",
            "scripts/ci/fixtures/ios-owned-geometry581-fixture-recovery.json": "441995a9a586509700a8359c744c6a2d7420abed2df2924333c6f111598dcd58",
            "scripts/ci/android_camera_developer_prerequisite.py": "92f8d79d3a0871f1abb619a0a17b36c87568e11151fb3dbefa4f12773de78bdb",
            "calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedDeveloperSettingsUi.kt": "01771567b969a88094d88a2906dadc6bc4d1e8502e695abc9f145b7ca197e06e",
        }
        for name, digest in originals.items():
            raw_current = (ROOT / name).read_bytes()
            from calendar_share_selector_source_projection import peel_calendar_share_selectors_for_history
            comparison = peel_calendar_share_selectors_for_history(name, raw_current)
            self.assertEqual(digest, sha(comparison), name)
        kotlin = (ROOT / KOTLIN_TEST).read_bytes()
        previous = history.source_before_home_affinity(KOTLIN_TEST, kotlin)
        self.assertEqual(previous.decode().rsplit("\n}", 1)[0] + "\n",
                         kotlin.decode().split("\n    private fun manifestHome()", 1)[0])
        self.assertEqual(8, len(re.findall(r"@Test fun ([a-zA-Z0-9_]+)", previous.decode())))
        self.assertEqual(13, len(re.findall(r"@Test fun ([a-zA-Z0-9_]+)", kotlin.decode())))
        class TransparentSourceView(ast.NodeTransformer):
            def visit_Call(self, node):
                node = self.generic_visit(node)
                if isinstance(node.func, ast.Name) and node.func.id == "current_source_before_home_affinity":
                    if len(node.args) != 2 or node.keywords:
                        raise AssertionError("Only the exact binary source view is qualified")
                    return node.args[1]
                return node
        def obligations(raw):
            tree = TransparentSourceView().visit(ast.parse(raw))
            return ([node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")],
                    [ast.dump(node, include_attributes=False) for node in ast.walk(tree) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                     and node.func.value.id == "self" and node.func.attr.startswith("assert")])
        for name in (HOME_TEST, "scripts/ci/test_ios_owned_geometry_fixture_recovery.py"):
            raw_current = (ROOT / name).read_bytes()
            from calendar_share_selector_source_projection import peel_calendar_share_selectors_for_history
            current = peel_calendar_share_selectors_for_history(name, raw_current)
            self.assertEqual(obligations(history.source_before_home_affinity(name, current)), obligations(current), name)

    def test_manifest_ordinary_exact_single_link_held_and_bounded_failures_remain_refusals(self):
        raw = history.SPEC_PATH.read_bytes()
        self.assertEqual(history.SPEC_SHA256, sha(raw))
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-home-affinity-") as directory:
            copied = Path(directory) / "manifest.json"
            copied.write_bytes(raw)
            link = copied.with_name("alias.json")
            link.symlink_to(copied)
            with patch.object(history, "SPEC_PATH", link), self.assertRaises(ValueError):
                history._bindings()
            link.unlink()
            link.hardlink_to(copied)
            with patch.object(history, "SPEC_PATH", copied), self.assertRaises(ValueError):
                history._bindings()
            link.unlink()
            for bad in (b"", b"{}", raw + b"\n", b"x" * (history.MAX_SPEC_BYTES + 1)):
                copied.write_bytes(bad)
                with patch.object(history, "SPEC_PATH", copied), self.assertRaises(ValueError):
                    history._bindings()
        with self.assertRaises(ValueError):
            history._unique([("duplicated", 1), ("duplicated", 2)])

    def test_source_history_never_executes_candidate_parser_native_process_or_dynamic_code(self):
        tree = ast.parse((ROOT / "scripts/ci/camera_home_affinity_source_projection.py").read_bytes())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, {"eval", "exec", "compile", "open", "__import__"})
                elif isinstance(node.func, ast.Attribute):
                    self.assertNotIn(node.func.attr, {"parse_home_task", "parse_recent_home_baseline", "run", "Popen", "control", "write_bytes", "write_text"})
        self.assertEqual("51cc224488eb366034f8edea83f1a31465f8818059bad96a802a1fff0aa655ca",
                         sha(history.SPEC_PATH.read_bytes()))


if __name__ == "__main__":
    unittest.main()
