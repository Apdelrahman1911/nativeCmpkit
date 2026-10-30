"""Own one disposable separate-UID source consumer, never publish its APK.

AGP's test APK is installed with -g. A separate installed source consumer permits
actual denied/revoked permissions without revoking/killing the test reporter.
Only the explicitly verified owned AVD and byte-identical owned app may change.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess

import library_tests as lt

PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.geoprobe"
FIXTURE = "tests/consumer/android-geo-probe"
PERMISSIONS = ("android.permission.ACCESS_COARSE_LOCATION", "android.permission.ACCESS_FINE_LOCATION")


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate actual APK metadata key")
        result[key] = value
    return result


def metadata_apk(root: Path, *, fixture: str = FIXTURE, package: str = PACKAGE) -> Path:
    if (fixture, package) not in {
        (FIXTURE, PACKAGE),
        ("tests/consumer/android-camera-receiver", "io.github.apdelrahman1911.nativecmpkit.verification.camerareceiver"),
        ("tests/consumer/android-share-recipient", "io.github.apdelrahman1911.nativecmpkit.verification.sharerecipient"),
        ("tests/consumer/android-share-documents", "io.github.apdelrahman1911.nativecmpkit.verification.sharedocuments"),
    }:
        raise ValueError("Only exact reviewed disposable fixture/package pairs are permitted")
    base = lt.safe_path(root, fixture + "/build/outputs/apk/debug")
    metadata = lt.safe_path(root, (base / "output-metadata.json").relative_to(root).as_posix())
    if (not metadata.is_file() or metadata.stat().st_nlink != 1 or metadata.stat().st_size > 65536):
        raise ValueError("Expected bounded actual separate-probe APK metadata")
    data = json.loads(metadata.read_bytes(), object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite APK metadata")))
    if (not isinstance(data, dict) or not isinstance(data.get("artifactType"), dict) or
            data.get("applicationId") != package or data.get("variantName") != "debug" or
            data["artifactType"].get("type") != "APK"):
        raise ValueError("Foreign source APK metadata")
    rows = data.get("elements")
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ValueError("Expected exactly one actual APK metadata element")
    row = rows[0]
    name = row.get("outputFile", "")
    if row.get("type") != "SINGLE" or row.get("filters") != [] or not re.fullmatch(r"[A-Za-z0-9_.-]+\.apk", name):
        raise ValueError("Only one actual unsplit owned APK is permitted")
    path = lt.safe_path(root, (base / name).relative_to(root).as_posix())
    if not path.is_file() or path.stat().st_nlink != 1 or not 0 < path.stat().st_size < 256 * 1024**2:
        raise ValueError("Expected actual bounded regular source APK")
    return path


def installed_path(result: subprocess.CompletedProcess) -> str | None:
    if len(result.stdout) + len(result.stderr) > 65536:
        raise ValueError("Unbounded package observation")
    if result.returncode in (0, 1) and not result.stdout.strip() and not result.stderr.strip():
        return None
    if result.returncode != 0 or result.stderr.strip():
        raise ValueError("Unknown package presence; never overwrite or uninstall")
    value = result.stdout.decode("utf-8").strip()
    if not re.fullmatch(r"package:/data/app/[A-Za-z0-9_./+=~-]+/base\.apk", value) or ".." in value:
        raise ValueError("Expected exactly one actual installed app path")
    return value.removeprefix("package:")


def permission_result(result: subprocess.CompletedProcess) -> bool:
    """Scalar PermissionManager result, not a heuristic over the human package dump.

    API35 DumpHelper's explicit check-permission command prints exactly one
    PackageManager.PERMISSION_GRANTED (0) or PERMISSION_DENIED (-1) value.
    Unknown/error/duplicate output cannot become a grant or an inferred denial.
    The native tests independently read permission state from the real probe UID.
    """
    if (result.returncode != 0 or result.stderr or not isinstance(result.stdout, bytes) or
            re.fullmatch(rb"(?:0|-1)(?:\r?\n)?", result.stdout) is None):
        raise ValueError("Unknown actual permission-service result")
    return result.stdout.rstrip(b"\r\n") == b"0"


class OwnedGeoProbe:
    def __init__(self, root: Path, output: Path, home: Path, serial: str, is_owned, *, environment: dict[str, str]):
        if serial != "emulator-5588" or not callable(is_owned):
            raise ValueError("No guessed/personal device or ownership fallback")
        self.root, self.home, self.serial, self.is_owned = root, home, serial, is_owned
        if (not isinstance(environment, dict) or environment.get("ANDROID_SERIAL") != serial or
                environment.get("ANDROID_USER_HOME") != str(output / "android-user")):
            raise ValueError("The controller's exact private signing environment is required")
        self.environment = dict(environment)  # Private child copy; never dump or upload it.
        self.output = lt.safe_path(root, (output / "geo-probe").relative_to(root).as_posix())
        if not self.output.is_relative_to(lt.safe_path(root, "build/ci-verification")):
            raise ValueError("Owned verification output required")
        self.output.mkdir(exist_ok=False)
        self.digest = None
        self.installed = False
        self.install_attempted = False
        self.receipt = {"schema_version": 1, "package": PACKAGE, "source_fixture": FIXTURE,
                        "packages_published": False, "release_readiness_certified": False,
                        "probe_installed": False, "owned_probe_removed": False,
                        "raw_package_dump_paths_or_console_uploaded": False,
                        "scope": "Disposable separate-UID public-source Android library consumer only. Default-debug APK stays private; no packaged Maven consumer, ABI, minimum-platform or release certification."}

    def control(self, *arguments: str, timeout: int = 30) -> subprocess.CompletedProcess:
        if not self.is_owned():
            raise ValueError("Actual selected AVD lease lost; no device mutation or foreign cleanup")
        result = subprocess.run([str(self.home / "platform-tools/adb"), "-s", self.serial, *arguments],
                                cwd=self.root, capture_output=True, timeout=timeout)
        if len(result.stdout) + len(result.stderr) > 1024**2:
            raise ValueError("Unbounded owned-device control result")
        return result

    def readback(self) -> dict | None:
        native = installed_path(self.control("shell", "pm", "path", PACKAGE))
        if native is None:
            return None
        result = self.control("shell", "sha256sum", native)
        if result.returncode or result.stderr.strip():
            raise ValueError("Installed APK bytes unavailable")
        parts = result.stdout.decode("utf-8").strip().split()
        if len(parts) != 2 or not re.fullmatch("[a-f0-9]{64}", parts[0]) or parts[1] != native:
            raise ValueError("Unknown installed APK identity")
        return {"apk_sha256": parts[0], "exact_one_APK_path_observed": True,
                "raw_path_uploaded": False}

    def prepare(self) -> dict:
        if self.readback() is not None:
            raise ValueError("A prior/foreign probe app exists; never replace it")
        command = ["./gradlew", "--no-daemon", "--no-configuration-cache", "--max-workers=2", "--console=plain",
                   "--no-parallel", "-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8",
                   "-Pkotlin.compiler.execution.strategy=in-process", "-p", FIXTURE, "assembleDebug"]
        execution = lt.execute(self.root, command, self.output / "source-apk-build.log", 900, 8192, env=self.environment)
        self.receipt.update(assembly_command=command, assembly=execution)
        if execution["exit_code"] or execution.get("stop_reason"):
            raise RuntimeError("Separate native source consumer did not assemble")
        apk = metadata_apk(self.root)
        self.digest = lt.sha256(apk)
        self.receipt.update(source_apk_sha256=self.digest, source_apk_bytes=apk.stat().st_size)
        self.install_attempted = True
        install = self.control("install", "-t", str(apk), timeout=120)  # Deliberately no -g/-r or foreign replacement.
        actual = self.readback()  # Reconcile even an uncertain install, before any possible cleanup.
        self.installed = actual is not None and actual["apk_sha256"] == self.digest
        self.receipt.update(install_exit_code=install.returncode, installed_readback=actual,
                            probe_installed=self.installed, automatic_runtime_permission_grant=False)
        if install.returncode or b"Success" not in install.stdout.splitlines() or not self.installed:
            raise RuntimeError("Owned separate source APK install/readback failed; no blind retry")
        permissions = {permission: permission_result(self.control(
            "shell", "dumpsys", "package", "check-permission", permission, PACKAGE, "0"))
            for permission in PERMISSIONS}
        self.receipt["initial_actual_foreground_permissions"] = permissions
        self.receipt["initial_denial_verified_by_permission_service"] = all(value is False for value in permissions.values())
        self.receipt["permission_observation"] = {"mechanism": "dumpsys package check-permission", "user": 0,
                                                  "actual_permission_manager_constants": True}
        self.receipt["actual_native_permission_reads_still_required"] = True
        if any(value is True for value in permissions.values()):
            raise ValueError("The fresh source consumer was unexpectedly granted foreground permissions")
        return self.receipt

    def close(self) -> dict:
        if self.install_attempted:
            actual = self.readback()
            if actual is not None:
                if actual["apk_sha256"] != self.digest:
                    raise ValueError("Installed probe bytes changed; refuse foreign cleanup")
                stop = self.control("shell", "am", "force-stop", PACKAGE, timeout=30)
                remove = self.control("uninstall", PACKAGE, timeout=90)
                absent = self.readback() is None
                self.receipt.update(owned_identity_reverified=True, stop_exit_code=stop.returncode,
                                    uninstall_exit_code=remove.returncode, owned_probe_removed=absent)
                if stop.returncode or remove.returncode or not absent:
                    raise ValueError("Owned native probe shutdown/uninstall unverified")
            else:
                self.receipt["owned_probe_removed"] = True
        else:
            self.receipt.update(foreign_or_preexisting_probe_mutated=False, owned_probe_removed=True)
        lt.write_json(self.output / "receipt.json", self.receipt)
        return self.receipt
