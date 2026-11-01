"""Finite separate-UID storage helper, exact APK identities and ordered teardown.

Source/manifest/signing refusals precede installation and reporter compilation.
Only the eight reviewed API/flavor/method rows are admitted. Helper-UID cleanup
releases only the nonce-bound SAF grant before WRITE/app-op restoration and app
removal. Receipts never infer native case, consumer, security or release success.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid
import xml.etree.ElementTree as ET

from android_geo_probe import unique
from android_share_recipient import OwnedShareRecipient
import android_storage_compatibility_plan as storage
import library_tests as lt

PACKAGE, REPORTER, MODULE = storage.PACKAGE, storage.REPORTER, storage.MODULE
FIXTURE = "tests/consumer/android-storage-probe"
PERMISSION = PACKAGE + ".CONTROL_STORAGE"
# Known separate signature-protected permission-demo control, not a runtime storage grant.
PERMISSION_DEMO_BIND = "io.github.apdelrahman1911.nativecmpkit.verification.permissiondemo.BIND_DEMO"
AUTHORITY = PACKAGE + ".control"
WRITE = "android.permission.WRITE_EXTERNAL_STORAGE"
ALL_FILES = "android.permission.MANAGE_EXTERNAL_STORAGE"
DYNAMIC = PACKAGE + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
ANDROID = "{http://schemas.android.com/apk/res/android}"
OPTIONAL_LIBRARIES = frozenset({"androidx.window.extensions", "androidx.window.sidecar"})
SIGNER_REVISION = "36.0.0"
MAX_HOST_BYTES = 1024**2
FLAVORS = tuple(dict.fromkeys(row.flavor for row in storage.ROWS))
KOTLIN = MODULE + "/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/permissions/"
HELPER_KOTLIN = FIXTURE + "/src/main/kotlin/" + PACKAGE.replace(".", "/") + "/"
REPORTER_NAMES = ("AndroidStorageCompatibilityTest", "OwnedStorageProbe", "StorageTestDocumentsProvider")
HELPER_NAMES = ("StorageProbe", "StorageProbeIdentity", "StorageProbeControlProvider")
HELPER_SOURCE_FILES = tuple(sorted((FIXTURE + "/src/main/AndroidManifest.xml",
    *(FIXTURE + "/src/" + flavor + "/AndroidManifest.xml" for flavor in FLAVORS),
    *(HELPER_KOTLIN + name + ".kt" for name in HELPER_NAMES))))
SOURCE_FILES = tuple(sorted(("gradle/libs.versions.toml", MODULE + "/build.gradle.kts",
    MODULE + "/src/androidDeviceTest/AndroidManifest.xml", FIXTURE + "/build.gradle.kts",
    FIXTURE + "/settings.gradle.kts", FIXTURE + "/gradle.properties",
    "scripts/ci/android_storage_compatibility_plan.py", "scripts/ci/android_storage_probe.py",
    *HELPER_SOURCE_FILES, *(KOTLIN + name + ".kt" for name in REPORTER_NAMES))))
STATUS_KEYS = {"schema", "operation", "case_nonce", "request_nonce", "package", "uid", "pid", "sdk", "target", "mode",
    "apk_sha256", "certificate_sha256", "splits_absent", "record_present", "activity_active",
    "persisted_read_count", "foreign_persisted_count", "native_read_grant", "write_granted",
    "manager", "manager_mode", "release_verified", "record_cleared", "status"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def xml(payload: bytes) -> ET.Element:
    require(isinstance(payload, bytes) and 0 < len(payload) <= 65536, "Expected bounded owned manifest bytes")
    try:
        return ET.fromstring(payload, parser=ET.XMLParser(target=lt.NoDtdBuilder()))
    except ET.ParseError as error:
        raise ValueError("Owned storage manifest is not XML") from error


def name(node: ET.Element) -> str:
    value = node.get(ANDROID + "name", "")
    return PACKAGE + value if value.startswith(".") else value


def validate_flavor_manifest(payload: bytes, flavor: str) -> None:
    require(flavor in FLAVORS, "Unknown static storage flavor")
    row = next(row for row in storage.ROWS if row.flavor == flavor)
    manifest = xml(payload)
    require(manifest.tag == "manifest" and not manifest.attrib.keys() - {"package"} and
            manifest.get("package") in {None, PACKAGE} and
            all(node.tag in {"uses-permission", "application"} for node in manifest), "Unexpected flavor declarations")
    permissions = manifest.findall("uses-permission")
    expected = ({ANDROID + "name": WRITE, ANDROID + "maxSdkVersion": "28" if flavor == "legacy28" else "29"}
                if row.declares_write else {ANDROID + "name": ALL_FILES} if row.declares_all_files else None)
    require((len(permissions) == 0 if expected is None else len(permissions) == 1 and permissions[0].attrib == expected) and
            all(len(node) == 0 for node in permissions), "Wrong flavor storage permission boundary")
    applications = manifest.findall("application")
    legacy = "true" if flavor == "legacy29" else "false" if flavor in {"scoped29", "modern", "allFiles"} else None
    require((not applications if legacy is None else len(applications) == 1 and
            applications[0].attrib == {ANDROID + "requestLegacyExternalStorage": legacy} and len(applications[0]) == 0),
            "Target28 defaults and explicit target29/scoped modes must not be interchanged")


def validate_support_component(node: ET.Element, package: str) -> None:
    """Only fixed AndroidX merge contributions, never an arbitrary exported ingress."""
    component = node.get(ANDROID + "name")
    require(node.get(ANDROID + "process") is None and node.get(ANDROID + "enabled") in {None, "true"},
            "Unexpected support component process/state")
    if node.tag == "uses-library" and component in OPTIONAL_LIBRARIES:
        require(node.attrib == {ANDROID + "name": component, ANDROID + "required": "false"} and len(node) == 0,
                "Only the exact optional AndroidX window libraries are permitted")
        return
    if node.tag == "provider" and component == "androidx.startup.InitializationProvider":
        require(node.get(ANDROID + "authorities") == package + ".androidx-startup" and
                node.get(ANDROID + "exported") == "false" and
                node.get(ANDROID + "grantUriPermissions") in {None, "false"} and
                node.get(ANDROID + "permission") is None and
                all(item.tag == "meta-data" and item.get(ANDROID + "name") in {
                    "androidx.lifecycle.ProcessLifecycleInitializer", "androidx.emoji2.text.EmojiCompatInitializer",
                    "androidx.profileinstaller.ProfileInstallerInitializer"} and
                    item.get(ANDROID + "value") == "androidx.startup" and len(item) == 0 for item in node) and
                len({item.get(ANDROID + "name") for item in node}) == len(node), "Unknown AndroidX startup merge contribution")
        return
    if node.tag == "receiver" and component == "androidx.profileinstaller.ProfileInstallReceiver":
        actions = [item.get(ANDROID + "name") for group in node for item in group]
        require(node.get(ANDROID + "exported") == "true" and node.get(ANDROID + "permission") == "android.permission.DUMP" and
                all(group.tag == "intent-filter" and len(group) == 1 and group[0].tag == "action" for group in node) and
                len(actions) == 4 and set(actions) == {"androidx.profileinstaller.action.INSTALL_PROFILE",
                    "androidx.profileinstaller.action.SKIP_FILE", "androidx.profileinstaller.action.SAVE_PROFILE",
                    "androidx.profileinstaller.action.BENCHMARK_OPERATION"}, "Unknown profile-installer ingress")
        return
    raise ValueError("Unknown helper merged component; no broad manifest fallback")


def support_refusal_facts(node: ET.Element, payload: bytes) -> dict:
    """Fixed labels or bounded hashes only; no unreviewed names/values/paths."""
    require(isinstance(payload, bytes) and 0 < len(payload) <= 65536, "Expected bounded support refusal bytes")
    tag, component = node.tag, node.get(ANDROID + "name", "")
    tag_bytes, component_bytes = tag.encode("utf-8"), component.encode("utf-8")
    return {"schema": "nativecmpkit-storage-support-refusal-facts-v1", "status": "retained",
        "manifest_bytes": len(payload), "manifest_sha256": hashlib.sha256(payload).hexdigest(),
        "node_tag": tag if tag in {"activity", "activity-alias", "service", "provider", "receiver", "uses-library", "meta-data"} else "other",
        "node_tag_bytes": len(tag_bytes), "node_tag_sha256": hashlib.sha256(tag_bytes).hexdigest(),
        "component_name": component if component in OPTIONAL_LIBRARIES | {
            "androidx.startup.InitializationProvider", "androidx.profileinstaller.ProfileInstallReceiver"} else "other" if component else "missing",
        "component_name_bytes": len(component_bytes), "component_name_sha256": hashlib.sha256(component_bytes).hexdigest(),
        "attribute_count": len(node.attrib), "attribute_names_sha256": hashlib.sha256(json.dumps(sorted(node.attrib)).encode()).hexdigest(),
        "child_count": len(node), "raw_names_values_paths_or_exception_bodies_uploaded": False, "native_success_inferred": False}


def validate_manifest(payload: bytes, *, compiled: bool, profile: str | None = None, support_refusal: dict | None = None) -> dict:
    manifest = xml(payload)
    row = storage.row_for(profile) if compiled else None
    require(manifest.tag == "manifest" and (manifest.get("package") == PACKAGE if compiled else manifest.get("package") in {None, PACKAGE}) and
            manifest.get(ANDROID + "sharedUserId") is None and manifest.get(ANDROID + "sharedUserMaxSdkVersion") is None and
            all(node.tag in {"permission", "uses-permission", "queries", "application", "uses-sdk"} for node in manifest),
            "Wrong owned helper package, shared UID or manifest route")
    require(compiled or not manifest.findall("uses-sdk"), "Source SDK belongs to the exact Gradle flavor")
    queries = manifest.findall("queries")
    require(len(queries) == 1 and len(queries[0]) == 2 and
            len(queries[0].findall("package")) == 1 and queries[0].find("package").attrib == {ANDROID + "name": REPORTER},
            "Only the fixed reporter package and genuine OPEN_DOCUMENT query are admitted")
    intents = queries[0].findall("intent")
    require(len(intents) == 1 and [(item.tag, item.attrib) for item in intents[0]] == [
        ("action", {ANDROID + "name": "android.intent.action.OPEN_DOCUMENT"}),
        ("category", {ANDROID + "name": "android.intent.category.OPENABLE"}),
        ("data", {ANDROID + "mimeType": "application/octet-stream"})], "Unexpected helper intent visibility")
    levels = {"signature", "0x00000002", "0x2", "2"} if compiled else {"signature"}
    permissions = manifest.findall("permission")
    declared = {node.get(ANDROID + "name"): node for node in permissions}
    require(len(declared) == len(permissions) and set(declared) in ({PERMISSION}, {PERMISSION, DYNAMIC} if compiled else {PERMISSION}) and
            all(node.get(ANDROID + "protectionLevel") in levels and len(node) == 0 for node in permissions),
            "Wrong helper signature-control permission declarations")
    requested = manifest.findall("uses-permission")
    requested_names = [node.get(ANDROID + "name") for node in requested]
    expected_requested = ({WRITE} if row and row.declares_write else {ALL_FILES} if row and row.declares_all_files else set())
    require(len(set(requested_names)) == len(requested_names) and set(requested_names) - {DYNAMIC} == expected_requested and
            ((DYNAMIC in requested_names) == (DYNAMIC in declared)), "No broad or automatic runtime storage permission")
    for node in requested:
        if node.get(ANDROID + "name") == WRITE:
            require(node.get(ANDROID + "maxSdkVersion") == ("28" if row.flavor == "legacy28" else "29"), "Wrong bounded WRITE SDK")
        else:
            require(node.get(ANDROID + "maxSdkVersion") is None, "Unexpected helper special/internal permission maximum")
        require(len(node) == 0, "Unexpected requested-permission children")
    applications = manifest.findall("application")
    require(len(applications) == 1, "Expected one owned helper application")
    app = applications[0]
    require(app.get(ANDROID + "allowBackup") == "false" and app.get(ANDROID + "process") is None and
            app.get(ANDROID + "permission") is None and app.get(ANDROID + "enabled") in {None, "true"} and
            app.get(ANDROID + "appComponentFactory") in {None, "androidx.core.app.CoreComponentFactory"},
            "No application-wide process/permission/backup bypass")
    expected_components = {PACKAGE + ".StorageProbeActivity": "activity", PACKAGE + ".StorageProbeService": "service",
                           PACKAGE + ".StorageProbeControlProvider": "provider"}
    owned = [node for node in app if name(node) in expected_components]
    require({name(node) for node in owned} == set(expected_components) and len(owned) == 3,
            "Missing or duplicate fixed helper components")
    for node in owned:
        require(node.tag == expected_components[name(node)] and node.get(ANDROID + "exported") == "true" and
                node.get(ANDROID + "enabled") in {None, "true"} and node.get(ANDROID + "process") is None and len(node) == 0,
                "Wrong helper component/process/intent admission")
        if node.tag == "provider":
            require(node.get(ANDROID + "permission") == "android.permission.DUMP" and
                    node.get(ANDROID + "readPermission") is None and node.get(ANDROID + "writePermission") is None and
                    node.get(ANDROID + "authorities") == (AUTHORITY if compiled else "${applicationId}.control") and
                    node.get(ANDROID + "grantUriPermissions") == "false", "Cleanup has no grant/path or unprotected route")
        else:
            require(node.get(ANDROID + "permission") == PERMISSION, "Only signature-protected reporter entry is admitted")
    require(len({name(node) for node in app}) == len(app), "Duplicate helper merged components")
    for node in app:
        if node not in owned:
            require(compiled, "Unexpected helper source component")
            try:
                validate_support_component(node, PACKAGE)
            except ValueError:
                if type(support_refusal) is dict:
                    try:
                        support_refusal.update(support_refusal_facts(node, payload))
                    except (Exception, KeyboardInterrupt):
                        pass  # Diagnostic failure never replaces the original refusal.
                raise
    if compiled:
        sdk = manifest.findall("uses-sdk")
        legacy = "true" if row.flavor == "legacy29" else "false" if row.flavor in {"scoped29", "modern", "allFiles"} else None
        require(len(sdk) == 1 and sdk[0].get(ANDROID + "minSdkVersion") == "23" and
                sdk[0].get(ANDROID + "targetSdkVersion") == str(row.target) and sdk[0].get(ANDROID + "maxSdkVersion") is None and
                app.get(ANDROID + "debuggable") == "true" and app.get(ANDROID + "requestLegacyExternalStorage") == legacy,
                "Compiled storage SDK/flavor/debug mode changed")
    return {"compiled_manifest_inspected": compiled, "manifest_sha256": hashlib.sha256(payload).hexdigest(),
            "signature_control_only": True, "shell_cleanup_requires_DUMP_and_UID2000": True,
            "fixed_helper_components_verified": True, "static_storage_permissions_verified": True,
            "native_permission_or_result_inferred": False}


def validate_reporter_manifest(payload: bytes) -> dict:
    manifest = xml(payload)
    require(manifest.tag == "manifest" and manifest.get("package") == REPORTER and
            manifest.get(ANDROID + "sharedUserId") is None and manifest.get(ANDROID + "sharedUserMaxSdkVersion") is None,
            "Wrong reporter package/shared UID")
    sdk, applications, instrumentation = manifest.findall("uses-sdk"), manifest.findall("application"), manifest.findall("instrumentation")
    require(len(sdk) == len(applications) == len(instrumentation) == 1 and
            sdk[0].get(ANDROID + "minSdkVersion") == "23" and sdk[0].get(ANDROID + "targetSdkVersion") == "37" and
            instrumentation[0].get(ANDROID + "name") == "androidx.test.runner.AndroidJUnitRunner" and
            instrumentation[0].get(ANDROID + "targetPackage") == REPORTER,
            "Reporter must be the actual min23/target37 library AndroidJUnitRunner")
    requested = [node.get(ANDROID + "name") for node in manifest.findall("uses-permission")]
    allowed = {PERMISSION, PERMISSION_DEMO_BIND, "android.permission.INTERNET", "android.permission.ACCESS_NETWORK_STATE",
               REPORTER + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"}
    require(PERMISSION in requested and len(requested) == len(set(requested)) and set(requested) <= allowed and
            not manifest.findall("uses-permission-sdk-23"), "Reporter cannot bypass another UID's native storage or SAF grant")
    app = applications[0]
    require(app.get(ANDROID + "debuggable") == "true" and app.get(ANDROID + "process") is None and
            app.get(ANDROID + "permission") is None, "Wrong reporter debug/process/permission boundary")
    providers = [node for node in app.findall("provider") if node.get(ANDROID + "name") ==
                 "com.mohamedrejeb.calf.permissions.StorageTestDocumentsProvider"]
    require(len(providers) == 1, "Missing or duplicate owned reporter document provider")
    provider = providers[0]
    require(provider.get(ANDROID + "authorities") == REPORTER + ".storage-documents" and
            provider.get(ANDROID + "exported") == "true" and provider.get(ANDROID + "grantUriPermissions") == "true" and
            provider.get(ANDROID + "permission") == "android.permission.MANAGE_DOCUMENTS" and
            provider.get(ANDROID + "readPermission") is None and provider.get(ANDROID + "writePermission") is None and
            provider.get(ANDROID + "process") is None and len(provider) == 1 and
            provider[0].tag == "intent-filter" and len(provider[0]) == 1 and provider[0][0].tag == "action" and
            provider[0][0].get(ANDROID + "name") == "android.content.action.DOCUMENTS_PROVIDER",
            "Reporter private document bytes require genuine system-created grants")
    return {"compiled_manifest_inspected": True, "manifest_sha256": hashlib.sha256(payload).hexdigest(),
            "native_storage_permissions_absent": True, "document_requires_android_grant": True,
            "native_result_inferred": False}


def validate_source_receipt(contract: dict) -> None:
    require(isinstance(contract, dict) and set(contract) == {"source_policy_verified", "source_inputs", "source_inputs_sha256", "native_or_compile_success_inferred"} and
            contract.get("source_policy_verified") is True and contract.get("native_or_compile_success_inferred") is False,
            "Missing source-only storage policy witness")
    inputs = contract.get("source_inputs")
    require(isinstance(inputs, dict) and tuple(sorted(inputs)) == SOURCE_FILES and
            all(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) for value in inputs.values()) and
            contract.get("source_inputs_sha256") == lt.input_digest(inputs), "Unknown or changed storage source identity")


def source_contract(root: Path) -> dict:
    texts, inputs = {}, {}
    for relative in SOURCE_FILES:
        path = lt.safe_path(root, relative); before = path.stat()
        require(path.is_file() and before.st_nlink == 1 and 0 < before.st_size <= 256 * 1024, "Missing, linked or unbounded storage source")
        payload = path.read_bytes(); after = path.stat()
        require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), "Storage source changed while reading")
        inputs[relative] = hashlib.sha256(payload).hexdigest(); texts[relative] = payload.decode("utf-8")
    actual = {path.relative_to(root).as_posix() for path in lt.source_files(root, FIXTURE + "/src")}
    require(actual == set(HELPER_SOURCE_FILES), "Unexpected helper/flavor source inventory")
    validate_manifest(texts[FIXTURE + "/src/main/AndroidManifest.xml"].encode(), compiled=False)
    for flavor in FLAVORS:
        validate_flavor_manifest(texts[FIXTURE + "/src/" + flavor + "/AndroidManifest.xml"].encode(), flavor)
    reporter = xml(texts[MODULE + "/src/androidDeviceTest/AndroidManifest.xml"].encode())
    requested = [node.get(ANDROID + "name") for node in reporter.findall("uses-permission")]
    require(PERMISSION in requested and len(requested) == len(set(requested)) and
            set(requested) <= {PERMISSION, PERMISSION_DEMO_BIND} and not reporter.findall("uses-permission-sdk-23") and
            reporter.get(ANDROID + "sharedUserId") is None, "Reporter source cannot acquire native storage permissions")
    app = reporter.find("application")
    require(app is not None and app.get(ANDROID + "permission") is None and app.get(ANDROID + "process") is None and
            len(app) == 1 and app[0].tag == "provider" and app[0].get(ANDROID + "name") ==
            "com.mohamedrejeb.calf.permissions.StorageTestDocumentsProvider" and
            app[0].get(ANDROID + "authorities") == "${applicationId}.storage-documents" and
            app[0].get(ANDROID + "permission") == "android.permission.MANAGE_DOCUMENTS" and
            app[0].get(ANDROID + "readPermission") is None and app[0].get(ANDROID + "writePermission") is None and
            app[0].get(ANDROID + "exported") == "true" and app[0].get(ANDROID + "grantUriPermissions") == "true",
            "Reporter owns only the protected private SAF test provider")
    build = texts[FIXTURE + "/build.gradle.kts"]
    require('namespace = "' + PACKAGE + '"' in build and 'applicationId = "' + PACKAGE + '"' in build and
            all(token in build for token in ('compileSdk = libs.versions.android.compileSdk.get().toInt()',
                'minSdk = libs.versions.android.minSdk.get().toInt()', 'targetSdk = 35', 'targetSdk = sdk',
                'flavorDimensions += "storageMode"', 'buildFeatures { buildConfig = true }',
                '"legacy28" to 28', '"legacyTarget28" to 28', '"legacy29" to 29', '"scoped29" to 29',
                '"modern" to 35', '"allFiles" to 35', 'implementation("verification.nativecmpkit:unpublished-permissions-core")')) and
            'from(files("../../../gradle/libs.versions.toml"))' in texts[FIXTURE + "/settings.gradle.kts"] and
            'project(":calf-permissions:calf-permissions-core")' in texts[FIXTURE + "/settings.gradle.kts"] and
            'android-minSdk = "23"' in texts['gradle/libs.versions.toml'] and
            'android-compileSdk = "37"' in texts['gradle/libs.versions.toml'], "Exact storage build/source substitution/SDK declarations changed")
    test = texts[KOTLIN + "AndroidStorageCompatibilityTest.kt"]
    methods = re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", test)
    require(methods == list(dict.fromkeys(row.method for row in storage.ROWS)) and
            not re.search(r"@(Ignore|Disabled|IgnoredTest)\b", test), "The six finite native methods must remain authored and enabled")
    native = "\n".join(texts[HELPER_KOTLIN + name + ".kt"] for name in HELPER_NAMES)
    reporter_code = "\n".join(texts[KOTLIN + name + ".kt"] for name in REPORTER_NAMES)
    for relative, tokens in {
        HELPER_KOTLIN + "StorageProbe.kt": ('rememberPermissionState(Permission.WriteStorage)', 'request.sendingUid',
            'setOf(REPORTER)', 'StorageControlRecord.begin', 'Intent.ACTION_OPEN_DOCUMENT', 'takePersistableUriPermission',
            'releasePersistableUriPermission', 'OsConstants.O_EXCL', 'context.checkSelfPermission'),
        HELPER_KOTLIN + "StorageProbeIdentity.kt": ('apkContentsSigners', 'hasMultipleSigners()', 'sourceDir', 'MessageDigest', 'Os.lstat'),
        HELPER_KOTLIN + "StorageProbeControlProvider.kt": ('Binder.getCallingUid() == 2000', 'enforceCallingPermission',
            'android.permission.DUMP', 'AtomicFile', 'checkUriPermission', 'finishAndRemoveTask()', 'StorageControlRecord.ownedUri'),
        KOTLIN + "OwnedStorageProbe.kt": ('nativecmpkitOwnedStorageProbe', 'nativecmpkitStorageApkSha256',
            'nativecmpkitStorageReporterApkSha256', 'getPackagesForUid', 'service.linkToDeath', 'isBinderAlive'),
        KOTLIN + "AndroidStorageCompatibilityTest.kt": ('nativecmpkitStorageCaseNonce', 'grantRuntimePermission',
            'revokeRuntimePermission', 'stopRebindingBeforeRevocation', 'rootInActiveWindow', 'MODE_DEFAULT'),
    }.items():
        require(all(token in texts[relative] for token in tokens), "Storage nonce/identity/public/native/ordered-cleanup source contract changed")
    require("grantUriPermission(" not in native + reporter_code and "Runtime.getRuntime" not in native and
            "UiAutomation" not in native and "executeShellCommand" not in native and
            'getString("document_uri"' not in texts[HELPER_KOTLIN + "StorageProbeControlProvider.kt"],
            "No manual URI grant or arbitrary cleanup URI/path/shell operation is admitted")
    result = {"source_policy_verified": True, "source_inputs": inputs, "source_inputs_sha256": lt.input_digest(inputs),
              "native_or_compile_success_inferred": False}
    validate_source_receipt(result)
    return result


def metadata_apk(root: Path, profile: str, *, reporter: bool = False) -> Path:
    row = storage.row_for(profile)
    base = lt.safe_path(root, MODULE + "/build/outputs/apk/androidTest" if reporter else
                       FIXTURE + "/build/outputs/apk/" + row.flavor + "/debug")
    metadata = lt.safe_path(root, (base / "output-metadata.json").relative_to(root).as_posix())
    require(metadata.is_file() and metadata.stat().st_nlink == 1 and 0 < metadata.stat().st_size <= 65536,
            "Expected exact selected-variant APK metadata; no APK search")
    data = json.loads(metadata.read_bytes(), object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite APK metadata")))
    require(isinstance(data, dict) and data.get("applicationId") == (REPORTER if reporter else PACKAGE) and
            data.get("variantName") == ("androidDeviceTest" if reporter else row.flavor + "Debug") and
            isinstance(data.get("artifactType"), dict) and data["artifactType"].get("type") == "APK",
            "Wrong fixed package or selected APK variant")
    rows = data.get("elements")
    require(isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict), "Expected exactly one owned APK metadata element")
    element = rows[0]; filename = element.get("outputFile", "")
    require(element.get("type") == "SINGLE" and element.get("filters") == [] and
            isinstance(filename, str) and re.fullmatch(r"[A-Za-z0-9_.-]+\.apk", filename), "Only one unsplit selected APK is admitted")
    apk = lt.safe_path(root, (base / filename).relative_to(root).as_posix())
    require(apk.is_file() and apk.stat().st_nlink == 1 and 0 < apk.stat().st_size < 256 * 1024**2, "Expected bounded regular actual APK")
    return apk


def signer_certificate(result: subprocess.CompletedProcess) -> str:
    require(isinstance(result.stdout, bytes) and isinstance(result.stderr, bytes) and
            len(result.stdout) + len(result.stderr) <= MAX_HOST_BYTES and result.returncode == 0 and not result.stderr.strip(),
            "APK signature verification unavailable")
    text = result.stdout.decode("utf-8")
    require(not re.search(r"(?im)\b(?:warning|error|does not verify)\b", text), "Signer warning/error/unknown verification remains refused")
    lines = text.splitlines()
    allowed_lines = (
        r"Verifies", r"Number of signers: 1",
        r"Verified using v1 scheme \(JAR signing\): (?:true|false)",
        r"Verified using v2 scheme \(APK Signature Scheme v2\): (?:true|false)",
        r"Verified using v3 scheme \(APK Signature Scheme v3\): (?:true|false)",
        r"Verified using v3\.1 scheme \(APK Signature Scheme v3\.1\): (?:true|false)",
        r"Verified using v4 scheme \(APK Signature Scheme v4\): (?:true|false)",
        r"Verified for SourceStamp: false",
        r"Signer #1 certificate DN: [^\r\n\x00]{1,4096}",
        r"Signer #1 (?:certificate|public key) SHA-256 digest: [a-f0-9]{64}",
        r"Signer #1 (?:certificate|public key) SHA-1 digest: [a-f0-9]{40}",
        r"Signer #1 (?:certificate|public key) MD5 digest: [a-f0-9]{32}",
        r"Signer #1 key algorithm: (?:RSA|EC|DSA)", r"Signer #1 key size \(bits\): [0-9]{2,6}",
    )
    require(lines and len(lines) == len(set(lines)) and
            all(any(re.fullmatch(pattern, line) for pattern in allowed_lines) for line in lines),
            "Unknown or duplicate APK signer protocol output")
    certificates = re.findall(r"(?m)^Signer #1 certificate SHA-256 digest: ([a-f0-9]{64})$", text)
    require(len(certificates) == 1 and re.search(r"(?m)^Number of signers: 1$", text) is not None and
            re.search(r"(?m)^Verified using v[23] scheme \([^\r\n]+\): true$", text) is not None and
            not re.search(r"(?m)^Signer #[2-9][0-9]* ", text), "Expected one actual verified APK signer")
    return certificates[0]


def validate_native_status(status: dict, receipt: dict, *, operation: str, request_nonce: str | None = None) -> None:
    row = storage.row_for(receipt.get("profile"))
    require(isinstance(status, dict) and set(status) == STATUS_KEYS and status.get("schema") == "nativecmpkit-storage-control-v1" and
            status.get("status") == "passed" and status.get("operation") == operation and operation in {"status", "cleanup"} and
            status.get("case_nonce") == receipt.get("case_nonce") and
            isinstance(status.get("request_nonce"), str) and re.fullmatch(r"[a-f0-9]{32}", status["request_nonce"]) and
            (request_nonce is None or status["request_nonce"] == request_nonce) and status.get("package") == PACKAGE and
            type(status.get("uid")) is int and status["uid"] == receipt.get("installed_uid") and status["uid"] >= 10000 and
            type(status.get("pid")) is int and status["pid"] > 0 and type(status.get("sdk")) is int and status["sdk"] == row.api and
            type(status.get("target")) is int and status["target"] == row.target and status.get("mode") == row.flavor and
            status.get("apk_sha256") == receipt.get("source_apk_sha256") and
            status.get("certificate_sha256") == receipt.get("apk_policy", {}).get("certificate_sha256") and
            status.get("splits_absent") is True, "Native helper UID/APK/certificate/SDK/flavor or cleanup receipt disagrees")
    require(all(type(status.get(key)) is bool for key in ("record_present", "activity_active", "native_read_grant",
            "write_granted", "release_verified", "record_cleared")) and
            type(status.get("persisted_read_count")) is int and status["persisted_read_count"] in {0, 1} and
            type(status.get("foreign_persisted_count")) is int and status["foreign_persisted_count"] == 0,
            "Unknown/foreign actual storage cleanup state")
    if row.api >= 30:
        require(type(status.get("manager")) is bool and type(status.get("manager_mode")) is int and
                status["manager_mode"] in {0, 3}, "Unknown actual special-access state")
    else:
        require(status.get("manager") is None and status.get("manager_mode") is None,
                "No API30 special-access call or fabricated result below API30")
    if operation == "cleanup":
        require(status["release_verified"] is True and status["record_cleared"] is True and
                status["record_present"] is False and status["activity_active"] is False and
                status["persisted_read_count"] == 0 and status["native_read_grant"] is False,
                "SAF release and Activity removal must precede grant/app-op restore or blind app removal")


def validate_prepared_receipt(receipt: dict, expected_source: dict | None = None, *, require_reporter: bool = True) -> None:
    require(isinstance(receipt, dict), "Missing exact owned storage preparation")
    row = storage.row_for(receipt.get("profile"))
    require(receipt.get("package") == PACKAGE and receipt.get("source_fixture") == FIXTURE and
            receipt.get("prepare_status") == "passed" and receipt.get("recipient_installed") is True and
            type(receipt.get("verification_api_level")) is int and receipt["verification_api_level"] == row.api and
            type(receipt.get("target_sdk")) is int and receipt["target_sdk"] == row.target and receipt.get("flavor") == row.flavor and
            receipt.get("manual_URI_grant") is False and receipt.get("automatic_runtime_permission_grant") is False and
            type(receipt.get("installed_uid")) is int and receipt["installed_uid"] >= 10000 and
            isinstance(receipt.get("case_nonce"), str) and re.fullmatch(r"[a-f0-9]{32}", receipt["case_nonce"]),
            "Owned storage row/native identity preparation has not passed")
    digest, installed, policy = receipt.get("source_apk_sha256"), receipt.get("installed_readback"), receipt.get("apk_policy")
    require(isinstance(digest, str) and re.fullmatch(r"[a-f0-9]{64}", digest) and isinstance(installed, dict) and
            installed.get("apk_sha256") == digest and installed.get("exact_one_APK_path_observed") is True and isinstance(policy, dict) and
            all(policy.get(key) is True for key in ("compiled_manifest_inspected", "signature_control_only",
                "shell_cleanup_requires_DUMP_and_UID2000", "fixed_helper_components_verified", "static_storage_permissions_verified")) and
            isinstance(policy.get("certificate_sha256"), str) and re.fullmatch(r"[a-f0-9]{64}", policy["certificate_sha256"]) and
            policy["certificate_sha256"] == policy.get("private_key_certificate_sha256") and
            isinstance(policy.get("manifest_sha256"), str) and re.fullmatch(r"[a-f0-9]{64}", policy["manifest_sha256"]) and
            policy.get("apk_signer_revision") == SIGNER_REVISION and
            type(policy.get("signature_verification_min_sdk_version")) is int and policy["signature_verification_min_sdk_version"] == row.api and
            type(policy.get("signature_verification_max_sdk_version")) is int and policy["signature_verification_max_sdk_version"] == row.api,
            "Selected helper APK/source/private-key or exact API signer range disagrees")
    validate_source_receipt(receipt.get("source_contract"))
    require(expected_source is None or receipt["source_contract"] == expected_source, "Helper/reporter source freeze differs")
    initial = receipt.get("initial_native_status")
    validate_native_status(initial, receipt, operation="status")
    require(initial["record_present"] is False and initial["activity_active"] is False and initial["persisted_read_count"] == 0 and
            initial["native_read_grant"] is False and initial["write_granted"] is False and
            (row.api < 30 or initial["manager"] is False and initial["manager_mode"] == 3), "The fresh helper must not inherit grants/activity/special access")
    if require_reporter:
        reporter = receipt.get("reporter_policy")
        require(isinstance(reporter, dict) and reporter.get("package") == REPORTER and reporter.get("compiled_manifest_inspected") is True and
                reporter.get("native_storage_permissions_absent") is True and reporter.get("document_requires_android_grant") is True and
                reporter.get("certificate_sha256") == reporter.get("private_key_certificate_sha256") == policy["certificate_sha256"] and
                isinstance(reporter.get("manifest_sha256"), str) and re.fullmatch(r"[a-f0-9]{64}", reporter["manifest_sha256"]) and
                reporter.get("apk_signer_revision") == SIGNER_REVISION and
                isinstance(reporter.get("source_apk_sha256"), str) and re.fullmatch(r"[a-f0-9]{64}", reporter["source_apk_sha256"]) and
                type(reporter.get("signature_verification_min_sdk_version")) is int and reporter["signature_verification_min_sdk_version"] == row.api and
                type(reporter.get("signature_verification_max_sdk_version")) is int and reporter["signature_verification_max_sdk_version"] == row.api,
                "The actual reporter manifest/APK/signer must pass before native hook dispatch")


class OwnedStorageProbe(OwnedShareRecipient):
    PACKAGE, FIXTURE, OUTPUT = PACKAGE, FIXTURE, "storage-probe"

    def __init__(self, *args, profile: str, **kwargs):
        self.row = storage.row_for(profile)
        super().__init__(*args, **kwargs)
        self.receipt.update(profile=profile, verification_api_level=self.row.api, target_sdk=self.row.target,
            flavor=self.row.flavor, case_nonce=uuid.uuid4().hex, prepare_status="not-started", cleanup_status="not-started",
            scope="One exact separate-UID API/flavor storage method only. Native public helper, normal-UID bytes, genuine system SAF, WRITE/app-op readback and ordered resource restoration remain fresh test assertions; no physical/vendor/dialog/process-restoration/consumer/API-ABI/security/release certification.")

    def host(self, command: list[str]) -> subprocess.CompletedProcess:
        result = subprocess.run(command, cwd=self.root, env=self.environment, capture_output=True, timeout=30)
        require(len(result.stdout) + len(result.stderr) <= MAX_HOST_BYTES, "Unbounded APK inspection")
        return result

    def inspectors(self) -> tuple[Path, Path]:
        analyzer = self.home / "cmdline-tools/23.0/bin/apkanalyzer"
        signer = self.home / ("build-tools/" + SIGNER_REVISION + "/apksigner")
        require(all(path.is_file() and os.access(path, os.X_OK) for path in (analyzer, signer)), "The exact official APK inspection recipe is unavailable")
        return analyzer, signer

    def inspect_apk(self, apk: Path, *, reporter: bool = False) -> dict:
        analyzer, signer = self.inspectors()
        manifest = self.host([str(analyzer), "manifest", "print", str(apk)])
        require(manifest.returncode == 0 and not manifest.stderr.strip(), "Actual compiled manifest unavailable")
        support_refusal = {}
        try:
            policy = validate_reporter_manifest(manifest.stdout) if reporter else validate_manifest(
                manifest.stdout, compiled=True, profile=self.row.profile, support_refusal=support_refusal)
        except ValueError:
            if support_refusal:
                try:
                    self.receipt["compiled_support_refusal"] = support_refusal
                except (Exception, KeyboardInterrupt):
                    pass  # Persisting diagnostic facts must not mask the refusal.
            raise
        api = str(self.row.api)
        certificate = signer_certificate(self.host([str(signer), "verify", "--verbose", "--print-certs",
            "--min-sdk-version", api, "--max-sdk-version", api, str(apk)]))
        key = Path(self.environment["ANDROID_USER_HOME"]) / "debug.keystore"
        checked = lt.safe_path(self.root, key.relative_to(self.root).as_posix()); before = checked.stat()
        require(checked.is_file() and before.st_nlink == 1 and 0 < before.st_size <= 65536, "Exact private controller key unavailable")
        exported = self.host(["keytool", "-exportcert", "-keystore", str(checked), "-alias", "androiddebugkey", "-storepass", "android"])
        require(exported.returncode == 0 and not exported.stderr.strip() and 0 < len(exported.stdout) <= 16384, "Actual private certificate unavailable")
        after = checked.stat()
        require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_nlink) ==
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_nlink), "Private key changed during certificate readback")
        expected = hashlib.sha256(exported.stdout).hexdigest()
        require(certificate == expected, "Actual APK signer differs from the exact controller key")
        return policy | {"package": REPORTER if reporter else PACKAGE, "certificate_sha256": certificate,
            "private_key_certificate_sha256": expected, "apk_signer_revision": SIGNER_REVISION,
            "signature_verification_min_sdk_version": self.row.api, "signature_verification_max_sdk_version": self.row.api,
            "raw_manifest_certificate_key_or_paths_uploaded": False}

    def native_status(self, operation: str) -> dict:
        require(operation in {"status", "cleanup"}, "Only finite native status/cleanup control")
        request_nonce = uuid.uuid4().hex
        result = self.control("shell", "content", "call", "--uri", "content://" + AUTHORITY,
                              "--method", operation, "--arg", self.receipt["case_nonce"], "--user", "0",
                              "--extra", "s:request_nonce:" + request_nonce, timeout=30)
        require(result.returncode == 0 and not result.stderr.strip(), "Native control call unavailable")
        # The human content-call output is NEVER a success witness. Read the
        # helper-UID AtomicFile JSON bound to this operation, nonce and APK.
        filename = "files/storage-control-" + self.receipt["case_nonce"] + ".json"
        read = self.control("shell", "run-as", PACKAGE, "cat", filename, timeout=30)
        require(read.returncode == 0 and not read.stderr.strip() and 0 < len(read.stdout) <= 65536, "Native atomic control receipt unavailable")
        status = json.loads(read.stdout, object_pairs_hook=unique,
                            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite native status")))
        validate_native_status(status, self.receipt, operation=operation, request_nonce=request_nonce)
        return status

    def installed_uid(self) -> int:
        result = self.control("shell", "pm", "list", "packages", "--user", "0", "-U", PACKAGE)
        require(result.returncode == 0 and not result.stderr.strip(), "Native installed UID unavailable")
        match = re.fullmatch(re.escape("package:" + PACKAGE + " uid:") + r"([0-9]{5,7})(?:\r?\n)?", result.stdout.decode("utf-8"))
        require(match is not None and int(match.group(1)) >= 10000, "Expected one actual user0 normal installed helper UID")
        return int(match.group(1))

    def prepare(self) -> dict:
        self.receipt["prepare_status"] = "running"
        try:
            self.receipt["source_contract"] = source_contract(self.root)
            self.inspectors()
            require(self.readback() is None, "Prior/foreign helper exists; no overwrite")
            command = ["./gradlew", "--no-daemon", "--no-configuration-cache", "--max-workers=2", "--console=plain",
                "--no-parallel", "-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8", "-Pkotlin.compiler.execution.strategy=in-process",
                "-p", FIXTURE, "assemble" + self.row.flavor[0].upper() + self.row.flavor[1:] + "Debug"]
            execution = lt.execute(self.root, command, self.output / "source-apk-build.log", 900, 8192, env=self.environment)
            self.receipt.update(assembly_command=command, assembly=execution)
            require(execution["exit_code"] == 0 and not execution.get("stop_reason"), "Selected helper did not assemble")
            apk = metadata_apk(self.root, self.row.profile); self.digest = lt.sha256(apk)
            self.receipt.update(source_apk_sha256=self.digest, source_apk_bytes=apk.stat().st_size)
            self.receipt["apk_policy"] = self.inspect_apk(apk)  # Before install, never inherited post-install admission.
            require(lt.sha256(apk) == self.digest and source_contract(self.root) == self.receipt["source_contract"], "Helper source/APK changed before install")
            require(self.readback() is None, "An intervening helper package exists; refuse replacement")
            self.install_attempted = True
            install = self.control("install", "-t", str(apk), timeout=120)  # Deliberately no -g or -r.
            actual = self.readback()
            installed = actual is not None and actual["apk_sha256"] == self.digest
            self.receipt.update(install_exit_code=install.returncode, automatic_runtime_permission_grant=False,
                installed_readback=actual, recipient_installed=installed, native_results_still_required=True)
            require(install.returncode == 0 and not install.stderr.strip() and install.stdout.strip() in {b"Success", b"Performing Streamed Install\nSuccess"} and installed,
                    "Helper install/byte identity failed; no blind retry")
            self.receipt["installed_uid"] = self.installed_uid()
            self.receipt["initial_native_status"] = self.native_status("status")
            self.receipt["prepare_status"] = "passed"
            validate_prepared_receipt(self.receipt, require_reporter=False)
            return self.receipt
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt) as error:
            self.receipt.update(prepare_status="failed", prepare_error=type(error).__name__)
            raise
        finally:
            lt.write_json(self.output / "receipt.json", self.receipt)

    def prepare_reporter(self) -> dict:
        try:
            validate_prepared_receipt(self.receipt, require_reporter=False)
            apk = metadata_apk(self.root, self.row.profile, reporter=True); digest = lt.sha256(apk)
            self.receipt["reporter_policy"] = self.inspect_apk(apk, reporter=True) | {
                "source_apk_sha256": digest, "source_apk_bytes": apk.stat().st_size}
            require(lt.sha256(apk) == digest and source_contract(self.root) == self.receipt["source_contract"] and
                    lt.sha256(metadata_apk(self.root, self.row.profile)) == self.digest and
                    self.readback() == self.receipt["installed_readback"] and self.installed_uid() == self.receipt["installed_uid"],
                    "Reporter/helper source/APK/UID changed before dispatch")
            validate_prepared_receipt(self.receipt)
            return self.receipt
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt) as error:
            self.receipt.update(reporter_prepare_error=type(error).__name__)
            raise
        finally:
            lt.write_json(self.output / "receipt.json", self.receipt)

    def close(self) -> dict:
        self.receipt["cleanup_status"] = "running"
        try:
            if not self.install_attempted:
                self.receipt.update(foreign_or_preexisting_recipient_mutated=False, owned_recipient_removed=True)
            else:
                actual = self.readback()
                if actual is None:
                    require(self.receipt.get("recipient_installed") is not True, "Installed helper vanished before ordered native cleanup proof")
                    self.receipt["owned_recipient_removed"] = True
                else:
                    require(actual["apk_sha256"] == self.digest, "Helper bytes changed; no foreign cleanup")
                    # Reconcile a partial install using the already inspected
                    # APK/native normal UID, never laundering prepare_status.
                    current_uid = self.installed_uid()
                    require(self.receipt.get("installed_uid") in {None, current_uid}, "Helper UID changed; refuse native cleanup mutation")
                    self.receipt.setdefault("installed_uid", current_uid)
                    self.receipt["owned_identity_reverified"] = True
                    released = self.native_status("cleanup")
                    self.receipt["ordered_saf_activity_cleanup"] = released
                    if released["write_granted"]:
                        require(self.row.declares_write, "Unexpected modern WRITE grant; refuse arbitrary permission mutation")
                        revoke = self.control("shell", "pm", "revoke", "--user", "0", PACKAGE, WRITE)
                        require(revoke.returncode == 0 and not revoke.stdout.strip() and not revoke.stderr.strip(), "Owned WRITE restoration unavailable")
                    if self.row.declares_all_files:
                        reset = self.control("shell", "cmd", "appops", "set", "--uid", PACKAGE, "MANAGE_EXTERNAL_STORAGE", "default")
                        require(reset.returncode == 0 and not reset.stdout.strip() and not reset.stderr.strip(), "Owned all-files default restoration unavailable")
                    restored = self.native_status("status")
                    require(restored["write_granted"] is False and restored["record_present"] is False and
                            restored["activity_active"] is False and restored["persisted_read_count"] == 0 and restored["native_read_grant"] is False and
                            (self.row.api < 30 or restored["manager"] is False and restored["manager_mode"] == 3),
                            "Native grant/app-op/Activity restoration unverified")
                    self.receipt["final_native_restoration"] = restored
                    stop = self.control("shell", "am", "force-stop", PACKAGE, timeout=30)
                    require(stop.returncode == 0 and not stop.stdout.strip() and not stop.stderr.strip(), "Owned helper shutdown unavailable")
                    remove = self.control("uninstall", PACKAGE, timeout=90)
                    absent = self.readback() is None
                    self.receipt.update(stop_exit_code=stop.returncode, uninstall_exit_code=remove.returncode, owned_recipient_removed=absent)
                    require(remove.returncode == 0 and not remove.stderr.strip() and remove.stdout.strip() == b"Success" and absent,
                            "Owned helper uninstall/readback unverified")
            self.receipt["cleanup_status"] = "passed"
            return self.receipt
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt) as error:
            self.receipt.update(cleanup_status="failed", cleanup_error=type(error).__name__, owned_recipient_removed=False)
            raise
        finally:
            lt.write_json(self.output / "receipt.json", self.receipt)
