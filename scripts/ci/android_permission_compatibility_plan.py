"""Finite source-only Android permission compatibility proposal.

No controller, compiler, native process, grant, install or release runs here. A
plan or inert manifest policy is never a prepared/native acceptance receipt.
"""
from __future__ import annotations

from dataclasses import dataclass
import xml.etree.ElementTree as ET

MODULES = ("calf-permissions/core", "calf-permissions/location", "calf-permissions/background-location", "calf-permissions/camera")
FIXTURE = "tests/consumer/android-permission-compatibility"
PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.permissioncompat"
REPORTER = PACKAGE + ".reporter"
CLASS = "com.mohamedrejeb.calf.permissions.AndroidPermissionCompatibilityDeviceTest"
NAMESPACE = "{http://schemas.android.com/apk/res/android}"
MIN_SDK = 23
CURRENT_TARGET = 37
SYSTEM_UI_PACKAGES = frozenset(("com.android.settings", "com.android.permissioncontroller", "com.google.android.permissioncontroller",
                                "com.android.packageinstaller", "com.google.android.packageinstaller"))
STARTUP_INITIALIZERS = frozenset(("androidx.emoji2.text.EmojiCompatInitializer", "androidx.lifecycle.ProcessLifecycleInitializer",
                                  "androidx.profileinstaller.ProfileInstallerInitializer"))
PROFILE_ACTIONS = frozenset("androidx.profileinstaller.action." + name for name in
                            ("INSTALL_PROFILE", "SKIP_FILE", "SAVE_PROFILE", "BENCHMARK_OPERATION"))
FINE = "android.permission.ACCESS_FINE_LOCATION"
COARSE = "android.permission.ACCESS_COARSE_LOCATION"
BACKGROUND = "android.permission.ACCESS_BACKGROUND_LOCATION"
CAMERA = "android.permission.CAMERA"
ROLE_PERMISSIONS = {
    "fine": frozenset((FINE, COARSE)),  # Logical fine alone must include native coarse on API31+.
    "coarse": frozenset((COARSE,)),
    "pair": frozenset((FINE, COARSE)),
    "batch": frozenset((FINE, COARSE, BACKGROUND)),
    "omitted": frozenset(),
    "camera": frozenset((CAMERA,)),
}
MATRIX_METHOD = "freshFineCoarsePairAndBackgroundUseRealApiTargetDialogs"
SERVICES_METHOD = "manifestOmissionAndServicesOffKeepDifferentNativeAndPermissionSemantics"
CAMERA_METHOD = "cameraSettingsRevocationRefreshesSingleBatchAtSameIdentity"
LOCATION_METHOD = "locationSettingsRevocationRefreshesSingleBatchAtSameIdentity"
DISPOSAL_METHOD = "pendingNativeCameraDialogDisposalSuppressesRealLateResult"


@dataclass(frozen=True)
class CompatibilityRow:
    profile: str
    api: int
    target: int
    roles: tuple[str, ...]
    method: str


ROWS = tuple(
    CompatibilityRow(f"android-permission-compat-api{api}-target{target}", api, target,
                     ("fine", "coarse", "pair", "batch"), MATRIX_METHOD)
    for api, legacy in ((23, 23), (29, 28), (30, 29), (31, 30), (33, 32))
    for target in (legacy, CURRENT_TARGET)
) + (
    CompatibilityRow("android-permission-manifest-services-api35", 35, 37, ("omitted", "batch"), SERVICES_METHOD),
    CompatibilityRow("android-permission-camera-revoke-api35", 35, 37, ("camera",), CAMERA_METHOD),
    CompatibilityRow("android-permission-location-revoke-api35", 35, 37, ("fine",), LOCATION_METHOD),
    CompatibilityRow("android-permission-pending-disposal-api35", 35, 37, ("camera",), DISPOSAL_METHOD),
)


def row_for(profile: str, *, actual_api: int | None = None, actual_target: int | None = None) -> CompatibilityRow:
    matches = [row for row in ROWS if row.profile == profile]
    if type(profile) is not str or len(matches) != 1:
        raise ValueError("Unknown finite permission compatibility profile")
    row = matches[0]
    for observed, expected in ((actual_api, row.api), (actual_target, row.target)):
        if observed is not None and (type(observed) is not int or observed != expected):
            raise ValueError("Actual API/target does not match the exact compatibility profile")
    return row


