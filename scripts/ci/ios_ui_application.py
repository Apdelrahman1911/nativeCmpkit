#!/usr/bin/env python3
"""Owned simulator application transport for KGP's *actual* native test parser.

Never generates JUnit, selects a foreign device/app, uploads a package, accepts
arbitrarily filtered/zero suites, or infers success from simctl launch acceptance. The app
bundle is a local disposable library-test host, not a sample or distributable.
Only finite, source-reviewed application profiles may filter this task;
full profiles retain their original mandatory suites. Python adversarial fixtures
are tooling evidence, not Apple runtime verification.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import selectors
import shutil
import signal
import stat
import struct
import subprocess
import sys
import time
import uuid

import apple_crash_diagnostics as crashes
import library_tests as lt
import runtime_context as runtime
import simulator_appearance

TASK = ":calf-ui:iosSimulatorArm64ApplicationTest"
HOST_SOURCE = "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt"
HOST_TEST = "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHostTest.kt"
EXPECTED_BINARY_DIRECTORY = "calf-ui/build/bin/iosSimulatorArm64/applicationDebugTest"
APPLICATION_HOSTS = {
    "calf-ui": {"task": TASK, "binary_directory": EXPECTED_BINARY_DIRECTORY,
                "receipt_subdirectory": "native-ui-application"},
    "calf-file-picker": {"task": ":calf-file-picker:" + lt.IOS_APPLICATION_TASK,
                         "binary_directory": "calf-file-picker/build/bin/iosSimulatorArm64/applicationDebugTest",
                         "receipt_subdirectory": "native-picker-application"},
    "calf-webview": {"task": ":calf-webview:" + lt.IOS_APPLICATION_TASK,
                     "binary_directory": "calf-webview/build/bin/iosSimulatorArm64/applicationDebugTest",
                     "receipt_subdirectory": "native-webview-application"},
}
APP_EXECUTABLE = "NativeCmpkitLibraryTests"
MAX_BINARY_BYTES = 1024 * 1024**2
MAX_STREAM_BYTES = 16 * 1024**2
MAX_LINE_BYTES = 512 * 1024
APP_TIMEOUT_SECONDS = 1920
SLIDER_TIMEOUT_SECONDS = 300


def application_timeout_seconds(focus: str | None) -> int:
    if focus is not None and focus not in lt.UI_APPLICATION_FOCUS_SPECS:
        raise ValueError("Unknown finite application focus")
    if focus in {lt.IOS_IMAGE_MEMORY_FOCUS, *lt.IOS_IMAGE_DARWIN_FOCUSES}:
        return 360
    return (SLIDER_TIMEOUT_SECONDS if focus in (
        lt.IOS_SLIDER_LIFECYCLE_FOCUS, lt.IOS_SLIDER_REMAINING_FOCUS, lt.IOS_SLIDER_STRUCTURE_FOCUS,
        lt.IOS_VECTOR_THEME_FOCUS,
        lt.IOS_VECTOR_RENDERING_FOCUS, lt.IOS_SYSTEM_APPEARANCE_FOCUS,
        lt.IOS_SLIDER_TAP_FOCUS, lt.IOS_SLIDER_PAIR_STRUCTURE_FOCUS,
    ) else APP_TIMEOUT_SECONDS)


SLIDER_STRUCTURAL_CASES = {
    "Liquid": (lt.IOS_SLIDER_LIFECYCLE_CLASS, lt.IOS_SLIDER_LIFECYCLE_METHODS[2]),
    "Cupertino": (lt.IOS_SLIDER_LIFECYCLE_CLASS, lt.IOS_SLIDER_LIFECYCLE_METHODS[3]),
}
SLIDER_STRUCTURAL_STEPS = (
    ((0, "before-content"), (0, "content-installed")) +
    tuple((axis, phase) for axis in range(1, 7) for phase in (
        "before-reset", "reset", "before-drag", "dragged", "before-replace", "replaced",
        "stale-released", "cancellation-verified", "fresh-reset", "fresh-input-verified"))
)
SYSTEM_APPEARANCE_CASE = (lt.IOS_VECTOR_THEME_CLASS, lt.IOS_VECTOR_THEME_METHODS[-1])
SLIDER_TAP_CASES = {
    "Liquid": (lt.IOS_SLIDER_LIFECYCLE_CLASS, lt.IOS_SLIDER_LIFECYCLE_METHODS[4]),
    "Cupertino": (lt.IOS_SLIDER_LIFECYCLE_CLASS, lt.IOS_SLIDER_LIFECYCLE_METHODS[5]),
}
SLIDER_TAP_STEPS = (
    "before-content", "content-installed", "before-tap", "tapped", "before-drag", "dragged",
    "first-input-verified", "before-opposite-taps", "opposite-taps", "successful-input-verified",
    "before-writer-clock", "writer-clock-advanced", "writer-cleared", "before-cancelled-drag",
    "cancelled-injector", "scene-cancelled", "cancellation-idle", "cancellation-verified",
    "before-cancelled-writer-clock", "cancelled-writer-clock-advanced", "cancelled-writer-cleared",
    "before-semantic", "semantic", "complete",
)
SLIDER_OBSERVER_STRUCTURAL_STEPS = tuple(
    (axis, phase) for axis in range(1, 7) for phase in ("drag-wait", "cancel-wait"))
SLIDER_OBSERVER_TAP_STEPS = ((0, "cancel-wait"),)
SYSTEM_APPEARANCE_STEPS = tuple(
    (phase, step, style) for step, style in simulator_appearance.REQUESTS for phase in ("request", "verified"))
TEST_ARGUMENTS = {"--ktest_logger=TEAMCITY", "--ktest_no_exit_code"}
DATE_BOUNDS_ARGUMENT = "--ktest_gradle_filter=" + lt.UI_DATE_BOUNDS_CLASS
DATE_REPLACEMENT_ARGUMENT = "--ktest_gradle_filter=" + lt.UI_DATE_REPLACEMENT_CLASS
APPLICATION_FOCUS_ARGUMENTS = {
    focus: "--ktest_gradle_filter=" + lt.ui_application_focus_filter(focus)
    for focus in lt.UI_APPLICATION_FOCUS_SPECS
}
IMAGE_LIFETIME_CASE = ("com.mohamedrejeb.calf.ui.utils.UIImageConversionTest",
                       "returnedImageOwnsItsPixelsAfterTemporaryArraysAndContextsAreCollected")
COMPACT_APPEARANCE_CASE = (lt.UI_DATE_REPLACEMENT_CLASS, lt.UI_DATE_REPLACEMENT_METHODS[1])
COMPACT_APPEARANCE_PHASES = (
    "created", "configured-before-attachment", "attached-laid-out",
    "colors-reapplied-after-attachment", "after-size-to-fit", "after-enabled-change",
    "after-theme-change", "detached",
)
IMAGE_LIFETIME_STEPS = (
    (("retained-ready", None),) +
    tuple((phase, iteration) for iteration in range(1, 21) for phase in ("before-conversion", "before-gc", "after-gc")) +
    (("before-verify", None), ("verified", None))
)
IMAGE_PROFILE_CASE = (lt.IOS_IMAGE_MEMORY_CLASS, lt.IOS_IMAGE_MEMORY_METHODS[-1])
PICKER_HOST_CASE = ("com.mohamedrejeb.calf.picker.internal.NativePickerApplicationHostTest",
                    "repeatedRealComposeRootsRecomposeDisposeAndRestoreTheirOwner")
PICKER_HOST_STEPS = tuple((phase, iteration, main_thread) for iteration in (1, 2) for phase, main_thread in (
    ("before-host", False), ("content-installed", False), ("initial-composed", True),
    ("recomposed", True), ("restored", True)))
# Exact source-defined validation messages -> finite diagnostic IDs. Never archive str(error)
# itself: malformed frames can contain private data. An unknown error stays unclassified/red.
TRANSPORT_FAILURE_REASONS = {
    "Malformed native TeamCity frame; do not fabricate replacement XML": "malformed-teamcity-frame",
    "Duplicate TeamCity attribute": "duplicate-teamcity-attribute",
    "Unknown TeamCity escape": "unknown-teamcity-escape",
    "Native application output exceeds bounded transport": "protocol-byte-limit",
    "Native transport already failed at startup": "already-failed-startup",
    "Native transport already failed its owned lifecycle": "already-failed-lifecycle",
    "Native application reported an error, timeout or unknown lifecycle marker": "unknown-lifecycle-marker",
    "Owned UIKit application reported a native lifecycle failure": "native-lifecycle-failure",
    "Unexpected native runner/worker completion contract": "invalid-worker-completion",
    "Native test frame outside the owned UIKit application lifecycle": "frame-outside-active-lifecycle",
    "Unexpected nested/active native suite": "overlapping-suite",
    "Unbalanced native suite completion": "unbalanced-suite",
    "Native testcase has no suite or overlaps another case": "overlapping-case",
    "Duplicate/unbounded native testcase": "duplicate-or-unbounded-case",
    "Native result has no matching started testcase": "unmatched-result",
    "Duplicate native testcase failure": "duplicate-case-failure",
    "Unreviewed native test protocol record": "unreviewed-protocol-record",
    "Nonzero or invalid console process exit": "nonzero-console-exit",
    "Failed native startup or lifecycle": "failed-native-lifecycle",
    "Missing native application activation": "missing-activation",
    "Missing native Worker/application completion": "missing-worker-completion",
    "Native suite or testcase is still open": "unfinished-native-case",
    "Zero/incomplete native test execution is not successful transport": "zero-or-incomplete-native-execution",
    "Unbounded incomplete native protocol line": "incomplete-line-byte-limit",
}


def macho_simulator_identity(path: Path) -> dict:
    """Read the linked executable's real header/load commands, not its filename."""
    stat = path.stat()
    if not path.is_file() or path.is_symlink() or stat.st_nlink != 1 or not 32 <= stat.st_size <= MAX_BINARY_BYTES:
        raise ValueError("Expected a bounded regular unshared test executable")
    with path.open("rb") as handle:
        header = handle.read(32)
        magic, cpu, subtype, kind, count, size, flags, reserved = struct.unpack("<8I", header)
        if magic != 0xFEEDFACF or cpu != 0x0100000C or kind != 2:
            raise ValueError("UIKit host requires an Arm64 Mach-O executable, not a KLIB/framework/device/fat binary")
        if count > 4096 or size > 1024**2 or size > stat.st_size - 32:
            raise ValueError("Unbounded or truncated Mach-O load-command table")
        commands = handle.read(size)
    offset = 0
    builds = []
    executable_uuids = []
    for _ in range(count):
        if offset + 8 > len(commands):
            raise ValueError("Truncated Mach-O load command")
        command, length = struct.unpack_from("<2I", commands, offset)
        if length < 8 or length % 8 or offset + length > len(commands):
            raise ValueError("Invalid Mach-O load-command length")
        if command == 0x32:  # LC_BUILD_VERSION, current Kotlin/Native/Xcode model.
            if length < 24:
                raise ValueError("Truncated Apple build-version command")
            apple_platform, minimum, sdk, tools = struct.unpack_from("<4I", commands, offset + 8)
            if length != 24 + tools * 8:
                raise ValueError("Invalid build-version tool table")
            def version(value):
                return f"{value >> 16}.{(value >> 8) & 255}.{value & 255}"
            builds.append({"platform": apple_platform, "minimum_os": version(minimum), "sdk": version(sdk)})
        if command == 0x1B:  # LC_UUID: real linked slice identity for crash correlation.
            if length != 24:
                raise ValueError("Invalid Mach-O UUID command")
            identifier = uuid.UUID(bytes=commands[offset + 8:offset + 24])
            if identifier.int == 0 or executable_uuids:
                raise ValueError("Zero or ambiguous Mach-O executable UUID")
            executable_uuids.append(str(identifier))
        offset += length
    if offset != len(commands) or len(builds) != 1 or builds[0]["platform"] != 7:
        raise ValueError("Expected exactly one explicit iOS-simulator build version")
    after = path.stat()
    if (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError("Executable changed during Mach-O inspection")
    return {"architecture": "arm64", "file_type": "executable", **builds[0],
            "executable_uuid": executable_uuids[0] if executable_uuids else None}


def app_information(bundle_id: str, minimum_os: str) -> dict:
    if not re.fullmatch(r"io\.github\.apdelrahman1911\.nativecmpkit\.verification\.ui\.r[0-9a-f]{12}\.t[0-9a-f]{32}", bundle_id):
        raise ValueError("Expected a fresh source-bound owned verification bundle identifier")
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){2}", minimum_os):
        raise ValueError("Minimum OS must come from the linked Mach-O")
    return {"CFBundleIdentifier": bundle_id, "CFBundleExecutable": APP_EXECUTABLE,
            "CFBundleName": "NativeCmpKit library tests", "CFBundlePackageType": "APPL",
            "CFBundleVersion": "1", "CFBundleShortVersionString": "0.1.0",
            "CFBundleSupportedPlatforms": ["iPhoneSimulator"], "LSRequiresIPhoneOS": True,
            "MinimumOSVersion": minimum_os, "UIDeviceFamily": [1, 2],
            # Required by Compose's strict iPhone plist sanity check. Keep that
            # check enabled; a fixture crash must not become a silent bypass.
            "CADisableMinimumFrameDurationOnPhone": True,
            "UILaunchScreen": {}, "UIApplicationSupportsIndirectInputEvents": True}


