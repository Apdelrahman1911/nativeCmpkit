"""New finite Desktop request-state guards; synthetic tooling, never native acceptance."""
from collections import Counter
import io
import json
import os
from pathlib import Path
import re
import tempfile
import time
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

import desktop_media_context
import library_tests as lt
import workflow_matrix as matrix


FOCUS = "webview-desktop-request-state"
CLASS = "com.mohamedrejeb.calf.ui.web.DesktopWebViewRequestStateAcceptanceTest"
METHOD = "twoHeldNativeTransportFailuresResetOldErrorsAndRecoverOnTheSameOwner"
SOURCE = "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewRequestStateAcceptanceTest.kt"
SOURCE_SHA256 = "c08bcdc062d18d24c5a370aaa818a8171c352d06acca35af1202fd4eb2c13f13"
SLOTS = ("desktop-linux-x64", "desktop-macos-arm64", "desktop-windows-x64", "desktop-linux-arm64", "desktop-macos-x64")
HOSTS = (("Linux", "x86_64"), ("Darwin", "arm64"), ("Windows", "AMD64"), ("Linux", "aarch64"), ("Darwin", "x86_64"))


class DesktopWebViewRequestFocusTests(unittest.TestCase):
    def plan(self, root=lt.ROOT):
        return lt.plan(root, "desktop", only_modules=("calf-webview",), focus=FOCUS)

    def source_root(self, directory):
        root = Path(directory).resolve()
        (root / "settings.gradle.kts").write_text('include(\n    ":calf-webview",\n)\n')
        build = root / "calf-webview/build.gradle.kts"
        build.parent.mkdir()
        build.write_text("// Explicitly synthetic discovery root; never compiled\n")
        source = root / SOURCE
        source.parent.mkdir(parents=True)
        source.write_bytes((lt.ROOT / SOURCE).read_bytes())
        return root

    def cases(self):
        return [{"classname": CLASS, "name": METHOD + "[desktop]"}]

    def collect(self, cases=None, outcome="", stale=False, duplicate=False, extra_empty=False, markers=1, system="Linux"):
        plan = self.plan()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected, = plan["expected"]
            folder = root / selected["report_directory"]
            folder.mkdir(parents=True)
            xml = ET.Element("testsuite")
            for case in self.cases() if cases is None else cases:
                node = ET.SubElement(xml, "testcase", **case)
                if outcome:
                    ET.SubElement(node, outcome)
            file = folder / "TEST-explicitly-synthetic.xml"
            file.write_bytes(ET.tostring(xml))
            if duplicate:
                (folder / "TEST-duplicate.xml").write_bytes(file.read_bytes())
            if extra_empty:
                (folder / "TEST-extra-empty.xml").write_bytes(b"<testsuite/>")
            now = time.time_ns()
            if stale:
                os.utime(file, ns=(now - 20_000_000_000, now - 20_000_000_000))
            return lt.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                      Counter({selected["task"]: markers}), host_system=system)

    def test_profile_selects_only_one_new_method_on_all_five_declared_desktop_hosts(self):
        rows = matrix.matrix(FOCUS)["include"]
        self.assertEqual(list(SLOTS), [row["slot"] for row in rows])
        self.assertTrue(all(row["suite"] == "desktop" and row["test-modules"] == "calf-webview" and
                            row["test-focus"] == FOCUS for row in rows))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        self.assertEqual(["browser-js", "browser-wasm"], [row["slot"] for row in matrix.matrix("webview-request-state")["include"]])
        self.assertTrue(all(row["test-focus"] == "webview-browser-request-state" for row in matrix.matrix("webview-request-state")["include"]))
        for profile in ("all", "core", "apple", "windows", "webview-desktop"):
            self.assertTrue(all("test-focus" not in row for row in matrix.matrix(profile)["include"]))

    def test_plan_and_command_pin_one_method_one_source_and_preserve_inherited_compilation(self):
        plan = self.plan()
        selected, = plan["expected"]
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(list(lt.SUITES["desktop"][1]), plan["inherited_test_source_sets"])
        self.assertEqual([SOURCE], selected["test_source_files"])
        self.assertEqual(["desktopTest"], selected["test_source_sets"])
        self.assertEqual({SOURCE: SOURCE_SHA256}, selected["test_source_sha256"])
        self.assertEqual(self.cases(), selected["required_testcases"])
        self.assertEqual(CLASS + "." + METHOD, selected["test_filter"])
        for system, architecture in HOSTS:
            with patch("library_tests.platform.system", return_value=system), patch("library_tests.platform.machine", return_value=architecture):
                command = lt.gradle_command("desktop", plan)
            self.assertEqual(1, command.count("--tests"))
            self.assertEqual(CLASS + "." + METHOD, command[command.index("--tests") + 1])
            self.assertIn(":calf-webview:desktopTest", command)
            self.assertNotIn("publish", " ".join(command))
            self.assertNotIn("stopCancelsRealSlowLoad", " ".join(command))

    def test_real_cli_plans_exact_focus_and_refuses_wrong_suite_module_or_unknown_focus(self):
        args = ["library_tests.py", "plan", "--suite", "desktop", "--module", "calf-webview", "--focus", FOCUS]
        stream = io.StringIO()
        with patch("sys.argv", args), patch("sys.stdout", stream):
            self.assertEqual(0, lt.main())
        self.assertEqual(self.plan(), json.loads(stream.getvalue()))
        for suite in ("android-host", "android-device", "ios", "js", "wasm"):
            with self.assertRaises(ValueError):
                lt.plan(lt.ROOT, suite, only_modules=("calf-webview",), focus=FOCUS)
            wrong = args.copy(); wrong[3] = suite
            with patch("sys.argv", wrong), patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit) as error:
                lt.main()
            self.assertEqual(2, error.exception.code)
        for modules in (None, (), ("calf-ui",), ("calf-webview", "calf-ui"), ("calf-webview", "calf-webview")):
            with self.assertRaises(ValueError):
                lt.plan(lt.ROOT, "desktop", only_modules=modules, focus=FOCUS)
        wrong = args.copy(); wrong[5] = "calf-ui"
        with patch("sys.argv", wrong), patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit) as error:
            lt.main()
        self.assertEqual(2, error.exception.code)
        with patch("sys.argv", args[:-1] + ["unreviewed-wildcard"]), patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit) as error:
            lt.main()
        self.assertEqual(2, error.exception.code)

    def test_supported_runtime_aliases_pass_and_unknown_host_architecture_is_refused(self):
        for system, architecture in (*HOSTS, ("Linux", "x64"), ("Linux", "arm64")):
            lt.validate_webview_desktop_request_host(system, architecture)
        for system, architecture in (("Linux", "riscv64"), ("Linux", "i686"), ("Darwin", "x86"),
                                     ("Windows", "arm64"), ("FreeBSD", "x64"), ("", ""), (None, "x64"), ("Linux", None)):
            with self.assertRaises(ValueError):
                lt.validate_webview_desktop_request_host(system, architecture)
            with patch("library_tests.platform.system", return_value=system), patch("library_tests.platform.machine", return_value=architecture):
                with self.assertRaises(ValueError):
                    lt.gradle_command("desktop", self.plan())
        with self.assertRaises(ValueError):
            lt.gradle_command("js", self.plan())

    def test_source_calibration_precedes_any_renamed_ignored_extra_or_changed_fixture_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.source_root(directory)
            self.assertTrue(lt.validate_test_focus(self.plan(root)))
            source = root / SOURCE
            original = source.read_text()
            variants = (original.replace(METHOD, "wrongMethod", 1), original.replace("class DesktopWebViewRequestStateAcceptanceTest", "class ForeignTest", 1),
                        original.replace("package com.mohamedrejeb.calf.ui.web", "package foreign", 1),
                        original.replace("@Test", "@Ignore @Test", 1), original.replace("@Test", "@IgnoredTest", 1),
                        original + "\n@Test fun extra() {}\n", original.replace("owned.release.await(15, TimeUnit.SECONDS)", "owned.release.await(16, TimeUnit.SECONDS)", 1))
            for changed in variants:
                self.assertNotEqual(original, changed)
                source.write_bytes(changed.encode("utf-8"))
                with self.assertRaises(ValueError):
                    self.plan(root)
            source.write_bytes(original.encode("utf-8"))
            self.assertEqual(SOURCE_SHA256, lt.snapshot_inputs(root)[SOURCE])
            self.assertTrue(lt.validate_test_focus(self.plan(root)))
            source.unlink()
            with self.assertRaises(ValueError):
                self.plan(root)
            source.symlink_to(root / "calf-webview/build.gradle.kts")
            with self.assertRaises(ValueError):
                self.plan(root)

    def test_filter_source_case_task_report_or_complete_suite_mutations_cannot_fall_back(self):
        variants = (("project", ":calf-io"), ("module", "calf-io"), ("task", ":calf-webview:publish"),
                    ("report_directory", "calf-io/build/test-results/desktopTest"), ("test_filter", "*"),
                    ("test_filter", "com.mohamedrejeb.calf.ui.web.JavaFxWebViewTest.stopCancelsRealSlowLoadWithoutFeedbackLoop"),
                    ("test_source_files", []), ("test_source_files", [SOURCE, lt.WEBVIEW_IDENTITY_SPECS["desktop"]["source"]]),
                    ("test_source_files", [lt.WEBVIEW_IDENTITY_SPECS["desktop"]["source"]]), ("test_source_sets", ["commonTest"]),
                    ("test_source_sha256", {}), ("test_source_sha256", {SOURCE: "0" * 64}),
                    ("required_testcases", []), ("required_testcases", self.cases() * 2),
                    ("required_testcases", [{"classname": "Foreign.Test", "name": METHOD + "[desktop]"}]))
        for key, value in variants:
            plan = self.plan(); plan["expected"][0][key] = value
            with self.assertRaises(ValueError):
                lt.validate_test_focus(plan)
        for key, value in (("complete_suite_requested", True), ("suite", "android-device"),
                           ("inherited_test_source_sets", ["iosTest"]), ("explicit_test_focus", None)):
            plan = self.plan(); plan[key] = value
            with self.assertRaises(ValueError):
                lt.validate_test_focus(plan)

    def test_only_one_fresh_exact_success_is_required_without_host_na_or_accepted_cases(self):
        for system in ("Linux", "Darwin", "Windows"):
            result = self.collect(system=system)
            self.assertEqual([], result["errors"], result["errors"])
            self.assertEqual(1, result["totals"]["passed"])
            self.assertEqual(0, result["totals"]["not_applicable"])
            scenario, = result["modules"][0]["native_scenarios"]
            self.assertEqual(SOURCE, scenario["source"])
            self.assertTrue(scenario["required_on_host"])
            self.assertEqual("required-executed", scenario["disposition"])

    def test_empty_extra_duplicate_foreign_or_wrong_target_xml_stays_red(self):
        for cases in ([], self.cases() * 2, self.cases() + [{"classname": CLASS, "name": "acceptedStop[desktop]"}],
                      [{"classname": "Foreign.Test", "name": METHOD + "[desktop]"}], [{"classname": CLASS, "name": METHOD}],
                      [{"classname": CLASS, "name": METHOD + "[iosSimulatorArm64]"}]):
            self.assertTrue(self.collect(cases=cases)["errors"])
        self.assertTrue(self.collect(extra_empty=True)["errors"], "Extra empty XML cannot make the one-report selection broader")

    def test_failed_errored_skipped_stale_or_nonfresh_task_evidence_is_not_accepted(self):
        for changed in ({"outcome": "failure"}, {"outcome": "error"}, {"outcome": "skipped"}, {"stale": True},
                        {"duplicate": True}, {"markers": 0}, {"markers": 2}):
            self.assertTrue(self.collect(**changed)["errors"])

    def test_nonmedia_selection_does_not_start_source_inferred_audio_or_change_full_source_inventory(self):
        focused = self.plan()
        full = lt.plan(lt.ROOT, "desktop", only_modules=("calf-webview",))
        self.assertIn(SOURCE, full["expected"][0]["test_source_files"])
        self.assertIn(desktop_media_context.MEDIA_SOURCE, full["expected"][0]["test_source_files"])
        with tempfile.TemporaryDirectory() as directory, patch("desktop_media_context.platform.system", return_value="Linux"):
            root = Path(directory)
            audio = desktop_media_context.OwnedAudio(root, root / "build/ci-verification/synthetic-only", focused)
            self.assertFalse(audio.requested)
            self.assertIsNone(audio.process)
            self.assertTrue(desktop_media_context.OwnedAudio(root, root / "build/ci-verification/synthetic-only", full).requested)

    def test_only_profile_option_is_added_without_permissions_upload_or_parallel_policy_expansion(self):
        workflow = (lt.ROOT / ".github/workflows/gradle.yml").read_text()
        options = re.search(r"options: \[([^\n]+)\]", workflow).group(1)
        self.assertIn(FOCUS, {option.strip() for option in options.split(",")})
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("inputs.profile == 'webview-request-state' || inputs.profile == 'webview-content-transitions') && 1 || 2 }}", workflow)
        upload = workflow.split("- name: Keep receipts and actual selected-task XML", 1)[1].split("\n  consumer-core-io:", 1)[0]
        for forbidden in ("*.jar", "*.aar", "*.apk", "*.kexe", "*.app", "*.hprof"):
            self.assertNotIn(forbidden, upload)
        self.assertNotIn("packages: write", workflow)
        self.assertNotIn("id-token: write", workflow)


if __name__ == "__main__":
    unittest.main()