def proposed_plan(profile: str) -> dict:
    row = row_for(profile)
    return {
        "schema_version": 1,
        "profile": row.profile, "actual_api_required": row.api,
        "helper_target_required": row.target, "helper_min_sdk_required": MIN_SDK,
        "modules": list(MODULES), "fixture": FIXTURE,
        "reporter_package": REPORTER, "reporter_target": CURRENT_TARGET,
        "helper_roles": list(row.roles),
        "helper_packages": [PACKAGE + "." + role for role in row.roles],
        "helper_tasks": [":helper:assemble" + role.title() + "Debug" for role in row.roles],
        "helper_gradle_property": "nativecmpkitPermissionCompatProfile=" + row.profile,
        "reporter_task": ":reporter:connectedDebugAndroidTest",
        "native_filter": CLASS + "#" + row.method,
        "required_xml": [{"classname": CLASS, "name": row.method, "skipped_allowed": False}],
        "installer_runtime_grants_allowed": False,
        "target_minimum_bypass_allowed": False,
        "fresh_each_helper_uid_and_install_required": True,
        "compiled_manifest_signer_installed_bytes_and_source_required": True,
        "same_process_and_activity_required": True,
        "owned_thread_app_settings_and_guest_cleanup_required": True,
        "accepted_population_replay_allowed": False,
        "prepared_receipt_emitted": False,
        "controller_or_standard_CI_ingress_implemented": False,
        "native_or_compile_success_inferred": False,
    }


class EntityFreeManifestBuilder(ET.TreeBuilder):
    def doctype(self, _name, _public_id, _system_id):
        raise ValueError("Compatibility manifest DTD/entity declarations are forbidden")


def _manifest(payload: bytes) -> ET.Element:
    if not isinstance(payload, bytes) or not 0 < len(payload) <= 65536:
        raise ValueError("Bounded compatibility manifest required")
    try:
        root = ET.fromstring(payload, parser=ET.XMLParser(target=EntityFreeManifestBuilder()))
    except ET.ParseError:
        raise ValueError("Malformed bounded compatibility manifest") from None
    if root.tag != "manifest" or any(NAMESPACE + key in root.attrib for key in ("sharedUserId", "sharedUserMaxSdkVersion")):
        raise ValueError("Separate-UID compatibility manifest required")
    return root


def _auxiliary_components(app: ET.Element, *, package: str, compiled: bool) -> None:
    extras = [node for node in app if node.tag not in {"activity", "service"}]
    if extras and not compiled:
        raise ValueError("No extra source helper application components")
    if len(app.findall("provider")) > 1 or len(app.findall("receiver")) > 1:
        raise ValueError("No duplicate compiled AndroidX components")
    for node in extras:
        if node.tag == "provider":
            if (node.get(NAMESPACE + "name") != "androidx.startup.InitializationProvider" or
                node.get(NAMESPACE + "authorities") != package + ".androidx-startup" or
                node.get(NAMESPACE + "exported") != "false" or
                set(node.attrib) != {NAMESPACE + name for name in ("name", "authorities", "exported")}):
                raise ValueError("Exact nonexported compiled startup provider required")
            names = [child.get(NAMESPACE + "name") for child in node]
            if len(names) != len(set(names)) or not set(names) <= STARTUP_INITIALIZERS or any(
                child.tag != "meta-data" or list(child) or child.get(NAMESPACE + "value") != "androidx.startup" or
                set(child.attrib) != {NAMESPACE + "name", NAMESPACE + "value"} for child in node):
                raise ValueError("Only exact AndroidX startup initializers are permitted")
        elif node.tag == "receiver":
            if (node.get(NAMESPACE + "name") != "androidx.profileinstaller.ProfileInstallReceiver" or
                node.get(NAMESPACE + "permission") != "android.permission.DUMP" or
                node.get(NAMESPACE + "exported") != "true" or
                not set(node.attrib) <= {NAMESPACE + name for name in ("name", "permission", "exported", "enabled", "directBootAware")} or
                node.get(NAMESPACE + "enabled") not in {None, "true"} or node.get(NAMESPACE + "directBootAware") not in {None, "false"}):
                raise ValueError("Only the exact DUMP-protected profile receiver is permitted")
            actions = []
            for child in node:
                if (child.tag != "intent-filter" or child.attrib or len(child) != 1 or child[0].tag != "action" or
                    list(child[0]) or set(child[0].attrib) != {NAMESPACE + "name"}):
                    raise ValueError("Exact profile receiver action shape required")
                actions.append(child[0].get(NAMESPACE + "name"))
            if len(actions) != len(set(actions)) or set(actions) != PROFILE_ACTIONS:
                raise ValueError("Exact profile receiver action set required")
        elif node.tag == "uses-library":
            if (node.get(NAMESPACE + "name") not in {"androidx.window.extensions", "androidx.window.sidecar"} or
                node.get(NAMESPACE + "required") != "false" or list(node) or
                set(node.attrib) != {NAMESPACE + "name", NAMESPACE + "required"}):
                raise ValueError("Only exact optional AndroidX window libraries are permitted")
        else:
            raise ValueError("Unexpected compiled helper application component")
    libraries = [node.get(NAMESPACE + "name") for node in app.findall("uses-library")]
    if len(libraries) != len(set(libraries)):
        raise ValueError("No duplicate optional native libraries")


