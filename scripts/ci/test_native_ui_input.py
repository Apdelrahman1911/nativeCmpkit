# SPDX-License-Identifier: Apache-2.0
"""NEW bounded protocol/HTTP/ownership controls. ZERO XCTest/native input here."""
from contextlib import contextmanager
import copy
import hashlib
import http.client
import json
import os
from pathlib import Path
import plistlib
import socket
import stat
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import native_ui_input as native
import library_tests as library

ROOT = Path(__file__).resolve().parents[2]
TOKEN = "b" * 32
AUTH = "c" * 32
DEVICE = "726D52AF-426A-408A-974D-CA8B9BE8A479"
BUNDLE = "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + "a" * 12 + ".t" + TOKEN
HASH = "a" * 64
CASE = library.IOS_MODAL_XCUI_METHODS[0]


def no_native(*args, **kwargs):
    raise AssertionError("A source/HTTP control must never execute an SDK/native command")


@contextmanager
def driver_fixture():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with patch.object(native.secrets, "token_hex", return_value=AUTH):
            driver = native.InputDriver(root, DEVICE, BUNDLE, TOKEN, no_native, HASH, HASH)
        driver.directory = root / TOKEN
        driver.directory.mkdir()
        info = driver.directory.stat()
        driver.directory_identity = (info.st_dev, info.st_ino)
        try:
            yield driver
        finally:
            if driver.thread is not None and driver.thread.is_alive():
                driver.close()


def request(operation="tap", sequence=1):
    return {"sequence": sequence, "operation": operation, "case": CASE,
            **({"x": .5, "y": .5} if operation in ("tap", "drag") else
               {"title": "Owned alert", "label": "Owned field"}),
            **({"toX": .5, "toY": .9} if operation == "drag" else {}),
            **({"text": "Changed"} if operation == "alert-field" else {})}


def publish_request(driver, document):
    path = driver.directory / ("request-%d.json" % document["sequence"])
    path.write_bytes(json.dumps(document).encode())
    return path


