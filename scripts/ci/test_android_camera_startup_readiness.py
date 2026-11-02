"""Exactly18 new startup-boundary synthetic controls; never native camera acceptance.

Only the test-free ModelFixture is constructed. Accepted test classes/methods,
SDKs, network, processes, native methods and discovery are not selected here.
Every subcase owns a fresh receipt directory: no receipt deletion or model replay.
"""
from __future__ import annotations
import ast
import copy
from contextlib import ExitStack, contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import unittest
from unittest.mock import patch

TREE = Path(os.environ.get("NATIVECMPKIT_CAMERA_STARTUP_MODEL_TREE", Path(__file__).resolve().parents[2])).resolve()
FIXTURE_PATH = TREE / "scripts/ci/test_android_camera_developer_prerequisite.py"
HELPER_PATH = TREE / "scripts/ci/android_camera_developer_prerequisite.py"
GUARD_PATH = TREE / "scripts/ci/test_android_camera_settings_activity_refusal_diagnostics.py"
STARTUP_INVERSE_PATH = TREE / "scripts/ci/fixtures/android-camera-startup-readiness-inverse.json"
OBSERVATION_INVERSE_PATH = TREE / "scripts/ci/fixtures/android-camera-settings-absence-observation-inverse.json"
EXPECTED_INPUT_SHA256 = {'scripts/ci/android_camera_developer_prerequisite.py': '0e47097d10f1886bec0ee8eebc280b29afb704dc47d09df1bbdb41ddaa651b26', 'scripts/ci/test_android_camera_developer_prerequisite.py': '4a78c909420383a59cb453c1ca58ab3c0ca909a08f17201ddc0bcea657a061bb', 'scripts/ci/test_android_camera_settings_activity_refusal_diagnostics.py': '048b40f6976fc6af2160c9934b39d620bbdac466d912edfbb9e315dfa92f8bf7', 'scripts/ci/fixtures/android-camera-startup-readiness-inverse.json': '43a8963e59a7851e968fbbeeaafa19944956cbc6a6f0b5cb8924a4dba0342e2c', 'scripts/ci/fixtures/android-camera-settings-absence-observation-inverse.json': 'e7b0e9a3e361e39d1732ed33cd5e1d4e51a3e30ed377adf487001b742754c953'}
PRE_STARTUP_HELPER_SHA256 = "2d2fb89491d5435963b983052a96f7a9e80e02d9b7ed394c0b3d23cf4b194532"
HISTORICAL_HELPER_SHA256 = "f15163bd0406476d4c8e271aa6fa18c652590c1e1665ee7bb9306ca9140ddfd0"
UNCHANGED_CAMERA_INPUT_SHA256 = {'convention-plugins/src/main/kotlin/Android.kt': '204b7b0bb30e33144794ffda1d993f925f670cac87c809155d81fe9f09f7a256', 'calf-camera-picker/build.gradle.kts': 'f074767f7042ac6e07955b361400e672ae43209f99b17986acd27cf5078428c7', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraRestorationTest.kt': '357c8545e35d5fa529a6b38b064a86c1724ea2b0a2d2b7ec46d5ff4c3671a7d0', 'scripts/ci/android_device_tests.py': 'daac8786b1b034efcad0687a2f3a995c2216ea1a400116f9c592693d5c6395ec'}
DECLARED_METHODS = (
    "test_sr01_readiness_precedes_complete_capture_and_mutations",
    "test_sr02_finite_user_startup_sequence_has_one_budget",
    "test_sr03_exact_fallback_to_same_home_hold_is_read_only",
    "test_sr04_alternating_home_resets_hold_not_total_deadline",
    "test_sr05_only_exact_no_resolver_branch_may_wait",
    "test_sr06_terminal_and_unknown_user_states_refuse_after_pending",
    "test_sr07_current_user_change_or_disagreement_refuses",
    "test_sr08_typed_result_errors_are_not_pending_retries",
    "test_sr09_ready_hold_never_catches_final_star_parser_refusal",
    "test_sr10_ready_hold_never_substitutes_for_positive_activity_absence",
    "test_sr11_original_complete_snapshot_and_pair_refusals_stay_exact",
    "test_sr12_command_sleep_and_clock_temporal_bounds_refuse_late_results",
    "test_sr13_total_budget_includes_final_snapshots_pair_and_postparse",
    "test_sr14_startup_transport_is_never_reboot_transient",
    "test_sr15_ownership_and_runtime_changes_during_hold_refuse",
    "test_sr16_missing_original_close_stays_separate_and_mutation_free",
    "test_sr17_receipts_only_export_fixed_numeric_boolean_facts",
    "test_sr18_full_reversible_source_boundary_and_native_inputs_are_exact",
)
FORBIDDEN_ACTIONS = []
COUNTERS = {"fresh_owned_models": 0, "new_refusal_samples": 0, "privacy_checkpoints": 0,
            "full_source_mutation_refusals": 0, "original_parser_failure_samples": 0,
            "existing_accepted_test_methods_selected": 0, "native_invocations": 0}
CURRENT_USER = ("shell", "am", "get-current-user")
USER_STATE = ("shell", "am", "get-started-user-state", "0")
HOME = ("shell", "cmd", "package", "resolve-activity", "--components", "--query-flags", "0", "--user", "0",
        "-a", "android.intent.action.MAIN", "-c", "android.intent.category.HOME")
ACTIVITIES = ("shell", "dumpsys", "activity", "-p", "com.android.settings", "activities")
BOOT = ("shell", "cat", "/proc/sys/kernel/random/boot_id")
READY_HOME = "com.google.android.apps.nexuslauncher/.NexusLauncherActivity"
SECOND_HOME = "org.example.home/.OtherActivity"


def digest(path):
    # Historical pins remain literal; the outer bridge separately admits raw current bytes.
    from android_external328_source_projection import read_current_source_for_history
    return hashlib.sha256(read_current_source_for_history(path, TREE)).hexdigest()


def forbidden(*args, **kwargs):
    FORBIDDEN_ACTIONS.append("forbidden-sdk-process-network-or-native-action")
    raise AssertionError("No process, SDK, network, native or unstubbed control is admitted")


def action_guards(stack):
    for module, names in ((subprocess, ("Popen", "run", "call", "check_call", "check_output", "getoutput", "getstatusoutput")),
                          (os, ("kill", "killpg", "system", "popen", "fork", "forkpty", "posix_spawn", "posix_spawnp",
                                "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe",
                                "execl", "execle", "execlp", "execlpe", "execv", "execve", "execvp", "execvpe")),
                          (socket, ("socket", "socketpair", "create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex"))):
        for name in names:
            if hasattr(module, name):
                stack.enter_context(patch.object(module, name, forbidden))


for relative, expected in EXPECTED_INPUT_SHA256.items():
    source_path = TREE / relative
    if source_path.is_symlink() or digest(source_path) != expected:
        raise AssertionError("Exact startup source binding is changed")
TRACKED_INPUT_PATHS = tuple(TREE / rel for rel in (*EXPECTED_INPUT_SHA256, *UNCHANGED_CAMERA_INPUT_SHA256,
                                                 "scripts/ci/library_tests.py", ".github/workflows/gradle.yml",
                                                 ".github/workflows/build-native-libs.yml"))
SOURCE_HASHES_BEFORE = {str(path.relative_to(TREE)): digest(path) for path in TRACKED_INPUT_PATHS}
SPEC = importlib.util.spec_from_file_location("nativecmpkit_camera_startup_fixture_only", FIXTURE_PATH)
fixtures = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = fixtures
with ExitStack() as import_guards:
    action_guards(import_guards)
    SPEC.loader.exec_module(fixtures)
helper = fixtures.camera
if (Path(fixtures.__file__).resolve() != FIXTURE_PATH or SPEC.origin != str(FIXTURE_PATH) or
        Path(helper.__file__).resolve() != HELPER_PATH or helper.__spec__.origin != str(HELPER_PATH)):
    raise AssertionError("Private fixture/helper module origin changed")
if any(name.startswith("test_") for name in fixtures.ModelFixture.__dict__):
    raise AssertionError("Only a test-free owning fixture is reusable")


class CameraStartupReadinessNewOnlyTests(unittest.TestCase):
    def setUp(self):
        self.guards = ExitStack()
        self.addCleanup(self.guards.close)
        action_guards(self.guards)
        self.guards.enter_context(patch.object(helper, "bounded_run", forbidden))
        self.guards.enter_context(patch.object(helper, "probe_child", forbidden))
        self.roots = set()

    def tearDown(self):
        self.assertEqual(FORBIDDEN_ACTIONS, [])

    @contextmanager
    def fresh(self, *, master=None, scalar=None, native=False):
        fixture = fixtures.ModelFixture("runTest")
        fixture.setUp()
        try:
            self.assertNotIn(str(fixture.root), self.roots)
            self.roots.add(str(fixture.root))
            fixture.model(master if master is not None else helper.Row(True, "1"), scalar=scalar, native=native)
            COUNTERS["fresh_owned_models"] += 1
            yield fixture
        finally:
            fixture.tearDown()

    def assert_refused(self, fixture, expected=ValueError, *, message=None, before_capture=True):
        # unittest.assertRaises clears traceback on exit; retain the actual
        # primary object/origin for the new ready-then-strict-refusal boundary.
        try:
            fixture.owner.prepare()
        except BaseException as caught:
            error = caught
            self.assertIs(type(error), expected)
        else:
            self.fail("The initial startup boundary unexpectedly admitted this refusing scenario")
        if message is not None:
            self.assertEqual(error.args, (message,))
        self.assertIsNone(fixture.owner.original)
        self.assertIsNone(fixture.owner.startup_deadline)
        self.assertIsNone(fixture.owner.startup_last_clock)
        self.assertIsNone(fixture.owner.deadline)
        self.assertEqual(fixture.owner.receipt["prepare_status"], "failed")
        self.assertEqual(fixture.owner.receipt["startup_readiness_status"], "failed")
        self.assertEqual([fixture.owner.receipt[key] for key in
                          ("master_enable_attempts", "normal_reboot_attempts", "master_restore_attempts")], [0, 0, 0])
        self.assertEqual(fixture.device.actions, [])
        self.assertFalse(fixture.owner.receipt["reporter_dispatch_attempted"])
        self.assertFalse(fixture.owner.receipt["native_acceptance_inferred"])
        if before_capture:
            self.assertEqual([argv for argv in fixture.device.calls if tuple(argv[3:]) == ACTIVITIES], [])
        COUNTERS["new_refusal_samples"] += 1
        return error

    def test_sr01_readiness_precedes_complete_capture_and_mutations(self):
        with self.fresh(master=helper.Row(False, None)) as f:
            snapshots, mutation_captures, homes = [], [], []
            actual_snapshot = f.owner.snapshot
            def observe_snapshot(*, fresh):
                snapshots.append({"fresh": fresh, "original_is_none": f.owner.original is None,
                                  "startup_deadline": f.owner.startup_deadline,
                                  "ready_hold": f.owner.receipt["startup_ready_hold_verified"]})
                return actual_snapshot(fresh=fresh)
            def hook(args, device):
                if args == HOME:
                    homes.append(f.clock.now)
                    self.assertEqual(device.actions, [])
                if args[:6] == ("shell", "settings", "--user", "0", "put", "global"):
                    self.assertIsNotNone(f.owner.original)
                    self.assertIsNone(f.owner.startup_deadline)
                    self.assertIsNone(f.owner.deadline)
                    self.assertEqual(f.owner.receipt["startup_readiness_status"], "passed")
                    mutation_captures.append(len(snapshots))
            f.device.hook = hook
            with patch.object(f.owner, "snapshot", observe_snapshot):
                receipt = f.owner.prepare()
            self.assertEqual(receipt["prepare_status"], "passed")
            self.assertEqual(receipt["startup_observations"], 2)
            self.assertEqual(homes, [0.0, 0.5, 0.5])
            self.assertEqual(snapshots[:2], [{"fresh": True, "original_is_none": True,
                "startup_deadline": 60.0, "ready_hold": True}] * 2)
            self.assertEqual(mutation_captures, [2])
            self.assertEqual(len(snapshots), 4)
            self.assertEqual(f.owner.original.master, helper.Row(False, None))
            self.assertEqual(f.device.actions, [("shell", "settings", "--user", "0", "put", "global", helper.MASTER, "1")])
            self.assertFalse(receipt["reporter_dispatch_attempted"])
            self.assertFalse(receipt["native_acceptance_inferred"])

    def test_sr02_finite_user_startup_sequence_has_one_budget(self):
        with self.fresh() as f:
            replies = ["BOOTING", "RUNNING_LOCKED", "RUNNING_UNLOCKING", "RUNNING_UNLOCKED", "RUNNING_UNLOCKED"]
            seen, deadlines, capture_times, sleeps = [], [], [], []
            def hook(args, device):
                if args == USER_STATE:
                    value = replies.pop(0) if replies else "RUNNING_UNLOCKED"
                    seen.append(value); deadlines.append(f.owner.startup_deadline)
                    return fixtures.cp((value + "\n").encode())
                if args == ACTIVITIES:
                    capture_times.append(f.clock.now)
            def sleeping(duration):
                sleeps.append(duration); f.clock.sleep(duration)
            f.device.hook, f.owner.sleep = hook, sleeping
            receipt = f.owner.prepare()
            self.assertEqual(seen, ["BOOTING", "RUNNING_LOCKED", "RUNNING_UNLOCKING",
                                   "RUNNING_UNLOCKED", "RUNNING_UNLOCKED", "RUNNING_UNLOCKED"])
            self.assertEqual(deadlines, [60.0] * 6)
            self.assertEqual(sleeps, [0.5] * 4)
            self.assertEqual(capture_times, [2.0, 2.0])
            self.assertEqual(receipt["startup_observations"], 5)
            self.assertEqual(receipt["startup_readiness_status"], "passed")
            self.assertEqual(f.device.actions, [])

    def test_sr03_exact_fallback_to_same_home_hold_is_read_only(self):
        with self.fresh() as f:
            homes, deadlines = [], []
            def hook(args, device):
                if args == HOME:
                    home = "com.android.settings/.FallbackHome" if not homes else READY_HOME
                    homes.append(home); deadlines.append(f.owner.startup_deadline)
                    return fixtures.cp((home + "\n").encode())
            f.device.hook = hook
            receipt = f.owner.prepare()
            self.assertEqual(homes, ["com.android.settings/.FallbackHome", READY_HOME, READY_HOME, READY_HOME])
            self.assertEqual(deadlines, [60.0] * 4)
            self.assertEqual(receipt["startup_observations"], 3)
            self.assertEqual(f.clock.now, 1.0)
            self.assertNotIn("startup_home_component_sha256", receipt)
            self.assertEqual(receipt["startup_readiness_status"], "passed")
            self.assertTrue(receipt["startup_ready_hold_verified"])
            self.assertEqual(f.device.actions, [])
            self.assertTrue(receipt["startup_queries_read_only"])

    def test_sr04_alternating_home_resets_hold_not_total_deadline(self):
        with self.fresh() as f:
            homes, deadlines = [], []
            def hook(args, device):
                if args == HOME:
                    home = READY_HOME if len(homes) % 2 == 0 else SECOND_HOME
                    homes.append(home); deadlines.append(f.owner.startup_deadline)
                    return fixtures.cp((home + "\n").encode())
            f.device.hook = hook
            self.assert_refused(f, TimeoutError, message="Initial startup observation exceeded its total bound")
            self.assertEqual(len(homes), 120)
            self.assertEqual(set(deadlines), {60.0})
            self.assertEqual(f.clock.now, 60.0)
            self.assertFalse(f.owner.receipt["startup_ready_hold_verified"])

    def test_sr05_only_exact_no_resolver_branch_may_wait(self):
        with self.fresh() as f:
            homes = []
            def hook(args, device):
                if args == HOME:
                    home = "No activity found" if len(homes) < 2 else READY_HOME
                    homes.append(home)
                    return fixtures.cp((home + "\n").encode())
            f.device.hook = hook
            receipt = f.owner.prepare()
            self.assertEqual(homes, ["No activity found", "No activity found", READY_HOME, READY_HOME, READY_HOME])
            self.assertEqual(receipt["startup_observations"], 4)
            self.assertEqual(f.clock.now, 1.5)
            self.assertEqual(f.device.actions, [])
        for index, malformed in enumerate((b"NO ACTIVITY FOUND\n", b"No activity found \n")):
            with self.subTest(near_miss=index), self.fresh() as f:
                calls = []
                def hook(args, device):
                    if args == HOME:
                        calls.append(args)
                        return fixtures.cp(b"No activity found\n" if len(calls) == 1 else malformed)
                f.device.hook = hook
                self.assert_refused(f, message="Unknown initial startup HOME component shape")
                self.assertEqual(len(calls), 2)
                self.assertEqual(f.clock.now, 0.5)

    def test_sr06_terminal_and_unknown_user_states_refuse_after_pending(self):
        for index, state in enumerate(("STOPPING", "SHUTDOWN", "User is not started: 0", "6", "RUNNING_UNKNOWN", "")):
            with self.subTest(state_case=index), self.fresh() as f:
                states = []
                def hook(args, device):
                    if args == USER_STATE:
                        value = "BOOTING" if not states else state
                        states.append(value)
                        return fixtures.cp((value + "\n").encode())
                f.device.hook = hook
                message = "Unknown initial startup scalar bytes" if state == "" else "Unknown or terminal initial startup user0 state"
                self.assert_refused(f, message=message)
                self.assertEqual(states, ["BOOTING", state])
                self.assertEqual(f.clock.now, 0.5)

    def test_sr07_current_user_change_or_disagreement_refuses(self):
        for pattern in (("10",), ("0", "10"), ("0", "0", "0", "10")):
            with self.subTest(read_count=len(pattern)), self.fresh() as f:
                reads = []
                def hook(args, device):
                    if args == CURRENT_USER:
                        value = pattern[min(len(reads), len(pattern)-1)]
                        reads.append(value)
                        return fixtures.cp((value + "\n").encode())
                f.device.hook = hook
                self.assert_refused(f, message="Current user changed during initial startup")
                self.assertEqual(tuple(reads), pattern)
                self.assertTrue(all(tuple(argv[3:]) == USER_STATE for argv in f.device.calls
                                    if tuple(argv[3:5]) == ("shell", "am") and "get-started-user-state" in argv))
                self.assertTrue(all(tuple(argv[3:]) == HOME for argv in f.device.calls
                                    if tuple(argv[3:7]) == ("shell", "cmd", "package", "resolve-activity")))

    def test_sr08_typed_result_errors_are_not_pending_retries(self):
        samples = (
            (USER_STATE, fixtures.cp(b"RUNNING_UNLOCKED\nextra\n")),
            (USER_STATE, fixtures.cp(b"RUNNING_UNLOCKED\r\n")),
            (USER_STATE, fixtures.cp(b"\xff\n")),
            (USER_STATE, fixtures.cp(b"RUNNING_UNLOCKED\n", code=1)),
            (USER_STATE, fixtures.cp(b"RUNNING_UNLOCKED\n", stderr=b"warning")),
            (HOME, fixtures.cp((READY_HOME + "\n" + READY_HOME + "\n").encode())),
            (HOME, fixtures.cp(b"org.example.home/.Home\x00\n")),
            (HOME, fixtures.cp(b"org.example.home/.Home\x1b\n")),
            (HOME, fixtures.cp(b"x" * 513)),
            (HOME, fixtures.cp("not-binary")),
            (HOME, fixtures.cp((READY_HOME + "\n").encode(), stderr=b"hidden error", code=0)),
            (HOME, fixtures.cp((READY_HOME + "\n").encode(), code=2)),
            (HOME, fixtures.cp(b"com.android.settings/.Settings\n")),
            (HOME, fixtures.cp(b"android/.ResolverActivity\n")),
            (HOME, fixtures.cp(b"org.example.home/org.example.home.Home\n")),
            (HOME, fixtures.cp(b"org.example.home/Home\n")),
        )
        for index, (target, result) in enumerate(samples):
            with self.subTest(sample=index), self.fresh() as f:
                target_calls = []
                def hook(args, device):
                    if args == target:
                        target_calls.append(args)
                        if len(target_calls) == 2:
                            return result
                        return fixtures.cp(b"BOOTING\n" if target == USER_STATE else b"No activity found\n")
                f.device.hook = hook
                self.assert_refused(f)
                self.assertEqual(len(target_calls), 2)
                self.assertEqual(f.clock.now, 0.5)
                self.assertFalse(f.owner.receipt["startup_ready_hold_verified"])

    def test_sr09_ready_hold_never_catches_final_star_parser_refusal(self):
        with self.fresh() as f:
            # Explicit synthetic body; never reconstructs actual original row2.
            f.device.settings_activities = (helper.ACTIVITIES_HEADER +
                "\nDisplay #0 (activities from top to bottom):\n  * Task{synthetic-positive-body}\n  (nothing)\n").encode()
            original_errors, snapshot_starts = [], []
            actual_failure, actual_snapshot = f.owner.failure, f.owner.snapshot
            def failure(phase, error):
                if phase == "prepare": original_errors.append(error)
                return actual_failure(phase, error)
            def snapshot(*, fresh):
                snapshot_starts.append(fresh)
                return actual_snapshot(fresh=fresh)
            with patch.object(f.owner, "failure", failure), patch.object(f.owner, "snapshot", snapshot):
                error = self.assert_refused(f, message="Settings Activity absence traversal is unproved", before_capture=False)
            self.assertEqual(len(original_errors), 1)
            self.assertIs(error, original_errors[0])
            self.assertEqual(snapshot_starts, [True])
            self.assertEqual(sum(tuple(argv[3:]) == ACTIVITIES for argv in f.device.calls), 1)
            self.assertEqual(helper.require_call_origin(error), {"source": HELPER_PATH.name,
                "symbol": "parse_settings_activity_absence", "line": 307})
            node = error.__traceback__
            while node.tb_next is not None:
                node = node.tb_next
            self.assertIs(node.tb_frame.f_code, helper.require.__code__)
            self.assertEqual(node.tb_lineno, 48)
            self.assertTrue(f.owner.receipt["startup_ready_hold_verified"])
            self.assertEqual(f.owner.receipt["errors"][0]["require_call_origin"],
                             helper.require_call_origin(error))
            self.assertEqual(f.owner.receipt["errors"][0]["settings_activity_absence_refusal"]["row_reference_fixed_shape"],
                             "ascii-even-indent-star-space-prefix")
            COUNTERS["original_parser_failure_samples"] += 1

    def test_sr10_ready_hold_never_substitutes_for_positive_activity_absence(self):
        bodies = (
            "  * Task{synthetic-owner}\n    * Hist #0: ActivityRecord{aa u0 com.android.settings/.Settings t1}\n",
            "  Activities waiting to finish:\n    * ActivityRecord{bb u0 com.android.settings/.Settings t2}\n",
        )
        for index, body in enumerate(bodies):
            with self.subTest(queue_kind=index), self.fresh() as f:
                f.device.settings_activities = (helper.ACTIVITIES_HEADER +
                    "\nDisplay #0 (activities from top to bottom):\n" + body + "  (nothing)\n").encode()
                self.assert_refused(f, message="Settings Activity absence traversal is unproved", before_capture=False)
                self.assertEqual(sum(tuple(argv[3:]) == ACTIVITIES for argv in f.device.calls), 1)
                self.assertTrue(f.owner.receipt["startup_ready_hold_verified"])
                self.assertEqual(f.owner.receipt["startup_observations"], 2)
                COUNTERS["original_parser_failure_samples"] += 1

    def test_sr11_original_complete_snapshot_and_pair_refusals_stay_exact(self):
        def changed_master(f): f.device.master = helper.Row(True, "0")
        def changed_scalar(f): f.device.scalar = helper.Row(True, "0")
        def changed_native(f): f.device.native = True
        def changed_kernel(f): f.device.boot = fixtures.NEW
        for index, mutate in enumerate((changed_master, changed_scalar, changed_native, changed_kernel)):
            with self.subTest(field_kind=index), self.fresh() as f:
                completed = []
                actual = f.owner.snapshot
                def snapshot(*, fresh):
                    value = actual(fresh=fresh)
                    completed.append(value)
                    if len(completed) == 1:
                        mutate(f)
                    return value
                with patch.object(f.owner, "snapshot", snapshot):
                    self.assert_refused(f, message="State/boot changed across complete snapshots", before_capture=False)
                self.assertEqual(len(completed), 2)
                self.assertNotEqual(completed[0], completed[1])
                self.assertEqual(sum(tuple(argv[3:]) == ACTIVITIES for argv in f.device.calls), 2)
        with self.fresh(scalar=helper.Row(True, "1"), native=False) as f:
            self.assert_refused(f, message="Original native/scalar pair is inconsistent", before_capture=False)
            self.assertEqual(sum(tuple(argv[3:]) == ACTIVITIES for argv in f.device.calls), 2)
            self.assertEqual(sum(tuple(argv[3:]) == HOME for argv in f.device.calls), 2)

    def test_sr12_command_sleep_and_clock_temporal_bounds_refuse_late_results(self):
        with self.fresh() as f:
            active_timeouts = []
            actual_runner = f.owner.runner
            def runner(argv, **kwargs):
                if f.owner.startup_deadline is not None:
                    active_timeouts.append(kwargs["timeout"])
                    self.assertLessEqual(kwargs["timeout"], 10.0)
                    self.assertGreater(kwargs["timeout"], 0.0)
                return actual_runner(argv, **kwargs)
            def hook(args, device):
                if args == HOME:
                    f.clock.now += 10.01
                    return fixtures.cp((READY_HOME + "\n").encode())
            f.owner.runner, f.device.hook = runner, hook
            self.assert_refused(f, TimeoutError, message="Initial startup command exceeded its clamped bound")
            self.assertTrue(active_timeouts)
            self.assertEqual(f.clock.now, 10.01)
        with self.fresh() as f:
            late_timeout = []
            actual_runner = f.owner.runner
            def runner(argv, **kwargs):
                if f.owner.startup_deadline is not None and tuple(argv[3:]) == USER_STATE and f.clock.now == 59.5:
                    late_timeout.append(kwargs["timeout"])
                return actual_runner(argv, **kwargs)
            def hook(args, device):
                if args == USER_STATE:
                    if f.clock.now == 59.5:
                        f.clock.now += 0.5
                        return fixtures.cp(b"RUNNING_UNLOCKED\n")
                    return fixtures.cp(b"BOOTING\n")
            f.owner.runner, f.device.hook = runner, hook
            self.assert_refused(f, TimeoutError, message="Initial startup observation exceeded its total bound")
            self.assertEqual(late_timeout, [0.5])
            self.assertEqual(f.clock.now, 60.0)
        for elapsed, expected, message in ((0.0, ValueError, "Initial startup sleep returned before its requested hold"),
                                           (1.01, TimeoutError, "Initial startup sleep exceeded its clamped completion bound")):
            with self.subTest(sleep_policy=elapsed), self.fresh() as f:
                f.owner.sleep = lambda duration: setattr(f.clock, "now", f.clock.now + elapsed)
                self.assert_refused(f, expected, message=message)
                self.assertEqual(f.clock.now, elapsed)
        # A slower scheduling return is admitted below the separate finite1s cap;
        # it is not falsely required to return at the exact0.5s source cadence.
        with self.fresh() as f:
            f.owner.sleep = lambda duration: setattr(f.clock, "now", f.clock.now + 0.8)
            self.assertEqual(f.owner.prepare()["startup_readiness_status"], "passed")
            self.assertEqual(f.clock.now, 0.8)
            self.assertEqual(f.device.actions, [])
        for index, value in enumerate((float("nan"), float("inf"), -1.0, True)):
            with self.subTest(clock_case=index), self.fresh() as f:
                def hook(args, device):
                    if args == USER_STATE:
                        f.clock.now = value
                        return fixtures.cp(b"RUNNING_UNLOCKED\n")
                f.device.hook = hook
                self.assert_refused(f, message="Initial startup clock is non-finite or moved backwards")

    def test_sr13_total_budget_includes_final_snapshots_pair_and_postparse(self):
        for phase in ("second-snapshot-command", "final-stable", "pair-admission", "post-typed-read", "fixed-status-update"):
            with self.subTest(expiry_phase=phase), self.fresh() as f:
                class ExpiringReceipt(dict):
                    def __setitem__(self, key, value):
                        super().__setitem__(key, value)
                        if phase == "fixed-status-update" and key == "startup_readiness_status" and value == "passed":
                            f.clock.now = 60.0
                f.owner.receipt = ExpiringReceipt(f.owner.receipt)
                actual_stable, actual_pair, actual_observation = f.owner.stable, helper.pair_admitted, f.owner.startup_observation
                typed_calls, activity_reads = [], []
                def hook(args, device):
                    if args == ACTIVITIES:
                        activity_reads.append(args)
                        if phase == "second-snapshot-command" and len(activity_reads) == 2:
                            f.clock.now = 60.0
                            return fixtures.cp(device.settings_activities)
                f.device.hook = hook
                def stable(*, fresh):
                    value = actual_stable(fresh=fresh)
                    if phase == "final-stable" and f.owner.original is None:
                        f.clock.now = 60.0
                    return value
                def pair(value):
                    admitted = actual_pair(value)
                    if phase == "pair-admission":
                        f.clock.now = 60.0
                    return admitted
                def observation(expected_boot):
                    value = actual_observation(expected_boot)
                    typed_calls.append(value)
                    if phase == "post-typed-read" and len(typed_calls) == 3:
                        f.clock.now = 60.0
                    return value
                with patch.object(f.owner, "stable", stable), patch.object(helper, "pair_admitted", pair), \
                        patch.object(f.owner, "startup_observation", observation):
                    self.assert_refused(f, TimeoutError, message="Initial startup observation exceeded its total bound", before_capture=False)
                self.assertEqual(sum(tuple(argv[3:]) == ACTIVITIES for argv in f.device.calls), 2)
                self.assertEqual(f.clock.now, 60.0)
                self.assertTrue(f.owner.receipt["startup_ready_hold_verified"])

    def test_sr14_startup_transport_is_never_reboot_transient(self):
        for mode in ("offline-table", "absent-table", "offline-boot", "not-found-boot"):
            with self.subTest(transport_kind=mode), self.fresh() as f:
                boot_transient = []
                actual_control = f.owner.control
                def control(*args, **kwargs):
                    if args == BOOT:
                        boot_transient.append(kwargs.get("transient", False))
                        self.assertIsNone(f.owner.deadline)
                    return actual_control(*args, **kwargs)
                actual_runner = f.owner.runner
                def runner(argv, **kwargs):
                    if argv[1:] == ["devices"] and f.clock.now >= 0.5:
                        if mode == "offline-table":
                            return fixtures.cp(("List of devices attached\n" + helper.SERIAL + "\toffline\n").encode())
                        if mode == "absent-table":
                            return fixtures.cp(b"List of devices attached\n")
                    return actual_runner(argv, **kwargs)
                def hook(args, device):
                    if args == USER_STATE:
                        return fixtures.cp(b"BOOTING\n")
                    if args == BOOT and f.clock.now >= 0.5:
                        stderr = b"error: device offline\n" if mode == "offline-boot" else b"error: device 'emulator-5588' not found\n"
                        if mode in ("offline-boot", "not-found-boot"):
                            return fixtures.cp(b"", stderr=stderr, code=1)
                f.owner.runner, f.device.hook = runner, hook
                with patch.object(f.owner, "control", control):
                    error = self.assert_refused(f)
                self.assertNotIsInstance(error, helper.Unavailable)
                self.assertTrue(boot_transient)
                self.assertEqual(set(boot_transient), {False})

    def test_sr15_ownership_and_runtime_changes_during_hold_refuse(self):
        cases = ("guest-live", "foreign-serial", "AVD", "UID", "kernel", "API", "ABI", "boot-completed", "SELinux")
        for mode in cases:
            with self.subTest(identity_kind=mode), self.fresh() as f:
                def sleep(duration):
                    f.clock.sleep(duration)
                    if mode == "guest-live": f.guest.live = False
                    if mode == "foreign-serial": f.device.foreign_table = True
                    if mode == "UID": f.device.shell_uid = b"0"
                    if mode == "kernel": f.device.boot = fixtures.NEW
                def hook(args, device):
                    if f.clock.now < 0.5:
                        return None
                    if mode == "AVD" and args == ("emu", "avd", "name"):
                        return fixtures.cp(b"nativecmpkit-api35-foreign\nOK\n")
                    properties = {"API": ("ro.build.version.sdk", b"36\n"),
                                  "ABI": ("ro.product.cpu.abi", b"arm64-v8a\n"),
                                  "boot-completed": ("sys.boot_completed", b"0\n")}
                    if mode in properties and args == ("shell", "getprop", properties[mode][0]):
                        return fixtures.cp(properties[mode][1])
                    if mode == "SELinux" and args == ("shell", "getenforce"):
                        return fixtures.cp(b"Permissive\n")
                f.owner.sleep, f.device.hook = sleep, hook
                self.assert_refused(f)
                self.assertEqual(f.clock.now, 0.5)
        # The late UID change occurs inside typed reads, so the new end-bracket
        # must refuse in the same observation, before any hold/capture succeeds.
        with self.fresh() as f:
            def hook(args, device):
                if args == HOME:
                    device.shell_uid = b"0"
                    return fixtures.cp((READY_HOME + "\n").encode())
            f.device.hook = hook
            self.assert_refused(f, message="Unknown scalar control shape")
            self.assertEqual(f.clock.now, 0.0)

    def test_sr16_missing_original_close_stays_separate_and_mutation_free(self):
        with self.fresh() as f:
            f.device.hook = lambda args, device: fixtures.cp(b"SHUTDOWN\n") if args == USER_STATE else None
            prepare_error = self.assert_refused(f, message="Unknown or terminal initial startup user0 state")
            cleanup_errors = []
            actual_failure = f.owner.failure
            def failure(phase, error):
                if phase == "cleanup": cleanup_errors.append(error)
                return actual_failure(phase, error)
            with patch.object(f.owner, "failure", failure):
                receipt = f.close_model()
            self.assertEqual(len(cleanup_errors), 1)
            self.assertIs(type(cleanup_errors[0]), ValueError)
            self.assertEqual(cleanup_errors[0].args, ("Original exact state was not acquired",))
            self.assertEqual(receipt["cleanup_status"], "failed")
            self.assertEqual(receipt["prepare_status"], "failed")
            self.assertEqual(receipt["startup_readiness_status"], "failed")
            self.assertEqual([row["phase"] for row in receipt["errors"]], ["prepare", "cleanup"])
            self.assertEqual([row["class"] for row in receipt["errors"]], ["ValueError", "ValueError"])
            self.assertEqual(receipt["errors"][1]["require_call_origin"]["symbol"], "close")
            self.assertEqual([receipt[key] for key in ("master_enable_attempts", "normal_reboot_attempts", "master_restore_attempts")], [0, 0, 0])
            self.assertIsNone(f.owner.original)
            self.assertIsNone(f.owner.startup_deadline)
            self.assertIsNone(f.owner.deadline)
            self.assertEqual(f.device.actions, [])
            calls_before = tuple(f.device.calls)
            self.assertEqual(f.owner.close(), receipt)
            self.assertEqual(tuple(f.device.calls), calls_before)
            self.assertEqual(prepare_error.args, ("Unknown or terminal initial startup user0 state",))

    def test_sr17_receipts_only_export_fixed_numeric_boolean_facts(self):
        with self.fresh() as f:
            raw_home = "org.example.privatehome/.OwnerSpecificActivity$Inner"
            f.device.hook = lambda args, device: fixtures.cp((raw_home + "\n").encode()) if args == HOME else None
            checkpoints = []
            actual_write = f.owner.journal.write
            def write(receipt):
                checkpoints.append(copy.deepcopy(receipt))
                return actual_write(receipt)
            with patch.object(f.owner.journal, "write", write):
                receipt = f.owner.prepare()
            expected_startup_keys = {"startup_readiness_status", "startup_observations", "startup_ready_hold_verified",
                "startup_queries_read_only", "startup_total_budget_seconds", "startup_ready_hold_seconds",
                "startup_sleep_completion_bound_seconds"}
            self.assertEqual({key for key in receipt if key.startswith("startup_")}, expected_startup_keys)
            self.assertNotIn("startup_home_component_sha256", receipt)
            self.assertEqual(receipt["original_boot_id_sha256"], hashlib.sha256(fixtures.OLD.encode()).hexdigest())
            self.assertEqual((receipt["startup_total_budget_seconds"], receipt["startup_ready_hold_seconds"],
                              receipt["startup_sleep_completion_bound_seconds"]), (60.0, 0.5, 1.0))
            for checkpoint in checkpoints + [json.loads((f.output / "camera-developer-prerequisite.json").read_bytes())]:
                encoded = json.dumps(checkpoint, sort_keys=True)
                for value in (raw_home, "org.example.privatehome", hashlib.sha256(raw_home.encode()).hexdigest(), fixtures.OLD, fixtures.NAME,
                              str(f.root), str(f.home), str(f.guest.environment)):
                    self.assertNotIn(value, encoded)
                self.assertFalse(checkpoint["raw_boot_ids_dumps_paths_or_environment_exported"])
                self.assertFalse(checkpoint["native_acceptance_inferred"])
                self.assertFalse(checkpoint["reporter_dispatch_attempted"])
                self.assertIn(checkpoint["startup_readiness_status"], ("not-started", "running", "passed"))
                self.assertIs(type(checkpoint["startup_observations"]), int)
                for name in ("startup_queries_read_only", "startup_ready_hold_verified"):
                    self.assertIs(type(checkpoint[name]), bool)
                COUNTERS["privacy_checkpoints"] += 1
            self.assertEqual(f.device.actions, [])

    def test_sr18_full_reversible_source_boundary_and_native_inputs_are_exact(self):
        source = HELPER_PATH.read_text()
        guard = ast.parse(GUARD_PATH.read_text())
        names = ("pre_startup_helper_source", "historical_helper_source")
        functions = [next(node for node in guard.body if isinstance(node, ast.FunctionDef) and node.name == name) for name in names]
        pins = {name: next(node for node in guard.body if isinstance(node, ast.Assign) and
                           any(isinstance(target, ast.Name) and target.id == name for target in node.targets))
                for name in ("STARTUP_INVERSE_SHA256", "OBSERVATION_INVERSE_SHA256")}
        namespace = {"Path": Path, "hashlib": hashlib, "json": json, "__file__": str(GUARD_PATH),
                     **{name: ast.literal_eval(node.value) for name, node in pins.items()}}
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(GUARD_PATH), "exec"), namespace)
        normalize, historical = (namespace[name] for name in names)
        before = normalize(source)
        self.assertEqual(hashlib.sha256(before.encode()).hexdigest(), PRE_STARTUP_HELPER_SHA256)
        self.assertEqual(hashlib.sha256(historical(source).encode()).hexdigest(), HISTORICAL_HELPER_SHA256)
        startup = json.loads(STARTUP_INVERSE_PATH.read_bytes())
        observation = json.loads(OBSERVATION_INVERSE_PATH.read_bytes())
        self.assertEqual(len(startup["inverse_fragments"]), 17)
        self.assertEqual(len(observation["inverse_fragments"]), 4)
        self.assertEqual(startup["before_sha256"], observation["after_sha256"])
        self.assertEqual(before.index("\n\n\ndef record_settings_activity_absence_refusal("), 62558)
        self.assertEqual(before.splitlines()[47], "        raise ValueError(message)")
        self.assertEqual(before.splitlines()[297], '            require(display is not None, "Settings Activity absence traversal is unproved")')
        mutations = (
            source.replace("self.startup_deadline, self.startup_last_clock = None, None", "self.deadline, self.startup_last_clock = None, None", 1),
            source.replace("raise ValueError(message)", "return", 1),
            source.replace("State/boot changed across complete snapshots", "accepted-without-complete-snapshots", 1),
            source.replace("Original exact state was not acquired", "missing-original-is-accepted", 1),
            source.replace("parse_settings_activity_absence(self.control", "parse_recents(self.control", 1),
        )
        for mutation in mutations:
            self.assertNotEqual(mutation, source)
            with self.assertRaisesRegex(AssertionError, "Full current helper bytes differ from the qualified afterimage"):
                historical(mutation)
            COUNTERS["full_source_mutation_refusals"] += 1
        for pin, message in (("STARTUP_INVERSE_SHA256", "Exact owning startup-inverse fixture is changed"),
                             ("OBSERVATION_INVERSE_SHA256", "Exact owning observation-inverse fixture is changed")):
            saved = namespace[pin]
            try:
                namespace[pin] = "0" * 64
                with self.assertRaisesRegex(AssertionError, message):
                    historical(source)
                COUNTERS["full_source_mutation_refusals"] += 1
            finally:
                namespace[pin] = saved
        for relative, expected in UNCHANGED_CAMERA_INPUT_SHA256.items():
            self.assertEqual(digest(TREE / relative), expected)
        self.assertEqual({str(path.relative_to(TREE)): digest(path) for path in TRACKED_INPUT_PATHS}, SOURCE_HASHES_BEFORE)
        self.assertEqual(COUNTERS["existing_accepted_test_methods_selected"], 0)
        self.assertEqual(COUNTERS["native_invocations"], 0)
