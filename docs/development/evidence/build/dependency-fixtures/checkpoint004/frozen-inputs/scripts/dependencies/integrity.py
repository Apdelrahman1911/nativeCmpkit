#!/usr/bin/env python3
"""Explicit, isolated Gradle acquisition/check orchestration; never publish.

Bootstrap writes candidate locks/checksums ONLY in an explicitly marked copy.
Check refuses writer flags and requires an explicitly recorded candidate review.
This is a resource guard and integrity observation, not a security sandbox,
independent provenance, ordinary-repository policy installation or release gate.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

import integrity_model as m

TOOL_DIRECTORY = Path(__file__).resolve().parent
MARKER = ".nativecmpkit-dependency-workspace.json"
ROOT_FILES = {
    "settings.gradle.kts", "settings.gradle", "build.gradle.kts", "build.gradle",
    "gradle.properties", "gradlew", "gradlew.bat", "rust-toolchain.toml",
    "LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", ".gitattributes",
}
IGNORED_DIRECTORIES = {".git", ".gradle", ".kotlin", "build", "target", "node_modules", "__pycache__",
                       ".dependency-cache", ".dependency-home"}
PRIVATE_NAMES = {"local.properties", "key.properties", "signing.properties", ".env", ".netrc", ".npmrc"}
PRIVATE_SUFFIXES = {".jks", ".keystore", ".p12", ".pfx", ".pem", ".key"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def is_integrity_path(name: str) -> bool:
    path = Path(name)
    return (path.name in {"gradle.lockfile", "buildscript-gradle.lockfile"} or
            name.endswith("gradle/verification-metadata.xml") or
            (path.parent.name == "dependency-locks" and path.parent.parent.name == "gradle" and path.suffix == ".lockfile"))


def _selection_roots(root: Path, kind: str) -> list[Path]:
    if kind == "controlled-fixture":
        # Fixture-only local Maven artifacts are intentionally included as inputs.
        return [path for path in root.iterdir() if path.name not in IGNORED_DIRECTORIES and
                not path.name.startswith(".nativecmpkit-")]
    roots = [root / name for name in ROOT_FILES if (root / name).exists()]
    roots.extend(path for path in root.iterdir() if path.name.startswith("calf-") and path.is_dir())
    roots.extend(root / name for name in ("convention-plugins", "sample", "gradle", "kotlin-js-store", "licenses", ".cargo",
                                        "scripts/native", "scripts/dependencies") if (root / name).exists())
    return sorted(set(roots))


def selected_inputs(root: Path, kind: str) -> tuple[dict[str, str], dict[str, str], list[str], list[str]]:
    """Inventory current files, separate mutable Gradle state, retain test topology."""
    files: dict[str, str] = {}
    integrity: dict[str, str] = {}
    directories: set[str] = set()
    topology: set[str] = set()

    def inspect(path: Path) -> None:
        name = path.relative_to(root).as_posix()
        m.relative_path(name)
        m.require(not path.is_symlink(), "Symlinked selected source input")
        if path.name in PRIVATE_NAMES or path.name.startswith(".env.") or path.suffix.lower() in PRIVATE_SUFFIXES:
            return
        m.require(path.is_file(), "Nonregular selected input")
        (integrity if is_integrity_path(name) else files)[name] = m.file_sha256(path)

    for selected in _selection_roots(root, kind):
        m.require(not selected.is_symlink(), "Symlinked selected root")
        if selected.is_file():
            inspect(selected)
            continue
        m.require(selected.is_dir(), "Nonregular selection root")
        for base, children, names in os.walk(selected, followlinks=False):
            base_path = Path(base)
            relative = base_path.relative_to(root).as_posix()
            if relative != ".":
                directories.add(relative)
                if "src" in base_path.relative_to(root).parts:
                    topology.add(relative)
            children[:] = sorted(name for name in children if name not in IGNORED_DIRECTORIES)
            for child in children:
                m.require(not (base_path / child).is_symlink(), "Symlinked source directory")
            for name in sorted(names):
                inspect(base_path / name)
    return dict(sorted(files.items())), dict(sorted(integrity.items())), sorted(topology), sorted(directories)


def source_digest(files: dict[str, str], topology: list[str]) -> str:
    m.manifest_digest(files)
    m.require(topology == sorted(set(topology)), "Duplicate/unsorted source topology")
    for name in topology:
        m.relative_path(name)
    return m.sha256_bytes(m.json_bytes({"files": files, "source_directories": topology}))


def expected_source_projects(source: Path) -> dict[str, dict[str, str]]:
    """Fail-closed parser of THIS repository's literal settings include/rename idiom."""
    settings = m.read_regular(source / "settings.gradle.kts", 1024 * 1024).decode()
    blocks = re.findall(r"(?ms)^include\(\s*(.*?)^\)", settings)
    m.require(len(blocks) == 1, "Expected this repository's single literal include block")
    block = re.sub(r"(?m)//[^\n]*", "", blocks[0])
    paths = re.findall(r'"([^"\n]+)"', block)
    remainder = re.sub(r'"[^"\n]+"', "", block)
    m.require(paths and len(paths) == len(set(paths)) and not remainder.strip(" \t\r\n,"),
              "Computed/duplicate project includes need a deliberate inventory update")
    renames_list = re.findall(r'(?m)^project\("([^"\n]+)"\)\.name = "([a-z][a-z0-9-]*)"\s*$', settings)
    m.require(len(renames_list) == len(re.findall(r'(?m)^project\([^\n]+\)\.name\s*=', settings)), "Unsupported project rename syntax")
    renames = dict(renames_list)
    m.require(len(renames) == len(renames_list) and not set(renames) - set(paths), "Duplicate/unmatched project rename")
    project_map = {":": "."}
    for original in paths:
        m.part_key(original)
        parts = original[1:].split(":")
        for count in range(1, len(parts) + 1):
            directory = "/".join(parts[:count])
            actual = ":" + ":".join(renames.get(":" + ":".join(parts[:index + 1]), part)
                                       for index, part in enumerate(parts[:count]))
            m.require(actual not in project_map or project_map[actual] == directory, "Ambiguous renamed project")
            m.confined(source, directory, must_exist=True)
            project_map[actual] = directory
    includes = re.findall(r'includeBuild\("([^"\n]+)"\)', settings)
    m.require(includes == ["convention-plugins"], "Included-build topology needs explicit tool coverage")
    m.require((source / "convention-plugins/settings.gradle.kts").is_file(), "Standalone convention settings are missing")
    return {".": dict(sorted(project_map.items())), "convention-plugins": {":": "convention-plugins"}}