def teamcity_fields(line: str) -> tuple[str, dict] | None:
    if not line.startswith("##teamcity["):
        return None
    match = re.fullmatch(r"##teamcity\[([A-Za-z]+)((?: [A-Za-z][A-Za-z0-9]*='(?:\|.|[^'\r\n])*')*)\]", line)
    if not match:
        raise ValueError("Malformed native TeamCity frame; do not fabricate replacement XML")
    fields = {}
    escapes = {"|": "|", "'": "'", "n": "\n", "r": "\r", "[": "[", "]": "]"}
    for key, value in re.findall(r" ([A-Za-z][A-Za-z0-9]*)='((?:\|.|[^'\r\n])*)'", match[2]):
        if key in fields:
            raise ValueError("Duplicate TeamCity attribute")
        def decode(found):
            if found[1] not in escapes:
                raise ValueError("Unknown TeamCity escape")
            return escapes[found[1]]
        fields[key] = re.sub(r"\|(.)", decode, value)
    return match[1], fields


class NativeProtocol:
    """Independent transport checks; KGP still owns actual failure/JUnit parsing."""
    def __init__(self, bundle_id: str | None = None):
        if bundle_id is not None and not crashes.BUNDLE.fullmatch(bundle_id):
            raise ValueError("Expected an exact owned verification launch bundle")
        self.expected_bundle = bundle_id
        self.observed_launch_pid = None
        self.transport_observation = None
        self.image_lifetime_observation = None
        self.image_profile_observations = []
        self.image_profile_pid = None
        self.image_profile_request = None
        self.image_profile_poll = None
        self.image_profile_request_sent = False
        self.compact_appearance_observation = []
        self.active = None
        self.completed = None
        self.stack = []
        self.open_case = None
        self.cases = {}
        self.stream_bytes = 0
        self.startup_failure_observation = None
        self.lifecycle_failure_observation = None
        self.picker_admission_observations = []
        self.picker_host_observations = []
        self.slider_structural_observations = {}
        self.slider_drag_observations = {}
        self.slider_failure_cleanup_observations = {}
        self.slider_tap_observations = {}
        self.slider_observer_observations = {}
        self.vector_scale_observations = []
        self.system_appearance_observations = []
        self.system_appearance_request = None

    def feed(self, line: str):
        self.stream_bytes += len((line + "\n").encode())
        if self.stream_bytes > MAX_STREAM_BYTES or len(line.encode()) > MAX_LINE_BYTES:
            raise ValueError("Native application output exceeds bounded transport")
        if self.startup_failure_observation is not None:
            raise ValueError("Native transport already failed at startup")
        if self.lifecycle_failure_observation is not None:
            raise ValueError("Native transport already failed its owned lifecycle")
        if self.expected_bundle is not None and line.startswith(self.expected_bundle + ":"):
            launch = re.fullmatch(re.escape(self.expected_bundle) + r": ([1-9][0-9]{0,9})", line)
            if launch is None or int(launch[1]) > 2**31 - 1 or self.observed_launch_pid is not None:
                raise ValueError("Invalid or duplicate exact simulator launch PID")
            # simctl's header and forwarded child output can be independently
            # buffered. Do not invent a pre-activation stdout ordering contract.
            # This is a bounded console witness, not a trusted-OS attestation.
            self.observed_launch_pid = int(launch[1])
            if self.image_profile_pid is not None and self.image_profile_pid != self.observed_launch_pid:
                raise ValueError("Native image workload PID differs from the exact simulator launch PID")
            self._request_image_profile_if_ready()
            return
        profile = re.fullmatch(
            r"NATIVECMPKIT_IMAGE_PROFILE phase=(ready|complete)(?: process_id=([1-9][0-9]{0,9}))?(?: rounds=([1-9][0-9]{0,3}))?", line)
        if profile:
            if self.active is None or self.completed is not None or self.open_case != IMAGE_PROFILE_CASE:
                raise ValueError("Image profile marker outside its exact active native testcase")
            if profile[1] == "ready":
                if (self.cases[self.open_case]["status"] != "running" or self.image_profile_observations or
                        profile[2] is None or profile[3] is not None or
                        int(profile[2]) >= 2**31):
                    raise ValueError("Missing, repeated or malformed native image profile request")
                self.image_profile_pid = int(profile[2])
                if self.observed_launch_pid is not None and self.image_profile_pid != self.observed_launch_pid:
                    raise ValueError("Native image workload PID differs from the exact simulator launch PID")
                self.image_profile_observations.append({"phase": "ready", "process_id": self.image_profile_pid})
                self._request_image_profile_if_ready()
            else:
                if (len(self.image_profile_observations) != 1 or self.image_profile_pid is None or
                        self.image_profile_observations[0] != {"phase": "ready", "process_id": self.image_profile_pid} or
                        profile[2] is not None or profile[3] is None or not 1 <= int(profile[3]) <= 4096):
                    raise ValueError("Missing, reordered or unbounded native image profile workload")
                self.image_profile_observations.append({"phase": "complete", "rounds": int(profile[3])})
            return
        if line.startswith("NATIVECMPKIT_IMAGE_PROFILE"):
            raise ValueError("Unknown or malformed native image profile marker")
        appearance = re.fullmatch(
            r"NATIVECMPKIT_SYSTEM_APPEARANCE phase=(request|verified) step=([12]) style=(light|dark)", line)
        if appearance:
            if self.active is None or self.completed is not None or self.open_case != SYSTEM_APPEARANCE_CASE:
                raise ValueError("System appearance marker outside its exact active native testcase")
            index = len(self.system_appearance_observations)
            actual = (appearance[1], int(appearance[2]), appearance[3])
            if index >= len(SYSTEM_APPEARANCE_STEPS) or actual != SYSTEM_APPEARANCE_STEPS[index]:
                raise ValueError("Missing, repeated or reordered actual system appearance marker")
            self.system_appearance_observations.append({"phase": actual[0], "step": actual[1], "style": actual[2]})
            if actual[0] == "request" and self.system_appearance_request is not None:
                self.system_appearance_request(actual[1], actual[2])
            return
        if line.startswith("NATIVECMPKIT_SYSTEM_APPEARANCE"):
            raise ValueError("Unknown or malformed actual system appearance marker")
        tap = re.fullmatch(r"NATIVECMPKIT_SLIDER_TAP renderer=(Liquid|Cupertino) phase=([a-z-]+)", line)
        if tap:
            renderer, phase = tap.groups()
            if self.active is None or self.completed is not None or self.open_case != SLIDER_TAP_CASES[renderer]:
                raise ValueError("Slider tap marker outside its exact active native testcase")
            observations = self.slider_tap_observations.setdefault(renderer, [])
            index = len(observations)
            if index >= len(SLIDER_TAP_STEPS) or phase != SLIDER_TAP_STEPS[index]:
                raise ValueError("Missing, repeated or reordered native slider tap phase")
            observations.append({"phase": phase})
            return
        if line.startswith("NATIVECMPKIT_SLIDER_TAP"):
            raise ValueError("Unknown or malformed native slider tap marker")
        observer = re.fullmatch(
            r"NATIVECMPKIT_SLIDER_OBSERVER renderer=(Liquid|Cupertino) axis=([0-6]) "
            r"phase=(drag-wait|cancel-wait) starts=(0|[1-9][0-9]{0,4}) "
            r"cancelled=(0|[1-9][0-9]{0,4}) stopped=(0|[1-9][0-9]{0,4}) "
            r"observed=(true|false) finished=(0|[1-9][0-9]{0,4})", line)
        if observer:
            renderer, axis, phase = observer[1], int(observer[2]), observer[3]
            if self.active is None or self.completed is not None:
                raise ValueError("Slider observer snapshot outside active native execution")
            if axis == 0:
                phases = self.slider_tap_observations.get(renderer, [])
                need_phase = {"phase": "cancellation-idle"}
                expected = SLIDER_OBSERVER_TAP_STEPS
                key = SLIDER_TAP_CASES[renderer]
            else:
                phases = self.slider_structural_observations.get(renderer, [])
                need_phase = {"axis": axis, "phase": "before-drag" if phase == "drag-wait" else "replaced"}
                expected = SLIDER_OBSERVER_STRUCTURAL_STEPS
                key = SLIDER_STRUCTURAL_CASES[renderer]
            rows = self.slider_observer_observations.setdefault(renderer, [])
            # Full profiles run both methods for each renderer in one process.
            # Keep their diagnostics together but count each exact case's
            # finite sequence independently; axis zero belongs only to taps.
            index = sum((row["axis"] == 0) == (axis == 0) for row in rows)
            numbers = {k: int(v) for k, v in zip(("starts", "cancelled", "stopped", "finished"),
                                                 (observer[4], observer[5], observer[6], observer[8]))}
            if (self.open_case != key or not phases or phases[-1] != need_phase or
                    index >= len(expected) or (axis, phase) != expected[index] or
                    any(n > 65535 for n in numbers.values())):
                raise ValueError("Missing, repeated, reordered or unbounded actual slider observer snapshot")
            rows.append({"axis": axis, "phase": phase, **numbers, "observed": observer[7] == "true"})
            return
        if line.startswith("NATIVECMPKIT_SLIDER_OBSERVER"):
            raise ValueError("Unknown or malformed actual slider observer snapshot")
        vector_scale = re.fullmatch(
            r"NATIVECMPKIT_VECTOR_SCALE density=(2\.0|3\.0) nativeScreen=([1-4]\.0) "
            r"view=(2\.0|3\.0) layer=(2\.0|3\.0)", line)
        if vector_scale:
            if (self.active is None or self.completed is not None or
                    self.open_case != (lt.IOS_VECTOR_THEME_CLASS, lt.IOS_VECTOR_THEME_METHODS[0])):
                raise ValueError("Native vector scale witness outside its exact active testcase")
            index = len(self.vector_scale_observations)
            density, screen, view, layer = map(float, vector_scale.groups())
            if index != 0 or screen != density or view != density or layer != density:
                raise ValueError("Missing, repeated, reordered or mismatched actual native vector scale")
            self.vector_scale_observations.append({"density": density, "native_screen": screen,
                                                   "view": view, "layer": layer})
            return
        if line.startswith("NATIVECMPKIT_VECTOR_SCALE"):
            raise ValueError("Unknown or malformed actual native vector scale witness")
        drag = re.fullmatch(
            r"NATIVECMPKIT_SLIDER_DRAG renderer=(Liquid|Cupertino) axis=([1-6]) "
            r"started=(true|false) changed=(true|false) observed=(true|false)", line)
        cleanup = re.fullmatch(
            r"NATIVECMPKIT_SLIDER_FAILURE_CLEANUP renderer=(Liquid|Cupertino) axis=([1-6]) "
            r"phase=(request|verified|failed)", line)
        if drag or cleanup:
            marker = drag or cleanup
            renderer, axis = marker[1], int(marker[2])
            if (self.active is None or self.completed is not None or self.open_case != SLIDER_STRUCTURAL_CASES[renderer]):
                raise ValueError("Slider drag/cleanup marker outside its exact active native testcase")
            if drag:
                phases = self.slider_structural_observations.get(renderer, [])
                observations = self.slider_drag_observations.setdefault(renderer, [])
                if not phases or phases[-1] != {"axis": axis, "phase": "dragged"} or axis != len(observations) + 1:
                    raise ValueError("Missing, repeated or reordered actual pre-assertion drag diagnostic")
                observations.append({"axis": axis, **{key: value == "true" for key, value in
                    zip(("started", "changed", "observed"), drag.groups()[2:])}})
            else:
                observations = self.slider_failure_cleanup_observations.setdefault(renderer, [])
                phases = self.slider_structural_observations.get(renderer, [])
                if (not phases or phases[-1]["axis"] != axis or
                        not observations and cleanup[3] != "request" or
                        observations and (len(observations) != 1 or observations[0]["axis"] != axis or cleanup[3] == "request")):
                    raise ValueError("Missing, repeated or reordered failure-only pointer cleanup diagnostic")
                observations.append({"axis": axis, "phase": cleanup[3]})
            return
        if line.startswith(("NATIVECMPKIT_SLIDER_DRAG", "NATIVECMPKIT_SLIDER_FAILURE_CLEANUP")):
            raise ValueError("Unknown or malformed actual slider drag/cleanup diagnostic")
        compact = re.fullmatch(
            r"NATIVECMPKIT_COMPACT_APPEARANCE phase=([a-z-]+) backgroundMatches=(true|false) "
            r"tintMatches=(true|false) attached=(true|false) enabled=(true|false) rtl=(true|false) "
            r"dark=(true|false) mainThread=(true|false)", line)
        if compact:
            if self.active is None or self.completed is not None or self.open_case != COMPACT_APPEARANCE_CASE:
                raise ValueError("Compact diagnostic outside its exact active native testcase")
            index = len(self.compact_appearance_observation)
            if index >= len(COMPACT_APPEARANCE_PHASES) or compact[1] != COMPACT_APPEARANCE_PHASES[index]:
                raise ValueError("Missing, duplicate or reordered compact appearance diagnostic")
            if compact[8] != "true":
                raise ValueError("Compact diagnostic is not on the actual main thread")
            expected_attached = index in range(2, 7)
            if (compact[4] == "true") != expected_attached:
                raise ValueError("Compact diagnostic attachment/owned detachment is unverified")
            self.compact_appearance_observation.append({"phase": compact[1], **{
                key: value == "true" for key, value in zip(
                    ("background_matches", "tint_matches", "attached", "enabled", "rtl", "dark", "main_thread"),
                    compact.groups()[1:])}})
            return
        if line.startswith("NATIVECMPKIT_COMPACT_APPEARANCE"):
            raise ValueError("Unknown or malformed compact appearance diagnostic")
        admission = re.fullmatch(
            r"NATIVECMPKIT_PICKER_ADMISSION phase=(export-initial|photo-initial) iteration=([0-4]) "
            r"backlink=(true|false) presenting=(true|false) dismissing=(true|false) "
            r"forward=(true|false) noPresentation=(true|false)", line)
        if admission:
            owner = "com.mohamedrejeb.calf.picker.IosPickerRuntimeOwnershipTest"
            expected = {"export-initial": "cancellationDuringRealExportPresentationWaitsForNativeCompletionBeforeRemovingStaging",
                        "photo-initial": "retainedPublicPhotoLauncherUsesFourNativeConfigurationSnapshotsAndCurrentCallback"}
            phase, iteration = admission[1], int(admission[2])
            if self.active is None or self.completed is not None or self.open_case != (owner, expected[phase]):
                raise ValueError("Picker admission diagnostic outside its exact active native testcase")
            prior = [o for o in self.picker_admission_observations if o["phase"] == phase]
            if (phase == "export-initial" and (iteration != 0 or prior) or
                    phase == "photo-initial" and (iteration != len(prior) + 1 or not 1 <= iteration <= 4)):
                raise ValueError("Missing, duplicate or reordered finite picker admission diagnostic")
            self.picker_admission_observations.append({"phase": phase, "iteration": iteration, **{
                key: value == "true" for key, value in zip(
                    ("backlink", "presenting", "dismissing", "forward", "no_presentation"), admission.groups()[2:])}})
            return
        if line.startswith("NATIVECMPKIT_PICKER_ADMISSION"):
            raise ValueError("Unknown or malformed picker admission diagnostic")
        host = re.fullmatch(
            r"NATIVECMPKIT_PICKER_HOST phase=(before-host|content-installed|initial-composed|recomposed|restored) "
            r"iteration=([12]) mainThread=(true|false)", line)
        if host:
            if self.active is None or self.completed is not None or self.open_case != PICKER_HOST_CASE:
                raise ValueError("Picker host diagnostic outside its exact active native testcase")
            index = len(self.picker_host_observations)
            actual = (host[1], int(host[2]), host[3] == "true")
            if index >= len(PICKER_HOST_STEPS) or actual != PICKER_HOST_STEPS[index]:
                raise ValueError("Missing, duplicate, reordered or wrong-thread picker host diagnostic")
            self.picker_host_observations.append({"phase": actual[0], "iteration": actual[1], "main_thread": actual[2]})
            return
        if line.startswith("NATIVECMPKIT_PICKER_HOST"):
            raise ValueError("Unknown or malformed picker host diagnostic")
        slider = re.fullmatch(
            r"NATIVECMPKIT_SLIDER_STRUCTURE renderer=(Liquid|Cupertino) axis=([0-6]) phase=([a-z-]+)", line)
        if slider:
            renderer = slider[1]
            if self.active is None or self.completed is not None or self.open_case != SLIDER_STRUCTURAL_CASES[renderer]:
                raise ValueError("Slider diagnostic outside its exact active native testcase")
            observations = self.slider_structural_observations.setdefault(renderer, [])
            actual = (int(slider[2]), slider[3])
            index = len(observations)
            if index >= len(SLIDER_STRUCTURAL_STEPS) or actual != SLIDER_STRUCTURAL_STEPS[index]:
                raise ValueError("Missing, duplicate or reordered finite slider structural diagnostic")
            observations.append({"axis": actual[0], "phase": actual[1]})
            return
        if line.startswith("NATIVECMPKIT_SLIDER_STRUCTURE"):
            raise ValueError("Unknown or malformed slider structural diagnostic")
        image = re.fullmatch(
            r"NATIVECMPKIT_UIKIT_IMAGE_LIFETIME phase=(retained-ready|before-conversion|before-gc|after-gc|before-verify|verified)"
            r"(?: iteration=([1-9][0-9]?))? mainThread=(true|false)", line)
        if image:
            if self.active is None or self.completed is not None or self.open_case != IMAGE_LIFETIME_CASE:
                raise ValueError("Image lifetime diagnostic outside its exact active native testcase")
            previous = self.image_lifetime_observation
            index = previous["marker_count"] if previous else 0
            iteration = int(image[2]) if image[2] else None
            if index >= len(IMAGE_LIFETIME_STEPS) or (image[1], iteration) != IMAGE_LIFETIME_STEPS[index]:
                raise ValueError("Missing, duplicate or reordered finite image lifetime diagnostic")
            self.image_lifetime_observation = {
                "marker_count": index + 1, "last_phase": image[1], "last_iteration": iteration,
                "main_thread": image[3] == "true", "retained_image_bytes_verified": image[1] == "verified"}
            if image[3] != "true":
                raise ValueError("Image lifetime callback is not on the actual main thread")
            return
        startup = re.fullmatch(
            r"NATIVECMPKIT_UIKIT_STARTUP_TIMEOUT active=(true|false) key=(true|false) hidden=(true|false) "
            r"rootAttached=(true|false) rootNativeEqual=(true|false) workerStarted=false", line)
        if startup:
            if self.active is not None or self.completed is not None or self.cases:
                raise ValueError("Startup timeout is outside the pre-worker lifecycle")
            # Known, bounded booleans only. Retain this failure even though the
            # frame is NOT forwarded/accepted as TeamCity or successful transport.
            self.startup_failure_observation = {
                key: value == "true" for key, value in zip(
                    ("active", "key", "hidden", "root_attached", "root_native_equal"), startup.groups())}
            self.startup_failure_observation["worker_started"] = False
            raise ValueError("UIKit startup readiness failed")
        failure = re.fullmatch(r"NATIVECMPKIT_UIKIT_(RUNNER_ERROR|TERMINATION_ERROR) type=([A-Za-z][A-Za-z0-9_]{0,79})", line)
        timeout = line == "NATIVECMPKIT_UIKIT_TIMEOUT workerTerminationVerified=false"
        if failure or timeout:
            if self.active is None or self.completed is not None:
                raise ValueError("Native failure marker outside the owned active lifecycle")
            # Public error TYPE/known stage only, never arbitrary exception message,
            # stack, path or unknown marker text. Retained diagnostic still FAILS
            # before forwarding and cannot finish a testcase/Worker or satisfy a gate.
            self.lifecycle_failure_observation = ({"stage": failure[1].lower(), "error_type": failure[2],
                                                    "worker_termination_verified": False} if failure else
                                                 {"stage": "timeout", "worker_termination_verified": False})
            raise ValueError("Owned UIKit application reported a native lifecycle failure")
        active = re.fullmatch(r"NATIVECMPKIT_UIKIT_ACTIVE mainWorker=([1-9][0-9]*) ownedWorker=([1-9][0-9]*)", line)
        complete = re.fullmatch(r"NATIVECMPKIT_UIKIT_COMPLETED runnerExit=([0-9]+) workerTerminated=true", line)
        if active:
            if self.active is not None or self.completed is not None or active[1] == active[2]:
                raise ValueError("Expected exactly one genuine main/owned-worker activation")
            self.active = {"main_worker": int(active[1]), "owned_worker": int(active[2])}
            return
        if complete:
            if self.active is not None and self.completed is None and 0 < int(complete[1]) <= 2**31 - 1:
                self.lifecycle_failure_observation = {"stage": "runner_completion", "runner_exit": int(complete[1]),
                                                      "worker_termination_verified": True}
            if self.completed is not None or self.active is None or int(complete[1]) != 0 or self.stack or self.open_case is not None:
                raise ValueError("Unexpected native runner/worker completion contract")
            self.completed = {"runner_exit": 0, "worker_terminated": True}
            return
        if line.startswith("NATIVECMPKIT_UIKIT_"):
            raise ValueError("Native application reported an error, timeout or unknown lifecycle marker")
        record = teamcity_fields(line)
        if record is None:
            return
        kind, fields = record
        if self.active is None or self.completed is not None:
            raise ValueError("Native test frame outside the owned UIKit application lifecycle")
        if kind in {"testSuiteStarted", "testSuiteFinished", "testStarted", "testFinished", "testFailed", "testIgnored"}:
            name = fields.get("name", "")
            if not name or len(name) > 4096 or any(c in name for c in "\r\n"):
                raise ValueError("Missing or invalid native testcase/suite identity")
        if kind == "testSuiteStarted":
            if self.open_case is not None or len(self.stack) >= 32:
                raise ValueError("Unexpected nested/active native suite")
            self.stack.append(name)
        elif kind == "testSuiteFinished":
            if not self.stack or self.stack[-1] != name or self.open_case is not None:
                raise ValueError("Unbalanced native suite completion")
            self.stack.pop()
        elif kind in {"testStarted", "testIgnored"}:
            if not self.stack or self.open_case is not None:
                raise ValueError("Native testcase has no suite or overlaps another case")
            key = (self.stack[-1], name)
            if key in self.cases or len(self.cases) >= lt.MAX_CASES:
                raise ValueError("Duplicate/unbounded native testcase")
            self.cases[key] = {"classname": key[0], "name": key[1], "status": "skipped" if kind == "testIgnored" else "running",
                               "finished": kind == "testIgnored"}
            if kind == "testStarted":
                self.open_case = key
        elif kind in {"testFinished", "testFailed"}:
            if self.open_case is None or self.open_case[1] != name:
                raise ValueError("Native result has no matching started testcase")
            case = self.cases[self.open_case]
            if kind == "testFailed":
                if case["status"] != "running":
                    raise ValueError("Duplicate native testcase failure")
                case["status"] = "failed"
            else:
                if case["status"] == "running":
                    if self.open_case == IMAGE_PROFILE_CASE and (
                            len(self.image_profile_observations) != 2 or
                            self.image_profile_observations[-1].get("phase") != "complete"):
                        raise ValueError("A passing profile workload needs both complete actual native phases")
                    if self.open_case == IMAGE_LIFETIME_CASE and (self.image_lifetime_observation is None or
                            self.image_lifetime_observation["marker_count"] != len(IMAGE_LIFETIME_STEPS) or
                            self.image_lifetime_observation["retained_image_bytes_verified"] is not True):
                        raise ValueError("A passing image lifetime case needs its complete actual diagnostic sequence")
                    if self.open_case == PICKER_HOST_CASE and len(self.picker_host_observations) != len(PICKER_HOST_STEPS):
                        raise ValueError("A passing picker host case needs its complete actual phase/thread sequence")
                    for renderer, key in SLIDER_STRUCTURAL_CASES.items():
                        if self.open_case == key and len(self.slider_structural_observations.get(renderer, [])) != len(SLIDER_STRUCTURAL_STEPS):
                            raise ValueError("A passing slider structural case needs all six actual axis sequences")
                        if self.open_case == key:
                            drag = self.slider_drag_observations.get(renderer)
                            if drag is not None and (len(drag) != 6 or not all(
                                    row["started"] and row["changed"] and row["observed"] for row in drag)):
                                raise ValueError("Observed native drag failure cannot become a passing structural case")
                            if self.slider_failure_cleanup_observations.get(renderer):
                                raise ValueError("Failure-only pointer cleanup cannot become a passing structural case")
                            observations = self.slider_observer_observations.get(renderer)
                            if observations is not None and tuple((row["axis"], row["phase"]) for row in observations if row["axis"] != 0) != SLIDER_OBSERVER_STRUCTURAL_STEPS:
                                raise ValueError("A passing slider structural case cannot truncate observed wait diagnostics")
                    if self.open_case == SYSTEM_APPEARANCE_CASE and len(self.system_appearance_observations) != len(SYSTEM_APPEARANCE_STEPS):
                        raise ValueError("A passing system appearance case needs both actual requested/verified transitions")
                    if (self.open_case == (lt.IOS_VECTOR_THEME_CLASS, lt.IOS_VECTOR_THEME_METHODS[0]) and
                            len(self.vector_scale_observations) != 1):
                        raise ValueError("A passing vector case needs its exact actual native screen witness")
                    for renderer, key in SLIDER_TAP_CASES.items():
                        if self.open_case == key and len(self.slider_tap_observations.get(renderer, [])) != len(SLIDER_TAP_STEPS):
                            raise ValueError("A passing slider tap case needs its complete actual phase sequence")
                        if self.open_case == key:
                            observations = self.slider_observer_observations.get(renderer)
                            if observations is not None and tuple((row["axis"], row["phase"]) for row in observations if row["axis"] == 0) != SLIDER_OBSERVER_TAP_STEPS:
                                raise ValueError("A passing slider tap case cannot truncate observed wait diagnostics")
                    case["status"] = "passed"
                case["finished"] = True
                self.open_case = None
        elif kind not in {"testStdOut", "testStdErr", "message", "testCount"}:
            raise ValueError("Unreviewed native test protocol record")

    def _request_image_profile_if_ready(self) -> None:
        if (self.active is not None and self.completed is None and self.open_case == IMAGE_PROFILE_CASE and
                self.image_profile_pid is not None and self.image_profile_request is not None and
                self.cases[self.open_case]["status"] == "running" and
                self.image_profile_observations == [{"phase": "ready", "process_id": self.image_profile_pid}] and
                not self.image_profile_request_sent):
            self.image_profile_request_sent = True
            self.image_profile_request(self.image_profile_pid)

    def partial(self) -> dict:
        """Finished frames only; interruption is never promoted to a testcase.

        KGP owns its real XML/failure synthesis. This observation does not emit
        XML, infer a runner result, claim crash absence or satisfy any test gate.
        """
        finished = [{k: c[k] for k in ("classname", "name", "status")} for c in self.cases.values() if c["finished"]]
        pending = self.cases.get(self.open_case)
        return {"activation": self.active, "completion": self.completed,
                "complete_native_lifecycle": self.active is not None and self.completed is not None and
                    not self.stack and self.open_case is None and bool(finished),
                "testcases": finished, "counts": lt.case_counts(finished),
                "unfinished_testcase": {"classname": pending["classname"], "name": pending["name"],
                    "status": "incomplete", "failure_frame_observed": pending["status"] == "failed"} if pending else None,
                "open_suites": list(self.stack), "stream_bytes": self.stream_bytes,
                "observed_launch_pid": self.observed_launch_pid,
                "image_lifetime_observation": self.image_lifetime_observation,
                **({"image_profile_observations": self.image_profile_observations}
                   if self.image_profile_observations else {}),
                **({"lifecycle_failure_observation": self.lifecycle_failure_observation}
                   if self.lifecycle_failure_observation is not None else {}),
                **({"picker_admission_observations": self.picker_admission_observations}
                   if self.picker_admission_observations else {}),
                **({"picker_host_observations": self.picker_host_observations}
                   if self.picker_host_observations else {}),
                **({"slider_structural_observations": self.slider_structural_observations}
                   if self.slider_structural_observations else {}),
                **({"slider_drag_observations": self.slider_drag_observations}
                   if self.slider_drag_observations else {}),
                **({"slider_failure_cleanup_observations": self.slider_failure_cleanup_observations}
                   if self.slider_failure_cleanup_observations else {}),
                **({"slider_tap_observations": self.slider_tap_observations}
                   if self.slider_tap_observations else {}),
                **({"slider_observer_observations": self.slider_observer_observations}
                   if self.slider_observer_observations else {}),
                **({"vector_scale_observations": self.vector_scale_observations}
                   if self.vector_scale_observations else {}),
                **({"system_appearance_observations": self.system_appearance_observations}
                   if self.system_appearance_observations else {}),
                **({"compact_appearance_observation": self.compact_appearance_observation}
                   if self.compact_appearance_observation else {})}

    def finish(self, process_exit: int) -> dict:
        if type(process_exit) is not int or process_exit != 0:
            raise ValueError("Nonzero or invalid console process exit")
        if self.startup_failure_observation is not None or self.lifecycle_failure_observation is not None:
            raise ValueError("Failed native startup or lifecycle")
        if self.active is None:
            raise ValueError("Missing native application activation")
        if self.completed is None:
            raise ValueError("Missing native Worker/application completion")
        if self.stack or self.open_case is not None:
            raise ValueError("Native suite or testcase is still open")
        cases = list(self.cases.values())
        if not cases or not all(c["finished"] for c in cases) or all(c["status"] == "skipped" for c in cases):
            raise ValueError("Zero/incomplete native test execution is not successful transport")
        if self.compact_appearance_observation and len(self.compact_appearance_observation) != len(COMPACT_APPEARANCE_PHASES):
            raise ValueError("Incomplete compact appearance diagnostic, not accepted evidence")
        if self.image_profile_observations and self.observed_launch_pid != self.image_profile_pid:
            raise ValueError("Native image workload lacks a matching actual simulator launch PID")
        return {"activation": self.active, "completion": self.completed,
                "testcases": [{k: c[k] for k in ["classname", "name", "status"]} for c in cases],
                "counts": lt.case_counts(cases), "stream_bytes": self.stream_bytes,
                "observed_launch_pid": self.observed_launch_pid,
                "image_lifetime_observation": self.image_lifetime_observation,
                **({"image_profile_observations": self.image_profile_observations}
                   if self.image_profile_observations else {}),
                **({"picker_admission_observations": self.picker_admission_observations}
                   if self.picker_admission_observations else {}),
                **({"picker_host_observations": self.picker_host_observations}
                   if self.picker_host_observations else {}),
                **({"slider_structural_observations": self.slider_structural_observations}
                   if self.slider_structural_observations else {}),
                **({"slider_drag_observations": self.slider_drag_observations}
                   if self.slider_drag_observations else {}),
                **({"slider_failure_cleanup_observations": self.slider_failure_cleanup_observations}
                   if self.slider_failure_cleanup_observations else {}),
                **({"slider_tap_observations": self.slider_tap_observations}
                   if self.slider_tap_observations else {}),
                **({"slider_observer_observations": self.slider_observer_observations}
                   if self.slider_observer_observations else {}),
                **({"vector_scale_observations": self.vector_scale_observations}
                   if self.vector_scale_observations else {}),
                **({"system_appearance_observations": self.system_appearance_observations}
                   if self.system_appearance_observations else {}),
                **({"compact_appearance_observation": self.compact_appearance_observation}
                   if self.compact_appearance_observation else {})}


