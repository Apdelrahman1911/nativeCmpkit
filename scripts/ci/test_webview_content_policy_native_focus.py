# SPDX-License-Identifier: Apache-2.0
"""NEW finite selector/source/XML models; no Gradle, providers or browser/fixture replay."""
import ast
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import time
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

import library_tests as r
import webview_content_policy_native_focus as policy
import workflow_matrix as matrix

ROOT = Path(__file__).resolve().parents[2]


def copy_model_checkout(root):
    """Ordinary source discovery fixture only; never built or launched."""
    (root / "settings.gradle.kts").write_text('include(\n    ":calf-webview",\n)\n')
    module = root / "calf-webview"; module.mkdir()
    (module / "build.gradle.kts").write_text("// Synthetic discovery only; never compiled\n")
    sources = set()
    for tree in ("calf-webview/src", "calf-webview/karma.config.d"):
        sources.update(path.relative_to(ROOT).as_posix() for path in r.source_files(ROOT, tree))
    sources.update((policy.SOURCE, policy.SPEC_RELATIVE, policy.IOS_FIXTURE))
    from webview_current_contract667_source_projection import contract_input_paths
    sources.update(contract_input_paths())
    for name in sources:
        target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())


def native_plan(root, focus):
    return r.plan(root, policy.spec(focus)["suite"], only_modules=(policy.MODULE,), focus=focus)


def xml_cases(focus):
    if focus in (policy.JS_FOCUS, policy.WASM_FOCUS):
        row = policy.spec(focus); task = row["task"].rsplit(":", 1)[1]
        target = "js" if focus == policy.JS_FOCUS else "wasmJs"
        return [{"classname": task + "." + row["classname"], "name": method + f"[{target}, browser, ChromeHeadlessModel]", "status": "passed"}
                for method in row["methods"]]
    return [{**case, "status": "passed"} for case in policy.identities(focus)]


class WebViewContentPolicyNativeFocusControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve(); copy_model_checkout(self.root)

    def test_five_literal_profiles_match_unchanged_author_classes_fourteen_methods_and_seventeen_new_targets(self):
        proposal = json.loads((ROOT / "docs/testing/webview-content-policy-focuses.json").read_text())
        self.assertEqual(list(policy.FOCUSES), [row["focus"] for row in proposal["profiles"]])
        self.assertEqual((4, 14, 17), (proposal["authored_classes"], proposal["authored_methods"], proposal["target_executions"]))
        for original in proposal["profiles"]:
            current = policy.spec(original["focus"])
            for key in ("profile", "focus", "slot", "suite", "task", "classname", "source"):
                self.assertEqual(original[key], current[key])
            self.assertEqual(original["methods"], list(current["methods"]))
            self.assertEqual(original["helpers"], list(current["helpers"]))
        self.assertEqual(18, sum(len(policy.identities(focus)) for focus in policy.FOCUSES))

    def test_each_matrix_profile_has_only_its_single_existing_host_module_and_identical_focus(self):
        for focus in policy.FOCUSES:
            row = policy.spec(focus)
            selected = matrix.matrix(focus)["include"]
            self.assertEqual(1, len(selected)); actual = selected[0]
            self.assertEqual((row["slot"], row["suite"], policy.MODULE, focus),
                             (actual["slot"], actual["suite"], actual["test-modules"], actual["test-focus"]))
            self.assertEqual((row["slot"],), matrix.PROFILES[focus])
            self.assertEqual(policy.MODULE, matrix.MODULE_SUBSETS[focus])
        workflow = (ROOT / ".github/workflows/gradle.yml").read_text()
        options = re.search(r"options: \[([^\n]+)\]", workflow).group(1).split(", ")
        for focus in policy.FOCUSES: self.assertEqual(1, options.count(focus))
        self.assertFalse(any("content-policy" in slot for slot in matrix.PROFILES["all"]))

    def test_plans_select_new_three_five_three_three_four_with_exact_task_report_and_current_source_contracts(self):
        for focus, count in zip(policy.FOCUSES, (3, 5, 3, 3, 4)):
            plan = native_plan(self.root, focus); item = plan["expected"][0]; row = policy.spec(focus)
            self.assertTrue(r.validate_test_focus(plan)); self.assertFalse(plan["complete_suite_requested"])
            self.assertEqual((row["task"], row["report_directory"], count, 1),
                             (item["task"], item["report_directory"], len(item["required_testcases"]), item["required_original_xml"]))
            self.assertEqual(policy.source_contract(self.root, focus), item[policy.CONTRACT_FIELD])
            self.assertEqual(policy.selector(focus), item["test_filter"])
            self.assertEqual(policy.identities(focus), item["required_testcases"])

    def test_normal_inheritance_keeps_accepted_native_classes_compiled_but_not_selected(self):
        for focus in policy.FOCUSES:
            row = policy.spec(focus); plan = native_plan(self.root, focus); item = plan["expected"][0]
            inherited = {path.relative_to(self.root).as_posix() for source_set in r.SUITES[row["suite"]][1]
                         for path in r.source_files(self.root, "calf-webview/src/" + source_set) if path.suffix in (".kt", ".java")}
            self.assertTrue(inherited <= set(item["test_source_files"]))
            required = {(case["classname"], case["name"]) for case in item["required_testcases"]}
            self.assertEqual(len(policy.identities(focus)), len(required))
            self.assertFalse(any("NativeWebViewApplicationHostTest" in classname for classname, _ in required))
            if focus == policy.ANDROID_FOCUS:
                affected = [case for case in item["required_testcases"] if case["classname"] == policy.ANDROID_AFFECTED_CLASS]
                self.assertEqual([{"classname": policy.ANDROID_AFFECTED_CLASS, "name": policy.ANDROID_AFFECTED_METHOD}], affected)

    def test_exact_suite_single_module_and_literal_focus_refuse_all_other_requests(self):
        for focus in policy.FOCUSES:
            row = policy.spec(focus)
            self.assertTrue(policy.allowed(row["suite"], (policy.MODULE,), focus))
            for modules in (None, (), (policy.MODULE, "calf-share"), ("calf-share",), (policy.MODULE, policy.MODULE)):
                self.assertFalse(policy.allowed(row["suite"], modules, focus))
                with self.assertRaises(ValueError): r.plan(self.root, row["suite"], only_modules=modules, focus=focus)
            for suite in set(r.SUITES) - {row["suite"]}:
                self.assertFalse(policy.allowed(suite, (policy.MODULE,), focus))
        for unknown in ("webview-content-policy-all", "ios-webview-content-policy-ipad", "*", None, [], True):
            self.assertFalse(policy.allowed("ios", (policy.MODULE,), unknown))
            with self.assertRaises(ValueError): policy.spec(unknown)

    def test_source_and_owner_manifest_drift_missing_symlink_and_hardlink_inputs_refuse_before_command(self):
        for focus in policy.FOCUSES:
            path = self.root / policy.spec(focus)["source"]; original = path.read_bytes()
            path.write_bytes(original + b"\n")
            with self.assertRaises(ValueError): native_plan(self.root, focus)
            path.write_bytes(original)
        name = policy.ANDROID_FILTER_SOURCE; path = self.root / name; original = path.read_bytes()
        path.unlink()
        with self.assertRaises(FileNotFoundError): native_plan(self.root, policy.ANDROID_FOCUS)
        path.symlink_to(ROOT / name)
        with self.assertRaises(ValueError): native_plan(self.root, policy.ANDROID_FOCUS)
        path.unlink(); backing = path.with_name("filter-backing.kt"); backing.write_bytes(original); path.hardlink_to(backing)
        with self.assertRaises(ValueError): native_plan(self.root, policy.ANDROID_FOCUS)
        path.unlink(); backing.unlink(); path.write_bytes(original)
        owner = self.root / policy.SOURCE; raw = owner.read_bytes(); owner.write_bytes(raw + b"\n")
        with self.assertRaises(ValueError): native_plan(self.root, policy.JS_FOCUS)
        owner.write_bytes(raw)

    def test_strict_plan_metadata_refuses_omissions_extra_methods_filters_foreign_tasks_and_boolean_counts(self):
        for focus in policy.FOCUSES:
            plan = native_plan(self.root, focus)
            def variants():
                for key, value in (("test_filter", "*"), ("task", ":calf-share:desktopTest"),
                                   ("report_directory", "calf-webview/build/foreign"), ("required_original_xml", True),
                                   ("required_testcases", plan["expected"][0]["required_testcases"][:-1]),
                                   ("test_exclusion_annotation", "unreviewed.Ignore")):
                    bad = copy.deepcopy(plan); bad["expected"][0][key] = value; yield bad
                for key, value in (("schema_version", True), ("new_methods", True), ("native_executions_attested", False)):
                    bad = copy.deepcopy(plan); bad["expected"][0][policy.CONTRACT_FIELD][key] = value; yield bad
                bad = copy.deepcopy(plan); bad["explicit_module_subset"].append("calf-ui"); yield bad
                bad = copy.deepcopy(plan); bad["expected"][0]["test_source_files"].remove(policy.SOURCE); yield bad
            for bad in variants():
                with self.assertRaises(ValueError): r.validate_test_focus(bad)

    def test_android_filter_is_one_public_noarg_zero_test_exact_five_leaf_identity_tree(self):
        source = (ROOT / policy.ANDROID_FILTER_SOURCE).read_text()
        self.assertIn("class AndroidContentPolicyVerificationFilter : Filter()", source)
        self.assertIn("if (!description.isTest) return description.children.any { shouldRun(it) }", source)
        self.assertNotRegex(source, r"@(Test|Ignore|Disabled)|Bundle|InstrumentationRegistry|Regex|System\\.")
        quoted = re.findall(r'"([^"]+)"', source)
        native_methods = [value for value in quoted if value in policy.spec(policy.ANDROID_FOCUS)["methods"] or value == policy.ANDROID_AFFECTED_METHOD]
        self.assertEqual([*policy.spec(policy.ANDROID_FOCUS)["methods"], policy.ANDROID_AFFECTED_METHOD], native_methods)
        leaves = {(policy.spec(policy.ANDROID_FOCUS)["classname"], name) for name in native_methods[:-1]}
        leaves.add((policy.ANDROID_AFFECTED_CLASS, native_methods[-1]))
        self.assertEqual({(case["classname"], case["name"]) for case in policy.identities(policy.ANDROID_FOCUS)}, leaves)
        for leaf in ((policy.ANDROID_AFFECTED_CLASS, "compositionDisposalClosesItsRealSlowConnectionAndStopsTheLiveMediaDocument"),
                     (policy.spec(policy.ANDROID_FOCUS)["classname"], "unreviewed"), (None, None), ("foreign", native_methods[0])):
            self.assertNotIn(leaf, leaves)
        self.assertEqual(2, source.count("else -> false"))

    def test_android_single_filter_argument_roundtrips_lossless_without_comma_class_or_annotation_transport(self):
        plan = native_plan(self.root, policy.ANDROID_FOCUS)
        command = r.gradle_command("android-device", plan, root=self.root, android_serial="emulator-5588")
        prefix = "-Pandroid.testInstrumentationRunnerArguments."
        arguments = dict(argument[len(prefix):].split("=", 1) for argument in command if argument.startswith(prefix))
        self.assertEqual(policy.ANDROID_FILTER_CLASS, arguments["filter"])
        self.assertNotIn("class", arguments); self.assertNotIn("annotation", arguments); self.assertNotIn("notClass", arguments)
        encoded = ",".join(key + "=" + value for key, value in arguments.items())
        decoded = dict(token.split("=", 1) for token in encoded.split(",") if "=" in token)
        self.assertEqual(arguments, decoded); self.assertNotIn("--tests", command)
        self.assertEqual(1, command.count(policy.spec(policy.ANDROID_FOCUS)["task"]))
        self.assertIn("-PnativecmpkitAndroidDeviceSerial=emulator-5588", command)
        assembly = r.gradle_command("android-device", plan, root=self.root, android_serial="emulator-5588", for_assembly=True)
        self.assertIn(":calf-webview:assembleAndroidDeviceTest", assembly)
        self.assertNotIn(policy.spec(policy.ANDROID_FOCUS)["task"], assembly)

    def test_android_controller_requires_api35_and_only_the_finite_webview_module(self):
        import android_device_tests as controller
        controller.validate_api_selection(35, (policy.MODULE,), policy.ANDROID_FOCUS)
        for api, modules in ((23, (policy.MODULE,)), (34, (policy.MODULE,)), (36, (policy.MODULE,)), (True, (policy.MODULE,)), (35, None), (35, ("calf-ui",))):
            with self.assertRaises(ValueError): controller.validate_api_selection(api, modules, policy.ANDROID_FOCUS)
        source = (ROOT / "scripts/ci/android_device_tests.py").read_text()
        self.assertIn('choices=[lt.content_policy.ANDROID_FOCUS,', source)

    def test_each_new_command_revalidates_current_source_hashes_and_never_selects_another_target(self):
        for focus in policy.FOCUSES:
            row = policy.spec(focus); plan = native_plan(self.root, focus)
            kwargs = {"root": self.root}
            if focus == policy.IOS_FOCUS: kwargs["simulator"] = "11111111-2222-3333-4444-555555555555"
            if focus == policy.ANDROID_FOCUS: kwargs["android_serial"] = "emulator-5588"
            command = r.gradle_command(row["suite"], plan, **kwargs)
            self.assertEqual(1, command.count(row["task"]))
            selected = [command[i + 1] for i, value in enumerate(command[:-1]) if value == "--tests"]
            self.assertEqual(policy.selector(focus).split(",") if focus == policy.IOS_FOCUS else
                             [] if focus == policy.ANDROID_FOCUS else [policy.selector(focus)], selected)
            native = self.root / row["source"]; raw = native.read_bytes(); native.write_bytes(raw + b"\n")
            with self.assertRaises(ValueError): r.gradle_command(row["suite"], plan, **kwargs)
            native.write_bytes(raw)

    def test_browser_backend_class_and_actual_kotlin_target_suffix_are_independently_exact(self):
        for focus in (policy.JS_FOCUS, policy.WASM_FOCUS):
            cases = xml_cases(focus); self.assertTrue(policy.case_inventory(focus, cases))
            other = policy.WASM_FOCUS if focus == policy.JS_FOCUS else policy.JS_FOCUS
            self.assertFalse(policy.case_inventory(other, cases))
            for bad in (cases[:-1], cases + [cases[0]], [{**cases[0], "classname": policy.spec(focus)["classname"]}, *cases[1:]],
                        [{**cases[0], "name": cases[0]["name"].replace(", browser,", ", nodejs,")}, *cases[1:]],
                        [{**cases[0], "name": "*"}, *cases[1:]], [{**cases[0], "name": None}, *cases[1:]]):
                self.assertFalse(policy.case_inventory(focus, bad))

    def test_desktop_and_native_inventory_refuse_missing_duplicate_unsuffixed_and_foreign_cases(self):
        for focus in (policy.DESKTOP_FOCUS, policy.ANDROID_FOCUS, policy.IOS_FOCUS):
            cases = xml_cases(focus); self.assertTrue(policy.case_inventory(focus, cases))
            for bad in (cases[:-1], cases + [cases[0]], [cases[0], cases[0], *cases[2:]],
                        [{**cases[0], "classname": "foreign"}, *cases[1:]],
                        [{**cases[0], "name": cases[0]["name"].replace("[desktop]", "").replace("[iosSimulatorArm64]", "") + "unreviewed"}, *cases[1:]],
                        [{**cases[0], "classname": []}, *cases[1:]]):
                self.assertFalse(policy.case_inventory(focus, bad))

    def test_desktop_command_and_acceptance_reject_all_non_linux_x64_hosts(self):
        policy.validate_host(policy.DESKTOP_FOCUS, "Linux", "x86_64")
        for system, arch in (("Darwin", "arm64"), ("Windows", "amd64"), ("Linux", "arm64"), ("Linux", "unknown")):
            with self.assertRaises(ValueError): policy.validate_host(policy.DESKTOP_FOCUS, system, arch)
        plan = native_plan(self.root, policy.DESKTOP_FOCUS)
        with patch.object(r.platform, "system", return_value="Darwin"), patch.object(r.platform, "machine", return_value="arm64"):
            with self.assertRaises(ValueError): r.gradle_command("desktop", plan, root=self.root)

    def test_each_xml_gate_requires_one_fresh_original_exact_target_report_and_preserves_actual_status(self):
        for focus in policy.FOCUSES:
            plan = native_plan(self.root, focus); item = plan["expected"][0]
            folder = self.root / item["report_directory"]; folder.mkdir(parents=True, exist_ok=True)
            report = folder / "TEST-content-policy-model.xml"
            def write(cases, failed=False):
                suite = ET.Element("testsuite", tests=str(len(cases)))
                for index, case in enumerate(cases):
                    native = ET.SubElement(suite, "testcase", classname=case["classname"], name=case["name"])
                    if failed and index == 0: ET.SubElement(native, "failure")
                report.write_bytes(ET.tostring(suite))
            def collect():
                now = time.time_ns()
                return r.collect_reports(self.root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                         Counter({item["task"]: 1}), host_system="Darwin" if focus == policy.IOS_FOCUS else "Linux")
            cases = xml_cases(focus); write(cases); accepted = collect()
            self.assertEqual([], accepted["errors"])
            self.assertEqual(len(cases), accepted["totals"]["passed"])
            write(cases, failed=True); failed = collect()
            self.assertEqual(1, failed["totals"]["failures"]); self.assertTrue(failed["errors"])
            write(cases[:-1]); self.assertTrue(collect()["errors"])
            write(cases); extra = folder / "TEST-extra-model.xml"; extra.write_text('<testsuite tests="0"/>')
            self.assertTrue(collect()["errors"]); extra.unlink(); report.unlink()

    def test_unfocused_and_other_finite_plans_cannot_carry_a_content_fixture_or_filter_contract(self):
        plan = r.plan(self.root, "ios", only_modules=(policy.MODULE,))
        self.assertNotIn("explicit_test_focus", plan)
        self.assertNotIn("test_filter", plan["expected"][0])
        self.assertFalse(r.validate_test_focus(plan))
        plan["expected"][0][policy.CONTRACT_FIELD] = policy.source_contract(self.root, policy.IOS_FOCUS)
        with self.assertRaises(ValueError): r.validate_test_focus(plan)
        for focus in policy.FOCUSES:
            self.assertNotIn("accepted", policy.selector(focus).lower())
            self.assertIn("No unchanged replay", policy.scope(focus))

    def test_cli_only_exposes_literal_five_focus_constants_and_no_new_general_dispatch_alias(self):
        tree = ast.parse((ROOT / "scripts/ci/library_tests.py").read_text())
        parser = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        focus_call = next(node for node in ast.walk(parser) if isinstance(node, ast.Call) and node.args and
                          isinstance(node.args[0], ast.Constant) and node.args[0].value == "--focus")
        self.assertIn("content_policy.FOCUSES", ast.unparse(focus_call))
        self.assertNotIn("content-policy-all", (ROOT / "scripts/ci/workflow_matrix.py").read_text())
        self.assertEqual(0, sum(bool(re.search(r"@(?:Ignore|Disabled|IgnoredTest)\\b", (ROOT / policy.spec(focus)["source"]).read_text()))
                                for focus in policy.FOCUSES))

    def test_existing_unrelated_secure_and_desktop_fixture_guards_precede_content_focus_return(self):
        # NEW negative model: exact content admission cannot bypass older fixture refusals.
        for focus in policy.FOCUSES:
            plan = native_plan(self.root, focus)
            for field, message in (("secure_alert_input_contract", "No secure-input source fixture"),
                                   ("desktop_security_fixture", "No security-only trust/isolation fixture")):
                leaked = copy.deepcopy(plan)
                if field == "secure_alert_input_contract": leaked["expected"][0][field] = {"unrelated": True}
                else: leaked[field] = {"unrelated": True}
                with self.subTest(focus=focus, field=field), self.assertRaisesRegex(ValueError, message):
                    r.validate_test_focus(leaked)

    def test_existing_share630_fixture_guard_precedes_content_focus_return(self):
        # NEW exact ecff composition negative; the old Share630 lease is unrelated.
        for focus in policy.FOCUSES:
            leaked = native_plan(self.root, focus)
            leaked["expected"][0][r.share_missing.CONTRACT_KEY] = {"unrelated": True}
            with self.subTest(focus=focus), self.assertRaisesRegex(ValueError, "No Share630 recovery source fixture"):
                r.validate_test_focus(leaked)