def _new_workspace_path(destination: Path) -> Path:
    m.require(not destination.exists() and not destination.is_symlink(), "Candidate destination must not already exist")
    m.require(not any(path.is_symlink() for path in destination.absolute().parents), "Symlinked candidate ancestor")
    destination = destination.resolve()
    m.require(not any((path / ".git").exists() for path in destination.parents),
              "Candidate must be outside every existing Git worktree, not under its build directory")
    return destination


def snapshot(source: Path, destination: Path) -> dict:
    source = source.resolve()
    destination = _new_workspace_path(destination)
    m.require(not destination.is_relative_to(source), "Candidate cannot be inside the source checkout")
    files, integrity, topology, directories = selected_inputs(source, "source-snapshot")
    for required in ("gradlew", "build.gradle.kts", "settings.gradle.kts", "gradle/wrapper/gradle-wrapper.properties",
                     "scripts/dependencies/resolve-graphs.init.gradle", "scripts/dependencies/integrity.py"):
        m.require(required in files, f"Missing required candidate source: {required}")
    projects = expected_source_projects(source)
    revision = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    m.require(re.fullmatch(r"[0-9a-f]{40,64}", revision), "Unrecognized source revision identity")
    dirty = bool(subprocess.run(["git", "-C", str(source), "status", "--porcelain", "--untracked-files=normal"],
                                capture_output=True, text=True, check=True).stdout)
    destination.mkdir(parents=True)
    for directory in directories:
        m.confined(destination, directory).mkdir(parents=True, exist_ok=True)
    for name in sorted({**files, **integrity}):
        target = m.confined(destination, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(m.confined(source, name, must_exist=True), target, follow_symlinks=False)
    after = selected_inputs(source, "source-snapshot")
    copied = selected_inputs(destination, "source-snapshot")
    m.require(after[:3] == (files, integrity, topology) and copied[:3] == (files, integrity, topology),
              "Source changed or candidate copy did not preserve exact inputs/topology")
    marker = {"schema_version": 1, "kind": "source-snapshot", "created_utc": utc_now(),
              "source_revision": revision, "source_tree_dirty": dirty, "host": m.host_key(),
              "source_files": files, "source_directories": topology, "source_input_digest": source_digest(files, topology),
              "initial_integrity_files": integrity, "build_roots": sorted(projects), "expected_projects": projects,
              "independent_trust_reviewed": False, "coverage_gaps": list(m.COVERAGE_GAPS)}
    m.write_new(destination / MARKER, m.json_bytes(marker))
    return {"operation": "snapshot", "files": len(files), "source_directories": len(topology),
            "source_input_digest": marker["source_input_digest"], "source_revision": revision,
            "source_tree_dirty": dirty, "gradle_executed": False}


def load_workspace(workspace: Path) -> dict:
    m.require(workspace.is_dir() and not workspace.is_symlink(), "Expected regular candidate workspace")
    m.require(not any(path.is_symlink() for path in workspace.absolute().parents), "Symlinked candidate ancestor")
    m.require(not any((path / ".git").exists() for path in [workspace, *workspace.parents]), "Candidate is inside a Git worktree")
    marker = m.read_json(m.confined(workspace, MARKER, must_exist=True))
    m.require(marker.get("schema_version") == 1 and marker.get("kind") in {"source-snapshot", "controlled-fixture"}, "Invalid candidate marker")
    m.require(marker.get("host") == m.host_key(), "Candidate belongs to a different actual host")
    m.require(marker.get("independent_trust_reviewed") is False, "Candidate marker must not claim independent trust")
    roots = marker.get("build_roots")
    m.require(isinstance(roots, list) and roots == sorted(set(roots)) and "." in roots, "Malformed build-root inventory")
    for root in roots:
        if root != ".":
            m.confined(workspace, root, must_exist=True)
    m.require(set(marker.get("expected_projects", {})) == set(roots), "Missing independent expected-project inventory")
    check_source(workspace, marker)
    return marker


def check_source(workspace: Path, marker: dict) -> dict[str, str]:
    files, integrity, topology, _ = selected_inputs(workspace, marker["kind"])
    m.require(files == marker.get("source_files") and topology == marker.get("source_directories") and
              source_digest(files, topology) == marker.get("source_input_digest"), "Candidate source/configuration/topology changed")
    return integrity


def _graph_file(run_id: str, root: str) -> str:
    return f"build/dependency-integrity/{run_id}/graphs/{m.build_key(root)}/graph.json"


def validate_scheduled_tasks(tasks: object, marker: dict, build_root: str) -> None:
    """Independently check the init-script allowlist and required owner tasks."""
    m.require(isinstance(tasks, list) and 0 < len(tasks) <= m.MAX_ENTRIES,
              "Missing/bounded scheduled-task inventory")
    acquisition = {"nativeCmpkitDependencyGraphPart", "nativeCmpkitDependencyGraph", "nativeCmpkitDependencyInventory"}
    seen = set()
    for item in tasks:
        m.require(isinstance(item, dict), "Malformed scheduled-task entry")
        root, project, task = (item.get(key) for key in ("build_root", "project", "task"))
        m.require(isinstance(root, str) and root in marker["expected_projects"] and
                  isinstance(project, str) and project in marker["expected_projects"][root] and
                  isinstance(task, str) and m.CONFIGURATION.fullmatch(task), "Foreign/malformed scheduled-task identity")
        identity = (root, project, task)
        m.require(identity not in seen and not any(word in task.lower() for word in ("publish", "release", "deploy")),
                  "Duplicate or publishing/release task in acquisition graph")
        m.require(task in acquisition or (marker["kind"] == "source-snapshot" and root == "convention-plugins"),
                  "Non-acquisition library/sample task in graph receipt")
        seen.add(identity)
    expected = {(build_root, project, "nativeCmpkitDependencyGraphPart") for project in marker["expected_projects"][build_root]}
    expected.add((build_root, ":", "nativeCmpkitDependencyGraph"))
    m.require(expected <= seen, "Scheduled-task inventory omitted a required owner/aggregate acquisition")


def validate_graph_tree(workspace: Path, marker: dict, *, run_id: str, mode: str, entry_root: str,
                        verify_locks: bool = True) -> dict:
    m.require(m.RUN_ID.fullmatch(run_id) and mode in {"bootstrap", "check"}, "Invalid run identity")
    visited: set[str] = set()
    used_files: set[str] = set()
    totals = {"projects": 0, "configurations": 0, "resolved_configurations": 0, "artifact_view_outputs": 0}
    external_modules: set[tuple[str, str, str]] = set()
    lock_files: set[str] = set()

    def visit(build_root: str, path: str) -> None:
        m.require(build_root not in visited and build_root in marker["build_roots"] and path == _graph_file(run_id, build_root),
                  "Duplicate/foreign/misrouted included-build receipt")
        visited.add(build_root)
        used_files.add(path)
        graph = m.read_json(m.confined(workspace, path, must_exist=True))
        m.require(graph.get("schema_version") == 1 and graph.get("record_type") == "build-graph" and
                  graph.get("run_id") == run_id and graph.get("mode") == mode and graph.get("build_root") == build_root and
                  graph.get("host") == marker["host"] and graph.get("source_input_digest") == marker["source_input_digest"] and
                  graph.get("gradle_version") == m.GRADLE_VERSION and graph.get("java_major") == 17 and graph.get("complete") is True,
                  "Incomplete/stale/foreign build receipt")
        for flag in ("ordinary_build_policy_installed", "independent_trust_reviewed", "settings_script_graph_acquired", "detached_graph_inventory_complete"):
            m.require(graph.get(flag) is False, "Receipt exaggerates unsupported integrity coverage")
        validate_scheduled_tasks(graph.get("scheduled_tasks"), marker, build_root)
        parts = graph.get("parts")
        m.require(isinstance(parts, list), "Missing project part list")
        found_projects: dict[str, str] = {}
        for part in parts:
            project = part.get("project_path")
            part_file = f"build/dependency-integrity/{run_id}/graphs/{m.build_key(build_root)}/parts/{m.part_key(project)}.json"
            m.require(part.get("file") == part_file and part_file not in used_files, "Duplicate/misrouted owner receipt")
            used_files.add(part_file)
            record = m.read_json(m.confined(workspace, part_file, must_exist=True))
            result = m.validate_project_record(record, run_id=run_id, mode=mode, host=marker["host"], digest=marker["source_input_digest"],
                                               build_root=build_root, workspace=workspace, verify_locks=verify_locks)
            m.require(result["project"] == project and project not in found_projects, "Owner does not match declared project")
            found_projects[project] = result["project_directory"]
            totals["projects"] += 1
            for key in ("configurations", "resolved_configurations", "artifact_view_outputs"):
                totals[key] += result[key]
            external_modules.update(tuple(value) for value in result["external_modules"])
            if result["lock_file"]:
                lock_files.add(result["lock_file"])
        m.require(found_projects == marker["expected_projects"][build_root], "A settings-declared owner project was omitted or added")
        children = graph.get("included_builds")
        m.require(isinstance(children, list), "Missing included-build accounting")
        for child in children:
            visit(child.get("build_root"), child.get("file"))

    visit(entry_root, _graph_file(run_id, entry_root))
    required = set(marker["build_roots"]) if entry_root == "." else {entry_root}
    m.require(visited == required, "The root/composite inventory omitted a required build")
    m.require(totals["resolved_configurations"] > 0, "Zero resolved configurations is not acquisition success")
    trust = m.parse_metadata(m.read_regular(m.confined(workspace, m.metadata_path(entry_root), must_exist=True), m.MAX_XML))
    trusted_components = {key[:3] for key in trust}
    m.require(not external_modules - trusted_components, "Selected external components lack any original artifact/metadata trust entry")
    return {**totals, "build_roots": sorted(visited), "lock_files": sorted(lock_files),
            "external_modules": sorted(external_modules), "verification_artifacts": len(trust),
            "receipt_files": {path: m.file_sha256(m.confined(workspace, path, must_exist=True)) for path in sorted(used_files)}}


def build_command(workspace: Path, marker: dict, *, entry_root: str, run_id: str, mode: str,
                  offline: bool = False, gradle_home: Path | None = None) -> list[str]:
    m.require(entry_root in marker["build_roots"] and mode in {"bootstrap", "check"} and m.RUN_ID.fullmatch(run_id), "Invalid command scope")
    m.require(not offline or mode == "check", "Offline is a verification check, not acquisition bootstrap")
    if gradle_home is not None:
        m.require(marker["kind"] == "controlled-fixture", "Installed-distribution override is restricted to controlled fixtures")
        executable = gradle_home / "bin/gradle"
        m.require(gradle_home.name == "gradle-9.7.1" and executable.is_file() and
                  (gradle_home / "lib/gradle-core-api-9.7.1.jar").is_file(), "Expected the inspected installed Gradle9.7.1 distribution")
    else:
        executable = m.confined(workspace, "gradlew", must_exist=True)
    command = [str(executable)]
    if entry_root != ".":
        command.extend(["-p", entry_root])
    command.extend(["nativeCmpkitDependencyGraph", "--init-script", str(m.confined(workspace, "scripts/dependencies/resolve-graphs.init.gradle", must_exist=True)),
                    f"-Dnativecmpkit.dependencies.workspace={workspace}", f"-Dnativecmpkit.dependencies.mode={mode}",
                    f"-Dnativecmpkit.dependencies.run={run_id}", f"-Dnativecmpkit.dependencies.entry={entry_root}",
                    f"-Dnativecmpkit.dependencies.digest={marker['source_input_digest']}", "--dependency-verification", "strict",
                    "--no-daemon", "--no-configuration-cache", "--max-workers=1", "--console=plain"])
    if mode == "bootstrap":
        command.extend(["--write-locks", "--write-verification-metadata", "sha256"])
    if offline:
        command.append("--offline")
    return command


def _environment(workspace: Path, *, fresh: bool = False) -> dict[str, str]:
    java_home = os.environ.get("JAVA_HOME")
    m.require(java_home and (Path(java_home) / "bin/java").is_file(), "Select the existing JDK17 with JAVA_HOME before running")
    cache = m.confined(workspace, ".dependency-cache")
    if fresh:
        m.require(not cache.exists(), "Fixture cache must be fresh; do not reuse a tamper-test cache")
    cache.mkdir(exist_ok=True)
    home = m.confined(workspace, ".dependency-home")
    home.mkdir(exist_ok=True)
    environment = {"JAVA_HOME": java_home, "PATH": str(Path(java_home) / "bin") + os.pathsep + os.environ.get("PATH", os.defpath),
                   "HOME": str(home), "GRADLE_USER_HOME": str(cache), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC"}
    # SDK identity is retained in its own receipt by the lead; no values are dumped.
    for name in ("ANDROID_HOME", "ANDROID_SDK_ROOT", "DEVELOPER_DIR", "SDKROOT", "TMPDIR"):
        if os.environ.get(name):
            environment[name] = os.environ[name]
    # Deliberately no user init scripts/properties, JAVA_TOOL_OPTIONS, GRADLE_OPTS,
    # ORG_GRADLE_PROJECT_* credentials or inherited dependency-verification bypass.
    return environment


def _bounded(command: list[str], *, workspace: Path, environment: dict[str, str], log: Path,
             timeout: int, reserve_mib: int, deadline: float | None = None) -> dict:
    m.require(os.name == "posix", "This process-group runner is POSIX-only; Windows remains a missing execution gate")
    m.require(1 <= timeout <= 3600 and reserve_mib >= 8192, "Use a bounded <=1h slot and at least8GiB reserve")
    m.require(not log.exists(), "Fresh log path required")
    result = {"started_utc": utc_now(), "timeout_seconds": timeout, "reserve_mib": reserve_mib,
              "overall_deadline_applied": deadline is not None,
              "free_bytes_before": shutil.disk_usage(workspace).free, "process_started": False}
    if result["free_bytes_before"] < reserve_mib * 1024 ** 2:
        return {**result, "exit_code": 75, "reason": "disk-reserve-unavailable", "finished_utc": utc_now()}
    start = time.monotonic()
    # Keep ten seconds for process-group termination and two for receipt writing.
    # The fixture caller shares ONE monotonic deadline across every invocation.
    stop_at = min(start + timeout, deadline - 12) if deadline is not None else start + timeout
    stop_reason = "total-timeout" if stop_at < start + timeout else "timeout"
    if stop_at <= start:
        return {**result, "exit_code": 75, "reason": "total-timeout-before-launch", "finished_utc": utc_now()}
    with log.open("xb") as output:
        process = subprocess.Popen(command, cwd=workspace, env=environment, stdout=output, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        result["process_started"] = True
        try:
            while process.poll() is None:
                if shutil.disk_usage(workspace).free < reserve_mib * 1024 ** 2:
                    result["reason"] = "disk-reserve-reached"
                elif time.monotonic() >= stop_at:
                    result["reason"] = stop_reason
                if "reason" in result:
                    break
                time.sleep(0.5)
        except KeyboardInterrupt:
            result["reason"] = "interrupted"
        finally:
            if process.poll() is None:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
        result["exit_code"] = process.returncode
    return {**result, "finished_utc": utc_now(), "elapsed_seconds": round(time.monotonic() - start, 3),
            "free_bytes_after": shutil.disk_usage(workspace).free, "log_sha256": m.file_sha256(log)}


def _review_path(entry_root: str) -> str:
    return f"build/dependency-integrity/reviews/{m.build_key(entry_root)}.json"


def check_review(workspace: Path, marker: dict, entry_root: str, state: dict[str, str]) -> dict:
    review = m.read_json(m.confined(workspace, _review_path(entry_root), must_exist=True))
    m.require(review.get("schema_version") == 1 and review.get("record_type") == "candidate-review" and
              review.get("source_input_digest") == marker["source_input_digest"] and review.get("host") == marker["host"] and
              review.get("entry_root") == entry_root and review.get("independent_trust_reviewed") is False,
              "Missing/foreign/exaggerated candidate review")
    expected_kind = "controlled-fixture" if marker["kind"] == "controlled-fixture" else "explicit-registry-tofu-acceptance"
    m.require(review.get("trust_level") == expected_kind and review.get("integrity_files") == state, "Candidate state is not the explicitly reviewed state")
    m.parse_metadata(m.read_regular(m.confined(workspace, m.metadata_path(entry_root), must_exist=True), m.MAX_XML))
    return review


@contextlib.contextmanager
def exclusive_workspace(workspace: Path, run_id: str):
    """Do not race two writers/checks in one candidate, and never break stale locks."""
    path = m.confined(workspace, ".nativecmpkit-dependency-active.json")
    data = m.json_bytes({"run_id": run_id, "pid": os.getpid()})
    m.write_new(path, data)
    try:
        yield
    finally:
        # Refuse to remove a replaced/foreign reservation, even on failure.
        m.require(m.read_regular(path, 4096) == data, "Candidate reservation changed; do not remove another process's lock")
        path.unlink()


def run(workspace: Path, *, entry_root: str, run_id: str, mode: str, timeout: int = 900,
        reserve_mib: int = 8192, offline: bool = False, gradle_home: Path | None = None,
        fresh_cache: bool = False, deadline: float | None = None) -> dict:
    workspace = workspace.absolute()
    load_workspace(workspace)  # Reject the live checkout before creating even a reservation file.
    with exclusive_workspace(workspace, run_id):
        return _run_locked(workspace, entry_root=entry_root, run_id=run_id, mode=mode, timeout=timeout,
                           reserve_mib=reserve_mib, offline=offline, gradle_home=gradle_home, fresh_cache=fresh_cache,
                           deadline=deadline)


def _run_locked(workspace: Path, *, entry_root: str, run_id: str, mode: str, timeout: int,
                reserve_mib: int, offline: bool, gradle_home: Path | None, fresh_cache: bool,
                deadline: float | None) -> dict:
    marker = load_workspace(workspace)
    before = check_source(workspace, marker)
    if mode == "check":
        check_review(workspace, marker, entry_root, before)
    command = build_command(workspace, marker, entry_root=entry_root, run_id=run_id, mode=mode, offline=offline, gradle_home=gradle_home)
    directory = m.confined(workspace, f"build/dependency-integrity/{run_id}")
    m.require(not directory.exists(), "Run IDs are immutable; choose a new output directory")
    directory.mkdir(parents=True)
    state = {"schema_version": 1, "record_type": "dependency-invocation", "run_id": run_id, "mode": mode,
             "entry_root": entry_root, "host": marker["host"], "source_input_digest": marker["source_input_digest"],
             "source_revision": marker.get("source_revision"), "source_tree_dirty": marker.get("source_tree_dirty"),
             "integrity_before": before, "command": [argument.replace(str(workspace), "<candidate>").replace(
                 str(gradle_home), "<installed-gradle-9.7.1>") if gradle_home else argument.replace(str(workspace), "<candidate>")
                 for argument in command],
             "selected_project_graph_complete": False, "project_lock_state_complete": False,
             "checksum_enforcement_exercised": False, "all_required_hosts_complete": False,
             "ordinary_build_policy_installed": False, "independent_trust_reviewed": False,
             "coverage_gaps": list(m.COVERAGE_GAPS), "errors": []}
    try:
        environment = _environment(workspace, fresh=fresh_cache)
        state["execution"] = _bounded(command, workspace=workspace, environment=environment, log=directory / "gradle.log",
                                      timeout=timeout, reserve_mib=reserve_mib, deadline=deadline)
        after = check_source(workspace, marker)
        state["integrity_after"] = after
        for name, digest in after.items():
            source = m.confined(workspace, name, must_exist=True)
            m.write_new(directory / "captured" / name, m.read_regular(source, m.MAX_XML if name.endswith(".xml") else m.MAX_LOCK))
            m.require(m.file_sha256(directory / "captured" / name) == digest, "Integrity state changed during capture")
        m.require(state["execution"]["exit_code"] == 0 and "reason" not in state["execution"], "Gradle command did not complete successfully")
        if mode == "check":
            m.require(before == after, "Ordinary check changed checksum/lock state")
        state["graph_summary"] = validate_graph_tree(workspace, marker, run_id=run_id, mode=mode, entry_root=entry_root)
        state["selected_project_graph_complete"] = True
        state["project_lock_state_complete"] = True
        state["checksum_enforcement_exercised"] = mode == "check"
    except (m.IntegrityError, OSError, subprocess.SubprocessError) as failure:
        state["errors"].append({"type": type(failure).__name__, "message": str(failure) if isinstance(failure, m.IntegrityError)
                               else "Local process/filesystem failure; inspect private task log"})
    state["finished_utc"] = utc_now()
    m.write_new(directory / "result.json", m.json_bytes(state))
    return state


def merge_files(inputs: list[Path], output: Path) -> dict:
    m.require(inputs and all(path.resolve() != output.resolve() for path in inputs), "Merge output cannot replace any input")
    before = {str(path): m.file_sha256(path) for path in inputs}
    entries = m.merge_metadata([m.parse_metadata(m.read_regular(path, m.MAX_XML)) for path in inputs])
    data = m.metadata_bytes(entries)
    m.require(before == {str(path): m.file_sha256(path) for path in inputs}, "Candidate changed during trust reconciliation")
    m.write_new(output, data)
    return {"operation": "merge", "artifacts": len(entries), "output_sha256": m.sha256_bytes(data),
            "inputs_unchanged": True, "independent_trust_reviewed": False, "installed_into_source_checkout": False}


def review(workspace: Path, *, entry_root: str, run_ids: list[str], acknowledge_tofu: bool) -> dict:
    marker = load_workspace(workspace)
    m.require(marker["kind"] == "source-snapshot" and acknowledge_tofu, "Source review requires explicit registry-TOFU acknowledgement")
    m.require(entry_root in marker["build_roots"] and run_ids and len(run_ids) == len(set(run_ids)), "Explicit distinct acquisition runs are required")
    state = check_source(workspace, marker)
    candidates = []
    runs = []
    seen_roots = set()
    for run_id in run_ids:
        m.require(m.RUN_ID.fullmatch(run_id), "Invalid reviewed run ID")
        path = m.confined(workspace, f"build/dependency-integrity/{run_id}/result.json", must_exist=True)
        receipt = m.read_json(path)
        m.require(receipt.get("record_type") == "dependency-invocation" and receipt.get("mode") == "bootstrap" and
                  receipt.get("source_input_digest") == marker["source_input_digest"] and receipt.get("host") == marker["host"] and
                  receipt.get("selected_project_graph_complete") is True and receipt.get("project_lock_state_complete") is True and
                  receipt.get("execution", {}).get("exit_code") == 0 and not receipt.get("errors"), "Cannot accept an incomplete/foreign bootstrap")
        root = receipt["entry_root"]
        m.require(root in marker["build_roots"] and root not in seen_roots, "One latest complete acquisition per invocation root is required")
        seen_roots.add(root)
        summary = validate_graph_tree(workspace, marker, run_id=run_id, mode="bootstrap", entry_root=root)
        for name in summary["lock_files"]:
            m.require(receipt["integrity_after"].get(name) == state.get(name), "Current lock state differs from reviewed acquisition")
        captured_name = f"build/dependency-integrity/{run_id}/captured/{m.metadata_path(root)}"
        captured = m.confined(workspace, captured_name, must_exist=True)
        m.require(m.file_sha256(captured) == receipt["integrity_after"].get(m.metadata_path(root)), "Captured trust was modified")
        candidates.append(m.parse_metadata(m.read_regular(captured, m.MAX_XML)))
        runs.append({"run_id": run_id, "receipt_sha256": m.file_sha256(path), "captured_metadata": captured_name,
                     "captured_metadata_sha256": m.file_sha256(captured)})
    required_roots = set(marker["build_roots"]) if entry_root == "." else {entry_root}
    m.require(seen_roots == required_roots, "Review needs separate root/composite and standalone acquisitions for the selected scope")
    merged = m.merge_metadata(candidates)
    current = m.parse_metadata(m.read_regular(m.confined(workspace, m.metadata_path(entry_root), must_exist=True), m.MAX_XML))
    m.require(current == merged, "Active candidate trust is not the exact conflict-free acquired union; reconcile separately before review")
    if entry_root == ".":
        for other in marker["build_roots"]:
            if other == ".":
                continue
            standalone = m.parse_metadata(m.read_regular(m.confined(workspace, m.metadata_path(other), must_exist=True), m.MAX_XML))
            m.require(all(merged.get(key) == value for key, value in standalone.items()), "Standalone trust is not a matching subset of root trust")
    result = {"schema_version": 1, "record_type": "candidate-review", "entry_root": entry_root, "host": marker["host"],
              "source_input_digest": marker["source_input_digest"], "integrity_files": state,
              "trust_level": "explicit-registry-tofu-acceptance", "independent_trust_reviewed": False,
              "recorded_utc": utc_now(), "reviewed_acquisitions": runs, "coverage_gaps": list(m.COVERAGE_GAPS),
              "review_note": "Explicit caller acceptance of observed candidate consistency; not independently verified artifact provenance."}
    m.write_new(m.confined(workspace, _review_path(entry_root)), m.json_bytes(result))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    command = commands.add_parser("snapshot", help="Copy current dirty build inputs into a NEW external candidate; no Gradle")
    command.add_argument("--source", type=Path, required=True)
    command.add_argument("--destination", type=Path, required=True)
    command = commands.add_parser("run", help="Run explicitly scheduled isolated bootstrap/check, never the live checkout")
    command.add_argument("--workspace", type=Path, required=True)
    command.add_argument("--build", default=".", dest="entry_root")
    command.add_argument("--mode", choices=("bootstrap", "check"), required=True)
    command.add_argument("--run-id", required=True)
    command.add_argument("--timeout", type=int, default=900)
    command.add_argument("--reserve-mib", type=int, default=8192)
    command.add_argument("--offline", action="store_true")
    command = commands.add_parser("merge", help="Reconcile exact SHA candidates into a NEW file; never install or overwrite")
    command.add_argument("--input", type=Path, action="append", required=True, dest="inputs")
    command.add_argument("--output", type=Path, required=True)
    command = commands.add_parser("review", help="Record explicit candidate TOFU acceptance after inspecting actual acquisition")
    command.add_argument("--workspace", type=Path, required=True)
    command.add_argument("--build", default=".", dest="entry_root")
    command.add_argument("--run-id", action="append", required=True, dest="run_ids")
    command.add_argument("--acknowledge-registry-tofu", action="store_true", dest="acknowledge_tofu")
    command = commands.add_parser("fixtures", help="Scheduled REAL local-Maven/Gradle positive and tamper fixtures (not offline self-tests)")
    command.add_argument("--destination", type=Path, required=True)
    command.add_argument("--gradle-home", type=Path, required=True)
    command.add_argument("--timeout", type=int, default=300)
    command.add_argument("--total-timeout", type=int, default=300,
                         help="ONE total budget for all fixture setup/invocations; 12s reserved for termination/receipts")
    command.add_argument("--case", action="append", dest="cases",
                         help="Select a fixture by exact name (repeatable); bootstrap and baseline-check always run")
    command.add_argument("--reserve-mib", type=int, default=8192)
    arguments = vars(parser.parse_args(argv))
    operation = arguments.pop("operation")
    try:
        if operation == "snapshot":
            result = snapshot(**arguments)
        elif operation == "run":
            result = run(**arguments)
        elif operation == "merge":
            result = merge_files(**arguments)
        elif operation == "review":
            result = review(**arguments)
        else:
            import gradle_fixtures
            result = gradle_fixtures.execute(**arguments)
        print(json.dumps(result, sort_keys=True, indent=2))
        if operation == "run":
            return 0 if result["selected_project_graph_complete"] and not result["errors"] else 1
        if operation == "fixtures":
            return 0 if result["selected_cases_observed_as_expected"] else 1
        return 0
    except (m.IntegrityError, OSError, subprocess.SubprocessError) as failure:
        print(json.dumps({"operation": operation, "error_type": type(failure).__name__,
                          "error": str(failure) if isinstance(failure, m.IntegrityError) else
                          "Local filesystem/process failure; no success claim"}), file=sys.stderr)
        return 1


@contextlib.contextmanager
def sigterm_as_interrupt():
    """Let the bounded runner terminate its child group when the CLI is stopped."""
    previous = signal.getsignal(signal.SIGTERM)

    def stop(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)


if __name__ == "__main__":
    with sigterm_as_interrupt():
        try:
            raise SystemExit(main())
        except KeyboardInterrupt:
            print("Dependency operation interrupted; no success claim.", file=sys.stderr)
            raise SystemExit(130)
