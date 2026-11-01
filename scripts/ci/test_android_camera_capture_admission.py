"""New capture/order owning mocks only; no SDK, Gradle, Git or native execution."""
from __future__ import annotations

import ast
from contextlib import ExitStack
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

TREE = Path(os.environ.get("CAMERA_CAPTURE_ADMISSION_MODEL_TREE", Path(__file__).resolve().parents[2])).resolve()
PRIVATE = Path(os.environ.get("CAMERA_CAPTURE_ADMISSION_MODEL_TMP", tempfile.gettempdir())).resolve()
CONTROLLER = TREE / "scripts/ci/android_device_tests.py"
FOCUS = "android-camera-real-restoration-dont-keep"
MARKER = "synthetic-unpublished-exception-body"
UNAVAILABLE = {"source": "unavailable", "symbol": "unavailable", "line": 0}


def forbidden(*args, **kwargs):
    raise AssertionError("An unstubbed SDK/build/native/control action is forbidden")


# Import only the held controller. All project imports are isolated inert stubs,
# so model discovery cannot execute another suite or acquire SDK/runtime assets.
DEPENDENCIES = {name: types.ModuleType(name) for name in (
    "library_tests", "runtime_context", "android_webview_heap", "android_geo_probe",
    "android_share_recipient", "android_camera_receiver", "android_io_documents",
    "android_permission_demo", "android_storage_probe", "android_camera_developer_prerequisite")}
lt = DEPENDENCIES["library_tests"]
lt.ANDROID_CAMERA_FOCUSES = {FOCUS, "android-camera-real-restoration", "android-camera-provider"}
lt.ANDROID_IO_PROVIDER_FOCUS = "android-io-provider"
lt.ANDROID_IO_UNAVAILABLE_FOCUS = "android-io-provider-unavailable"
lt.ANDROID_IO_DEFAULT_DECODE_FOCUS = "android-io-default-decode"
lt.ANDROID_IO_REFERENCE_FOCUS = "android-io-reference"
lt.ANDROID_IO_NAMED_SYSTEM_FOCUS = "android-io-named-system-providers"
lt.WEBVIEW_ANDROID_MEDIA_FOCUS = "webview-android-media"
for name in ("safe_path", "plan", "android_io_documents_required", "android_permission_demo_required",
             "android_storage_probe_required", "android_camera_receiver_required", "android_geo_probe_required",
             "android_share_recipient_required", "gradle_command", "execute", "run", "write_json",
             "snapshot_inputs", "git_revision", "utc_now", "terminate_owned"):
    setattr(lt, name, forbidden)
DEPENDENCIES["runtime_context"].capture = forbidden
camera = DEPENDENCIES["android_camera_developer_prerequisite"]
camera.is_required = forbidden
camera.OwnedFreshGuest = forbidden
camera.OwnedDeveloperPrerequisite = forbidden
camera.accepted = forbidden
DEPENDENCIES["android_camera_receiver"].OwnedCameraReceiver = forbidden
SPEC = importlib.util.spec_from_file_location("camera_capture_admission_controller_under_test", CONTROLLER)
device = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, DEPENDENCIES):
    SPEC.loader.exec_module(device)


# Preserve the real generic require definition and its original public source
# line. All callers below are explicitly synthetic traceback shapes, not claims
# about the unseen actual012 configuration or which original guard failed.
HELPER = CONTROLLER.with_name("android_camera_developer_prerequisite.py")
REQUIRE = next(node for node in ast.parse(HELPER.read_text()).body
               if isinstance(node, ast.FunctionDef) and node.name == "require")
REQUIRE_LINE = REQUIRE.body[0].body[0].lineno
TRACE = {"__name__": "camera_capture_traceback_fixture", "MARKER": MARKER}
TRACE_LINES = {}
body = [copy.deepcopy(REQUIRE)]
for name, start, statement in (
    ("capture_avd", 100, "require(False, MARKER)"),
    ("unique", 200, "require(False, MARKER)"),
    ("parse_properties", 300, "unique()"),
    ("nested_capture", 400, "parse_properties()"),
    ("verify_config", 500, "require(False, MARKER)"),
):
    node = ast.parse(f"def {name}():\n    {statement}\n").body[0]
    ast.increment_lineno(node, start - 1)
    TRACE_LINES[name] = node.body[0].lineno
    body.append(node)
exec(compile(ast.Module(body=body, type_ignores=[]), str(HELPER), "exec"), TRACE)
PRIMARY = {"source": HELPER.name, "symbol": "require", "line": REQUIRE_LINE}


