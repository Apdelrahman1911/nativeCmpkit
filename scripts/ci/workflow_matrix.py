#!/usr/bin/env python3
"""Finite manual-dispatch library matrix; no shell expansion or runner input.

Profiles select work, not support declarations. Only recorded runtime/test
receipts establish coverage; extended slots are not silently dropped from all.
"""
from __future__ import annotations
import argparse
import json

SLOTS = (
    {"slot": "desktop-linux-x64", "suite": "desktop", "runner": "ubuntu-24.04", "arch": "x64", "python": "python3"},
    {"slot": "android-host", "suite": "android-host", "runner": "ubuntu-24.04", "arch": "x64", "python": "python3"},
    {"slot": "browser-js", "suite": "js", "runner": "ubuntu-24.04", "arch": "x64", "python": "python3"},
    {"slot": "browser-wasm", "suite": "wasm", "runner": "ubuntu-24.04", "arch": "x64", "python": "python3"},
    {"slot": "desktop-macos-arm64", "suite": "desktop", "runner": "macos-26", "arch": "arm64", "python": "python3", "native-ui": "true"},
    {"slot": "ios-iphone", "suite": "ios", "runner": "macos-26", "arch": "arm64", "python": "python3", "simulator-kind": "iphone"},
    {"slot": "desktop-windows-x64", "suite": "desktop", "runner": "windows-2025", "arch": "x64", "python": "python"},
    {"slot": "desktop-linux-arm64", "suite": "desktop", "runner": "ubuntu-24.04-arm", "arch": "arm64", "python": "python3"},
    {"slot": "desktop-macos-x64", "suite": "desktop", "runner": "macos-26-intel", "arch": "x64", "python": "python3", "native-ui": "true"},
    {"slot": "ios-ipad", "suite": "ios", "runner": "macos-26", "arch": "arm64", "python": "python3", "simulator-kind": "ipad"},
    {"slot": "android-device-api35", "suite": "android-device", "runner": "ubuntu-24.04", "arch": "x64", "python": "python3", "emulator-api": "35"},
)
PROFILES = {
    "core": ("desktop-linux-x64", "android-host"),
    "browser": ("browser-js", "browser-wasm"),
    "apple": ("desktop-macos-arm64", "ios-iphone"),
    "ios": ("ios-iphone",),
    "ios-ui": ("ios-iphone",),
    "windows": ("desktop-windows-x64",),
    "windows-cache": ("desktop-windows-x64",),
    "extended": ("desktop-linux-arm64", "desktop-macos-x64", "ios-ipad"),
    "android-device": ("android-device-api35",),
    "all": tuple(slot["slot"] for slot in SLOTS),
    "tooling": (),
}
MODULE_SUBSETS = {
    "windows-cache": "calf-file-picker,calf-share",
    "ios-ui": "calf-ui",
}


def matrix(profile: str) -> dict:
    if profile not in PROFILES:
        raise ValueError("Unknown verification profile; arbitrary runner/task input is prohibited")
    selected = set(PROFILES[profile])
    rows = [dict(slot) for slot in SLOTS if slot["slot"] in selected]
    if profile in MODULE_SUBSETS:
        for row in rows:
            row["test-modules"] = MODULE_SUBSETS[profile]
    return {"include": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=sorted(PROFILES))
    args = parser.parse_args()
    print(json.dumps(matrix(args.profile), separators=(",", ":")))


if __name__ == "__main__":
    main()
