# SPDX-License-Identifier: Apache-2.0
"""Essential NEW656 fixture/source controls; zero compiler, controller or native IO.

These controls run only after the single final outer659 composition is frozen.
They do not replay accepted Camera models or execute inverse-reconstructed code.
"""
from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path
import re
import subprocess
import types
import unittest
from unittest.mock import patch

import camera_recents_source_projection as recents
import webview_content_policy_source_projection as content_history

ROOT = Path(__file__).resolve().parents[2]
CONTENT_FOCUS = "webview-content-policy-android"
PERMISSION_FOCUS = "android-permission-demo-call-denial-recovery"
PERMISSION_CORE = "calf-permissions/core"
IMAGE_CONTROL = "scripts/ci/test_apple_image_launcher_source_projection.py"


def function(tree, name):
    matches = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(matches) != 1:
        raise AssertionError("One exact named source function is required")
    return matches[0]


def call_name(node):
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return ast.unparse(node.func)
    raise AssertionError("One exact named source call is required")


def selector_environment():
    """Execute only the exact owning pure AST extractors, never the full module."""
    tree = ast.parse((ROOT / "scripts/ci/test_android_permission_demo_selector.py").read_bytes())
    names = ("function", "permission_branch", "compile_nodes", "owning_environment")
    namespace = {"ast": ast, "deepcopy": deepcopy, "Path": Path, "re": re, "types": types,
                 "CORE": PERMISSION_CORE, "PROFILE": PERMISSION_FOCUS,
                 "source": lambda relative: (ROOT / relative).read_text(encoding="utf-8")}
    nodes = [deepcopy(function(tree, name)) for name in names]
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                 "selected-owning-pure-permission-source-extractors", "exec"), namespace)
    return namespace["owning_environment"]()[1]


