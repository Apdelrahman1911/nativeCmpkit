# SPDX-License-Identifier: Apache-2.0
"""NEW Camera routing AST/fake-object models; no host/controller or native execution."""
import ast
import copy
import hashlib
from pathlib import Path
import plistlib
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import apple_image_sidecar_evidence as image_sidecar
import camera_ios_ownership_native_focus as camera
import camera_ios_ownership_source_projection as history
import ios_camera_photo_fixture as photos
import ios_ui_application as application
from ios_ui_split664_source_projection import current_source_before_ui_split664
import library_tests as library
from test_ios_camera_photo_fixture import BUNDLE, DEVICE, NONCE, PID, SOURCE, native_status

ROOT = Path(__file__).resolve().parents[2]
APP_SOURCE = "scripts/ci/ios_ui_application.py"
LIBRARY_SOURCE = "scripts/ci/library_tests.py"


def functions(name, payload=None):
    return {node.name: node for node in ast.parse((ROOT / name).read_bytes() if payload is None else payload).body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))}


def block(function, call):
    return next(node for node in ast.walk(function) if isinstance(node, ast.If) and
                any(isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and child.func.attr == call
                    for child in ast.walk(node)))


def camera_block(call):
    run = functions(APP_SOURCE)["run"]
    return next(node for node in ast.walk(run) if isinstance(node, ast.If) and
                ast.unparse(node.test) in {"host['module'] == lt.camera_ios.MODULE", "camera_photos is not None"} and
                any(isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and child.func.attr == call
                    for child in ast.walk(node)))


def model(node, namespace):
    """Execute only a NEW current Camera block with explicit ordinary fake objects."""
    document = ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(node)], type_ignores=[]))
    exec(compile(document, "<new-camera-routing-source-only-model>", "exec"), namespace)


class FakePhotosLease:
    def __init__(self, events, *, prepare_error=None, close_error=None, receipt_error=None):
        self.events = events
        self.prepare_error = prepare_error
        self.close_error = close_error
        self.receipt_error = receipt_error

    def prepare(self):
        self.events.append("prepare")
        if self.prepare_error:
            raise self.prepare_error

    def close(self):
        self.events.append("close")
        if self.close_error:
            raise self.close_error

    def receipt(self, status):
        self.events.append(("receipt", status))
        if self.receipt_error:
            raise self.receipt_error
        return {"source_model_only": True}


