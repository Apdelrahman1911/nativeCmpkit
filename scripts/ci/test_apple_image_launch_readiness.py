"""NEW syntax/owned-query/launch-hook models; ZERO Apple, native or SDK work.

Only tiny synthetic installed files are real. All host/tool/control/launch
boundaries are mocked. Prior accepted test methods are never selected; a prior
transport fixture is used only as an owned synthetic scaffold for NEW hooks.
"""
from dataclasses import replace
import copy
import datetime as dt
import json
import os
from pathlib import Path
import plistlib
import struct
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import apple_appinfo_capability as capability
import apple_appinfo_shape as shape
import apple_appinfo_shape_route as route
import apple_image_launch_readiness as readiness
import ios_ui_application as application
import library_tests as lt
import test_ios_ui_application as transport_fixtures

DEVICE = "11111111-1111-1111-1111-111111111111"
REVISION = "a" * 40
PRIVATE = "private-unknown-metadata-or-path-must-not-be-uploaded"


class SerializedStructureObservationTests(unittest.TestCase):
    def check_structure(self, body, format_name):
        observed = readiness.serialized_structure(body)
        self.assertEqual("observed-complete-serialized-structure", observed["status"])
        self.assertIn(format_name, observed["complete_payload_grammar_matches"])
        self.assertFalse(observed["serializer_implementation_identified"])
        self.assertFalse(observed["appinfo_output_schema_observed"])
        self.assertFalse(observed["registration_observed"])
        self.assertFalse(observed["structure"]["registration_field_semantics_verified"])
        self.assertFalse(observed["structure"]["field_absence_or_registration_absence_proven"])
        self.assertNotIn(PRIVATE, json.dumps(observed))
        return observed["structure"]

    def test_complete_json_pairs_distinguish_real_keys_from_literals_without_registration_semantics(self):
        body = ('{"\\u0043FBundleIdentifier":"' + PRIVATE + '","CFBundleIdentifier":false,'
                '"Unknown' + PRIVATE + '":{"CFBundleExecutable":[1,2.5,null,true]},'
                '"literal":"CFBundlePackageType"}').encode()
        structure = self.check_structure(body, "json")
        self.assertEqual(4, structure["root_dictionary_key_occurrences"])
        self.assertEqual(1, structure["duplicate_dictionary_key_occurrences"])
        fields = structure["own_plist_name_key_structures"]
        self.assertEqual(2, fields["CFBundleIdentifier"]["root_key_occurrences"])
        self.assertEqual({"string": 1, "boolean": 1}, fields["CFBundleIdentifier"]["value_kind_counts"])
        self.assertEqual(1, fields["CFBundleExecutable"]["nested_key_occurrences"])
        self.assertEqual(0, fields["CFBundlePackageType"]["root_key_occurrences"])

    def test_complete_ascii_dictionary_handles_whole_comments_escapes_arrays_and_hex_data(self):
        body = ('/*' + PRIVATE + '*/ { "\\U0043FBundleIdentifier" = "' + PRIVATE + '"; '
                'CFBundleIdentifier = bare-atom; Unknown = ({ CFBundleExecutable = "' + PRIVATE + '"; }, '
                '"CFBundlePackageType", <cafe babe>,); } // complete tail\n').encode()
        structure = self.check_structure(body, "ascii-plist")
        self.assertEqual(1, structure["duplicate_dictionary_key_occurrences"])
        fields = structure["own_plist_name_key_structures"]
        self.assertEqual(2, fields["CFBundleIdentifier"]["root_key_occurrences"])
        self.assertEqual({"string": 2}, fields["CFBundleIdentifier"]["value_kind_counts"])
        self.assertEqual(1, fields["CFBundleExecutable"]["nested_key_occurrences"])
        self.assertEqual(1, structure["value_kind_counts"]["data"])
        self.assertEqual(0, fields["CFBundlePackageType"]["nested_key_occurrences"])

    def test_complete_xml_dictionary_preserves_duplicates_and_observes_only_fixed_types(self):
        body = plistlib.dumps({"CFBundleIdentifier": PRIVATE, "Unknown": [True, 12, 2.5, b"data", dt.datetime(2026, 1, 1)]})
        body = body.replace(b"</dict>", b"<key>CFBundleIdentifier</key><string>" + PRIVATE.encode() + b"</string></dict>")
        structure = self.check_structure(body, "xml-plist-v1")
        self.assertEqual(1, structure["duplicate_dictionary_key_occurrences"])
        self.assertEqual(2, structure["own_plist_name_key_structures"]["CFBundleIdentifier"]["root_key_occurrences"])
        for kind in ("boolean", "integer", "real", "data", "date"):
            self.assertEqual(1, structure["value_kind_counts"][kind])

    def test_complete_binary_object_table_checks_all_objects_and_preserves_duplicate_key_references(self):
        body = plistlib.dumps({"CFBundleIdentifier": PRIVATE, "CFBundleExecutable": "unicode-\U0001f4f1",
                              "Other": [True, 12, 2.5, b"data", dt.datetime(2026, 1, 1)]}, fmt=plistlib.FMT_BINARY)
        structure = self.check_structure(body, "binary-plist-v00")
        self.assertEqual(3, structure["root_dictionary_key_occurrences"])
        self.assertEqual(1, structure["own_plist_name_key_structures"]["CFBundleExecutable"]["root_key_occurrences"])
        duplicate = bytearray(plistlib.dumps({"CFBundleIdentifier": PRIVATE, "CFBundleExecutable": "unused"}, fmt=plistlib.FMT_BINARY))
        self.assertEqual(0xD2, duplicate[8])
        self.assertEqual(1, duplicate[-25])  # Generated tiny fixture reference width.
        duplicate[10] = duplicate[9]
        structure = self.check_structure(bytes(duplicate), "binary-plist-v00")
        self.assertEqual(1, structure["duplicate_dictionary_key_occurrences"])
        self.assertEqual(2, structure["own_plist_name_key_structures"]["CFBundleExecutable"]["root_key_occurrences"])
        width = duplicate[-26]
        count, top, table = struct.unpack(">QQQ", duplicate[-24:])
        unused = int.from_bytes(duplicate[table + 2 * width:table + 3 * width], "big")
        duplicate[unused] = 0xE0
        observed = readiness.serialized_structure(bytes(duplicate))
        self.assertEqual("unavailable", observed["status"], "Unreachable malformed objects are not ignored")
        self.assertIsNone(observed["structure"])

    def test_incomplete_unknown_nonstandard_or_entity_payloads_never_turn_literal_counts_into_fields(self):
        bodies = (b"arbitrary unknown serializer", b"CFBundleIdentifier = unframed;\n",
                  b'{ CFBundleIdentifier = "' + PRIVATE.encode() + b'"; ', b'{ Key = <abc>; }',
                  b'{ Key = "value"; } trailing-private', b'{ Key = "\\q"; }',
                  b'{ Key = "\\Udd00"; }', b'{ Key = value; /* unterminated',
                  b'{"CFBundleIdentifier": NaN}', b'{"CFBundleIdentifier":"x"} trailing',
                  b'<?xml version="1.0"?><plist version="1.0"><dict><key>x</key></dict></plist>',
                  b'<!DOCTYPE plist [<!ENTITY x "' + PRIVATE.encode() + b'">]><plist version="1.0"><string>&x;</string></plist>',
                  b'<plist version="1.0"><data>invalid?base64</data></plist>',
                  b'bplist00\0not-a-complete-object-table', b'{"key":"nul\0"}')
        for body in bodies:
            with self.subTest(body_hash=shape.digest(body)):
                observed = readiness.serialized_structure(body)
                self.assertEqual("unavailable", observed["status"])
                self.assertIsNone(observed["structure"])
                self.assertFalse(observed["appinfo_output_schema_observed"])
                self.assertNotIn(PRIVATE, json.dumps(observed))

    def test_complete_empty_ambiguous_grammar_non_dictionary_and_all_bounds_remain_nonsemantic(self):
        ambiguous = readiness.serialized_structure(b"{}")
        self.assertEqual(["json", "ascii-plist"], ambiguous["complete_payload_grammar_matches"])
        self.assertFalse(ambiguous["unique_representation_format_observed"])
        self.assertFalse(ambiguous["structure"]["field_absence_or_registration_absence_proven"])
        array = readiness.serialized_structure(b'["CFBundleIdentifier"]')
        self.assertEqual("array", array["structure"]["root_kind"])
        self.assertIsNone(array["structure"]["root_dictionary_key_occurrences"])
        cases = (("MAX_DEPTH", 3, b'{"key":' * 6 + b'"' + PRIVATE.encode() + b'"' + b'}' * 6),
                 ("MAX_NODES", 8, json.dumps({str(index): PRIVATE for index in range(10)}).encode()))
        for constant, value, body in cases:
            with patch.object(readiness, constant, value):
                observed = readiness.serialized_structure(body)
            self.assertEqual("unavailable", observed["status"])
            self.assertIsNone(observed["structure"])
        observed = readiness.serialized_structure(b"x" * (capability.MAX_COMMAND_BYTES + 1))
        self.assertEqual("unavailable", observed["status"])
        self.assertIsNone(observed["structure"])


class OwnedLaunchReadinessObservationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="synthetic-image-launch-readiness-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.developer = self.root / "synthetic-selected-developer"
        self.developer.mkdir()
        self.host = {"system": "Darwin", "architecture": "arm64", "python": "synthetic"}
        self.xcode = {"version": "26.6", "build": "17F113"}
        self.paths = {"developer": self.developer, "simctl": self.root / "synthetic-tools/simctl",
                      "xcodebuild": self.root / "synthetic-tools/xcodebuild"}
        self.identities = {name: {"basename": name, "bytes": 10, "sha256": shape.digest(name.encode()),
                                 "path_sha256": "c" * 64, "canonical_path_sha256": "d" * 64}
                           for name in ("xcrun", "simctl", "xcodebuild")}
        accepted = {"capability_available": True, "owned_private_output_removed": True,
                    "help": {"known_syntax": shape.ACCEPTED_SYNTAX}, "appinfo_output_schema_observed": False,
                    "subsequent_appinfo_ready": False, "host": self.host, "xcode": self.xcode,
                    "developer_directory_sha256": shape.digest(str(self.developer).encode()),
                    "developer_directory_canonical_sha256": shape.digest(str(self.developer.resolve()).encode()),
                    "tool_identities": self.identities}
        help_bytes = json.dumps(accepted, sort_keys=True).encode()
        path = self.root / route.HELP_RECEIPT
        path.parent.mkdir(parents=True)
        path.write_bytes(help_bytes)
        self.controls, self.captures = [], []
        for mocker in (patch.object(lt, "ROOT", self.root),
                       patch.object(shape, "ACCEPTED_HELP_RECEIPT_SHA256", shape.digest(help_bytes)),
                       patch.object(capability, "host", return_value=self.host),
                       patch.object(shape.shutil, "disk_usage", return_value=SimpleNamespace(free=16 * 1024**3)),
                       patch.object(capability, "tool_identity", side_effect=lambda path, name: copy.deepcopy(self.identities[name]))):
            mocker.start()
            self.addCleanup(mocker.stop)
        self.context = self.make_context("b" * 32)

    def make_context(self, token):
        bundle = "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + REVISION[:12] + ".t" + token
        output = self.root / "build/ci-verification/synthetic-ios/native-ui-application" / token
        output.mkdir(parents=True)
        installed = self.root / "synthetic-installed" / token / "NativeCmpkitLibraryTests.app"
        local = output / "NativeCmpkitLibraryTests.app"
        body = b"Synthetic signed bytes only; not native executable\n"
        info = plistlib.dumps(application.app_information(bundle, "15.0.0"), sort_keys=True)
        for directory in (installed, local):
            directory.mkdir(parents=True)
            (directory / application.APP_EXECUTABLE).write_bytes(body)
            (directory / application.APP_EXECUTABLE).chmod(0o755)
            (directory / "Info.plist").write_bytes(info)
        argv = ["/usr/bin/xcrun", "simctl", "get_app_container", DEVICE, bundle, "app"]
        return shape.OwnedInstallation(self.root, output, DEVICE, bundle, token, REVISION, shape.digest(body), shape.digest(info),
            {"source_revision": REVISION, "source_tree_dirty": False, "host": copy.deepcopy(self.host),
             "xcode": copy.deepcopy(self.xcode), "simulator": {"udid": DEVICE, "state": "Booted"}},
            subprocess.CompletedProcess(argv, 2, b"", b"(domain=NSPOSIXErrorDomain, code=2)"),
            subprocess.CompletedProcess(["/usr/bin/xcrun", "simctl", "install", DEVICE, str(local)], 0, b"", b""),
            subprocess.CompletedProcess(argv, 0, str(installed).encode() + b"\n", b""))

    def control(self, argv, root, timeout):
        self.controls.append((argv, root, timeout))
        name = next(name for name in self.paths if tuple(argv) == capability.COMMANDS[name])
        return capability.Result(0, str(self.paths[name]).encode() + b"\n", b"", None)

    def collect(self, context=None, result=None, capture=None):
        context = context or self.context
        def synthetic_capture(argv, root, timeout):
            self.captures.append((argv, root, timeout))
            return result if result is not None else capability.Result(0,
                b'{ CFBundleIdentifier = "' + PRIVATE.encode() + b'"; Unknown = "' + PRIVATE.encode() + b'"; }\n', b"", None)
        return readiness.observe(context, control=self.control, capture=capture or synthetic_capture)

    def executable(self, context=None):
        context = context or self.context
        return Path(context.container.stdout.decode().strip()) / application.APP_EXECUTABLE

    def assert_not_ready(self, receipt):
        for key in ("appinfo_output_schema_observed", "registration_observed", "launch_readiness_verified", "root_cause_proven",
                    "native_functionality_verified", "profile_passed", "packages_published", "release_readiness_certified",
                    "raw_payload_keys_values_paths_or_inventory_uploaded"):
            self.assertIs(receipt[key], False)
        self.assertIsNone(receipt["registered_container_matches_verified_container"])
        self.assertIsNone(receipt["registered_executable_identity_verified"])
        public = json.dumps(receipt)
        for value in (PRIVATE, self.context.bundle, DEVICE, str(self.executable().parent)):
            self.assertNotIn(value, public)

    def test_one_exact_query_brackets_host_access_and_full_installed_identity_without_exposing_metadata(self):
        observed = self.collect()
        self.assertEqual("observed-owned-prelaunch-structure", observed["status"])
        self.assertEqual([((*shape.QUERY_PREFIX, DEVICE, self.context.bundle), self.root, 15)], self.captures)
        self.assertEqual([capability.COMMANDS[name] for name in ("developer", "simctl", "xcodebuild")],
                         [call[0] for call in self.controls])
        self.assertEqual([15] * 3, [call[2] for call in self.controls])
        self.assertEqual(1, observed["query_count"])
        self.assertTrue(observed["installed_identity_stable_observed"])
        self.assertFalse(observed["installed_identity_drift_observed"])
        self.assertEqual(observed["installed_executable_before"], observed["installed_executable_after"])
        access = observed["installed_executable_before"]
        self.assertTrue(access["host_real_id_X_OK"])
        self.assertEqual("0755", access["permission_mode"])
        self.assertEqual("calling-host-process-real-ids", access["access_scope"])
        self.assertFalse(access["simulator_executable_acceptance_verified"])
        self.assertTrue(observed["owned_private_output_removed"])
        self.assertFalse((self.context.output / readiness.PRIVATE_DIRECTORY).exists())
        record = self.context.output / readiness.RECORD_NAME
        self.assertEqual(observed, json.loads(record.read_bytes()))
        self.assertEqual(0o600, record.stat().st_mode & 0o777)
        readiness.require_current_owned_identity(self.context, observed)
        self.assert_not_ready(observed)

    def test_exclusive_record_prevents_query_or_path_resolution_retry_after_private_removal(self):
        first = self.collect()
        original_record = (self.context.output / readiness.RECORD_NAME).read_bytes()
        second = self.collect()
        self.assertEqual("observed-owned-prelaunch-structure", first["status"])
        self.assertEqual("unavailable", second["status"])
        self.assertFalse(second["query_attempted"])
        self.assertEqual(1, len(self.captures))
        self.assertEqual(3, len(self.controls))
        self.assertEqual(original_record, (self.context.output / readiness.RECORD_NAME).read_bytes())
        self.assert_not_ready(second)

    def test_foreign_or_unbound_contexts_never_reach_executable_observer_or_any_sdk_query(self):
        changes = ({"bundle": self.context.bundle + ".foreign"}, {"device": "Booted"}, {"source_revision": "c" * 40},
                   {"token": "c" * 32}, {"install": subprocess.CompletedProcess(self.context.install.args, False, b"", b"")},
                   {"preexisting": subprocess.CompletedProcess(self.context.preexisting.args, 0, b"foreign", b"")},
                   {"runtime_before": {**self.context.runtime_before, "source_tree_dirty": True}},
                   {"container": subprocess.CompletedProcess([*self.context.container.args[:-2], "foreign", "app"], 0,
                                                             self.context.container.stdout, b"")})
        with patch.object(readiness, "installed_executable_observation", side_effect=AssertionError("Unbound read forbidden")):
            for change in changes:
                observed = self.collect(replace(self.context, **change))
                self.assertEqual("unavailable", observed["status"])
                self.assertFalse(observed["query_attempted"])
                self.assertIsNone(observed["installed_executable_before"])
        self.assertEqual([], self.captures)
        self.assertEqual([], self.controls)

    def test_unknown_nonzero_partial_empty_boolean_or_oversize_queries_stay_observational_and_private(self):
        results = (capability.Result(0, b"unknown serializer " + PRIVATE.encode(), b"", None),
                   capability.Result(1, PRIVATE.encode(), b"", None), capability.Result(0, b"", b"", None),
                   capability.Result(0, b"{}", PRIVATE.encode(), None), capability.Result(False, b"{}", b"", None),
                   capability.Result(0, b"x" * (capability.MAX_COMMAND_BYTES + 1), b"", None),
                   capability.Result(0, b"{ incomplete", b"", "timeout"))
        for index, result in enumerate(results):
            context = self.make_context(f"{index + 1:032x}")
            observed = self.collect(context, result)
            self.assertEqual("unavailable", observed["status"])
            self.assertFalse(observed["installed_identity_drift_observed"])
            self.assertTrue(observed["owned_private_output_removed"])
            readiness.require_current_owned_identity(context, observed)
            self.assert_not_ready(observed)
        context = self.make_context("f" * 32)
        def refused_capture(*_):
            error = capability.CapabilityError("owned_control_session_changed")
            error.control_result = capability.Result(None, b"{ partial " + PRIVATE.encode(), b"", "owned-control-refusal")
            raise error
        observed = self.collect(context, capture=refused_capture)
        self.assertTrue(observed["owned_control_cleanup_refused"])
        self.assertTrue(observed["owned_private_output_removed"])
        self.assertFalse(observed["installed_identity_drift_observed"])
        readiness.require_current_owned_identity(context, observed)
        self.assert_not_ready(observed)

    def test_negative_host_X_OK_is_measured_without_chmod_or_claiming_simulator_acceptance(self):
        executable = self.executable()
        executable.chmod(0o600)
        before = executable.stat()
        observed = self.collect()
        self.assertFalse(observed["installed_executable_before"]["host_real_id_X_OK"])
        self.assertEqual("0600", observed["installed_executable_after"]["permission_mode"])
        self.assertTrue(observed["installed_identity_stable_observed"])
        self.assertFalse(observed["installed_identity_drift_observed"])
        self.assertEqual(before.st_mode, executable.stat().st_mode)
        self.assertEqual(before.st_ctime_ns, executable.stat().st_ctime_ns)
        readiness.require_current_owned_identity(self.context, observed)
        self.assert_not_ready(observed)

    def test_mode_byte_symlink_and_open_read_identity_changes_refuse_original_launch_ownership(self):
        for index, change in enumerate(("mode", "bytes", "symlink")):
            context = self.make_context(f"{index + 40:032x}")
            executable = self.executable(context)
            def capture(*_, change=change, executable=executable):
                if change == "mode":
                    executable.chmod(0o700)
                elif change == "bytes":
                    executable.write_bytes(b"Different synthetic bytes\n")
                else:
                    target = context.output / "synthetic-foreign-target"
                    target.write_bytes(executable.read_bytes())
                    executable.unlink()
                    executable.symlink_to(target)
                return capability.Result(0, b"{}", b"", None)
            observed = self.collect(context, capture=capture)
            self.assertTrue(observed["installed_identity_drift_observed"])
            self.assertEqual("unavailable", observed["status"])
            with self.assertRaises(readiness.InstalledIdentityError):
                readiness.require_current_owned_identity(context, observed)
        context = self.make_context("e" * 32)
        def changed_read(descriptor, maximum):
            self.executable(context).write_bytes(b"Changed during exact read\n")
            return original_read(descriptor, maximum)
        original_read = os.read
        with patch.object(readiness.os, "read", side_effect=changed_read):
            observed = self.collect(context)
        self.assertTrue(observed["installed_identity_drift_observed"])
        self.assertEqual(0, observed["query_count"])

    def test_private_membership_change_refuses_deletion_and_never_exposes_foreign_file(self):
        def capture(*_):
            foreign = self.context.output / readiness.PRIVATE_DIRECTORY / "synthetic-foreign"
            foreign.write_bytes(PRIVATE.encode())
            return capability.Result(0, b"{}", b"", None)
        observed = self.collect(capture=capture)
        self.assertEqual("unavailable", observed["status"])
        self.assertFalse(observed["owned_private_output_removed"])
        self.assertEqual(PRIVATE.encode(), (self.context.output / readiness.PRIVATE_DIRECTORY / "synthetic-foreign").read_bytes())
        self.assertFalse(observed["installed_identity_drift_observed"])
        readiness.require_current_owned_identity(self.context, observed)
        self.assert_not_ready(observed)

    def test_tool_changes_and_resource_or_time_refusals_never_fabricate_readiness_or_suppress_owned_attempt(self):
        def changed_tool(*_):
            self.identities["simctl"] = {"basename": "simctl", "sha256": "e" * 64}
            return capability.Result(0, b"{}", b"", None)
        observed = self.collect(capture=changed_tool)
        self.assertEqual("unavailable", observed["status"])
        self.assertFalse(observed["installed_identity_drift_observed"])
        readiness.require_current_owned_identity(self.context, observed)
        context = self.make_context("d" * 32)
        with patch.object(shape.shutil, "disk_usage", return_value=SimpleNamespace(free=8 * 1024**3)):
            observed = self.collect(context)
        self.assertFalse(observed["query_attempted"])
        self.assertEqual("eight_GiB_observation_reserve_required", observed["error_guard"])
        self.assertFalse(observed["installed_identity_drift_observed"])
        readiness.require_current_owned_identity(context, observed)
        context = self.make_context("c" * 32)
        self.identities["simctl"] = copy.deepcopy(json.loads((self.root / route.HELP_RECEIPT).read_bytes())["tool_identities"]["simctl"])
        clock = {"time": 100.0}
        def expired_capture(*_):
            clock["time"] = 100.0 + capability.TOTAL_SECONDS + 1
            return capability.Result(0, b"{}", b"", None)
        with patch.object(readiness.time, "monotonic", side_effect=lambda: clock["time"]):
            observed = self.collect(context, capture=expired_capture)
        self.assertEqual("unavailable", observed["status"])
        self.assertTrue(observed["budget_exhausted"])
        self.assertFalse(observed["installed_identity_drift_observed"])
        readiness.require_current_owned_identity(context, observed)
        self.assert_not_ready(observed)


