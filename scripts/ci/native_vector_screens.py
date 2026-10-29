#!/usr/bin/env python3
"""Require both fresh actual native screen resolutions, reusing compilation only.

Read-only review of two independently archived library executions. No package,
release, platform-wide coverage or automatic issue closure is certified.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

import archive_focused_junit as archive
import library_tests as tests

OUTPUTS = ("build/ci-verification/ios-ipad", "build/ci-verification/ios-ipad-related-recovery")
FIELDS = {"density", "native_screen", "view", "layer", "simulator", "source_revision",
          "actual_cases", "passed_cases", "complete_native_lifecycle", "original_XML_preserved"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_pair(rows: list[dict]) -> dict:
    require(type(rows) is list and len(rows) == 2, "Both native screen executions are required")
    for row, density in zip(rows, (2.0, 3.0)):
        require(isinstance(row, dict) and set(row) == FIELDS, "Unexpected native screen evidence fields")
        require(all(type(row[k]) in (int, float) and row[k] == density
                    for k in ("density", "native_screen", "view", "layer")),
                "Require unresampled actual 2x then 3x native view, layer and source")
        require(isinstance(row["simulator"], str) and 0 < len(row["simulator"]) <= 128 and
                isinstance(row["source_revision"], str) and re.fullmatch(r"[0-9a-f]{40}", row["source_revision"]),
                "Missing actual simulator or immutable source revision")
        require(type(row["actual_cases"]) is int and row["actual_cases"] == 1 and
                type(row["passed_cases"]) is int and row["passed_cases"] == 1 and
                row["complete_native_lifecycle"] is True and row["original_XML_preserved"] is True,
                "Failed, skipped, incomplete or stale native half cannot pass")
    require(rows[0]["simulator"] != rows[1]["simulator"] and
            rows[0]["source_revision"] == rows[1]["source_revision"],
            "Native pair must use distinct actual screens and identical source")
    return {"verified_native_densities": [2.0, 3.0], "fresh_native_methods": 2,
            "source_revision": rows[0]["source_revision"], "screens": rows,
            "compilation_reuse_not_old_test_XML": True, "release_readiness_certified": False,
            "packages_published": False}


def review(root: Path) -> dict:
    projections = []
    bindings = []
    current_inputs = tests.snapshot_inputs(root)
    for relative, family in zip(OUTPUTS, ("iPad", "iPhone")):
        document = lambda name: archive.document(root, relative + "/" + name)
        receipt, plan, context = (document(name) for name in ("receipt.json", "plan.json", "runtime.json"))
        original = document("fresh-reports.json")
        before, after = document("inputs-before.json"), document("inputs-after.json")
        require(before == after == current_inputs and receipt.get("changed_inputs") == [] and
                receipt.get("source_tree_dirty") is False and context.get("source_tree_dirty") is False and
                receipt.get("source_revision") == receipt.get("source_revision_after") ==
                context.get("source_revision") == tests.git_revision(root), "Native pair source binding changed")
        require(receipt.get("inputs_before_sha256") == receipt.get("inputs_after_sha256") == tests.input_digest(before) and
                receipt.get("runtime_receipt_sha256") == tests.sha256(tests.safe_path(root, relative + "/runtime.json")),
                "Native pair input/runtime digests disagree")
        require(plan == tests.plan(root, "ios", only_modules=("calf-ui",), focus=tests.IOS_VECTOR_RENDERING_FOCUS) and
                receipt.get("passed") is True and receipt.get("execution", {}).get("exit_code") == 0 and
                receipt.get("errors") == receipt.get("uncovered") == [] and
                receipt.get("task_execution_markers") == {archive.TASK: 1}, "Wrong or unsuccessful fresh native selection")
        simulator = context["simulator"]
        require(family in simulator["name"] and simulator["state"] == "Booted" and
                receipt["command"] == tests.gradle_command("ios", plan, simulator=simulator["udid"], root=root),
                "Wrong native simulator family or actual command")
        module, = receipt["modules"]
        report, = module["reports"]
        require(original.get("original_result_preserved") is True and original.get("owned_application_cleanup_checked") is True and
                original.get("source_revision") == receipt["source_revision"] and
                original.get("focus") == tests.IOS_VECTOR_RENDERING_FOCUS and
                original.get("original_path") == report["path"] and original.get("sha256") == report["sha256"],
                "Missing independent original XML archival")
        xml_path = original["archived_path"]
        require(Path(xml_path).parent.as_posix() == relative + "/fresh-reports", "Wrong original XML archive path")
        body = archive.read(tests.safe_path(root, xml_path), 8 * 1024**2)
        cases = tests.junit_cases(body)
        expected = tests.ui_application_focus_identities(tests.IOS_VECTOR_RENDERING_FOCUS)
        require(hashlib.sha256(body).hexdigest() == report["sha256"] and
                cases == module["testcases"] == original["actual_cases"] and
                tests.case_counts(cases) == receipt["totals"] == original["actual_totals"] and
                [{k: c[k] for k in ("classname", "name")} for c in cases] == expected,
                "Native XML digest, cases or counts disagree")
        start = int(datetime.fromisoformat(receipt["started_at_utc"]).timestamp() * 10**9)
        end = int(datetime.fromisoformat(receipt["finished_at_utc"]).timestamp() * 10**9)
        cross = tests.collect_ios_application_receipts(root, plan, tests.safe_path(root, relative), start, end, context, [module])
        require(cross["errors"] == [] and cross["ios_applications"] == receipt["ios_applications"],
                "Independent native Worker/runtime/binary/install/cleanup review failed")
        native, = cross["ios_applications"]
        payload = archive.document(root, native["receipt_path"])
        scale, = payload["application_protocol"]["vector_scale_observations"]
        projections.append({**scale, "simulator": simulator["udid"], "source_revision": receipt["source_revision"],
                            "actual_cases": receipt["totals"]["executed"], "passed_cases": receipt["totals"]["passed"],
                            "complete_native_lifecycle": True, "original_XML_preserved": True})
        bindings.append({"output": relative, "receipt_sha256": tests.sha256(tests.safe_path(root, relative + "/receipt.json")),
                         "original_XML_sha256": report["sha256"], "native_receipt_sha256": native["receipt_sha256"],
                         "held_input_count": len(before), "observed_compile_tasks": original["observed_compile_task_statuses"]})
    require(tests.snapshot_inputs(root) == current_inputs and
            tests.git_revision(root) == projections[0]["source_revision"], "Source changed during the shared review")
    return {**validate_pair(projections), "independent_original_receipt_bindings": bindings,
            "no_automatic_issue_closure": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    destination = tests.safe_path(tests.ROOT, args.output)
    require(destination.parent == tests.safe_path(tests.ROOT, "build/ci-verification") and not destination.exists(),
            "Use a fresh owned verification summary path")
    result = review(tests.ROOT)
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True); stream.write("\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