def execute_control(argv: list[str], timeout: int = 90) -> subprocess.CompletedProcess:
    result = subprocess.run(argv, cwd=lt.ROOT, capture_output=True, timeout=timeout)
    if len(result.stdout) + len(result.stderr) > 1024**2:
        raise ValueError("Unbounded simulator-control result")
    return result


def control_status(result: subprocess.CompletedProcess) -> dict:
    """Retain bounded structured control-error identities, never a transcript.

    Domain/code observations explain a fail-closed simctl/codesign refusal. An
    unexpected service/error identity does not authorize foreign app mutation or
    a retry. Actual missing/already-stopped simctl behavior still needs Apple CI.
    """
    matches = re.findall(r"\(domain=([A-Za-z][A-Za-z0-9_.-]{0,127}), code=(-?[0-9]{1,10})\)",
                         result.stderr[:65536].decode("utf-8", errors="replace"))
    return {"exit_code": result.returncode,
            "error_identities": [{"domain": domain, "code": int(code)} for domain, code in matches[:3]]}


def missing_app(result: subprocess.CompletedProcess) -> bool:
    return result.returncode == 2 and {"domain": "NSPOSIXErrorDomain", "code": 2} in control_status(result)["error_identities"]


def stopped_app(result: subprocess.CompletedProcess) -> bool:
    return result.returncode == 0 or (result.returncode == 3 and
        {"domain": "NSPOSIXErrorDomain", "code": 3} in control_status(result)["error_identities"])


