# SPDX-License-Identifier: Apache-2.0
"""Finite adaptive iPhone selection from complete actual simctl JSON inventories.

This pure helper does not capture, boot, retry, erase or claim native readiness.
The lead wires it into a NEW capture's inventory boundary for the two reviewed
adaptive focuses. Existing runtime selection and all native assertions stay.
"""
from __future__ import annotations

import json
import re

FOCUSES = ("ui-native-adaptive-pre26", "ui-native-adaptive-ios26plus")
MAX_INVENTORY_BYTES = 2 * 1024 * 1024
MAX_DEVICES = 1024
MAX_RUNTIMES = 128
MAX_INT = 2147483647
SIMULATOR_FIELDS = frozenset(("udid", "device_type", "state", "runtime_identifier",
                              "runtime_version", "runtime_build"))
_PREFIX = "com.apple.CoreSimulator.SimRuntime."
_RUNTIME = re.compile(re.escape(_PREFIX) + r"[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*\Z")
_VERSION_PART = r"(?:0|[1-9][0-9]{0,9})"
_VERSION = re.compile(r"[1-9][0-9]{0,9}(?:\." + _VERSION_PART + r"){0,2}\Z")
_IOS = re.compile(re.escape(_PREFIX) + r"iOS-([1-9][0-9]{0,9}(?:-" + _VERSION_PART + r"){0,2})\Z")
_TYPE_PREFIX = "com.apple.CoreSimulator.SimDeviceType."
_TYPE = re.compile(re.escape(_TYPE_PREFIX) + r"[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*\Z")
_IPHONE = re.compile(re.escape(_TYPE_PREFIX) + r"iPhone(?:-[A-Za-z0-9]+)+\Z")
_UUID = re.compile(r"[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}\Z")
_BUILD = re.compile(r"[0-9A-Za-z]{1,64}\Z")
_STATES = frozenset(("Booted", "Shutdown"))


def branch(focus: str) -> str:
    if type(focus) is not str or focus not in FOCUSES:
        raise ValueError("Select exactly one reviewed adaptive runtime focus")
    return "pre26" if focus == FOCUSES[0] else "ios26plus"


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate simulator inventory field")
        result[key] = value
    return result


def _constant(value):
    raise ValueError("Nonstandard simulator JSON constant")


def _inventory(raw, role):
    if type(raw) not in (bytes, str):
        raise ValueError("Full ordinary simulator inventory JSON required")
    try:
        payload = raw.encode("utf-8") if type(raw) is str else raw
        if not 0 < len(payload) <= MAX_INVENTORY_BYTES:
            raise ValueError("Bounded complete simulator inventory JSON required")
        document = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique,
                              parse_constant=_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("Unrecognized complete simulator inventory JSON") from None
    if type(document) is not dict or set(document) != {role}:
        raise ValueError("Exact complete simulator inventory root required")
    return document[role]


def _version(value):
    if type(value) is not str or _VERSION.fullmatch(value) is None:
        raise ValueError("Exact positive numeric simulator runtime version required")
    parts = tuple(map(int, value.split(".")))
    if any(part > MAX_INT for part in parts):
        raise ValueError("Simulator runtime version exceeds its numeric bounds")
    return parts


def _ios_version(identifier, version):
    match = _IOS.fullmatch(identifier) if type(identifier) is str else None
    if match is None:
        raise ValueError("Exact iOS simulator runtime identifier required")
    parts = _version(version)
    identity = tuple(map(int, match[1].split("-")))
    # Actual iOS-26-4 identifies a runtime reporting version26.4.1. Preserve that
    # full version/build; every identifier component must still match its prefix.
    if any(part > MAX_INT for part in identity) or parts[:len(identity)] != identity:
        raise ValueError("iOS runtime identifier and actual version disagree")
    return parts


def _udid(value):
    if (type(value) is not str or _UUID.fullmatch(value) is None or
            int(value.replace("-", ""), 16) == 0):
        raise ValueError("An exact nonzero simulator UDID is required")
    return value.upper()


def validate_selected(simulator: dict, focus: str, *, udid: str | None = None,
                      require_booted: bool = False) -> bool:
    """Validate an actual selection; do not edit it or infer missing fields."""
    wanted = branch(focus)
    if type(require_booted) is not bool or type(simulator) is not dict or set(simulator) != SIMULATOR_FIELDS:
        raise ValueError("The complete ordinary selected-simulator identity is required")
    actual_udid = _udid(simulator["udid"])
    if udid is not None and actual_udid != _udid(udid):
        raise ValueError("Selected simulator differs from the explicit device")
    kind = simulator["device_type"]
    if type(kind) is not str or len(kind) > 180 or _IPHONE.fullmatch(kind) is None:
        raise ValueError("Adaptive native groups require an actual iPhone device type")
    state = simulator["state"]
    if type(state) is not str or state not in _STATES or (require_booted and state != "Booted"):
        raise ValueError("Selected iPhone does not have the required actual boot state")
    version = _ios_version(simulator["runtime_identifier"], simulator["runtime_version"])
    build = simulator["runtime_build"]
    if type(build) is not str or _BUILD.fullmatch(build) is None:
        raise ValueError("Exact selected iOS runtime build required")
    if (version[0] < 26) != (wanted == "pre26"):
        raise ValueError("Selected iPhone does not belong to the required adaptive OS branch")
    return True


