#!/usr/bin/env python3
"""Finite shared SAMPLE checks, never library, physical-device or release certification.

One producer invocation shares compilation between real app builds and only the
previously unaccepted Android-host/browser/native sample methods. Compiled inputs
may be reused; fresh test XML, explicit runtime, exact method inventories and
source holding are mandatory. No publication, arbitrary tasks or native UI shim.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import tomllib

import daemon_jvm
import library_tests as lt
import runtime_context

ROOT = Path(__file__).resolve().parents[2]
PROFILES = {
    "sample-platforms-linux": {"mode": "linux", "runner": "ubuntu-24.04", "arch": "x64", "build_only": False},
    "sample-platforms-apple": {"mode": "apple", "runner": "macos-26", "arch": "arm64", "build_only": False},
    "sample-builds-linux": {"mode": "linux", "runner": "ubuntu-24.04", "arch": "x64", "build_only": True},
    "sample-builds-apple": {"mode": "apple", "runner": "macos-26", "arch": "arm64", "build_only": True},
}
BUILD_TASKS = {
    "linux": (":sample:android:assembleDebug", ":sample:desktop:jvmJar",
              ":sample:web-js:jsBrowserProductionWebpack", ":sample:web-js:jsBrowserDistribution",
              ":sample:web-wasm:wasmJsBrowserProductionWebpack", ":sample:web-wasm:wasmJsBrowserDistribution"),
    "apple": (":sample:common:linkDebugFrameworkIosArm64", ":sample:common:linkDebugFrameworkIosSimulatorArm64"),
}
SUITES = {"linux": ("android-host", "js", "wasm"), "apple": ("ios",)}
KNOWN_TEST_SETS = frozenset(lt.KNOWN_TEST_SETS)
SAMPLE_TREES = ("sample/common/src", "sample/android/src", "sample/desktop/src",
                "sample/web-js/src", "sample/web-js/webpack.config.d", "sample/web-wasm/src", "sample/ios/Calf")
GRAPH_TASK = ":nativecmpkitSampleCompileDependencies"


def workflow_matrix(profile: str) -> dict:
    return {"include": [dict(PROFILES[profile])] if profile in PROFILES else []}


def source_testcases(root: Path, source_set: str) -> list[dict]:
    if source_set not in KNOWN_TEST_SETS:
        raise ValueError("An unreviewed sample test source set cannot disappear from coverage")
    result = []
    for path in lt.source_files(root, "sample/common/src/" + source_set):
        if path.suffix != ".kt":
            continue
        text = path.read_text(encoding="utf-8")
        annotations = re.findall(r"@Test\b", text)
        if not annotations:
            continue
        package = re.findall(r"(?m)^package ([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*)\s*$", text)
        declaration = re.findall(r"\bclass " + re.escape(path.stem) + r"\b", text)
        methods = re.findall(r"@Test\s+fun ([a-zA-Z_]\w*)\s*\(\s*\)", text)
        if (len(package) != 1 or len(declaration) != 1 or len(methods) != len(annotations) or
                len(methods) != len(set(methods)) or "@Ignore" in text or "@Disabled" in text):
            raise ValueError("Sample test declarations changed; review rather than silently omit methods")
        result += [{"classname": package[0] + "." + path.stem, "name": name} for name in methods]
    if len(result) > 256:
        raise ValueError("Unexpectedly large sample method inventory")
    return result


def plan(root: Path, mode: str, *, build_only: bool = False) -> dict:
    if mode not in BUILD_TASKS or type(build_only) is not bool:
        raise ValueError("Unknown fixed sample platform mode")
    for path in lt.safe_path(root, "sample/common/src").iterdir():
        if path.is_dir() and path.name.endswith("Test") and path.name not in KNOWN_TEST_SETS:
            raise ValueError("Unknown sample test source hierarchy")
    tests = []
    for suite in (() if build_only else SUITES[mode]):
        task_name, source_sets = lt.SUITES[suite]
        cases = [case for name in source_sets for case in source_testcases(root, name)]
        if not cases or len(cases) != len({(c["classname"], c["name"]) for c in cases}):
            raise ValueError("Missing or duplicate actual sample methods")
        tests.append({"suite": suite, "module": "sample/common", "task": ":sample:common:" + task_name,
                      "report_directory": "sample/common/build/test-results/" + task_name,
                      "source_sets": list(source_sets), "required_testcases": cases,
                      "test_classes": sorted({case["classname"] for case in cases})})
    return {"schema_version": 1, "mode": mode, "build_only": build_only, "build_tasks": list(BUILD_TASKS[mode]),
            "dependency_task": GRAPH_TASK, "tests": tests, "sample_minSdk_lowered": False,
            "library_verification": False, "physical_device_verification": False,
            "release_readiness_certified": False,
            "scope": ("Sample app builds/compile graphs only; ZERO test executions requested or inferred, no accepted method replay"
                      if build_only else
                      "Sample apps/compile graphs and fresh previously unaccepted sample platform methods only; accepted desktop methods not replayed")}


def gradle_command(root: Path, selected: dict, simulator: str | None = None) -> list[str]:
    if selected != plan(root, selected.get("mode"), build_only=selected.get("build_only", False)):
        raise ValueError("Sample plan differs from the fixed source selection")
    apple = selected["mode"] == "apple"
    if (apple and (not simulator or not runtime_context.UUID.fullmatch(simulator))) or (not apple and simulator):
        raise ValueError("Only Apple sample execution requires its exact selected booted simulator")
    command = ["./gradlew", "--continue", "--no-daemon", "--console=plain", "--no-configuration-cache",
               "--max-workers=1", "--no-parallel", "-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8",
               "-Pkotlin.compiler.execution.strategy=in-process", "-Pkotlin.native.jvmArgs=-Xmx2048m",
               "--init-script", "scripts/ci/fresh-tests.init.gradle.kts",
               "--init-script", "scripts/ci/daemon-jvm.init.gradle.kts",
               "--init-script", "scripts/ci/sample-platforms.init.gradle.kts",
               "-Dnativecmpkit.sampleProducerRoot=" + str(root.resolve()),
               "-PnativecmpkitSampleMode=" + selected["mode"]]
    if simulator:
        command.append("-PnativecmpkitSimulatorDevice=" + simulator)
    command += selected["build_tasks"] + [selected["dependency_task"]]
    for item in selected["tests"]:
        command.append(item["task"])
        for classname in item["test_classes"]:
            command += ["--tests", classname]
    return command


def xcode_command(root: Path, simulator: str) -> list[str]:
    if not runtime_context.UUID.fullmatch(simulator):
        raise ValueError("Xcode must use the explicitly selected sample simulator")
    return ["xcodebuild", "-project", "sample/ios/Calf.xcodeproj", "-scheme", "Calf",
            "-configuration", "Debug", "-sdk", "iphonesimulator", "-destination", "id=" + simulator,
            "-derivedDataPath", "build/ci-sample-xcode", "-jobs", "1", "CODE_SIGNING_ALLOWED=NO", "build"]


def exact_case_inventory(item: dict, cases: list[dict], *, require_runtime_suffix: bool = False) -> bool:
    actual = []
    suite = item["suite"]
    for case in cases:
        if case.get("status") != "passed":
            return False
        classname, name = case["classname"], case["name"]
        prefix = lt.SUITES[suite][0] + "."
        if suite in {"js", "wasm", "ios"}:
            if classname.startswith(prefix):
                classname = classname[len(prefix):]
            elif require_runtime_suffix:
                return False
        method, separator, suffix = name.partition("[")
        if suite == "ios":
            if (require_runtime_suffix or separator) and separator + suffix != "[iosSimulatorArm64]":
                return False
        elif suite in {"js", "wasm"}:
            target = "js" if suite == "js" else "wasmJs"
            if (require_runtime_suffix or separator) and (not separator or not re.fullmatch(
                    re.escape(target) + r", browser, [^\[\]\r\n]{1,512}\]", suffix)):
                return False
        elif separator:
            return False
        actual.append((classname, method))
    required = [(case["classname"], case["name"]) for case in item["required_testcases"]]
    return bool(required) and Counter(actual) == Counter(required)


def inputs(root: Path) -> dict:
    result = lt.snapshot_inputs(root)
    for tree in SAMPLE_TREES:
        for path in lt.source_files(root, tree):
            result[path.relative_to(root).as_posix()] = lt.sha256(path)
    for relative in (".github/workflows/gradle.yml", "sample/ios/Calf.xcodeproj/project.pbxproj",
                     "sample/ios/Calf.xcodeproj/project.xcworkspace/contents.xcworkspacedata",
                     "sample/ios/Calf.xcodeproj/project.xcworkspace/xcshareddata/IDEWorkspaceChecks.plist"):
        path = lt.safe_path(root, relative)
        if not path.is_file():
            raise ValueError("Missing actual sample/workflow input")
        result[relative] = lt.sha256(path)
    return dict(sorted(result.items()))


def inspect_graph(root: Path, mode: str) -> dict:
    relative = "build/ci-verification/sample-platforms-" + mode + "/compile-dependencies.json"
    path = lt.safe_path(root, relative)
    if not path.is_file() or path.stat().st_nlink != 1 or path.stat().st_size > lt.MAX_REPORT_BYTES:
        raise ValueError("Missing bounded actual sample compilation dependency graph")
    data = json.loads(path.read_bytes())
    targets = {"android", "desktop", "js", "wasmJs"} if mode == "linux" else {"iosArm64", "iosSimulatorArm64"}
    if (data.get("mode") != mode or data.get("project") != ":sample:common" or
            data.get("sample_minSdk_lowered") is not False or len(data.get("compilations", [])) != len(targets) or
            {c["target"] for c in data["compilations"]} != targets):
        raise ValueError("Actual dependency graph does not contain every selected main compilation")
    for row in data["compilations"]:
        if row["unresolved_dependencies"] != 0 or not row["resolved_modules"]:
            raise ValueError("Unresolved or empty actual sample dependency graph")
        # NavigationEvent is a different API/group, present in real Apple
        # Compose graphs. Match the removed Navigation library's exact group
        # identities, not a prefix that also rejects navigationevent.
        if any(module["group"] in {"org.jetbrains.androidx.navigation", "androidx.navigation"}
               for module in row["resolved_modules"]):
            raise ValueError("Unused second navigation library remains on an actual compilation graph")
    sources = [p for p in lt.source_files(root, "sample/common/src/commonMain") if p.suffix == ".kt"]
    if any(re.search(r"(?m)^import (?:org\.jetbrains\.androidx\.navigation|androidx\.navigation)\b", p.read_text()) for p in sources):
        raise ValueError("Sample directly imports a removed navigation implementation")
    catalog = tomllib.loads(lt.safe_path(root, "gradle/libs.versions.toml").read_text())["versions"]
    sample_android = lt.safe_path(root, "sample/android/build.gradle.kts").read_text()
    if catalog["android-sample-minSdk"] != "24" or "minSdk = libs.versions.android.sample.minSdk.get().toInt()" not in sample_android:
        raise ValueError("Sample app minimum differs from the retained API24 setting; review before lowering")
    return {"path": relative, "sha256": lt.sha256(path), "all_selected_compile_graphs_reviewed": True,
            "unused_second_navigation_group_absent": True, "direct_navigation_imports_absent": True,
            "sample_app_declared_minSdk": 24, "sample_minSdk_lowered": False, "minimum_platform_certified": False}


def build_outputs(root: Path, selected: dict, *, started_ns: int, ended_ns: int) -> dict:
    patterns = ({"android": ("sample/android/build/outputs/apk/debug", "*.apk"),
                 "jvm": ("sample/desktop/build/libs", None),
                 "js": ("sample/web-js/build/dist/js/productionExecutable", "web.js"),
                 "wasm": ("sample/web-wasm/build/dist/wasmJs/productionExecutable", "web.js")}
                if selected["mode"] == "linux" else
                {"ios-device": ("sample/common/build/bin/iosArm64/debugFramework/Common.framework", "Common"),
                 "ios-simulator": ("sample/common/build/bin/iosSimulatorArm64/debugFramework/Common.framework", "Common")})
    tasks = ({"android": BUILD_TASKS["linux"][:1], "jvm": BUILD_TASKS["linux"][1:2],
              "js": BUILD_TASKS["linux"][2:4], "wasm": BUILD_TASKS["linux"][4:6]}
             if selected["mode"] == "linux" else
             {"ios-device": BUILD_TASKS["apple"][:1], "ios-simulator": BUILD_TASKS["apple"][1:2]})
    result = {"schema_version": 1, "targets": {}, "errors": [], "test_success_inferred": False}
    for target, (directory, pattern) in patterns.items():
        observed = {"passed": False, "output": None, "tasks": [], "errors": []}
        for task in tasks[target]:
            index = BUILD_TASKS[selected["mode"]].index(task)
            relative = "build/ci-verification/sample-platforms-" + selected["mode"] + f"/task-build-{index}.json"
            try:
                path = lt.safe_path(root, relative)
                if not path.is_file() or path.stat().st_nlink != 1 or not 0 < path.stat().st_size <= 8192:
                    raise ValueError("Missing or unbounded task evidence")
                row = json.loads(path.read_bytes())
                boolean_keys = ("executed", "failed", "skipped", "up_to_date", "no_source", "test_success_inferred")
                if (row.get("schema_version") != 1 or row.get("task") != task or
                        any(type(row.get(key)) is not bool for key in boolean_keys) or
                        type(row.get("observed_epoch_ms")) is not int or
                        not started_ns // 1_000_000 <= row["observed_epoch_ms"] <= ended_ns // 1_000_000 or
                        row.get("skip_message") not in (None, "UP-TO-DATE", "FROM-CACHE", "SKIPPED", "NO-SOURCE") or
                        row["test_success_inferred"]):
                    raise ValueError("Task evidence identity, types or time window rejected")
                observed["tasks"].append({**row, "path": relative, "sha256": lt.sha256(path)})
                if (not row["executed"] or row["failed"] or row["no_source"] or
                        row["skipped"] and row["skip_message"] not in ("UP-TO-DATE", "FROM-CACHE")):
                    raise ValueError("Task did not successfully build its output")
            except (OSError, ValueError, KeyError) as error:
                observed["errors"].append({"error": "Actual sample task evidence rejected", "task": task,
                                            "reason": type(error).__name__})
        try:
            if target == "jvm":
                # The successful task's public archiveFile property binds its actual
                # versioned JAR. A different nonempty file is never equivalent proof.
                relative = observed["tasks"][0].get("archive_file") if observed["tasks"] else None
                if (not isinstance(relative, str) or len(relative) > 1024 or
                        Path(relative).parent.as_posix() != directory or Path(relative).suffix != ".jar"):
                    raise ValueError("Missing or foreign declared JVM archive output")
                files = [lt.safe_path(root, relative)]
            else:
                files = sorted(lt.safe_path(root, directory).glob(pattern))
            if len(files) != 1 or not files[0].is_file() or not files[0].stat().st_size:
                raise ValueError("Expected one actual nonempty sample output")
            path = lt.safe_path(root, files[0].relative_to(root).as_posix())
            if path.stat().st_nlink != 1:
                raise ValueError("Sample output must not be hardlinked")
            observed["output"] = {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size,
                                    "sha256": lt.sha256(path), "uploaded": False}
        except (OSError, ValueError) as error:
            observed["errors"].append({"error": "Actual sample target output rejected", "reason": type(error).__name__})
        observed["passed"] = not observed["errors"]
        result["targets"][target] = observed
        result["errors"] += [{"target": target, **error} for error in observed["errors"]]
    return result


def inspect_web_node_environments(root: Path, *, started_ns: int, ended_ns: int) -> dict:
    """Actual public project/root spec and executable witnesses, not PATH node."""
    result = {}
    for target, project, task in (("js", ":sample:web-js", BUILD_TASKS["linux"][2]),
                                   ("wasm", ":sample:web-wasm", BUILD_TASKS["linux"][4])):
        relative = "build/ci-verification/sample-platforms-linux/node-webpack-" + target + ".json"
        path = lt.safe_path(root, relative)
        if not path.is_file() or path.stat().st_nlink != 1 or not 0 < path.stat().st_size <= 8192:
            raise ValueError("Missing actual selected webpack Node environment witness")
        data = json.loads(path.read_bytes())
        rows = data.get("environments")
        if (data.get("schema_version") != 1 or data.get("task") != task or
                type(data.get("observed_epoch_ms")) is not int or
                not started_ns // 1_000_000 <= data["observed_epoch_ms"] <= ended_ns // 1_000_000 or
                data.get("test_success_inferred") is not False or not isinstance(rows, list) or len(rows) != 2 or
                [row.get("project") for row in rows] != [":", project]):
            raise ValueError("Wrong webpack Node witness task/project/time window")
        for row in rows:
            executable = row.get("executable")
            if (row.get("configured_version") != "24.16.0" or row.get("observed_version") != "v24.16.0" or
                    type(row.get("version_exit_code")) is not int or row["version_exit_code"] != 0 or
                    row.get("passed") is not True or not isinstance(executable, str) or
                    not Path(executable).is_absolute() or Path(executable).name != "node" or
                    not isinstance(row.get("extension"), str) or not row["extension"].endswith("NodeJsSpec") or
                    not re.fullmatch(r"[0-9a-f]{64}", row.get("executable_sha256", ""))):
                raise ValueError("Actual selected webpack Node version/executable rejected")
        if rows[0]["executable"] != rows[1]["executable"] or rows[0]["executable_sha256"] != rows[1]["executable_sha256"]:
            raise ValueError("Root and project select different Node executables")
        result[target] = {"path": relative, "sha256": lt.sha256(path), "task": task,
                          "environments": rows, "root_and_project_same_pinned_executable": True,
                          "test_success_inferred": False}
    return result


def collect_sample_reports(root: Path, item: dict, started_ns: int, ended_ns: int,
                           markers: Counter, host_system: str) -> dict:
    """Share safe XML parsing, NOT a library focus or library pass claim.

    The sample owner validates its full source-derived selection independently.
    Do not pass that owner's required_testcases to an unfiltered library plan:
    the library policy correctly rejects arbitrary library filters. Do not weaken
    that policy to repair the sample caller.
    """
    mode = "apple" if item.get("suite") == "ios" else "linux"
    if item not in plan(root, mode)["tests"]:
        raise ValueError("Sample report selection differs from its owning source plan")
    expected = {key: item[key] for key in ("module", "task", "report_directory")}
    result = lt.collect_reports(root, {"suite": item["suite"], "explicit_test_focus": None,
                                      "expected": [expected]},
                                started_ns, ended_ns, markers, host_system=host_system)
    module, = result["modules"]
    if not exact_case_inventory(item, module["testcases"], require_runtime_suffix=True):
        result["errors"].append({"error": "Fresh sample XML does not contain exactly every selected passing method",
                                 "suite": item["suite"]})
    for error in result["errors"]:
        if error.get("error") == "No actual non-skipped library testcases":
            error["error"] = "No actual non-skipped sample testcases"
    result["library_verification"] = False
    return result


def run(root: Path, mode: str, simulator: str | None, timeout: int, *, build_only: bool = False) -> dict:
    selected = plan(root, mode, build_only=build_only)
    command = gradle_command(root, selected, simulator)
    output = lt.safe_path(root, "build/ci-verification/sample-platforms-" + mode)
    if output.exists() or os.environ.get("OVERRIDE_KOTLIN_BUILD_IDE_SUPPORTED") == "YES":
        raise ValueError("Use a fresh sample output and never bypass the real Xcode framework shell phase")
    lock = lt.safe_path(root, "build/ci-verification/.library-tests.lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        output.mkdir()
        before = inputs(root)
        context = runtime_context.capture(expected_arch="arm64" if mode == "apple" else "x64", require_clean=True,
                                          apple=mode == "apple", device=simulator, require_booted=mode == "apple",
                                          android_package="android-37.0", browser=mode == "linux")
        lt.write_json(output / "plan.json", selected)
        lt.write_json(output / "inputs-before.json", before)
        lt.write_json(output / "runtime.json", context)
        quarantined = []
        for item in selected["tests"]:
            quarantined += lt.quarantine_reports(root, output, {"expected": [item]})
        started_ns = time.time_ns()
        execution = lt.execute(root, command, output / "gradle.log", timeout, 8192)
        ended_ns = time.time_ns()
        # A results-reducer failure must not erase the process outcome or force
        # replay of already completed methods merely to recover its exit code.
        lt.write_json(output / "execution.json", {"source_revision": context["source_revision"],
                                                  "started_ns": started_ns, "ended_ns": ended_ns,
                                                  "command": command, "execution": execution,
                                                  "build_only": build_only,
                                                  "test_success_inferred": False})
        markers = lt.execution_markers(output / "gradle.log") if (output / "gradle.log").exists() else Counter()
        receipts, errors = [], []
        for item in selected["tests"]:
            try:
                result = collect_sample_reports(root, item, started_ns, ended_ns, markers,
                                                context["host"]["system"])
                module, = result["modules"]
            except (OSError, ValueError, KeyError) as error:
                # Preserve the failed process, after-inputs and remaining build
                # observations even if evidence parsing itself is refused.
                # A rejection is an explicit failure, never silent success.
                module = {"module": item["module"], "task": item["task"], **lt.case_counts([]),
                          "reports": [], "testcases": [], "native_scenarios": []}
                result = {"errors": [{"error": "Sample report evidence rejected", "suite": item["suite"],
                                       "reason": type(error).__name__}]}
            receipts.append({"suite": item["suite"], **module})
            errors += result["errors"]
        receipt = {"schema_version": 1, "mode": mode, "build_only": build_only, "source_revision": context["source_revision"],
                   "source_tree_dirty": context["source_tree_dirty"], "runtime_receipt_sha256": lt.sha256(output / "runtime.json"),
                   "started_ns": started_ns, "ended_ns": ended_ns, "command": command, "execution": execution,
                   "task_execution_markers": dict(markers), "quarantined_prior_reports": quarantined,
                   "sample_suites": receipts, "errors": errors, "library_verification": False,
                   "physical_device_verification": False, "packages_releases_deployments_or_Pages_created": False,
                   "release_readiness_certified": False, "scope": selected["scope"]}
        # Independent observers preserve a successful target even if another
        # observer/target fails. No error is waived or converted to whole success.
        observers = [("gradle_daemon", lambda: daemon_jvm.observation(output / "gradle.log")),
                     ("compile_dependency_graph", lambda: inspect_graph(root, mode)),
                     ("actual_built_outputs", lambda: build_outputs(root, selected, started_ns=started_ns, ended_ns=ended_ns))]
        if mode == "linux":
            observers.append(("web_node_environments", lambda: inspect_web_node_environments(root, started_ns=started_ns, ended_ns=ended_ns)))
        for key, observer in observers:
            try:
                receipt[key] = observer()
                if key == "actual_built_outputs":
                    errors += receipt[key]["errors"]
            except (OSError, ValueError, KeyError) as error:
                errors.append({"error": "Actual sample evidence rejected", "observer": key, "reason": type(error).__name__})
        if mode == "apple":
            listing = subprocess.run(["xcodebuild", "-list", "-json", "-project", "sample/ios/Calf.xcodeproj"],
                                     cwd=root, capture_output=True, timeout=180)
            receipt["xcode_list_exit_code"] = listing.returncode
            project = json.loads(listing.stdout).get("project", {}) if listing.returncode == 0 else {}
            if "Calf" not in project.get("schemes", []) or "Calf" not in project.get("targets", []):
                errors.append({"error": "Actual Xcode Calf target/scheme is missing; never guess a project or skip its build"})
            else:
                xcommand = xcode_command(root, simulator)
                xexecution = lt.execute(root, xcommand, output / "xcode.log", timeout, 8192)
                receipt["xcode"] = {"command": xcommand, "execution": xexecution, "signing_allowed": False,
                                    "real_framework_shell_phase_required": True}
                shell = (output / "xcode.log").read_text(errors="replace")
                app_binary = lt.safe_path(root, "build/ci-sample-xcode/Build/Products/Debug-iphonesimulator/Calf.app/Calf")
                if (xexecution["exit_code"] != 0 or "Skipping Gradle build task invocation" in shell or
                        ":sample:common:embedAndSignAppleFrameworkForXcode" not in shell or
                        not app_binary.is_file() or not app_binary.stat().st_size):
                    errors.append({"error": "Actual unsigned Xcode sample integration failed or bypassed Gradle"})
                else:
                    receipt["xcode"]["actual_app_binary"] = {"path": app_binary.relative_to(root).as_posix(),
                                                             "sha256": lt.sha256(app_binary), "uploaded": False}
        after = inputs(root)
        lt.write_json(output / "inputs-after.json", after)
        receipt["inputs_before_sha256"] = lt.input_digest(before)
        receipt["inputs_after_sha256"] = lt.input_digest(after)
        receipt["changed_inputs"] = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
        receipt["source_revision_after"] = lt.git_revision(root)
        receipt["passed"] = (execution["exit_code"] == 0 and not execution.get("stop_reason") and not errors and
                             not receipt["changed_inputs"] and receipt["source_revision_after"] == context["source_revision"])
        lt.write_json(output / "receipt.json", receipt)
        return receipt
    finally:
        os.close(descriptor)
        lock.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("plan", "matrix", "run"))
    parser.add_argument("--mode", choices=BUILD_TASKS)
    parser.add_argument("--profile", choices=PROFILES)
    parser.add_argument("--simulator")
    parser.add_argument("--build-only", action="store_true",
                        help="Recover app builds only; request and count zero sample test executions")
    parser.add_argument("--timeout", type=int, default=4800)
    args = parser.parse_args()
    if args.operation == "matrix":
        if not args.profile or args.mode or args.simulator or args.build_only:
            parser.error("matrix requires only its fixed profile")
        result = workflow_matrix(args.profile)
    elif args.operation == "plan":
        if not args.mode or args.profile or args.simulator:
            parser.error("plan requires only its fixed mode and executes no build")
        result = plan(ROOT, args.mode, build_only=args.build_only)
    else:
        if not args.mode or args.profile or not 1 <= args.timeout <= 4800:
            parser.error("run requires a fixed mode and a bounded positive timeout")
        result = run(ROOT, args.mode, args.simulator, args.timeout, build_only=args.build_only)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.operation != "run" or result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
