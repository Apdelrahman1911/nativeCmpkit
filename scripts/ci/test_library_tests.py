from collections import Counter
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import library_tests as r
from test_daemon_jvm import FIXTURE as SYNTHETIC_DAEMON


class LibraryTestReceipts(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.write("settings.gradle.kts", 'include(\n    ":calf-fixture",\n    ":calf-empty",\n    ":calf-permissions:core",\n    ":sample:common",\n)\nproject(":calf-permissions:core").name = "calf-permissions-core"\n')
        for module in ("calf-fixture", "calf-empty", "calf-permissions/core", "sample/common"):
            self.write(module + "/build.gradle.kts", "// build fixture\n")
        self.write("calf-fixture/src/commonTest/kotlin/Fixture.kt", "// synthetic test input\n")

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value if isinstance(value, bytes) else value.encode())
        return path

    def plan(self, suite="desktop"):
        return r.plan(self.root, suite, minimum_modules=("calf-fixture",))

    def report(self, name="a", status="", **attributes):
        extra = " ".join(f'{key}="{value}"' for key, value in attributes.items())
        return f'<testsuite name="fixture" {extra}><testcase classname="Fixture" name="{name}">{status}</testcase></testsuite>'.encode()

    def collect(self, test_plan=None, markers=True):
        test_plan = test_plan or self.plan()
        now = time.time_ns()
        return r.collect_reports(self.root, test_plan, now - 1_000_000_000, now + 1_000_000_000,
                                 Counter(item["task"] for item in test_plan["expected"]) if markers else Counter())

    def test_literal_project_renames_and_sample_exclusion(self):
        projects = r.projects(self.root)
        self.assertEqual(":calf-permissions:calf-permissions-core", projects["calf-permissions/core"])
        self.assertNotIn("sample/common", projects)

    def test_source_set_inheritance_is_target_specific(self):
        for source_set in ("materialTest", "nonAndroidTest", "iosTest", "androidHostTest", "webTest"):
            self.write(f"calf-fixture/src/{source_set}/kotlin/{source_set}.kt", "// fixture")
        desktop = self.plan()["expected"][0]["test_source_sets"]
        android = self.plan("android-host")["expected"][0]["test_source_sets"]
        ios = self.plan("ios")["expected"][0]["test_source_sets"]
        web = self.plan("wasm")["expected"][0]["test_source_sets"]
        self.assertEqual(["commonTest", "materialTest", "nonAndroidTest"], desktop)
        self.assertEqual(["commonTest", "materialTest", "androidHostTest"], android)
        self.assertEqual(["commonTest", "nonAndroidTest", "iosTest"], ios)
        self.assertEqual(["commonTest", "materialTest", "nonAndroidTest", "webTest"], web)
        self.assertEqual(2, len(self.plan()["uncovered"]))

    def test_removing_last_required_source_is_failure(self):
        (self.root / "calf-fixture/src/commonTest/kotlin/Fixture.kt").unlink()
        with self.assertRaises(ValueError):
            self.plan()

    def test_explicit_diagnostic_subset_is_not_full_ci_coverage(self):
        self.write("calf-empty/src/commonTest/kotlin/A.kt", "// extra module tests")
        plan = r.plan(self.root, "desktop", only_modules=("calf-fixture",))
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(["calf-fixture"], plan["explicit_module_subset"])
        self.assertEqual(["calf-empty"], plan["test_bearing_modules_not_requested"])
        self.assertEqual(1, len(plan["expected"]))
        for modules in (("calf-fixture", "calf-fixture"), ("../../outside",), ("calf-permissions/core",)):
            with self.assertRaises(ValueError):
                r.plan(self.root, "desktop", only_modules=modules)

    def test_unknown_hierarchy_cannot_silently_drop_sources(self):
        self.write("calf-fixture/src/mysteryTest/kotlin/A.kt", "// fixture")
        with self.assertRaises(ValueError):
            self.plan()

    def test_dynamic_settings_include_requires_review(self):
        self.write("settings.gradle.kts", 'include(\n    libraryProjects.map { it.name }\n)\n')
        with self.assertRaises(ValueError):
            r.projects(self.root)

    def test_snapshot_covers_new_changed_sources_and_build_configuration(self):
        before = r.snapshot_inputs(self.root)
        self.write("calf-fixture/src/commonTest/kotlin/Added.kt", "// new input")
        self.write("calf-fixture/build/ignored.kt", "// generated, not source")
        self.write("sample/common/src/commonTest/kotlin/Sample.kt", "// never substitute sample tests")
        self.write("sample/common/build.gradle.kts", "// evaluated configuration changed")
        after = r.snapshot_inputs(self.root)
        self.assertIn("calf-fixture/src/commonTest/kotlin/Added.kt", after)
        self.assertNotIn("calf-fixture/build/ignored.kt", after)
        self.assertNotIn("sample/common/src/commonTest/kotlin/Sample.kt", after)
        self.assertNotEqual(before["sample/common/build.gradle.kts"], after["sample/common/build.gradle.kts"])
        self.assertNotEqual(r.input_digest(before), r.input_digest(after))

    def test_traversal_and_symlink_sources_refused(self):
        with self.assertRaises(ValueError):
            r.safe_path(self.root, "../external")
        (self.root / "calf-fixture/src/commonTest/link.kt").symlink_to(self.root / "settings.gradle.kts")
        with self.assertRaises(ValueError):
            self.plan()

    def test_actual_case_elements_not_trusted_summary_attributes(self):
        cases = r.junit_cases(self.report(tests="1", failures="0", errors="0", skipped="0"))
        self.assertEqual({"tests": 1, "failures": 0, "errors": 0, "skipped": 0, "passed": 1, "executed": 1,
                          "not_applicable": 0, "unexpected_skipped": 0}, r.case_counts(cases))
        for payload in (self.report(tests="300"), b'<testsuite name="fake" tests="300"/>', self.report(tests="-1")):
            with self.assertRaises(ValueError):
                r.junit_cases(payload)

    def test_duplicate_case_identity_is_not_double_counted(self):
        payload = b'<testsuite name="fixture"><testcase classname="A" name="a"/><testcase classname="A" name="a"/></testsuite>'
        with self.assertRaises(ValueError):
            r.junit_cases(payload)

    def test_dtd_and_entity_payloads_rejected_even_utf16(self):
        payload = '<!DOCTYPE testsuite [<!ENTITY x "entity">]><testsuite name="fixture"><testcase classname="A" name="&x;"/></testsuite>'
        for encoding in ("utf-8", "utf-16"):
            with self.assertRaises(ValueError):
                r.junit_cases(payload.encode(encoding))

    def test_nested_suites_count_once_and_validate_totals(self):
        payload = b'<testsuites tests="1"><testsuite name="fixture" tests="1"><testcase classname="A" name="a"/></testsuite></testsuites>'
        self.assertEqual(1, r.case_counts(r.junit_cases(payload))["tests"])
        with self.assertRaises(ValueError):
            r.junit_cases(payload.replace(b'tests="1"', b'tests="2"', 1))

    def test_test_failure_and_output_bodies_not_exported(self):
        cases = r.junit_cases(self.report(status='<failure message="private message">private body</failure><system-out>secret data</system-out>'))
        self.assertEqual("failed", cases[0]["status"])
        self.assertNotIn("private", json.dumps(cases))
        self.assertNotIn("secret", json.dumps(cases))

    def test_conflicting_skipped_and_failed_case_is_invalid(self):
        with self.assertRaises(ValueError):
            r.junit_cases(self.report(status="<skipped/><failure/>"))

    def test_empty_and_all_skipped_modules_are_not_passing(self):
        directory = self.plan()["expected"][0]["report_directory"]
        self.assertTrue(self.collect()["errors"])
        self.write(directory + "/TEST-empty.xml", b'<testsuite name="fixture" tests="0"/>')
        self.assertTrue(self.collect()["errors"])
        self.write(directory + "/TEST-empty.xml", self.report(status="<skipped/>"))
        result = self.collect()
        self.assertTrue(result["errors"])
        self.assertEqual(0, result["totals"]["executed"])

    def test_fresh_reports_require_actual_task_execution_marker(self):
        self.write(self.plan()["expected"][0]["report_directory"] + "/TEST-a.xml", self.report())
        self.assertFalse(self.collect()["errors"])
        self.assertTrue(self.collect(markers=False)["errors"])

    def test_stale_and_future_dated_reports_are_rejected(self):
        path = self.write(self.plan()["expected"][0]["report_directory"] + "/TEST-a.xml", self.report())
        for delta in (-60, 60):
            timestamp = time.time() + delta
            os.utime(path, (timestamp, timestamp))
            self.assertTrue(self.collect()["errors"])

    def test_one_missing_module_is_failure_despite_other_passing_module(self):
        self.write("calf-empty/src/commonTest/kotlin/A.kt", "// added tests")
        plan = self.plan()
        populated = next(item for item in plan["expected"] if item["module"] == "calf-fixture")
        self.write(populated["report_directory"] + "/TEST-a.xml", self.report())
        result = self.collect(plan)
        self.assertEqual(1, result["totals"]["passed"])
        self.assertTrue(any(error["module"] == "calf-empty" for error in result["errors"]))

    def test_duplicate_case_across_report_files_is_failure(self):
        directory = self.plan()["expected"][0]["report_directory"]
        self.write(directory + "/TEST-a.xml", self.report())
        self.write(directory + "/TEST-b.xml", self.report())
        self.assertTrue(self.collect()["errors"])

    def test_hardlinked_and_symlinked_reports_not_accepted(self):
        directory = self.plan()["expected"][0]["report_directory"]
        original = self.write("build/unrelated/old.xml", self.report())
        report = self.root / directory / "TEST-a.xml"
        report.parent.mkdir(parents=True)
        os.link(original, report)
        self.assertTrue(self.collect()["errors"])
        report.unlink()
        report.symlink_to(original)
        with self.assertRaises(ValueError):
            self.collect()

    def test_quarantine_moves_only_selected_task_reports(self):
        directory = self.plan()["expected"][0]["report_directory"]
        selected = self.write(directory + "/TEST-old.xml", self.report())
        unrelated = self.write("calf-fixture/build/test-results/allTests/TEST-old.xml", self.report())
        output = self.root / "build/ci-verification/run"
        output.mkdir(parents=True)
        moved = r.quarantine_reports(self.root, output, self.plan())
        self.assertEqual([directory], moved)
        self.assertFalse(selected.exists())
        self.assertTrue(unrelated.is_file())
        self.assertTrue((output / "previous-reports" / directory / "TEST-old.xml").is_file())

    def test_quarantine_validates_all_entries_before_mutation(self):
        directory = self.plan()["expected"][0]["report_directory"]
        selected = self.write(directory + "/TEST-old.xml", self.report())
        (selected.parent / "link").symlink_to(self.root / "settings.gradle.kts")
        output = self.root / "build/ci-verification/run"
        output.mkdir(parents=True)
        with self.assertRaises(ValueError):
            r.quarantine_reports(self.root, output, self.plan())
        self.assertTrue(selected.exists())

    def test_command_is_narrow_and_ios_device_is_explicit(self):
        command = r.gradle_command("desktop", self.plan())
        self.assertIn("--init-script", command)
        self.assertIn(":calf-fixture:desktopTest", command)
        self.assertNotIn("--rerun-tasks", command)
        for simulator in (None, "$(untrusted)"):
            with self.assertRaises(ValueError):
                r.gradle_command("ios", self.plan("ios"), simulator)
        with self.assertRaises(ValueError):
            r.gradle_command("desktop", self.plan(), "11111111-1111-1111-1111-111111111111")

    def test_runtime_markers_ignore_cached_task_lines(self):
        log = self.write("build/run.log", "> Task :calf-fixture:desktopTest FROM-CACHE\nNATIVECMPKIT_TEST_RUNTIME task=:calf-fixture:desktopTest gradle=9.7.1 java=17\n")
        self.assertEqual(Counter({":calf-fixture:desktopTest": 1}), r.execution_markers(log))

    def test_bounded_execution_does_not_start_without_disk_reserve(self):
        with patch.object(r.shutil, "disk_usage") as usage, patch.object(r.subprocess, "Popen") as process:
            usage.return_value.free = 0
            result = r.execute(self.root, [sys.executable, "-c", "pass"], self.root / "run.log", 60, 1024)
            self.assertEqual(75, result["exit_code"])
            process.assert_not_called()

    def fake_run(self, *, exit_code=0, mutate_source=False, revision_after=None):
        def execute(root, command, log_path, timeout, reserve_mib):
            self.write("calf-fixture/build/test-results/desktopTest/TEST-a.xml", self.report())
            log_path.write_text("NATIVECMPKIT_TEST_RUNTIME task=:calf-fixture:desktopTest gradle=9.7.1 java=17\n" +
                                r.daemon_jvm.PREFIX + json.dumps(SYNTHETIC_DAEMON) + "\n")
            if mutate_source:
                self.write("calf-fixture/src/commonTest/kotlin/Fixture.kt", "// changed during simulated execution")
            return {"exit_code": exit_code}
        with patch.dict(r.MINIMUM_MODULES, {"desktop": ("calf-fixture",)}), \
                patch.object(r.runtime_context, "capture", return_value={"source_revision": "a" * 40, "source_tree_dirty": True, "host": {"system": "Linux"}, "java": {"major": 17}}), \
                patch.object(r, "git_revision", side_effect=["a" * 40, revision_after or "a" * 40]), \
                patch.object(r, "execute", side_effect=execute):
            return r.run(self.root, "desktop", "build/ci-verification/synthetic", None, 60, 1024)

    def test_simulated_complete_fresh_run_creates_source_bound_receipt(self):
        receipt = self.fake_run()
        self.assertTrue(receipt["passed"])
        self.assertEqual(receipt["inputs_before_sha256"], receipt["inputs_after_sha256"])
        self.assertFalse((self.root / "build/ci-verification/.library-tests.lock").exists())
        with self.assertRaises(ValueError):
            self.fake_run()

    def test_exit_failure_is_not_masked_by_another_passing_suite(self):
        receipt = self.fake_run(exit_code=1)
        self.assertEqual(1, receipt["totals"]["passed"])
        self.assertFalse(receipt["passed"])

    def test_source_change_invalidates_otherwise_passing_simulated_run(self):
        receipt = self.fake_run(mutate_source=True)
        self.assertFalse(receipt["passed"])
        self.assertEqual(["calf-fixture/src/commonTest/kotlin/Fixture.kt"], receipt["changed_inputs"])

    def test_git_revision_change_invalidates_same_bytes(self):
        receipt = self.fake_run(revision_after="b" * 40)
        self.assertFalse(receipt["passed"])
        self.assertEqual("Git source revision changed during test invocation", receipt["input_capture_error"])

    def test_report_nesting_has_a_bound(self):
        payload = b"<testsuites>" * 34 + self.report() + b"</testsuites>" * 34
        with self.assertRaises(ValueError):
            r.junit_cases(payload)


