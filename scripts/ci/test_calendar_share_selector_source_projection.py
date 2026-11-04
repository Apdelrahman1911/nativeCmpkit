# SPDX-License-Identifier: Apache-2.0
"""NEW finite selector ingress/owning-input controls; zero compiler/native IO."""
import ast
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import calendar_share_selector_source_projection as selectors
import camera_home_affinity_source_projection as camera
import ios_owned_geometry_fixture_recovery as recovery
import ios_geometry_simulator_source_projection as owned
import android_external328_source_projection as bridge
import apple_image_launcher_source_projection as image_history

ROOT = Path(__file__).resolve().parents[2]
LAYER = "scripts/ci/calendar_share_selector_source_projection.py"
LAYER_SHA256 = "9e08ae99513cc2c29688b69668f78a5ba319d1e40a7b615519382f14ad728a64"
CAMERA = "scripts/ci/camera_home_affinity_source_projection.py"
CAMERA_SPEC = "scripts/ci/fixtures/camera-home-affinity-source-inverse.json"
SHARED = ("scripts/ci/library_tests.py", "scripts/ci/workflow_matrix.py", ".github/workflows/gradle.yml")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class CalendarShareSelectorSourceControls(unittest.TestCase):
    def test_four_complete_images_and_all_finite_unique_fragments_roundtrip(self):
        document = selectors._document()
        self.assertEqual(set(SHARED) | {CAMERA}, set(document["bindings"]))
        for name, binding in document["bindings"].items():
            current = (ROOT / name).read_bytes()
            old = selectors.current_source_before_calendar_share_selectors(name, current)
            self.assertEqual((binding["after_sha256"], binding["after_bytes"]), (sha(current), len(current)), name)
            self.assertEqual((binding["before_sha256"], binding["before_bytes"]), (sha(old), len(old)), name)
            self.assertIs(old, selectors.source_before_calendar_share_selectors(name, old))
            forward = old
            for fragment in binding["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(fragment["before_fragment_sha256"], sha(before))
                self.assertEqual(fragment["after_fragment_sha256"], sha(after))
                self.assertEqual(1, forward.count(before))
                forward = forward.replace(before, after, 1)
            self.assertEqual(current, forward)

    def test_only_current_images_admit_and_fragment_or_identity_drift_refuses(self):
        document = selectors._document()
        for name, binding in document["bindings"].items():
            current = (ROOT / name).read_bytes()
            old = selectors.source_before_calendar_share_selectors(name, current)
            fragment = binding["fragments"][0]["after"].encode()
            displaced = current.replace(fragment, b"", 1) + fragment
            self.assertNotEqual(current, displaced)
            for bad in (old, current[:-1], current + b"\n", displaced, b"", None, bytearray(current),
                        b"x" * (selectors.MAX_SOURCE_BYTES + 1)):
                with self.subTest(name=name, kind=type(bad).__name__), self.assertRaises(ValueError):
                    selectors.current_source_before_calendar_share_selectors(name, bad)
        for identity in (None, Path(SHARED[0]), [], 1):
            with self.assertRaises(ValueError):
                selectors.current_source_before_calendar_share_selectors(identity, (ROOT / SHARED[0]).read_bytes())
        with self.assertRaises(ValueError):
            selectors.current_source_before_calendar_share_selectors(SHARED[0], (ROOT / SHARED[1]).read_bytes())
        name = SHARED[0]
        current = (ROOT / name).read_bytes()
        for field, value in (("before_fragment_sha256", "0" * 64), ("after_fragment_sha256", "0" * 64),
                             ("before", "missing preimage"), ("after", "missing afterimage")):
            altered = copy.deepcopy(document)
            altered["bindings"][name]["fragments"][0][field] = value
            with patch.object(selectors, "_document", return_value=altered), self.assertRaises(ValueError):
                selectors.source_before_calendar_share_selectors(name, current)

    def test_raw_selector_admission_occurs_once_before_camera_and_unchanged_dated_pins(self):
        for name in (*SHARED, CAMERA):
            current = (ROOT / name).read_bytes()
            with patch.object(selectors, "current_source_before_calendar_share_selectors",
                              wraps=selectors.current_source_before_calendar_share_selectors) as raw:
                ancestor = bridge.current_source_for_history(name, current)
                raw.assert_called_once_with(name, current)
            if name in SHARED:
                self.assertEqual(bridge._bindings()[name]["before_sha256"], sha(ancestor))
            else:
                self.assertEqual(selectors._document()["bindings"][name]["before_sha256"], sha(ancestor))
            previous = selectors.source_before_calendar_share_selectors(name, current)
            for bad in (previous, current[:-1], current + b"\n"):
                with patch.object(camera, "_bindings", side_effect=AssertionError("Invalid selector crossed its raw boundary")) as reader:
                    with self.assertRaises(ValueError):
                        bridge.current_source_for_history(name, bad)
                    reader.assert_not_called()
        workflow = ".github/workflows/gradle.yml"
        self.assertEqual("3d5d2ea0313055366bf6bc83550f7e2f40c50438c450508588db778fb6bb75f7",
                         sha(owned.current_source_before_owned_geometry(workflow, (ROOT / workflow).read_bytes())))

    def test_ancestor_peeling_keeps_old_unknown_and_unlisted_domains_separate(self):
        for name in selectors._document()["bindings"]:
            current = (ROOT / name).read_bytes()
            old = selectors.source_before_calendar_share_selectors(name, current)
            self.assertEqual(old, selectors.peel_calendar_share_selectors_for_history(name, current))
            self.assertIs(old, selectors.peel_calendar_share_selectors_for_history(name, old))
            unknown = current + b"\n# synthetic unreviewed selector\n"
            self.assertIs(unknown, selectors.peel_calendar_share_selectors_for_history(name, unknown))
            with self.assertRaises(ValueError):
                selectors.source_before_calendar_share_selectors(name, unknown)
            with self.assertRaises(ValueError):
                owned.current_source_before_owned_geometry(name, old)
        unlisted = b"not certified or guessed"
        for reader in (selectors.source_before_calendar_share_selectors,
                       selectors.current_source_before_calendar_share_selectors,
                       selectors.peel_calendar_share_selectors_for_history):
            self.assertIs(unlisted, reader("unlisted-source", unlisted))
        self.assertEqual(selectors._document()["unchanged_inputs"][CAMERA_SPEC], sha((ROOT / CAMERA_SPEC).read_bytes()))

    def test_owning_validator_requires_all_four_added_inputs_and_ordinary_current_images(self):
        document = selectors._document()
        self.assertEqual({"scripts/ci/ios_calendar_native_focus.py", "scripts/ci/macos_share_native_focus.py",
                          "scripts/ci/test_ios_calendar_native_focus.py", "scripts/ci/test_macos_share_native_focus.py"},
                         set(document["added_inputs"]))
        self.assertEqual(LAYER_SHA256, sha(image_history.current_source_before_image_launch(LAYER, (ROOT / LAYER).read_bytes())))
        paths = (set(document["bindings"]) | set(document["added_inputs"]) |
                 set(document["unchanged_inputs"]) | {selectors.SPEC_RELATIVE})
        image = image_history._document()
        paths |= (set(image["bindings"]) | set(image["added_inputs"]) |
                  set(image["unchanged_inputs"]) | {image_history.SPEC_RELATIVE})
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-selectors617-") as temporary:
            root = Path(temporary)
            for name in paths:
                target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / name).read_bytes())
            self.assertTrue(selectors.validate_current_sources(root))
            for name in document["added_inputs"]:
                target = root / name; original = target.read_bytes()
                target.unlink()
                with self.assertRaises(FileNotFoundError): selectors.validate_current_sources(root)
                target.symlink_to(ROOT / name)
                with self.assertRaises(ValueError): selectors.validate_current_sources(root)
                target.unlink(); target.write_bytes(original)
                backing = target.with_name(target.name + ".backing"); backing.write_bytes(original)
                target.unlink(); target.hardlink_to(backing)
                with self.assertRaises(ValueError): selectors.validate_current_sources(root)
                target.unlink(); backing.unlink(); target.write_bytes(original + b"\n")
                with self.assertRaises(ValueError): selectors.validate_current_sources(root)
                target.write_bytes(original)
            for name in document["bindings"]:
                target = root / name; original = target.read_bytes()
                target.write_bytes(selectors.source_before_calendar_share_selectors(name, original))
                with self.assertRaises(ValueError): selectors.validate_current_sources(root)
                target.write_bytes(original)
        raw = selectors.SPEC_PATH.read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            with patch.object(selectors, "SPEC_PATH", path):
                for bad in (raw + b"\n", b"{}", b"", b"x" * (selectors.MAX_SPEC_BYTES + 1)):
                    path.write_bytes(bad)
                    with self.assertRaises(ValueError): selectors._document()
                path.unlink(); path.symlink_to(ROOT / selectors.SPEC_RELATIVE)
                with self.assertRaises(ValueError): selectors._document()
                path.unlink(); backing = path.with_name("backing.json"); backing.write_bytes(raw)
                path.hardlink_to(backing)
                with self.assertRaises(ValueError): selectors._document()
        with self.assertRaises(ValueError): selectors._unique([("duplicate", 1), ("duplicate", 2)])

    def test_only_three_transparent_camera_hooks_and_unchanged_recovery_mirror_pins(self):
        current = (ROOT / CAMERA).read_bytes()
        before = selectors.source_before_calendar_share_selectors(CAMERA, current)
        class TransparentHooks(ast.NodeTransformer):
            def visit_ImportFrom(self, node):
                return None if node.module == "calendar_share_selector_source_projection" else node
            def visit_Assign(self, node):
                node = self.generic_visit(node)
                if (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and
                        node.targets[0].id == "payload" and isinstance(node.value, ast.Name) and
                        node.value.id == "payload"):
                    return None
                return node
            def visit_Call(self, node):
                node = self.generic_visit(node)
                if isinstance(node.func, ast.Name) and node.func.id in {
                        "current_source_before_calendar_share_selectors", "peel_calendar_share_selectors_for_history"}:
                    if len(node.args) != 2 or node.keywords:
                        raise AssertionError("One exact binary source-stage hook is required")
                    return node.args[1]
                return node
        self.assertEqual(ast.dump(ast.parse(before), include_attributes=False),
                         ast.dump(TransparentHooks().visit(ast.parse(current)), include_attributes=False))
        for name, expected in selectors._document()["unchanged_inputs"].items():
            self.assertEqual(expected, sha((ROOT / name).read_bytes()), name)
        self.assertEqual("175c69071fa0bf8bbf106b6cc127ae6cd90344512d70f960b5447a4d2b9dc3c4",
                         sha((ROOT / "scripts/ci/ios_owned_geometry_fixture_recovery.py").read_bytes()))
        for name in (LAYER, CAMERA):
            for node in ast.walk(ast.parse((ROOT / name).read_bytes())):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        self.assertNotIn(node.func.id, {"eval", "exec", "compile", "open", "__import__"})
                    elif isinstance(node.func, ast.Attribute):
                        self.assertNotIn(node.func.attr, {"parse_home_task", "parse_recent_home_baseline", "run",
                                                         "Popen", "control", "write_bytes", "write_text"})


if __name__ == "__main__":
    unittest.main()
