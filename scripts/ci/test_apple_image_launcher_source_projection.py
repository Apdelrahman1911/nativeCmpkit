# SPDX-License-Identifier: Apache-2.0
"""NEW exact-ingress controls only; no accepted image models or native replay."""
import ast
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import apple_image_launcher_source_projection as history
import ios_ui_related_source_projection as ui_history
import calendar_share_selector_source_projection as selectors
import camera_home_affinity_source_projection as camera
import android_external328_source_projection as bridge
import ios_popover_anchor_source_projection as anchor
import ios_popover_geometry_source_projection as geometry
import ios_worker_completion_source_projection as completion
import ios_sheet_repeat_source_projection as repeat
import ios_modal_worker_source_projection as worker
import ios_modal_xcui_source_projection as xcui
import ios_modal_ownership_source_projection as modal
import test_ui_alert_important_recovery as alert_history

ROOT = Path(__file__).resolve().parents[2]
HELPER = "scripts/ci/apple_image_launcher_source_projection.py"
HELPER_SHA256 = "5f13a039c95d4a9f0ce7fbf3026da3de572370aaf2bb80bb0dd60bfe6c65875a"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def launcher_ancestors():
    """Only exact inverse arithmetic over unchanged source manifests/pins."""
    current = (ROOT / history.LAUNCHER).read_bytes()
    base = history.source_before_image_launch(history.LAUNCHER, current)
    geometry_before = geometry.source_before_geometry(history.LAUNCHER, base)
    completion_before = completion.source_before_worker_completion(history.LAUNCHER, geometry_before)
    modal_before = xcui.source_before_modal_xcui(history.LAUNCHER, completion_before)
    old = modal_before
    binding = alert_history.SHARE_ALERT153_REBASE[history.LAUNCHER]
    if sha(old) != binding["share_composed_sha256"]:
        raise AssertionError("The unchanged original alert launcher pin is required")
    for row in reversed(binding["fragments"]):
        before, after = row["before"].encode(), row["after"].encode()
        if (sha(before) != row["before_fragment_sha256"] or sha(after) != row["after_fragment_sha256"] or
                old.count(after) != 1):
            raise AssertionError("Only the unchanged complete alert inverse is required")
        old = old.replace(after, before, 1)
    if sha(old) != binding["original153_sha256"]:
        raise AssertionError("The original complete alert launcher must be restored")
    return [base, geometry_before, completion_before, modal_before, old]