class KotlinUserHomeOptionTests(unittest.TestCase):
    """Offline requested-argv checks, not effective KGP home/browser proof."""

    def setUp(self):
        self.fixture = LibraryTestReceipts()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root

    def command(self, suite, home, simulator=None):
        return r.gradle_command(suite, self.fixture.plan(suite), simulator,
                                kotlin_user_home=home, root=self.root)

    def test_default_commands_retain_all_behavior_and_add_the_actual_daemon_witness(self):
        device = "11111111-1111-1111-1111-111111111111"
        # Only the new root-daemon observation is added. The five pre-device
        # commands retain all established task/SDK/Kotlin-user-home behavior.
        for suite in ("desktop", "android-host", "js", "wasm", "ios"):
            with self.subTest(suite=suite):
                expected = [".\\gradlew.bat" if os.name == "nt" else "./gradlew", "--continue", "--no-daemon",
                            "--console=plain", "--no-configuration-cache", f"--max-workers={1 if suite == 'ios' else 2}",
                            "-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8",
                            "-Pkotlin.compiler.execution.strategy=in-process", "-Pkotlin.native.jvmArgs=-Xmx2048m",
                            "--init-script", "scripts/ci/fresh-tests.init.gradle.kts",
                            "--init-script", "scripts/ci/daemon-jvm.init.gradle.kts"]
                if suite == "ios":
                    expected.append(f"-PnativecmpkitSimulatorDevice={device}")
                expected.append(self.fixture.plan(suite)["expected"][0]["task"])
                self.assertEqual(expected, r.gradle_command(suite, self.fixture.plan(suite), device if suite == "ios" else None))
                self.assertEqual(expected, self.command(suite, None, device if suite == "ios" else None))

    def test_browser_home_is_one_canonical_argument_and_prepared_bytes_survive(self):
        home = "build/prepared --info/kotlin home"
        marker = self.fixture.write(home + "/installed/marker", "existing prepared installation")
        for suite in ("js", "wasm"):
            with self.subTest(suite=suite):
                default = r.gradle_command(suite, self.fixture.plan(suite))
                property_arg = f"-Pkotlin.user.home={(self.root / home).resolve()}"
                self.assertEqual(default[:-1] + [property_arg] + default[-1:], self.command(suite, home))
                self.assertNotIn("--info", self.command(suite, home))
                self.assertEqual("existing prepared installation", marker.read_text())
                future = "build/not-created/kotlin home"
                self.assertIn(f"-Pkotlin.user.home={self.root / future}", self.command(suite, future))
                self.assertFalse((self.root / future).exists())

    def test_home_requires_a_strict_build_descendant_directory(self):
        self.fixture.write("build/file", "not a directory")
        for home in ("", ".", "build", "../outside", str(self.root / "build/absolute"),
                     "calf-fixture/build/home", "build/../calf-fixture", "build/../../outside",
                     "build/file", "build/file/child"):
            with self.subTest(home=home), self.assertRaises(ValueError):
                self.command("wasm", home)

    def test_symlinked_build_ancestor_or_home_is_rejected(self):
        target = self.root / "target-directory"
        target.mkdir()
        build = self.root / "build"
        build.symlink_to(target, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.command("js", "build/home")
        build.unlink()
        build.mkdir()
        for name, destination in (("external", target), ("internal", build)):
            link = build / name
            link.symlink_to(destination, target_is_directory=True)
            for home in (f"build/{name}", f"build/{name}/child"):
                with self.subTest(home=home), self.assertRaises(ValueError):
                    self.command("wasm", home)

    def test_non_browser_commands_reject_the_home_option(self):
        for suite in ("desktop", "android-host", "ios"):
            with self.subTest(suite=suite), self.assertRaisesRegex(ValueError, "JS/Wasm"):
                self.command(suite, "build/home", "11111111-1111-1111-1111-111111111111" if suite == "ios" else None)

    def test_invalid_run_home_fails_before_outputs_or_execution(self):
        with patch.object(r, "execute") as execute, patch.object(r, "quarantine_reports") as quarantine:
            for home in ("build", "../outside", "calf-fixture/build/home"):
                with self.subTest(home=home), self.assertRaises(ValueError):
                    r.run(self.root, "js", "build/ci-verification/invalid", None, 60, 1024,
                          ("calf-fixture",), kotlin_user_home=home)
            execute.assert_not_called()
            quarantine.assert_not_called()
        self.assertFalse((self.root / "build/ci-verification").exists())

    def test_cli_threads_browser_option_without_other_arguments(self):
        for suite in ("js", "wasm"):
            result = {"suite": suite, "source_revision": "a" * 40, "passed": True,
                      "complete_suite_requested": False, "explicit_module_subset": ["calf-fixture"],
                      "execution": {"exit_code": 0}, "totals": {}, "errors": []}
            argv = ["library_tests.py", "run", "--suite", suite, "--module", "calf-fixture",
                    "--output", "build/ci-verification/cli", "--timeout", "60", "--reserve-mib", "1024",
                    "--kotlin-user-home", "build/prepared home"]
            with self.subTest(suite=suite), patch.object(sys, "argv", argv), patch.object(r, "ROOT", self.root), \
                    patch.object(r, "run", return_value=result) as run, patch.object(sys, "stdout", io.StringIO()):
                self.assertEqual(0, r.main())
                run.assert_called_once_with(self.root, suite, "build/ci-verification/cli", None, 60, 1024,
                                            ("calf-fixture",), kotlin_user_home="build/prepared home")

    def test_cli_refuses_plan_and_non_browser_option_without_work(self):
        cases = [("plan", "js", "build/home"), ("plan", "wasm", ""),
                 *(("run", suite, "build/home") for suite in ("desktop", "android-host", "ios"))]
        for operation, suite, home in cases:
            argv = ["library_tests.py", operation, "--suite", suite, "--kotlin-user-home", home]
            if operation == "run":
                argv += ["--output", "build/ci-verification/invalid"]
            with self.subTest(operation=operation, suite=suite), patch.object(sys, "argv", argv), \
                    patch.object(r, "run") as run, patch.object(r, "plan") as plan, \
                    patch.object(sys, "stderr", io.StringIO()), self.assertRaises(SystemExit) as stopped:
                r.main()
            self.assertEqual(2, stopped.exception.code)
            run.assert_not_called()
            plan.assert_not_called()

    def test_cli_does_not_add_an_arbitrary_gradle_argument_channel(self):
        for extra in ("--gradle-args=--write-locks", "--write-locks", "-Pkotlin.user.home=outside"):
            argv = ["library_tests.py", "run", "--suite", "js", "--output", "build/ci-verification/invalid",
                    "--kotlin-user-home", "build/home", extra]
            with self.subTest(extra=extra), patch.object(sys, "argv", argv), patch.object(r, "run") as run, \
                    patch.object(sys, "stderr", io.StringIO()), self.assertRaises(SystemExit) as stopped:
                r.main()
            self.assertEqual(2, stopped.exception.code)
            run.assert_not_called()

    def simulated_browser_run(self, suite, failure="none"):
        observed = []
        task = r.SUITES[suite][0]
        home = "build/prepared kotlin-home"
        marker = self.fixture.write(home + "/installed/marker", "keep prepared bytes")

        def execute(root, command, log_path, timeout, reserve_mib):
            observed.extend(command)
            if failure != "missing-report":
                self.fixture.write(f"calf-fixture/build/test-results/{task}/TEST-a.xml",
                                   self.fixture.report(status="<failure/>" if failure == "failed-case" else ""))
            log_path.write_text("" if failure == "missing-marker" else
                                f"NATIVECMPKIT_TEST_RUNTIME task=:calf-fixture:{task} gradle=9.7.1 java=17\n" +
                                r.daemon_jvm.PREFIX + json.dumps(SYNTHETIC_DAEMON) + "\n")
            if failure == "source-change":
                self.fixture.write("calf-fixture/src/commonTest/kotlin/Fixture.kt", "// changed during synthetic run")
            return {"exit_code": 1 if failure == "gradle" else 0,
                    **({"stop_reason": "synthetic stop"} if failure == "stop-reason" else {})}

        output = f"build/ci-verification/{suite}-{failure}"
        with patch.object(r.runtime_context, "capture", return_value={"source_revision": "a" * 40,
                         "source_tree_dirty": True, "host": {"system": "Linux"}, "java": {"major": 17}}), \
                patch.object(r, "git_revision", return_value="a" * 40), patch.object(r, "execute", side_effect=execute):
            receipt = r.run(self.root, suite, output, None, 60, 1024, ("calf-fixture",), kotlin_user_home=home)
        self.assertEqual(observed, receipt["command"])
        self.assertEqual(receipt, json.loads((self.root / output / "receipt.json").read_text()))
        self.assertEqual([f"-Pkotlin.user.home={self.root / home}"],
                         [arg for arg in observed if arg.startswith("-Pkotlin.user.home=")])
        self.assertEqual("keep prepared bytes", marker.read_text())
        self.assertFalse((self.root / "build/ci-verification/.library-tests.lock").exists())
        return receipt

    def test_simulated_run_records_requested_home_and_preserves_prepared_install(self):
        for suite in ("js", "wasm"):
            with self.subTest(suite=suite):
                receipt = self.simulated_browser_run(suite)
                self.assertTrue(receipt["passed"])
                self.assertEqual(1, receipt["totals"]["passed"])
                self.assertFalse(receipt["complete_suite_requested"])
                self.assertEqual(receipt["inputs_before_sha256"], receipt["inputs_after_sha256"])

    def test_requested_home_never_overrides_existing_failure_gates(self):
        for failure in ("gradle", "missing-report", "failed-case", "missing-marker", "source-change", "stop-reason"):
            with self.subTest(failure=failure):
                self.assertFalse(self.simulated_browser_run("wasm", failure)["passed"])


class NativeShareBoundaryFocusTests(unittest.TestCase):
    """Synthetic tooling checks, never reported as actual native executions."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.write("settings.gradle.kts", 'include(\n    ":calf-share",\n)\n')
        self.write("calf-share/build.gradle.kts", "// synthetic build\n")
        self.write(r.native_test_policy.SOURCE, "// required bridge source is still retained\n")
        self.source = "package com.mohamedrejeb.calf.share.platform\nclass NativeLoaderBoundaryIntegrationTest {\n" + \
            "\n".join("@Test fun " + method + "() {}" for method in r.NATIVE_SHARE_BOUNDARY_METHODS) + "\n}\n"
        self.write(r.NATIVE_SHARE_BOUNDARY_SOURCE, self.source)

    def write(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)
        return path

    def plan(self):
        return r.plan(self.root, "desktop", only_modules=("calf-share",), focus=r.NATIVE_SHARE_BOUNDARY_FOCUS)

    def collect(self, methods=None, skip=False, focused=True):
        plan = self.plan() if focused else r.plan(self.root, "desktop", only_modules=("calf-share",))
        methods = r.NATIVE_SHARE_BOUNDARY_METHODS if methods is None else methods
        body = "".join('<testcase classname="' + r.NATIVE_SHARE_BOUNDARY_CLASS + '" name="' + method +
                       '[desktop]">' + ('<skipped/>' if skip and index == 0 else '') + '</testcase>'
                       for index, method in enumerate(methods))
        self.write("calf-share/build/test-results/desktopTest/TEST-boundary.xml", "<testsuite>" + body + "</testsuite>")
        now = time.time_ns()
        return r.collect_reports(self.root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                 Counter({":calf-share:desktopTest": 1}), host_system="Windows")

    def test_exact_plan_keeps_all_source_inputs_but_requests_only_five_cases(self):
        plan = self.plan()
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(r.NATIVE_SHARE_BOUNDARY_FOCUS, plan["explicit_test_focus"])
        self.assertIn(r.native_test_policy.SOURCE, plan["expected"][0]["test_source_files"])
        self.assertEqual(5, len(plan["expected"][0]["required_testcases"]))
        command = r.gradle_command("desktop", plan, root=self.root)
        self.assertEqual([":calf-share:desktopTest", "--tests", r.NATIVE_SHARE_BOUNDARY_CLASS], command[-3:])
        self.assertEqual(1, command.count("--tests"))
        with self.assertRaises(ValueError):
            r.gradle_command("js", plan, root=self.root)

    def test_only_reviewed_desktop_module_focus_is_allowed(self):
        for suite, modules, focus in (("js", ("calf-share",), r.NATIVE_SHARE_BOUNDARY_FOCUS),
                                      ("desktop", None, r.NATIVE_SHARE_BOUNDARY_FOCUS),
                                      ("desktop", ("calf-share", "calf-io"), r.NATIVE_SHARE_BOUNDARY_FOCUS),
                                      ("desktop", ("calf-share",), "arbitrary.*")):
            with self.subTest(suite=suite, modules=modules, focus=focus), self.assertRaises(ValueError):
                r.plan(self.root, suite, only_modules=modules, focus=focus)

    def test_changed_or_extra_authored_method_cannot_be_silently_filtered_out(self):
        for source in (self.source.replace(r.NATIVE_SHARE_BOUNDARY_METHODS[0], "changedMethod"),
                       self.source + "\n@Test fun extraMethod() {}", self.source.replace("@Test", "@IgnoredTest", 1)):
            self.write(r.NATIVE_SHARE_BOUNDARY_SOURCE, source)
            with self.subTest(source=source), self.assertRaises(ValueError):
                self.plan()

    def test_poisoned_plan_never_creates_an_arbitrary_argument_or_weaker_case_set(self):
        plan = self.plan()
        for key, value in (("test_filter", "*"), ("required_testcases", []), ("task", ":calf-share:publish")):
            changed = json.loads(json.dumps(plan))
            changed["expected"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.gradle_command("desktop", changed, root=self.root)
        del plan["explicit_test_focus"]
        with self.assertRaises(ValueError):
            r.gradle_command("desktop", plan, root=self.root)

    def test_all_five_actual_xml_cases_required_with_no_native_na_claim(self):
        result = self.collect()
        self.assertFalse(result["errors"])
        self.assertEqual(5, result["totals"]["executed"])
        self.assertEqual(0, result["totals"]["not_applicable"])
        self.assertEqual(5, len(result["modules"][0]["native_scenarios"]))

    def test_missing_foreign_or_skipped_cases_never_pass_focused_gate(self):
        for methods, skip in ((r.NATIVE_SHARE_BOUNDARY_METHODS[:-1], False),
                              ((*r.NATIVE_SHARE_BOUNDARY_METHODS, "unrelatedMethod"), False),
                              (r.NATIVE_SHARE_BOUNDARY_METHODS, True)):
            with self.subTest(methods=methods, skip=skip):
                self.assertTrue(self.collect(methods, skip)["errors"])

    def test_full_share_suite_still_requires_its_unrequested_native_bridge_cases(self):
        result = self.collect(focused=False)
        self.assertTrue(result["errors"])
        self.assertTrue(any("must appear exactly once" in e["error"] for e in result["errors"]))

    def test_cli_refuses_wrong_scope_before_work(self):
        for args in (("--suite", "desktop"), ("--suite", "js", "--module", "calf-share"),
                     ("--suite", "desktop", "--module", "calf-share", "--module", "calf-io")):
            argv = ["library_tests.py", "run", *args, "--focus", r.NATIVE_SHARE_BOUNDARY_FOCUS,
                    "--output", "build/ci-verification/refused"]
            with self.subTest(args=args), patch.object(sys, "argv", argv), patch.object(r, "run") as run, \
                    patch.object(sys, "stderr", io.StringIO()), self.assertRaises(SystemExit):
                r.main()
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
