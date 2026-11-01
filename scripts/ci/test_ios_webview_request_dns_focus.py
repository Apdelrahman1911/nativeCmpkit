"""Finite request2 + DNS1 application routing models, never WK/DNS/TLS proof.

Every control, SDK/Mach-O, console frame, plist and transport receipt is explicitly
synthetic. No real listener, resolver, SDK, signing, process or native test is run.
One source-bound real UIApplication/KGP request with all three original methods
and actual receipt/XML/owned-cleanup review is still required for acceptance.
"""
from collections import Counter
import copy
import io
import itertools
import json
import os
from pathlib import Path
import plistlib
import re
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import ios_ui_application as app
import ios_webview_request_fixture as requests
import library_tests as lt
import workflow_matrix as matrix
import test_ios_application_receipts as runtime_fixture
import test_ios_webview_lifecycle_focus as lifecycle_fixture
import test_ios_ui_application as transport_fixture
from test_ios_io_profile import profile_options
from test_ios_webview_request_focus import synthetic_request_receipt

PROFILE = "ios-webview-request-dns"
FOCUS = "webview-ios-native-request-dns"
NATIVE_PINS = {
    "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosWebViewRequestAcceptanceTest.kt":
        "569716cf0524d25b1b3c2712dbe040c0ec82cfe3db24f6dac3775e5ec15bd857",
    "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosWebViewProvisionalDnsAcceptanceTest.kt":
        "25efe05ca6ce4cc2f027dc74eaf22a3a74cd4213d315940be9b64bdf7f0fe594",
    "scripts/ci/ios_webview_request_fixture.py":
        "a5b4780ab39822a4ee261c07d434bacb9ce9fe72943c1924eeaddcbbeb1e17a7",
}