class ProfileRecoveryLaunchHookTests(unittest.TestCase):
    def owner(self):
        # Helpers only: no earlier accepted test method is selected or replayed.
        owner = transport_fixtures.OwnedApplicationTests(methodName="runTest")
        owner.setUp()
        owner.expected_timeout = 360
        self.addCleanup(owner.doCleanups)
        return owner

    def arguments(self, focus=lt.IOS_IMAGE_PROFILE_RECOVERY_FOCUS):
        return [*sorted(application.TEST_ARGUMENTS), "--ktest_gradle_filter=" + lt.ui_application_focus_filter(focus)]

    def test_unknown_observation_keeps_exact_original_one_launch_deadline_failure_and_all_cleanup(self):
        owner = self.owner()
        contexts = []
        def observe(context):
            contexts.append(context)
            return {"status": "unavailable", "installed_identity_drift_observed": False, "launch_readiness_verified": False}
        launches = []
        def launch(argv, protocol, *, timeout):
            launches.append((argv, timeout))
            return owner.failed_profile_launch()(argv, protocol, timeout=timeout)
        with patch.object(readiness, "observe", side_effect=observe):
            document = owner.fixture_run(control=owner.launch_diagnostic_control, launch=launch,
                arguments=self.arguments(), image_diagnostics="darwin-tools")
        self.assertEqual(1, len(contexts))
        context = contexts[0]
        self.assertEqual([(["/usr/bin/xcrun", "simctl", "launch", "--console", "--terminate-running-process",
                           DEVICE, context.bundle, *self.arguments()], 360)], launches)
        self.assertEqual(context.output.name, context.token)
        self.assertEqual(REVISION, context.source_revision)
        self.assertEqual("launch-and-real-test-transport", document["error"]["phase"])
        self.assertFalse(document["transport_passed"])
        self.assertFalse(document["image_memory_profile"]["profile_passed"])
        for flag in route.CLEANUP_FLAGS:
            self.assertTrue(document["cleanup"][flag])
        self.assertFalse(owner.installed.exists())
        self.assertEqual("unavailable", document["owned_image_launch_readiness"]["status"])

    def test_positive_identity_drift_blocks_launch_before_profile_prep_but_preserves_original_cleanup(self):
        owner = self.owner()
        def observe(context):
            (Path(context.container.stdout.decode().strip()) / application.APP_EXECUTABLE).chmod(0o600)
            return {"status": "unavailable", "installed_identity_drift_observed": True}
        with patch.object(readiness, "observe", side_effect=observe), \
                patch.object(application, "forward_application", side_effect=AssertionError("Unowned launch forbidden")):
            document = owner.fixture_run(control=owner.launch_diagnostic_control,
                arguments=self.arguments(), image_diagnostics="darwin-tools")
        self.assertEqual("observe-owned-image-prelaunch-readiness", document["error"]["phase"])
        self.assertFalse(document["transport_passed"])
        self.assertNotIn("image_memory_profile", document)
        self.assertTrue(document["cleanup"]["owned_app_absence_verified"])
        self.assertTrue(document["cleanup"]["owned_local_bundle_removed"])
        self.assertFalse(any("launch" in argv for argv in owner.commands))

    def test_installed_symlink_recheck_never_launches_or_mutates_foreign_installed_bytes(self):
        owner = self.owner()
        target = owner.root / "synthetic-foreign-target"
        def observe(context):
            executable = Path(context.container.stdout.decode().strip()) / application.APP_EXECUTABLE
            target.write_bytes(executable.read_bytes())
            executable.unlink()
            executable.symlink_to(target)
            return {"status": "unavailable", "installed_identity_drift_observed": False}
        with patch.object(readiness, "observe", side_effect=observe):
            document = owner.fixture_run(control=owner.launch_diagnostic_control,
                arguments=self.arguments(), image_diagnostics="darwin-tools")
        self.assertEqual("observe-owned-image-prelaunch-readiness", document["error"]["phase"])
        self.assertFalse(document["cleanup"]["owned_app_identity_reverified"])
        self.assertFalse(any("launch" in argv or "uninstall" in argv or "terminate" in argv for argv in owner.commands))
        self.assertTrue(target.is_file())
        self.assertTrue(owner.installed.exists())

    def test_other_finite_image_focus_and_full_transport_do_not_add_appinfo_or_prelaunch_query(self):
        owner = self.owner()
        owner.expected_timeout = 360
        with patch.object(readiness, "observe", side_effect=AssertionError("Unrelated image query forbidden")):
            document = owner.fixture_run(arguments=self.arguments(lt.IOS_IMAGE_DARWIN_FOCUS), image_diagnostics="darwin-tools")
        self.assertNotIn("owned_image_launch_readiness", document)
        self.assertTrue(document["transport_passed"])
        owner.expected_timeout = application.APP_TIMEOUT_SECONDS
        with patch.object(readiness, "observe", side_effect=AssertionError("Full-profile query forbidden")):
            document = owner.fixture_run()
        self.assertNotIn("owned_image_launch_readiness", document)
        self.assertTrue(document["transport_passed"])


if __name__ == "__main__":
    unittest.main()