def installed_identity(result: subprocess.CompletedProcess, bundle_id: str, signed_hash: str, plist_hash: str) -> bool:
    if result.returncode != 0:
        return False
    path = Path(result.stdout.decode("utf-8").strip())
    if not path.is_absolute() or path.name != "NativeCmpkitLibraryTests.app" or path.is_symlink() or not path.is_dir():
        return False
    for name, digest in [(APP_EXECUTABLE, signed_hash), ("Info.plist", plist_hash)]:
        file = path / name
        if not file.is_file() or file.is_symlink() or file.stat().st_nlink != 1 or lt.sha256(file) != digest:
            return False
    return plistlib.loads((path / "Info.plist").read_bytes()).get("CFBundleIdentifier") == bundle_id


def forward_application(argv: list[str], protocol: NativeProtocol, timeout: int = APP_TIMEOUT_SECONDS,
                        environment: dict[str, str] | None = None) -> dict:
    """Preserve real frames verbatim through KGP, while bounding owned transport."""
    started = time.monotonic()
    transport = {"started_at_utc": lt.utc_now(), "timeout_seconds": timeout, "console_process_exit": None,
                 "console_process_exit_after_cleanup": None, "console_cleanup_requested": False}
    options = {} if environment is None else {"env": environment}
    process = subprocess.Popen(argv, cwd=lt.ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               start_new_session=True, bufsize=0, **options)
    pending = b""
    stage = "protocol-read"
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while selector.get_map():
                stage = "protocol-read"
                if time.monotonic() - started > timeout:
                    raise TimeoutError("Owned UIKit application timed out")
                if shutil.disk_usage(lt.ROOT).free < 8192 * 1024**2:
                    raise OSError("UIKit transport disk reserve unavailable")
                if protocol.image_profile_poll is not None:
                    stage = "owned-image-profile-readiness"
                    protocol.image_profile_poll()
                for key, _ in selector.select(timeout=0.25):
                    stage = "protocol-read"
                    block = os.read(key.fd, 65536)
                    if not block:
                        selector.unregister(key.fileobj)
                        break
                    pending += block
                    while b"\n" in pending:
                        line, pending = pending.split(b"\n", 1)
                        stage = "protocol-decode"
                        text = line.decode("utf-8", errors="strict").rstrip("\r")
                        stage = "protocol-feed"
                        protocol.feed(text)
                        stage = "protocol-forward"
                        sys.stdout.buffer.write(line + b"\n")
                        sys.stdout.buffer.flush()
                    if len(pending) > MAX_LINE_BYTES:
                        raise ValueError("Unbounded incomplete native protocol line")
        if pending:
            stage = "protocol-tail-decode"
            tail = pending.decode("utf-8", errors="strict")
            stage = "protocol-tail-feed"
            protocol.feed(tail)
            stage = "protocol-tail-forward"
            sys.stdout.buffer.write(pending + b"\n")
            sys.stdout.buffer.flush()
        stage = "console-wait"
        result = process.wait(timeout=30)
        stage = "protocol-finish"
        summary = protocol.finish(result)
        return {"process_exit": result, "elapsed_seconds": round(time.monotonic() - started, 2), **summary}
    except BaseException as error:
        # Fixed error type only. Never retain a report/app/environment message.
        transport["error_type"] = type(error).__name__
        transport["failure_stage"] = stage
        transport["failure_reason"] = (TRANSPORT_FAILURE_REASONS.get(str(error), "unclassified")
                                       if isinstance(error, ValueError) else "unclassified")
        raise
    finally:
        transport["console_process_exit"] = process.poll()
        try:
            if transport["console_process_exit"] is None:
                # Only our xcrun console group, NOT an inferred native app PID.
                transport["console_cleanup_requested"] = True
                lt.terminate_owned(process)
        finally:
            transport.update(finished_at_utc=lt.utc_now(), elapsed_seconds=round(time.monotonic() - started, 2),
                             console_process_exit_after_cleanup=process.poll())
            protocol.transport_observation = transport
            if process.stdout:
                process.stdout.close()