def validate_helper_manifest(payload: bytes, *, profile: str, role: str, compiled: bool) -> dict:
    """Inert source/inspector policy validation only, not an actual APK inspection."""
    row = row_for(profile)
    if type(role) is not str or role not in row.roles or type(compiled) is not bool:
        raise ValueError("Only the selected profile's exact helper role is allowed")
    root = _manifest(payload)
    package = PACKAGE + "." + role
    if root.get("package") not in ({package} if compiled else {None, package}):
        raise ValueError("Exact compiled helper package required")
    permissions = [node.get(NAMESPACE + "name") for node in root.findall("uses-permission")]
    generated = package + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
    allowed = set(ROLE_PERMISSIONS[role]) | ({generated} if compiled else set())
    requested = root.findall("uses-permission")
    if (len(permissions) != len(set(permissions)) or not set(ROLE_PERMISSIONS[role]) <= set(permissions) <= allowed or
        any(set(node.attrib) != {NAMESPACE + "name"} or list(node) for node in requested)):
        raise ValueError("Exact selected helper runtime declarations required")
    controls = root.findall("permission")
    control = package + ".CONTROL_COMPATIBILITY" if compiled else "${applicationId}.CONTROL_COMPATIBILITY"
    named = [node for node in controls if node.get(NAMESPACE + "name") == control]
    if len(named) != 1 or named[0].get(NAMESPACE + "protectionLevel") not in ("signature", "0x2", "2"):
        raise ValueError("Exact signature control required")
    if (len(controls) != len({node.get(NAMESPACE + "name") for node in controls}) or
        any(node.get(NAMESPACE + "name") not in ({control, generated} if compiled else {control}) or
            node.get(NAMESPACE + "protectionLevel") not in ({"signature", "0x2", "2", "0x00000002"} if compiled else {"signature"}) or
            set(node.attrib) != {NAMESPACE + "name", NAMESPACE + "protectionLevel"} or list(node) for node in controls)):
        raise ValueError("Unexpected helper control declaration")
    app = root.find("application")
    if (len(root.findall("application")) != 1 or app is None or app.get(NAMESPACE + "allowBackup") != "false" or
        app.get(NAMESPACE + "permission") is not None or app.get(NAMESPACE + "process") is not None or
        app.get(NAMESPACE + "enabled") not in {None, "true"}):
        raise ValueError("Nonbacked-up helper application required")
    for kind, name in (("activity", ".PermissionCompatibilityActivity"), ("service", ".PermissionCompatibilityService")):
        nodes = app.findall(kind)
        if (len(nodes) != 1 or nodes[0].get(NAMESPACE + "exported") != "true" or nodes[0].get(NAMESPACE + "permission") != control or
            nodes[0].get(NAMESPACE + "process") is not None or nodes[0].get(NAMESPACE + "enabled") not in {None, "true"} or list(nodes[0])):
            raise ValueError("Exactly one signature-protected helper component per kind required")
        expanded = PACKAGE + name
        if nodes[0].get(NAMESPACE + "name") not in ({expanded} if compiled else {expanded, name}):
            raise ValueError("Exact helper component class required")
    _auxiliary_components(app, package=package, compiled=compiled)
    queries = root.find("queries")
    if (len(root.findall("queries")) != 1 or queries is None or queries.attrib or len(queries) != 1 or
        queries[0].tag != "package" or queries[0].get(NAMESPACE + "name") != REPORTER or
        set(queries[0].attrib) != {NAMESPACE + "name"} or list(queries[0])):
        raise ValueError("Exact reporter visibility required")
    if compiled:
        sdk = root.find("uses-sdk")
        if (len(root.findall("uses-sdk")) != 1 or sdk is None or sdk.get(NAMESPACE + "minSdkVersion") != str(MIN_SDK) or
            sdk.get(NAMESPACE + "targetSdkVersion") != str(row.target) or sdk.get(NAMESPACE + "maxSdkVersion") is not None):
            raise ValueError("Actual compiled min/target SDK must match the finite profile")
        if app.get(NAMESPACE + "debuggable") != "true":
            raise ValueError("Disposable debug helper required")
    elif root.findall("uses-sdk"):
        raise ValueError("Source SDK comes only from the exact finite Gradle profile")
    if any(node.tag not in {"uses-permission", "permission", "application", "queries", "uses-sdk"} for node in root):
        raise ValueError("Unexpected compatibility manifest root declaration")
    return {"source_policy_consistent": True, "role": role, "target": row.target,
            "native_or_compile_success_inferred": False}