class CameraIosOwnershipApplicationRoutingControls(unittest.TestCase):
    def namespace(self, *, prepare_error=None, close_error=None, receipt_error=None, validated=True, stopped=True):
        events = []
        lease = FakePhotosLease(events, prepare_error=prepare_error, close_error=close_error, receipt_error=receipt_error)
        construct = Mock(side_effect=lambda **kwargs: (events.append(("construct", kwargs)), lease)[1])
        validate = Mock(return_value=validated)
        module = SimpleNamespace(OwnedPhotosLease=construct, validate_receipt=validate)
        namespace = {"host": {"module": camera.MODULE}, "lt": SimpleNamespace(camera_ios=camera),
                     "root": ROOT, "device": DEVICE, "bundle_id": BUNDLE, "before": {"source_revision": SOURCE},
                     "token": NONCE, "signed_hash": "c" * 64, "plist_hash": "d" * 64,
                     "execute_control": Mock(), "installed_identity": Mock(), "control_status": application.control_status,
                     "camera_photo": module, "camera_photos": None,
                     "protocol": SimpleNamespace(observed_launch_pid=PID, camera_photo_observation=native_status()),
                     "stop": subprocess.CompletedProcess([], 0 if stopped else 99, b"", b""),
                     "stopped_app": application.stopped_app, "receipt": {"transport_passed": True}}
        return namespace, lease, events, construct, validate

    def test_distinct_camera_application_task_binary_and_receipt_require_exact_new5_and_reject_other_hosts_full_or_sdk(self):
        host = application.APPLICATION_HOSTS[camera.MODULE]
        self.assertEqual((camera.TASK, "calf-camera-picker/build/bin/iosSimulatorArm64/applicationDebugTest", "native-camera-application"),
                         (host["task"], host["binary_directory"], host["receipt_subdirectory"]))
        binary = host["binary_directory"] + "/application.kexe"
        self.assertEqual(camera.MODULE, application.application_host(binary, camera.FOCUS)["module"])
        for focus in (None, library.IOS_MODAL_LIFECYCLE_FOCUS, library.IOS_IMAGE_PROFILE_RECOVERY_FOCUS,
                      library.IOS_WEBVIEW_LIFECYCLE_FOCUS):
            with self.assertRaises(ValueError):
                application.application_host(binary, focus)
        for owner, other in application.APPLICATION_HOSTS.items():
            if owner != camera.MODULE:
                with self.assertRaises(ValueError):
                    application.application_host(other["binary_directory"] + "/application.kexe", camera.FOCUS)
        arguments = list(application.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + ",".join(camera.selectors())]
        self.assertEqual(camera.FOCUS, application.application_test_focus(arguments))
        for selectors in (camera.selectors()[:-1], camera.selectors() + camera.selectors()[:1],
                          camera.selectors() + ("foreign.method",), (camera.CLASS + ".*",)):
            with self.assertRaises(ValueError):
                application.application_test_focus(list(application.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + ",".join(selectors)])
        with patch.object(application.platform, "system", return_value="Darwin"), patch.object(application.platform, "machine", return_value="arm64"), self.assertRaises(ValueError):
            application.run(binary, [], appinfo_shape_only=True)

    def test_photos_prepare_occurs_after_foreign_absence_install_and_signed_plist_readback_before_original_launch(self):
        source = (ROOT / APP_SOURCE).read_text()
        run = functions(APP_SOURCE)["run"]
        prepare = camera_block("OwnedPhotosLease")
        self.assertLess(source.index('phase = "foreign-app-preflight"'), source.index('phase = "install-owned-app"'))
        self.assertLess(source.index('receipt["steps"][phase]["installed_owned_bytes_verified"] = installed'),
                        source.index('phase = "prepare-owned-camera-photos-controlled-setup"'))
        launch = next(node for node in ast.walk(run) if isinstance(node, ast.Call) and ast.unparse(node.func) == "forward_application")
        self.assertLess(prepare.end_lineno, launch.lineno)
        sdk = next(node for node in ast.walk(run) if isinstance(node, ast.If) and ast.unparse(node.test) == "appinfo_shape_only" and
                   any(isinstance(child, ast.Return) for child in ast.walk(node)))
        self.assertLess(sdk.end_lineno, prepare.lineno)
        namespace, lease, events, construct, validate = self.namespace()
        model(prepare, namespace)
        self.assertIs(lease, namespace["camera_photos"])
        construct.assert_called_once_with(root=ROOT, simulator=DEVICE, bundle_id=BUNDLE, source_revision=SOURCE,
            session_nonce=NONCE, signed_hash="c" * 64, plist_hash="d" * 64,
            execute_control=namespace["execute_control"], installed_identity=namespace["installed_identity"],
            control_status=application.control_status)
        self.assertEqual("prepare", events[-1])
        validate.assert_not_called()

    def test_only_camera_plist_gets_both_exact_keys_and_no_ats_scene_debug_or_foreign_fixture(self):
        node = camera_block("privacy_information")
        for module in (camera.MODULE, "calf-ui", "calf-share", "calf-webview", "calf-file-picker"):
            original = application.app_information(BUNDLE, "17.0.0")
            namespace = {"host": {"module": module}, "lt": SimpleNamespace(camera_ios=camera),
                         "information": original.copy(), "camera_photo": photos}
            model(node, namespace)
            self.assertEqual(original | (photos.privacy_information() if module == camera.MODULE else {}), namespace["information"])
            self.assertNotIn("NSAppTransportSecurity", namespace["information"])
            self.assertNotIn("UIApplicationSceneManifest", namespace["information"])
        before = history.source_before_camera_ios_ownership(APP_SOURCE, (ROOT / APP_SOURCE).read_bytes())
        self.assertEqual(ast.dump(functions(APP_SOURCE, before)["app_information"], include_attributes=False),
                         ast.dump(functions(APP_SOURCE)["app_information"], include_attributes=False))

    def test_camera_protocol_adapter_binds_actual_source_nonce_and_original_protocol_without_environment_fixture(self):
        node = camera_block("protocol_adapter")
        contract = Mock()
        adapter = Mock(return_value=SimpleNamespace(source_model_only=True))
        module = SimpleNamespace(protocol_adapter=adapter)
        namespace = {"host": {"module": camera.MODULE}, "lt": SimpleNamespace(camera_ios=SimpleNamespace(MODULE=camera.MODULE, source_contract=contract)),
                     "root": ROOT, "bundle_id": BUNDLE, "before": {"source_revision": SOURCE}, "token": NONCE,
                     "NativeProtocol": application.NativeProtocol}
        with patch.dict(sys.modules, {"ios_camera_photo_fixture": module}):
            model(node, namespace)
        contract.assert_called_once_with(ROOT)
        adapter.assert_called_once_with(application.NativeProtocol, bundle_id=BUNDLE, source_revision=SOURCE, session_nonce=NONCE)
        self.assertIs(adapter.return_value, namespace["protocol"])
        self.assertNotIn("native_environment", namespace)
        self.assertEqual(1, sum(isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and
                         child.func.attr == "protocol_adapter" for child in ast.walk(functions(APP_SOURCE)["run"])))

    def test_verified_owned_stop_precedes_reset_and_reset_failures_never_skip_independent_original_uninstall(self):
        node = camera_block("close")
        run = functions(APP_SOURCE)["run"]
        stop = next(child for child in ast.walk(run) if isinstance(child, ast.Assign) and ast.unparse(child.targets[0]) == "stop")
        uninstall = next(child for child in ast.walk(run) if isinstance(child, ast.Assign) and ast.unparse(child.targets[0]) == "uninstall")
        self.assertLess(stop.end_lineno, node.lineno)
        self.assertLess(node.end_lineno, uninstall.lineno)
        for stopped, close_error in ((True, None), (True, OSError("new reset model")), (True, ValueError("new reset model")), (False, None)):
            namespace, lease, events, construct, validate = self.namespace(stopped=stopped, close_error=close_error)
            namespace["camera_photos"] = lease
            model(node, namespace)
            events.append("following-original-owned-uninstall-absence-local-cleanup-model")
            self.assertEqual("following-original-owned-uninstall-absence-local-cleanup-model", events[-1])
            if not stopped:
                self.assertNotIn("close", events)
            if close_error or not stopped:
                self.assertFalse(namespace["receipt"]["transport_passed"])
                self.assertIn("camera_photos_reset_error_type", namespace["receipt"])
            else:
                self.assertTrue(namespace["receipt"]["transport_passed"])

    def test_prepare_refusal_retains_owned_lease_and_reset_receipt_failures_preserve_independent_local_cleanup(self):
        namespace, lease, events, construct, validate = self.namespace(prepare_error=ValueError("new prepare model"))
        with self.assertRaises(ValueError):
            model(camera_block("OwnedPhotosLease"), namespace)
        self.assertIs(lease, namespace["camera_photos"])
        model(camera_block("close"), namespace)
        self.assertIn("close", events)
        receipt_node = camera_block("receipt")
        run = functions(APP_SOURCE)["run"]
        local = next(node for node in ast.walk(run) if isinstance(node, ast.If) and ast.unparse(node.test) == "app.exists()")
        self.assertLess(receipt_node.end_lineno, local.lineno)
        for kwargs in ({"receipt_error": OSError("new receipt model")}, {"validated": False}):
            namespace, lease, events, construct, validate = self.namespace(**kwargs)
            namespace["camera_photos"] = lease
            model(receipt_node, namespace)
            events.append("following-original-owned-local-cleanup-model")
            self.assertEqual("following-original-owned-local-cleanup-model", events[-1])
            self.assertFalse(namespace["receipt"]["transport_passed"])
            self.assertIn("error", namespace["receipt"])
            if "receipt_error" not in kwargs:
                validate.assert_called_once_with({"source_model_only": True}, simulator=DEVICE, bundle_id=BUNDLE,
                    source_revision=SOURCE, session_nonce=NONCE, signed_hash="c" * 64, plist_hash="d" * 64, native_pid=PID)

    def test_original_argv_deadlines_native_protocol_sdk_helpers_and_native_xml_runtime_worker_cleanup_gates_remain(self):
        raw = (ROOT / APP_SOURCE).read_bytes()
        before = history.source_before_camera_ios_ownership(APP_SOURCE, raw)
        # UI664 added only its exact finite timeout/host/runtime wiring after
        # this Camera checkpoint. Admit the complete current image before its
        # dated predecessor; never relax helper AST or native receipt gates.
        qualified = current_source_before_ui_split664(APP_SOURCE, raw)
        current, prior = functions(APP_SOURCE, qualified), functions(APP_SOURCE, before)
        for name in ("NativeProtocol", "execute_control", "control_status", "installed_identity", "stopped_app",
                     "forward_application", "application_timeout_seconds", "macho_simulator_identity",
                     "profile_debug_entitlements", "provider_c3_observation_route"):
            self.assertEqual(ast.dump(prior[name], include_attributes=False), ast.dump(current[name], include_attributes=False))
        library_raw = (ROOT / LIBRARY_SOURCE).read_bytes()
        library_before = history.source_before_camera_ios_ownership(LIBRARY_SOURCE, library_raw)
        def gates(payload):
            node = functions(LIBRARY_SOURCE, payload)["collect_one_ios_application_receipt"]
            return [ast.dump(child, include_attributes=False) for child in ast.walk(node) if isinstance(child, ast.Call)
                    and ast.unparse(child.func) == "need" and not (len(child.args) > 1 and isinstance(child.args[-1], ast.Constant)
                    and child.args[-1].value == "Receipt missing or disposable app/other files remain")]
        new_gates = iter(gates(library_raw))
        for gate in gates(library_before):
            self.assertTrue(any(candidate == gate for candidate in new_gates), "An original native gate was changed or omitted")
        # The reviewed Image633 reader replaces only the old membership operand.
        # Its unrelated Camera route remains strict receipt-only.
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            session = Path(temporary).resolve() / NONCE
            session.mkdir()
            (session / "receipt.json").write_text("{}")
            image_sidecar.require_session_membership(session, camera.MODULE, camera.FOCUS)
            (session / image_sidecar.RECORD_NAME).write_text("{}")
            with self.assertRaises(ValueError):
                image_sidecar.require_session_membership(session, camera.MODULE, camera.FOCUS)

    def test_collector_requires_exact_plist_photos_lease_same_native_pid_and_status_and_refuses_foreign_fields(self):
        collector = functions(LIBRARY_SOURCE)["collect_one_ios_application_receipt"]
        node = next(child for child in ast.walk(collector) if isinstance(child, ast.If) and
                    any(isinstance(call, ast.Call) and ast.unparse(call.func) == "camera_photo.validate_receipt" for call in ast.walk(child)))
        information = application.app_information(BUNDLE, "17.0.0") | photos.privacy_information()
        plist_hash = hashlib.sha256(plistlib.dumps(information, sort_keys=True)).hexdigest()
        lease = photos.OwnedPhotosLease(root=ROOT, simulator=DEVICE, bundle_id=BUNDLE, source_revision=SOURCE,
            session_nonce=NONCE, signed_hash="c" * 64, plist_hash=plist_hash,
            execute_control=lambda argv: subprocess.CompletedProcess(argv, 0, b"", b""),
            installed_identity=lambda *args: True, control_status=application.control_status)
        lease.prepare()
        lease.close()
        status = native_status()
        document = {"bundle_id": BUNDLE, "macho": {"minimum_os": "17.0.0"},
                    "application_plist_sha256": plist_hash, "signed_application_executable_sha256": "c" * 64,
                    "camera_photos": lease.receipt(status)}
        def need(condition, message):
            if not condition:
                raise ValueError(message)
        namespace = {"test_plan": {"explicit_test_focus": camera.FOCUS}, "camera_ios": camera,
                     "app": application, "document": document, "context": {"simulator": {"udid": DEVICE}, "source_revision": SOURCE},
                     "token": NONCE, "protocol": {"observed_launch_pid": PID, "camera_photo_authorization": status},
                     "need": need, "hashlib": hashlib}
        model(node, namespace)
        mutations = (
            lambda n: n["document"].update(application_plist_sha256="d" * 64),
            lambda n: n["document"]["camera_photos"].update(native_status=None),
            lambda n: n["protocol"].update(observed_launch_pid=PID + 1),
            lambda n: n["protocol"].update(camera_photo_authorization=None),
            lambda n: n["document"].update(webview_request_fixture={}),
            lambda n: n["document"].update(native_xctest_input={}),
        )
        for mutate in mutations:
            bad = {**namespace, "document": copy.deepcopy(document), "protocol": copy.deepcopy(namespace["protocol"])}
            mutate(bad)
            with self.assertRaises(ValueError):
                model(node, bad)
        unrelated = {**namespace, "test_plan": {"explicit_test_focus": None}}
        with self.assertRaises(ValueError):
            model(node, unrelated)


if __name__ == "__main__":
    unittest.main()
