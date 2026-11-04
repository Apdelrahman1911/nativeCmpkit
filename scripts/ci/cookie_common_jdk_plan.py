# SPDX-License-Identifier: Apache-2.0
"""Source-only finite common/JDK4 command plan; no execution or wire acceptance."""
from __future__ import annotations

import argparse
from pathlib import Path
import json

import cookie_common_jdk_source_projection as history

FOCUS = "common-jdk4"
MODULE = "calf-webview"
TASK = ":calf-webview:desktopTest"
NATIVE_EXCLUSION = "--ktest_negative_gradle_filter=com.mohamedrejeb.calf.ui.web.IosCookieWireAcceptanceTest.*"
PARKED = (
    "com.mohamedrejeb.calf.ui.web.DesktopCookieWireAcceptanceTest",
    "com.mohamedrejeb.calf.ui.web.IosCookieWireAcceptanceTest",
    "com.mohamedrejeb.calf.ui.web.BrowserCookieWireAcceptanceTest",
)
GROUPS = (
    ("com.mohamedrejeb.calf.ui.web.CookieHeaderMultiplicityTest", (
        "requestCookieParsingRetainsDuplicateNamesAndEqualValues",
        "nestedPathAndDomainScopeStillApplyToDuplicateCookieIdentities")),
    ("com.mohamedrejeb.calf.ui.web.DesktopCookieRequestParityTest", (
        "realJdkRequestHeadersAndLibraryResultsKeepDuplicateNamesAcrossPathAndDomainScopes",
        "anOwnedJdkHandlerSelectingOneEqualValueOccurrenceDoesNotInventTwoResults")),
)
SELECTORS = tuple(owner + "." + method for owner, methods in GROUPS for method in methods)


def native_argument_view(arguments: list[str]) -> list[str]:
    """Remove only the one exact parked class argument before unchanged old parsing."""
    if type(arguments) is not list or any(type(value) is not str for value in arguments):
        raise ValueError("Exact native argument list is required")
    if NATIVE_EXCLUSION not in arguments:
        return arguments  # No other flag is removed, normalized, accepted or broadened.
    if arguments.count(NATIVE_EXCLUSION) != 1 or len(set(arguments)) != len(arguments):
        raise ValueError("One unique finite native cookie exclusion is required")
    return [value for value in arguments if value != NATIVE_EXCLUSION]


def validate_native_exclusion_owner(module: str, arguments: list[str]) -> None:
    native_argument_view(arguments)
    if type(module) is not str:
        raise ValueError("Exact owning native module is required")
    if module == MODULE:
        if arguments.count(NATIVE_EXCLUSION) != 1:
            raise ValueError("Ordinary WebView application cannot run a parked cookie wire body")
    elif NATIVE_EXCLUSION in arguments:
        raise ValueError("Native cookie exclusion cannot be transported to a foreign application")


def plan(root: Path, focus: str = FOCUS, module: str = MODULE) -> dict:
    if type(focus) is not str or focus != FOCUS or type(module) is not str or module != MODULE:
        raise ValueError("Only exact common/JDK4 calf-webview source plan is allowed")
    hashes = history.validate_current_sources(root)
    command = ["./gradlew", "--console=plain", "--no-parallel", "--max-workers=1",
               "--init-script", "scripts/ci/fresh-tests.init.gradle.kts",
               "-PnativecmpkitCookieCommonJdkFocus=" + FOCUS, TASK]
    for selector in SELECTORS:
        command.extend(["--tests", selector])
    return {"schema_version": 1, "kind": "source-qualified-common-jdk4-plan-only", "focus": FOCUS,
            "module": MODULE, "task": TASK, "command": command, "selectors": list(SELECTORS),
            "required_original_xml": 2,
            "required_testcases": [{"classname": owner, "name": method + "[desktop]"}
                                   for owner, methods in GROUPS for method in methods],
            "source_hashes": hashes, "parked_native_browser_classes": list(PARKED),
            "common_methods_requested": 2, "jdk_methods_requested": 2, "native_methods_requested": 0,
            "compiler_executions_attested": 0, "test_executions_attested": 0,
            "compiler_input_map_complete": False, "ROOT_shared671_CI668_composition_qualified": False,
            "scope": "One NEW common/JDK4 union only; no accepted native/scalar replay, compilation, wire or issue acceptance."}


def case_inventory(cases: list[dict]) -> bool:
    """Strict future Desktop XML identities; no missing/duplicate/parked/skip success."""
    expected = {(owner, method + "[desktop]") for owner, methods in GROUPS for method in methods}
    return (type(cases) is list and len(cases) == 4 and all(type(case) is dict for case in cases) and
            all(type(case.get(key)) is str for case in cases for key in ("classname", "name", "status")) and
            {(case.get("classname"), case.get("name")) for case in cases} == expected and
            all(case.get("status") == "passed" for case in cases))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=history.ROOT)
    parser.add_argument("--focus", choices=[FOCUS], default=FOCUS)
    parser.add_argument("--module", choices=[MODULE], default=MODULE)
    options = parser.parse_args()
    print(json.dumps(plan(options.root, options.focus, options.module), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
