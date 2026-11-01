#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Missing-host full Desktop graphs only; not advisory/native/security acceptance.

Two byte-pinned historical collectors, once each, serially. No native selector,
trust init, publication, advisory query, arbitrary task or accepted Linux replay.
This is bounded acquisition, not a sandbox or a trusted-builder attestation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import stat
import sys
import time

import library_tests as lt

PROFILE = "webview-desktop-security-regressions"
ROUTES = {
    "desktop-macos-arm64": ("Darwin", "arm64", "mac-aarch64", "tls-rendering-cookies-policy"),
    "desktop-windows-x64": ("Windows", "x64", "win", "tls-rendering-cookies-policy"),
    "desktop-linux-arm64": ("Linux", "arm64", "linux-aarch64", "tls-rendering-cookies-policy-media"),
    "desktop-macos-x64": ("Darwin", "x64", "mac", "tls-rendering-cookies-policy"),
}
PROJECTS = (
    ":calf-camera-picker", ":calf-core", ":calf-cupertino-icons", ":calf-file-picker",
    ":calf-file-picker-coil", ":calf-geo", ":calf-io", ":calf-maps", ":calf-navigation",
    ":calf-permissions",
    *(":calf-permissions:calf-permissions-" + name for name in (
        "background-location", "bluetooth", "calendar", "camera", "contacts", "core",
        "gallery", "location", "microphone", "notifications", "wifi")),
    ":calf-share", ":calf-ui", ":calf-webview",
)
COLLECTORS = (
    {
        "phase": "runtime", "bytes": 3531,
        "sha256": "317a75102b265a173705571cb384f55a866e48e5c9f794eb07c17efb3890c639",
        "source": "docs/development/evidence/desktop-resolved-dependencies-20261030/runtime001/acquisition.init.gradle",
        "graph": "build/ci-verification/desktop-dependency-audit-20261030/graph.json",
        "configurations": ("desktopRuntimeClasspath",),
        "scope": "All24 declared library desktopRuntimeClasspath configurations; external artifacts only. No Gradle/plugin/Android/Apple/npm/Cargo graph, independent trust, runtime correctness, publication or release certification.",
    },
    {
        "phase": "compile-test", "bytes": 3688,
        "sha256": "821056946d590f14ee7f88d807d3c88f0b3a32a885f193063383cc7eb6a66a6e",
        "source": "docs/development/evidence/desktop-resolved-dependencies-20261030/compile-test002/acquisition.init.gradle",
        "graph": "build/ci-verification/desktop-dependency-audit-supplement-20261030/graph.json",
        "configurations": ("desktopCompileClasspath", "desktopTestRuntimeClasspath"),
        "scope": "All48 declared library desktopCompileClasspath/desktopTestRuntimeClasspath configurations; supplementary to separately preserved24 runtime graphs; external artifacts only. No Gradle/plugin/Android/Apple/npm/Cargo graph, independent trust, runtime correctness, publication or release certification.",
    },
)
TASK = "nativeCmpKitAuditDesktopDependencies"
PRIVATE = "build/ci-verification/desktop-dependency-capture-private"
FLAT = "build/ci-runtime/desktop-dependencies-"
RUNTIME = "build/ci-runtime/actual.json"
WORKFLOW = ".github/workflows/gradle.yml"
TIMEOUT_SECONDS = 600
DISK_RESERVE_MIB = 8192
MAX_BYTES = 32 * 1024 * 1024
STOP_REASONS = {
    "Disk reserve unavailable; command not started",
    "Disk reserve reached; terminated only this invocation's process group",
    "Timeout; terminated only this invocation's process group",
}


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def identity(info: os.stat_result) -> tuple:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size, info.st_mtime_ns)


def regular(path: Path) -> os.stat_result:
    info = path.lstat()
    need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "Nonregular or linked capture input/output")
    return info


def read(root: Path, relative: str) -> tuple[bytes, tuple]:
    path = lt.safe_path(root, relative)
    before = regular(path)
    need(before.st_size <= MAX_BYTES, "Capture document exceeds bounded size")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    with os.fdopen(os.open(path, flags), "rb") as handle:
        need(identity(os.fstat(handle.fileno())) == identity(before), "Capture file changed before read")
        value = handle.read(MAX_BYTES + 1)
        need(identity(os.fstat(handle.fileno())) == identity(before), "Capture file changed during read")
    need(identity(regular(path)) == identity(before) and len(value) == before.st_size,
         "Capture file changed after read")
    return value, identity(before)


