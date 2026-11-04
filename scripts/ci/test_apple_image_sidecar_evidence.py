"""NEW synthetic sidecar/read-boundary controls, never appinfo/native/profile runs.

Only fresh temporary, explicitly fabricated receipts/files are read here. No
producer observation, payload parser, native transport, tool or hosted original
is executed or reconstructed. A passing model cannot waive original633 failures.
"""
from __future__ import annotations

import ast
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import time
import unittest
from unittest.mock import patch

import apple_image_sidecar_evidence as boundary
import library_tests as library

ROOT = Path(__file__).resolve().parents[2]
FOCUS = "ios-native-image-allocation-profile-recovery"
RECORD = "image-launch-readiness-observation.json"
INLINE = "owned_image_launch_readiness"
TOKEN = "b" * 32
SOURCE = "a" * 40
DEVICE = "11111111-1111-1111-1111-111111111111"
BUNDLE = "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + SOURCE[:12] + ".t" + TOKEN
EMPTY = hashlib.sha256(b"").hexdigest()
FIELDS = ("CFBundleIdentifier", "CFBundleExecutable", "CFBundlePackageType")
DELIMITERS = ("left-brace", "right-brace", "left-bracket", "right-bracket", "left-parenthesis",
              "right-parenthesis", "less-than", "greater-than", "equals", "colon", "semicolon", "double-quote")