class Model:
    """Admission boundary only. Boot is stopped before any APK/native/lease work."""
    def __init__(self, *, capture_refusal=False, create_code=0, create_stop=None,
                 assembly_code=0, config_refusal=False, focus=FOCUS, api=35, camera_route=True):
        self.capture_refusal, self.create_code, self.create_stop = capture_refusal, create_code, create_stop
        self.assembly_code, self.config_refusal = assembly_code, config_refusal
        self.focus, self.api, self.camera_route = focus, api, camera_route
        self.events, self.writes, self.disposals = [], {}, []
        self.process, self.guest, self.stack = None, None, ExitStack()

    def __enter__(self):
        PRIVATE.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(prefix="camera-capture-owning-", dir=PRIVATE)
        self.root = Path(self.directory.name)
        self.home = self.root / "nonexistent-sdk"
        self.old_umask = os.umask(0o077)
        self.stack.enter_context(patch.dict(os.environ, {"ANDROID_HOME": str(self.home)}, clear=True))
        plan = {"expected": [{"project": ":calf-camera-picker"}], "complete_suite_requested": False,
                "explicit_module_subset": ["calf-camera-picker"], "test_bearing_modules_not_requested": []}
        inert = {
            "safe_path": lambda root, relative: root / relative,
            "plan": lambda *a, **k: copy.deepcopy(plan),
            "android_io_documents_required": lambda p: False,
            "android_permission_demo_required": lambda p: False,
            "android_storage_probe_required": lambda p: False,
            "android_camera_receiver_required": lambda p: self.camera_route,
            "android_geo_probe_required": lambda p: False,
            "android_share_recipient_required": lambda p: False,
            "gradle_command": lambda *a, **k: ["model-gradle", ":calf-camera-picker:connectedAndroidDeviceTest"],
            "execute": self.execute,
            "write_json": lambda path, value: self.writes.__setitem__(path.name, copy.deepcopy(value)),
            "snapshot_inputs": lambda root: {"held-controller": hashlib.sha256(CONTROLLER.read_bytes()).hexdigest()},
            "git_revision": lambda root: "model-held-revision",
            "utc_now": lambda: "2000-01-01T00:00:00Z",
        }
        for name, value in inert.items():
            self.stack.enter_context(patch.object(lt, name, value))
        self.stack.enter_context(patch.object(camera, "is_required", lambda api, modules, focus: focus == FOCUS))
        self.stack.enter_context(patch.object(camera, "OwnedFreshGuest", self.Guest()))
        self.stack.enter_context(patch.object(device.runtime, "capture", lambda **k: {
            "source_revision": "model-held-revision", "source_tree_dirty": False}))
        self.stack.enter_context(patch.object(device, "sdk_assets", lambda *a, **k: {
            "system_image": f"system-images;android-{self.api};google_apis;x86_64"}))
        self.stack.enter_context(patch.object(device, "ensure_ports_unused", lambda: None))
        self.stack.enter_context(patch.object(device, "adb", self.adb))
        self.stack.enter_context(patch.object(device, "wait_for_owned_boot", self.boot_boundary))
        self.stack.enter_context(patch.object(device, "stop_owned_emulator", self.stop))
        self.stack.enter_context(patch.object(device, "wait_for_owned_transport_removal", self.transport_absent))
        self.stack.enter_context(patch.object(device.subprocess, "Popen", self.launch))
        self.stack.enter_context(patch.object(device.subprocess, "run", forbidden))
        return self

    def __exit__(self, *exc):
        try:
            self.stack.close()
        finally:
            os.umask(self.old_umask)
            self.directory.cleanup()

    def Guest(self):
        model = self

        class Guest:
            def __init__(self, root, output, name, environment):
                assert root == model.root and environment["ANDROID_SERIAL"] == device.SERIAL
                self.output, self.process, self.captured, self.launch_attempted = output, None, False, False
                self.receipt = {"launch_attempted": False}
                model.guest = self

            def create(self):
                model.events.append("guest.create")
                for name in ("avd", "android-user"):
                    (self.output / name).mkdir(mode=0o700)

            def capture_avd(self, home):
                assert home == model.home and not self.captured and not self.launch_attempted
                model.events.append("guest.capture")
                if model.capture_refusal:
                    TRACE["capture_avd"]()
                self.captured = True

            def verify_config(self):
                model.events.append("guest.verify_config")
                assert self.captured
                if model.config_refusal:
                    TRACE["verify_config"]()

            def before_launch(self):
                model.events.append("guest.before_launch")
                self.verify_config()
                assert not self.launch_attempted
                self.launch_attempted = True
                self.receipt["launch_attempted"] = True

            def attach(self, process):
                model.events.append("guest.attach")
                assert self.launch_attempted and self.process is None
                self.process = process

            def verify_live(self):
                model.events.append("guest.verify_live")
                assert self.process is model.process and self.process.poll() is None
                return True

            def dispose(self, **values):
                model.events.append("guest.dispose")
                model.disposals.append(copy.deepcopy(values))
                assert set(values) == {"engine_exited", "transport_absent", "clean_shutdown"}
                if self.launch_attempted:
                    assert values["engine_exited"] is True and values["transport_absent"] is True
                else:
                    assert values == {"engine_exited": False, "transport_absent": False, "clean_shutdown": False}
                for name in ("avd", "android-user"):
                    (self.output / name).rmdir()
                self.receipt.update(disposal_status="passed", roots_absent=True,
                                    engine_known_exited=not self.launch_attempted or values["engine_exited"],
                                    owned_transport_absent=not self.launch_attempted or values["transport_absent"],
                                    clean_shutdown=values["clean_shutdown"])
                return dict(self.receipt)

        return Guest

    def execute(self, root, command, log, timeout, reserve, *, env):
        stage = log.stem
        assert root == self.root and env["ANDROID_SERIAL"] == device.SERIAL and reserve == 8192
        assert stage in {"owned-avd-create", "apk-assembly"}
        assert timeout == (120 if stage == "owned-avd-create" else 900)
        self.events.append(stage)
        if stage == "owned-avd-create":
            return {"exit_code": self.create_code, "stop_reason": self.create_stop}
        return {"exit_code": self.assembly_code, "stop_reason": None}

    def adb(self, home, *arguments, **kwargs):
        assert home == self.home and arguments == ("devices",)
        return "List of devices attached"

    def launch(self, command, **kwargs):
        assert self.process is None and kwargs["start_new_session"] is True
        assert command[0] == str(self.home / "emulator/emulator")
        self.events.append("emulator.launch")
        self.process = types.SimpleNamespace(pid=4242, returncode=None)
        self.process.poll = lambda: self.process.returncode
        return self.process

    def boot_boundary(self, *args, **kwargs):
        self.events.append("boot.boundary")
        raise RuntimeError("Synthetic model stops before APK installs, leases and native dispatch")

    def stop(self, home, process, name, verified):
        assert process is self.process and verified is False
        self.events.append("emulator.stop")
        process.returncode = 0
        return {"exit_code": 0, "clean_shutdown": False, "graceful_kill_requested": False}

    def transport_absent(self, home):
        self.events.append("transport.absent")
        return True

    def run(self):
        result = device._run(self.root, "build/ci-verification/owning-capture-model",
                             only_modules=("calf-camera-picker",), focus=self.focus, api_level=self.api)
        assert result["passed"] is False and result["test_suite_passed"] is False
        assert "test_totals" not in result and "boot.json" not in self.writes
        assert MARKER not in json.dumps(result) and str(self.root) not in json.dumps(result)
        return result


