# SPDX-License-Identifier: Apache-2.0
"""NEW finite wiring models with synthetic inventories, never captured native data."""
import ast
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import tomllib
import unittest
from unittest.mock import Mock, patch

import ios_adaptive_controls_runtime as adaptive_runtime
import ios_ui_related_native_focus as related
import ios_ui_related_source_projection as history
import ios_ui_application as application
import library_tests as library
import runtime_context as runtime
import workflow_matrix as workflow
from test_ios_ui_related_native_focus import model_plan

ROOT = Path(__file__).resolve().parents[2]
PRE_UUID = "11111111-2222-3333-4444-555555555555"
NEW_UUID = "AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE"
PROFILES = ("ios-ui-adaptive-pre26", "ios-ui-adaptive-drag-shader-ios26plus")


def synthetic_inventory():
    versions = (("18-0", "18.0", "22A3354", PRE_UUID), ("26-4", "26.4.1", "23E254a", NEW_UUID))
    runtimes, devices = [], {}
    for identifier, version, build, udid in versions:
        key = "com.apple.CoreSimulator.SimRuntime.iOS-" + identifier
        runtimes.append({"identifier": key, "version": version, "buildversion": build, "isAvailable": True})
        devices[key] = [{"udid": udid, "name": "Synthetic model only", "state": "Booted", "isAvailable": True,
                         "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17"}]
    return {"devices": devices}, {"runtimes": runtimes}


def synthetic_context(focus, udid):
    devices, runtimes = synthetic_inventory()
    return {"schema_version": 1, "host": {"system": "Darwin", "architecture": "arm64", "python": "3.13"},
            "source_revision": "a" * 40, "source_tree_dirty": False,
            "adaptive_runtime_focus": related.runtime_focus(focus),
            "simulator": adaptive_runtime.select_iphone_json(json.dumps(devices), json.dumps(runtimes),
                                                             related.runtime_focus(focus), udid=udid)}


def command_model(devices_raw, runtimes_raw):
    rust = tomllib.loads((ROOT / "rust-toolchain.toml").read_text())["toolchain"]["channel"]
    outputs = {("git", "rev-parse", "HEAD"): "a" * 40 + "\n",
               ("git", "status", "--porcelain", "--untracked-files=normal"): "",
               ("java", "-version"): 'openjdk version "17.0.18"\n',
               ("rustc", "--version", "--verbose"): "release: " + rust + "\nhost: aarch64-apple-darwin\ncommit-hash: " + "b" * 40 + "\ncommit-date: 2026-10-01\n",
               ("xcodebuild", "-version"): "Xcode 26.5\nBuild version 17F42\n",
               ("xcrun", "simctl", "list", "devices", "--json"): devices_raw,
               ("xcrun", "simctl", "list", "runtimes", "--json"): runtimes_raw}
    outputs.update({("xcrun", "--sdk", sdk, "--show-sdk-version"): "26.5\n"
                    for sdk in ("macosx", "iphoneos", "iphonesimulator")})
    return lambda *args: outputs[args]


def capture_model(focus=None, *, udid=None, devices=None, runtimes=None):
    if devices is None or runtimes is None:
        devices, runtimes = synthetic_inventory()
    with patch.object(runtime.platform, "machine", return_value="arm64"), \
            patch.object(runtime.platform, "system", return_value="Darwin"), \
            patch.object(runtime, "command", side_effect=command_model(json.dumps(devices), json.dumps(runtimes))):
        return runtime.capture(expected_arch="arm64", apple=True, select="iphone" if udid is None else None,
                               device=udid, require_clean=True,
                               **({"adaptive_focus": related.runtime_focus(focus)} if focus is not None else {}))


def calls(path, name):
    return [node for node in ast.walk(ast.parse((ROOT / path).read_bytes()))
            if isinstance(node, ast.Call) and ast.unparse(node.func) == name]


