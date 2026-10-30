"""Exact owning WebView application plan guards; no UIKit/compiler executions."""
from collections import Counter
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

import ios_ui_application as app
import library_tests as lt
import workflow_matrix as matrix
import test_ios_application_receipts as fixtures


class IosWebViewLifecycleFocusTests(unittest.TestCase):
    def test_webview_owns_one_finite_real_application_profile(self):
        self.assertIn("ios-webview-lifecycle", matrix.PROFILES,
                      "The current native WebView has no actual UIKit test-app verification profile")
        row, = matrix.matrix("ios-webview-lifecycle")["include"]
        self.assertEqual(("ios-iphone", "calf-webview", lt.IOS_WEBVIEW_LIFECYCLE_FOCUS),
                         tuple(row[k] for k in ("slot", "test-modules", "test-focus")))
        plan = self.plan()
        self.assertFalse(plan["complete_suite_requested"])
        expected, = plan["expected"]
        self.assertEqual(":calf-webview:" + lt.IOS_APPLICATION_TASK, expected["task"])
        self.assertEqual("genuine-uikit-application", expected["native_test_host"])
        self.assertEqual(10, len(expected["required_testcases"]))
        command = lt.gradle_command("ios", plan, simulator=fixtures.DEVICE)
        self.assertEqual(10, command.count("--tests"))
        self.assertNotIn("UIImage", " ".join(command))
        self.assertNotIn("AndroidWebViewHistory", " ".join(command))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))

    def plan(self, root=lt.ROOT):
        return lt.plan(root, "ios", only_modules=("calf-webview",), focus=lt.IOS_WEBVIEW_LIFECYCLE_FOCUS)

    def collect(self, identities=None, outcome="", markers=1, stale=False, duplicate=False):
        plan = self.plan()
        selected = plan["expected"][0]
        identities = lt.ui_application_focus_identities(lt.IOS_WEBVIEW_LIFECYCLE_FOCUS) if identities is None else identities
        xml = "<testsuite>" + "".join(
            f'<testcase classname="{c["classname"]}" name="{c["name"]}">{outcome}</testcase>' for c in identities) + "</testsuite>"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = root / selected["report_directory"]
            reports.mkdir(parents=True)
            path = reports / "TEST-explicitly-synthetic.xml"
            path.write_text(xml)
            if duplicate:
                (reports / "TEST-duplicate.xml").write_text(xml)
            now = time.time_ns()
            if stale:
                import os
                os.utime(path, ns=(now - 20_000_000_000, now - 20_000_000_000))
            return lt.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                      Counter({selected["task"]: markers}), host_system="Darwin")

    def fixture(self):
        f = fixtures.IosApplicationReceipts("test_exact_app_protocol_xml_runtime_binary_and_cleanup_are_required")
        self.addCleanup(f.doCleanups)
        f.setUp()
        f.write("settings.gradle.kts", 'include(\n    ":calf-ui",\n    ":calf-webview",\n)\n')
        f.write("calf-webview/build.gradle.kts", "// synthetic model; never executed")
        for source in {*lt.IOS_WEBVIEW_APPLICATION_SOURCES, *(g["source"] for g in lt.IOS_WEBVIEW_LIFECYCLE_GROUPS)}:
            f.write(source, (lt.ROOT / source).read_bytes())
        directory = app.APPLICATION_HOSTS["calf-webview"]["binary_directory"]
        binary = f.write(directory + "/test.kexe", f.binary.read_bytes())
        binary.chmod(0o700)
        f.plan = self.plan(f.root)
        f.app_root = f.output / "native-webview-application"
        f.receipt_path = f.app_root / fixtures.TOKEN / "receipt.json"
        cases = [{"classname": g["classname"], "name": name, "status": "passed"}
                 for g in lt.IOS_WEBVIEW_LIFECYCLE_GROUPS for name in g["methods"]]
        f.document.update(task=":calf-webview:" + lt.IOS_APPLICATION_TASK,
                          explicit_test_focus=lt.IOS_WEBVIEW_LIFECYCLE_FOCUS,
                          binary_path=binary.relative_to(f.root).as_posix(), binary_sha256=lt.sha256(binary),
                          binary_sha256_after=lt.sha256(binary), macho=app.macho_simulator_identity(binary))
        f.document["application_protocol"].update(testcases=cases, counts=lt.case_counts(cases))
        f.document["application_protocol"].pop("image_lifetime_observation", None)
        f.modules = [{"module": "calf-webview", "task": ":calf-webview:" + lt.IOS_APPLICATION_TASK,
                      "testcases": f.xml_cases(cases)}]
        f.save()
        return f

    def test_real_cli_transports_exact_native_identities_without_a_publish_task(self):
        command = [lt.sys.executable, "-B", str(lt.ROOT / "scripts/ci/library_tests.py"), "plan", "--suite", "ios",
                   "--module", "calf-webview", "--focus", lt.IOS_WEBVIEW_LIFECYCLE_FOCUS]
        result = subprocess.run(command, capture_output=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(self.plan(), json.loads(result.stdout))
        filters = lt.ui_application_focus_filter(lt.IOS_WEBVIEW_LIFECYCLE_FOCUS).split(",")
        for selected in (filters, list(reversed(filters))):
            self.assertEqual(lt.IOS_WEBVIEW_LIFECYCLE_FOCUS, app.application_test_focus(
                sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + ",".join(selected)]))
        for invalid in (filters[:-1], filters + filters[:1], ["*"]):
            with self.assertRaises(ValueError):
                app.application_test_focus(sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + ",".join(invalid)])
        self.assertNotIn("publish", " ".join(lt.gradle_command("ios", self.plan(), simulator=fixtures.DEVICE)))

    def test_other_suites_owner_modules_and_unknown_binary_paths_are_rejected(self):
        for suite, modules in (("desktop", ("calf-webview",)), ("ios", ("calf-ui",)),
                               ("ios", ("calf-file-picker",)), ("ios", None), ("android-device", ("calf-webview",))):
            with self.assertRaises(ValueError):
                lt.plan(lt.ROOT, suite, only_modules=modules, focus=lt.IOS_WEBVIEW_LIFECYCLE_FOCUS)
        path = app.APPLICATION_HOSTS["calf-webview"]["binary_directory"] + "/test.kexe"
        self.assertEqual("calf-webview", app.application_host(path, lt.IOS_WEBVIEW_LIFECYCLE_FOCUS)["module"])
        for changed, focus in ((path.replace("calf-webview", "calf-ui"), lt.IOS_WEBVIEW_LIFECYCLE_FOCUS),
                               (path, lt.IOS_IMAGE_MEMORY_FOCUS), (path.replace("applicationDebugTest", "debugTest"), None)):
            with self.assertRaises(ValueError): app.application_host(changed, focus)

    def test_every_native_host_is_retained_and_full_webview_uses_its_own_application(self):
        for module in ("calf-ui", "calf-file-picker", "calf-webview"):
            plan = lt.plan(lt.ROOT, "ios", only_modules=(module,))
            self.assertFalse(plan["complete_suite_requested"], "One selected module is not the complete all-module suite")
            self.assertNotIn("test_filter", plan["expected"][0])
            self.assertEqual(":" + module + ":" + lt.IOS_APPLICATION_TASK, plan["expected"][0]["task"])
        image = lt.plan(lt.ROOT, "ios", only_modules=("calf-ui",), focus=lt.IOS_IMAGE_MEMORY_FOCUS)
        self.assertEqual(3, len(image["expected"][0]["required_testcases"]))
        self.assertEqual(360, app.application_timeout_seconds(lt.IOS_IMAGE_MEMORY_FOCUS))
        self.assertEqual(app.APP_TIMEOUT_SECONDS, app.application_timeout_seconds(lt.IOS_WEBVIEW_LIFECYCLE_FOCUS))

    def test_fresh_exact_nonzero_xml_required_and_missing_stale_extra_failed_or_skipped_is_red(self):
        result = self.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual(10, result["totals"]["passed"])
        cases = lt.ui_application_focus_identities(lt.IOS_WEBVIEW_LIFECYCLE_FOCUS)
        for changed in ({"identities": []}, {"identities": cases[:-1]}, {"identities": cases + cases[:1]},
                        {"outcome": "<failure/>"}, {"outcome": "<error/>"}, {"outcome": "<skipped/>"},
                        {"stale": True}, {"duplicate": True}, {"markers": 0}, {"markers": 2}):
            with self.subTest(changed=changed): self.assertTrue(self.collect(**changed)["errors"])

    def test_missing_hosts_ignored_or_extra_declarations_cannot_shrink_the_native_plan(self):
        f = self.fixture()
        self.assertTrue(lt.validate_test_focus(self.plan(f.root)))
        source = f.root / lt.IOS_WEBVIEW_LIFECYCLE_SOURCE
        original = source.read_text()
        for changed in (original.replace("@Test", "@IgnoredTest", 1),
                        original.replace(lt.IOS_WEBVIEW_LIFECYCLE_METHODS[0], "wrongMethod", 1),
                        original + "\n@Test fun extra() {}\n"):
            source.write_text(changed)
            with self.assertRaises(ValueError): self.plan(f.root)
        source.write_text(original)
        (f.root / lt.IOS_WEBVIEW_APPLICATION_SOURCES[0]).unlink()
        with self.assertRaises(ValueError): self.plan(f.root)

    def test_complete_protocol_xml_binary_runtime_and_cleanup_required_for_this_owner(self):
        f = self.fixture()
        result = f.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual(10, result["ios_applications"][0]["required_native_cases_found"])
        original = copy.deepcopy(f.document)
        for change in (
            lambda d: d.update(task=app.TASK),
            lambda d: d.update(explicit_test_focus=lt.IOS_IMAGE_MEMORY_FOCUS),
            lambda d: d.update(transport_passed=False),
            lambda d: d.update(binary_sha256_after="f" * 64),
            lambda d: d["runtime_after"].update(source_revision="f" * 40),
            lambda d: d["application_protocol"].update(completion={"runner_exit": 0, "worker_terminated": False}),
            lambda d: d["cleanup"].update(owned_app_absence_verified=False),
            lambda d: d["steps"]["install-owned-app"].update(installed_owned_bytes_verified=False),
        ):
            f.document = copy.deepcopy(original); change(f.document); f.save()
            self.assertTrue(f.collect()["errors"])

    def test_unfiltered_webview_still_requires_every_owning_host_and_native_method(self):
        f = self.fixture()
        f.plan = lt.plan(f.root, "ios", only_modules=("calf-webview",))
        f.document["explicit_test_focus"] = None
        f.save()
        result = f.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual(10, result["ios_applications"][0]["required_native_cases_found"])
        f.document["application_protocol"]["testcases"] = f.document["application_protocol"]["testcases"][1:]
        f.document["application_protocol"]["counts"] = lt.case_counts(f.document["application_protocol"]["testcases"])
        f.modules[0]["testcases"] = f.xml_cases(f.document["application_protocol"]["testcases"])
        f.save()
        self.assertTrue(f.collect()["errors"], "An unfiltered module run must not lose a required native-host test")

    def test_wrong_task_full_suite_claim_filter_or_required_case_inventory_is_rejected(self):
        for key, value in (("task", ":calf-webview:publish"), ("test_filter", "*"), ("required_testcases", []),
                           ("native_test_host", "command-line"), ("test_source_files", [])):
            plan = self.plan(); plan["expected"][0][key] = value
            with self.assertRaises(ValueError): lt.validate_test_focus(plan)
        plan = self.plan(); plan["complete_suite_requested"] = True
        with self.assertRaises(ValueError): lt.validate_test_focus(plan)

    def test_host_preserves_the_accepted_worker_native_identity_and_every_cleanup_statement(self):
        replacements = (("package com.mohamedrejeb.calf.ui.internal", "package com.mohamedrejeb.calf.ui.web.internal"),
                        ("NativeUiApplicationDelegate", "NativeWebViewApplicationDelegate"),
                        ("NativeUiApplicationHostTest", "NativeWebViewApplicationHostTest"),
                        ("NativecmpkitUIKitLibraryTestDelegate", "NativecmpkitWebViewLibraryTestDelegate"))
        for original, target in (("NativeUiApplicationHost.kt", lt.IOS_WEBVIEW_APPLICATION_SOURCES[0]),
                                 ("NativeUiApplicationHostTest.kt", lt.IOS_WEBVIEW_APPLICATION_SOURCES[1]),
                                 ("NativeObjectIdentity.kt", lt.IOS_WEBVIEW_APPLICATION_SOURCES[2])):
            source = (lt.ROOT / "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal" / original).read_text()
            for old, new in replacements: source = source.replace(old, new)
            actual = (lt.ROOT / target).read_text()
            self.assertEqual(source, actual.split("\n", 2)[2])

    def test_native_tests_use_actual_webkit_and_do_not_claim_video_swipe_or_network_execution(self):
        source = (lt.ROOT / lt.IOS_WEBVIEW_LIFECYCLE_SOURCE).read_text()
        self.assertEqual(6, source.count("@Test"))
        for required in ("evaluateJavascriptResult", "assertTrue(NSThread.isMainThread)", "assertFalse(NSThread.isMainThread",
                         "view.configuration", "navigationDelegate", "assertNull(firstView.superview)",
                         "waitForNative", "allowsBackForwardNavigationGestures", "encoding = \"utf-16\"",
                         "stateAndNavigatorUnicodeHtml", "physical-device", "No video playback"):
            self.assertIn(required, source)
        self.assertNotIn("override fun webView", source)  # Never inject delegate completions as engine results.
        self.assertNotIn("Mock", source)
        self.assertNotIn("override fun evaluateJavaScript", source)

    def test_workflow_is_one_read_only_host_and_reports_only_native_output(self):
        workflow = (lt.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn("ios-webview-lifecycle", workflow)
        self.assertIn("build/ci-verification/${{ matrix.slot }}/native-webview-application/*/receipt.json", workflow)
        self.assertNotIn("native-webview-application/**", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        build = (lt.ROOT / "calf-webview/build.gradle.kts").read_text()
        for required in ("binaries.test(\"application\"", "com.mohamedrejeb.calf.ui.web.internal.nativeApplicationMain",
                         "ignoreFailures = false", "ignoreRunFailures = false", "outputs.upToDateWhen { false }",
                         "outputs.doNotCacheIf", "reports.junitXml.required.set(true)"):
            self.assertIn(required, build)
        self.assertNotIn("binaryOption(", build)  # No public framework sanitizer/runtime changes.


if __name__ == "__main__": unittest.main()