def select_iphone_json(devices_json, runtimes_json, focus: str, *,
                       udid: str | None = None) -> dict:
    """Select within the requested band once; no wrong-band or boot fallback.

The caller supplies both full completed actual inventory responses. User names,
runtime filesystem paths and unrelated inventory data never enter the result.
Explicit UDIDs are matched exactly; missing/unavailable identities cannot select
another device. Availability is an exact boolean on BOTH runtime and device.
"""
    branch(focus)
    wanted_udid = _udid(udid) if udid is not None else None
    devices = _inventory(devices_json, "devices")
    runtimes = _inventory(runtimes_json, "runtimes")
    if type(devices) is not dict or len(devices) > MAX_RUNTIMES or type(runtimes) is not list or len(runtimes) > MAX_RUNTIMES:
        raise ValueError("Bounded complete device and runtime inventories required")
    identities = {}
    for row in runtimes:
        if type(row) is not dict:
            raise ValueError("Ordinary complete simulator runtime rows required")
        identifier, version, build = (row.get(key) for key in ("identifier", "version", "buildversion"))
        if (type(identifier) is not str or len(identifier) > 180 or _RUNTIME.fullmatch(identifier) is None or
                identifier in identities or type(row.get("isAvailable")) is not bool or
                type(build) is not str or _BUILD.fullmatch(build) is None):
            raise ValueError("Unambiguous actual simulator runtime identity and availability required")
        _version(version)
        if identifier.startswith(_PREFIX + "iOS"):
            _ios_version(identifier, version)
        identities[identifier] = row
    seen = set()
    candidates = []
    for identifier, rows in devices.items():
        if (type(identifier) is not str or identifier not in identities or
                type(rows) is not list or len(rows) > MAX_DEVICES):
            raise ValueError("Every device group requires its exact complete runtime identity")
        runtime = identities[identifier]
        for row in rows:
            if type(row) is not dict:
                raise ValueError("Ordinary complete simulator device rows required")
            device_id = _udid(row.get("udid"))
            kind, name = row.get("deviceTypeIdentifier"), row.get("name")
            if (device_id in seen or type(kind) is not str or len(kind) > 180 or _TYPE.fullmatch(kind) is None or
                    type(row.get("isAvailable")) is not bool or type(row.get("state")) is not str or
                    row["state"] not in _STATES or
                    type(name) is not str or len(name) > 4096):
                raise ValueError("Unambiguous actual simulator device identity/state/availability required")
            seen.add(device_id)
            if len(seen) > MAX_DEVICES:
                raise ValueError("Simulator inventory exceeds its finite device budget")
            if (row["isAvailable"] is not True or runtime["isAvailable"] is not True or
                    _IPHONE.fullmatch(kind) is None or _IOS.fullmatch(identifier) is None or
                    (wanted_udid is not None and device_id != wanted_udid)):
                continue
            selected = {"udid": row["udid"], "device_type": kind, "state": row["state"],
                        "runtime_identifier": identifier, "runtime_version": runtime["version"],
                        "runtime_build": runtime["buildversion"]}
            version = _version(runtime["version"])
            if (version[0] < 26) == (focus == FOCUSES[0]):
                validate_selected(selected, focus, udid=udid)
                candidates.append(selected)
    if not candidates:
        raise ValueError("No actually available iPhone in the required adaptive runtime branch")
    candidates.sort(key=lambda row: (_version(row["runtime_version"]), row["device_type"], _udid(row["udid"])))
    return candidates[-1]


def validate_context(context: dict, focus: str, *, udid: str) -> bool:
    """Check a NEW actual capture at the native boundary, without changing it.

Availability is established by select_iphone_json at that capture's full-query
boundary. This additional identity/branch check is not native test acceptance.
"""
    branch(focus)
    if (type(context) is not dict or type(context.get("schema_version")) is not int or
            context["schema_version"] != 1 or type(context.get("host")) is not dict or
            context["host"].get("system") != "Darwin" or context["host"].get("architecture") != "arm64" or
            type(context.get("source_revision")) is not str or
            re.fullmatch(r"[a-f0-9]{40}", context["source_revision"]) is None or
            context.get("source_tree_dirty") is not False):
        raise ValueError("Adaptive native execution requires a clean actual macOS Arm64 capture")
    _udid(udid)
    return validate_selected(context.get("simulator"), focus, udid=udid, require_booted=True)
