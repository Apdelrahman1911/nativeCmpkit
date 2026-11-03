# SPDX-License-Identifier: Apache-2.0
"""Owned test-only XCTest input rendezvous; no server or process starts on import.

The Kotlin library tests own all assertions and presentation lifecycles. A
separate nonce-bound UI-test runner attaches to that existing application and
delivers only public XCTest input. No private selectors, fallback callbacks,
foreign app launch, remote input, packages or screenshots are exported.
"""
from __future__ import annotations

import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import math
import os
from pathlib import Path
import plistlib
import re
import secrets
import shutil
import signal
import socket
import stat
import subprocess
import threading
import time

FOCUS = "ui-native-modal-xcui-batch"
SOURCE = "scripts/ci/native_ui_input.py"
SWIFT = "tests/native-ui-input/NativeCmpKitInputTests.swift"
PROJECT = "tests/native-ui-input/NativeCmpKitInput.xcodeproj/project.pbxproj"
SCHEME = "tests/native-ui-input/NativeCmpKitInput.xcodeproj/xcshareddata/xcschemes/NativeCmpKitInput.xcscheme"
NATIVE = "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeXcuiInput.kt"
MAX_BYTES = 8192
MAX_OPERATIONS = 96
TOKEN = re.compile(r"[0-9a-f]{32}\Z")
UUID = re.compile(r"[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}\Z")
BUNDLE = re.compile(r"io\.github\.apdelrahman1911\.nativecmpkit\.verification\.ui\.r[0-9a-f]{12}\.t[0-9a-f]{32}\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
CLEANUP = ("owned_xcode_process_stopped", "owned_server_stopped",
           "owned_runner_absent", "owned_private_workspace_removed")


def read_ordinary(path: Path, limit: int = MAX_BYTES) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= limit:
            raise ValueError("An ordinary bounded native input file is required")
        stream = os.fdopen(descriptor, "rb")
        descriptor = -1  # Ownership transferred only after fdopen succeeds.
        with stream:
            raw = stream.read(limit + 1)
            after = os.fstat(stream.fileno())
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns,
                              s.st_nlink, s.st_mode, s.st_uid)
        if identity(before) != identity(after) or len(raw) != before.st_size:
            raise ValueError("Native input file changed during reading")
        return raw
    finally:
        if descriptor != -1:
            os.close(descriptor)  # Refused directories/FIFOs/fdopen failures cannot leak the descriptor.


def unique_object(pairs):
    document = {}
    for key, value in pairs:
        if key in document:
            raise ValueError("Duplicate native input JSON key")
        document[key] = value
    return document


def decode(raw: bytes) -> dict:
    if not 0 < len(raw) <= MAX_BYTES:
        raise ValueError("Unbounded native input document")
    def finite_float(value):
        result = float(value)
        if not math.isfinite(result): raise ValueError("Nonfinite input")
        return result
    try:
        document = json.loads(raw, object_pairs_hook=unique_object, parse_float=finite_float,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite input")))
    except RecursionError as error:
        raise ValueError("Excessively nested native input JSON") from error
    if type(document) is not dict or any(type(value) in (dict, list) for value in document.values()):
        raise ValueError("Flat native input object required")
    return document


def validate_request(document: dict, sequence: int) -> dict:
    if type(document.get("sequence")) is not int or document["sequence"] != sequence or not 1 <= sequence <= MAX_OPERATIONS:
        raise ValueError("Exact next native input sequence required")
    operation = document.get("operation")
    if type(operation) is not str: raise ValueError("Explicit native operation required")
    keys = {"sequence", "operation", "case"}
    if operation in {"alert-button", "alert-field"}:
        keys |= {"title", "label"}
        if operation == "alert-field":
            keys |= {"text"}
    elif operation in {"tap", "drag"}:
        coordinates = {"x", "y"} | ({"toX", "toY"} if operation == "drag" else set())
        keys |= coordinates
        for key in coordinates:
            value = document.get(key)
            if type(value) not in (int, float) or not .01 <= value <= .99 or not math.isfinite(value):
                raise ValueError("Native coordinates must stay inside this application")
    else:
        raise ValueError("Unreviewed native operation")
    if set(document) != keys:
        raise ValueError("Exact finite native input fields required")
    for key in keys - {"sequence", "x", "y", "toX", "toY"}:
        if type(document[key]) is not str or not 0 < len(document[key]) <= 128:
            raise ValueError("Bounded native input text required")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,127}", document["case"]):
        raise ValueError("Explicit native test identity required")
    return document


