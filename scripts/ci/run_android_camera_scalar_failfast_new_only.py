#!/usr/bin/env python3
"""Explicit first-only runner for exactly30 newly authored source controls.

No discovery, old test method, SDK, build, Git, process, network, native method or
automatic retry is authorized. The lead must independently review and verify the
proposal seal before invoking this file once with a new private output parent.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import time
import unittest

sys.dont_write_bytecode = True
EXPECTED_SOURCE_SHA256 = {'.github/workflows/gradle.yml': '282254f7af66a47f065693f5fd4b30ae0acf8c44ca589fcc9432857ab473ef09', 'calf-camera-picker/build.gradle.kts': 'f074767f7042ac6e07955b361400e672ae43209f99b17986acd27cf5078428c7', 'calf-camera-picker/src/androidDeviceTest/AndroidManifest.xml': 'c24a6c2498dddb660cafd78d31bfc4f4730f8ae34f1c807eff3f17ff6034962b', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraProviderTest.kt': 'e222639ed728465798aa0be937f13dc181c36dfd566db0b2fa9bbdbe67f18532', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraRestorationTest.kt': '357c8545e35d5fa529a6b38b064a86c1724ea2b0a2d2b7ec46d5ff4c3671a7d0', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraRestorationVerificationActivity.kt': '8aeb2acf56287c08619c854f4da21c3f0c4f95d7dba19e17ca6ceacff03a0c12', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraVerificationProviders.kt': '09956cd5f88d5c18dff5be3251d9ece6beb679f5c961c3041e1450cf46e96f82', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedAlwaysFinish.kt': '2010803e066ce0de1a34051ed40a50c9bca08f238a6218dcaabb4e7d0a09bee7', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedCameraReceiver.kt': 'a15663164f0b66eccf225a0a24d0af7be77e13c80bc620be501d388224a76a6d', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedDeveloperSettingsUi.kt': 'a1fb76c6092881a3681ec38002b4820f1d0d8282727a4d18fa89968f6b8c5b50', 'calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt': 'b7094d795bfaa209b254bbf2c549de21a7fff07df636fbb68f4cb1a3baa917a7', 'calf-camera-picker/src/commonTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraRequestStateTest.kt': '0ff1470d93f9580e27b54e499b2dda6843a50c5d7b4f4b5c4cfaca7980c7e841', 'convention-plugins/src/main/kotlin/Android.kt': '204b7b0bb30e33144794ffda1d993f925f670cac87c809155d81fe9f09f7a256', 'scripts/ci/android_camera_developer_prerequisite.py': 'da07bedb680e9ce36842bbf581f22bf7b3ebf8ab1c5d307b05745069c77bb5a4', 'scripts/ci/android_camera_receiver.py': '032ac23053338ec9e839cdae8b3a946a84712ff92a7f821f4972230241eb03a2', 'scripts/ci/android_device_tests.py': 'daac8786b1b034efcad0687a2f3a995c2216ea1a400116f9c592693d5c6395ec', 'scripts/ci/android_kvm_timeline.py': '488442a673d07f0a92bfffc31adcdeac3cf7de11568662fa6b6925eee7c1149b', 'scripts/ci/camera_scalar_failfast_source_projection.py': '3a0f5a01f30e482af2cf3c6953d68a21aa3d824952eaca54556abe06045ccbbb', 'scripts/ci/fixtures/android-camera-scalar-failfast-controller-inverse.json': '9a3479f92b05e1bffda3b408ad9f5833ca655b0c913af813e888209de9b2828c', 'scripts/ci/fixtures/android-camera-settings-absence-observation-inverse.json': 'e7b0e9a3e361e39d1732ed33cd5e1d4e51a3e30ed377adf487001b742754c953', 'scripts/ci/fixtures/android-camera-startup-readiness-inverse.json': '43a8963e59a7851e968fbbeeaafa19944956cbc6a6f0b5cb8924a4dba0342e2c', 'scripts/ci/library_tests.py': 'b333567dff6f85bad734077bb44b2f4028035316ee2c3771cbe82b2019d00dfb', 'scripts/ci/runtime_context.py': 'e23aff04c665dc1041dc9e27db775135223ace15c63a651e17b94a7155731712', 'scripts/ci/sample_platform_verification.py': '6780e5c355d22cf74716b0cb344fc02ee968710db5382d6460c930b99d395ca7', 'scripts/ci/test_android_camera_capture_admission.py': '2bd33a287cc8fd6d85b1c3baa7e3589c175619f2f38e09e62f53bfc872ee1467', 'scripts/ci/test_android_camera_developer_prerequisite.py': '4a78c909420383a59cb453c1ca58ab3c0ca909a08f17201ddc0bcea657a061bb', 'scripts/ci/test_android_camera_documented_data_default.py': '7b5a75da995f4ae7a93035e459728f8046a3082c9df868c6e429ad8423e1cf13', 'scripts/ci/test_android_camera_dont_keep.py': '7c936bf4a071233f19ada5ad02f587c211b7213b1f9008d0dd45418a98ad21a9', 'scripts/ci/test_android_camera_mutable_path_diagnostics.py': 'd527d9177e1cb45f4ce594bb6a97fb777ccd6ef6e1b84e12c117c73959e77de6', 'scripts/ci/test_android_camera_pre_reporter_fail_fast.py': '92d923e23c4fb7366811d9fedc5b949e5fc3043372adc5b75fbefa8d9dac3020', 'scripts/ci/test_android_camera_prerequisite_require_origin.py': 'e93298e1f8fe5f04f718c68ac1d6d95b8a5802b53b76058d989d279a350b00ae', 'scripts/ci/test_android_camera_provider.py': 'd56088155fc7ff4fd61b076b0c45f39ec577d02145103a305c3f4c96b2c45567', 'scripts/ci/test_android_camera_scalar_control_refusal.py': '2bde6d9d02a8c2a3167992e4df024930d5e0bbe731272e6a71693fb8a83088f9', 'scripts/ci/test_android_camera_settings_activity_boundary.py': '9b726a295d3eed6d7a7344f592b11b3ead551651ebd3e5be807c8047a804913d', 'scripts/ci/test_android_camera_settings_activity_reference_prefix_diagnostics.py': '4eff2430a81b2010e289d0cbca9a1e0511547cd59b750fea9da1cc5fa1b5843a', 'scripts/ci/test_android_camera_settings_activity_refusal_diagnostics.py': 'bd539b328cdf586cca655b7a34e5006f7417ee21724308f906fa1d5199d4224e', 'scripts/ci/test_android_camera_settings_ui.py': 'b66d63ab003bf8ef57088e8ce7a8d8cb86277e8a486715b8dfdda1fae2035936', 'scripts/ci/test_android_camera_startup_readiness.py': '6593bf3e08f0a26e825cbf9a772268f0c5f73ede43ddc6191c04225daf517fe2', 'scripts/ci/test_android_kvm_timeline.py': '9eab5e2173ca1bb3520028d11bdeefb03dad8a47a43f1872342d5979d5ca7f32', 'scripts/ci/test_runtime_context.py': '6fe2fccaee0680edacbf0ecd69aef29d4cfe1a1253fcae32d0389ff0e7cdd866', 'tests/consumer/android-camera-receiver/build.gradle.kts': '92000d4bad25e57121cb5c100363d44955f0bdef290372bd3da965342f1523f4', 'tests/consumer/android-camera-receiver/settings.gradle.kts': '31507eb3489726a100053c8624e941f2ad0511460a55a4f62edf6a8b9f850c4f', 'tests/consumer/android-camera-receiver/src/main/AndroidManifest.xml': '2e507acb6e0ec0f3fbb3c3bbc7908a5d882277804a68f670e8814160e16fadd5', 'tests/consumer/android-camera-receiver/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraDelayedReceiverActivity.java': '8a5df77d685676fe29842d4231e86d0a8cf7a3bc388ec69ccf95be28c1d59a93', 'tests/consumer/android-camera-receiver/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraReceiverActivity.java': '2df3ad3ab2e985fa87483c18f269f3fbcf98d44210cf2c346c955dc60a13c8c9', 'tests/consumer/android-camera-receiver/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraReceiverService.java': 'b7e366c37f91208afafd8fe6db1160a6048e740ead8c6cc334101b7a4a353a53'}  # Exact source-only readbacks; no qualification result is inferred.
EXPECTED_METHODS = {'failfast': ['test_ff01_actual_new_run_scalar_refusal_prevents_all_reporter_assembly_and_native', 'test_ff02_actual_new_run_captures_before_exact_assembly_and_never_promotes_preflight', 'test_ff03_actual_new_run_nonzero_or_stop_keeps_compile_red_and_owned_boot_cleanup', 'test_ff04_compile_and_secondary_publication_errors_keep_the_same_primary', 'test_ff05_missing_apk_is_not_read_during_read_only_capture_and_no_success_is_inferred', 'test_ff06_postcompile_master_scalar_native_or_row_presence_drift_never_recaptures', 'test_ff07_postcompile_kernel_owner_runtime_user_or_home_drift_refuses_before_mutation', 'test_ff08_postcompile_pending_state_is_a_single_refusal_not_a_new_startup_loop', 'test_ff09_separate_postcompile_clock_command_and_total_bounds_refuse_late_results', 'test_ff10_original_compiled_reporter_and_frozen_file_guards_still_refuse_after_capture', 'test_ff11_assembly_and_capture_latches_refuse_unproved_or_repeated_completion', 'test_ff12_new_timing_keeps_exact_original_mutation_and_owned_cleanup_boundaries', 'test_ff13_other_profiles_keep_their_original_pre_native_order_and_no_c1_fields', 'test_ff14_full_source_inverses_preserve_original_readers_actions_cleanup_and_single_call', 'test_ff15_historical_fixture_projection_is_exact_and_cannot_qualify_mutated_current_source', 'test_ff16_native_sources_plans_workflows_and_read_only_receipt_privacy_stay_exact', 'test_ff17_terminal_postreporter_timeout_resets_phase_but_later_master_failure_keeps_completed_phase', 'test_ff18_generic_discovery_needs_no_private_environment_and_scoped_temp_custody_stays_strict'], 'scalar': ['test_sc01_exact_getter_role_and_both_allowlisted_keys_survive_original_refusal', 'test_sc02_provider_rows_whitespace_and_unsafe_bytes_never_become_accepted', 'test_sc03_owner_context_binds_exact_allowlisted_command_and_result_identity', 'test_sc04_unknown_near_miss_and_cross_result_context_never_guess_a_query', 'test_sc05_original_result_and_regex_refusals_precede_scalar_observation', 'test_sc06_secondary_observer_and_publisher_failures_preserve_primary_identity', 'test_sc07_forged_extra_mistyped_unbounded_and_inconsistent_facts_are_not_published', 'test_sc08_foreign_origin_copied_exception_and_direct_context_injection_refuse', 'test_sc09_nonrefusing_scalar_calls_do_not_run_the_observer', 'test_sc10_original_row_agreement_and_arbitrary_key_guards_are_not_shape_facts', 'test_sc11_missing_original_cleanup_stays_separate_sticky_and_mutation_free', 'test_sc12_publication_is_bounded_hash_shape_only_and_has_no_global_registry']}  # Exactly30 new methods; never discovery or accepted-suite selection.
MODULES = (
    ("scalar", "scripts/ci/test_android_camera_scalar_control_refusal.py", "ScalarControlRefusalNewOnlyTests"),
    ("failfast", "scripts/ci/test_android_camera_pre_reporter_fail_fast.py", "PreReporterFailFastNewOnlyTests"),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate private runner input field")
        result[key] = value
    return result


def ordinary_source(path):
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and not path.is_symlink(),
            "A held ordinary unshared source file is required")
    return info


def all_ancestors_are_directories(path):
    current = path
    while True:
        if current.exists() or current.is_symlink():
            info = current.lstat()
            require(stat.S_ISDIR(info.st_mode) and not current.is_symlink(), "No private runner ancestor symlink is admitted")
        if current == current.parent:
            break
        current = current.parent


class FirstOnlyResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rows, self.order = {}, []

    def startTest(self, test):
        super().startTest(test)
        key = test.id()
        require(key not in self.rows, "No new source control may be executed twice")
        self.order.append(key)
        self.rows[key] = {"id": key, "new_method": True, "started_monotonic": time.monotonic(),
                          "failures": 0, "errors": 0, "skips": 0, "subtest_failures": 0}

    def stopTest(self, test):
        row = self.rows[test.id()]
        row["seconds"] = time.monotonic() - row.pop("started_monotonic")
        super().stopTest(test)

    def addFailure(self, test, err):
        self.rows[test.id()]["failures"] += 1
        super().addFailure(test, err)

    def addError(self, test, err):
        self.rows[test.id()]["errors"] += 1
        super().addError(test, err)

    def addSkip(self, test, reason):
        self.rows[test.id()]["skips"] += 1
        super().addSkip(test, reason)

    def addSubTest(self, test, subtest, err):
        if err is not None:
            self.rows[test.id()]["subtest_failures"] += 1
        super().addSubTest(test, subtest, err)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--expected-runner-sha256", required=True)
    options = parser.parse_args()
    tree, output = Path(options.tree).absolute(), Path(options.output).absolute()
    require(tree.is_dir() and not tree.is_symlink(), "An exact held source tree is required")
    require(re.fullmatch(r"[a-f0-9]{64}", options.expected_runner_sha256) is not None and
            digest(Path(__file__)) == options.expected_runner_sha256, "The independently held runner bytes differ")
    require(not output.is_relative_to(tree) and not output.parent.is_relative_to(tree), "Runner facts cannot write into the held source tree")
    require(not output.parent.exists() and not output.exists(), "A new sole-execution output parent is required")
    all_ancestors_are_directories(output.parent)
    output.parent.mkdir(mode=0o700, parents=True)
    private = output.parent / "model-temp"
    private.mkdir(mode=0o700)
    claim = output.parent / "FIRST-ONLY.claim.json"
    descriptor = os.open(claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    started_ns, started = time.time_ns(), time.monotonic()
    try:
        payload = (json.dumps({"schema": "camera-scalar-failfast-first-only-claim.v1", "started_unix_ns": started_ns,
                              "runner_sha256": options.expected_runner_sha256, "automatic_retry": False}, sort_keys=True) + "\n").encode()
        require(os.write(descriptor, payload) == len(payload), "Exclusive new-control claim write failed")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    before = {}
    for relative, expected in EXPECTED_SOURCE_SHA256.items():
        path = tree / relative
        ordinary_source(path)
        before[relative] = digest(path)
        require(before[relative] == expected, "A held new-only source/control/compatibility input changed")
    os.environ.update(NATIVECMPKIT_CAMERA_SCALAR_MODEL_TREE=str(tree),
                      NATIVECMPKIT_CAMERA_FAILFAST_MODEL_TREE=str(tree),
                      NATIVECMPKIT_CAMERA_FAILFAST_MODEL_TMP=str(private),
                      CAMERA_PREREQUISITE_MODEL_TREE=str(tree), CAMERA_PREREQUISITE_MODEL_TMP=str(private),
                      PYTHONDONTWRITEBYTECODE="1")
    modules, suite, selected = {}, unittest.TestSuite(), []
    for key, relative, class_name in MODULES:
        path = tree / relative
        syntax = ast.parse(path.read_bytes(), filename=str(path))
        assignments = [node for node in syntax.body if isinstance(node, ast.Assign) and
                       any(isinstance(target, ast.Name) and target.id == "DECLARED_METHODS" for target in node.targets)]
        require(len(assignments) == 1 and tuple(ast.literal_eval(assignments[0].value)) == tuple(EXPECTED_METHODS[key]),
                "Only the two exact new literal method declarations are authorized")
        spec = importlib.util.spec_from_file_location("nativecmpkit_camera_scalar_failfast_new_only_" + key, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        require(Path(module.__file__).absolute() == path and module.__spec__.origin == str(path), "New module import origin changed")
        cls = vars(module).get(class_name)
        require(isinstance(cls, type) and issubclass(cls, unittest.TestCase), "The exact new test class is required")
        require({name for name in vars(cls) if name.startswith("test_")} == set(EXPECTED_METHODS[key]),
                "New-only class contains an unexpected method")
        for name in EXPECTED_METHODS[key]:
            test = cls(name)
            suite.addTest(test)
            selected.append(test.id())
        modules[key] = module
    require(len(selected) == 30 and len(set(selected)) == 30, "Exactly30 unique new source controls must be selected")
    result = unittest.TextTestRunner(verbosity=2, failfast=True, resultclass=FirstOnlyResult).run(suite)
    after = {relative: digest(tree / relative) for relative in EXPECTED_SOURCE_SHA256}
    counters = {key: dict(module.COUNTERS) for key, module in modules.items()}
    forbidden = {key: list(module.FORBIDDEN_ACTIONS) for key, module in modules.items()}
    passed = (result.wasSuccessful() and result.testsRun == 30 and not result.skipped and
              result.order == selected and before == after and digest(Path(__file__)) == options.expected_runner_sha256 and
              all(not values for values in forbidden.values()) and
              all(values.get("existing_accepted_test_methods_selected") == values.get("native_invocations") == 0
                  for values in counters.values()))
    report = {"schema": "nativecmpkit.camera-scalar-failfast-new-only-source-controls.v1",
        "started_unix_ns": started_ns, "finished_unix_ns": time.time_ns(), "seconds": time.monotonic() - started,
        "passed": passed, "selected_methods": selected, "selected_count": 30, "executed_count": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors), "skips": len(result.skipped),
        "rows": [result.rows[key] for key in result.order], "counters": counters, "forbidden_actions": forbidden,
        "source_sha256_before": before, "source_sha256_after": after, "runner_sha256": options.expected_runner_sha256,
        "source_unchanged": before == after, "source_only": True, "accepted_test_method_replays": 0,
        "compiler_executions": 0, "native_executions": 0, "Git_or_network_acquisitions": 0,
        "original_camera009_replays": 0, "original_camera41344349446_acquisitions": 0,
        "automatic_retry": False, "native_acceptance_or_issue_closure_inferred": False}
    descriptor = os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        payload = (json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            require(written > 0, "Fresh new-only result write failed")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
