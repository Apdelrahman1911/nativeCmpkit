"""Own the fresh signature-scoped Call/media source app; native assertions remain in library tests."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

from android_geo_probe import metadata_apk
from android_io_documents import signer_certificate
from android_share_recipient import OwnedShareRecipient
import library_tests as lt

PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.permissiondemo"
REPORTER = "com.mohamedrejeb.calf.calfpermissions.calfpermissionscore.test"
FIXTURE = "tests/consumer/android-permission-demo"
PERMISSION = PACKAGE + ".BIND_DEMO"
RUNTIME_PERMISSIONS = {"android.permission." + name for name in (
    "CALL_PHONE", "RECORD_AUDIO", "READ_MEDIA_IMAGES", "READ_MEDIA_VIDEO", "READ_MEDIA_VISUAL_USER_SELECTED")}
KOTLIN = "calf-permissions/core/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/permissions/"
APPLICATION_KOTLIN = FIXTURE + "/src/main/kotlin/" + PACKAGE.replace(".", "/") + "/"
SOURCE_FILES = tuple(sorted(("gradle/libs.versions.toml", "calf-permissions/core/build.gradle.kts",
    "calf-permissions/core/src/androidDeviceTest/AndroidManifest.xml", FIXTURE + "/settings.gradle.kts",
    FIXTURE + "/build.gradle.kts", FIXTURE + "/gradle.properties", FIXTURE + "/src/main/AndroidManifest.xml",
    *(KOTLIN + name + ".kt" for name in ("AndroidPermissionDemoDeviceTest", "AndroidMediaSelectionDeviceTest",
        "OwnedPermissionDemo", "PermissionDemoSystemUi")),
    *(APPLICATION_KOTLIN + name + ".kt" for name in ("PermissionDemoActivity", "PermissionDemoService")))))
ANDROID = "{http://schemas.android.com/apk/res/android}"
SIGNER_REVISION = "36.0.0"
APPROVED_APIS = (33, 34, 35)
MAX_INSTALLER_REPLY_BYTES = 1024**2
STARTUP_INITIALIZERS = {"androidx.emoji2.text.EmojiCompatInitializer", "androidx.lifecycle.ProcessLifecycleInitializer",
    "androidx.profileinstaller.ProfileInstallerInitializer"}
OPTIONAL_LIBRARIES = {"androidx.window.extensions", "androidx.window.sidecar"}
PROFILE_ACTIONS = {"androidx.profileinstaller.action." + name for name in
    ("INSTALL_PROFILE", "SKIP_FILE", "SAVE_PROFILE", "BENCHMARK_OPERATION")}


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def installer_reply_facts(result: subprocess.CompletedProcess) -> dict:
    """Bounded inert diagnostics, not an installer/byte/signature success receipt."""
    require(type(result.returncode) is int and isinstance(result.stdout, bytes) and isinstance(result.stderr, bytes),
        "Expected typed actual installer exit and byte streams")
    require(len(result.stdout) + len(result.stderr) <= MAX_INSTALLER_REPLY_BYTES,
        "Unbounded actual installer reply")
    lines = result.stdout.splitlines()
    shape = ("success" if lines == [b"Success"] else
        "streamed-success" if lines == [b"Performing Streamed Install", b"Success"] else "unrecognized")
    return {"stdout_bytes": len(result.stdout), "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
        "stdout_shape": shape, "stderr_bytes": len(result.stderr),
        "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
        "stderr_empty_after_trim": not result.stderr.strip(),
        "raw_stdout_stderr_or_paths_uploaded": False, "native_success_inferred": False}


def validate_manifest(payload: bytes, *, compiled: bool) -> dict:
    require(isinstance(payload, bytes) and 0 < len(payload) <= 65536, "Expected bounded approved-variant manifest")
    require(b"<!DOCTYPE" not in payload and b"<!ENTITY" not in payload, "Manifest entity/DTD refusal")
    manifest = ET.fromstring(payload, parser=ET.XMLParser(target=lt.NoDtdBuilder()))
    require(manifest.tag == "manifest" and manifest.get("package") in ({PACKAGE} if compiled else {None, PACKAGE}) and
        manifest.get(ANDROID + "sharedUserId") is None and manifest.get(ANDROID + "sharedUserMaxSdkVersion") is None,
        "Foreign app or shared-UID permission bypass")
    declarations = [node.get(ANDROID + "name") for node in manifest.findall("uses-permission")]
    permitted = RUNTIME_PERMISSIONS | ({PACKAGE + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"} if compiled else set())
    require(len(declarations) == len(set(declarations)) and set(declarations) <= permitted and
        RUNTIME_PERMISSIONS <= set(declarations) and not manifest.findall("uses-permission-sdk-23"),
        "Only the five explicitly approved variant permissions are permitted")
    require(all(node.get(ANDROID + "maxSdkVersion") is None for node in manifest.findall("uses-permission")),
        "The native fixture must not cap away a required runtime request")
    permissions = manifest.findall("permission")
    names = {node.get(ANDROID + "name") for node in permissions}
    permitted_names = {PERMISSION} | ({PACKAGE + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"} if compiled else set())
    levels = {"signature", "0x2", "0x00000002", "2"} if compiled else {"signature"}
    require(len(names) == len(permissions) and PERMISSION in names and names <= permitted_names and
        all(node.get(ANDROID + "protectionLevel") in levels for node in permissions), "Signature-only app control required")
    queries = manifest.findall("queries")
    require(len(queries) == 1 and len(queries[0]) == 1 and queries[0][0].tag == "package" and
        queries[0][0].get(ANDROID + "name") == REPORTER, "Only the exact reporter is visible to the fixture")
    applications = manifest.findall("application")
    require(len(applications) == 1, "Expected one disposable application")
    app = applications[0]
    require(app.get(ANDROID + "allowBackup") == "false" and app.get(ANDROID + "permission") is None and
        app.get(ANDROID + "process") is None and app.get(ANDROID + "enabled") in {None, "true"},
        "No app-wide UID/process/control override or backup")
    def full_name(node):
        name = node.get(ANDROID + "name", "")
        return PACKAGE + name if name.startswith(".") else name
    for tag, suffix in (("activity", "PermissionDemoActivity"), ("service", "PermissionDemoService")):
        nodes = app.findall(tag)
        require(len(nodes) == 1 and full_name(nodes[0]) == PACKAGE + "." + suffix and
            nodes[0].get(ANDROID + "permission") == PERMISSION and nodes[0].get(ANDROID + "exported") == "true" and
            nodes[0].get(ANDROID + "process") is None and nodes[0].get(ANDROID + "enabled") in {None, "true"} and not list(nodes[0]),
            "Only the explicit signature-protected Activity and service may expose fixture control")
    for node in app:
        if node.tag in {"activity", "service"}:
            continue
        require(compiled, "No extra source fixture component")
        if node.tag == "provider":
            require(full_name(node) == "androidx.startup.InitializationProvider" and
                node.get(ANDROID + "authorities") == PACKAGE + ".androidx-startup" and node.get(ANDROID + "exported") == "false" and
                set(node.attrib) == {ANDROID + key for key in ("name", "authorities", "exported")},
                "Unexpected compiled provider exposure")
            names = [child.get(ANDROID + "name") for child in node]
            require(len(names) == len(set(names)) and set(names) <= STARTUP_INITIALIZERS and
                all(child.tag == "meta-data" and not list(child) and
                    set(child.attrib) == {ANDROID + "name", ANDROID + "value"} and
                    child.get(ANDROID + "value") == "androidx.startup" for child in node),
                "Only the exact reviewed AndroidX startup metadata may initialize the app")
        elif node.tag == "uses-library":
            require(node.get(ANDROID + "name") in OPTIONAL_LIBRARIES and
                node.get(ANDROID + "required") == "false" and not list(node) and
                set(node.attrib) == {ANDROID + "name", ANDROID + "required"},
                "Only the exact optional AndroidX window libraries are permitted")
        elif node.tag == "receiver":
            require(full_name(node) == "androidx.profileinstaller.ProfileInstallReceiver" and
                node.get(ANDROID + "permission") == "android.permission.DUMP" and node.get(ANDROID + "exported") == "true" and
                node.get(ANDROID + "enabled") in {None, "true"} and node.get(ANDROID + "directBootAware") in {None, "false"} and
                set(node.attrib) <= {ANDROID + key for key in ("name", "permission", "exported", "enabled", "directBootAware")},
                "Unexpected compiled receiver exposure")
            require(all(child.tag == "intent-filter" and not child.attrib and len(child) == 1 and
                child[0].tag == "action" and not list(child[0]) and set(child[0].attrib) == {ANDROID + "name"} for child in node),
                "No extra profile-receiver category, data, metadata or control subtree")
            actions = [child[0].get(ANDROID + "name") for child in node]
            require(len(actions) == len(set(actions)) and set(actions) == PROFILE_ACTIONS,
                "Only the four exact DUMP-protected profile actions are permitted")
        else:
            raise ValueError("Unexpected compiled application declaration")
    libraries = [node.get(ANDROID + "name") for node in app.findall("uses-library")]
    require(len(libraries) == len(set(libraries)), "No duplicate compiled optional AndroidX library")
    require(len(app.findall("provider")) <= 1 and len(app.findall("receiver")) <= 1,
        "No duplicate compiled AndroidX components")
    sdk = manifest.findall("uses-sdk")
    if compiled:
        require(len(sdk) == 1 and sdk[0].get(ANDROID + "minSdkVersion") == "33" and
            sdk[0].get(ANDROID + "targetSdkVersion") == "37" and sdk[0].get(ANDROID + "maxSdkVersion") is None and
            app.get(ANDROID + "debuggable") == "true", "Wrong actual API33-minimum debug source variant")
    else:
        require(not sdk, "Use the pinned build SDK declaration")
    require(all(node.tag in {"uses-permission", "permission", "queries", "application", "uses-sdk"} for node in manifest),
        "Unexpected app manifest declaration")
    return {"compiled_manifest_inspected": compiled, "signature_control_only": True,
        "dedicated_call_variant": True, "all_files_and_sms_absent": True,
        "separate_uid_manifest": True, "manifest_sha256": hashlib.sha256(payload).hexdigest()}


def source_contract(root: Path) -> dict:
    inputs, code = {}, {}
    for relative in SOURCE_FILES:
        path = lt.safe_path(root, relative)
        before = path.stat()
        require(path.is_file() and before.st_nlink == 1 and 0 < before.st_size <= 1024**2,
            "Missing/nonregular/unbounded native permission fixture source")
        payload = path.read_bytes()
        after = path.stat()
        require((before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns),
            "Native fixture source changed during review")
        inputs[relative] = hashlib.sha256(payload).hexdigest()
        code[relative] = payload.decode("utf-8")
    validate_manifest(code[FIXTURE + "/src/main/AndroidManifest.xml"].encode(), compiled=False)
    source = "\n".join(text for path, text in code.items() if path.endswith(".kt"))
    require(not re.search(r"\b(?:grantRuntimePermission|revokeRuntimePermission|grantUriPermission|dispatchResult|setResult|adoptShellPermissionIdentity)\s*\(", source) and
        "Instrumentation.ActivityMonitor" not in source and "Runtime.getRuntime" not in source,
        "Manual grants, result injection, routing or shell-permission substitutes are forbidden")
    activity = code[APPLICATION_KOTLIN + "PermissionDemoActivity.kt"]
    require(all(token in activity for token in ("rememberPermissionState(Permission.Call)",
        "rememberPermissionState(Permission.RecordAudio)", "rememberMultiplePermissionsState(listOf(Permission.ReadImage, Permission.ReadVideo))",
        "rememberFilePickerLauncher(", "platformSelection.launch(arrayOf(Manifest.permission.READ_MEDIA_IMAGES",
        "Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED", "file.readByteArray(maxBytes = 65536)",
        "MediaStore.MediaColumns.OWNER_PACKAGE_NAME", "assertOwnedAndUnchanged(seed)",
        "contentResolver.delete(seed.uri, null, null) == 1")), "Actual public API/native owned-content obligations were removed")
    service = code[APPLICATION_KOTLIN + "PermissionDemoService.kt"]
    require("names == listOf(REPORTER)" in service and "PackageManager.SIGNATURE_MATCH" in service and
        "request.sendingUid" in service and "checkNotNull(PermissionDemoActivity.active).perform(operation)" in service,
        "Finite signature/actual sender admission must remain")
    return {"source_policy_verified": True, "source_inputs": inputs, "source_inputs_sha256": lt.input_digest(inputs),
        "native_or_compile_success_inferred": False}


def validate_prepared_receipt(receipt: dict, expected_source: dict, api_level: int | None = None) -> None:
    require(isinstance(receipt, dict), "The device controller's actual prepared fixture receipt is required")
    actual_api = receipt.get("verification_api_level")
    require(type(actual_api) is int and actual_api in APPROVED_APIS and (api_level is None or actual_api == api_level) and
        receipt.get("package") == PACKAGE and receipt.get("source_fixture") == FIXTURE and
        receipt.get("prepare_status") == "passed" and receipt.get("recipient_installed") is True and
        receipt.get("automatic_runtime_permission_grant") is False and receipt.get("source_contract") == expected_source,
        "No native permission request before exact source app preparation")
    policy, installed = receipt.get("apk_policy"), receipt.get("installed_readback")
    digest = receipt.get("source_apk_sha256")
    require(isinstance(policy, dict) and isinstance(installed, dict) and isinstance(digest, str) and
        re.fullmatch(r"[a-f0-9]{64}", digest) is not None and installed.get("apk_sha256") == digest and
        installed.get("exact_one_APK_path_observed") is True and policy.get("compiled_manifest_inspected") is True and
        policy.get("dedicated_call_variant") is True and policy.get("all_files_and_sms_absent") is True and
        policy.get("signature_control_only") is True and policy.get("separate_uid_manifest") is True,
        "Owned APK byte or compiled permission/UID boundary differs")
    certificate = policy.get("certificate_sha256")
    require(isinstance(certificate, str) and re.fullmatch(r"[a-f0-9]{64}", certificate) is not None and
        certificate == policy.get("private_key_certificate_sha256") and
        type(policy.get("signature_verification_min_sdk_version")) is int and
        type(policy.get("signature_verification_max_sdk_version")) is int and
        policy["signature_verification_min_sdk_version"] == policy["signature_verification_max_sdk_version"] == actual_api,
        "The actual private signer or exact authorized native SDK was not verified")


class OwnedPermissionDemo(OwnedShareRecipient):
    PACKAGE, FIXTURE, OUTPUT = PACKAGE, FIXTURE, "permission-demo"

    def __init__(self, *args, api_level: int, **kwargs):
        require(type(api_level) is int and api_level in APPROVED_APIS, "Only the finite API33/34/35 fixture is authorized")
        super().__init__(*args, **kwargs)
        self.api_level = api_level
        self.receipt.update(verification_api_level=api_level, prepare_status="not-started",
            prepare_phase="not-started",
            automatic_runtime_permission_grant=False,
            scope="Fresh separate-UID source app mounts public permission/picker APIs. Native grants, denials, selected-media and real OS picker results remain library test assertions. No sample/Maven consumer, phone call, audio recording, physical/minimum/ABI/security or release certification.")

    def host(self, command: list[str]) -> subprocess.CompletedProcess:
        result = subprocess.run(command, cwd=self.root, env=self.environment, capture_output=True, timeout=30)
        require(len(result.stdout) + len(result.stderr) <= 1024**2, "Unbounded actual APK inspection")
        return result

    def inspectors(self):
        analyzer = self.home / "cmdline-tools/23.0/bin/apkanalyzer"
        signer = self.home / ("build-tools/" + SIGNER_REVISION + "/apksigner")
        require(all(path.is_file() and os.access(path, os.X_OK) for path in (analyzer, signer)),
            "Explicit actual SDK analyzer/signer unavailable")
        return analyzer, signer

    def inspect_apk(self, apk: Path) -> dict:
        analyzer, signer = self.inspectors()
        manifest = self.host([str(analyzer), "manifest", "print", str(apk)])
        require(manifest.returncode == 0 and not manifest.stderr.strip(), "Actual compiled app manifest unavailable")
        policy = validate_manifest(manifest.stdout, compiled=True)
        certificate = signer_certificate(self.host([str(signer), "verify", "--verbose", "--print-certs",
            "--min-sdk-version", str(self.api_level), "--max-sdk-version", str(self.api_level), str(apk)]))
        key = lt.safe_path(self.root, (Path(self.environment["ANDROID_USER_HOME"]) / "debug.keystore").relative_to(self.root).as_posix())
        before = key.stat()
        require(key.is_file() and before.st_nlink == 1 and 0 < before.st_size <= 65536,
            "Exact private controller signing input unavailable")
        exported = self.host(["keytool", "-exportcert", "-keystore", str(key), "-alias", "androiddebugkey", "-storepass", "android"])
        require(exported.returncode == 0 and not exported.stderr.strip() and 0 < len(exported.stdout) <= 16384,
            "Actual private signing certificate unavailable")
        after = key.stat()
        require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_nlink) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_nlink),
            "Private key changed during certificate readback")
        expected = hashlib.sha256(exported.stdout).hexdigest()
        require(certificate == expected, "APK is not signed by the controller's actual private debug key")
        return policy | {"certificate_sha256": certificate, "private_key_certificate_sha256": expected,
            "signature_verification_min_sdk_version": self.api_level,
            "signature_verification_max_sdk_version": self.api_level,
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
            require(self.readback() is None, "Existing/foreign app must not be replaced or uninstalled")
            command = ["./gradlew", "--no-daemon", "--no-configuration-cache", "--max-workers=2", "--console=plain",
                "--no-parallel", "-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8",
                "-Pkotlin.compiler.execution.strategy=in-process", "-p", FIXTURE, "assembleDebug"]
            self.receipt["prepare_phase"] = "source-app-assembly"
            execution = lt.execute(self.root, command, self.output / "source-apk-build.log", 900, 8192, env=self.environment)
            self.receipt.update(assembly_command=command, assembly=execution)
            require(execution["exit_code"] == 0 and not execution.get("stop_reason"), "Separate source app did not assemble")
            self.receipt["prepare_phase"] = "source-apk-metadata"
            apk = metadata_apk(self.root, fixture=FIXTURE, package=PACKAGE)
            self.digest = lt.sha256(apk)
            self.receipt["prepare_phase"] = "source-apk-policy"
            self.receipt.update(source_apk_sha256=self.digest, source_apk_bytes=apk.stat().st_size,
                apk_policy=self.inspect_apk(apk))
            self.receipt["prepare_phase"] = "source-apk-source-recheck"
            require(lt.sha256(apk) == self.digest and source_contract(self.root) == contract, "Source/APK changed during inspection")
            self.install_attempted = True
            self.receipt["prepare_phase"] = "owned-installer"
            install = self.control("install", "-t", str(apk), timeout=120)
            self.receipt["install_exit_code"] = install.returncode
            self.receipt["prepare_phase"] = "installer-reply-facts"
            self.receipt["installer_reply"] = installer_reply_facts(install)
            self.receipt["prepare_phase"] = "installed-byte-readback"
            actual = self.readback() # Reconcile an uncertain installer before any possible owned cleanup.
            installed = actual is not None and actual.get("apk_sha256") == self.digest
            self.receipt.update(install_exit_code=install.returncode, installed_readback=actual, recipient_installed=installed)
            self.receipt["prepare_phase"] = "installer-reply-validation"
            reply = self.receipt["installer_reply"]
            require(install.returncode == 0 and reply["stdout_shape"] in {"success", "streamed-success"} and
                reply["stderr_empty_after_trim"] and installed,
                "Fresh app install/byte readback did not pass")
            self.receipt["prepare_status"] = "passed"
            self.receipt["prepare_phase"] = "prepared-receipt-validation"
            validate_prepared_receipt(self.receipt, contract, self.api_level)
            self.receipt["prepare_phase"] = "complete"
            return self.receipt
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt) as failure:
            self.receipt.update(prepare_status="failed", prepare_error=type(failure).__name__,
                prepare_error_phase=self.receipt["prepare_phase"])
            raise
        finally:
            lt.write_json(self.output / "receipt.json", self.receipt)

    def close(self) -> dict:
        try:
            value = super().close()
            require(value.get("owned_recipient_removed") is True, "Actual owned source app removal is unverified")
            value["cleanup_status"] = "passed"
            return value
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as failure:
            self.receipt.update(cleanup_status="failed", cleanup_error=type(failure).__name__)
            raise
        finally:
            lt.write_json(self.output / "receipt.json", self.receipt)
