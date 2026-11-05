"""New finite AST/source/XML models only; no full-module import, CLI, SDK, Gradle or native replay."""
from __future__ import annotations

import ast
from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import types
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from native_matrix_declarative_aliases import native_aliases, validate_literal_matrix_declarations
from android_permission_selected_context import (camera_callback_admission_context,
    permission_lifecycle_context, permission_spec_extension)

TREE = Path(os.environ.get("PERMISSION_RECOVERY_REVIEW_TREE", Path(__file__).resolve().parents[2])).resolve()
REFERENCE = Path(os.environ.get("PERMISSION_RECOVERY_REVIEW_REFERENCE", TREE)).resolve()
PROFILE = "android-permission-demo-call-denial-recovery"
CORE = "calf-permissions/core"
CLASS = "com.mohamedrejeb.calf.permissions.AndroidPermissionDemoDeviceTest"
SOURCE = CORE + "/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/permissions/AndroidPermissionDemoDeviceTest.kt"
METHODS = ("callOnFreshApprovedVariantUsesPublicRequestAndActualSystemGrant",
           "denialThenPermanentDenialKeepsActualRationaleAndOneResultPerRequest")
PICKER = "pickersReadRealDocumentsAndImagesWithoutAllFilesOrSmsPermissions"
SDK = "cmdline-tools;23.0 platforms;android-37.0 build-tools;36.0.0 emulator system-images;android-35;google_apis;x86_64"


def source_at(relative, *, reference=False):
    return ((REFERENCE if reference else TREE) / relative).read_text()


def syntax():
    return ast.parse(source_at("scripts/ci/library_tests.py"))


def named_function(tree, name):
    matches = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name]
    if len(matches) != 1:
        raise AssertionError("The exact owning source function or class is required")
    return matches[0]