class Tooling656FixtureRecoveryControls(unittest.TestCase):
    def setUp(self):
        def forbidden(*args, **kwargs):
            raise AssertionError("A source fixture control cannot execute external processes")
        for name in ("run", "Popen"):
            control = patch.object(subprocess, name, forbidden)
            control.start()
            self.addCleanup(control.stop)

    def test_one_complete_fixture_derivative_keeps_original_pin_and_refuses_stale_partial_and_type_drift(self):
        self.assertEqual(IMAGE_CONTROL, content_history._TOOLING656_CONTROL_PATH)
        binding = content_history._TOOLING656_CONTROL_BINDING
        raw = (ROOT / IMAGE_CONTROL).read_bytes()
        before = content_history._current_tooling656_control_source(IMAGE_CONTROL, raw)
        sealed = content_history._document()["unchanged_inputs"][IMAGE_CONTROL]
        self.assertEqual("9d7870ffcd1cf584c7e2914143d93066defba889638df05f0f91781ab5dd2fa9", sealed)
        self.assertEqual((sealed, binding["before_bytes"]), (content_history.sha(before), len(before)))
        self.assertEqual((binding["after_sha256"], binding["after_bytes"]), (content_history.sha(raw), len(raw)))
        old_fragment, new_fragment = binding["before"].encode(), binding["after"].encode()
        self.assertEqual(1, before.count(old_fragment))
        self.assertEqual(1, raw.count(new_fragment))
        self.assertEqual(raw, before.replace(old_fragment, new_fragment, 1))
        foreign = (ROOT / "scripts/ci/camera_recents_source_projection.py").read_bytes()
        displaced = raw.replace(new_fragment, b"", 1) + new_fragment
        for bad in (before, raw + b"\n", raw[:-1], displaced, foreign, b"", None, bytearray(raw), raw.decode()):
            with self.subTest(kind=type(bad).__name__), self.assertRaises(ValueError):
                content_history._current_tooling656_control_source(IMAGE_CONTROL, bad)
        with self.assertRaises(ValueError):
            content_history._current_tooling656_control_source(Path(IMAGE_CONTROL), raw)
        unlisted = "unlisted-source-is-not-certified"
        self.assertIs(raw, content_history._current_tooling656_control_source(unlisted, raw))
        changed = deepcopy(binding)
        changed["after_fragment_sha256"] = "0" * 64
        with patch.object(content_history, "_TOOLING656_CONTROL_BINDING", changed), self.assertRaises(ValueError):
            content_history._current_tooling656_control_source(IMAGE_CONTROL, raw)
        document = deepcopy(content_history._document())
        document["unchanged_inputs"][IMAGE_CONTROL] = "0" * 64
        with patch.object(content_history, "_document", return_value=document), self.assertRaises(ValueError):
            content_history._current_tooling656_control_source(IMAGE_CONTROL, raw)

    def test_latest_raw_admission_and_idempotent_recents_ancestor_are_distinct_domains(self):
        for relative, binding in recents._bindings().items():
            raw = (ROOT / relative).read_bytes()
            stage = content_history.current_source_before_content_policy(relative, raw)
            self.assertEqual(binding["after_sha256"], content_history.sha(stage), relative)
            before = recents.current_source_before_recents_observation(relative, raw)
            self.assertEqual(binding["before_sha256"], content_history.sha(before), relative)
            with patch.object(content_history, "current_source_before_content_policy",
                              side_effect=AssertionError("A dated reader cannot admit latest current again")):
                self.assertEqual(before, recents.current_source_before_recents_observation(relative, stage))
                self.assertIs(before, recents.source_before_recents_observation(relative, before))
            for bad in (before, stage + b"\n", stage[:-1], b"unknown", b"", None, bytearray(stage)):
                with self.subTest(relative=relative, kind=type(bad).__name__), self.assertRaises(ValueError):
                    recents.current_source_before_recents_observation(relative, bad)
            if relative in content_history.BOUND_PATHS:
                with self.assertRaises(ValueError):
                    content_history.current_source_before_content_policy(relative, stage)

    def test_exact_real_content_namespace_drives_filter_and_api35_not_empty_bypass(self):
        focus_tree = ast.parse((ROOT / "scripts/ci/webview_content_policy_native_focus.py").read_bytes())
        declarations = [node.value for node in focus_tree.body if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "ANDROID_FOCUS" for target in node.targets)]
        self.assertEqual(1, len(declarations))
        self.assertEqual(CONTENT_FOCUS, ast.literal_eval(declarations[0]))
        env = selector_environment()
        self.assertIs(type(env["content_policy"]), types.SimpleNamespace)
        self.assertEqual(CONTENT_FOCUS, env["content_policy"].ANDROID_FOCUS)
        item = {"test_filter": "owning-content-policy-filter"}
        self.assertEqual(["-Pandroid.testInstrumentationRunnerArguments.filter=" + item["test_filter"]],
                         env["selector_property"](CONTENT_FOCUS, item))
        annotation = env["ANDROID_PERMISSION_DEMO_RECOVERY_ANNOTATION"]
        self.assertEqual(["-Pandroid.testInstrumentationRunnerArguments.annotation=" + annotation],
                         env["selector_property"](PERMISSION_FOCUS, {"test_filter": annotation}))
        recovery = ast.parse((ROOT / "scripts/ci/test_android_permission_demo_call_denial_recovery.py").read_bytes())
        owner = function(recovery, "test_recovery_uses_existing_complete_helper_sources_cli_and_exact_api_admission")
        native = [node.value for node in ast.walk(owner) if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "native" for target in node.targets)]
        self.assertEqual(1, len(native))
        namespace = [keyword.value for keyword in native[0].keywords if keyword.arg == "content_policy"]
        self.assertEqual(1, len(namespace))
        selected = ast.Assign(targets=[ast.Name(id="selected_content_policy", ctx=ast.Store())], value=deepcopy(namespace[0]))
        api_env = {"types": types, "API": 35}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[selected], type_ignores=[])),
                     "exact-owning-content-namespace-keyword-only", "exec"), api_env)
        self.assertIs(type(api_env["selected_content_policy"]), types.SimpleNamespace)
        self.assertEqual(CONTENT_FOCUS, api_env["selected_content_policy"].ANDROID_FOCUS)
        api_env["lt"] = types.SimpleNamespace(content_policy=api_env["selected_content_policy"])
        owner = function(ast.parse((ROOT / "scripts/ci/android_device_tests.py").read_bytes()), "validate_api_selection")
        exec(compile(ast.Module(body=[owner], type_ignores=[]), "unchanged-owning-api-source-only", "exec"), api_env)
        self.assertIsNone(api_env["validate_api_selection"](35, ("calf-webview",), CONTENT_FOCUS))
        for api, modules in ((True, ("calf-webview",)), ("35", ("calf-webview",)), (34, ("calf-webview",)),
                             (36, ("calf-webview",)), (35, (PERMISSION_CORE,)), (35, ("calf-webview", "calf-io")),
                             (35, None), (35, ["calf-webview"])):
            with self.subTest(api=api, modules=modules), self.assertRaises(ValueError):
                api_env["validate_api_selection"](api, modules, CONTENT_FOCUS)

    def test_ancestor_hooks_and_exact_image_operand_keep_every_original_method_and_assertion(self):
        tree = ast.parse((ROOT / "scripts/ci/camera_recents_source_projection.py").read_bytes())
        for name, old_reader in (("source_before_recents_observation", "source_before_recents_fixture"),
                                 ("current_source_before_recents_observation", "recents_fixture_after_qualified_outer_ingress")):
            owner = function(tree, name)
            payload_calls = [node.value for node in owner.body if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "payload" for target in node.targets)]
            self.assertEqual(["peel_content_policy_for_history", old_reader], [call_name(node) for node in payload_calls])
            self.assertNotIn("current_source_before_content_policy", [call_name(node) for node in ast.walk(owner) if isinstance(node, ast.Call)])
        source_tree = ast.parse((ROOT / "scripts/ci/test_camera_recents_observation.py").read_bytes())
        owners = [node for node in source_tree.body if isinstance(node, ast.ClassDef) and node.name == "CameraRecentsSourceControls"]
        self.assertEqual(1, len(owners))
        setup = function(owners[0], "setUpClass")
        calls = [node for node in ast.walk(setup) if isinstance(node, ast.Call) and
                 call_name(node) == "content_history.current_source_before_content_policy"]
        self.assertEqual(1, len(calls))
        from tooling_recovery671_source_projection import current_source_before_tooling671
        current = current_source_before_tooling671(IMAGE_CONTROL, (ROOT / IMAGE_CONTROL).read_bytes())
        previous = content_history._current_tooling656_control_source(IMAGE_CONTROL, current)
        old_tree, new_tree = ast.parse(previous), ast.parse(current)
        self.assertEqual([node.name for node in ast.walk(old_tree) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")],
                         [node.name for node in ast.walk(new_tree) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")])
        def assertions(value):
            return [ast.dump(node, include_attributes=False) for node in ast.walk(value) if isinstance(node, ast.Call) and
                    isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and
                    node.func.value.id == "self" and node.func.attr.startswith("assert")]
        self.assertEqual(assertions(old_tree), assertions(new_tree))
        name = "test_image609_sources_hook_finally_launch_argv_and_deadline_are_unchanged"
        old_method, new_method = function(old_tree, name), deepcopy(function(new_tree, name))
        assignments = [node for node in new_method.body if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "current" for target in node.targets)]
        self.assertEqual(1, len(assignments))
        self.assertEqual("ui_history.peel_ui_related_for_history", call_name(assignments[0].value))
        old_assignment = next(node for node in old_method.body if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "current" for target in node.targets))
        new_method.body[new_method.body.index(assignments[0])] = deepcopy(old_assignment)
        self.assertEqual(ast.dump(old_method, include_attributes=False), ast.dump(new_method, include_attributes=False))
        guard = function(ast.parse((ROOT / content_history.SOURCE_RELATIVE).read_bytes()), "_current_tooling656_control_source")
        prohibited = {"exec", "eval", "compile", "__import__", "open", "run", "Popen", "write_bytes", "write_text"}
        self.assertFalse(any(call_name(node).rsplit(".", 1)[-1] in prohibited for node in ast.walk(guard) if isinstance(node, ast.Call)))


if __name__ == "__main__":
    unittest.main()
