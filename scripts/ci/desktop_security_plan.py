#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Finite missing-only BUILD-002 source selection; not native/security acceptance.

Existing cookie, policy and media methods run only on hosts missing those cells.
The new TLS/rendering method remains unaccepted until fresh source/results review.
#64 request/Stop/redirect selections are independent and never selected here.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import stat

SECURITY_CLASS = "com.mohamedrejeb.calf.ui.web.DesktopWebViewTlsRenderingAcceptanceTest"
SECURITY_METHOD = "trustedHttpsPaintsTwoAuthoredDocumentsAndUntrustedCertificateFailsBeforeHttpOnTheSameOwner"
COOKIE_CLASS = "com.mohamedrejeb.calf.ui.web.JavaFxCookieIntegrationTest"
COOKIE_METHOD = "realNativeLoginSurvivesLibraryCookieReadsAndHttpOnlyNeverLeaksIntoDocumentCookie"
POLICY_CLASS = "com.mohamedrejeb.calf.ui.web.DesktopWebViewIdentityAcceptanceTest"
POLICY_METHOD = "actualFxTypedValuesOffMainAndThrowingOrDetachedCallbacksAreExactlyOnce"
MEDIA_CLASS = "com.mohamedrejeb.calf.ui.web.DesktopWebViewLifetimeTest"
MEDIA_METHOD = "disposingARealWindowClosesItsSlowConnectionAndStopsTheLiveMediaDocument"
SPECS = {
    "tls-rendering": (SECURITY_CLASS, SECURITY_METHOD),
    "cookie": (COOKIE_CLASS, COOKIE_METHOD),
    "policy": (POLICY_CLASS, POLICY_METHOD),
    "media": (MEDIA_CLASS, MEDIA_METHOD),
}
ROWS = (
    {"slot": "desktop-linux-x64", "system": "Linux", "arch": "x64", "runner": "ubuntu-24.04", "focus": "tls-rendering", "selected": ("tls-rendering",)},
    {"slot": "desktop-macos-arm64", "system": "Darwin", "arch": "arm64", "runner": "macos-26", "focus": "tls-rendering-cookies-policy", "selected": ("tls-rendering", "cookie", "policy")},
    {"slot": "desktop-windows-x64", "system": "Windows", "arch": "x64", "runner": "windows-2025", "focus": "tls-rendering-cookies-policy", "selected": ("tls-rendering", "cookie", "policy")},
    {"slot": "desktop-linux-arm64", "system": "Linux", "arch": "arm64", "runner": "ubuntu-24.04-arm", "focus": "tls-rendering-cookies-policy-media", "selected": ("tls-rendering", "cookie", "policy", "media")},
    {"slot": "desktop-macos-x64", "system": "Darwin", "arch": "x64", "runner": "macos-26-intel", "focus": "tls-rendering-cookies-policy", "selected": ("tls-rendering", "cookie", "policy")},
)
EXPECTED_SELECTED = {
    ("Linux", "x64"): ("tls-rendering",),
    ("Darwin", "arm64"): ("tls-rendering", "cookie", "policy"),
    ("Windows", "x64"): ("tls-rendering", "cookie", "policy"),
    ("Linux", "arm64"): ("tls-rendering", "cookie", "policy", "media"),
    ("Darwin", "x64"): ("tls-rendering", "cookie", "policy"),
}
PROFILE = "webview-desktop-security-regressions"
MAX_PARALLEL = 2


def validate_rows(rows: tuple[dict, ...]) -> None:
    if len(rows) != 5 or len({row["slot"] for row in rows}) != 5:
        raise ValueError("Exactly five distinct existing Desktop slots are required")
    seen = set()
    for row, original in zip(rows, ROWS):
        identity = (row["system"], row["arch"])
        if (identity in seen or identity not in EXPECTED_SELECTED or
                tuple(row["selected"]) != EXPECTED_SELECTED[identity] or
                any(row[key] != original[key] for key in ("slot", "system", "arch", "runner", "focus"))):
            raise ValueError("Missing-only host/focus/runner inventory changed; no accepted replay or fallback")
        seen.add(identity)
    if seen != set(EXPECTED_SELECTED):
        raise ValueError("Do not omit a literal host or add another host")


