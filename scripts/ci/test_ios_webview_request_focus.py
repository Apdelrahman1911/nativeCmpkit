"""Owning request/full-inventory integration guards; never native or socket proof.

Every application, Mach-O, SDK, console frame and loopback receipt below is
explicitly simulated. No listener is prepared; execute_control/forward_application
are replaced only in these Python tooling models, never in the native WK tests.
The genuine two-method simulator request and original XML/cleanup review remain
mandatory. Existing seven WK and four application-host methods are not selected
by the new finite request profile.
"""
from collections import Counter
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import cookie_common_jdk_plan as cookie_scope
import ios_ui_application as app
import ios_webview_request_fixture as requests
import library_tests as lt
import workflow_matrix as matrix
import test_ios_application_receipts as runtime_fixture
import test_ios_webview_lifecycle_focus as lifecycle_fixture
from test_ios_io_profile import profile_options

PROFILE = "ios-webview-request-state"
FOCUS = "webview-ios-native-request-state"


def synthetic_request_receipt(root, document):
    """Strictly shaped fake counters, NOT actual TLS/client EOF/native evidence."""
    stages = {}
    for stage, (mode, generations) in requests.STAGE_SPECS.items():
        counters = requests.zero_counters()
        counters.update(generation=generations, arrived=generations, closed=generations)
        if mode == "tls":
            counters.update(hello=1, alert=1, response_bytes=7)
        elif mode == "hold":
            counters.update(client_cancelled=1)
        elif mode == "page":
            counters.update(page=generations, response_bytes=512 * generations)
        elif mode == "redirect":
            counters.update(redirect=1, response_bytes=128)
        stages[stage] = counters
    return {
        "schema_version": 1, "kind": "owned-localhost-wk-request-transport", "prepared": True,
        "bundle_id": document["bundle_id"],
        "signed_application_executable_sha256": document["signed_application_executable_sha256"],
        "application_plist_sha256": document["application_plist_sha256"],
        "fixture_source_sha256": lt.sha256(root / requests.SOURCE),
        "native_source_sha256": lt.sha256(root / requests.NATIVE_SOURCE),
        "token_sha256": hashlib.sha256(b"explicitly-synthetic-no-native-lease").hexdigest(),
        "native_process_id": document["application_protocol"]["observed_launch_pid"],
        "native_claims": 2, "work": 32, "connections_started": 32, "connections_closed": 32,
        "completed_methods": sorted(requests.METHOD_KEYS), "stages": stages, "errors": [],
        "local_loopback_only": True, "tls_certificate_private_key_or_trust_bypass": False,
        "dns_or_system_offline_verified": False,
        "cleanup": {"owned_listeners_closed": True, "owned_connections_closed": True,
                    "owned_threads_terminated": True, "launch_environment_process_local_only": True},
    }


def synthetic_webview_request_receipt(fixture):
    """Used by the existing full-module guard, never by the runtime transport."""
    return synthetic_request_receipt(fixture.root, fixture.document)


