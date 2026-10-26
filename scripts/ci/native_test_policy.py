"""Exact, source-bound native JNI scenario eligibility; never a general skip list.

Only two logically host-inapplicable cases may remain skipped. A required macOS
AppKit case must execute with explicit GUI opt-in; headless/opt-out is not N/A.
Single-host evidence cannot establish the complete cross-host native matrix.
"""
from __future__ import annotations

MODULE = "calf-share"
CLASS = "com.mohamedrejeb.calf.share.platform.NativeShareBridgeTest"
SOURCE = "calf-share/src/desktopTest/kotlin/com/mohamedrejeb/calf/share/platform/NativeShareBridgeTest.kt"
ALL_HOSTS = (
    "nativeAbiAndDiagnosticsLoadOnTheActualHost",
    "borrowedNativeWindowPointersAreRejectedWithoutDereference",
)
NON_MAC = "unsupportedHostRequestsAndCancellationNeverRetainNativeOwners"
MAC_GUI = "macOsPickerCancellationReleasesRealMainThreadOwners"
REQUIRED_CASES = (*ALL_HOSTS, NON_MAC, MAC_GUI)


def canonical_host(system: str) -> str:
    aliases = {"linux": "linux", "windows": "windows", "win32": "windows",
               "darwin": "macos", "mac": "macos", "macos": "macos", "mac os x": "macos"}
    if not isinstance(system, str) or system.strip().lower() not in aliases:
        raise ValueError("Unrecognized native scenario host; do not guess applicability")
    return aliases[system.strip().lower()]


def apply(module: str, suite: str, cases: list[dict], system: str,
          native_ui_opt_in: bool) -> tuple[list[dict], list[str]]:
    if module != MODULE or suite != "desktop":
        return [], []
    host = canonical_host(system)
    scenarios, errors = [], []
    for method in REQUIRED_CASES:
        matching = [case for case in cases if case["classname"] == CLASS and
                    case["name"] in {method, method + "[desktop]"}]
        applicable = method in ALL_HOSTS or (method == NON_MAC and host != "macos") or (method == MAC_GUI and host == "macos")
        scenario = {"classname": CLASS, "method": method, "source": SOURCE, "host": host,
                    "required_on_host": applicable, "native_ui_opt_in_requested": native_ui_opt_in if method == MAC_GUI and applicable else None}
        if len(matching) != 1:
            errors.append(f"Native scenario {method} must appear exactly once, including explicit host N/A evidence")
            scenario["disposition"] = "missing-or-duplicate"
        else:
            case = matching[0]
            if not applicable:
                if case["status"] != "skipped":
                    errors.append(f"Host-inapplicable native scenario {method} must be reported N/A, not executed or counted passed")
                    scenario["disposition"] = "invalid-host-outcome"
                else:
                    case["disposition"] = "not-applicable"
                    case["not_applicable_reason"] = "AppKit-only scenario on non-macOS" if method == MAC_GUI else "Unavailable-native-sharing contract does not apply to macOS"
                    scenario["disposition"] = "not-applicable"
            else:
                scenario["disposition"] = "required-executed" if case["status"] == "passed" else "required-not-passed"
                if case["status"] != "passed":
                    errors.append(f"Required native scenario {method} did not pass; skipped/headless/opt-out is not N/A")
                if method == MAC_GUI and native_ui_opt_in is not True:
                    errors.append("The required macOS AppKit GUI scenario needs explicit NATIVECMPKIT_NATIVE_UI_TESTS=true")
        scenarios.append(scenario)
    return scenarios, errors
