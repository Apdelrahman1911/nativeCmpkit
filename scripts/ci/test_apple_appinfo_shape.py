"""New synthetic exact-install/privacy controls; ZERO Apple SDK/native queries."""
from dataclasses import replace
import copy
import hashlib
import json
import os
from pathlib import Path
import plistlib
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import apple_appinfo_capability as capability
import apple_appinfo_shape as shape
import ios_ui_application as application
import library_tests as lt

DEVICE = "11111111-1111-1111-1111-111111111111"
REVISION = "a" * 40


class AppleAppinfoShapeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="synthetic-appinfo-shape-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.developer = self.root / "synthetic-selected-developer"
        self.developer.mkdir()
        self.paths = {"xcrun": Path("/usr/bin/xcrun"), "simctl": Path("/synthetic-selected-tool/simctl"),
                      "xcodebuild": Path("/synthetic-selected-tool/xcodebuild")}
        self.identities = {name: {"basename": name, "sha256": hashlib.sha256(name.encode()).hexdigest(),
                                 "bytes": 100, "path_sha256": "c" * 64, "canonical_path_sha256": "d" * 64}
                           for name in self.paths}
        self.host = {"system": "Darwin", "architecture": "arm64", "python": "synthetic"}
        self.xcode = {"version": "26.6", "build": "17F113"}
        # All tool/runtime/help records in this suite are simulated. Only the
        # production collector pins the accepted actual006 receipt hash.
        accepted = {"capability_available": True, "owned_private_output_removed": True,
                    "help": {"known_syntax": shape.ACCEPTED_SYNTAX}, "appinfo_output_schema_observed": False,
                    "subsequent_appinfo_ready": False, "host": self.host, "xcode": self.xcode,
                    "developer_directory_sha256": shape.digest(str(self.developer).encode()),
                    "developer_directory_canonical_sha256": shape.digest(str(self.developer.resolve()).encode()),
                    "tool_identities": self.identities}
        self.accepted_bytes = json.dumps(accepted, sort_keys=True).encode()
        for mocker in (
                patch.object(lt, "ROOT", self.root),
                patch.object(shape, "ACCEPTED_HELP_RECEIPT_SHA256", shape.digest(self.accepted_bytes)),
                patch.object(capability, "host", return_value=self.host),
                patch.object(shape.shutil, "disk_usage", return_value=SimpleNamespace(free=16 * 1024**3)),
                patch.object(capability, "tool_identity", side_effect=lambda path, name: copy.deepcopy(self.identities[name]))):
            mocker.start()
            self.addCleanup(mocker.stop)
        self.context = self.make_context("b" * 32)
        self.calls = []

    def make_context(self, token):
        bundle = "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + REVISION[:12] + ".t" + token
        output = self.root / "build/ci-verification/synthetic-ios/native-ui-application" / token
        output.mkdir(parents=True)
        installed = self.root / "synthetic-installed" / token / "NativeCmpkitLibraryTests.app"
        local = output / "NativeCmpkitLibraryTests.app"
        body = b"Synthetic signed executable; no native binary"
        info = plistlib.dumps(application.app_information(bundle, "15.0.0"), sort_keys=True)
        for directory in (installed, local):
            directory.mkdir(parents=True)
            (directory / application.APP_EXECUTABLE).write_bytes(body)
            (directory / "Info.plist").write_bytes(info)
        container_command = ["/usr/bin/xcrun", "simctl", "get_app_container", DEVICE, bundle, "app"]
        return shape.OwnedInstallation(
            self.root, output, DEVICE, bundle, token, REVISION, shape.digest(body), shape.digest(info),
            {"source_revision": REVISION, "source_tree_dirty": False, "host": copy.deepcopy(self.host),
             "xcode": copy.deepcopy(self.xcode), "simulator": {"udid": DEVICE, "state": "Booted"}},
            subprocess.CompletedProcess(container_command, 2, b"", b"(domain=NSPOSIXErrorDomain, code=2)"),
            subprocess.CompletedProcess(["/usr/bin/xcrun", "simctl", "install", DEVICE, str(local)], 0, b"", b""),
            subprocess.CompletedProcess(container_command, 0, str(installed).encode() + b"\n", b""))

    def collect(self, result=None, *, context=None, capture=None):
        def synthetic_capture(command, root, timeout):
            self.calls.append((command, root, timeout))
            return result or capability.Result(0, b"arbitrary unknown serializer\n", b"", None)
        return shape.collect(context or self.context, capability_bytes=self.accepted_bytes,
                             tool_paths=self.paths, developer=self.developer,
                             capture=capture or synthetic_capture)

    def assert_unverified(self, receipt):
        for name in ("appinfo_output_schema_observed", "subsequent_appinfo_ready", "registration_observed",
                     "root_cause_proven", "native_functionality_verified", "profile_passed", "packages_published",
                     "release_readiness_certified", "raw_payload_keys_values_paths_or_inventory_uploaded"):
            self.assertIs(receipt[name], False)
        self.assertIsNone(receipt["registered_container_matches_verified_container"])
        self.assertIsNone(receipt["registered_executable_identity_verified"])

    def test_one_exact_current_install_query_emits_only_hashes_types_fixed_names_and_counts(self):
        private_path = str(Path(self.context.container.stdout.decode().strip()))
        body = ("CFBundleIdentifier = " + self.context.bundle + ";\n" +
                "CFBundleExecutable = /private/never-emit-this/owned-executable;\n" +
                "SecretUnknownRuntimeKey = " + private_path + ";\n").encode()
        receipt = self.collect(capability.Result(0, body, b"", None))
        self.assertEqual("observed-bounded-lexical-shape", receipt["status"])
        self.assertEqual([((*shape.QUERY_PREFIX, DEVICE, self.context.bundle), self.root, 15)], self.calls)
        self.assertEqual(1, receipt["query_count"])
        summary = receipt["streams"]["stdout"]
        self.assertEqual(shape.digest(body), summary["sha256"])
        self.assertEqual(1, summary["allowlisted_name_literal_counts"]["CFBundleIdentifier"])
        self.assertEqual(1, summary["allowlisted_name_literal_counts"]["CFBundleExecutable"])
        self.assertEqual(3, summary["nonempty_line_count"])
        self.assertIs(receipt["owned_private_output_removed"], True)
        self.assertFalse((self.context.output / shape.PRIVATE_DIRECTORY).exists())
        public = json.dumps(receipt)
        for text in (self.context.bundle, DEVICE, private_path, "/private/never-emit-this", "SecretUnknownRuntimeKey"):
            self.assertNotIn(text, public)
        self.assertEqual(receipt, json.loads((self.context.output / shape.RECORD_NAME).read_bytes()))
        self.assertEqual(0o600, (self.context.output / shape.RECORD_NAME).stat().st_mode & 0o777)
        self.assert_unverified(receipt)

    def test_candidate_serializer_bytes_never_accept_any_payload_schema_or_duplicate_field_semantics(self):
        for index, body in enumerate((b'{"CFBundleIdentifier":"untrusted", "CFBundleIdentifier":"duplicate"}\n',
                                     b'<?xml version="1.0"?><plist><dict><key>CFBundleIdentifier</key></dict></plist>',
                                     b'{ CFBundleExecutable = "untrusted"; CFBundlePackageType = APPL; }\n',
                                     b'CFBundleIdentifierX prefixCFBundleIdentifier CFBundleIdentifier\n')):
            with self.subTest(index=index):
                context = self.make_context(f"{index + 1:032x}")
                receipt = self.collect(capability.Result(0, body, b"", None), context=context)
                self.assertEqual("observed-bounded-lexical-shape", receipt["status"])
                self.assertIs(receipt["streams"]["stdout"]["serializer_or_field_schema_accepted"], False)
                if index == 0:
                    self.assertEqual(2, receipt["streams"]["stdout"]["allowlisted_name_literal_counts"]["CFBundleIdentifier"])
                if index == 3:
                    self.assertEqual(1, receipt["streams"]["stdout"]["allowlisted_name_literal_counts"]["CFBundleIdentifier"])
                self.assert_unverified(receipt)

    def test_nonzero_empty_two_streams_nontext_boolean_exit_and_oversize_remain_unavailable(self):
        results = (capability.Result(1, b"payload", b"", None), capability.Result(0, b"", b"", None),
                   capability.Result(0, b"payload", b"diagnostic", None), capability.Result(0, b"\xff", b"", None),
                   capability.Result(0, b"bplist00\0binary", b"", None), capability.Result(True, b"payload", b"", None),
                   capability.Result(0, b"x" * (capability.MAX_COMMAND_BYTES + 1), b"", None))
        for index, result in enumerate(results):
            with self.subTest(index=index):
                receipt = self.collect(result, context=self.make_context(f"{index + 20:032x}"))
                self.assertEqual("unavailable", receipt["status"])
                self.assertIs(receipt["owned_private_output_removed"], True)
                self.assert_unverified(receipt)

    def test_old_bundle_default_device_wrong_source_foreign_install_and_identity_drift_never_query(self):
        changes = (
            {"bundle": self.context.bundle + ".old"}, {"device": "Booted"}, {"source_revision": "c" * 40},
            {"token": "c" * 32}, {"signed_hash": "c" * 64},
            {"preexisting": subprocess.CompletedProcess(self.context.preexisting.args, 0, b"foreign", b"")},
            {"install": subprocess.CompletedProcess(self.context.install.args, 1, b"", b"")},
            {"container": subprocess.CompletedProcess(["/usr/bin/xcrun", "simctl", "get_app_container", DEVICE,
                                                        self.context.bundle + ".foreign", "app"], 0,
                                                       self.context.container.stdout, b"")},
            {"runtime_before": {**self.context.runtime_before, "source_tree_dirty": True}},
            {"runtime_before": {**self.context.runtime_before, "simulator": {"udid": DEVICE, "state": "Shutdown"}}},
            {"runtime_before": {**self.context.runtime_before, "xcode": {"version": "26.6", "build": "foreign"}}},
        )
        for index, fields in enumerate(changes):
            with self.subTest(index=index):
                receipt = self.collect(context=replace(self.context, **fields))
                self.assertEqual("unavailable", receipt["status"])
                self.assertIs(receipt["query_attempted"], False)
                self.assert_unverified(receipt)
        self.assertEqual([], self.calls)
        with patch.object(capability, "tool_identity", return_value={"sha256": "foreign"}):
            self.assertIs(self.collect()["query_attempted"], False)
        self.assertEqual([], self.calls)

    def test_exclusive_sanitized_record_refuses_a_second_query_even_after_private_cleanup(self):
        first = self.collect()
        second = self.collect()
        self.assertEqual("observed-bounded-lexical-shape", first["status"])
        self.assertEqual("unavailable", second["status"])
        self.assertIs(second["query_attempted"], False)
        self.assertEqual(1, len(self.calls))
        self.assertEqual(first, json.loads((self.context.output / shape.RECORD_NAME).read_bytes()))
        self.assert_unverified(second)

    def test_low_disk_reserve_or_exhausted_observation_budget_prevents_the_one_query(self):
        with patch.object(shape.shutil, "disk_usage", return_value=SimpleNamespace(free=8192 * 1024**2)):
            receipt = self.collect()
        self.assertEqual("eight_GiB_capture_and_record_reserve_required", receipt["error_guard"])
        self.assertIs(receipt["query_attempted"], False)
        self.assertEqual([], self.calls)
        with patch.object(shape.time, "monotonic", side_effect=(0, 100, 100)):
            receipt = self.collect()
        self.assertEqual("observation_budget_exhausted_before_query", receipt["error_guard"])
        self.assertIs(receipt["query_attempted"], False)
        self.assertIs(receipt["budget_exhausted"], True)
        self.assertEqual([], self.calls)
        self.assert_unverified(receipt)

    def test_partial_owned_capture_metadata_is_saved_but_exit_zero_never_accepts_it(self):
        for index, reason in enumerate(("timeout", "output-bound", "owned-control-refusal")):
            context = self.make_context(f"{index + 40:032x}")
            def partial_capture(command, root, timeout):
                self.calls.append((command, root, timeout))
                error = capability.CapabilityError("owned_control_leader_unavailable")
                error.control_result = capability.Result(0, b"bounded partial payload", b"", reason)
                raise error
            receipt = self.collect(context=context, capture=partial_capture)
            self.assertEqual("unavailable", receipt["status"])
            self.assertEqual(reason, receipt["query"]["stop_reason"])
            self.assertEqual(shape.digest(b"bounded partial payload"), receipt["query"]["stdout_sha256"])
            self.assertIs(receipt["owned_private_output_removed"], True)
            self.assert_unverified(receipt)

    def test_foreign_private_membership_and_changed_file_modes_are_preserved_and_refuse_acceptance(self):
        def foreign_capture(command, root, timeout):
            (self.context.output / shape.PRIVATE_DIRECTORY / "foreign").write_bytes(b"synthetic foreign file")
            return capability.Result(0, b"payload", b"", None)
        receipt = self.collect(capture=foreign_capture)
        self.assertEqual("unavailable", receipt["status"])
        self.assertIs(receipt["owned_private_output_removed"], False)
        self.assertTrue((self.context.output / shape.PRIVATE_DIRECTORY / "foreign").exists())
        self.assertTrue((self.context.output / shape.PRIVATE_DIRECTORY / "stdout").exists())
        self.assert_unverified(receipt)
        context = self.make_context("e" * 32)
        original = shape.lexical_summary
        def changed_mode(body):
            target = context.output / shape.PRIVATE_DIRECTORY / "stdout"
            if target.exists():
                target.chmod(0o644)
            return original(body)
        with patch.object(shape, "lexical_summary", side_effect=changed_mode):
            receipt = self.collect(context=context)
        self.assertEqual("unavailable", receipt["status"])
        self.assertIs(receipt["owned_private_output_removed"], False)
        self.assertTrue((context.output / shape.PRIVATE_DIRECTORY / "stdout").exists())
        self.assert_unverified(receipt)

    def test_installed_bytes_changed_during_capture_and_raw_oserror_never_become_readiness(self):
        def drift_capture(command, root, timeout):
            container = Path(self.context.container.stdout.decode().strip())
            (container / application.APP_EXECUTABLE).write_bytes(b"changed synthetic executable")
            return capability.Result(0, b"payload", b"", None)
        receipt = self.collect(capture=drift_capture)
        self.assertEqual("unavailable", receipt["status"])
        self.assertEqual("installed_owned_bytes_required", receipt["error_guard"])
        self.assertIs(receipt["owned_private_output_removed"], True)
        self.assert_unverified(receipt)
        context = self.make_context("f" * 32)
        def unavailable_capture(command, root, timeout):
            raise OSError("/private/never-export-this exception payload")
        receipt = self.collect(context=context, capture=unavailable_capture)
        self.assertEqual("unavailable", receipt["status"])
        self.assertEqual("OSError", receipt["error_type"])
        self.assertNotIn("never-export-this", json.dumps(receipt))
        self.assertIs(receipt["owned_private_output_removed"], True)
        self.assert_unverified(receipt)


if __name__ == "__main__":
    unittest.main()
