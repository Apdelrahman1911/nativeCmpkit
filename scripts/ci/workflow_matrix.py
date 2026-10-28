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
    "browser-picker": ("browser-js", "browser-wasm"),
    "webview-browser": ("browser-js", "browser-wasm"),
    "webview-wasm": ("browser-wasm",),
    "share-browser": ("browser-js", "browser-wasm"),
    "ui-date-browser": ("browser-js", "browser-wasm"),
    "ui-date-js": ("browser-js",),
    "ui-date-platforms": ("browser-js", "browser-wasm", "android-device-api35"),
    "ui-date-wasm": ("browser-wasm",),
    "ui-date-android": ("android-device-api35",),
    "navigation-geo": ("browser-js", "browser-wasm"),
    "navigation-desktop": ("desktop-linux-x64",),
    "webview-desktop": ("desktop-linux-x64",),
    "desktop-data-safety": ("desktop-linux-x64", "desktop-macos-arm64", "desktop-windows-x64"),
    "android-resource-safety": ("android-host",),
    "android-coil-resource": ("android-host",),
    "android-permission-alias": ("android-host",),
    "permissions-unsupported": ("desktop-linux-x64", "desktop-macos-arm64", "desktop-windows-x64", "browser-js", "browser-wasm"),
    # Checkout-only repair: preserve the four already accepted same-input hosts.
    "permissions-unsupported-windows": ("desktop-windows-x64",),
    "permissions-ios": ("ios-iphone",),
    "permissions-ios-safety": ("ios-iphone",),
    "permissions-ios-empty-batch": ("ios-iphone",),
    "permissions-completion-android": ("android-host",),
    "navigation-geo-matrix": ("desktop-linux-x64", "browser-js", "browser-wasm", "ios-iphone"),
    "apple": ("desktop-macos-arm64", "ios-iphone"),
    "ios": ("ios-iphone",),
    "ios-ui": ("ios-iphone",),
    "ios-date-bounds": ("ios-iphone",),
    "ios-date-replacement": ("ios-iphone",),
    "ios-date-compact": ("ios-iphone",),
    "ios-dates-important": ("ios-iphone",),
    "ios-io": ("ios-iphone",),
    "windows": ("desktop-windows-x64",),
    "windows-cache": ("desktop-windows-x64",),
    "windows-share-loader": ("desktop-windows-x64",),
    "windows-share-boundaries": ("desktop-windows-x64",),
    "extended": ("desktop-linux-arm64", "desktop-macos-x64", "ios-ipad"),
    "android-device": ("android-device-api35",),
    "android-webview": ("android-device-api35",),
    "android-io-oversize": ("android-device-api35",),
    "android-saver-identity": ("android-device-api35",),
    "android-saver-identity-missing": ("android-device-api35",),
    # Separate explicitly PARTIAL Maven consumer job, not a library/source suite.
    "consumer-core-io": (),
    "all": tuple(slot["slot"] for slot in SLOTS),
    "tooling": (),
}
MODULE_SUBSETS = {
    # Public Compose/DOM picker lifetime only; no replay of unchanged IO/other suites.
    "browser-picker": "calf-file-picker",
    # Real public WebView/Compose viewport disposal on both browser backends only.
    "webview-browser": "calf-webview",
    # Recover a Wasm-only fixture/compiler failure without replaying accepted JS.
    "webview-wasm": "calf-webview",
    # Share/clipboard callback boundaries only; unchanged Android results are reusable.
    "share-browser": "calf-share",
    # Four important public dialog transactions, not an unrelated UI suite replay.
    "ui-date-browser": "calf-ui",
    "ui-date-js": "calf-ui",
    "ui-date-platforms": "calf-ui",
    "ui-date-wasm": "calf-ui",
    "ui-date-android": "calf-ui",
    # Immutable portable argument/saver/numerical checks without repeating the
    # entire19-module browser suite. Does not change full browser/all coverage.
    "navigation-geo": "calf-navigation,calf-geo",
    # JVM-only allocation/work probes need an immutable desktop run, not replay
    # of unchanged JS/Wasm/Apple/geo or full-library results.
    "navigation-desktop": "calf-navigation",
    # Real JavaFX/window cancellation and reattachment; never replay unrelated
    # passed platform, consumer, native-picker or shared UI suites.
    "webview-desktop": "calf-webview",
    # Changed interruptible file-copy and no-open share policy: actual JVM tests
    # on all three desktop OS families, not unrelated browser/mobile/sample jobs.
    "desktop-data-safety": "calf-file-picker,calf-share",
    "android-resource-safety": "calf-io,calf-file-picker-coil",
    # Reuse unchanged accepted IO27 results; only the repaired Coil fixture runs.
    "android-coil-resource": "calf-file-picker-coil",
    # Actual builtin cold initialization in both orders at SDK28/32/33; core
    # host tests consume Gallery production code without rerunning other suites.
    "android-permission-alias": "calf-permissions/core",
    "permissions-unsupported": "calf-permissions/core",
    "permissions-unsupported-windows": "calf-permissions/core",
    "permissions-ios": "calf-permissions/core",
    "permissions-ios-safety": "calf-permissions/core",
    "permissions-ios-empty-batch": "calf-permissions/core",
    "permissions-completion-android": "calf-permissions/core",
    # A changed common test requires its own JVM/browser/Native execution, not
    # reuse of the older source tests or repetition of unrelated UIKit/consumer
    # suites. The browser-only continuation remains a separate finite profile.
    "navigation-geo-matrix": "calf-navigation,calf-geo",
    "windows-cache": "calf-file-picker,calf-share",
    # Preserve the accepted picker57; diagnose only the share read-only boundary.
    "windows-share-loader": "calf-share",
    # Five real boundary methods only; preserve all38 accepted unrelated share
    # methods and picker57 rather than rerun version/DLL/application suites.
    "windows-share-boundaries": "calf-share",
    "ios-ui": "calf-ui",
    "ios-date-bounds": "calf-ui",
    "ios-date-replacement": "calf-ui",
    "ios-date-compact": "calf-ui",
    "ios-dates-important": "calf-ui",
    # Foundation/guarded-copy/stream/Coil evidence without replaying unchanged
    # UIKit, picker-dialog, browser, Windows or packaged-consumer execution.
    "ios-io": "calf-io,calf-file-picker-coil",
    "android-webview": "calf-webview",
    "android-io-oversize": "calf-io",
    "android-saver-identity": "calf-file-picker",
    "android-saver-identity-missing": "calf-file-picker",
}