def assignment(tree, name):
    matches = [node for node in tree.body if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    if len(matches) != 1:
        raise AssertionError("The exact owning finite declaration is required")
    return matches[0]


def has_spec_name(node):
    return any(isinstance(item, ast.Name) and item.id == "ANDROID_PERMISSION_DEVICE_SPECS" for item in ast.walk(node))


def permission_branch(tree, function):
    matches = [node for node in ast.walk(named_function(tree, function))
               if isinstance(node, ast.If) and has_spec_name(node.test)]
    if len(matches) != 1:
        raise AssertionError("The one existing permission branch must remain owning")
    return matches[0]


def execute_nodes(nodes, env, label):
    module = ast.fix_missing_locations(ast.Module(body=deepcopy(nodes), type_ignores=[]))
    exec(compile(module, label, "exec"), env)


def owning_environment():
    tree = syntax()
    constants = ("ANDROID_PERMISSION_DEMO_FOCUS", "ANDROID_PERMISSION_DEMO_RECOVERY_FOCUS",
                 "ANDROID_PERMISSION_DEMO_DENIAL_RECOVERY_FOCUS",
                 "ANDROID_PERMISSION_DEMO_RECOVERY_ANNOTATION",
                 "ANDROID_MEDIA_SELECTION_FOCUS", "ANDROID_PERMISSION_DEVICE_SPECS", "MAX_REPORT_BYTES", "MAX_CASES", "COUNTS")
    functions = ("android_permission_device_filter", "android_permission_device_identities", "input_digest",
                 "validate_android_permission_demo_recovery_annotation",
                 "android_permission_demo_required", "validate_android_permission_demo_plan", "NoDtdBuilder", "junit_cases", "case_counts")
    env = {"Path": Path, "re": re, "ET": ET, "Counter": Counter, "hashlib": hashlib,
           "permission_lifecycle": permission_lifecycle_context(source_at)}
    execute_nodes([assignment(tree, name) for name in constants] + [permission_spec_extension(tree)] +
                  [named_function(tree, name) for name in functions],
                  env, "selected-owning-permission-declarations-and-pure-functions")
    allowed = named_function(tree, "allowed_test_focus")
    expression = next(node.value for node in allowed.body if isinstance(node, ast.Return))
    clauses = [node for node in expression.values if has_spec_name(node)]
    if len(clauses) != 1:
        raise AssertionError("Exact permission suite/module clause required")
    narrow_allowed = deepcopy(allowed)
    narrow_allowed.body = [ast.Return(value=deepcopy(clauses[0]))]
    execute_nodes([narrow_allowed], env, "owning-permission-suite-and-module-clause")
    selected = deepcopy(ast.parse("def select_source(root, focus, selected, result):\n    pass\n").body[0])
    selected.body = deepcopy(permission_branch(tree, "plan").body) + [ast.Return(value=ast.Tuple(
        elts=[ast.Name(id="result", ctx=ast.Load()), ast.Name(id="selected", ctx=ast.Load())], ctx=ast.Load()))]
    execute_nodes([selected], env, "owning-finite-permission-source-selection-branch")
    validate = ast.parse('''def validate_permission_focus(test_plan):
    validate_android_permission_demo_plan(test_plan)
    focus = test_plan.get("explicit_test_focus")
    expected = test_plan["expected"]
    if focus not in ANDROID_PERMISSION_DEVICE_SPECS:
        raise ValueError("Unknown finite permission focus cannot broaden")
''').body[0]
    validate.body += deepcopy(permission_branch(tree, "validate_test_focus").body)
    execute_nodes([validate], env, "owning-strict-permission-plan-validation-branch")
    inventory = ast.parse('''def xml_inventory(test_plan, expected, module_cases, reports):
    pass
''').body[0]
    inventory.body = deepcopy(permission_branch(tree, "collect_reports").body)
    inventory.body += ast.parse('''counts = case_counts(module_cases)
errors = []
''').body
    collector = named_function(tree, "collect_reports")
    checks = [node for node in ast.walk(collector) if isinstance(node, ast.If) and (
        ast.unparse(node.test) == "not reports or not counts['executed']" or
        ast.unparse(node.test) == "counts['failures'] or counts['errors'] or counts['unexpected_skipped']")]
    if len(checks) != 2:
        raise AssertionError("Original nonempty/non-skipped and failure gates must remain")
    inventory.body += deepcopy(checks)
    inventory.body += ast.parse("return not policy_errors and not errors\n").body
    execute_nodes([inventory], env, "owning-one-report-exact-identities-and-outcome-gates")
    return env


def matrix_environment():
    env = {}
    # Execute bounded declarative metadata only, never import the process-backed controller or library module.
    modules = {}
    for name in ("android_device_batch_plan", "android_storage_compatibility_plan", "desktop_security_plan"):
        module = types.ModuleType(name)
        module.__file__ = "selected-declarative-metadata/" + name + ".py"
        modules[name] = module
    with patch.dict(sys.modules, modules):
        for name, module in modules.items():
            exec(compile(source_at("scripts/ci/" + name + ".py", reference=True), module.__file__, "exec"), module.__dict__)
    env.update(android_batch_plan=modules["android_device_batch_plan"], storage_plan=modules["android_storage_compatibility_plan"],
               desktop_security_plan=modules["desktop_security_plan"],
               permission_lifecycle=permission_lifecycle_context(source_at))
    tree = ast.parse(source_at("scripts/ci/workflow_matrix.py"))
    aliases = native_aliases(tree, source_at)
    validate_literal_matrix_declarations(tree, aliases)
    env.update(aliases)
    execute_nodes([assignment(tree, name) for name in ("SLOTS", "PROFILES", "MODULE_SUBSETS")] + [named_function(tree, "matrix")],
                  env, "selected-declarative-matrix-and-existing-finite-function")
    return env


def plan_model(env):
    inputs = {"synthetic-only-source-not-an-actual-contract": "1" * 64}
    return {"suite": "android-device", "explicit_test_focus": PROFILE,
        "explicit_module_subset": [CORE], "complete_suite_requested": False,
        "android_permission_demo": {"package": "io.github.apdelrahman1911.nativecmpkit.verification.permissiondemo",
            "source_fixture": "tests/consumer/android-permission-demo", "source_contract": {
                "source_policy_verified": True, "native_or_compile_success_inferred": False,
                "source_inputs": inputs, "source_inputs_sha256": env["input_digest"](inputs)}},
        "expected": [{"module": CORE, "project": ":calf-permissions:calf-permissions-core",
            "task": ":calf-permissions:calf-permissions-core:connectedAndroidDeviceTest",
            "report_directory": CORE + "/build/outputs/androidTest-results/connected/androidMain",
            "test_filter": env["android_permission_device_filter"](PROFILE), "test_filter_argument": "annotation",
            "required_testcases": env["android_permission_device_identities"](PROFILE), "test_source_files": [SOURCE]}]}


def xml_model(methods=METHODS, *, outcome=None, classname=CLASS):
    suite = ET.Element("testsuite", {"name": "synthetic-owning-permission-recovery", "tests": str(len(methods)),
        "failures": "1" if outcome == "failure" else "0", "errors": "1" if outcome == "error" else "0",
        "skipped": "1" if outcome == "skipped" else "0"})
    for index, method in enumerate(methods):
        case = ET.SubElement(suite, "testcase", {"classname": classname, "name": method})
        if outcome and index == 0:
            ET.SubElement(case, outcome)
    return ET.tostring(suite)


class AndroidPermissionDemoCallDenialRecoveryTests(unittest.TestCase):
    def setUp(self):
        def forbidden(*args, **kwargs):
            raise AssertionError("A finite source/model guard must not execute an external process")
        self.run_patch = patch.object(subprocess, "run", forbidden)
        self.popen_patch = patch.object(subprocess, "Popen", forbidden)
        self.run_patch.start()
        self.popen_patch.start()
        self.addCleanup(self.run_patch.stop)
        self.addCleanup(self.popen_patch.stop)

    def test_new_focus_selects_only_call_and_denial_with_complete_original_declarations(self):
        self.assertIn('ANDROID_PERMISSION_DEMO_RECOVERY_FOCUS = "' + PROFILE + '"', source_at("scripts/ci/library_tests.py"))
        env = owning_environment()
        spec = env["ANDROID_PERMISSION_DEVICE_SPECS"][PROFILE]
        self.assertEqual(CLASS, spec["classname"])
        self.assertEqual(SOURCE, spec["source"])
        self.assertEqual(METHODS, spec["methods"])
        self.assertEqual(METHODS + (PICKER,), spec["declared_methods"])
        expected = env["ANDROID_PERMISSION_DEMO_RECOVERY_ANNOTATION"]
        self.assertEqual(expected, env["android_permission_device_filter"](PROFILE))
        self.assertEqual([{"classname": CLASS, "name": method} for method in METHODS],
            env["android_permission_device_identities"](PROFILE))
        self.assertNotIn(PICKER, expected)
        for name in ("", "all", "android-permission-demo", "unknown", "$(env)"):
            with self.subTest(unreviewed_focus=name), self.assertRaises(KeyError):
                env["android_permission_device_filter"](name)

    def test_original_three_method_media_and_serial_batch_profiles_remain_unmodified(self):
        env = owning_environment()
        original = env["ANDROID_PERMISSION_DEVICE_SPECS"][env["ANDROID_PERMISSION_DEMO_FOCUS"]]
        self.assertEqual(METHODS + (PICKER,), original["methods"])
        self.assertNotIn("declared_methods", original)
        self.assertEqual(CLASS, env["android_permission_device_filter"](env["ANDROID_PERMISSION_DEMO_FOCUS"]))
        media = env["ANDROID_PERMISSION_DEVICE_SPECS"][env["ANDROID_MEDIA_SELECTION_FOCUS"]]
        self.assertEqual(("realPlatformMediaSelectionIsReflectedByPublicLibraryStates",), media["methods"])
        self.assertEqual(media["classname"], env["android_permission_device_filter"](env["ANDROID_MEDIA_SELECTION_FOCUS"]))
        workflow = matrix_environment()
        original_row, = workflow["matrix"]("android-permission-demo")["include"]
        self.assertEqual(("35", CORE, "android-permission-demo-contracts"),
            (original_row["emulator-api"], original_row["test-modules"], original_row["test-focus"]))
        fixed = workflow["android_batch_plan"]
        self.assertEqual(("android-permission-demo", "android-storage-api35-normal", "android-storage-api35-all-files"),
            fixed.BATCHES["android-permission-storage-api35-recovery"])
        self.assertEqual(("android-io-reference-regressions", "android-permission-demo", "android-storage-api35-normal",
            "android-storage-api35-all-files"), fixed.BATCHES["android-io-permission-storage-api35"])
        self.assertNotIn(PROFILE, fixed.BATCHES)
        self.assertNotIn(PROFILE, fixed.SELECTIONS)
        self.assertEqual(11, len(workflow["matrix"]("all")["include"]))

    def test_owning_source_branch_requires_all_three_declarations_not_just_selected_two(self):
        env = owning_environment()
        native = source_at(SOURCE)
        class Snapshot:
            def __init__(self, value): self.value = value
            def read_text(self, *, encoding):
                if encoding != "utf-8": raise AssertionError("Exact native source encoding required")
                return self.value
        def select(value, source_files=(SOURCE,)):
            def path(root, relative):
                if relative != SOURCE: raise AssertionError("Unknown native source inventory")
                return Snapshot(value)
            env["safe_path"] = path
            return env["select_source"](None, PROFILE, [{"test_source_files": list(source_files)}], {})
        result, selected = select(native)
        self.assertEqual(PROFILE, result["explicit_test_focus"])
        self.assertEqual(2, len(selected[0]["required_testcases"]))
        self.assertEqual(env["ANDROID_PERMISSION_DEMO_RECOVERY_ANNOTATION"], selected[0]["test_filter"])
        self.assertEqual("annotation", selected[0]["test_filter_argument"])
        for old, new in (
            ("@Test fun " + PICKER, "fun " + PICKER),
            ("@Test fun " + METHODS[0], "@Test fun unreviewedCallReplacement"),
            ("class AndroidPermissionDemoDeviceTest", "class UnknownNativeTest"),
            ("package com.mohamedrejeb.calf.permissions", "package foreign.synthetic"),
        ):
            with self.subTest(declaration_mutation=old), self.assertRaises(ValueError): select(native.replace(old, new, 1))
        for extra in ("\n@Test fun extraUnreviewedMethod() {}\n", "\n@Ignore\n"):
            with self.subTest(extra_declaration=extra), self.assertRaises(ValueError): select(native + extra)
        with self.assertRaises(ValueError): select(native, source_files=())

    def test_strict_plan_fields_reject_whole_class_picker_missing_or_foreign_scope(self):
        env = owning_environment()
        original = plan_model(env)
        self.assertTrue(env["validate_permission_focus"](original))
        mutations = (
            lambda p: p.update(suite="android-host"),
            lambda p: p.update(explicit_module_subset=[CORE, "calf-io"]),
            lambda p: p.update(complete_suite_requested=True),
            lambda p: p["expected"][0].update(module="calf-io"),
            lambda p: p["expected"][0].update(project=":calf-permissions:core"),
            lambda p: p["expected"][0].update(task=":calf-permissions:calf-permissions-core:androidHostTest"),
            lambda p: p["expected"][0].update(report_directory=CORE + "/build/test-results/androidHostTest"),
            lambda p: p["expected"][0].update(test_filter=CLASS),
            lambda p: p["expected"][0]["required_testcases"].append({"classname": CLASS, "name": PICKER}),
            lambda p: p["expected"][0]["required_testcases"].pop(),
            lambda p: p["expected"][0].update(test_source_files=[]),
            lambda p: p["expected"].append(deepcopy(p["expected"][0])),
            lambda p: p["android_permission_demo"]["source_contract"].update(source_inputs_sha256="0" * 64),
            lambda p: p["android_permission_demo"]["source_contract"].update(native_or_compile_success_inferred=True),
            lambda p: p.pop("android_permission_demo"),
        )
        for index, mutate in enumerate(mutations):
            modeled = deepcopy(original)
            mutate(modeled)
            with self.subTest(strict_plan_mutation=index), self.assertRaises(ValueError):
                env["validate_permission_focus"](modeled)

    def test_original_one_report_exact_identity_xml_and_non_skipped_outcome_gates_stay_strict(self):
        env = owning_environment()
        plan = plan_model(env)
        def accepted(payload, reports=1):
            return env["xml_inventory"](plan, plan["expected"][0], env["junit_cases"](payload), [{}] * reports)
        self.assertTrue(accepted(xml_model()))
        for payload in (xml_model(METHODS[:1]), xml_model(METHODS + (PICKER,)), xml_model(classname=CLASS + "Foreign"),
            xml_model(outcome="failure"), xml_model(outcome="error"), xml_model(outcome="skipped")):
            with self.subTest(strict_case_shape=hashlib.sha256(payload).hexdigest()):
                self.assertFalse(accepted(payload))
        self.assertFalse(accepted(xml_model(), reports=0))
        self.assertFalse(accepted(xml_model(), reports=2))
        duplicate = xml_model(METHODS + (METHODS[0],))
        contradiction = xml_model().replace(b'tests="2"', b'tests="3"')
        conflict = xml_model(outcome="failure").replace(b'<failure />', b'<failure /><error />')
        for payload in (duplicate, contradiction, conflict, b'<!DOCTYPE testsuite [<!ENTITY x "synthetic">]>' + xml_model()):
            with self.subTest(strict_parser_shape=hashlib.sha256(payload).hexdigest()), self.assertRaises(ValueError):
                env["junit_cases"](payload)

    def test_new_profile_is_one_api35_core_slot_with_literal_sdk_and_no_batch_or_serial_fallback(self):
        env = matrix_environment()
        row, = env["matrix"](PROFILE)["include"]
        self.assertEqual({"slot": "android-device-api35-permission-call-denial-recovery", "suite": "android-device",
            "runner": "ubuntu-24.04", "arch": "x64", "python": "python3", "emulator-api": "35",
            "test-modules": CORE, "test-focus": PROFILE}, row)
        self.assertNotIn("android-batch", row)
        self.assertFalse(any(key.startswith("serial-") for key in row))
        workflow = source_at(".github/workflows/gradle.yml")
        parser_tree = ast.parse(source_at("scripts/ci/test_ios_io_profile.py", reference=True))
        parser_env = {"re": re}
        execute_nodes([named_function(parser_tree, "profile_options")], parser_env, "existing-strict-literal-choice-parser-only")
        options = parser_env["profile_options"](workflow)
        self.assertEqual(set(env["PROFILES"]), set(options))
        self.assertEqual(1, options.count(PROFILE))
        for bad in (workflow.replace(PROFILE + ",", PROFILE + ", " + PROFILE + ",", 1),
                    workflow.replace(PROFILE + ",", "$(env),", 1)):
            with self.assertRaises(ValueError): parser_env["profile_options"](bad)
        branches = re.findall(r"inputs\.profile == '" + PROFILE + r"' && '([^'\n]+)'", workflow)
        self.assertEqual([SDK], branches)
        self.assertEqual([SDK], re.findall(r"inputs\.profile == 'android-permission-demo' && '([^'\n]+)'", workflow))
        self.assertIn('"$PYTHON" scripts/ci/android_device_tests.py "${args[@]}"', workflow)

    def test_recovery_uses_existing_complete_helper_sources_cli_and_exact_api_admission(self):
        env = owning_environment()
        self.assertTrue(env["allowed_test_focus"]("android-device", (CORE,), PROFILE))
        for suite, modules in (("android-host", (CORE,)), ("android-device", None), ("android-device", ("calf-io",)),
            ("android-device", (CORE, "calf-io"))):
            self.assertFalse(env["allowed_test_focus"](suite, modules, PROFILE))
        device_source = source_at("scripts/ci/android_device_tests.py", reference=True)
        self.assertIn("*lt.ANDROID_PERMISSION_DEVICE_SPECS", device_source)
        self.assertIn("*ANDROID_PERMISSION_DEVICE_SPECS", source_at("scripts/ci/library_tests.py"))
        workflow = matrix_environment()
        native = types.SimpleNamespace(ANDROID_WEBVIEW_REQUEST_FOCUS="android-webview-request-state",
            content_policy=types.SimpleNamespace(ANDROID_FOCUS="webview-content-policy-android"),
            ANDROID_WEBVIEW_STOP_REDIRECT_RECOVERY_FOCUS="android-webview-stop-redirect-recovery",
            ANDROID_IO_NAMED_SYSTEM_FOCUS="android-io-named-system-providers",
            ANDROID_IO_UNAVAILABLE_FOCUS="android-io-provider-unavailable",
            ANDROID_STORAGE_FOCUSES=frozenset(row.profile for row in workflow["storage_plan"].ROWS),
            storage_plan=workflow["storage_plan"], ANDROID_STORAGE_MODULE=CORE,
            ANDROID_CAMERA_PROVIDER_FOCUSES=("android-camera-provider-contracts", "android-camera-no-handler-recovery"),
            ANDROID_MEDIA_SELECTION_FOCUS=env["ANDROID_MEDIA_SELECTION_FOCUS"])
        native.camera_callback = camera_callback_admission_context(source_at)
        library_env = {"camera_callback": native.camera_callback}
        execute_nodes([assignment(syntax(), name) for name in (
            "ANDROID_CAMERA_PROVIDER_FOCUS", "ANDROID_CAMERA_NO_HANDLER_FOCUS", "ANDROID_CAMERA_PROVIDER_FOCUSES",
            "ANDROID_CAMERA_RESTORATION_FOCUS", "ANDROID_CAMERA_DONT_KEEP_FOCUS", "ANDROID_CAMERA_RESTORATION_FOCUSES",
            "ANDROID_CAMERA_FOCUSES", "ANDROID_IO_REMOTE_FOCUSES")], library_env,
            "actual-finite-camera-and-remote-admission-declarations-only")
        native.ANDROID_CAMERA_FOCUSES = library_env["ANDROID_CAMERA_FOCUSES"]
        native.ANDROID_IO_REMOTE_FOCUSES = library_env["ANDROID_IO_REMOTE_FOCUSES"]
        api_env = {"lt": native, "API": 35,
                   "permission_lifecycle_contract": env["permission_lifecycle"]}
        execute_nodes([named_function(ast.parse(device_source), "validate_api_selection")], api_env,
            "existing-exact-api-admission-only")
        api_env["validate_api_selection"](35, (CORE,), PROFILE)
        for api in (True, "35", 23, 28, 33, 34, 36):
            with self.subTest(unreviewed_api=api), self.assertRaises(ValueError):
                api_env["validate_api_selection"](api, (CORE,), PROFILE)
        helper_tree = ast.parse(source_at("scripts/ci/android_permission_demo.py", reference=True))
        helper_env = {}
        execute_nodes([assignment(helper_tree, name) for name in
            ("PACKAGE", "REPORTER", "FIXTURE", "KOTLIN", "APPLICATION_KOTLIN", "SOURCE_FILES")],
            helper_env, "unchanged-complete-permission-source-file-contract-only")
        sources = helper_env["SOURCE_FILES"]
        self.assertIn(SOURCE, sources)
        self.assertIn(CORE + "/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/permissions/PermissionDemoSystemUi.kt", sources)
        self.assertTrue(any(path.endswith("AndroidMediaSelectionDeviceTest.kt") for path in sources))
        self.assertTrue(any(path.endswith("PermissionDemoActivity.kt") for path in sources))
        self.assertTrue(any(path.endswith("PermissionDemoService.kt") for path in sources))
        self.assertIn("tests/consumer/android-permission-demo/src/main/AndroidManifest.xml", sources)
        self.assertEqual(13, len(sources))
        self.assertIn('"source_contract": android_permission_demo.source_contract(root)', source_at("scripts/ci/library_tests.py"))


if __name__ == "__main__":
    unittest.main()
