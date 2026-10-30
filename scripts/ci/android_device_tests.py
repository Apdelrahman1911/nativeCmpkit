#!/usr/bin/env python3
"""Bounded API35 library instrumentation on one explicitly owned enforcing AVD.

Official SDK assets must already be installed. No package acquisition, global
AVD overwrite, physical-device selection, SELinux changes, release/publication,
or sample substitution occurs here. APKs are local build outputs, never uploaded.
The controller records engine/setup failures separately from actual JUnit cases.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import uuid

import library_tests as lt
import runtime_context as runtime
import android_webview_heap

API = 35
PORT = 5588
SERIAL = f"emulator-{PORT}"
RESERVE_MIB = 8192
IMAGE = f"system-images;android-{API};google_apis;x86_64"


def properties(path: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 65536:
        raise ValueError("Expected bounded regular installed-SDK properties")
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = (part.strip() for part in line.split("=", 1))
            if key in result:
                raise ValueError("Duplicate installed-SDK property")
            result[key] = value
    return result


def sdk_assets(home: Path) -> dict:
    image = properties(home / f"system-images/android-{API}/google_apis/x86_64/source.properties")
    emulator = properties(home / "emulator/source.properties")
    if (image.get("AndroidVersion.ApiLevel") != str(API) or image.get("SystemImage.Abi") != "x86_64"
            or image.get("SystemImage.TagId") != "google_apis"):
        raise ValueError("Installed image differs from the explicit API35/google_apis/x86_64 contract")
    for revision in (image.get("Pkg.Revision"), emulator.get("Pkg.Revision")):
        if not isinstance(revision, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", revision):
            raise ValueError("Installed SDK image/emulator version was not established")
    for executable in ("platform-tools/adb", "emulator/emulator", "cmdline-tools/23.0/bin/avdmanager"):
        path = home / executable
        if not path.is_file() or not os.access(path, os.X_OK):
            raise ValueError("Required official SDK executable is not installed/executable")
    return {"system_image": IMAGE, "api_level": str(API), "abi": "x86_64", "tag_id": "google_apis",
            "image_revision": image["Pkg.Revision"], "emulator_revision": emulator["Pkg.Revision"]}


def require_host() -> None:
    if platform.system() != "Linux" or platform.machine().lower() not in {"x86_64", "amd64"}:
        raise ValueError("This explicit instrumentation slot requires a Linux x64 KVM host")
    if not Path("/dev/kvm").is_char_device() or not os.access("/dev/kvm", os.R_OK | os.W_OK):
        raise ValueError("KVM is unavailable; do not silently substitute slow/unverified acceleration")


def ensure_ports_unused() -> None:
    for port in (PORT, PORT + 1):
        with socket.socket() as handle:
            handle.bind(("127.0.0.1", port))


def adb(home: Path, *arguments: str, timeout: int = 10) -> str:
    result = subprocess.run([str(home / "platform-tools/adb"), *arguments], capture_output=True,
                            text=True, timeout=timeout, check=True)
    return result.stdout.strip()


def avd_name(home: Path) -> str:
    lines = adb(home, "-s", SERIAL, "emu", "avd", "name").splitlines()
    if len(lines) != 2 or lines[1] != "OK":
        raise ValueError("Explicit emulator AVD ownership could not be established")
    return lines[0]


def wait_for_owned_boot(home: Path, process: subprocess.Popen, name: str, root: Path,
                        timeout: int = 360) -> dict:
    started = time.monotonic()
    while time.monotonic() - started < timeout:
        if process.poll() is not None:
            raise RuntimeError("Owned emulator exited before verified boot")
        if shutil.disk_usage(root).free < RESERVE_MIB * 1024 * 1024:
            raise RuntimeError("Disk reserve reached during emulator boot")
        try:
            boot = adb(home, "-s", SERIAL, "shell", "getprop", "sys.boot_completed")
        except subprocess.SubprocessError:
            boot = ""
        if boot == "1":
            if avd_name(home) != name:
                raise ValueError("Do not test or terminate an emulator that is not this controller's AVD")
            values = {key: adb(home, "-s", SERIAL, "shell", "getprop", prop) for key, prop in
                      (("api_level", "ro.build.version.sdk"), ("release", "ro.build.version.release"),
                       ("abi", "ro.product.cpu.abi"), ("boot_completed", "sys.boot_completed"))}
            values["selinux"] = adb(home, "-s", SERIAL, "shell", "getenforce")
            identity = runtime.parse_android_emulator(SERIAL, values)
            if identity["api_level"] != str(API) or identity["abi"] != "x86_64":
                raise ValueError("Booted emulator differs from the selected SDK image")
            return identity
        time.sleep(2)
    raise TimeoutError("Owned emulator did not establish verified boot within the bound")


def stop_owned_emulator(home: Path, process: subprocess.Popen, name: str, verified: bool) -> dict:
    result = {"requested_at_utc": lt.utc_now(), "graceful_kill_requested": False, "forced_owned_group": False}
    if process.poll() is None and verified:
        try:
            if avd_name(home) == name:
                adb(home, "-s", SERIAL, "emu", "kill")
                result["graceful_kill_requested"] = True
            else:
                result["ownership_error"] = "AVD name changed; never send kill to the foreign serial"
        except (OSError, ValueError, subprocess.SubprocessError):
            result["graceful_shutdown_error"] = "Unable to re-establish ownership and request native shutdown"
    try:
        process.wait(timeout=60)
    except subprocess.TimeoutExpired:
        lt.terminate_owned(process)
        result["forced_owned_group"] = True
    result["exit_code"] = process.returncode
    result["clean_shutdown"] = (result["exit_code"] == 0 and result["graceful_kill_requested"]
                                and not result["forced_owned_group"] and not result.get("ownership_error")
                                and not result.get("graceful_shutdown_error"))
    result["finished_at_utc"] = lt.utc_now()
    return result


def _run(root: Path, relative: str, only_modules: tuple[str, ...] | None = None, *, focus: str | None = None) -> dict:
    output = lt.safe_path(root, relative)
    base = root / "build/ci-verification"
    if output == base or not output.is_relative_to(base) or output.exists():
        raise ValueError("Use a new dedicated output directory strictly below build/ci-verification")
    home_value = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not home_value:
        raise ValueError("Use the explicitly configured official Android SDK")
    home = Path(home_value)
    assets = sdk_assets(home)
    ensure_ports_unused()
    # Never print personal serials or select an existing device as a fallback.
    if adb(home, "devices").splitlines() != ["List of devices attached"]:
        raise ValueError("Existing device table is nonempty; refuse unrelated/personal devices")
    context = runtime.capture(expected_arch="x64", android_package="android-37.0", require_clean=True)
    focus_options = {"focus": focus} if focus is not None else {}
    plan = lt.plan(root, "android-device", only_modules=only_modules, **focus_options)
    before = lt.snapshot_inputs(root)
    output.mkdir(parents=True)
    lt.write_json(output / "inputs-before.json", before)
    lt.write_json(output / "runtime-host.json", context)
    lt.write_json(output / "sdk-assets.json", assets)
    name = "nativecmpkit-api35-" + uuid.uuid4().hex[:12]
    env = os.environ.copy()
    env.update(ANDROID_AVD_HOME=str(output / "avd"), ANDROID_EMULATOR_HOME=str(output / "avd"),
               ANDROID_USER_HOME=str(output / "android-user"), ANDROID_SERIAL=SERIAL)
    (output / "avd").mkdir()
    (output / "android-user").mkdir()
    connected = lt.gradle_command("android-device", plan, android_serial=SERIAL)
    assemble = connected[:-len(plan["expected"])] + [item["project"] + ":assembleAndroidDeviceTest" for item in plan["expected"]]
    create = [str(home / "cmdline-tools/23.0/bin/avdmanager"), "create", "avd", "--name", name,
              "--package", IMAGE, "--device", "pixel_6", "--force"]
    launch = [str(home / "emulator/emulator"), "-avd", name, "-port", str(PORT), "-no-window", "-no-snapshot",
              "-no-audio", "-no-boot-anim", "-gpu", "swiftshader_indirect", "-accel", "on", "-memory", "2048",
              "-cores", "2", "-camera-back", "none", "-camera-front", "none"]
    lt.write_json(output / "plan.json", {"source_revision": context["source_revision"], "api_level": API,
                  "serial": SERIAL, "avd_name": name, "assembly_command": assemble, "create_avd_command": create,
                  "launch_command": launch, "source_suite": plan, "reserve_mib": RESERVE_MIB,
                  "scope": "API35 software-GPU/KVM library instrumentation; no physical-device/minimum-API or system-picker certification"})
    result = {"source_revision": context["source_revision"], "source_tree_dirty": context["source_tree_dirty"],
              "started_at_utc": lt.utc_now(), "setup_stages": {}, "test_suite_passed": False,
              "complete_suite_requested": plan["complete_suite_requested"],
              "explicit_module_subset": plan["explicit_module_subset"],
              "test_bearing_modules_not_requested": plan["test_bearing_modules_not_requested"],
              "packages_published": False, "release_readiness_certified": False}
    if focus is not None:
        result["explicit_test_focus"] = focus
    process = None
    heap = None
    verified = False
    log = None
    try:
        for stage, command, timeout in (("apk-assembly", assemble, 900), ("owned-avd-create", create, 120)):
            execution = lt.execute(root, command, output / (stage + ".log"), timeout, RESERVE_MIB, env=env)
            result["setup_stages"][stage] = execution
            if execution["exit_code"] != 0 or execution.get("stop_reason"):
                raise RuntimeError("Setup failed before any device test execution")
        log = (output / "emulator.log").open("w", encoding="utf-8")
        process = subprocess.Popen(launch, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        lt.write_json(output / "launch.json", {"pid": process.pid, "serial": SERIAL, "avd_name": name,
                      "observed_utc": lt.utc_now(), "ownership": "Popen child in its own process group; no guessed existing process"})
        identity = wait_for_owned_boot(home, process, name, root)
        verified = True
        lt.write_json(output / "boot.json", identity)
        if focus == lt.WEBVIEW_ANDROID_MEDIA_FOCUS:
            heap = android_webview_heap.OwnedHeap(root, output, home, SERIAL, process, name, avd_name)
            heap.prepare().start()
        receipt = lt.run(root, "android-device", (output / "library").relative_to(root).as_posix(),
                         None, 1800, RESERVE_MIB, android_serial=SERIAL, only_modules=only_modules, **focus_options)
        result["test_suite_passed"] = receipt["passed"]
        result["test_totals"] = receipt["totals"]
    except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        result["controller_error"] = type(error).__name__
        # Keep the owned logs, not arbitrary exception bodies/environment values.
    finally:
        # A repeated termination signal must not interrupt owned-engine cleanup
        # and leave no receipt. Cleanup remains bounded by stop_owned_emulator.
        previous_handlers = {}
        if __name__ == "__main__":
            for number in (signal.SIGINT, signal.SIGTERM):
                previous_handlers[number] = signal.signal(number, signal.SIG_IGN)
        try:
            try:
                if heap is not None:
                    try:
                        result["heap_diagnostics"] = heap.close()
                    except (OSError, ValueError, subprocess.SubprocessError) as error:
                        result["heap_diagnostics"] = {"clean_monitor_shutdown": False, "capture_error": type(error).__name__}
            finally:
                if process is not None:
                    result["emulator_shutdown"] = stop_owned_emulator(home, process, name, verified)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
            result["emulator_shutdown"] = {"clean_shutdown": False, "controller_cleanup_error": True}
        finally:
            if log is not None:
                log.close()
            for number, handler in previous_handlers.items():
                signal.signal(number, handler)
        try:
            after = lt.snapshot_inputs(root)
            lt.write_json(output / "inputs-after.json", after)
            result["changed_inputs"] = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
            result["source_revision_after"] = lt.git_revision(root)
            result["source_unchanged"] = not result["changed_inputs"] and result["source_revision_after"] == context["source_revision"]
        except (OSError, ValueError, subprocess.SubprocessError):
            result["source_unchanged"] = False
        result["passed"] = (result["test_suite_passed"] and result["source_unchanged"]
                            and result.get("emulator_shutdown", {}).get("clean_shutdown") is True
                            and not result.get("controller_error") and
                            (heap is None or (result.get("heap_diagnostics", {}).get("clean_monitor_shutdown") is True and
                             not result["heap_diagnostics"].get("capture_error"))))
        result["finished_at_utc"] = lt.utc_now()
        lt.write_json(output / "controller.json", result)
    return result


def run(root: Path, relative: str, only_modules: tuple[str, ...] | None = None, *, focus: str | None = None) -> dict:
    if focus is not None and not lt.allowed_test_focus("android-device", only_modules, focus):
        raise ValueError("Device focus requires its exact reviewed suite and single module")
    require_host()
    output = lt.safe_path(root, relative)
    base = lt.safe_path(root, "build/ci-verification")
    if output == base or not output.is_relative_to(base) or output.exists():
        raise ValueError("Use a new dedicated output directory strictly below build/ci-verification")
    base.mkdir(parents=True, exist_ok=True)
    # Own this checkout's explicit port through setup, test and shutdown, not
    # just the later Gradle test phase. Never delete another invocation's lock.
    lock = base / ".android-device-controller.lock"
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, f"{os.getpid()}\n".encode())
        return _run(root, relative, only_modules, **({"focus": focus} if focus is not None else {}))
    finally:
        os.close(descriptor)
        lock.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", nargs="?", choices=["plan", "run"], default="run",
                        help="Read-only source plan or actual owned emulator execution; old invocations still run")
    parser.add_argument("--output", required=True)
    parser.add_argument("--api-level", type=int, choices=[API], required=True)
    parser.add_argument("--module", action="append", help="Explicit authored device-test subset; never a complete-suite claim")
    parser.add_argument("--focus", choices=[lt.DATE_TRANSACTION_FOCUS, *lt.DROPDOWN_FOCUSES, lt.ANDROID_IO_OVERSIZE_FOCUS, lt.WEBVIEW_LIFETIME_FOCUS, lt.ANDROID_POPUP_FOCUS, lt.ANDROID_NAV_BACK_FOCUS,
                                            lt.WEBVIEW_ANDROID_MEDIA_FOCUS, *lt.WEBVIEW_IDENTITY_FOCUSES, *lt.ANDROID_SAVE_IDENTITY_FOCUSES],
                        help="Finite important device methods only; never complete suite coverage")
    args = parser.parse_args()
    modules = tuple(args.module) if args.module else None
    if args.focus is not None and not lt.allowed_test_focus("android-device", modules, args.focus):
        parser.error("--focus requires its exact reviewed single --module")
    if args.operation == "plan":
        print(json.dumps(lt.plan(lt.ROOT, "android-device", only_modules=modules,
                                 **({"focus": args.focus} if args.focus is not None else {})), indent=2, sort_keys=True))
        return 0
    def interrupted(*_) -> None:
        raise KeyboardInterrupt()
    for number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(number, interrupted)
    result = run(lt.ROOT, args.output, only_modules=modules, **({"focus": args.focus} if args.focus is not None else {}))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Android instrumentation preflight refused: {type(error).__name__}", file=sys.stderr)
        sys.exit(2)
