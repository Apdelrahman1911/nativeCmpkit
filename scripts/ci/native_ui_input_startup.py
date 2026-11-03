# SPDX-License-Identifier: Apache-2.0
"""Independent Swift/XCTest rendezvous only; ZERO library app/input acceptance.

Uses exactly the real input runner's compiler/startup/server/cleanup paths. No
Kotlin build, sample, installed AUT, fake signed binary or library XML is used.
The reserved AUT identifier is configuration only and is never launched.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import platform
import re
import secrets
import subprocess
import time

import library_tests as library
import native_ui_input as native

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = "build/ci-verification/xctest-startup/receipt.json"
REVISION = re.compile(r"[0-9a-f]{40}\Z")


class StartupDriver(native.InputDriver):
    def __init__(self, root, device, bundle_id, token, execute):
        if (any(type(value) is not str for value in (device, bundle_id, token)) or
                not native.UUID.fullmatch(device) or not native.TOKEN.fullmatch(token) or
                not native.BUNDLE.fullmatch(bundle_id) or not bundle_id.endswith(".t" + token)):
            raise ValueError("One reserved startup-only simulator/session required")
        self._initialize(root, device, bundle_id, token, execute)
        self.receipt.update(focus="xctest-startup-only", startup_passed=False,
                            library_application_installed=False, library_application_launched=False,
                            native_library_methods_executed=0)
        # The runner finishes at its first poll; it cannot ask for app input or
        # need a fabricated application container while no AUT exists.
        self.finishing = True

    def verify_startup(self):
        self._prepare_project()
        self._start_runner()
        if not self.finished.wait(30):
            raise RuntimeError("Startup-only XCTest completion missing")
        code = self.process.wait(timeout=90)
        self.receipt.update(runner_exit_code=code, runner_finished=True)
        if code != 0 or self.receipt["operations"] or self.receipt.get("protocol_error"):
            raise RuntimeError("Startup-only XCTest failed or delivered unexpected input")
        self.receipt["startup_passed"] = True
        # Never set the library driver's 'verified' field to True here.

    def prepare(self):
        raise RuntimeError("Startup-only driver cannot prepare library application input")

    def finish(self):
        raise RuntimeError("Startup-only driver cannot certify library application input")


def execute(arguments, timeout):
    return subprocess.run(arguments, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=False, timeout=timeout)


def observe_simulator(device=None):
    import runtime_context
    documents = []
    for kind in ("devices", "runtimes"):
        result = execute(["/usr/bin/xcrun", "simctl", "list", kind, "--json"], 30)
        if result.returncode or not 0 < len(result.stdout) <= 1024 * 1024:
            raise ValueError("Bounded actual simulator inventory required")
        documents.append(json.loads(result.stdout))
    return runtime_context.simulator(*documents, kind="iphone" if device is None else None, udid=device)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--simulator")
    selection.add_argument("--select-simulator", action="store_true")
    selection.add_argument("--restore-check")
    args = parser.parse_args()
    if platform.system() != "Darwin" or platform.machine().lower() != "arm64":
        raise ValueError("Actual Arm64 Apple startup runner required")
    output = ROOT / OUTPUT
    if args.select_simulator or args.restore_check:
        if args.restore_check and not native.UUID.fullmatch(args.restore_check):
            raise ValueError("One exact owned simulator restoration required")
        row = observe_simulator(args.restore_check)
        if args.restore_check:
            prior = json.loads(native.read_ordinary(output.with_name("selection.json")))
            if prior["udid"] != row["udid"] or prior["state"] != row["state"] or row["state"] != "Shutdown":
                raise ValueError("Original selected simulator shutdown was not restored")
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.with_name("restored.json" if args.restore_check else "selection.json").open("x") as stream:
            json.dump(row, stream, indent=2, sort_keys=True); stream.write("\n")
        return 0
    if not native.UUID.fullmatch(args.simulator):
        raise ValueError("One explicitly selected simulator required")
    source = execute(["git", "rev-parse", "HEAD"], 30)
    revision = source.stdout.decode().strip()
    dirty = execute(["git", "status", "--porcelain"], 30)
    if source.returncode or dirty.returncode or dirty.stdout or not REVISION.fullmatch(revision):
        raise ValueError("Clean immutable startup source required")
    row = observe_simulator(args.simulator)
    selected = json.loads(native.read_ordinary(output.with_name("selection.json")))
    if row["udid"] != selected["udid"] or row["state"] != "Booted":
        raise ValueError("Exact selected simulator must actually be Booted")
    xcode = execute(["/usr/bin/xcodebuild", "-version"], 30)
    if xcode.returncode or not 0 < len(xcode.stdout) <= native.MAX_BYTES:
        raise ValueError("Actual bounded Xcode version required")
    import runtime_context
    before = library.snapshot_inputs(ROOT)
    token = secrets.token_hex(16)
    bundle = "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + revision[:12] + ".t" + token
    driver = StartupDriver(ROOT, args.simulator, bundle, token, execute)
    started = time.monotonic()
    receipt = {"schema_version": 1, "source_revision": revision, "source_inputs_before": before,
               "host": {"system": platform.system(), "architecture": platform.machine(), "python": platform.python_version()},
               "simulator_before": row, "xcode": runtime_context.parse_xcode(xcode.stdout.decode()),
               "scope": "Independent Swift/XCTest startup only; ZERO library app, input, XML, native methods, consumer or release acceptance",
               "started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "packages_published": False, "release_readiness_certified": False}
    try:
        # Exact reserved ID must be absent; never install/launch/stop any AUT.
        from ios_ui_application import missing_app
        prior = execute(["/usr/bin/xcrun", "simctl", "get_app_container", args.simulator, bundle, "app"], 60)
        if not missing_app(prior):
            raise ValueError("Startup-only reserved AUT absence not admitted")
        receipt["reserved_aut_absence_admitted"] = True
        driver.verify_startup()
    except Exception as error:
        receipt["error_type"] = type(error).__name__
    finally:
        try: driver.close()
        except Exception as error: receipt["cleanup_error_type"] = type(error).__name__
        receipt["driver"] = driver.receipt
        receipt["source_inputs_after"] = library.snapshot_inputs(ROOT)
        try: receipt["simulator_after"] = observe_simulator(args.simulator)
        except Exception as error: receipt["simulator_after_error_type"] = type(error).__name__
        receipt["elapsed_seconds"] = round(time.monotonic() - started, 3)
        receipt["finished_at_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        receipt["passed"] = (driver.receipt["startup_passed"] is True and not receipt.get("error_type") and
                             not receipt.get("cleanup_error_type") and before == receipt["source_inputs_after"] and
                             row == receipt.get("simulator_after") and
                             all(driver.receipt["cleanup"].get(key) is True for key in native.CLEANUP))
        path = ROOT / OUTPUT
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as stream:
            json.dump(receipt, stream, indent=2, sort_keys=True); stream.write("\n")
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
