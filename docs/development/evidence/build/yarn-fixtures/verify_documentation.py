#!/usr/bin/env python3
"""Read back authored Yarn evidence/doc bindings; no Gradle/Node/Yarn or network.

Does not execute/import the fixture harness, proposed parser, or init snippet.
Only optional --report documentation-verificationNNN.json writes a new receipt.
Git subprocesses below are read-only ignore checks, each bounded to ten seconds.
This local check requires the recorded generated manifests and installed JARs.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit
import zipfile

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[4]
inputs = {}
checks = 0


def check(value, message):
    global checks
    checks += 1
    if not value:
        raise ValueError(message)


def read(path):
    path = Path(path)
    if not path.is_absolute():
        path = REPO / path
    check(".." not in path.parts, "Input path traversal")
    check(path.is_file() and not path.is_symlink(), "Missing/symlink input: " + str(path))
    allowed_jar = path.suffix == ".jar" and (
        path.is_relative_to(Path("/root/.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-gradle-plugin/2.4.20"))
        or path.is_relative_to(Path("/root/.gradle/wrapper/dists/gradle-9.7.1-bin")))
    check(path.is_relative_to(REPO) or allowed_jar, "Input outside authored evidence/public tool artifact scope")
    check(not any(p.is_symlink() for p in path.parents), "Symlink input ancestor")
    data = path.read_bytes()
    key = str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)
    digest = hashlib.sha256(data).hexdigest()
    check(key not in inputs or inputs[key] == digest, "Input changed during readback: " + key)
    inputs[key] = digest
    return data


def document(path):
    return json.loads(read(path))


def bound(path, expected):
    check(hashlib.sha256(read(path)).hexdigest() == expected, "Hash differs: " + str(path))


def verify():
    check(shutil.disk_usage(REPO).free >= 8192 * 1024**2, "Less than 8 GiB disk reserve")
    result = {"scope": "documentation/source-binding consistency, not new fixture/library tests",
              "new_gradle_node_yarn_or_network_execution": False, "library_tests_executed": 0,
              "policy_or_trust_gate_passed": False, "archived_manifest_entries": {}, "local_links": []}
    for run, key, expected in (("offline001", "archived_file_sha256", 6),
                               ("offline002", "archived_file_sha256", 6),
                               ("raw001", "archived_file_hashes", 125)):
        receipt = document(BASE / run / ("summary.json" if run == "raw001" else "receipt.json"))
        manifest = receipt[key]
        check(len(manifest) == expected, "Archived manifest size changed")
        for name, digest in manifest.items():
            parts = Path(name)
            check(not parts.is_absolute() and not {"..", "work", "tmp"}.intersection(parts.parts),
                  "Unsafe archived-manifest path")
            bound(BASE / run / name, digest)
        result["archived_manifest_entries"][run] = len(manifest)
    for run, code, ending in (("offline001", 1, "FAILED (errors=1)"), ("offline002", 0, "OK")):
        receipt = document(BASE / run / "receipt.json")
        log = read(BASE / run / "stderr.log").decode()
        check(receipt["returncode"] == code and "Ran 67 tests in " in log and log.rstrip().endswith(ending),
              "Original offline result changed")
    original = document(BASE / "verification001.json")
    check(original["exit_code"] == 0 and original["error"] is None and original["checks"] == 1876,
          "Original independent readback result differs")
    bound(BASE / "verify_raw001.py", original["verifier_sha256"])

    wasm = document(BASE / "wasm-tooling-ignore-scripts-source-review.json")
    bound(wasm["report"]["path"], wasm["report"]["sha256"])
    bound(wasm["root_input"]["path"], wasm["root_input"]["sha256"])
    bound(wasm["kgp"]["path"], wasm["kgp"]["sha256"])
    check(not wasm["actual_tooling_argv_observed"] and not wasm["frozen_policy_verified"], "Source-only scope changed")
    class_checks = 0
    with zipfile.ZipFile(wasm["kgp"]["path"]) as archive:
        for row in wasm["flow"]:
            check(hashlib.sha256(archive.read(row["jar_entry"])).hexdigest() == row["class_sha256"], "Class hash differs")
            class_checks += 1
    for basename, manifest_key in (("ordinary-policy-graph-observation001.json", "read_input_hashes"),
                                   ("wasm-tooling-destination-source-review.json", "input_hashes"),
                                   ("wasm-tooling-init-api-review.json", "input_hashes")):
        evidence = document(BASE / basename)
        for path, meta in evidence[manifest_key].items():
            bound(path, meta["sha256"])
        rows = evidence.get("source_only_task_flow", evidence.get("flow", evidence.get("classes", [])))
        for row in rows:
            jar = row.get("artifact", evidence.get("kgp", {}).get("path"))
            check(jar in inputs, "Class artifact was not hash-bound first")
            with zipfile.ZipFile(jar) as archive:
                check(hashlib.sha256(archive.read(row["jar_entry"])).hexdigest() == row["class_sha256"], "Class hash differs")
            class_checks += 1
        for row in evidence.get("resources", []):
            with zipfile.ZipFile(evidence["kgp"]["path"]) as archive:
                data = archive.read(row["jar_entry"])
            check(len(data) == row["bytes"] and hashlib.sha256(data).hexdigest() == row["sha256"], "Resource differs")
    result["class_entry_hash_checks_including_repeated_classes"] = class_checks

    docs = [REPO / "scripts/dependencies/yarn" / name for name in
            ("README.md", "ordinary-policy-plan.md", "tooling-receipt-init-proposal.md")]
    docs += [BASE / name for name in ("README.md", "wasm-tooling-ignore-scripts-source-review.md",
                                     "wasm-tooling-destination-source-review.md")]
    for path in docs:
        source = read(path).decode()
        references = dict(re.findall(r"^\[([^\]]+)\]:\s+(\S+)\s*$", source, re.MULTILINE))
        for key in re.findall(r"\[[^\]]*\]\[([^\]]+)\]", source):
            check(key in references, "Undefined Markdown reference")
        links = list(references.values()) + re.findall(r"(?<!!)\[[^\]\n]*\]\(([^)\n]+)\)", source)
        for link in links:
            parsed = urlsplit(link)
            check(not parsed.scheme and not parsed.netloc, "External links are not verified by this local checker")
            target = (path.parent / unquote(parsed.path)).resolve()
            check(target.is_relative_to(REPO) and target.exists(), "Broken/out-of-repository local link: " + link)
            result["local_links"].append({"document": str(path.relative_to(REPO)), "target": str(target.relative_to(REPO))})

    for name in ("scripts/dependencies/yarn/.gitignore", BASE / ".gitignore"):
        read(name)
    check(not (REPO / "scripts/dependencies/yarn/__init__.py").exists(), "Sibling discovery boundary changed")
    ignored = ["scripts/dependencies/yarn/__pycache__/sentinel", "scripts/dependencies/yarn/.test-work/sentinel",
               "docs/development/evidence/build/yarn-fixtures/raw001/work/YF001-positive/package.json",
               "docs/development/evidence/build/yarn-fixtures/raw001/tmp/sentinel"]
    argv = ["git", "check-ignore", "-v", "-z", "--stdin"]
    process = subprocess.run(argv, input=("\0".join(ignored) + "\0").encode(), cwd=REPO,
                             capture_output=True, check=False, timeout=10)
    check(process.returncode == 0 and not process.stderr, "Git ignore readback failed")
    fields = process.stdout.decode().split("\0")
    check(fields[-1] == "" and len(fields[:-1]) == len(ignored) * 4, "Not all task-owned work paths ignored")
    result["git_ignore"] = {"argv": argv, "exit_code": process.returncode,
                            "records": [dict(zip(("source", "line", "pattern", "path"), fields[i:i+4]))
                                        for i in range(0, len(fields)-1, 4)]}
    check([row["path"] for row in result["git_ignore"]["records"]] == ignored, "Ignored paths differ")
    result["free_bytes_at_end"] = shutil.disk_usage(REPO).free
    check(result["free_bytes_at_end"] >= 8192 * 1024**2, "Disk reserve lost")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report")
    args = parser.parse_args()
    if args.report:
        check(re.fullmatch(r"documentation-verification[0-9]{3}\.json", args.report), "Invalid report basename")
        check(not (BASE / args.report).exists() and not (BASE / args.report).is_symlink(), "Receipt already exists")
    record = {"argv": sys.argv, "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "error": None}
    try:
        record.update(verify())
    except Exception as exc:
        record["error"] = type(exc).__name__ + ": " + str(exc)
    record.update(exit_code=1 if record["error"] else 0, checks=checks, inspected_file_sha256=inputs,
                  ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    if args.report:
        with (BASE / args.report).open("x") as stream:
            json.dump(record, stream, indent=2, sort_keys=True)
            stream.write("\n")
    print(json.dumps({key: record.get(key) for key in ("exit_code", "error", "checks", "archived_manifest_entries",
                      "class_entry_hash_checks_including_repeated_classes")}, indent=2))
    return record["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