class ImageLauncherSourceProjectionControls(unittest.TestCase):
    def test_complete_image_calendar_and_control_inverses_restore_exact_parents_and_forward(self):
        document = history._document()
        self.assertEqual({history.LAUNCHER, history.SELECTOR, history.CONTROL}, set(document["bindings"]))
        self.assertEqual(8, sum(len(row["fragments"]) for row in document["bindings"].values()))
        self.assertEqual(HELPER_SHA256, sha(ui_history.peel_ui_related_for_history(HELPER, (ROOT / HELPER).read_bytes())))
        for name, row in document["bindings"].items():
            raw_current = (ROOT / name).read_bytes()
            current = ui_history.peel_ui_related_for_history(name, raw_current)
            previous = history.current_source_before_image_launch(name, raw_current)
            self.assertEqual((row["after_sha256"], row["after_bytes"]), (sha(current), len(current)), name)
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(previous), len(previous)), name)
            self.assertIs(previous, history.source_before_image_launch(name, previous))
            forward = previous
            for fragment in row["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(fragment["before_fragment_sha256"], sha(before))
                self.assertEqual(fragment["after_fragment_sha256"], sha(after))
                self.assertEqual(1, forward.count(before))
                forward = forward.replace(before, after, 1)
            self.assertEqual(current, forward)

    def test_current_rejects_old_partial_displaced_drifted_and_foreign_payloads(self):
        foreign = (ROOT / ".github/workflows/gradle.yml").read_bytes()
        for name, row in history._document()["bindings"].items():
            current = (ROOT / name).read_bytes()
            previous = history.source_before_image_launch(name, current)
            fragment = row["fragments"][0]["after"].encode()
            displaced = current.replace(fragment, b"", 1) + fragment
            self.assertNotEqual(current, displaced)
            for bad in (previous, current[:-1], current + b"\n", current.replace(b"\n", b"\r\n"),
                        displaced, foreign, b"", None, bytearray(current), current.decode(),
                        b"x" * (history.MAX_SOURCE_BYTES + 1)):
                with self.subTest(name=name, kind=type(bad).__name__):
                    with patch.object(camera, "_bindings", side_effect=AssertionError("Invalid image crossed raw ingress")) as older:
                        with self.assertRaises(ValueError):
                            bridge.current_source_for_history(name, bad)
                        older.assert_not_called()

    def test_one_raw_ingress_precedes_only_ancestor_nested_readers(self):
        for name in history.BOUND_PATHS:
            current = (ROOT / name).read_bytes()
            with patch.object(history, "current_source_before_image_launch",
                              wraps=history.current_source_before_image_launch) as raw:
                previous = history.read_current_source_for_history(ROOT / name, ROOT)
                raw.assert_called_once_with(name, current)
                if name == history.LAUNCHER:
                    self.assertEqual(xcui._bindings()[name]["before_sha256"], sha(previous))
                    for reader in (geometry.source_before_geometry, completion.source_before_worker_completion,
                                   worker.source_before_modal_worker, modal.source_before_modal_ownership):
                        self.assertIsInstance(reader(name, current), bytes)
                else:
                    self.assertEqual(history._document()["bindings"][name]["before_sha256"], sha(previous))
                self.assertEqual(1, raw.call_count)

    def test_only_fixed_pinned_launcher_ancestors_are_transparent(self):
        ancestors = launcher_ancestors()
        self.assertEqual(history.PINNED_LAUNCHER_ANCESTORS, {sha(raw) for raw in ancestors})
        for raw in ancestors:
            self.assertIs(raw, history.peel_image_launch_for_history(history.LAUNCHER, raw))
            with self.assertRaises(ValueError):
                history.current_source_before_image_launch(history.LAUNCHER, raw)
            for bad in (raw + b"\n", raw[:-1], raw.replace(b"\n", b"\r\n")):
                with self.assertRaisesRegex(ValueError, "exact current source or a fixed pinned ancestor"):
                    history.peel_image_launch_for_history(history.LAUNCHER, bad)
        for name in (history.SELECTOR, history.CONTROL):
            raw = history.source_before_image_launch(name, (ROOT / name).read_bytes())
            self.assertIs(raw, history.peel_image_launch_for_history(name, raw))
            with self.assertRaises(ValueError):
                history.peel_image_launch_for_history(name, ancestors[0])

    def test_unchanged_launcher_pin_chain_reaches_worker_and_modal(self):
        name = history.LAUNCHER
        current = (ROOT / name).read_bytes()
        geometry_before = geometry.current_source_before_geometry(name, current)
        self.assertEqual(geometry._bindings()[name]["before_sha256"], sha(geometry_before))
        self.assertEqual(geometry_before, anchor.current_source_before_popover_anchor(name, current))
        completion_before = completion.current_source_before_worker_completion(name, current)
        self.assertEqual(completion._bindings()[name]["before_sha256"], sha(completion_before))
        self.assertEqual(completion_before, repeat.current_source_before_sheet_repeat(name, completion_before))
        self.assertEqual(completion_before, worker.current_source_before_modal_worker(name, current))
        modal_before = xcui.current_source_before_modal_xcui(name, current)
        self.assertEqual(xcui._bindings()[name]["before_sha256"], sha(modal_before))
        self.assertEqual(modal_before, modal.current_source_before_modal_ownership(name, current))
        self.assertEqual(modal_before, bridge.current_source_for_history(name, current))

    def test_exact_bound_identity_never_guesses_foreign_relative_paths(self):
        current = (ROOT / history.LAUNCHER).read_bytes()
        for identity in (None, Path(history.LAUNCHER), [], 1, True):
            for reader in (history.source_before_image_launch, history.current_source_before_image_launch,
                           history.peel_image_launch_for_history):
                with self.assertRaises(ValueError):
                    reader(identity, current)
        for name in history.BOUND_PATHS - {history.LAUNCHER}:
            with self.assertRaises(ValueError):
                history.current_source_before_image_launch(name, current)
        # Transparent unlisted bytes make no admission claim and are never
        # digest-guessed into a listed identity at the new path boundary.
        for reader in (history.source_before_image_launch, history.current_source_before_image_launch,
                       history.peel_image_launch_for_history):
            self.assertIs(current, reader("unlisted-source", current))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "unlisted-source"; path.write_bytes(current)
            with self.assertRaises(ValueError):
                history.read_current_source_for_history(path, root)

    def test_manifest_drift_schema_and_alias_links_refuse(self):
        raw = history.SPEC_PATH.read_bytes()
        self.assertEqual(history.SPEC_SHA256, sha(raw))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            with patch.object(history, "SPEC_PATH", path):
                for bad in (raw + b"\n", b"{}", b"", b"x" * (history.MAX_SPEC_BYTES + 1)):
                    path.write_bytes(bad)
                    with self.assertRaises(ValueError): history._document()
                path.write_bytes(raw)
                self.assertEqual(history.BOUND_PATHS, set(history._document()["bindings"]))
                path.unlink(); path.symlink_to(ROOT / history.SPEC_RELATIVE)
                with self.assertRaises(ValueError): history._document()
                path.unlink(); backing = path.with_name("backing.json"); backing.write_bytes(raw)
                path.hardlink_to(backing)
                with self.assertRaises(ValueError): history._document()
                path.unlink(); backing.unlink()
                import json
                path.write_bytes(raw)
                document = history._document()
                for key, value in (("schema_version", True), ("bindings", {}), ("added_inputs", {}),
                                   ("unchanged_inputs", None)):
                    changed = copy.deepcopy(document); changed[key] = value
                    bad = json.dumps(changed).encode(); path.write_bytes(bad)
                    with patch.object(history, "SPEC_SHA256", sha(bad)), self.assertRaises(ValueError):
                        history._document()
        with self.assertRaises(ValueError): history._unique([("duplicate", 1), ("duplicate", 2)])

    def test_fragment_hashes_unique_sites_and_complete_restoration_are_mandatory(self):
        name = history.LAUNCHER
        current = ui_history.peel_ui_related_for_history(name, (ROOT / name).read_bytes())
        self.assertEqual(history._document()["bindings"][name]["after_sha256"], sha(current))
        for field, value in (("before", "missing"), ("after", "missing"), ("before", ""), ("after", ""),
                             ("before_fragment_sha256", "0" * 64), ("after_fragment_sha256", "0" * 64)):
            changed = copy.deepcopy(history._document())
            changed["bindings"][name]["fragments"][0][field] = value
            with patch.object(history, "_document", return_value=changed), self.assertRaises(ValueError):
                history.source_before_image_launch(name, current)
        for field, value in (("before_sha256", "0" * 64), ("after_sha256", "0" * 64),
                             ("before_bytes", len(current)), ("after_bytes", len(current) + 1)):
            changed = copy.deepcopy(history._document()); changed["bindings"][name][field] = value
            with patch.object(history, "_document", return_value=changed), self.assertRaises(ValueError):
                history.source_before_image_launch(name, current)
        changed = copy.deepcopy(history._document()); row = changed["bindings"][name]
        duplicate = current + row["fragments"][0]["after"].encode()
        row.update(after_sha256=sha(duplicate), after_bytes=len(duplicate))
        with patch.object(history, "_document", return_value=changed), self.assertRaises(ValueError):
            history.source_before_image_launch(name, duplicate)
        changed = copy.deepcopy(history._document()); row = changed["bindings"][name]
        fragment = row["fragments"][0]; fragment["before"] = "import json\n"
        fragment["before_fragment_sha256"] = sha(fragment["before"].encode())
        restored = current.replace(fragment["after"].encode(), fragment["before"].encode(), 1)
        row.update(before_sha256=sha(restored), before_bytes=len(restored))
        self.assertGreater(restored.count(fragment["before"].encode()), 1)
        with patch.object(history, "_document", return_value=changed), self.assertRaises(ValueError):
            history.source_before_image_launch(name, current)

    def test_confined_raw_read_rejects_foreign_symlink_and_hardlink_paths(self):
        current = (ROOT / history.LAUNCHER).read_bytes()
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as foreign_directory:
            root = Path(directory); foreign = Path(foreign_directory)
            path = root / history.LAUNCHER; path.parent.mkdir(parents=True); path.write_bytes(current)
            self.assertEqual(xcui._bindings()[history.LAUNCHER]["before_sha256"],
                             sha(history.read_current_source_for_history(path, root)))
            foreign_path = foreign / history.LAUNCHER; foreign_path.parent.mkdir(parents=True); foreign_path.write_bytes(current)
            for candidate, checkout in ((foreign_path, root), (Path(history.LAUNCHER), root),
                                        (path, Path("relative-checkout")), (str(path), root)):
                with self.assertRaises(ValueError): history.read_current_source_for_history(candidate, checkout)
            path.unlink(); path.symlink_to(ROOT / history.LAUNCHER)
            with self.assertRaises(ValueError): history.read_current_source_for_history(path, root)
            path.unlink(); path.hardlink_to(foreign_path)
            with self.assertRaises(ValueError): history.read_current_source_for_history(path, root)
            path.unlink(); path.parent.rmdir(); (root / "scripts").rmdir()
            (root / "scripts").symlink_to(foreign / "scripts", target_is_directory=True)
            with self.assertRaises(ValueError): history.read_current_source_for_history(path, root)
            alias = foreign / "root-alias"; alias.symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError): history.read_current_source_for_history(alias / history.LAUNCHER, alias)

    def test_latest_three_hooks_and_mirror_qualification_preserve_original_bodies(self):
        raw_current = (ROOT / history.SELECTOR).read_bytes()
        current = ui_history.peel_ui_related_for_history(history.SELECTOR, raw_current)
        old = history.current_source_before_image_launch(history.SELECTOR, raw_current)
        class ExactImageHooks(ast.NodeTransformer):
            def visit_ImportFrom(self, node):
                return None if node.module == "apple_image_launcher_source_projection" else node
            def visit_Import(self, node):
                return None if ast.unparse(node) == "import apple_image_launcher_source_projection as image_history" else node
            def visit_Expr(self, node):
                return None if ast.unparse(node) == "image_history.validate_current_sources(root)" else self.generic_visit(node)
            def visit_Call(self, node):
                node = self.generic_visit(node)
                if isinstance(node.func, ast.Name) and node.func.id in {
                        "current_source_before_image_launch", "peel_image_launch_for_history"}:
                    if len(node.args) != 2 or node.keywords:
                        raise AssertionError("Only exact binary image-source hooks are qualified")
                    return node.args[1]
                return node
            def visit_Assign(self, node):
                node = self.generic_visit(node)
                return None if ast.unparse(node) == "payload = payload" else node
        self.assertEqual(ast.dump(ast.parse(old), include_attributes=False),
                         ast.dump(ExactImageHooks().visit(ast.parse(current)), include_attributes=False))
        source = current.decode()
        self.assertEqual(2, source.count("payload = peel_image_launch_for_history(relative, payload)"))
        self.assertEqual(1, source.count("payload = current_source_before_image_launch(relative, payload)"))
        raw_control = (ROOT / history.CONTROL).read_bytes()
        control = ui_history.peel_ui_related_for_history(history.CONTROL, raw_control)
        previous = history.current_source_before_image_launch(history.CONTROL, raw_control)
        class ExactHashOperand(ast.NodeTransformer):
            def visit_Call(self, node):
                node = self.generic_visit(node)
                if (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and
                        node.func.value.id == "image_history" and node.func.attr == "current_source_before_image_launch"):
                    if len(node.args) != 2 or node.keywords or ast.unparse(node.args[0]) != "LAYER":
                        raise AssertionError("Only the exact retained LAYER hash operand is qualified")
                    return node.args[1]
                return node
        def obligations(raw):
            tree = ExactHashOperand().visit(ast.parse(raw))
            methods = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")]
            assertions = [ast.dump(node, include_attributes=False) for node in ast.walk(tree)
                          if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
                          isinstance(node.func.value, ast.Name) and node.func.value.id == "self" and
                          node.func.attr.startswith("assert")]
            return methods, assertions
        self.assertEqual(obligations(previous), obligations(control))
        self.assertIn('LAYER_SHA256 = "9e08ae99513cc2c29688b69668f78a5ba319d1e40a7b615519382f14ad728a64"', control.decode())

    def test_image609_sources_hook_finally_launch_argv_and_deadline_are_unchanged(self):
        document = history._document()
        for name, digest in document["added_inputs"].items():
            self.assertEqual(digest, sha((ROOT / name).read_bytes()), name)
        current = ui_history.peel_ui_related_for_history(
            history.LAUNCHER, (ROOT / history.LAUNCHER).read_bytes())
        old = history.source_before_image_launch(history.LAUNCHER, current)
        row = document["bindings"][history.LAUNCHER]["fragments"][0]
        self.assertEqual(10, len(row["after"].splitlines()) - len(row["before"].splitlines()))
        self.assertEqual("71d1b3092af3f4701b869019abbe15eb843431a8d0768af7273eb79f5418f4c7", row["before_fragment_sha256"])
        self.assertEqual("65541c4dda1daff931ee7697b55183829b0b27c2c7ccdad99df6d0db85eede44", row["after_fragment_sha256"])
        def retained(raw):
            tree = ast.parse(raw)
            final = [ast.dump(ast.Module(body=node.finalbody, type_ignores=[]), include_attributes=False)
                     for node in ast.walk(tree) if isinstance(node, ast.Try) and node.finalbody]
            launch = [ast.dump(node, include_attributes=False) for node in ast.walk(tree)
                      if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "forward_application"]
            timeout = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "application_timeout_seconds")
            self.assertIn("return 360", ast.unparse(timeout))
            return final, launch, ast.dump(timeout, include_attributes=False)
        self.assertEqual(retained(old), retained(current))
        self.assertIn("Unknown syntax/query observations cannot replace the original", row["after"])

    def test_old_pins_and_guard_bodies_are_not_refreshed_or_replayed(self):
        document = history._document()
        for name, digest in document["unchanged_inputs"].items():
            self.assertEqual(digest, sha((ROOT / name).read_bytes()), name)
        self.assertEqual("175c69071fa0bf8bbf106b6cc127ae6cd90344512d70f960b5447a4d2b9dc3c4",
                         sha((ROOT / "scripts/ci/ios_owned_geometry_fixture_recovery.py").read_bytes()))
        self.assertEqual("0a9267ec0455668688ce3a4a76dc20f534294bf2d48edf1f4c80fd3e43a34bab",
                         sha(selectors.SPEC_PATH.read_bytes()))
        self.assertEqual("51cc224488eb366034f8edea83f1a31465f8818059bad96a802a1fff0aa655ca",
                         sha(camera.SPEC_PATH.read_bytes()))
        for node in ast.walk(ast.parse((ROOT / HELPER).read_bytes())):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, {"eval", "exec", "compile", "open", "__import__"})
                elif isinstance(node.func, ast.Attribute):
                    self.assertNotIn(node.func.attr, {"run", "Popen", "control", "observe", "write_bytes", "write_text"})
        self.assertIs(document["accepted_image_controls_replayed"], False)
        self.assertEqual(0, document["native_tests_executed"])
        self.assertIs(document["issue141_closed"], False)


if __name__ == "__main__":
    unittest.main()