def canonical(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def metadata(size=80):
    return {"exit_code": 0, "stop_reason": None, "stdout_bytes": size, "stdout_sha256": "e" * 64,
            "stderr_bytes": 0, "stderr_sha256": EMPTY}


def lexical(size):
    return {"bytes": size, "sha256": "e" * 64 if size else EMPTY, "utf8_decodable": True,
            "nul_byte_count": 0, "lf_byte_count": 0, "cr_byte_count": 0,
            "nonempty_line_count": int(bool(size)), "maximum_line_bytes": size,
            "first_non_whitespace_byte_kind": "left-brace" if size else "empty",
            "last_non_whitespace_byte_kind": "right-brace" if size else "empty",
            "fixed_prefix_markers": [], "delimiter_byte_counts": {name: 0 for name in DELIMITERS},
            "allowlisted_name_literal_counts": {name: 0 for name in FIELDS},
            "serializer_or_field_schema_accepted": False}


def observation():
    executable = {"status": "observed-exact-installed-executable", "bytes": 64,
                  "signed_executable_sha256": "c" * 64, "installed_path_sha256": "e" * 64,
                  "installed_file_stat_identity_sha256": "f" * 64, "permission_mode": "0755",
                  "host_real_id_X_OK": True, "access_scope": "calling-host-process-real-ids",
                  "simulator_executable_acceptance_verified": False, "launch_readiness_verified": False,
                  "raw_identity_ids_or_paths_uploaded": False}
    tools = {name: {"basename": name, "bytes": 64, "sha256": "d" * 64,
                    "path_sha256": "e" * 64, "canonical_path_sha256": "f" * 64}
             for name in ("xcrun", "simctl", "xcodebuild")}
    structure = {"root_kind": "dictionary", "nodes_including_keys": 7,
                 "value_kind_counts": {"dictionary": 1, "string": 3}, "dictionary_key_occurrences": 3,
                 "duplicate_dictionary_key_occurrences": 0, "root_dictionary_key_occurrences": 3,
                 "own_plist_name_key_structures": {name: {"root_key_occurrences": 1,
                     "nested_key_occurrences": 0, "value_kind_counts": {"string": 1}} for name in FIELDS},
                 "registration_field_semantics_verified": False, "field_absence_or_registration_absence_proven": False,
                 "raw_unknown_keys_values_or_paths_uploaded": False}
    serialized = {"status": "observed-complete-serialized-structure", "complete_payload_grammar_matches": ["json"],
                  "structure": structure, "unique_representation_format_observed": True,
                  "serializer_implementation_identified": False, "appinfo_output_schema_observed": False,
                  "registration_observed": False, "raw_unknown_keys_values_or_paths_uploaded": False}
    return {"schema_version": 1, "operation": "owned-image-prelaunch-observation",
            "status": "observed-owned-prelaunch-structure", "query_attempted": True, "query_count": 1,
            "query_timeout_seconds": 15, "observation_budget_seconds": 90, "maximum_capture_bytes": 131072,
            "installed_executable_before": executable, "installed_executable_after": copy.deepcopy(executable),
            "installed_identity_drift_observed": False, "installed_identity_stable_observed": True,
            "tool_path_resolution": [{"name": name, **metadata(64)} for name in ("developer", "simctl", "xcodebuild")],
            "owned_private_output_removed": True, "appinfo_output_schema_observed": False, "registration_observed": False,
            "registered_container_matches_verified_container": None, "registered_executable_identity_verified": None,
            "launch_readiness_verified": False, "root_cause_proven": False, "native_functionality_verified": False,
            "profile_passed": False, "packages_published": False, "release_readiness_certified": False,
            "raw_payload_keys_values_paths_or_inventory_uploaded": False, "source_revision": SOURCE,
            "capability_receipt_sha256": "9c46f397f21aeff951b7d13baf1a7cc9f704cc14a6bba1b1a920920698f6a426",
            "simulator_uuid_sha256": hashlib.sha256(DEVICE.encode()).hexdigest(),
            "bundle_identifier_sha256": hashlib.sha256(BUNDLE.encode()).hexdigest(),
            "verified_installed_container_path_sha256": "e" * 64,
            "query_argv_template": ["/usr/bin/xcrun", "simctl", "appinfo", "<selected UUID>", "<current owned bundle>"],
            "query": metadata(), "streams": {"stdout": lexical(80), "stderr": lexical(0)},
            "serialized_structure": serialized, "tool_identities_before": tools, "tool_identities_after": copy.deepcopy(tools),
            "elapsed_seconds": 0.5}


class ImageSidecarEvidenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.output = self.root / "build/ci-verification/synthetic-image"
        self.session = self.output / "native-ui-application" / TOKEN
        self.session.mkdir(parents=True)
        self.sidecar, self.receipt = self.session / RECORD, self.session / "receipt.json"
        self.record = observation()
        self.context = {"source_revision": SOURCE, "source_tree_dirty": False,
                        "simulator": {"udid": DEVICE, "state": "Booted"},
                        "host": {"system": "Darwin", "architecture": "arm64"}}
        self.document = {"schema_version": 1, "task": ":calf-ui:" + library.IOS_APPLICATION_TASK,
                         "source_revision": SOURCE, "source_tree_dirty": False, "explicit_test_focus": FOCUS,
                         "bundle_id": BUNDLE, "signed_application_executable_sha256": "c" * 64,
                         "packages_published": False, "release_readiness_certified": False, INLINE: self.record}
        now = time.time_ns()
        self.started, self.ended = now - 5_000_000_000, now + 5_000_000_000
        self.save()

    def save(self, *, sidecar=True):
        self.document[INLINE] = self.record
        self.receipt_payload = canonical(self.document)
        self.receipt.write_bytes(self.receipt_payload)
        if sidecar:
            self.sidecar.write_bytes(canonical(self.record))
            self.sidecar.chmod(0o600)

    def validate(self, *, context=None, payload=None, focus=FOCUS, module="calf-ui"):
        return boundary.validate_retained(self.session, self.document, context or self.context,
            self.started, self.ended, module, focus,
            receipt_payload=self.receipt_payload if payload is None else payload)

    def assert_preserved_refusal(self, action=None):
        before = {path.name: (path.read_bytes(), path.lstat().st_mode, path.lstat().st_ino)
                  for path in self.session.iterdir() if path.is_file() and not path.is_symlink()}
        with self.assertRaises((ValueError, OSError)):
            (action or self.validate)()
        after = {path.name: (path.read_bytes(), path.lstat().st_mode, path.lstat().st_ino)
                 for path in self.session.iterdir() if path.is_file() and not path.is_symlink()}
        self.assertEqual(before, after, "Refusal cannot delete or rewrite retained/unknown evidence")

    def test_source_retention_and_exact_reader_hooks_leave_producer_and_native_gates_unchanged(self):
        producer = (ROOT / "scripts/ci/apple_image_launch_readiness.py").read_bytes()
        self.assertEqual("bafea0957404052acfb3a6f6ec56dabb96319448ae736f6b81f9ebdfeae18fc5", hashlib.sha256(producer).hexdigest())
        self.assertIn(b'RECORD_NAME = "' + RECORD.encode() + b'"', producer)
        self.assertIn(b'json.dumps(receipt, indent=2, sort_keys=True) + "\\n"', producer)
        reader = (ROOT / "scripts/ci/library_tests.py").read_text()
        self.assertEqual(1, reader.count("image_sidecar.require_session_membership("))
        self.assertEqual(1, reader.count("image_sidecar.validate_retained("))
        self.assertLess(reader.index("image_sidecar.validate_retained("), reader.index('"Application transport failed or incomplete"'))
        self.assertIn('"Passing image-profile workload lacks its exact owned tool-attempt/cleanup evidence"', reader)
        source = ast.parse((ROOT / "scripts/ci/apple_image_sidecar_evidence.py").read_text())
        imports = {name.name.split(".")[0] for node in ast.walk(source) if isinstance(node, ast.Import) for name in node.names}
        imports |= {node.module.split(".")[0] for node in ast.walk(source) if isinstance(node, ast.ImportFrom)}
        self.assertLessEqual(imports, {"__future__", "hashlib", "json", "math", "os", "pathlib", "re", "stat"})

    def test_only_exact_calf_ui_profile_session_admits_retained_sidecar(self):
        boundary.require_session_membership(self.session, "calf-ui", FOCUS)
        self.assertEqual(hashlib.sha256(self.sidecar.read_bytes()).hexdigest(), self.validate())
        for module, focus in (("calf-file-picker", FOCUS), ("calf-share", FOCUS), ("calf-ui", None),
                              ("calf-ui", "ios-native-image-darwin-tools"), ("calf-ui", FOCUS + "-unknown")):
            with self.subTest(module=module, focus=focus):
                self.assert_preserved_refusal(lambda: boundary.require_session_membership(self.session, module, focus))
        self.sidecar.unlink()  # Only this known temporary model file.
        del self.document[INLINE]
        self.receipt_payload = canonical(self.document); self.receipt.write_bytes(self.receipt_payload)
        boundary.require_session_membership(self.session, "calf-ui", None)
        self.assertIsNone(self.validate(focus=None))
        self.assert_preserved_refusal(lambda: boundary.require_session_membership(self.session, "calf-ui", FOCUS))

    def test_links_modes_types_extra_entries_and_ancestor_aliases_refuse_without_deletion(self):
        self.validate()
        unknown = self.session / "preserve-unknown"; unknown.write_text("synthetic owner must retain this")
        self.assert_preserved_refusal(); self.assertTrue(unknown.exists())
        unknown.unlink()  # Known model fixture, never an original/unknown owned session.
        for mode in (0o644, 0o660, 0o400):
            self.sidecar.chmod(mode); self.assert_preserved_refusal()
        self.sidecar.chmod(0o600)
        alias = self.root / "sidecar-hardlink"; os.link(self.sidecar, alias)
        self.assert_preserved_refusal(); alias.unlink()
        foreign = self.root / "foreign"; foreign.write_text("preserve foreign model bytes")
        self.sidecar.unlink(); self.sidecar.symlink_to(foreign)
        self.assert_preserved_refusal(); self.assertEqual("preserve foreign model bytes", foreign.read_text())
        self.sidecar.unlink(); self.sidecar.mkdir()
        self.assert_preserved_refusal(); self.assertTrue(self.sidecar.is_dir())
        self.sidecar.rmdir(); self.save()
        self.sidecar.unlink(); os.mkfifo(self.sidecar)
        with self.assertRaises(ValueError): self.validate()
        self.sidecar.unlink(); self.save()
        self.receipt.unlink(); self.receipt.symlink_to(foreign)
        with self.assertRaises(ValueError): self.validate()
        self.receipt.unlink(); self.save()
        redirected = self.root / "redirected"; redirected.symlink_to(self.output, target_is_directory=True)
        with self.assertRaises(ValueError):
            boundary.require_session_membership(redirected / "native-ui-application" / TOKEN, "calf-ui", FOCUS)

    def test_bounds_freshness_canonical_json_duplicate_nonfinite_and_changed_read_refuse(self):
        self.validate()
        raw = self.sidecar.read_bytes()
        for invalid in (b"", b"x" * 65537, json.dumps(self.record).encode(), raw + b" ",
                        raw.replace(b'"schema_version": 1', b'"schema_version": 1, "schema_version": 1'),
                        raw.replace(b'"elapsed_seconds": 0.5', b'"elapsed_seconds": NaN'), b"\xff"):
            self.sidecar.write_bytes(invalid); self.assert_preserved_refusal()
        self.sidecar.write_bytes(raw)
        os.utime(self.sidecar, ns=(self.started - 10_000_000_000, self.started - 10_000_000_000))
        self.assert_preserved_refusal(); self.save()
        original_read, count = os.read, 0
        inode = self.sidecar.lstat().st_ino
        def changed_read(descriptor, limit):
            nonlocal count
            body = original_read(descriptor, limit)
            if os.fstat(descriptor).st_ino == inode:
                count += 1
                if count == 2: return body[:-1] + b"x"
            return body
        with patch.object(boundary.os, "read", side_effect=changed_read): self.assert_preserved_refusal()

    def test_independent_source_session_simulator_and_signed_bytes_refuse_even_if_inline_agrees(self):
        self.validate()
        original = copy.deepcopy(self.record)
        for key, value in (("source_revision", "f" * 40), ("bundle_identifier_sha256", "f" * 64),
                           ("simulator_uuid_sha256", "f" * 64), ("capability_receipt_sha256", "f" * 64)):
            self.record = copy.deepcopy(original); self.record[key] = value; self.save(); self.assert_preserved_refusal()
        self.record = copy.deepcopy(original)
        self.record["installed_executable_before"]["signed_executable_sha256"] = "f" * 64
        self.record["installed_executable_after"]["signed_executable_sha256"] = "f" * 64
        self.save(); self.assert_preserved_refusal()
        self.record = copy.deepcopy(original); self.save()
        for key, value in (("source_revision", "f" * 40), ("source_tree_dirty", True)):
            context = copy.deepcopy(self.context); context[key] = value
            self.assert_preserved_refusal(lambda: self.validate(context=context))
        context = copy.deepcopy(self.context); context["simulator"]["udid"] = "bad-device"
        self.assert_preserved_refusal(lambda: self.validate(context=context))
        for key, value in (("bundle_id", BUNDLE + "foreign"), ("source_revision", "f" * 40),
                           ("signed_application_executable_sha256", "f" * 64), ("explicit_test_focus", None)):
            self.document[key] = value; self.save(); self.assert_preserved_refusal()
            self.document[key] = {"bundle_id": BUNDLE, "source_revision": SOURCE,
                                  "signed_application_executable_sha256": "c" * 64, "explicit_test_focus": FOCUS}[key]
        self.save()

    def test_exact_top_nested_schema_numeric_types_and_noncertification_flags_refuse_drift(self):
        self.validate()
        original = copy.deepcopy(self.record)
        mutations = [((), "unknown_private_inventory", ["do not upload"]), ((), "schema_version", True),
                     ((), "query_count", True), ((), "query_count", 2), ((), "query_timeout_seconds", 16),
                     ((), "profile_passed", True), ((), "registration_observed", True),
                     ((), "launch_readiness_verified", True), ((), "root_cause_proven", True),
                     ((), "raw_payload_keys_values_paths_or_inventory_uploaded", True),
                     ((), "registered_executable_identity_verified", False),
                     ((), "owned_private_output_removed", False), ((), "installed_identity_drift_observed", True),
                     (("query",), "stdout_bytes", True), (("query",), "stdout_sha256", "not-a-digest"),
                     (("streams", "stderr"), "sha256", "f" * 64),
                     (("streams", "stdout"), "raw_text", "unowned data"),
                     (("streams", "stdout", "delimiter_byte_counts"), "left-brace", 131073),
                     (("installed_executable_before",), "raw_identity_ids_or_paths_uploaded", True),
                     (("installed_executable_after",), "installed_file_stat_identity_sha256", "d" * 64),
                     (("tool_identities_before", "simctl"), "path", "/private/unowned"),
                     (("serialized_structure",), "serializer_implementation_identified", True),
                     (("serialized_structure", "structure"), "nodes_including_keys", 4097),
                     (("serialized_structure", "structure", "own_plist_name_key_structures"), "UnknownName", {}),
                     (("serialized_structure", "structure", "value_kind_counts"), "string", True)]
        for path, key, value in mutations:
            with self.subTest(path=path, key=key):
                self.record = copy.deepcopy(original); target = self.record
                for field in path: target = target[field]
                target[key] = value; self.save(); self.assert_preserved_refusal()
        self.record = copy.deepcopy(original); del self.record["source_revision"]
        self.save(); self.assert_preserved_refusal()

    def test_canonical_hash_inline_correspondence_and_receipt_byte_identity_are_required(self):
        self.assertEqual(hashlib.sha256(self.sidecar.read_bytes()).hexdigest(), self.validate())
        self.record["elapsed_seconds"] = 0.6; self.save(sidecar=False)
        self.assert_preserved_refusal()
        self.save()
        wrong_payload = self.receipt_payload + b" "
        self.assert_preserved_refusal(lambda: self.validate(payload=wrong_payload))
        self.receipt.write_bytes(self.receipt_payload + b" ")
        self.assert_preserved_refusal()

    def test_bound_unavailable_observations_stay_diagnostic_and_write_failures_refuse(self):
        self.validate()
        self.record["status"] = "unavailable"
        self.record["serialized_structure"].update(status="unavailable", complete_payload_grammar_matches=[],
                                                  structure=None, unique_representation_format_observed=False,
                                                  error_type="ObservationError", error_guard="unknown_or_ambiguous_payload_structure")
        self.save(); self.validate()
        self.assertFalse(self.record["profile_passed"])
        self.assertFalse(self.record["registration_observed"])
        self.assertFalse(self.record["launch_readiness_verified"])
        self.record["error_type"] = "ObservationError"; self.record["error_guard"] = "/private/unknown/payload"
        self.save(); self.assert_preserved_refusal()
        del self.record["error_type"]; del self.record["error_guard"]
        self.record["record_error_type"] = "OSError"; self.save(); self.assert_preserved_refusal()

    def application_model(self):
        """A complete fabricated one-method receipt, not a replay of old tests."""
        context = copy.deepcopy(self.context)
        context.update(java={"major": 17}, rust={"release": "synthetic"}, xcode={"version": "synthetic"},
                       apple_sdks={"iphonesimulator": "synthetic"})
        self.context = context
        binary = self.root / "calf-ui/build/bin/iosSimulatorArm64/applicationDebugTest/model.kexe"
        binary.parent.mkdir(parents=True)
        command = struct.pack("<6I", 0x32, 24, 7, 15 << 16, 26 << 16, 0)
        binary.write_bytes(struct.pack("<8I", 0xFEEDFACF, 0x0100000C, 0, 2, 1, len(command), 0, 0) + command)
        binary.chmod(0o700)
        classname = "com.mohamedrejeb.calf.ui.utils.UIImageMemoryDiagnosticsTest"
        method = "actualLibraryConversionsRemainBoundedDuringOwnedAllocationProfile"
        cases = [{"classname": classname, "name": method, "status": "passed"}]
        xml = [{"classname": library.IOS_APPLICATION_TASK + "." + classname,
                "name": method + "[iosSimulatorArm64]", "status": "passed"}]
        counts = {"tests": 1, "passed": 1, "failures": 0, "errors": 0, "skipped": 0, "executed": 1,
                  "not_applicable": 0, "unexpected_skipped": 0}
        profile = {"schema_version": 1, "simulator_udid": DEVICE, "bundle_identifier": BUNDLE,
                   "signed_application_executable_sha256": "c" * 64, "application_plist_sha256": "d" * 64,
                   "process_id": 12345, "darwin_heap_requests": {"MallocScribble": "1", "MallocGuardEdges": "1",
                       "MallocErrorAbort": "1", "MallocStackLogging": "1"}, "ASan_verified": False,
                   "private_files_uploaded": False, "prepared": True, "attempt_completion_ack_created": True,
                   "owned_ack_removed": True, "native_readiness_file_verified": True, "owned_readiness_removed": True,
                   "native_console_pid_correlated": True,
                   "native_readiness_file_sha256": hashlib.sha256(b"process_id=12345\n").hexdigest(),
                   "owned_private_tree_removed": True, "supported": False, "profile_passed": False,
                   "errors": [{"error": "Synthetic unsupported attempt; NOT native/profile evidence"}]}
        now = dt.datetime.now(dt.timezone.utc)
        self.document.update(transport_passed=True, image_diagnostics_mode="darwin-tools",
            strict_runtime_assertions_attested=False, runtime_before=copy.deepcopy(context), runtime_after=copy.deepcopy(context),
            started_at_utc=(now - dt.timedelta(seconds=1)).isoformat(), finished_at_utc=now.isoformat(),
            binary_path=binary.relative_to(self.root).as_posix(), binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
            binary_sha256_after=hashlib.sha256(binary.read_bytes()).hexdigest(),
            macho={"architecture": "arm64", "file_type": "executable", "platform": 7, "minimum_os": "15.0.0",
                   "sdk": "26.0.0", "executable_uuid": None}, application_plist_sha256="d" * 64,
            steps={"foreign-app-preflight": {"exit_code": 2, "preexisting_app_absence_verified": True},
                   "adhoc-sign-local-verification-app": {"exit_code": 0, "remote_signing_or_publication": False},
                   "install-owned-app": {"exit_code": 0, "installed_owned_bytes_verified": True}},
            cleanup={"owned_app_identity_reverified": True, "owned_app_stopped_verified": True,
                     "owned_app_absence_verified": True, "owned_local_bundle_removed": True, "uninstall_exit_code": 0},
            application_protocol={"process_exit": 0, "activation": {"main_worker": 1, "owned_worker": 2},
                "completion": {"runner_exit": 0, "worker_terminated": True}, "stream_bytes": 64,
                "testcases": cases, "counts": counts, "observed_launch_pid": 12345,
                "image_profile_observations": [{"phase": "ready", "process_id": 12345}, {"phase": "complete", "rounds": 1}]},
            image_memory_profile=profile)
        expected = {"module": "calf-ui", "task": ":calf-ui:" + library.IOS_APPLICATION_TASK,
                    "native_test_host": "genuine-uikit-application", "test_filter": classname + "." + method,
                    "required_testcases": [{"classname": library.IOS_APPLICATION_TASK + "." + classname,
                                             "name": method + "[iosSimulatorArm64]"}],
                    "test_source_files": [library.IOS_IMAGE_MEMORY_SOURCE]}
        self.plan = {"suite": "ios", "explicit_test_focus": FOCUS, "explicit_module_subset": ["calf-ui"],
                     "complete_suite_requested": False, "expected": [expected]}
        self.modules = [{"module": "calf-ui", "task": expected["task"], "testcases": xml}]
        self.save()

    def collect_model(self):
        return library.collect_ios_application_receipts(self.root, self.plan, self.output,
            self.started, self.ended, self.context, self.modules)

    def test_original_reader_accepts_exact_synthetic_sidecar_without_recounting_native_cases(self):
        self.application_model()
        result = self.collect_model()
        self.assertEqual([], result["errors"])
        self.assertEqual(1, len(result["ios_applications"]))
        self.assertEqual(1, result["ios_applications"][0]["counts"]["executed"])
        self.assertEqual(1, result["ios_applications"][0]["required_native_cases_found"])
        self.assertEqual(hashlib.sha256(self.receipt.read_bytes()).hexdigest(), result["ios_applications"][0]["receipt_sha256"])
        self.assertTrue(self.sidecar.exists())
        self.assertFalse(self.document["image_memory_profile"]["profile_passed"])

    def test_original_transport_startup_cleanup_xml_profile_and_runtime_failures_still_refuse(self):
        self.application_model()
        self.validate()
        self.assertEqual([], self.collect_model()["errors"])
        original = copy.deepcopy(self.document)
        mutations = [((), "transport_passed", False), ((), "startup_failure_observation", {}),
                     (("cleanup",), "owned_app_absence_verified", False),
                     (("runtime_after",), "source_revision", "f" * 40),
                     (("application_protocol",), "process_exit", 1),
                     (("application_protocol", "completion"), "worker_terminated", False),
                     (("image_memory_profile",), "native_console_pid_correlated", False)]
        for path, key, value in mutations:
            with self.subTest(path=path, key=key):
                self.document = copy.deepcopy(original); target = self.document
                for field in path: target = target[field]
                target[key] = value; self.save()
                result = self.collect_model()
                self.assertEqual([], result["ios_applications"])
                self.assertTrue(result["errors"])
        self.document = copy.deepcopy(original); self.save()
        self.modules[0]["testcases"][0]["status"] = "failed"
        self.assertTrue(self.collect_model()["errors"])


if __name__ == "__main__":
    unittest.main()
