# SPDX-License-Identifier: Apache-2.0
"""Finite Share630 recovery identities and bounded failure evidence, never native passes.

The once-acquired originals remain failed. These readers do not run native queries,
infer window activation, expose panic/error bodies or waive an owning assertion.
"""
from __future__ import annotations

import posixpath
import re

ORIGINAL_RUN = 41774113636
ORIGINAL_SOURCE = "6fb368eb77a0863cd3d725f75e85d59b41caee71"
APPKIT_CASES = (
    "cancel_before_dispatch", "no_key_window", "missing_content_view",
    "real_picker_cancel", "controlled_picker_dismissal",
    "controlled_success_duplicate_late", "controlled_service_failure",
    "bounded_concurrent_requests",
)
ACCEPTED_APPKIT = APPKIT_CASES[:2]
MISSING_APPKIT = APPKIT_CASES[2:]
JNI_CLASS = "com.mohamedrejeb.calf.share.MacOsShareCoroutineLifecycleTest"
JNI_SOURCE = "calf-share/src/desktopTest/kotlin/com/mohamedrejeb/calf/share/MacOsShareCoroutineLifecycleTest.kt"
JNI_METHOD = "realNativeTimeoutReportsOnceWithoutFallbackAndAllowsFreshRequestAfterMainCleanup"
JNI_FOCUS = "macos-share-timeout-retention-recovery"
JNI_PROFILE = "macos-share-missing-lifecycle"
ACCEPTED_JNI = (
    "independentRealNativeOwnersRejectOverlapWithoutReplacingTheRetainedRequest",
    "cancellingRetainedAppKitRequestFreesOwnersAndDoesNotOccupySingleCoroutineWorker",
)
CASES_SOURCE = "calf-share/native/tests/appkit_lifecycle/cases.rs"
CASES_SHA = "9e038b83b4e2e4d3d4718869ec05c9eaa198ce1f3c886a38b97b7c13ff83842b"
OPERATION_SOURCE = "calf-share/native/src/operation.rs"
OPERATION_SHA = "926b8c1fd41c2039e6bb8a81e9d05333165ed459aa10b9381ab28d140ed62942"
MAX_STDERR = 4096
MAX_JNI_OUTPUT = 32768


def appkit_selection(case: str | None = None, *, missing_only: bool = False) -> tuple[str, ...]:
    if type(missing_only) is not bool or (case is not None and missing_only):
        raise ValueError("require-one-exact-appkit-recovery-selection")
    if missing_only:
        return MISSING_APPKIT
    if case is None:
        return APPKIT_CASES  # Retain the original default8 contract, not a recovery request.
    if type(case) is not str or case not in MISSING_APPKIT:
        raise ValueError("refuse-accepted-unknown-or-stress-appkit-replay")
    return (case,)


def validate_population(cases: tuple[str, ...]) -> None:
    if type(cases) is not tuple or not (cases == APPKIT_CASES or cases == MISSING_APPKIT or
                                     (len(cases) == 1 and cases[0] in MISSING_APPKIT)):
        raise ValueError("require-fixed-default-single-or-six-appkit-population")


def recovery_reference() -> dict:
    return {"original_run": ORIGINAL_RUN, "original_source": ORIGINAL_SOURCE,
            "unchanged_passed_appkit_cases_reused_not_replayed": list(ACCEPTED_APPKIT),
            "unchanged_passed_jni_methods_reused_not_replayed": list(ACCEPTED_JNI),
            "original_failures_unwaived": True, "release_readiness_certified": False}


def jni_identities() -> list[dict]:
    return [{"classname": JNI_CLASS, "name": JNI_METHOD + "[desktop]"}]


