"""Keep an exact fresh iOS report before the next same-host focused invocation.

Only the two finite rendering/theme recovery selections are accepted. This
copies actual XML, not packages, compilation outputs or logs. Failed results
remain failed; archival never certifies native functionality or issue closure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import stat

import library_tests as tests

FOCUSES = (tests.IOS_VECTOR_RENDERING_FOCUS, tests.IOS_SYSTEM_APPEARANCE_FOCUS)
TASK = ":calf-ui:iosSimulatorArm64ApplicationTest"
REPORTS = "calf-ui/build/test-results/iosSimulatorArm64ApplicationTest"
COMPILE_TASKS = (
    ":calf-ui:compileKotlinIosSimulatorArm64",
    ":calf-ui:compileTestKotlinIosSimulatorArm64",
    ":calf-ui:linkApplicationDebugTestIosSimulatorArm64",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read(path: Path, maximum: int = 2 * 1024**2) -> bytes:
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
            0 < before.st_size <= maximum, "Expected an unshared bounded report")
    body = path.read_bytes()
    after = path.lstat()
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    require(identity(before) == identity(after) and len(body) == before.st_size,
            "Report changed during archival")
    return body


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON keys in report evidence")
        result[key] = value
    return result


def document(root: Path, relative: str) -> dict:
    result = json.loads(read(tests.safe_path(root, relative)), object_pairs_hook=unique_object,
                        parse_constant=lambda _: require(False, "Nonfinite report JSON"))
    require(isinstance(result, dict), "Expected a report object")
    return result


def archive(root: Path, relative: str) -> dict:
    output = tests.safe_path(root, relative)
    allowed = tests.safe_path(root, "build/ci-verification")
    require(output != allowed and output.is_relative_to(allowed) and output.is_dir(),
            "Use the existing owned focused invocation output")
    destination = output / "fresh-reports"
    require(not destination.exists(), "Never overwrite prior report evidence")
    receipt = document(root, relative + "/receipt.json")
    plan = document(root, relative + "/plan.json")
    focus = receipt.get("explicit_test_focus")
    require(focus in FOCUSES and plan.get("explicit_test_focus") == focus and
            tests.validate_test_focus(plan), "Wrong finite focused selection")
    require(receipt.get("source_tree_dirty") is False and
            receipt.get("source_revision") == receipt.get("source_revision_after") and
            isinstance(receipt.get("source_revision"), str) and
            re.fullmatch(r"[0-9a-f]{40}", receipt["source_revision"]) and
            receipt.get("changed_inputs") == [] and "input_capture_error" not in receipt,
            "Source identity changed or was not established")
    before = document(root, relative + "/inputs-before.json")
    after = document(root, relative + "/inputs-after.json")
    require(before == after == tests.snapshot_inputs(root) and
            receipt.get("inputs_before_sha256") == receipt.get("inputs_after_sha256") == tests.input_digest(before),
            "Do not copy stale or changed-source reports")
    require(receipt.get("task_execution_markers") == {TASK: 1} and
            receipt.get("suite") == "ios" and len(receipt.get("modules", [])) == 1,
            "Missing exact fresh application task execution")
    module = receipt["modules"][0]
    require(module.get("module") == "calf-ui" and module.get("task") == TASK and
            len(module.get("reports", [])) == 1, "Wrong or empty native XML scope")
    row, = module["reports"]
    source = tests.safe_path(root, row["path"])
    require(source.parent == tests.safe_path(root, REPORTS) and
            re.fullmatch(r"TEST-[A-Za-z0-9_.-]+\.xml", source.name), "Wrong actual XML location")
    body = read(source, 8 * 1024**2)
    require(hashlib.sha256(body).hexdigest() == row.get("sha256"), "Fresh XML digest mismatch")
    cases = tests.junit_cases(body)
    require(cases == module.get("testcases") and len(cases) == 1 and
            {(c["classname"], c["name"]) for c in cases} ==
            {(c["classname"], c["name"]) for c in tests.ui_application_focus_identities(focus)} and
            tests.case_counts(cases) == receipt.get("totals"), "Actual XML/selection/counts disagree")
    native_root = tests.safe_path(root, relative + "/native-ui-application")
    sessions = list(native_root.iterdir())
    require(len(sessions) == 1 and re.fullmatch(r"[0-9a-f]{32}", sessions[0].name),
            "Missing unique owned native session")
    native = document(root, relative + "/native-ui-application/" + sessions[0].name + "/receipt.json")
    cleanup = native.get("cleanup", {})
    require(native.get("source_revision") == receipt["source_revision"] and
            native.get("explicit_test_focus") == focus and native.get("packages_published") is False and
            native.get("release_readiness_certified") is False and
            cleanup.get("uninstall_exit_code") == 0 and all(cleanup.get(k) is True for k in (
                "owned_app_identity_reverified", "owned_app_stopped_verified",
                "owned_app_absence_verified", "owned_local_bundle_removed")),
            "Prior application cleanup must be verified before another launch")
    log = tests.safe_path(root, relative + "/gradle.log")
    compile_statuses = {}
    if log.is_file():
        with log.open("rb") as stream:
            stream.seek(max(0, log.stat().st_size - 256 * 1024))
            tail = stream.read(256 * 1024).decode("utf-8", errors="replace")
        for task in COMPILE_TASKS:
            statuses = re.findall(r"^> Task " + re.escape(task) + r"(?: (UP-TO-DATE|FROM-CACHE|SKIPPED|NO-SOURCE|FAILED))?\s*$",
                                  tail, re.MULTILINE)
            if statuses:
                compile_statuses[task] = statuses[-1] or "executed"
    result = {"schema_version": 1, "source_revision": receipt["source_revision"], "focus": focus,
              "original_path": row["path"], "archived_path": (destination / source.name).relative_to(root).as_posix(),
              "sha256": row["sha256"], "actual_cases": cases, "actual_totals": receipt["totals"],
              "original_result_preserved": True, "owned_application_cleanup_checked": True,
              "observed_compile_task_statuses": compile_statuses,
              "compilation_or_native_pass_inferred_from_archival": False, "packages_uploaded": False}
    destination.mkdir()
    with (destination / source.name).open("xb") as stream:
        stream.write(body)
    require(read(destination / source.name, 8 * 1024**2) == body, "Archived XML readback differs")
    with (output / "fresh-reports.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(archive(tests.ROOT, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