def prepare_xctestrun(document: dict, endpoint: str, token: str, bundle_id: str, auth: str) -> dict:
    """Inject only this ephemeral runner's environment, never another target."""
    if (any(type(value) is not str for value in (token, auth, bundle_id, endpoint)) or
            not TOKEN.fullmatch(token) or not TOKEN.fullmatch(auth) or auth == token or
            not BUNDLE.fullmatch(bundle_id) or not bundle_id.endswith(".t" + token)):
        raise ValueError("Owned native input configuration required")
    if (not re.fullmatch(r"http://127\.0\.0\.1:[1-9][0-9]{0,4}", endpoint) or
            int(endpoint.rsplit(":", 1)[1]) > 65535):
        raise ValueError("Loopback-only native input endpoint required")
    if type(document) is not dict:
        raise ValueError("An ordinary XCTest configuration object is required")
    if any(type(key) is not str for key in document):
        raise ValueError("Ordinary XCTest configuration names required")
    if "TestConfigurations" in document:
        configurations = document["TestConfigurations"]
        if type(configurations) is not list or len(configurations) != 1 or type(configurations[0]) is not dict:
            raise ValueError("One owned XCTest configuration required")
        targets = configurations[0].get("TestTargets")
    else:
        targets = [value for key, value in document.items() if not key.startswith("__")]
    if type(targets) is not list or len(targets) != 1 or type(targets[0]) is not dict:
        raise ValueError("One owned XCTest target required")
    target = targets[0]
    if target.get("IsUITestBundle") is not True or target.get("BlueprintName") != "NativeCmpKitInputTests":
        raise ValueError("Only the independent native-input UI target is allowed")
    # Scheme test-action variables use EnvironmentVariables. Preserve Xcode's
    # separate TestingEnvironmentVariables (DYLD paths/placeholders) unchanged.
    # Both fields are documented; this is not proof of the old startup cause.
    environment = target.get("EnvironmentVariables", {})
    testing = target.get("TestingEnvironmentVariables", {})
    if any(type(values) is not dict or any(type(key) is not str or type(value) is not str
            for key, value in values.items()) for values in (environment, testing)):
        raise ValueError("Ordinary string XCTest environment required")
    if any(key.startswith("NATIVECMPKIT_INPUT_") for values in (environment, testing) for key in values):
        raise ValueError("Do not replace preexisting native input credentials")
    # The library app is already installed/launched by its original controller.
    # No app-under-test path may ask Xcode to replace/relaunch it implicitly.
    if target.get("UITargetAppPath") or target.get("UITargetAppBundleIdentifier"):
        raise ValueError("XCTest must not own or launch a second target application")
    target["EnvironmentVariables"] = {
        **environment,
        "NATIVECMPKIT_INPUT_URL": endpoint,
        "NATIVECMPKIT_INPUT_AUTH": auth,
        "NATIVECMPKIT_INPUT_SESSION": token,
        "NATIVECMPKIT_INPUT_BUNDLE": bundle_id,
    }
    target["OnlyTestIdentifiers"] = ["NativeCmpKitInputTests/testDeliverOnlyOwnedLibraryNativeInput"]
    return document


def owned_runner_id(bundle_id: str, token: str) -> bool:
    """Only exact product-derived runner IDs, never a generic/foreign runner."""
    return type(token) is str and bool(TOKEN.fullmatch(token)) and type(bundle_id) is str and bundle_id in {
        "io.github.apdelrahman1911.nativecmpkit.verification.input." + token + suffix
        for suffix in (".xctrunner", "-Runner")
    }


def validate_sources(root: Path) -> bool:
    """Source-only preflight: no HTTP server, compiler, SDK or process starts."""
    for relative in (SOURCE, SWIFT, PROJECT, SCHEME, NATIVE):
        raw = read_ordinary(root / relative, 256 * 1024)
        if relative == PROJECT and raw.count(b"NCK_RUN_TOKEN") != 2:
            raise ValueError("Exact two owned project identity parameters required")
        if relative == NATIVE and re.search(rb"@(Test|Ignore|Disabled|IgnoredTest)\b", raw):
            raise ValueError("Native input helper must remain an enabled zero-test source")
    return True