def jni_validate_source(source: str, test_sources: list[str]) -> None:
    methods = re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", source)
    expected = [ACCEPTED_JNI[1], JNI_METHOD, ACCEPTED_JNI[0]]
    if (JNI_SOURCE not in test_sources or methods != expected or
            "package com.mohamedrejeb.calf.share" not in source or
            "class MacOsShareCoroutineLifecycleTest" not in source or
            re.search(r"@(Ignore|Disabled|IgnoredTest)\b", source) or
            "DesktopShareOwner(scope," not in source or
            "desktopTimeoutMillis = 2_000, allowClipboardFallback = false" not in source or
            "awaitTimeoutRetention(fixture, RetentionPhase.InitialTimeout)" not in source or
            "awaitTimeoutRetention(fixture, RetentionPhase.ReplacementAfterTimeout)" not in source or
            "NativeShareBridge.beginShareSheet(" not in source):
        raise ValueError("require-genuine-unchanged-deadline-timeout-recovery-source")


def jni_validate_host(system: str, machine: str) -> None:
    if type(system) is not str or type(machine) is not str or system.lower() not in {
            "darwin", "macos", "mac os x"} or machine.lower() not in {"arm64", "aarch64"}:
        raise ValueError("require-actual-macos-arm64-timeout-recovery-host")


def jni_outcomes(cases: list[dict], system: str, native_ui_opt_in: bool) -> tuple[list[dict], list[str]]:
    expected = jni_identities()[0]
    errors = []
    if type(system) is not str or system.lower() not in {"darwin", "macos", "mac os x"}:
        errors.append("timeout-recovery-opposite-host-is-not-a-native-pass")
    if native_ui_opt_in is not True:
        errors.append("timeout-recovery-native-ui-optin-is-required")
    if (len(cases) != 1 or cases[0].get("classname") != expected["classname"] or
            cases[0].get("name") not in {JNI_METHOD, expected["name"]} or
            cases[0].get("status") != "passed"):
        errors.append("timeout-recovery-needs-only-the-one-real-passed-method")
    return ([{"classname": JNI_CLASS, "method": JNI_METHOD, "host": "macos",
              "required_on_host": True, "native_ui_opt_in_requested": native_ui_opt_in is True,
              "disposition": "required-executed" if not errors else "required-not-passed",
              "source": JNI_SOURCE, "task": "desktopTest"}], errors)


# Exact unchanged native source assertions, not general panic-message scraping.
# The printed numeric thread token is deliberately not interpreted as a process ID.
_HEADER = re.compile(r"thread 'main'(?: \([0-9]{1,20}\))? panicked at ([^\r\n]+):([0-9]{1,5}):[0-9]{1,5}:\Z")
_PHASES = {
    (61, "Owned AppKit window did not become key"): "owned-window-key-wait",
    (213, "Owned window needs its original content view"): "owned-original-content-view",
    (215, "The real nil-content-view precondition did not hold"): "real-nil-content-view-precondition",
    (53, "The actual native operation must be admitted"): "native-admission",
    (61, "Native operation never became terminal"): "native-terminal-wait",
    (151, "assertion `left == right` failed"): "native-terminal-result-assertion",
    (61, "Queued Main cleanup did not complete"): "main-cleanup-wait",
    (61, "An actual Objective-C delegate or Rust completion still has a strong owner"): "weak-owner-release-wait",
}
_RESULTS = {-1: "Pending", 0: "Success", 1: "Dismissed", 2: "Unavailable", 3: "Failed"}


def unavailable(reason: str) -> dict:
    return {"available": False, "reason": reason, "exact_native_cause_verified": False,
            "raw_payload_exported": False, "native_queries_repeated": False}


