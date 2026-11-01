"""New finite WK DNS tooling/source guards; synthetic models, not DNS/native proof.

No model resolves a name, prepares a listener or executes SDK/Gradle/UIKit. Actual
acceptance still requires the source-bound one-method application XML and every
native -1003/provisional/retained-document/owned-cleanup assertion. .invalid uses
the existing runner resolver; no deterministic/controlled resolver is claimed.
"""
from collections import Counter
import copy
import io
import json
import os
from pathlib import Path
import re
import tempfile
import time
import unittest
from unittest.mock import patch

import ios_ui_application as app
import library_tests as lt
import workflow_matrix as matrix
import test_ios_application_receipts as runtime_fixture
import test_ios_webview_lifecycle_focus as lifecycle_fixture
from test_ios_io_profile import profile_options

PROFILE = "ios-webview-provisional-dns"
FOCUS = "webview-ios-native-provisional-dns"
CLASS = "com.mohamedrejeb.calf.ui.web.IosWebViewProvisionalDnsAcceptanceTest"
METHOD = "nativeProvisionalDnsFailFailResetsPreviousErrorBeforeCommitOnSameDocument"
SOURCE = "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosWebViewProvisionalDnsAcceptanceTest.kt"


class IosWebViewDnsFocusTests(unittest.TestCase):
    def plan(self, root=lt.ROOT):
        return lt.plan(root, "ios", only_modules=("calf-webview",), focus=FOCUS)

    def test_new_dns_profile_is_one_additive_genuine_application_selection(self):
        self.assertIn(PROFILE, matrix.PROFILES,
                      "There is no finite genuine DNS selection for original NATIVE-005 criterion three")
        options = profile_options((lt.ROOT / ".github/workflows/gradle.yml").read_text())
        self.assertEqual(set(matrix.PROFILES), set(options))
        self.assertEqual(1, options.count(PROFILE))
        self.assertEqual({PROFILE, "ios-webview-request-dns"}, {name for name in matrix.PROFILES if "dns" in name})
        row, = matrix.matrix(PROFILE)["include"]
        self.assertEqual(("ios-iphone", "ios", "calf-webview", FOCUS),
            tuple(row[k] for k in ("slot", "suite", "test-modules", "test-focus")))
        self.assertNotIn("serial-test-focus", row)
        self.assertNotIn("android-batch", row)
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        for name in ("all", "apple", "ios", "core", "browser"):
            self.assertTrue(all("test-focus" not in item for item in matrix.matrix(name)["include"]))
        for name in ("android-io-permission-storage-api35", "android-permission-storage-compatibility",
                     "android-camera-restoration-dont-keep"):
            self.assertNotEqual(FOCUS, matrix.matrix(name)["include"][0].get("test-focus"))
        selected, = self.plan()["expected"]
        self.assertEqual(1, len(selected["required_testcases"]))
        self.assertEqual("genuine-uikit-application", selected["native_test_host"])
        self.assertEqual(":" + "calf-webview:" + lt.IOS_APPLICATION_TASK, selected["task"])
        self.assertIn(SOURCE, selected["test_source_files"])
        self.assertNotIn("ios_webview_request_fixture", selected)
        self.assertIsNone(app.profile_debug_entitlements(FOCUS))
        self.assertEqual(app.APP_TIMEOUT_SECONDS, app.application_timeout_seconds(FOCUS))
        workflow = (lt.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("native-webview-application/*/receipt.json", workflow)
        self.assertNotIn("native-webview-application/**", workflow)

    def test_real_generic_plan_cli_filter_and_application_router_cannot_broaden_dns(self):
        plan = self.plan()
        selected, = plan["expected"]
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(["calf-webview"], plan["explicit_module_subset"])
        expected = [{"classname": "iosSimulatorArm64ApplicationTest." + CLASS,
                     "name": METHOD + "[iosSimulatorArm64]"}]
        self.assertEqual(expected, selected["required_testcases"])
        self.assertTrue(lt.validate_test_focus(plan))
        self.assertEqual(CLASS + "." + METHOD, selected["test_filter"])
        command = lt.gradle_command("ios", plan, simulator=runtime_fixture.DEVICE)
        self.assertEqual(1, command.count("--tests"))
        self.assertNotIn("publish", " ".join(command))
        self.assertNotIn(lt.IOS_WEBVIEW_REQUEST_CLASS, selected["test_filter"])
        arguments = sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + selected["test_filter"]]
        self.assertEqual(FOCUS, app.application_test_focus(arguments))
        binary = app.APPLICATION_HOSTS["calf-webview"]["binary_directory"] + "/test.kexe"
        self.assertEqual("calf-webview", app.application_host(binary, FOCUS)["module"])
        for patterns in ("*", CLASS + ".wrongMethod", selected["test_filter"] + "," + selected["test_filter"],
                         lt.ui_application_focus_filter(lt.IOS_WEBVIEW_REQUEST_FOCUS).split(",")[0] + "," + selected["test_filter"]):
            with self.assertRaises(ValueError):
                app.application_test_focus(sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + patterns])
        for suite, modules in (("desktop", ("calf-webview",)), ("js", ("calf-webview",)),
                               ("android-device", ("calf-webview",)), ("ios", ("calf-ui",)),
                               ("ios", ("calf-file-picker",)), ("ios", None)):
            with self.assertRaises(ValueError): lt.plan(lt.ROOT, suite, only_modules=modules, focus=FOCUS)
        for key, value in (("test_filter", "*"), ("required_testcases", []), ("native_test_host", "command-line"),
                           ("task", ":calf-webview:publish"), ("test_source_files", [])):
            invalid = copy.deepcopy(plan)
            invalid["expected"][0][key] = value
            with self.assertRaises(ValueError): lt.validate_test_focus(invalid)
        invalid = copy.deepcopy(plan); invalid["complete_suite_requested"] = True
        with self.assertRaises(ValueError): lt.validate_test_focus(invalid)
        stream = io.StringIO()
        with patch("sys.argv", ["library_tests.py", "plan", "--suite", "ios", "--module", "calf-webview", "--focus", FOCUS]), \
             patch("sys.stdout", stream):
            self.assertEqual(0, lt.main()) # In-process read-only parser, never subprocess/preflight/run.
        self.assertEqual(plan, json.loads(stream.getvalue()))

    def test_native_dns_requires_real_consecutive_links_actual_minus1003_and_zero_commit(self):
        source = (lt.ROOT / SOURCE).read_text()
        self.assertEqual([METHOD], re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", source))
        self.assertIn('NSUUID().UUIDString.replace("-", "").lowercase()', source)
        self.assertIn("https://dns-one-$nonce.nativecmpkit.invalid/", source)
        self.assertIn("https://dns-two-$nonce.nativecmpkit.invalid/", source)
        self.assertIn("for (index in targets.indices)", source)
        self.assertIn("document.getElementById('${ids[index]}').click(); 1", source)
        self.assertIn("attempt.beforeStart == attempt.priorErrors", source)
        self.assertIn("attempt.afterStart?.isEmpty() == true && attempt.startResetBeforeCommit", source)
        self.assertIn("attempt.beforeFailure?.isEmpty() == true", source)
        self.assertIn("error.domain == NSURLErrorDomain", source)
        self.assertIn("error.code == NSURLErrorCannotFindHost && error.code == -1003L", source)
        self.assertIn("publicError.code == -1003 && publicError.description == error.localizedDescription", source)
        self.assertIn("assertEquals(0, attempt.commits); assertEquals(0, attempt.finishes); assertEquals(0, attempt.committedFailures)", source)
        self.assertIn("it.sameFailureNavigation = sameNativeObject(it.navigation, didFailProvisionalNavigation)", source)
        self.assertIn("sameNativeObject(attempts[0].navigation, attempts[1].navigation)", source)
        self.assertIn("owner.requestedUrl == it.target", source)
        self.assertIn("owner.lastLoadedUrl == null && owner.pageTitle.isNullOrEmpty()", source)
        self.assertIn("document.URL", source)
        self.assertIn("evaluate(state, documentScript) == retainedDocument", source)
        self.assertIn("waitForNative { lease.hasFault || (lease.hasTerminalCallback && !native.loading) }", source)
        for forbidden in ("NSError(", "NSError.error", "state.content =", "navigator.loadUrl(", "navigator.loadHtml(",
                          "loadRequest(", "NSURLProtocol", "setURLSchemeHandler", "NSAllowsArbitraryLoads",
                          "SecTrust", "didReceiveAuthenticationChallenge", "Thread.sleep", "usleep", "stopLoading(",
                          "NSURLConnection", "NSProcessInfo", "NSHost", "getaddrinfo", "/etc/hosts"):
            self.assertNotIn(forbidden, source)
        self.assertNotRegex(source, r"(?:owner|state)\.(?:loadingState|requestedUrl|lastLoadedUrl|pageTitle|webView|nativeObserver|navigator|errorsForCurrentRequest)\s*=(?!=)")
        host = (lt.ROOT / lt.IOS_WEBVIEW_APPLICATION_SOURCES[0]).read_text()
        self.assertIn("NSProcessInfo.processInfo.systemUptime + 10.0", host)

    def test_forwarder_is_normal_framework_only_strong_owned_and_restored_before_genuine_release(self):
        source = (lt.ROOT / SOURCE).read_text()
        callbacks = ("didStartProvisionalNavigation", "didCommitNavigation", "didFinishNavigation",
                     "didFailNavigation", "didFailProvisionalNavigation")
        self.assertEqual(5, source.count("@ObjCSignatureOverride"))
        self.assertEqual(5, source.count("override fun webView("))
        self.assertEqual(5, source.count("originalDelegate.webView("))
        for selector in callbacks:
            self.assertEqual(1, source.count("originalDelegate.webView(webView, " + selector + " = " + selector))
        self.assertIn("it.error = withError", source)
        self.assertIn("withError = withError", source)
        self.assertIn("sameNativeObject(view.navigationDelegate as? NSObject, this)", source)
        self.assertIn("sameNativeObject(owner.nativeObserver, observer)", source)
        self.assertIn("sameNativeObject(owner.webView, native)", source)
        self.assertIn("sameNativeObject(view.window, window) && view.superview != null", source)
        self.assertIn("private val originalDelegate: WebViewState", source)
        self.assertIn("val lease = runOnIdle { DnsForwarder.acquire", source)
        self.assertIn("native.navigationDelegate = originalDelegate", source)
        self.assertIn("assertTrue(owns(native), \"Refuse restoring a foreign", source)
        self.assertIn("onApplicationMain { lease.restore() }", source)
        self.assertIn("prior.addSuppressed(cleanup)", source)
        self.assertIn("runApplicationUiTest {", source)
        self.assertIn("assertNull(released.navigationDelegate); assertNull(released.superview); assertNull(released.window)", source)
        self.assertIn("assertNull(state.webView); assertNull(state.nativeObserver); assertNull(state.navigator)", source)
        forward = source[source.index("private fun forward("):source.index('@Suppress("PARAMETER_NAME_CHANGED_ON_OVERRIDE")')]
        self.assertNotRegex(forward, r"\b(?:assert[A-Z]\w*|check|require|error)\s*\(|\bthrow\s+[A-Za-z]")
        self.assertIn("catch (_: Throwable) { noteFault(CallbackFault.ForwardedCallbackFailed) }", forward)
        overrides = source[source.index('@Suppress("PARAMETER_NAME_CHANGED_ON_OVERRIDE")'):source.index("companion object {")]
        self.assertNotRegex(overrides, r"\b(?:assert[A-Z]\w*|check|require|error|throw)\s*\(")
        self.assertNotIn(".webView(", source[:source.index('@Suppress("PARAMETER_NAME_CHANGED_ON_OVERRIDE")')])
        host = (lt.ROOT / lt.IOS_WEBVIEW_APPLICATION_SOURCES[0]).read_text()
        self.assertIn("ownedInteropViews.all { it.superview == null && it.window == null && it.navigationDelegate == null }", host)
        self.assertIn("try { host.close() } catch (cleanup: Throwable)", host)
        self.assertIn("prior.addSuppressed(cleanup)", host)

    def collect_xml(self, *, cases=None, outcome="", markers=1, stale=False, duplicate=False):
        plan = self.plan()
        selected, = plan["expected"]
        cases = selected["required_testcases"] if cases is None else cases
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); reports = root / selected["report_directory"]; reports.mkdir(parents=True)
            xml = "<testsuite>" + "".join(
                f'<testcase classname="{case["classname"]}" name="{case["name"]}">{outcome}</testcase>'
                for case in cases) + "</testsuite>"
            path = reports / "TEST-explicitly-synthetic.xml"; path.write_text(xml)
            if duplicate: (reports / "TEST-duplicate.xml").write_text(xml)
            now = time.time_ns()
            if stale: os.utime(path, ns=(now - 20_000_000_000, now - 20_000_000_000))
            return lt.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                      Counter({selected["task"]: markers}), host_system="Darwin")

    def test_dns_requires_one_exact_fresh_passed_xml_not_tls_replay_skip_timeout_or_duplicates(self):
        result = self.collect_xml()
        self.assertEqual([], result["errors"])
        self.assertEqual(1, result["totals"]["passed"])
        expected = self.plan()["expected"][0]["required_testcases"]
        for invalid in ({"cases": []}, {"cases": expected + expected},
                        {"cases": lt.ui_application_focus_identities(lt.IOS_WEBVIEW_REQUEST_FOCUS)[:1]},
                        {"outcome": '<failure message="Explicitly synthetic timeout; not DNS acceptance"/>'},
                        {"outcome": '<failure message="Explicitly synthetic offline -1009; not DNS acceptance"/>'},
                        {"outcome": '<failure message="Explicitly synthetic TLS -1200; not DNS acceptance"/>'},
                        {"outcome": "<error/>"}, {"outcome": "<skipped/>"}, {"stale": True},
                        {"duplicate": True}, {"markers": 0}, {"markers": 2}):
            with self.subTest(invalid=invalid): self.assertTrue(self.collect_xml(**invalid)["errors"])

    def fixture(self):
        parent = lifecycle_fixture.IosWebViewLifecycleFocusTests(
            "test_complete_protocol_xml_binary_runtime_and_cleanup_required_for_this_owner")
        self.addCleanup(parent.doCleanups)
        fixture = parent.fixture() # Helpers only; no accepted test method is invoked.
        fixture.plan = self.plan(fixture.root)
        cases = [{"classname": CLASS, "name": METHOD, "status": "passed"}]
        fixture.document["explicit_test_focus"] = FOCUS
        fixture.document["application_protocol"].update(testcases=cases, counts=lt.case_counts(cases))
        fixture.modules[0]["testcases"] = fixture.xml_cases(cases)
        fixture.document.pop("webview_request_fixture", None)
        fixture.save()
        return fixture

    def test_one_dns_application_keeps_actual_worker_signer_install_xml_and_owned_cleanup_gates(self):
        fixture = self.fixture()
        result = fixture.collect()
        self.assertEqual([], result["errors"], result["errors"])
        self.assertEqual(1, result["ios_applications"][0]["required_native_cases_found"])
        self.assertNotIn("webview_request_fixture", fixture.document)
        original = copy.deepcopy(fixture.document)
        for change in (
            lambda d: d.update(explicit_test_focus=lt.IOS_WEBVIEW_REQUEST_FOCUS),
            lambda d: d.update(task=":calf-webview:iosSimulatorArm64Test"),
            lambda d: d.update(binary_sha256_after="e" * 64),
            lambda d: d["steps"]["adhoc-sign-local-verification-app"].update(exit_code=1),
            lambda d: d["steps"]["install-owned-app"].update(installed_owned_bytes_verified=False),
            lambda d: d["application_protocol"]["activation"].update(owned_worker=1),
            lambda d: d["application_protocol"]["completion"].update(worker_terminated=False),
            lambda d: d["application_protocol"].update(process_exit=9),
            lambda d: d["runtime_after"].update(apple_sdks={"iphonesimulator": "25.0"}),
            lambda d: d["cleanup"].update(owned_app_identity_reverified=False),
            lambda d: d["cleanup"].update(owned_app_stopped_verified=False),
            lambda d: d["cleanup"].update(uninstall_exit_code=1),
            lambda d: d["cleanup"].update(owned_app_absence_verified=False),
            lambda d: d["cleanup"].update(owned_local_bundle_removed=False),
            lambda d: d.update(application_protocol_partial={}),
        ):
            with self.subTest(change=change):
                fixture.document = copy.deepcopy(original); change(fixture.document); fixture.save()
                self.assertTrue(fixture.collect()["errors"])
        fixture.document = copy.deepcopy(original)
        fixture.document["application_protocol"]["testcases"] = [
            {"classname": lt.IOS_WEBVIEW_REQUEST_CLASS, "name": lt.IOS_WEBVIEW_REQUEST_METHODS[0], "status": "passed"}]
        fixture.document["application_protocol"]["counts"] = lt.case_counts(fixture.document["application_protocol"]["testcases"])
        fixture.modules[0]["testcases"] = fixture.xml_cases(fixture.document["application_protocol"]["testcases"])
        fixture.save()
        self.assertTrue(fixture.collect()["errors"], "A previous genuine TLS method cannot substitute for DNS")