def application_test_focus(arguments: list[str], image_diagnostics: str | None = None) -> str | None:
    if image_diagnostics is not None:
        if image_diagnostics != "darwin-tools":
            raise ValueError("Unknown native image diagnostic mode")
        # The identical source methods have deliberately distinct diagnostic
        # requests. A finite transport flag binds the new attempt; do not infer
        # it from ambiguous filter order or reinterpret an old strict request.
        extra = set(arguments) - TEST_ARGUMENTS
        if len(arguments) == 3 and len(extra) == 1 and TEST_ARGUMENTS <= set(arguments):
            argument = next(iter(extra))
            prefix = "--ktest_gradle_filter="
            if argument.startswith(prefix):
                patterns = argument.removeprefix(prefix).split(",")
                for focus in lt.IOS_IMAGE_DARWIN_FOCUSES:
                    reviewed = lt.ui_application_focus_filter(focus).split(",")
                    if len(patterns) == len(reviewed) and len(set(patterns)) == len(patterns) and set(patterns) == set(reviewed):
                        return focus
        raise ValueError("Darwin diagnostics require exactly their reviewed image methods")
    if len(arguments) == 2 and set(arguments) == TEST_ARGUMENTS:
        return None
    if len(arguments) == 3:
        for focus, argument in APPLICATION_FOCUS_ARGUMENTS.items():
            if focus in lt.IOS_IMAGE_DARWIN_FOCUSES:
                continue  # This independent mode requires its explicit transport flag.
            if set(arguments) == TEST_ARGUMENTS | {argument}:
                return focus
        # Gradle/KGP can enumerate include-pattern sets in a different order.
        # Accept exactly a reviewed focus's method identities, never omissions,
        # duplicates, wildcards, unreviewed methods or a second filter argument.
        extra = set(arguments) - TEST_ARGUMENTS
        if len(extra) == 1 and TEST_ARGUMENTS <= set(arguments):
            argument = next(iter(extra))
            prefix = "--ktest_gradle_filter="
            if argument.startswith(prefix):
                patterns = argument.removeprefix(prefix).split(",")
                for focus in lt.UI_APPLICATION_FOCUS_SPECS:
                    if focus in lt.IOS_IMAGE_DARWIN_FOCUSES:
                        continue
                    reviewed = lt.ui_application_focus_filter(focus).split(",")
                    if len(patterns) == len(reviewed) and len(set(patterns)) == len(patterns) and set(patterns) == set(reviewed):
                        return focus
    raise ValueError("Only full KGP protocol or one exact reviewed native UI selection is allowed")


