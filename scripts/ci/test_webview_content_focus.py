"""Finite #63 iframe selection guards; synthetic tooling, not browser acceptance."""
from collections import Counter
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unittest
from xml.etree import ElementTree as ET

import library_tests as lt
import workflow_matrix as matrix


FOCUS = "webview-browser-content-transitions"
PROFILE = "webview-content-transitions"
CLASS = "com.mohamedrejeb.calf.ui.web.BrowserWebViewContentAcceptanceTest"
SOURCE = "calf-webview/src/webTest/kotlin/com/mohamedrejeb/calf/ui/web/BrowserWebViewContentAcceptanceTest.kt"
FIXTURE = "calf-webview/karma.config.d/nativecmpkit-iframe-fixture.js"
METHODS = (
    "directAndRememberedContentTransitionsMatchNavigatorAttributesAndDocuments",
    "realCrossOriginCspAndFrameOptionsRefusalsCannotRetainOrReportTheOldDocument",
)


class WebViewContentFocusTests(unittest.TestCase):
    def plan(self, suite="js", root=lt.ROOT):
        return lt.plan(root, suite, only_modules=("calf-webview",), focus=FOCUS)

    def identities(self, suite):
        target = "js" if suite == "js" else "wasmJs"
        return [{"classname": lt.SUITES[suite][0] + "." + CLASS,
                 "name": method + "[" + target + ", browser, ChromeHeadless synthetic-tooling]"}
                for method in METHODS]

    def source_root(self, directory):
        root = Path(directory).resolve()
        (root / "settings.gradle.kts").write_text('include(\n    ":calf-webview",\n)\n')
        build = root / "calf-webview/build.gradle.kts"
        build.parent.mkdir()
        build.write_text("// Synthetic discovery model, never built\n")
        for relative in (SOURCE, FIXTURE):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((lt.ROOT / relative).read_bytes())
        return root

    def collect(self, suite, cases=None, outcome="", markers=1, stale=False, duplicate=False):
        plan = self.plan(suite)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected, = plan["expected"]
            folder = root / selected["report_directory"]
            folder.mkdir(parents=True)
            xml = ET.Element("testsuite")
            for case in self.identities(suite) if cases is None else cases:
                node = ET.SubElement(xml, "testcase", **case)
                if outcome:
                    ET.SubElement(node, outcome)
            path = folder / "TEST-explicitly-synthetic.xml"
            path.write_bytes(ET.tostring(xml))
            if duplicate:
                (folder / "TEST-duplicate.xml").write_bytes(path.read_bytes())
            now = time.time_ns()
            if stale:
                os.utime(path, ns=(now - 20_000_000_000, now - 20_000_000_000))
            return lt.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                      Counter({selected["task"]: markers}), host_system="Linux")

    def test_finite_profile_has_only_two_browser_targets_and_keeps_full_and_android_inventories(self):
        self.assertIn(PROFILE, matrix.PROFILES)
        rows = matrix.matrix(PROFILE)["include"]
        self.assertEqual(["browser-js", "browser-wasm"], [row["slot"] for row in rows])
        self.assertTrue(all(row["test-modules"] == "calf-webview" and row["test-focus"] == FOCUS for row in rows))
        self.assertEqual(4, sum(len(self.plan(row["suite"])["expected"][0]["required_testcases"]) for row in rows))
        self.assertEqual({"desktop-linux-x64", "android-host", "browser-js", "browser-wasm",
                          "desktop-macos-arm64", "ios-iphone", "desktop-windows-x64", "desktop-linux-arm64",
                          "desktop-macos-x64", "ios-ipad", "android-device-api35"},
                         {row["slot"] for row in matrix.matrix("all")["include"]})
        self.assertEqual(("calf-io", "calf-file-picker", "calf-geo", "calf-webview", "calf-ui",
                          "calf-navigation", "calf-share", "calf-camera-picker"), lt.MINIMUM_MODULES["android-device"])
        for profile in ("all", "browser", "webview-browser", "webview-wasm", "core", "android-device"):
            self.assertTrue(all("test-focus" not in row for row in matrix.matrix(profile)["include"]))

    def test_exact_two_method_plan_holds_owned_http_fixture_and_uses_existing_gradle_filter_transport(self):
        for suite in ("js", "wasm"):
            plan = self.plan(suite)
            selected, = plan["expected"]
            self.assertTrue(lt.validate_test_focus(plan))
            self.assertFalse(plan["complete_suite_requested"])
            self.assertEqual(":calf-webview:" + lt.SUITES[suite][0], selected["task"])
            self.assertEqual(CLASS, selected["test_filter"])
            self.assertEqual([{"classname": CLASS, "name": method} for method in METHODS], selected["required_testcases"])
            self.assertEqual(FIXTURE, selected["browser_http_fixture"])
            self.assertIn(SOURCE, selected["test_source_files"])
            command = lt.gradle_command(suite, plan)
            self.assertEqual(1, command.count("--tests"))
            self.assertEqual(CLASS, command[command.index("--tests") + 1])
            self.assertNotIn("publish", " ".join(command))

    def test_real_readonly_cli_accepts_only_exact_browser_suite_module_and_focus(self):
        for suite in ("js", "wasm"):
            command = [sys.executable, "-B", str(lt.ROOT / "scripts/ci/library_tests.py"), "plan",
                       "--suite", suite, "--module", "calf-webview", "--focus", FOCUS]
            result = subprocess.run(command, cwd=lt.ROOT, capture_output=True, text=True, timeout=30)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(self.plan(suite), json.loads(result.stdout))
        result = subprocess.run(command[:-1] + ["unreviewed-wildcard"], cwd=lt.ROOT,
                                capture_output=True, text=True, timeout=30)
        self.assertNotEqual(0, result.returncode)

    def test_wrong_suite_module_filter_task_inventory_source_fixture_and_full_claim_are_rejected(self):
        for suite, modules in (("ios", ("calf-webview",)), ("desktop", ("calf-webview",)),
                               ("android-host", ("calf-webview",)), ("android-device", ("calf-webview",)),
                               ("js", None), ("wasm", ("calf-io",)), ("js", ("calf-webview", "calf-ui"))):
            with self.assertRaises(ValueError):
                lt.plan(lt.ROOT, suite, only_modules=modules, focus=FOCUS)
        for suite in ("js", "wasm"):
            for key, value in (("module", "calf-ui"), ("task", ":calf-webview:publish"), ("test_filter", "*"),
                               ("required_testcases", []), ("test_source_files", []), ("browser_http_fixture", "foreign.js")):
                plan = self.plan(suite)
                plan["expected"][0][key] = value
                with self.assertRaises(ValueError):
                    lt.validate_test_focus(plan)
            plan = self.plan(suite)
            plan["complete_suite_requested"] = True
            with self.assertRaises(ValueError):
                lt.validate_test_focus(plan)

    def test_exact_native_target_class_and_name_inventories_have_fresh_nonzero_synthetic_xml(self):
        for suite in ("js", "wasm"):
            result = self.collect(suite)
            self.assertEqual([], result["errors"], result["errors"])
            self.assertEqual(2, result["totals"]["passed"])
            self.assertEqual(2, len(result["modules"][0]["native_scenarios"]))
            self.assertTrue(all(c["source"] == SOURCE for c in result["modules"][0]["native_scenarios"]))

    def test_missing_extra_duplicate_foreign_class_and_wrong_target_xml_cannot_be_laundered(self):
        for suite in ("js", "wasm"):
            cases = self.identities(suite)
            variants = [[], cases[:-1], cases * 2, cases + [{**cases[0], "name": "unrelated"}]]
            for key, value in (("classname", "Foreign.AcceptanceTest"), ("classname", CLASS),
                               ("name", "unrelated"), ("name", METHODS[0] + "[desktop]"),
                               ("name", METHODS[0] + "[wasmJs" if suite == "js" else METHODS[0] + "[js")):
                changed = copy.deepcopy(cases)
                changed[0][key] = value
                variants.append(changed)
            other = self.identities("wasm" if suite == "js" else "js")
            variants.append(other)
            for changed in variants:
                with self.subTest(suite=suite, cases=changed):
                    self.assertTrue(self.collect(suite, cases=changed)["errors"])

    def test_failed_skipped_errored_stale_duplicate_reports_and_wrong_markers_stay_red(self):
        for suite in ("js", "wasm"):
            for changed in ({"outcome": "failure"}, {"outcome": "error"}, {"outcome": "skipped"},
                            {"stale": True}, {"duplicate": True}, {"markers": 0}, {"markers": 2}):
                with self.subTest(suite=suite, changed=changed):
                    self.assertTrue(self.collect(suite, **changed)["errors"])

    def test_valid_source_precedes_missing_renamed_extra_or_ignored_declaration_refusal(self):
        for suite in ("js", "wasm"):
            with tempfile.TemporaryDirectory() as directory:
                root = self.source_root(directory)
                self.assertTrue(lt.validate_test_focus(self.plan(suite, root)))
                path = root / SOURCE
                original = path.read_text()
                for changed in (original.replace(METHODS[0], "wrongMethod", 1), original + "\n@Test fun extra() {}\n",
                                original.replace("@Test", "@Ignore @Test", 1),
                                original.replace("@Test", "@IgnoredTest", 1)):
                    path.write_text(changed)
                    with self.assertRaises(ValueError):
                        self.plan(suite, root)
                path.write_text(original)
                self.assertTrue(lt.validate_test_focus(self.plan(suite, root)))
                path.unlink()
                with self.assertRaises(ValueError):
                    self.plan(suite, root)

    def test_owned_karma_fixture_is_required_confined_and_hashed_as_an_actual_build_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.source_root(directory)
            self.assertTrue(lt.validate_test_focus(self.plan("js", root)))
            before = lt.snapshot_inputs(root)
            self.assertIn(FIXTURE, before)
            path = root / FIXTURE
            path.write_text(path.read_text() + "\n// Explicit synthetic mutation\n")
            after = lt.snapshot_inputs(root)
            self.assertNotEqual(before[FIXTURE], after[FIXTURE])
            self.assertNotEqual(lt.input_digest(before), lt.input_digest(after))
            path.unlink()
            with self.assertRaises(ValueError):
                self.plan("js", root)
            path.symlink_to(root / SOURCE)
            with self.assertRaises(ValueError):
                self.plan("wasm", root)
            with self.assertRaises(ValueError):
                lt.snapshot_inputs(root)

    def test_owning_methods_use_real_public_dom_loads_headers_messages_and_preserved_cleanup(self):
        source = (lt.ROOT / SOURCE).read_text()
        for required in ("ComposeViewport", "WebView(", "rememberWebViewState(", "rememberWebViewStateWithHTMLData(",
                         "owner.content = WebContent.Data", "owner.content = WebContent.Url", "navigator.loadUrl",
                         "navigator.loadHtml", "snapshot(frame)", "frame.attributes", "native.contentDocument == null",
                         "contentDocument?.title", "owner.pageTitle",
                         "owner.lastLoadedUrl", "event.isTrusted", "message.isTrusted", "message.source", "message.origin",
                         "fixture.receipt()", "NonCancellable", "error.addSuppressed(cleanup)", "composeWindow.dispose()"):
            self.assertIn(required, source)
        for forbidden in ("dispatchEvent(", "@Ignore", "assumeTrue(", "assumeFalse(", "BrowserWebViewOwner("):
            self.assertNotIn(forbidden, source)
        self.assertNotRegex(source, r"(?m)^import\s+[^\n]*\bsample\.")
        fixture = (lt.ROOT / FIXTURE).read_text()
        for required in ("sessions.size >= 64", "request.method !== 'GET'", "'no-store'",
                         "'Content-Security-Policy'", "frame-ancestors 'none'", "'X-Frame-Options'", "'DENY'",
                         "response.getHeader(", "sessions.delete(token)", "middleware:nativecmpkit-iframe-fixture"):
            self.assertIn(required, fixture)
        for forbidden in ("require(", "child_process", "fetch(", "https://", "file://"):
            self.assertNotIn(forbidden, fixture)

    def test_workflow_serializes_only_new_profile_and_retains_readonly_evidence_boundaries(self):
        workflow = (lt.ROOT / ".github/workflows/gradle.yml").read_text()
        options = re.search(r"options: \[([^\n]+)\]", workflow).group(1)
        self.assertIn(PROFILE, {option.strip() for option in options.split(",")})
        library_job = workflow.split("\n  library-tests:\n", 1)[1].split("\n  consumer-core-io:\n", 1)[0]
        self.assertIn("|| inputs.profile == 'webview-content-transitions') && 1 || 2 }}", library_job)
        self.assertIn("fail-fast: false", library_job)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("persist-credentials: false", library_job)
        upload = library_job.split("- name: Keep receipts and actual selected-task XML", 1)[1]
        for forbidden in ("*.jar", "*.aar", "*.apk", "*.kexe", "*.app", "*.hprof"):
            self.assertNotIn(forbidden, upload)


if __name__ == "__main__":
    unittest.main()
