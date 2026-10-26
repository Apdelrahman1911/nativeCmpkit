#!/usr/bin/env python3
"""Independent readback of raw001/offline evidence; never executes the harness.

Requires retained task-owned raw001/work for local filesystem cross-checks.
Optional --report verificationNNN.json is exclusive-create; default is read-only.
No Gradle, Node/Yarn, network requests, installation or cleanup is performed.
"""
from __future__ import annotations

import argparse
import base64
import datetime
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tarfile
from urllib.parse import urlsplit
import zipfile

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[4]
PARENT = "nativecmpkit-fixture-parent"
LEAF = "nativecmpkit-fixture-leaf"
NODE = "/root/.gradle/nodejs/node-v24.16.0-linux-x64/bin/node"
YARN = "/root/.gradle/yarn/yarn-v1.22.22/bin/yarn.js"
MARKER = b"self-authored harmless fixture marker\n"
EXPECTED = {
    "bootstrap": (0, "unfrozen-bootstrap-succeeded"),
    "YF001-positive": (0, "frozen-install-succeeded"),
    "YF002-missing-lock": (0, "accepted-without-lock-counterexample"),
    "YF003-direct-drift": (1, "frozen-lock-rejection"),
    "YF004-wrong-sri": (1, "tarball-integrity-rejection"),
    "YF005-changed-tarball": (1, "tarball-integrity-rejection"),
    "YF006-incomplete-transitive": (0, "accepted-incomplete-transitive-lock-counterexample"),
    "YF008-script-control": (0, "scripts-control-succeeded"),
    "YF008-scripts-suppressed": (0, "frozen-install-scripts-suppressed"),
}
inputs = {}
checks = 0


def check(condition, message):
    global checks
    checks += 1
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    check(path.is_file(), "Missing evidence input: " + str(path))
    check(not any(p.is_symlink() for p in (path, *path.parents)), "Symlink evidence input")
    data = path.read_bytes()
    name = str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)
    inputs[name] = sha(data)
    return data


def document(path):
    return json.loads(read(path))


def snapshot(path):
    if not path.exists():
        check(not path.is_symlink(), "Absent input is a symlink")
        return {"exists": False, "bytes": 0, "sha256": None}
    data = read(path)
    return {"exists": True, "bytes": len(data), "sha256": sha(data)}


def check_manifest(directory, manifest):
    for name, expected in manifest.items():
        path = directory / name
        check(not Path(name).is_absolute() and ".." not in Path(name).parts, "Unsafe manifest path")
        check("work" not in Path(name).parts and "tmp" not in Path(name).parts, "Work directory archived")
        check(sha(read(path)) == expected, "Evidence hash mismatch: " + name)


def sri(data, algorithm="sha512"):
    return algorithm + "-" + base64.b64encode(hashlib.new(algorithm, data).digest()).decode()


def tar_members(path):
    data = read(path)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        result = {}
        for member in archive:
            check(member.isfile() and re.fullmatch(r"package/[a-z][a-z0-9.-]*", member.name), "Unexpected tar member")
            check((member.uid, member.gid, member.mtime, member.mode) == (0, 0, 0, 0o644), "Tar metadata drift")
            name = member.name.removeprefix("package/")
            check(name not in result, "Duplicate tar member")
            result[name] = archive.extractfile(member).read()
        return result


