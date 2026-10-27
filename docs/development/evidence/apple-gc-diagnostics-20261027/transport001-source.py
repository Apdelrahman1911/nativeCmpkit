#!/usr/bin/env python3
"""Owned simulator application transport for KGP's *actual* native test parser.

Never generates JUnit, selects a foreign device/app, uploads a package, accepts
filtered/zero suites, or infers success from simctl launch acceptance. The app
bundle is a local disposable library-test host, not a sample or distributable.
Python adversarial fixtures are tooling evidence, not Apple runtime verification.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import selectors
import shutil
import signal
import struct
import subprocess
import sys
import time
import uuid

import apple_crash_diagnostics as crashes
import library_tests as lt
import runtime_context as runtime

TASK = ":calf-ui:iosSimulatorArm64ApplicationTest"
HOST_SOURCE = "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt"
HOST_TEST = "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHostTest.kt"
EXPECTED_BINARY_DIRECTORY = "calf-ui/build/bin/iosSimulatorArm64/applicationDebugTest"
APP_EXECUTABLE = "NativeCmpkitLibraryTests"
MAX_BINARY_BYTES = 1024 * 1024**2
MAX_STREAM_BYTES = 16 * 1024**2
MAX_LINE_BYTES = 512 * 1024
APP_TIMEOUT_SECONDS = 1920
TEST_ARGUMENTS = {"--ktest_logger=TEAMCITY", "--ktest_no_exit_code"}
IMAGE_LIFETIME_CASE = ("com.mohamedrejeb.calf.ui.utils.UIImageConversionTest",
                       "returnedImageOwnsItsPixelsAfterTemporaryArraysAndContextsAreCollected")
IMAGE_LIFETIME_STEPS = (
    (("retained-ready", None),) +
    tuple((phase, iteration) for iteration in range(1, 21) for phase in ("before-conversion", "before-gc", "after-gc")) +
    (("before-verify", None), ("verified", None))


def macho_simulator_identity(path: Path) -> dict:
    """Read the linked executable's real header/load commands, not its filename."""
    stat = path.stat()
    if not path.is_file() or path.is_symlink() or stat.st_nlink != 1 or not 32 <= stat.st_size <= MAX_BINARY_BYTES:
        raise ValueError("Expected a bounded regular unshared test executable")
    with path.open("rb") as handle:
        header = handle.read(32)
        magic, cpu, subtype, kind, count, size, flags, reserved = struct.unpack("<8I", header)
        if magic != 0xFEEDFACF or cpu != 0x0100000C or kind != 2:
            raise ValueError("UIKit host requires an Arm64 Mach-O executable, not a KLIB/framework/device/fat binary")
        if count > 4096 or size > 1024**2 or size > stat.st_size - 32:
            raise ValueError("Unbounded or truncated Mach-O load-command table")
        commands = handle.read(size)
    offset = 0
    builds = []
    executable_uuids = []
    for _ in range(count):
        if offset + 8 > len(commands):
            raise ValueError("Truncated Mach-O load command")
        command, length = struct.unpack_from("<2I", commands, offset)
        if length < 8 or length % 8 or offset + length > len(commands):
            raise ValueError("Invalid Mach-O load-command length")
        if command == 0x32:  # LC_BUILD_VERSION, current Kotlin/Native/Xcode model.
            if length < 24:
                raise ValueError("Truncated Apple build-version command")
            apple_platform, minimum, sdk, tools = struct.unpack_from("<4I", commands, offset + 8)
            if length != 24 + tools * 8:
                raise ValueError("Invalid build-version tool table")
            def version(value):
                return f"{value >> 16}.{(value >> 8) & 255}.{value & 255}"
            builds.append({"platform": apple_platform, "minimum_os": version(minimum), "sdk": version(sdk)})
        if command == 0x1B:  # LC_UUID: real linked slice identity for crash correlation.
            if length != 24:
                raise ValueError("Invalid Mach-O UUID command")
            identifier = uuid.UUID(bytes=commands[offset + 8:offset + 24])
            if identifier.int == 0 or executable_uuids:
                raise ValueError("Zero or ambiguous Mach-O executable UUID")
            executable_uuids.append(str(identifier))
        offset += length
    if offset != len(commands) or len(builds) != 1 or builds[0]["platform"] != 7:
        raise ValueError("Expected exactly one explicit iOS-simulator build version")
    after = path.stat()
    if (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError("Executable changed during Mach-O inspection")
    return {"architecture": "arm64", "file_type": "executable", **builds[0],
            "executable_uuid": executable_uuids[0] if executable_uuids else None}


def app_information(bundle_id: str, minimum_os: str) -> dict:
    if not re.fullmatch(r"io\.github\.apdelrahman1911\.nativecmpkit\.verification\.ui\.r[0-9a-f]{12}\.t[0-9a-f]{32}", bundle_id):
        raise ValueError("Expected a fresh source-bound owned verification bundle identifier")
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){2}", minimum_os):
        raise ValueError("Minimum OS must come from the linked Mach-O")
    return {"CFBundleIdentifier": bundle_id, "CFBundleExecutable": APP_EXECUTABLE,
            "CFBundleName": "NativeCmpKit library tests", "CFBundlePackageType": "APPL",
            "CFBundleVersion": "1", "CFBundleShortVersionString": "0.1.0",
            "CFBundleSupportedPlatforms": ["iPhoneSimulator"], "LSRequiresIPhoneOS": True,
            "MinimumOSVersion": minimum_os, "UIDeviceFamily": [1, 2],
            # Required by Compose's strict iPhone plist sanity check. Keep that
            # check enabled; a fixture crash must not become a silent bypass.
            "CADisableMinimumFrameDurationOnPhone": True,
            "UILaunchScreen": {}, "UIApplicationSupportsIndirectInputEvents": True}