def selection(system: str, architecture: str) -> dict:
    if not isinstance(system, str) or not isinstance(architecture, str):
        raise ValueError("Actual system and architecture strings are required")
    arch = architecture.lower()
    arch = {"amd64": "x64", "x86_64": "x64", "aarch64": "arm64"}.get(arch, arch)
    row = next((row for row in ROWS if (row["system"], row["arch"]) == (system, arch)), None)
    if row is None:
        raise ValueError("Unsupported actual Desktop host; no other-host or full-suite fallback")
    return {
        **row,
        "test_modules": ("calf-webview",),
        "task": ":calf-webview:desktopTest",
        "isolation_property": "-PnativecmpkitDesktopSecurityFocus=" + row["focus"],
        "selectors": tuple(SPECS[key][0] + "." + SPECS[key][1] for key in row["selected"]),
        "required_testcases": tuple({"classname": SPECS[key][0], "name": SPECS[key][1] + "[desktop]"} for key in row["selected"]),
        "required_original_xml": len(row["selected"]),
    }


def matrix() -> dict:
    validate_rows(ROWS)
    return {"profile": PROFILE, "max_parallel": MAX_PARALLEL,
            "include": [selection(row["system"], row["arch"]) for row in ROWS]}


FOCUSES = tuple(dict.fromkeys(row["focus"] for row in ROWS))
SOURCE_PATHS = {'tls-rendering': 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewTlsRenderingAcceptanceTest.kt', 'cookie': 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/JavaFxCookieIntegrationTest.kt', 'policy': 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewIdentityAcceptanceTest.kt', 'media': 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewLifetimeTest.kt'}
SOURCE_SHA256 = {'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewTlsRenderingAcceptanceTest.kt': '00698c638a729549c890240b000e64cbd88be9f6ac32d4ca067b304b1443187c', 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/OwnedDesktopTlsFixture.kt': 'a7c8b3fe15c94ef5f30ccb648cdbe5a52770aad1b0bf5eeed6415a802a05c703', 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/JavaFxCookieIntegrationTest.kt': 'd5b1da0a1b2c18c65cf4fff35b63d07138f0f631e6cd8b64464c9ebeeaa02183', 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewIdentityAcceptanceTest.kt': '2811d91948312b9626f9b3f99112de8bffaa26100405c402bba7989e02248e96', 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewLifetimeTest.kt': 'aa57d7b6475b3b2b5931af90e22a77440e71a5fae3fe5edf2d31874facac8456'}
TLS_HELPER = "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/OwnedDesktopTlsFixture.kt"
BUILD_SOURCE = "calf-webview/build.gradle.kts"
INIT_SCRIPT = "scripts/ci/desktop-security.init.gradle.kts"
INIT_SCRIPT_SHA256 = 'bbe38d5d5ffc53cb56258b2996d41a3015f41237fb782c9b701376bcc62579b1'
ISOLATION_BLOCK = 'val desktopSecurityClass = "com.mohamedrejeb.calf.ui.web.DesktopWebViewTlsRenderingAcceptanceTest"\nval desktopSecurityMethod = "trustedHttpsPaintsTwoAuthoredDocumentsAndUntrustedCertificateFailsBeforeHttpOnTheSameOwner"\nval desktopCookieSelector = "com.mohamedrejeb.calf.ui.web.JavaFxCookieIntegrationTest.realNativeLoginSurvivesLibraryCookieReadsAndHttpOnlyNeverLeaksIntoDocumentCookie"\nval desktopPolicySelector = "com.mohamedrejeb.calf.ui.web.DesktopWebViewIdentityAcceptanceTest.actualFxTypedValuesOffMainAndThrowingOrDetachedCallbacksAreExactlyOnce"\nval desktopMediaSelector = "com.mohamedrejeb.calf.ui.web.DesktopWebViewLifetimeTest.disposingARealWindowClosesItsSlowConnectionAndStopsTheLiveMediaDocument"\nval desktopSecurityFocus = providers.gradleProperty("nativecmpkitDesktopSecurityFocus").orNull\nval desktopSecuritySelectors = when (desktopSecurityFocus) {\n    null -> emptyList()\n    "tls-rendering" -> listOf("$desktopSecurityClass.$desktopSecurityMethod")\n    "tls-rendering-cookies-policy" -> listOf("$desktopSecurityClass.$desktopSecurityMethod", desktopCookieSelector, desktopPolicySelector)\n    "tls-rendering-cookies-policy-media" -> listOf("$desktopSecurityClass.$desktopSecurityMethod", desktopCookieSelector, desktopPolicySelector, desktopMediaSelector)\n    else -> error("Unknown finite Desktop security focus; no arbitrary class or whole-suite fallback")\n}\n\ntasks.withType<Test>().matching { it.name == "desktopTest" }.configureEach {\n    if (desktopSecurityFocus == null) {\n        // Never auto-enable a process-global test trust lease in an ordinary worker.\n        filter { excludeTestsMatching(desktopSecurityClass) }\n    } else {\n        // Each selected class has exactly one selected method; no second class can\n        // reuse HTTP2Loader\'s static fixture-trusted HttpClient or a cookie handler.\n        maxParallelForks = 1\n        forkEvery = 1L\n        systemProperty("nativecmpkit.desktop.security.worker", "one-selected-class")\n        filter {\n            setIncludePatterns(*desktopSecuritySelectors.toTypedArray())\n            isFailOnNoMatchingTests = true\n        }\n    }\n}\n'
ISOLATION_BLOCK_SHA256 = '99b6e740b98cbe6f584be887e78ab2c3734c283a38afe57577cdea301138dadf'