class NativeUiInputControls(unittest.TestCase):
    def test_ordinary_files_reject_empty_oversized_links_directories_fifo_and_read_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ordinary = root / "ordinary"
            ordinary.write_bytes(b"bounded")
            self.assertEqual(b"bounded", native.read_ordinary(ordinary))
            for name, contents in (("empty", b""), ("large", b"a" * (native.MAX_BYTES + 1))):
                path = root / name; path.write_bytes(contents)
                with self.subTest(name=name), self.assertRaises(ValueError): native.read_ordinary(path)
            linked = root / "symlink"; linked.symlink_to(ordinary)
            with self.assertRaises(OSError): native.read_ordinary(linked)
            hard = root / "hard"; os.link(ordinary, hard)
            with self.assertRaises(ValueError): native.read_ordinary(ordinary)
            hard.unlink()
            fifo = root / "fifo"; os.mkfifo(fifo)
            for path in (fifo, root):
                with self.subTest(path=path.name), self.assertRaises(ValueError): native.read_ordinary(path)
            original = os.fstat
            calls = 0
            def changing(descriptor):
                nonlocal calls
                info = original(descriptor); calls += 1
                return info if calls == 1 else SimpleNamespace(**{key: getattr(info, key) + (key == "st_mtime_ns")
                    for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink", "st_mode", "st_uid")})
            with patch.object(native.os, "fstat", side_effect=changing), self.assertRaises(ValueError):
                native.read_ordinary(ordinary)

    def test_json_rejects_duplicate_nonfinite_overflow_nested_and_nonobject_payloads(self):
        self.assertEqual({"sequence": 1}, native.decode(b'{"sequence":1}'))
        bad = [b"", b"x" * (native.MAX_BYTES + 1), b"[]", b"true", b"null",
               b'{"x":1,"x":2}', b'{"x":{"y":1,"y":2}}', b'{"x":NaN}', b'{"x":Infinity}',
               b'{"x":-Infinity}', b'{"x":1e999}', b'{"x":' + b"[" * 1100 + b"0" + b"]" * 1100 + b"}"]
        for raw in bad:
            with self.subTest(size=len(raw)), self.assertRaises(ValueError): native.decode(raw)

    def test_refused_file_and_fdopen_failure_close_only_the_descriptor_they_own(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); ordinary = root / "file"; ordinary.write_bytes(b"ordinary")
            original_close = os.close
            with patch.object(native.os, "close", wraps=original_close) as closed:
                with self.assertRaises(ValueError): native.read_ordinary(root)
                closed.assert_called_once()
                with self.assertRaises(OSError): os.fstat(closed.call_args.args[0])
            with patch.object(native.os, "fdopen", side_effect=OSError("fixed synthetic fdopen refusal")), \
                    patch.object(native.os, "close", wraps=original_close) as closed:
                with self.assertRaises(OSError): native.read_ordinary(ordinary)
                closed.assert_called_once()
                with self.assertRaises(OSError): os.fstat(closed.call_args.args[0])

    def test_requests_admit_only_exact_bounded_operations_and_typed_next_sequence(self):
        for operation in ("tap", "drag", "alert-button", "alert-field"):
            self.assertEqual(request(operation), native.validate_request(request(operation), 1))
        bad = [dict(request(), sequence=True), dict(request(), sequence=2), dict(request(), sequence=0),
               dict(request(), operation="launch"), dict(request(), foreign="x"), dict(request(), case="foreign.method"),
               dict(request(), x=True), dict(request(), x=float("nan")), dict(request(), x=float("inf")),
               dict(request(), x=10**400), dict(request(), y=.001), dict(request(), y=1),
               dict(request("alert-field"), text="x" * 129), dict(request("alert-button"), label="")]
        for candidate in bad:
            with self.subTest(fields=set(candidate)), self.assertRaises(ValueError): native.validate_request(candidate, 1)
        with self.assertRaises(ValueError): native.validate_request(request(sequence=97), 97)

    def test_two_xctestrun_formats_are_typed_single_targets_with_private_separate_configuration(self):
        target = {"IsUITestBundle": True, "BlueprintName": "NativeCmpKitInputTests",
                  "TestingEnvironmentVariables": {"OWNED": "retained"}}
        old = {"NativeCmpKitInputTests": target, "__xctestrun_metadata__": {"FormatVersion": 1}}
        new = {"TestConfigurations": [{"TestTargets": [target]}], "__xctestrun_metadata__": {"FormatVersion": 2}}
        for document in (old, new):
            document = plistlib.loads(plistlib.dumps(document))
            prepared = native.prepare_xctestrun(document, "http://127.0.0.1:49123", TOKEN, BUNDLE, AUTH)
            selected = (prepared["TestConfigurations"][0]["TestTargets"][0] if "TestConfigurations" in prepared
                        else prepared["NativeCmpKitInputTests"])
            self.assertEqual(["NativeCmpKitInputTests/testDeliverOnlyOwnedLibraryNativeInput"], selected["OnlyTestIdentifiers"])
            environment = selected["TestingEnvironmentVariables"]
            self.assertEqual(AUTH, environment["NATIVECMPKIT_INPUT_AUTH"])
            self.assertNotEqual(TOKEN, environment["NATIVECMPKIT_INPUT_AUTH"])
            self.assertEqual("retained", environment["OWNED"])
        for malformed in ({}, {"TestConfigurations": []}, {"TestConfigurations": [{}, {}]},
                          {"TestConfigurations": [{"TestTargets": [target, target]}]},
                          {"NativeCmpKitInputTests": dict(target, IsUITestBundle=1)},
                          {"NativeCmpKitInputTests": dict(target, BlueprintName="Foreign")},
                          {"NativeCmpKitInputTests": dict(target, TestingEnvironmentVariables={"x": 1})}):
            with self.assertRaises(ValueError):
                native.prepare_xctestrun(malformed, "http://127.0.0.1:49123", TOKEN, BUNDLE, AUTH)

    def test_foreign_app_launch_remote_endpoint_and_shared_credential_are_refused_before_configuration_mutation(self):
        base = {"NativeCmpKitInputTests": {"IsUITestBundle": True, "BlueprintName": "NativeCmpKitInputTests"}}
        for key in ("UITargetAppPath", "UITargetAppBundleIdentifier"):
            document = copy.deepcopy(base); document["NativeCmpKitInputTests"][key] = "foreign"
            original = copy.deepcopy(document)
            with self.assertRaises(ValueError): native.prepare_xctestrun(document, "http://127.0.0.1:1", TOKEN, BUNDLE, AUTH)
            self.assertEqual(original, document)
        for endpoint in ("http://localhost:1", "https://127.0.0.1:1", "http://127.0.0.1:0",
                         "http://127.0.0.1:65536", "http://127.0.0.1:1/path", "http://127.0.0.1:1#fragment"):
            with self.assertRaises(ValueError): native.prepare_xctestrun(copy.deepcopy(base), endpoint, TOKEN, BUNDLE, AUTH)
        with self.assertRaises(ValueError): native.prepare_xctestrun(base, "http://127.0.0.1:1", TOKEN, BUNDLE, TOKEN)
        for wrong in (BUNDLE, "foreign", "io.github.apdelrahman1911.nativecmpkit.verification.input." + AUTH + ".xctrunner"):
            self.assertFalse(native.owned_runner_id(wrong, TOKEN))

    def test_readiness_pending_mutation_stale_responses_and_once_only_finish_are_strict(self):
        with driver_fixture() as driver:
            with self.assertRaises(ValueError): driver.handle("GET", "/next", None)
            self.assertEqual({"ready": True}, driver.handle("POST", "/ready", {}))
            with self.assertRaises(ValueError): driver.handle("POST", "/ready", {})
            self.assertIsNone(driver.handle("GET", "/next", None))
            document = request(); path = publish_request(driver, document)
            self.assertEqual(document, driver.handle("GET", "/next", None))
            self.assertEqual(document, driver.handle("GET", "/next", None))
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "mutated"): driver.handle("GET", "/next", None)
            with self.assertRaisesRegex(ValueError, "changed"): driver.handle("POST", "/response", {
                "sequence": 1, "status": "delivered", "operation": "tap", "foreground": True})
            path.write_bytes(json.dumps(document).encode())
            response = {"sequence": 1, "status": "delivered", "operation": "tap", "foreground": True}
            for wrong in (dict(response, sequence=True), dict(response, sequence=2), dict(response, foreground=1),
                          dict(response, operation="drag"), dict(response, extra="x")):
                with self.assertRaises(ValueError): driver.handle("POST", "/response", wrong)
            self.assertEqual({"acknowledged": 1}, driver.handle("POST", "/response", response))
            self.assertEqual(response, native.decode(native.read_ordinary(driver.directory / "response-1.json")))
            self.assertFalse((driver.directory / "response-1.tmp").exists())
            with self.assertRaises(ValueError): driver.handle("POST", "/response", response)
            with self.assertRaises(ValueError): driver.handle("POST", "/finished", {"delivered": 1})
            driver.finishing = True
            self.assertEqual({"operation": "finish"}, driver.handle("GET", "/next", None))
            with self.assertRaises(ValueError): driver.handle("POST", "/finished", {"delivered": True})
            self.assertEqual({"finished": True}, driver.handle("POST", "/finished", {"delivered": 1}))
            with self.assertRaises(ValueError): driver.handle("POST", "/finished", {"delivered": 1})

    def test_directory_replacement_dangling_requests_and_foreign_case_cannot_look_like_no_input(self):
        with driver_fixture() as driver:
            driver.handle("POST", "/ready", {})
            path = driver.directory / "request-1.json"; path.symlink_to(driver.directory / "missing")
            with self.assertRaises(OSError): driver.handle("GET", "/next", None)
            path.unlink(); publish_request(driver, dict(request(), case="ForeignCase"))
            with self.assertRaises(ValueError): driver.handle("GET", "/next", None)
            old = driver.directory.with_name("retired"); driver.directory.rename(old)
            driver.directory.mkdir()
            with self.assertRaisesRegex(ValueError, "ownership"): driver.handle("GET", "/next", None)

    def test_atomic_response_never_overwrites_existing_bytes_or_admits_a_partial_publication(self):
        with driver_fixture() as driver:
            driver.handle("POST", "/ready", {}); publish_request(driver, request())
            driver.handle("GET", "/next", None)
            target = driver.directory / "response-1.json"; target.write_bytes(b"original")
            with self.assertRaises(FileExistsError): driver.handle("POST", "/response", {
                "sequence": 1, "status": "delivered", "operation": "tap", "foreground": True})
            self.assertEqual(b"original", target.read_bytes())
            self.assertEqual([], driver.receipt["operations"])
            self.assertIsNotNone(driver.pending)

    def test_field_and_button_delivery_require_all_typed_native_witnesses(self):
        for operation in ("alert-button", "alert-field"):
            with driver_fixture() as driver:
                driver.handle("POST", "/ready", {}); publish_request(driver, request(operation))
                driver.handle("GET", "/next", None)
                response = {"sequence": 1, "status": "delivered", "operation": operation, "unique": True,
                    **({"enabled": True, "hittable": True} if operation == "alert-button" else {"value": "Changed"})}
                bad = [dict(response, unique=1), {key: value for key, value in response.items() if key != "unique"},
                       dict(response, value="x" * 129), dict(response, foreground=True)]
                for malformed in bad:
                    with self.assertRaises(ValueError): driver.handle("POST", "/response", malformed)
                self.assertEqual({"acknowledged": 1}, driver.handle("POST", "/response", response))

    def test_only_fixed_refusal_codes_are_published_and_refusals_can_never_verify_native_success(self):
        with driver_fixture() as driver:
            driver.handle("POST", "/ready", {}); publish_request(driver, request())
            driver.handle("GET", "/next", None)
            with self.assertRaises(ValueError): driver.handle("POST", "/response", {
                "sequence": 1, "status": "refused", "reason": "arbitrary credentials"})
            self.assertEqual({"acknowledged": 1}, driver.handle("POST", "/response", {
                "sequence": 1, "status": "refused", "reason": "notHittable"}))
            driver.process = Mock(); driver.process.wait.return_value = 0
            driver.finished.set(); driver.finishing = True
            with self.assertRaises(RuntimeError): driver.finish()
            driver.close()
            self.assertFalse(driver.receipt["verified"])
            self.assertEqual("notHittable", driver.receipt["operations"][0]["reason"])

    def test_real_loopback_http_auth_and_round_trip_use_only_this_owned_temporary_directory(self):
        with driver_fixture() as driver:
            driver._serve()
            self.assertEqual("127.0.0.1", driver.server.server_address[0])
            def exchange(method, path, body=None, credential=AUTH):
                connection = http.client.HTTPConnection("127.0.0.1", driver.server.server_port, timeout=3)
                raw = None if body is None else json.dumps(body).encode()
                connection.request(method, path, body=raw, headers={"Authorization": "Bearer " + credential})
                response = connection.getresponse(); payload = response.read(); status = response.status
                connection.close(); return status, payload
            self.assertEqual(403, exchange("POST", "/ready", {}, credential=TOKEN)[0])
            self.assertFalse(driver.ready.is_set())
            self.assertEqual(404, exchange("GET", "/foreign")[0])
            self.assertEqual(200, exchange("POST", "/ready", {})[0])
            self.assertEqual((204, b""), exchange("GET", "/next"))
            publish_request(driver, request("alert-button"))
            status, raw = exchange("GET", "/next"); self.assertEqual(200, status)
            self.assertEqual(request("alert-button"), native.decode(raw))
            self.assertEqual(200, exchange("POST", "/response", {
                "sequence": 1, "status": "delivered", "operation": "alert-button",
                "unique": True, "enabled": True, "hittable": True})[0])
            driver.finishing = True
            self.assertEqual(200, exchange("POST", "/finished", {"delivered": 1})[0])
            driver.close()
            self.assertTrue(driver.receipt["cleanup"]["owned_server_stopped"])
            self.assertFalse(driver.receipt["verified"], "A Python HTTP exchange is not XCTest/native execution")

    def test_cleanup_closes_a_real_blocked_owned_http_connection_without_waiting_for_its_body(self):
        with driver_fixture() as driver:
            driver._serve()
            client = socket.create_connection(driver.server.server_address, timeout=3)
            try:
                client.sendall(("POST /ready HTTP/1.1\r\nHost: 127.0.0.1\r\nAuthorization: Bearer " + AUTH +
                    "\r\nContent-Length: 8192\r\n\r\n{").encode())
                deadline = time.monotonic() + 2
                while not driver.server.connections and time.monotonic() < deadline: time.sleep(.005)
                self.assertTrue(driver.server.connections)
                started = time.monotonic(); driver.close()
                self.assertLess(time.monotonic() - started, 3)
                self.assertFalse(driver.thread.is_alive())
                self.assertTrue(driver.receipt["cleanup"]["owned_server_stopped"])
            finally: client.close()

    def test_cleanup_stage_failure_does_not_bypass_other_stages_or_remove_a_live_workspace(self):
        with driver_fixture() as driver:
            visited = []
            def fail(): visited.append("processes"); raise AttributeError("fixed synthetic failure")
            with patch.object(driver, "_stop_processes", side_effect=fail), \
                    patch.object(driver, "_capture_log", side_effect=lambda: visited.append("log")), \
                    patch.object(driver, "_cleanup_runner", side_effect=lambda: visited.append("runner")), \
                    patch.object(driver, "_remove_workspace", side_effect=lambda: visited.append("workspace")):
                with self.assertRaises(RuntimeError): driver.close()
            self.assertEqual(["processes", "log", "runner", "workspace"], visited)
            self.assertEqual([{"stage": "xcode-processes", "type": "AttributeError"}], driver.receipt["cleanup_errors"])
            driver.scratch.mkdir(parents=True); info = driver.scratch.stat()
            driver.scratch_identity = (info.st_dev, info.st_ino)
            driver.receipt["cleanup"]["owned_xcode_process_stopped"] = False
            with self.assertRaises(RuntimeError): driver._remove_workspace()
            self.assertTrue(driver.scratch.is_dir())

    def test_cleanup_reaps_its_actual_python_process_group_not_a_foreign_process(self):
        with driver_fixture() as driver:
            process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], start_new_session=True)
            driver.processes.append(process)
            try:
                driver._stop_processes()
                self.assertIsNotNone(process.poll())
                self.assertTrue(driver.receipt["cleanup"]["owned_xcode_process_stopped"])
            finally:
                if process.poll() is None: process.kill(); process.wait(timeout=5)

    def test_foreign_runner_can_never_be_stopped_or_uninstalled_even_with_the_expected_bundle_id(self):
        with driver_fixture() as driver:
            executed = Mock(side_effect=no_native); driver.execute = executed
            driver.runner_id = "io.github.apdelrahman1911.nativecmpkit.verification.input." + TOKEN + ".xctrunner"
            driver._cleanup_runner(); executed.assert_not_called()
            driver.runner_absence_admitted = True; driver.runner_id = "foreign"
            with self.assertRaises(ValueError): driver._cleanup_runner()
            executed.assert_not_called()
            driver.runner_id = "io.github.apdelrahman1911.nativecmpkit.verification.input." + TOKEN + "-Runner"
            driver.execute = Mock(return_value=subprocess.CompletedProcess([], 0, b"/foreign/app", b""))
            with self.assertRaises(ValueError): driver._cleanup_runner()
            self.assertEqual(1, driver.execute.call_count)
            self.assertEqual("get_app_container", driver.execute.call_args.args[0][2])

    def test_private_log_diagnostics_exclude_the_credential_and_do_not_export_raw_log_or_paths(self):
        with driver_fixture() as driver:
            driver.scratch.mkdir(parents=True)
            driver.log = (driver.scratch / "xcodebuild.log").open("wb")
            driver.log.write(("private unrelated log\n" +
                str(driver.scratch) + "/NativeCmpKitInputTests.swift:2:3: error: " + AUTH + "\n" +
                str(driver.scratch) + "/NativeCmpKitInputTests.swift:3:4: warning: fixed compiler diagnostic\n").encode())
            driver._capture_log()
            serialized = json.dumps(driver.receipt)
            self.assertNotIn(AUTH, serialized); self.assertNotIn("private unrelated log", serialized)
            self.assertNotIn(str(driver.scratch), serialized)
            self.assertEqual([{"severity": "warning", "message": "fixed compiler diagnostic"}], driver.receipt["diagnostics"])

    def test_independent_receipt_tampering_and_python_only_success_cannot_pass_native_admission(self):
        receipt = {"schema_version": 1, "focus": native.FOCUS, "verified": True,
            "source_sha256": {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
                              for relative in (native.SOURCE, native.SWIFT, native.PROJECT, native.SCHEME, native.NATIVE)},
            "bundle_id": BUNDLE, "selected_simulator": DEVICE, "signed_application_executable_sha256": HASH,
            "application_plist_sha256": HASH, "native_launch_pid": 1234,
            "operations": [{"sequence": index, "operation": "tap", "case": case, "status": "delivered",
                            "request_sha256": HASH} for index, case in enumerate(library.IOS_MODAL_XCUI_METHODS, 1)],
            "loopback_only": True, "separate_public_xctest_runner": True,
            "raw_configuration_logs_or_screenshots_uploaded": False, "app_launched_by_input_driver": False,
            "private_input_used": False, "copied_sources_held": True, "runner_ready": True,
            "runner_bundle_id": "io.github.apdelrahman1911.nativecmpkit.verification.input." + TOKEN + ".xctrunner",
            "runner_exit_code": 0, "runner_finished": True, "build": {"exit_code": 0},
            "cleanup": dict.fromkeys(native.CLEANUP, True)}
        def admitted(candidate):
            return native.validate_receipt(candidate, ROOT, library.IOS_MODAL_XCUI_METHODS, bundle_id=BUNDLE,
                device=DEVICE, native_pid=1234, signed_hash=HASH, plist_hash=HASH)
        self.assertTrue(admitted(receipt), "Synthetic receipt schema acceptance is not an actual native result")
        for key, value in (("verified", False), ("schema_version", True), ("native_launch_pid", True),
                           ("native_launch_pid", 1235), ("runner_exit_code", False), ("operations", []),
                           ("loopback_only", False), ("private_input_used", True), ("source_sha256", {}),
                           ("cleanup", {}), ("copied_sources_held", False), ("protocol_error", True),
                           ("cleanup_errors", [{"stage": "synthetic", "type": "ValueError"}]),
                           ("build", {"exit_code": True}), ("runner_bundle_id", "foreign")):
            with self.subTest(key=key): self.assertFalse(admitted({**receipt, key: value}))
        for key, value in (("sequence", True), ("sequence", 2), ("status", "refused"),
                           ("case", "ForeignCase"), ("request_sha256", "short"), ("operation", "launch")):
            malformed = copy.deepcopy(receipt); malformed["operations"][0][key] = value
            self.assertFalse(admitted(malformed))


if __name__ == "__main__":
    unittest.main()