def verify():
    report = {"scope": "independent-post-run-readback-not-a-new-Yarn-or-Gradle-execution", "manifest_entries": {}}
    for run, code, ending in (("offline001", 1, "FAILED (errors=1)"), ("offline002", 0, "OK")):
        directory = BASE / run
        receipt = document(directory / "receipt.json")
        check_manifest(directory, receipt["archived_file_sha256"])
        log = read(directory / "stderr.log").decode()
        check("Ran 67 tests in " in log and log.rstrip().endswith(ending), "Offline count/result mismatch")
        check(receipt["returncode"] == code and receipt["reason"] == "completed", "Offline process result mismatch")
        check(receipt["source_sha256_before"] == receipt["source_sha256_after"], "Offline inputs changed during run")
        for name, digest in receipt["source_sha256_before"].items():
            check(sha(read(directory / "harness-inputs" / Path(name).name)) == digest, "Offline source snapshot mismatch")
        report["manifest_entries"][run] = len(receipt["archived_file_sha256"])
    check("Cannot call rmtree on a symbolic link" in read(BASE / "offline001/stderr.log").decode(), "First failure not retained")
    report["offline_tests"] = {"offline001": {"executed": 67, "errors": 1, "exit_code": 1},
                               "offline002": {"executed": 67, "errors": 0, "exit_code": 0}}

    directory = BASE / "raw001"
    summary = document(directory / "summary.json")
    check_manifest(directory, summary["archived_file_hashes"])
    report["manifest_entries"]["raw001"] = len(summary["archived_file_hashes"])
    check(summary["planned_cases"] == list(EXPECTED) == summary["attempted_cases"], "Case plan/order mismatch")
    check(summary["exit_code"] == 0 and summary["all_selected_observations_matched"], "Raw suite did not match predictions")
    check(not summary["harness_error"] and not summary["unexecuted_cases"] and not summary["incomplete_case_receipts"], "Incomplete raw suite")
    check(not summary["security_enforcement_complete"] and not summary["kernel_or_egress_sandbox"], "Scope overclaim")
    check(summary["harness_inputs_before"] == summary["harness_inputs_after"], "Raw sources changed while running")
    check(summary["tool_inputs_before"] == summary["tool_inputs_after"], "Raw tools changed while running")
    for name, digest in summary["harness_inputs_before"].items():
        check(sha(read(REPO / name)) == digest, "Current harness source differs from raw001 input")
        check(sha(read(directory / "harness-inputs" / Path(name).name)) == digest, "Archived raw source mismatch")
    for tool in summary["tool_inputs_before"]:
        check(sha(read(Path(tool["path"]))) == tool["sha256"], "Pinned installed tool has changed")
    for name, stdout in (("node", b"v24.16.0\n"), ("yarn", b"1.22.22\n")):
        logs = directory / "versions" / name
        process = document(logs / "process.json")
        check(process["reason"] == "completed" and process["exit_code"] == 0, "Version command failed")
        check(read(logs / "stdout.log") == stdout and read(logs / "stderr.log") == b"", "Version observation differs")
        for channel in ("stdout", "stderr"):
            check(snapshot(logs / (channel + ".log")) == process[channel], "Version log hash differs")

    artifacts = {name: read(directory / "registry" / (name + ".tgz")) for name in (
        PARENT + "-1.0.0", PARENT + "-2.0.0", LEAF + "-1.0.0", LEAF + "-1.0.0-changed")}
    packages = {name: tar_members(directory / "registry" / (name + "-1.0.0.tgz")) for name in (PARENT, LEAF)}
    changed = tar_members(directory / "registry" / (LEAF + "-1.0.0-changed.tgz"))
    check(set(packages[LEAF]) == set(changed), "Changed tar member set differs")
    check([key for key in packages[LEAF] if packages[LEAF][key] != changed[key]] == ["payload.txt"], "Changed tar is not only payload drift")
    check(changed["payload.txt"] == b"changed valid payload\n", "Changed tar payload differs")
    seed = read(directory / "seed/yarn.lock")
    known = {"/registry/" + name: read(directory / "registry" / (name + ".json")) for name in (PARENT, LEAF)}
    for name in (PARENT, LEAF):
        meta = json.loads(known["/registry/" + name])
        for version, package in meta["versions"].items():
            tarpath = "/registry/" + name + "/-/" + name + "-" + version + ".tgz"
            data = artifacts[name + "-" + version]
            check(package["dist"]["tarball"] == summary["registry"] + tarpath.removeprefix("/registry"), "Nonfixture registry origin")
            check(package["dist"]["integrity"] == sri(data), "Metadata integrity differs")
            check(package["dist"]["shasum"] == hashlib.sha1(data).hexdigest(), "Metadata SHA1 differs")
            known[tarpath] = data

    server = document(directory / "server-requests.json")
    check(len(server) == 22, "Unexpected registry request count")
    report["cases"] = []
    process_times = []
    for case, (exit_code, category) in EXPECTED.items():
        archive = directory / "cases" / case
        work = directory / "work" / case
        receipt = document(archive / "receipt.json")
        plan = document(archive / "case-plan.json")
        process = document(archive / "process.json")
        check(receipt["process"] == process, "Nested process receipt differs")
        check(process["reason"] == "completed" and process["exit_code"] == exit_code and process["cleanup"] is None, "Actual process outcome differs")
        check(process["free_bytes_before"] >= 8192 * 1024**2 and process["free_bytes_after"] >= 8192 * 1024**2, "Reserve evidence below bound")
        process_times.append(process["elapsed_seconds"])
        argv = process["argv"]
        check(argv[:3] == [NODE, YARN, "install"], "Unpinned executable argv")
        check(argv == plan["argv"] and argv[argv.index("--registry") + 1] == summary["registry"], "Actual registry/argv differs")
        check(("--frozen-lockfile" in argv) == (case != "bootstrap"), "Frozen flag differs")
        check(("--ignore-scripts" in argv) == (case != "YF008-script-control"), "Script flag differs")
        check(not any(flag in argv for flag in ("--force", "--update-checksums", "--offline", "--audit")), "Unintended bypass flag")
        check(plan["node_modules_absent_before"] and all(plan["fresh_directories"].values()), "Not fresh before install")
        check(receipt["inputs_before"] == receipt["inputs_after"] == plan["inputs_before"], "Root inputs changed")
        for name, value in receipt["inputs_before"].items():
            check(snapshot(archive / "inputs" / name) == value == snapshot(work / name), "Root input snapshot differs")
        check(snapshot(archive / "inputs/yarn.lock") == receipt["lock_before"], "Before lock snapshot differs")
        check(snapshot(archive / "outputs/yarn.lock") == receipt["lock_after"] == snapshot(work / "yarn.lock"), "After lock snapshot differs")
        check(read(archive / "outputs/package.json") == read(archive / "inputs/package.json"), "Output manifest changed")
        if case not in {"bootstrap", "YF002-missing-lock"}:
            check(receipt["lock_before"] == receipt["lock_after"], "Frozen invocation mutated lock")
        if case == "YF002-missing-lock":
            check(not receipt["lock_before"]["exists"] and not receipt["lock_after"]["exists"], "Missing lock was created")
        elif case == "YF004-wrong-sri":
            before = read(archive / "inputs/yarn.lock")
            wrong = "sha512-" + base64.b64encode(bytes(64)).decode()
            check(base64.b64decode(receipt["lock_leaf_integrity_before"].split("-", 1)[1], validate=True) == bytes(64), "Wrong SRI malformed")
            check(before == seed.replace(sri(artifacts[LEAF + "-1.0.0"]).encode(), wrong.encode(), 1), "Wrong-SRI mutation not singular")
        elif case == "YF006-incomplete-transitive":
            text = read(archive / "inputs/yarn.lock").decode()
            check(LEAF + "@1.0.0:" not in text and PARENT + "@1.0.0:" in text and '    ' + LEAF + ' "1.0.0"' in text, "Transitive case mutation differs")
        elif case != "bootstrap":
            check(read(archive / "inputs/yarn.lock") == seed, "Case did not receive original seed")

        root_package = json.loads(read(archive / "inputs/package.json"))
        check(root_package["dependencies"] == {PARENT: "2.0.0" if case == "YF003-direct-drift" else "1.0.0"}, "Direct drift differs")
        for name, path in (("root", work / "root-script-ran.txt"),
                           ("dependency", work / "node_modules" / LEAF / "dependency-script-ran.txt")):
            value = snapshot(path)
            check(value == receipt["markers"][name], "Marker snapshot differs")
            check(value["exists"] == (case == "YF008-script-control"), "Script marker state differs")
            if value["exists"]:
                check(read(path) == MARKER == read(archive / "outputs" / (name + "-marker.txt")), "Harmless marker bytes differ")
        if exit_code == 0:
            for name in (PARENT, LEAF):
                graph = receipt["installed_graph"][name]
                check(graph["version"] == "1.0.0" and not graph["unexpected_entries"], "Installed graph differs")
                for file, data in packages[name].items():
                    target = work / "node_modules" / name / file
                    check(read(target) == data and snapshot(target) == graph["files"][file], "Installed package bytes differ")

        records = [item for item in server if item["case"] == case]
        check(records == receipt["server_requests"], "Per-case server events differ")
        for row in records:
            data = artifacts[LEAF + "-1.0.0-changed"] if case == "YF005-changed-tarball" and row["path"].endswith(LEAF + "-1.0.0.tgz") else known[row["path"]]
            check(row["method"] == "GET" and row["status"] == 200 and row["write_complete"], "Incomplete/rejected server event")
            check(not row["auth_header_present"] and row["host_allowed"] and row["client_allowed"], "Disallowed server request")
            check(row["response_sha256"] == sha(data) and row["response_bytes"] == len(data), "Served body differs")
        errors = []
        for channel in ("stdout", "stderr"):
            path = archive / (channel + ".log")
            check(snapshot(path) == process[channel], "Process log hash mismatch")
            errors.extend(record["data"] for line in read(path).decode().splitlines() if line.startswith("{")
                          for record in [json.loads(line)] if record.get("type") == "error")
        check(errors == receipt["actual_errors"], "Parsed error records differ")
        if case == "YF003-direct-drift":
            check(errors == ["Your lockfile needs to be updated, but yarn was run with `--frozen-lockfile`."], "Not exact frozen error")
        elif exit_code == 1:
            data = artifacts[LEAF + "-1.0.0" + ("-changed" if case == "YF005-changed-tarball" else "")]
            url = summary["registry"] + "/" + LEAF + "/-/" + LEAF + "-1.0.0.tgz"
            expected = (url + ': Integrity check failed for "' + LEAF
                        + '" (computed integrity doesn\'t match our records, got "'
                        + sri(data) + " " + sri(data, "sha1") + '")')
            check(errors == [expected], "Not exact served-byte integrity error")
        else:
            check(not errors, "Successful install had reporter errors")
        classification = receipt["classification"]
        check(classification["expected_category"] == category == classification["observed_category"], "Category mismatch")
        check(classification["observation_matched"] and not classification["security_enforcement_pass"], "Raw scope overclaim")
        counterexample = case in {"YF002-missing-lock", "YF006-incomplete-transitive"}
        check(classification["counterexample"] == counterexample, "Counterexample mislabeled")
        report["cases"].append({"case": case, "exit_code": exit_code, "category": category,
                                "counterexample": counterexample, "requests": len(records)})

    review = document(BASE / "wasm-tooling-ignore-scripts-source-review.json")
    check(sha(read(REPO / review["report"]["path"])) == review["report"]["sha256"], "Wasm report hash differs")
    check(sha(read(REPO / review["root_input"]["path"])) == review["root_input"]["sha256"], "Wasm reviewed root bytes changed")
    check(sha(read(Path(review["kgp"]["path"]))) == review["kgp"]["sha256"], "Wasm reviewed KGP bytes changed")
    with zipfile.ZipFile(review["kgp"]["path"]) as archive:
        for row in review["flow"]:
            check(sha(archive.read(row["jar_entry"])) == row["class_sha256"], "Wasm reviewed class hash differs")
    check(not review["actual_tooling_argv_observed"] and not review["frozen_policy_verified"], "Wasm source review overclaim")

    report.update(raw_install_invocations=9, raw_fixture_cases_excluding_bootstrap=8, version_probes=2,
                  actual_raw_yarn_or_gradle_execution_by_verifier=False, server_requests=22,
                  elapsed_seconds_raw_suite=summary["elapsed_seconds"], max_install_elapsed_seconds=max(process_times),
                  raw_suite_bound_satisfied=summary["elapsed_seconds"] < 300,
                  local_task_owned_work_files_checked=True, source_and_tool_hashes_rechecked=True,
                  counterexamples=summary["counterexamples"], kernel_or_egress_sandbox=False,
                  policy_or_trust_gate_passed=False)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report")
    args = parser.parse_args()
    if args.report:
        check(re.fullmatch(r"verification[0-9]{3}\.json", args.report), "Invalid report basename")
        check(not (BASE / args.report).exists() and not (BASE / args.report).is_symlink(), "Refusing existing report")
    result = {"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "argv": sys.argv,
              "verifier_sha256": sha(Path(__file__).read_bytes()), "error": None}
    try:
        result.update(verify())
    except Exception as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
    result.update(ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), checks=checks,
                  inspected_file_sha256=inputs, exit_code=1 if result["error"] else 0)
    if args.report:
        with (BASE / args.report).open("x") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")
    print(json.dumps({key: result.get(key) for key in ("exit_code", "error", "checks", "manifest_entries",
          "raw_fixture_cases_excluding_bootstrap", "server_requests", "counterexamples")}, indent=2))
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
