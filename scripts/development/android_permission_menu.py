#!/usr/bin/env python3
"""NAV-015 source/merged-XML correspondence. All status rows are predictions, not native results."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tomllib
import xml.etree.ElementTree as ET

ANDROID = "{http://schemas.android.com/apk/res/android}"
SCREEN = "sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/PermissionsScreen.kt"
MANIFEST = "sample/android/src/main/AndroidManifest.xml"
EXPECTED = (
    ("Camera", "camera", "CameraPermissions"),
    ("Gallery", "gallery", "GalleryPermissions"),
    ("ReadStorage", "core", "StoragePermissions"),
    ("WriteStorage", "core", "StoragePermissions"),
    ("ReadImage", "gallery", "GalleryPermissions"),
    ("ReadVideo", "gallery", "GalleryPermissions"),
    ("ReadAudio", "core", "StoragePermissions"),
    ("FineLocation", "location", "LocationPermissions"),
    ("CoarseLocation", "location", "LocationPermissions"),
    ("BackgroundLocation", "background-location", "BackgroundLocationPermissions"),
    ("Notification", "notifications", "NotificationPermissions"),
    ("RemoteNotification", "notifications", "NotificationPermissions"),
    ("RecordAudio", "microphone", "MicrophonePermissions"),
    ("BluetoothLe", "bluetooth", "BluetoothPermissions"),
    ("BluetoothScan", "bluetooth", "BluetoothPermissions"),
    ("BluetoothConnect", "bluetooth", "BluetoothPermissions"),
    ("BluetoothAdvertise", "bluetooth", "BluetoothPermissions"),
    ("ReadContacts", "contacts", "ContactPermissions"),
    ("WriteContacts", "contacts", "ContactPermissions"),
    ("ReadCalendar", "calendar", "CalendarPermissions"),
    ("WriteCalendar", "calendar", "CalendarPermissions"),
    ("WifiAccessState", "wifi", "WifiPermissions"),
    ("WifiChangeState", "wifi", "WifiPermissions"),
    ("WifiNearbyDevices", "wifi", "WifiPermissions"),
)
NORMAL = {"android.permission.BLUETOOTH", "android.permission.ACCESS_WIFI_STATE", "android.permission.CHANGE_WIFI_STATE"}
FORBIDDEN = {"android.permission." + value for value in ("CALL_PHONE", "MANAGE_EXTERNAL_STORAGE", "READ_SMS", "SEND_SMS", "RECEIVE_SMS")}


def source_path(module: str, filename: str) -> str:
    return f"calf-permissions/{module}/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/{filename}.android.kt"


class NoDtd(ET.TreeBuilder):
    def doctype(self, name, public_id, system_id):
        raise ValueError("Manifest DTD/entity declarations are refused")


def read(root: Path, relative: str) -> bytes:
    base = root.resolve(strict=True)
    path = base / relative
    if Path(relative).is_absolute() or not path.resolve(strict=True).is_relative_to(base):
        raise ValueError("Source path escapes the reviewed root")
    for entry in (path, *path.parents):
        if entry.is_relative_to(base) and entry.is_symlink():
            raise ValueError("Symlinked source/manifest input")
    before = path.stat()
    if not path.is_file() or before.st_nlink != 1 or not 0 < before.st_size <= 1024**2:
        raise ValueError("Expected bounded regular source/manifest input")
    result = path.read_bytes()
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError("Source/manifest input changed during review")
    return result


def declarations(payload: bytes) -> dict[str, dict]:
    if b"<!DOCTYPE" in payload or b"<!ENTITY" in payload:
        raise ValueError("Manifest DTD/entity declarations are refused")
    manifest = ET.fromstring(payload, parser=ET.XMLParser(target=NoDtd()))
    if manifest.tag != "manifest":
        raise ValueError("Not an Android manifest")
    result = {}
    for node in manifest:
        if node.tag not in {"uses-permission", "uses-permission-sdk-23"}:
            continue
        name = node.get(ANDROID + "name")
        if not isinstance(name, str) or name in result:
            raise ValueError("Missing/duplicate manifest permission identity")
        maximum = node.get(ANDROID + "maxSdkVersion")
        if maximum is not None and re.fullmatch(r"[0-9]+", maximum) is None:
            raise ValueError("Unknown manifest SDK cap")
        result[name] = {"tag": node.tag, "max_sdk": int(maximum) if maximum is not None else None}
    if result.keys() & FORBIDDEN:
        raise ValueError("The general sample acquired a forbidden Call/all-files/SMS permission")
    for name, maximum in (("READ_EXTERNAL_STORAGE", 32), ("WRITE_EXTERNAL_STORAGE", 28)):
        if result.get("android.permission." + name) != {"tag": "uses-permission", "max_sdk": maximum}:
            raise ValueError("The general sample's exact legacy SDK cap is missing")
    return result


def mapping(name: str, payload: bytes) -> dict:
    text = payload.decode("utf-8")
    method = re.findall(r"internal actual fun register" + re.escape(name) +
        r"Permission\(permission: Permission\)\s*\{(.*?)\n\}", text, re.S)
    if len(method) != 1:
        raise ValueError("Missing/duplicate owning Android mapper")
    native = re.findall(r"permissionString\s*=\s*Manifest\.permission\.([A-Z_]+)", method[0])
    no_gate = bool(re.search(r'AndroidPermissionMapping\("",\s*alwaysGranted\s*=\s*true\)', method[0]))
    if len(native) != (0 if no_gate else 1):
        raise ValueError("Unknown/ambiguous Android native mapping")
    minimum = re.findall(r"minSdkVersion\s*=\s*([0-9]+)", method[0])
    maximum = re.findall(r"maxSdkVersion\s*=\s*([0-9]+)", method[0])
    if len(minimum) > 1 or len(maximum) > 1:
        raise ValueError("Ambiguous mapper SDK interval")
    return {"native_permission": "android.permission." + native[0] if native else None,
            "min_sdk": int(minimum[0]) if minimum else 0,
            "max_sdk": int(maximum[0]) if maximum else None, "always_granted": no_gate}


def inspect(root: Path, merged_manifest: str | None = None) -> dict:
    inputs = {path: read(root, path) for path in {SCREEN, MANIFEST, "gradle/libs.versions.toml",
        "calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/AndroidPermissionRegistry.kt",
        *(source_path(module, filename) for _, module, filename in EXPECTED)}}
    screen = inputs[SCREEN].decode("utf-8")
    menus = re.findall(r"val permissions = remember\s*\{\s*listOf\((.*?)\)\s*\}", screen, re.S)
    if len(menus) != 1:
        raise ValueError("Unknown current menu construction")
    rows = re.findall(r"Permission\.([A-Za-z]+)\s*,", menus[0])
    if rows != [name for name, _, _ in EXPECTED] or len(rows) != len(set(rows)):
        raise ValueError("Every current menu declaration must be reviewed; no unknown, duplicate or omitted row")
    registry = inputs["calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/AndroidPermissionRegistry.kt"].decode("utf-8")
    if "val minSdkVersion: Int = 0" not in registry or "val maxSdkVersion: Int = Int.MAX_VALUE" not in registry:
        raise ValueError("Registry default SDK bounds changed")
    catalog = tomllib.loads(inputs["gradle/libs.versions.toml"].decode("utf-8"))["versions"]
    minimum, maximum = int(catalog["android-sample-minSdk"]), int(catalog["android-compileSdk"])
    if (minimum, maximum) != (24, 37):
        raise ValueError("Review the new supported sample/target SDK interval")
    source_manifest = declarations(inputs[MANIFEST])
    declared = source_manifest
    if merged_manifest is not None:
        path = Path(merged_manifest)
        if path.is_absolute() or not any(path.is_relative_to(prefix) for prefix in (
            Path("sample/android/build/intermediates/merged_manifest"), Path("sample/android/build/intermediates/merged_manifests"))):
            raise ValueError("Merged XML must come from the sample's generated manifest tree")
        inputs[merged_manifest] = read(root, merged_manifest)
        declared = declarations(inputs[merged_manifest])
    result_rows = []
    for name, module, filename in EXPECTED:
        location = source_path(module, filename)
        entry = mapping(name, inputs[location])
        native = entry["native_permission"]
        if native is not None and native not in declared:
            raise ValueError("A current mapped menu permission has no declaration")
        predictions = {}
        for api in range(minimum, maximum + 1):
            no_gate = entry["always_granted"] or api < entry["min_sdk"] or (entry["max_sdk"] is not None and api > entry["max_sdk"])
            if no_gate:
                prediction = {"status": "Granted", "availability": "NotRequired", "access": "Unknown", "requestability": "NotRequired"}
            elif native in NORMAL:
                prediction = {"status": "Granted", "availability": "Available", "access": "Full", "requestability": "NotRequired"}
            else:
                prediction = {"status": "Denied(false)", "availability": "Available", "access": "None",
                    "requestability": "PrerequisiteRequired" if name == "BackgroundLocation" else "Unknown"}
            predictions[str(api)] = prediction
        result_rows.append({"menu": name, "mapper_source": location, **entry,
            "manifest_declaration": declared.get(native), "fresh_install_status_predictions_by_api": predictions})
    return {"schema_version": 1, "menu_count": len(rows), "sample_min_sdk": minimum, "sample_target_sdk": maximum,
        "manifest_kind": "provided-generated-XML" if merged_manifest else "source-only",
        "manifest_generation_execution_proven": False, "native_executions": 0,
        "status_predictions_are_native_results": False,
        "source_inputs": {path: hashlib.sha256(payload).hexdigest() for path, payload in sorted(inputs.items())},
        "permissions_not_requested_by_a_menu_row": sorted(set(declared) - {entry["native_permission"] for entry in result_rows}),
        "rows": result_rows,
        "limits": ["Availability/status does not prove a hardware operation or app-op.",
            "RemoteNotification is an explicit NotRequired mapping; Android APNs delivery is unavailable.",
            "BackgroundLocation requires foreground first; API29 is separate runtime, API30+ is settings-only after foreground.",
            "FineLocation requests Coarse+Fine on API31+; coarse-only yields Approximate rather than Full precise access.",
            "On API34+ ReadImage/ReadVideo observe Limited only when selected access is genuinely granted and full permission is denied.",
            "Merged XML alone has no Gradle/install/native execution provenance."]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--merged-manifest")
    arguments = parser.parse_args()
    print(json.dumps(inspect(arguments.root, arguments.merged_manifest), indent=2))


if __name__ == "__main__":
    main()