def application_host(binary_relative: str, focus: str | None) -> dict:
    # Exact finite owning module/directory, not a guessed prefix or globals
    # patched for another library. The canonical filesystem path is checked in run.
    directory = Path(binary_relative).parent.as_posix()
    matching = [(module, host) for module, host in APPLICATION_HOSTS.items()
                if directory == host["binary_directory"]]
    if len(matching) != 1:
        raise ValueError("Unknown library application executable directory")
    module, host = matching[0]
    if focus is not None and lt.UI_APPLICATION_FOCUS_SPECS[focus].get("module", "calf-ui") != module:
        raise ValueError("Application test selection belongs to a different owning module")
    return {"module": module, **host}


def profile_debug_entitlements(focus: str | None) -> dict | None:
    """One disposable failed-profile recovery only; never public binary signing."""
    if focus == lt.IOS_IMAGE_PROFILE_RECOVERY_FOCUS:
        return {"get-task-allow": True}
    if focus is not None and focus not in lt.UI_APPLICATION_FOCUS_SPECS:
        raise ValueError("Unknown verification signing mode")
    return None


def sign_owned_debug_profile_application(root: Path, app: Path, focus: str, details: dict) -> subprocess.CompletedProcess:
    """Ad-hoc sign an owned local profile app with one explicit debugger flag.

    No credentials, elevation, device configuration, public frameworks or package
    signing. A readback is a prerequisite observation, not attach authorization or
    a successful profile. All other modes retain their exact previous signer.
    """
    requested = profile_debug_entitlements(focus)
    if requested is None or not isinstance(details, dict) or details:
        raise ValueError("Use one new finite debug-profile signing receipt")
    app = lt.safe_path(root, app.relative_to(root).as_posix())
    base = lt.safe_path(root, "build/ci-verification")
    if (not app.is_relative_to(base) or app.parent == base or
            app.name != "NativeCmpkitLibraryTests.app" or not app.is_dir()):
        raise ValueError("Only an owned disposable verification bundle may be signed")
    path = lt.safe_path(root, (app.parent / "owned-image-profile-debug.entitlements.plist").relative_to(root).as_posix())
    payload = plistlib.dumps(requested, sort_keys=True)
    details.update(policy="failed-darwin-profile-recovery-only", ios_debug_requested=True,
                   mac_debug_requested=False, requested_entitlements_sha256=hashlib.sha256(payload).hexdigest(),
                   owned_entitlement_input_removed=False, public_framework_or_package_signing=False,
                   raw_entitlements_or_paths_uploaded=False, attach_authorization_proven=False)
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns,
                          s.st_uid, s.st_nlink, s.st_mode)
    # Exclusive/no-follow and0600: never replace an earlier/foreign input.
    stream = open(path, "xb", opener=lambda name, flags: os.open(name, flags | os.O_NOFOLLOW, 0o600))
    expected = identity(os.fstat(stream.fileno()))
    try:
        with stream:
            stream.write(payload)
            stream.flush()
            expected = identity(os.fstat(stream.fileno()))
        result = execute_control(["/usr/bin/codesign", "--force", "--sign", "-", "--entitlements",
                                  str(path), str(app)], 120)
        if result.returncode == 0:
            import apple_image_profile
            observed = execute_control(["/usr/bin/codesign", "--display", "--entitlements", ":-", str(app)], 30)
            flags = apple_image_profile.debug_entitlement_observation(observed)
            details["signed_debug_flag_observation"] = flags
            if not flags["ios_debug_allowed"] or flags["mac_debug_allowed"]:
                raise ValueError("The owned profile app lacks its exact requested signed debug flag")
        return result
    finally:
        before = path.lstat()
        if (identity(before) != expected or not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or
                before.st_uid != os.getuid() or before.st_size != len(payload)):
            raise ValueError("Debug-profile input ownership changed; refuse deletion")
        body = path.read_bytes()
        if body != payload or identity(path.lstat()) != expected or path.is_symlink():
            raise ValueError("Debug-profile input payload changed; refuse deletion")
        path.unlink()
        details["owned_entitlement_input_removed"] = True


