"""Synthetic receipt/child-environment contracts, never real UIKit executions.

Mach-O and protocol/SDK records below are explicitly simulated. The actual
immutable Arm64 simulator job, real KGP XML and complete native lifecycle are
still required. This suite is not substituted for the sixteen required native cases.
"""
from collections import Counter
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

import library_tests as r
import ios_ui_application as a
from test_daemon_jvm import FIXTURE as SYNTHETIC_DAEMON

DEVICE = "11111111-1111-1111-1111-111111111111"
OUTPUT = "build/ci-verification/synthetic-ui"
TOKEN = "b" * 32
TASK = ":calf-ui:iosSimulatorArm64ApplicationTest"
PREFIX = "iosSimulatorArm64ApplicationTest."
SUFFIX = "[iosSimulatorArm64]"
REQUIRED = (
    ("dialog.NativeAlertLifecycleTest", "presentedAlertUsesLatestActionAndTextFieldCallbacks"),
    ("dialog.NativeAlertLifecycleTest", "disposalDuringPresentationQueuesCleanupAndReplacement"),
    ("dialog.NativeAlertLifecycleTest", "actionSheetHasAPresentingViewPopoverAnchor"),
    ("dialog.NativeAlertLifecycleTest", "outsideDismissRequestsAndDisposalRemainExactlyOnce"),
    ("dropdown.NativeDropDownLifecycleTest", "expandedStateControlsActualMenuAndDismissalIsNotReportedAtOpen"),
    ("sheet.NativeSheetLifecycleTest", "cancellingAShowWaiterDoesNotReuseItsCompletionForHide"),
    ("sheet.NativeSheetLifecycleTest", "disposalDuringShowDetachesOwnerWithoutUserDismissal"),
    ("timepicker.NativeTimePickerTest", "replacingStateReplacesTheNativeOwnerAndNeverWritesToOldState"),
    ("internal.NativeUiApplicationHostTest", "generatedBodyRunsOnOwnedWorkerWithActiveAttachedApplication"),
    ("internal.NativeUiApplicationHostTest", "repeatedRealComposeRootsRecomposeDisposeAndRestoreTheirOwner"),
    ("internal.NativeUiApplicationHostTest", "failedAssertionPreservesCauseAndReleasesRealCompositionAndPresenter"),
    ("internal.NativeUiApplicationHostTest", "nativeObjectIdentityRejectsNullAndEqualButDistinctObjects"),
    ("utils.UIImageConversionTest", "returnedImageOwnsItsPixelsAfterTemporaryArraysAndContextsAreCollected"),
    ("dialog.RememberNativeAlertPropertiesTest", "stableInputsRetainIdentityButTextFieldReplacementReachesTheCaller"),
    ("navigation.NativeBarOwnershipTest", "emptyTabsClearSelectionAndRepopulationClampsIndex"),
    ("navigation.NativeBarOwnershipTest", "selectionUsesCurrentNativeMembershipInsteadOfStaleOrMutableTags"),
)


