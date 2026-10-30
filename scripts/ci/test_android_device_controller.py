"""Adversarial controller fixtures; zero emulators, Android APIs or library tests.

Actual SDK properties and confined temporary evidence files are exercised. Process,
KVM, Gradle, boot and test execution are mocked explicitly, not reported as runtime
verification. The hosted enforcing AVD remains its own acceptance requirement.
"""
from contextlib import ExitStack, contextmanager
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import android_device_tests as c


class InstalledSdkContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.image = self.home / "system-images/android-35/google_apis/x86_64/source.properties"
        self.image.parent.mkdir(parents=True)
        self.image.write_text("AndroidVersion.ApiLevel=35\nSystemImage.Abi=x86_64\n"
                              "SystemImage.TagId=google_apis\nPkg.Revision=9\nPrivateName=do-not-export\n")
        emulator = self.home / "emulator/source.properties"
        emulator.parent.mkdir()
        emulator.write_text("Pkg.Revision=36.2.12\nPrivateValue=do-not-export\n")
        for name in ("platform-tools/adb", "emulator/emulator", "cmdline-tools/23.0/bin/avdmanager"):
            p = self.home / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("not executed synthetic SDK executable\n")
            p.chmod(0o700)

    def test_exact_official_package_identity_and_versions_exclude_private_properties(self):
        assets = c.sdk_assets(self.home)
        self.assertEqual("system-images;android-35;google_apis;x86_64", assets["system_image"])
        self.assertEqual("9", assets["image_revision"])
        self.assertEqual("36.2.12", assets["emulator_revision"])
        self.assertNotIn("do-not-export", json.dumps(assets))

    def test_wrong_api_abi_tag_or_missing_version_is_not_substituted(self):
        original = self.image.read_text()
        for old, new in (("ApiLevel=35", "ApiLevel=34"), ("Abi=x86_64", "Abi=arm64-v8a"),
                         ("TagId=google_apis", "TagId=default"), ("Revision=9", "Revision=unknown")):
            with self.subTest(new=new):
                self.image.write_text(original.replace(old, new))
                with self.assertRaises(ValueError):
                    c.sdk_assets(self.home)

    def test_duplicate_oversized_symlink_or_missing_properties_are_rejected(self):
        self.image.write_text("Pkg.Revision=9\nPkg.Revision=10\n")
        with self.assertRaises(ValueError):
            c.properties(self.image)
        self.image.write_text("x" * 65537)
        with self.assertRaises(ValueError):
            c.properties(self.image)
        self.image.unlink()
        with self.assertRaises(ValueError):
            c.properties(self.image)
        target = self.home / "other"
        target.write_text("Pkg.Revision=9\n")
        self.image.symlink_to(target)
        with self.assertRaises(ValueError):
            c.properties(self.image)

    def test_missing_executable_fails_before_any_launch(self):
        (self.home / "emulator/emulator").unlink()
        with self.assertRaises(ValueError):
            c.sdk_assets(self.home)


