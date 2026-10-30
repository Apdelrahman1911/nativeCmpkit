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
    "browser-coil-io": ("browser-js", "browser-wasm"),
    "browser-coil-io-js": ("browser-js",),
    "browser-coil-io-wasm": ("browser-wasm",),
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
    "ios-date-bounds": ("ios-iphone",),
    "ios-date-replacement": ("ios-iphone",),
    "ios-date-compact": ("ios-iphone",),
    "ios-dates-important": ("ios-iphone",),
    "ios-io": ("ios-iphone",),
    "ios-saver-write-failure": ("ios-iphone",),
    "ios-picker-batch": ("ios-iphone",),
    "ios-picker-recovery": ("ios-iphone",),
    "ios-picker-admission": ("ios-iphone",),
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
    "ios-webview-lifecycle": ("ios-iphone",),
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
    "ios-webview-lifecycle": "calf-webview",
    "ios-image-memory-darwin": "calf-ui",
    # Public Compose/DOM picker lifetime only; no replay of unchanged IO/other suites.
    "browser-picker": "calf-file-picker",
    "browser-coil-io": "calf-file-picker-coil",
    "browser-coil-io-js": "calf-file-picker-coil",
    "browser-coil-io-wasm": "calf-file-picker-coil",
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
    # Foundation/guarded-copy/stream/Coil evidence without replaying unchanged
    # UIKit, picker-dialog, browser, Windows or packaged-consumer execution.
    "ios-io": "calf-io,calf-file-picker-coil",
    "ios-saver-write-failure": "calf-file-picker",
    "ios-picker-batch": "calf-file-picker",
    "ios-picker-recovery": "calf-file-picker",
    "ios-picker-admission": "calf-file-picker",
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
    if profile == "ios-webview-lifecycle":
        for row in rows:
            row["test-focus"] = "webview-ios-native-lifecycle"
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
    # One host, two independent applications. Validate both real CLIs before
    # requesting that host; the second must not be hidden by a first failure.
    selections = [selection for row in rows for selection in
                  ([row, {**row, "test-focus": row["serial-test-focus"]}]
                   if row.get("serial-test-focus") else [row])]
    for row in selections:
        command = [sys.executable, "-B", str(root / "scripts/ci/library_tests.py"), "plan",
                   "--suite", row["suite"]]
        modules = row.get("test-modules", "").split(",") if row.get("test-modules") else []
        for module in modules:
            command += ["--module", module]
        if row.get("test-focus"):
            command += ["--focus", row["test-focus"]]
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=30, check=False)
        if result.returncode:
            raise ValueError(f"Read-only profile CLI preflight failed for {row['slot']}; exit {result.returncode}")
        plan = json.loads(result.stdout)
        if not isinstance(plan, dict) or plan.get("suite") != row["suite"] or not plan.get("expected"):
            raise ValueError(f"Read-only profile CLI returned an invalid/empty plan for {row['slot']}")
        verified.append({"slot": row["slot"], "suite": row["suite"], "command": command,
                         "expected_modules": len(plan["expected"]), "exit_code": result.returncode})
    return {"profile": profile, "operation": "plan", "source_only": True,
            "Gradle_builds_executed": 0, "library_tests_executed": 0, "slots": verified}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=sorted(PROFILES))
    args = parser.parse_args()
    print(json.dumps(matrix(args.profile), separators=(",", ":")))


if __name__ == "__main__":
    main()
