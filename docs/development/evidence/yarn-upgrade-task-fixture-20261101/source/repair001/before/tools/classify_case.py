#!/usr/bin/env python3
"""Classify ONE completed private U1/U2/U3/U4 run; never launch, retry or signal a process.

Input receipts/logs require independent lead source/runtime/ownership review. This
classifier does not authenticate JSON producers or establish root dependency trust.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import freeze_inputs as frozen

HELPER_SHA256 = "6473a953ad6c95e0eb00f0e79e2275aac0731976db06356b73bcfa6abfac0f14"
GATE = ":nativeCmpkitRefuseOrdinaryYarnUpgrade"
SENTINEL = ":nativeCmpkitActionSentinel"
JS_UPGRADE = ":kotlinUpgradeYarnLock"
WASM_UPGRADE = ":kotlinWasmUpgradeYarnLock"
JS_PRIMARY = ":kotlinNpmInstall"
WASM_PRIMARY = ":kotlinWasmNpmInstall"
INDIRECT_JS = ":nativeCmpkitIndirectJsUpgrade"
INDIRECT_WASM = ":nativeCmpkitIndirectWasmUpgrade"
ERROR = "NCYUG-actual-upgrade-forbidden-before-root-task-actions"
REQUESTS = {
    "U1": ["kotlinUpgradeYarnLock", "nativeCmpkitActionSentinel"],
    "U2": ["nativeCmpkitIndirectWasmUpgrade", "nativeCmpkitActionSentinel"],
    "U3": ["nativeCmpkitIndirectJsUpgrade", "nativeCmpkitIndirectWasmUpgrade", "nativeCmpkitActionSentinel"],
    "U4": ["nativeCmpkitActionSentinel"],
}
BINDINGS = frozenset((
    "js_upgrade_typed_provider_identity", "wasm_upgrade_typed_provider_identity",
    "js_primary_typed_provider_identity", "wasm_primary_typed_provider_identity", "gate_typed_provider_identity",
    "js_upgrade_depends_on_primary", "wasm_upgrade_depends_on_primary", "js_upgrade_depends_on_gate", "wasm_upgrade_depends_on_gate",
    "indirect_js_depends_on_actual_upgrade", "indirect_wasm_depends_on_actual_upgrade", "gate_dependency_free",
))
IDENTITY = frozenset(("schema", "case_id", "run_id", "input_sha256", "helper_sha256", "gradle_version", "java_major", "configured_kgp_version"))
PATH = re.compile(r":[A-Za-z0-9_:-]+\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")

class Refusal(ValueError):
    pass

def require(value, code):
    if not value:
        raise Refusal(code)

def strict_keys(value, keys, code):
    require(type(value) is dict and set(value) == set(keys), code)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def no_duplicates(pairs):
    data = {}
    for key, value in pairs:
        require(key not in data, "duplicate-json-key")
        data[key] = value
    return data

def json_bytes(raw):
    require(type(raw) is bytes and 0 < len(raw) <= 256 * 1024, "receipt-byte-cap")
    try:
        return json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=no_duplicates,
                          parse_constant=lambda _: (_ for _ in ()).throw(Refusal("nonfinite-json")))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise Refusal("invalid-json") from error

def read_regular(path, cap):
    st = path.stat(follow_symlinks=False)
    require(stat.S_ISREG(st.st_mode) and st.st_nlink == 1 and 0 <= st.st_size <= cap, "unsafe-or-oversized-input")
    require(not any(p.is_symlink() for p in (path, *path.parents)), "symlink-input")
    raw = path.read_bytes()
    require(len(raw) == st.st_size, "input-changed-during-read")
    return raw

def identity(record, expected, extra):
    strict_keys(record, IDENTITY | set(extra), "receipt-fields")
    require(type(record["schema"]) is int and record["schema"] == 1, "receipt-schema")
    require(record["case_id"] == expected["case_id"] and record["run_id"] == expected["run_id"], "foreign-or-stale-invocation")
    require(record["input_sha256"] == expected["input_sha256"] and HEX.fullmatch(record["input_sha256"]), "source-input-binding")
    require(record["helper_sha256"] == HELPER_SHA256, "helper-source-binding")
    require(record["gradle_version"] == "9.7.1" and type(record["java_major"]) is int and record["java_major"] == 17,
            "runtime-version-binding")
    require(record["configured_kgp_version"] == "2.4.20", "configured-kgp-binding")


def validate_case(graph, result, actions, sentinel, execution, log, expected, hashes):
    """Pure comparison seam, also exercised by synthetic-only tests."""
    strict_keys(expected, ("case_id", "run_id", "input_sha256", "command_sha256"), "expected-fields")
    case = expected["case_id"]
    require(case in REQUESTS and type(expected["run_id"]) is str and re.fullmatch(case + r"-[0-9a-f]{16}", expected["run_id"]), "expected-invocation")
    require(type(expected["input_sha256"]) is str and HEX.fullmatch(expected["input_sha256"]), "expected-input-digest")
    require(type(expected["command_sha256"]) is str and HEX.fullmatch(expected["command_sha256"]), "expected-command-digest")
    strict_keys(execution, ("schema", "case_id", "run_id", "input_sha256", "command_sha256", "exit_code", "stop_reason",
                           "sources_unchanged", "bounds_verified", "cleanup_verified", "artifacts_sha256"), "execution-fields")
    require(type(execution["schema"]) is int and execution["schema"] == 1, "execution-schema")
    for key in expected:
        require(execution[key] == expected[key], "execution-invocation-binding")
    require(execution["stop_reason"] == "completed", "not-normal-completion")
    require(all(execution[k] is True for k in ("sources_unchanged", "bounds_verified", "cleanup_verified")), "external-control-not-verified")
    require(type(execution["exit_code"]) is int and execution["exit_code"] == (0 if case == "U4" else 1), "wrong-process-exit")
    require(execution["artifacts_sha256"] == hashes, "original-artifact-hash-binding")
    identity(graph, expected, ("record_type", "requested_tasks", "bindings", "registered_upgrade_paths", "root_tasks",
                              "all_root_non_gate_tasks_ordered_after_gate", "gate_selected_by_actual_object", "included_build_actions_in_scope"))
    require(graph["record_type"] == "actual-kgp-upgrade-graph", "graph-type")
    require(graph["requested_tasks"] == REQUESTS[case], "requested-tasks")
    strict_keys(graph["bindings"], BINDINGS, "typed-binding-fields")
    require(all(v is True for v in graph["bindings"].values()), "typed-object-or-dependency-binding")
    require(graph["registered_upgrade_paths"] == sorted((JS_UPGRADE, WASM_UPGRADE)), "actual-upgrade-registry")
    require(graph["all_root_non_gate_tasks_ordered_after_gate"] is True, "root-ordering-binding")
    require(graph["gate_selected_by_actual_object"] is (case != "U4"), "actual-gate-membership")
    require(graph["included_build_actions_in_scope"] is False, "scope-expansion")
    require(type(graph["root_tasks"]) is list and 1 <= len(graph["root_tasks"]) <= 128, "root-graph-cap")
    kinds = {}
    for row in graph["root_tasks"]:
        strict_keys(row, ("path", "kind"), "task-fields")
        require(type(row["path"]) is str and PATH.fullmatch(row["path"]) and row["path"] not in kinds, "task-path-or-duplicate")
        require(row["kind"] in ("denial", "upgrade", "primary", "other"), "task-kind")
        kinds[row["path"]] = row["kind"]
    required = {SENTINEL: "other"}
    if case != "U4": required[GATE] = "denial"
    if case in ("U1", "U3"): required.update({JS_UPGRADE: "upgrade", JS_PRIMARY: "primary"})
    if case in ("U2", "U3"): required.update({WASM_UPGRADE: "upgrade", WASM_PRIMARY: "primary", INDIRECT_WASM: "other"})
    if case == "U3": required[INDIRECT_JS] = "other"
    require(all(kinds.get(path) == kind for path, kind in required.items()), "required-actual-graph-membership")
    require({p for p, k in kinds.items() if k == "upgrade"} == {p for p, k in required.items() if k == "upgrade"}, "foreign-selected-upgrade")
    require({p for p, k in kinds.items() if k == "primary"} == {p for p, k in required.items() if k == "primary"}, "foreign-selected-primary")
    if case == "U4": require(kinds == required, "sentinel-only-root-graph")
    identity(result, expected, ("record_type", "graph_sha256", "build_failed", "observed_actions", "root_task_states", "included_build_actions_in_scope"))
    require(result["record_type"] == "actual-kgp-upgrade-result" and result["graph_sha256"] == hashes["graph"], "completed-result-graph-binding")
    require(result["build_failed"] is (case != "U4") and result["included_build_actions_in_scope"] is False, "result-status-or-scope")
    expected_action = SENTINEL if case == "U4" else GATE
    require(result["observed_actions"] == [expected_action] and len(actions) == 1, "unexpected-or-missing-root-action")
    action = actions[0]
    identity(action, expected, ("record_type", "sequence", "path", "allowed_by_fixture_tripwire"))
    require(action["record_type"] == "root-task-action" and type(action["sequence"]) is int and action["sequence"] == 1,
            "action-record-or-sequence")
    require(action["path"] == expected_action and action["allowed_by_fixture_tripwire"] is True, "tripwire-or-foreign-action")
    require(type(result["root_task_states"]) is list and len(result["root_task_states"]) == len(kinds), "task-state-coverage")
    states = {}
    for row in result["root_task_states"]:
        strict_keys(row, ("path", "kind", "executed", "failed", "skipped", "up_to_date", "no_source", "exact_denial_in_failure_chain"), "task-state-fields")
        require(row["path"] in kinds and row["path"] not in states and row["kind"] == kinds[row["path"]], "task-state-identity")
        require(all(type(row[k]) is bool for k in ("executed", "failed", "skipped", "up_to_date", "no_source", "exact_denial_in_failure_chain")), "task-state-booleans")
        states[row["path"]] = row
    target = states[expected_action]
    require(target["executed"] and not any(target[k] for k in ("skipped", "up_to_date", "no_source")), "fresh-action-outcome-not-established")
    require(target["failed"] is (case != "U4") and target["exact_denial_in_failure_chain"] is (case != "U4"), "wrong-task-failure")
    require(not any(row["failed"] or row["exact_denial_in_failure_chain"] for p, row in states.items() if p != expected_action), "unrelated-task-failure")
    require(type(log) is str and len(log.encode("utf-8")) <= 8 * 1024 * 1024, "log-cap")
    markers = re.findall(r"(?m)^NCYB-FIXTURE-ACTION path=(:[A-Za-z0-9_:-]+)\r?$", log)
    require(markers == [expected_action] and log.count("NCYB-FIXTURE-ACTION") == 1, "original-log-action-binding")
    if case == "U4":
        require(sentinel is not None, "sentinel-receipt-missing")
        identity(sentinel, expected, ("record_type", "ran"))
        require(sentinel["record_type"] == "sentinel-action" and sentinel["ran"] is True, "sentinel-receipt-status")
        require(log.count("NCYB-FIXTURE-SENTINEL-RAN") == 1 and ERROR not in log, "original-log-sentinel-binding")
        require(re.search(r"(?m)^> Task :nativeCmpkitActionSentinel\r?$", log), "sentinel-console-outcome")
    else:
        require(sentinel is None and "NCYB-FIXTURE-SENTINEL-RAN" not in log, "sentinel-ran-before-denial")
        require(re.search(r"(?m)^> Task :nativeCmpkitRefuseOrdinaryYarnUpgrade FAILED\r?$", log), "denial-console-outcome")
        require(re.search(r"(?m)^\s*(?:>\s*)?" + re.escape(ERROR) + r"\s*$", log), "original-log-exact-denial")
    return {"schema": 1, "case_id": case, "run_id": expected["run_id"], "input_sha256": expected["input_sha256"],
            "result": "scoped-upgrade-schedule-verified", "actual_node_yarn_install_acceptance": False,
            "ordinary_root_adoption_or_dependency_trust": False, "included_build_actions_in_scope": False}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--case", choices=tuple(REQUESTS), required=True)
    p.add_argument("--receipts", type=Path, required=True)
    p.add_argument("--execution", type=Path, required=True)
    p.add_argument("--merged-log", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    try:
        plan = json_bytes(read_regular(args.plan, 256 * 1024))
        freeze_raw = read_regular(args.freeze, 256 * 1024)
        freeze = json_bytes(freeze_raw)
        current = frozen.inventory(args.root.resolve())
        require(current == freeze["files"] and frozen.source_digest(current) == freeze["source_digest"],
                "current-frozen-source-or-topology-changed")
        require(plan["source_freeze_sha256"] == digest(freeze_raw) and plan["source_digest"] == freeze["source_digest"],
                "plan-source-freeze-binding")
        selected = next(x for x in plan["cases"] if x["case_id"] == args.case)
        require(selected["input_sha256"] == freeze["source_digest"], "case-source-freeze-binding")
        expected = {k: selected[k] for k in ("case_id", "run_id", "input_sha256", "command_sha256")}
        names = {"graph.json", "result.json", "action-0001.json"} | ({"sentinel.json"} if args.case == "U4" else set())
        require(args.receipts.is_dir() and not args.receipts.is_symlink(), "receipt-directory")
        require({x.name for x in args.receipts.iterdir()} == names, "missing-extra-or-stale-receipt-files")
        raw = {name: read_regular(args.receipts/name, 256 * 1024) for name in names}
        log_raw = read_regular(args.merged_log, 8 * 1024 * 1024)
        hashes = {"graph": digest(raw["graph.json"]), "result": digest(raw["result.json"]),
                  "action-0001": digest(raw["action-0001.json"]), "merged_log": digest(log_raw)}
        if "sentinel.json" in raw: hashes["sentinel"] = digest(raw["sentinel.json"])
        result = validate_case(json_bytes(raw["graph.json"]), json_bytes(raw["result.json"]), [json_bytes(raw["action-0001.json"])],
                               json_bytes(raw["sentinel.json"]) if "sentinel.json" in raw else None,
                               json_bytes(read_regular(args.execution, 256 * 1024)), log_raw.decode("utf-8", "strict"), expected, hashes)
    except (ValueError, OSError, UnicodeError, KeyError, StopIteration, TypeError) as error:
        result = {"schema": 1, "case_id": args.case, "result": "refused",
                  "reason": str(error) if isinstance(error, Refusal) else "input-unavailable-or-invalid",
                  "ordinary_root_adoption_or_dependency_trust": False}
    with args.output.open("x") as f: json.dump(result, f, indent=2, sort_keys=True); f.write("\n")
    print(json.dumps(result, sort_keys=True))
    return int(result["result"] == "refused")


if __name__ == "__main__":
    raise SystemExit(main())
