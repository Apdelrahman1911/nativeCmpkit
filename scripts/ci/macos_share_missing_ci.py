# SPDX-License-Identifier: Apache-2.0
"""Only the missing Share630 timeout JNI method; no native execution on import.

The carried recovery readers, assertions, deadlines and accepted method bodies
are exact ordinary source inputs. Plans and synthetic XML are not native passes.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import macos_share_missing_only as recovery
from ios_popover_anchor_plan import _ordinary_bytes

FOCUS = recovery.JNI_FOCUS
PROFILE = recovery.JNI_PROFILE
MODULE = "calf-share"
TASK = ":calf-share:desktopTest"
CLASS = recovery.JNI_CLASS
SOURCE = recovery.JNI_SOURCE
METHOD = recovery.JNI_METHOD
FILTER = CLASS + "." + METHOD
CONTRACT_KEY = "share630_source_contract"
SCOPE = (
    "One missing actual default DesktopShareOwner/JNI/AppKit timeout method only; "
    "the independent AppKit step requests six missing cases and stops at its first "
    "failure/refusal. Original failed run 41774113636 remains failed. Four accepted "
    "AppKit/JNI bodies are reused, not selected again. No inferred native cause, "
    "visible picker/recipient delivery, stress/instrumentation, other-host, consumer, "
    "API-ABI/security/release or issue-closure certification."
)
SOURCE_SHA256 = {
    SOURCE: "43bcc488ed94c0568b9fba1448c278d8438e6d4c7536ab3035063102820970a2",
    "scripts/ci/macos_share_missing_only.py": "26946c343deec7337310b9ee880c8d5eb39732e5ce7d557dd1630088d5a0a4a8",
    "scripts/ci/macos_share_appkit_lifecycle.py": "b04a67a0a8b80e6d335ee6408e6149db0f3616f353b38b984b6cf39406415455",
    "calf-share/native/tests/appkit_lifecycle/cases.rs": "9e038b83b4e2e4d3d4718869ec05c9eaa198ce1f3c886a38b97b7c13ff83842b",
    "calf-share/native/tests/appkit_lifecycle_main.rs": "b31cad1ca8403b8649b33f43067d778459fe5816099c90c40059465d6b6bbd79",
    "calf-share/native/src/operation.rs": "926b8c1fd41c2039e6bb8a81e9d05333165ed459aa10b9381ab28d140ed62942",
    "calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.desktop.kt": "ac2c199aae4c24359905a9ddeb2951b9babedd2919b035d437087e71ebef64c9",
    "calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/platform/NativeShareBridge.kt": "e146cab08a36acbc356f0283868150ad0ed12b786146bb5fe3a4bf58f82757af",
    "scripts/ci/fresh-tests.init.gradle.kts": "bc14e3ac5105e6a337c896f4f7e88dd565e8862b2b2dc0d8ff055f40ab8cb9d4",
}


def identities() -> list[dict]:
    return recovery.jni_identities()


def _contract() -> dict:
    return {
        "schema_version": 1, "profile": PROFILE, "focus": FOCUS,
        "module": MODULE, "task": TASK, "filter": FILTER,
        "required_testcases": identities(),
        "independent_missing_appkit_cases": list(recovery.MISSING_APPKIT),
        "source_sha256": dict(SOURCE_SHA256),
        "original_reference": recovery.recovery_reference(),
        "native_tests_executed": 0, "scope": "Exact Share630 source admission only; never native acceptance",
    }


def validate_contract(contract: dict) -> None:
    expected = _contract()
    if (type(contract) is not dict or contract != expected or
            type(contract.get("schema_version")) is not int or
            type(contract.get("native_tests_executed")) is not int or
            type(contract.get("original_reference")) is not dict or
            any(type(contract["original_reference"].get(key)) is not bool
                for key in ("original_failures_unwaived", "release_readiness_certified"))):
        raise ValueError("The complete exact missing-only Share630 source contract is required")


def source_contract(root: Path, test_sources: list[str]) -> dict:
    if (type(root) is not type(Path()) or not root.is_absolute() or
            root.absolute() != root.resolve(strict=True) or type(test_sources) is not list or
            any(type(name) is not str for name in test_sources) or test_sources.count(SOURCE) != 1):
        raise ValueError("One ordinary checkout and its exact missing timeout declaration are required")
    source = None
    for name, digest in SOURCE_SHA256.items():
        payload = _ordinary_bytes(root, name)[0]
        if hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError("The unchanged Share630 recovery input differs: " + name)
        if name == SOURCE:
            source = payload.decode("utf-8", errors="strict")
    recovery.jni_validate_source(source, test_sources)
    return _contract()


def validate_host(system: str, machine: str) -> None:
    recovery.jni_validate_host(system, machine)


def outcomes(cases: list[dict], system: str, native_ui_opt_in: bool) -> tuple[list[dict], list[str]]:
    return recovery.jni_outcomes(cases, system, native_ui_opt_in)
