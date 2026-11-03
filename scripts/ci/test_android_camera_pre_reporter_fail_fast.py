"""Eighteen new sole-C1 compiler-boundary controls; authored, not native evidence.

The real candidate _run/capture/staged-completion methods execute only against
inert, fresh owned fixtures when the lead selects these new methods. No existing
test_ method is selected. The reusable ModelFixture is test-free. No APK, SDK,
process, Git, network or accepted camera009 method executes. The historical
controller projection is checked separately and never used as the new _run.
"""
from __future__ import annotations

import ast
from contextlib import ExitStack, contextmanager
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

TREE = Path(os.environ.get("NATIVECMPKIT_CAMERA_FAILFAST_MODEL_TREE", Path(__file__).resolve().parents[2])).resolve()
# Generic CI discovery needs no private environment and acquires no model root
# at import. The class later creates exactly one fresh owned0700 root. An optional
# explicit parent is validated, never created/adopted as a model root or silently
# replaced when missing/unowned. Existing roots and the source tree stay untouched.
PRIVATE = None
projection = fixtures = helper = None
HELPER_PATH = TREE / "scripts/ci/android_camera_developer_prerequisite.py"
CONTROLLER_PATH = TREE / "scripts/ci/android_device_tests.py"
FIXTURE_PATH = TREE / "scripts/ci/test_android_camera_developer_prerequisite.py"
PROJECTION_PATH = TREE / "scripts/ci/camera_scalar_failfast_source_projection.py"
STARTUP_INVERSE_PATH = TREE / "scripts/ci/fixtures/android-camera-startup-readiness-inverse.json"
CONTROLLER_INVERSE_PATH = TREE / "scripts/ci/fixtures/android-camera-scalar-failfast-controller-inverse.json"
OBSERVATION_INVERSE_PATH = TREE / "scripts/ci/fixtures/android-camera-settings-absence-observation-inverse.json"
EXPECTED_INPUT_SHA256 = {
    "scripts/ci/android_camera_developer_prerequisite.py": "0e47097d10f1886bec0ee8eebc280b29afb704dc47d09df1bbdb41ddaa651b26",
    "scripts/ci/android_device_tests.py": "daac8786b1b034efcad0687a2f3a995c2216ea1a400116f9c592693d5c6395ec",
    "scripts/ci/test_android_camera_developer_prerequisite.py": "4a78c909420383a59cb453c1ca58ab3c0ca909a08f17201ddc0bcea657a061bb",
    "scripts/ci/camera_scalar_failfast_source_projection.py": "6858fbd343cefad52b709663fbf5e98bccfa52111c2a1b8fd6eff8d8536cdb12",
    "scripts/ci/fixtures/android-camera-scalar-failfast-controller-inverse.json": "9a3479f92b05e1bffda3b408ad9f5833ca655b0c913af813e888209de9b2828c",
    "scripts/ci/fixtures/android-camera-startup-readiness-inverse.json": "43a8963e59a7851e968fbbeeaafa19944956cbc6a6f0b5cb8924a4dba0342e2c",
    "scripts/ci/fixtures/android-camera-settings-absence-observation-inverse.json": "e7b0e9a3e361e39d1732ed33cd5e1d4e51a3e30ed377adf487001b742754c953",
}
UNCHANGED_NATIVE_SOURCE_SHA256 = {'.github/workflows/gradle.yml': '282254f7af66a47f065693f5fd4b30ae0acf8c44ca589fcc9432857ab473ef09', 'calf-camera-picker/build.gradle.kts': 'f074767f7042ac6e07955b361400e672ae43209f99b17986acd27cf5078428c7', 'calf-camera-picker/src/androidDeviceTest/AndroidManifest.xml': 'c24a6c2498dddb660cafd78d31bfc4f4730f8ae34f1c807eff3f17ff6034962b', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraProviderTest.kt': 'e222639ed728465798aa0be937f13dc181c36dfd566db0b2fa9bbdbe67f18532', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraRestorationTest.kt': '357c8545e35d5fa529a6b38b064a86c1724ea2b0a2d2b7ec46d5ff4c3671a7d0', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraRestorationVerificationActivity.kt': '8aeb2acf56287c08619c854f4da21c3f0c4f95d7dba19e17ca6ceacff03a0c12', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraVerificationProviders.kt': '09956cd5f88d5c18dff5be3251d9ece6beb679f5c961c3041e1450cf46e96f82', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedAlwaysFinish.kt': '2010803e066ce0de1a34051ed40a50c9bca08f238a6218dcaabb4e7d0a09bee7', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedCameraReceiver.kt': 'a15663164f0b66eccf225a0a24d0af7be77e13c80bc620be501d388224a76a6d', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedDeveloperSettingsUi.kt': 'a1fb76c6092881a3681ec38002b4820f1d0d8282727a4d18fa89968f6b8c5b50', 'calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt': 'b7094d795bfaa209b254bbf2c549de21a7fff07df636fbb68f4cb1a3baa917a7', 'calf-camera-picker/src/commonTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraRequestStateTest.kt': '0ff1470d93f9580e27b54e499b2dda6843a50c5d7b4f4b5c4cfaca7980c7e841', 'convention-plugins/src/main/kotlin/Android.kt': '204b7b0bb30e33144794ffda1d993f925f670cac87c809155d81fe9f09f7a256', 'scripts/ci/android_camera_receiver.py': '032ac23053338ec9e839cdae8b3a946a84712ff92a7f821f4972230241eb03a2', 'scripts/ci/library_tests.py': 'b333567dff6f85bad734077bb44b2f4028035316ee2c3771cbe82b2019d00dfb', 'scripts/ci/sample_platform_verification.py': '6780e5c355d22cf74716b0cb344fc02ee968710db5382d6460c930b99d395ca7', 'tests/consumer/android-camera-receiver/build.gradle.kts': '92000d4bad25e57121cb5c100363d44955f0bdef290372bd3da965342f1523f4', 'tests/consumer/android-camera-receiver/settings.gradle.kts': '31507eb3489726a100053c8624e941f2ad0511460a55a4f62edf6a8b9f850c4f', 'tests/consumer/android-camera-receiver/src/main/AndroidManifest.xml': '2e507acb6e0ec0f3fbb3c3bbc7908a5d882277804a68f670e8814160e16fadd5', 'tests/consumer/android-camera-receiver/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraDelayedReceiverActivity.java': '8a5df77d685676fe29842d4231e86d0a8cf7a3bc388ec69ccf95be28c1d59a93', 'tests/consumer/android-camera-receiver/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraReceiverActivity.java': '2df3ad3ab2e985fa87483c18f269f3fbcf98d44210cf2c346c955dc60a13c8c9', 'tests/consumer/android-camera-receiver/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraReceiverService.java': 'b7e366c37f91208afafd8fe6db1160a6048e740ead8c6cc334101b7a4a353a53'}  # Exact held source declarations; no recomputed/native plan acceptance.
# CI224 admits only the two already-qualified current Share188 shared leaves.
# The original UNCHANGED literal above and every native/control body stay exact;
# ordinary digest still reads actual bytes and never normalizes a historical pin.
CAMERA224_SHARE188_SHARED_SOURCE_SHA256 = {
    ".github/workflows/gradle.yml": "ac55aee1f485f78914de5405c517f4a9f8a5a6fed2f7ba88650e2a4fb8401561",
    "scripts/ci/library_tests.py": "5012c3e2be83e62eba8239a0db12104d5f9f7efb3f262abd3b3080012f7afdc2",
}
UNCHANGED_NATIVE_SOURCE_SHA256.update(CAMERA224_SHARE188_SHARED_SOURCE_SHA256)
FROZEN_HELPER_SHA256 = "5318d5893457dca141d08f3d269dc1a21078d42931c7846d4d105b7134154af1"
FROZEN_CONTROLLER_SHA256 = "02bb9ab153f147fab13bf58ff9fccaef754cc66f2dfcc067dc3ad2b1d8726640"
PRE_STARTUP_HELPER_SHA256 = "2d2fb89491d5435963b983052a96f7a9e80e02d9b7ed394c0b3d23cf4b194532"
HISTORICAL_HELPER_SHA256 = "f15163bd0406476d4c8e271aa6fa18c652590c1e1665ee7bb9306ca9140ddfd0"
DECLARED_METHODS = (
    "test_ff01_actual_new_run_scalar_refusal_prevents_all_reporter_assembly_and_native",
    "test_ff02_actual_new_run_captures_before_exact_assembly_and_never_promotes_preflight",
    "test_ff03_actual_new_run_nonzero_or_stop_keeps_compile_red_and_owned_boot_cleanup",
    "test_ff04_compile_and_secondary_publication_errors_keep_the_same_primary",
    "test_ff05_missing_apk_is_not_read_during_read_only_capture_and_no_success_is_inferred",
    "test_ff06_postcompile_master_scalar_native_or_row_presence_drift_never_recaptures",
    "test_ff07_postcompile_kernel_owner_runtime_user_or_home_drift_refuses_before_mutation",
    "test_ff08_postcompile_pending_state_is_a_single_refusal_not_a_new_startup_loop",
    "test_ff09_separate_postcompile_clock_command_and_total_bounds_refuse_late_results",
    "test_ff10_original_compiled_reporter_and_frozen_file_guards_still_refuse_after_capture",
    "test_ff11_assembly_and_capture_latches_refuse_unproved_or_repeated_completion",
    "test_ff12_new_timing_keeps_exact_original_mutation_and_owned_cleanup_boundaries",
    "test_ff13_other_profiles_keep_their_original_pre_native_order_and_no_c1_fields",
    "test_ff14_full_source_inverses_preserve_original_readers_actions_cleanup_and_single_call",
    "test_ff15_historical_fixture_projection_is_exact_and_cannot_qualify_mutated_current_source",
    "test_ff16_native_sources_plans_workflows_and_read_only_receipt_privacy_stay_exact",
    "test_ff17_terminal_postreporter_timeout_resets_phase_but_later_master_failure_keeps_completed_phase",
    "test_ff18_generic_discovery_needs_no_private_environment_and_scoped_temp_custody_stays_strict",
)
FOCUS = "android-camera-real-restoration-dont-keep"
CURRENT_USER = ("shell", "am", "get-current-user")
USER_STATE = ("shell", "am", "get-started-user-state", "0")
HOME = ("shell", "cmd", "package", "resolve-activity", "--components", "--query-flags", "0", "--user", "0",
        "-a", "android.intent.action.MAIN", "-c", "android.intent.category.HOME")
MARKER = "synthetic-unpublished-compiler-boundary-data"
COUNTERS = {"fresh_helper_models": 0, "fresh_controller_models": 0, "new_refusal_samples": 0,
            "compiler_boundaries": 0, "postcompile_drift_refusals": 0, "source_mutation_refusals": 0,
            "other_route_models": 0, "privacy_checkpoints": 0, "existing_accepted_test_methods_selected": 0,
            "native_invocations": 0}
FORBIDDEN_ACTIONS = []


def digest(path):
    # Private synthetic config bytes are not source-history inputs. Keep their
    # raw digest; only explicit source-tree identities enter the current bridge.
    if not path.is_relative_to(TREE):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    # Historical pins remain literal; the outer bridge separately admits raw current bytes.
    from android_external328_source_projection import read_current_source_for_history
    return hashlib.sha256(read_current_source_for_history(path, TREE)).hexdigest()


def forbidden(*args, **kwargs):
    FORBIDDEN_ACTIONS.append("forbidden-sdk-process-network-Git-build-or-native-action")
    raise AssertionError("No SDK, process, network, Git, build or native action is admitted")


def action_guards(stack):
    for module, names in (
        (subprocess, ("Popen", "run", "call", "check_call", "check_output", "getoutput", "getstatusoutput")),
        (os, ("kill", "killpg", "system", "popen", "fork", "forkpty", "posix_spawn", "posix_spawnp",
              "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe",
              "execl", "execle", "execlp", "execlpe", "execv", "execve", "execvp", "execvpe")),
        (socket, ("socket", "socketpair", "create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex")),
    ):
        for name in names:
            if hasattr(module, name):
                stack.enter_context(patch.object(module, name, forbidden))


def _checked_private_directory(value):
    """An existing owned0700 ordinary directory; validation never creates it."""
    if type(value) is not str or not value or len(value) > 4096:
        raise AssertionError("A bounded private model directory declaration is required")
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts:
        raise AssertionError("An absolute unambiguous private model directory is required")
    current = path
    try:
        while True:
            info = current.lstat()
            if not stat.S_ISDIR(info.st_mode) or current.is_symlink():
                raise AssertionError("No private model ancestor symlink or nondirectory is admitted")
            if current == current.parent:
                break
            current = current.parent
        info = path.lstat()
    except OSError:
        raise AssertionError("The declared private model directory is unavailable") from None
    if (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700 or
            path.is_relative_to(TREE) or TREE.is_relative_to(path)):
        raise AssertionError("Only a source-external owned0700 private model directory is admitted")
    return path


@contextmanager
def private_model_parent(value=None):
    """One fresh secure temporary root per scope, never a shared-directory fallback.

    Missing environment is the ordinary generic-CI contract, not a refusal waiver:
    tempfile creates a unique0700 child, then the same full ownership/no-symlink/
    source-external contract verifies it. A supplied parent must already satisfy
    that contract. No SDK/process/native action occurs and cleanup is scope-owned.
    This bounds root acquisitions and source writes, not filesystem wall-clock time.
    """
    parent = _checked_private_directory(value) if value is not None else None
    with tempfile.TemporaryDirectory(prefix="nativecmpkit-camera-failfast-model-", dir=parent) as name:
        private = _checked_private_directory(name)
        yield private


for relative, expected in EXPECTED_INPUT_SHA256.items():
    path = TREE / relative
    if path.is_symlink() or digest(path) != expected:
        raise AssertionError("Exact fail-fast owning input source binding is changed")
SOURCE_HASHES_BEFORE = {relative: digest(TREE / relative) for relative in EXPECTED_INPUT_SHA256}
def _load_inert_fixture(private):
    global projection, fixtures, helper
    if any(value is not None for value in (projection, fixtures, helper)):
        raise AssertionError("No private reusable-fixture import retry is admitted")
    _checked_private_directory(str(private))
    for relative, expected in EXPECTED_INPUT_SHA256.items():
        path = TREE / relative
        if path.is_symlink() or digest(path) != expected:
            raise AssertionError("Exact fail-fast source changed before fixture acquisition")
    PROJECTION_SPEC = importlib.util.spec_from_file_location("nativecmpkit_camera_failfast_projection_fixture", PROJECTION_PATH)
    projection = importlib.util.module_from_spec(PROJECTION_SPEC)
    FIXTURE_SPEC = importlib.util.spec_from_file_location("nativecmpkit_camera_failfast_reusable_test_free_fixture", FIXTURE_PATH)
    fixtures = importlib.util.module_from_spec(FIXTURE_SPEC)
    with ExitStack() as import_guards, patch.dict(os.environ, {"CAMERA_PREREQUISITE_MODEL_TREE": str(TREE),
                                                            "CAMERA_PREREQUISITE_MODEL_TMP": str(PRIVATE)}), \
            patch.dict(sys.modules, {PROJECTION_SPEC.name: projection, FIXTURE_SPEC.name: fixtures,
                                     "camera_scalar_failfast_source_projection": projection}):
        action_guards(import_guards)
        PROJECTION_SPEC.loader.exec_module(projection)
        FIXTURE_SPEC.loader.exec_module(fixtures)
    helper = fixtures.camera
    if (Path(fixtures.__file__).resolve() != FIXTURE_PATH or fixtures.__spec__.origin != str(FIXTURE_PATH) or
            Path(helper.__file__).resolve() != HELPER_PATH or helper.__spec__.origin != str(HELPER_PATH) or
            any(name.startswith("test_") for name in fixtures.ModelFixture.__dict__)):
        raise AssertionError("Only the exact reusable test-free owning fixture may be constructed")


# Retain the exact pre-handoff compiler-boundary stage for these old controls;
# the additive read-only handoff is qualified by its own new controls.
from camera_boot_handoff_source_projection import current_source_before_boot_handoff
CONTROLLER_SOURCE = current_source_before_boot_handoff(
    "scripts/ci/android_device_tests.py", CONTROLLER_PATH.read_bytes()).decode("utf-8")
CONTROLLER_AST = ast.parse(CONTROLLER_SOURCE)
CONTROLLER_NODES = [node for node in CONTROLLER_AST.body if isinstance(node, ast.FunctionDef) and node.name in ("_run", "preflight_error_origin")]
if {node.name for node in CONTROLLER_NODES} != {"_run", "preflight_error_origin"}:
    raise AssertionError("The two exact controller definitions must be selected")


def caught(call):
    try:
        call()
    except BaseException as error:
        COUNTERS["new_refusal_samples"] += 1
        return error
    raise AssertionError("The new compiler-boundary control unexpectedly passed")


def normalize_runner(device):
    original = device.runner

    def runner(argv, **kwargs):
        result = original(argv, **kwargs)
        if type(result) is subprocess.CompletedProcess:
            result.args = list(argv)  # Synthetic result only; mirror the actual requested CompletedProcess argv.
        return result

    return runner


@contextmanager
def fresh_helper(*, master=None, scalar=None, native=False):
    fixture = fixtures.ModelFixture("runTest")
    fixture.setUp()
    try:
        fixture.model(master if master is not None else helper.Row(True, "1"), scalar=scalar, native=native)
        fixture.owner.runner = normalize_runner(fixture.device)
        fixture.wait_calls, fixture.sleep_calls = 0, []
        original_wait, original_sleep = fixture.owner.wait_startup_readiness, fixture.owner.sleep

        def wait():
            fixture.wait_calls += 1
            return original_wait()

        def sleep(duration):
            fixture.sleep_calls.append(duration)
            return original_sleep(duration)

        fixture.owner.wait_startup_readiness, fixture.owner.sleep = wait, sleep
        COUNTERS["fresh_helper_models"] += 1
        yield fixture
    finally:
        fixture.tearDown()


def stage_compile(fixture, *, elapsed=350.13):
    fixture.clock.now += elapsed
    fixture.owner.record_reporter_assembly_success({"exit_code": 0, "stop_reason": None})
    COUNTERS["compiler_boundaries"] += 1


class FlowModel:
    """Actual new _run plus real candidate developer methods; every exterior action is inert.

    The guest/controller/SDK observations below are synthetic owning models, not
    fresh native receipt substitutes. All camera native work stops before the
    receiver factory. Other profiles stop at their original boot boundary.
    """
    def __init__(self, *, focus=FOCUS, api=35, camera_route=True, master=None, scalar_refusal=False,
                 assembly_code=0, assembly_stop=None, assembly_error=None, publication_error=None,
                 compile_elapsed=350.13, during_compile=None, io=False, permission=False, storage=False):
        self.focus, self.api, self.camera_route = focus, api, camera_route
        self.master = master if master is not None else helper.Row(True, "1")
        self.scalar_refusal = scalar_refusal
        self.assembly_code, self.assembly_stop, self.assembly_error = assembly_code, assembly_stop, assembly_error
        self.publication_error, self.publication_failed = publication_error, False
        self.compile_elapsed, self.during_compile = compile_elapsed, during_compile
        self.io, self.permission, self.storage = io, permission, storage
        self.events, self.failures, self.writes, self.compiler_samples = [], [], {}, []
        self.guest = self.developer = self.device = self.process = None
        self.clock = fixtures.ModelClock()
        self.stack = ExitStack()
        self.required = focus == FOCUS

    def __enter__(self):
        _checked_private_directory(str(PRIVATE))  # Never recreate/adopt a lost custody root.
        self.temp = tempfile.TemporaryDirectory(prefix="new-c1-controller-", dir=PRIVATE)
        self.root = Path(self.temp.name)
        self.home = self.root / "synthetic-sdk-not-executed"
        for relative in (helper.CONVENTION, helper.MODULE + "/build.gradle.kts"):
            destination = self.root / relative
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            shutil.copyfile(TREE / relative, destination)
        analyzer = self.home / "cmdline-tools/23.0/bin/apkanalyzer"
        analyzer.parent.mkdir(mode=0o700, parents=True)
        analyzer.write_text("synthetic fixture, never an executed analyzer")
        analyzer.chmod(0o700)
        self.apk_base = self.root / helper.MODULE / "build/outputs/apk/androidTest"
        self.apk = self.apk_base / "synthetic-reporter.apk"
        self.stack.enter_context(patch.dict(os.environ, {"ANDROID_HOME": str(self.home)}, clear=True))
        plan = {"expected": [{"project": ":calf-camera-picker", "task": ":calf-camera-picker:connectedAndroidDeviceTest"}],
                "complete_suite_requested": False, "explicit_module_subset": [helper.MODULE],
                "test_bearing_modules_not_requested": [], "finite_only_device_modules_not_requested": []}
        self.assemble = ["synthetic-gradle-not-executed", "--no-daemon", "-PsyntheticSerial=" + helper.SERIAL,
                         ":calf-camera-picker:assembleAndroidDeviceTest"]
        lt = types.SimpleNamespace(
            safe_path=lambda root, relative: root / relative,
            plan=lambda *args, **kwargs: copy.deepcopy(plan),
            android_io_documents_required=lambda plan: self.io,
            android_permission_demo_required=lambda plan: self.permission,
            android_storage_probe_required=lambda plan: self.storage,
            android_camera_receiver_required=lambda plan: self.camera_route,
            android_geo_probe_required=lambda plan: False,
            android_share_recipient_required=lambda plan: False,
            ANDROID_CAMERA_FOCUSES={FOCUS, "android-camera-real-restoration", "android-camera-provider"},
            ANDROID_IO_PROVIDER_FOCUS="android-io-provider", ANDROID_IO_UNAVAILABLE_FOCUS="android-io-provider-unavailable",
            ANDROID_IO_DEFAULT_DECODE_FOCUS="android-io-default-decode", ANDROID_IO_REFERENCE_FOCUS="android-io-reference",
            ANDROID_IO_NAMED_SYSTEM_FOCUS="android-io-named-system-providers", WEBVIEW_ANDROID_MEDIA_FOCUS="webview-android-media",
            gradle_command=lambda *args, **kwargs: list(self.assemble) if kwargs.get("for_assembly") else
                self.assemble[:-1] + [":calf-camera-picker:connectedAndroidDeviceTest"],
            snapshot_inputs=lambda root: {"synthetic-controller-source": EXPECTED_INPUT_SHA256["scripts/ci/android_device_tests.py"]},
            git_revision=lambda root: "synthetic-not-a-Git-read", utc_now=lambda: "2000-01-01T00:00:00Z",
            write_json=self.write_json, execute=self.execute, run=forbidden)
        exterior = types.SimpleNamespace(OwnedGeoProbe=forbidden, OwnedShareDocuments=forbidden,
                                        OwnedShareRecipient=forbidden, OwnedIoDocuments=forbidden,
                                        OwnedPermissionDemo=forbidden, OwnedStorageProbe=forbidden,
                                        OwnedHeap=forbidden)
        globals_ = {"__name__": "nativecmpkit_new_c1_actual_controller_definition", "__file__": str(CONTROLLER_PATH),
            "Path": Path, "os": os, "re": helper.re, "shutil": shutil, "signal": helper.signal, "uuid": helper.uuid,
            "time": helper.time, "subprocess": types.SimpleNamespace(Popen=self.launch, STDOUT=subprocess.STDOUT,
                SubprocessError=subprocess.SubprocessError), "lt": lt,
            "runtime": types.SimpleNamespace(capture=lambda **kwargs: {"source_revision": "synthetic-not-a-Git-read", "source_tree_dirty": False}),
            "camera_developer": types.SimpleNamespace(is_required=helper.is_required, OwnedFreshGuest=self.Guest,
                OwnedDeveloperPrerequisite=self.Developer, accepted=helper.accepted),
            "android_camera_receiver": types.SimpleNamespace(OwnedCameraReceiver=self.receiver_boundary),
            "android_geo_probe": exterior, "android_share_recipient": exterior, "android_io_documents": exterior,
            "android_permission_demo": exterior, "android_storage_probe": exterior, "android_webview_heap": exterior,
            "API": 35, "SERIAL": helper.SERIAL, "PORT": 5588, "RESERVE_MIB": 8192,
            "sdk_assets": lambda *args, **kwargs: {"system_image": f"system-images;android-{self.api};google_apis;x86_64"},
            "ensure_ports_unused": lambda: None, "adb": lambda *args, **kwargs: "List of devices attached",
            "avd_name": lambda *args: self.guest.name if self.guest is not None else fixtures.NAME,
            "wait_for_owned_boot": self.boot, "stop_owned_emulator": self.stop,
            "wait_for_owned_transport_removal": self.transport_absent}
        exec(compile(ast.Module(body=copy.deepcopy(CONTROLLER_NODES), type_ignores=[]), str(CONTROLLER_PATH), "exec"), globals_)
        self.run_controller = globals_["_run"]  # Actual current source, never the historical projection.
        COUNTERS["fresh_controller_models"] += 1
        return self

    def __exit__(self, *exc):
        try:
            if self.guest is not None and not self.guest.closed:
                self.guest.finish()
            self.stack.close()
        finally:
            self.temp.cleanup()

    def write_json(self, path, value):
        self.writes[path.name] = copy.deepcopy(value)
        path.write_text(json.dumps(value, sort_keys=True))

    def Guest(self, root, output, name, environment):
        model = self

        class Guest(fixtures.FakeGuest):
            def __init__(self):
                super().__init__(root, output)
                self.name, self.environment = name, dict(environment)
                self.launch_attempted = self.captured = False
                self.process, self.pid, self.config_digest = None, None, None
                self.receipt = {"schema": "nativecmpkit.camera-fresh-guest.v1", "errors": [], "launch_attempted": False}
                model.guest = self

            def create(self):
                model.events.append("guest.create")
                for directory in ("avd", "android-user"):
                    (output / directory).mkdir(mode=0o700)

            def capture_avd(self, home):
                model.events.append("guest.capture")
                assert home == model.home and not self.captured and not self.launch_attempted
                self.config_digest = digest(output / "avd/synthetic-config")
                self.captured = True

            def verify_config(self):
                helper.require(self.captured and digest(output / "avd/synthetic-config") == self.config_digest,
                               "Synthetic captured config identity changed")

            def before_launch(self):
                model.events.append("guest.before-launch")
                self.verify_config()
                assert not self.launch_attempted
                self.launch_attempted = True
                self.receipt["launch_attempted"] = True

            def attach(self, process):
                model.events.append("guest.attach")
                assert self.launch_attempted and self.process is None
                self.process, self.pid = process, process.pid

            def verify_live(self):
                self.verify_config()
                helper.require(self.live and self.process is model.process and self.process.pid == self.pid and
                               self.process.poll() is None and self.process.group_owned,
                               "Synthetic same owned direct child/config identity lost")
                return True

            def dispose(self, *, engine_exited, transport_absent, clean_shutdown):
                model.events.append("guest.dispose")
                assert self.launch_attempted and engine_exited and transport_absent
                config_same = digest(output / "avd/synthetic-config") == self.config_digest
                for directory in ("avd", "android-user"):
                    shutil.rmtree(output / directory)
                self.receipt.update(disposal_status="passed" if config_same else "failed", roots_absent=True,
                    identity_confined_disposal=config_same, engine_known_exited=engine_exited,
                    owned_transport_absent=transport_absent, clean_shutdown=clean_shutdown)
                self.finish()
                return dict(self.receipt)

        return Guest()

    def Developer(self, root, output, home, serial, guest):
        assert root == self.root and home == self.home and guest is self.guest
        self.events.append("developer.acquired")
        self.device = fixtures.DeviceModel(guest, self.master)
        self.device.apk_digest = hashlib.sha256(b"synthetic-not-an-actual-APK").hexdigest()
        if self.scalar_refusal:
            self.device.hook = lambda arguments, device: fixtures.cp(b"0 ") if arguments == (
                "shell", "settings", "--user", "0", "get", "global", helper.MASTER) else None
        owner = helper.OwnedDeveloperPrerequisite(root, output, home, serial, guest,
            runner=normalize_runner(self.device), clock=self.clock, sleep=self.clock.sleep)
        self.developer = owner
        original_capture, original_prepare = owner.capture_before_reporter, owner.prepare
        original_failure, original_publish = owner.failure, owner.publish

        def capture():
            self.events.append("developer.capture.begin")
            receipt = original_capture()
            self.events.append("developer.capture.end")
            return receipt

        def prepare():
            self.events.append("developer.complete.begin")
            receipt = original_prepare()
            self.events.append("developer.complete.end")
            return receipt

        def failure(phase, error):
            self.failures.append((phase, error))
            self.last_failure_phase = phase
            return original_failure(phase, error)

        def publish():
            if (self.publication_error is not None and not self.publication_failed and
                    getattr(self, "last_failure_phase", None) == "reporter-assembly"):
                self.publication_failed = True
                raise self.publication_error
            return original_publish()

        owner.capture_before_reporter, owner.prepare, owner.failure, owner.publish = capture, prepare, failure, publish
        return owner

    def execute(self, root, command, log, timeout, reserve, *, env):
        assert root == self.root and reserve == 8192 and env["ANDROID_SERIAL"] == helper.SERIAL
        stage = log.stem
        self.events.append(stage)
        if stage == "owned-avd-create":
            assert timeout == 120
            if self.guest is not None:
                (self.guest.output / "avd/synthetic-config").write_bytes(b"synthetic-owned-config")
            return {"exit_code": 0, "stop_reason": None}
        assert stage == "apk-assembly" and timeout == 900 and command == self.assemble
        if self.required:
            owner = self.developer
            assert owner is not None and owner._pre_reporter_capture_completed and owner.original is not None
            assert self.guest.process is self.process and self.process.poll() is None
            assert owner.startup_deadline is owner.startup_last_clock is owner.deadline is None
            assert owner.receipt["prepare_status"] == "running" and self.device.actions == []
            assert not owner.receipt["reporter_dispatch_attempted"] and not owner.receipt["native_acceptance_inferred"]
            assert owner.reporter.path is owner.reporter.digest is owner.reporter.metadata_identity is None
            self.compiler_samples.append(copy.deepcopy(owner.receipt))
            self.clock.now += self.compile_elapsed
            if self.during_compile is not None:
                self.during_compile(self)
            COUNTERS["compiler_boundaries"] += 1
        if self.assembly_error is not None:
            raise self.assembly_error
        self.apk_base.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.apk.write_bytes(b"synthetic-not-an-actual-APK")
        (self.apk_base / "output-metadata.json").write_text(json.dumps({"applicationId": helper.REPORTER,
            "variantName": "androidDeviceTest", "artifactType": {"type": "APK"},
            "elements": [{"type": "SINGLE", "filters": [], "outputFile": self.apk.name}]}))
        return {"exit_code": self.assembly_code, "stop_reason": self.assembly_stop}

    def launch(self, command, **kwargs):
        self.events.append("emulator.launch")
        assert self.process is None and kwargs["start_new_session"] is True
        assert command[0] == str(self.home / "emulator/emulator")
        self.process = types.SimpleNamespace(pid=4242, returncode=None, group_owned=True)
        self.process.poll = lambda: self.process.returncode
        return self.process

    def boot(self, home, process, name, root, **kwargs):
        self.events.append("boot.boundary")
        assert process is self.process and root == self.root
        if not self.required:
            raise RuntimeError("Synthetic other-profile stop before helpers and native")
        return {"api_level": "35", "abi": "x86_64", "selinux": "Enforcing", "boot_completed": "1"}

    def receiver_boundary(self, *args, **kwargs):
        self.events.append("receiver.boundary-no-install")
        assert self.developer.receipt["prepare_status"] == "passed"
        raise RuntimeError("Synthetic C1 stop before receiver install and native")

    def stop(self, home, process, name, verified):
        self.events.append("emulator.stop")
        assert process is self.process
        process.returncode = 0
        return {"exit_code": 0, "clean_shutdown": verified is True,
                "graceful_kill_requested": verified is True, "forced_owned_group": False}

    def transport_absent(self, home):
        self.events.append("transport.absent")
        assert self.process.poll() is not None
        return True

    def run(self):
        return self.run_controller(self.root, "build/ci-verification/new-only-flow",
            (helper.MODULE,) if self.required else None, focus=self.focus, api_level=self.api)


class PreReporterFailFastNewOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global PRIVATE
        if PRIVATE is not None:
            raise AssertionError("No private model custody-root reacquisition is admitted")
        cls.private_scope = ExitStack()
        cls.addClassCleanup(cls.private_scope.close)
        PRIVATE = cls.private_scope.enter_context(private_model_parent(
            os.environ.get("NATIVECMPKIT_CAMERA_FAILFAST_MODEL_TMP")))
        _load_inert_fixture(PRIVATE)

    def setUp(self):
        _checked_private_directory(str(PRIVATE))
        self.guards = ExitStack()
        self.addCleanup(self.guards.close)
        action_guards(self.guards)
        self.guards.enter_context(patch.object(helper, "bounded_run", forbidden))
        self.guards.enter_context(patch.object(helper, "probe_child", forbidden))

    def tearDown(self):
        self.assertEqual(FORBIDDEN_ACTIONS, [])
        self.assertEqual({relative: digest(TREE / relative) for relative in EXPECTED_INPUT_SHA256}, SOURCE_HASHES_BEFORE)

    def assert_no_success(self, receipt):
        self.assertNotEqual(receipt["prepare_status"], "passed")
        self.assertFalse(receipt["reporter_dispatch_attempted"])
        self.assertFalse(receipt["native_acceptance_inferred"])
        self.assertEqual([receipt[key] for key in ("master_enable_attempts", "normal_reboot_attempts", "master_restore_attempts")], [0, 0, 0])

    def assert_post_refusal(self, fixture, error):
        self.assertIsInstance(error, (ValueError, TimeoutError))
        self.assertIs(fixture.owner.original, fixture.owner._pre_reporter_original)
        self.assertEqual(fixture.owner.receipt["startup_readiness_status"], "passed")
        self.assertEqual(fixture.owner.receipt["post_reporter_revalidation_status"], "failed")
        self.assertEqual(fixture.owner.receipt["post_reporter_revalidation_attempts"], 1)
        self.assertEqual(fixture.wait_calls, 1)
        self.assertEqual(fixture.sleep_calls, [0.5])
        self.assertIsNone(fixture.owner.startup_deadline)
        self.assertIsNone(fixture.owner.startup_last_clock)
        self.assertIsNone(fixture.owner.post_reporter_deadline)
        self.assertIsNone(fixture.owner.post_reporter_last_clock)
        self.assertIsNone(fixture.owner.deadline)
        self.assertEqual(fixture.device.actions, [])
        self.assert_no_success(fixture.owner.receipt)
        COUNTERS["postcompile_drift_refusals"] += 1

    def test_ff01_actual_new_run_scalar_refusal_prevents_all_reporter_assembly_and_native(self):
        with FlowModel(scalar_refusal=True) as model:
            result = model.run()
            self.assertEqual(result["controller_error"], "ValueError")
            self.assertEqual(set(result["setup_stages"]), {"owned-avd-create"})
            self.assertNotIn("apk-assembly", model.events)
            self.assertFalse(model.apk.exists())
            self.assertIsNone(model.developer.original)
            receipt = result["camera_developer_prerequisite"]
            self.assertEqual((receipt["prepare_status"], receipt["cleanup_status"], receipt["startup_readiness_status"]),
                             ("failed", "failed", "failed"))
            self.assertEqual([phase for phase, _ in model.failures], ["prepare", "cleanup"])
            self.assertEqual(model.failures[0][1].args, ("Unknown scalar control shape",))
            self.assertEqual(model.failures[1][1].args, ("Original exact state was not acquired",))
            self.assertEqual(receipt["errors"][0]["scalar_control_refusal"]["setting_key"], helper.MASTER)
            self.assertEqual(receipt["errors"][0]["scalar_control_refusal"]["query"], "global-settings-get-user0")
            self.assertEqual(model.device.actions, [])
            self.assert_no_success(receipt)
            self.assertFalse(result["passed"])
            self.assertFalse(result["test_suite_passed"])
            self.assertNotIn("test_totals", result)
            self.assertNotIn("receiver.boundary-no-install", model.events)
            self.assertTrue(result["emulator_shutdown"]["clean_shutdown"])
            self.assertTrue(result["camera_guest_disposal"]["roots_absent"])

    def test_ff02_actual_new_run_captures_before_exact_assembly_and_never_promotes_preflight(self):
        with FlowModel() as model:
            result = model.run()
            order = ["guest.create", "owned-avd-create", "guest.capture", "guest.before-launch", "emulator.launch",
                     "guest.attach", "boot.boundary", "developer.acquired", "developer.capture.begin",
                     "developer.capture.end", "apk-assembly", "developer.complete.begin", "developer.complete.end",
                     "receiver.boundary-no-install", "emulator.stop", "transport.absent", "guest.dispose"]
            self.assertEqual([model.events.index(item) for item in order], sorted(model.events.index(item) for item in order))
            self.assertEqual(model.events.count("apk-assembly"), 1)
            self.assertEqual(model.events.count("emulator.launch"), 1)
            self.assertEqual(len(model.compiler_samples), 1)
            before = model.compiler_samples[0]
            self.assertEqual((before["prepare_status"], before["reporter_compile_preflight_status"]), ("running", "passed"))
            self.assertFalse(before["reporter_assembly_recorded_passed"])
            self.assertNotIn("reporter_source_apk_sha256", before)
            receipt = result["camera_developer_prerequisite"]
            self.assertEqual(receipt["post_reporter_revalidation_status"], "passed")
            self.assertEqual(receipt["post_reporter_revalidation_attempts"], 1)
            self.assertEqual(receipt["startup_observations"], 2)
            self.assertFalse(receipt["reporter_dispatch_attempted"])
            self.assertFalse(result["passed"])
            self.assertFalse(result["test_suite_passed"])
            self.assertNotIn("test_totals", result)

    def test_ff03_actual_new_run_nonzero_or_stop_keeps_compile_red_and_owned_boot_cleanup(self):
        for code, stop in ((1, None), (0, "synthetic-explicit-stop")):
            with FlowModel(assembly_code=code, assembly_stop=stop) as model:
                result = model.run()
                receipt = result["camera_developer_prerequisite"]
                self.assertEqual(result["setup_stages"]["apk-assembly"], {"exit_code": code, "stop_reason": stop})
                self.assertEqual(result["controller_error"], "RuntimeError")
                self.assertEqual(receipt["prepare_status"], "failed")
                self.assertEqual(receipt["post_reporter_revalidation_attempts"], 0)
                self.assertFalse(receipt["reporter_assembly_recorded_passed"])
                self.assertNotIn("reporter_source_apk_sha256", receipt)
                self.assertNotIn("developer.complete.begin", model.events)
                self.assertNotIn("receiver.boundary-no-install", model.events)
                self.assertEqual(model.device.actions, [])
                self.assertFalse(result["passed"])
                self.assertTrue(result["emulator_shutdown"]["clean_shutdown"])
                self.assertTrue(result["camera_guest_disposal"]["roots_absent"])

    def test_ff04_compile_and_secondary_publication_errors_keep_the_same_primary(self):
        for primary in (OSError(MARKER), RuntimeError(MARKER), KeyboardInterrupt(MARKER)):
            with FlowModel(assembly_error=primary, publication_error=ValueError("synthetic-secondary")) as model:
                result = model.run()
                self.assertIs(model.failures[0][1], primary)
                self.assertEqual(model.failures[0][0], "reporter-assembly")
                self.assertEqual(primary.args, (MARKER,))
                self.assertEqual(result["controller_error"], type(primary).__name__)
                self.assertTrue(model.publication_failed)
                self.assertEqual(result["camera_developer_prerequisite"]["prepare_status"], "failed")
                self.assertNotIn("developer.complete.begin", model.events)
                self.assertNotIn(MARKER, json.dumps(result))
                self.assertFalse(result["passed"])

    def test_ff05_missing_apk_is_not_read_during_read_only_capture_and_no_success_is_inferred(self):
        with fresh_helper(master=helper.Row(False, None)) as fixture:
            parked_apk = fixture.apk.with_suffix(".unbuilt")
            parked_metadata = fixture.metadata.with_suffix(".unbuilt")
            fixture.apk.rename(parked_apk)
            fixture.metadata.rename(parked_metadata)
            with patch.object(fixture.owner.reporter, "freeze", forbidden):
                receipt = fixture.owner.capture_before_reporter()
            self.assertEqual((receipt["prepare_status"], receipt["reporter_compile_preflight_status"]), ("running", "passed"))
            self.assertTrue(receipt["reporter_initial_absent"])
            self.assertTrue(receipt["receiver_initial_absent"])
            self.assertIsNone(fixture.owner.reporter.path)
            self.assertNotIn("reporter_source_apk_sha256", receipt)
            self.assertEqual(fixture.device.actions, [])
            self.assert_no_success(receipt)
            parked_apk.rename(fixture.apk)
            parked_metadata.rename(fixture.metadata)
            stage_compile(fixture)
            prepared = fixture.owner.prepare()
            self.assertEqual(prepared["prepare_status"], "passed")
            self.assertEqual(prepared["master_enable_attempts"], 1)
            self.assertFalse(prepared["reporter_dispatch_attempted"])

    def test_ff06_postcompile_master_scalar_native_or_row_presence_drift_never_recaptures(self):
        for master, scalar, native in ((helper.Row(True, "0"), helper.Row(False, None), False),
                                      (helper.Row(True, "1"), helper.Row(True, "0"), False),
                                      (helper.Row(True, "1"), helper.Row(True, "1"), True),
                                      (helper.Row(True, "1"), helper.Row(False, None), True)):
            with fresh_helper() as fixture:
                fixture.owner.capture_before_reporter()
                original = fixture.owner.original
                stage_compile(fixture)
                fixture.device.master, fixture.device.scalar, fixture.device.native = master, scalar, native
                error = caught(fixture.owner.prepare)
                self.assertEqual(error.args, ("Exact original master/native/scalar/epoch changed while the reporter compiled",))
                self.assertIs(fixture.owner.original, original)
                self.assert_post_refusal(fixture, error)
                closed = fixture.close_model()
                self.assertEqual(closed["prepare_status"], "failed")
                self.assertEqual(fixture.device.actions, [])

    def test_ff07_postcompile_kernel_owner_runtime_user_or_home_drift_refuses_before_mutation(self):
        for target, payload in ((CURRENT_USER, b"10\n"), (USER_STATE, b"RUNNING_LOCKED\n"),
                                (HOME, b"org.example.otherhome/.OtherActivity\n"),
                                (("shell", "getprop", "ro.product.cpu.abi"), b"x86\n"),
                                (("shell", "getenforce"), b"Permissive\n"),
                                (("emu", "avd", "name"), b"foreign-avd\nOK\n"),
                                (("shell", "id", "-u"), b"0\n"),
                                (("shell", "cat", "/proc/sys/kernel/random/boot_id"), (fixtures.NEW + "\n").encode())):
            with fresh_helper() as fixture:
                fixture.owner.capture_before_reporter()
                stage_compile(fixture)
                fixture.device.hook = lambda arguments, device: fixtures.cp(payload) if arguments == target else None
                error = caught(fixture.owner.prepare)
                self.assert_post_refusal(fixture, error)
        for during in (lambda model: setattr(model.guest, "live", False),
                       lambda model: setattr(model.process, "group_owned", False),
                       lambda model: (model.guest.output / "avd/synthetic-config").write_bytes(b"synthetic-config-drift")):
            with FlowModel(during_compile=during) as model:
                result = model.run()
                self.assertEqual(result["camera_developer_prerequisite"]["prepare_status"], "failed")
                self.assertNotIn("developer.complete.end", model.events)
                self.assertNotIn("receiver.boundary-no-install", model.events)
                self.assertEqual(model.device.actions, [])
                self.assertFalse(result["passed"])

    def test_ff08_postcompile_pending_state_is_a_single_refusal_not_a_new_startup_loop(self):
        for target, payload in ((USER_STATE, b"BOOTING\n"), (HOME, b"com.android.settings/.FallbackHome\n"),
                                (HOME, b"No activity found\n")):
            with fresh_helper() as fixture:
                fixture.owner.capture_before_reporter()
                original = fixture.owner.original
                stage_compile(fixture, elapsed=900.0)
                calls = []

                def hook(arguments, device):
                    if arguments == target:
                        calls.append(arguments)
                        return fixtures.cp(payload)

                fixture.device.hook = hook
                error = caught(fixture.owner.prepare)
                self.assertEqual(error.args, ("Typed startup identity changed while the reporter compiled",))
                self.assertEqual(calls, [target])
                self.assertIs(fixture.owner.original, original)
                self.assert_post_refusal(fixture, error)
                second = caught(fixture.owner.prepare)
                self.assertIs(type(second), ValueError)
                self.assertEqual(fixture.wait_calls, 1)
                self.assertEqual(calls, [target])

    def test_ff09_separate_postcompile_clock_command_and_total_bounds_refuse_late_results(self):
        for advance in (10.01, 120.0, float("nan"), float("inf"), -1.0):
            with fresh_helper() as fixture:
                fixture.owner.capture_before_reporter()
                stage_compile(fixture)
                used = []

                def hook(arguments, device):
                    if not used and fixture.owner.post_reporter_deadline is not None:
                        used.append(arguments)
                        fixture.clock.now += advance

                fixture.device.hook = hook
                error = caught(fixture.owner.prepare)
                self.assertIsInstance(error, (ValueError, TimeoutError))
                self.assertEqual(len(used), 1)
                self.assertIsNone(fixture.owner.post_reporter_deadline)
                self.assertIsNone(fixture.owner.post_reporter_last_clock)
                self.assertIsNone(fixture.owner.startup_deadline)
                self.assertIsNone(fixture.owner.deadline)
                self.assert_no_success(fixture.owner.receipt)
                self.assertEqual(fixture.device.actions, [])
        with fresh_helper() as fixture:
            fixture.owner.capture_before_reporter()
            stage_compile(fixture)
            received = []
            actual = fixture.owner.runner

            def runner(argv, **kwargs):
                if fixture.owner.post_reporter_deadline is not None:
                    received.append(kwargs["timeout"])
                return actual(argv, **kwargs)

            fixture.owner.runner = runner
            fixture.owner.prepare()
            self.assertTrue(received)
            self.assertTrue(all(0 < timeout <= 10.0 for timeout in received))

    def test_ff10_original_compiled_reporter_and_frozen_file_guards_still_refuse_after_capture(self):
        with fresh_helper() as fixture:
            fixture.owner.capture_before_reporter()
            stage_compile(fixture)
            fixture.metadata_data["applicationId"] = "foreign.synthetic.reporter"
            fixture.metadata.write_text(json.dumps(fixture.metadata_data))
            error = caught(fixture.owner.prepare)
            self.assertEqual(error.args, ("Wrong selected reporter metadata",))
            self.assertEqual(fixture.owner.receipt["prepare_status"], "failed")
            self.assertEqual(fixture.device.actions, [])
            self.assertFalse(fixture.owner.receipt["reporter_dispatch_attempted"])
        with fresh_helper() as fixture:
            fixture.owner.capture_before_reporter()
            stage_compile(fixture)
            visits = []
            original = fixture.owner.reporter.unchanged

            def change_after_freeze():
                visits.append(True)
                if len(visits) == 2:
                    fixture.apk.write_bytes(b"synthetic-different-owned-file")
                return original()

            fixture.owner.reporter.unchanged = change_after_freeze
            error = caught(fixture.owner.prepare)
            self.assertEqual(error.args, ("Frozen source APK/metadata changed; refuse managed install/uninstall",))
            self.assertEqual(len(visits), 2)
            self.assert_no_success(fixture.owner.receipt)
            self.assertEqual(fixture.device.actions, [])

    def test_ff11_assembly_and_capture_latches_refuse_unproved_or_repeated_completion(self):
        with fresh_helper() as fixture:
            before = caught(lambda: fixture.owner.record_reporter_assembly_success({"exit_code": 0}))
            self.assertIs(type(before), ValueError)
            self.assertEqual(fixture.owner.receipt["prepare_status"], "not-started")
            fixture.owner.capture_before_reporter()
            unproved = caught(fixture.owner.prepare)
            self.assertIs(type(unproved), ValueError)
            self.assertFalse(fixture.owner._post_reporter_started)
            for execution in ({"exit_code": 1}, {"exit_code": 0, "stop_reason": "synthetic-stop"}):
                error = caught(lambda: fixture.owner.record_reporter_assembly_success(execution))
                self.assertEqual(error.args, ("Reporter assembly did not pass the unchanged exit/stop guard",))
                self.assertFalse(fixture.owner._reporter_assembly_completed)
            repeated_capture = caught(fixture.owner.capture_before_reporter)
            self.assertIs(type(repeated_capture), ValueError)
            stage_compile(fixture)
            repeated_compile = caught(lambda: fixture.owner.record_reporter_assembly_success({"exit_code": 0}))
            self.assertIs(type(repeated_compile), ValueError)
            fixture.owner.prepare()
            repeat = caught(fixture.owner.prepare)
            self.assertIs(type(repeat), ValueError)
            self.assertEqual(fixture.wait_calls, 1)
            self.assertEqual(fixture.owner.receipt["post_reporter_revalidation_attempts"], 1)

    def test_ff12_new_timing_keeps_exact_original_mutation_and_owned_cleanup_boundaries(self):
        with fresh_helper(master=helper.Row(False, None)) as fixture:
            fixture.owner.capture_before_reporter()
            original = fixture.owner.original
            self.assertEqual(fixture.device.actions, [])
            stage_compile(fixture)
            fixture.owner.prepare()
            self.assertIs(fixture.owner.original, original)
            self.assertEqual(fixture.device.actions, [("shell", "settings", "--user", "0", "put", "global", helper.MASTER, "1")])
            self.assertFalse(fixture.owner.receipt["reporter_dispatch_attempted"])
            closed = fixture.close_model()
            self.assertEqual(closed["cleanup_status"], "passed")
            self.assertEqual(fixture.device.actions, [("shell", "settings", "--user", "0", "put", "global", helper.MASTER, "1"),
                ("reboot",), ("shell", "settings", "--user", "0", "delete", "global", helper.MASTER)])
            self.assertEqual(closed["master_restore_attempts"], 1)
            self.assertFalse(helper.accepted(closed, fixture.disposal()))  # No reporter/native dispatch occurred.

    def test_ff13_other_profiles_keep_their_original_pre_native_order_and_no_c1_fields(self):
        cases = (
            (None, 35, False, False, False, False, ["apk-assembly", "owned-avd-create"]),
            ("android-camera-real-restoration", 35, True, False, False, False, ["owned-avd-create", "apk-assembly"]),
            ("android-camera-provider", 23, True, False, False, False, ["owned-avd-create"]),
            ("webview-android-media", 33, False, False, False, False, ["apk-assembly", "owned-avd-create"]),
            ("webview-android-media", 34, False, False, False, False, ["apk-assembly", "owned-avd-create"]),
            ("android-io-provider", 35, False, True, False, False, ["owned-avd-create"]),
            ("android-permission-demo-call-denial", 35, False, False, True, False, ["owned-avd-create"]),
            ("android-storage-api28", 28, False, False, False, True, ["owned-avd-create"]),
            ("android-storage-api29", 29, False, False, False, True, ["owned-avd-create"]),
            ("android-storage-api30", 30, False, False, False, True, ["owned-avd-create"]),
        )
        for focus, api, camera_route, io, permission, storage, stages in cases:
            with FlowModel(focus=focus, api=api, camera_route=camera_route, io=io, permission=permission, storage=storage) as model:
                result = model.run()
                self.assertEqual(model.events[:len(stages)], stages)
                self.assertEqual(model.events.count("emulator.launch"), 1)
                self.assertIsNone(model.guest)
                self.assertIsNone(model.developer)
                self.assertNotIn("camera_developer_prerequisite", result)
                self.assertNotIn("reporter_compile_deferred_until_camera_read_only_prerequisite", result)
                self.assertFalse(result["passed"])
                COUNTERS["other_route_models"] += 1

    def test_ff14_full_source_inverses_preserve_original_readers_actions_cleanup_and_single_call(self):
        current = projection.camera197_helper_source_before_owned_console(HELPER_PATH.read_text())
        contract = json.loads(STARTUP_INVERSE_PATH.read_bytes())
        self.assertEqual(len(contract["inverse_fragments"]), 17)
        frozen = current
        for fragment in contract["inverse_fragments"][:11]:
            self.assertEqual(frozen.count(fragment["new"]), 1)
            frozen = frozen.replace(fragment["new"], fragment["old"], 1)
        self.assertEqual(hashlib.sha256(frozen.encode()).hexdigest(), FROZEN_HELPER_SHA256)
        old_ast, new_ast = ast.parse(frozen), ast.parse(current)

        def function(tree, name):
            owner, dot, symbol = name.partition(".")
            body = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == owner).body if dot else tree.body
            return next(node for node in body if isinstance(node, ast.FunctionDef) and node.name == (symbol if dot else owner))

        names = ("require", "result_bytes", "parse_native", "parse_settings_activity_absence", "parse_recents", "parse_live_tasks",
                 "OwnedFreshGuest.verify_config", "OwnedFreshGuest.verify_live", "OwnedFreshGuest.dispose",
                 "Reporter.freeze", "Reporter.cleanup", "OwnedDeveloperPrerequisite.snapshot", "OwnedDeveloperPrerequisite.stable",
                 "OwnedDeveloperPrerequisite.action_guard", "OwnedDeveloperPrerequisite.wait_startup_readiness",
                 "OwnedDeveloperPrerequisite.startup_observation", "OwnedDeveloperPrerequisite.close", "accepted")
        for name in names:
            self.assertEqual(ast.dump(function(old_ast, name), include_attributes=False), ast.dump(function(new_ast, name), include_attributes=False))
        old_prepare = function(old_ast, "OwnedDeveloperPrerequisite.prepare")
        new_prepare = copy.deepcopy(function(new_ast, "OwnedDeveloperPrerequisite.prepare"))
        self.assertEqual(ast.dump(new_prepare.body[0], include_attributes=False), ast.dump(ast.parse(
            'if vars(self).get("_pre_reporter_capture_attempted") is True:\n    return self.complete_after_reporter()\n').body[0], include_attributes=False))
        new_prepare.body = new_prepare.body[1:]
        self.assertEqual(ast.dump(old_prepare, include_attributes=False), ast.dump(new_prepare, include_attributes=False))
        startup = function(new_ast, "OwnedDeveloperPrerequisite.startup_observation")
        post = copy.deepcopy(function(new_ast, "OwnedDeveloperPrerequisite.post_reporter_observation"))
        post.name = startup.name
        for node in ast.walk(post):
            if isinstance(node, ast.Attribute) and node.attr == "post_reporter_remaining":
                node.attr = "startup_remaining"
        self.assertEqual(ast.dump(startup, include_attributes=False), ast.dump(post, include_attributes=False))
        before = frozen
        for fragment in contract["inverse_fragments"][11:]:
            self.assertEqual(before.count(fragment["new"]), 1)
            before = before.replace(fragment["new"], fragment["old"], 1)
        self.assertEqual(hashlib.sha256(before.encode()).hexdigest(), PRE_STARTUP_HELPER_SHA256)
        observation = json.loads(OBSERVATION_INVERSE_PATH.read_bytes())
        for fragment in observation["inverse_fragments"]:
            self.assertEqual(before.count(fragment["new"]), 1)
            before = before.replace(fragment["new"], fragment["old"], 1)
        self.assertEqual(hashlib.sha256(before.encode()).hexdigest(), HISTORICAL_HELPER_SHA256)

    def test_ff15_historical_fixture_projection_is_exact_and_cannot_qualify_mutated_current_source(self):
        before = projection.historical_controller_source(CONTROLLER_SOURCE)
        self.assertEqual(hashlib.sha256(before.encode()).hexdigest(), FROZEN_CONTROLLER_SHA256)
        contract = json.loads(CONTROLLER_INVERSE_PATH.read_bytes())
        self.assertEqual(len(contract["inverse_fragments"]), 4)
        for mutation in (
            CONTROLLER_SOURCE.replace("or camera_developer_required:", ":", 1),
            CONTROLLER_SOURCE.replace("developer.capture_before_reporter()", "developer.prepare()", 1),
            CONTROLLER_SOURCE.replace("execution.get(\"stop_reason\")", "False", 1),
            CONTROLLER_SOURCE.replace("developer.close()", "developer.prepare()", 1),
        ):
            self.assertNotEqual(mutation, CONTROLLER_SOURCE)
            error = caught(lambda: projection.historical_controller_source(mutation))
            self.assertIs(type(error), AssertionError)
            self.assertEqual(error.args, ("Full current controller bytes differ from the qualified afterimage",))
            COUNTERS["source_mutation_refusals"] += 1
        self.assertNotEqual(before, CONTROLLER_SOURCE)
        self.assertIn("developer.capture_before_reporter()", CONTROLLER_SOURCE)
        self.assertNotIn("developer.capture_before_reporter()", before)

    def test_ff16_native_sources_plans_workflows_and_read_only_receipt_privacy_stay_exact(self):
        self.assertTrue(UNCHANGED_NATIVE_SOURCE_SHA256)
        for relative, expected in UNCHANGED_NATIVE_SOURCE_SHA256.items():
            self.assertEqual(digest(TREE / relative), expected)
        with fresh_helper() as fixture:
            receipt = fixture.owner.capture_before_reporter()
            rendered = json.dumps(receipt, sort_keys=True)
            self.assertLess(len(rendered), 8192)
            for raw in (fixtures.OLD, fixtures.NAME, str(fixture.root), str(fixture.home),
                        "com.google.android.apps.nexuslauncher/.NexusLauncherActivity", MARKER):
                self.assertNotIn(raw, rendered)
            self.assertEqual(receipt["startup_observations"], 2)
            self.assertEqual(receipt["reporter_compile_preflight_status"], "passed")
            self.assertEqual(receipt["prepare_status"], "running")
            self.assertFalse(receipt["reporter_assembly_recorded_passed"])
            self.assertEqual(receipt["post_reporter_revalidation_attempts"], 0)
            self.assertFalse(receipt["native_acceptance_inferred"])
            self.assertFalse(receipt["reporter_dispatch_attempted"])
            COUNTERS["privacy_checkpoints"] += 1
        self.assertEqual(COUNTERS["native_invocations"], 0)
        self.assertEqual(COUNTERS["existing_accepted_test_methods_selected"], 0)


    def test_ff17_terminal_postreporter_timeout_resets_phase_but_later_master_failure_keeps_completed_phase(self):
        with fresh_helper() as fixture:
            fixture.owner.capture_before_reporter()
            original = fixture.owner.original
            stage_compile(fixture)
            clock, terminal, failures = fixture.owner.clock, [], []
            original_failure = fixture.owner.failure

            def final_boundary_clock():
                if (fixture.owner.post_reporter_deadline is not None and
                        fixture.owner.receipt["post_reporter_revalidation_status"] == "passed"):
                    terminal.append(fixture.owner.post_reporter_deadline)
                    fixture.clock.now = fixture.owner.post_reporter_deadline
                return clock()

            def failure(phase, error):
                failures.append((phase, error))
                return original_failure(phase, error)

            fixture.owner.clock, fixture.owner.failure = final_boundary_clock, failure
            primary = caught(fixture.owner.prepare)
            self.assertIs(type(primary), TimeoutError)
            self.assertEqual(primary.args, ("Post-reporter revalidation exceeded its total one-shot bound",))
            self.assertEqual(len(terminal), 1)
            self.assertEqual(len(failures), 1)
            self.assertEqual(failures[0][0], "prepare")
            self.assertIs(failures[0][1], primary)
            self.assertIs(fixture.owner.original, original)
            self.assert_post_refusal(fixture, primary)
            self.assertEqual(fixture.owner.receipt["prepare_status"], "failed")
            self.assertFalse(fixture.owner.receiver_prepare_attempted)
            self.assertFalse(fixture.owner.receipt["reporter_dispatch_attempted"])
            self.assertEqual(fixture.device.actions, [])
        # A separately attributed failure after genuine phase completion must not
        # erase that phase pass. No master PUT/reboot/restore/native action occurs.
        with fresh_helper(master=helper.Row(False, None)) as fixture:
            fixture.owner.capture_before_reporter()
            original = fixture.owner.original
            stage_compile(fixture)
            fixture.device.denied.add("android.permission.WRITE_SECURE_SETTINGS")
            primary = caught(fixture.owner.prepare)
            self.assertIs(type(primary), ValueError)
            self.assertEqual(primary.args, ("Write permission not granted",))
            self.assertIs(fixture.owner.original, original)
            self.assertEqual(fixture.owner.receipt["post_reporter_revalidation_status"], "passed")
            self.assertEqual(fixture.owner.receipt["post_reporter_revalidation_attempts"], 1)
            self.assertEqual(fixture.owner.receipt["prepare_status"], "failed")
            self.assertEqual(fixture.wait_calls, 1)
            self.assertEqual(fixture.device.actions, [])
            self.assertIsNone(fixture.owner.post_reporter_deadline)
            self.assertIsNone(fixture.owner.post_reporter_last_clock)
            self.assertIsNone(fixture.owner.startup_deadline)
            self.assertIsNone(fixture.owner.startup_last_clock)
            self.assertIsNone(fixture.owner.deadline)
            self.assertFalse(fixture.owner.receiver_prepare_attempted)
            self.assert_no_success(fixture.owner.receipt)

    def test_ff18_generic_discovery_needs_no_private_environment_and_scoped_temp_custody_stays_strict(self):
        # Inert same-source import and generic unittest loader construction only:
        # no selected test body or class setup is run a second time, and no private
        # root or reusable fixture is acquired during discovery/module import.
        source_path = Path(__file__).resolve()
        payload = source_path.read_bytes()
        name = "nativecmpkit_camera_failfast_generic_discovery_no_private_environment"
        probe = types.ModuleType(name)
        probe.__file__, probe.__package__ = str(source_path), None
        with patch.dict(os.environ, {}, clear=True), patch.dict(sys.modules, {name: probe}), \
                patch.object(tempfile, "TemporaryDirectory", side_effect=AssertionError(
                    "Model temporary roots must not be acquired during generic import")):
            exec(compile(payload, str(source_path), "exec"), probe.__dict__)
            suite = unittest.TestLoader().loadTestsFromModule(probe)
            self.assertEqual(suite.countTestCases(), len(DECLARED_METHODS))
            self.assertEqual(tuple(probe.DECLARED_METHODS), DECLARED_METHODS)
            self.assertIsNone(probe.PRIVATE)
            self.assertIsNone(probe.fixtures)
            self.assertIsNone(probe.helper)
            self.assertEqual(probe.COUNTERS["native_invocations"], 0)
            self.assertEqual(probe.COUNTERS["existing_accepted_test_methods_selected"], 0)
        # The ordinary no-environment path creates a fresh secure child; it never
        # reuses tempfile.gettempdir() itself or a source/shared mutable root.
        with probe.private_model_parent() as parent:
            self.assertEqual(stat.S_IMODE(parent.lstat().st_mode), 0o700)
            self.assertEqual(parent.lstat().st_uid, os.getuid())
            self.assertFalse(parent.is_symlink())
            self.assertFalse(parent.is_relative_to(TREE))
            self.assertFalse(TREE.is_relative_to(parent))
            with probe.private_model_parent(str(parent)) as child:
                self.assertNotEqual(child, parent)
                self.assertEqual(child.parent, parent)
                self.assertEqual(stat.S_IMODE(child.lstat().st_mode), 0o700)
            self.assertFalse(child.exists())
            regular, loose, linked = parent / "regular-file", parent / "loose-parent", parent / "linked-parent"
            regular.write_text("synthetic-private-model-custody-only")
            loose.mkdir(mode=0o700)
            loose.chmod(0o755)
            linked.symlink_to(parent, target_is_directory=True)
            for declaration in ("relative-parent", "", str(parent / "missing-parent"), str(regular), str(loose), str(linked)):
                with self.subTest(declaration_type="synthetic-invalid-parent"), self.assertRaises(AssertionError):
                    with probe.private_model_parent(declaration):
                        self.fail("No missing/unowned/symlink/nondirectory parent may be silently substituted")
            with patch.object(os, "getuid", return_value=os.getuid() + 1), self.assertRaises(AssertionError):
                with probe.private_model_parent(str(parent)):
                    self.fail("A foreign-owned private parent is never adopted")
            self.assertEqual(stat.S_IMODE(parent.lstat().st_mode), 0o700)
            self.assertTrue(regular.is_file())
            self.assertEqual(FORBIDDEN_ACTIONS, [])
        self.assertFalse(parent.exists())
        self.assertIsNone(probe.PRIVATE)
        self.assertIsNone(probe.helper)




if {name for name in vars(PreReporterFailFastNewOnlyTests) if name.startswith("test_")} != set(DECLARED_METHODS):
    raise AssertionError("The exact new fail-fast method set changed")