class IosApplicationReceipts(unittest.TestCase):
    def test_claimed_success_cannot_hide_an_explicit_startup_failure_observation(self):
        for value in [None, {}, {"root_attached": False}]:
            with self.subTest(value=value):
                self.document["startup_failure_observation"] = value
                self.save()
                self.assertTrue(self.collect()["errors"])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / OUTPUT
        self.app_root = self.output / "native-ui-application"
        self.receipt_path = self.app_root / TOKEN / "receipt.json"
        self.write("settings.gradle.kts", 'include(\n    ":calf-ui",\n    ":calf-io",\n)\n')
        for module in ["calf-ui", "calf-io"]:
            self.write(module + "/build.gradle.kts", "// synthetic build")
            self.write(module + "/src/commonTest/kotlin/Common.kt", "// synthetic test")
        for name in r.IOS_APPLICATION_SOURCES:
            self.write(name, "// synthetic native host input")
        self.plan = r.plan(self.root, "ios", only_modules=("calf-ui",))
        command = struct.pack("<6I", 0x32, 24, 7, 15 << 16, 26 << 16, 0)
        self.binary = self.write(a.EXPECTED_BINARY_DIRECTORY + "/test.kexe",
            struct.pack("<8I", 0xFEEDFACF, 0x0100000C, 0, 2, 1, len(command), 0, 0) + command)
        self.binary.chmod(0o700)
        self.context = {"source_revision": "a" * 40, "source_tree_dirty": False,
            "host": {"system": "Darwin", "architecture": "arm64", "python": "synthetic"},
            "java": {"major": 17}, "rust": {"release": "1.98.0"}, "xcode": {"version": "26.0"},
            "apple_sdks": {"macosx": "26.0", "iphoneos": "26.0", "iphonesimulator": "26.0"},
            "simulator": {"udid": DEVICE, "state": "Booted", "runtime_version": "26.0"}}
        self.cases = [{"classname": "com.mohamedrejeb.calf.ui." + c, "name": n, "status": "passed"}
                      for c, n in REQUIRED]
        now = dt.datetime.now(dt.timezone.utc)
        self.document = {"schema_version": 1, "task": TASK, "transport_passed": True,
            "source_revision": self.context["source_revision"], "source_tree_dirty": False,
            "started_at_utc": (now - dt.timedelta(milliseconds=300)).isoformat(),
            "finished_at_utc": now.isoformat(), "runtime_before": copy.deepcopy(self.context),
            "runtime_after": copy.deepcopy(self.context),
            "binary_path": self.binary.relative_to(self.root).as_posix(),
            "binary_sha256": r.sha256(self.binary), "binary_sha256_after": r.sha256(self.binary),
            "macho": a.macho_simulator_identity(self.binary),
            "bundle_id": "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + "a" * 12 + ".t" + TOKEN,
            "signed_application_executable_sha256": "c" * 64, "application_plist_sha256": "d" * 64,
            "packages_published": False, "release_readiness_certified": False,
            "steps": {
                "foreign-app-preflight": {"exit_code": 2, "preexisting_app_absence_verified": True},
                "adhoc-sign-local-verification-app": {"exit_code": 0, "remote_signing_or_publication": False},
                "install-owned-app": {"exit_code": 0, "installed_owned_bytes_verified": True}},
            "cleanup": {"owned_app_identity_reverified": True, "terminate_exit_code": 0,
                        "owned_app_stopped_verified": True,
                        "uninstall_exit_code": 0, "owned_app_absence_verified": True,
                        "owned_local_bundle_removed": True},
            "application_protocol": {"process_exit": 0, "elapsed_seconds": 1,
                "activation": {"main_worker": 1, "owned_worker": 2},
                "completion": {"runner_exit": 0, "worker_terminated": True},
                "testcases": copy.deepcopy(self.cases), "counts": r.case_counts(self.cases), "stream_bytes": 100,
                "image_lifetime_observation": {"marker_count": 63, "last_phase": "verified", "last_iteration": None,
                    "main_thread": True, "retained_image_bytes_verified": True}}}
        self.modules = [{"module": "calf-ui", "task": TASK, "testcases": self.xml_cases(self.cases)}]
        self.save()

    def write(self, relative, data):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data if isinstance(data, bytes) else data.encode())
        return target

    def xml_cases(self, cases):
        return [{**c, "classname": PREFIX + c["classname"], "name": c["name"] + SUFFIX} for c in cases]

    def save(self):
        self.receipt_path.parent.mkdir(parents=True, exist_ok=True)
        self.receipt_path.write_text(json.dumps(self.document))

    def collect(self):
        now = time.time_ns()
        return r.collect_ios_application_receipts(self.root, self.plan, self.output,
            now - 2_000_000_000, now + 2_000_000_000, self.context, self.modules)

    def test_exact_app_protocol_xml_runtime_binary_and_cleanup_are_required(self):
        result = self.collect()
        self.assertFalse(result["errors"])
        app = result["ios_applications"][0]
        self.assertTrue(app["protocol_xml_agreement"])
        self.assertEqual(16, app["counts"]["executed"])
        self.assertEqual(16, app["required_native_cases_found"])
        self.assertEqual(r.sha256(self.receipt_path), app["receipt_sha256"])

    def test_missing_identity_case_is_rejected_even_when_protocol_and_xml_match(self):
        cases = [c for c in self.cases if c["name"] != "nativeObjectIdentityRejectsNullAndEqualButDistinctObjects"]
        self.document["application_protocol"]["testcases"] = cases
        self.document["application_protocol"]["counts"] = r.case_counts(cases)
        self.modules[0]["testcases"] = self.xml_cases(cases)
        self.save()
        self.assertTrue(self.collect()["errors"])

    def test_matching_green_protocol_and_xml_cannot_omit_current_property_or_tab_cases(self):
        original = copy.deepcopy(self.document)
        for method in ["stableInputsRetainIdentityButTextFieldReplacementReachesTheCaller",
                       "emptyTabsClearSelectionAndRepopulationClampsIndex",
                       "selectionUsesCurrentNativeMembershipInsteadOfStaleOrMutableTags"]:
            with self.subTest(method=method):
                self.document = copy.deepcopy(original)
                cases = [case for case in self.cases if case["name"] != method]
                self.document["application_protocol"]["testcases"] = cases
                self.document["application_protocol"]["counts"] = r.case_counts(cases)
                self.modules[0]["testcases"] = self.xml_cases(cases)
                self.save()
                self.assertTrue(self.collect()["errors"])

    def test_missing_alert_dismissal_regression_is_rejected_even_when_protocol_and_xml_match(self):
        cases = [c for c in self.cases if c["name"] != "outsideDismissRequestsAndDisposalRemainExactlyOnce"]
        self.document["application_protocol"]["testcases"] = cases
        self.document["application_protocol"]["counts"] = r.case_counts(cases)
        self.modules[0]["testcases"] = self.xml_cases(cases)
        self.save()
        self.assertTrue(self.collect()["errors"])

    def test_original_failed_image_gc_case_cannot_disappear_from_matching_green_protocol_and_xml(self):
        cases = [c for c in self.cases if c["classname"] != "com.mohamedrejeb.calf.ui.utils.UIImageConversionTest"]
        self.document["application_protocol"]["testcases"] = cases
        self.document["application_protocol"]["counts"] = r.case_counts(cases)
        self.modules[0]["testcases"] = self.xml_cases(cases)
        self.save(); self.assertTrue(self.collect()["errors"])

    def test_partial_protocol_or_failure_diagnostic_fields_cannot_be_relabelled_green(self):
        for field in ["application_protocol_partial", "owned_crash_diagnostics"]:
            with self.subTest(field=field):
                self.document[field] = {}; self.save(); self.assertTrue(self.collect()["errors"])
                self.document.pop(field)

    def test_passing_gc_case_requires_complete_actual_finite_main_thread_diagnostics(self):
        original = copy.deepcopy(self.document["application_protocol"]["image_lifetime_observation"])
        for change in [lambda o: o.update(marker_count=True), lambda o: o.update(marker_count=62),
                       lambda o: o.update(last_phase="before-gc"), lambda o: o.update(last_iteration=20),
                       lambda o: o.update(main_thread=False), lambda o: o.update(retained_image_bytes_verified=False)]:
            with self.subTest(change=change):
                observed = copy.deepcopy(original); change(observed)
                self.document["application_protocol"]["image_lifetime_observation"] = observed
                self.save(); self.assertTrue(self.collect()["errors"])

    def test_absent_or_empty_owned_output_is_not_zero_test_success(self):
        self.receipt_path.unlink()
        self.assertTrue(self.collect()["errors"])
        self.receipt_path.parent.rmdir()
        self.assertTrue(self.collect()["errors"])

    def test_two_fresh_receipts_do_not_double_count_or_choose_a_green_one(self):
        self.write(OUTPUT + "/native-ui-application/" + "e" * 32 + "/receipt.json", json.dumps(self.document))
        self.assertTrue(self.collect()["errors"])

    def test_malformed_step_shapes_schema_types_and_nonfinite_json_fail_closed(self):
        original = copy.deepcopy(self.document)
        for change in [lambda d: d["steps"].update({"install-owned-app": []}),
                       lambda d: d.update(schema_version=True),
                       lambda d: d["cleanup"].update(owned_app_stopped_verified=False),
                       lambda d: d["steps"]["install-owned-app"].update(exit_code=False)]:
            with self.subTest(change=change):
                self.document = copy.deepcopy(original); change(self.document); self.save()
                self.assertTrue(self.collect()["errors"])
        self.document = original
        self.document["untrusted_number"] = float("nan"); self.save()
        self.assertTrue(self.collect()["errors"])

    def test_receipt_size_is_bounded_before_json_decode(self):
        self.receipt_path.write_bytes(b" " * (2 * 1024**2 + 1))
        self.assertTrue(self.collect()["errors"])

    def test_stale_file_or_receipt_time_is_rejected(self):
        now = time.time()
        os.utime(self.receipt_path, (now - 60, now - 60))
        self.assertTrue(self.collect()["errors"])
        self.document["started_at_utc"] = "2000-01-01T00:00:00+00:00"
        self.save()
        self.assertTrue(self.collect()["errors"])

    def test_naive_or_reversed_timestamps_do_not_establish_freshness(self):
        for key, value in [("started_at_utc", "2026-10-27T00:00:00"),
                           ("finished_at_utc", "2000-01-01T00:00:00+00:00")]:
            with self.subTest(key=key):
                original = self.document[key]; self.document[key] = value; self.save()
                self.assertTrue(self.collect()["errors"])
                self.document[key] = original

    def test_revision_dirty_bundle_and_task_identity_cannot_be_substituted(self):
        for key, value in [("source_revision", "e" * 40), ("source_tree_dirty", True),
                           ("bundle_id", "foreign.application"), ("task", ":calf-ui:iosSimulatorArm64Test")]:
            with self.subTest(key=key):
                original = self.document[key]; self.document[key] = value; self.save()
                self.assertTrue(self.collect()["errors"])
                self.document[key] = original

    def test_selected_simulator_compiler_sdk_and_arch_must_agree_before_and_after(self):
        original = copy.deepcopy(self.document)
        for when, key, value in [("runtime_before", "simulator", {"udid": "e" * 36}),
                                ("runtime_after", "java", {"major": 21}),
                                ("runtime_after", "host", {"system": "Linux", "architecture": "arm64"}),
                                ("runtime_after", "apple_sdks", {"iphonesimulator": "25.0"})]:
            with self.subTest(when=when, key=key):
                self.document = copy.deepcopy(original); self.document[when][key] = value; self.save()
                self.assertTrue(self.collect()["errors"])

    def test_failed_transport_errors_or_missing_cleanup_cannot_be_green(self):
        original = copy.deepcopy(self.document)
        for change in [lambda d: d.update(transport_passed=False), lambda d: d.update(error={"phase": "launch"}),
                       lambda d: d["cleanup"].update(owned_app_absence_verified=False),
                       lambda d: d["cleanup"].update(error_type="RuntimeError"),
                       lambda d: d["cleanup"].pop("owned_local_bundle_removed"),
                       lambda d: d["steps"]["install-owned-app"].update(installed_owned_bytes_verified=False),
                       lambda d: d.update(packages_published=True)]:
            with self.subTest(change=change):
                self.document = copy.deepcopy(original); change(self.document); self.save()
                self.assertTrue(self.collect()["errors"])

    def test_crash_worker_identity_and_incomplete_protocol_invalidate_other_passes(self):
        original = copy.deepcopy(self.document)
        for change in [lambda p: p.update(process_exit=9), lambda p: p.pop("completion"),
                       lambda p: p["activation"].update(owned_worker=1),
                       lambda p: p["completion"].update(worker_terminated=False),
                       lambda p: p["counts"].update(tests=1000), lambda p: p.update(testcases=[])]:
            with self.subTest(change=change):
                self.document = copy.deepcopy(original); change(self.document["application_protocol"]); self.save()
                self.assertTrue(self.collect()["errors"])

    def test_current_linked_bytes_and_real_macho_header_must_match_the_receipt(self):
        self.binary.write_bytes(self.binary.read_bytes() + b"changed")
        self.assertTrue(self.collect()["errors"])
        self.document["binary_sha256"] = self.document["binary_sha256_after"] = r.sha256(self.binary)
        self.document["macho"]["platform"] = 2; self.save()
        self.assertTrue(self.collect()["errors"])

    def test_protocol_and_actual_xml_must_agree_on_complete_identities_and_statuses(self):
        for change in [lambda cs: cs[0].update(status="failed"), lambda cs: cs[0].update(name="other" + SUFFIX),
                       lambda cs: cs.pop()]:
            with self.subTest(change=change):
                self.modules[0]["testcases"] = self.xml_cases(self.cases)
                change(self.modules[0]["testcases"])
                self.assertTrue(self.collect()["errors"])

    def test_kgp_no_exit_code_does_not_erase_a_matching_failed_testcase(self):
        self.cases[0]["status"] = "failed"
        self.document["application_protocol"]["testcases"] = copy.deepcopy(self.cases)
        self.document["application_protocol"]["counts"] = r.case_counts(self.cases)
        self.modules[0]["testcases"] = self.xml_cases(self.cases); self.save()
        result = self.collect()
        self.assertFalse(result["errors"], "Valid transport preserves failure; the parent JUnit gate still fails")
        self.assertEqual(1, result["ios_applications"][0]["counts"]["failures"])

    def test_seven_presenter_and_three_genuine_host_cases_cannot_disappear(self):
        self.cases.pop()
        self.document["application_protocol"]["testcases"] = copy.deepcopy(self.cases)
        self.document["application_protocol"]["counts"] = r.case_counts(self.cases)
        self.modules[0]["testcases"] = self.xml_cases(self.cases); self.save()
        self.assertTrue(self.collect()["errors"])

    def test_only_exact_observed_kgp_prefix_and_target_suffix_are_normalized(self):
        for key, value in [("classname", self.cases[0]["classname"]),
                           ("classname", "otherTask." + self.cases[0]["classname"]),
                           ("name", self.cases[0]["name"]), ("name", self.cases[0]["name"] + "[differentTarget]")]:
            with self.subTest(key=key, value=value):
                self.modules[0]["testcases"] = self.xml_cases(self.cases)
                self.modules[0]["testcases"][0][key] = value
                self.assertTrue(self.collect()["errors"])

    def test_duplicate_protocol_case_or_junit_identity_is_rejected(self):
        self.document["application_protocol"]["testcases"].append(copy.deepcopy(self.cases[0]))
        self.document["application_protocol"]["counts"] = r.case_counts(self.document["application_protocol"]["testcases"])
        self.save(); self.assertTrue(self.collect()["errors"])
        self.document["application_protocol"]["testcases"].pop(); self.document["application_protocol"]["counts"] = r.case_counts(self.cases)
        self.modules[0]["testcases"].append(copy.deepcopy(self.modules[0]["testcases"][0]))
        self.save(); self.assertTrue(self.collect()["errors"])

    def test_symlink_hardlink_duplicate_json_and_leftover_bundle_are_not_receipts(self):
        original = self.receipt_path.read_bytes()
        other = self.root / "foreign.json"; other.write_bytes(original)
        self.receipt_path.unlink(); os.link(other, self.receipt_path)
        self.assertTrue(self.collect()["errors"])
        self.receipt_path.unlink(); self.receipt_path.symlink_to(other)
        self.assertTrue(self.collect()["errors"])
        self.receipt_path.unlink(); self.receipt_path.write_bytes(original[:-1] + b',"transport_passed":true}')
        self.assertTrue(self.collect()["errors"])
        self.receipt_path.write_bytes(original)
        (self.receipt_path.parent / "NativeCmpkitLibraryTests.app").mkdir()
        self.assertTrue(self.collect()["errors"])

    def test_non_application_ios_subset_and_other_platforms_need_no_app_receipt(self):
        for plan in [r.plan(self.root, "ios", only_modules=("calf-io",)),
                     r.plan(self.root, "desktop", only_modules=("calf-ui",))]:
            result = r.collect_ios_application_receipts(self.root, plan, self.output, 0, 1, {}, [])
            self.assertEqual([], result["ios_applications"])
            self.assertEqual([], result["errors"])
            self.assertIsNone(r.ios_application_environment(self.root, self.output, plan))

    def test_environment_is_confined_to_child_and_fresh_output_without_exposing_it(self):
        with patch.dict(os.environ, {"NATIVECMPKIT_UIKIT_RESULT_ROOT": ""}, clear=False):
            del os.environ["NATIVECMPKIT_UIKIT_RESULT_ROOT"]
            before = os.environ.copy()
            env = r.ios_application_environment(self.root, self.output, self.plan)
            self.assertEqual(OUTPUT + "/native-ui-application", env["NATIVECMPKIT_UIKIT_RESULT_ROOT"])
            self.assertEqual(before, os.environ)

    def test_conflicting_inherited_app_root_is_refused_before_outputs_or_quarantine(self):
        with patch.dict(os.environ, {"NATIVECMPKIT_UIKIT_RESULT_ROOT": "build/ci-verification/foreign"}), \
                patch.object(r, "execute") as execute, patch.object(r, "quarantine_reports") as quarantine:
            with self.assertRaises(ValueError):
                r.run(self.root, "ios", "build/ci-verification/not-created", DEVICE, 60, 8192, ("calf-ui",))
            execute.assert_not_called(); quarantine.assert_not_called()
        self.assertFalse((self.root / "build/ci-verification/not-created").exists())

    def simulated_run(self, failed=False):
        self.receipt_path.unlink(); self.receipt_path.parent.rmdir(); self.app_root.rmdir()
        self.output.rmdir()
        if failed:
            self.cases[0]["status"] = "failed"
            self.document["application_protocol"]["testcases"] = copy.deepcopy(self.cases)
            self.document["application_protocol"]["counts"] = r.case_counts(self.cases)
        def execute(root, command, log_path, timeout, reserve_mib, *, env):
            self.assertEqual(OUTPUT + "/native-ui-application", env["NATIVECMPKIT_UIKIT_RESULT_ROOT"])
            now = dt.datetime.now(dt.timezone.utc).isoformat()
            self.document["started_at_utc"] = self.document["finished_at_utc"] = now
            self.save()
            cases = self.xml_cases(self.cases)
            xml = '<testsuite name="synthetic">' + ''.join(
                f'<testcase classname="{c["classname"]}" name="{c["name"]}">' +
                ('<failure/>' if c["status"] == "failed" else '') + '</testcase>' for c in cases) + '</testsuite>'
            self.write(self.plan["expected"][0]["report_directory"] + "/TEST-synthetic.xml", xml)
            log_path.write_text("NATIVECMPKIT_TEST_RUNTIME task=" + TASK + " gradle=9.7.1 java=17\n" +
                                r.daemon_jvm.PREFIX + json.dumps(SYNTHETIC_DAEMON) + "\n")
            return {"exit_code": 0}
        with patch.object(r.runtime_context, "capture", return_value=self.context), \
                patch.object(r, "git_revision", return_value="a" * 40), \
                patch.object(r, "execute", side_effect=execute), \
                patch.dict(os.environ, {"NATIVECMPKIT_NATIVE_UI_TESTS": "true"}):
            return r.run(self.root, "ios", OUTPUT, DEVICE, 60, 8192, ("calf-ui",))

    def test_simulated_run_threads_actual_child_environment_and_collects_agreement(self):
        result = self.simulated_run()
        self.assertTrue(result["passed"])
        self.assertTrue(result["ios_applications"][0]["protocol_xml_agreement"])
        self.assertNotIn("PATH", json.dumps(result))

    def test_failed_xml_stays_failed_despite_valid_app_transport_and_runner_exit_zero(self):
        result = self.simulated_run(failed=True)
        self.assertFalse(result["passed"])
        self.assertEqual(1, result["totals"]["failures"])
        self.assertTrue(result["ios_applications"][0]["protocol_xml_agreement"])


if __name__ == "__main__":
    unittest.main()
