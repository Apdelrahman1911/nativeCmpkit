"""Finite actual-engine identity/value batch guards; synthetic tooling, not library executions."""
from collections import Counter
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

import library_tests as lt
import workflow_matrix as matrix


class WebViewIdentityFocusTests(unittest.TestCase):
    SUITES = ("desktop", "android-device", "js", "wasm")

    def plan(self, suite="desktop", root=lt.ROOT):
        return lt.plan(root, suite, only_modules=("calf-webview",), focus=lt.WEBVIEW_IDENTITY_FOCUS)

    def identities(self, suite):
        cases = copy.deepcopy(lt.webview_identity_identities(suite))
        if suite in {"js", "wasm"}:
            target = "js" if suite == "js" else "wasmJs"
            for case in cases:
                case["classname"] = lt.SUITES[suite][0] + "." + case["classname"]
                case["name"] += "[" + target + ", browser, ChromeHeadless synthetic-tooling]"
        return cases

    def collect(self, suite="desktop", cases=None, outcome="", markers=1, stale=False, duplicate=False):
        plan = self.plan(suite)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected, = plan["expected"]
            folder = root / selected["report_directory"]
            folder.mkdir(parents=True)
            xml = ET.Element("testsuite")
            for case in self.identities(suite) if cases is None else cases:
                node = ET.SubElement(xml, "testcase", **case)
                if outcome: ET.SubElement(node, outcome)
            path = folder / "TEST-explicitly-synthetic.xml"
            path.write_bytes(ET.tostring(xml))
            if duplicate: (folder / "TEST-duplicate.xml").write_bytes(path.read_bytes())
            now = time.time_ns()
            if stale: os.utime(path, ns=(now - 20_000_000_000, now - 20_000_000_000))
            return lt.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                      Counter({selected["task"]: markers}), host_system="Linux")

    def source_root(self, directory, suite):
        root = Path(directory).resolve()
        (root / "settings.gradle.kts").write_text('include(\n    ":calf-webview",\n)\n')
        build = root / "calf-webview/build.gradle.kts"
        build.parent.mkdir()
        build.write_text("// Explicit synthetic model, never executed\n")
        source = lt.WEBVIEW_IDENTITY_SPECS[suite]["source"]
        path = root / source
        path.parent.mkdir(parents=True)
        path.write_bytes((lt.ROOT / source).read_bytes())
        if suite == "android-device":
            for relative in lt.WEBVIEW_DEVICE_FIXTURES:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((lt.ROOT / relative).read_bytes())
        return root

    def test_related_identity_batch_has_all_four_engine_targets_without_replaying_unrelated_tests(self):
        self.assertIn("webview-identity", matrix.PROFILES,
                      "Missing cross-platform public WebView creation/state/callback/value verification")
        rows = matrix.matrix("webview-identity")["include"]
        self.assertEqual({"desktop-linux-x64", "browser-js", "browser-wasm", "android-device-api35"},
                         {row["slot"] for row in rows})
        self.assertTrue(all(row["test-modules"] == "calf-webview" and
                            row["test-focus"] == lt.WEBVIEW_IDENTITY_FOCUS for row in rows))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        self.assertEqual(9, sum(len(self.plan(row["suite"])["expected"][0]["required_testcases"]) for row in rows))

    def test_bounded_recovery_profiles_select_only_their_unaccepted_platform_results(self):
        for profile, slots in (("linux", ["desktop-linux-x64"]), ("browser", ["browser-js", "browser-wasm"]),
                               ("wasm", ["browser-wasm"]), ("android", ["android-device-api35"])):
            self.assertEqual(slots, [r["slot"] for r in matrix.matrix("webview-identity-" + profile)["include"]])
        for profile in ("all", "core", "browser", "android-device", "webview-desktop"):
            self.assertTrue(all("test-focus" not in row for row in matrix.matrix(profile)["include"]))

    def test_exact_class_filter_uses_lossless_native_browser_and_android_transports(self):
        for suite in self.SUITES:
            plan = self.plan(suite)
            selected, = plan["expected"]
            self.assertFalse(plan["complete_suite_requested"])
            self.assertEqual(":calf-webview:" + lt.SUITES[suite][0], selected["task"])
            self.assertEqual(lt.WEBVIEW_IDENTITY_SPECS[suite]["classname"], selected["test_filter"])
            command = lt.gradle_command(suite, plan, android_serial="emulator-5588" if suite == "android-device" else None)
            if suite == "android-device":
                selectors = [v for v in command if v.startswith("-Pandroid.testInstrumentationRunnerArguments.class=")]
                self.assertEqual(["-Pandroid.testInstrumentationRunnerArguments.class=" + selected["test_filter"]], selectors)
                self.assertNotIn(",", selectors[0])
                self.assertNotIn("--tests", command)
            else:
                self.assertEqual(1, command.count("--tests"))
                self.assertEqual(selected["test_filter"], command[command.index("--tests") + 1])
            self.assertNotIn("publish", " ".join(command))

    def test_real_cli_plans_each_exact_suite_and_rejects_an_unreviewed_focus(self):
        for suite in self.SUITES:
            args = ["library_tests.py", "plan", "--suite", suite, "--module", "calf-webview", "--focus", lt.WEBVIEW_IDENTITY_FOCUS]
            stream = io.StringIO()
            with patch("sys.argv", args), patch("sys.stdout", stream): self.assertEqual(0, lt.main())
            self.assertEqual(self.plan(suite), json.loads(stream.getvalue()))
        with patch("sys.argv", args[:-1] + ["unreviewed-wildcard"]), patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit):
            lt.main()

    def test_wrong_suite_module_filter_inventory_source_task_or_full_suite_claim_is_rejected(self):
        for suite, modules in (("ios", ("calf-webview",)), ("android-host", ("calf-webview",)),
                               ("desktop", ("calf-ui",)), ("desktop", None), ("js", ("calf-io",))):
            with self.assertRaises(ValueError): lt.plan(lt.ROOT, suite, only_modules=modules, focus=lt.WEBVIEW_IDENTITY_FOCUS)
        for suite in self.SUITES:
            for key, value in (("module", "calf-io"), ("task", ":calf-webview:publish"), ("test_filter", "*"),
                               ("required_testcases", []), ("test_source_files", [])):
                plan = self.plan(suite); plan["expected"][0][key] = value
                with self.assertRaises(ValueError): lt.validate_test_focus(plan)
            plan = self.plan(suite); plan["complete_suite_requested"] = True
            with self.assertRaises(ValueError): lt.validate_test_focus(plan)

    def test_actual_target_identities_have_exact_fresh_nonzero_xml(self):
        for suite, count in (("desktop", 3), ("android-device", 2), ("js", 2), ("wasm", 2)):
            result = self.collect(suite)
            self.assertEqual([], result["errors"], result["errors"])
            self.assertEqual(count, result["totals"]["passed"])
            self.assertEqual(count, len(result["modules"][0]["native_scenarios"]))

    def test_empty_missing_extra_duplicate_foreign_class_and_wrong_target_xml_is_rejected(self):
        for suite in self.SUITES:
            cases = self.identities(suite)
            variants = [[], cases[:-1], cases * 2, cases + [{**cases[0], "name": "unrelated"}]]
            for key, value in (("classname", "Foreign.AcceptanceTest"), ("name", "unrelated"),
                               ("name", cases[0]["name"] + "[foreign]")):
                changed = copy.deepcopy(cases); changed[0][key] = value; variants.append(changed)
            if suite in {"js", "wasm"}:
                for key, value in (("classname", lt.WEBVIEW_IDENTITY_SPECS[suite]["classname"]),
                                   ("name", lt.WEBVIEW_IDENTITY_SPECS[suite]["methods"][0] + "[desktop]")):
                    changed = copy.deepcopy(cases); changed[0][key] = value; variants.append(changed)
            for changed in variants:
                with self.subTest(suite=suite, cases=changed): self.assertTrue(self.collect(suite, cases=changed)["errors"])

    def test_failed_errored_skipped_stale_xml_and_absent_or_duplicate_task_execution_is_red(self):
        for suite in self.SUITES:
            for changed in ({"outcome": "failure"}, {"outcome": "error"}, {"outcome": "skipped"},
                            {"stale": True}, {"duplicate": True}, {"markers": 0}, {"markers": 2}):
                with self.subTest(suite=suite, changed=changed): self.assertTrue(self.collect(suite, **changed)["errors"])

    def test_valid_source_calibration_precedes_missing_renamed_ignored_or_extra_method_rejection(self):
        for suite in self.SUITES:
            with tempfile.TemporaryDirectory() as directory:
                root = self.source_root(directory, suite)
                self.assertTrue(lt.validate_test_focus(self.plan(suite, root)))
                spec = lt.WEBVIEW_IDENTITY_SPECS[suite]; path = root / spec["source"]; original = path.read_text()
                for changed in (original.replace(spec["methods"][0], "wrongMethod", 1),
                                original.replace("@Test", "@IgnoredTest", 1),
                                original.replace("@Test", "@Ignore @Test", 1), original + "\n@Test fun extra() {}\n"):
                    path.write_text(changed)
                    with self.assertRaises(ValueError): self.plan(suite, root)
                path.write_text(original)
                self.assertTrue(lt.validate_test_focus(self.plan(suite, root)))
                path.unlink()
                with self.assertRaises(ValueError): self.plan(suite, root)

    def test_owning_methods_use_real_public_composition_documents_values_and_cleanup_not_samples_or_fakes(self):
        for suite in self.SUITES:
            source = (lt.ROOT / lt.WEBVIEW_IDENTITY_SPECS[suite]["source"]).read_text()
            for required in ("WebView(", "onCreated", "onDispose", "document.title", "evaluateJavascriptResult",
                             "JavascriptResult.Undefined", "owned-script-error", "must-not-load", "mounted"):
                self.assertIn(required, source)
            for forbidden in ("@Ignore", "assumeTrue(", "assumeFalse(", "override fun evaluateJavaScript"):
                self.assertNotIn(forbidden, source)
            self.assertNotRegex(source, r"(?m)^import\s+[^\n]*\bsample\.")
        desktop = (lt.ROOT / lt.WEBVIEW_IDENTITY_SPECS["desktop"]["source"]).read_text()
        self.assertIn("entered.await", desktop)
        self.assertIn("release.countDown()", desktop)
        self.assertIn("finally { scope.cancel() }", desktop)
        self.assertIn("Thread.currentThread().uncaughtExceptionHandler = previous", desktop)
        android = (lt.ROOT / lt.WEBVIEW_IDENTITY_SPECS["android-device"]["source"]).read_text()
        self.assertEqual(2, android.count("compose.setContent"), "Exactly one composition per owning method")
        browser = (lt.ROOT / lt.WEBVIEW_IDENTITY_SPECS["js"]["source"]).read_text()
        self.assertIn("BrowserSandboxPolicy.Trusted", browser)
        self.assertIn("composeWindow.dispose()", browser)
        self.assertIn("finally { viewport.close() }", browser)

    def test_workflow_keeps_readonly_permissions_and_evidence_only_no_new_artifact_publication(self):
        workflow = (lt.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("max-parallel: 2", workflow)
        self.assertIn("persist-credentials: false", workflow)
        upload = workflow.split("- name: Keep receipts and actual selected-task XML", 1)[1].split("\n  consumer-core-io:", 1)[0]
        for forbidden in ("*.jar", "*.aar", "*.apk", "*.kexe", "*.app", "*.hprof"):
            self.assertNotIn(forbidden, upload)


if __name__ == "__main__": unittest.main()
