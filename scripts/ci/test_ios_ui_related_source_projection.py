# SPDX-License-Identifier: Apache-2.0
"""NEW exact UI ingress/custody controls; no original host query or native replay."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import ios_ui_related_source_projection as history
import apple_image_launcher_source_projection as image
import calendar_share_selector_source_projection as calendar
import camera_home_affinity_source_projection as camera
import android_external328_source_projection as bridge
import ios_ui_related_native_focus as related

ROOT = Path(__file__).resolve().parents[2]
GUARD = "scripts/ci/ios_ui_related_source_projection.py"
GUARD_SHA256 = "b6e5bdc9cfd8b86117292d325419acdf4ad2fc7052559a8acdbcc3e8cfbf379e"
READONLY_SHA256 = {'calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/button/LiquidGlassButton.kt': '68c1d422b0994aeadbd9ac443ea273eac8410b0446cc751f39864552a9be68a3',
 'calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragAnimation.kt': 'efc57f78749bcf4fe81f7fd0e9746159a5edbfaf38596cbd8176f920af400895',
 'calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/InteractiveHighlight.kt': '7b111cf30b994374f5780175b790682e75f20f9df8f5aae283103dd5522c14c5',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/button/LiquidButtonConstructionTraceTest.kt': '1b417a078d26c7d2f09dcaa5c5e17ac9be0806fd4f8a88dffb5e616978207954',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlCustomizationMatrixTest.kt': 'c792203a97cc8bdea914856b5cd53195f7a623170820fbc3f91a4ef9fd55d61d',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlNativeHost.kt': '5132474a968f50ce40e161049b32700c28d1709d0e6b1bbd6fecb239f6fd9e20',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt': 'd3cccfc654399598abf00e04d6f40529a3802e9488448afde120da8180932df0',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt': 'ea18a76b5270fee0c95e953e6a4d280cc00b4fc2b64538a6ca23f7097ca43a0f',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/PointerCancellation.kt': '5e9aef0d114a3e4b9d992ce3be2fd5fd96951443a527e68f1c6f87f78d6a1b2b',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSliderNativeMatrixTest.kt': '9ed073effcf3b5399f4838887d271a1b893a2a9bb123afc6771fcd15d2ca87d4',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbarFallbackNativeTest.kt': 'c7cfac7363f93e1fa880378f5e38c7289faa9e0b3570e3999c9fe11b2bdc2207',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragLifecycleRegressionTest.kt': 'd1e96296dce57bb817a08abca87a2943d9924745d1208fd7591751ed9d5dd3e8',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/DragAnimationAndHighlightTest.kt': '701f5d1ae8e91f8d4419d8781f9b0554251e427b338cf22ee3567b52ec6f841c',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/InteractiveHighlightResourceLifecycleTest.kt': '9ded1ba61f6702ef2b6f28312b6971a37a112564c1d030dbe22b0f25419fefbf',
 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/UiDragShaderTestHost.kt': '7ce8cef67a1d4df0430852e77d37967574d42fd039b76a0a6ebb347f93b8cb8c',
 'scripts/ci/adaptive_controls_compile.init.gradle.kts': '29787a01ed76e780c0054102f276d683280799bdc9733a113360dc6b2440f866',
 'scripts/ci/android_external328_source_projection.py': 'd931688dd5f1bd196c6ee358a35e3c7664e1ee24639320cdecefa7057a2358f9',
 'scripts/ci/apple_appinfo_capability.py': 'd5d091757a7996d8265667b2c1dfc0f6d977b6b6c1c0f4d9e6d61d565c7fe263',
 'scripts/ci/apple_appinfo_shape.py': 'd3c9624c8e3b51c8e1b50c7f560df7a9ab67766d2255bc70cb804ea4301e1508',
 'scripts/ci/apple_appinfo_shape_route.py': 'eff38992e587037d848eb6c93fcd50496bf269d072c8060abef852c82025efc7',
 'scripts/ci/apple_image_launch_readiness.py': 'bafea0957404052acfb3a6f6ec56dabb96319448ae736f6b81f9ebdfeae18fc5',
 'scripts/ci/camera_home_affinity_source_projection.py': '313d05b5be8c8c223f547baf7b69b5fe2ec07d9c975d2e2ae09572e18814aefe',
 'scripts/ci/fixtures/apple-image-launcher-source-inverse.json': '7fd94a3f2249840fb61a6cbe835bc8d3fe0809951dd3e3ed77cb33f422f55cef',
 'scripts/ci/fixtures/calendar-share-selector-source-inverse.json': '0a9267ec0455668688ce3a4a76dc20f534294bf2d48edf1f4c80fd3e43a34bab',
 'scripts/ci/ios_adaptive_controls_native.init.gradle.kts': '90ac4d7f46ee8f88192eb23a3da5b3ce62ef1c00c9a8003a89800b47e305e8e8',
 'scripts/ci/ios_adaptive_controls_native_focus.py': '696826bbdf9dfff7142f0e5f905d6114a7e0f9fda06c25e155e86d3aa9914a28',
 'scripts/ci/ios_adaptive_controls_runtime.py': '420ba61013fc790d03fadc00360642fd7d65651b0da3b358027b90b49a2ce67e',
 'scripts/ci/ios_owned_geometry_fixture_recovery.py': '175c69071fa0bf8bbf106b6cc127ae6cd90344512d70f960b5447a4d2b9dc3c4',
 'scripts/ci/test_apple_image_launch_readiness.py': 'd7b4bcb1a8c1efa61baa64498d39e908da809520e9c19cdb40a946233727f1b7',
 'scripts/ci/test_ios_adaptive_controls_native_focus.py': '7fa4ceb016c7ef1e39829e9b2e1bf4ef05df9253512b933597c9305d1e3c9e50',
 'scripts/ci/test_ios_adaptive_controls_runtime.py': 'f12533841037f7ea6e8c9e672a2eee56a55be6fd0b93c9b5a307ac997b4131c3',
 'scripts/ci/ui_drag_shader_compile.init.gradle.kts': 'bc8045f3893de119925546703cf59c4006a9e5013e41a17a16fd4d37941893c7'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fixture_inputs():
    paths = {GUARD, "scripts/ci/test_ios_ui_related_source_projection.py"}
    for layer in (history, image, calendar):
        document = layer._document()
        paths |= set(document["bindings"]) | set(document["added_inputs"]) | set(document["unchanged_inputs"]) | {layer.SPEC_RELATIVE}
    from macos_share_missing_source_projection import fixture_inputs as share_fixture_inputs
    paths |= share_fixture_inputs()
    return paths


def copy_fixture(root):
    for name in fixture_inputs():
        target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())


class UiRelatedSourceProjectionControls(unittest.TestCase):
    def test_complete_ui_inverses_restore_all_exact_parent_images_and_forward_bytes(self):
        document = history._document()
        self.assertEqual(9, len(document["bindings"]))
        self.assertEqual(36, sum(len(binding["fragments"]) for binding in document["bindings"].values()))
        from macos_share_missing_source_projection import source_before_share_missing_ci
        self.assertEqual(GUARD_SHA256, sha(source_before_share_missing_ci(GUARD, (ROOT / GUARD).read_bytes())))
        self.assertEqual(history.SPEC_SHA256, sha((ROOT / history.SPEC_RELATIVE).read_bytes()))
        for name, binding in document["bindings"].items():
            raw_current = (ROOT / name).read_bytes(); current = source_before_share_missing_ci(name, raw_current)
            old = history.current_source_before_ui_related(name, raw_current)
            self.assertEqual((binding["after_sha256"], binding["after_bytes"]), (sha(current), len(current)))
            self.assertEqual((binding["before_sha256"], binding["before_bytes"]), (sha(old), len(old)))
            self.assertIs(old, history.source_before_ui_related(name, old))
            forward = old
            for fragment in binding["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(fragment["before_fragment_sha256"], sha(before))
                self.assertEqual(fragment["after_fragment_sha256"], sha(after))
                self.assertEqual(1, forward.count(before)); forward = forward.replace(before, after, 1)
            self.assertEqual(current, forward)

    def test_current_rejects_prior_partial_displaced_drifted_foreign_and_unbounded_sources(self):
        for name, binding in history._document()["bindings"].items():
            current = (ROOT / name).read_bytes(); old = history.source_before_ui_related(name, current)
            fragment = binding["fragments"][0]["after"].encode()
            displaced = current.replace(fragment, b"", 1) + fragment
            foreign = (ROOT / next(other for other in history.BOUND_PATHS if other != name)).read_bytes()
            self.assertNotEqual(current, displaced)
            for bad in (old, current[:-1], current + b"\n", displaced, foreign, b"", None, current.decode(),
                        bytearray(current), b"x" * (history.MAX_SOURCE_BYTES + 1)):
                with patch.object(camera, "_bindings", side_effect=AssertionError("Bad UI raw source crossed latest ingress")) as older:
                    with self.assertRaises(ValueError): bridge.current_source_for_history(name, bad)
                    older.assert_not_called()

    def test_one_raw_latest_ui_ingress_precedes_only_image_calendar_camera_ancestor_readers(self):
        for name in history.BOUND_PATHS:
            current = (ROOT / name).read_bytes()
            with patch.object(history, "current_source_before_ui_related", wraps=history.current_source_before_ui_related) as raw:
                old = history.read_current_source_for_history(ROOT / name, ROOT)
                raw.assert_called_once_with(name, current)
                self.assertIsInstance(old, bytes)
            self.assertEqual(1, raw.call_count)
        source = (ROOT / "scripts/ci/apple_image_launcher_source_projection.py").read_text()
        self.assertEqual(1, source.count('from ios_ui_related_source_projection import current_source_before_ui_related'))
        self.assertEqual(2, source.count('from ios_ui_related_source_projection import peel_ui_related_for_history'))

    def test_nested_exact_ancestor_peeling_never_admits_old_or_unknown_as_current(self):
        for name in history.BOUND_PATHS:
            current = (ROOT / name).read_bytes(); old = history.source_before_ui_related(name, current)
            self.assertEqual(old, history.peel_ui_related_for_history(name, current))
            self.assertIs(old, history.peel_ui_related_for_history(name, old))
            unknown = old + b"\n# synthetic unreviewed history\n"
            self.assertIs(unknown, history.peel_ui_related_for_history(name, unknown))
            for bad in (old, unknown):
                with self.assertRaises(ValueError): history.current_source_before_ui_related(name, bad)
            with self.assertRaises(ValueError): history.source_before_ui_related(name, unknown)
            self.assertIsInstance(image.peel_image_launch_for_history(name, current), bytes)
        unlisted = b"not certified, not rewritten"
        for reader in (history.source_before_ui_related, history.current_source_before_ui_related, history.peel_ui_related_for_history):
            self.assertIs(unlisted, reader("unlisted-source", unlisted))
            with self.assertRaises(ValueError): reader(Path("unlisted-source"), unlisted)

    def test_manifest_schema_hash_duplicate_fields_and_alias_links_refuse(self):
        raw = (ROOT / history.SPEC_RELATIVE).read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            with patch.object(history, "SPEC_PATH", path):
                for bad in (raw + b"\n", b"{}", b"", b"x" * (history.MAX_SPEC_BYTES + 1)):
                    path.write_bytes(bad)
                    with self.assertRaises(ValueError): history._document()
                for key, value in (("schema_version", True), ("bindings", {}), ("added_inputs", {}), ("scope", "native accepted")):
                    changed = json.loads(raw); changed[key] = value; payload = json.dumps(changed).encode(); path.write_bytes(payload)
                    with patch.object(history, "SPEC_SHA256", sha(payload)), self.assertRaises(ValueError): history._document()
                duplicate = raw.rstrip()[:-1] + b',"schema_version":1}'
                path.write_bytes(duplicate)
                with patch.object(history, "SPEC_SHA256", sha(duplicate)), self.assertRaisesRegex(ValueError, "Duplicate"):
                    history._document()
                path.unlink(); path.symlink_to(ROOT / history.SPEC_RELATIVE)
                with self.assertRaises(ValueError): history._document()
                path.unlink(); backing = path.with_name("backing.json"); backing.write_bytes(raw); path.hardlink_to(backing)
                with self.assertRaises(ValueError): history._document()
        with self.assertRaises(ValueError): history._unique([("field", 1), ("field", 2)])

    def test_fragment_hash_unique_sites_and_complete_roundtrip_are_mandatory(self):
        document = history._document(); name = "scripts/ci/library_tests.py"; current = (ROOT / name).read_bytes()
        for mutation in ("before_hash", "after_hash", "duplicate", "missing_site", "wrong_parent_bytes"):
            changed = copy.deepcopy(document); binding = changed["bindings"][name]
            if mutation == "before_hash": binding["fragments"][0]["before_fragment_sha256"] = "0" * 64
            elif mutation == "after_hash": binding["fragments"][0]["after_fragment_sha256"] = "0" * 64
            elif mutation == "duplicate": binding["fragments"].append(copy.deepcopy(binding["fragments"][-1]))
            elif mutation == "missing_site":
                binding["fragments"][-1]["after"] = "synthetic absent source site"
                binding["fragments"][-1]["after_fragment_sha256"] = sha(b"synthetic absent source site")
            else: binding["before_bytes"] += 1
            with patch.object(history, "_document", return_value=changed), self.assertRaises(ValueError):
                history.source_before_ui_related(name, current)

    def test_owning_latest_validator_requires_exact_new_inputs_and_current_raw_images(self):
        document = history._document()
        self.assertEqual(history.ADDED_PATHS, set(document["added_inputs"]))
        self.assertTrue(history.validate_current_sources(ROOT))
        self.assertTrue(image.validate_current_sources(ROOT))
        self.assertTrue(calendar.validate_current_sources(ROOT))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); copy_fixture(root)
            self.assertTrue(calendar.validate_current_sources(root))
            for name in document["added_inputs"]:
                target = root / name; original = target.read_bytes(); target.unlink()
                with self.assertRaises(FileNotFoundError): calendar.validate_current_sources(root)
                target.symlink_to(ROOT / name)
                with self.assertRaises(ValueError): calendar.validate_current_sources(root)
                target.unlink(); target.write_bytes(original + b"\n")
                with self.assertRaises(ValueError): calendar.validate_current_sources(root)
                target.write_bytes(original)
            for name in document["bindings"]:
                target = root / name; original = target.read_bytes()
                target.write_bytes(history.source_before_ui_related(name, original))
                with self.assertRaises(ValueError): history.validate_current_sources(root)
                target.write_bytes(original)

    def test_confined_ordinary_checkout_boundary_rejects_foreign_symlink_and_hardlink_paths(self):
        name = "scripts/ci/runtime_context.py"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); copy_fixture(root); target = root / name; original = target.read_bytes()
            target.unlink(); target.symlink_to(ROOT / name)
            with self.assertRaises(ValueError): history.read_current_source_for_history(target, root)
            target.unlink(); backing = target.with_name("backing.py"); backing.write_bytes(original); target.hardlink_to(backing)
            with self.assertRaises(ValueError): history.read_current_source_for_history(target, root)
            with self.assertRaises(ValueError): history.read_current_source_for_history(ROOT / name, root)
            for path in (root / "foreign.py", Path(name)):
                with self.assertRaises(ValueError): history.read_current_source_for_history(path, root)
            alias = root / "alias"; alias.symlink_to(ROOT, target_is_directory=True)
            with self.assertRaises(ValueError): history.read_current_source_for_history(alias / name, alias)

    def test_retained_image_calendar_assertions_and_all_dated_pins_have_exact_ancestor_operands(self):
        affected = {
            "scripts/ci/test_calendar_share_selector_source_projection.py": {
                "test_four_complete_images_and_all_finite_unique_fragments_roundtrip",
                "test_owning_validator_requires_all_four_added_inputs_and_ordinary_current_images"},
            "scripts/ci/test_apple_image_launcher_source_projection.py": {
                "test_complete_image_calendar_and_control_inverses_restore_exact_parents_and_forward",
                "test_latest_three_hooks_and_mirror_qualification_preserve_original_bodies"},
        }
        from macos_share_missing_source_projection import source_before_share_missing_ci
        for name, changed in affected.items():
            current = source_before_share_missing_ci(name, (ROOT / name).read_bytes())
            old = history.source_before_ui_related(name, current)
            old_methods = {node.name: node for node in ast.walk(ast.parse(old)) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
            new_methods = {node.name: node for node in ast.walk(ast.parse(current)) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
            self.assertEqual(set(old_methods), set(new_methods))
            for method in set(old_methods) - changed:
                self.assertEqual(ast.dump(old_methods[method], include_attributes=False), ast.dump(new_methods[method], include_attributes=False))
            for method in changed:
                old_asserts = [node.func.attr for node in ast.walk(old_methods[method]) if isinstance(node, ast.Call) and
                              isinstance(node.func, ast.Attribute) and node.func.attr.startswith("assert")]
                new_asserts = [node.func.attr for node in ast.walk(new_methods[method]) if isinstance(node, ast.Call) and
                              isinstance(node.func, ast.Attribute) and node.func.attr.startswith("assert")]
                self.assertEqual(old_asserts, new_asserts)
        for layer in (image, calendar):
            self.assertEqual(sha((ROOT / layer.SPEC_RELATIVE).read_bytes()), layer.SPEC_SHA256)
        self.assertEqual(READONLY_SHA256["scripts/ci/ios_owned_geometry_fixture_recovery.py"],
                         "175c69071fa0bf8bbf106b6cc127ae6cd90344512d70f960b5447a4d2b9dc3c4")

    def test_original_application_launch_argv_deadlines_finally_sdk_and_native_bodies_are_unchanged(self):
        name = "scripts/ci/ios_ui_application.py"; current = (ROOT / name).read_bytes()
        old = history.source_before_ui_related(name, current)
        old_functions = {node.name: node for node in ast.parse(old).body if isinstance(node, ast.FunctionDef)}
        new_functions = {node.name: node for node in ast.parse(current).body if isinstance(node, ast.FunctionDef)}
        self.assertEqual(set(old_functions), set(new_functions))
        for function in set(old_functions) - {"run"}:
            self.assertEqual(ast.dump(old_functions[function], include_attributes=False), ast.dump(new_functions[function], include_attributes=False))
        old_finally = [ast.dump(ast.Module(body=node.finalbody, type_ignores=[]), include_attributes=False)
                       for node in ast.walk(old_functions["run"]) if isinstance(node, ast.Try) and node.finalbody]
        new_finally = [ast.dump(ast.Module(body=node.finalbody, type_ignores=[]), include_attributes=False)
                       for node in ast.walk(new_functions["run"]) if isinstance(node, ast.Try) and node.finalbody]
        self.assertEqual(old_finally, new_finally)
        for source in related.sources(related.FOCUSES[1]):
            self.assertEqual(READONLY_SHA256[source], sha((ROOT / source).read_bytes()))
        self.assertEqual(READONLY_SHA256[related.init_script(related.FOCUSES[0])],
                         sha((ROOT / related.init_script(related.FOCUSES[0])).read_bytes()))

    def test_camera_bridge_175c_and_runtime620_inputs_are_not_edited_or_replayed(self):
        self.assertFalse(set(READONLY_SHA256) & history.BOUND_PATHS)
        for name, digest in READONLY_SHA256.items():
            self.assertEqual(digest, sha((ROOT / name).read_bytes()), name)
        self.assertEqual("420ba61013fc790d03fadc00360642fd7d65651b0da3b358027b90b49a2ce67e",
                         READONLY_SHA256["scripts/ci/ios_adaptive_controls_runtime.py"])
        self.assertEqual("f12533841037f7ea6e8c9e672a2eee56a55be6fd0b93c9b5a307ac997b4131c3",
                         READONLY_SHA256["scripts/ci/test_ios_adaptive_controls_runtime.py"])
        self.assertNotIn("scripts/ci/android_external328_source_projection.py", history.BOUND_PATHS)
        self.assertNotIn("scripts/ci/camera_home_affinity_source_projection.py", history.BOUND_PATHS)


if __name__ == "__main__":
    unittest.main()