def fact(relative: str, value: bytes) -> dict:
    return {"path": relative, "bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}


def absent(root: Path, relative: str) -> Path:
    path = lt.safe_path(root, relative)
    need(not path.exists(), "Preserve existing capture/native evidence; no overwrite or retry")
    return path


def directory(root: Path, relative: str, expected: tuple | None = None) -> tuple:
    info = lt.safe_path(root, relative).lstat()
    result = (info.st_dev, info.st_ino)
    need(stat.S_ISDIR(info.st_mode) and (expected is None or result == expected),
         "Owned capture directory changed")
    if relative.startswith(PRIVATE) and os.name != "nt":
        need(stat.S_IMODE(info.st_mode) == 0o700, "Private capture directory is not owner-only")
    return result


def write(root: Path, relative: str, value: bytes) -> tuple[dict, tuple]:
    path = absent(root, relative)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    with os.fdopen(os.open(path, flags, 0o600), "wb") as handle:
        handle.write(value)
    copied, held = read(root, relative)
    need(copied == value, "Exclusive capture copy differs from original bytes")
    return fact(relative, copied), held


def write_json(root: Path, relative: str, value: dict) -> tuple[dict, tuple]:
    return write(root, relative, (json.dumps(value, sort_keys=True, indent=2) + "\n").encode())


def document(value: bytes) -> dict:
    def pairs(items):
        result = {}
        for key, item in items:
            need(key not in result, "Duplicate capture JSON key")
            result[key] = item
        return result
    def invalid_constant(_):
        raise ValueError("Nonfinite capture JSON value")
    result = json.loads(value, object_pairs_hook=pairs, parse_constant=invalid_constant)
    need(isinstance(result, dict), "Capture JSON must be an object")
    return result


def snapshot(root: Path) -> dict:
    files = lt.snapshot_inputs(root)  # Full map, never the cache-selected module subset.
    need(isinstance(files, dict) and bool(files), "Missing complete configured input map")
    files = dict(files)
    for relative in (WORKFLOW, *(item["source"] for item in COLLECTORS)):
        value, _ = read(root, relative)
        files[relative] = hashlib.sha256(value).hexdigest()
    for relative, digest in files.items():
        need(isinstance(relative, str) and isinstance(digest, str) and
             re.fullmatch(r"[0-9a-f]{64}", digest), "Malformed configured input map")
        path = lt.safe_path(root, relative)
        before = identity(regular(path))
        need(lt.sha256(path) == digest and identity(regular(path)) == before,
             "Configured input changed during full snapshot")
    return files


def collector(root: Path, item: dict, relative: str) -> tuple[bytes, tuple]:
    value, held = read(root, relative)
    need(len(value) == item["bytes"] and hashlib.sha256(value).hexdigest() == item["sha256"],
         "Review exact archived/private collector bytes")
    return value, held


def route(profile: str, slot: str, environment: dict) -> tuple:
    need(profile == PROFILE and slot in ROUTES, "Only four missing-host security graph routes are admitted")
    selected = ROUTES[slot]
    need((environment.get("SLOT"), environment.get("SUITE"), environment.get("TEST_MODULES"),
          environment.get("TEST_FOCUS")) == (slot, "desktop", "calf-webview", selected[3]),
         "Foreign slot/suite/module/focus; no native or accepted-host fallback")
    arch = platform.machine().lower()
    arch = {"amd64": "x64", "x86_64": "x64", "aarch64": "arm64"}.get(arch, arch)
    need((platform.system(), arch) == selected[:2], "Current host differs from finite graph route")
    return selected


def runtime(root: Path, selected: tuple) -> tuple[dict, bytes, tuple]:
    value, held = read(root, RUNTIME)
    context = document(value)
    revision = lt.git_revision(root)
    need(re.fullmatch(r"[0-9a-f]{40}", revision) is not None and
         type(context.get("schema_version")) is int and context["schema_version"] == 1 and
         context.get("source_tree_dirty") is False and
         context.get("source_revision") == revision, "Current clean source/runtime revision is required")
    host = context.get("host")
    need(isinstance(host, dict) and (host.get("system"), host.get("architecture")) == selected[:2],
         "Actual runtime host differs from finite graph route")
    return context, value, held


def command(system: str, init_path: Path) -> list[str]:
    return [".\\gradlew.bat" if system == "Windows" else "./gradlew", "--no-daemon",
            "--no-configuration-cache", "--max-workers=2", "--no-parallel", "--console=plain",
            "-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8",
            "-Pkotlin.compiler.execution.strategy=in-process", "--init-script", str(init_path), TASK]


def coordinate(item: dict) -> tuple:
    need(isinstance(item, dict), "Malformed external module/artifact identity")
    result = tuple(item.get(key) for key in ("group", "name", "version"))
    need(all(isinstance(value, str) and 0 < len(value) <= 1024 and
             not any(ord(char) < 33 or char in ":/\\" for char in value) for value in result),
         "Malformed external module coordinate")
    return result


def graph(value: bytes, item: dict) -> dict:
    data = document(value)
    need(set(data) == {"scope", "configurations", "complete", "packages_published"} and
         data["scope"] == item["scope"] and data["complete"] is True and data["packages_published"] is False,
         "Foreign/incomplete graph scope; no advisory acceptance")
    rows = data["configurations"]
    expected = {(project, name) for project in PROJECTS for name in item["configurations"]}
    need(isinstance(rows, list) and len(rows) == len(expected), "Missing graph configuration rows")
    seen, modules, artifacts = set(), set(), {}
    for row in rows:
        need(isinstance(row, dict) and set(row) ==
             {"project", "configuration", "modules", "artifacts", "unresolved", "complete"},
             "Foreign graph row schema")
        need(isinstance(row["project"], str) and isinstance(row["configuration"], str), "Malformed graph row identity")
        key = (row["project"], row["configuration"])
        need(key in expected and key not in seen and row["complete"] is True and row["unresolved"] == [],
             "Duplicate/foreign/unresolved/incomplete graph row")
        seen.add(key)
        need(isinstance(row["modules"], list) and isinstance(row["artifacts"], list), "Malformed graph lists")
        current = set()
        for module in row["modules"]:
            need(isinstance(module, dict) and set(module) == {"group", "name", "version"}, "Foreign module schema")
            module_key = coordinate(module)
            need(module_key not in current, "Duplicate external module in graph row")
            current.add(module_key)
        modules.update(current)  # allComponents includes artifactless and unexpected modules.
        row_artifacts = set()
        for artifact in row["artifacts"]:
            need(isinstance(artifact, dict) and set(artifact) ==
                 {"group", "name", "version", "filename", "bytes", "sha256"}, "Foreign artifact schema")
            module_key, name = coordinate(artifact), artifact["filename"]
            need(module_key in current and isinstance(name, str) and 0 < len(name) <= 1024 and
                 name not in {".", ".."} and not any(ord(char) < 32 or char in "/\\:" for char in name) and
                 type(artifact["bytes"]) is int and artifact["bytes"] >= 0 and
                 isinstance(artifact["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"]),
                 "Foreign/nonregular artifact identity")
            key, content = (*module_key, name), (artifact["bytes"], artifact["sha256"])
            need(key not in row_artifacts and (key not in artifacts or artifacts[key] == content),
                 "Duplicate/conflicting external artifact identity")
            row_artifacts.add(key)
            artifacts[key] = content
    need(seen == expected, "Incomplete exact project/configuration identity set")
    return {"configurations": len(rows), "external_coordinates": len(modules), "artifacts": len(artifacts)}


def markers(value: bytes, observed: dict) -> None:
    lines = value.decode("utf-8", errors="replace").splitlines()
    tasks = [(index, line) for index, line in enumerate(lines) if line.strip().startswith("> Task :" + TASK)]
    summaries = [(index, line) for index, line in enumerate(lines) if line.strip().startswith("NATIVECMPKIT_DESKTOP_GRAPH")]
    expected = ("NATIVECMPKIT_DESKTOP_GRAPH configurations=" + str(observed["configurations"]) +
                " external-coordinates=" + str(observed["external_coordinates"]))
    need(len(tasks) == 1 and tasks[0][1] == "> Task :" + TASK and len(summaries) == 1 and
         summaries[0][1] == expected and tasks[0][0] < summaries[0][0], "Missing/duplicate/foreign graph task or summary marker")


def phase(root: Path, item: dict, selected: tuple, init: str, init_identity: tuple,
          owned: dict[str, tuple]) -> tuple[dict, dict[str, tuple[dict, tuple]]]:
    argv = command(selected[0], root / init)
    result = {"phase": item["phase"], "collector_sha256": item["sha256"], "command":
              ["<owned-private-init>" if index == 9 else arg for index, arg in enumerate(argv)], "errors": []}
    copies = {}
    log = PRIVATE + "/" + item["phase"] + ".log"
    started = time.time_ns()
    result["started_at_utc"] = lt.utc_now()
    try:
        for relative, held in owned.items():
            directory(root, relative, held)
        collector(root, item, item["source"])
        need(collector(root, item, init)[1] == init_identity, "Owned private collector identity changed")
        absent(root, log)
        actual = lt.execute(root, argv, lt.safe_path(root, log), TIMEOUT_SECONDS, DISK_RESERVE_MIB)
        need(isinstance(actual, dict) and set(actual) <= {"exit_code", "elapsed_seconds", "stop_reason"} and
             type(actual.get("exit_code")) is int and
             ("elapsed_seconds" not in actual or (type(actual["elapsed_seconds"]) in (int, float) and
              math.isfinite(actual["elapsed_seconds"]) and actual["elapsed_seconds"] >= 0)) and
             ("stop_reason" not in actual or actual["stop_reason"] in STOP_REASONS), "Malformed execution result")
        result["execution"] = actual
        if actual["exit_code"] != 0 or actual.get("stop_reason"):
            result["errors"].append("graph-command-failed")
    except Exception as error:
        result["errors"].append("graph-command-refused:" + type(error).__name__)
    ended = time.time_ns()
    result["ended_at_utc"] = lt.utc_now()
    try:
        collector(root, item, item["source"])
        need(collector(root, item, init)[1] == init_identity, "Owned private collector identity changed")
        for relative, held in owned.items():
            directory(root, relative, held)
    except Exception as error:
        result["errors"].append("collector-or-directory-changed:" + type(error).__name__)
    try:
        raw, raw_identity = read(root, item["graph"])
        result["original_graph"] = fact(item["graph"], raw)
        copy = FLAT + item["phase"] + "-graph.json"
        copies[item["graph"]] = (result["original_graph"], raw_identity)
        copies[copy] = write(root, copy, raw)
        result["copied_graph"] = copies[copy][0]
        need(started - 2_000_000_000 <= raw_identity[-1] <= ended + 2_000_000_000, "Stale graph output")
        result["observed_graph"] = graph(raw, item)
    except Exception as error:
        result["errors"].append("graph-review-refused:" + type(error).__name__)
    try:
        raw, held = read(root, log)
        result["private_log"] = fact(log, raw)
        copies[log] = (result["private_log"], held)
        need(started - 2_000_000_000 <= held[-1] <= ended + 2_000_000_000, "Stale graph execution log")
        need("observed_graph" in result, "Graph marker cannot certify an unreviewed graph")
        markers(raw, result["observed_graph"])
        result["graph_markers_match"] = True
    except Exception as error:
        result["errors"].append("log-review-refused:" + type(error).__name__)
    result["capture_complete"] = not result["errors"]
    return result, copies


def run(root: Path, profile: str, slot: str, *, environment: dict | None = None) -> dict:
    need(not root.is_symlink(), "No symlinked capture checkout")
    root = root.resolve()
    selected = route(profile, slot, os.environ if environment is None else environment)
    context, runtime_bytes, runtime_identity = runtime(root, selected)
    native = "build/ci-verification/" + slot
    flat_paths = [FLAT + name + ".json" for name in
                  ("inputs-before", "inputs-after", "runtime-graph", "compile-test-graph", "receipt")]
    for relative in (native, PRIVATE, *flat_paths, *(str(Path(item["graph"]).parent) for item in COLLECTORS)):
        absent(root, relative)
    before = snapshot(root)
    collector_bytes = [collector(root, item, item["source"])[0] for item in COLLECTORS]
    receipt = {"schema_version": 1, "scope": "Missing-host full Desktop graph acquisition only; independent source/graph/advisory/native/security review remains required.",
               "profile": profile, "slot": slot, "host": {"system": selected[0], "architecture": selected[1]},
               "javafx_classifier_for_independent_review": selected[2], "source_revision": context["source_revision"],
               "runtime": fact(RUNTIME, runtime_bytes), "phases": [], "errors": [], "native_methods_requested": 0,
               "packages_published": False, "advisory_queries_requested": 0, "capture_complete": False}
    copies, inits, owned = {}, {}, {}
    try:
        lt.safe_path(root, "build/ci-verification").mkdir(parents=True, exist_ok=True)
        for relative in (PRIVATE, *(str(Path(item["graph"]).parent) for item in COLLECTORS), PRIVATE + "/init"):
            absent(root, relative).mkdir(mode=0o700)
            owned[relative] = directory(root, relative)
        name = FLAT + "inputs-before.json"
        copies[name] = write_json(root, name, before)
        receipt["inputs_before"] = {**copies[name][0], "files": len(before), "input_digest": lt.input_digest(before)}
        for item, value in zip(COLLECTORS, collector_bytes):
            init = PRIVATE + "/init/" + item["phase"] + ".gradle"
            inits[init] = write(root, init, value)[1]
        for item in COLLECTORS:  # Failure of phase1 never retries or suppresses independent phase2.
            init = PRIVATE + "/init/" + item["phase"] + ".gradle"
            outcome, held = phase(root, item, selected, init, inits[init], owned)
            receipt["phases"].append(outcome)
            copies.update(held)
    finally:
        try:
            after = snapshot(root)
            name = FLAT + "inputs-after.json"
            copies[name] = write_json(root, name, after)
            receipt["inputs_after"] = {**copies[name][0], "files": len(after), "input_digest": lt.input_digest(after)}
            need(after == before, "Full configured source inputs changed during capture")
            need(lt.git_revision(root) == context["source_revision"], "Source revision changed during capture")
            current, held = read(root, RUNTIME)
            need(current == runtime_bytes and held == runtime_identity, "Actual runtime receipt changed during capture")
            for relative, (expected, held) in copies.items():
                current, observed = read(root, relative)
                need(fact(relative, current) == expected and observed == held, "Owned graph/input copy changed after capture")
            for relative, held in owned.items():
                directory(root, relative, held)
            receipt["inputs_and_runtime_unchanged"] = True
        except Exception as error:
            receipt["errors"].append("final-binding-refused:" + type(error).__name__)
        try:
            directory(root, PRIVATE, owned[PRIVATE])
            directory(root, PRIVATE + "/init", owned[PRIVATE + "/init"])
            need({path.name for path in lt.safe_path(root, PRIVATE + "/init").iterdir()} ==
                 {Path(relative).name for relative in inits}, "Private init contents changed; preserve unowned files")
            for relative, held in inits.items():
                item = next(item for item in COLLECTORS if Path(relative).stem == item["phase"])
                need(collector(root, item, relative)[1] == held, "Private init ownership changed; preserve substitution")
            for relative in inits:
                lt.safe_path(root, relative).unlink()
            lt.safe_path(root, PRIVATE + "/init").rmdir()
            receipt["owned_private_inits_removed"] = True
        except Exception as error:
            receipt["errors"].append("private-init-cleanup-refused:" + type(error).__name__)
        try:
            absent(root, native)
            receipt["native_slot_output_absent"] = True
        except Exception as error:
            receipt["errors"].append("native-output-absence-refused:" + type(error).__name__)
        receipt["capture_complete"] = (not receipt["errors"] and len(receipt["phases"]) == 2 and
                                       all(item["capture_complete"] for item in receipt["phases"]))
        write_json(root, FLAT + "receipt.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--slot", required=True)
    args = parser.parse_args()
    try:
        receipt = run(lt.ROOT, args.profile, args.slot)
        print(json.dumps({"slot": receipt["slot"], "capture_complete": receipt["capture_complete"],
                          "graph_invocations_recorded": len(receipt["phases"]), "native_methods_requested": 0}))
        return 0 if receipt["capture_complete"] else 1
    except Exception as error:
        print(json.dumps({"capture_complete": False, "error_type": type(error).__name__,
                          "native_methods_requested": 0}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