def appkit_failure(stderr: bytes, *, source_hash: str, operation_hash: str | None,
                   source_absolute: str, failed_case: str) -> dict:
    """Read one bounded original stream; unknown/ambiguous text remains unavailable."""
    if failed_case != "missing_content_view" or source_hash != CASES_SHA:
        return unavailable("unqualified-source-or-failed-case")
    if type(stderr) is not bytes or not stderr:
        return unavailable("not-emitted")
    if len(stderr) > MAX_STDERR:
        return unavailable("private-stream-outside-observation-bound")
    try:
        lines = stderr.decode("utf-8", errors="strict").splitlines()
    except UnicodeDecodeError:
        return unavailable("private-stream-not-utf8")
    headers = [(i, _HEADER.fullmatch(line)) for i, line in enumerate(lines) if "panicked at " in line]
    if len(headers) != 1 or headers[0][1] is None:
        return unavailable("absent-or-ambiguous-original-panic-frame")
    index, frame = headers[0]
    allowed_paths = {CASES_SOURCE, "tests/appkit_lifecycle/cases.rs", posixpath.normpath(source_absolute)}
    if posixpath.normpath(frame[1]) not in allowed_paths or index + 1 >= len(lines):
        return unavailable("original-panic-source-not-qualified")
    line = int(frame[2])
    phase = _PHASES.get((line, lines[index + 1]))
    if phase is None:
        return unavailable("original-assertion-not-in-fixed-source-catalogue")
    result = {"available": True, "phase": phase, "source": CASES_SOURCE,
              "source_sha256": CASES_SHA, "line": line,
              "exact_native_cause_verified": False, "raw_payload_exported": False,
              "native_queries_repeated": False, "raw_control_or_weak_readings_exported": False,
              "terminal_result_enum": "unavailable"}
    if phase == "native-terminal-result-assertion" and operation_hash == OPERATION_SHA:
        pair = lines[index + 2:index + 4]
        if len(pair) == 2:
            left = re.fullmatch(r"\s*left: (-?[0-9]+)", pair[0])
            right = re.fullmatch(r"\s*right: (-?[0-9]+)", pair[1])
            if left is not None and right is not None and left[1] == "2" and int(right[1]) in _RESULTS:
                result["terminal_result_enum"] = _RESULTS[int(right[1])]
                result["result_enum_source_sha256"] = OPERATION_SHA
    return result


_COUNT = r"(?:[0-9]|[1-5][0-9]|6[0-4]|unavailable|out-of-range)"
_EMITTED = r"(?:[0-9]|[1-5][0-9]|6[0-4]|overflow)"
_OUTCOME = r"(?:Presented|Selected|Completed|CopiedToClipboard|Dismissed|Busy|Unavailable|Failed\.(?:InvalidContent|Configuration|Permission|Platform|TimedOut)|not-emitted|multiple|overflow)"
_JNI = re.compile(r"NATIVECMPKIT_SHARE_RETENTION phase=(InitialTimeout|ReplacementAfterTimeout) "
                  r"active=(" + _COUNT + r") live=(" + _COUNT + r") outcome=(" + _OUTCOME +
                  r") result_count=(" + _EMITTED + r") failure_count=(" + _EMITTED + r")\Z")


def jni_failure(output: bytes, *, expected_phase: str) -> dict:
    """Only fixed marker fields; missing/short-circuited observations are never zero."""
    if expected_phase not in {"InitialTimeout", "ReplacementAfterTimeout"}:
        return unavailable("unknown-original-retention-phase")
    if type(output) is not bytes or len(output) > MAX_JNI_OUTPUT:
        return unavailable("jni-output-outside-observation-bound")
    try:
        markers = [line for line in output.decode("utf-8", errors="strict").splitlines()
                   if line.startswith("NATIVECMPKIT_SHARE_RETENTION")]
    except UnicodeDecodeError:
        return unavailable("jni-output-not-utf8")
    if not markers:
        return unavailable("not-emitted")
    if len(markers) != 1:
        return unavailable("duplicate-retention-markers")
    match = _JNI.fullmatch(markers[0])
    if match is None or match[1] != expected_phase:
        return unavailable("retention-marker-shape-or-phase-mismatch")
    active, live, outcome, count, failures = match.groups()[1:]
    if (active == "1" and live == "1" or
            active != "1" and live != "unavailable" or
            count == "0" and outcome != "not-emitted" or
            count == "1" and outcome in {"not-emitted", "multiple", "overflow"} or
            count == "overflow" and outcome != "overflow" or
            count not in {"0", "1", "overflow"} and outcome != "multiple"):
        return unavailable("retention-marker-inconsistent-original-query")
    return {"available": True, "phase": match[1], "active": active, "live": live,
            "outcome": outcome, "result_count": count, "failure_count": failures,
            "raw_payload_exported": False, "native_queries_repeated": False,
            "exact_native_cause_verified": False}
