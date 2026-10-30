"""Own one disposable native URI recipient; no APK publication or manual URI grant.

The source library instrumentation remains the real caller. This separate-UID app
observes Android grants and descriptors, not a packaged library consumer or sample.
Every device control and uninstall rechecks the controller's actual AVD lease.
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess

from android_geo_probe import installed_path, metadata_apk
import library_tests as lt

PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.sharerecipient"
FIXTURE = "tests/consumer/android-share-recipient"


class OwnedShareRecipient:
    PACKAGE = PACKAGE
    FIXTURE = FIXTURE
    OUTPUT = "share-recipient"

    def __init__(self, root: Path, output: Path, home: Path, serial: str, is_owned, *, environment: dict[str, str]):
        if serial != "emulator-5588" or not callable(is_owned):
            raise ValueError("No guessed/personal device or ownership fallback")
        if (not isinstance(environment, dict) or environment.get("ANDROID_SERIAL") != serial or
                environment.get("ANDROID_USER_HOME") != str(output / "android-user")):
            raise ValueError("The controller's exact private signing environment is required")
        self.root, self.home, self.serial, self.is_owned = root, home, serial, is_owned
        self.environment = dict(environment)  # Never persist or upload the signing environment.
        self.output = lt.safe_path(root, (output / self.OUTPUT).relative_to(root).as_posix())
        if not self.output.is_relative_to(lt.safe_path(root, "build/ci-verification")):
            raise ValueError("Owned verification output required")
        self.output.mkdir(exist_ok=False)
        self.digest = None
        self.install_attempted = False
        self.receipt = {"schema_version": 1, "package": self.PACKAGE, "source_fixture": self.FIXTURE,
                        "packages_published": False, "release_readiness_certified": False,
                        "recipient_installed": False, "owned_recipient_removed": False,
                        "raw_paths_console_APKs_or_signing_inputs_uploaded": False,
                        "manual_URI_grant": False,
                        "scope": "Separate-UID Android URI recipient only; library caller is instrumentation. Not packaged consumer, chooser/DocumentsUI/vendor UX, minimum/physical-device, ABI or release certification."}

    def control(self, *arguments: str, timeout: int = 30) -> subprocess.CompletedProcess:
        if not self.is_owned():
            raise ValueError("Actual selected AVD lease lost; no device mutation or foreign cleanup")
        result = subprocess.run([str(self.home / "platform-tools/adb"), "-s", self.serial, *arguments],
                                cwd=self.root, capture_output=True, timeout=timeout)
        if len(result.stdout) + len(result.stderr) > 1024**2:
            raise ValueError("Unbounded owned-device control result")
        return result

    def readback(self) -> dict | None:
        path = installed_path(self.control("shell", "pm", "path", self.PACKAGE))
        if path is None:
            return None
        result = self.control("shell", "sha256sum", path)
        if result.returncode or result.stderr.strip():
            raise ValueError("Installed recipient APK bytes unavailable")
        parts = result.stdout.decode("utf-8").strip().split()
        if len(parts) != 2 or not re.fullmatch("[a-f0-9]{64}", parts[0]) or parts[1] != path:
            raise ValueError("Unknown installed recipient identity")
        return {"apk_sha256": parts[0], "exact_one_APK_path_observed": True, "raw_path_uploaded": False}

    def prepare(self) -> dict:
        if self.readback() is not None:
            raise ValueError("A prior/foreign recipient app exists; never replace it")
        command = ["./gradlew", "--no-daemon", "--no-configuration-cache", "--max-workers=2", "--console=plain",
                   "--no-parallel", "-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8",
                   "-p", self.FIXTURE, "assembleDebug"]
        execution = lt.execute(self.root, command, self.output / "source-apk-build.log", 900, 8192, env=self.environment)
        self.receipt.update(assembly_command=command, assembly=execution)
        if execution["exit_code"] or execution.get("stop_reason"):
            raise RuntimeError("Separate native recipient did not assemble")
        apk = metadata_apk(self.root, fixture=self.FIXTURE, package=self.PACKAGE)
        self.digest = lt.sha256(apk)
        self.receipt.update(source_apk_sha256=self.digest, source_apk_bytes=apk.stat().st_size)
        self.install_attempted = True
        install = self.control("install", "-t", str(apk), timeout=120)  # No -g, -r or foreign replacement.
        actual = self.readback()  # Reconcile even a failed/uncertain install before cleanup.
        installed = actual is not None and actual["apk_sha256"] == self.digest
        self.receipt.update(install_exit_code=install.returncode, installed_readback=actual,
                            recipient_installed=installed, automatic_runtime_permission_grant=False,
                            native_signature_UID_and_URI_reads_still_required=True)
        if install.returncode or b"Success" not in install.stdout.splitlines() or not installed:
            raise RuntimeError("Owned recipient install/readback failed; no blind retry")
        return self.receipt

    def close(self) -> dict:
        if self.install_attempted:
            actual = self.readback()
            if actual is not None:
                if actual["apk_sha256"] != self.digest:
                    raise ValueError("Installed recipient bytes changed; refuse foreign cleanup")
                stop = self.control("shell", "am", "force-stop", self.PACKAGE, timeout=30)
                remove = self.control("uninstall", self.PACKAGE, timeout=90)
                absent = self.readback() is None
                self.receipt.update(owned_identity_reverified=True, stop_exit_code=stop.returncode,
                                    uninstall_exit_code=remove.returncode, owned_recipient_removed=absent)
                if stop.returncode or remove.returncode or not absent:
                    raise ValueError("Owned native recipient shutdown/uninstall unverified")
            else:
                self.receipt["owned_recipient_removed"] = True
        else:
            self.receipt.update(foreign_or_preexisting_recipient_mutated=False, owned_recipient_removed=True)
        lt.write_json(self.output / "receipt.json", self.receipt)
        return self.receipt


class OwnedShareDocuments(OwnedShareRecipient):
    """Exact third-UID fixture; reuses byte-identity ownership, never recipient read results."""
    PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.sharedocuments"
    FIXTURE = "tests/consumer/android-share-documents"
    OUTPUT = "share-documents"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.receipt["scope"] = "Third-UID read-only DocumentsProvider plus finite Activity-result grant of two synthetic files. Android creates incoming source grants; not DocumentsUI/vendor/photo-picker UX, packaged consumer, physical/minimum-device, ABI or release certification."
