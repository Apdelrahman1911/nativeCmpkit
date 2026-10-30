"""Owning native-identity guards; synthetic tooling, never an Apple runtime pass."""
from collections import Counter
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

import ios_ui_application as app
import library_tests as lt
import workflow_matrix as matrix
import test_ios_application_receipts as runtime_fixture
import test_ios_webview_lifecycle_focus as webview_fixture


class IosWebViewNativeIdentityTests(unittest.TestCase):
    def test_native_callbacks_match_the_retained_objc_owner_not_a_kotlin_wrapper(self):
        source = (lt.ROOT / "calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt").read_text()
        self.assertIn("hasSameNativeWebView", source,
                      "KVO/delegate ownership cannot depend on referential equality of Objective-C wrappers")
        self.assertNotIn("this.webView !== webView", source)
        self.assertNotIn("state.webView !== webView", source)
        self.assertNotIn("webView !== view", source)

    def plan(self, root=lt.ROOT):
        return lt.plan(root, "ios", only_modules=("calf-webview",), focus=lt.IOS_WEBVIEW_RECOVERY_FOCUS)

    def test_identity_compares_live_native_pointers_and_nulls_never_form_a_lease(self):
        source = (lt.ROOT / "calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/NativeWebViewIdentity.ios.kt").read_text()
        self.assertIn("first != null && second != null && first.objcPtr() == second.objcPtr()", source)
        self.assertNotIn("first == second", source)
        self.assertNotIn("first === second", source)
        self.assertIn("internal fun hasSameNativeWebView", source)

    def test_recovery_runs_six_failed_cases_and_one_new_bridge_case_not_four_accepted_hosts(self):
        row, = matrix.matrix("ios-webview-recovery")["include"]
        self.assertEqual(("ios-iphone", "calf-webview", lt.IOS_WEBVIEW_RECOVERY_FOCUS),
                         tuple(row[k] for k in ("slot", "test-modules", "test-focus")))
        plan = self.plan()
        selected, = plan["expected"]
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(7, len(selected["required_testcases"]))
        self.assertEqual({lt.IOS_WEBVIEW_BRIDGE_METHOD, *lt.IOS_WEBVIEW_LIFECYCLE_METHODS},
                         {x["name"].split("[")[0] for x in selected["required_testcases"]})
        self.assertNotIn("NativeWebViewApplicationHostTest", selected["test_filter"])
        command = lt.gradle_command("ios", plan, simulator=runtime_fixture.DEVICE)
        self.assertEqual(7, command.count("--tests"))
        self.assertEqual(":calf-webview:" + lt.IOS_APPLICATION_TASK, selected["task"])
        self.assertEqual(11, len(matrix.matrix("all")["include"]))

    def test_original_ten_case_profile_and_unfiltered_eleven_case_contract_are_retained(self):
        original = lt.plan(lt.ROOT, "ios", only_modules=("calf-webview",), focus=lt.IOS_WEBVIEW_LIFECYCLE_FOCUS)
        self.assertEqual(10, len(original["expected"][0]["required_testcases"]))
        full = lt.plan(lt.ROOT, "ios", only_modules=("calf-webview",))
        self.assertNotIn("test_filter", full["expected"][0])
        self.assertEqual(11, sum(len(g["methods"]) for g in lt.IOS_WEBVIEW_APPLICATION_REQUIRED_GROUPS))
        self.assertNotIn("publish", " ".join(lt.gradle_command("ios", self.plan(), simulator=runtime_fixture.DEVICE)))

    def test_real_cli_transports_exact_recovery_and_native_registry_identities(self):
        command = [lt.sys.executable, "-B", str(lt.ROOT / "scripts/ci/library_tests.py"), "plan", "--suite", "ios",
                   "--module", "calf-webview", "--focus", lt.IOS_WEBVIEW_RECOVERY_FOCUS]
        result = subprocess.run(command, capture_output=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(self.plan(), json.loads(result.stdout))
        selectors = lt.ui_application_focus_filter(lt.IOS_WEBVIEW_RECOVERY_FOCUS).split(",")
        self.assertEqual(lt.IOS_WEBVIEW_RECOVERY_FOCUS, app.application_test_focus(
            sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + ",".join(selectors)]))
        for changed in (selectors[:-1], selectors + selectors[:1], ["*"]):
            with self.assertRaises(ValueError):
                app.application_test_focus(sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + ",".join(changed)])

    def test_unrelated_suites_owners_or_changed_filter_task_inventory_cannot_use_recovery(self):
        for suite, modules in (("ios", ("calf-ui",)), ("ios", None), ("desktop", ("calf-webview",)),
                               ("android-device", ("calf-webview",)), ("js", ("calf-webview",))):
            with self.assertRaises(ValueError): lt.plan(lt.ROOT, suite, only_modules=modules, focus=lt.IOS_WEBVIEW_RECOVERY_FOCUS)
        for key, value in (("task", ":calf-webview:publish"), ("test_filter", "*"), ("required_testcases", [])):
            plan = self.plan(); plan["expected"][0][key] = value
            with self.assertRaises(ValueError): lt.validate_test_focus(plan)

    def collect(self, cases=None, outcome="", markers=1, stale=False, duplicate=False):
        plan = self.plan()
        selected, = plan["expected"]
        cases = selected["required_testcases"] if cases is None else cases
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); folder = root / selected["report_directory"]; folder.mkdir(parents=True)
            payload = "<testsuite>" + "".join(
                f'<testcase classname="{c["classname"]}" name="{c["name"]}">{outcome}</testcase>' for c in cases) + "</testsuite>"
            path = folder / "TEST-explicitly-synthetic.xml"; path.write_text(payload)
            if duplicate: (folder / "TEST-duplicate.xml").write_text(payload)
            now = time.time_ns()
            if stale: os.utime(path, ns=(now - 20_000_000_000, now - 20_000_000_000))
            return lt.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                      Counter({selected["task"]: markers}), host_system="Darwin")

    def test_exact_nonzero_fresh_seven_case_xml_not_missing_duplicate_skipped_or_stale_is_required(self):
        result = self.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual(7, result["totals"]["passed"])
        cases = self.plan()["expected"][0]["required_testcases"]
        for invalid in ({"cases": []}, {"cases": cases[:-1]}, {"cases": cases + cases[:1]},
                        {"outcome": "<failure/>"}, {"outcome": "<error/>"}, {"outcome": "<skipped/>"},
                        {"stale": True}, {"duplicate": True}, {"markers": 0}, {"markers": 2}):
            with self.subTest(invalid=invalid): self.assertTrue(self.collect(**invalid)["errors"])

    def fixture(self):
        parent = webview_fixture.IosWebViewLifecycleFocusTests("test_complete_protocol_xml_binary_runtime_and_cleanup_required_for_this_owner")
        self.addCleanup(parent.doCleanups)
        f = parent.fixture()
        f.plan = self.plan(f.root)
        cases = [{"classname": lt.IOS_WEBVIEW_LIFECYCLE_CLASS, "name": name, "status": "passed"}
                 for name in lt.IOS_WEBVIEW_LIFECYCLE_DECLARATIONS]
        f.document["explicit_test_focus"] = lt.IOS_WEBVIEW_RECOVERY_FOCUS
        f.document["application_protocol"].update(testcases=cases, counts=lt.case_counts(cases))
        f.modules[0]["testcases"] = f.xml_cases(cases)
        f.save()
        return f

    def test_actual_transport_contract_still_requires_worker_runtime_binary_install_and_owned_cleanup(self):
        f = self.fixture()
        result = f.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual(7, result["ios_applications"][0]["required_native_cases_found"])
        original = copy.deepcopy(f.document)
        for change in (lambda d: d.update(transport_passed=False),
                       lambda d: d.update(binary_sha256_after="f" * 64),
                       lambda d: d["runtime_after"].update(source_revision="f" * 40),
                       lambda d: d["application_protocol"].update(completion={"runner_exit": 0, "worker_terminated": False}),
                       lambda d: d["cleanup"].update(owned_app_absence_verified=False),
                       lambda d: d["steps"]["install-owned-app"].update(installed_owned_bytes_verified=False)):
            f.document = copy.deepcopy(original); change(f.document); f.save()
            self.assertTrue(f.collect()["errors"])

    def test_readiness_preserves_native_title_state_title_loading_window_and_original_timeout(self):
        source = (lt.ROOT / lt.IOS_WEBVIEW_LIFECYCLE_SOURCE).read_text()
        self.assertIn("view.title == title && state.pageTitle == title", source)
        self.assertIn("!view.loading && state.loadingState == LoadingState.Finished", source)
        self.assertIn("sameNativeObject(view.window, requireOwnedApplicationWindow())", source)
        self.assertIn("throw IllegalStateException(\"Real WebKit readiness failed: $observed\", failure)", source)
        self.assertIn("parent.subviews.filterIsInstance<WKWebView>()", source)
        self.assertIn("state.webView(foreign, didFinishNavigation = null)", source)
        self.assertIn("state.webView(bridged, didFinishNavigation = null)", source)
        host = (lt.ROOT / lt.IOS_WEBVIEW_APPLICATION_SOURCES[0]).read_text()
        self.assertIn("systemUptime + 10.0", host)

    def test_four_previously_accepted_host_methods_and_helpers_are_byte_identical(self):
        revision = "16c9a53026cb087f359a45bcfbbe4d56c1473243"
        for path in lt.IOS_WEBVIEW_APPLICATION_SOURCES:
            original = subprocess.check_output(["git", "show", revision + ":" + path], cwd=lt.ROOT)
            self.assertEqual(original, (lt.ROOT / path).read_bytes())


if __name__ == "__main__":
    unittest.main()