class IosWebViewRequestDnsFocusTests(unittest.TestCase):
    def plan(self, root=lt.ROOT):
        return lt.plan(root, "ios", only_modules=("calf-webview",), focus=FOCUS)

    def groups(self):
        return (lt.IOS_WEBVIEW_REQUEST_GROUP, lt.IOS_WEBVIEW_DNS_GROUP)

    def cases(self):
        return [{"classname": group["classname"], "name": method, "status": "passed"}
                for group in self.groups() for method in group["methods"]]

    def test_combined_profile_is_exactly_one_job_three_unexecuted_methods_and_no_inventory_expansion(self):
        self.assertIn(PROFILE, matrix.PROFILES,
                      "The finite request2 + DNS1 selection is absent; do not compile two Apple jobs")
        options = profile_options((lt.ROOT / ".github/workflows/gradle.yml").read_text())
        self.assertEqual(set(matrix.PROFILES), set(options))
        self.assertEqual(1, options.count(PROFILE))
        row, = matrix.matrix(PROFILE)["include"]
        self.assertEqual(("ios-iphone", "ios", "macos-26", "arm64", "iphone", "calf-webview", FOCUS),
                         tuple(row[k] for k in ("slot", "suite", "runner", "arch", "simulator-kind", "test-modules", "test-focus")))
        self.assertNotIn("serial-test-focus", row)
        self.assertNotIn("android-batch", row)
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        self.assertEqual(self.groups(), lt.ui_application_focus_groups(FOCUS))
        full = {(group["classname"], method) for group in lt.IOS_WEBVIEW_APPLICATION_REQUIRED_GROUPS
                for method in group["methods"]}
        selected_ids = {(case["classname"], case["name"]) for case in self.cases()}
        accepted_ids = {(group["classname"], method)
                        for group in (lt.IOS_WEBVIEW_APPLICATION_REQUIRED_GROUPS[0],
                                      lt.IOS_WEBVIEW_APPLICATION_REQUIRED_GROUPS[1]) for method in group["methods"]}
        self.assertEqual(14, len(full))
        self.assertEqual(11, len(accepted_ids))
        self.assertEqual(3, len(selected_ids))
        self.assertFalse(selected_ids & accepted_ids)
        self.assertEqual(full, selected_ids | accepted_ids)
        plan = self.plan(); selected, = plan["expected"]
        self.assertEqual(":calf-webview:" + lt.IOS_APPLICATION_TASK, selected["task"])
        self.assertEqual("genuine-uikit-application", selected["native_test_host"])
        self.assertEqual(3, len(selected["required_testcases"]))
        self.assertEqual(3, lt.gradle_command("ios", plan, simulator=runtime_fixture.DEVICE).count("--tests"))
        self.assertIsNone(app.profile_debug_entitlements(FOCUS))
        self.assertEqual(app.APP_TIMEOUT_SECONDS, app.application_timeout_seconds(FOCUS))
        for source, pin in NATIVE_PINS.items():
            self.assertEqual(pin, lt.sha256(lt.ROOT / source), "Existing native/fixture bytes must remain unchanged")
        workflow = (lt.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("native-webview-application/*/receipt.json", workflow)
        self.assertNotIn("native-webview-application/**", workflow)

    def test_generic_plan_and_router_accept_only_exact_three_identity_union_for_this_owner(self):
        plan = self.plan(); selected, = plan["expected"]
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(["calf-webview"], plan["explicit_module_subset"])
        self.assertTrue(lt.validate_test_focus(plan))
        patterns = selected["test_filter"].split(",")
        self.assertEqual(3, len(patterns))
        self.assertEqual(set(lt.ui_application_focus_filter(lt.IOS_WEBVIEW_REQUEST_FOCUS).split(",")) |
                         set(lt.ui_application_focus_filter(lt.IOS_WEBVIEW_DNS_FOCUS).split(",")), set(patterns))
        arguments = sorted(app.TEST_ARGUMENTS)
        for ordered in itertools.permutations(patterns):
            self.assertEqual(FOCUS, app.application_test_focus(arguments + ["--ktest_gradle_filter=" + ",".join(ordered)]))
        # The exact existing one-/two-method focuses stay valid independently;
        # only an unreviewed mixed subset/duplicate/extra identity must refuse.
        for old_focus in (lt.IOS_WEBVIEW_REQUEST_FOCUS, lt.IOS_WEBVIEW_DNS_FOCUS):
            self.assertEqual(old_focus, app.application_test_focus(arguments + [
                "--ktest_gradle_filter=" + lt.ui_application_focus_filter(old_focus)]))
        lifecycle = lt.ui_application_focus_filter(lt.IOS_WEBVIEW_LIFECYCLE_FOCUS).split(",")[0]
        invalid_filters = ("*", patterns[0] + "," + patterns[-1], ",".join(patterns + patterns[:1]),
                           ",".join(patterns + [lifecycle]), ",".join(patterns).replace(lt.IOS_WEBVIEW_DNS_METHOD, "wrongMethod"))
        for text in invalid_filters:
            with self.subTest(filter=text), self.assertRaises(ValueError):
                app.application_test_focus(arguments + ["--ktest_gradle_filter=" + text])
        with self.assertRaises(ValueError):
            app.application_test_focus(arguments + ["--ktest_gradle_filter=" + ",".join(patterns), "--ktest_gradle_filter=*"])
        binary = app.APPLICATION_HOSTS["calf-webview"]["binary_directory"] + "/test.kexe"
        self.assertEqual("calf-webview", app.application_host(binary, FOCUS)["module"])
        for changed in (binary.replace("calf-webview", "calf-ui"), binary.replace("applicationDebugTest", "debugTest")):
            with self.assertRaises(ValueError): app.application_host(changed, FOCUS)
        for suite, modules in (("desktop", ("calf-webview",)), ("js", ("calf-webview",)),
                               ("wasm", ("calf-webview",)), ("android-device", ("calf-webview",)),
                               ("ios", ("calf-ui",)), ("ios", ("calf-file-picker",)), ("ios", None)):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                lt.plan(lt.ROOT, suite, only_modules=modules, focus=FOCUS)
        for key, value in (("test_filter", "*"), ("required_testcases", selected["required_testcases"][:2]),
                           ("native_test_host", "command-line"), ("task", ":calf-webview:publish"),
                           ("test_source_files", [])):
            changed = copy.deepcopy(plan); changed["expected"][0][key] = value
            with self.assertRaises(ValueError): lt.validate_test_focus(changed)
        changed = copy.deepcopy(plan); changed["complete_suite_requested"] = True
        with self.assertRaises(ValueError): lt.validate_test_focus(changed)
        stream = io.StringIO()
        with patch("sys.argv", ["library_tests.py", "plan", "--suite", "ios", "--module", "calf-webview", "--focus", FOCUS]), \
             patch("sys.stdout", stream):
            self.assertEqual(0, lt.main())  # In-process source parser only; no subprocess/preflight/SDK.
        self.assertEqual(plan, json.loads(stream.getvalue()))

    def fixture(self):
        parent = lifecycle_fixture.IosWebViewLifecycleFocusTests(
            "test_complete_protocol_xml_binary_runtime_and_cleanup_required_for_this_owner")
        self.addCleanup(parent.doCleanups)
        fixture = parent.fixture()  # Existing helpers only; no accepted test method is invoked.
        fixture.plan = self.plan(fixture.root)
        cases = self.cases()
        fixture.document["explicit_test_focus"] = FOCUS
        fixture.document["application_protocol"].update(testcases=cases, counts=lt.case_counts(cases))
        fixture.modules[0]["testcases"] = fixture.xml_cases(cases)
        fixture.document["webview_request_fixture"] = synthetic_request_receipt(fixture.root, fixture.document)
        fixture.save()
        return fixture

    def test_combined_preflight_requires_exact_loopback_identity_and_dns_only_stays_transport_free(self):
        plan = self.plan(); selected, = plan["expected"]
        self.assertEqual(requests.SOURCE, selected["ios_webview_request_fixture"])
        self.assertEqual(lt.sha256(lt.ROOT / requests.SOURCE), selected["ios_webview_request_fixture_sha256"])
        for group in self.groups(): self.assertIn(group["source"], selected["test_source_files"])
        self.assertIn(requests.SOURCE, selected["test_source_files"])
        for key, value in (("ios_webview_request_fixture", "wrong.py"), ("ios_webview_request_fixture_sha256", None),
                           ("ios_webview_request_fixture_sha256", "not-a-hash"),
                           ("test_source_files", [p for p in selected["test_source_files"] if p != requests.SOURCE])):
            changed = copy.deepcopy(plan); changed["expected"][0][key] = value
            with self.assertRaises(ValueError): lt.validate_test_focus(changed)
        dns = lt.plan(lt.ROOT, "ios", only_modules=("calf-webview",), focus=lt.IOS_WEBVIEW_DNS_FOCUS)
        self.assertNotIn("ios_webview_request_fixture", dns["expected"][0])
        self.assertNotIn(requests.SOURCE, dns["expected"][0]["test_source_files"])
        fixture = self.fixture(); path = fixture.root / requests.SOURCE; original = path.read_bytes()
        path.unlink()
        with self.assertRaises(ValueError): self.plan(fixture.root)
        path.write_bytes(original)
        original_safe_path = lt.safe_path
        class AliasedModel:
            def is_file(self): return True
            def stat(self): return SimpleNamespace(st_nlink=2)
        def modeled_alias(root, relative):
            return AliasedModel() if relative == requests.SOURCE else original_safe_path(root, relative)
        with patch.object(lt, "safe_path", side_effect=modeled_alias), self.assertRaises(ValueError):
            self.plan(fixture.root)  # No real hardlink/symlink is created.
        for group in self.groups():
            source = fixture.root / group["source"]; native = source.read_text()
            source.write_text(native.replace(group["methods"][0], "syntheticUnreviewedMethod", 1))
            with self.assertRaises(ValueError): self.plan(fixture.root)
            source.write_text(native)

    def collect_xml(self, *, cases=None, outcome="", markers=1, stale=False, duplicate=False):
        plan = self.plan(); selected, = plan["expected"]
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

    def test_all_three_fresh_original_xml_methods_are_mandatory_without_old_native_substitution(self):
        result = self.collect_xml()
        self.assertEqual([], result["errors"])
        self.assertEqual(3, result["totals"]["passed"])
        expected = self.plan()["expected"][0]["required_testcases"]
        missing = [{"cases": [case for index, case in enumerate(expected) if index != omit]} for omit in range(3)]
        old = lt.ui_application_focus_identities(lt.IOS_WEBVIEW_LIFECYCLE_FOCUS)[:1]
        for invalid in (*missing, {"cases": []}, {"cases": expected + expected[:1]},
                        {"cases": expected[:2] + old}, {"outcome": "<failure/>"}, {"outcome": "<error/>"},
                        {"outcome": "<skipped/>"}, {"stale": True}, {"duplicate": True}, {"markers": 0}, {"markers": 2}):
            with self.subTest(invalid=invalid): self.assertTrue(self.collect_xml(**invalid)["errors"])

    def test_three_case_protocol_xml_and_current_request_receipt_keep_every_native_cleanup_gate(self):
        fixture = self.fixture(); result = fixture.collect()
        self.assertEqual([], result["errors"], result["errors"])
        self.assertEqual(3, result["ios_applications"][0]["required_native_cases_found"])
        original = copy.deepcopy(fixture.document)
        changes = (
            lambda d: d.pop("webview_request_fixture"),
            lambda d: d.update(explicit_test_focus=lt.IOS_WEBVIEW_REQUEST_FOCUS),
            lambda d: d["webview_request_fixture"].update(native_process_id=12346),
            lambda d: d["webview_request_fixture"].update(native_source_sha256="e" * 64),
            lambda d: d["webview_request_fixture"].update(signed_application_executable_sha256="e" * 64),
            lambda d: d["webview_request_fixture"].update(application_plist_sha256="e" * 64),
            lambda d: d["webview_request_fixture"].update(dns_or_system_offline_verified=True),
            lambda d: d["webview_request_fixture"]["stages"]["tls-two"].update(alert=0),
            lambda d: d["webview_request_fixture"]["stages"]["matrix-hold"].update(client_cancelled=0),
            lambda d: d["webview_request_fixture"]["stages"]["matrix-hold"].update(response_bytes=1),
            lambda d: d["webview_request_fixture"]["cleanup"].update(owned_threads_terminated=False),
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
        )
        for change in changes:
            with self.subTest(change=change):
                fixture.document = copy.deepcopy(original); change(fixture.document); fixture.save()
                self.assertTrue(fixture.collect()["errors"])
        for cases in (self.cases()[:2], self.cases()[2:], self.cases()[:2] + [{
                "classname": lt.IOS_WEBVIEW_LIFECYCLE_CLASS, "name": lt.IOS_WEBVIEW_LIFECYCLE_METHODS[0], "status": "passed"}]):
            fixture.document = copy.deepcopy(original)
            fixture.document["application_protocol"].update(testcases=cases, counts=lt.case_counts(cases))
            fixture.modules[0]["testcases"] = fixture.xml_cases(cases); fixture.save()
            self.assertTrue(fixture.collect()["errors"], "A matching green transport/XML cannot omit or substitute DNS/request methods")

    def test_green_current_transport_hash_cannot_replace_combined_preflight_fixture_identity(self):
        fixture = self.fixture()
        self.assertEqual([], fixture.collect()["errors"])
        fixture_source = fixture.root / requests.SOURCE
        fixture_source.write_bytes(fixture_source.read_bytes() + b"\n# Explicit synthetic post-plan fixture identity change, never executed.\n")
        fixture.document["webview_request_fixture"]["fixture_source_sha256"] = lt.sha256(fixture_source)
        fixture.save()
        self.assertTrue(fixture.collect()["errors"], "Current receipt hash does not authorize changing the preflight fixture")

    def modeled_run(self, *, dns_only=False, prepare_failure=False, close_failure=False, invalid_receipt=False, runtime_failure=False):
        """One fake SDK lifecycle; no accepted test or actual subprocess is invoked."""
        source_root = lt.ROOT
        helper = transport_fixture.OwnedApplicationTests(
            "test_owned_only_install_launch_readback_uninstall_and_local_cleanup")
        helper.setUp()
        try:
            binary = helper.root / app.APPLICATION_HOSTS["calf-webview"]["binary_directory"] / "test.kexe"
            binary.parent.mkdir(parents=True); binary.write_bytes(helper.binary.read_bytes()); binary.chmod(0o700)
            helper.binary = binary
            for source in NATIVE_PINS:
                destination = helper.root / source; destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((source_root / source).read_bytes())
            events = []; leases = []; plists = []
            environment = {"SIMCTL_CHILD_NATIVECMPKIT_WEBVIEW_REQUEST_TOKEN": "f" * 32,
                           "SIMCTL_CHILD_NATIVECMPKIT_WEBVIEW_REQUEST_HTTP_PORT": "20001",
                           "SIMCTL_CHILD_NATIVECMPKIT_WEBVIEW_REQUEST_TLS_PORT": "20002"}
            class FakeLease:
                def __init__(self, root, bundle_id, signed_hash, plist_hash):
                    self.root = root; self.receipt = {}; self.prepared = False
                    self.document = {"bundle_id": bundle_id, "signed_application_executable_sha256": signed_hash,
                                     "application_plist_sha256": plist_hash, "application_protocol": {"observed_launch_pid": 12345}}
                    leases.append(self)
                def prepare(self):
                    events.append("prepare")
                    if prepare_failure: raise RuntimeError("Explicit synthetic partial preparation refusal")
                    self.prepared = True; return environment
                def close(self):
                    events.append("close")
                    if close_failure: raise RuntimeError("Explicit synthetic close refusal")
                    self.receipt = synthetic_request_receipt(self.root, self.document)
                    if not self.prepared: self.receipt.update(prepared=False, completed_methods=[])
                    if invalid_receipt: self.receipt["cleanup"]["owned_threads_terminated"] = False
            def control(argv, timeout=90):
                event = "sign" if argv[0] == "/usr/bin/codesign" else argv[2]
                events.append(event)
                if event == "sign":
                    plists.append(plistlib.loads((Path(argv[-1]) / "Info.plist").read_bytes()))
                    self.assertNotIn("--entitlements", argv)
                return helper.control(argv, timeout)
            focus = lt.IOS_WEBVIEW_DNS_FOCUS if dns_only else FOCUS
            groups = (lt.IOS_WEBVIEW_DNS_GROUP,) if dns_only else self.groups()
            def launch(argv, protocol, *, timeout, environment=None):
                events.append("launch")
                self.assertEqual(app.APP_TIMEOUT_SECONDS, timeout)
                self.assertEqual(None if dns_only else environment_expected, environment)
                filters = [arg for arg in argv if arg.startswith("--ktest_gradle_filter=")]
                self.assertEqual(["--ktest_gradle_filter=" + lt.ui_application_focus_filter(focus)], filters)
                protocol.observed_launch_pid = 12345  # Explicit synthetic console PID, never a native observation.
                protocol.feed(transport_fixture.ACTIVE)
                for group in groups:
                    protocol.feed(transport_fixture.frame("testSuiteStarted", name=group["classname"]))
                    for method in group["methods"]:
                        protocol.feed(transport_fixture.frame("testStarted", name=method))
                        protocol.feed(transport_fixture.frame("testFinished", name=method, duration="1"))
                    protocol.feed(transport_fixture.frame("testSuiteFinished", name=group["classname"]))
                protocol.feed(transport_fixture.COMPLETE)
                return {"process_exit": 0, **protocol.finish(0)}
            environment_expected = environment
            after = copy.deepcopy(helper.before)
            if runtime_failure: after["source_revision"] = "e" * 40
            arguments = [*sorted(app.TEST_ARGUMENTS), "--ktest_gradle_filter=" + lt.ui_application_focus_filter(focus)]
            with patch.dict(os.environ, {"NATIVECMPKIT_UIKIT_RESULT_ROOT": "build/ci-verification/fixture/native-webview-application"}), \
                 patch.object(app.runtime, "capture", side_effect=[helper.before, after]), \
                 patch.object(app, "execute_control", side_effect=control), \
                 patch.object(app, "forward_application", side_effect=launch), \
                 patch.object(app.shutil, "disk_usage", return_value=SimpleNamespace(free=10 * 1024**3)), \
                 patch.object(requests, "RequestFixture", FakeLease):
                result = app.run(helper.binary.relative_to(helper.root).as_posix(), arguments)
            self.assertEqual(1, events.count("sign")); self.assertEqual(1, events.count("install"))
            self.assertEqual(1, events.count("uninstall")); self.assertEqual(1, len(plists))
            self.assertLess(events.index("sign"), events.index("install"))
            self.assertEqual(0 if dns_only else 1, len(leases))
            self.assertEqual(0 if dns_only else 1, events.count("close"))
            if not dns_only:
                self.assertLess(events.index("install"), events.index("prepare"))
                self.assertLess(events.index("close"), events.index("terminate"))
                self.assertEqual({"NSAllowsLocalNetworking": True}, plists[0]["NSAppTransportSecurity"])
            else:
                self.assertNotIn("NSAppTransportSecurity", plists[0])
                self.assertNotIn("webview_request_fixture", result)
            self.assertNotIn("NSAllowsArbitraryLoads", repr(plists))
            self.assertTrue(result["cleanup"]["owned_app_identity_reverified"])
            self.assertTrue(result["cleanup"]["owned_app_absence_verified"])
            self.assertTrue(result["cleanup"]["owned_local_bundle_removed"])
            self.assertFalse(helper.installed.exists())
            self.assertFalse(any("--entitlements" in cmd for cmd in helper.commands))
            self.assertFalse(result["packages_published"])
            if prepare_failure: self.assertNotIn("launch", events)
            else: self.assertEqual(1, events.count("launch"))
            return result
        finally:
            helper.doCleanups()

    def test_one_combined_sign_install_launch_and_fixture_lease_uses_only_request_transport(self):
        result = self.modeled_run()
        self.assertTrue(result["transport_passed"])
        self.assertEqual(FOCUS, result["explicit_test_focus"])
        self.assertEqual(3, result["application_protocol"]["counts"]["passed"])
        self.assertEqual({(c["classname"], c["name"]) for c in self.cases()},
                         {(c["classname"], c["name"]) for c in result["application_protocol"]["testcases"]})
        self.assertFalse(result["webview_request_fixture"]["dns_or_system_offline_verified"])
        dns = self.modeled_run(dns_only=True)
        self.assertTrue(dns["transport_passed"])
        self.assertEqual(1, dns["application_protocol"]["counts"]["passed"])

    def test_combined_fixture_refusals_keep_owned_cleanup_and_preserve_primary_failure(self):
        for kwargs, phase, kind in (({"prepare_failure": True}, "prepare-owned-localhost-wk-request-fixture", "RuntimeError"),
                                    ({"close_failure": True}, "owned-localhost-wk-request-fixture-cleanup", "RuntimeError"),
                                    ({"invalid_receipt": True}, "owned-localhost-wk-request-fixture", "EvidenceError")):
            with self.subTest(kwargs=kwargs):
                result = self.modeled_run(**kwargs)
                self.assertFalse(result["transport_passed"])
                self.assertEqual({"phase": phase, "type": kind}, result["error"])
        result = self.modeled_run(runtime_failure=True, close_failure=True)
        self.assertFalse(result["transport_passed"])
        self.assertEqual({"phase": "post-runtime-and-binary", "type": "ValueError"}, result["error"])
        self.assertEqual({"cleanup_error_type": "RuntimeError"}, result["webview_request_fixture"])


if __name__ == "__main__": unittest.main()