def teamcity_fields(line: str) -> tuple[str, dict] | None:
    if not line.startswith("##teamcity["):
        return None
    match = re.fullmatch(r"##teamcity\[([A-Za-z]+)((?: [A-Za-z][A-Za-z0-9]*='(?:\|.|[^'\r\n])*')*)\]", line)
    if not match:
        raise ValueError("Malformed native TeamCity frame; do not fabricate replacement XML")
    fields = {}
    escapes = {"|": "|", "'": "'", "n": "\n", "r": "\r", "[": "[", "]": "]"}
    for key, value in re.findall(r" ([A-Za-z][A-Za-z0-9]*)='((?:\|.|[^'\r\n])*)'", match[2]):
        if key in fields:
            raise ValueError("Duplicate TeamCity attribute")
        def decode(found):
            if found[1] not in escapes:
                raise ValueError("Unknown TeamCity escape")
            return escapes[found[1]]
        fields[key] = re.sub(r"\|(.)", decode, value)
    return match[1], fields


class NativeProtocol:
    """Independent transport checks; KGP still owns actual failure/JUnit parsing."""
    def __init__(self, bundle_id: str | None = None):
        if bundle_id is not None and not crashes.BUNDLE.fullmatch(bundle_id):
            raise ValueError("Expected an exact owned verification launch bundle")
        self.expected_bundle = bundle_id
        self.observed_launch_pid = None
        self.transport_observation = None
        self.image_lifetime_observation = None
        self.active = None
        self.completed = None
        self.stack = []
        self.open_case = None
        self.cases = {}
        self.stream_bytes = 0
        self.startup_failure_observation = None

    def feed(self, line: str):
        self.stream_bytes += len((line + "\n").encode())
        if self.stream_bytes > MAX_STREAM_BYTES or len(line.encode()) > MAX_LINE_BYTES:
            raise ValueError("Native application output exceeds bounded transport")
        if self.startup_failure_observation is not None:
            raise ValueError("Native transport already failed at startup")
        if self.expected_bundle is not None and line.startswith(self.expected_bundle + ":"):
            launch = re.fullmatch(re.escape(self.expected_bundle) + r": ([1-9][0-9]{0,9})", line)
            if (launch is None or int(launch[1]) > 2**31 - 1 or self.observed_launch_pid is not None or
                    self.active is not None or self.completed is not None or self.cases):
                raise ValueError("Invalid, duplicate or late exact simulator launch PID")
            self.observed_launch_pid = int(launch[1])
            return
        image = re.fullmatch(
            r"NATIVECMPKIT_UIKIT_IMAGE_LIFETIME phase=(retained-ready|before-conversion|before-gc|after-gc|before-verify|verified)"
            r"(?: iteration=([1-9][0-9]?))? mainThread=(true|false)", line)
        if image:
            if self.active is None or self.completed is not None or self.open_case != IMAGE_LIFETIME_CASE:
                raise ValueError("Image lifetime diagnostic outside its exact active native testcase")
            previous = self.image_lifetime_observation
            index = previous["marker_count"] if previous else 0
            iteration = int(image[2]) if image[2] else None
            if index >= len(IMAGE_LIFETIME_STEPS) or (image[1], iteration) != IMAGE_LIFETIME_STEPS[index]:
                raise ValueError("Missing, duplicate or reordered finite image lifetime diagnostic")
            self.image_lifetime_observation = {
                "marker_count": index + 1, "last_phase": image[1], "last_iteration": iteration,
                "main_thread": image[3] == "true", "retained_image_bytes_verified": image[1] == "verified"}
            if image[3] != "true":
                raise ValueError("Image lifetime callback is not on the actual main thread")
            return
        startup = re.fullmatch(
            r"NATIVECMPKIT_UIKIT_STARTUP_TIMEOUT active=(true|false) key=(true|false) hidden=(true|false) "
            r"rootAttached=(true|false) rootNativeEqual=(true|false) workerStarted=false", line)
        if startup:
            if self.active is not None or self.completed is not None or self.cases:
                raise ValueError("Startup timeout is outside the pre-worker lifecycle")
            # Known, bounded booleans only. Retain this failure even though the
            # frame is NOT forwarded/accepted as TeamCity or successful transport.
            self.startup_failure_observation = {
                key: value == "true" for key, value in zip(
                    ("active", "key", "hidden", "root_attached", "root_native_equal"), startup.groups())}
            self.startup_failure_observation["worker_started"] = False
            raise ValueError("UIKit startup readiness failed")
        active = re.fullmatch(r"NATIVECMPKIT_UIKIT_ACTIVE mainWorker=([1-9][0-9]*) ownedWorker=([1-9][0-9]*)", line)
        complete = re.fullmatch(r"NATIVECMPKIT_UIKIT_COMPLETED runnerExit=([0-9]+) workerTerminated=true", line)
        if active:
            if self.active is not None or self.completed is not None or active[1] == active[2]:
                raise ValueError("Expected exactly one genuine main/owned-worker activation")
            self.active = {"main_worker": int(active[1]), "owned_worker": int(active[2])}
            return
        if complete:
            if self.completed is not None or self.active is None or int(complete[1]) != 0 or self.stack or self.open_case is not None:
                raise ValueError("Unexpected native runner/worker completion contract")
            self.completed = {"runner_exit": 0, "worker_terminated": True}
            return
        if line.startswith("NATIVECMPKIT_UIKIT_"):
            raise ValueError("Native application reported an error, timeout or unknown lifecycle marker")
        record = teamcity_fields(line)
        if record is None:
            return
        kind, fields = record
        if self.active is None or self.completed is not None:
            raise ValueError("Native test frame outside the owned UIKit application lifecycle")
        if kind in {"testSuiteStarted", "testSuiteFinished", "testStarted", "testFinished", "testFailed", "testIgnored"}:
            name = fields.get("name", "")
            if not name or len(name) > 4096 or any(c in name for c in "\r\n"):
                raise ValueError("Missing or invalid native testcase/suite identity")
        if kind == "testSuiteStarted":
            if self.open_case is not None or len(self.stack) >= 32:
                raise ValueError("Unexpected nested/active native suite")
            self.stack.append(name)
        elif kind == "testSuiteFinished":
            if not self.stack or self.stack[-1] != name or self.open_case is not None:
                raise ValueError("Unbalanced native suite completion")
            self.stack.pop()
        elif kind in {"testStarted", "testIgnored"}:
            if not self.stack or self.open_case is not None:
                raise ValueError("Native testcase has no suite or overlaps another case")
            key = (self.stack[-1], name)
            if key in self.cases or len(self.cases) >= lt.MAX_CASES:
                raise ValueError("Duplicate/unbounded native testcase")
            self.cases[key] = {"classname": key[0], "name": key[1], "status": "skipped" if kind == "testIgnored" else "running",
                               "finished": kind == "testIgnored"}
            if kind == "testStarted":
                self.open_case = key
        elif kind in {"testFinished", "testFailed"}:
            if self.open_case is None or self.open_case[1] != name:
                raise ValueError("Native result has no matching started testcase")
            case = self.cases[self.open_case]
            if kind == "testFailed":
                if case["status"] != "running":
                    raise ValueError("Duplicate native testcase failure")
                case["status"] = "failed"
            else:
                if case["status"] == "running":
                    if self.open_case == IMAGE_LIFETIME_CASE and (self.image_lifetime_observation is None or
                            self.image_lifetime_observation["marker_count"] != len(IMAGE_LIFETIME_STEPS) or
                            self.image_lifetime_observation["retained_image_bytes_verified"] is not True):
                        raise ValueError("A passing image lifetime case needs its complete actual diagnostic sequence")
                    case["status"] = "passed"
                case["finished"] = True
                self.open_case = None
        elif kind not in {"testStdOut", "testStdErr", "message", "testCount"}:
            raise ValueError("Unreviewed native test protocol record")

    def partial(self) -> dict:
        """Finished frames only; interruption is never promoted to a testcase.

        KGP owns its real XML/failure synthesis. This observation does not emit
        XML, infer a runner result, claim crash absence or satisfy any test gate.
        """
        finished = [{k: c[k] for k in ("classname", "name", "status")} for c in self.cases.values() if c["finished"]]
        pending = self.cases.get(self.open_case)
        return {"activation": self.active, "completion": self.completed,
                "complete_native_lifecycle": self.active is not None and self.completed is not None and
                    not self.stack and self.open_case is None and bool(finished),
                "testcases": finished, "counts": lt.case_counts(finished),
                "unfinished_testcase": {"classname": pending["classname"], "name": pending["name"],
                    "status": "incomplete", "failure_frame_observed": pending["status"] == "failed"} if pending else None,
                "open_suites": list(self.stack), "stream_bytes": self.stream_bytes,
                "observed_launch_pid": self.observed_launch_pid,
                "image_lifetime_observation": self.image_lifetime_observation}

    def finish(self, process_exit: int) -> dict:
        if (process_exit != 0 or self.startup_failure_observation is not None or self.active is None or
                self.completed is None or self.stack or self.open_case is not None):
            raise ValueError("App crash/transport failure or missing complete native lifecycle")
        cases = list(self.cases.values())
        if not cases or not all(c["finished"] for c in cases) or all(c["status"] == "skipped" for c in cases):
            raise ValueError("Zero/incomplete native test execution is not successful transport")
        return {"activation": self.active, "completion": self.completed,
                "testcases": [{k: c[k] for k in ["classname", "name", "status"]} for c in cases],
                "counts": lt.case_counts(cases), "stream_bytes": self.stream_bytes,
                "observed_launch_pid": self.observed_launch_pid,
                "image_lifetime_observation": self.image_lifetime_observation}