class OwnedEngineLifecycle(unittest.TestCase):
    def setUp(self):
        self.home = Path("/synthetic/sdk")
        self.process = Mock()
        self.process.poll.return_value = None
        self.process.returncode = 0

    def test_native_host_and_kvm_are_required_before_any_controller_setup(self):
        for system, machine, character, accessible in (
            ("Darwin", "arm64", True, True), ("Linux", "aarch64", True, True),
            ("Linux", "x86_64", False, True), ("Linux", "x86_64", True, False),
        ):
            with (self.subTest(system=system, machine=machine, character=character, accessible=accessible),
                  patch.object(c.platform, "system", return_value=system),
                  patch.object(c.platform, "machine", return_value=machine),
                  patch.object(c.Path, "is_char_device", return_value=character),
                  patch.object(c.os, "access", return_value=accessible)):
                with self.assertRaises(ValueError):
                    c.require_host()
        with (patch.object(c.platform, "system", return_value="Linux"),
              patch.object(c.platform, "machine", return_value="x86_64"),
              patch.object(c.Path, "is_char_device", return_value=True),
              patch.object(c.os, "access", return_value=True)):
            c.require_host()

    def test_avd_name_readback_requires_the_exact_adb_protocol(self):
        for value in ("owned", "owned\nFAILED", "owned\nOK\nextra"):
            with self.subTest(value=value), patch.object(c, "adb", return_value=value):
                with self.assertRaises(ValueError):
                    c.avd_name(self.home)
        with patch.object(c, "adb", return_value="owned\nOK"):
            self.assertEqual("owned", c.avd_name(self.home))

    def test_graceful_shutdown_requires_reestablished_name_and_native_zero_exit(self):
        with patch.object(c, "avd_name", return_value="owned") as name, patch.object(c, "adb") as adb:
            result = c.stop_owned_emulator(self.home, self.process, "owned", True)
        name.assert_called_once_with(self.home)
        adb.assert_called_once_with(self.home, "-s", c.SERIAL, "emu", "kill")
        self.assertTrue(result["clean_shutdown"])
        self.assertFalse(result["forced_owned_group"])

    def test_foreign_serial_is_never_sent_an_adb_kill(self):
        with (patch.object(c, "avd_name", return_value="someone-elses-avd"),
              patch.object(c, "adb") as adb, patch.object(c.lt, "terminate_owned") as terminate):
            self.process.wait.side_effect = subprocess.TimeoutExpired("owned-child", 60)
            result = c.stop_owned_emulator(self.home, self.process, "owned", True)
        adb.assert_not_called()
        terminate.assert_called_once_with(self.process)
        self.assertTrue(result["forced_owned_group"])
        self.assertIn("ownership_error", result)
        self.assertFalse(result["clean_shutdown"])

    def test_unverified_boot_only_stops_the_popen_owned_group(self):
        with (patch.object(c, "avd_name") as name, patch.object(c, "adb") as adb,
              patch.object(c.lt, "terminate_owned") as terminate):
            self.process.wait.side_effect = subprocess.TimeoutExpired("owned-child", 60)
            result = c.stop_owned_emulator(self.home, self.process, "owned", False)
        name.assert_not_called()
        adb.assert_not_called()
        terminate.assert_called_once_with(self.process)
        self.assertFalse(result["clean_shutdown"])

    def test_abnormal_or_spontaneous_exit_is_not_clean_teardown(self):
        for exited, code in ((None, 139), (0, 0)):
            with self.subTest(exited=exited, code=code):
                self.process.poll.return_value = exited
                self.process.returncode = code
                with patch.object(c, "avd_name", return_value="owned"), patch.object(c, "adb"):
                    result = c.stop_owned_emulator(self.home, self.process, "owned", True)
                self.assertFalse(result["clean_shutdown"])

    def test_ownership_readback_failure_is_not_hidden_by_native_zero_exit(self):
        with patch.object(c, "avd_name", side_effect=OSError("synthetic unavailable adb")), patch.object(c, "adb") as adb:
            result = c.stop_owned_emulator(self.home, self.process, "owned", True)
        adb.assert_not_called()
        self.assertFalse(result["clean_shutdown"])

    def test_boot_refuses_a_dead_child_or_insufficient_disk(self):
        self.process.poll.return_value = 1
        with self.assertRaises(RuntimeError):
            c.wait_for_owned_boot(self.home, self.process, "owned", Path("/synthetic"))
        self.process.poll.return_value = None
        with patch.object(c.shutil, "disk_usage", return_value=Mock(free=0)):
            with self.assertRaises(RuntimeError):
                c.wait_for_owned_boot(self.home, self.process, "owned", Path("/synthetic"))

    def test_boot_refuses_another_avd_at_the_expected_port(self):
        with (patch.object(c.shutil, "disk_usage", return_value=Mock(free=20 * 1024**3)),
              patch.object(c, "adb", return_value="1"), patch.object(c, "avd_name", return_value="foreign")):
            with self.assertRaises(ValueError):
                c.wait_for_owned_boot(self.home, self.process, "owned", Path("/synthetic"))

    def test_boot_enforcing_identity_is_not_only_a_boot_completed_string(self):
        props = {"sys.boot_completed": "1", "ro.build.version.sdk": "35",
                 "ro.build.version.release": "15", "ro.product.cpu.abi": "x86_64"}
        for security in ("Enforcing", "Permissive"):
            with (self.subTest(security=security),
                  patch.object(c.shutil, "disk_usage", return_value=Mock(free=20 * 1024**3)),
                  patch.object(c, "avd_name", return_value="owned"),
                  patch.object(c, "adb", side_effect=lambda home, *args: security if args[-1] == "getenforce" else props[args[-1]])):
                if security == "Enforcing":
                    self.assertEqual("Enforcing", c.wait_for_owned_boot(self.home, self.process, "owned", Path("/synthetic"))["selinux"])
                else:
                    with self.assertRaises(ValueError):
                        c.wait_for_owned_boot(self.home, self.process, "owned", Path("/synthetic"))

    def test_boot_timeout_is_bounded_and_does_not_select_a_fallback(self):
        with patch.object(c.time, "monotonic", side_effect=[0, 361]), patch.object(c, "adb") as adb:
            with self.assertRaises(TimeoutError):
                c.wait_for_owned_boot(self.home, self.process, "owned", Path("/synthetic"), timeout=360)
        adb.assert_not_called()


