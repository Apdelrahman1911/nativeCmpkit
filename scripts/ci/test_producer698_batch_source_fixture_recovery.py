# SPDX-License-Identifier: Apache-2.0
"""NEW current-proposal/source controls; no accepted method/producer/native replay."""
import ast
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import ci668_outer_source_projection as ci668
import macos_share_ci668_composition as joint
import producer698_source_fixture_recovery as recovery
import tooling_recovery671_source_projection as tooling

ROOT = Path(__file__).resolve().parents[2]
TEMPORARY_ROOT = None
UI_SPLIT = "scripts/ci/test_ios_ui_split664_native_routing.py"
OFFLINE = "scripts/ci/offline_tooling_reuse.py"
CI_CONTROL = "scripts/ci/test_ci668_outer_source_projection.py"
NINE_FIXTURES = {
    "scripts/ci/test_camera_home_baseline_source_projection.py",
    "scripts/ci/test_camera_ios_ownership_application_routing.py",
    "scripts/ci/test_camera_tooling566_source_projection.py",
    "scripts/ci/test_ios_geometry_simulator_source_projection.py",
    UI_SPLIT,
    "scripts/ci/test_tooling656_fixture_recovery.py",
    "scripts/ci/test_webview_content_policy_source_projection.py",
    "scripts/ci/test_library_sdk_context.py",
    "scripts/ci/test_workflow_source.py",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def methods(raw):
    return {node.name: node for node in ast.walk(ast.parse(raw))
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}


def assertions(raw):
    return [node for node in ast.walk(ast.parse(raw)) if isinstance(node, ast.Call) and
            isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and
            node.func.value.id == "self" and node.func.attr.startswith("assert")]


class Producer698BatchSourceFixtureRecoveryControls(unittest.TestCase):
    def test_only_exact_combined_twelve_endpoints_admit_and_every_complete_ancestor_roundtrips(self):
        document = recovery._document()
        self.assertEqual(NINE_FIXTURES | {OFFLINE, CI_CONTROL, ci668.SOURCE_RELATIVE}, recovery.BOUND_PATHS)
        self.assertEqual((12, 27), (len(document["bindings"]), sum(len(row["fragments"]) for row in document["bindings"].values())))
        for name, row in document["bindings"].items():
            raw = (ROOT / name).read_bytes()
            named190 = joint.current_source_in_view(name, raw, joint.PRODUCER_VIEW)
            ancestor = recovery.current_source_before_producer698(name, raw)
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(ancestor), len(ancestor)), name)
            self.assertEqual(ancestor, recovery.source_before_producer698(name, raw), name)
            self.assertEqual(ancestor, recovery.source_before_producer698(name, ancestor), name)
            forward = ancestor
            for span in row["fragments"]:
                before, after = span["before"].encode(), span["after"].encode()
                self.assertEqual(1, forward.count(before), name)
                forward = forward.replace(before, after, 1)
            self.assertEqual(named190, forward, name)
            self.assertEqual((row["after_sha256"], row["after_bytes"]), (sha(named190), len(named190)), name)
            if named190 != raw:
                with self.assertRaises(ValueError):
                    recovery.current_source_before_producer698(name, named190)
            for bad in (ancestor, raw + b"\n", raw[:-1], bytearray(raw), memoryview(raw), None):
                with self.subTest(name=name, kind=type(bad).__name__), self.assertRaises(ValueError):
                    recovery.current_source_before_producer698(name, bad)

    def test_one_newest_ci_ingress_restores_ui668_and_offline9bd_without_repinning_any_old_spec(self):
        document = recovery._document()
        for name in (UI_SPLIT, OFFLINE, ci668.SOURCE_RELATIVE):
            raw = (ROOT / name).read_bytes()
            with patch.object(recovery, "current_source_before_producer698", wraps=recovery.current_source_before_producer698) as entry:
                result = ci668.current_source_before_ci668(name, raw)
            self.assertEqual([(name, raw)], [call.args for call in entry.call_args_list if call.args[0] == name])
            expected = ("dc0b1f4a5a4bd9dc22989043a3e1f65137a0466adb1543fb36b2a1686079e5a7" if name == UI_SPLIT else
                        "9bd6b6d8daa7d8e6270fc874c28a8b7692f815334d4d77130fb3d81c35d7897b" if name == OFFLINE else
                        recovery.ORIGINAL_CI668_SOURCE_SHA256)
            self.assertEqual(expected, sha(result), name)
            self.assertEqual(result, ci668.source_before_ci668(name, raw), name)
        self.assertEqual("58a6e93641d2f221fb09a74f2ae69fa28b2b2278624c96605782cd1bc89447a2", document["bindings"][UI_SPLIT]["before_sha256"])
        self.assertEqual("9bd6b6d8daa7d8e6270fc874c28a8b7692f815334d4d77130fb3d81c35d7897b", ci668.SEALED_CI_LEAVES[OFFLINE])
        self.assertEqual("bbfdb2454182ce8c1fc90e793c3552e49f317b35437b61fcd3e8743b86f9d86e", sha((ROOT / ci668.SPEC_RELATIVE).read_bytes()))
        self.assertEqual("9def6c416e199237600bdcdc2a16a3fd22dc2158796e1116f999b8681c96a110", sha((ROOT / tooling.SPEC_RELATIVE).read_bytes()))

    def test_raw_current190_and_named_original175_are_distinct_truthful_complete_ordinary_views(self):
        latest = recovery.current_input_hashes()
        original = recovery.original_ci668_input_hashes()
        producer190 = recovery.original_producer190_input_hashes()
        self.assertEqual((303, 190, 175), (len(latest), len(producer190), len(original)))
        self.assertEqual(producer190, joint.predecessor_input_hashes(joint.PRODUCER_VIEW))
        self.assertEqual(latest, ci668.current_input_hashes())
        self.assertEqual(latest, tooling.current_input_hashes())
        self.assertEqual(set(latest), recovery.fixture_inputs())
        self.assertEqual(set(latest), ci668.fixture_inputs())
        self.assertEqual(set(latest), tooling.fixture_inputs())
        self.assertEqual(original, ci668.sealed_ci668_175_hashes())
        self.assertTrue(all(sha((ROOT / name).read_bytes()) == digest for name, digest in latest.items()))
        self.assertNotEqual(latest[OFFLINE], original[OFFLINE])
        self.assertNotEqual(latest[UI_SPLIT], original[UI_SPLIT])
        self.assertNotEqual(latest[ci668.SOURCE_RELATIVE], original[ci668.SOURCE_RELATIVE])
        self.assertEqual(original[ci668.SOURCE_RELATIVE], recovery.ORIGINAL_CI668_SOURCE_SHA256)
        self.assertEqual("a1ea0950a96472e6c602e3a776f74ce519cb8bdadf78920512a1ee6649961d5b", latest[ci668.WORKFLOW])
        workflow = (ROOT / ci668.WORKFLOW).read_bytes()
        named_ci175 = joint.current_source_in_view(ci668.WORKFLOW, workflow, joint.CI_VIEW, ROOT)
        self.assertEqual(ci668.WORKFLOW_AFTER_SHA256, sha(named_ci175))
        self.assertTrue(all(producer190[name] == digest for name, digest in original.items()
                            if name not in recovery.BOUND_PATHS))
        self.assertTrue(all(sha(joint.current_source_in_view(name, (ROOT / name).read_bytes(), joint.CI_VIEW)) == digest
                            for name, digest in original.items()))

    def test_history_peels_only_named_complete_afterimages_and_never_unknown_current_or_global_content(self):
        for name in recovery.BOUND_PATHS:
            raw = (ROOT / name).read_bytes()
            ancestor = recovery.source_before_producer698(name, raw)
            self.assertEqual(ancestor, recovery.peel_producer698_for_history(name, raw))
            self.assertEqual(ancestor, recovery.peel_producer698_for_history(name, ancestor))
            for bad in (raw + b"\n", raw[:-1], b"unknown ancestor bytes"):
                self.assertEqual(bad, recovery.peel_producer698_for_history(name, bad))
                with self.assertRaises(ValueError):
                    recovery.current_source_before_producer698(name, bad)
        raw = b"unlisted bytes are not source certification"
        self.assertEqual(raw, recovery.peel_producer698_for_history("unlisted.py", raw))
        self.assertEqual(raw, recovery.source_before_producer698("unlisted.py", raw))
        for wrong in (Path(OFFLINE), "../offline.py", "/offline.py", "scripts//ci/offline.py"):
            with self.assertRaises(ValueError):
                recovery.current_source_before_producer698(wrong, raw)

    def test_every_new_input_is_required_and_new_guard_template_spec_and_fragment_drift_refuse(self):
        self.assertTrue(recovery.validate_current_sources(ROOT))
        document = recovery._document()
        for name in recovery.ADDED_PATHS:
            raw = (ROOT / name).read_bytes()
            for bad in (raw + b"\n", raw[:-1]):
                with self.assertRaises(ValueError):
                    recovery.current_source_before_producer698(name, bad)
            real = recovery._ordinary
            def absent(root, relative, limit):
                if relative == name:
                    raise FileNotFoundError("Missing newly required source input")
                return real(root, relative, limit)
            with patch.object(recovery, "_ordinary", side_effect=absent), self.assertRaises(FileNotFoundError):
                recovery.validate_current_sources(ROOT)
        for name in (recovery.SOURCE_RELATIVE, recovery.SPEC_RELATIVE):
            raw = (ROOT / name).read_bytes()
            for bad in (raw + b"\n", raw[:-1]):
                with self.assertRaises(ValueError):
                    recovery.current_source_before_producer698(name, bad)
        bad = copy.deepcopy(document)
        bad["bindings"][OFFLINE]["fragments"][0]["after_fragment_sha256"] = "a" * 64
        with patch.object(recovery, "_document", return_value=bad), self.assertRaises(ValueError):
            recovery.current_source_before_producer698(OFFLINE, (ROOT / OFFLINE).read_bytes())
        for transform in (lambda value: value["bindings"].pop(OFFLINE),
                          lambda value: value["added_inputs"].update({"scripts/ci/foreign.py": "a" * 64}),
                          lambda value: value["original_ci668_inputs"].update({OFFLINE: "a" * 64}),
                          lambda value: value.update({"allow_old_current": True})):
            bad = copy.deepcopy(document); transform(bad)
            with self.assertRaises(ValueError):
                recovery._shape(bad)
        for raw in (b'{"schema_version":1,"schema_version":1}', b'{"x":NaN}'):
            with self.assertRaises(ValueError):
                recovery._parse(raw)

    def test_ordinary_reader_refuses_symlink_hardlink_alias_foreign_identity_empty_and_oversize(self):
        with tempfile.TemporaryDirectory(dir=TEMPORARY_ROOT) as directory:
            root = Path(directory).resolve()
            target = root / "probe.py"; target.write_bytes(b"source")
            self.assertEqual(b"source", recovery._ordinary(root, "probe.py", 16))
            with self.assertRaises(ValueError):
                recovery._ordinary(root, "probe.py", 3)
            target.write_bytes(b"")
            with self.assertRaises(ValueError):
                recovery._ordinary(root, "probe.py", 16)
            backing = root / "backing.py"; backing.write_bytes(b"source")
            target.unlink(); target.symlink_to(backing)
            with self.assertRaises(ValueError):
                recovery._ordinary(root, "probe.py", 16)
            target.unlink(); target.hardlink_to(backing)
            with self.assertRaises(ValueError):
                recovery._ordinary(root, "probe.py", 16)
            with self.assertRaises(ValueError):
                recovery._ordinary(root, target.as_posix(), 16)

    def test_owning_ci_adapter_keeps_original_template_pins_other_six_methods_and_all_assertion_callees(self):
        raw = (ROOT / ci668.SOURCE_RELATIVE).read_bytes()
        original = recovery.source_before_producer698(ci668.SOURCE_RELATIVE, raw)
        self.assertEqual(recovery.ORIGINAL_CI668_SOURCE_SHA256, sha(original))
        old_tree, current_tree = ast.parse(original), ast.parse(raw)
        old_pins = {node.targets[0].id: ast.dump(node.value, include_attributes=False) for node in old_tree.body
                    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and "SHA256" in node.targets[0].id}
        new_pins = {node.targets[0].id: ast.dump(node.value, include_attributes=False) for node in current_tree.body
                    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and "SHA256" in node.targets[0].id}
        self.assertEqual(old_pins, new_pins)
        source = (ROOT / CI_CONTROL).read_bytes()
        named190 = joint.current_source_in_view(CI_CONTROL, source, joint.PRODUCER_VIEW, ROOT)
        self.assertEqual(("ff1f2ac9530135089b55d1f5f82079c2ed17f5a2eea4e9ad35ff4088b639635d", 7780),
                         (sha(named190), len(named190)))
        prior = recovery.source_before_producer698(CI_CONTROL, source)
        self.assertEqual(("8e6d2e76f9de755f5d53bdc6a5a29aeb7161e9777ffcf7b5a0a163164889dfce", 7650),
                         (sha(prior), len(prior)))
        old, new = methods(prior), methods(named190)
        self.assertEqual(set(old), set(new))
        self.assertEqual({"test_current_hash_and_path_apis_report_actual175_not_ancestor_hashes", "test_new_ci_guard_template_and_manifest_partial_drift_refuse"},
                         {name for name in old if ast.dump(old[name], include_attributes=False) != ast.dump(new[name], include_attributes=False)})
        self.assertEqual([ast.unparse(node.func) for node in assertions(prior)],
                         [ast.unparse(node.func) for node in assertions(named190)])
        self.assertEqual(sha(raw), ci668._validate_own_guard(ROOT, ci668._document()))

    def test_current_outer_routes_old_ui_geometry_and_webview_source_owners_without_native_or_restored_execution(self):
        import ios_geometry_simulator_source_projection as geometry
        import ios_owned_geometry_fixture_recovery as geometry_recovery
        import platform_recovery659_source_projection as platform
        import ios_ui_split664_source_projection as split
        name = "scripts/ci/test_ios_geometry_simulator_source_projection.py"
        raw = (ROOT / name).read_bytes()
        self.assertEqual("a80980b48069ac0b83a18d71f43e2c71df698f4cf3c7a7d0a66fd0944864c4f9", sha(geometry.current_source_before_owned_geometry(name, raw)))
        self.assertEqual("a13aa64cdc102fe1d755c5e4c95c7a5e4b24330f32109312927a688713b150d4", sha(recovery.current_source_before_producer698(name, raw)))
        name = "scripts/ci/test_tooling656_fixture_recovery.py"; raw = (ROOT / name).read_bytes()
        self.assertEqual("8107f77ebc0e2c74aa4fcf6b55eed9b644160fb8bdfb8e19d8670dee4bd71e33", sha(platform.current_source_before_platform_recovery659(name, raw)))
        name = "scripts/ci/test_webview_content_policy_source_projection.py"; raw = (ROOT / name).read_bytes()
        self.assertEqual("9649bca14a080999da984b852cc3ab360e88f928c3c0bf59a252168e4fb04dd3", sha(platform.current_source_before_platform_recovery659(name, raw)))
        self.assertTrue(geometry_recovery.validate_current_sources(ROOT))
        self.assertTrue(geometry.validate_current_sources(ROOT))
        source = ast.parse((ROOT / recovery.SOURCE_RELATIVE).read_bytes())
        prohibited = {"exec", "eval", "compile", "__import__", "run", "Popen", "write_bytes", "write_text"}
        regex = [node for node in ast.walk(source) if isinstance(node, ast.Call) and ast.unparse(node.func) == "re.compile"]
        self.assertEqual(1, len(regex))
        self.assertEqual(1, len(regex[0].args))
        self.assertEqual([], regex[0].keywords)
        self.assertEqual(r"[0-9a-f]{64}\Z", ast.literal_eval(regex[0].args[0]))
        self.assertFalse(any(isinstance(node, ast.Call) and ast.unparse(node.func).rsplit(".", 1)[-1] in prohibited and
                             ast.unparse(node.func) != "re.compile" for node in ast.walk(source)))
        self.assertEqual("7f83bd970329ad885821f80a0f56cf9a8d27a58e8e5a8c8b354a124e544ee8a4", sha((ROOT / "calf-ui/build.gradle.kts").read_bytes()))