class InputDriver:
    def __init__(self, root: Path, device: str, bundle_id: str, token: str, execute,
                 signed_hash: str, plist_hash: str):
        if (any(type(value) is not str for value in (device, token, bundle_id, signed_hash, plist_hash)) or
                not UUID.fullmatch(device) or not TOKEN.fullmatch(token) or not BUNDLE.fullmatch(bundle_id) or
                not bundle_id.endswith(".t" + token) or not HASH.fullmatch(signed_hash) or not HASH.fullmatch(plist_hash)):
            raise ValueError("Exact owned application/simulator/session required")
        self._initialize(root, device, bundle_id, token, execute)
        self.receipt.update(signed_application_executable_sha256=signed_hash, application_plist_sha256=plist_hash)

    def _initialize(self, root, device, bundle_id, token, execute):
        self.root, self.device, self.bundle_id, self.token, self.execute = root, device, bundle_id, token, execute
        self.auth = secrets.token_hex(16)  # Never reuse the publicly archived application nonce as a credential.
        if self.auth == token:
            raise ValueError("Native input requires a separate private credential")
        self.scratch = root / "build/ci-runtime/native-input" / token
        self.scratch_identity = None
        self.server = self.thread = self.process = self.log = None
        self.processes = []
        self.copied_sources = {}
        self.ready = threading.Event()
        self.finished = threading.Event()
        self.lock = threading.Lock()
        self.pending = None
        self.pending_hash = None
        self.directory = None
        self.directory_identity = None
        self.finishing = False
        self.runner_id = self.runner_app = self.runner_hash = None
        self.runner_absence_admitted = False
        from library_tests import IOS_MODAL_XCUI_METHODS
        self.methods = IOS_MODAL_XCUI_METHODS
        self.receipt = {"schema_version": 1, "focus": FOCUS, "source_sha256": {}, "operations": [],
                        "bundle_id": bundle_id, "selected_simulator": device,
                        "loopback_only": True, "separate_public_xctest_runner": True,
                        "app_launched_by_input_driver": False, "private_input_used": False,
                        "raw_configuration_logs_or_screenshots_uploaded": False,
                        "verified": False, "cleanup": {}}

    def _control(self, arguments, timeout=90):
        result = self.execute(arguments, timeout)
        if result.returncode:
            raise RuntimeError("Owned native input control failed")
        return result

    def _input_directory(self):
        if self.directory is None or self.directory_identity is None:
            raise ValueError("An admitted owned input directory is required")
        info = self.directory.lstat()
        if (not stat.S_ISDIR(info.st_mode) or (info.st_dev, info.st_ino) != self.directory_identity or
                self.directory.resolve() != self.directory or self.directory.name != self.token):
            raise ValueError("Native input directory ownership changed")
        return self.directory

    def _serve(self):
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_): pass
            def do_GET(self): self.respond()
            def do_POST(self): self.respond()
            def respond(self):
                self.connection.settimeout(5)
                try:
                    if not secrets.compare_digest(self.headers.get("Authorization", ""), "Bearer " + owner.auth):
                        self.send_error(403); return
                    if self.path not in {"/ready", "/next", "/response", "/finished"}:
                        self.send_error(404); return
                    body = None
                    if self.command == "POST":
                        length = self.headers.get("Content-Length", "")
                        if not length.isdigit() or not 0 < int(length) <= MAX_BYTES:
                            self.send_error(400); return
                        body = decode(self.rfile.read(int(length)))
                    payload = owner.handle(self.command, self.path, body)
                    raw = b"" if payload is None else json.dumps(payload, allow_nan=False).encode()
                    self.send_response(204 if payload is None else 200)
                    self.send_header("Content-Length", str(len(raw)))
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(raw)
                except (OSError, ValueError, KeyError, TypeError):
                    owner.receipt["protocol_error"] = True
                    try: self.send_error(400)
                    except OSError: pass  # Owned connection may already have been closed during cleanup.
        class BoundedServer(HTTPServer):
            def __init__(self, *arguments):
                self.connections = set()
                self.connection_lock = threading.Lock()
                super().__init__(*arguments)
            def get_request(self):
                connection, address = super().get_request()
                connection.settimeout(5)
                with self.connection_lock: self.connections.add(connection)
                return connection, address
            def shutdown_request(self, connection):
                try: super().shutdown_request(connection)
                finally:
                    with self.connection_lock: self.connections.discard(connection)
            def close_owned_connections(self):
                with self.connection_lock: connections = tuple(self.connections)
                for connection in connections:
                    try: connection.shutdown(socket.SHUT_RDWR)
                    except OSError: pass
                    connection.close()
        self.server = BoundedServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def _prepare_project(self):
        self.receipt["phase"] = "private-project"
        self.scratch.mkdir(mode=0o700, parents=True, exist_ok=False)
        info = self.scratch.lstat()
        if (not stat.S_ISDIR(info.st_mode) or self.scratch.resolve() != self.scratch or
                info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700):
            raise ValueError("An exclusive ordinary private native input workspace is required")
        self.scratch_identity = (info.st_dev, info.st_ino)
        project_root = self.scratch / "project"
        project_root.mkdir()
        for relative in (SOURCE, SWIFT, PROJECT, SCHEME, NATIVE):
            raw = read_ordinary(self.root / relative, 256 * 1024)
            self.receipt["source_sha256"][relative] = hashlib.sha256(raw).hexdigest()
            if relative.startswith("tests/native-ui-input/"):
                target = project_root / relative.removeprefix("tests/native-ui-input/")
                target.parent.mkdir(parents=True, exist_ok=True)
                if relative == PROJECT:
                    if raw.count(b"NCK_RUN_TOKEN") != 2:
                        raise ValueError("Exact two owned project identity parameters required")
                    raw = raw.replace(b"NCK_RUN_TOKEN", self.token.encode())
                target.write_bytes(raw)
                self.copied_sources[target] = hashlib.sha256(raw).hexdigest()
    def prepare(self) -> dict:
        self._prepare_project()
        self.receipt["phase"] = "owned-application-data"
        data = self._control(["/usr/bin/xcrun", "simctl", "get_app_container", self.device, self.bundle_id, "data"])
        container = Path(data.stdout.decode("utf-8", errors="strict").strip())
        base = Path.home() / "Library/Developer/CoreSimulator/Devices" / self.device / "data/Containers/Data/Application"
        if (not container.is_absolute() or container.is_symlink() or not container.is_dir() or
                container.resolve().parent != base.resolve() or not UUID.fullmatch(container.name)):
            raise ValueError("Unknown or foreign selected-app data container")
        self.directory = container.resolve() / "Documents/NativeCmpKitInput" / self.token
        self.directory.mkdir(parents=True, exist_ok=False)
        self.directory_identity = (self.directory.stat().st_dev, self.directory.stat().st_ino)
        self._input_directory()
        return self._start_runner()

    def _start_runner(self) -> dict:
        self._serve()
        endpoint = "http://127.0.0.1:" + str(self.server.server_port)
        derived = self.scratch / "derived"
        log_path = self.scratch / "xcodebuild.log"
        self.log = log_path.open("xb")
        command = ["/usr/bin/xcodebuild", "build-for-testing", "-project", str(project_root / "NativeCmpKitInput.xcodeproj"),
                   "-scheme", "NativeCmpKitInput", "-destination", "id=" + self.device, "-derivedDataPath", str(derived),
                   "-parallel-testing-enabled", "NO", "-jobs", "1", "CODE_SIGN_IDENTITY=-", "CODE_SIGNING_REQUIRED=NO"]
        started = time.monotonic()
        self.receipt["phase"] = "build-for-testing"
        self.process = subprocess.Popen(command, cwd=self.root, stdout=self.log, stderr=subprocess.STDOUT,
                                        start_new_session=True)
        self.processes.append(self.process)
        code = self.process.wait(timeout=600)  # close() owns the whole process group even after a timeout.
        self.receipt["build"] = {"exit_code": code, "elapsed_seconds": round(time.monotonic()-started, 3)}
        if code:
            raise RuntimeError("Independent public XCTest runner compilation failed")
        if any(hashlib.sha256(read_ordinary(path, 256 * 1024)).hexdigest() != digest
               for path, digest in self.copied_sources.items()):
            raise ValueError("Owned XCTest compiler input changed")
        self.receipt["copied_sources_held"] = True
        self.receipt["phase"] = "xctestrun-admission"
        files = list((derived / "Build/Products").glob("*.xctestrun"))
        if len(files) != 1 or files[0].is_symlink():
            raise ValueError("One fresh owned xctestrun required")
        configuration = prepare_xctestrun(plistlib.loads(read_ordinary(files[0], 1024 * 1024)), endpoint, self.token, self.bundle_id, self.auth)
        self.xctestrun = files[0]
        self.xctestrun.write_bytes(plistlib.dumps(configuration, sort_keys=True))
        self.receipt["phase"] = "runner-identity"
        runners = list((derived / "Build/Products").glob("*-iphonesimulator/NativeCmpKitInputTests-Runner.app"))
        if len(runners) != 1 or runners[0].is_symlink():
            raise ValueError("One owned UI-test runner application required")
        self.runner_app = runners[0]
        info = plistlib.loads(read_ordinary(self.runner_app / "Info.plist", 256 * 1024))
        self.runner_id = info["CFBundleIdentifier"]
        if not owned_runner_id(self.runner_id, self.token):
            raise ValueError("Runner bundle is not this exclusive test session")
        self.runner_executable = info["CFBundleExecutable"]
        if type(self.runner_executable) is not str or not re.fullmatch(r"[A-Za-z0-9_-]+", self.runner_executable):
            raise ValueError("Invalid owned runner executable")
        self.runner_hash = hashlib.sha256(read_ordinary(self.runner_app / self.runner_executable, 100 * 1024**2)).hexdigest()
        self.receipt["runner_bundle_id"] = self.runner_id
        prior = self.execute(["/usr/bin/xcrun", "simctl", "get_app_container", self.device, self.runner_id, "app"], 60)
        from ios_ui_application import missing_app
        if not missing_app(prior):
            raise ValueError("Do not overwrite a foreign XCTest runner")
        self.runner_absence_admitted = True
        self.process = subprocess.Popen(["/usr/bin/xcodebuild", "test-without-building", "-xctestrun", str(self.xctestrun),
            "-destination", "id="+self.device, "-parallel-testing-enabled", "NO", "-maximum-concurrent-test-simulator-destinations", "1",
            "-resultBundlePath", str(self.scratch / "result.xcresult")], cwd=self.root, stdout=self.log,
            stderr=subprocess.STDOUT, start_new_session=True)
        self.processes.append(self.process)
        self._await_runner_readiness()
        self.receipt["phase"] = "native-input"
        environment = os.environ.copy()
        environment["SIMCTL_CHILD_NATIVECMPKIT_NATIVE_INPUT_TOKEN"] = self.token
        return environment

    def _await_runner_readiness(self):
        self.receipt["phase"] = "runner-readiness"
        started = time.monotonic()
        deadline = started + 180
        while not self.ready.wait(.1):
            code = self.process.poll()
            now = time.monotonic()
            if code is not None or now >= deadline:
                self.receipt["runner_startup"] = {
                    "ready": False, "process_exit_code": code,
                    "deadline_reached": now >= deadline,
                    "elapsed_seconds": round(now - started, 3),
                }
                raise RuntimeError("Independent XCTest did not become ready")
        self.receipt["runner_startup"] = {
            "ready": True, "process_exit_code": self.process.poll(),
            "deadline_reached": False, "elapsed_seconds": round(time.monotonic() - started, 3),
        }
        self.receipt["runner_ready"] = True

    def handle(self, method: str, path: str, body: dict | None):
        with self.lock:
            if path == "/ready" and method == "POST" and body == {} and not self.ready.is_set():
                self.ready.set(); return {"ready": True}
            if not self.ready.is_set():
                raise ValueError("Native input runner must first acknowledge readiness")
            if path == "/next" and method == "GET" and body is None:
                if self.finishing:
                    if self.pending is not None: raise ValueError("Unacknowledged native input")
                    return {"operation": "finish"}
                sequence = len(self.receipt["operations"]) + 1
                request = self._input_directory() / ("request-%d.json" % sequence)
                # lstat preserves dangling-symlink refusals; exists() would
                # incorrectly turn a malformed request into a benign no-input poll.
                try: request.lstat()
                except FileNotFoundError: return None
                raw = read_ordinary(request)
                current = validate_request(decode(raw), sequence)
                if current["case"] not in self.methods:
                    raise ValueError("Only the selected native test identities are admitted")
                current_hash = hashlib.sha256(raw).hexdigest()
                if self.pending is not None and (current != self.pending or current_hash != self.pending_hash):
                    raise ValueError("Pending native input mutated")
                self.pending = current
                self.pending_hash = current_hash
                return current
            if path == "/response" and method == "POST" and type(body) is dict and self.pending is not None:
                sequence = self.pending["sequence"]
                if (type(body.get("sequence")) is not int or body["sequence"] != sequence or
                        type(body.get("status")) is not str or body["status"] not in {"delivered", "refused"} or
                        set(body)-{"sequence","status","operation","unique","enabled","hittable","value","foreground","reason"}):
                    raise ValueError("Unknown or out-of-order native input response")
                operation = self.pending["operation"]
                directory = self._input_directory()
                request = directory / ("request-%d.json" % sequence)
                if hashlib.sha256(read_ordinary(request)).hexdigest() != self.pending_hash:
                    raise ValueError("Native request changed before its response")
                if body["status"] == "refused":
                    if set(body) != {"sequence", "status", "reason"} or body.get("reason") not in {
                            "invalidConfiguration", "sequence", "deadline", "foreignOrInactiveApplication",
                            "notUnique", "notHittable", "coordinate", "unknownOperation", "transport"}:
                        raise ValueError("Exact native refusal required")
                else:
                    expected = {"sequence", "status", "operation"}
                    flags = ({"unique", "enabled", "hittable"} if operation == "alert-button" else
                             {"unique"} if operation == "alert-field" else {"foreground"})
                    expected |= flags | ({"value"} if operation == "alert-field" else set())
                    if (set(body) != expected or body.get("operation") != operation or
                            any(body.get(key) is not True for key in flags) or
                            (operation == "alert-field" and
                             (type(body.get("value")) is not str or len(body["value"]) > 128))):
                        raise ValueError("Native operation evidence is incomplete")
                target = directory / ("response-%d.json" % sequence)
                temporary = directory / ("response-%d.tmp" % sequence)
                with temporary.open("xb") as stream:
                    stream.write(json.dumps(body, allow_nan=False).encode())
                os.link(temporary, target)  # Publish complete bytes, never replace or expose a partial response.
                temporary.unlink()
                self.receipt["operations"].append({"sequence": sequence, "operation": self.pending["operation"],
                    "case": self.pending["case"], "status": body["status"],
                    **({"reason": body["reason"]} if body["status"] == "refused" else {}),
                    "request_sha256": self.pending_hash})
                self.pending = None
                self.pending_hash = None
                return {"acknowledged": sequence}
            if (path == "/finished" and method == "POST" and type(body) is dict and
                    type(body.get("delivered")) is int and body == {"delivered": len(self.receipt["operations"])} and
                    self.finishing and self.pending is None and not self.finished.is_set()):
                self.finished.set(); return {"finished": True}
            raise ValueError("Unexpected native input protocol state")

    def finish(self):
        self.receipt["phase"] = "native-input-completion"
        with self.lock:
            self.finishing = True
        deadline = time.monotonic() + 30
        while not self.finished.wait(.1):
            if self.process is None or self.process.poll() is not None or time.monotonic() >= deadline:
                raise RuntimeError("XCTest native input completion missing")
        code = self.process.wait(timeout=90)
        self.receipt["runner_exit_code"] = code
        self.receipt["runner_finished"] = True
        if code != 0 or self.pending is not None or self.receipt.get("protocol_error") or not self.receipt["operations"] or any(r["status"] != "delivered" for r in self.receipt["operations"]):
            raise RuntimeError("Independent XCTest native input failed")

    def _cleanup_error(self, stage, error):
        self.receipt.setdefault("cleanup_errors", []).append({"stage": stage, "type": type(error).__name__})

    def _stop_processes(self):
        processes = self.processes or ([self.process] if self.process is not None else [])
        for index, process in enumerate(reversed(processes)):
            try:
                if process.poll() is None:
                    try: os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        if process.poll() is None: raise
                    try: process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        try: os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            if process.poll() is None: raise
                        process.wait(timeout=10)
            except Exception as error:
                self._cleanup_error("owned-xcode-process-" + str(index), error)
        self.receipt["cleanup"]["owned_xcode_process_stopped"] = all(process.poll() is not None for process in processes)

    def _capture_log(self):
        if self.log is None: return
        self.log.close()
        raw = read_ordinary(self.scratch / "xcodebuild.log", 16 * 1024**2)
        self.receipt["private_log_sha256"] = hashlib.sha256(raw).hexdigest()
        # Fixed source-authored startup phases and typed OS error codes only.
        # Never export arbitrary XCTest/URL/exception/configuration text.
        startup = []
        for line in raw.decode("utf-8", errors="replace").splitlines():
            if len(startup) >= 24: break
            if self.auth in line or self.token in line: continue
            match = re.fullmatch(r"NATIVECMPKIT_XCTEST_STARTUP (setup-enter|setup-configured|setup-refused|ready-enter|ready-acknowledged|finished)", line)
            if match: startup.append({"phase": match[1]}); continue
            match = re.fullmatch(r"NATIVECMPKIT_XCTEST_TRANSPORT domain=(NSURLErrorDomain|NSCocoaErrorDomain|NSPOSIXErrorDomain|other) code=(-?[0-9]{1,10})", line)
            if match and -(2**31) <= int(match[2]) < 2**31:
                startup.append({"phase": "transport", "domain": match[1], "code": int(match[2])})
        self.receipt["startup_diagnostics"] = startup
        diagnostics = []
        for line in raw.decode("utf-8", errors="replace").splitlines():
            if len(diagnostics) >= 24: break
            if self.auth in line: continue
            if not (re.search(r"NativeCmpKitInputTests\.swift:[0-9]+:[0-9]+: (error|warning):", line) or
                    line.startswith("xcodebuild: error:")): continue
            message = re.split(r"\b(error|warning):", line, maxsplit=1)
            if len(message) == 3:
                value = message[2].strip().replace(str(self.scratch), "<owned-input-workspace>")
                diagnostics.append({"severity": message[1], "message": value.replace(self.token, "<session>")[:512]})
        self.receipt["diagnostics"] = diagnostics

    def _cleanup_runner(self):
        # An existing/unknown pre-build app is foreign even if its bytes match.
        if not self.runner_absence_admitted: return
        if not owned_runner_id(self.runner_id, self.token):
            raise ValueError("No exclusive runner identity for cleanup")
        from ios_ui_application import missing_app, stopped_app
        app = self.execute(["/usr/bin/xcrun", "simctl", "get_app_container", self.device, self.runner_id, "app"], 60)
        if missing_app(app):
            self.receipt["cleanup"]["owned_runner_absent"] = True
            return
        if app.returncode != 0: raise ValueError("Unknown owned runner installation state")
        container = Path(app.stdout.decode("utf-8", errors="strict").strip())
        base = Path.home() / "Library/Developer/CoreSimulator/Devices" / self.device / "data/Containers/Bundle/Application"
        if (not container.is_absolute() or container.is_symlink() or not container.is_dir() or
                container.name != "NativeCmpKitInputTests-Runner.app" or not UUID.fullmatch(container.parent.name) or
                container.resolve().parent.parent != base.resolve()):
            raise ValueError("Unknown or foreign installed runner container")
        info = plistlib.loads(read_ordinary(container / "Info.plist", 256 * 1024))
        if (info.get("CFBundleIdentifier") != self.runner_id or info.get("CFBundleExecutable") != self.runner_executable or
                hashlib.sha256(read_ordinary(container / self.runner_executable, 100 * 1024**2)).hexdigest() != self.runner_hash):
            raise ValueError("Refuse cleanup of a different installed runner")
        stop = self.execute(["/usr/bin/xcrun", "simctl", "terminate", self.device, self.runner_id], 60)
        if not stopped_app(stop): raise RuntimeError("Owned XCTest runner stop unverified")
        self._control(["/usr/bin/xcrun", "simctl", "uninstall", self.device, self.runner_id], 60)
        gone = self.execute(["/usr/bin/xcrun", "simctl", "get_app_container", self.device, self.runner_id, "app"], 60)
        if not missing_app(gone): raise RuntimeError("Owned XCTest runner absence unverified")
        self.receipt["cleanup"]["owned_runner_absent"] = True

    def _remove_workspace(self):
        if self.scratch_identity is None: return
        if not self.receipt["cleanup"].get("owned_xcode_process_stopped") or not self.receipt["cleanup"].get("owned_server_stopped"):
            raise RuntimeError("Do not delete a potentially live private input workspace")
        if not self.scratch.exists():
            if self.receipt["cleanup"].get("owned_private_workspace_removed") is True: return
            raise ValueError("Private native input workspace disappeared without owned cleanup")
        info = self.scratch.lstat()
        if (not stat.S_ISDIR(info.st_mode) or (info.st_dev, info.st_ino) != self.scratch_identity or
                self.scratch.resolve() != self.scratch):
            raise ValueError("Private native input workspace ownership changed")
        shutil.rmtree(self.scratch)
        self.receipt["cleanup"]["owned_private_workspace_removed"] = True

    def close(self):
        # Every stage is attempted independently. A test-input bug must neither
        # bypass the original library-app cleanup nor silently become success.
        def attempt(stage, action):
            try: action()
            except Exception as error: self._cleanup_error(stage, error)
        attempt("xcode-processes", self._stop_processes)
        if self.server is not None:
            attempt("server-connections", self.server.close_owned_connections)
            if self.thread is not None and self.thread.is_alive():
                attempt("server-shutdown", self.server.shutdown)
            attempt("server-close", self.server.server_close)
        if self.thread is not None: attempt("server-thread", lambda: self.thread.join(timeout=5))
        self.receipt["cleanup"]["owned_server_stopped"] = self.thread is None or not self.thread.is_alive()
        attempt("private-log", self._capture_log)
        attempt("owned-runner", self._cleanup_runner)
        attempt("private-workspace", self._remove_workspace)
        self.receipt["verified"] = (not self.receipt.get("cleanup_errors") and
            self.receipt.get("runner_finished") is True and type(self.receipt.get("runner_exit_code")) is int and
            self.receipt["runner_exit_code"] == 0 and self.receipt.get("runner_ready") is True and
            self.receipt.get("copied_sources_held") is True and not self.receipt.get("protocol_error") and
            bool(self.receipt["operations"]) and all(r["status"] == "delivered" for r in self.receipt["operations"]) and
            all(self.receipt["cleanup"].get(key) is True for key in CLEANUP))
        if self.receipt.get("cleanup_errors"):
            raise RuntimeError("Independent XCTest cleanup failed; original failures retained")


