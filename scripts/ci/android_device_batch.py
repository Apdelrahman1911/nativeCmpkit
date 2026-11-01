"""Run one fixed Android batch serially through the existing owned-device CLI.

Each route retains its fresh AVD, private signer, helper preparation and original
finite methods. Same-checkout Gradle compilation may be reused; no assembly,
signing, native task or fresh-result guard is skipped. XML is archived before the
next route can quarantine the shared report directory. Any route failure remains
red; uncertain cleanup, inputs or archival refuse every remaining route.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import sys

import android_device_batch_plan as fixed
import android_device_tests as device
import archive_focused_junit as evidence
import library_tests as lt
import workflow_matrix as workflow

HELPERS = {"android_io_documents": "io-documents", "android_permission_demo": "permission-demo",
           "android_storage_probe": "storage-probe"}
RESERVE_MIB = 8192
ROUTE_TIMEOUT_SECONDS = 4200


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def plan(root: Path, batch: str) -> dict:
    require(batch in fixed.BATCHES, "Only the two fixed Android batches are permitted")
    routes = []
    allowed_keys = {"slot", "suite", "runner", "arch", "python", "emulator-api", "test-modules",
                    "test-focus", "storage-flavor", "storage-target-sdk"}
    for profile in fixed.BATCHES[batch]:
        api, module, focus = fixed.SELECTIONS[profile]
        rows = workflow.matrix(profile)["include"]
        require(len(rows) == 1, "Each original profile must select exactly one original route")
        row = rows[0]
        require(set(row) <= allowed_keys and row.get("suite") == "android-device" and
                row.get("runner") == "ubuntu-24.04" and row.get("arch") == "x64" and
                row.get("python") == "python3" and row.get("emulator-api") == str(api) and
                row.get("test-modules") == module and row.get("test-focus") == focus,
                "Original route expanded or changed its exact reviewed API/module/focus/host")
        device.validate_api_selection(api, (module,), focus)
        source = lt.plan(root, "android-device", only_modules=(module,), focus=focus)
        require(lt.validate_test_focus(source) and len(source["expected"]) == 1 and
                source["expected"][0].get("required_testcases"), "Missing original finite method selection")
        routes.append({"profile": profile, "api_level": api, "module": module,
                       "focus": focus, "original_slot": row["slot"], "source_suite": source})
    cases = [(case["classname"], case["name"]) for route in routes
             for case in route["source_suite"]["expected"][0]["required_testcases"]]
    return {"schema_version": 1, "suite": "android-device", "batch": batch, "source_only": True,
            "Gradle_builds_executed": 0, "native_tests_executed": 0, "routes": routes,
            "requested_target_executions": len(cases), "requested_distinct_methods": len(set(cases)),
            "same_workspace_serial_only": True, "compilation_or_native_acceptance_inferred": False}


def command(root: Path, relative: str, route: dict) -> list[str]:
    return [sys.executable, "-B", str(root / "scripts/ci/android_device_tests.py"), "run",
            "--api-level", str(route["api_level"]), "--module", route["module"],
            "--focus", route["focus"], "--output", relative]


def control_inputs(root: Path) -> dict:
    return {".github/workflows/gradle.yml": lt.sha256(lt.safe_path(root, ".github/workflows/gradle.yml"))}


def cleanup_certified(root: Path, relative: str, route: dict, controller: dict, revision: str) -> bool:
    try:
        require(controller.get("source_revision") == controller.get("source_revision_after") == revision and
                controller.get("source_tree_dirty") is False and controller.get("source_unchanged") is True and
                controller.get("changed_inputs") == [] and controller.get("explicit_test_focus") == route["focus"],
                "Controller source/route identity was not preserved")
        shutdown = controller.get("emulator_shutdown", {})
        require(shutdown.get("clean_shutdown") is True and shutdown.get("owned_adb_transport_removed") is True and
                type(shutdown.get("exit_code")) is int and shutdown["exit_code"] == 0 and
                shutdown.get("graceful_kill_requested") is True and shutdown.get("forced_owned_group") is False and
                not any(key in shutdown for key in ("ownership_error", "graceful_shutdown_error", "controller_cleanup_error")),
                "Owned emulator/ADB cleanup must be certified before another route")
        for key, directory in HELPERS.items():
            if key not in route["source_suite"]:
                continue
            source = route["source_suite"][key]
            helper = controller.get(key.removeprefix("android_"), {})
            require(helper == evidence.document(root, relative + "/" + directory + "/receipt.json") and
                    helper.get("package") == source["package"] and helper.get("source_fixture") == source["source_fixture"] and
                    type(helper.get("verification_api_level")) is int and helper["verification_api_level"] == route["api_level"] and
                    helper.get("cleanup_status") == "passed" and helper.get("owned_recipient_removed") is True and
                    "cleanup_error" not in helper, "Owned helper cleanup receipt is missing or disagrees")
            if key == "android_storage_probe":
                require(helper.get("profile") == route["profile"], "Wrong storage helper lifecycle")
        require(not (root / "build/ci-verification/.android-device-controller.lock").exists() and
                not (root / "build/ci-verification/.library-tests.lock").exists(), "Prior controller/library lease remains")
        return True
    except (OSError, ValueError, KeyError, TypeError):
        return False


def failed_child_origin(root: Path, relative: str) -> dict:
    """Retain one bounded public frame, never private child output or success."""
    result = {"status": "unavailable", "raw_log_uploaded": False, "native_success_inferred": False}
    marker = b"NATIVECMPKIT_ANDROID_PREFLIGHT_ORIGIN"
    prefix = marker + b" "
    allowed = {"android_device_tests.py", "library_tests.py", "runtime_context.py",
               "android_camera_receiver.py", "android_share_recipient.py", "android_geo_probe.py",
               "android_io_documents.py", "android_permission_demo.py", "android_storage_probe.py"}
    try:
        body = evidence.read(lt.safe_path(root, relative), 64 * 1024)
        rows = [row for row in body.split(b"\n") if marker in row]
        if not rows:
            return result
        require(len(rows) == 1 and rows[0].startswith(prefix) and len(rows[0]) <= 512,
                "Expected one exact bounded public child-origin marker")
        origin = json.loads(rows[0][len(prefix):], object_pairs_hook=evidence.unique_object,
                            parse_constant=lambda _: require(False, "Nonfinite child-origin JSON"))
        require(isinstance(origin, dict) and set(origin) == {"source", "symbol", "line"},
                "Only public source, symbol and line may be retained")
        if type(origin["line"]) is int and origin == {"source": "unavailable", "symbol": "unavailable", "line": 0}:
            return result
        require(origin["source"] in allowed and isinstance(origin["symbol"], str) and
                re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", origin["symbol"]) is not None and
                type(origin["line"]) is int and 0 < origin["line"] < 20000,
                "Foreign or malformed child-origin identity")
        source = evidence.read(lt.safe_path(root, "scripts/ci/" + origin["source"]), 512 * 1024)
        syntax = ast.parse(source)
        require(any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and
                    node.name == origin["symbol"] and node.lineno <= origin["line"] <= node.end_lineno
                    for node in ast.walk(syntax)), "Child-origin must name its exact public source function")
        result.update(status="retained", origin=origin)
    except FileNotFoundError:
        pass
    except (OSError, ValueError, TypeError, UnicodeError, SyntaxError, RecursionError) as error:
        result.update(status="refused", diagnostic_error=type(error).__name__)
    return result


def archive_route(root: Path, relative: str, route: dict, inputs: dict, revision: str, controller: dict) -> dict:
    output = lt.safe_path(root, relative)
    summary = output / "fresh-reports.json"
    destination = output / "fresh-reports"
    require(not summary.exists() and not destination.exists(), "Never overwrite archived result evidence")
    receipt_path = lt.safe_path(root, relative + "/library/receipt.json")
    if not receipt_path.exists():
        require(controller.get("passed") is False and controller.get("test_suite_passed") is False,
                "Passing controller lacks its original library receipt")
        result = {"profile": route["profile"], "original_library_receipt_present": False,
                  "original_reports": [], "actual_cases": [], "actual_totals": lt.case_counts([]),
                  "original_XML_execution_count_complete": False,
                  "original_result_preserved": True, "native_success_inferred_from_archival": False}
        with summary.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result
    receipt = evidence.document(root, relative + "/library/receipt.json")
    authored = evidence.document(root, relative + "/library/plan.json")
    expected, = route["source_suite"]["expected"]
    require(authored == route["source_suite"] and lt.validate_test_focus(authored) and
            receipt.get("suite") == "android-device" and receipt.get("explicit_test_focus") == route["focus"] and
            receipt.get("required_focused_testcases") == expected["required_testcases"], "Wrong original finite library scope")
    require(receipt.get("source_revision") == receipt.get("source_revision_after") == revision and
            receipt.get("source_tree_dirty") is False and receipt.get("changed_inputs") == [] and
            "input_capture_error" not in receipt and
            evidence.document(root, relative + "/library/inputs-before.json") ==
            evidence.document(root, relative + "/library/inputs-after.json") == inputs == lt.snapshot_inputs(root) and
            receipt.get("inputs_before_sha256") == receipt.get("inputs_after_sha256") == lt.input_digest(inputs),
            "Stale or changed-source reports cannot be archived as this route")
    require(receipt.get("task_execution_markers") == {expected["task"]: 1} and
            len(receipt.get("modules", [])) == 1, "Missing exact original fresh connected task execution")
    module, = receipt["modules"]
    require(module.get("module") == route["module"] and module.get("task") == expected["task"] and
            len(module.get("reports", [])) <= 1, "Wrong/expanded original Android XML scope")
    started = dt.datetime.fromisoformat(receipt["started_at_utc"])
    ended = dt.datetime.fromisoformat(receipt["finished_at_utc"])
    require(started.utcoffset() is not None and ended.utcoffset() is not None and started <= ended,
            "Fresh report execution requires bounded timezone-aware timestamps")
    cases, reports, bodies = [], [], []
    allowed = lt.safe_path(root, expected["report_directory"])
    for row in module.get("reports", []):
        source = lt.safe_path(root, row["path"])
        require(source.is_relative_to(allowed) and source != allowed, "Wrong original report location")
        original_name = re.fullmatch(r"TEST-[A-Za-z0-9_.-]+\.xml", source.name) is not None
        if not original_name:
            # AGP adds its owned AVD and observed Android release verbatim. Do
            # not widen the old filename alphabet or treat the AVD as a regex.
            device_plan = evidence.document(root, relative + "/plan.json")
            boot = evidence.document(root, relative + "/boot.json")
            avd_name, release = device_plan.get("avd_name"), boot.get("release")
            require(device_plan.get("source_revision") == revision and
                    type(device_plan.get("api_level")) is int and device_plan["api_level"] == route["api_level"] and
                    device_plan.get("serial") == boot.get("serial") == device.SERIAL and
                    boot.get("api_level") == str(route["api_level"]) and boot.get("boot_completed") == "1" and
                    boot.get("selinux") == "Enforcing" and isinstance(avd_name, str) and
                    re.fullmatch(f"nativecmpkit-api{route['api_level']}-[0-9a-f]{{12}}", avd_name) is not None and
                    isinstance(release, str) and re.fullmatch(r"[0-9]{1,2}(?:\.[0-9]{1,2}){0,2}", release) is not None,
                    "Wrong owned emulator report identity")
            original_name = source.name == f"TEST-{avd_name}(AVD) - {release}.xml"
        require(original_name, "Wrong original report location")
        before = source.lstat()
        require(started.timestamp() - 2 <= before.st_mtime <= ended.timestamp() + 2, "Stale or future original XML")
        body = evidence.read(source, lt.MAX_REPORT_BYTES)
        require(hashlib.sha256(body).hexdigest() == row.get("sha256"), "Original XML digest disagrees")
        actual = lt.junit_cases(body)
        require(lt.case_counts(actual) == {key: row.get(key) for key in lt.case_counts(actual)}, "Original report totals disagree")
        cases.extend(actual)
        reports.append({"original_path": row["path"], "archived_path": relative + "/fresh-reports/" + source.name,
                        "sha256": row["sha256"]})
        bodies.append((source.name, body))
    required = {(case["classname"], case["name"]) for case in expected["required_testcases"]}
    actual = {(case["classname"], case["name"]) for case in cases}
    require(cases == module.get("testcases") and len(cases) == len(actual) and actual <= required and
            lt.case_counts(cases) == receipt.get("totals") == controller.get("test_totals"),
            "Original XML identities/outcomes and controller/library totals disagree")
    require(type(receipt.get("passed")) is bool and type(receipt.get("execution", {}).get("exit_code")) is int,
            "Missing original library outcome")
    require(controller.get("test_suite_passed") is receipt["passed"], "Controller and original library outcome disagree")
    if receipt["passed"]:
        require(actual == required and len(reports) == 1 and receipt["execution"]["exit_code"] == 0 and
                all(case["status"] == "passed" for case in cases), "Passing route needs every original non-skipped method")
    else:
        require(controller.get("passed") is False, "Failed library result cannot become a passing controller")
    result = {"profile": route["profile"], "original_library_receipt_present": True,
              "original_reports": reports, "actual_cases": cases, "actual_totals": lt.case_counts(cases),
              "missing_selected_cases": [case for case in expected["required_testcases"]
                                         if (case["classname"], case["name"]) not in actual],
              "original_XML_execution_count_complete": actual == required,
              "original_result_preserved": True, "native_success_inferred_from_archival": False}
    destination.mkdir()
    for filename, body in bodies:
        with (destination / filename).open("xb") as stream:
            stream.write(body)
        require(evidence.read(destination / filename, lt.MAX_REPORT_BYTES) == body, "Archived original XML readback disagrees")
    with summary.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def reclaim_owned_state(root: Path, relative: str, route: dict, revision: str) -> dict:
    """Discard only this completed route's two private disposable directories."""
    output = lt.safe_path(root, relative)
    summary = lt.safe_path(root, relative + "/local-state-cleanup.json")
    require(not summary.exists(), "Never overwrite prior local cleanup evidence")
    result = {"status": "running", "removed_directories": [], "evidence_or_cache_removed": False}
    try:
        allowed = lt.safe_path(root, "build/ci-verification")
        require(output != allowed and output.is_relative_to(allowed) and output.parent.name == "routes" and
                output.name == route["profile"] and cleanup_certified(root, relative, route,
                    evidence.document(root, relative + "/controller.json"), revision),
                "Exact prior owned controller/helper cleanup must be certified before local reclamation")
        lock = lt.safe_path(root, "build/ci-verification/.android-device-batch.lock")
        require(lock.read_text() == f"{os.getpid()}\n" and
                evidence.document(root, relative + "/fresh-reports.json").get("original_result_preserved") is True,
                "Only the current exclusive batch may reclaim its already archived route")
        folders = [lt.safe_path(root, relative + "/" + name) for name in ("avd", "android-user")]
        for folder in folders:
            require(folder.parent == output and folder.is_dir(), "Missing exact private route directory")
            for base, directories, names in os.walk(folder, followlinks=False):
                for name in [*directories, *names]:
                    lt.safe_path(root, (Path(base) / name).relative_to(root).as_posix())
        # Validate both entire owned trees before any deletion. rmtree operates
        # only below these known fresh output paths; no SDK or build cache path.
        for folder in folders:
            shutil.rmtree(folder)
            require(not folder.exists(), "Owned private state removal readback failed")
            result["removed_directories"].append(folder.name)
        result["status"] = "passed"
    except (Exception, KeyboardInterrupt) as error:
        result.update(status="failed", error_class=type(error).__name__)
    finally:
        with summary.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def run(root: Path, batch: str, relative: str) -> dict:
    selection = plan(root, batch)
    output = lt.safe_path(root, relative)
    base = lt.safe_path(root, "build/ci-verification")
    require(output != base and output.is_relative_to(base) and not output.exists(), "Use a fresh dedicated batch output")
    base.mkdir(parents=True, exist_ok=True)
    lock = base / ".android-device-batch.lock"
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, f"{os.getpid()}\n".encode())
        inputs = lt.snapshot_inputs(root)
        controls = control_inputs(root)
        revision = lt.git_revision(root)
        require(re.fullmatch(r"[0-9a-f]{40}", revision) is not None, "Exact source revision is required")
        output.mkdir(parents=True)
        (output / "routes").mkdir()
        lt.write_json(output / "plan.json", selection)
        lt.write_json(output / "inputs-before.json", inputs)
        lt.write_json(output / "control-inputs-before.json", controls)
        result = {"schema_version": 1, "batch": batch, "source_revision": revision,
                  "started_at_utc": lt.utc_now(), "routes": [], "refused_profiles": [], "passed": False,
                  "packages_published": False, "packages_uploaded": False, "release_readiness_certified": False,
                  "native_acceptance_or_issue_closure_inferred": False, "reserve_mib": RESERVE_MIB,
                  "requested_target_executions": selection["requested_target_executions"],
                  "requested_distinct_methods": selection["requested_distinct_methods"],
                  "same_workspace_compilation_reuse_only": True}
        names = set()
        for index, route in enumerate(selection["routes"]):
            route_relative = relative + "/routes/" + route["profile"]
            item = {"profile": route["profile"], "output": route_relative, "passed": False, "cleanup_certified": False}
            result["routes"].append(item)
            try:
                require(lt.snapshot_inputs(root) == inputs and control_inputs(root) == controls and
                        lt.git_revision(root) == revision, "Batch source or workflow identity changed")
                execution = lt.execute(root, command(root, route_relative, route),
                                       output / (route["profile"] + ".log"), ROUTE_TIMEOUT_SECONDS, RESERVE_MIB)
                item["execution"] = execution
                if type(execution.get("exit_code")) is int and execution["exit_code"] != 0:
                    item["failed_child_origin"] = failed_child_origin(
                        root, relative + "/" + route["profile"] + ".log")
                controller = evidence.document(root, route_relative + "/controller.json")
                item.update(controller_path=route_relative + "/controller.json",
                            controller_sha256=lt.sha256(root / route_relative / "controller.json"))
                authored = evidence.document(root, route_relative + "/plan.json")
                name = authored.get("avd_name", "")
                require(authored.get("source_revision") == revision and authored.get("api_level") == route["api_level"] and
                        authored.get("serial") == device.SERIAL and authored.get("source_suite") == route["source_suite"] and
                        re.fullmatch(f"nativecmpkit-api{route['api_level']}-[0-9a-f]{{12}}", name) is not None and name not in names,
                        "Each route needs its exact fresh owned AVD and original plan")
                names.add(name)
                item["cleanup_certified"] = cleanup_certified(root, route_relative, route, controller, revision)
                try:
                    item["archive"] = archive_route(root, route_relative, route, inputs, revision, controller)
                except Exception as error:
                    item["archive_error"] = type(error).__name__
                    raise
                item["passed"] = (type(execution.get("exit_code")) is int and execution["exit_code"] == 0 and
                                  not execution.get("stop_reason") and controller.get("passed") is True and
                                  item["cleanup_certified"] is True and not item["archive"].get("missing_selected_cases"))
                require(item["cleanup_certified"] and not execution.get("stop_reason"),
                        "Uncertified prior cleanup or a stopped controller refuses remaining routes")
                item["local_state_cleanup"] = reclaim_owned_state(root, route_relative, route, revision)
                require(item["local_state_cleanup"].get("status") == "passed", "Prior private AVD/signing state reclamation failed")
            except (Exception, KeyboardInterrupt) as error:
                item["adapter_error"] = type(error).__name__
                item["passed"] = False
                result["refused_profiles"] = [row["profile"] for row in selection["routes"][index + 1:]]
                break
        cases = [case for item in result["routes"] for case in item.get("archive", {}).get("actual_cases", [])]
        result["actual_target_executions"] = sum(case["status"] != "skipped" for case in cases)
        result["actual_distinct_methods"] = len({(case["classname"], case["name"]) for case in cases if case["status"] != "skipped"})
        result["original_XML_execution_count_complete"] = (
            len(result["routes"]) == len(selection["routes"]) and
            all(item.get("archive", {}).get("original_XML_execution_count_complete") is True for item in result["routes"]))
        try:
            after = lt.snapshot_inputs(root)
            controls_after = control_inputs(root)
            lt.write_json(output / "inputs-after.json", after)
            lt.write_json(output / "control-inputs-after.json", controls_after)
            result["source_unchanged"] = inputs == after and controls == controls_after and revision == lt.git_revision(root)
        except Exception:
            result["source_unchanged"] = False
        result["passed"] = (len(result["routes"]) == len(selection["routes"]) and not result["refused_profiles"] and
                            all(item["passed"] for item in result["routes"]) and result["source_unchanged"] is True)
        result["finished_at_utc"] = lt.utc_now()
        lt.write_json(output / "batch.json", result)
        return result
    finally:
        os.close(descriptor)
        lock.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("plan", "run"))
    parser.add_argument("--batch", required=True, choices=tuple(fixed.BATCHES))
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.operation == "plan":
        print(json.dumps(plan(lt.ROOT, args.batch), indent=2, sort_keys=True))
        return 0
    if args.output is None:
        parser.error("run requires a fresh --output below build/ci-verification")
    def interrupted(*_):
        raise KeyboardInterrupt()
    for number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(number, interrupted)
    result = run(lt.ROOT, args.batch, args.output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print("Android batch preflight refused: " + type(error).__name__, file=sys.stderr)
        sys.exit(2)