def focus_selection(focus: str) -> dict:
    validate_rows(ROWS)
    if focus not in FOCUSES:
        raise ValueError("Unknown finite Desktop security focus; no class/full-suite fallback")
    row = next(row for row in ROWS if row["focus"] == focus)
    return selection(row["system"], row["arch"])


def selected_sources(focus: str) -> dict[str, str]:
    selected = focus_selection(focus)["selected"]
    paths = [SOURCE_PATHS["tls-rendering"], TLS_HELPER]
    paths.extend(SOURCE_PATHS[name] for name in selected if name != "tls-rendering")
    return {path: SOURCE_SHA256[path] for path in paths}


def validate_host(system: str, architecture: str, focus: str) -> None:
    if focus not in FOCUSES or selection(system, architecture)["focus"] != focus:
        raise ValueError("Desktop security focus must match its actual missing-only host")


def _source(root: Path, relative: str) -> bytes:
    root = root.resolve()
    current = root
    for part in Path(relative).parts:
        if part in {".", ".."} or Path(relative).is_absolute():
            raise ValueError("Expected a confined owning Desktop security source")
        current = current / part
        if current.is_symlink():
            raise ValueError("No symlinked Desktop security source/fixture")
    before = current.stat()
    if (not current.resolve().is_relative_to(root) or not stat.S_ISREG(before.st_mode) or
            before.st_nlink != 1 or before.st_size > 1024 * 1024):
        raise ValueError("Desktop security source must be bounded, confined and regular")
    value = current.read_bytes()
    after = current.stat()
    if (before.st_ino, before.st_mtime_ns, before.st_size) != (after.st_ino, after.st_mtime_ns, after.st_size):
        raise ValueError("Desktop security source changed during readback")
    return value


def fixture_contract(root: Path, focus: str) -> dict:
    for relative, expected in selected_sources(focus).items():
        if hashlib.sha256(_source(root, relative)).hexdigest() != expected:
            raise ValueError("Review the exact selected Desktop security native source/fixture")
    build = _source(root, BUILD_SOURCE)
    text = build.decode("utf-8")
    if (text.count(ISOLATION_BLOCK) != 1 or text.count("nativecmpkitDesktopSecurityFocus") != 1 or
            text.count("import org.gradle.api.tasks.testing.Test\n") != 1):
        raise ValueError("Mandatory exact finite fork isolation/default exclusion is missing or changed")
    if hashlib.sha256(_source(root, INIT_SCRIPT)).hexdigest() != INIT_SCRIPT_SHA256:
        raise ValueError("Exact bounded security-only public worker observation source changed")
    return {"focus": focus, "build_source": BUILD_SOURCE,
            "build_sha256": hashlib.sha256(build).hexdigest(),
            "isolation_block_sha256": ISOLATION_BLOCK_SHA256,
            "init_script_source": INIT_SCRIPT, "init_script_sha256": INIT_SCRIPT_SHA256,
            "max_parallel_forks": 1, "fork_every": 1,
            "worker_fixture_property": "one-selected-class",
            "public_worker_boundary_observation_required": True}