def validate_receipt(receipt: dict, root: Path, required_methods: tuple[str, ...], *, bundle_id: str,
                     device: str, native_pid: int, signed_hash: str, plist_hash: str) -> bool:
    if type(receipt) is not dict or receipt.get("verified") is not True or receipt.get("focus") != FOCUS:
        return False
    try:
        expected = {relative: hashlib.sha256(read_ordinary(root / relative, 256 * 1024)).hexdigest()
                    for relative in (SOURCE, SWIFT, PROJECT, SCHEME, NATIVE)}
        operations = receipt["operations"]
        token = bundle_id.rsplit(".t", 1)[-1]
        return (type(receipt.get("schema_version")) is int and receipt["schema_version"] == 1 and
                type(bundle_id) is str and BUNDLE.fullmatch(bundle_id) and
                type(device) is str and UUID.fullmatch(device) and
                type(signed_hash) is str and HASH.fullmatch(signed_hash) and
                type(plist_hash) is str and HASH.fullmatch(plist_hash) and
                receipt.get("source_sha256") == expected and
                receipt.get("bundle_id") == bundle_id and receipt.get("selected_simulator") == device and
                receipt.get("signed_application_executable_sha256") == signed_hash and
                receipt.get("application_plist_sha256") == plist_hash and
                type(native_pid) is int and 0 < native_pid < 2**31 and
                type(receipt.get("native_launch_pid")) is int and receipt["native_launch_pid"] == native_pid and
                type(operations) is list and 1 <= len(operations) <= MAX_OPERATIONS and
                all(type(r) is dict and set(r) == {"sequence", "operation", "case", "status", "request_sha256"} for r in operations) and
                all(type(r["sequence"]) is int for r in operations) and
                [r["sequence"] for r in operations] == list(range(1, len(operations)+1)) and
                all(r["status"] == "delivered" and r["operation"] in {"alert-button","alert-field","tap","drag"} and
                    re.fullmatch(r"[0-9a-f]{64}", r["request_sha256"]) for r in operations) and
                {r["case"] for r in operations} == set(required_methods) and
                receipt.get("loopback_only") is True and receipt.get("separate_public_xctest_runner") is True and
                receipt.get("raw_configuration_logs_or_screenshots_uploaded") is False and
                receipt.get("app_launched_by_input_driver") is False and receipt.get("private_input_used") is False and
                receipt.get("copied_sources_held") is True and receipt.get("runner_ready") is True and
                owned_runner_id(receipt.get("runner_bundle_id"), token) and
                type(receipt.get("runner_exit_code")) is int and receipt["runner_exit_code"] == 0 and
                type(receipt.get("build")) is dict and type(receipt["build"].get("exit_code")) is int and
                receipt["build"]["exit_code"] == 0 and receipt.get("runner_finished") is True and
                not receipt.get("protocol_error") and not receipt.get("cleanup_errors") and
                all(receipt.get("cleanup", {}).get(k) is True for k in CLEANUP))
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return False