class CaptureAdmissionOwningModels(unittest.TestCase):
    def test_capture_before_reporter_and_retained_reverify_before_sole_launch(self):
        with Model() as model:
            result = model.run()
            self.assertEqual(model.events[:8], ["guest.create", "owned-avd-create", "guest.capture",
                             "apk-assembly", "guest.before_launch", "guest.verify_config", "emulator.launch", "guest.attach"])
            self.assertEqual(model.events.count("guest.capture"), 1)
            self.assertEqual(model.events.count("emulator.launch"), 1)
            self.assertNotIn("camera_guest_capture_error_origin", result)

    def test_capture_refusal_short_circuits_reporter_native_and_preserves_primary(self):
        with Model(capture_refusal=True) as model:
            result = model.run()
            self.assertEqual(model.events, ["guest.create", "owned-avd-create", "guest.capture", "guest.dispose"])
            self.assertEqual(set(result["setup_stages"]), {"owned-avd-create"})
            self.assertEqual(result["controller_error"], "ValueError")
            self.assertEqual(result["controller_error_origin"], PRIMARY)
            self.assertEqual(result["camera_guest_capture_error_origin"], {
                "source": HELPER.name, "symbol": "capture_avd", "line": TRACE_LINES["capture_avd"]})
            self.assertEqual(model.disposals, [{"engine_exited": False, "transport_absent": False, "clean_shutdown": False}])
            self.assertIs(result["camera_guest_disposal"]["clean_shutdown"], False)
            self.assertFalse((model.root / "build/ci-verification/owning-capture-model/emulator.log").exists())

    def test_avd_create_nonzero_or_stop_never_captures_assembles_or_launches(self):
        for values in ({"create_code": 1}, {"create_stop": "synthetic-budget-stop"}):
            with self.subTest(values=values), Model(**values) as model:
                result = model.run()
                self.assertEqual(model.events, ["guest.create", "owned-avd-create", "guest.dispose"])
                self.assertEqual(result["controller_error"], "RuntimeError")
                self.assertNotIn("camera_guest_capture_error_origin", result)

    def test_reporter_failure_retains_captured_owner_and_prevents_launch(self):
        with Model(assembly_code=1) as model:
            result = model.run()
            self.assertEqual(model.events, ["guest.create", "owned-avd-create", "guest.capture", "apk-assembly", "guest.dispose"])
            self.assertEqual(result["controller_error"], "RuntimeError")
            self.assertNotIn("camera_guest_capture_error_origin", result)

    def test_post_assembly_config_refusal_keeps_default_origin_and_no_capture_diagnostic(self):
        with Model(config_refusal=True) as model:
            result = model.run()
            self.assertEqual(model.events, ["guest.create", "owned-avd-create", "guest.capture", "apk-assembly",
                             "guest.before_launch", "guest.verify_config", "guest.dispose"])
            self.assertEqual(result["controller_error_origin"], PRIMARY)
            self.assertNotIn("camera_guest_capture_error_origin", result)
            self.assertFalse(model.guest.launch_attempted)

    def test_capture_diagnostic_failure_cannot_replace_original_refusal(self):
        original = device.preflight_error_origin
        for kind in (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt):
            def failing_diagnostic(error, *, skip_prerequisite_require=False):
                if skip_prerequisite_require:
                    raise kind(MARKER)
                return original(error)
            with self.subTest(exception=kind.__name__), Model(capture_refusal=True) as model:
                with patch.object(device, "preflight_error_origin", failing_diagnostic):
                    result = model.run()
                self.assertEqual(result["controller_error"], "ValueError")
                self.assertEqual(result["controller_error_origin"], PRIMARY)
                self.assertEqual(result["camera_guest_capture_error_origin"], UNAVAILABLE)
                self.assertEqual(model.events, ["guest.create", "owned-avd-create", "guest.capture", "guest.dispose"])

    def test_other_routes_keep_original_setup_order_without_capture_field(self):
        for focus, api, camera_route, stages in (
            (None, 35, False, ["apk-assembly", "owned-avd-create"]),
            ("android-camera-real-restoration", 35, True, ["owned-avd-create", "apk-assembly"]),
            ("android-camera-provider", 23, True, ["owned-avd-create"]),
        ):
            with self.subTest(focus=focus, api=api), Model(focus=focus, api=api, camera_route=camera_route) as model:
                result = model.run()
                self.assertEqual(model.events[:len(stages)], stages)
                self.assertEqual(model.events.count("emulator.launch"), 1)
                self.assertIsNone(model.guest)
                self.assertNotIn("camera_guest_capture_error_origin", result)
                if api == 23:
                    self.assertTrue(result["reporter_compile_deferred_until_receiver_byte_identity"])

    def test_caller_filter_selects_nearest_approved_without_changing_default(self):
        for entry, caller in (("capture_avd", "capture_avd"), ("nested_capture", "unique")):
            try:
                TRACE[entry]()
            except ValueError as error:
                self.assertEqual(device.preflight_error_origin(error), PRIMARY)
                observed = device.preflight_error_origin(error, skip_prerequisite_require=True)
                self.assertEqual(observed, {"source": HELPER.name, "symbol": caller, "line": TRACE_LINES[caller]})
                self.assertEqual(set(observed), {"source", "symbol", "line"})
                self.assertNotIn(MARKER, json.dumps(observed))
                self.assertNotIn(str(TREE), json.dumps(observed))
            else:
                self.fail("Synthetic prerequisite refusal did not occur")

    def test_caller_filter_does_not_skip_other_allowed_require_source(self):
        namespace = {"MARKER": MARKER}
        exec(compile("def require():\n    raise ValueError(MARKER)\n", str(CONTROLLER), "exec"), namespace)
        try:
            namespace["require"]()
        except ValueError as error:
            expected = {"source": CONTROLLER.name, "symbol": "require", "line": 2}
            self.assertEqual(device.preflight_error_origin(error), expected)
            self.assertEqual(device.preflight_error_origin(error, skip_prerequisite_require=True), expected)

    def test_caller_filter_keeps_existing_directory_symbol_and_line_bounds(self):
        for filename, symbol, offset in (
            (HELPER.parent / "unapproved.py", "source_only_caller", 0),
            (HELPER.parent / "other-parent" / HELPER.name, "source_only_caller", 0),
            (HELPER, "invalid-symbol", 0),
            (HELPER, "source_only_caller", 20000),
            (HELPER, "require", 0),
        ):
            namespace = {"MARKER": MARKER}
            node = ast.parse("def source_only_caller():\n    raise ValueError(MARKER)\n")
            ast.increment_lineno(node, offset)
            exec(compile(node, str(filename), "exec"), namespace)
            function = namespace["source_only_caller"]
            function.__code__ = function.__code__.replace(co_name=symbol)
            with self.subTest(source=filename.name, symbol=symbol, offset=offset):
                try:
                    function()
                except ValueError as error:
                    self.assertEqual(device.preflight_error_origin(error, skip_prerequisite_require=True), UNAVAILABLE)


if __name__ == "__main__":
    unittest.main()