def matrix(profile: str) -> dict:
    if profile not in PROFILES:
        raise ValueError("Unknown verification profile; arbitrary runner/task input is prohibited")
    selected = set(PROFILES[profile])
    rows = [dict(slot) for slot in SLOTS if slot["slot"] in selected]
    if profile in MODULE_SUBSETS:
        for row in rows:
            row["test-modules"] = MODULE_SUBSETS[profile]
    if profile == "windows-share-boundaries":
        for row in rows:
            row["test-focus"] = "native-share-boundaries"
    if profile in {"permissions-unsupported", "permissions-unsupported-windows"}:
        for row in rows:
            row["test-focus"] = "permission-public-unsupported"
    if profile == "permissions-ios":
        for row in rows:
            row["test-focus"] = "permission-ios-factories"
    if profile == "permissions-ios-safety":
        for row in rows:
            row["test-focus"] = "permission-ios-safety"
    if profile == "permissions-ios-empty-batch":
        for row in rows:
            row["test-focus"] = "permission-ios-empty-batch"
    if profile == "permissions-completion-android":
        for row in rows:
            row["test-focus"] = "permission-android-completion"
    if profile == "ios-date-bounds":
        for row in rows:
            row["test-focus"] = "ui-native-date-bounds"
    if profile == "ios-date-replacement":
        for row in rows:
            row["test-focus"] = "ui-native-date-replacement"
    if profile == "ios-date-compact":
        for row in rows:
            row["test-focus"] = "ui-native-compact-replacement"
    if profile == "ios-dates-important":
        for row in rows:
            row["test-focus"] = "ui-native-important-dates"
    if profile in {"ui-date-platforms", "ui-date-browser", "ui-date-js", "ui-date-wasm", "ui-date-android"}:
        for row in rows:
            row["test-focus"] = "material-date-transaction"
    if profile == "android-io-oversize":
        for row in rows:
            row["test-focus"] = "io-device-known-oversize"
    if profile == "android-saver-identity":
        for row in rows:
            row["test-focus"] = "save-device-identity"
    if profile == "android-saver-identity-missing":
        for row in rows:
            row["test-focus"] = "save-device-identity-missing"
    return {"include": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=sorted(PROFILES))
    args = parser.parse_args()
    print(json.dumps(matrix(args.profile), separators=(",", ":")))


if __name__ == "__main__":
    main()