def execute_control(argv: list[str], timeout: int = 90) -> subprocess.CompletedProcess:
    result = subprocess.run(argv, cwd=lt.ROOT, capture_output=True, timeout=timeout)
    if len(result.stdout) + len(result.stderr) > 1024**2:
        raise ValueError("Unbounded simulator-control result")
    return result


def control_status(result: subprocess.CompletedProcess) -> dict:
    """Retain bounded structured control-error identities, never a transcript.

    Domain/code observations explain a fail-closed simctl/codesign refusal. An
    unexpected service/error identity does not authorize foreign app mutation or
    a retry. Actual missing/already-stopped simctl behavior still needs Apple CI.
    """
    matches = re.findall(r"\(domain=([A-Za-z][A-Za-z0-9_.-]{0,127}), code=(-?[0-9]{1,10})\)",
                         result.stderr[:65536].decode("utf-8", errors="replace"))
    return {"exit_code": result.returncode,
            "error_identities": [{"domain": domain, "code": int(code)} for domain, code in matches[:3]]}


def missing_app(result: subprocess.CompletedProcess) -> bool:
    return result.returncode == 2 and {"domain": "NSPOSIXErrorDomain", "code": 2} in control_status(result)["error_identities"]


def stopped_app(result: subprocess.CompletedProcess) -> bool:
    return result.returncode == 0 or (result.returncode == 3 and
        {"domain": "NSPOSIXErrorDomain", "code": 3} in control_status(result)["error_identities"])


