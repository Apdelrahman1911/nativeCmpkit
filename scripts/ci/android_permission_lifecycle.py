"""Own one fresh API35 permission lifecycle source app, never native acceptance.

Reuses the existing private SDK/signing/APK-byte/AVD-lease ownership protocol.
Public-library and actual Settings/dialog assertions live in library tests.
"""
from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path
import subprocess

from android_io_documents import signer_certificate
from android_permission_demo import installer_reply_facts
from android_share_recipient import OwnedShareRecipient
from android_permission_lifecycle_contract import (
    API, MODULE, PACKAGE, FIXTURE, source_contract, validate_manifest, validate_metadata, validate_request, validate_prepared_receipt, require,
)
import library_tests as lt

SIGNER_REVISION = "36.0.0"


class OwnedPermissionLifecycle(OwnedShareRecipient):
    PACKAGE, FIXTURE, OUTPUT = PACKAGE, FIXTURE, "permission-lifecycle"

    def __init__(self, *args, api_level: int, focus: str, **kwargs):
        validate_request(api_level, (MODULE,), focus)
        super().__init__(*args, **kwargs)
        self.receipt.update(verification_api_level=API, focus=focus, prepare_status="not-started", prepare_phase="not-started",
                            automatic_runtime_permission_grant=False,
                            scope="Source fixture preparation only. Actual location dialogs/Settings/native-public permission/lifecycle/PID and fresh XML remain separate library test requirements; no whole issue/consumer/release inference.")

    def host(self, command: list[str]) -> subprocess.CompletedProcess:
        value = subprocess.run(command, cwd=self.root, env=self.environment, capture_output=True, timeout=30)
        require(len(value.stdout) + len(value.stderr) <= 1024**2, "Unbounded APK inspector output")
        return value

    def inspectors(self):
        analyzer = self.home / "cmdline-tools/23.0/bin/apkanalyzer"
        signer = self.home / ("build-tools/" + SIGNER_REVISION + "/apksigner")
        require(all(p.is_file() and os.access(p, os.X_OK) for p in (analyzer, signer)), "Exact SDK analyzer/signer required")
        return analyzer, signer

    def metadata_apk(self) -> Path:
        # Do not expand android_geo_probe's accepted historical fixture whitelist.
        base = lt.safe_path(self.root, FIXTURE + "/build/outputs/apk/debug")
        metadata = lt.safe_path(self.root, (base / "output-metadata.json").relative_to(self.root).as_posix())
        before = metadata.lstat()
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size <= 65536,
                "Exact bounded regular metadata required")
        payload = metadata.read_bytes()
        after = metadata.lstat()
        require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), "Metadata changed during readback")
        name = validate_metadata(payload)
        apk = lt.safe_path(self.root, (base / name).relative_to(self.root).as_posix())
        identity = apk.lstat()
        require(stat.S_ISREG(identity.st_mode) and identity.st_nlink == 1 and 0 < identity.st_size < 256 * 1024**2,
                "Actual bounded regular unsplit APK required")
        return apk

    def inspect_apk(self, apk: Path) -> dict:
        analyzer, signer = self.inspectors()
        manifest = self.host([str(analyzer), "manifest", "print", str(apk)])
        require(manifest.returncode == 0 and not manifest.stderr.strip(), "Actual compiled manifest unavailable")
        policy = validate_manifest(manifest.stdout, compiled=True)
        certificate = signer_certificate(self.host([str(signer), "verify", "--verbose", "--print-certs",
            "--min-sdk-version", str(API), "--max-sdk-version", str(API), str(apk)]))
        key = lt.safe_path(self.root, (Path(self.environment["ANDROID_USER_HOME"]) / "debug.keystore").relative_to(self.root).as_posix())
        before = key.lstat()
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size <= 65536 and
                key.parent.is_dir() and key.parent.stat().st_mode & 0o077 == 0, "Exact bounded private signing key required")
        exported = self.host(["keytool", "-exportcert", "-keystore", str(key), "-alias", "androiddebugkey", "-storepass", "android"])
        require(exported.returncode == 0 and not exported.stderr.strip() and 0 < len(exported.stdout) <= 16384,
                "Actual private signing certificate unavailable")
        after = key.lstat()
        require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_nlink) ==
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_nlink),
                "Private signing key changed during certificate readback")
        expected = hashlib.sha256(exported.stdout).hexdigest()
        require(certificate == expected, "APK differs from the controller's actual private certificate")
        return policy | {"certificate_sha256": certificate, "private_key_certificate_sha256": expected,
                         "signature_verification_min_sdk_version": API, "signature_verification_max_sdk_version": API,
                         "raw_manifest_certificate_key_or_paths_uploaded": False}

    def prepare(self) -> dict:
        self.receipt["prepare_status"] = "running"
        try:
            self.receipt["prepare_phase"] = "source-contract"
            contract = source_contract(self.root)
            self.receipt["source_contract"] = contract
            self.receipt["prepare_phase"] = "sdk-inspectors"
            self.inspectors()
            self.receipt["prepare_phase"] = "initial-install-absence"
            require(self.readback() is None, "Existing/foreign helper cannot be replaced or reset")
            command = ["./gradlew", "--no-daemon", "--no-configuration-cache", "--max-workers=2", "--console=plain", "--no-parallel",
                       "-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8", "-Pkotlin.compiler.execution.strategy=in-process",
                       "-p", FIXTURE, "assembleDebug"]
            self.receipt["prepare_phase"] = "source-app-assembly"
            execution = lt.execute(self.root, command, self.output / "source-apk-build.log", 900, 8192, env=self.environment)
            self.receipt.update(assembly_command=command, assembly=execution)
            require(execution["exit_code"] == 0 and not execution.get("stop_reason"), "Separate source app did not assemble")
            self.receipt["prepare_phase"] = "source-apk-policy"
            apk = self.metadata_apk()
            self.digest = lt.sha256(apk)
            self.receipt.update(source_apk_sha256=self.digest, source_apk_bytes=apk.stat().st_size, apk_policy=self.inspect_apk(apk))
            require(lt.sha256(apk) == self.digest and source_contract(self.root) == contract, "Source/APK changed during inspection")
            self.install_attempted = True
            self.receipt["prepare_phase"] = "owned-installer"
            install = self.control("install", "-t", str(apk), timeout=120)
            self.receipt.update(install_exit_code=install.returncode, installer_reply=installer_reply_facts(install))
            self.receipt["prepare_phase"] = "installed-byte-readback"
            actual = self.readback()  # Reconcile even an uncertain installer before identity-safe cleanup.
            installed = actual is not None and actual.get("apk_sha256") == self.digest
            self.receipt.update(installed_readback=actual, recipient_installed=installed)
            reply = self.receipt["installer_reply"]
            require(install.returncode == 0 and reply["stdout_shape"] in {"success", "streamed-success"} and
                    reply["stderr_empty_after_trim"] and installed, "Fresh helper installer/byte readback did not pass")
            self.receipt["prepare_status"] = "passed"
            self.receipt["prepare_phase"] = "prepared-receipt-validation"
            validate_prepared_receipt(self.receipt, contract, API, focus=self.receipt["focus"])
            self.receipt["prepare_phase"] = "complete"
            return self.receipt
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt) as failure:
            self.receipt.update(prepare_status="failed", prepare_error=type(failure).__name__, prepare_error_phase=self.receipt["prepare_phase"])
            raise
        finally:
            lt.write_json(self.output / "receipt.json", self.receipt)

    def close(self) -> dict:
        try:
            value = super().close()
            require(value.get("owned_recipient_removed") is True, "Actual owned helper removal is unverified")
            value["cleanup_status"] = "passed"
            return value
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt) as failure:
            self.receipt.update(cleanup_status="failed", cleanup_error=type(failure).__name__)
            raise
        finally:
            lt.write_json(self.output / "receipt.json", self.receipt)
