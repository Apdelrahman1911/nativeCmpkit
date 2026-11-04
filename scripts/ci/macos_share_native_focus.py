# SPDX-License-Identifier: Apache-2.0
"""Only three new actual AppKit/JNI coroutine cases, never a full native gate."""
from __future__ import annotations

import re

import native_test_policy as policy

FOCUS = "macos-share-coroutine-lifecycle"
PROFILE = "macos-share-lifecycle"
MODULE = "calf-share"
TASK = ":calf-share:desktopTest"
CLASS = policy.MAC_LIFECYCLE_CLASS
SOURCE = policy.MAC_LIFECYCLE_SOURCE
METHODS = policy.MAC_LIFECYCLE_METHODS
SCOPE = (
    "Three new actual default DesktopShareOwner/JNI/AppKit coroutine methods only: "
    "same-worker responsiveness and cancellation, real native deadline/re-admission and "
    "independent single-flight rejection. Native retained ownership is not visible picker, "
    "recipient delivery, instrumentation/ASan/stress, all-host, packaged consumer, "
    "API-ABI/security or release certification. No accepted old native method replay."
)


def validate_source(source: str, test_sources: list[str]) -> None:
    package, classname = CLASS.rsplit(".", 1)
    methods = re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", source)
    if (SOURCE not in test_sources or methods != list(METHODS) or
            "package " + package not in source or "class " + classname not in source or
            re.search(r"@(Ignore|Disabled|IgnoredTest)\b", source) or
            "DesktopShareOwner(scope," not in source or
            "NativeShareBridge.beginShareSheet(" not in source or
            "NativeShareBridge.liveUiOperationCount()" not in source):
        raise ValueError("AppKit coroutine focus needs the exact three genuine default-owner declarations")


def identities() -> list[dict]:
    return [{"classname": CLASS, "name": method + "[desktop]"} for method in METHODS]


def validate_host(system: str, machine: str) -> None:
    if policy.canonical_host(system) != "macos" or machine.lower() not in {"arm64", "aarch64"}:
        raise ValueError("AppKit lifecycle focus requires the actual fixed macos-arm64 host")


def outcomes(cases: list[dict], system: str, native_ui_opt_in: bool) -> tuple[list[dict], list[str]]:
    scenarios, errors = policy.macos_lifecycle_cases(cases, system, native_ui_opt_in)
    allowed = {(CLASS, name) for method in METHODS for name in (method, method + "[desktop]")}
    if len(cases) != len(METHODS) or any((case["classname"], case["name"]) not in allowed for case in cases):
        errors.append("AppKit coroutine XML must contain only the exact three selected native methods")
    if policy.canonical_host(system) != "macos":
        errors.append("An opposite-host skip is not a native pass for the fixed AppKit focus")
    return scenarios, errors
