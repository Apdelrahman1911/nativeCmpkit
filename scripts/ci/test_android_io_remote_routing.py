# SPDX-License-Identifier: Apache-2.0
"""Nine NEW finite IO665 routing controls; synthetic orchestration/XML are not native receipts.

Only selected owning source/parser/controller code is exercised when explicitly
requested. No SDK, APK build/install, socket, native process or guarded CLI is
run. The old remote/helper/native populations are not selected by this file.
"""
from __future__ import annotations

import ast
from collections import Counter
from contextlib import ExitStack
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

TREE = Path(os.environ.get("NATIVECMPKIT_IO_REMOTE_ROUTING_TREE",
            os.environ.get("NATIVECMPKIT_IO_REMOTE_TREE", Path(__file__).resolve().parents[2]))).resolve()
sys.path.insert(0, str(TREE / "scripts/ci"))
import android_device_tests as controller
import android_io_documents as old_io
import android_io_remote_documents as remote
import android_io_remote_routing_source_projection as projection
import library_tests as lt
import workflow_matrix
import ci_source_domain740 as source_domain
import ci_source_recovery740_742 as source_recovery


def function_source(relative, name):
    source = (TREE / relative).read_text(encoding="utf-8")
    matches = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(matches) != 1:
        raise AssertionError("One exact owning source function is required")
    return ast.get_source_segment(source, matches[0])


def copy_remote_fixture(root):
    # Copy code/manifest dependencies separately; never enlarge raw fixture admission.
    inputs = (projection.fixture_inputs() | source_domain.dependency_inputs() |
              source_recovery.dependency_inputs())
    for relative in inputs:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((TREE / relative).read_bytes())


class AndroidIoRemoteRoutingControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for module in (controller, remote, old_io, projection, lt, workflow_matrix):
            if Path(module.__file__).resolve().parents[2] != TREE:
                raise AssertionError("Controls must read this exact selected source tree, not another worktree")
        cls.plans = {focus: lt.plan(TREE, "android-device", only_modules=("calf-io",), focus=focus)
                     for focus in lt.ANDROID_IO_REMOTE_FOCUSES}
        cls.native = (TREE / lt.ANDROID_IO_REMOTE_SOURCE).read_text(encoding="utf-8")
        cls.source = cls.plans["android-io-controlled-remote"]["android_io_remote_documents"]["source_contract"]

    def setUp(self):
        def forbidden(*args, **kwargs):
            raise AssertionError("A finite source control cannot execute an external process")
        for name in ("run", "Popen"):
            control = patch.object(subprocess, name, forbidden)
            control.start()
            self.addCleanup(control.stop)
        control = patch.object(os, "system", forbidden)
        control.start()
        self.addCleanup(control.stop)

    def prepared(self):
        # Explicit synthetic schema data. No real source APK/signature/install/native claim.
        digest, certificate = "d" * 64, "c" * 64
        return {"package": remote.PACKAGE, "source_fixture": remote.FIXTURE,
            "prepare_status": "passed", "verification_api_level": 35, "recipient_installed": True,
            "manual_URI_grant": False, "automatic_runtime_permission_grant": False,
            "native_or_consumer_success_inferred": False, "source_apk_sha256": digest,
            "installed_readback": {"apk_sha256": digest, "exact_one_APK_path_observed": True},
            "source_contract": deepcopy(self.source), "apk_policy": {
                "compiled_manifest_inspected": True, "content_requires_android_grant": True,
                "signature_control_only": True, "INTERNET_only": True, "no_helper_grant_activity": True,
                "native_or_consumer_success_inferred": False, "certificate_sha256": certificate,
                "private_key_certificate_sha256": certificate, "apk_signer_revision": remote.SIGNER_REVISION,
                "signature_verification_min_sdk_version": 35, "signature_verification_max_sdk_version": 35}}

    def orchestration(self, failure=None):
        """Execute the actual owning controller against only named synthetic side-effect seams."""
        events, prepared = [], self.prepared()
        source = deepcopy(self.source)
        selected = deepcopy(self.plans["android-io-controlled-remote"])
        state = {"name": None}
        owner_control = self
        class FakeProcess:
            pid = 123456  # Synthetic in-memory child, never a live PID or signal target.
            def __init__(self, *args, **kwargs):
                self.exit = None
                events.append("owned-child-launch")
            def poll(self):
                return self.exit
        class FakeGuest:
            def __init__(self, root, output, name, environment):
                self.output = output
                self.receipt = {"schema": "nativecmpkit.camera-fresh-guest.v1", "errors": []}
                events.append("owned-guest-owner-assigned")
            def create(self):
                for name in ("avd", "android-user"):
                    (self.output / name).mkdir(mode=0o700)
                events.append("owned-guest-roots-created")
            def capture_avd(self, home):
                events.append("owned-avd-captured")
            def before_launch(self):
                events.append("owned-guest-before-launch")
            def attach(self, process):
                events.append("owned-child-attached")
            def verify_live(self):
                return True
            def dispose(self, **kwargs):
                owner_control.assertTrue(kwargs["engine_exited"])
                owner_control.assertTrue(kwargs["transport_absent"])
                events.append("owned-guest-disposal")
                for name in ("avd", "android-user"):
                    (self.output / name).rmdir()
                return self.receipt | {"disposal_status": "passed", "roots_absent": True,
                    "identity_confined_disposal": True}
        class FakeRemote:
            def __init__(self, *args, **kwargs):
                self.receipt = deepcopy(prepared)
                events.append("remote-owner-assigned")
            def prepare(self):
                events.append("remote-prepare")
                if failure == "partial-prepare":
                    self.receipt.update(prepare_status="failed", prepare_error="ValueError")
                    raise ValueError("Synthetic partial source/APK preparation refusal")
                events.append("synthetic-signer-install-readback-complete")
                return deepcopy(self.receipt)
            def close(self):
                events.append("remote-close")
                if failure == "cleanup":
                    raise RuntimeError("Synthetic identity cleanup refusal")
                self.receipt.update(cleanup_status="passed", owned_recipient_removed=True)
                return deepcopy(self.receipt)
        def execute(root, command, log, *args, **kwargs):
            stage = Path(log).stem
            events.append(stage)
            if stage == "owned-avd-create":
                state["name"] = command[command.index("--name") + 1]
            return {"exit_code": 1 if failure == "reporter-compile" and stage == "apk-assembly" else 0}
        def native(root, suite, output, *args, **kwargs):
            events.append("synthetic-native-dispatch")
            owner_control.assertEqual(kwargs["android_io_remote_documents_receipt"], prepared)
            owner_control.assertNotIn("android_io_documents_receipt", kwargs)
            owner_control.assertEqual(kwargs["android_serial"], controller.SERIAL)
            owner_control.assertTrue(kwargs["android_user_home"].endswith("/android-user"))
            return {"passed": True, "totals": {"tests": 2, "passed": 2}, "modules": []}
        def stop(home, process, name, verified):
            owner_control.assertEqual(name, state["name"])
            owner_control.assertTrue(verified)
            process.exit = 0
            events.append("owned-child-shutdown")
            return {"clean_shutdown": True}
        def no_camera(*args, **kwargs):
            raise AssertionError("Remote reuse of the guest ledger must not acquire Camera C1 prerequisites")
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            seams = (
                (lt, "plan", lambda *a, **k: deepcopy(selected)),
                (lt, "snapshot_inputs", lambda *a, **k: {"synthetic-global-source": "e" * 64}),
                (lt, "git_revision", lambda *a, **k: "f" * 40),
                (lt, "execute", execute), (lt, "run", native),
                (controller, "sdk_assets", lambda *a, **k: {"system_image": controller.IMAGE}),
                (controller, "ensure_ports_unused", lambda: None),
                (controller, "adb", lambda *a, **k: "List of devices attached\n"),
                (controller, "avd_name", lambda *a, **k: state["name"]),
                (controller, "wait_for_owned_boot", lambda *a, **k: {"api_level": "35", "serial": controller.SERIAL}),
                (controller, "stop_owned_emulator", stop),
                (controller, "wait_for_owned_transport_removal", lambda *a, **k: True),
                (controller.runtime, "capture", lambda *a, **k: {"source_revision": "f" * 40, "source_tree_dirty": False}),
                (controller.camera_developer, "OwnedFreshGuest", FakeGuest),
                (controller.camera_developer, "OwnedDeveloperPrerequisite", no_camera),
                (remote, "OwnedRemoteIoDocuments", FakeRemote),
                (remote, "source_contract", lambda *a, **k: deepcopy(source)),
                (controller.subprocess, "Popen", FakeProcess),
            )
            for module, name, replacement in seams:
                stack.enter_context(patch.object(module, name, replacement))
            stack.enter_context(patch.dict(os.environ, {"ANDROID_HOME": str(root / "synthetic-sdk")}))
            result = controller._run(root, "build/ci-verification/synthetic-remote-orchestration",
                                     only_modules=("calf-io",), focus="android-io-controlled-remote", api_level=35)
            return deepcopy(result), list(events)

    def test_combined_class_and_exact_single_missing_only_routes_share_two_direct_enabled_methods(self):
        remote.validate_direct_native_population(self.native)
        self.assertEqual(tuple(lt.ANDROID_IO_REMOTE_FOCUSES), tuple(remote.FOCUSES))
        for focus, methods in remote.FOCUSES.items():
            with self.subTest(focus=focus):
                plan = self.plans[focus]
                self.assertTrue(lt.validate_test_focus(plan))
                self.assertTrue(lt.android_io_remote_documents_required(plan))
                self.assertFalse(lt.android_io_documents_required(plan))
                item = plan["expected"][0]
                expected_filter = remote.CLASS if len(methods) == 2 else remote.CLASS + "#" + methods[0]
                self.assertEqual(expected_filter, item["test_filter"])
                self.assertEqual("class", item["test_filter_argument"])
                self.assertEqual(list(remote.identities(focus)), item["required_testcases"])
                self.assertEqual(tuple(remote.CLASS + "." + method for method in methods), remote.required_tests(focus))
                command = lt.gradle_command("android-device", plan, root=TREE, android_serial=controller.SERIAL,
                    android_io_remote_documents_receipt=self.prepared())
                self.assertIn("-Pandroid.testInstrumentationRunnerArguments.class=" + expected_filter, command)
                self.assertNotIn("-Pandroid.testInstrumentationRunnerArguments.nativecmpkitOwnedIoDocuments=true", command)
                self.assertEqual(1, command.count(":calf-io:connectedAndroidDeviceTest"))
                self.assertNotIn(",", expected_filter)
        self.assertEqual(2, len(remote.METHODS))

    def test_inherited_nested_disabled_extra_duplicate_or_unknown_native_population_refuses(self):
        owner = "class AndroidIoRemoteDocumentsTest {"
        second = "    @Test fun " + remote.METHODS[1]
        mutations = {
            "inherited": self.native.replace(owner, "class AndroidIoRemoteDocumentsTest : Parent() {", 1),
            "delegated": self.native.replace(owner, "class AndroidIoRemoteDocumentsTest : Marker by delegate {", 1),
            "open-owner": self.native.replace(owner, "open " + owner, 1),
            "nested": self.native.replace("    @Test fun " + remote.METHODS[0],
                        "    class Nested {\n    @Test fun " + remote.METHODS[0], 1).replace(second, "    }\n" + second, 1),
            "disabled": self.native.replace("    @Test fun", "    @org.junit.Ignore\n    @Test fun", 1),
            "extra": self.native.replace(owner, owner + "\n    @Test fun foreign() = runBlocking(Dispatchers.IO) {}", 1),
            "qualified-extra": self.native.replace(owner, owner + "\n    @org.junit.Test fun foreign() {}", 1),
            "duplicate": self.native.replace(remote.METHODS[1] + "()", remote.METHODS[0] + "()", 1),
            "unknown": self.native.replace(remote.METHODS[1] + "()", "unselectedNativeCase()", 1),
            "alias": self.native.replace("import org.junit.Test", "import org.junit.Test as OtherTest", 1),
            "typealias": self.native.replace("@RunWith(AndroidJUnit4::class)",
                            "typealias OtherTest = org.junit.Test\n@RunWith(AndroidJUnit4::class)", 1),
            "foreign-runner": self.native.replace("androidx.test.ext.junit.runners.AndroidJUnit4", "foreign.AndroidJUnit4", 1),
            "foreign-package": self.native.replace("package com.mohamedrejeb.calf.io", "package foreign.io", 1),
            "ambiguous-braces": self.native.rstrip()[:-1],
            "unterminated-comment": self.native + "\n/* @Test",
        }
        for name, source in mutations.items():
            self.assertNotEqual(self.native, source, name)
            with self.subTest(population=name), self.assertRaises(ValueError):
                remote.validate_direct_native_population(source)
        # Body/comment text is a narrow lexical domain, not a generic whole-byte pin.
        quoted = self.native.replace(owner, owner + '\n    private val note = "@Test fun foreign() {}"', 1)
        self.assertIsNone(remote.validate_direct_native_population(quoted))
        for bad in (None, self.native.encode(), self.native + "\nclass Foreign {}", "x" * 524289):
            with self.subTest(kind=type(bad).__name__), self.assertRaises(ValueError):
                remote.validate_direct_native_population(bad)

    def test_exact_api35_calf_io_only_native_and_cli_routes_refuse_wrong_type_or_expansion(self):
        for focus in lt.ANDROID_IO_REMOTE_FOCUSES:
            controller.validate_api_selection(35, ("calf-io",), focus)
            for api in (True, "35", 35.0, None, 23, 33, 34, 36):
                with self.subTest(focus=focus, api_type=type(api).__name__), self.assertRaises(ValueError):
                    controller.validate_api_selection(api, ("calf-io",), focus)
            for modules in (None, ["calf-io"], ("calf-share",), ("calf-io", "calf-share"), ("calf-io", "calf-io")):
                self.assertFalse(lt.allowed_test_focus("android-device", modules, focus))
                with self.assertRaises(ValueError):
                    controller.validate_api_selection(35, modules, focus)
            for suite in ("desktop", "android-host", "ios", "js", "wasm"):
                self.assertFalse(lt.allowed_test_focus(suite, ("calf-io",), focus))
        for module_request in (("calf-io",), None):
            with self.subTest(unfiltered_modules=module_request), self.assertRaisesRegex(ValueError, "Unfiltered Android discovery"):
                lt.plan(TREE, "android-device", only_modules=module_request)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            # Neither deleting the enabled class nor declaring a synthetic minimum
            # can transform a full/default or calf-io-unfiltered request into admission.
            with patch.object(lt, "projects", side_effect=AssertionError("Domain refusal must precede source discovery")), \
                 patch.object(controller, "require_host", side_effect=AssertionError("Full refusal must precede host")):
                for modules in (None, (), ("calf-io",), ("calf-io", "calf-share")):
                    with self.subTest(no_tree_modules=modules), self.assertRaisesRegex(ValueError, "Unfiltered Android discovery"):
                        lt.plan(root, "android-device", minimum_modules=("calf-fixture",), only_modules=modules)
                    for owning_run in (controller.run, controller._run):
                        with self.subTest(controller=owning_run.__name__, modules=modules), self.assertRaisesRegex(ValueError, "Unfiltered Android discovery"):
                            owning_run(root, "build/ci-verification/unfiltered-refused", only_modules=modules, api_level=35)
            self.assertFalse((root / "build").exists(), "Full refusal must precede outputs and locks")
            for api in (True, "35", 34):
                with self.subTest(direct_remote_api_type=type(api).__name__), self.assertRaisesRegex(ValueError, "exact integer API35"):
                    controller._run(root, "build/ci-verification/direct-remote-refused", only_modules=("calf-io",),
                                     focus="android-io-controlled-remote", api_level=api)
            self.assertFalse((root / "build").exists(), "Direct remote API refusal must also precede output")
        for name, value in (("verification_api_level", True), ("test_filter", remote.CLASS + "#" + remote.METHODS[0] + "," + remote.CLASS + "#" + remote.METHODS[1]),
                            ("test_filter_argument", "annotation"), ("required_original_xml", True), ("task", ":calf-io:connectedCheck"),
                            ("required_testcases", list(remote.identities("android-io-controlled-remote")) + [{"classname": remote.CLASS, "name": "foreign"}])):
            bad = deepcopy(self.plans["android-io-controlled-remote"])
            bad["expected"][0][name] = value
            with self.subTest(finite_operand=name), self.assertRaises(ValueError):
                lt.validate_test_focus(bad)
        bad = deepcopy(self.plans["android-io-controlled-remote"])
        bad["android_io_remote_documents"]["verification_api_level"] = "35"
        with self.assertRaises(ValueError):
            lt.validate_test_focus(bad)
        library_cli = function_source("scripts/ci/library_tests.py", "main")
        device_cli = function_source("scripts/ci/android_device_tests.py", "main")
        self.assertIn("*ANDROID_IO_REMOTE_FOCUSES", library_cli)
        self.assertIn("*lt.ANDROID_IO_REMOTE_FOCUSES", device_cli)
        for bad_focus in (None, "android-io-controlled-remote-all", remote.CLASS, True):
            with self.assertRaises(ValueError):
                remote.instrumentation_filter(bad_focus)

    def test_source_manifest_union_is_complete_reversible_and_never_broadens_old_reporter_grants(self):
        self.assertEqual(38, len(remote.SOURCE_FILES))
        self.assertEqual(set(remote.SOURCE_FILES), set(self.source["source_inputs"]))
        self.assertTrue(set(remote.SOURCE_FILES) <= projection.fixture_inputs())
        raw = (TREE / remote.REPORTER_MANIFEST).read_bytes()
        before = remote.normalize_reporter_manifest(raw)
        self.assertEqual(remote.OLD_REPORTER_SHA256, hashlib.sha256(before).hexdigest())
        self.assertEqual(before, old_io.normalize_remote_reporter_source(raw))
        self.assertEqual(before, old_io.normalize_remote_reporter_source(before))
        self.assertEqual(4, len(remote.REPORTER_FRAGMENTS))
        for fragment in remote.REPORTER_FRAGMENTS:
            for bad in (raw.replace(fragment, b"", 1), raw + fragment, raw.replace(fragment, b"foreign", 1)):
                with self.subTest(fragment_sha256=hashlib.sha256(fragment).hexdigest()), self.assertRaises(ValueError):
                    old_io.normalize_remote_reporter_source(bad)
        for bad in (raw + b"\n", raw.replace(b"android:exported=\"false\"", b"android:exported=\"true\"", 1)):
            with self.assertRaises(ValueError):
                old_io.normalize_remote_reporter_source(bad)
        self.assertEqual(old_io.PACKAGE, "io.github.apdelrahman1911.nativecmpkit.verification.iodocuments")
        self.assertNotIn(remote.PACKAGE, old_io.SOURCE_FILES)
        with self.assertRaises(ValueError):
            old_io.metadata_apk(TREE, fixture=remote.FIXTURE, package=remote.PACKAGE)
        receipt = deepcopy(self.source)
        receipt["source_inputs"].pop("scripts/ci/test_android_io_reporter_manifest_union.py")
        receipt["source_inputs_sha256"] = lt.input_digest(receipt["source_inputs"])
        with self.assertRaises(ValueError):
            remote.validate_source_receipt(receipt)
        receipt = deepcopy(self.source)
        receipt["native_or_compile_success_inferred"] = True
        with self.assertRaises(ValueError):
            remote.validate_source_receipt(receipt)

    def test_remote_prepare_source_apk_signer_install_readback_precedes_reporter_and_native(self):
        syntax = ast.parse((TREE / "scripts/ci/android_io_remote_documents.py").read_text())
        owner = next(node for node in syntax.body if isinstance(node, ast.ClassDef) and node.name == "OwnedRemoteIoDocuments")
        method = next(node for node in owner.body if isinstance(node, ast.FunctionDef) and node.name == "prepare")
        body = ast.get_source_segment((TREE / "scripts/ci/android_io_remote_documents.py").read_text(), method)
        positions = [body.index(token) for token in ("source_contract(self.root)", "self.inspect_apk(apk)",
                     "self.control(\"install\"", "actual = self.readback()", 'self.receipt["prepare_status"] = "passed"')]
        self.assertEqual(sorted(positions), positions)
        self.assertIn("source_contract(self.root) == self.receipt[\"source_contract\"]", body)
        self.assertIn("finally:", body)
        self.assertIn('lt.write_json(self.output / "receipt.json", self.receipt)', body)
        result, events = self.orchestration()
        self.assertEqual(["remote-owner-assigned", "remote-prepare", "synthetic-signer-install-readback-complete",
                          "apk-assembly", "synthetic-native-dispatch", "remote-close", "owned-child-shutdown", "owned-guest-disposal"],
                         [event for event in events if event in {"remote-owner-assigned", "remote-prepare", "synthetic-signer-install-readback-complete",
                          "apk-assembly", "synthetic-native-dispatch", "remote-close", "owned-child-shutdown", "owned-guest-disposal"}])
        self.assertTrue(result["passed"], "Synthetic controller routing only, not an actual native acceptance")
        self.assertNotIn("camera_developer_prerequisite", result)
        self.assertNotIn("camera_guest_disposal", result)
        self.assertFalse(result["remote_io_documents"]["native_or_consumer_success_inferred"])
        assembly = lt.gradle_command("android-device", self.plans["android-io-controlled-remote"],
                                    root=TREE, android_serial=controller.SERIAL, for_assembly=True)
        self.assertIn(":calf-io:assembleAndroidDeviceTest", assembly)
        self.assertNotIn(":calf-io:connectedAndroidDeviceTest", assembly)
        self.assertNotIn("-Pandroid.testInstrumentationRunnerArguments.nativecmpkitOwnedRemoteIoDocuments=true", assembly)
        with self.assertRaises(ValueError):
            lt.gradle_command("android-device", self.plans["android-io-controlled-remote"], root=TREE,
                android_serial=controller.SERIAL, for_assembly=True, android_io_remote_documents_receipt=self.prepared())

    def test_partial_prepare_compile_failure_and_cleanup_failure_preserve_facts_and_owned_guest_disposal(self):
        for failure in ("partial-prepare", "reporter-compile", "cleanup"):
            with self.subTest(synthetic_failure=failure):
                result, events = self.orchestration(failure)
                self.assertFalse(result["passed"])
                self.assertIn("remote-close", events)
                self.assertIn("owned-child-shutdown", events)
                self.assertIn("owned-guest-disposal", events)
                self.assertEqual(self.prepared()["source_apk_sha256"], result["remote_io_documents"]["source_apk_sha256"])
                self.assertEqual(self.source, result["remote_io_documents"]["source_contract"])
                self.assertTrue(result["remote_source_unchanged_after_cleanup"], "Synthetic held source fact does not erase failed prepare/native/cleanup")
                self.assertEqual("passed", result["remote_guest_disposal"]["disposal_status"])
                self.assertTrue(result["remote_guest_disposal"]["identity_confined_disposal"])
                self.assertFalse(result["remote_io_documents"]["native_or_consumer_success_inferred"])
                if failure == "partial-prepare":
                    self.assertEqual("failed", result["remote_io_documents"]["prepare_status"])
                    self.assertNotIn("apk-assembly", events)
                if failure != "cleanup":
                    self.assertNotIn("synthetic-native-dispatch", events)
                else:
                    self.assertEqual("failed", result["remote_io_documents"]["cleanup_status"])
                    self.assertFalse(result["remote_io_documents"]["owned_recipient_removed"])
                    self.assertEqual("RuntimeError", result["remote_io_documents"]["cleanup_error"])

    def test_remote_receipt_source_union_and_wrong_old_helper_cannot_satisfy_native_gate(self):
        plan = self.plans["android-io-controlled-remote"]
        for bad in (None, {}, self.prepared() | {"package": old_io.PACKAGE},
                    self.prepared() | {"source_fixture": old_io.FIXTURE},
                    self.prepared() | {"recipient_installed": False}, self.prepared() | {"verification_api_level": 34},
                    self.prepared() | {"verification_api_level": 35.0}):
            with self.subTest(receipt_kind=type(bad).__name__), self.assertRaises(ValueError):
                lt.gradle_command("android-device", plan, root=TREE, android_serial=controller.SERIAL,
                                  android_io_remote_documents_receipt=bad)
        bad = self.prepared()
        bad["source_contract"]["source_inputs"].pop("scripts/ci/android_device_tests.py")
        bad["source_contract"]["source_inputs_sha256"] = lt.input_digest(bad["source_contract"]["source_inputs"])
        with self.assertRaises(ValueError):
            lt.gradle_command("android-device", plan, root=TREE, android_serial=controller.SERIAL,
                              android_io_remote_documents_receipt=bad)
        with self.assertRaises(ValueError):
            lt.gradle_command("android-device", plan, root=TREE, android_serial=controller.SERIAL,
                              android_io_documents_receipt=self.prepared())
        unrelated = lt.plan(TREE, "android-device", only_modules=("calf-io",), focus=lt.ANDROID_IO_OVERSIZE_FOCUS)
        self.assertFalse(lt.android_io_remote_documents_required(unrelated))
        with self.assertRaises(ValueError):
            lt.gradle_command("android-device", unrelated, root=TREE, android_serial=controller.SERIAL,
                              android_io_remote_documents_receipt=self.prepared())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_remote_fixture(root)
            path = root / "scripts/ci/android_device_tests.py"
            path.write_bytes(path.read_bytes() + b"\n# uncertified controller drift\n")
            with self.assertRaises(ValueError):
                lt.gradle_command("android-device", plan, root=root, android_serial=controller.SERIAL,
                                  android_io_remote_documents_receipt=self.prepared())
        run = function_source("scripts/ci/library_tests.py", "run")
        self.assertIn('context.get("android_emulator", {}).get("api_level") != "35"', run)
        self.assertIn('receipt["android_io_remote_documents"] = dict(android_io_remote_documents_receipt)', run)
        self.assertIn('receipt["remote_source_capture_error"]', run)
        self.assertLess(run.index('context.get("android_emulator", {}).get("api_level")'), run.index("execution = execute("))

    def test_exact_fresh_xml_one_report_has_only_selected_identities_and_duplicate_skip_stale_unrelated_refuses(self):
        def xml(cases):
            suite = ET.Element("testsuite", {"tests": str(len(cases)), "failures": "0", "errors": "0",
                                             "skipped": str(sum(case.get("skip", False) for case in cases))})
            for case in cases:
                item = ET.SubElement(suite, "testcase", {"classname": case["classname"], "name": case["name"]})
                if case.get("skip"):
                    ET.SubElement(item, "skipped")
            return ET.tostring(suite)
        def collect(plan, cases, *, stale=False, extra=False, host="Linux", marker=1):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                folder = root / plan["expected"][0]["report_directory"]
                folder.mkdir(parents=True)
                path = folder / "TEST-controlled-remote.xml"
                path.write_bytes(xml(cases))
                now = time.time_ns()
                os.utime(path, ns=(now - 20_000_000_000 if stale else now,) * 2)
                if extra:
                    (folder / "TEST-extra.xml").write_bytes(xml([]))
                return lt.collect_reports(root, plan, now, now, Counter({plan["expected"][0]["task"]: marker}), host_system=host)
        for focus, plan in self.plans.items():
            cases = list(remote.identities(focus))
            result = collect(plan, cases)
            self.assertFalse(result["errors"])
            self.assertEqual(len(cases), result["totals"]["passed"])
            self.assertEqual(1, len(result["modules"][0]["reports"]))
            negatives = (
                (cases + [dict(cases[0])], {}), (cases[:-1], {}),
                ([dict(case, skip=True) if index == 0 else dict(case) for index, case in enumerate(cases)], {}),
                (cases + [{"classname": remote.CLASS, "name": "foreign"}], {}),
                (cases, {"stale": True}), (cases, {"extra": True}), (cases, {"host": "Darwin"}), (cases, {"marker": 0}),
            )
            for bad, options in negatives:
                with self.subTest(focus=focus, cases=len(bad), options=tuple(options)):
                    self.assertTrue(collect(plan, bad, **options)["errors"], "Synthetic rejected XML cannot satisfy the native outcome gate")

    def test_finite_workflow_one_api35_row_permissions_and_sdk_recipe_do_not_mutate_old_profiles(self):
        profiles = set(lt.ANDROID_IO_REMOTE_FOCUSES)
        for focus in profiles:
            expected = dict(workflow_matrix.SLOTS[-1], **{"test-modules": "calf-io", "test-focus": focus})
            self.assertEqual(("android-device-api35",), workflow_matrix.PROFILES[focus])
            self.assertEqual("calf-io", workflow_matrix.MODULE_SUBSETS[focus])
            self.assertEqual({"include": [expected]}, workflow_matrix.matrix(focus))
        self.assertEqual(11, len(workflow_matrix.matrix("all")["include"]))
        workflow = (TREE / ".github/workflows/gradle.yml").read_bytes()
        before = projection.current_source_before_remote_routing(".github/workflows/gradle.yml", workflow)
        from tooling_recovery671_source_projection import source_before_tooling671, source_before_callback_composition680
        owning_workflow = source_before_callback_composition680(
            ".github/workflows/gradle.yml", source_before_tooling671(".github/workflows/gradle.yml", workflow))
        restored = owning_workflow.decode()
        choice = "android-io-controlled-remote, android-io-controlled-remote-positive, android-io-controlled-remote-cancel, "
        self.assertEqual(1, restored.count(choice))
        restored = restored.replace(choice, "", 1)
        for focus in lt.ANDROID_IO_REMOTE_FOCUSES:
            branch = " || inputs.profile == '" + focus + "'"
            self.assertEqual(1, restored.count(branch))
            restored = restored.replace(branch, "", 1)
        self.assertEqual(before, restored.encode(), "Only choices and the exact existing official SDK recipe may differ")
        source = workflow.decode()
        sdk_line = next(line for line in source.splitlines() if line.lstrip().startswith("packages: ${{"))
        for focus in profiles:
            self.assertIn("inputs.profile == '" + focus + "'", sdk_line)
        self.assertIn("platforms;android-37.0 build-tools;36.0.0 emulator system-images;android-35;google_apis;x86_64", sdk_line)
        choices = re.search(r"options: \[([^\n]+)\]", source).group(1)
        self.assertEqual(set(workflow_matrix.PROFILES), {value.strip() for value in choices.split(",")})
        artifact = source.split("- name: Keep receipts and actual selected-task XML", 1)[1].split("\n  consumer-core-io:", 1)[0]
        for forbidden in (".apk", ".aar", ".jar", "*.log", "*.pb"):
            self.assertNotIn(forbidden, artifact)
        self.assertIn("/library/*.json", artifact)
        self.assertIn("TEST-*.xml", artifact)
        self.assertIn("contents: read", source)
