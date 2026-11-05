# SPDX-License-Identifier: Apache-2.0
"""New740-R2 domain/bridge/context controls; no original passing-method replay."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import ci_source_domain740 as stage
import ci_source_recovery740_742 as recovery
import ci668_outer_source_projection as ci
import macos_share_ci668_composition as joint
import tooling_recovery671_source_projection as tooling

ROOT = Path(__file__).resolve().parents[2]
UNLISTED = (
    "scripts/ci/camera_boot_busy_source_projection.py",
    "scripts/ci/camera_scalar_failfast_source_projection.py",
    "scripts/ci/test_android_camera_boot_busy.py",
)
CONTEXTS = (
    "scripts/ci/test_camera_home_baseline_source_projection.py",
    "scripts/ci/test_camera_tooling562_source_projection.py",
    "scripts/ci/test_camera_tooling566_source_projection.py",
    "scripts/ci/test_macos_share_ci668_composition.py",
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def nodes(raw):
    return {node.name: node for node in ast.parse(raw).body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}


class CiSourceDomain740R2Controls(unittest.TestCase):
    def test_r2_six_exact_reader_and_context_roundtrips_retain_current303_ancestor(self):
        document = stage._document()
        self.assertEqual({tooling.SOURCE_RELATIVE, joint.OWNER} | set(CONTEXTS), set(stage.BEFORE))
        self.assertEqual(set(stage.BEFORE), set(document["bindings"]))
        for relative, row in document["bindings"].items():
            current = (ROOT / relative).read_bytes()
            original = stage.current_source_before_domain740(relative, current)
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(original), len(original)))
            forward = original
            for fragment in row["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(1, forward.count(before))
                forward = forward.replace(before, after, 1)
            self.assertEqual(recovery.current_source_before_recovery(relative, current, ROOT), forward)
            self.assertEqual(original, stage.peel_domain740_for_history(relative, current))
            self.assertEqual(original, stage.peel_domain740_for_history(relative, original))
            for bad in (original, current[:-1], current + b"\n", b"", None, bytearray(current), current.decode()):
                with self.subTest(relative=relative, kind=type(bad).__name__), self.assertRaises(ValueError):
                    stage.current_source_before_domain740(relative, bad)
            unknown = current + b"\n# unknown740 context\n"
            self.assertEqual(unknown, stage.peel_domain740_for_history(relative, unknown))
        self.assertEqual("41979c2e9eb4b74b7da41da42408ac636d60102fea10269b1d181992df4bea5f",
                         sha((ROOT / ci.SOURCE_RELATIVE).read_bytes()))
        self.assertNotIn(ci.SOURCE_RELATIVE, stage.MODIFIED)

    def test_r2_broader671_unlisted_data_never_enters_strict_ci_or_joint_domain(self):
        import camera_home_baseline_source_projection as home
        import test_camera_home_baseline_source_projection as owner
        document = joint._document()
        for relative in UNLISTED + ("unlisted-source",):
            raw = (ROOT / relative).read_bytes() if relative in UNLISTED else b"unqualified-data"
            self.assertNotIn(relative, document["raw_inputs"])
            self.assertEqual(raw, tooling.current_source_before_tooling671(relative, raw))
            self.assertEqual(raw, stage.current_source_before_domain740(relative, raw))
            with self.assertRaises(ValueError):
                ci.current_source_before_ci668(relative, raw)
            with self.assertRaises(ValueError):
                joint.current_source_in_view(relative, raw, joint.PRODUCER_VIEW)
            if relative in UNLISTED:
                current = owner.preserved_home_stage(relative, raw)
                old = home.source_before_home_baseline(relative, current)
                after = home._bindings()[relative]["fragments"][0]["after"].encode()
                displaced = current.replace(after, b"", 1) + after
                for bad in (old, current[:-1], current + b"\n", displaced):
                    with self.subTest(relative=relative), self.assertRaises(ValueError):
                        home.current_source_before_home_baseline(relative, bad)
        context = "scripts/ci/test_camera_tooling562_source_projection.py"
        raw = (ROOT / context).read_bytes()
        self.assertNotIn(context, document["raw_inputs"])
        self.assertEqual(stage.current_source_before_domain740(context, raw),
                         tooling.current_source_before_tooling671(context, raw))
        for identity in (Path(context), "../" + context, "/" + context, context + "/../foreign.py"):
            with self.subTest(identity=str(identity)), self.assertRaises(ValueError):
                stage.current_source_before_domain740(identity, raw)

    def test_r2_exact718_bridge_precedes_geometry_but_never_changes_named_views(self):
        import ios_geometry_simulator_source_projection as geometry
        raw = (ROOT / stage.BRIDGE).read_bytes()
        document = joint._document()
        self.assertEqual(stage.BRIDGE_AFTER, document["raw_inputs"][stage.BRIDGE])
        for view in joint.VIEWS:
            self.assertNotIn(stage.BRIDGE, document["predecessor_inputs"][view])
            self.assertEqual(raw, joint.current_source_in_view(stage.BRIDGE, raw, view))
            self.assertEqual(raw, joint.peel_for_history(stage.BRIDGE, raw, view))
        old = stage.bridge_after_qualified_current_ingress(stage.BRIDGE, raw)
        self.assertEqual((stage.BRIDGE_BEFORE["sha256"], stage.BRIDGE_BEFORE["bytes"]), (sha(old), len(old)))
        self.assertEqual(old, tooling.current_source_before_tooling671(stage.BRIDGE, raw))
        self.assertEqual(geometry._bindings()[stage.BRIDGE]["after_sha256"], sha(old))
        self.assertEqual(old, stage.peel_bridge740_for_history(stage.BRIDGE, raw))
        self.assertEqual(old, stage.peel_bridge740_for_history(stage.BRIDGE, old))
        unknown = raw + b"\n# unknown bridge\n"
        self.assertEqual(unknown, stage.peel_bridge740_for_history(stage.BRIDGE, unknown))
        for bad in (old, raw[:-1], raw + b"\n", raw.replace(b"Exact Android18 admission", b"Foreign Android18 admission", 1)):
            self.assertNotEqual(raw, bad)
            with self.assertRaises(ValueError):
                tooling.current_source_before_tooling671(stage.BRIDGE, bad)
            with self.assertRaises(ValueError):
                stage.bridge_after_qualified_current_ingress(stage.BRIDGE, bad)
        row = stage._document()["bridge_binding"]
        self.assertEqual(1, len(row["fragments"]))
        self.assertEqual(stage.BRIDGE_AUTHORITY, stage._document()["bridge_authority"])
        forward = old
        for fragment in row["fragments"]:
            self.assertEqual(1, forward.count(fragment["before"].encode()))
            forward = forward.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
        self.assertEqual(raw, forward)

    def test_r2_actual_same303_hashes_and_independent_cookie40_custody_hold(self):
        import cookie_ci668_outer_source_projection as cookie
        self.assertTrue(stage.validate_current_sources())
        document = joint._document()
        self.assertEqual((518906, stage.CURRENT303_SPEC_SHA256),
                         ((ROOT / joint.SPEC).stat().st_size, sha((ROOT / joint.SPEC).read_bytes())))
        self.assertEqual(512 * 1024, joint.MAX_SPEC)
        self.assertEqual(301, len(document["raw_inputs"]))
        current = joint.current_input_hashes()
        original = {name: row["sha256"] for name, row in document["raw_inputs"].items()}
        self.assertEqual(set(original) | {joint.OWNER, joint.SPEC}, set(current))
        self.assertEqual(303, len(current))
        self.assertEqual({relative: sha((ROOT / relative).read_bytes()) for relative in current}, current)
        for relative in set(original) - (stage.MODIFIED | recovery.MODIFIED):
            self.assertEqual(original[relative], current[relative])
        for relative in stage.MODIFIED & set(original):
            self.assertEqual(stage.BEFORE[relative]["sha256"], original[relative])
            self.assertNotEqual(original[relative], current[relative])
        for relative in (recovery.MODIFIED - stage.MODIFIED) & set(original):
            self.assertEqual(original[relative], sha(recovery.current_source_before_recovery(relative, (ROOT / relative).read_bytes(), ROOT)))
            self.assertNotEqual(original[relative], current[relative])
        for relative in {stage.OWNER, stage.CONTROL, stage.SPEC}:
            self.assertNotIn(relative, current)
        sizes = {joint.CI_VIEW: 175, joint.PRODUCER_VIEW: 190, joint.COOKIE_VIEW: 40, joint.SHARE_VIEW: 36}
        for view, count in sizes.items():
            named = joint.predecessor_input_hashes(view)
            self.assertEqual(count, len(named))
            self.assertEqual({name: row["sha256"] for name, row in document["predecessor_inputs"][view].items()}, named)
        cookie_hashes = cookie.current_input_hashes(ROOT)
        self.assertEqual(40, len(cookie_hashes))
        self.assertFalse(stage.MODIFIED & set(cookie_hashes))
        self.assertEqual({relative: sha((ROOT / relative).read_bytes()) for relative in cookie_hashes}, cookie_hashes)

    def test_r2_live_own_hash_refusals_and_original714_ast_template_stay_bound(self):
        raw = (ROOT / joint.OWNER).read_bytes()
        original = stage.current_source_before_domain740(joint.OWNER, raw)
        document = joint._document()
        self.assertEqual(sha(raw), joint._own_payload(raw, document))
        for bad in (original, raw[:-1], raw + b"\n", (ROOT / ci.SOURCE_RELATIVE).read_bytes()):
            with self.assertRaises(ValueError):
                joint._own_payload(bad, document)
        test_source = stage.current_source_before_domain740(joint.NEW_CONTROL, (ROOT / joint.NEW_CONTROL).read_bytes())
        method = next(n for n in ast.walk(ast.parse(test_source)) if isinstance(n, ast.FunctionDef)
                      and n.name == "test46_714_path_only_cache_fresh_custody_512k_template_and_original_new10_bytes_hold")
        assignment = next(n for n in method.body if isinstance(n, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == "unchanged714_ast_sha256" for t in n.targets))
        pins = ast.literal_eval(assignment.value)
        functions = nodes(original)
        for name, expected in pins.items():
            node = functions[name]
            if name == "_sealed_predecessor_hashes":
                text = ast.get_source_segment(original.decode(), node)
                prelude = "        raw = peel_android_lifecycle_for_history(relative, raw, root)\n"
                self.assertEqual(1, text.count(prelude))
                node = ast.parse(text.replace(prelude, "", 1)).body[0]
            self.assertEqual(expected, sha(ast.dump(node, include_attributes=False).encode()), name)
        needle = ('SPEC_SHA256 = "' + joint.SPEC_SHA256 + '"\n').encode()
        self.assertEqual(1, original.count(needle))
        self.assertEqual(document["own_guard"]["bytes"], len(original))
        self.assertEqual(document["own_guard"]["template_sha256"],
                         sha(original.replace(needle, ('SPEC_SHA256 = "' + '0' * 64 + '"\n').encode(), 1)))
        self.assertEqual(original, joint._raw_payload(joint.OWNER, raw, document))

    def test_r2_model_declares_separate_dependencies_without303_enrollment(self):
        import test_macos_share_ci668_composition as owner
        expected = joint.fixture_inputs(ROOT) | stage.dependency_inputs() | recovery.dependency_inputs()
        with owner.source_model() as root:
            model_name = root
            actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
            self.assertEqual(expected, actual)
            self.assertEqual(303, len(joint.fixture_inputs(root)))
            self.assertTrue(stage.validate_current_sources(root))
            document = joint._document(root)
            for relative in stage.MODIFIED & joint.fixture_inputs(root):
                raw = (root / relative).read_bytes()
                self.assertEqual(stage.current_source_before_domain740(relative, raw, root),
                                 joint._raw_payload(relative, raw, document, root))
            for relative in {stage.OWNER, stage.CONTROL, stage.SPEC}:
                self.assertNotIn(relative, joint.fixture_inputs(root))
        self.assertFalse(model_name.exists())

    def test_r2_dated_setup_changes_preserve_every_assertion_and_raw_digest_body(self):
        for relative in CONTEXTS:
            current = (ROOT / relative).read_bytes()
            original = stage.current_source_before_domain740(relative, current)
            old_tree, new_tree = ast.parse(original), ast.parse(current)
            def assertions(tree):
                return [ast.dump(node, include_attributes=False) for node in ast.walk(tree)
                        if isinstance(node, ast.Assert) or isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute) and node.func.attr.startswith("assert")]
            self.assertEqual(assertions(old_tree), assertions(new_tree), relative)
        home = nodes((ROOT / CONTEXTS[0]).read_bytes())["HomeBaselineHistoryTests"]
        methods = {n.name: n for n in home.body if isinstance(n, ast.FunctionDef)}
        for method in ("test_shared_current_chain_keeps_all_original_source_pins_not_new_behavior",
                       "test_latest_shared_entry_itself_is_bound_and_refuses_its_old_or_unknown_image"):
            self.assertTrue(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                                and n.func.id == "preserved_home_stage" for n in ast.walk(methods[method])))
        for path in ("scripts/ci/test_android_camera_scalar_control_refusal.py",
                     "scripts/ci/test_android_camera_settings_activity_reference_prefix_diagnostics.py"):
            current = (ROOT / path).read_bytes()
            original = __import__("camera_tooling562_source_projection").source_before_tooling(path, current)
            self.assertEqual(ast.dump(nodes(current)["digest"], include_attributes=False),
                             ast.dump(nodes(original)["digest"], include_attributes=False))

    def test_r2_bridge_authority_fragments_aliases_and_tails_refuse_with_cleanup(self):
        raw = (ROOT / stage.SPEC).read_bytes()
        original = stage._document()
        for alter in (lambda doc: doc["bridge_authority"].update(parent_blob="0" * 40),
                      lambda doc: doc["bridge_binding"]["fragments"][0].update(after_fragment_sha256="0" * 64),
                      lambda doc: doc["bridge_binding"].update(after_bytes=doc["bridge_binding"]["after_bytes"] - 1)):
            fake = copy.deepcopy(original)
            alter(fake)
            encoded = (json.dumps(fake, sort_keys=True, separators=(",", ":")) + "\n").encode()
            with tempfile.TemporaryDirectory() as name:
                root = Path(name)
                target = root / stage.SPEC
                target.parent.mkdir(parents=True)
                target.write_bytes(encoded)
                with patch.object(stage, "SPEC_SHA256", sha(encoded)), self.assertRaises(ValueError):
                    stage._document(root)
            self.assertFalse(root.exists())
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            target = root / stage.SPEC
            target.parent.mkdir(parents=True)
            target.write_bytes(raw + b"\n")
            with self.assertRaises(ValueError):
                stage._document(root)
            target.unlink()
            backing = target.with_name("backing.json")
            backing.write_bytes(raw)
            target.symlink_to(backing)
            with self.assertRaises(ValueError):
                stage._document(root)
            target.unlink()
            target.hardlink_to(backing)
            with self.assertRaises(ValueError):
                stage._document(root)
            target.unlink()
            backing.unlink()
        self.assertFalse(root.exists())


if __name__ == "__main__":
    unittest.main()
