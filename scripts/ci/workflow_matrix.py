#!/usr/bin/env python3
"""Finite manual-dispatch library matrix; no shell expansion or runner input.

Profiles select work, not support declarations. Only recorded runtime/test
receipts establish coverage; extended slots are not silently dropped from all.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
import android_storage_compatibility_plan as storage_plan
import android_device_batch_plan as android_batch_plan
import desktop_security_plan

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
    "android-io-permission-storage-api35": ("android-device-api35",),
    "android-permission-storage-api35-recovery": ("android-device-api35",),
    "android-permission-storage-compatibility": ("android-device-api35",),
    "android-media-selection-compatibility": ("android-device-api35",),
    "android-storage-compatibility": ("android-device-api35",),
    "android-storage-api28": ("android-device-api35",),
    "android-storage-api29-target28": ("android-device-api35",),
    "android-storage-api29-legacy": ("android-device-api35",),
    "android-storage-api29-scoped": ("android-device-api35",),
    "android-storage-api30-normal": ("android-device-api35",),
    "android-storage-api30-all-files": ("android-device-api35",),
    "android-storage-api35-normal": ("android-device-api35",),
    "android-storage-api35-all-files": ("android-device-api35",),
    "core": ("desktop-linux-x64", "android-host"),
    "android-geo-ownership": ("android-device-api35",),
    "android-geo-provider": ("android-device-api35",),
    "android-geo-prerequisites": ("android-device-api35",),
    "android-share-grants": ("android-device-api35",),
    "android-io-provider-lifecycle": ("android-device-api35",),
    "android-io-provider-unavailable": ("android-device-api35",),
    "android-io-default-decode": ("android-device-api35",),
    "android-io-named-system-providers": ("android-device-api35",),
    "android-io-named-external-storage": ("android-device-api35",),
    "android-io-reference-regressions": ("android-device-api35",),
    "android-permission-demo": ("android-device-api35",),
    "android-permission-demo-call-denial-recovery": ("android-device-api35",),
    "android-permission-demo-denial-recovery": ("android-device-api35",),
    "android-media-selection-api33": ("android-device-api35",),
    "android-media-selection-api34": ("android-device-api35",),
    "android-camera-provider": ("android-device-api35",),
    "android-camera-provider-minimum": ("android-device-api35",),
    "android-camera-no-handler-minimum": ("android-device-api35",),
    "android-camera-restoration": ("android-device-api35",),
    "android-camera-restoration-dont-keep": ("android-device-api35",),
    "browser": ("browser-js", "browser-wasm"),
    "browser-picker": ("browser-js", "browser-wasm"),
    "browser-coil-io": ("browser-js", "browser-wasm"),
    "browser-coil-io-js": ("browser-js",),
    "browser-coil-io-wasm": ("browser-wasm",),
    "webview-browser": ("browser-js", "browser-wasm"),
    "webview-content-transitions": ("browser-js", "browser-wasm"),
    "webview-request-state": ("browser-js", "browser-wasm"),
    "webview-offline-destination": ("browser-js", "browser-wasm"),
    "webview-desktop-request-state": ("desktop-linux-x64", "desktop-macos-arm64", "desktop-windows-x64", "desktop-linux-arm64", "desktop-macos-x64"),
    "webview-desktop-security-regressions": ("desktop-macos-arm64", "desktop-windows-x64", "desktop-linux-arm64", "desktop-macos-x64"),
    "webview-desktop-request-state-linux-pair": ("desktop-linux-x64", "desktop-linux-arm64"),
    "webview-desktop-request-state-macos-pair": ("desktop-macos-arm64", "desktop-macos-x64"),
    "webview-desktop-request-state-windows-single": ("desktop-windows-x64",),
    "webview-desktop-stop-windows-recovery": ("desktop-windows-x64",),
    "webview-desktop-security-linux-arm64-windows-pair": ("desktop-windows-x64", "desktop-linux-arm64"),
    "webview-desktop-security-macos-pair": ("desktop-macos-arm64", "desktop-macos-x64"),
    "webview-desktop-policy-macos-recovery": ("desktop-macos-arm64", "desktop-macos-x64"),
    "webview-desktop-tls-windows-recovery": ("desktop-windows-x64",),
    "webview-wasm": ("browser-wasm",),
    "share-browser": ("browser-js", "browser-wasm"),
    "share-clipboard-native": ("browser-js", "browser-wasm"),
    "share-clipboard-native-wasm": ("browser-wasm",),
    "ui-date-browser": ("browser-js", "browser-wasm"),
    "ui-date-js": ("browser-js",),
    "ui-date-platforms": ("browser-js", "browser-wasm", "android-device-api35"),
    "ui-date-wasm": ("browser-wasm",),
    "ui-date-android": ("android-device-api35",),
    "ui-dropdown-platforms": ("desktop-linux-x64", "browser-js", "browser-wasm", "android-device-api35"),
    "ui-dropdown-android-recovery": ("android-device-api35",),
    "navigation-geo": ("browser-js", "browser-wasm"),
    "navigation-desktop": ("desktop-linux-x64",),
    "webview-desktop": ("desktop-linux-x64",),
    "webview-identity": ("desktop-linux-x64", "browser-js", "browser-wasm", "android-device-api35"),
    "webview-identity-linux": ("desktop-linux-x64",),
    "webview-identity-browser": ("browser-js", "browser-wasm"),
    "webview-identity-wasm": ("browser-wasm",),
    "webview-identity-android": ("android-device-api35",),
    "webview-identity-recovery": ("desktop-linux-x64", "ios-iphone", "android-device-api35"),
    "webview-identity-remount-recovery": ("ios-iphone", "android-device-api35"),
    "webview-identity-ios-remount-recovery": ("ios-iphone",),
    "webview-lifetime": ("android-device-api35", "desktop-linux-x64", "desktop-macos-arm64", "desktop-macos-x64", "desktop-windows-x64"),
    "webview-lifetime-android": ("android-device-api35",),
    "webview-lifetime-android-media": ("android-device-api35",),
    "webview-lifetime-linux": ("desktop-linux-x64",),
    "webview-lifetime-macos-arm64": ("desktop-macos-arm64",),
    "webview-lifetime-macos-x64": ("desktop-macos-x64",),
    "webview-lifetime-macos-media": ("desktop-macos-x64",),
    "webview-lifetime-windows": ("desktop-windows-x64",),
    "picker-batch": ("desktop-linux-x64", "desktop-macos-arm64", "desktop-windows-x64"),
    "picker-batch-recovery": ("desktop-linux-x64", "desktop-macos-arm64"),
    "picker-batch-linux": ("desktop-linux-x64",),
    "picker-batch-macos": ("desktop-macos-arm64",),
    "picker-batch-windows": ("desktop-windows-x64",),
    "picker-saver-state": ("desktop-linux-x64", "desktop-macos-arm64", "desktop-windows-x64"),
    "picker-linux-portal": ("desktop-linux-x64",),
    "picker-linux-portal-save": ("desktop-linux-x64",),
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
    "ios-secure-alert-input": ("ios-iphone",),
    "ios-date-bounds": ("ios-iphone",),
    "ios-date-replacement": ("ios-iphone",),
    "ios-date-compact": ("ios-iphone",),
    "ios-dates-important": ("ios-iphone",),
    "ios-alert-date-important": ("ios-iphone",),
    "ios-alert-important-recovery": ("ios-iphone",),
    "ios-modal-ownership-batch": ("ios-iphone",),
    "ios-modal-ownership-ipad": ("ios-ipad",),
    "ios-modal-lifecycle-replacement": ("ios-iphone",),
    "ios-modal-lifecycle-replacement-ipad": ("ios-ipad",),
    "ios-date-year-predicate-red": ("ios-iphone",),
    "ios-io": ("ios-iphone",),
    "ios-saver-write-failure": ("ios-iphone",),
    "ios-picker-batch": ("ios-iphone",),
    "ios-picker-recovery": ("ios-iphone",),
    "ios-picker-admission": ("ios-iphone",),
    "ios-picker-provider-cancellation": ("ios-iphone",),
    "ios-share-presentation-disposal": ("ios-iphone",),
    "ios-share-remembered-failure-observation": ("ios-iphone",),
    "ios-switch-cancellation": ("ios-iphone",),
    "ios-switch-ownership": ("ios-iphone",),
    "ios-slider-numeric": ("ios-iphone",),
    "ios-ui-state": ("ios-iphone",),
    "ios-time-state-recovery": ("ios-iphone",),
    "ios-slider-lifecycle": ("ios-iphone",),
    "ios-slider-remaining": ("ios-iphone",),
    "ios-slider-structure": ("ios-iphone",),
    "ios-slider-tap": ("ios-iphone",),
    "ios-slider-pair-structure": ("ios-iphone",),
    "ios-vector-theme": ("ios-ipad",),
    "ios-vector-theme-recovery": ("ios-ipad",),
    "ios-vector-rendering-recovery": ("ios-ipad",),
    "ios-vector-rendering-iphone-recovery": ("ios-iphone",),
    "ios-vector-native-screen-pair": ("ios-ipad",),
    "ios-slider-recovery": ("ios-iphone",),
    "ios-image-memory": ("ios-iphone",),
    "ios-image-memory-darwin": ("ios-iphone",),
    "ios-image-profile-recovery": ("ios-iphone",),
    # Separate SDK help/identity discovery; no library/device/consumer execution.
    "ios-appinfo-capability": (),
    # Current owned-app shape prerequisite, not a native/library-test selection.
    "ios-appinfo-shape": (),
    "ios-webview-lifecycle": ("ios-iphone",),
    "ios-webview-recovery": ("ios-iphone",),
    "ios-webview-request-state": ("ios-iphone",),
    "ios-webview-provisional-dns": ("ios-iphone",),
    "ios-webview-request-dns": ("ios-iphone",),
    "windows": ("desktop-windows-x64",),
    "windows-cache": ("desktop-windows-x64",),
    "windows-share-loader": ("desktop-windows-x64",),
    "windows-share-boundaries": ("desktop-windows-x64",),
    "extended": ("desktop-linux-arm64", "desktop-macos-x64", "ios-ipad"),
    "android-device": ("android-device-api35",),
    "android-webview": ("android-device-api35",),
    "android-webview-popups": ("android-device-api35",),
    "android-webview-request-state": ("android-device-api35",),
    "android-webview-stop-redirect-recovery": ("android-device-api35",),
    "android-navigation-back": ("android-device-api35",),
    "android-io-oversize": ("android-device-api35",),
    "android-saver-identity": ("android-device-api35",),
    "android-saver-identity-missing": ("android-device-api35",),
    # Separate explicitly PARTIAL Maven consumer job, not a library/source suite.
    "consumer-core-io": (),
    "consumer-webview": (),
    "consumer-webview-remaining": (),
    "consumer-webview-linux-x64": (),
    "consumer-webview-linux-arm64": (),
    "consumer-webview-macos-arm64": (),
    "consumer-webview-macos-x64": (),
    "consumer-webview-windows-x64": (),
    # Separate finite sample jobs; never shrink or replace any library/device slot.
    "sample-platforms-linux": (),
    "sample-platforms-apple": (),
    "sample-builds-linux": (),
    "sample-builds-apple": (),
    "all": tuple(slot["slot"] for slot in SLOTS),
    "tooling": (),
}
MODULE_SUBSETS = {
    "android-io-permission-storage-api35": "calf-io,calf-permissions/core",
    "android-permission-storage-api35-recovery": "calf-permissions/core",
    "android-permission-storage-compatibility": "calf-permissions/core",
    "android-media-selection-compatibility": "calf-permissions/core",
    "android-storage-compatibility": "calf-permissions/core",
    "android-storage-api28": "calf-permissions/core",
    "android-storage-api29-target28": "calf-permissions/core",
    "android-storage-api29-legacy": "calf-permissions/core",
    "android-storage-api29-scoped": "calf-permissions/core",
    "android-storage-api30-normal": "calf-permissions/core",
    "android-storage-api30-all-files": "calf-permissions/core",
    "android-storage-api35-normal": "calf-permissions/core",
    "android-storage-api35-all-files": "calf-permissions/core",
    "android-geo-ownership": "calf-geo",
    "android-geo-provider": "calf-geo",
    "android-geo-prerequisites": "calf-geo",
    "android-share-grants": "calf-share",
    "android-io-provider-lifecycle": "calf-io",
    "android-io-provider-unavailable": "calf-io",
    "android-io-default-decode": "calf-io",
    "android-io-named-system-providers": "calf-io",
    "android-io-named-external-storage": "calf-io",
    "android-io-reference-regressions": "calf-io",
    "android-permission-demo": "calf-permissions/core",
    "android-permission-demo-call-denial-recovery": "calf-permissions/core",
    "android-permission-demo-denial-recovery": "calf-permissions/core",
    "android-media-selection-api33": "calf-permissions/core",
    "android-media-selection-api34": "calf-permissions/core",
    "android-camera-provider": "calf-camera-picker",
    "android-camera-provider-minimum": "calf-camera-picker",
    "android-camera-no-handler-minimum": "calf-camera-picker",
    "android-camera-restoration": "calf-camera-picker",
    "android-camera-restoration-dont-keep": "calf-camera-picker",
    "android-navigation-back": "calf-navigation",
    "ios-webview-lifecycle": "calf-webview",
    "ios-webview-recovery": "calf-webview",
    "ios-webview-request-state": "calf-webview",
    "ios-webview-provisional-dns": "calf-webview",
    "ios-webview-request-dns": "calf-webview",
    "ios-secure-alert-input": "calf-ui",
    "ios-image-memory-darwin": "calf-ui",
    "ios-image-profile-recovery": "calf-ui",
    # Public Compose/DOM picker lifetime only; no replay of unchanged IO/other suites.
    "browser-picker": "calf-file-picker",
    "browser-coil-io": "calf-file-picker-coil",
    "browser-coil-io-js": "calf-file-picker-coil",
    "browser-coil-io-wasm": "calf-file-picker-coil",
    # Real public WebView/Compose viewport disposal on both browser backends only.
    "webview-browser": "calf-webview",
    # Two missing original iframe criteria methods only; accepted Browser004 stays reusable.
    "webview-content-transitions": "calf-webview",
    "webview-request-state": "calf-webview",
    "webview-offline-destination": "calf-webview",
    "webview-desktop-request-state": "calf-webview",
    "webview-desktop-security-regressions": "calf-webview",
    "webview-desktop-request-state-linux-pair": "calf-webview",
    "webview-desktop-request-state-macos-pair": "calf-webview",
    "webview-desktop-request-state-windows-single": "calf-webview",
    "webview-desktop-stop-windows-recovery": "calf-webview",
    "webview-desktop-security-linux-arm64-windows-pair": "calf-webview",
    "webview-desktop-security-macos-pair": "calf-webview",
    "webview-desktop-policy-macos-recovery": "calf-webview",
    "webview-desktop-tls-windows-recovery": "calf-webview",
    # Recover a Wasm-only fixture/compiler failure without replaying accepted JS.
    "webview-wasm": "calf-webview",
    # Share/clipboard callback boundaries only; unchanged Android results are reusable.
    "share-browser": "calf-share",
    "share-clipboard-native": "calf-share",
    "share-clipboard-native-wasm": "calf-share",
    # Four important public dialog transactions, not an unrelated UI suite replay.
    "ui-date-browser": "calf-ui",
    "ui-date-js": "calf-ui",
    "ui-date-platforms": "calf-ui",
    "ui-date-wasm": "calf-ui",
    "ui-date-android": "calf-ui",
    "ui-dropdown-platforms": "calf-ui",
    "ui-dropdown-android-recovery": "calf-ui",
    # Immutable portable argument/saver/numerical checks without repeating the
    # entire19-module browser suite. Does not change full browser/all coverage.
    "navigation-geo": "calf-navigation,calf-geo",
    # JVM-only allocation/work probes need an immutable desktop run, not replay
    # of unchanged JS/Wasm/Apple/geo or full-library results.
    "navigation-desktop": "calf-navigation",
    # Real JavaFX/window cancellation and reattachment; never replay unrelated
    # passed platform, consumer, native-picker or shared UI suites.
    "webview-desktop": "calf-webview",
    "webview-identity": "calf-webview",
    "webview-identity-linux": "calf-webview",
    "webview-identity-browser": "calf-webview",
    "webview-identity-wasm": "calf-webview",
    "webview-identity-android": "calf-webview",
    "webview-identity-recovery": "calf-webview",
    "webview-identity-remount-recovery": "calf-webview",
    "webview-identity-ios-remount-recovery": "calf-webview",
    "webview-lifetime": "calf-webview",
    "webview-lifetime-android": "calf-webview",
    "webview-lifetime-android-media": "calf-webview",
    "webview-lifetime-linux": "calf-webview",
    "webview-lifetime-macos-arm64": "calf-webview",
    "webview-lifetime-macos-x64": "calf-webview",
    "webview-lifetime-macos-media": "calf-webview",
    "webview-lifetime-windows": "calf-webview",
    "picker-batch": "calf-file-picker",
    "picker-batch-recovery": "calf-file-picker",
    "picker-batch-linux": "calf-file-picker",
    "picker-batch-macos": "calf-file-picker",
    "picker-batch-windows": "calf-file-picker",
    "picker-saver-state": "calf-file-picker",
    "picker-linux-portal": "calf-file-picker",
    "picker-linux-portal-save": "calf-file-picker",
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
    "ios-alert-date-important": "calf-ui",
    "ios-alert-important-recovery": "calf-ui",
    "ios-modal-ownership-batch": "calf-ui",
    "ios-modal-ownership-ipad": "calf-ui",
    "ios-modal-lifecycle-replacement": "calf-ui",
    "ios-modal-lifecycle-replacement-ipad": "calf-ui",
    "ios-date-year-predicate-red": "calf-ui",
    # Foundation/guarded-copy/stream/Coil evidence without replaying unchanged
    # UIKit, picker-dialog, browser, Windows or packaged-consumer execution.
    "ios-io": "calf-io,calf-file-picker-coil",
    "ios-saver-write-failure": "calf-file-picker",
    "ios-picker-batch": "calf-file-picker",
    "ios-picker-recovery": "calf-file-picker",
    "ios-picker-admission": "calf-file-picker",
    "ios-picker-provider-cancellation": "calf-file-picker",
    "ios-share-presentation-disposal": "calf-share",
    "ios-share-remembered-failure-observation": "calf-share",
    "ios-switch-cancellation": "calf-ui",
    "ios-switch-ownership": "calf-ui",
    "ios-slider-numeric": "calf-ui",
    "ios-ui-state": "calf-ui",
    "ios-time-state-recovery": "calf-ui",
    "ios-slider-lifecycle": "calf-ui",
    "ios-slider-remaining": "calf-ui",
    "ios-slider-structure": "calf-ui",
    "ios-slider-tap": "calf-ui",
    "ios-slider-pair-structure": "calf-ui",
    "ios-vector-theme": "calf-ui",
    "ios-vector-theme-recovery": "calf-ui",
    "ios-vector-rendering-recovery": "calf-ui",
    "ios-vector-rendering-iphone-recovery": "calf-ui",
    "ios-vector-native-screen-pair": "calf-ui",
    "ios-slider-recovery": "calf-ui",
    "ios-image-memory": "calf-ui",
    "android-webview": "calf-webview",
    "android-webview-popups": "calf-webview",
    "android-webview-request-state": "calf-webview",
    "android-webview-stop-redirect-recovery": "calf-webview",
    "android-io-oversize": "calf-io",
    "android-saver-identity": "calf-file-picker",
    "android-saver-identity-missing": "calf-file-picker",
}


def matrix(profile: str) -> dict:
    if profile not in PROFILES:
        raise ValueError("Unknown verification profile; arbitrary runner/task input is prohibited")
    if profile == "webview-desktop-stop-windows-recovery":
        if PROFILES[profile] != ("desktop-windows-x64",) or MODULE_SUBSETS.get(profile) != "calf-webview":
            raise ValueError("Windows Stop recovery requires its exact single Windows slot and WebView module")
        inherited = matrix("webview-desktop-request-state-windows-single")["include"]
        canonical = {"slot": "desktop-windows-x64", "suite": "desktop", "runner": "windows-2025",
                     "arch": "x64", "python": "python", "test-modules": "calf-webview",
                     "test-focus": "webview-desktop-request-state-stop"}
        if inherited != [canonical]:
            raise ValueError("Windows Stop recovery refuses canonical runner/architecture/suite/module/field drift")
        row = dict(inherited[0])
        row["test-focus"] = "webview-desktop-stop-windows-recovery"
        return {"include": [row]}
    if profile == desktop_security_plan.WINDOWS_TLS_RECOVERY_PROFILE:
        if PROFILES[profile] != ("desktop-windows-x64",) or MODULE_SUBSETS.get(profile) != "calf-webview":
            raise ValueError("Windows TLS recovery requires its exact single host and WebView module")
        inherited = [row for row in matrix("webview-desktop-security-linux-arm64-windows-pair")["include"]
                     if row["slot"] == "desktop-windows-x64"]
        canonical = {"slot": "desktop-windows-x64", "suite": "desktop", "runner": "windows-2025",
                     "arch": "x64", "python": "python", "test-modules": "calf-webview",
                     "test-focus": "tls-rendering-cookies-policy"}
        if inherited != [canonical]:
            raise ValueError("Windows TLS recovery refuses runner/architecture/suite/module/field drift")
        return {"include": [dict(inherited[0], **{"test-focus": desktop_security_plan.WINDOWS_TLS_RECOVERY_FOCUS})]}
    if profile == desktop_security_plan.POLICY_RECOVERY_PROFILE:
        slots = ("desktop-macos-arm64", "desktop-macos-x64")
        if PROFILES[profile] != slots or MODULE_SUBSETS.get(profile) != "calf-webview":
            raise ValueError("Policy recovery refuses host or module broadening")
        inherited = matrix("webview-desktop-security-macos-pair")["include"]
        if tuple(row["slot"] for row in inherited) != slots:
            raise ValueError("Policy recovery requires both original failed macOS rows")
        return {"include": [dict(row, **{"test-focus": desktop_security_plan.POLICY_RECOVERY_FOCUS})
                            for row in inherited]}
    aliases = {
        "webview-desktop-request-state-linux-pair": ("webview-desktop-request-state", ("desktop-linux-x64", "desktop-linux-arm64")),
        "webview-desktop-request-state-macos-pair": ("webview-desktop-request-state", ("desktop-macos-arm64", "desktop-macos-x64")),
        "webview-desktop-request-state-windows-single": ("webview-desktop-request-state", ("desktop-windows-x64",)),
        "webview-desktop-security-linux-arm64-windows-pair": ("webview-desktop-security-regressions", ("desktop-windows-x64", "desktop-linux-arm64")),
        "webview-desktop-security-macos-pair": ("webview-desktop-security-regressions", ("desktop-macos-arm64", "desktop-macos-x64")),
    }
    if profile in aliases:
        parent, slots = aliases[profile]
        if PROFILES[profile] != slots or MODULE_SUBSETS.get(profile) != "calf-webview":
            raise ValueError("Finite Desktop alias requires its exact slot tuple and WebView module; no arbitrary subset")
        # Inherit every existing canonical row field/focus without narrowing its full branch.
        inherited = [row for row in matrix(parent)["include"] if row["slot"] in slots]
        if tuple(row["slot"] for row in inherited) != slots:
            raise ValueError("Finite Desktop alias requires its exact inherited row order; no omitted or added host")
        desktop_security_plan.validate_rows(desktop_security_plan.ROWS)
        required = {row["slot"]: row for row in desktop_security_plan.ROWS}
        if any(row.get("suite") != "desktop" or row.get("test-modules") != "calf-webview" or
               any(row.get(key) != required[row["slot"]][key] for key in ("runner", "arch"))
               for row in inherited):
            raise ValueError("Finite Desktop alias runner/architecture/suite/module drift; no other-host fallback")
        return {"include": inherited}
    selected = set(PROFILES[profile])
    rows = [dict(slot) for slot in SLOTS if slot["slot"] in selected]
    if profile in MODULE_SUBSETS:
        for row in rows:
            row["test-modules"] = MODULE_SUBSETS[profile]
    if profile in android_batch_plan.BATCHES:
        for row in rows:
            row.update(slot=android_batch_plan.SLOTS[profile], **{"android-batch": profile})
            row.pop("emulator-api")
        return {"include": rows}
    if profile in {row.profile for row in storage_plan.ROWS}:
        storage = storage_plan.row_for(profile)
        for row in rows:
            row.update(slot="android-device-" + profile.removeprefix("android-"), **{
                "emulator-api": str(storage.api), "test-focus": profile, "storage-flavor": storage.flavor,
                "storage-target-sdk": str(storage.target)})
    if profile == "ui-dropdown-platforms":
        for row in rows:
            row["test-focus"] = "material-dropdown-contract"
    if profile == "ui-dropdown-android-recovery":
        for row in rows:
            row["test-focus"] = "material-dropdown-android-dismissal-recovery"
    if profile == "android-webview-request-state":
        for row in rows:
            row["test-focus"] = "android-webview-request-state"
    if profile == "android-webview-stop-redirect-recovery":
        for row in rows:
            row["test-focus"] = "android-webview-stop-redirect-recovery"
    if profile == "android-webview-popups":
        for row in rows:
            row["test-focus"] = "android-webview-popup-policy"
    if profile == "android-navigation-back":
        for row in rows:
            row["test-focus"] = "android-adaptive-navigation-back"
    if profile == "android-geo-ownership":
        for row in rows:
            row["test-focus"] = "geo-android-owner-lifetime"
    if profile == "android-geo-provider":
        for row in rows:
            row["test-focus"] = "geo-android-provider-contracts"
    if profile == "android-geo-prerequisites":
        for row in rows:
            row["test-focus"] = "geo-android-real-prerequisites"
    if profile == "android-permission-demo":
        for row in rows:
            row["test-focus"] = "android-permission-demo-contracts"
    if profile == "android-permission-demo-call-denial-recovery":
        for row in rows:
            row.update(slot="android-device-api35-permission-call-denial-recovery",
                **{"test-focus": "android-permission-demo-call-denial-recovery"})
    if profile == "android-permission-demo-denial-recovery":
        for row in rows:
            row.update(slot="android-device-api35-permission-denial-recovery",
                **{"test-focus": "android-permission-demo-denial-recovery"})
    if profile in {"android-media-selection-api33", "android-media-selection-api34"}:
        api = profile.rsplit("api", 1)[1]
        for row in rows:
            row.update(slot="android-device-api" + api + "-media",
                **{"emulator-api": api, "test-focus": "android-media-selection"})
    if profile == "android-camera-provider":
        for row in rows:
            row["test-focus"] = "android-camera-provider-contracts"
            row["serial-emulator-api"] = "23"
    if profile == "android-camera-provider-minimum":
        for row in rows:
            row.update(slot="android-device-api23-camera", **{"emulator-api": "23", "test-focus": "android-camera-provider-contracts"})
    if profile == "android-camera-no-handler-minimum":
        for row in rows:
            row.update(slot="android-device-api23-camera", **{"emulator-api": "23", "test-focus": "android-camera-no-handler-recovery"})
    if profile == "android-camera-restoration":
        for row in rows:
            row["test-focus"] = "android-camera-real-restoration"
    if profile == "android-camera-restoration-dont-keep":
        for row in rows:
            row["test-focus"] = "android-camera-real-restoration-dont-keep"
    if profile == "android-share-grants":
        for row in rows:
            row["test-focus"] = "android-share-uri-grants"
    if profile in ("share-clipboard-native", "share-clipboard-native-wasm"):
        for row in rows:
            row["test-focus"] = "web-share-clipboard-native-contexts"
    if profile == "webview-content-transitions":
        for row in rows:
            row["test-focus"] = "webview-browser-content-transitions"
    if profile == "webview-request-state":
        for row in rows:
            row["test-focus"] = "webview-browser-request-state"
    if profile == "webview-offline-destination":
        for row in rows:
            row["test-focus"] = "webview-browser-offline-destination"
    if profile == "webview-desktop-request-state":
        focuses = {
            "desktop-linux-x64": "webview-desktop-request-state",
            "desktop-macos-arm64": "webview-desktop-request-state-stop",
            "desktop-windows-x64": "webview-desktop-request-state-stop",
            "desktop-linux-arm64": "webview-desktop-request-state-stop-redirect",
            "desktop-macos-x64": "webview-desktop-request-state-stop",
        }
        for row in rows:
            row["test-focus"] = focuses[row["slot"]]
    if profile == desktop_security_plan.PROFILE:
        desktop_security_plan.validate_rows(desktop_security_plan.ROWS)
        # Linux x64 TLS1 is accepted; keep original metadata for receipts, not replay.
        exact = {row["slot"]: row for row in desktop_security_plan.ROWS
                 if row["slot"] != "desktop-linux-x64"}
        if PROFILES[profile] != tuple(exact) or [row["slot"] for row in rows] != list(exact):
            raise ValueError("Desktop security must select exactly four remaining slots; no accepted TLS replay")
        for row in rows:
            required = exact[row["slot"]]
            if row["suite"] != "desktop" or any(row[key] != required[key] for key in ("runner", "arch")):
                raise ValueError("Desktop security runner/architecture drift; no other-host fallback")
            row["test-focus"] = required["focus"]
    if profile.startswith("webview-identity"):
        for row in rows:
            if profile in {"webview-identity-recovery", "webview-identity-remount-recovery", "webview-identity-ios-remount-recovery"}:
                row["test-focus"] = ("webview-ios-native-remount-recovery" if row["suite"] == "ios" else
                                     "webview-public-remount-recovery" if profile == "webview-identity-remount-recovery" else
                                     "webview-public-identity-recovery")
            else:
                row["test-focus"] = "webview-public-identity-values"
    if profile.startswith("webview-lifetime"):
        order = {"android-device-api35": 0, "desktop-linux-x64": 1, "desktop-macos-arm64": 2,
                 "desktop-macos-x64": 3, "desktop-windows-x64": 4}
        rows.sort(key=lambda row: order[row["slot"]])
        for row in rows:
            row["test-focus"] = ("webview-native-media" if profile == "webview-lifetime-macos-media" else
                                 "webview-android-native-media" if profile == "webview-lifetime-android-media" else "webview-native-lifetime")
    if profile.startswith("picker-batch"):
        for row in rows:
            row["test-focus"] = "picker-native-lifetime"
    if profile == "picker-saver-state":
        for row in rows:
            row["test-focus"] = "picker-desktop-saver-state"
    if profile == "picker-linux-portal":
        for row in rows:
            row["test-focus"] = "picker-linux-portal-functionality"
    if profile == "picker-linux-portal-save":
        for row in rows:
            row["test-focus"] = "picker-linux-portal-save"
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
    if profile == "ios-secure-alert-input":
        for row in rows:
            row["test-focus"] = "ios-native-secure-alert-input"
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
    if profile in ("ios-alert-date-important", "ios-date-year-predicate-red"):
        if (PROFILES[profile] != ("ios-iphone",) or MODULE_SUBSETS.get(profile) != "calf-ui" or
                len(rows) != 1 or tuple(rows[0].get(key) for key in ("slot", "suite", "runner", "arch", "simulator-kind", "test-modules")) !=
                ("ios-iphone", "ios", "macos-26", "arm64", "iphone", "calf-ui")):
            raise ValueError("Important alert/year profiles require the one fixed Arm64 iPhone host and calf-ui module")
        rows[0]["test-focus"] = ("ui-native-alert-date-important" if profile == "ios-alert-date-important" else
                                "ui-native-date-year-predicate-red")
    if profile == "ios-alert-important-recovery":
        canonical = {"slot": "ios-iphone", "suite": "ios", "runner": "macos-26", "arch": "arm64",
                     "python": "python3", "simulator-kind": "iphone", "test-modules": "calf-ui"}
        if (PROFILES[profile] != ("ios-iphone",) or MODULE_SUBSETS.get(profile) != "calf-ui" or
                rows != [canonical]):
            raise ValueError("Important alert recovery requires the exact single Arm64 iPhone row and calf-ui module")
        rows[0]["test-focus"] = "ui-native-alert-important-recovery"
    if profile in ("ios-modal-ownership-batch", "ios-modal-ownership-ipad"):
        kind = "iphone" if profile == "ios-modal-ownership-batch" else "ipad"
        canonical = {"slot": "ios-" + kind, "suite": "ios", "runner": "macos-26", "arch": "arm64",
                     "python": "python3", "simulator-kind": kind, "test-modules": "calf-ui"}
        if PROFILES[profile] != ("ios-" + kind,) or MODULE_SUBSETS.get(profile) != "calf-ui" or rows != [canonical]:
            raise ValueError("Modal ownership batches require one fixed genuine Arm64 UIKit host and calf-ui only")
        rows[0]["test-focus"] = "ui-native-modal-ownership-batch"
    if profile in ("ios-modal-lifecycle-replacement", "ios-modal-lifecycle-replacement-ipad"):
        kind = "iphone" if profile == "ios-modal-lifecycle-replacement" else "ipad"
        canonical = {"slot": "ios-" + kind, "suite": "ios", "runner": "macos-26", "arch": "arm64",
                     "python": "python3", "simulator-kind": kind, "test-modules": "calf-ui"}
        if PROFILES[profile] != ("ios-" + kind,) or MODULE_SUBSETS.get(profile) != "calf-ui" or rows != [canonical]:
            raise ValueError("Modal lifecycle replacement requires one fixed genuine Arm64 UIKit host and calf-ui only")
        rows[0]["test-focus"] = "ui-native-modal-lifecycle-replacement"
    if profile == "ios-saver-write-failure":
        for row in rows:
            row["test-focus"] = "ios-native-saver-write-failure"
    if profile == "ios-picker-batch":
        for row in rows:
            row["test-focus"] = "picker-ios-native-ownership"
    if profile == "ios-picker-recovery":
        for row in rows:
            row["test-focus"] = "picker-ios-native-ownership-recovery"
    if profile == "ios-picker-admission":
        for row in rows:
            row["test-focus"] = "picker-ios-deferred-admission"
    if profile == "ios-picker-provider-cancellation":
        for row in rows:
            row["test-focus"] = "picker-ios-provider-cancellation"
    if profile in ("ios-share-presentation-disposal", "ios-share-remembered-failure-observation"):
        canonical = {"slot": "ios-iphone", "suite": "ios", "runner": "macos-26", "arch": "arm64",
                     "python": "python3", "simulator-kind": "iphone", "test-modules": "calf-share"}
        if (PROFILES[profile] != ("ios-iphone",) or MODULE_SUBSETS.get(profile) != "calf-share" or
                rows != [canonical]):
            raise ValueError("New Share disposal profile requires its exact single genuine iPhone library host")
        rows[0]["test-focus"] = ("share-ios-remembered-failure-observation"
                                  if profile == "ios-share-remembered-failure-observation"
                                  else "share-ios-presentation-disposal")
    if profile == "ios-switch-cancellation":
        for row in rows:
            row["test-focus"] = "ios-native-switch-cancellation"
    if profile == "ios-switch-ownership":
        for row in rows:
            row["test-focus"] = "ios-native-switch-ownership"
    if profile == "ios-slider-numeric":
        for row in rows:
            row["test-focus"] = "ios-native-slider-numeric"
    if profile == "ios-ui-state":
        for row in rows:
            row["test-focus"] = "ios-native-remembered-state"
    if profile == "ios-time-state-recovery":
        for row in rows:
            row["test-focus"] = "ios-native-time-state-recovery"
    if profile == "ios-slider-lifecycle":
        for row in rows:
            row["test-focus"] = "ios-native-slider-input-lifecycle"
    if profile in ("ios-slider-remaining", "ios-slider-structure"):
        for row in rows:
            row["test-focus"] = ("ios-native-slider-input-remaining" if profile == "ios-slider-remaining" else
                                 "ios-native-slider-structure-diagnostic")
    if profile == "ios-vector-theme":
        for row in rows:
            row["test-focus"] = "ios-native-vector-theme-ownership"
    if profile == "ios-vector-theme-recovery":
        for row in rows:
            row["test-focus"] = "ios-native-vector-rendering-recovery"
            row["serial-test-focus"] = "ios-native-system-appearance-recovery"
    if profile in ("ios-vector-rendering-recovery", "ios-vector-rendering-iphone-recovery"):
        for row in rows:
            row["test-focus"] = "ios-native-vector-rendering-recovery"
    if profile == "ios-vector-native-screen-pair":
        for row in rows:
            row["test-focus"] = "ios-native-vector-rendering-recovery"
            row["serial-test-focus"] = "ios-native-vector-rendering-recovery"
            row["serial-simulator-kind"] = "iphone"
    if profile == "ios-slider-recovery":
        for row in rows:
            row["test-focus"] = "ios-native-slider-pair-structure"
            row["serial-test-focus"] = "ios-native-slider-tap-cancellation"
    if profile == "ios-image-memory":
        for row in rows:
            row["test-focus"] = "ios-native-image-memory"
    if profile == "ios-image-memory-darwin":
        for row in rows:
            row["test-focus"] = "ios-native-image-memory-darwin-tools"
    if profile == "ios-image-profile-recovery":
        for row in rows:
            row["test-focus"] = "ios-native-image-allocation-profile-recovery"
    if profile == "ios-webview-lifecycle":
        for row in rows:
            row["test-focus"] = "webview-ios-native-lifecycle"
    if profile == "ios-webview-recovery":
        for row in rows:
            row["test-focus"] = "webview-ios-native-lifecycle-recovery"
    if profile == "ios-webview-request-state":
        for row in rows:
            row["test-focus"] = "webview-ios-native-request-state"
    if profile == "ios-webview-provisional-dns":
        for row in rows:
            row["test-focus"] = "webview-ios-native-provisional-dns"
    if profile == "ios-webview-request-dns":
        for row in rows:
            row["test-focus"] = "webview-ios-native-request-dns"
    if profile in {"ios-slider-tap", "ios-slider-pair-structure"}:
        for row in rows:
            row["test-focus"] = ("ios-native-slider-tap-cancellation" if profile == "ios-slider-tap" else
                                 "ios-native-slider-pair-structure")
    if profile in {"browser-coil-io", "browser-coil-io-js", "browser-coil-io-wasm"}:
        for row in rows:
            row["test-focus"] = "browser-file-read-coil"
    if profile in {"ui-date-platforms", "ui-date-browser", "ui-date-js", "ui-date-wasm", "ui-date-android"}:
        for row in rows:
            row["test-focus"] = "material-date-transaction"
    if profile == "android-io-provider-lifecycle":
        for row in rows:
            row["test-focus"] = "android-io-provider-lifecycle"
    if profile == "android-io-provider-unavailable":
        for row in rows:
            row["test-focus"] = "android-io-provider-unavailable"
    if profile == "android-io-default-decode":
        for row in rows:
            row["test-focus"] = "android-io-default-decode"
    if profile in {"android-io-named-system-providers", "android-io-named-external-storage"}:
        for row in rows:
            row["test-focus"] = profile
    if profile == "android-io-reference-regressions":
        for row in rows:
            row["test-focus"] = "android-io-reference-regressions"
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


def preflight_plans(profile: str, root: Path | None = None) -> dict:
    """Validate the real read-only CLI before requesting expensive host runners.

    Source planning is not Gradle compilation, test execution or release evidence.
    The host job still rechecks its plan against the actual checkout/runtime.
    """
    root = (root or Path(__file__).resolve().parents[2]).resolve()
    verified = []
    rows = matrix(profile)["include"]
    if profile == "ios-appinfo-shape":
        import apple_appinfo_shape_route
        return {"profile": profile, "operation": "plan", "source_only": True,
                "Gradle_builds_executed": 0, "library_tests_executed": 0, "slots": [],
                "sdk_prerequisites": [apple_appinfo_shape_route.plan(root)]}
    # One host, two independent applications. Validate both real CLIs before
    # requesting that host; the second must not be hidden by a first failure.
    selections = [selection for row in rows for selection in
                  ([row, {**row, "test-focus": row["serial-test-focus"]}]
                   if row.get("serial-test-focus") else [row])]
    selections += [{**row, "emulator-api": row["serial-emulator-api"]} for row in rows if row.get("serial-emulator-api")]
    # One related UIKit application followed serially by two Material methods.
    # Different suite/task/report trees: never use the second-UIKit-app mechanism.
    if profile == "ios-alert-date-important":
        selections += [{**rows[0], "suite": "desktop", "test-focus": "ui-material-year-policy-important"}]
    for row in selections:
        if row.get("android-batch"):
            command = [sys.executable, "-B", str(root / "scripts/ci/android_device_batch.py"), "plan",
                       "--batch", row["android-batch"]]
        elif row["suite"] == "android-device":
            # Validate the controller actually invoked by the host, not a different
            # parser which can accept a focus the emulator controller rejects.
            command = [sys.executable, "-B", str(root / "scripts/ci/android_device_tests.py"), "plan",
                       "--api-level", row["emulator-api"], "--output", "build/ci-plan"]
        else:
            command = [sys.executable, "-B", str(root / "scripts/ci/library_tests.py"), "plan",
                       "--suite", row["suite"]]
        modules = row.get("test-modules", "").split(",") if row.get("test-modules") else []
        for module in ([] if row.get("android-batch") else modules):
            command += ["--module", module]
        if row.get("test-focus"):
            command += ["--focus", row["test-focus"]]
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=30, check=False)
        if result.returncode:
            raise ValueError(f"Read-only profile CLI preflight failed for {row['slot']}; exit {result.returncode}")
        plan = json.loads(result.stdout)
        expected = plan.get("expected", []) if isinstance(plan, dict) else []
        if row.get("android-batch") and isinstance(plan, dict):
            if (plan.get("batch") != row["android-batch"] or plan.get("source_only") is not True or
                    [route.get("profile") for route in plan.get("routes", [])] !=
                    list(android_batch_plan.BATCHES[row["android-batch"]])):
                raise ValueError("Read-only Android batch CLI changed the exact route union")
            expected = [item for route in plan["routes"] for item in route["source_suite"]["expected"]]
        if not isinstance(plan, dict) or plan.get("suite") != row["suite"] or not expected:
            raise ValueError(f"Read-only profile CLI returned an invalid/empty plan for {row['slot']}")
        verified.append({"slot": row["slot"], "suite": row["suite"], "command": command,
                         "expected_modules": len(expected), "exit_code": result.returncode})
    return {"profile": profile, "operation": "plan", "source_only": True,
            "Gradle_builds_executed": 0, "library_tests_executed": 0, "slots": verified}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=sorted(PROFILES))
    args = parser.parse_args()
    print(json.dumps(matrix(args.profile), separators=(",", ":")))


if __name__ == "__main__":
    main()