def run(binary_relative: str, arguments: list[str], *, image_diagnostics: str | None = None) -> dict:
    if platform.system() != "Darwin" or platform.machine().lower() != "arm64":
        raise ValueError("Genuine UIKit application execution requires the actual macOS Arm64 host")
    focus = application_test_focus(arguments, image_diagnostics)
    host = application_host(binary_relative, focus)
    device = os.environ.get("NATIVECMPKIT_UIKIT_SIMULATOR", "")
    if not runtime.UUID.fullmatch(device):
        raise ValueError("Use the exact task-recorded simulator, not a guessed/default device")
    root = lt.ROOT
    binary = lt.safe_path(root, binary_relative)
    expected = lt.safe_path(root, host["binary_directory"])
    if binary.parent != expected or binary.suffix != ".kexe" or not os.access(binary, os.X_OK):
        raise ValueError("Expected the distinct linked application test executable")
    result_relative = os.environ.get("NATIVECMPKIT_UIKIT_RESULT_ROOT", "")
    result_root = lt.safe_path(root, result_relative)
    if host["module"] in {"calf-file-picker", "calf-webview"}:
        if result_root.name not in {"native-ui-application", host["receipt_subdirectory"]}:
            raise ValueError("Library receipts require their finite owning application output")
        result_root = lt.safe_path(root, (result_root.parent / host["receipt_subdirectory"]).relative_to(root).as_posix())
    base = lt.safe_path(root, "build/ci-verification")
    if result_root == base or not result_root.is_relative_to(base):
        raise ValueError("Application receipts must stay in the owned verification output")
    token = uuid.uuid4().hex
    output = lt.safe_path(root, (result_root / token).relative_to(root).as_posix())
    output.mkdir(parents=True, exist_ok=False)
    receipt = {"schema_version": 1, "task": host["task"], "started_at_utc": lt.utc_now(),
               "transport_passed": False, "packages_published": False, "release_readiness_certified": False,
               "explicit_test_focus": focus,
               "scope": "Owned real UIKit application transport. Real KGP TeamCity/JUnit decides testcase failures; launch/completion alone never establishes library/release success.",
               "steps": {}, "cleanup": {}, "application_protocol": None}
    if focus in lt.IOS_IMAGE_DARWIN_FOCUSES:
        receipt.update(image_diagnostics_mode="darwin-tools", strict_runtime_assertions_attested=False)
    app = output / "NativeCmpkitLibraryTests.app"
    bundle_id = None
    signed_hash = plist_hash = None
    installed = False
    phase = "runtime-preflight"
    protocol = NativeProtocol()
    appearance_driver = None
    image_profile_driver = None
    native_environment = None
    try:
        before = runtime.capture(expected_arch="arm64", apple=True, device=device, require_booted=True, require_clean=True)
        receipt.update(source_revision=before["source_revision"], source_tree_dirty=before["source_tree_dirty"], runtime_before=before)
        binary_hash = lt.sha256(binary)
        identity = macho_simulator_identity(binary)
        receipt.update(binary_path=binary_relative, binary_sha256=binary_hash, macho=identity)
        bundle_id = f"io.github.apdelrahman1911.nativecmpkit.verification.ui.r{before['source_revision'][:12]}.t{token}"
        receipt["bundle_id"] = bundle_id
        protocol = NativeProtocol(bundle_id=bundle_id)
        phase = "foreign-app-preflight"
        preexisting = execute_control(["/usr/bin/xcrun", "simctl", "get_app_container", device, bundle_id, "app"])
        receipt["steps"][phase] = {**control_status(preexisting), "preexisting_app_absence_verified": missing_app(preexisting)}
        if not missing_app(preexisting):
            raise ValueError("Foreign installed app or unknown absence check; never overwrite it")
        phase = "local-bundle"
        if shutil.disk_usage(root).free < 8192 * 1024**2 + binary.stat().st_size * 2:
            raise OSError("Application staging would violate the owned disk reserve")
        app.mkdir()
        shutil.copy2(binary, app / APP_EXECUTABLE)
        (app / "Info.plist").write_bytes(plistlib.dumps(app_information(bundle_id, identity["minimum_os"]), sort_keys=True))
        phase = "adhoc-sign-local-verification-app"
        if profile_debug_entitlements(focus) is not None:
            debug_details = {}
            receipt["steps"][phase] = {"remote_signing_or_publication": False, "debug_profile": debug_details}
            sign = sign_owned_debug_profile_application(root, app, focus, debug_details)
            receipt["steps"][phase].update(control_status(sign))
        else:
            sign = execute_control(["/usr/bin/codesign", "--force", "--sign", "-", str(app)], 120)
            receipt["steps"][phase] = {**control_status(sign), "remote_signing_or_publication": False}
        if sign.returncode:
            raise RuntimeError("Ad-hoc local application signing failed")
        signed_hash, plist_hash = lt.sha256(app / APP_EXECUTABLE), lt.sha256(app / "Info.plist")
        signed_identity = macho_simulator_identity(app / APP_EXECUTABLE)
        if signed_identity != identity:
            raise ValueError("Signing changed the linked architecture/platform/UUID identity")
        receipt.update(signed_application_executable_sha256=signed_hash, application_plist_sha256=plist_hash)
        receipt["signed_macho_identity"] = signed_identity
        phase = "install-owned-app"
        result = execute_control(["/usr/bin/xcrun", "simctl", "install", device, str(app)], 180)
        receipt["steps"][phase] = control_status(result)
        # Reconcile even an uncertain install failure before any cleanup/retry.
        container = execute_control(["/usr/bin/xcrun", "simctl", "get_app_container", device, bundle_id, "app"])
        installed = installed_identity(container, bundle_id, signed_hash, plist_hash)
        receipt["steps"][phase]["installed_owned_bytes_verified"] = installed
        receipt["steps"][phase]["container_status"] = control_status(container)
        if result.returncode or not installed:
            raise RuntimeError("Owned installation/byte readback failed; do not retry or remove foreign data")
        if host["module"] == "calf-ui" and focus in (None, lt.IOS_IMAGE_MEMORY_FOCUS, *lt.IOS_IMAGE_DARWIN_FOCUSES):
            import apple_image_profile
            phase = "prepare-owned-image-memory-profile"
            image_profile_driver = apple_image_profile.ImageProfileDriver(
                root, output, device, bundle_id, signed_hash, plist_hash, execute_control)
            native_environment = image_profile_driver.prepare()
            protocol.image_profile_request = image_profile_driver.observe_native_request
            protocol.image_profile_poll = image_profile_driver.poll
        if host["module"] == "calf-ui" and focus in (
                None, lt.IOS_VECTOR_THEME_FOCUS, lt.IOS_SYSTEM_APPEARANCE_FOCUS):
            phase = "prepare-owned-simulator-system-appearance"
            appearance_driver = simulator_appearance.AppearanceDriver(device, execute_control)
            appearance_driver.start()
            protocol.system_appearance_request = appearance_driver.request
        phase = "launch-and-real-test-transport"
        receipt["application_protocol"] = forward_application(
            ["/usr/bin/xcrun", "simctl", "launch", "--console", "--terminate-running-process", device, bundle_id, *arguments],
            protocol, timeout=application_timeout_seconds(focus),
            **({"environment": native_environment} if native_environment is not None else {}))
        if appearance_driver is not None:
            phase = "restore-owned-simulator-system-appearance"
            appearance_driver.restore()
            if any((c["classname"], c["name"]) == SYSTEM_APPEARANCE_CASE and c["status"] == "passed"
                   for c in receipt["application_protocol"]["testcases"]):
                if not simulator_appearance.validate_receipt(appearance_driver.receipt, device):
                    raise ValueError("Passing native system appearance lacks actual control/readback/restoration evidence")
        phase = "post-runtime-and-binary"
        after = runtime.capture(expected_arch="arm64", apple=True, device=device, require_booted=True, require_clean=True)
        receipt["runtime_after"] = after
        receipt["binary_sha256_after"] = lt.sha256(binary)
        if before["source_revision"] != after["source_revision"] or before["simulator"] != after["simulator"] or receipt["binary_sha256_after"] != binary_hash:
            raise ValueError("Selected device/source/linked binary changed during native execution")
        receipt["transport_passed"] = True
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        receipt["error"] = {"phase": phase, "type": type(error).__name__}
        # No arbitrary exception/app/environment transcript is archived.
    finally:
        if image_profile_driver is not None:
            image_profile_driver.close()
            receipt["image_memory_profile"] = image_profile_driver.receipt
            if not (image_profile_driver.receipt.get("owned_ack_removed") is True and
                    image_profile_driver.receipt.get("owned_readiness_removed") is True and
                    image_profile_driver.receipt.get("owned_private_tree_removed") is True):
                receipt["transport_passed"] = False
        if appearance_driver is not None:
            try:
                appearance_driver.restore()
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                appearance_driver.receipt["error_type"] = type(error).__name__
                receipt["transport_passed"] = False
            receipt["system_appearance_driver"] = appearance_driver.receipt
        if protocol.transport_observation is not None:
            receipt["application_transport"] = protocol.transport_observation
        if not receipt["transport_passed"] and phase == "launch-and-real-test-transport":
            receipt["application_protocol_partial"] = protocol.partial()
            observed = protocol.transport_observation or {}
            if (focus == lt.IOS_IMAGE_PROFILE_RECOVERY_FOCUS and installed and
                    protocol.observed_launch_pid is None and protocol.active is None and
                    observed.get("failure_reason") == "nonzero-console-exit"):
                # A pre-PID refusal cannot authorize reading a guessed process's
                # crash/heap. One read-only unique bundle/time system-log query
                # supplies bounded observations, never launch/native/profile success.
                import apple_launch_diagnostics
                try:
                    receipt["owned_launch_diagnostics"] = apple_launch_diagnostics.collect(
                        device, bundle_id, observed.get("started_at_utc", ""),
                        observed.get("finished_at_utc", ""), execute_control)
                except (OSError, ValueError, RuntimeError, TypeError, KeyError,
                        RecursionError, subprocess.SubprocessError) as error:
                    receipt["owned_launch_diagnostics"] = {
                        "status": "unavailable", "error_type": type(error).__name__,
                        "raw_messages_paths_or_log_uploaded": False,
                        "root_cause_proven": False, "native_functionality_verified": False}
            try:
                receipt["owned_crash_diagnostics"] = crashes.collect(
                    Path.home() / "Library/Logs/DiagnosticReports", bundle_id=bundle_id,
                    pid=protocol.observed_launch_pid, executable_uuid=identity.get("executable_uuid"),
                    executable=APP_EXECUTABLE, started_utc=observed.get("started_at_utc", ""),
                    ended_utc=observed.get("finished_at_utc", ""))
            except (OSError, ValueError, TypeError, KeyError, RecursionError) as error:
                receipt["owned_crash_diagnostics"] = {"status": "unavailable", "error_type": type(error).__name__,
                    "raw_reports_uploaded": False, "native_functionality_verified": False}
            # A missing/bad/matching report NEVER changes the failed transport.
        if protocol.startup_failure_observation is not None:
            receipt["startup_failure_observation"] = protocol.startup_failure_observation
            receipt["transport_passed"] = False
        if installed:
            try:
                lease = execute_control(["/usr/bin/xcrun", "simctl", "get_app_container", device, bundle_id, "app"])
                still_owned = installed_identity(lease, bundle_id, signed_hash, plist_hash)
                receipt["cleanup"]["owned_app_identity_reverified"] = still_owned
                if not still_owned:
                    raise ValueError("Installed app identity changed; refuse foreign cleanup")
                stop = execute_control(["/usr/bin/xcrun", "simctl", "terminate", device, bundle_id], 60)
                # Normally exitProcess already stopped it. The exact container
                # identity, not a guessed PID or ignored error, authorizes uninstall.
                receipt["cleanup"]["terminate_exit_code"] = stop.returncode
                receipt["cleanup"]["terminate_status"] = control_status(stop)
                receipt["cleanup"]["owned_app_stopped_verified"] = stopped_app(stop)
                uninstall = execute_control(["/usr/bin/xcrun", "simctl", "uninstall", device, bundle_id], 120)
                gone = execute_control(["/usr/bin/xcrun", "simctl", "get_app_container", device, bundle_id, "app"])
                receipt["cleanup"].update(uninstall_exit_code=uninstall.returncode,
                                           uninstall_status=control_status(uninstall),
                                           absence_status=control_status(gone),
                                           owned_app_absence_verified=missing_app(gone))
                if uninstall.returncode or not missing_app(gone):
                    raise RuntimeError("Owned application uninstall/absence is unverified")
                if not stopped_app(stop):
                    # Still release our verified installation on a stop error;
                    # preserve the uncertainty as failure, never silent success.
                    raise RuntimeError("Owned application stop/termination is unverified")
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                receipt["cleanup"]["error_type"] = type(error).__name__
                receipt["transport_passed"] = False
        else:
            receipt["cleanup"]["foreign_app_mutated"] = False
        if app.exists():
            try:
                if app.is_symlink() or app.parent != output:
                    raise ValueError("Local application ownership changed")
                shutil.rmtree(app)  # only this invocation's disposable bundle.
                receipt["cleanup"]["owned_local_bundle_removed"] = True
            except (OSError, ValueError) as error:
                receipt["cleanup"]["local_error_type"] = type(error).__name__
                receipt["transport_passed"] = False
        receipt["finished_at_utc"] = lt.utc_now()
        lt.write_json(output / "receipt.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--image-diagnostics", choices=("darwin-tools",))
    options, arguments = parser.parse_known_args()
    try:
        binary = options.binary.absolute().relative_to(lt.ROOT).as_posix()
        result = run(binary, arguments, image_diagnostics=options.image_diagnostics)
        print("NATIVECMPKIT_UIKIT_TRANSPORT passed=" + str(result["transport_passed"]).lower(), flush=True)
        return 0 if result["transport_passed"] else 2
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print("Owned UIKit application transport refused: " + type(error).__name__, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
