#!/usr/bin/env python3
"""Read-only, allowlisted runtime/SDK identity receipts. Never dump the environment.

Simulator selection does not boot, erase, install or modify a device. The caller
must explicitly boot the selected CI simulator and record a second receipt.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[2]
UUID = re.compile(r"[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}\Z")
IOS_RUNTIME = re.compile(r"com\.apple\.CoreSimulator\.SimRuntime\.iOS-([0-9]+(?:-[0-9]+)*)\Z")


def command(*args: str) -> str:
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=60)
    if result.returncode:
        # Exception/terminal output can include paths or application data. Record
        # the tool and exit code only; no environment values or raw transcripts.
        raise RuntimeError(f"{Path(args[0]).name} returned exit {result.returncode}")
    return result.stdout + result.stderr


def parse_java(text: str) -> dict:
    match = re.search(r'(?:openjdk|java) version "([0-9][^"\s]*)"', text)
    if not match:
        raise ValueError("Unable to identify actual Java version")
    return {"version": match.group(1), "major": int(match.group(1).split(".")[0])}


def parse_rust(text: str) -> dict:
    lines = dict(line.split(": ", 1) for line in text.splitlines() if ": " in line)
    required = ["release", "host", "commit-hash", "commit-date"]
    if not all(lines.get(key) for key in required) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", lines["release"]):
        raise ValueError("Incomplete actual Rust toolchain identity")
    if not re.fullmatch(r"[0-9a-f]{40}", lines["commit-hash"]):
        raise ValueError("Invalid Rust compiler commit identity")
    return {key: lines[key] for key in required}


def parse_xcode(text: str) -> dict:
    version = re.search(r"(?m)^Xcode ([0-9]+(?:\.[0-9]+)*)$", text)
    build = re.search(r"(?m)^Build version ([0-9A-Za-z]+)$", text)
    if not version or not build:
        raise ValueError("Incomplete actual Xcode version/build")
    return {"version": version.group(1), "build": build.group(1)}


def sdk_version(text: str) -> str:
    value = text.strip()
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", value):
        raise ValueError("Unrecognized effective Apple SDK version")
    return value


def parse_browser(text: str) -> dict:
    match = re.fullmatch(r"(Google Chrome(?: for Testing)?|Chromium) ([0-9]+(?:\.[0-9]+){3})\s*", text)
    if not match:
        raise ValueError("Unable to establish the explicitly configured Chromium browser version")
    return {"name": match.group(1), "version": match.group(2)}


def simulator(devices: dict, runtimes: dict, kind: str | None = None, udid: str | None = None) -> dict:
    if kind not in {None, "iphone", "ipad"} or (udid and not UUID.fullmatch(udid)):
        raise ValueError("Invalid explicit simulator selection")
    available = {item["identifier"]: item for item in runtimes.get("runtimes", [])
                 if item.get("isAvailable") is True and IOS_RUNTIME.fullmatch(item.get("identifier", ""))}
    candidates = []
    for runtime_id, values in devices.get("devices", {}).items():
        if runtime_id not in available:
            continue
        runtime = available[runtime_id]
        version = sdk_version(runtime.get("version", ""))
        for device in values:
            device_id = device.get("udid", "")
            type_id = device.get("deviceTypeIdentifier", "")
            if not device.get("isAvailable") or not UUID.fullmatch(device_id):
                continue
            if udid and device_id.lower() != udid.lower():
                continue
            if kind and not type_id.startswith("com.apple.CoreSimulator.SimDeviceType." +
                                               ("iPhone" if kind == "iphone" else "iPad")):
                continue
            if not re.fullmatch(r"com\.apple\.CoreSimulator\.SimDeviceType\.[A-Za-z0-9.-]+", type_id):
                raise ValueError("Unexpected simulator device type identifier")
            # User-assigned device names and runtime filesystem paths are private
            # and deliberately excluded. The built-in device type is sufficient.
            candidates.append({"udid": device_id, "device_type": type_id, "state": device.get("state"),
                               "runtime_identifier": runtime_id, "runtime_version": version,
                               "runtime_build": runtime.get("buildversion")})
    if not candidates:
        raise ValueError("No explicitly compatible available iOS simulator; do not silently use a different platform")
    candidates.sort(key=lambda item: (tuple(map(int, item["runtime_version"].split("."))), item["device_type"], item["udid"]))
    return candidates[-1]


def android_platform(sdk: Path, package: str) -> dict:
    if not re.fullmatch(r"android-[0-9]+(?:\.[0-9]+)?", package):
        raise ValueError("Invalid Android platform package")
    path = sdk / "platforms" / package / "source.properties"
    if not path.is_file() or path.is_symlink():
        raise ValueError("Configured Android platform source.properties is missing")
    properties = dict(line.split("=", 1) for line in path.read_text().splitlines()
                      if "=" in line and not line.lstrip().startswith("#"))
    properties = {key.strip(): value.strip() for key, value in properties.items()}
    allowed = ["Pkg.Revision", "AndroidVersion.ApiLevel", "AndroidVersion.ApiLevelFull",
               "AndroidVersion.CodeName", "AndroidVersion.ExtensionLevel"]
    # Released SDK identifiers may include a minor component (for example 37.0).
    # Keep the exact normalized identifier in the receipt/cache fingerprint.
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", properties.get("AndroidVersion.ApiLevel", "")):
        raise ValueError("Configured platform has no numeric Android API level")
    return {"package": f"platforms;{package}", **{key: properties[key] for key in allowed if key in properties}}


def validate_emulator_serial(serial: str | None) -> str:
    match = re.fullmatch(r"emulator-([1-9][0-9]{3})", serial) if isinstance(serial, str) else None
    if not match or not 5554 <= int(match[1]) <= 5682 or int(match[1]) % 2:
        raise ValueError("Use an explicit owned emulator on a valid even console port, never a personal device or injected serial")
    return serial


def parse_android_emulator(serial: str, values: dict) -> dict:
    validate_emulator_serial(serial)
    result = {key: values.get(key) for key in ("api_level", "release", "abi", "boot_completed", "selinux")}
    if (not isinstance(result["api_level"], str) or not re.fullmatch(r"[1-9][0-9]*", result["api_level"])
            or not isinstance(result["release"], str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", result["release"])
            or result["abi"] not in {"x86_64", "x86", "arm64-v8a", "armeabi-v7a"}):
        raise ValueError("Connected emulator identity was not established")
    if result["boot_completed"] != "1" or result["selinux"] != "Enforcing":
        raise ValueError("Verification requires the selected booted SELinux-Enforcing emulator")
    return {"serial": serial, **result}


def compiler_runtime_fingerprint(context: dict) -> str:
    """Stable cache partition, not integrity proof; pair it with source SHA/suite.

    Ephemeral device UDIDs, boot state and observation timestamps must not prevent
    dependency-cache reuse. Actual Xcode/SDK/simulator runtime changes must.
    """
    identity = {key: context[key] for key in ("host", "java", "rust", "xcode", "apple_sdks", "android_platform", "android_emulator", "browser")
                if key in context}
    if "simulator" in context:
        identity["simulator"] = {key: context["simulator"][key] for key in
                                 ("device_type", "runtime_identifier", "runtime_version", "runtime_build")}
    if "android_emulator" in context:
        identity["android_emulator"] = {key: context["android_emulator"][key] for key in
                                       ("api_level", "release", "abi")}
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def capture(*, expected_arch: str | None = None, apple: bool = False, select: str | None = None,
            device: str | None = None, require_booted: bool = False, android_package: str | None = None,
            android_serial: str | None = None, require_clean: bool = False, browser: bool = False) -> dict:
    arch = platform.machine().lower()
    arch = {"amd64": "x64", "x86_64": "x64", "aarch64": "arm64", "arm64": "arm64"}.get(arch, arch)
    if expected_arch and arch != expected_arch:
        raise ValueError("Actual runner architecture differs from the declared matrix slot")
    result = {"schema_version": 1, "observed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "source_revision": command("git", "rev-parse", "HEAD").strip(),
              "source_tree_dirty": bool(command("git", "status", "--porcelain", "--untracked-files=normal").strip()),
              "host": {"system": platform.system(), "architecture": arch, "python": platform.python_version()},
              "java": parse_java(command("java", "-version")),
              "rust": parse_rust(command("rustc", "--version", "--verbose"))}
    if result["java"]["major"] != 17:
        raise ValueError("Verification runner must use the declared JDK17")
    declared_rust = tomllib.loads((ROOT / "rust-toolchain.toml").read_text())["toolchain"]["channel"]
    if result["rust"]["release"] != declared_rust:
        raise ValueError("Actual Rust compiler differs from the checked-in pinned toolchain")
    if require_clean and result["source_tree_dirty"]:
        raise ValueError("Immutable CI evidence requires a clean checkout")
    if browser:
        binary = os.environ.get("CHROME_BIN")
        if not binary:
            raise ValueError("Set CHROME_BIN explicitly so Karma and the receipt use the same browser binary")
        result["browser"] = parse_browser(command(binary, "--version"))
    if apple or select or device:
        if platform.system() != "Darwin":
            raise ValueError("Apple runtime evidence must be captured on an actual macOS host")
        result["xcode"] = parse_xcode(command("xcodebuild", "-version"))
        result["apple_sdks"] = {sdk: sdk_version(command("xcrun", "--sdk", sdk, "--show-sdk-version"))
                                for sdk in ["macosx", "iphoneos", "iphonesimulator"]}
        if select or device:
            result["simulator"] = simulator(json.loads(command("xcrun", "simctl", "list", "devices", "--json")),
                                            json.loads(command("xcrun", "simctl", "list", "runtimes", "--json")), select, device)
            if require_booted and result["simulator"]["state"] != "Booted":
                raise ValueError("Selected simulator is not actually booted")
    elif require_booted:
        raise ValueError("--require-booted requires explicit simulator selection")
    if android_package:
        home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
        if not home:
            raise ValueError("Android SDK context is unavailable; do not guess another installation")
        result["android_platform"] = android_platform(Path(home), android_package)
    if android_serial is not None:
        validate_emulator_serial(android_serial)
        values = {key: command("adb", "-s", android_serial, "shell", "getprop", prop).strip()
                  for key, prop in [("api_level", "ro.build.version.sdk"), ("release", "ro.build.version.release"),
                                    ("abi", "ro.product.cpu.abi"), ("boot_completed", "sys.boot_completed")]}
        values["selinux"] = command("adb", "-s", android_serial, "shell", "getenforce").strip()
        result["android_emulator"] = parse_android_emulator(android_serial, values)
    result["compiler_runtime_fingerprint"] = compiler_runtime_fingerprint(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-arch", choices=["x64", "arm64"])
    parser.add_argument("--apple", action="store_true")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--select-simulator", choices=["iphone", "ipad"])
    group.add_argument("--simulator")
    parser.add_argument("--require-booted", action="store_true")
    parser.add_argument("--require-clean", action="store_true")
    parser.add_argument("--android-platform")
    parser.add_argument("--android-emulator")
    parser.add_argument("--browser", action="store_true", help="Record the actual explicit CHROME_BIN used by Karma")
    args = parser.parse_args()
    result = capture(expected_arch=args.expected_arch, apple=args.apple, select=args.select_simulator,
                     device=args.simulator, require_booted=args.require_booted, android_package=args.android_platform,
                     android_serial=args.android_emulator, require_clean=args.require_clean, browser=args.browser)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
