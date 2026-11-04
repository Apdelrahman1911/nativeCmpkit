"""Finite API35 permission source/manifest contract. Not native verification.

Three independently owned single-method requests; no default/full/demo replay.
Nothing in this module launches a planner, process, compiler, device or network.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat
import xml.etree.ElementTree as ET

API = 35
TARGET = 37
MODULE = "calf-permissions/core"
PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.permissionlifecycle"
REPORTER = "com.mohamedrejeb.calf.calfpermissions.calfpermissionscore.test"
FIXTURE = "tests/consumer/android-permission-lifecycle"
PERMISSION = PACKAGE + ".CONTROL_LIFECYCLE"
CLASS = "com.mohamedrejeb.calf.permissions.AndroidPermissionLifecycleDeviceTest"
KOTLIN = MODULE + "/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/permissions/"
SOURCE = KOTLIN + "AndroidPermissionLifecycleDeviceTest.kt"
APPLICATION_KOTLIN = FIXTURE + "/src/main/kotlin/" + PACKAGE.replace(".", "/") + "/"
METHODS = (
    "api35ApproximateFineRequestAndForegroundBackgroundBatchUseRealDialogs",
    "settingsGrantRepeatedResumeAndDisposedBatchKeepTheSameNativeProcess",
    "notificationSettingsRevocationRefreshesSingleAndBatchWithoutProcessDeath",
)
SPECS = {
    "android-permission-location-api35": {
        "classname": CLASS, "source": SOURCE, "declared_methods": METHODS, "methods": (METHODS[0],),
        "scope": "NEW API35 only: real fine/coarse approximate dialog, coarse already-granted request, real precise upgrade and foreground/background batch with RequiresForeground/SettingsOnly. Older SDK/target, fresh coarse-only dialog, background Settings grant, omitted manifest and disabled services remain unverified.",
    },
    "android-permission-lifecycle-grant-api35": {
        "classname": CLASS, "source": SOURCE, "declared_methods": METHODS, "methods": (METHODS[1],),
        "scope": "NEW API35 only: real camera Settings grant, same PID/Binder/service/Activity, repeated actual resume, single/batch refresh and disposed observer retention during real notification Settings grant. No one-time expiry, process recreation, pending-dialog cancellation, physical/iOS or release inference.",
    },
    "android-permission-lifecycle-revoke-api35": {
        "classname": CLASS, "source": SOURCE, "declared_methods": METHODS, "methods": (METHODS[2],),
        "scope": "NEW API35 only: real notification request then Settings revoke and native/public single/batch denied read on the SAME process/Activity. System-induced death is a failure, never restart/AppOps/rebind success. Camera/location revocation, one-time expiry and broader SDK/platform matrices remain unverified.",
    },
}
FOCUSES = frozenset(SPECS)
RUNTIME_PERMISSIONS = {"android.permission." + name for name in (
    "ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION", "ACCESS_BACKGROUND_LOCATION", "CAMERA", "POST_NOTIFICATIONS")}
ANDROID = "{http://schemas.android.com/apk/res/android}"
STARTUP_INITIALIZERS = {"androidx.emoji2.text.EmojiCompatInitializer", "androidx.lifecycle.ProcessLifecycleInitializer",
                        "androidx.profileinstaller.ProfileInstallerInitializer"}
PROFILE_ACTIONS = {"androidx.profileinstaller.action." + x for x in
                   ("INSTALL_PROFILE", "SKIP_FILE", "SAVE_PROFILE", "BENCHMARK_OPERATION")}
SOURCE_FILES = tuple(sorted((
    ".github/workflows/gradle.yml",
    *("scripts/ci/" + name + ".py" for name in ("library_tests", "android_device_tests", "workflow_matrix",
        "android_storage_probe", "android_permission_lifecycle", "android_permission_lifecycle_contract",
        "android_share_recipient", "android_geo_probe", "android_io_documents", "android_permission_demo")),
    "gradle/libs.versions.toml", MODULE + "/build.gradle.kts", MODULE + "/src/androidDeviceTest/AndroidManifest.xml",
    *(FIXTURE + "/" + p for p in ("settings.gradle.kts", "build.gradle.kts", "gradle.properties", "src/main/AndroidManifest.xml")),
    *(APPLICATION_KOTLIN + name + ".kt" for name in ("PermissionLifecycleActivity", "PermissionLifecycleService")),
    *(KOTLIN + name + ".kt" for name in ("AndroidPermissionLifecycleDeviceTest", "OwnedPermissionLifecycle", "PermissionLifecycleSystemUi")),
    *(MODULE + "/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/" + name + ".kt" for name in
      ("AndroidPermissionRegistry", "AndroidPermissionRequestPlan", "MutablePermissionState.android", "MutableMultiplePermissionsState.android", "PermissionsUtil.android")),
    *(MODULE + "/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/" + name + ".kt" for name in
      ("PermissionState", "MultiplePermissionsState", "PermissionDetails", "PermissionRequestGate",
       "MutablePermissionState", "MutableMultiplePermissionsState")),
    *("calf-permissions/" + module + "/src/" + source_set + "/kotlin/" + package_path + "/permissions/" + file
      for module, file in (("location", "LocationPermissions"), ("background-location", "BackgroundLocationPermissions"),
                           ("camera", "CameraPermissions"), ("notifications", "NotificationPermissions"))
      for source_set, package_path, file in (("commonMain", "com.mohamedrejeb.calf", file + ".kt"),
                                           ("androidMain", "com/mohamedrejeb/calf", file + ".android.kt"))),
)))


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def validate_request(api_level: int, modules: tuple[str, ...], focus: str) -> None:
    require(type(api_level) is int and api_level == API and type(modules) is tuple and modules == (MODULE,) and
            isinstance(focus, str) and focus in FOCUSES, "Exact integer API35/one permission core/finite focus required")


def validate_metadata(payload: bytes) -> str:
    """One inert metadata record for this NEW package; never expands the old whitelist."""
    require(isinstance(payload, bytes) and 0 < len(payload) <= 65536, "Bounded actual APK metadata required")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate actual metadata identity")
            result[key] = value
        return result
    def nonfinite(_):
        raise ValueError("Nonfinite APK metadata")
    data = json.loads(payload, object_pairs_hook=unique, parse_constant=nonfinite)
    require(isinstance(data, dict) and isinstance(data.get("artifactType"), dict) and
            data["artifactType"].get("type") == "APK" and data.get("applicationId") == PACKAGE and
            data.get("variantName") == "debug", "Exact own debug APK metadata required")
    rows = data.get("elements")
    require(isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict), "Exactly one APK metadata element required")
    row = rows[0]
    name = row.get("outputFile")
    require(row.get("type") == "SINGLE" and row.get("filters") == [] and isinstance(name, str) and
            re.fullmatch(r"[A-Za-z0-9_.-]+\.apk", name) and ".." not in name, "Unsplit own APK basename required")
    return name


class EntityFreeManifestBuilder(ET.TreeBuilder):
    """Reject actual parsed DTDs, including encodings invisible to UTF8 byte guards."""
    def doctype(self, _name, _public_id, _system_id):
        raise ValueError("Manifest DTD/entity declarations are forbidden")


def validate_reporter_source(payload: bytes) -> None:
    require(isinstance(payload, bytes) and 0 < len(payload) <= 65536 and
            b"<!DOCTYPE" not in payload and b"<!ENTITY" not in payload, "Bounded entity-free reporter source required")
    try:
        root = ET.fromstring(payload, parser=ET.XMLParser(target=EntityFreeManifestBuilder()))
    except ET.ParseError:
        raise ValueError("Malformed bounded reporter manifest XML") from None
    names = [node.get(ANDROID + "name") for node in root.findall("uses-permission")]
    controls = {PERMISSION, "io.github.apdelrahman1911.nativecmpkit.verification.permissiondemo.BIND_DEMO",
                "io.github.apdelrahman1911.nativecmpkit.verification.storageprobe.CONTROL_STORAGE"}
    require(root.tag == "manifest" and root.get(ANDROID + "sharedUserId") is None and
            root.get(ANDROID + "sharedUserMaxSdkVersion") is None and len(names) == len(set(names)) and set(names) == controls and
            all(set(n.attrib) == {ANDROID + "name"} and not list(n) for n in root.findall("uses-permission")) and
            not root.findall("uses-permission-sdk-23"), "Reporter cannot acquire runtime or arbitrary signature permissions")
    queries = root.findall("queries")
    require(len(queries) == 1, "One reporter visibility declaration required")
    packages = [node.get(ANDROID + "name") for node in queries[0].findall("package")]
    require(len(packages) == len(set(packages)) and {PACKAGE, "com.android.settings"} <= set(packages),
            "Actual helper and Settings visibility required")


def test_filter(focus: str) -> str:
    require(isinstance(focus, str) and focus in FOCUSES, "Unknown or unfocused permission lifecycle request")
    return CLASS + "#" + SPECS[focus]["methods"][0]


def validate_manifest(payload: bytes, *, compiled: bool) -> dict:
    require(isinstance(payload, bytes) and 0 < len(payload) <= 65536 and
            b"<!DOCTYPE" not in payload and b"<!ENTITY" not in payload, "Bounded entity-free manifest required")
    try:
        root = ET.fromstring(payload, parser=ET.XMLParser(target=EntityFreeManifestBuilder()))
    except ET.ParseError:
        raise ValueError("Malformed bounded helper manifest XML") from None
    require(root.tag == "manifest" and root.get("package") in ({PACKAGE} if compiled else {None, PACKAGE}) and
            root.get(ANDROID + "sharedUserId") is None and root.get(ANDROID + "sharedUserMaxSdkVersion") is None,
            "Exact separate-UID fixture required")
    requested = root.findall("uses-permission")
    names = [node.get(ANDROID + "name") for node in requested]
    dynamic = PACKAGE + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
    allowed = RUNTIME_PERMISSIONS | ({dynamic} if compiled else set())
    require(len(names) == len(set(names)) and RUNTIME_PERMISSIONS <= set(names) <= allowed and
            all(set(node.attrib) == {ANDROID + "name"} and not list(node) for node in requested) and
            not root.findall("uses-permission-sdk-23"), "Only five exact permissions; no capped or broad grants")
    definitions = root.findall("permission")
    levels = {"signature", "2", "0x2", "0x00000002"} if compiled else {"signature"}
    defined = [node.get(ANDROID + "name") for node in definitions]
    require(len(defined) == len(set(defined)) and PERMISSION in defined and
            set(defined) <= ({PERMISSION, dynamic} if compiled else {PERMISSION}) and
            all(node.get(ANDROID + "protectionLevel") in levels and not list(node) and
                set(node.attrib) == {ANDROID + "name", ANDROID + "protectionLevel"} for node in definitions),
            "Only signature-protected test control")
    queries = root.findall("queries")
    require(len(queries) == 1 and not queries[0].attrib and len(queries[0]) == 1 and
            queries[0][0].tag == "package" and queries[0][0].get(ANDROID + "name") == REPORTER and
            set(queries[0][0].attrib) == {ANDROID + "name"} and not list(queries[0][0]), "Only exact reporter visibility")
    apps = root.findall("application")
    require(len(apps) == 1, "One test-only application required")
    app = apps[0]
    require(app.get(ANDROID + "allowBackup") == "false" and app.get(ANDROID + "label") == "NativeCmpKit permission lifecycle verification" and
            app.get(ANDROID + "permission") is None and
            app.get(ANDROID + "process") is None and app.get(ANDROID + "enabled") in {None, "true"},
            "No app-wide UID/process/control or backup override")
    def full_name(node):
        name = node.get(ANDROID + "name", "")
        return PACKAGE + name if name.startswith(".") else name
    for tag, suffix in (("activity", "PermissionLifecycleActivity"), ("service", "PermissionLifecycleService")):
        nodes = app.findall(tag)
        require(len(nodes) == 1 and full_name(nodes[0]) == PACKAGE + "." + suffix and
                nodes[0].get(ANDROID + "permission") == PERMISSION and nodes[0].get(ANDROID + "exported") == "true" and
                nodes[0].get(ANDROID + "process") is None and nodes[0].get(ANDROID + "enabled") in {None, "true"} and not list(nodes[0]),
                "Only finite signature-protected Activity/service may expose control")
    for node in app:
        if node.tag in {"activity", "service"}:
            continue
        require(compiled, "No extra source application component")
        if node.tag == "provider":
            require(full_name(node) == "androidx.startup.InitializationProvider" and
                    node.get(ANDROID + "authorities") == PACKAGE + ".androidx-startup" and
                    node.get(ANDROID + "exported") == "false" and
                    set(node.attrib) == {ANDROID + k for k in ("name", "authorities", "exported")}, "Unexpected compiled provider")
            names = [child.get(ANDROID + "name") for child in node]
            require(len(names) == len(set(names)) and set(names) <= STARTUP_INITIALIZERS and
                    all(child.tag == "meta-data" and not list(child) and child.get(ANDROID + "value") == "androidx.startup" and
                        set(child.attrib) == {ANDROID + "name", ANDROID + "value"} for child in node), "Unexpected startup metadata")
        elif node.tag == "uses-library":
            require(node.get(ANDROID + "name") in {"androidx.window.extensions", "androidx.window.sidecar"} and
                    node.get(ANDROID + "required") == "false" and not list(node) and
                    set(node.attrib) == {ANDROID + "name", ANDROID + "required"}, "Unexpected optional native library")
        elif node.tag == "receiver":
            require(full_name(node) == "androidx.profileinstaller.ProfileInstallReceiver" and
                    node.get(ANDROID + "permission") == "android.permission.DUMP" and node.get(ANDROID + "exported") == "true" and
                    set(node.attrib) <= {ANDROID + k for k in ("name", "permission", "exported", "enabled", "directBootAware")} and
                    node.get(ANDROID + "enabled") in {None, "true"} and node.get(ANDROID + "directBootAware") in {None, "false"},
                    "Unexpected compiled receiver")
            actions = []
            for child in node:
                require(child.tag == "intent-filter" and not child.attrib and len(child) == 1 and child[0].tag == "action" and
                        not list(child[0]) and set(child[0].attrib) == {ANDROID + "name"}, "Unexpected receiver control subtree")
                actions.append(child[0].get(ANDROID + "name"))
            require(len(actions) == len(set(actions)) and set(actions) == PROFILE_ACTIONS, "Unexpected receiver actions")
        else:
            raise ValueError("Unexpected compiled application declaration")
    require(len(app.findall("provider")) <= 1 and len(app.findall("receiver")) <= 1 and
            len({n.get(ANDROID + "name") for n in app.findall("uses-library")}) == len(app.findall("uses-library")),
            "No duplicate AndroidX components")
    sdk = root.findall("uses-sdk")
    require((len(sdk) == 1 and sdk[0].get(ANDROID + "minSdkVersion") == str(API) and
             sdk[0].get(ANDROID + "targetSdkVersion") == str(TARGET) and sdk[0].get(ANDROID + "maxSdkVersion") is None and
             app.get(ANDROID + "debuggable") == "true") if compiled else not sdk, "Exact API35/target37 debug fixture")
    require(all(n.tag in {"uses-permission", "permission", "queries", "application", "uses-sdk"} for n in root),
            "Unexpected root manifest declaration")
    return {"compiled_manifest_inspected": compiled, "signature_control_only": True, "separate_uid_manifest": True,
            "five_runtime_permissions_only": True, "manifest_sha256": hashlib.sha256(payload).hexdigest()}


def source_contract(root: Path) -> dict:
    inputs, texts = {}, {}
    root = root.resolve(strict=True)
    for relative in SOURCE_FILES:
        path = root / relative
        before = path.lstat()
        require(path.resolve(strict=True).is_relative_to(root) and stat.S_ISREG(before.st_mode) and
                before.st_nlink == 1 and 0 < before.st_size <= 1024**2, "Missing/linked/nonregular/unbounded source")
        payload = path.read_bytes()
        after = path.lstat()
        require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_mode, before.st_nlink) ==
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_mode, after.st_nlink), "Source changed during readback")
        inputs[relative] = hashlib.sha256(payload).hexdigest()
        texts[relative] = payload.decode("utf-8")
    validate_manifest(texts[FIXTURE + "/src/main/AndroidManifest.xml"].encode(), compiled=False)
    validate_reporter_source(texts[MODULE + "/src/androidDeviceTest/AndroidManifest.xml"].encode())
    expected_fixture_sources = {FIXTURE + "/src/main/AndroidManifest.xml",
        APPLICATION_KOTLIN + "PermissionLifecycleActivity.kt", APPLICATION_KOTLIN + "PermissionLifecycleService.kt"}
    actual_fixture_sources = set()
    for path in (root / FIXTURE / "src").rglob("*"):
        require(not path.is_symlink(), "No linked source fixture inventory")
        if path.is_file():
            actual_fixture_sources.add(path.relative_to(root).as_posix())
        require(len(actual_fixture_sources) <= len(expected_fixture_sources), "Unexpected source fixture input")
    require(actual_fixture_sources == expected_fixture_sources, "Exact three helper source inputs required")
    new_kotlin = "\n".join(texts[p] for p in SOURCE_FILES if p.startswith((KOTLIN, APPLICATION_KOTLIN)))
    require(not re.search(r"\b(?:grantRuntimePermission|revokeRuntimePermission|grantUriPermission|dispatchResult|onNativeResult|adoptShellPermissionIdentity|execShellCommand|handleLifecycleEvent)\s*\(", new_kotlin) and
            not re.search(r"\.status\s*=", new_kotlin) and "Runtime.getRuntime" not in new_kotlin and "LocalInspectionMode" not in new_kotlin,
            "No grants, callback/status/lifecycle injection, shell/AppOps or inspection-mode substitute")
    tests = texts[SOURCE]
    require(set(re.findall(r"@Test\s+fun\s+(\w+)\s*\(", tests)) == set(METHODS) and
            "@SdkSuppress(minSdkVersion = 35, maxSdkVersion = 35)" in tests, "Exact three API35 native declarations required")
    activity = texts[APPLICATION_KOTLIN + "PermissionLifecycleActivity.kt"]
    require(all("rememberPermissionState(Permission." + name + ")" in activity for name in
                ("FineLocation", "CoarseLocation", "BackgroundLocation", "Camera", "Notification")) and
            "rememberMultiplePermissionsState(" in activity and "super.onRequestPermissionsResult(requestCode, permissions, grantResults)" in activity,
            "Public composition and genuine platform callbacks must remain")
    # A source digest binds bytes, never certifies the native assertions or compilation.
    digest = hashlib.sha256("".join(p + "\0" + inputs[p] + "\n" for p in sorted(inputs)).encode()).hexdigest()
    return {"schema_version": 1, "source_inputs": inputs, "source_inputs_sha256": digest,
            "source_policy_verified": True, "verification_api_level": API, "native_or_compile_success_inferred": False}


def validate_source_receipt(receipt: dict) -> None:
    require(isinstance(receipt, dict) and set(receipt) == {"schema_version", "source_inputs", "source_inputs_sha256",
            "source_policy_verified", "verification_api_level", "native_or_compile_success_inferred"} and
            type(receipt.get("schema_version")) is int and receipt["schema_version"] == 1 and
            type(receipt.get("verification_api_level")) is int and receipt["verification_api_level"] == API and
            receipt.get("source_policy_verified") is True and receipt.get("native_or_compile_success_inferred") is False,
            "Exact source-only receipt schema required")
    inputs = receipt.get("source_inputs")
    require(isinstance(inputs, dict) and set(inputs) == set(SOURCE_FILES) and
            all(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) for value in inputs.values()),
            "Complete finite source identities required")
    digest = hashlib.sha256("".join(p + "\0" + inputs[p] + "\n" for p in sorted(inputs)).encode()).hexdigest()
    require(receipt.get("source_inputs_sha256") == digest, "Source receipt digest differs")


def validate_plan(test_plan: dict) -> None:
    focus = test_plan.get("explicit_test_focus")
    helper = test_plan.get("android_permission_lifecycle")
    if focus not in FOCUSES:
        require(helper is None, "No lifecycle fixture contract on default/unrelated/accepted selections")
        return
    require(test_plan.get("suite") == "android-device" and test_plan.get("explicit_module_subset") == [MODULE] and
            test_plan.get("complete_suite_requested") is False and isinstance(helper, dict) and
            set(helper) == {"package", "source_fixture", "verification_api_level", "source_contract"} and
            helper.get("package") == PACKAGE and helper.get("source_fixture") == FIXTURE and
            type(helper.get("verification_api_level")) is int and helper["verification_api_level"] == API,
            "Exact API35 single-module source plan required")
    validate_source_receipt(helper["source_contract"])


def validate_prepared_receipt(receipt: dict, expected_source: dict, api_level: int = API, *, focus: str) -> None:
    validate_source_receipt(expected_source)
    validate_request(api_level, (MODULE,), focus)
    require(isinstance(receipt, dict) and receipt.get("focus") == focus and
            receipt.get("verification_api_level") == API and type(receipt.get("verification_api_level")) is int and
            receipt.get("package") == PACKAGE and receipt.get("source_fixture") == FIXTURE and
            receipt.get("prepare_status") == "passed" and receipt.get("recipient_installed") is True and
            receipt.get("automatic_runtime_permission_grant") is False and receipt.get("source_contract") == expected_source and
            type(receipt.get("source_apk_bytes")) is int and 0 < receipt["source_apk_bytes"] < 256 * 1024**2,
            "Exact prepared API35 source fixture required before compiler/native dispatch")
    policy, installed = receipt.get("apk_policy"), receipt.get("installed_readback")
    digest = receipt.get("source_apk_sha256")
    require(isinstance(policy, dict) and isinstance(installed, dict) and isinstance(digest, str) and
            re.fullmatch(r"[a-f0-9]{64}", digest) and installed.get("apk_sha256") == digest and
            installed.get("exact_one_APK_path_observed") is True and policy.get("compiled_manifest_inspected") is True and
            policy.get("signature_control_only") is True and policy.get("separate_uid_manifest") is True and
            policy.get("five_runtime_permissions_only") is True, "Actual manifest and installed APK byte boundary required")
    cert = policy.get("certificate_sha256")
    require(isinstance(cert, str) and re.fullmatch(r"[a-f0-9]{64}", cert) and
            cert == policy.get("private_key_certificate_sha256") and
            type(policy.get("signature_verification_min_sdk_version")) is int and
            type(policy.get("signature_verification_max_sdk_version")) is int and
            policy["signature_verification_min_sdk_version"] == policy["signature_verification_max_sdk_version"] == API,
            "Actual private certificate and exact API35 signature verification required")