def validate_reporter_manifest(payload: bytes, *, compiled: bool) -> dict:
    """Exact target-reporter policy only; a separate test APK is not this domain."""
    if type(compiled) is not bool:
        raise ValueError("Exact reporter manifest domain required")
    root = _manifest(payload)
    if root.get("package") not in ({REPORTER} if compiled else {None, REPORTER}):
        raise ValueError("Exact reporter package required")
    requested = root.findall("uses-permission")
    names = [node.get(NAMESPACE + "name") for node in requested]
    expected = {PACKAGE + "." + role + ".CONTROL_COMPATIBILITY" for role in ROLE_PERMISSIONS}
    if (len(names) != len(expected) or set(names) != expected or
        any(set(node.attrib) != {NAMESPACE + "name"} or list(node) for node in requested)):
        raise ValueError("Reporter can request only six exact uncapped named signature controls")
    applications = root.findall("application")
    if len(applications) != 1:
        raise ValueError("Exactly one reporter application required")
    app = applications[0]
    if (app.get(NAMESPACE + "allowBackup") != "false" or list(app) or
        app.get(NAMESPACE + "process") is not None or app.get(NAMESPACE + "permission") is not None or
        app.get(NAMESPACE + "enabled") not in {None, "true"}):
        raise ValueError("Reporter cannot expose extra application components or change process/control")
    queries = root.find("queries")
    expected_queries = {PACKAGE + "." + role for role in ROLE_PERMISSIONS} | set(SYSTEM_UI_PACKAGES)
    if (len(root.findall("queries")) != 1 or queries is None or queries.attrib or
        len(queries) != len(expected_queries) or
        {node.get(NAMESPACE + "name") for node in queries} != expected_queries or
        any(node.tag != "package" or set(node.attrib) != {NAMESPACE + "name"} or list(node) for node in queries)):
        raise ValueError("Exact helper/system UI reporter visibility required")
    sdks = root.findall("uses-sdk")
    if compiled:
        if (len(sdks) != 1 or sdks[0].get(NAMESPACE + "minSdkVersion") != str(MIN_SDK) or
            sdks[0].get(NAMESPACE + "targetSdkVersion") != str(CURRENT_TARGET) or list(sdks[0]) or
            set(sdks[0].attrib) != {NAMESPACE + "minSdkVersion", NAMESPACE + "targetSdkVersion"}):
            raise ValueError("One exact actual reporter min/target SDK without a cap required")
        if app.get(NAMESPACE + "debuggable") != "true":
            raise ValueError("Disposable debug target reporter required")
    elif sdks:
        raise ValueError("Source reporter SDK comes only from its fixed Gradle configuration")
    if any(node.tag not in {"uses-permission", "application", "queries", "uses-sdk"} for node in root):
        raise ValueError("Unexpected target reporter declaration; test instrumentation has a separate domain")
    return {"source_policy_consistent": True, "native_or_compile_success_inferred": False}


def unavailable_one_time_expiry_plan() -> dict:
    return {
        "profile_registered": False, "native_dispatch_allowed": False,
        "grant_expiry_observed": False, "same_process_expiry_verified": False,
        "blocker": "A reporter binding can keep helper process importance high and prevent natural one-time expiry. A genuine expiry-preserving, death-observing handoff still requires a separate reviewed design and live platform verification.",
        "forbidden_substitutes": ["synthetic clock", "shell/AppOps grant or revoke", "restart", "rebind", "fabricated lifecycle/status/callback"],
        "native_or_compile_success_inferred": False,
    }