class RelatedUiNativeWiringControls(unittest.TestCase):
    def test_literal_profiles_modules_and_exact_canonical_rows_have_no_alias_or_serial_companion(self):
        tree = ast.parse((ROOT / "scripts/ci/workflow_matrix.py").read_bytes())
        definitions = {target.id: node.value for node in tree.body if isinstance(node, ast.Assign)
                       for target in node.targets if isinstance(target, ast.Name) and target.id in {"PROFILES", "MODULE_SUBSETS"}}
        for profile, focus in zip(PROFILES, related.FOCUSES):
            for name, wanted in (("PROFILES", ("ios-iphone",)), ("MODULE_SUBSETS", "calf-ui")):
                node = definitions[name]; value = next(value for key, value in zip(node.keys, node.values)
                                                      if isinstance(key, ast.Constant) and key.value == profile)
                self.assertEqual(wanted, ast.literal_eval(value))
                self.assertFalse(any(isinstance(child, (ast.Name, ast.Attribute)) for child in ast.walk(value)))
            row = {"slot": "ios-iphone", "suite": "ios", "runner": "macos-26", "arch": "arm64", "python": "python3",
                   "simulator-kind": "iphone", "test-modules": "calf-ui", "test-focus": focus}
            self.assertEqual({"include": [row]}, workflow.matrix(profile))
            for field, bad in (("runner", "macos-15"), ("arch", "x64"), ("python", "python"),
                               ("suite", "desktop"), ("simulator-kind", "ipad"), ("extra", "unknown")):
                slots = copy.deepcopy(workflow.SLOTS)
                for slot in slots:
                    if slot["slot"] == "ios-iphone": slot[field] = bad
                with patch.object(workflow, "SLOTS", slots), self.assertRaises(ValueError): workflow.matrix(profile)
            with patch.dict(workflow.PROFILES, {profile: ("ios-iphone", "ios-ipad")}), self.assertRaises(ValueError):
                workflow.matrix(profile)

    def test_native_registry_and_gradle_requests_select_only_exact_ten_or_four(self):
        for focus in related.FOCUSES:
            self.assertEqual(related.focus_spec(focus), library.UI_APPLICATION_FOCUS_SPECS[focus])
            plan = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=focus)
            self.assertTrue(related.validate_plan(plan)); self.assertTrue(library.validate_test_focus(plan))
            command = library.gradle_command("ios", plan, NEW_UUID, root=ROOT)
            self.assertIn(related.init_script(focus), command)
            self.assertIn("-P" + related.focus_property(focus) + "=" + focus, command)
            self.assertIn("-PnativecmpkitSimulatorDevice=" + NEW_UUID, command)
            self.assertEqual(related.native_request(focus), command[command.index(related.TASK):])
            self.assertNotIn("scripts/ci/ui_drag_shader_compile.init.gradle.kts", command)
            self.assertNotIn("scripts/ci/adaptive_controls_compile.init.gradle.kts", command)
        self.assertNotIn("ui-native-adaptive-ios26plus", library.UI_APPLICATION_FOCUS_SPECS)

    def test_native_plan_rejects_source_task_module_focus_and_hash_contract_broadening(self):
        focus = related.FOCUSES[1]; original = model_plan(focus)
        for key, value in (("task", ":calf-ui:allTests"), ("project", ":other"), ("module", "calf-core"),
                           ("test_source_sets", ["commonTest", "iosTest"]), ("test_source_files", []),
                           ("test_filter", "*"), ("required_testcases", []),
                           ("report_directory", "foreign"), ("ui_related_source_contract", {})):
            changed = copy.deepcopy(original); changed["expected"][0][key] = value
            with self.assertRaises(ValueError): library.validate_test_focus(changed)
        for key, value in (("source_sha256", {}), ("common_sources", ["foreign.kt"]),
                           ("runtime_focus", related.FOCUSES[0]), ("compiler_executions_attested", True),
                           ("schema_version", True)):
            changed = copy.deepcopy(original); changed["expected"][0]["ui_related_source_contract"][key] = value
            with self.assertRaises(ValueError): related.validate_plan(changed)
        for key, value in (("suite", "desktop"), ("explicit_module_subset", ["calf-ui", "calf-core"]),
                           ("complete_suite_requested", True), ("explicit_test_focus", "ui-native-adaptive-ios26plus")):
            changed = copy.deepcopy(original); changed[key] = value
            with self.assertRaises(ValueError): library.validate_test_focus(changed)

    def test_application_filters_accept_only_exact_reviewed_methods_and_permutations(self):
        for focus in related.FOCUSES:
            selected = related.selectors(focus)
            for methods in (selected, tuple(reversed(selected))):
                arguments = [*sorted(application.TEST_ARGUMENTS), "--ktest_gradle_filter=" + ",".join(methods)]
                self.assertEqual(focus, application.application_test_focus(arguments))
            for methods in (selected[:-1], selected + selected[:1], selected + ("foreign",), ("*",)):
                arguments = [*sorted(application.TEST_ARGUMENTS), "--ktest_gradle_filter=" + ",".join(methods)]
                with self.assertRaises(ValueError): application.application_test_focus(arguments)

    def test_new_capture_consumes_first_complete_raw_devices_and_runtimes_json_once(self):
        devices, runtimes = synthetic_inventory(); devices_raw = json.dumps(devices, indent=2) + "\n"
        runtimes_raw = json.dumps(runtimes, indent=2) + "\n"
        for focus, udid in zip(related.FOCUSES, (PRE_UUID, NEW_UUID)):
            with patch.object(runtime.platform, "machine", return_value="arm64"), \
                    patch.object(runtime.platform, "system", return_value="Darwin"), \
                    patch.object(runtime, "command", side_effect=command_model(devices_raw, runtimes_raw)) as query, \
                    patch.object(adaptive_runtime, "select_iphone_json", wraps=adaptive_runtime.select_iphone_json) as select:
                context = runtime.capture(expected_arch="arm64", apple=True, select="iphone", require_clean=True,
                                          adaptive_focus=related.runtime_focus(focus))
            select.assert_called_once_with(devices_raw, runtimes_raw, related.runtime_focus(focus), udid=None)
            self.assertEqual(1, query.call_args_list.count(unittest.mock.call("xcrun", "simctl", "list", "devices", "--json")))
            self.assertEqual(1, query.call_args_list.count(unittest.mock.call("xcrun", "simctl", "list", "runtimes", "--json")))
            self.assertEqual(udid, context["simulator"]["udid"])
            self.assertEqual(related.runtime_focus(focus), context["adaptive_runtime_focus"])
        self.assertEqual("26.4.1", context["simulator"]["runtime_version"])
        self.assertEqual("23E254a", context["simulator"]["runtime_build"])

    def test_new_capture_rejects_wrong_band_unavailable_and_unknown_explicit_device(self):
        with self.assertRaises(ValueError): capture_model(related.FOCUSES[0], udid=NEW_UUID)
        with self.assertRaises(ValueError): capture_model(related.FOCUSES[1], udid=PRE_UUID)
        with self.assertRaises(ValueError): capture_model(related.FOCUSES[1], udid="99999999-8888-7777-6666-555555555555")
        for availability in (False, 1):
            devices, runtimes = synthetic_inventory(); runtimes["runtimes"][-1]["isAvailable"] = availability
            with self.assertRaises(ValueError): capture_model(related.FOCUSES[1], devices=devices, runtimes=runtimes)
        with patch.object(runtime, "command", side_effect=AssertionError("Incompatible new route queried host")) as query:
            with self.assertRaises(ValueError): runtime.capture(apple=True, select="ipad", adaptive_focus=related.runtime_focus(related.FOCUSES[1]))
            query.assert_not_called()

    def test_library_preflight_and_both_application_captures_map_same_uuid_and_real_band(self):
        app_calls = [node for node in calls("scripts/ci/ios_ui_application.py", "runtime.capture")
                     if any(key.arg is None for key in node.keywords)]
        self.assertEqual(2, len(app_calls))
        library_call = next(node for node in calls("scripts/ci/library_tests.py", "runtime_context.capture")
                            if any(key.arg is None for key in node.keywords))
        self.assertEqual(2, len(calls("scripts/ci/ios_ui_application.py", "lt.ui_related.validate_context")))
        for focus, udid in zip(related.FOCUSES, (PRE_UUID, NEW_UUID)):
            context = synthetic_context(focus, udid); capture = Mock(return_value=context)
            namespace = {"runtime": SimpleNamespace(capture=capture), "runtime_context": SimpleNamespace(capture=capture),
                         "lt": library, "ui_related": related, "focus": focus, "device": udid,
                         "suite": "ios", "simulator": udid, "android_serial": None}
            for call in (*app_calls, library_call):
                result = eval(compile(ast.Expression(call), "synthetic-capture-expression-only", "eval"), namespace)
                self.assertTrue(related.validate_context(result, focus, udid=udid))
                self.assertEqual(udid, capture.call_args.kwargs["device"])
                self.assertEqual(related.runtime_focus(focus), capture.call_args.kwargs["adaptive_focus"])
                self.assertIs(True, capture.call_args.kwargs["require_clean"])
                self.assertEqual("arm64", capture.call_args.kwargs["expected_arch"])
            with self.assertRaises(ValueError): related.validate_context(context, focus, udid=NEW_UUID if udid == PRE_UUID else PRE_UUID)
        source = (ROOT / "scripts/ci/library_tests.py").read_text()
        self.assertIn('for when in ("runtime_before", "runtime_after"):', source)
        self.assertIn('ui_related.validate_context(observed, test_plan["explicit_test_focus"], udid=context["simulator"]["udid"])', source)

    def test_default_capture_and_sdk_only_native_environment_call_shapes_stay_unchanged(self):
        with patch.object(adaptive_runtime, "select_iphone_json", side_effect=AssertionError("Default capture entered new selector")) as select:
            context = capture_model()
            select.assert_not_called(); self.assertNotIn("adaptive_runtime_focus", context)
        old = history.source_before_ui_related("scripts/ci/ios_ui_application.py", (ROOT / "scripts/ci/ios_ui_application.py").read_bytes())
        old_calls = [node for node in ast.walk(ast.parse(old)) if isinstance(node, ast.Call) and ast.unparse(node.func) == "runtime.capture"]
        old_calls.sort(key=lambda node: (node.lineno, node.col_offset))
        current = sorted(calls("scripts/ci/ios_ui_application.py", "runtime.capture"), key=lambda node: (node.lineno, node.col_offset))
        self.assertEqual(3, len(current))
        for before, after in zip(old_calls, current):
            capture = Mock(); namespace = {"runtime": SimpleNamespace(capture=capture), "lt": library, "focus": None, "device": NEW_UUID}
            eval(compile(ast.Expression(before), "old-expression-only", "eval"), namespace); wanted = capture.call_args
            eval(compile(ast.Expression(after), "new-default-expression-only", "eval"), namespace)
            self.assertEqual(wanted, capture.call_args)
        self.assertEqual(ast.dump(old_calls[1], include_attributes=False), ast.dump(current[1], include_attributes=False))
        for name in ("compiler_runtime_fingerprint", "command", "simulator"):
            parent = history.source_before_ui_related("scripts/ci/runtime_context.py", (ROOT / "scripts/ci/runtime_context.py").read_bytes())
            previous = next(node for node in ast.parse(parent).body if isinstance(node, ast.FunctionDef) and node.name == name)
            latest = next(node for node in ast.parse((ROOT / "scripts/ci/runtime_context.py").read_bytes()).body if isinstance(node, ast.FunctionDef) and node.name == name)
            self.assertEqual(ast.dump(previous, include_attributes=False), ast.dump(latest, include_attributes=False))

    def test_runtime_context_marker_full_version_build_and_clean_arm64_are_required(self):
        focus = related.FOCUSES[1]; context = synthetic_context(focus, NEW_UUID)
        self.assertTrue(related.validate_context(context, focus, udid=NEW_UUID))
        self.assertEqual("26.4.1", context["simulator"]["runtime_version"])
        self.assertEqual("com.apple.CoreSimulator.SimRuntime.iOS-26-4", context["simulator"]["runtime_identifier"])
        for key, value in (("adaptive_runtime_focus", None), ("adaptive_runtime_focus", related.FOCUSES[0]),
                           ("schema_version", True), ("source_tree_dirty", True), ("source_revision", "unknown"),
                           ("host", {"system": "Linux", "architecture": "arm64"}),
                           ("host", {"system": "Darwin", "architecture": "x64"})):
            changed = copy.deepcopy(context); changed[key] = value
            with self.assertRaises(ValueError): related.validate_context(changed, focus, udid=NEW_UUID)
        for key, value in (("runtime_build", ""), ("runtime_version", "25.4.1"), ("state", "Shutdown"),
                           ("device_type", "com.apple.CoreSimulator.SimDeviceType.iPad-Pro")):
            changed = copy.deepcopy(context); changed["simulator"][key] = value
            with self.assertRaises(ValueError): related.validate_context(changed, focus, udid=NEW_UUID)

    def test_workflow_maps_only_two_literal_routes_before_first_inventory_and_keeps_old_boot_cleanup(self):
        name = ".github/workflows/gradle.yml"; raw = (ROOT / name).read_bytes(); text = raw.decode()
        marker = 'case "$TEST_FOCUS" in\n              ui-native-adaptive-pre26)'
        start = text.index(marker); inventory = text.index('--output build/ci-runtime/selection.json', start)
        block = text[start:inventory]
        self.assertIn('ui-native-adaptive-pre26) args+=(--adaptive-focus ui-native-adaptive-pre26) ;;', block)
        self.assertIn('ui-native-adaptive-drag-shader-ios26plus) args+=(--adaptive-focus ui-native-adaptive-ios26plus) ;;', block)
        self.assertEqual(2, block.count('--adaptive-focus'))
        self.assertNotIn('*)', block)
        parent = history.source_before_ui_related(name, raw).decode()
        for fragment in ('xcrun simctl boot "$device"', 'xcrun simctl bootstatus "$device" -b',
                         'args+=(--apple --simulator "$device" --require-booted)'):
            self.assertEqual(parent.count(fragment), text.count(fragment))
        self.assertEqual(history._document()["bindings"][name]["before_sha256"], history.sha(parent.encode()))
        for profile in PROFILES:
            self.assertEqual(1, text.split('options: [', 1)[1].split(']', 1)[0].count(profile))


if __name__ == "__main__":
    unittest.main()
