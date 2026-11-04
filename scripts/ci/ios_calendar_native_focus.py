# SPDX-License-Identifier: Apache-2.0
"""Five genuine EventKit configuration regressions, never consent/release proof."""
from __future__ import annotations

import re

FOCUS = "permission-ios-calendar-configuration"
PROFILE = "permissions-ios-calendar-configuration"
MODULE = "calf-permissions/calendar"
TASK = ":calf-permissions:calf-permissions-calendar:iosSimulatorArm64Test"
CLASS = "com.mohamedrejeb.calf.permissions.helper.NativeCalendarConfigurationTest"
SOURCE = MODULE + "/src/iosTest/kotlin/com/mohamedrejeb/calf/permissions/helper/NativeCalendarConfigurationTest.kt"
METHODS = (
    "nativeSelectorsMatchTheRunningIOSVersionAndSelectedRequestKind",
    "passivePublicHelpersMatchActualEventKitWithoutPromptingOrChangingAuthorization",
    "freshUnconfiguredPublicRequestsFailOnceWithoutEnteringEventKitPrivacy",
    "backgroundEntryAndReentrantConfigurationFailuresAreMainConfinedAndRecoverable",
    "nativeBundleLookupHonorsLocalizedPurposeStringsAndRejectsOtherModeKeys",
)
SCOPE = (
    "Five new actual library EventKit/Darwin/NSBundle methods only: running selector availability, "
    "registered public helpers, fresh NotDetermined/no-purpose-key refusal, background/reentrant Main "
    "entry and localized owned fixture cleanup. No consent/privacy prompt, configured grant/upgrade, "
    "Settings/old OS/minimum linking, sample substitution, accepted-suite replay or release certification."
)


def validate_source(source: str, test_sources: list[str]) -> None:
    package, classname = CLASS.rsplit(".", 1)
    methods = re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", source)
    if (SOURCE not in test_sources or methods != list(METHODS) or
            "package " + package not in source or "class " + classname not in source or
            re.search(r"@(Ignore|Disabled|IgnoredTest)\b", source) or
            "PermissionDelegateRegistry.getDelegate(" not in source or
            "requireFreshUnconfiguredProcess()" not in source):
        raise ValueError("Calendar configuration requires its exact five real native declarations")


def identities() -> list[dict]:
    return [{"classname": "iosSimulatorArm64Test." + CLASS,
             "name": method + "[iosSimulatorArm64]"} for method in METHODS]


def outcomes(cases: list[dict], system: str) -> tuple[list[dict], list[str]]:
    """No skipped/N/A, duplicate or foreign-target alternative to native results."""
    host_ok = isinstance(system, str) and system.lower() in {"darwin", "macos", "mac os x"}
    errors, scenarios = [], []
    if not host_ok:
        errors.append("Calendar configuration requires actual Apple-host native execution")
    expected = identities()
    if len(cases) != len(expected) or any(
            not any((case["classname"], case["name"]) == (item["classname"], item["name"])
                    for item in expected) for case in cases):
        errors.append("Calendar XML must contain only the exact five selected native methods")
    for item in expected:
        matching = [case for case in cases if
                    (case["classname"], case["name"]) == (item["classname"], item["name"])]
        passed = len(matching) == 1 and host_ok and matching[0]["status"] == "passed"
        if not passed:
            errors.append("Calendar native method must pass exactly once: " + item["name"])
        scenarios.append({**item, "source": SOURCE, "task": "iosSimulatorArm64Test",
                          "target": "iosSimulatorArm64", "required_on_host": True,
                          "disposition": "required-executed" if passed else "required-not-passed"})
    return scenarios, errors
