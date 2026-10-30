"""Synthetic exact-plan/engine/archive guards only. No Android/native or release outcomes."""
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import time
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch, Mock

import library_tests as l
import android_device_tests as device
import android_camera_receiver as receiver
import android_geo_probe as geo
import workflow_matrix as w


class CameraMinimumInstallerTests(unittest.TestCase):
    """Real bounded host pipes with synthetic bytes, never Android/APK evidence."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / "build/ci-verification/minimum-installer"; self.output.mkdir(parents=True)
        self.env = {"ANDROID_SERIAL": "emulator-5588", "ANDROID_USER_HOME": str(self.output / "android-user"),
                    "PRIVATE_SYNTHETIC_SIGNING": "never-export-this"}
        self.arguments = (self.root, self.output, Path("/synthetic/sdk"), "emulator-5588", lambda: True)
        self.owner = receiver.OwnedCameraReceiver(*self.arguments, environment=self.env, api_level=23)
        self.native_path = "/data/app/owned.receiver-1/base.apk"

    def result(self, code=0, body=b"", error=b""):
        return subprocess.CompletedProcess([], code, body, error)

    @contextmanager
    def stream(self, script):
        real_popen = subprocess.Popen; children = []
        def launch(command, **options):
            child = real_popen([sys.executable, "-c", script], **options); children.append(child)
            return child
        with patch.object(receiver.subprocess, "Popen", side_effect=launch) as start:
            try: yield start, children
            finally:
                for child in children:
                    if child.poll() is None: child.kill(); child.wait(timeout=5)
                    for pipe in (child.stdout, child.stderr):
                        if pipe is not None: pipe.close()

    def apk(self):
        base = self.root / self.owner.FIXTURE / "build/outputs/apk/debug"; base.mkdir(parents=True)
        apk = base / "camera-debug.apk"; apk.write_bytes(b"synthetic-not-native-APK")
        (base / "output-metadata.json").write_text(json.dumps({"applicationId": self.owner.PACKAGE, "variantName": "debug",
            "artifactType": {"type": "APK"}, "elements": [{"type": "SINGLE", "filters": [], "outputFile": apk.name}]}))
        return apk

    def test_api23_hashes_exact_validated_installed_bytes_through_bounded_owned_host_pipes(self):
        payload = b"PRIVATE_SYNTHETIC_BYTES\x00\xff" * 20000
        with patch.object(self.owner, "control", return_value=self.result(body=("package:" + self.native_path + "\n").encode())) as control, \
                self.stream("import sys; sys.stdout.buffer.write(b'PRIVATE_SYNTHETIC_BYTES\\x00\\xff' * 20000)") as (start, children):
            actual = self.owner.readback()
            self.assertTrue(all(pipe.closed for child in children for pipe in (child.stdout, child.stderr)))
            self.assertTrue(all(child.poll() == 0 for child in children))
        self.assertEqual(("shell", "pm", "path", self.owner.PACKAGE), control.call_args.args)
        self.assertEqual(["/synthetic/sdk/platform-tools/adb", "-s", "emulator-5588", "exec-out", "cat", self.native_path], start.call_args.args[0])
        self.assertTrue(start.call_args.kwargs["start_new_session"])
        self.assertEqual(hashlib.sha256(payload).hexdigest(), actual["apk_sha256"])
        self.assertEqual(len(payload), actual["apk_bytes"])
        self.assertEqual("adb-exec-out-cat-host-SHA256", actual["byte_read_mechanism"])
        self.assertEqual(23, actual["api_level"]); self.assertFalse(actual["raw_path_uploaded"])
        self.assertNotIn("PRIVATE_SYNTHETIC", json.dumps(actual)); self.assertNotIn(self.native_path, json.dumps(actual))

    def test_api35_keeps_existing_native_checksum_identity_without_stream_or_fallback(self):
        output = self.root / "build/ci-verification/api35"; output.mkdir()
        env = self.env | {"ANDROID_USER_HOME": str(output / "android-user")}
        owner = receiver.OwnedCameraReceiver(self.root, output, Path("/synthetic/sdk"), "emulator-5588", lambda: True, environment=env)
        with patch.object(owner, "control", side_effect=[self.result(body=("package:" + self.native_path).encode()),
                self.result(body=("a" * 64 + "  " + self.native_path + "\n").encode())]) as control, \
                patch.object(receiver.subprocess, "Popen") as start:
            actual = owner.readback()
        self.assertEqual({"apk_sha256": "a" * 64, "exact_one_APK_path_observed": True, "raw_path_uploaded": False}, actual)
        self.assertEqual(("shell", "sha256sum", self.native_path), control.call_args.args); start.assert_not_called()

    def test_invalid_minimum_API_is_rejected_before_creating_any_owned_output(self):
        for api in (22, 24, 34, "23", True, None):
            with self.subTest(api=api), self.assertRaises(ValueError):
                receiver.OwnedCameraReceiver(*self.arguments, environment=self.env, api_level=api)

    def test_absent_or_invalid_package_paths_never_start_a_byte_reader(self):
        with patch.object(receiver.subprocess, "Popen") as start:
            with patch.object(self.owner, "control", return_value=self.result()): self.assertIsNone(self.owner.readback())
            for value in (b"package:/data/app/../other/base.apk", b"package:/data/app/p/base.apk\npackage:/data/app/q/base.apk",
                          b"package:/sdcard/p/base.apk", b"package:/data/app/p/base.apk;evil"):
                with self.subTest(value=value), patch.object(self.owner, "control", return_value=self.result(body=value)), self.assertRaises(ValueError):
                    self.owner.readback()
        start.assert_not_called()

    def test_empty_error_nonzero_or_oversized_streams_are_refused_without_hash_success(self):
        scripts = ("pass", "import sys; sys.stdout.buffer.write(b'123'); sys.stderr.write('private-error')",
                   "import sys; sys.stdout.buffer.write(b'123'); sys.exit(1)", "import sys; sys.stdout.buffer.write(b'123456789')",
                   "import sys; sys.stderr.buffer.write(b'x' * 65537)")
        for script in scripts:
            with self.subTest(script=script), patch.object(self.owner, "control", return_value=self.result(body=("package:" + self.native_path).encode())), \
                    patch.object(receiver, "MAX_INSTALLED_APK_BYTES", 8), self.stream(script) as (_, children):
                with self.assertRaises(ValueError): self.owner.readback()
                self.assertTrue(all(child.poll() is not None for child in children))
                self.assertTrue(all(pipe.closed for child in children for pipe in (child.stdout, child.stderr)))

    def test_byte_read_timeout_terminates_only_owned_child_and_closes_pipes(self):
        with patch.object(self.owner, "control", return_value=self.result(body=("package:" + self.native_path).encode())), \
                patch.object(receiver, "INSTALLED_APK_TIMEOUT_SECONDS", 0.05), self.stream("import time; time.sleep(20)") as (_, children):
            with self.assertRaises(TimeoutError): self.owner.readback()
            self.assertTrue(all(child.poll() is not None for child in children))
            self.assertTrue(all(pipe.closed for child in children for pipe in (child.stdout, child.stderr)))

    def test_lost_lease_before_or_after_byte_read_never_certifies_identity(self):
        self.owner.is_owned = lambda: False
        with patch.object(receiver.subprocess, "Popen") as start, self.assertRaises(ValueError): self.owner.readback()
        start.assert_not_called()
        self.owner.is_owned = Mock(side_effect=[True, False])
        with patch.object(self.owner, "control", return_value=self.result(body=("package:" + self.native_path).encode())), \
                self.stream("import sys; sys.stdout.buffer.write(b'123')"), self.assertRaises(ValueError): self.owner.readback()

    def test_failed_post_install_readback_preserves_assembly_source_bytes_install_exit_and_private_safe_failure(self):
        apk = self.apk()
        with patch.object(self.owner, "readback", side_effect=[None, ValueError("PRIVATE_READBACK_FAILURE")]), \
                patch.object(l, "execute", return_value={"exit_code": 0}), \
                patch.object(self.owner, "control", return_value=self.result(body=b"Success\n")) as control:
            with self.assertRaises(ValueError): self.owner.prepare()
        partial = json.loads((self.owner.output / "receipt.json").read_text())
        self.assertEqual(0, partial["assembly"]["exit_code"]); self.assertEqual(l.sha256(apk), partial["source_apk_sha256"])
        self.assertEqual(apk.stat().st_size, partial["source_apk_bytes"]); self.assertEqual(0, partial["install_exit_code"])
        self.assertEqual("failed", partial["prepare_status"]); self.assertEqual("ValueError", partial["prepare_error"])
        self.assertFalse(partial["recipient_installed"]); self.assertFalse(partial["owned_recipient_removed"])
        self.assertFalse(partial["automatic_runtime_permission_grant"])
        self.assertEqual(1, control.call_count); self.assertNotIn("PRIVATE_", json.dumps(partial)); self.assertNotIn("never-export-this", json.dumps(partial))

    def test_cleanup_readback_failure_preserves_original_facts_without_foreign_stop_uninstall_or_success(self):
        self.owner.install_attempted = True; self.owner.digest = "a" * 64
        self.owner.receipt.update(source_apk_sha256="a" * 64, source_apk_bytes=123, recipient_installed=True)
        with patch.object(self.owner, "readback", side_effect=ValueError("PRIVATE_CLEANUP_ERROR")), \
                patch.object(self.owner, "control") as control, self.assertRaises(ValueError): self.owner.close()
        control.assert_not_called()
        partial = json.loads((self.owner.output / "receipt.json").read_text())
        self.assertEqual("a" * 64, partial["source_apk_sha256"]); self.assertTrue(partial["recipient_installed"])
        self.assertEqual("failed", partial["cleanup_status"]); self.assertEqual("ValueError", partial["cleanup_error"])
        self.assertFalse(partial["owned_recipient_removed"]); self.assertNotIn("PRIVATE_", json.dumps(partial))

    def test_cleanup_after_uncertain_uninstall_preserves_exact_pre_cleanup_identity_and_exit_codes(self):
        self.owner.install_attempted = True; self.owner.digest = "a" * 64
        with patch.object(self.owner, "readback", side_effect=[{"apk_sha256": "a" * 64}, ValueError("PRIVATE_POST_UNINSTALL_ERROR")]), \
                patch.object(self.owner, "control", return_value=self.result()) as control, self.assertRaises(ValueError): self.owner.close()
        partial = json.loads((self.owner.output / "receipt.json").read_text())
        self.assertTrue(partial["owned_identity_reverified"]); self.assertEqual(0, partial["stop_exit_code"])
        self.assertEqual(0, partial["uninstall_exit_code"]); self.assertFalse(partial["owned_recipient_removed"])
        self.assertEqual(2, control.call_count); self.assertNotIn("PRIVATE_", json.dumps(partial))

    def test_readback_error_origin_names_own_public_source_without_exception_or_raw_path(self):
        output = self.root / "build/ci-verification/origin"; output.mkdir()
        owner = receiver.OwnedCameraReceiver(self.root, output, Path("/synthetic/sdk"), "emulator-5588", lambda: True,
            environment=self.env | {"ANDROID_USER_HOME": str(output / "android-user")})
        with patch.object(owner, "control", side_effect=[self.result(body=("package:" + self.native_path).encode()), self.result(1, error=b"PRIVATE_NATIVE_ERROR")]):
            try: owner.readback()
            except ValueError as error: origin = device.preflight_error_origin(error)
        self.assertEqual("android_share_recipient.py", origin["source"]); self.assertEqual("readback", origin["symbol"])
        self.assertGreater(origin["line"], 0); self.assertNotIn("PRIVATE_", json.dumps(origin)); self.assertNotIn(str(l.ROOT), json.dumps(origin))

    def test_API23_known_source_length_mismatch_never_certifies_installed_identity(self):
        self.owner.digest = hashlib.sha256(b"123").hexdigest(); self.owner.receipt["source_apk_bytes"] = 4
        with patch.object(self.owner, "control", return_value=self.result(body=("package:" + self.native_path).encode())), \
                self.stream("import sys; sys.stdout.buffer.write(b'123')"), self.assertRaises(ValueError): self.owner.readback()

    def test_api35_native_failure_remains_failed_without_automatic_legacy_reader(self):
        output = self.root / "build/ci-verification/modern-failure"; output.mkdir()
        owner = receiver.OwnedCameraReceiver(self.root, output, Path("/synthetic/sdk"), "emulator-5588", lambda: True,
            environment=self.env | {"ANDROID_USER_HOME": str(output / "android-user")})
        with patch.object(owner, "control", side_effect=[self.result(body=("package:" + self.native_path).encode()), self.result(1, error=b"PRIVATE_NATIVE_ERROR")]), \
                patch.object(receiver.subprocess, "Popen") as start, self.assertRaises(ValueError): owner.readback()
        start.assert_not_called()

    def test_lookalike_external_source_name_is_not_accepted_as_public_failure_origin(self):
        try:
            exec(compile("raise ValueError('PRIVATE_EXTERNAL_BODY')", "/unrelated-private/android_share_recipient.py", "exec"))
        except ValueError as error:
            origin = device.preflight_error_origin(error)
        self.assertEqual({"source": "unavailable", "symbol": "unavailable", "line": 0}, origin)
        self.assertNotIn("PRIVATE_", json.dumps(origin)); self.assertNotIn("unrelated-private", json.dumps(origin))

    def test_API23_rejected_path_preserves_shape_not_private_console_or_raw_installed_name(self):
        output = b'WARNING: linker: PRIVATE_TEXT unused DT entry: type 0x1d arg 0x123\r\npackage:' + self.native_path.encode() + b'\r\n'
        with patch.object(self.owner, "control", return_value=self.result(body=output)), \
                patch.object(receiver.subprocess, "Popen") as start, self.assertRaises(ValueError): self.owner.readback()
        start.assert_not_called()
        item, = self.owner.receipt["package_path_observations"]
        self.assertEqual(0, item["response_exit_code"]); self.assertEqual(2, item["stdout_line_count"])
        self.assertEqual(["linker-unused-DT-entry", "package-path"], [row["kind"] for row in item["lines"]])
        self.assertEqual(hashlib.sha256(output).hexdigest(), item["stdout_sha256"])
        self.assertEqual(0, item["stderr_bytes"]); self.assertNotIn("PRIVATE_", json.dumps(item)); self.assertNotIn(self.native_path, json.dumps(item))

    def test_path_observation_classification_does_not_accept_SELinux_errors_duplicates_or_unknown_text(self):
        body = (b'avc: denied PRIVATE_TEXT\npackage:' + self.native_path.encode() + b'\npackage:' + self.native_path.encode() + b'\n')
        result = receiver.package_path_shape(self.result(body=body))
        self.assertEqual(["SELinux-diagnostic", "package-path", "package-path"], [row["kind"] for row in result["lines"]])
        self.assertFalse(result["path_or_install_identity_accepted"])
        self.assertNotIn("PRIVATE_", json.dumps(result)); self.assertNotIn(self.native_path, json.dumps(result))


class CameraProviderPlanTests(unittest.TestCase):
    def plan(self): return l.plan(l.ROOT, "android-device", only_modules=("calf-camera-picker",), focus=l.ANDROID_CAMERA_PROVIDER_FOCUS)

    def test_exact_four_methods_and_two_serial_real_api_plans_preserve_all_prior_slots(self):
        row, = w.matrix("android-camera-provider")["include"]
        self.assertEqual(("android-device-api35", "android-device", "calf-camera-picker", "35", "23", l.ANDROID_CAMERA_PROVIDER_FOCUS),
                         tuple(row[k] for k in ("slot", "suite", "test-modules", "emulator-api", "serial-emulator-api", "test-focus")))
        p = self.plan(); self.assertTrue(l.validate_test_focus(p)); self.assertTrue(l.android_camera_receiver_required(p))
        self.assertFalse(p["complete_suite_requested"]); self.assertEqual(4, len(p["expected"][0]["required_testcases"]))
        self.assertEqual(11, len(w.matrix("all")["include"])); self.assertEqual(8, len(l.plan(l.ROOT, "android-device")["expected"]))
        actual = w.preflight_plans("android-camera-provider")
        self.assertEqual(2, len(actual["slots"]))
        for api, selection in zip(("35", "23"), actual["slots"]):
            self.assertEqual(api, selection["command"][selection["command"].index("--api-level") + 1])
            self.assertEqual(0, selection["exit_code"])

    def test_one_class_no_ate_comma_or_foreign_marker_requires_only_owned_camera_receiver(self):
        c = l.gradle_command("android-device", self.plan(), android_serial="emulator-5588")
        self.assertEqual(1, c.count("-Pandroid.testInstrumentationRunnerArguments.nativecmpkitOwnedCameraReceiver=true"))
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.class=" + l.ANDROID_CAMERA_PROVIDER_CLASS, c)
        self.assertFalse(any("," in x for x in c if x.startswith("-Pandroid.testInstrumentationRunnerArguments.")))
        self.assertFalse(any("OwnedShare" in x or "OwnedGeo" in x for x in c))
        self.assertEqual(":calf-camera-picker:connectedAndroidDeviceTest", c[-1])

    def test_minimum_only_recovery_selects_api23_and_never_replays_accepted_api35(self):
        row, = w.matrix("android-camera-provider-minimum")["include"]
        self.assertEqual(("android-device-api23-camera", "android-device", "23", "calf-camera-picker", l.ANDROID_CAMERA_PROVIDER_FOCUS),
                         tuple(row[k] for k in ("slot", "suite", "emulator-api", "test-modules", "test-focus")))
        self.assertNotIn("serial-emulator-api", row)
        receipt = w.preflight_plans("android-camera-provider-minimum")
        item, = receipt["slots"]
        self.assertEqual("23", item["command"][item["command"].index("--api-level")+1])
        self.assertEqual(0, item["exit_code"])
        self.assertEqual(11, len(w.matrix("all")["include"]))

    def test_no_handler_recovery_selects_only_failed_native_method_on_minimum_api(self):
        row, = w.matrix("android-camera-no-handler-minimum")["include"]
        self.assertEqual(("android-device-api23-camera", "23", "calf-camera-picker", l.ANDROID_CAMERA_NO_HANDLER_FOCUS),
                         tuple(row[k] for k in ("slot", "emulator-api", "test-modules", "test-focus")))
        self.assertNotIn("serial-emulator-api", row)
        plan = l.plan(l.ROOT, "android-device", only_modules=("calf-camera-picker",), focus=l.ANDROID_CAMERA_NO_HANDLER_FOCUS)
        expected, = plan["expected"]
        self.assertEqual(l.android_camera_provider_identities()[-1:], expected["required_testcases"])
        self.assertEqual(l.ANDROID_CAMERA_PROVIDER_CLASS + "#" + l.ANDROID_CAMERA_PROVIDER_METHODS[-1], expected["test_filter"])
        self.assertTrue(l.validate_test_focus(plan)); self.assertTrue(l.android_camera_receiver_required(plan))
        self.assertEqual(0, w.preflight_plans("android-camera-no-handler-minimum")["slots"][0]["exit_code"])
        self.assertEqual(11, len(w.matrix("all")["include"])); self.assertEqual(8, len(l.MINIMUM_MODULES["android-device"]))
        command = l.gradle_command("android-device", plan, android_serial="emulator-5588")
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.class=" + expected["test_filter"], command)
        self.assertFalse(any("," in arg for arg in command if arg.startswith("-Pandroid.testInstrumentationRunnerArguments.")))
        for filter_ in (l.ANDROID_CAMERA_PROVIDER_CLASS, expected["test_filter"] + ",other", "Foreign#method"):
            bad = deepcopy(plan); bad["expected"][0]["test_filter"] = filter_
            with self.assertRaises(ValueError): l.validate_test_focus(bad)

    def test_recovery_xml_never_counts_replayed_passes_or_missing_failed_skipped_case(self):
        plan = l.plan(l.ROOT, "android-device", only_modules=("calf-camera-picker",), focus=l.ANDROID_CAMERA_NO_HANDLER_FOCUS)
        expected, = plan["expected"]; cases = expected["required_testcases"]
        variants = [cases, [], l.android_camera_provider_identities(), cases * 2,
                    [cases[0] | {"outcome": "<failure/>"}], [cases[0] | {"outcome": "<skipped/>"}]]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); report = root / expected["report_directory"] / "TEST-synthetic.xml"; report.parent.mkdir(parents=True)
            for variant in variants:
                report.write_text("<testsuite>" + "".join('<testcase classname="' + c["classname"] + '" name="' + c["name"] + '">' + c.get("outcome", "") + '</testcase>' for c in variant) + "</testsuite>")
                now = time.time_ns()
                result = l.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000, Counter({expected["task"]: 1}))
                self.assertEqual(variant != cases, bool(result["errors"]))

    def test_legacy_default_restore_checks_actual_binder_signature_and_preserves_errors(self):
        # Source guard only; actual shell UID/Binder restoration needs the native test.
        source = (l.ROOT / l.ANDROID_CAMERA_PROVIDER_SOURCE).read_text()
        self.assertIn('private fun restoreLegacyDefaultCameraPackage', source)
        self.assertIn('Build.VERSION.SDK_INT == 23 && original == PackageManager.COMPONENT_ENABLED_STATE_DEFAULT', source)
        self.assertIn('TRANSACTION_setApplicationEnabledSetting', source)
        self.assertIn('setApplicationEnabledSetting', source)
        self.assertIn('check(method.returnType == Void.TYPE)', source)
        self.assertIn('service call package $transaction s16 $packageName i32 0 i32 0 i32 0 s16 shell:2000', source)
        self.assertIn('pm.getApplicationEnabledSetting(packageName)', source)
        self.assertIn('primary.addSuppressed', source)
        self.assertIn('cleanupFailure?.let { throw it }', source)

    def test_preflight_origin_reports_only_exact_public_source_symbol_and_line(self):
        try:
            device.validate_api_selection(24, ("calf-camera-picker",), l.ANDROID_CAMERA_PROVIDER_FOCUS)
        except ValueError as error:
            error.args = ("PRIVATE_ERROR_TEXT_NOT_FOR_RECEIPT",)
            origin = device.preflight_error_origin(error)
        self.assertEqual("android_device_tests.py", origin["source"])
        self.assertEqual("validate_api_selection", origin["symbol"])
        self.assertGreater(origin["line"], 0)
        self.assertNotIn("PRIVATE_ERROR", json.dumps(origin))
        self.assertNotIn(str(l.ROOT), json.dumps(origin))

    def test_api23_never_escapes_exact_camera_focus_and_default_api35_stays_available(self):
        device.validate_api_selection(35, None, None)
        device.validate_api_selection(23, ("calf-camera-picker",), l.ANDROID_CAMERA_PROVIDER_FOCUS)
        for api, modules, focus in [(23, None, None), (23, ("calf-io",), l.ANDROID_CAMERA_PROVIDER_FOCUS),
                                    (23, ("calf-camera-picker",), None), (24, ("calf-camera-picker",), l.ANDROID_CAMERA_PROVIDER_FOCUS),
                                    (23, ("calf-camera-picker", "calf-io"), l.ANDROID_CAMERA_PROVIDER_FOCUS)]:
            with self.assertRaises(ValueError): device.validate_api_selection(api, modules, focus)
        for api in (23, 35):
            args = ["android_device_tests.py", "plan", "--api-level", str(api), "--module", "calf-camera-picker", "--focus", l.ANDROID_CAMERA_PROVIDER_FOCUS, "--output", "build/ci-plan"]
            output = io.StringIO()
            with patch("sys.argv", args), patch("sys.stdout", output): self.assertEqual(0, device.main())
            self.assertEqual(self.plan(), json.loads(output.getvalue()))

    def test_api23_boot_requires_actual_enforcing_23_not_selected_label_or_35_fallback(self):
        process = Mock(); process.poll.return_value = None
        for api, security in (("23", "Enforcing"), ("35", "Enforcing"), ("23", "Permissive")):
            props = {"sys.boot_completed": "1", "ro.build.version.sdk": api, "ro.build.version.release": "6.0", "ro.product.cpu.abi": "x86_64"}
            with patch.object(device.shutil, "disk_usage", return_value=Mock(free=20 * 1024**3)), \
                 patch.object(device, "avd_name", return_value="owned"), \
                 patch.object(device, "adb", side_effect=lambda home, *args: security if args[-1] == "getenforce" else props[args[-1]]):
                if api == "23" and security == "Enforcing":
                    self.assertEqual("23", device.wait_for_owned_boot(Path("/synthetic/sdk"), process, "owned", Path("/synthetic"), api_level=23)["api_level"])
                else:
                    with self.assertRaises(ValueError): device.wait_for_owned_boot(Path("/synthetic/sdk"), process, "owned", Path("/synthetic"), api_level=23)

    def test_exact_four_fresh_cases_reject_missing_duplicate_extra_fail_skip_and_stale_task(self):
        plan = self.plan(); expected = plan["expected"][0]; cases = expected["required_testcases"]
        variants = [cases, cases[:2], cases + cases[:1], cases + [{"classname": "Foreign", "name": "extra"}],
                    [cases[0] | {"outcome": "<failure/>"}, *cases[1:]], [cases[0] | {"outcome": "<skipped/>"}, *cases[1:]]]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); report = root / expected["report_directory"] / "TEST-synthetic.xml"; report.parent.mkdir(parents=True)
            for variant in variants:
                report.write_text("<testsuite>" + "".join('<testcase classname="' + c["classname"] + '" name="' + c["name"] + '">' + c.get("outcome", "") + '</testcase>' for c in variant) + "</testsuite>")
                now = time.time_ns()
                result = l.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000, Counter({expected["task"]: 1}))
                self.assertEqual(variant != cases, bool(result["errors"]))
            self.assertTrue(l.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000, Counter())["errors"])
            self.assertTrue(l.collect_reports(root, plan, now + 10_000_000_000, now + 11_000_000_000, Counter({expected["task"]: 1}))["errors"])
        altered = deepcopy(plan); altered["expected"][0]["test_filter"] = "Foreign"
        with self.assertRaises(ValueError): l.validate_test_focus(altered)

    def test_native_sources_are_frozen_and_real_grants_not_manual_or_synthetic_camera_claims(self):
        inputs = l.snapshot_inputs(l.ROOT)
        base = "tests/consumer/android-camera-receiver"
        self.assertIn(base + "/build.gradle.kts", inputs); self.assertIn(base + "/src/main/AndroidManifest.xml", inputs)
        self.assertFalse(any(name.endswith((".apk", ".jks", ".keystore")) for name in inputs))
        native = (l.ROOT / l.ANDROID_CAMERA_PROVIDER_SOURCE).read_text()
        activity = (l.ROOT / base / "src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraReceiverActivity.java").read_text()
        service = (l.ROOT / base / "src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraReceiverService.java").read_text()
        for value in ("rememberCameraPickerResultLauncher", "startActivityForResult", "NonexistentCameraActivity", "FileProvider.getUriForFile", "CameraFailureReason.Configuration", "CameraFailureReason.Launch", "contentResolver.openInputStream"):
            self.assertIn(value, native)
        self.assertNotIn("grantUriPermission(", native + activity + service)
        self.assertNotIn("putExtra(Intent.EXTRA_STREAM", native)
        for value in ("checkUriPermission", 'openFileDescriptor(uri, "w")', "AutoCloseOutputStream", "getCallingPackage", "checkSignatures"):
            self.assertIn(value, activity)
        for value in ("getPackagesForUid", "request.sendingUid", "checkSignatures", '"Unknown operation"'):
            self.assertIn(value, service)
        self.assertIn('android:protectionLevel="signature"', (l.ROOT / base / "src/main/AndroidManifest.xml").read_text())
        for value in ("maven-publish", "module.publication", "publishTo"):
            self.assertNotIn(value, (l.ROOT / base / "build.gradle.kts").read_text())

    def test_workflow_serial_minimum_job_has_distinct_outputs_and_receipts_only(self):
        source = (l.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn("system-images;android-23;google_apis;x86_64", source)
        self.assertIn('matrix.serial-emulator-api == \'23\'', source)
        self.assertIn('--output "build/ci-verification/$SLOT-minimum-api23"', source)
        self.assertIn('matrix.slot }}-minimum-api23/fresh-reports/*.xml', source)
        self.assertIn('matrix.slot }}/camera-receiver/receipt.json', source)
        self.assertNotIn('matrix.slot }}/camera-receiver/*.apk', source)


class CameraArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); self.root = Path(self.temp.name)
        self.plan = l.plan(l.ROOT, "android-device", only_modules=("calf-camera-picker",), focus=l.ANDROID_CAMERA_PROVIDER_FOCUS)
        expected = self.plan["expected"][0]
        self.path = self.root / expected["report_directory"] / "TEST-synthetic.xml"; self.path.parent.mkdir(parents=True)
        self.path.write_text('<testsuite><properties><property name="private" value="not-for-archive"/></properties>' +
            ''.join('<testcase classname="' + c['classname'] + '" name="' + c['name'] + '"/>' for c in expected['required_testcases']) +
            '<system-out>private-console-not-for-archive</system-out></testsuite>')
        cases = l.junit_cases(self.path.read_bytes())
        self.receipt = {"suite": "android-device", "explicit_test_focus": l.ANDROID_CAMERA_PROVIDER_FOCUS,
            "source_tree_dirty": False, "source_revision": "a"*40, "source_revision_after": "a"*40, "changed_inputs": [], "passed": True,
            "task_execution_markers": {expected["task"]: 1}, "totals": l.case_counts(cases),
            "modules": [{"module": "calf-camera-picker", "testcases": cases, "reports": [{"path": self.path.relative_to(self.root).as_posix(), "sha256": l.sha256(self.path)}]}]}
        self.output = self.root / "build/ci-verification/synthetic-camera"; self.output.mkdir(parents=True)

    def test_archive_preserves_actual_outcomes_and_original_hash_while_removing_only_console_properties(self):
        original = self.path.read_bytes()
        result = receiver.archive_focused_reports(self.root, self.output, self.receipt, self.plan)
        archived = (self.root / result["archived_path"]).read_bytes()
        self.assertNotIn(b"not-for-archive", archived)
        self.assertEqual(hashlib.sha256(original).hexdigest(), result["original_sha256"])
        self.assertEqual(l.junit_cases(original), l.junit_cases(archived))
        self.assertFalse(result["native_success_inferred_from_archival"])
        with self.assertRaises(ValueError): receiver.archive_focused_reports(self.root, self.output, self.receipt, self.plan)

    def test_actual_gradle_avd_filename_is_archived_without_changing_test_or_source_guards(self):
        renamed = self.path.with_name('TEST-nativecmpkit-api35-58bff09dc20d(AVD) - 15.xml')
        self.path.rename(renamed); self.path = renamed
        self.receipt['modules'][0]['reports'][0]['path'] = renamed.relative_to(self.root).as_posix()
        archived = receiver.archive_focused_reports(self.root, self.output, self.receipt, self.plan)
        self.assertEqual(renamed.name, Path(archived['archived_path']).name)
        self.assertEqual(self.receipt['modules'][0]['testcases'], archived['actual_testcases'])

    def test_each_native_provider_authority_has_a_distinct_android_component_identity(self):
        manifest = ET.fromstring((l.ROOT / 'calf-camera-picker/src/androidDeviceTest/AndroidManifest.xml').read_bytes())
        providers = manifest.findall('application/provider')
        names = [p.attrib['{http://schemas.android.com/apk/res/android}name'] for p in providers]
        self.assertEqual(3, len(names)); self.assertEqual(3, len(set(names)))

    def test_owned_adb_shutdown_transition_is_observed_without_device_mutation_or_foreign_fallback(self):
        with patch.object(device, 'adb', side_effect=['List of devices attached\nemulator-5588\toffline', 'List of devices attached']) as adb, \
             patch.object(device.time, 'sleep'):
            self.assertTrue(device.wait_for_owned_transport_removal(Path('/synthetic/sdk'), timeout=1))
        self.assertEqual([(('devices',), {})] * 2, [(call.args[1:], call.kwargs) for call in adb.call_args_list])
        with patch.object(device, 'adb', return_value='List of devices attached\nprivate-foreign-device\tdevice'), \
             patch.object(device.time, 'sleep') as sleep, self.assertRaises(ValueError):
            device.wait_for_owned_transport_removal(Path('/synthetic/sdk'), timeout=1)
        sleep.assert_not_called()

    def test_wrong_hash_changed_source_or_task_and_foreign_selection_fail_before_archival(self):
        for bad in (self.receipt | {"source_tree_dirty": True}, self.receipt | {"changed_inputs": ["source"]},
                    self.receipt | {"source_revision_after": "b"*40}, self.receipt | {"task_execution_markers": {}},
                    self.receipt | {"explicit_test_focus": l.ANDROID_SHARE_GRANT_FOCUS}):
            with self.assertRaises(ValueError): receiver.archive_focused_reports(self.root, self.output, bad, self.plan)
            self.assertFalse((self.output / "fresh-reports").exists())
        self.path.write_text(self.path.read_text().replace('private-console', 'changed-console'))
        with self.assertRaises(ValueError): receiver.archive_focused_reports(self.root, self.output, self.receipt, self.plan)

    def test_failed_actual_xml_remains_failed_and_cannot_become_a_passing_archive_receipt(self):
        self.path.write_text(self.path.read_text().replace('/><testcase', '><failure message="synthetic failure"/></testcase><testcase', 1))
        cases = l.junit_cases(self.path.read_bytes())
        self.receipt["modules"][0]["testcases"] = cases; self.receipt["modules"][0]["reports"][0]["sha256"] = l.sha256(self.path)
        self.receipt.update(totals=l.case_counts(cases), passed=False)
        result = receiver.archive_focused_reports(self.root, self.output, self.receipt, self.plan)
        self.assertFalse(result["original_passed"]); self.assertEqual(1, l.case_counts(result["actual_testcases"])["failures"])

    def test_symlink_or_entity_xml_is_not_archived(self):
        original = self.path.read_bytes(); self.path.unlink(); other = self.root / "outside.xml"; other.write_bytes(original); self.path.symlink_to(other)
        with self.assertRaises(ValueError): receiver.archive_focused_reports(self.root, self.output, self.receipt, self.plan)
        self.path.unlink(); self.path.write_text('<!DOCTYPE testsuite [<!ENTITY x "private">]><testsuite/>')
        with self.assertRaises(ValueError): receiver.archive_focused_reports(self.root, self.output, self.receipt, self.plan)

    def test_exact_owned_camera_fixture_metadata_and_private_signing_context_reuse_installer_contract(self):
        env = {"ANDROID_SERIAL": "emulator-5588", "ANDROID_USER_HOME": str(self.output / "android-user"), "PRIVATE_SYNTHETIC": "not-for-receipt"}
        owner = receiver.OwnedCameraReceiver(self.root, self.output, Path("/synthetic/sdk"), "emulator-5588", lambda: True, environment=env)
        self.assertEqual(self.output / "camera-receiver", owner.output)
        self.assertNotIn("PRIVATE_SYNTHETIC", json.dumps(owner.receipt))
        base = self.root / owner.FIXTURE / "build/outputs/apk/debug"; base.mkdir(parents=True)
        apk = base / "camera-debug.apk"; apk.write_bytes(b"synthetic-not-native")
        (base / "output-metadata.json").write_text(json.dumps({"applicationId": owner.PACKAGE, "variantName": "debug", "artifactType": {"type": "APK"},
            "elements": [{"type": "SINGLE", "filters": [], "outputFile": apk.name}]}))
        self.assertEqual(apk, geo.metadata_apk(self.root, fixture=owner.FIXTURE, package=owner.PACKAGE))
        with self.assertRaises(ValueError): geo.metadata_apk(self.root, fixture=owner.FIXTURE, package=geo.PACKAGE)
        owner.is_owned = lambda: False
        with patch.object(owner, "readback") as read, self.assertRaises(ValueError): owner.control("uninstall", owner.PACKAGE)
        read.assert_not_called()


if __name__ == "__main__": unittest.main()