def validate_fixture_contract(contract: dict, focus: str) -> None:
    focus_selection(focus)
    expected = {"focus": focus, "build_source": BUILD_SOURCE,
                "isolation_block_sha256": ISOLATION_BLOCK_SHA256,
                "init_script_source": INIT_SCRIPT, "init_script_sha256": INIT_SCRIPT_SHA256,
                "max_parallel_forks": 1, "fork_every": 1,
                "worker_fixture_property": "one-selected-class",
                "public_worker_boundary_observation_required": True}
    if (not isinstance(contract, dict) or set(contract) != set(expected) | {"build_sha256"} or
            any(type(contract[key]) is not type(value) or contract[key] != value for key, value in expected.items()) or
            not isinstance(contract["build_sha256"], str) or
            re.fullmatch(r"[0-9a-f]{64}", contract["build_sha256"]) is None):
        raise ValueError("Invalid exact finite Desktop security fixture/isolation contract")


def worker_observation(log: Path, focus: str) -> dict:
    """Public Gradle TestListener events only; not OS-PID/exit or sandbox proof.

    Exactly one selected case per fresh sequential worker. Exact method names and
    original class XML are checked separately by the existing owning collector.
    No private log/error/test-output body is returned. Unknown shapes stay red.
    """
    route = focus_selection(focus)
    classes = {classname for classname, method in (SPECS[name] for name in route["selected"])}
    before = log.stat()
    if log.is_symlink() or not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > 32 * 1024 * 1024:
        raise ValueError("Worker observation needs one bounded owned regular Gradle log")
    prefix = "NATIVECMPKIT_DESKTOP_SECURITY_"
    lines = []
    with log.open(encoding="utf-8", errors="strict") as handle:
        for line in handle:
            if line.startswith(prefix):
                if len(line) > 1024 or len(lines) >= 1 + 4 * len(classes):
                    raise ValueError("Desktop security public worker observation exceeds its exact finite bound")
                lines.append(line.rstrip("\n"))
    after = log.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError("Worker observation changed during bounded readback")
    setup = prefix + "SETUP task=:calf-webview:desktopTest focus=" + focus + " forks=1 forkEvery=1 classes=" + str(len(classes))
    if len(lines) != 1 + 4 * len(classes) or lines[0] != setup:
        raise ValueError("Missing exact effective setup and one complete fresh boundary per selected class")
    event = re.compile(re.escape(prefix) + r"(WORKER|CASE) phase=(start|finish) worker=([1-9][0-9]{0,8})"
                       r"(?: classname=([A-Za-z_][A-Za-z0-9_.]*))?"
                       r"(?: tests=1 passed=1 failed=0 skipped=0 result=SUCCESS)?\Z")
    active = None
    finished = []
    seen_workers, seen_classes = set(), set()
    for line in lines[1:]:
        match = event.fullmatch(line)
        if match is None:
            raise ValueError("Unknown, failed, skipped or partial security worker event")
        kind, phase, worker, classname = match.groups()
        suffix = " tests=1 passed=1 failed=0 skipped=0 result=SUCCESS"
        if (phase == "finish") != line.endswith(suffix) or (kind == "CASE") != (classname is not None):
            raise ValueError("Public worker/case event lacks its exact bounded completion identity")
        if kind == "WORKER" and phase == "start":
            if active is not None or worker in seen_workers:
                raise ValueError("Security workers must be fresh, distinct and sequential")
            seen_workers.add(worker)
            active = {"worker": worker, "classname": None, "case_finished": False}
        elif kind == "CASE" and phase == "start":
            if (active is None or active["worker"] != worker or active["classname"] is not None or
                    classname not in classes or classname in seen_classes):
                raise ValueError("Only one exact missing selected class may enter each worker")
            active["classname"] = classname
            seen_classes.add(classname)
        elif kind == "CASE" and phase == "finish":
            if (active is None or active["worker"] != worker or active["classname"] != classname or active["case_finished"]):
                raise ValueError("Selected case completion is unowned, duplicated or reordered")
            active["case_finished"] = True
        else:
            if active is None or active["worker"] != worker or active["case_finished"] is not True:
                raise ValueError("Worker completed without its one owned completed selected case")
            finished.append({"descriptor_worker_index": int(worker), "classname": active["classname"]})
            active = None
    if active is not None or seen_classes != classes or len(finished) != len(classes):
        raise ValueError("Security worker boundary inventory is partial or changed")
    return {"focus": focus, "public_gradle_test_listener_boundaries_verified": True,
            "selected_class_workers": finished, "sequential_workers": True,
            "one_selected_case_per_worker": True, "os_worker_pid_observed": False,
            "os_worker_exit_or_sandbox_attested": False}
