# SPDX-License-Identifier: Apache-2.0
"""NEW exact Camera source/ancestor models; no restored code or native execution."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import android_external328_source_projection as bridge
import camera_ios_ownership_native_focus as focus
import camera_ios_ownership_source_projection as camera
import platform_recovery659_source_projection as newest
import webview_content_policy_source_projection as webview
import ci_source_domain740 as source_domain
import ci_source_recovery740_742 as source_recovery

ROOT = Path(__file__).resolve().parents[2]
WEBVIEW874_GUARD_SHA256 = "c8b75a6b06454135db4b6143987855e27588648d4eb3aefc0d72611fc35ac875"
WEBVIEW874_SPEC_SHA256 = "c44400087570740d3248704c2165c3222229f2c05ff1a2a3840dbda9aa04b916"
WEBVIEW648_FIXTURE_SHA256 = "75b52cd2abc6816bb23e02c01d89b7c5cade3219e737b18a9fe2ca17fd25c550"
SEALED_HOST_SHA256 = "b4477359b87faf19df236e3511f1545cb1e411f5ba6d8743316fbb2c15c51b9c"
PRODUCTION = "calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt"


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def copy_fixture(root):
    """Owning46/controls plus separately copied dependencies, never enrollment."""
    inputs = (camera.fixture_inputs() | source_domain.dependency_inputs() |
              source_recovery.dependency_inputs())
    for name in inputs:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())


class CameraIosOwnershipSourceProjectionControls(unittest.TestCase):
    def test_nine_complete_routing_images_and45_unique_fragments_restore_exact_final874_preimages(self):
        document = camera._document()
        self.assertEqual((9, 45), (len(document["bindings"]), sum(len(row["fragments"]) for row in document["bindings"].values())))
        for name, row in document["bindings"].items():
            raw_current = (ROOT / name).read_bytes()
            prior = camera.current_source_before_camera_ios_ownership(name, raw_current)
            raw = newest.source_before_platform_recovery659(name, raw_current)
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(prior), len(prior)))
            self.assertEqual((row["after_sha256"], row["after_bytes"]), (sha(raw), len(raw)))
            self.assertIs(prior, camera.source_before_camera_ios_ownership(name, prior))
            forward = prior
            for fragment in row["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual((sha(before), sha(after)), (fragment["before_fragment_sha256"], fragment["after_fragment_sha256"]))
                self.assertEqual(1, forward.count(before))
                forward = forward.replace(before, after, 1)
            self.assertEqual(raw, forward)
        self.assertEqual(WEBVIEW874_GUARD_SHA256, document["bindings"][webview.SOURCE_RELATIVE]["before_sha256"])
        self.assertEqual(WEBVIEW874_SPEC_SHA256, webview.SPEC_SHA256)

    def test_one_latest_camera_raw_ingress_precedes_only_exact_webview_share_ui_and_older_ancestors(self):
        for name in camera.BOUND_PATHS:
            raw = (ROOT / name).read_bytes()
            import macos_share_ci668_composition as latest
            if name in latest.ANDROID_BOUND_PATHS:
                with patch.object(latest, "source_before_android_lifecycle",
                                  wraps=latest.source_before_android_lifecycle) as newest:
                    with patch.object(camera, "current_source_before_camera_ios_ownership",
                                      side_effect=AssertionError("Android ancestor was strictly readmitted")) as nested:
                        ancestor = bridge.current_source_for_history(name, raw)
                        newest.assert_called_once_with(name, raw)
                        nested.assert_not_called()
                        self.assertIsInstance(ancestor, bytes)
            else:
                with patch.object(camera, "current_source_before_camera_ios_ownership", wraps=camera.current_source_before_camera_ios_ownership) as newest:
                    ancestor = bridge.current_source_for_history(name, raw)
                    newest.assert_called_once_with(name, raw)
                    self.assertIsInstance(ancestor, bytes)
        source = (ROOT / webview.SOURCE_RELATIVE).read_text()
        self.assertEqual(1, source.count("from camera_ios_ownership_source_projection import current_source_before_camera_ios_ownership"))
        self.assertEqual(2, source.count("from camera_ios_ownership_source_projection import peel_camera_ios_ownership_for_history"))

    def test_old_partial_displaced_unknown_foreign_type_and_unbounded_current_images_refuse_before_webview(self):
        for name in camera.BOUND_PATHS:
            raw = (ROOT / name).read_bytes()
            row = camera._document()["bindings"][name]
            prior = camera.source_before_camera_ios_ownership(name, raw)
            fragment = row["fragments"][0]["after"].encode()
            displaced = raw.replace(fragment, b"", 1) + fragment
            other = (ROOT / next(path for path in camera.BOUND_PATHS if path != name)).read_bytes()
            for candidate in (prior, raw[:-1], raw + b"\n", displaced, other, b"", None,
                              raw.decode(), bytearray(raw), b"x" * (camera.MAX_SOURCE_BYTES + 1)):
                with patch.object(webview, "source_before_content_policy", side_effect=AssertionError("Unqualified Camera crossed its ingress")) as older:
                    with self.assertRaises(ValueError):
                        webview.current_source_before_content_policy(name, candidate)
                    older.assert_not_called()

    def test_exact_history_peeling_is_idempotent_and_unknown_bytes_never_certify_current_sources(self):
        for name in camera.BOUND_PATHS:
            raw = (ROOT / name).read_bytes()
            prior = camera.source_before_camera_ios_ownership(name, raw)
            self.assertEqual(prior, camera.peel_camera_ios_ownership_for_history(name, raw))
            self.assertIs(prior, camera.peel_camera_ios_ownership_for_history(name, prior))
            unknown = prior + b"\n# unknown source model\n"
            self.assertIs(unknown, camera.peel_camera_ios_ownership_for_history(name, unknown))
            for candidate in (prior, unknown):
                with self.assertRaises(ValueError):
                    camera.current_source_before_camera_ios_ownership(name, candidate)
            with self.assertRaises(ValueError):
                camera.source_before_camera_ios_ownership(name, unknown)
        unlisted = b"Unlisted bytes are not certified or executed"
        for reader in (camera.source_before_camera_ios_ownership, camera.current_source_before_camera_ios_ownership,
                       camera.peel_camera_ios_ownership_for_history):
            self.assertIs(unlisted, reader("unlisted-source", unlisted))
            with self.assertRaises(ValueError):
                reader(Path("unlisted-source"), unlisted)

    def test_owning46_ordinary_inputs_and_finite_fixture_union_refuse_missing_drift_links_and_agents_binding(self):
        document = camera._document()
        expected = set(document["bindings"]) | set(document["added_inputs"]) | set(document["unchanged_inputs"]) | {camera.SPEC_RELATIVE}
        self.assertEqual(46, len(expected))
        self.assertNotIn("AGENTS.md", expected)
        self.assertNotIn("AGENTS.md", camera.fixture_inputs())
        self.assertEqual(expected | {camera.SOURCE_RELATIVE, "scripts/ci/test_camera_ios_ownership_source_projection.py"} |
                         newest.fixture_inputs(), camera.fixture_inputs())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            copy_fixture(root)
            self.assertTrue(camera.validate_current_sources(root))
            (root / "AGENTS.md").write_bytes(b"unrelated maintainer instructions\x00\xff")
            self.assertTrue(camera.validate_current_sources(root))
            for name in sorted(document["added_inputs"] | {PRODUCTION: "unused"}):
                target = root / name
                raw = target.read_bytes()
                target.unlink()
                with self.assertRaises(FileNotFoundError):
                    camera.validate_current_sources(root)
                target.write_bytes(raw + b"\n")
                with self.assertRaises(ValueError):
                    camera.validate_current_sources(root)
                target.unlink()
                target.symlink_to(ROOT / name)
                with self.assertRaises(ValueError):
                    camera.validate_current_sources(root)
                target.unlink()
                backing = target.with_name(target.name + ".backing")
                backing.write_bytes(raw)
                target.hardlink_to(backing)
                with self.assertRaises(ValueError):
                    camera.validate_current_sources(root)
                target.unlink()
                backing.unlink()
                target.write_bytes(raw)
            self.assertTrue(camera.validate_current_sources(root))

    def test_manifest_schema_duplicate_nonfinite_boolean_hash_and_fragment_identity_negatives_refuse(self):
        raw = (ROOT / camera.SPEC_RELATIVE).read_bytes()
        document = camera._document()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            for candidate in (raw + b"\n", b'{"schema_version":1,"schema_version":1}', b"{}", b"[]", b'{"schema_version":NaN}'):
                path.write_bytes(candidate)
                with patch.object(camera, "SPEC_PATH", path), self.assertRaises(ValueError):
                    camera._document()
            mutations = (
                lambda d: d.update(schema_version=True),
                lambda d: d.update(scope="native acceptance"),
                lambda d: d["bindings"].pop(next(iter(d["bindings"]))),
                lambda d: d["added_inputs"].update({"foreign.kt": "a" * 64}),
                lambda d: d["unchanged_inputs"].update({"AGENTS.md": "a" * 64}),
                lambda d: d["bindings"]["scripts/ci/library_tests.py"].update(after_bytes=True),
                lambda d: d["bindings"]["scripts/ci/library_tests.py"].update(after_sha256="A" * 64),
            )
            for mutate in mutations:
                bad = copy.deepcopy(document)
                mutate(bad)
                candidate = json.dumps(bad).encode()
                path.write_bytes(candidate)
                with patch.object(camera, "SPEC_PATH", path), patch.object(camera, "SPEC_SHA256", sha(candidate)), self.assertRaises(ValueError):
                    camera._document()
        name = "scripts/ci/library_tests.py"
        bad = copy.deepcopy(document)
        bad["bindings"][name]["fragments"][0]["after_fragment_sha256"] = "a" * 64
        with patch.object(camera, "_document", return_value=bad), self.assertRaises(ValueError):
            camera.source_before_camera_ios_ownership(name, (ROOT / name).read_bytes())
        bad = copy.deepcopy(document)
        fragment = bad["bindings"][name]["fragments"][0]["after"].encode()
        duplicate = (ROOT / name).read_bytes() + fragment
        bad["bindings"][name].update(after_sha256=sha(duplicate), after_bytes=len(duplicate))
        with patch.object(camera, "_document", return_value=bad), self.assertRaises(ValueError):
            camera.source_before_camera_ios_ownership(name, duplicate)

    def test_only_six_transparent_webview_hooks_and_narrow_mirrors_keep_final874_and_exact648_pins(self):
        document = camera._document()
        self.assertEqual(6, len(document["bindings"][webview.SOURCE_RELATIVE]["fragments"]))
        prior = camera.source_before_camera_ios_ownership(webview.SOURCE_RELATIVE, (ROOT / webview.SOURCE_RELATIVE).read_bytes())
        self.assertEqual(WEBVIEW874_GUARD_SHA256, sha(prior))
        self.assertIn(b'NONEXECUTABLE_MAINTAINER_INPUTS = frozenset({"AGENTS.md"})', prior)
        fixture = "scripts/ci/test_webview_content_policy_fixture.py"
        self.assertEqual(WEBVIEW648_FIXTURE_SHA256, webview._document()["unchanged_inputs"][fixture])
        self.assertEqual(WEBVIEW648_FIXTURE_SHA256, sha((ROOT / fixture).read_bytes()))
        source_name = "scripts/ci/test_webview_content_policy_source_projection.py"
        current = (ROOT / source_name).read_bytes()
        old = camera.source_before_camera_ios_ownership(source_name, current)
        self.assertIn(('GUARD_SHA256 = "' + WEBVIEW874_GUARD_SHA256 + '"').encode(), old)
        def assertions(payload):
            return [ast.unparse(node.func) for node in ast.walk(ast.parse(payload)) if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute) and node.func.attr.startswith("assert")]
        self.assertEqual(assertions(old), assertions(current))
        old_functions = {node.name: node for node in ast.walk(ast.parse(old)) if isinstance(node, ast.FunctionDef)}
        new_functions = {node.name: node for node in ast.walk(ast.parse(current)) if isinstance(node, ast.FunctionDef)}
        for method in ("test_only_maintainer_instructions_are_not_executable_inputs_or_fixture_prerequisites",
                       "test_exact_reviewed648_predecessor_and_every_other_owned_input_remain_required"):
            self.assertEqual(ast.dump(old_functions[method], include_attributes=False), ast.dump(new_functions[method], include_attributes=False))

    def test_final_photos_host_is_distinct_and_all_five_native_bodies_production_and_public_apis_are_held(self):
        document = camera._document()
        host = document["bindings"][focus.HOST_SOURCE]
        self.assertEqual(SEALED_HOST_SHA256, host["before_sha256"])
        self.assertNotEqual(host["before_sha256"], host["after_sha256"])
        self.assertEqual(focus.SOURCE_SHA256[focus.HOST_SOURCE], host["after_sha256"])
        self.assertEqual(focus.SOURCE_SHA256[focus.TEST_SOURCE], sha((ROOT / focus.TEST_SOURCE).read_bytes()))
        self.assertEqual("3956439ee461c54ad26f7b86eef6939379d2d0c8918948072119411c8802a729", sha((ROOT / PRODUCTION).read_bytes()))
        self.assertNotIn(PRODUCTION, document["bindings"])
        self.assertNotIn(focus.TEST_SOURCE, document["bindings"])
        host_source = (ROOT / focus.HOST_SOURCE).read_text()
        self.assertLess(host_source.index("if (!observeOwnedCameraPhotoAuthorization())"), host_source.index('Worker.start(name = "nativecmpkit-owned-camera'))
        self.assertIn("PHPhotoLibrary.authorizationStatusForAccessLevel(PHAccessLevelReadWrite)", host_source)
        self.assertIn("NSBundle.mainBundle.bundleIdentifier", host_source)
        self.assertIn("NSProcessInfo.processInfo.processIdentifier", host_source)
        self.assertNotIn("requestAuthorization", host_source)
        self.assertEqual("17a3fa29c8b82651d40b2cc820a83855fb467015b7acd51f8ffa3155310d54e5",
                         sha((ROOT / "scripts/ci/test_camera_ios_terminal_barrier_source.py").read_bytes()))


if __name__ == "__main__":
    unittest.main()