class IosWebViewRequestFocusTests(unittest.TestCase):
    def fixture(self, *, full=False):
        parent = lifecycle_fixture.IosWebViewLifecycleFocusTests(
            "test_unfiltered_webview_still_requires_every_owning_host_and_native_method")
        self.addCleanup(parent.doCleanups)
        fixture = parent.fixture()
        fixture.plan = lt.plan(fixture.root, "ios", only_modules=("calf-webview",),
                               focus=None if full else FOCUS)
        groups = lt.IOS_WEBVIEW_APPLICATION_REQUIRED_GROUPS if full else (lt.IOS_WEBVIEW_REQUEST_GROUP,)
        cases = [{"classname": group["classname"], "name": name, "status": "passed"}
                 for group in groups for name in group["methods"]]
        fixture.document["explicit_test_focus"] = None if full else FOCUS
        fixture.document["application_protocol"].update(testcases=cases, counts=lt.case_counts(cases))
        fixture.modules[0]["testcases"] = fixture.xml_cases(cases)
        fixture.document["webview_request_fixture"] = synthetic_webview_request_receipt(fixture)
        fixture.save()
        return fixture

    def assert_refused_document(self, fixture, original, change):
        fixture.document = copy.deepcopy(original)
        change(fixture.document)
        fixture.save()
        self.assertTrue(fixture.collect()["errors"], "A fake green loopback receipt must not waive its native/application gates")

    def test_current_profile_is_additive_to_android_batches_and_complete_slots(self):
        options = profile_options((lt.ROOT / ".github/workflows/gradle.yml").read_text())
        self.assertEqual(set(matrix.PROFILES), set(options))
        self.assertEqual(1, options.count(PROFILE))
        row, = matrix.matrix(PROFILE)["include"]
        self.assertEqual(("ios-iphone", "ios", "calf-webview", FOCUS),
                         tuple(row[key] for key in ("slot", "suite", "test-modules", "test-focus")))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        for old_profile in ("all", "apple", "ios", "core", "browser"):
            self.assertTrue(all("test-focus" not in selected for selected in matrix.matrix(old_profile)["include"]))
        for profile, modules in (("android-io-permission-storage-api35", "calf-io,calf-permissions/core"),
                                 ("android-permission-storage-compatibility", "calf-permissions/core")):
            android_row, = matrix.matrix(profile)["include"]
            self.assertEqual("android-device", android_row["suite"])
            self.assertEqual(modules, android_row["test-modules"])
            self.assertNotIn("test-focus", android_row)
            self.assertNotIn("calf-webview", android_row["test-modules"])
        workflow = (lt.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("native-webview-application/*/receipt.json", workflow)
        self.assertNotIn("native-webview-application/**", workflow)

    def test_full_source_inventory_is_fourteen_and_original_focused_ten_seven_one_are_unchanged(self):
        full = {(group["classname"], name) for group in lt.IOS_WEBVIEW_APPLICATION_REQUIRED_GROUPS
                for name in group["methods"]}
        declared = set()
        for group in lt.IOS_WEBVIEW_APPLICATION_REQUIRED_GROUPS:
            source = (lt.ROOT / group["source"]).read_text()
            names = re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", source)
            self.assertEqual(len(names), len(set(names)))
            declared.update((group["classname"], name) for name in names)
        self.assertEqual(14, len(full))
        self.assertEqual(full, declared)
        request_plan = lt.plan(lt.ROOT, "ios", only_modules=("calf-webview",), focus=FOCUS)
        selected, = request_plan["expected"]
        self.assertEqual(2, len(selected["required_testcases"]))
        self.assertEqual(2, lt.gradle_command("ios", request_plan, simulator=runtime_fixture.DEVICE).count("--tests"))
        self.assertEqual("genuine-uikit-application", selected["native_test_host"])
        self.assertEqual(":calf-webview:" + lt.IOS_APPLICATION_TASK, selected["task"])
        self.assertEqual(requests.SOURCE, selected["ios_webview_request_fixture"])
        self.assertEqual(lt.sha256(lt.ROOT / requests.SOURCE), selected["ios_webview_request_fixture_sha256"])
        for focus, count in ((lt.IOS_WEBVIEW_LIFECYCLE_FOCUS, 10), (lt.IOS_WEBVIEW_RECOVERY_FOCUS, 7),
                             (lt.IOS_WEBVIEW_REMOUNT_RECOVERY_FOCUS, 1)):
            old = lt.plan(lt.ROOT, "ios", only_modules=("calf-webview",), focus=focus)
            self.assertEqual(count, len(old["expected"][0]["required_testcases"]))
            self.assertEqual(count, lt.gradle_command("ios", old, simulator=runtime_fixture.DEVICE).count("--tests"))
            self.assertNotIn(lt.IOS_WEBVIEW_REQUEST_CLASS, old["expected"][0]["test_filter"])
            self.assertNotIn("ios_webview_request_fixture", old["expected"][0])
        self.assertIsNone(app.profile_debug_entitlements(FOCUS))
        self.assertEqual({"ios-webview-provisional-dns", "ios-webview-request-dns"},
                         {value for value in matrix.PROFILES if "dns" in value})

    def test_focused_application_collection_correlates_current_loopback_sources_pid_binary_and_plist(self):
        fixture = self.fixture()
        result = fixture.collect()
        self.assertEqual([], result["errors"], result["errors"])
        self.assertEqual(2, result["ios_applications"][0]["required_native_cases_found"])
        original = copy.deepcopy(fixture.document)
        for change in (
            lambda d: d.pop("webview_request_fixture"),
            lambda d: d["webview_request_fixture"].update(native_process_id=12346),
            lambda d: d["application_protocol"].update(observed_launch_pid=12346),
            lambda d: d["webview_request_fixture"].update(fixture_source_sha256="e" * 64),
            lambda d: d["webview_request_fixture"].update(native_source_sha256="e" * 64),
            lambda d: d["webview_request_fixture"].update(signed_application_executable_sha256="e" * 64),
            lambda d: d["webview_request_fixture"].update(application_plist_sha256="e" * 64),
            lambda d: d["webview_request_fixture"].update(error={"type": "synthetic-hidden-refusal"}),
            lambda d: d["webview_request_fixture"].update(private_native_error="synthetic-foreign-field"),
            lambda d: d["webview_request_fixture"].update(dns_or_system_offline_verified=True),
        ):
            with self.subTest(change=change): self.assert_refused_document(fixture, original, change)
        fixture.document = copy.deepcopy(original)
        fixture.save()
        path = fixture.root / requests.SOURCE
        original_source = path.read_bytes()
        path.write_bytes(original_source + b"\n# Explicit synthetic post-preflight source mutation\n")
        self.assertTrue(fixture.collect()["errors"])
        path.write_bytes(original_source)
        selected = fixture.plan["expected"][0]
        selected["ios_webview_request_fixture_sha256"] = "e" * 64
        self.assertTrue(fixture.collect()["errors"])

    def test_full_application_cannot_accept_old_eleven_twelve_thirteen_or_transportless_results(self):
        fixture = self.fixture(full=True)
        result = fixture.collect()
        self.assertEqual([], result["errors"], result["errors"])
        self.assertEqual(14, result["ios_applications"][0]["required_native_cases_found"])
        original = copy.deepcopy(fixture.document)
        cases = original["application_protocol"]["testcases"]
        for missing in ((lt.IOS_WEBVIEW_REQUEST_METHODS[0],), (lt.IOS_WEBVIEW_REQUEST_METHODS[1],),
                        lt.IOS_WEBVIEW_REQUEST_METHODS, (lt.IOS_WEBVIEW_DNS_METHOD,)):
            fixture.document = copy.deepcopy(original)
            remaining = [case for case in cases if case["name"] not in missing]
            fixture.document["application_protocol"].update(testcases=remaining, counts=lt.case_counts(remaining))
            fixture.modules[0]["testcases"] = fixture.xml_cases(remaining)
            fixture.save()
            self.assertTrue(fixture.collect()["errors"])
        fixture.modules[0]["testcases"] = fixture.xml_cases(cases)
        for change in (
            lambda d: d.pop("webview_request_fixture"),
            lambda d: d["webview_request_fixture"]["stages"]["matrix-hold"].update(client_cancelled=0),
            lambda d: d["webview_request_fixture"]["stages"]["matrix-hold"].update(response_bytes=1),
            lambda d: d["webview_request_fixture"]["stages"]["tls-two"].update(alert=0),
            lambda d: d["webview_request_fixture"]["cleanup"].update(owned_threads_terminated=False),
        ):
            with self.subTest(change=change): self.assert_refused_document(fixture, original, change)

    def test_green_request_transport_cannot_waive_signer_worker_sdk_install_or_application_cleanup(self):
        fixture = self.fixture()
        self.assertEqual([], fixture.collect()["errors"])
        original = copy.deepcopy(fixture.document)
        for change in (
            lambda d: d["steps"]["adhoc-sign-local-verification-app"].update(exit_code=1),
            lambda d: d["steps"]["adhoc-sign-local-verification-app"].update(remote_signing_or_publication=True),
            lambda d: d["steps"]["foreign-app-preflight"].update(preexisting_app_absence_verified=False),
            lambda d: d["steps"]["install-owned-app"].update(installed_owned_bytes_verified=False),
            lambda d: d["application_protocol"]["activation"].update(owned_worker=1),
            lambda d: d["application_protocol"]["completion"].update(worker_terminated=False),
            lambda d: d["application_protocol"].update(process_exit=9),
            lambda d: d["runtime_after"].update(apple_sdks={"iphonesimulator": "25.0"}),
            lambda d: d.update(binary_sha256_after="e" * 64),
            lambda d: d["cleanup"].update(owned_app_identity_reverified=False),
            lambda d: d["cleanup"].update(owned_app_stopped_verified=False),
            lambda d: d["cleanup"].update(uninstall_exit_code=1),
            lambda d: d["cleanup"].update(owned_app_absence_verified=False),
            lambda d: d["cleanup"].update(owned_local_bundle_removed=False),
            lambda d: d.update(application_protocol_partial={}),
        ):
            with self.subTest(change=change): self.assert_refused_document(fixture, original, change)

    def modeled_run(self, *, prepare_failure=False, close_failure=False, invalid_receipt=False, runtime_failure=False):
        """Exercise run() only against owned Python files and fake controls/console."""
        import test_ios_ui_application as transport_fixture
        source_root = lt.ROOT
        helper = transport_fixture.OwnedApplicationTests(
            "test_owned_only_install_launch_readback_uninstall_and_local_cleanup")
        helper.setUp()
        try:
            binary = helper.root / app.APPLICATION_HOSTS["calf-webview"]["binary_directory"] / "test.kexe"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(helper.binary.read_bytes())
            binary.chmod(0o700)
            helper.binary = binary
            for source in (requests.SOURCE, requests.NATIVE_SOURCE):
                destination = helper.root / source
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((source_root / source).read_bytes())
            events = []
            leases = []
            environment = {"SIMCTL_CHILD_NATIVECMPKIT_WEBVIEW_REQUEST_TOKEN": "f" * 32,
                           "SIMCTL_CHILD_NATIVECMPKIT_WEBVIEW_REQUEST_HTTP_PORT": "20001",
                           "SIMCTL_CHILD_NATIVECMPKIT_WEBVIEW_REQUEST_TLS_PORT": "20002"}
            class FakeLease:
                def __init__(self, root, bundle_id, signed_hash, plist_hash):
                    self.root = root
                    self.document = {"bundle_id": bundle_id,
                                     "signed_application_executable_sha256": signed_hash,
                                     "application_plist_sha256": plist_hash,
                                     "application_protocol": {"observed_launch_pid": 12345}}
                    self.receipt = {}
                    self.prepared = False
                    leases.append(self)
                def prepare(self):
                    events.append("prepare")
                    if prepare_failure: raise RuntimeError("Explicit synthetic partial preparation refusal")
                    self.prepared = True
                    return environment
                def close(self):
                    events.append("close")
                    if close_failure: raise RuntimeError("Explicit synthetic close refusal")
                    self.receipt = synthetic_request_receipt(self.root, self.document)
                    if not self.prepared:
                        self.receipt.update(prepared=False, completed_methods=[])
                    if invalid_receipt:
                        self.receipt["cleanup"]["owned_threads_terminated"] = False
            def control(argv, timeout=90):
                events.append("sign" if argv[0] == "/usr/bin/codesign" else argv[2])
                return helper.control(argv, timeout)
            def launch(argv, protocol, *, timeout, environment):
                events.append("launch")
                self.assertEqual(app.APP_TIMEOUT_SECONDS, timeout)
                self.assertEqual("f" * 32, environment["SIMCTL_CHILD_NATIVECMPKIT_WEBVIEW_REQUEST_TOKEN"])
                protocol.observed_launch_pid = 12345  # Explicit simulated console PID, never a native claim.
                protocol.feed(transport_fixture.ACTIVE)
                protocol.feed(transport_fixture.frame("testSuiteStarted", name=lt.IOS_WEBVIEW_REQUEST_CLASS))
                for method in lt.IOS_WEBVIEW_REQUEST_METHODS:
                    protocol.feed(transport_fixture.frame("testStarted", name=method))
                    protocol.feed(transport_fixture.frame("testFinished", name=method, duration="1"))
                protocol.feed(transport_fixture.frame("testSuiteFinished", name=lt.IOS_WEBVIEW_REQUEST_CLASS))
                protocol.feed(transport_fixture.COMPLETE)
                return {"process_exit": 0, **protocol.finish(0)}
            after = copy.deepcopy(helper.before)
            if runtime_failure: after["source_revision"] = "e" * 40
            arguments = [*sorted(app.TEST_ARGUMENTS), cookie_scope.NATIVE_EXCLUSION,
                         "--ktest_gradle_filter=" + lt.ui_application_focus_filter(FOCUS)]
            with patch.dict(os.environ, {"NATIVECMPKIT_UIKIT_RESULT_ROOT": "build/ci-verification/fixture/native-webview-application"}), \
                    patch.object(app.runtime, "capture", side_effect=[helper.before, after]), \
                    patch.object(app, "execute_control", side_effect=control), \
                    patch.object(app, "forward_application", side_effect=launch), \
                    patch.object(app.shutil, "disk_usage", return_value=SimpleNamespace(free=10 * 1024**3)), \
                    patch.object(requests, "RequestFixture", FakeLease):
                result = app.run(helper.binary.relative_to(helper.root).as_posix(), arguments)
            self.assertEqual(1, len(leases))
            self.assertEqual(1, events.count("close"))
            self.assertLess(events.index("sign"), events.index("install"))
            self.assertLess(events.index("install"), events.index("prepare"))
            self.assertLess(events.index("close"), events.index("terminate"))
            self.assertTrue(result["cleanup"]["owned_app_identity_reverified"])
            self.assertTrue(result["cleanup"]["owned_app_absence_verified"])
            self.assertTrue(result["cleanup"]["owned_local_bundle_removed"])
            self.assertFalse(helper.installed.exists())
            self.assertFalse(any("--entitlements" in command for command in helper.commands))
            if prepare_failure: self.assertNotIn("launch", events)
            return result
        finally:
            helper.doCleanups()

    def test_new_fixture_setup_close_and_invalid_receipt_never_skip_owned_application_cleanup(self):
        result = self.modeled_run()
        self.assertTrue(result["transport_passed"])
        self.assertEqual(2, result["application_protocol"]["counts"]["passed"])
        for arguments, phase, kind in (
            ({"prepare_failure": True}, "prepare-owned-localhost-wk-request-fixture", "RuntimeError"),
            ({"close_failure": True}, "owned-localhost-wk-request-fixture-cleanup", "RuntimeError"),
            ({"invalid_receipt": True}, "owned-localhost-wk-request-fixture", "EvidenceError"),
        ):
            with self.subTest(arguments=arguments):
                result = self.modeled_run(**arguments)
                self.assertFalse(result["transport_passed"])
                self.assertEqual({"phase": phase, "type": kind}, result["error"])

    def test_existing_primary_failure_is_not_masked_by_new_fixture_close_refusal(self):
        result = self.modeled_run(runtime_failure=True, close_failure=True)
        self.assertFalse(result["transport_passed"])
        self.assertEqual({"phase": "post-runtime-and-binary", "type": "ValueError"}, result["error"])
        self.assertEqual({"cleanup_error_type": "RuntimeError"}, result["webview_request_fixture"])


if __name__ == "__main__":
    unittest.main()