def installed_identity(result: subprocess.CompletedProcess, bundle_id: str, signed_hash: str, plist_hash: str) -> bool:
    if result.returncode != 0:
        return False
    path = Path(result.stdout.decode("utf-8").strip())
    if not path.is_absolute() or path.name != "NativeCmpkitLibraryTests.app" or path.is_symlink() or not path.is_dir():
        return False
    for name, digest in [(APP_EXECUTABLE, signed_hash), ("Info.plist", plist_hash)]:
        file = path / name
        if not file.is_file() or file.is_symlink() or file.stat().st_nlink != 1 or lt.sha256(file) != digest:
            return False
    return plistlib.loads((path / "Info.plist").read_bytes()).get("CFBundleIdentifier") == bundle_id


def forward_application(argv: list[str], protocol: NativeProtocol, timeout: int = APP_TIMEOUT_SECONDS) -> dict:
    """Preserve real frames verbatim through KGP, while bounding owned transport."""
    started = time.monotonic()
    transport = {"started_at_utc": lt.utc_now(), "console_process_exit": None,
                 "console_process_exit_after_cleanup": None, "console_cleanup_requested": False}
    process = subprocess.Popen(argv, cwd=lt.ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               start_new_session=True, bufsize=0)
    pending = b""
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while selector.get_map():
                if time.monotonic() - started > timeout:
                    raise TimeoutError("Owned UIKit application timed out")
                if shutil.disk_usage(lt.ROOT).free < 8192 * 1024**2:
                    raise OSError("UIKit transport disk reserve unavailable")
                for key, _ in selector.select(timeout=0.25):
                    block = os.read(key.fd, 65536)
                    if not block:
                        selector.unregister(key.fileobj)
                        break
                    pending += block
                    while b"\n" in pending:
                        line, pending = pending.split(b"\n", 1)
                        text = line.decode("utf-8", errors="strict").rstrip("\r")
                        protocol.feed(text)
                        sys.stdout.buffer.write(line + b"\n")
                        sys.stdout.buffer.flush()
                    if len(pending) > MAX_LINE_BYTES:
                        raise ValueError("Unbounded incomplete native protocol line")
        if pending:
            protocol.feed(pending.decode("utf-8", errors="strict"))
            sys.stdout.buffer.write(pending + b"\n")
            sys.stdout.buffer.flush()
        result = process.wait(timeout=30)
        summary = protocol.finish(result)
        return {"process_exit": result, "elapsed_seconds": round(time.monotonic() - started, 2), **summary}
    except BaseException as error:
        # Fixed error type only. Never retain a report/app/environment message.
        transport["error_type"] = type(error).__name__
        raise
    finally:
        transport["console_process_exit"] = process.poll()
        try:
            if transport["console_process_exit"] is None:
                # Only our xcrun console group, NOT an inferred native app PID.
                transport["console_cleanup_requested"] = True
                lt.terminate_owned(process)
        finally:
            transport.update(finished_at_utc=lt.utc_now(), elapsed_seconds=round(time.monotonic() - started, 2),
                             console_process_exit_after_cleanup=process.poll())
            protocol.transport_observation = transport
            if process.stdout:
                process.stdout.close()


