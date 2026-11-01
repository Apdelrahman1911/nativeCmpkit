"""New finite security-route models only; no compiler, TLS, painting or native pass."""
from collections import Counter
import copy
import os
from pathlib import Path
import re
import shutil
import tempfile
import time
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

import desktop_media_context
import desktop_security_plan as security
import library_tests as lt
import workflow_matrix as matrix
from test_ios_io_profile import profile_options


ROWS = (
    ("desktop-macos-arm64", "Darwin", "arm64", "tls-rendering-cookies-policy", 3),
    ("desktop-windows-x64", "Windows", "AMD64", "tls-rendering-cookies-policy", 3),
    ("desktop-linux-arm64", "Linux", "aarch64", "tls-rendering-cookies-policy-media", 4),
    ("desktop-macos-x64", "Darwin", "x86_64", "tls-rendering-cookies-policy", 3),
)


def temporary():
    return tempfile.TemporaryDirectory(prefix="nativecmpkit-security-source-model-",
                                     dir=os.environ.get("NATIVECMPKIT_SOURCE_MODEL_TMP"))


class DesktopSecurityRoutingModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plans = {focus: lt.plan(lt.ROOT, "desktop", only_modules=("calf-webview",), focus=focus)
                     for focus in security.FOCUSES}

    def plan(self, focus="tls-rendering"):
        return copy.deepcopy(self.plans[focus])

    def source_root(self, folder):
        root = Path(folder)
        (root / "settings.gradle.kts").write_text('include(\n    ":calf-webview",\n)\n')
        for relative in (*security.SOURCE_SHA256, security.BUILD_SOURCE, security.INIT_SCRIPT):
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(lt.ROOT / relative, destination)
        return root

    def reports(self, root, focus, groups=None, outcome="", stale=False, hardlink=False, symlink=False):
        item, = self.plan(focus)["expected"]
        folder = root / item["report_directory"]
        folder.mkdir(parents=True)
        if groups is None:
            groups = [[case] for case in item["required_testcases"]]
        files = []
        for index, cases in enumerate(groups):
            document = ET.Element("testsuite")
            for case in cases:
                node = ET.SubElement(document, "testcase", **case)
                if outcome:
                    ET.SubElement(node, outcome)
            file = folder / ("TEST-explicitly-synthetic-security-%s.xml" % index)
            file.write_bytes(ET.tostring(document)); files.append(file)
        if files and stale:
            now = time.time_ns()
            os.utime(files[0], ns=(now - 20_000_000_000, now - 20_000_000_000))
        if files and hardlink:
            os.link(files[0], root / "synthetic-hardlink.xml")
        if files and symlink:
            payload = files[0].read_bytes(); files[0].unlink()
            target = root / "synthetic-target.xml"; target.write_bytes(payload)
            files[0].symlink_to(target)
        return item

    def collect(self, focus, groups=None, outcome="", stale=False, markers=1, hardlink=False):
        with temporary() as folder:
            root = Path(folder)
            item = self.reports(root, focus, groups, outcome, stale, hardlink)
            now = time.time_ns()
            return lt.collect_reports(root, self.plan(focus), now - 1_000_000_000, now + 1_000_000_000,
                                      Counter({item["task"]: markers}), host_system="Linux")

    def events(self, focus):
        route = security.focus_selection(focus)
        prefix = "NATIVECMPKIT_DESKTOP_SECURITY_"
        lines = [prefix + "SETUP task=:calf-webview:desktopTest focus=" + focus +
                 " forks=1 forkEvery=1 classes=" + str(len(route["selected"]))]
        for index, name in enumerate(route["selected"], 7):
            classname = security.SPECS[name][0]
            worker = " worker=" + str(index)
            lines.extend((prefix + "WORKER phase=start" + worker,
                          prefix + "CASE phase=start" + worker + " classname=" + classname,
                          prefix + "CASE phase=finish" + worker + " classname=" + classname +
                          " tests=1 passed=1 failed=0 skipped=0 result=SUCCESS",
                          prefix + "WORKER phase=finish" + worker +
                          " tests=1 passed=1 failed=0 skipped=0 result=SUCCESS"))
        return lines

    def observe(self, focus, lines):
        with temporary() as folder:
            log = Path(folder) / "synthetic-public-worker-events.log"
            log.write_text("\n".join(lines) + "\n")
            return security.worker_observation(log, focus)

    def test_registered_profile_reaches_real_source_only_cli_on_exact_existing_rows(self):
        rows = matrix.matrix(security.PROFILE)["include"]
        self.assertEqual([row[0] for row in ROWS], [row["slot"] for row in rows])
        self.assertEqual([row[3] for row in ROWS], [row["test-focus"] for row in rows])
        self.assertTrue(all(row["suite"] == "desktop" and row["test-modules"] == "calf-webview" for row in rows))
        preflight = matrix.preflight_plans(security.PROFILE, root=lt.ROOT)
        self.assertTrue(preflight["source_only"])
        self.assertEqual(0, preflight["Gradle_builds_executed"])
        self.assertEqual(0, preflight["library_tests_executed"])
        self.assertEqual(4, len(preflight["slots"]))
        self.assertTrue(all(row["expected_modules"] == 1 and row["exit_code"] == 0 for row in preflight["slots"]))
        for row, expected in zip(preflight["slots"], ROWS):
            self.assertEqual(expected[3], row["command"][row["command"].index("--focus") + 1])
        self.assertEqual([3, 3, 4, 3], [len(self.plan(row[3])["expected"][0]["required_testcases"]) for row in ROWS])

    def test_owning_command_emits_thirteen_remaining_selectors_with_exact_fixture_property(self):
        selectors = []
        for slot, system, arch, focus, count in ROWS:
            with self.subTest(slot=slot), patch("library_tests.platform.system", return_value=system), \
                    patch("library_tests.platform.machine", return_value=arch):
                plan = self.plan(focus)
                command = lt.gradle_command("desktop", plan, root=lt.ROOT)
                selected = [command[index + 1] for index, value in enumerate(command) if value == "--tests"]
                self.assertEqual(list(security.focus_selection(focus)["selectors"]), selected)
                self.assertEqual(count, len(selected))
                self.assertEqual(1, command.count("-PnativecmpkitDesktopSecurityFocus=" + focus))
                self.assertEqual(1, command.count(security.INIT_SCRIPT))
                self.assertEqual(1, command.count(":calf-webview:desktopTest"))
                self.assertIn("--no-daemon", command)
                self.assertIn("scripts/ci/fresh-tests.init.gradle.kts", command)
                self.assertIn("scripts/ci/daemon-jvm.init.gradle.kts", command)
                selectors.extend(selected)
        self.assertEqual(13, len(selectors))
        self.assertEqual(4, len(set(selectors)))
        self.assertFalse(any("RequestState" in selector or "StopRedirect" in selector for selector in selectors))

    def test_dispatch_command_refuses_actual_focus_host_crossover_before_any_child_work(self):
        variants = (("Linux", "x86_64", "tls-rendering-cookies-policy"),
                    ("Linux", "aarch64", "tls-rendering"), ("Darwin", "arm64", "tls-rendering"),
                    ("Windows", "ARM64", "tls-rendering-cookies-policy"),
                    ("FreeBSD", "x86_64", "tls-rendering"), (None, "x64", "tls-rendering"))
        for system, arch, focus in variants:
            with self.subTest(system=system, arch=arch, focus=focus), \
                    patch("library_tests.platform.system", return_value=system), \
                    patch("library_tests.platform.machine", return_value=arch):
                with self.assertRaises(ValueError):
                    lt.gradle_command("desktop", self.plan(focus), root=lt.ROOT)
        for suite, modules in (("desktop", None), ("desktop", ("calf-io",)),
                               ("desktop", ("calf-webview", "calf-io")), ("android-device", ("calf-webview",))):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                lt.plan(lt.ROOT, suite, only_modules=modules, focus="tls-rendering")

    def test_owning_source_command_readback_refuses_changed_isolation_init_and_fixture(self):
        variants = ((security.BUILD_SOURCE, "forkEvery = 1L", "forkEvery = 0L"),
                    (security.BUILD_SOURCE, "maxParallelForks = 1", "maxParallelForks = 2"),
                    (security.BUILD_SOURCE, "excludeTestsMatching(desktopSecurityClass)", "excludeTestsMatching(\"Foreign\")"),
                    (security.INIT_SCRIPT, "repeat(16)", "repeat(17)"),
                    (security.TLS_HELPER, "// SPDX-License-Identifier: Apache-2.0", "// Changed owning fixture"))
        for relative, old, new in variants:
            with self.subTest(relative=relative, old=old), temporary() as folder, \
                    patch("library_tests.platform.system", return_value="Linux"), \
                    patch("library_tests.platform.machine", return_value="x86_64"):
                root = self.source_root(folder)
                plan = lt.plan(root, "desktop", only_modules=("calf-webview",), focus="tls-rendering")
                file = root / relative; text = file.read_text(); self.assertIn(old, text)
                file.write_text(text.replace(old, new, 1))
                with self.assertRaises(ValueError):
                    lt.gradle_command("desktop", plan, root=root)
        with temporary() as folder:
            root = self.source_root(folder)
            file = root / security.INIT_SCRIPT; file.unlink()
            with self.assertRaises((OSError, ValueError)):
                lt.plan(root, "desktop", only_modules=("calf-webview",), focus="tls-rendering")

    def test_owning_plan_mutations_cannot_broaden_case_source_task_or_worker_contract(self):
        focus = "tls-rendering-cookies-policy-media"
        variants = (("module", "calf-io"), ("project", ":calf-io"), ("task", ":calf-webview:publish"),
                    ("report_directory", "calf-io/build/test-results/desktopTest"), ("test_filter", "*"),
                    ("required_testcases", []), ("required_original_xml", 1), ("required_original_xml", True),
                    ("test_source_files", []), ("test_source_sha256", {}), ("test_source_sets", ["commonTest"]))
        for key, value in variants:
            plan = self.plan(focus); plan["expected"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                lt.validate_test_focus(plan)
        for key, value in (("fork_every", 0), ("max_parallel_forks", 2), ("fork_every", True),
                           ("focus", "tls-rendering"), ("init_script_sha256", "0" * 64),
                           ("worker_fixture_property", "shared-worker"), ("public_worker_boundary_observation_required", False)):
            plan = self.plan(focus); plan["desktop_security_fixture"][key] = value
            with self.subTest(contract=key), self.assertRaises(ValueError):
                lt.validate_test_focus(plan)
        for key, value in (("complete_suite_requested", True), ("suite", "android-device"),
                           ("inherited_test_source_sets", ["commonTest"]), ("explicit_module_subset", [])):
            plan = self.plan(focus); plan[key] = value
            with self.subTest(scope=key), self.assertRaises(ValueError):
                lt.validate_test_focus(plan)

    def test_security_fixture_is_absent_from_ordinary_and_existing_request_commands(self):
        default = lt.plan(lt.ROOT, "desktop", only_modules=("calf-webview",))
        request = lt.plan(lt.ROOT, "desktop", only_modules=("calf-webview",), focus=lt.WEBVIEW_DESKTOP_REQUEST_FOCUS)
        for plan in (default, request):
            self.assertNotIn("desktop_security_fixture", plan)
            with patch("library_tests.platform.system", return_value="Linux"), \
                    patch("library_tests.platform.machine", return_value="x86_64"):
                command = lt.gradle_command("desktop", plan, root=lt.ROOT)
            self.assertNotIn(security.INIT_SCRIPT, command)
            self.assertFalse(any(value.startswith("-PnativecmpkitDesktopSecurityFocus=") for value in command))
            plan["desktop_security_fixture"] = self.plan()["desktop_security_fixture"]
            with self.assertRaises(ValueError):
                lt.validate_test_focus(plan)

    def test_synthetic_originals_flow_through_new_collector_as_thirteen_remaining_cases(self):
        passed = 0
        for slot, system, arch, focus, count in ROWS:
            with self.subTest(slot=slot):
                result = self.collect(focus)
                self.assertEqual([], result["errors"])
                self.assertEqual(count, result["totals"]["passed"])
                self.assertEqual(0, result["totals"]["not_applicable"])
                module, = result["modules"]
                self.assertEqual(count, len(module["reports"]))
                self.assertTrue(all(report["tests"] == 1 for report in module["reports"]))
                self.assertEqual({case["classname"] for case in self.plan(focus)["expected"][0]["required_testcases"]},
                                 {case["classname"] for case in module["native_scenarios"]})
                self.assertTrue(all(case["required_on_host"] and case["source"] != "unselected" for case in module["native_scenarios"]))
                passed += result["totals"]["passed"]
        self.assertEqual(13, passed, "These are authored synthetic XML inputs, not native executions")

    def test_new_collector_refuses_mixed_empty_duplicate_accepted_and_wrong_target_xml(self):
        focus = "tls-rendering-cookies-policy-media"
        cases = self.plan(focus)["expected"][0]["required_testcases"]
        variants = ([], [[case] for case in cases[:-1]], [cases, [], [], []],
                    [[case] for case in cases] + [[]], [[case] for case in cases] + [[cases[0]]],
                    [[dict(case, name=case["name"].replace("[desktop]", ""))] for case in cases],
                    [[dict(case, name=case["name"].replace("[desktop]", "[iosSimulatorArm64]"))] for case in cases],
                    [[dict(case, classname="Foreign.Test")] for case in cases],
                    [[case] for case in cases] + [[{"classname": security.SPECS["cookie"][0], "name": "acceptedOtherCookie[desktop]"}]])
        for index, groups in enumerate(variants):
            with self.subTest(variant=index):
                self.assertTrue(self.collect(focus, groups=groups)["errors"])

    def test_new_collector_keeps_failure_skip_staleness_marker_and_hardlink_refusals(self):
        focus = "tls-rendering"
        for changed in ({"outcome": "failure"}, {"outcome": "error"}, {"outcome": "skipped"},
                        {"stale": True}, {"markers": 0}, {"markers": 2}, {"hardlink": True}):
            with self.subTest(changed=changed):
                self.assertTrue(self.collect(focus, **changed)["errors"])
        with temporary() as folder:
            root = Path(folder); item = self.reports(root, focus, symlink=True); now = time.time_ns()
            with self.assertRaises(ValueError):
                lt.collect_reports(root, self.plan(), now - 1_000_000_000, now + 1_000_000_000,
                                   Counter({item["task"]: 1}), host_system="Linux")

    def test_bounded_public_listener_models_capture_one_fresh_worker_per_selected_class(self):
        for focus in security.FOCUSES:
            with self.subTest(focus=focus):
                observed = self.observe(focus, self.events(focus))
                expected = len(security.focus_selection(focus)["selected"])
                self.assertEqual(expected, len(observed["selected_class_workers"]))
                self.assertTrue(observed["public_gradle_test_listener_boundaries_verified"])
                self.assertTrue(observed["sequential_workers"])
                self.assertTrue(observed["one_selected_case_per_worker"])
                self.assertFalse(observed["os_worker_pid_observed"])
                self.assertFalse(observed["os_worker_exit_or_sandbox_attested"])

    def test_worker_models_refuse_partial_reused_parallel_reordered_or_foreign_boundaries(self):
        focus = "tls-rendering-cookies-policy-media"; lines = self.events(focus)
        variants = (lines[:-1], lines[1:], lines + [lines[-1]],
                    [*lines[:4], *lines[5:9], lines[4], *lines[9:]],
                    [lines[0], lines[2], lines[1], *lines[3:]],
                    [line.replace("worker=8", "worker=7") for line in lines],
                    [line.replace(security.SPECS["cookie"][0], security.SPECS["tls-rendering"][0]) for line in lines],
                    [line.replace(security.SPECS["cookie"][0], "Foreign.Test") for line in lines])
        for index, changed in enumerate(variants):
            with self.subTest(variant=index), self.assertRaises(ValueError):
                self.observe(focus, changed)

    def test_worker_models_refuse_incomplete_watchdog_counts_unknown_shape_and_log_aliases(self):
        focus = "tls-rendering"; lines = self.events(focus)
        for old, new in (("forks=1", "forks=2"), ("forkEvery=1", "forkEvery=0"),
                         ("tests=1", "tests=0"), ("passed=1", "passed=0"),
                         ("failed=0", "failed=1"), ("skipped=0", "skipped=1"),
                         ("result=SUCCESS", "result=FAILURE"), ("worker=7", "worker=unknown")):
            with self.subTest(new=new), self.assertRaises(ValueError):
                self.observe(focus, [line.replace(old, new) for line in lines])
        with self.assertRaises(ValueError):
            self.observe(focus, [*lines, "NATIVECMPKIT_DESKTOP_SECURITY_UNKNOWN ignored=false"])
        for alias in ("symlink", "hardlink"):
            with self.subTest(alias=alias), temporary() as folder:
                root = Path(folder); target = root / "synthetic-original.log"; target.write_text("\n".join(lines) + "\n")
                log = root / "synthetic-alias.log"
                if alias == "symlink":
                    log.symlink_to(target)
                else:
                    os.link(target, log)
                with self.assertRaises(ValueError):
                    security.worker_observation(log, focus)

    def test_owning_run_pass_gate_rejects_missing_boundaries_and_external_watchdog_stops(self):
        # Entirely synthetic execute/runtime/daemon receipts. No child, Gradle,
        # SDK, TLS, JavaFX, keytool or native UI operation is invoked here.
        for present, stop, expected in ((True, False, True), (False, False, False), (True, True, False)):
            with self.subTest(public_events=present, watchdog=stop), temporary() as folder:
                root = self.source_root(folder)
                def execute(model_root, command, log, timeout, reserve_mib, **kwargs):
                    self.assertEqual(4200, timeout); self.assertEqual(8192, reserve_mib)
                    lines = ["NATIVECMPKIT_TEST_RUNTIME task=:calf-webview:desktopTest gradle=9.7.1"]
                    if present:
                        lines.extend(self.events("tls-rendering"))
                    log.write_text("\n".join(lines) + "\n")
                    self.reports(model_root, "tls-rendering")
                    return {"exit_code": 143 if stop else 0, "elapsed_seconds": 0,
                            **({"stop_reason": "Synthetic owning watchdog stop"} if stop else {})}
                context = {"source_revision": "1" * 40, "source_tree_dirty": False,
                           "host": {"system": "Linux", "architecture": "x86_64"}, "java": {"major": 17}}
                with patch("library_tests.git_revision", return_value="1" * 40), \
                        patch("library_tests.runtime_context.capture", return_value=context), \
                        patch("library_tests.execute", side_effect=execute), \
                        patch("library_tests.daemon_jvm.observation", return_value={"major": 17}), \
                        patch("library_tests.platform.system", return_value="Linux"), \
                        patch("library_tests.platform.machine", return_value="x86_64"):
                    result = lt.run(root, "desktop", "build/ci-verification/explicitly-synthetic-security", None,
                                    4200, 8192, only_modules=("calf-webview",), focus="tls-rendering")
                self.assertIs(expected, result["passed"])
                self.assertEqual(present, "desktop_security_workers" in result)
                if not present:
                    self.assertTrue(any("worker boundaries" in error["error"] for error in result["errors"]))
                if stop:
                    self.assertIn("stop_reason", result["execution"])
                self.assertFalse((root / "build/ci-verification/.library-tests.lock").exists())

    def test_existing_owned_audio_binding_selects_only_linux_arm64_missing_media(self):
        for slot, system, arch, focus, count in ROWS:
            with self.subTest(slot=slot), temporary() as folder, \
                    patch("desktop_media_context.platform.system", return_value=system):
                audio = desktop_media_context.OwnedAudio(Path(folder), Path(folder) / "build/ci-verification/synthetic", self.plan(focus))
                self.assertEqual(slot == "desktop-linux-arm64", audio.requested)
                self.assertIsNone(audio.process)
                self.assertIsNone(audio.environment)
                self.assertIsNone(audio.receipt)

    def test_only_profile_membership_expands_workflow_without_permissions_parallel_or_upload_scope(self):
        workflow = (lt.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn(security.PROFILE, profile_options(workflow))
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertNotIn("packages: write", workflow)
        self.assertNotIn("id-token: write", workflow)
        library = workflow.split("\n  library-tests:\n", 1)[1].split("\n  webview-consumer:\n", 1)[0]
        expression = re.search(r"(?m)^      max-parallel: (.+)$", library).group(1)
        self.assertNotIn(security.PROFILE, expression)
        self.assertTrue(expression.endswith("&& 1 || 2 }}"))
        self.assertEqual(2, security.MAX_PARALLEL)
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        self.assertEqual(["webview-desktop-request-state", "webview-desktop-request-state-stop",
                          "webview-desktop-request-state-stop", "webview-desktop-request-state-stop-redirect",
                          "webview-desktop-request-state-stop"],
                         [row["test-focus"] for row in matrix.matrix("webview-desktop-request-state")["include"]])
        upload = workflow.split("- name: Keep receipts and actual selected-task XML only; never packages", 1)[1].split("\n  webview-consumer:", 1)[0]
        for forbidden in ("*.jar", "*.aar", "*.apk", "*.kexe", "*.app", "*.hprof", "private-cookie"):
            self.assertNotIn(forbidden, upload)


if __name__ == "__main__":
    unittest.main()