class ControllerReceipts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.relative = "build/ci-verification/synthetic-device"
        self.revision = "a" * 40
        self.context = {"source_revision": self.revision, "source_tree_dirty": False}
        self.plan = {"expected": [{"project": ":calf-io"}, {"project": ":calf-file-picker"}, {"project": ":calf-webview"}],
                     "complete_suite_requested": True, "explicit_module_subset": [],
                     "test_bearing_modules_not_requested": []}
        self.receipt = {"passed": True, "totals": {"executed": 3, "passed": 3, "failures": 0}}

    @contextmanager
    def controlled(self):
        # No command is executed; only real confined JSON files are written.
        with ExitStack() as stack:
            stack.enter_context(patch.object(c, "require_host"))
            stack.enter_context(patch.dict(c.os.environ, {"ANDROID_HOME": "/synthetic/official-sdk"}))
            stack.enter_context(patch.object(c, "sdk_assets", return_value={"system_image": c.IMAGE}))
            stack.enter_context(patch.object(c, "ensure_ports_unused"))
            adb = stack.enter_context(patch.object(c, "adb", return_value="List of devices attached"))
            stack.enter_context(patch.object(c.runtime, "capture", return_value=self.context))
            plan = stack.enter_context(patch.object(c.lt, "plan", return_value=self.plan))
            snapshots = stack.enter_context(patch.object(c.lt, "snapshot_inputs", return_value={"held.kt": "b" * 64}))
            stack.enter_context(patch.object(c.lt, "git_revision", return_value=self.revision))
            command = stack.enter_context(patch.object(c.lt, "gradle_command", return_value=["./gradlew", "--no-parallel", "io", "picker", "web"]))
            execute = stack.enter_context(patch.object(c.lt, "execute", return_value={"exit_code": 0}))
            popen = stack.enter_context(patch.object(c.subprocess, "Popen"))
            popen.return_value.pid = 123
            boot = stack.enter_context(patch.object(c, "wait_for_owned_boot", return_value={"serial": c.SERIAL, "selinux": "Enforcing"}))
            shutdown = stack.enter_context(patch.object(c, "stop_owned_emulator", return_value={"clean_shutdown": True}))
            tests = stack.enter_context(patch.object(c.lt, "run", return_value=self.receipt))
            yield {"adb": adb, "snapshots": snapshots, "execute": execute, "popen": popen,
                   "boot": boot, "shutdown": shutdown, "tests": tests, "plan": plan, "command": command}

    def invoke(self):
        result = c.run(self.root, self.relative)
        self.assertEqual(result, json.loads((self.root / self.relative / "controller.json").read_text()))
        self.assertFalse((self.root / "build/ci-verification/.android-device-controller.lock").exists())
        self.assertFalse(result["packages_published"])
        self.assertFalse(result["release_readiness_certified"])
        return result

    def test_finite_focus_reaches_both_plan_and_actual_library_execution(self):
        with self.controlled() as mocks:
            result = c.run(self.root, self.relative, only_modules=("calf-ui",),
                           focus=c.lt.DATE_TRANSACTION_FOCUS)
        self.assertTrue(result["passed"])
        self.assertEqual(c.lt.DATE_TRANSACTION_FOCUS, result["explicit_test_focus"])
        self.assertEqual(c.lt.DATE_TRANSACTION_FOCUS, mocks["plan"].call_args.kwargs["focus"])
        self.assertEqual(c.lt.DATE_TRANSACTION_FOCUS, mocks["tests"].call_args.kwargs["focus"])
        self.assertEqual(("calf-ui",), mocks["tests"].call_args.kwargs["only_modules"])

    def test_wrong_focus_fails_before_host_or_engine_setup(self):
        with patch.object(c, "require_host") as host, self.assertRaises(ValueError):
            c.run(self.root, self.relative, only_modules=("calf-webview",),
                  focus=c.lt.DATE_TRANSACTION_FOCUS)
        host.assert_not_called()

    def test_separate_geo_probe_prepares_after_owned_boot_before_native_suite_and_uninstalls_before_shutdown(self):
        self.plan.update(suite="android-device", expected=[{"project": ":calf-geo", "module": "calf-geo"}],
                         explicit_test_focus=c.lt.ANDROID_GEO_PREREQUISITES_FOCUS)
        order = []
        with self.controlled() as mocks, patch.object(c.android_geo_probe, "OwnedGeoProbe") as factory:
            probe = factory.return_value
            mocks["boot"].side_effect = lambda *args: order.append("boot") or {"serial": c.SERIAL}
            probe.prepare.side_effect = lambda: order.append("probe") or {"probe_installed": True}
            mocks["tests"].side_effect = lambda *args, **kwargs: order.append("tests") or self.receipt
            probe.close.side_effect = lambda: order.append("uninstall") or {"owned_probe_removed": True}
            mocks["shutdown"].side_effect = lambda *args: order.append("shutdown") or {"clean_shutdown": True}
            result = c.run(self.root, self.relative, only_modules=("calf-geo",), focus=c.lt.ANDROID_GEO_PREREQUISITES_FOCUS)
        self.assertEqual(["boot", "probe", "tests", "uninstall", "shutdown"], order)
        self.assertTrue(result["passed"])
        self.assertEqual(c.SERIAL, factory.call_args.args[3])
        self.assertTrue(callable(factory.call_args.args[4]))
        self.assertEqual(mocks["execute"].call_args_list[0].kwargs["env"], factory.call_args.kwargs["environment"])
        self.assertEqual((Path(self.relative) / "android-user").as_posix(), mocks["tests"].call_args.kwargs["android_user_home"])
        self.assertEqual(c.lt.ANDROID_GEO_PREREQUISITES_FOCUS, mocks["tests"].call_args.kwargs["focus"])

    def test_geo_probe_prepare_failure_has_zero_test_claims_and_still_removes_owned_app_and_emulator(self):
        self.plan.update(suite="android-device", expected=[{"project": ":calf-geo", "module": "calf-geo"}])
        with self.controlled() as mocks, patch.object(c.android_geo_probe, "OwnedGeoProbe") as factory:
            probe = factory.return_value; probe.prepare.side_effect = RuntimeError("SYNTHETIC_PRIVATE_PROBE_ERROR")
            probe.close.return_value = {"owned_probe_removed": True}
            result = self.invoke()
        self.assertFalse(result["passed"]); mocks["tests"].assert_not_called()
        probe.close.assert_called_once(); mocks["shutdown"].assert_called_once()
        self.assertNotIn("SYNTHETIC_PRIVATE_PROBE_ERROR", json.dumps(result))

    def test_geo_probe_cleanup_error_cannot_promote_native_passes_or_skip_owned_emulator_shutdown(self):
        self.plan.update(suite="android-device", expected=[{"project": ":calf-geo", "module": "calf-geo"}])
        with self.controlled() as mocks, patch.object(c.android_geo_probe, "OwnedGeoProbe") as factory:
            probe = factory.return_value; probe.prepare.return_value = {"probe_installed": True}
            probe.close.side_effect = ValueError("SYNTHETIC_PRIVATE_PROBE_ERROR")
            result = self.invoke()
        self.assertTrue(result["test_suite_passed"]); self.assertFalse(result["passed"])
        self.assertFalse(result["geo_probe"]["owned_probe_removed"])
        self.assertEqual("ValueError", result["geo_probe"]["cleanup_error"])
        mocks["shutdown"].assert_called_once(); self.assertNotIn("SYNTHETIC_PRIVATE_PROBE_ERROR", json.dumps(result))

    def test_one_failed_webview_media_focus_observes_only_owned_private_heap_and_still_runs_actual_suite(self):
        with self.controlled() as mocks, patch.object(c.android_webview_heap, "OwnedHeap") as factory:
            owner = factory.return_value
            owner.prepare.return_value = owner
            owner.close.return_value = {"clean_monitor_shutdown": True, "capture_found": False}
            result = c.run(self.root, self.relative, only_modules=("calf-webview",), focus=c.lt.WEBVIEW_ANDROID_MEDIA_FOCUS)
        self.assertTrue(result["passed"])
        owner.prepare.assert_called_once(); owner.start.assert_called_once(); owner.close.assert_called_once()
        self.assertEqual(c.SERIAL, factory.call_args.args[3])
        self.assertIs(mocks["popen"].return_value, factory.call_args.args[4])
        self.assertEqual(c.lt.WEBVIEW_ANDROID_MEDIA_FOCUS, mocks["tests"].call_args.kwargs["focus"])
        self.assertTrue(result["emulator_shutdown"]["clean_shutdown"])

    def test_heap_cleanup_error_cannot_skip_owned_emulator_shutdown_or_claim_success(self):
        with self.controlled() as mocks, patch.object(c.android_webview_heap, "OwnedHeap") as factory:
            owner = factory.return_value
            owner.prepare.return_value = owner
            owner.close.side_effect = ValueError("synthetic private failure, not exported")
            result = c.run(self.root, self.relative, only_modules=("calf-webview",), focus=c.lt.WEBVIEW_ANDROID_MEDIA_FOCUS)
        mocks["shutdown"].assert_called_once()
        self.assertTrue(result["emulator_shutdown"]["clean_shutdown"])
        self.assertFalse(result["passed"])
        self.assertEqual("ValueError", result["heap_diagnostics"]["capture_error"])
        self.assertNotIn("synthetic private failure", json.dumps(result))

    def test_setup_is_serial_and_owned_environment_does_not_mutate_parent(self):
        with self.controlled() as mocks:
            before = os.environ.copy()
            result = self.invoke()
            self.assertEqual(before, dict(os.environ))
        self.assertTrue(result["passed"])
        calls = mocks["execute"].call_args_list
        self.assertEqual(2, len(calls))
        self.assertEqual([":calf-io:assembleAndroidDeviceTest", ":calf-file-picker:assembleAndroidDeviceTest",
                          ":calf-webview:assembleAndroidDeviceTest"], calls[0].args[1][-3:])
        self.assertEqual(c.SERIAL, calls[0].kwargs["env"]["ANDROID_SERIAL"])
        self.assertTrue(Path(calls[1].kwargs["env"]["ANDROID_AVD_HOME"]).is_relative_to(self.root / self.relative))
        mocks["tests"].assert_called_once()
        self.assertEqual(c.SERIAL, mocks["tests"].call_args.kwargs["android_serial"])
        self.assertTrue(mocks["popen"].call_args.kwargs["start_new_session"])
        self.assertIn("-accel", mocks["popen"].call_args.args[0])
        self.assertNotIn("-selinux", mocks["popen"].call_args.args[0])

    def test_camera_minimum_uses_official_device_id_and_creates_owned_avd_before_compilation(self):
        self.plan.update(suite="android-device", expected=[{"project": ":calf-camera-picker", "module": "calf-camera-picker"}],
                         explicit_test_focus=c.lt.ANDROID_CAMERA_PROVIDER_FOCUS)
        with self.controlled() as mocks, patch.object(c.android_camera_receiver, "OwnedCameraReceiver") as factory, \
                patch.object(c.android_camera_receiver, "archive_focused_reports", return_value={}):
            factory.return_value.close.return_value = {"owned_recipient_removed": True}
            result = c.run(self.root, self.relative, only_modules=("calf-camera-picker",),
                           focus=c.lt.ANDROID_CAMERA_PROVIDER_FOCUS, api_level=23)
        self.assertTrue(result["passed"])
        plan = json.loads((self.root / self.relative / "plan.json").read_text())
        self.assertEqual(["--device", "Nexus 5", "--force"], plan["create_avd_command"][-3:])
        calls = mocks["execute"].call_args_list
        self.assertEqual(2, len(calls))
        self.assertEqual(plan["create_avd_command"], calls[0].args[1])
        self.assertEqual(":calf-camera-picker:assembleAndroidDeviceTest", calls[1].args[1][-1])
        self.assertEqual(c.SERIAL, calls[0].kwargs["env"]["ANDROID_SERIAL"])
        self.assertEqual(c.SERIAL, calls[1].kwargs["env"]["ANDROID_SERIAL"])
        self.assertEqual(23, factory.call_args.kwargs["api_level"])

    def test_camera_failed_prepare_and_cleanup_preserve_partial_installer_receipt_and_safe_source_origins(self):
        self.plan.update(suite="android-device", expected=[{"project": ":calf-camera-picker", "module": "calf-camera-picker"}],
                         explicit_test_focus=c.lt.ANDROID_CAMERA_PROVIDER_FOCUS)
        partial = {"assembly": {"exit_code": 0}, "source_apk_sha256": "b" * 64, "source_apk_bytes": 123,
                   "install_exit_code": 0, "recipient_installed": False, "owned_recipient_removed": False,
                   "prepare_status": "failed", "prepare_error": "ValueError", "cleanup_status": "failed", "cleanup_error": "ValueError"}
        with self.controlled() as mocks, patch.object(c.android_camera_receiver, "OwnedCameraReceiver") as factory:
            owner = factory.return_value; owner.receipt = partial
            owner.prepare.side_effect = ValueError("PRIVATE_PREPARE_BODY")
            owner.close.side_effect = ValueError("PRIVATE_CLEANUP_BODY")
            result = c.run(self.root, self.relative, only_modules=("calf-camera-picker",), focus=c.lt.ANDROID_CAMERA_PROVIDER_FOCUS, api_level=23)
        self.assertFalse(result["passed"]); mocks["tests"].assert_not_called(); mocks["shutdown"].assert_called_once()
        self.assertEqual(partial, result["camera_receiver"])
        self.assertEqual({"source", "symbol", "line"}, set(result["controller_error_origin"]))
        self.assertEqual({"source", "symbol", "line"}, set(result["camera_receiver_cleanup_error_origin"]))
        self.assertNotIn("PRIVATE_", json.dumps(result))

    def test_camera_avd_refusal_never_starts_compilation_receiver_emulator_or_native_suite(self):
        self.plan.update(suite="android-device", expected=[{"project": ":calf-camera-picker", "module": "calf-camera-picker"}],
                         explicit_test_focus=c.lt.ANDROID_CAMERA_PROVIDER_FOCUS)
        with self.controlled() as mocks, patch.object(c.android_camera_receiver, "OwnedCameraReceiver") as factory:
            mocks["execute"].return_value = {"exit_code": 1}
            result = c.run(self.root, self.relative, only_modules=("calf-camera-picker",),
                           focus=c.lt.ANDROID_CAMERA_PROVIDER_FOCUS, api_level=23)
        self.assertFalse(result["passed"])
        self.assertEqual({"owned-avd-create"}, set(result["setup_stages"]))
        mocks["execute"].assert_called_once()
        self.assertIn("avdmanager", mocks["execute"].call_args.args[1][0])
        mocks["popen"].assert_not_called()
        mocks["tests"].assert_not_called()
        factory.assert_not_called()

    def test_explicit_subset_is_identical_for_assembly_discovery_execution_and_receipts(self):
        self.plan = {"expected": [{"project": ":calf-webview"}], "complete_suite_requested": False,
                     "explicit_module_subset": ["calf-webview"],
                     "test_bearing_modules_not_requested": ["calf-file-picker", "calf-io"]}
        with self.controlled() as mocks:
            mocks["command"].return_value = ["./gradlew", "--no-parallel", ":calf-webview:connectedAndroidDeviceTest"]
            result = c.run(self.root, self.relative, only_modules=("calf-webview",))
        mocks["plan"].assert_called_once_with(self.root, "android-device", only_modules=("calf-webview",))
        self.assertEqual(["./gradlew", "--no-parallel", ":calf-webview:assembleAndroidDeviceTest"],
                         mocks["execute"].call_args_list[0].args[1])
        self.assertEqual(("calf-webview",), mocks["tests"].call_args.kwargs["only_modules"])
        stored = json.loads((self.root / self.relative / "plan.json").read_text())
        self.assertEqual(self.plan, stored["source_suite"])
        self.assertFalse(result["complete_suite_requested"])
        self.assertEqual(["calf-webview"], result["explicit_module_subset"])
        self.assertEqual(["calf-file-picker", "calf-io"], result["test_bearing_modules_not_requested"])
        self.assertTrue(result["passed"], "A scoped pass must not be mislabeled complete coverage")

    def test_invalid_source_subset_cannot_start_gradle_or_emulator_and_releases_owned_lock(self):
        with self.controlled() as mocks:
            mocks["plan"].side_effect = ValueError("invalid authored-device module selection")
            with self.assertRaises(ValueError):
                c.run(self.root, self.relative, only_modules=("calf-missing",))
        mocks["execute"].assert_not_called()
        mocks["popen"].assert_not_called()
        mocks["tests"].assert_not_called()
        self.assertFalse((self.root / self.relative).exists())
        self.assertFalse((self.root / "build/ci-verification/.android-device-controller.lock").exists())

    def test_default_controller_still_requests_the_complete_device_suite(self):
        with self.controlled() as mocks:
            result = self.invoke()
        mocks["plan"].assert_called_once_with(self.root, "android-device", only_modules=None)
        self.assertIsNone(mocks["tests"].call_args.kwargs["only_modules"])
        self.assertTrue(result["complete_suite_requested"])
        self.assertEqual([], result["explicit_module_subset"])

    def test_each_setup_failure_has_zero_test_claims_and_never_launches_an_engine(self):
        for stage in (0, 1):
            with self.subTest(stage=stage):
                relative = f"build/ci-verification/setup-{stage}"
                self.relative = relative
                with self.controlled() as mocks:
                    mocks["execute"].side_effect = [{"exit_code": 0}] * stage + [{"exit_code": 1}]
                    result = self.invoke()
                self.assertFalse(result["passed"])
                self.assertFalse(result["test_suite_passed"])
                self.assertNotIn("test_totals", result)
                mocks["popen"].assert_not_called()
                mocks["tests"].assert_not_called()
                mocks["shutdown"].assert_not_called()

    def test_failed_boot_is_recorded_and_only_unverified_owned_child_is_stopped(self):
        with self.controlled() as mocks:
            mocks["boot"].side_effect = TimeoutError("synthetic boot failure")
            result = self.invoke()
        self.assertFalse(result["passed"])
        self.assertEqual("TimeoutError", result["controller_error"])
        self.assertIs(mocks["shutdown"].call_args.args[-1], False)
        mocks["tests"].assert_not_called()

    def test_native_test_failure_is_preserved_while_verified_owned_engine_is_stopped(self):
        with self.controlled() as mocks:
            mocks["tests"].return_value = {"passed": False, "totals": {"executed": 3, "passed": 2, "failures": 1}}
            result = self.invoke()
        self.assertFalse(result["passed"])
        self.assertEqual(1, result["test_totals"]["failures"])
        self.assertIs(mocks["shutdown"].call_args.args[-1], True)

    def test_engine_teardown_failure_cannot_be_overridden_by_passing_test_cases(self):
        with self.controlled() as mocks:
            mocks["shutdown"].return_value = {"clean_shutdown": False, "exit_code": 139}
            result = self.invoke()
        self.assertTrue(result["test_suite_passed"])
        self.assertFalse(result["passed"])

    def test_engine_cleanup_exception_still_writes_a_failed_controller_receipt(self):
        with self.controlled() as mocks:
            mocks["shutdown"].side_effect = OSError("synthetic cleanup failure")
            result = self.invoke()
        self.assertFalse(result["passed"])
        self.assertTrue(result["emulator_shutdown"]["controller_cleanup_error"])

    def test_source_changes_and_new_inputs_cannot_be_labeled_verified(self):
        with self.controlled() as mocks:
            mocks["snapshots"].side_effect = [{"held.kt": "b" * 64}, {"held.kt": "c" * 64, "new.kt": "d" * 64}]
            result = self.invoke()
        self.assertEqual(["held.kt", "new.kt"], result["changed_inputs"])
        self.assertFalse(result["source_unchanged"])
        self.assertFalse(result["passed"])

    def test_interrupted_tests_still_stop_the_owned_engine_and_keep_evidence(self):
        with self.controlled() as mocks:
            mocks["tests"].side_effect = KeyboardInterrupt()
            result = self.invoke()
        mocks["shutdown"].assert_called_once()
        self.assertFalse(result["passed"])
        self.assertEqual("KeyboardInterrupt", result["controller_error"])

    def test_any_existing_device_refuses_setup_without_exporting_personal_serials(self):
        with self.controlled() as mocks:
            mocks["adb"].return_value = "List of devices attached\nPERSONAL-SERIAL\tdevice"
            with self.assertRaises(ValueError) as caught:
                c.run(self.root, self.relative)
        self.assertNotIn("PERSONAL", str(caught.exception))
        mocks["execute"].assert_not_called()
        mocks["popen"].assert_not_called()
        self.assertFalse((self.root / self.relative).exists())

    def test_existing_lock_output_and_path_escape_do_not_mutate_other_owners(self):
        base = self.root / "build/ci-verification"
        base.mkdir(parents=True)
        lock = base / ".android-device-controller.lock"
        lock.write_text("unrelated-owner")
        with patch.object(c, "require_host"):
            with self.assertRaises(FileExistsError):
                c.run(self.root, self.relative)
            self.assertEqual("unrelated-owner", lock.read_text())
            for relative in ("build/ci-verification", "build/ci-verification/../other", "/tmp/escape"):
                with self.subTest(relative=relative), self.assertRaises(ValueError):
                    c.run(self.root, relative)


if __name__ == "__main__":
    unittest.main()
