"""Owning models only: no SDK, Android, Gradle, Git or accepted-suite execution."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import types
from unittest.mock import patch
from pathlib import Path
import unittest

TREE = Path(os.environ.get("CAMERA_PREREQUISITE_MODEL_TREE", Path(__file__).resolve().parents[2]))


class SourceWiring(unittest.TestCase):
    def setUp(self):
        self.source = (TREE / "scripts/ci/android_device_tests.py").read_text()

    def test_prepare_acquired_after_boot_before_any_apk_install(self):
        self.assertIn("camera_developer.is_required(api_level, only_modules, focus)", self.source)
        boot = self.source.index('lt.write_json(output / "boot.json", identity)')
        acquire = self.source.index("developer = camera_developer.OwnedDeveloperPrerequisite")
        prepare = self.source.index('result["camera_developer_prerequisite"] = developer.prepare()')
        receiver = self.source.index("camera_receiver = android_camera_receiver.OwnedCameraReceiver")
        dispatch = self.source.index("developer.mark_reporter_dispatch()")
        native = self.source.index('receipt = lt.run(root, "android-device"')
        self.assertLess(boot, acquire)
        self.assertLess(acquire, prepare)
        self.assertLess(prepare, receiver)
        self.assertLess(receiver, dispatch)
        self.assertLess(dispatch, native)

    def test_prerequisite_cleanup_after_recipient_before_engine_shutdown(self):
        receiver_close = self.source.index('result["camera_receiver"] = camera_receiver.close()')
        close = self.source.index('result["camera_developer_prerequisite"] = developer.close()')
        stop = self.source.index('result["emulator_shutdown"] = stop_owned_emulator')
        self.assertLess(receiver_close, close)
        self.assertLess(close, stop)
        self.assertIn('dict(developer.receipt)', self.source)

    def test_partial_fresh_roots_disposed_and_required_by_pass_gate(self):
        setup = self.source.index('    try:\n        if camera_developer_required:')
        owner = self.source.index("guest = camera_developer.OwnedFreshGuest")
        create = self.source.index("guest.create()")
        self.assertLess(setup, owner)
        self.assertLess(owner, create)
        self.assertIn('result["camera_guest_disposal"] = guest.dispose(', self.source)
        self.assertIn('camera_developer.accepted(', self.source)
        self.assertIn('result.get("camera_guest_disposal", {})', self.source)


SPEC = importlib.util.spec_from_file_location("camera_prerequisite_under_test", Path(__file__).with_name("android_camera_developer_prerequisite.py"))
camera = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = camera
SPEC.loader.exec_module(camera)
PRIVATE = Path(os.environ.get("CAMERA_PREREQUISITE_MODEL_TMP", tempfile.gettempdir()))
PRIVATE.mkdir(mode=0o700, exist_ok=True)
OLD = "11111111-1111-4111-8111-111111111111"
NEW = "22222222-2222-4222-8222-222222222222"
NAME = "nativecmpkit-api35-aabbccddeeff"


def cp(stdout=b"", *, stderr=b"", code=0):
    return subprocess.CompletedProcess(["modeled-control"], code, stdout, stderr)


def native_payload(enabled=False, settings=False):
    rows = [camera.PROCESS_HEADER]
    if settings:
        rows.append("  *APP* ProcessRecord{aa 321:com.android.settings/1000}")
        rows.append("    packageList={com.android.settings}")
    if enabled:
        rows.append("  mAlwaysFinishActivities=true")
    rows.extend([camera.READINESS, "  mForceBackgroundCheck=false"])
    return ("\n".join(rows) + "\n").encode()


ACTIVITIES = (camera.ACTIVITIES_HEADER + "\nDisplay #0 (activities from top to bottom):\n  (nothing)\n").encode()
RECENTS = (camera.RECENTS_HEADER + "\nmRecentsUid=1000\nmRecentsComponent=ComponentInfo{com.android.launcher3/.QuickstepService}\n"
           "mFreezeTaskListReordering=false\nmFreezeTaskListReorderingPendingTimeout=false\n  (nothing)\n").encode()
LIVE = ("RootTask id=1 bounds=[0,0][1080,2400] displayId=0 userId=0\n configuration={modeled-complete-config}\n"
        "  taskId=2: com.google.android.apps.nexuslauncher bounds=[0,0][1080,2400] userId=0 visible=true "
        "topActivity=ComponentInfo{com.google.android.apps.nexuslauncher/.NexusLauncherActivity}\n").encode()
MANIFEST = ('<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="' + camera.REPORTER + '">'
            '<application/><instrumentation android:name="androidx.test.runner.AndroidJUnitRunner" android:targetPackage="' +
            camera.REPORTER + '"/></manifest>').encode()


class RouteAdmission(unittest.TestCase):
    def test_exact_existing_route_only(self):
        self.assertTrue(camera.is_required(35, (camera.MODULE,), camera.FOCUS))

    def test_other_routes_are_true_no_op(self):
        for focus in (None, "android-camera-real-restoration", "android-camera-provider", "android-io-default-decode"):
            self.assertFalse(camera.is_required(35, None, focus))

    def test_wrong_api_refused(self):
        for api in (23, 34, 36, True, "35", 35.0):
            with self.subTest(api=api), self.assertRaises(ValueError):
                camera.is_required(api, (camera.MODULE,), camera.FOCUS)

    def test_wrong_module_or_type_refused(self):
        for modules in (None, (), [camera.MODULE], (camera.MODULE, "calf-io"), ("calf-io",)):
            with self.subTest(modules=modules), self.assertRaises(ValueError):
                camera.is_required(35, modules, camera.FOCUS)


class StrictParsers(unittest.TestCase):
    def test_exact_absence_and_present_values(self):
        for key in (camera.MASTER, camera.SCALAR):
            self.assertEqual(camera.parse_row(cp(b"null\n"), cp(b"No result found.\n"), key), camera.Row(False, None))
            for value in ("0", "1"):
                self.assertEqual(camera.parse_row(cp(value.encode()), cp(("Row: 0 name=" + key + ", value=" + value).encode()), key),
                                 camera.Row(True, value))

    def test_null_not_an_absent_row_proof(self):
        for query in (b"", b"Row: 0 name=development_settings_enabled, value=NULL", b"Row: 0 name=development_settings_enabled, value=null",
                      b"No result found.\nNo result found.", b"Error while accessing provider", b"Row: 0 name=other, value=0"):
            with self.subTest(query=query), self.assertRaises(ValueError):
                camera.parse_row(cp(b"null"), cp(query), camera.MASTER)

    def test_getter_row_disagreement_and_hidden_errors_refused(self):
        for getter, query in ((cp(b"0"), cp(b"No result found.")), (cp(b"1"), cp(b"Row: 0 name=development_settings_enabled, value=0")),
                              (cp(b"null", stderr=b"warning"), cp(b"No result found.")), (cp(b"null"), cp(b"No result found.", code=1))):
            with self.assertRaises(ValueError):
                camera.parse_row(getter, query, camera.MASTER)

    def test_native_true_and_complete_false(self):
        self.assertEqual(camera.parse_native(cp(native_payload())), (False, False))
        self.assertEqual(camera.parse_native(cp(native_payload(True))), (True, False))
        self.assertEqual(camera.parse_native(cp(native_payload(settings=True))), (False, True))

    def test_native_partial_omission_never_false(self):
        good = native_payload()
        for payload in (b"", b"mAlwaysFinishActivities=false", good.replace(camera.PROCESS_HEADER.encode(), b"OTHER"),
                        good.replace(camera.READINESS.encode(), b"  mProcessesReady=false mSystemReady=true mBooted=true mFactoryTest=0"),
                        good.replace(b"  mForceBackgroundCheck=false", b""), good + b"extra\n", good.replace(b"\n", b"\r\n"),
                        good + b"\0", good + b"\x1b", native_payload(True).replace(b"true\n", b"false\n", 1),
                        good.replace(camera.READINESS.encode(), b"  mAlwaysFinishActivities=true\n" + camera.READINESS.encode() + b"\n  mAlwaysFinishActivities=true")):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                camera.parse_native(cp(payload))

    def test_full_task_absence_only(self):
        camera.parse_recents(cp(RECENTS))
        camera.parse_live_tasks(cp(LIVE))
        for payload in (b"", RECENTS.replace(b"mRecentsUid=1000\n", b""), RECENTS + b"  Recent tasks:\n", RECENTS + b"Error\n"):
            with self.assertRaises(ValueError):
                camera.parse_recents(cp(payload))
        for payload in (b"", LIVE.replace(b" configuration={modeled-complete-config}\n", b""), LIVE.replace(b"com.google.android.apps.nexuslauncher", b"unknown", 1),
                        LIVE.replace(b"com.google.android.apps.nexuslauncher", b"com.android.settings"), LIVE + b"unknown leaf\n"):
            with self.assertRaises(ValueError):
                camera.parse_live_tasks(cp(payload))

    def test_permissions_exact_native_service_scalar(self):
        self.assertTrue(camera.permission(cp(b"0\n")))
        self.assertFalse(camera.permission(cp(b"-1\r\n")))
        for result in (cp(b"granted"), cp(b"0\n0\n"), cp(b"0", stderr=b"error"), cp(b"0", code=1), cp(b"1"), cp(b"")):
            with self.assertRaises(ValueError):
                camera.permission(result)

    def test_package_observation_exact_and_bounded(self):
        self.assertIsNone(camera.parse_installed_path(cp()))
        path = "/data/app/~~owned/reporter-token/base.apk"
        self.assertEqual(camera.parse_installed_path(cp(("package:" + path + "\n").encode())), path)
        for result in (cp(b"package:/system/app/foo.apk"), cp(b"package:/data/app/a/../base.apk"), cp(b"package:/data/app/a/base.apk\npackage:/data/app/b/base.apk"),
                       cp(b"", stderr=b"Error"), cp(b"", code=2), cp(b"x" * 65537)):
            with self.assertRaises(ValueError):
                camera.parse_installed_path(result)


class ModelClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, duration):
        self.now += duration


class FakeGuest:
    def __init__(self, root, output):
        self.root, self.output, self.name, self.closed, self.live = root, output, NAME, False, True
        self.environment = {"ANDROID_SERIAL": camera.SERIAL, "ANDROID_AVD_HOME": str(output / "avd"),
                            "ANDROID_EMULATOR_HOME": str(output / "avd"), "ANDROID_USER_HOME": str(output / "android-user")}
        self.fd = os.open(output, os.O_RDONLY | os.O_DIRECTORY)

    def verify_live(self):
        camera.require(self.live, "Modeled same Popen/AVD ownership lost")
        return True

    def finish(self):
        os.close(self.fd)
        self.closed = True


class DeviceModel:
    def __init__(self, guest, original, scalar=None, native=False):
        self.guest, self.master = guest, original
        self.scalar = scalar if scalar is not None else camera.Row(False, None)
        self.native, self.boot = native, OLD
        self.calls, self.actions = [], []
        self.denied, self.shell_uid, self.foreign_table = set(), b"2000", False
        self.present = {camera.REPORTER: False, camera.RECEIVER: False}
        self.path = "/data/app/~~owned/reporter-token/base.apk"
        self.apk_digest, self.installed_digest = None, None
        self.manifest, self.settings_process, self.recent_tasks, self.live_tasks = MANIFEST, False, RECENTS, LIVE
        self.settings_activities, self.new_settings_activities = ACTIVITIES, ACTIVITIES
        self.enable_timeout, self.enable_effect, self.enable_stdout = False, True, b""
        self.reboot_timeout, self.reboot_effect, self.new_settings_process = False, True, False
        self.new_master, self.new_scalar, self.new_native = None, None, None
        self.restore_timeout, self.restore_effect, self.delete_reply = False, True, b"Deleted 1 rows\n"
        self.uninstall_timeout, self.uninstall_effect = False, True
        self.hook = None

    def row(self, key):
        return self.master if key == camera.MASTER else self.scalar

    def runner(self, argv, *, cwd, timeout, limit, environment):
        self.calls.append(tuple(argv))
        camera.require(0 < timeout <= 120 and 0 < limit <= camera.DUMP_BYTES, "Model received unbounded control")
        camera.require(environment == self.guest.environment, "Model private environment mismatch")
        if Path(argv[0]).name == "apkanalyzer":
            return cp(self.manifest)
        if argv[1:] == ["devices"]:
            return cp(b"List of devices attached\nforeign-123\tdevice\n" if self.foreign_table else
                      ("List of devices attached\n" + camera.SERIAL + "\tdevice\n\n").encode())
        camera.require(argv[1:3] == ["-s", camera.SERIAL], "No arbitrary/personal serial")
        args = tuple(argv[3:])
        if self.hook is not None:
            result = self.hook(args, self)
            if result is not None:
                return result
        if args == ("shell", "id", "-u"):
            return cp(self.shell_uid + b"\n")
        if args[:4] == ("shell", "dumpsys", "package", "check-permission"):
            return cp(b"-1\n" if args[4] in self.denied else b"0\n")
        if args[:2] == ("shell", "getprop"):
            return cp({"sys.boot_completed": b"1\n", "ro.build.version.sdk": b"35\n", "ro.product.cpu.abi": b"x86_64\n"}[args[2]])
        if args == ("shell", "getenforce"):
            return cp(b"Enforcing\n")
        if args == ("shell", "cat", "/proc/sys/kernel/random/boot_id"):
            return cp((self.boot + "\n").encode())
        if args == ("emu", "avd", "name"):
            return cp((self.guest.name + "\nOK\n").encode())
        if args[:3] == ("shell", "pm", "path"):
            return cp(("package:" + self.path + "\n").encode() if self.present[args[3]] else b"")
        if args[:4] == ("shell", "pm", "list", "packages"):
            package = args[-1]
            return cp(("package:" + package + " uid:10123\n").encode() if self.present[package] else b"")
        if args[:2] == ("shell", "sha256sum"):
            return cp(((self.installed_digest or self.apk_digest) + "  " + self.path + "\n").encode())
        if args[:6] == ("shell", "settings", "--user", "0", "get", "global"):
            row = self.row(args[6])
            return cp(((row.value if row.present else "null") + "\n").encode())
        if args[:3] == ("shell", "content", "query"):
            key = args[6].rsplit("/", 1)[1]
            row = self.row(key)
            return cp(("Row: 0 name=" + key + ", value=" + row.value + "\n").encode() if row.present else b"No result found.\n")
        if args == ("shell", "dumpsys", "activity", "processes"):
            return cp(native_payload(self.native, self.settings_process))
        if args == ("shell", "dumpsys", "activity", "-p", "com.android.settings", "activities"):
            return cp(self.settings_activities)
        if args == ("shell", "dumpsys", "activity", "-p", "com.android.settings", "recents"):
            return cp(self.recent_tasks)
        if args == ("shell", "am", "stack", "list"):
            return cp(self.live_tasks)
        if args[:6] == ("shell", "settings", "--user", "0", "put", "global"):
            camera.require(args[6] == camera.MASTER, "Controller must never write always-finish")
            self.actions.append(args)
            if args[7] == "1":
                if self.enable_effect:
                    self.master = camera.Row(True, "1")
                if self.enable_timeout:
                    raise TimeoutError("Modeled uncertain enable; raw body never exported")
                return cp(self.enable_stdout)
            if self.restore_effect:
                self.master = camera.Row(True, "0")
            if self.restore_timeout:
                raise TimeoutError("Modeled uncertain restore")
            return cp()
        if args[:6] == ("shell", "settings", "--user", "0", "delete", "global"):
            camera.require(args[6] == camera.MASTER, "No native/scalar compensation")
            self.actions.append(args)
            if self.restore_effect:
                self.master = camera.Row(False, None)
            if self.restore_timeout:
                raise TimeoutError("Modeled uncertain delete")
            return cp(self.delete_reply)
        if args == ("uninstall", camera.REPORTER):
            self.actions.append(args)
            if self.uninstall_effect:
                self.present[camera.REPORTER] = False
            if self.uninstall_timeout:
                raise TimeoutError("Modeled uncertain uninstall")
            return cp(b"Success\n")
        if args == ("reboot",):
            self.actions.append(args)
            if self.reboot_effect:
                self.boot = NEW
                self.settings_process = self.new_settings_process
                self.settings_activities = self.new_settings_activities
                self.master = self.new_master if self.new_master is not None else self.master
                self.scalar = self.new_scalar if self.new_scalar is not None else self.scalar
                self.native = self.new_native if self.new_native is not None else self.scalar == camera.Row(True, "1")
            if self.reboot_timeout:
                raise TimeoutError("Modeled uncertain reboot")
            return cp()
        raise AssertionError("Unmodeled control: " + repr(args))


class ModelFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="case-", dir=PRIVATE)
        self.root = Path(self.temp.name)
        self.output = self.root / "build/ci-verification/fresh-case"
        self.output.mkdir(mode=0o700, parents=True)
        for relative in (camera.CONVENTION, camera.MODULE + "/build.gradle.kts"):
            destination = self.root / relative
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            shutil.copyfile(TREE / relative, destination)
        self.base = self.root / camera.MODULE / "build/outputs/apk/androidTest"
        self.base.mkdir(mode=0o700, parents=True)
        self.apk = self.base / "camera-androidDeviceTest.apk"
        self.apk.write_bytes(b"modeled-not-an-actual-APK")
        self.metadata = self.base / "output-metadata.json"
        self.metadata_data = {"applicationId": camera.REPORTER, "variantName": "androidDeviceTest", "artifactType": {"type": "APK"},
                              "elements": [{"type": "SINGLE", "filters": [], "outputFile": self.apk.name}]}
        self.metadata.write_text(json.dumps(self.metadata_data))
        self.home = self.root / "modeled-sdk"
        analyzer = self.home / "cmdline-tools/23.0/bin/apkanalyzer"
        analyzer.parent.mkdir(mode=0o700, parents=True)
        analyzer.write_text("not executed; fake runner only")
        analyzer.chmod(0o700)
        self.guest = FakeGuest(self.root, self.output)
        self.device, self.owner, self.clock = None, None, ModelClock()

    def model(self, master=None, *, scalar=None, native=False):
        if master is None:
            master = camera.Row(False, None)
        self.device = DeviceModel(self.guest, master, scalar, native)
        self.device.apk_digest = hashlib.sha256(self.apk.read_bytes()).hexdigest()
        self.owner = camera.OwnedDeveloperPrerequisite(self.root, self.output, self.home, camera.SERIAL, self.guest,
            runner=self.device.runner, clock=self.clock, sleep=self.clock.sleep)
        return self.owner

    def dispatch(self):
        self.owner.mark_receiver_prepare()
        self.owner.mark_reporter_dispatch()
        self.device.present[camera.REPORTER] = True
        self.device.settings_process = True  # Native Settings UI used; cached old process is allowed before reboot.

    def close_model(self, *, receiver_error=False):
        self.device.present[camera.RECEIVER] = False
        self.owner.record_receiver_cleanup({"package": camera.RECEIVER, "cleanup_status": "failed" if receiver_error else "passed",
            "owned_recipient_removed": True, **({"cleanup_error": "ValueError"} if receiver_error else {})} if
            self.owner.receiver_prepare_attempted else None)
        return self.owner.close()

    def setting_actions(self):
        return [action for action in self.device.actions if action[:2] == ("shell", "settings")]

    def disposal(self, **overrides):
        result = {"schema": "nativecmpkit.camera-fresh-guest.v1", "disposal_status": "passed", "errors": [],
                  "roots_absent": True, "identity_confined_disposal": True, "engine_known_exited": True,
                  "owned_transport_absent": True, "clean_shutdown": True}
        return result | overrides

    def tearDown(self):
        self.guest.finish()
        self.temp.cleanup()


class LifecycleModels(ModelFixture):
    def test_original_absence_one_enable_normal_reboot_exact_delete(self):
        self.model().prepare()
        self.dispatch()
        receipt = self.close_model()
        self.assertTrue(camera.accepted(receipt, self.disposal()))
        self.assertEqual(self.device.master, camera.Row(False, None))
        self.assertEqual(self.device.actions, [("shell", "settings", "--user", "0", "put", "global", camera.MASTER, "1"),
            ("uninstall", camera.REPORTER), ("reboot",), ("shell", "settings", "--user", "0", "delete", "global", camera.MASTER)])
        self.assertEqual(receipt["normal_reboot_attempts"], 1)
        self.assertNotIn(OLD, json.dumps(receipt))
        self.assertNotIn(NEW, json.dumps(receipt))

    def test_original0_one_put0_after_changed_kernel(self):
        self.model(camera.Row(True, "0")).prepare()
        self.dispatch()
        receipt = self.close_model()
        self.assertTrue(camera.accepted(receipt, self.disposal()))
        self.assertEqual(self.device.master, camera.Row(True, "0"))
        self.assertEqual(self.setting_actions()[-1][-1], "0")
        self.assertEqual(receipt["master_restore_attempts"], 1)

    def test_original1_true_no_op_even_native_true_scalar1(self):
        self.model(camera.Row(True, "1"), scalar=camera.Row(True, "1"), native=True).prepare()
        self.dispatch()
        receipt = self.close_model()
        self.assertTrue(camera.accepted(receipt, self.disposal()))
        self.assertEqual(self.setting_actions(), [])
        self.assertNotIn(("reboot",), self.device.actions)
        self.assertEqual(receipt["normal_reboot_attempts"], 0)

    def test_uncertain_enable_with_effect_reconciles_once_and_stays_failed(self):
        self.model()
        self.device.enable_timeout = True
        with self.assertRaises(TimeoutError):
            self.owner.prepare()
        receipt = self.close_model()
        self.assertEqual(receipt["prepare_status"], "failed")
        self.assertEqual(self.device.master, camera.Row(False, None))
        self.assertEqual(receipt["normal_reboot_attempts"], 1)
        self.assertEqual(receipt["master_restore_attempts"], 1)
        self.assertFalse(camera.accepted(receipt, self.disposal()))
        self.assertEqual(len([a for a in self.setting_actions() if a[-1] == "1"]), 1)

    def test_uncertain_enable_without_effect_no_restore_write(self):
        self.model(camera.Row(True, "0"))
        self.device.enable_timeout, self.device.enable_effect = True, False
        with self.assertRaises(TimeoutError):
            self.owner.prepare()
        receipt = self.close_model()
        self.assertEqual(receipt["normal_reboot_attempts"], 1)
        self.assertEqual(receipt["master_restore_attempts"], 0)
        self.assertEqual(self.device.master, camera.Row(True, "0"))
        self.assertFalse(camera.accepted(receipt, self.disposal()))

    def test_uncertain_reboot_changed_kernel_allows_safe_restore_not_acceptance(self):
        self.model().prepare()
        self.dispatch()
        self.device.reboot_timeout = True
        receipt = self.close_model()
        self.assertTrue(receipt["kernel_barrier_verified"])
        self.assertTrue(receipt["master_original_restored"])
        self.assertEqual(receipt["cleanup_status"], "failed")
        self.assertFalse(camera.accepted(receipt, self.disposal()))
        self.assertEqual(self.device.actions.count(("reboot",)), 1)

    def test_same_boot_id_never_barrier_and_no_master_restore(self):
        self.model().prepare()
        self.dispatch()
        self.device.reboot_effect = False
        receipt = self.close_model()
        self.assertFalse(receipt.get("kernel_barrier_verified", False))
        self.assertEqual(receipt["master_restore_attempts"], 0)
        self.assertEqual(self.device.actions.count(("reboot",)), 1)
        self.assertGreaterEqual(self.clock.now, 360)
        self.assertFalse(camera.accepted(receipt, self.disposal()))

    def test_unrequested_reboot_refuses_planned_reboot_and_write(self):
        self.model().prepare()
        self.dispatch()
        self.device.boot = NEW
        receipt = self.close_model()
        self.assertEqual(receipt["normal_reboot_attempts"], 0)
        self.assertEqual(receipt["master_restore_attempts"], 0)
        self.assertFalse(camera.accepted(receipt, self.disposal()))

    def test_started_settings_activity_new_epoch_gate_refuses_even_with_terminal_nothing(self):
        self.model().prepare()
        self.dispatch()
        self.device.new_settings_process = True
        self.device.new_settings_activities = ACTIVITIES.replace(b"  (nothing)\n",
            b"    * Hist #0: ActivityRecord{aa u0 com.android.settings/.Settings$DevelopmentSettingsDashboardActivity t2}\n"
            b"      state=STARTED\n  (nothing)\n")
        receipt = self.close_model()
        self.assertFalse(receipt.get("kernel_barrier_verified", False))
        self.assertEqual(receipt["master_restore_attempts"], 0)
        self.assertEqual(receipt["cleanup_status"], "failed")

    def test_original_native_scalar_cleanup_failure_sticky_after_reboot(self):
        self.model().prepare()
        self.dispatch()
        self.device.native, self.device.scalar = True, camera.Row(True, "1")
        receipt = self.close_model()
        self.assertFalse(receipt["pre_barrier_native_scalar_restored"])
        self.assertTrue(receipt["kernel_barrier_verified"])
        self.assertTrue(receipt["master_original_restored"])
        self.assertFalse(receipt["final_native_scalar_restored"])
        self.assertEqual(len(self.setting_actions()), 2)
        self.assertFalse(camera.accepted(receipt, self.disposal()))

    def test_post_boot_match_does_not_green_pre_boot_native_cleanup_failure(self):
        self.model().prepare()
        self.dispatch()
        self.device.native = True  # Scalar false: old native cache was not restored.
        receipt = self.close_model()
        self.assertFalse(receipt["pre_barrier_native_scalar_restored"])
        self.assertTrue(receipt["final_native_scalar_restored"])
        self.assertFalse(camera.accepted(receipt, self.disposal()))

    def test_reboot_exposes_scalar_durability_mismatch_never_compensated(self):
        self.model().prepare()
        self.dispatch()
        self.device.new_scalar, self.device.new_native = camera.Row(True, "1"), True
        receipt = self.close_model()
        self.assertTrue(receipt["pre_barrier_native_scalar_restored"])
        self.assertFalse(receipt["final_native_scalar_restored"])
        self.assertEqual(len(self.setting_actions()), 2)
        self.assertFalse(camera.accepted(receipt, self.disposal()))

    def test_delete0_rows_even_null_absence_readback_remains_failed(self):
        self.model().prepare()
        self.dispatch()
        self.device.delete_reply = b"Deleted 0 rows\n"
        receipt = self.close_model()
        self.assertTrue(receipt["master_original_restored"])
        self.assertEqual(receipt["cleanup_status"], "failed")
        self.assertFalse(camera.accepted(receipt, self.disposal()))

    def test_uncertain_restore_read_only_reconciliation_never_retry(self):
        self.model(camera.Row(True, "0")).prepare()
        self.dispatch()
        self.device.restore_timeout = True
        receipt = self.close_model()
        self.assertTrue(receipt["master_original_restored"])
        self.assertEqual(receipt["master_restore_attempts"], 1)
        self.assertFalse(camera.accepted(receipt, self.disposal()))
        self.owner.close()
        self.assertEqual(len([a for a in self.setting_actions() if a[-1] == "0"]), 1)

    def test_foreign_master_before_reboot_refuses_all_restoring_actions(self):
        self.model(camera.Row(True, "0")).prepare()
        self.dispatch()
        self.device.master = camera.Row(True, "0")
        receipt = self.close_model()
        self.assertEqual(receipt["normal_reboot_attempts"], 0)
        self.assertEqual(receipt["master_restore_attempts"], 0)
        self.assertFalse(camera.accepted(receipt, self.disposal()))

    def test_foreign_new_epoch_master_refuses_restoring_write(self):
        self.model(camera.Row(True, "0")).prepare()
        self.dispatch()
        self.device.new_master = camera.Row(False, None)
        receipt = self.close_model()
        self.assertTrue(receipt["kernel_barrier_verified"])
        self.assertEqual(receipt["master_restore_attempts"], 0)
        self.assertFalse(camera.accepted(receipt, self.disposal()))

    def test_foreign_table_after_reboot_refuses_restore(self):
        self.model().prepare()
        self.dispatch()
        def after_reboot(args, device):
            if args == ("reboot",):
                device.foreign_table = True
        self.device.hook = after_reboot
        receipt = self.close_model()
        self.assertEqual(receipt["master_restore_attempts"], 0)
        self.assertFalse(camera.accepted(receipt, self.disposal()))

    def test_lost_popen_before_cleanup_no_guest_mutations(self):
        self.model().prepare()
        self.dispatch()
        self.guest.live = False
        receipt = self.close_model()
        self.assertNotIn(("uninstall", camera.REPORTER), self.device.actions)
        self.assertEqual(receipt["normal_reboot_attempts"], 0)
        self.assertFalse(camera.accepted(receipt, self.disposal()))

    def test_receiver_cleanup_error_retained_when_absence_allows_restoration(self):
        self.model().prepare()
        self.dispatch()
        receipt = self.close_model(receiver_error=True)
        self.assertTrue(receipt["master_original_restored"])
        self.assertEqual(receipt["cleanup_status"], "failed")
        self.assertFalse(camera.accepted(receipt, self.disposal()))

    def test_disposal_or_shutdown_red_cannot_be_greened_by_native_like_receipt(self):
        self.model().prepare()
        self.dispatch()
        receipt = self.close_model()
        self.assertTrue(camera.accepted(receipt, self.disposal()))
        for override in ({"roots_absent": False}, {"clean_shutdown": False}, {"owned_transport_absent": False},
                         {"disposal_status": "failed"}, {"errors": [{"phase": "disposal", "class": "ValueError"}]}):
            self.assertFalse(camera.accepted(receipt, self.disposal(**override)))

    def test_latches_published_before_ipc(self):
        self.model()
        checked = []
        def assert_latch(args, device):
            key = None
            if args[:6] == ("shell", "settings", "--user", "0", "put", "global"):
                key = "master_enable_attempts" if args[-1] == "1" else "master_restore_attempts"
            elif args[:6] == ("shell", "settings", "--user", "0", "delete", "global"):
                key = "master_restore_attempts"
            elif args == ("reboot",):
                key = "normal_reboot_attempts"
            elif args == ("uninstall", camera.REPORTER):
                key = "reporter_uninstall_attempted"
            if key:
                published = json.loads((self.output / "camera-developer-prerequisite.json").read_bytes())
                self.assertEqual(published[key], 1)
                checked.append(key)
        self.device.hook = assert_latch
        self.owner.prepare()
        self.dispatch()
        self.close_model()
        self.assertEqual(checked, ["master_enable_attempts", "reporter_uninstall_attempted", "normal_reboot_attempts", "master_restore_attempts"])


class AdmissionModels(ModelFixture):
    def test_shell_root_refused_before_master_write(self):
        self.model()
        self.device.shell_uid = b"0"
        with self.assertRaises(ValueError):
            self.owner.prepare()
        self.assertEqual(self.device.actions, [])

    def test_required_read_permissions_refused_before_write(self):
        self.model()
        self.device.denied.add("android.permission.ACCESS_CONTENT_PROVIDERS_EXTERNALLY")
        with self.assertRaises(ValueError):
            self.owner.prepare()
        self.assertEqual(self.device.actions, [])

    def test_required_write_permission_refused_before_write(self):
        self.model()
        self.device.denied.add("android.permission.WRITE_SECURE_SETTINGS")
        with self.assertRaises(ValueError):
            self.owner.prepare()
        receipt = self.close_model()
        self.assertEqual(self.device.actions, [])
        self.assertTrue(receipt["master_original_restored"])
        self.assertFalse(camera.accepted(receipt, self.disposal()))

    def test_original1_needs_no_write_permission(self):
        self.model(camera.Row(True, "1"))
        self.device.denied.add("android.permission.WRITE_SECURE_SETTINGS")
        self.owner.prepare()
        self.dispatch()
        self.assertTrue(camera.accepted(self.close_model(), self.disposal()))

    def test_inconsistent_original_native_pair_refused(self):
        self.model(native=True)
        with self.assertRaises(ValueError):
            self.owner.prepare()
        self.assertEqual(self.device.actions, [])

    def test_fresh_started_settings_activity_refused_not_killed(self):
        self.model()
        self.device.settings_process = True
        self.device.settings_activities = ACTIVITIES.replace(b"  (nothing)\n",
            b"    * Hist #0: ActivityRecord{aa u0 com.android.settings/.Settings$DevelopmentSettingsDashboardActivity t2}\n"
            b"      state=STARTED\n  (nothing)\n")
        with self.assertRaises(ValueError):
            self.owner.prepare()
        self.assertEqual(self.device.actions, [])

    def test_recent_task_refused_before_master_enable(self):
        self.model()
        self.device.recent_tasks = RECENTS + b"  Recent tasks:\n"
        with self.assertRaises(ValueError):
            self.owner.prepare()
        self.assertEqual(self.device.actions, [])

    def test_changing_original_snapshot_refused(self):
        self.model()
        count = [0]
        def changed(args, device):
            if args == ("shell", "cat", "/proc/sys/kernel/random/boot_id"):
                count[0] += 1
                if count[0] == 2:
                    return cp((NEW + "\n").encode())
        self.device.hook = changed
        with self.assertRaises(ValueError):
            self.owner.prepare()
        self.assertEqual(self.device.actions, [])

    def test_non_binary_or_overflow_runner_output_refused(self):
        self.model()
        def bad(args, device):
            if args == ("shell", "id", "-u"):
                return cp(b"x" * 65537)
        self.device.hook = bad
        with self.assertRaises(ValueError):
            self.owner.prepare()
        self.assertEqual(self.device.actions, [])


class ReporterModels(ModelFixture):
    def test_existing_reporter_never_replaced_or_uninstalled(self):
        self.model()
        self.device.present[camera.REPORTER] = True
        with self.assertRaises(ValueError):
            self.owner.prepare()
        self.close_model()
        self.assertEqual(self.device.actions, [])

    def test_wrong_classname_derived_package_metadata_refused(self):
        self.metadata_data["applicationId"] = "com.mohamedrejeb.calf.camerapicker.test"
        self.metadata.write_text(json.dumps(self.metadata_data))
        self.model()
        with self.assertRaises(ValueError):
            self.owner.prepare()
        self.assertEqual(self.device.actions, [])

    def test_manifest_wrong_package_refusal(self):
        self.model()
        self.device.manifest = MANIFEST.replace(camera.REPORTER.encode(), b"foreign.reporter", 1)
        with self.assertRaises(ValueError):
            self.owner.prepare()
        self.assertEqual(self.device.actions, [])

    def test_source_apk_changed_after_managed_install_refuses_uninstall_barrier(self):
        self.model().prepare()
        self.dispatch()
        self.apk.write_bytes(b"foreign changed APK")
        receipt = self.close_model()
        self.assertNotIn(("uninstall", camera.REPORTER), self.device.actions)
        self.assertEqual(receipt["normal_reboot_attempts"], 0)
        self.assertFalse(camera.accepted(receipt, self.disposal()))

    def test_installed_foreign_bytes_refuse_uninstall_and_barrier(self):
        self.model().prepare()
        self.dispatch()
        self.device.installed_digest = "f" * 64
        receipt = self.close_model()
        self.assertFalse(receipt.get("reporter_installed_bytes_verified", False))
        self.assertNotIn(("uninstall", camera.REPORTER), self.device.actions)
        self.assertEqual(receipt["normal_reboot_attempts"], 0)

    def test_already_absent_retains_absence_not_invented_installed_byte_proof(self):
        self.model().prepare()
        self.dispatch()
        self.device.present[camera.REPORTER] = False
        receipt = self.close_model()
        self.assertTrue(receipt["reporter_removed"])
        self.assertFalse(receipt["reporter_installed_bytes_verified"])
        self.assertNotIn(("uninstall", camera.REPORTER), self.device.actions)
        self.assertTrue(camera.accepted(receipt, self.disposal()))

    def test_uncertain_uninstall_absence_readback_sticky_no_retry(self):
        self.model().prepare()
        self.dispatch()
        self.device.uninstall_timeout = True
        receipt = self.close_model()
        self.assertTrue(receipt["reporter_removed"])
        self.assertTrue(receipt["master_original_restored"])
        self.assertFalse(camera.accepted(receipt, self.disposal()))
        self.owner.close()
        self.assertEqual(self.device.actions.count(("uninstall", camera.REPORTER)), 1)

    def test_present_without_dispatch_ownership_refuses_uninstall(self):
        self.model().prepare()
        self.device.present[camera.REPORTER] = True
        receipt = self.close_model()
        self.assertEqual(receipt["normal_reboot_attempts"], 0)
        self.assertEqual(self.device.actions.count(("uninstall", camera.REPORTER)), 0)

    def test_no_new_force_stop_or_scalar_native_mutation(self):
        self.model().prepare()
        self.dispatch()
        self.close_model()
        for action in self.device.actions:
            self.assertNotIn("force-stop", action)
            self.assertNotIn("kill", action)
            self.assertNotIn(camera.SCALAR, action)
            if action[0] == "reboot":
                self.assertEqual(action, ("reboot",))


class FakeProcess:
    def __init__(self):
        self.pid, self.returncode, self.running = 3456, None, True

    def poll(self):
        return None if self.running else self.returncode


class GuestFilesystem(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fd-case-", dir=PRIVATE)
        self.root = Path(self.temp.name)
        self.output = self.root / "build/ci-verification/guest"
        self.output.mkdir(mode=0o700, parents=True)
        self.env = {"ANDROID_SERIAL": camera.SERIAL, "ANDROID_AVD_HOME": str(self.output / "avd"),
                    "ANDROID_EMULATOR_HOME": str(self.output / "avd"), "ANDROID_USER_HOME": str(self.output / "android-user")}
        self.guest = None

    def own(self):
        self.guest = camera.OwnedFreshGuest(self.root, self.output, NAME, self.env,
            child_probe=lambda process: process.running)
        return self.guest

    def config(self, *, escaped=False):
        directory = self.output / "avd" / (NAME + ".avd")
        directory.mkdir(mode=0o700)
        ini = "avd.ini.encoding=UTF-8\npath=" + str(directory) + "\npath.rel=avd/" + NAME + ".avd\ntarget=android-35\n"
        (self.output / "avd" / (NAME + ".ini")).write_text(ini)
        values = "AvdId=" + NAME + "\nabi.type=x86_64\ntag.id=google_apis\nimage.sysdir.1=system-images/android-35/google_apis/x86_64/\nskin.path=_no_skin\n"
        if escaped:
            values += "disk.dataPartition.path=" + str(self.root / "outside-userdata.img") + "\n"
        (directory / "config.ini").write_text(values)
        return directory

    def launch_model(self):
        self.guest.create()
        directory = self.config()
        self.guest.capture_avd(self.root / "modeled-sdk")
        self.guest.before_launch()
        process = FakeProcess()
        self.guest.attach(process)
        return directory, process

    def test_new_roots_mode_and_partial_setup_no_launch_full_disposal(self):
        self.own().create()
        (self.output / "avd/owned-data").write_bytes(b"owned userdata")
        (self.output / "android-user/debug.keystore").write_bytes(b"modeled signing file")
        for name in ("avd", "android-user"):
            self.assertEqual(stat.S_IMODE(os.lstat(self.output / name).st_mode), 0o700)
        receipt = self.guest.dispose(engine_exited=False, transport_absent=False, clean_shutdown=False)
        self.assertTrue(receipt["roots_absent"])
        self.assertTrue(receipt["identity_confined_disposal"])
        self.assertFalse(receipt["clean_shutdown"])
        self.assertTrue((self.output / "camera-fresh-guest.json").is_file())

    def test_partial_second_root_creation_tracks_first_and_refuses_foreign_second(self):
        self.own()
        real_mkdir = os.mkdir
        def fail_second(name, *args, **kwargs):
            if name == "android-user":
                raise OSError("Modeled setup failure")
            return real_mkdir(name, *args, **kwargs)
        with patch.object(camera.os, "mkdir", side_effect=fail_second), self.assertRaises(OSError):
            self.guest.create()
        receipt = self.guest.dispose(engine_exited=False, transport_absent=False, clean_shutdown=False)
        self.assertTrue(receipt["roots_absent"])
        self.assertEqual(receipt["created_roots"], ["avd"])

    def test_known_exited_owned_child_and_absent_transport_disposes_all_userdata(self):
        self.own()
        directory, process = self.launch_model()
        (directory / "userdata-qemu.img").write_bytes(b"owned modeled overlay")
        (self.output / "android-user/debug.keystore").write_bytes(b"modeled signing")
        process.running, process.returncode = False, 0
        receipt = self.guest.dispose(engine_exited=True, transport_absent=True, clean_shutdown=True)
        self.assertTrue(receipt["roots_absent"])
        self.assertEqual(receipt["disposal_status"], "passed")
        for name in ("avd", "android-user"):
            with self.assertRaises(FileNotFoundError):
                os.lstat(self.output / name)

    def test_live_child_or_transport_unknown_refuses_deletion(self):
        self.own()
        self.launch_model()
        receipt = self.guest.dispose(engine_exited=False, transport_absent=True, clean_shutdown=False)
        self.assertEqual(receipt["disposal_status"], "failed")
        self.assertTrue((self.output / "avd").is_dir())

    def test_unknown_popen_after_launch_latch_refuses_deletion(self):
        self.own().create()
        self.config()
        self.guest.capture_avd(self.root / "modeled-sdk")
        self.guest.before_launch()
        receipt = self.guest.dispose(engine_exited=True, transport_absent=True, clean_shutdown=False)
        self.assertEqual(receipt["disposal_status"], "failed")
        self.assertTrue((self.output / "avd").is_dir())

    def test_swapped_root_refuses_foreign_deletion(self):
        self.own().create()
        os.rename(self.output / "avd", self.output / "old-avd")
        (self.output / "avd").mkdir(mode=0o700)
        sentinel = self.output / "avd/foreign"
        sentinel.write_bytes(b"foreign data")
        receipt = self.guest.dispose(engine_exited=False, transport_absent=False, clean_shutdown=False)
        self.assertEqual(receipt["disposal_status"], "failed")
        self.assertEqual(sentinel.read_bytes(), b"foreign data")

    def test_root_symlink_swap_never_traversed(self):
        self.own().create()
        os.rename(self.output / "avd", self.output / "old-avd")
        external = self.root / "external"
        external.mkdir(mode=0o700)
        (external / "sentinel").write_bytes(b"must remain")
        (self.output / "avd").symlink_to(external, target_is_directory=True)
        receipt = self.guest.dispose(engine_exited=False, transport_absent=False, clean_shutdown=False)
        self.assertEqual(receipt["disposal_status"], "failed")
        self.assertEqual((external / "sentinel").read_bytes(), b"must remain")

    def test_descendant_symlink_unlinked_without_touching_external_target(self):
        self.own().create()
        external = self.root / "outside"
        external.mkdir(mode=0o700)
        (external / "sentinel").write_bytes(b"outside untouched")
        (self.output / "avd/external-link").symlink_to(external, target_is_directory=True)
        receipt = self.guest.dispose(engine_exited=False, transport_absent=False, clean_shutdown=False)
        self.assertTrue(receipt["roots_absent"])
        self.assertEqual((external / "sentinel").read_bytes(), b"outside untouched")

    def test_escaped_mutable_config_refuses_launch(self):
        self.own().create()
        self.config(escaped=True)
        with self.assertRaises(ValueError):
            self.guest.capture_avd(self.root / "modeled-sdk")
        self.assertFalse(self.guest.launch_attempted)

    def test_changed_config_or_same_pid_wrong_child_refuses_live_barrier(self):
        self.own()
        directory, process = self.launch_model()
        (directory / "config.ini").write_text("foreign config")
        with self.assertRaises(ValueError):
            self.guest.verify_live()
        process.running = False
        with self.assertRaises(ValueError):
            self.guest.verify_live()

    def test_failed_disposal_not_automatically_retried(self):
        self.own()
        _, process = self.launch_model()
        first = self.guest.dispose(engine_exited=False, transport_absent=False, clean_shutdown=False)
        process.running, process.returncode = False, 0
        second = self.guest.dispose(engine_exited=True, transport_absent=True, clean_shutdown=True)
        self.assertEqual(first, second)
        self.assertTrue((self.output / "avd").exists())

    def test_no_signals_after_reap_in_bounded_command_cleanup(self):
        process = FakeProcess()
        process.running, process.returncode = False, 0
        with patch.object(camera.os, "killpg", side_effect=AssertionError("No post-reap signal")):
            camera.stop_command(process)

    def tearDown(self):
        if self.guest is not None and not self.guest.closed:
            self.guest.dispose(engine_exited=False, transport_absent=False, clean_shutdown=False)
        self.temp.cleanup()


class SafetyRefinementModels(ModelFixture):
    def test_unrequested_epoch_refuses_reporter_uninstall_before_any_cleanup_action(self):
        self.model().prepare()
        self.dispatch()
        self.device.boot = NEW
        receipt = self.close_model()
        self.assertNotIn(("uninstall", camera.REPORTER), self.device.actions)
        self.assertEqual(receipt["normal_reboot_attempts"], 0)

    def test_avd_name_race_before_enable_refuses_the_put(self):
        self.model()
        def foreign_avd(args, device):
            if args == ("emu", "avd", "name") and "android.permission.WRITE_SECURE_SETTINGS" in self.device.denied:
                return cp(b"foreign-avd\nOK\n")
            if args[:4] == ("shell", "dumpsys", "package", "check-permission") and args[4] == "android.permission.WRITE_SECURE_SETTINGS":
                # Return a granted permission but make the following ownership query foreign.
                self.device.denied.add("android.permission.WRITE_SECURE_SETTINGS")
                return cp(b"0\n")
        self.device.hook = foreign_avd
        with self.assertRaises(ValueError):
            self.owner.prepare()
        self.assertEqual(self.setting_actions(), [])

    def test_shell_uid_changed_before_write_refuses_root_put(self):
        self.model()
        def root_after_read(args, device):
            if args[:4] == ("shell", "dumpsys", "package", "check-permission") and args[4] == "android.permission.WRITE_SECURE_SETTINGS":
                device.shell_uid = b"0"
        self.device.hook = root_after_read
        with self.assertRaises(ValueError):
            self.owner.prepare()
        self.assertEqual(self.setting_actions(), [])

    def test_boot_epoch_race_after_installed_byte_read_refuses_uninstall(self):
        self.model().prepare()
        self.dispatch()
        def change_epoch_at_hash(args, device):
            if args[:2] == ("shell", "sha256sum"):
                device.boot = NEW
        self.device.hook = change_epoch_at_hash
        receipt = self.close_model()
        self.assertNotIn(("uninstall", camera.REPORTER), self.device.actions)
        self.assertEqual(receipt["normal_reboot_attempts"], 0)

    def test_malformed_compiled_manifest_is_sticky_bounded_refusal(self):
        self.model()
        self.device.manifest = b"<manifest"
        with self.assertRaises(ValueError):
            self.owner.prepare()
        self.assertEqual(self.owner.receipt["prepare_status"], "failed")
        self.assertEqual(self.device.actions, [])


class GuestDisposalRefinement(unittest.TestCase):
    setUp = GuestFilesystem.setUp
    tearDown = GuestFilesystem.tearDown
    own = GuestFilesystem.own
    config = GuestFilesystem.config
    launch_model = GuestFilesystem.launch_model
    def test_changed_config_after_engine_exit_refuses_full_userdata_disposal_claim(self):
        self.own()
        directory, process = self.launch_model()
        (directory / "config.ini").write_text("disk.dataPartition.path=/foreign/userdata.img\n")
        process.running, process.returncode = False, 0
        receipt = self.guest.dispose(engine_exited=True, transport_absent=True, clean_shutdown=True)
        self.assertEqual(receipt["disposal_status"], "failed")
        self.assertTrue((self.output / "avd").exists())


class ControllerOwnershipModels(unittest.TestCase):
    """Execute only the owning controller function with all external work stubbed."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="controller-case-", dir=PRIVATE)
        self.root, self.events = Path(self.temp.name), []
        self.native_pass, self.prepare_error, self.close_error = True, False, False
        self.transport_error, self.create_error, self.partial_root_error = False, False, False
        self.process = None
        model = self
        class Guest:
            def __init__(self, root, output, name, env):
                self.output, self.launched = output, False
                self.receipt = {"schema": "nativecmpkit.camera-fresh-guest.v1", "disposal_status": "not-started", "errors": []}
                model.events.append("guest-acquired")
            def create(self):
                (self.output / "avd").mkdir(mode=0o700)
                if model.partial_root_error:
                    raise OSError("Modeled partial root setup")
                (self.output / "android-user").mkdir(mode=0o700)
                model.events.append("private-roots-created")
            def capture_avd(self, home):
                model.events.append("avd-config-captured")
            def before_launch(self):
                self.launched = True
                model.events.append("launch-latched")
            def attach(self, process):
                self.process = process
                model.events.append("popen-captured")
            def verify_live(self):
                camera.require(self.process.running, "Model Popen ownership lost")
                return True
            def dispose(self, **facts):
                model.events.append("full-disposal")
                safe = not self.launched or facts["engine_exited"] and facts["transport_absent"]
                if safe:
                    for name in ("avd", "android-user"):
                        if (self.output / name).exists():
                            shutil.rmtree(self.output / name)
                self.receipt.update(disposal_status="passed" if safe else "failed", roots_absent=safe,
                    identity_confined_disposal=safe, engine_known_exited=not self.launched or facts["engine_exited"],
                    owned_transport_absent=not self.launched or facts["transport_absent"], clean_shutdown=facts["clean_shutdown"])
                return dict(self.receipt)
        class Developer:
            def __init__(self, *args):
                self.receipt = {"schema": "nativecmpkit.camera-developer-prerequisite.v1", "focus": camera.FOCUS, "api_level": 35,
                    "prepare_status": "not-started", "cleanup_status": "not-started", "errors": [], "master1_observed": True,
                    "reporter_dispatch_attempted": False, "reporter_removed": True, "receiver_removed": True,
                    "pre_barrier_native_scalar_restored": True, "master_original_restored": True, "final_native_scalar_restored": True,
                    "master_enable_attempts": 1, "normal_reboot_attempts": 1, "master_restore_attempts": 1,
                    "master_initialization_completed": True, "kernel_barrier_verified": True, "normal_reboot_request_error_free": True,
                    "new_boot_epoch_changed": True, "same_popen_avd_userdata_verified": True,
                    "reporter_source_apk_sha256": "a" * 64}
            def prepare(self):
                model.events.append("developer-prepare")
                self.receipt["prepare_status"] = "failed" if model.prepare_error else "passed"
                if model.prepare_error:
                    self.receipt["errors"].append({"phase": "prepare", "class": "ValueError"})
                    raise ValueError("Modeled uncertain owning acquisition")
                return dict(self.receipt)
            def mark_receiver_prepare(self):
                model.events.append("receiver-install-latched")
            def mark_reporter_dispatch(self):
                model.events.append("reporter-install-latched")
                self.receipt["reporter_dispatch_attempted"] = True
            def record_receiver_cleanup(self, receipt):
                model.events.append("receiver-cleanup-recorded")
            def close(self):
                model.events.append("developer-close")
                self.receipt["cleanup_status"] = "passed"
                if model.close_error:
                    raise ValueError("Modeled partial owning cleanup")
                return dict(self.receipt)
        class Receiver:
            def __init__(self, *args, **kwargs):
                self.receipt = {"package": camera.RECEIVER, "owned_recipient_removed": False}
            def prepare(self):
                model.events.append("receiver-prepare")
                self.receipt["prepare_status"] = "passed"
                return self.receipt
            def close(self):
                model.events.append("receiver-close")
                self.receipt.update(cleanup_status="passed", owned_recipient_removed=True)
                return self.receipt
        def execute(root, command, log, timeout, reserve, **kwargs):
            model.events.append(log.stem)
            return {"exit_code": 1 if model.create_error and log.stem == "owned-avd-create" else 0}
        def native_like(*args, **kwargs):
            model.events.append("modeled-native-dispatch")
            return {"passed": model.native_pass, "totals": {"tests": 1}, "modules": []}
        lt = types.SimpleNamespace(safe_path=lambda root, relative: root / relative,
            plan=lambda root, target, **kwargs: {"focus": kwargs.get("focus"), "expected": [{"project": ":calf-camera-picker", "task": ":modeled"}],
                "complete_suite_requested": False, "explicit_module_subset": True, "test_bearing_modules_not_requested": [],
                "finite_only_device_modules_not_requested": []},
            android_io_documents_required=lambda plan: False, android_permission_demo_required=lambda plan: False,
            android_storage_probe_required=lambda plan: False, android_geo_probe_required=lambda plan: False,
            android_share_recipient_required=lambda plan: False, android_camera_receiver_required=lambda plan: plan.get("focus") == camera.FOCUS,
            ANDROID_CAMERA_FOCUSES={camera.FOCUS}, ANDROID_IO_PROVIDER_FOCUS="io-provider", ANDROID_IO_DEFAULT_DECODE_FOCUS="io-default",
            ANDROID_IO_REFERENCE_FOCUS="io-reference", WEBVIEW_ANDROID_MEDIA_FOCUS="webview-media",
            snapshot_inputs=lambda root: {"modeled-unchanged-source": "b" * 64}, git_revision=lambda root: "c" * 40,
            write_json=lambda path, value: path.write_text(json.dumps(value)), utc_now=lambda: "2026-11-01T00:00:00Z",
            gradle_command=lambda *args, **kwargs: ["not-executed-gradle", "not-executed-connected-task"], execute=execute, run=native_like)
        def launch(*args, **kwargs):
            model.events.append("modeled-popen")
            model.process = FakeProcess()
            return model.process
        def boot(*args, **kwargs):
            model.events.append("owned-boot")
            return {"api_level": "35", "abi": "x86_64", "selinux": "Enforcing", "boot_completed": "1"}
        def stop(*args):
            model.events.append("engine-stop")
            model.process.running, model.process.returncode = False, 0
            return {"exit_code": 0, "clean_shutdown": True, "graceful_kill_requested": True, "forced_owned_group": False}
        def transport(*args):
            model.events.append("transport-absence")
            if model.transport_error:
                raise ValueError("Modeled unknown post-exit device table")
            return True
        source = (TREE / "scripts/ci/android_device_tests.py").read_text()
        selected = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name in ("_run", "preflight_error_origin")]
        globals_ = {"__name__": "camera_controller_owning_model", "__file__": str(TREE / "scripts/ci/android_device_tests.py"),
            "Path": Path, "os": os, "re": camera.re, "shutil": shutil, "signal": camera.signal, "uuid": camera.uuid, "time": camera.time,
            "subprocess": types.SimpleNamespace(Popen=launch, STDOUT=subprocess.STDOUT, SubprocessError=subprocess.SubprocessError),
            "lt": lt, "runtime": types.SimpleNamespace(capture=lambda **kwargs: {"source_revision": "c" * 40, "source_tree_dirty": False}),
            "camera_developer": types.SimpleNamespace(is_required=camera.is_required, OwnedFreshGuest=Guest, OwnedDeveloperPrerequisite=Developer,
                                                      accepted=camera.accepted),
            "android_camera_receiver": types.SimpleNamespace(OwnedCameraReceiver=Receiver),
            "API": 35, "SERIAL": camera.SERIAL, "PORT": 5588, "RESERVE_MIB": 8192,
            "sdk_assets": lambda *args, **kwargs: {"system_image": "system-images;android-35;google_apis;x86_64"},
            "ensure_ports_unused": lambda: None, "adb": lambda *args, **kwargs: "List of devices attached",
            "avd_name": lambda *args: NAME, "wait_for_owned_boot": boot, "stop_owned_emulator": stop,
            "wait_for_owned_transport_removal": transport}
        exec(compile(ast.Module(body=selected, type_ignores=[]), globals_["__file__"], "exec"), globals_)
        self.run_controller = globals_["_run"]

    def run_model(self, *, focus=camera.FOCUS):
        with patch.dict(os.environ, {"ANDROID_HOME": str(self.root / "not-executed-sdk")}):
            return self.run_controller(self.root, "build/ci-verification/controller", (camera.MODULE,) if focus else None, focus=focus)

    def test_modeled_positive_order_and_every_extra_pass_gate(self):
        result = self.run_model()
        self.assertTrue(result["passed"])
        for first, second in (("owned-boot", "developer-prepare"), ("developer-prepare", "receiver-prepare"),
            ("reporter-install-latched", "modeled-native-dispatch"), ("receiver-close", "developer-close"),
            ("developer-close", "engine-stop"), ("transport-absence", "full-disposal")):
            self.assertLess(self.events.index(first), self.events.index(second))

    def test_modeled_failed_native_never_greened_by_cleanup(self):
        self.native_pass = False
        result = self.run_model()
        self.assertFalse(result["passed"])
        self.assertTrue(result["camera_guest_disposal"]["roots_absent"])

    def test_partial_prerequisite_failure_preserves_prepare_receipt_and_cleanup(self):
        self.prepare_error = True
        result = self.run_model()
        self.assertFalse(result["passed"])
        self.assertEqual(result["controller_error"], "ValueError")
        self.assertEqual(result["camera_developer_prerequisite"]["prepare_status"], "failed")
        self.assertEqual(result["camera_developer_prerequisite"]["reporter_source_apk_sha256"], "a" * 64)
        self.assertIn("developer-close", self.events)
        self.assertNotIn("receiver-prepare", self.events)

    def test_partial_close_error_preserves_kernel_and_apk_facts(self):
        self.close_error = True
        result = self.run_model()
        self.assertFalse(result["passed"])
        self.assertTrue(result["camera_developer_prerequisite"]["kernel_barrier_verified"])
        self.assertEqual(result["camera_developer_prerequisite"]["cleanup_status"], "failed")
        self.assertEqual(result["camera_developer_prerequisite"]["reporter_source_apk_sha256"], "a" * 64)

    def test_transport_error_retains_reaped_engine_facts_and_refuses_disposal(self):
        self.transport_error = True
        result = self.run_model()
        self.assertFalse(result["passed"])
        self.assertEqual(result["emulator_shutdown"]["exit_code"], 0)
        self.assertTrue(result["emulator_shutdown"]["graceful_kill_requested"])
        self.assertTrue(result["emulator_shutdown"]["controller_cleanup_error"])
        self.assertEqual(result["camera_guest_disposal"]["disposal_status"], "failed")

    def test_create_stage_red_without_guest_launch_still_disposes_fresh_roots(self):
        self.create_error = True
        result = self.run_model()
        self.assertFalse(result["passed"])
        self.assertTrue(result["camera_guest_disposal"]["roots_absent"])
        self.assertNotIn("modeled-popen", self.events)

    def test_partial_root_creation_is_inside_owning_finally(self):
        self.partial_root_error = True
        result = self.run_model()
        self.assertFalse(result["passed"])
        self.assertTrue(result["camera_guest_disposal"]["roots_absent"])
        self.assertEqual(result["controller_error"], "OSError")
        self.assertIn("full-disposal", self.events)

    def test_other_route_has_no_new_prerequisite_or_data_disposal(self):
        result = self.run_model(focus=None)
        self.assertTrue(result["passed"])
        self.assertNotIn("guest-acquired", self.events)
        self.assertNotIn("developer-prepare", self.events)
        self.assertNotIn("full-disposal", self.events)
        self.assertNotIn("camera_developer_prerequisite", result)
        self.assertTrue((self.root / "build/ci-verification/controller/avd").is_dir())

    def tearDown(self):
        self.temp.cleanup()


if __name__ == "__main__":
    os.umask(0o077)
    unittest.main()
