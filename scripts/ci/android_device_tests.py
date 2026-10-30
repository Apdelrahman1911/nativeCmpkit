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
import android_geo_probe
import android_share_recipient
import android_camera_receiver

API = 35
PORT = 5588
SERIAL = f"emulator-{PORT}"
RESERVE_MIB = 8192
IMAGE = f"system-images;android-{API};google_apis;x86_64"


def preflight_error_origin(error: Exception) -> dict:
    """Public source location only; never exception text, locals or machine paths."""
    allowed = {"android_device_tests.py", "library_tests.py", "runtime_context.py",
               "android_camera_receiver.py", "android_share_recipient.py", "android_geo_probe.py"}
    directory = Path(__file__).resolve().parent
    origin = {"source": "unavailable", "symbol": "unavailable", "line": 0}
    frame = error.__traceback__
    while frame is not None:
        filename = Path(frame.tb_frame.f_code.co_filename)
        symbol = frame.tb_frame.f_code.co_name
        if (filename.name in allowed and filename.resolve().parent == directory and
                re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", symbol) and 0 < frame.tb_lineno < 20000):
            origin = {"source": filename.name, "symbol": symbol, "line": frame.tb_lineno}
        frame = frame.tb_next
    return origin


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


def sdk_assets(home: Path, api_level: int = API) -> dict:
    image = properties(home / f"system-images/android-{api_level}/google_apis/x86_64/source.properties")
    emulator = properties(home / "emulator/source.properties")
    if (image.get("AndroidVersion.ApiLevel") != str(api_level) or image.get("SystemImage.Abi") != "x86_64"
            or image.get("SystemImage.TagId") != "google_apis"):
        raise ValueError("Installed image differs from the explicit selected API/google_apis/x86_64 contract")
    for revision in (image.get("Pkg.Revision"), emulator.get("Pkg.Revision")):
        if not isinstance(revision, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", revision):
            raise ValueError("Installed SDK image/emulator version was not established")
    for executable in ("platform-tools/adb", "emulator/emulator", "cmdline-tools/23.0/bin/avdmanager"):
        path = home / executable
        if not path.is_file() or not os.access(path, os.X_OK):
            raise ValueError("Required official SDK executable is not installed/executable")
    return {"system_image": f"system-images;android-{api_level};google_apis;x86_64", "api_level": str(api_level), "abi": "x86_64", "tag_id": "google_apis",
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


def wait_for_owned_transport_removal(home: Path, timeout: int = 30) -> bool:
    """Observe disappearance after this controller's verified graceful shutdown.

    No adb restart, device removal, foreign-device selection or mutating fallback.
    The owned serial may briefly remain in adb's table after its process exits.
    """
    started = time.monotonic()
    while time.monotonic() - started < timeout:
        rows = adb(home, "devices").splitlines()
        if rows == ["List of devices attached"]:
            return True
        if (len(rows) != 2 or rows[0] != "List of devices attached" or
                rows[1] not in {SERIAL + "\toffline", SERIAL + "\tdevice"}):
            raise ValueError("Unexpected device table after the owned emulator exited")
        time.sleep(0.2)
    return False


def wait_for_owned_boot(home: Path, process: subprocess.Popen, name: str, root: Path,
                        timeout: int = 360, *, api_level: int = API) -> dict:
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
            if identity["api_level"] != str(api_level) or identity["abi"] != "x86_64":
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


def _run(root: Path, relative: str, only_modules: tuple[str, ...] | None = None, *, focus: str | None = None, api_level: int = API) -> dict:
    output = lt.safe_path(root, relative)
    base = root / "build/ci-verification"
    if output == base or not output.is_relative_to(base) or output.exists():
        raise ValueError("Use a new dedicated output directory strictly below build/ci-verification")
    home_value = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not home_value:
        raise ValueError("Use the explicitly configured official Android SDK")
    home = Path(home_value)
    # Reject an invalid authored source selection before even diagnostic output.
    # Other profiles retain their original no-output-on-preflight-refusal contract.
    focus_options = {"focus": focus} if focus is not None else {}
    plan = lt.plan(root, "android-device", only_modules=only_modules, **focus_options)
    diagnostics = focus in lt.ANDROID_CAMERA_FOCUSES
    if diagnostics:
        output.mkdir(parents=True)
    preflight = {"api_level": api_level, "status": "running", "stage": "sdk-assets",
                 "raw_device_tables_paths_or_exception_bodies_uploaded": False,
                 "native_success_inferred": False}
    def checkpoint(**values):
        preflight.update(**values)
        if diagnostics:
            lt.write_json(output / "preflight.json", preflight)
    try:
        checkpoint()
        assets = sdk_assets(home, **({"api_level": api_level} if api_level != API else {}))
        checkpoint(stage="unoccupied-owned-ports")
        ensure_ports_unused()
        checkpoint(stage="empty-device-table")
        # Never print personal serials or select an existing device as a fallback.
        if adb(home, "devices").splitlines() != ["List of devices attached"]:
            raise ValueError("Existing device table is nonempty; refuse unrelated/personal devices")
        checkpoint(stage="clean-runtime")
        context = runtime.capture(expected_arch="x64", android_package="android-37.0", require_clean=True)
        before = lt.snapshot_inputs(root)
        checkpoint(stage="complete", status="passed")
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        checkpoint(status="failed", exception_class=type(error).__name__, error_origin=preflight_error_origin(error))
        raise
    if not diagnostics:
        output.mkdir(parents=True)
    lt.write_json(output / "inputs-before.json", before)
    lt.write_json(output / "runtime-host.json", context)
    lt.write_json(output / "sdk-assets.json", assets)
    name = f"nativecmpkit-api{api_level}-" + uuid.uuid4().hex[:12]
    env = os.environ.copy()
    env.update(ANDROID_AVD_HOME=str(output / "avd"), ANDROID_EMULATOR_HOME=str(output / "avd"),
               ANDROID_USER_HOME=str(output / "android-user"), ANDROID_SERIAL=SERIAL)
    (output / "avd").mkdir()
    (output / "android-user").mkdir()
    connected = lt.gradle_command("android-device", plan, android_serial=SERIAL)
    assemble = connected[:-len(plan["expected"])] + [item["project"] + ":assembleAndroidDeviceTest" for item in plan["expected"]]
    create = [str(home / "cmdline-tools/23.0/bin/avdmanager"), "create", "avd", "--name", name,
              "--package", assets["system_image"], "--device", "Nexus 5" if api_level == 23 else "pixel_6", "--force"]
    launch = [str(home / "emulator/emulator"), "-avd", name, "-port", str(PORT), "-no-window", "-no-snapshot",
              "-no-audio", "-no-boot-anim", "-gpu", "swiftshader_indirect", "-accel", "on", "-memory", "2048",
              "-cores", "2", "-camera-back", "emulated" if lt.android_camera_receiver_required(plan) else "none", "-camera-front", "none"]
    lt.write_json(output / "plan.json", {"source_revision": context["source_revision"], "api_level": api_level,
                  "serial": SERIAL, "avd_name": name, "assembly_command": assemble, "create_avd_command": create,
                  "launch_command": launch, "source_suite": plan, "reserve_mib": RESERVE_MIB,
                  "scope": f"Explicit API{api_level} software-GPU/KVM library instrumentation; no physical-device/system-camera UX or complete minimum-platform certification"})
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
    geo_probe = None
    share_recipient = None
    share_documents = None
    camera_receiver = None
    verified = False
    log = None
    deferred_api23_assembly = diagnostics and api_level == 23
    if deferred_api23_assembly:
        result["reporter_compile_deferred_until_receiver_byte_identity"] = True
    try:
        stages = (("apk-assembly", assemble, 900), ("owned-avd-create", create, 120))
        if lt.android_camera_receiver_required(plan):
            # Validate the finite camera's real SDK device profile before a costly APK
            # compilation. This creates only our private AVD; launch still waits for
            # both prerequisites. Other profiles preserve their existing setup order.
            stages = stages[::-1]
        if deferred_api23_assembly:
            # A minimum-only receiver/package-path refusal must not waste a full
            # library APK compilation. Both APKs still use the exact private key
            # environment, and the reporter/native suite cannot run without a
            # successfully byte-identified receiver and actual enforcing boot.
            stages = tuple(item for item in stages if item[0] != "apk-assembly")
        for stage, command, timeout in stages:
            execution = lt.execute(root, command, output / (stage + ".log"), timeout, RESERVE_MIB, env=env)
            result["setup_stages"][stage] = execution
            if execution["exit_code"] != 0 or execution.get("stop_reason"):
                raise RuntimeError("Setup failed before any device test execution")
        log = (output / "emulator.log").open("w", encoding="utf-8")
        process = subprocess.Popen(launch, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        lt.write_json(output / "launch.json", {"pid": process.pid, "serial": SERIAL, "avd_name": name,
                      "observed_utc": lt.utc_now(), "ownership": "Popen child in its own process group; no guessed existing process"})
        identity = wait_for_owned_boot(home, process, name, root, **({"api_level": api_level} if api_level != API else {}))
        verified = True
        lt.write_json(output / "boot.json", identity)
        if lt.android_geo_probe_required(plan):
            geo_probe = android_geo_probe.OwnedGeoProbe(root, output, home, SERIAL,
                lambda: process.poll() is None and avd_name(home) == name, environment=env)
            result["geo_probe"] = geo_probe.prepare()
        if lt.android_share_recipient_required(plan):
            share_documents = android_share_recipient.OwnedShareDocuments(root, output, home, SERIAL,
                lambda: process.poll() is None and avd_name(home) == name, environment=env)
            result["share_documents"] = share_documents.prepare()
            share_recipient = android_share_recipient.OwnedShareRecipient(root, output, home, SERIAL,
                lambda: process.poll() is None and avd_name(home) == name, environment=env)
            result["share_recipient"] = share_recipient.prepare()
        if lt.android_camera_receiver_required(plan):
            camera_receiver = android_camera_receiver.OwnedCameraReceiver(root, output, home, SERIAL,
                lambda: process.poll() is None and avd_name(home) == name, environment=env, api_level=api_level)
            result["camera_receiver"] = camera_receiver.prepare()
            if deferred_api23_assembly:
                execution = lt.execute(root, assemble, output / "apk-assembly.log", 900, RESERVE_MIB, env=env)
                result["setup_stages"]["apk-assembly"] = execution
                if execution["exit_code"] != 0 or execution.get("stop_reason"):
                    raise RuntimeError("Reporter setup failed before any device test execution")
        if focus == lt.WEBVIEW_ANDROID_MEDIA_FOCUS:
            heap = android_webview_heap.OwnedHeap(root, output, home, SERIAL, process, name, avd_name)
            heap.prepare().start()
        receipt = lt.run(root, "android-device", (output / "library").relative_to(root).as_posix(),
                         None, 1800, RESERVE_MIB, android_serial=SERIAL,
                         android_user_home=(output / "android-user").relative_to(root).as_posix(),
                         only_modules=only_modules, **focus_options)
        result["test_suite_passed"] = receipt["passed"]
        if focus in lt.ANDROID_CAMERA_FOCUSES and any(item.get("reports") for item in receipt.get("modules", [])):
            result["camera_fresh_reports"] = android_camera_receiver.archive_focused_reports(root, output, receipt, plan)
        result["test_totals"] = receipt["totals"]
    except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        result["controller_error"] = type(error).__name__
        if diagnostics:
            result["controller_error_origin"] = preflight_error_origin(error)
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
                if geo_probe is not None:
                    try:
                        result["geo_probe"] = geo_probe.close()
                    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                        result["geo_probe"] = {"owned_probe_removed": False, "cleanup_error": type(error).__name__}
                if share_recipient is not None:
                    try:
                        result["share_recipient"] = share_recipient.close()
                    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                        result["share_recipient"] = {"owned_recipient_removed": False, "cleanup_error": type(error).__name__}
                if camera_receiver is not None:
                    try:
                        result["camera_receiver"] = camera_receiver.close()
                    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                        result["camera_receiver"] = dict(camera_receiver.receipt) | {
                            "owned_recipient_removed": False, "cleanup_error": type(error).__name__}
                        result["camera_receiver_cleanup_error_origin"] = preflight_error_origin(error)
                if share_documents is not None:
                    try:
                        result["share_documents"] = share_documents.close()
                    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                        result["share_documents"] = {"owned_recipient_removed": False, "cleanup_error": type(error).__name__}
            finally:
                if process is not None:
                    result["emulator_shutdown"] = stop_owned_emulator(home, process, name, verified)
                    if (camera_receiver is not None and verified and
                            result["emulator_shutdown"].get("clean_shutdown") is True):
                        removed = wait_for_owned_transport_removal(home)
                        result["emulator_shutdown"]["owned_adb_transport_removed"] = removed
                        result["emulator_shutdown"]["clean_shutdown"] = removed
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
                             not result["heap_diagnostics"].get("capture_error"))) and
                            (geo_probe is None or (result.get("geo_probe", {}).get("owned_probe_removed") is True and
                             not result["geo_probe"].get("cleanup_error"))) and
                            (share_recipient is None or (result.get("share_recipient", {}).get("owned_recipient_removed") is True and
                             not result["share_recipient"].get("cleanup_error"))) and
                            (share_documents is None or (result.get("share_documents", {}).get("owned_recipient_removed") is True and
                             not result["share_documents"].get("cleanup_error"))) and
                            (camera_receiver is None or (result.get("camera_receiver", {}).get("owned_recipient_removed") is True and
                             not result["camera_receiver"].get("cleanup_error"))))
        result["finished_at_utc"] = lt.utc_now()
        lt.write_json(output / "controller.json", result)
    return result


def validate_api_selection(api_level: int, modules: tuple[str, ...] | None, focus: str | None) -> None:
    if api_level not in (23, API) or (api_level == 23 and (modules != ("calf-camera-picker",) or focus not in lt.ANDROID_CAMERA_PROVIDER_FOCUSES)):
        raise ValueError("API23 is permitted only for the exact camera-provider minimum-platform fixture")


def run(root: Path, relative: str, only_modules: tuple[str, ...] | None = None, *, focus: str | None = None, api_level: int = API) -> dict:
    if focus is not None and not lt.allowed_test_focus("android-device", only_modules, focus):
        raise ValueError("Device focus requires its exact reviewed suite and single module")
    validate_api_selection(api_level, only_modules, focus)
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
        return _run(root, relative, only_modules, **({"focus": focus} if focus is not None else {}),
                    **({"api_level": api_level} if api_level != API else {}))
    finally:
        os.close(descriptor)
        lock.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", nargs="?", choices=["plan", "run"], default="run",
                        help="Read-only source plan or actual owned emulator execution; old invocations still run")
    parser.add_argument("--output", required=True)
    parser.add_argument("--api-level", type=int, choices=[23, API], required=True)
    parser.add_argument("--module", action="append", help="Explicit authored device-test subset; never a complete-suite claim")
    parser.add_argument("--focus", choices=[lt.DATE_TRANSACTION_FOCUS, *lt.DROPDOWN_FOCUSES, lt.ANDROID_IO_OVERSIZE_FOCUS, lt.WEBVIEW_LIFETIME_FOCUS, lt.ANDROID_POPUP_FOCUS, lt.ANDROID_NAV_BACK_FOCUS, lt.ANDROID_GEO_OWNERSHIP_FOCUS, *lt.ANDROID_GEO_PROVIDER_FOCUSES, lt.ANDROID_SHARE_GRANT_FOCUS, *lt.ANDROID_CAMERA_FOCUSES,
                                            lt.WEBVIEW_ANDROID_MEDIA_FOCUS, *lt.WEBVIEW_IDENTITY_FOCUSES, *lt.ANDROID_SAVE_IDENTITY_FOCUSES],
                        help="Finite important device methods only; never complete suite coverage")
    args = parser.parse_args()
    modules = tuple(args.module) if args.module else None
    if args.focus is not None and not lt.allowed_test_focus("android-device", modules, args.focus):
        parser.error("--focus requires its exact reviewed single --module")
    validate_api_selection(args.api_level, modules, args.focus)
    if args.operation == "plan":
        print(json.dumps(lt.plan(lt.ROOT, "android-device", only_modules=modules,
                                 **({"focus": args.focus} if args.focus is not None else {})), indent=2, sort_keys=True))
        return 0
    def interrupted(*_) -> None:
        raise KeyboardInterrupt()
    for number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(number, interrupted)
    result = run(lt.ROOT, args.output, only_modules=modules, **({"focus": args.focus} if args.focus is not None else {}),
                 **({"api_level": args.api_level} if args.api_level != API else {}))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Android instrumentation preflight refused: {type(error).__name__}", file=sys.stderr)
        print("NATIVECMPKIT_ANDROID_PREFLIGHT_ORIGIN " + json.dumps(preflight_error_origin(error), sort_keys=True), file=sys.stderr)
        sys.exit(2)