def run(binary_relative: str, arguments: list[str]) -> dict:
    if platform.system() != "Darwin" or platform.machine().lower() != "arm64":
        raise ValueError("Genuine UIKit application execution requires the actual macOS Arm64 host")
    if len(arguments) != 2 or set(arguments) != TEST_ARGUMENTS:
        raise ValueError("Only KGP's full TEAMCITY/no-exit-code protocol is allowed; no arbitrary filters/arguments")
    device = os.environ.get("NATIVECMPKIT_UIKIT_SIMULATOR", "")
    if not runtime.UUID.fullmatch(device):
        raise ValueError("Use the exact task-recorded simulator, not a guessed/default device")
    root = lt.ROOT
    binary = lt.safe_path(root, binary_relative)
    expected = lt.safe_path(root, EXPECTED_BINARY_DIRECTORY)
    if binary.parent != expected or binary.suffix != ".kexe" or not os.access(binary, os.X_OK):
        raise ValueError("Expected the distinct linked application test executable")
    result_relative = os.environ.get("NATIVECMPKIT_UIKIT_RESULT_ROOT", "")
    result_root = lt.safe_path(root, result_relative)
    base = lt.safe_path(root, "build/ci-verification")
    if result_root == base or not result_root.is_relative_to(base):
        raise ValueError("Application receipts must stay in the owned verification output")
    token = uuid.uuid4().hex
    output = lt.safe_path(root, (result_root / token).relative_to(root).as_posix())
    output.mkdir(parents=True, exist_ok=False)
    receipt = {"schema_version": 1, "task": TASK, "started_at_utc": lt.utc_now(),
               "transport_passed": False, "packages_published": False, "release_readiness_certified": False,
               "scope": "Owned real UIKit application transport. Real KGP TeamCity/JUnit decides testcase failures; launch/completion alone never establishes library/release success.",
               "steps": {}, "cleanup": {}, "application_protocol": None}
    app = output / "NativeCmpkitLibraryTests.app"
    bundle_id = None
    signed_hash = plist_hash = None
    installed = False
    phase = "runtime-preflight"
    protocol = NativeProtocol()
    try:
        before = runtime.capture(expected_arch="arm64", apple=True, device=device, require_booted=True, require_clean=True)
        receipt.update(source_revision=before["source_revision"], source_tree_dirty=before["source_tree_dirty"], runtime_before=before)
        binary_hash = lt.sha256(binary)
        identity = macho_simulator_identity(binary)
        receipt.update(binary_path=binary_relative, binary_sha256=binary_hash, macho=identity)
        bundle_id = f"io.github.apdelrahman1911.nativecmpkit.verification.ui.r{before['source_revision'][:12]}.t{token}"
        receipt["bundle_id"] = bundle_id
        protocol = NativeProtocol(bundle_id=bundle_id)
        phase = "foreign-app-preflight"
        preexisting = execute_control(["/usr/bin/xcrun", "simctl", "get_app_container", device, bundle_id, "app"])
        receipt["steps"][phase] = {**control_status(preexisting), "preexisting_app_absence_verified": missing_app(preexisting)}
        if not missing_app(preexisting):
            raise ValueError("Foreign installed app or unknown absence check; never overwrite it")
        phase = "local-bundle"
        if shutil.disk_usage(root).free < 8192 * 1024**2 + binary.stat().st_size * 2:
            raise OSError("Application staging would violate the owned disk reserve")
        app.mkdir()
        shutil.copy2(binary, app / APP_EXECUTABLE)
        (app / "Info.plist").write_bytes(plistlib.dumps(app_information(bundle_id, identity["minimum_os"]), sort_keys=True))
        phase = "adhoc-sign-local-verification-app"
        sign = execute_control(["/usr/bin/codesign", "--force", "--sign", "-", str(app)], 120)
        receipt["steps"][phase] = {**control_status(sign), "remote_signing_or_publication": False}
        if sign.returncode:
            raise RuntimeError("Ad-hoc local application signing failed")
        signed_hash, plist_hash = lt.sha256(app / APP_EXECUTABLE), lt.sha256(app / "Info.plist")
        receipt.update(signed_application_executable_sha256=signed_hash, application_plist_sha256=plist_hash)
        phase = "install-owned-app"
        result = execute_control(["/usr/bin/xcrun", "simctl", "install", device, str(app)], 180)
        receipt["steps"][phase] = control_status(result)
        # Reconcile even an uncertain install failure before any cleanup/retry.
        container = execute_control(["/usr/bin/xcrun", "simctl", "get_app_container", device, bundle_id, "app"])
        installed = installed_identity(container, bundle_id, signed_hash, plist_hash)
        receipt["steps"][phase]["installed_owned_bytes_verified"] = installed
        receipt["steps"][phase]["container_status"] = control_status(container)
        if result.returncode or not installed:
            raise RuntimeError("Owned installation/byte readback failed; do not retry or remove foreign data")
        phase = "launch-and-real-test-transport"
        receipt["application_protocol"] = forward_application(
            ["/usr/bin/xcrun", "simctl", "launch", "--console", "--terminate-running-process", device, bundle_id, *arguments],
            protocol)
        phase = "post-runtime-and-binary"
        after = runtime.capture(expected_arch="arm64", apple=True, device=device, require_booted=True, require_clean=True)
        receipt["runtime_after"] = after
        receipt["binary_sha256_after"] = lt.sha256(binary)
        if before["source_revision"] != after["source_revision"] or before["simulator"] != after["simulator"] or receipt["binary_sha256_after"] != binary_hash:
            raise ValueError("Selected device/source/linked binary changed during native execution")
        receipt["transport_passed"] = True
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        receipt["error"] = {"phase": phase, "type": type(error).__name__}
        # No arbitrary exception/app/environment transcript is archived.
    finally:
        if protocol.transport_observation is not None:
            receipt["application_transport"] = protocol.transport_observation
        if not receipt["transport_passed"] and phase == "launch-and-real-test-transport":
            receipt["application_protocol_partial"] = protocol.partial()
            observed = protocol.transport_observation or {}
            try:
                receipt["owned_crash_diagnostics"] = crashes.collect(
                    Path.home() / "Library/Logs/DiagnosticReports", bundle_id=bundle_id,
                    pid=protocol.observed_launch_pid, executable_uuid=identity.get("executable_uuid"),
                    executable=APP_EXECUTABLE, started_utc=observed.get("started_at_utc", ""),
                    ended_utc=observed.get("finished_at_utc", ""))
            except (OSError, ValueError, TypeError, KeyError, RecursionError) as error:
                receipt["owned_crash_diagnostics"] = {"status": "unavailable", "error_type": type(error).__name__,
                    "raw_reports_uploaded": False, "native_functionality_verified": False}
            # A missing/bad/matching report NEVER changes the failed transport.
        if protocol.startup_failure_observation is not None:
            receipt["startup_failure_observation"] = protocol.startup_failure_observation
            receipt["transport_passed"] = False
        if installed:
            try:
                lease = execute_control(["/usr/bin/xcrun", "simctl", "get_app_container", device, bundle_id, "app"])
                still_owned = installed_identity(lease, bundle_id, signed_hash, plist_hash)
                receipt["cleanup"]["owned_app_identity_reverified"] = still_owned
                if not still_owned:
                    raise ValueError("Installed app identity changed; refuse foreign cleanup")
                stop = execute_control(["/usr/bin/xcrun", "simctl", "terminate", device, bundle_id], 60)
                # Normally exitProcess already stopped it. The exact container
                # identity, not a guessed PID or ignored error, authorizes uninstall.
                receipt["cleanup"]["terminate_exit_code"] = stop.returncode
                receipt["cleanup"]["terminate_status"] = control_status(stop)
                receipt["cleanup"]["owned_app_stopped_verified"] = stopped_app(stop)
                uninstall = execute_control(["/usr/bin/xcrun", "simctl", "uninstall", device, bundle_id], 120)
                gone = execute_control(["/usr/bin/xcrun", "simctl", "get_app_container", device, bundle_id, "app"])
                receipt["cleanup"].update(uninstall_exit_code=uninstall.returncode,
                                           uninstall_status=control_status(uninstall),
                                           absence_status=control_status(gone),
                                           owned_app_absence_verified=missing_app(gone))
                if uninstall.returncode or not missing_app(gone):
                    raise RuntimeError("Owned application uninstall/absence is unverified")
                if not stopped_app(stop):
                    # Still release our verified installation on a stop error;
                    # preserve the uncertainty as failure, never silent success.
                    raise RuntimeError("Owned application stop/termination is unverified")
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                receipt["cleanup"]["error_type"] = type(error).__name__
                receipt["transport_passed"] = False
        else:
            receipt["cleanup"]["foreign_app_mutated"] = False
        if app.exists():
            try:
                if app.is_symlink() or app.parent != output:
                    raise ValueError("Local application ownership changed")
                shutil.rmtree(app)  # only this invocation's disposable bundle.
                receipt["cleanup"]["owned_local_bundle_removed"] = True
            except (OSError, ValueError) as error:
                receipt["cleanup"]["local_error_type"] = type(error).__name__
                receipt["transport_passed"] = False
        receipt["finished_at_utc"] = lt.utc_now()
        lt.write_json(output / "receipt.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    options, arguments = parser.parse_known_args()
    try:
        binary = options.binary.absolute().relative_to(lt.ROOT).as_posix()
        result = run(binary, arguments)
        print("NATIVECMPKIT_UIKIT_TRANSPORT passed=" + str(result["transport_passed"]).lower(), flush=True)
        return 0 if result["transport_passed"] else 2
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print("Owned UIKit application transport refused: " + type(error).__name__, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
