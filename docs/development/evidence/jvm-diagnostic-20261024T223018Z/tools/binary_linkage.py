#!/usr/bin/env python3
"""Compile a narrow Java consumer against baseline JARs, then run UNCHANGED bytes.

No Gradle, network, source substitution or publication. Actual baseline and staged
candidate JARs plus explicitly supplied third-party dependencies are required.
An explicit separate diagnostic mode accepts input/receipt-bound local build JARs;
it never represents them as a staged Maven consumer or clears a distribution gate.
The same compiled classes run first on the baseline, then on the candidate with
only nativeCmpkit JARs replaced. This is six JVM linkage cases, not KMP ABI proof.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

from verify_artifacts import (CHECKSUM, GROUP, ROOT, InvalidArtifact, archive_names,
                              load_json_bytes, local_file, sha256)

SOURCE = ROOT / "tests/consumer/binary/src/nativecmpkit/consumer/LegacyBinaryConsumer.java"
MAIN_CLASS = "nativecmpkit.consumer.LegacyBinaryConsumer"


def file_record(path: Path, identity: str) -> dict:
    return {"identity": identity, "filename": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}


def verified_files(root: Path, records: list[dict]) -> dict[str, Path]:
    """Bind an evidence manifest to real confined bytes, never a asserted SHA alone."""
    result = {}
    if not isinstance(records, list) or not records:
        raise InvalidArtifact("Expected a nonempty artifact file inventory")
    for record in records:
        if not isinstance(record, dict):
            raise InvalidArtifact("Invalid artifact file record")
        name = record.get("path")
        path = local_file(root, root, name)
        if name in result or path in result.values():
            raise InvalidArtifact("Duplicate artifact file inventory entry")
        if type(record.get("bytes")) is not int or record["bytes"] != path.stat().st_size or record.get("sha256") != sha256(path):
            raise InvalidArtifact("Artifact bytes differ from source-bound/static inspection receipt")
        result[name] = path
    return result


def git_state(root: Path) -> tuple[str, bool]:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, timeout=30).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all"],
                                    cwd=root, text=True, timeout=30).strip()
    return head, bool(dirty)


def diagnostic_candidates(root: Path, inventory_path: Path, expected: set[str]) -> tuple[list[Path], dict, list[Path]]:
    """Validate local-build evidence without pretending it is a distributable package.

    The build command/unchanged-source receipts are supplied observations, not
    cryptographic build attestations. Actual receipt, source and JAR bytes are
    rechecked. This route remains independent of the strict staged-artifact path.
    """
    inventory = load_json_bytes(inventory_path.read_bytes())
    required = {"schema_version", "mode", "distribution_verified", "source_revision", "source_tree_dirty",
                "build_receipt", "source_input_receipt", "source_verification_receipt", "jars"}
    if (not isinstance(inventory, dict) or set(inventory) != required
            or type(inventory["schema_version"]) is not int or inventory["schema_version"] != 1
            or inventory["mode"] != "local-jar-diagnostic" or inventory["distribution_verified"] is not False
            or type(inventory["source_tree_dirty"]) is not bool
            or not isinstance(inventory["source_revision"], str) or not re.fullmatch(r"[0-9a-f]{40}", inventory["source_revision"])):
        raise InvalidArtifact("Explicit non-distribution local-JAR diagnostic inventory required")
    head, dirty = git_state(root)
    if (head, dirty) != (inventory["source_revision"], inventory["source_tree_dirty"]):
        raise InvalidArtifact("Diagnostic source base/dirtiness differs from its honest build inventory")
    receipts = {key: verified_files(root, [inventory[key]])[inventory[key]["path"]]
                for key in ("build_receipt", "source_input_receipt", "source_verification_receipt")}
    build, inputs, verification = (load_json_bytes(receipts[key].read_bytes())
                                   for key in ("build_receipt", "source_input_receipt", "source_verification_receipt"))
    if (not isinstance(build, dict) or type(build.get("exit_code")) is not int or build["exit_code"] != 0
            or not isinstance(build.get("command"), list) or not build["command"]
            or any(not isinstance(arg, str) for arg in build["command"])):
        raise InvalidArtifact("A successful inspected producer build receipt is required for local JAR diagnostics")
    if (not isinstance(verification, dict) or verification.get("input_hashes_unchanged") is not True
            or verification.get("changed_inputs") != [] or type(verification.get("exit_code")) is not int
            or verification["exit_code"] != 0):
        raise InvalidArtifact("Local producer build lacks successful unchanged-input verification")
    if (not isinstance(inputs, dict) or inputs.get("base_commit") != head
            or not isinstance(inputs.get("files"), dict) or not 1 <= len(inputs["files"]) <= 10_000):
        raise InvalidArtifact("Expected a bounded source-input receipt at the diagnostic base commit")
    source_paths = []
    for name, checksum in inputs["files"].items():
        path = local_file(root, root, name)
        if not isinstance(checksum, str) or not CHECKSUM.fullmatch(checksum) or sha256(path) != checksum:
            raise InvalidArtifact("Diagnostic producer source no longer matches captured build inputs")
        source_paths.append(path)
    jars = inventory["jars"]
    if not isinstance(jars, list) or any(not isinstance(item, dict) or type(item.get("published_module")) is not bool for item in jars):
        raise InvalidArtifact("Invalid local-JAR publication identity inventory")
    selected = [item for item in jars if item["published_module"]]
    if len(selected) != len(expected) or {item.get("artifact") for item in selected} != expected:
        raise InvalidArtifact("Missing/duplicate published modules in local-JAR diagnostic inventory")
    files = verified_files(root, jars)
    if any(path.suffix != ".jar" for path in files.values()):
        raise InvalidArtifact("Diagnostic classpath accepts actual JAR files only")
    selected_paths = [files[item["path"]] for item in sorted(selected, key=lambda item: item["artifact"])]
    info = {"mode": "local-jar-diagnostic", "distribution_verified": False,
            "maven_artifact_inspection_passed": False, "candidate_source_revision": head,
            "candidate_source_tree_dirty": dirty, "diagnostic_inventory_sha256": sha256(inventory_path),
            "candidate_build_receipt_sha256": sha256(receipts["build_receipt"]),
            "candidate_input_receipt_sha256": sha256(receipts["source_input_receipt"]),
            "candidate_source_verification_sha256": sha256(receipts["source_verification_receipt"]),
            "candidate_source_files_rechecked": len(source_paths)}
    return selected_paths, info, [inventory_path, *receipts.values(), *source_paths, *files.values()]


def ensure_unchanged(files: dict[Path, str]) -> None:
    for path, checksum in files.items():
        if path.is_symlink() or not path.is_file() or sha256(path) != checksum:
            raise InvalidArtifact("Recorded runtime/source/receipt/fixture bytes changed during linkage verification")


def third_party_jars(arguments: list[str]) -> list[tuple[str, Path]]:
    result, identities = [], set()
    for argument in arguments:
        identity, separator, name = argument.partition("=")
        if not separator or not identity or identity in identities or any(c in identity for c in ("\n", "\r", "\x00")):
            raise InvalidArtifact("--dependency requires a unique public-dependency-identity=/absolute/jar")
        path = Path(name)
        if not path.is_absolute() or not path.is_file() or path.is_symlink() or path.suffix != ".jar":
            raise InvalidArtifact("Explicit existing regular third-party JARs are required")
        with zipfile.ZipFile(path) as archive:
            names = archive_names(archive)
            if any(name.startswith(("com/mohamedrejeb/calf/", "jodd/")) for name in names):
                raise InvalidArtifact("A third-party dependency contains Calf/nativeCmpkit classes; no hidden baseline/candidate fallback")
        identities.add(identity)
        result.append((identity, path.resolve()))
    if not result:
        raise InvalidArtifact("Supply the exact third-party runtime dependency JARs, at least the supported Kotlin stdlib")
    return result


def class_inventory(directory: Path) -> dict[str, str]:
    files = sorted(directory.rglob("*"))
    if any(path.is_symlink() for path in files):
        raise InvalidArtifact("Compiled fixture output contains a symlink")
    actual = {path.relative_to(directory).as_posix(): sha256(path) for path in files if path.is_file()}
    expected = {"nativecmpkit/consumer/LegacyBinaryConsumer.class", "nativecmpkit/consumer/LegacyBinaryConsumer$1.class"}
    if set(actual) != expected:
        raise InvalidArtifact("Expected exactly the legacy fixture and its external interface implementation")
    return actual


def parse_execution(output: str) -> dict:
    result = load_json_bytes(output.strip().encode())
    if not isinstance(result, dict) or type(result.get("completed_cases")) is not int or type(result.get("assertions")) is not int:
        raise InvalidArtifact("Missing nonzero legacy linkage execution counts")
    if result["completed_cases"] != 6 or result["assertions"] != 31:
        raise InvalidArtifact("Unexpected/incomplete legacy linkage case/assertion counts")
    if result.get("kmp_abi_certified") is not False or result.get("native_ui_exercised") is not False:
        raise InvalidArtifact("Unexpected broadened compatibility/native behavior claim")
    return result


def run_checked(command: list[str], name: str, output: Path, runs: list[dict]) -> subprocess.CompletedProcess:
    started = datetime.now(timezone.utc).isoformat()
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired as exc:
        runs.append({"name": name, "command": command, "started_utc": started, "timed_out": True, "exit_code": None})
        raise InvalidArtifact("Bounded " + name + " timed out") from exc
    stdout, stderr = output / (name + ".stdout.txt"), output / (name + ".stderr.txt")
    stdout.write_text(result.stdout)
    stderr.write_text(result.stderr)
    runs.append({"name": name, "command": command, "started_utc": started, "exit_code": result.returncode,
                 "stdout_sha256": sha256(stdout), "stderr_sha256": sha256(stderr)})
    if result.returncode:
        raise InvalidArtifact(name + " failed; inspect its local bounded log and preserve failure evidence")
    return result


def execute(args, report: dict) -> None:
    identities = load_json_bytes((ROOT / "docs/migration/identity.json").read_bytes())
    expected = {item["new_artifact"] + "-desktop" for item in identities["modules"]}
    if len(expected) != 21:
        raise InvalidArtifact("Review the explicitly supported 21-publication consumer scope before changing it")
    baseline_inventory_path = args.baseline_evidence / "jar-inventory.json"
    baseline_api_path = args.baseline_evidence / "jvm-api.json"
    inventory = load_json_bytes(baseline_inventory_path.read_bytes())
    api = load_json_bytes(baseline_api_path.read_bytes())
    revision = inventory["source_revision"]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.baseline_root, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=args.baseline_root, text=True).strip()
    if head != revision or dirty or api["expected_source_revision"] != revision:
        raise InvalidArtifact("Baseline worktree/source-bound API inventory does not match the clean baseline revision")
    selected = [item for item in inventory["jars"] if item.get("published_module") is True]
    if len(selected) != 21 or {item["artifact"] for item in selected} != expected:
        raise InvalidArtifact("Missing/duplicate published baseline modules")
    baseline_files = verified_files(args.baseline_root.resolve(), selected)
    for item in selected:
        if item["sha256"] != api["artifacts"][item["artifact"]]["sha256"]:
            raise InvalidArtifact("Baseline JAR hash does not match independently captured API evidence")
    baseline_jars = [baseline_files[item["path"]] for item in sorted(selected, key=lambda item: item["artifact"])]
    if args.diagnostic_local_root is not None:
        candidate_jars, info, candidate_evidence_paths = diagnostic_candidates(
            args.diagnostic_local_root.resolve(), args.diagnostic_jar_inventory, expected)
        report.update(info)
    else:
        static = load_json_bytes(args.artifact_report.read_bytes())
        if (static.get("success") is not True or static.get("group") != GROUP or static.get("version") != args.version
                or "desktop" not in static.get("targets", []) or {item + "-desktop" for item in static.get("modules", [])} != expected):
            raise InvalidArtifact("A successful matching static inspection of all 21 desktop publication roots is required")
        candidate_files = verified_files(args.repository.resolve(), static["artifact_files"])
        candidate_jars = []
        for artifact in sorted(expected):
            relative = f"{GROUP.replace('.', '/')}/{artifact}/{args.version}/{artifact}-{args.version}.jar"
            if relative not in candidate_files:
                raise InvalidArtifact("Candidate desktop JAR was not in the verified staged set")
            candidate_jars.append(candidate_files[relative])
        candidate_evidence_paths = [args.artifact_report, *candidate_files.values()]
        report.update({"mode": "staged-artifacts", "maven_artifact_inspection_passed": True,
                       "candidate_version": args.version, "static_artifact_report_sha256": sha256(args.artifact_report)})
    dependencies = third_party_jars(args.dependency)
    report.update({"baseline_revision": revision, "baseline_api_sha256": sha256(baseline_api_path),
                   "baseline_inventory_sha256": sha256(baseline_inventory_path),
                   "baseline_jars": [file_record(path, artifact) for artifact, path in zip(sorted(expected), baseline_jars)],
                   "candidate_jars": [file_record(path, artifact) for artifact, path in zip(sorted(expected), candidate_jars)],
                   "third_party_dependencies": [file_record(path, identity) for identity, path in dependencies],
                   "fixture_source_sha256": sha256(SOURCE), "runner_sha256": sha256(Path(__file__)),
                   "artifact_checker_dependency_sha256": sha256(ROOT / "tests/consumer/verify_artifacts.py")})
    stable_paths = [*baseline_jars, *candidate_evidence_paths, *[path for _, path in dependencies],
                    baseline_inventory_path, baseline_api_path, SOURCE, Path(__file__), ROOT / "tests/consumer/verify_artifacts.py"]
    stable_files = {path: sha256(path) for path in stable_paths}
    classes = args.output / "classes"
    classes.mkdir()
    shared = [str(path) for _, path in dependencies]
    baseline_classpath = os.pathsep.join([str(path) for path in baseline_jars] + shared)
    candidate_classpath = os.pathsep.join([str(path) for path in candidate_jars] + shared)
    report["javac_version"] = subprocess.check_output([args.javac, "-version"], stderr=subprocess.STDOUT, text=True).strip()
    report["java_version"] = subprocess.check_output([args.java, "-version"], stderr=subprocess.STDOUT, text=True).strip()
    run_checked([args.javac, "--release", "17", "-encoding", "UTF-8", "-proc:none", "-classpath", baseline_classpath,
                 "-d", str(classes), str(SOURCE)], "compile-baseline", args.output, report["commands"])
    compiled = class_inventory(classes)
    report["compiled_classes"] = compiled
    for label, classpath in (("run-baseline", baseline_classpath), ("run-candidate", candidate_classpath)):
        ensure_unchanged(stable_files)
        if class_inventory(classes) != compiled:
            raise InvalidArtifact("The legacy compiled bytecode changed before runtime execution")
        result = run_checked([args.java, "-Xverify:all", "-ea", "-Djava.awt.headless=true", "-classpath",
                              str(classes) + os.pathsep + classpath, MAIN_CLASS], label, args.output, report["commands"])
        report[label] = parse_execution(result.stdout)
        if class_inventory(classes) != compiled:
            raise InvalidArtifact("The legacy compiled bytecode changed during runtime execution")
        ensure_unchanged(stable_files)
    report["unchanged_bytecode_on_both_runtimes"] = True
    report["recorded_inputs_unchanged_during_execution"] = True
    report["candidate_test_cases"] = 6
    report["candidate_assertions"] = 31
    report["success"] = True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-root", type=Path, required=True, help="Clean detached source-bound baseline output worktree")
    parser.add_argument("--baseline-evidence", type=Path, default=ROOT / "docs/development/evidence/abi-baseline-94d2492e")
    parser.add_argument("--repository", type=Path, help="The exact staged Maven repository already inspected")
    parser.add_argument("--artifact-report", type=Path, help="Successful static report; every recorded byte is rechecked")
    parser.add_argument("--version")
    parser.add_argument("--diagnostic-local-root", type=Path, help="Explicit non-distribution local-JAR diagnostic mode; never a staged consumer")
    parser.add_argument("--diagnostic-jar-inventory", type=Path, help="Receipt/source/hash-bound local build inventory; see binary/README.md")
    parser.add_argument("--dependency", action="append", required=True, help="public-identity=/absolute/third-party.jar, repeat; never Calf/nativeCmpkit")
    parser.add_argument("--javac", default="javac")
    parser.add_argument("--java", default="java")
    parser.add_argument("--output", type=Path, required=True, help="New/empty local evidence directory; never overwrites an old receipt")
    args = parser.parse_args()
    diagnostic = args.diagnostic_local_root is not None or args.diagnostic_jar_inventory is not None
    if diagnostic:
        if args.diagnostic_local_root is None or args.diagnostic_jar_inventory is None or any(
                arg is not None for arg in (args.repository, args.artifact_report, args.version)):
            parser.error("Diagnostic mode requires both diagnostic options and forbids staged-repository/report/version options")
    elif any(arg is None for arg in (args.repository, args.artifact_report, args.version)):
        parser.error("Staged-artifact mode requires --repository, --artifact-report and --version")
    report = {"schema_version": 1, "observed_utc": datetime.now(timezone.utc).isoformat(),
              "scope": ("Six Java/JVM old-binary/new-local-JAR diagnostics; no Maven/license/distribution/KMP/native/GUI verification"
                        if diagnostic else "Six Java/JVM source-bound old-binary/new-staged-artifact cases; no Kotlin/Native/GUI certification"),
              "mode": "local-jar-diagnostic" if diagnostic else "staged-artifacts", "distribution_verified": False,
              "maven_artifact_inspection_passed": False, "success": False, "binary_compatibility_certified": False,
              "release_readiness_certified": False, "commands": []}
    if args.output.is_symlink() or (args.output.exists() and (not args.output.is_dir() or any(args.output.iterdir()))):
        print(json.dumps({"success": False, "error": "Evidence output must be new/empty; no old output removed"}))
        return 2
    args.output.mkdir(parents=True, exist_ok=True)
    try:
        execute(args, report)
    except (ValueError, OSError, subprocess.SubprocessError, zipfile.BadZipFile, KeyError, TypeError, AttributeError) as exc:
        report["error"] = str(exc)
    (args.output / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: report[key] for key in ("success", "candidate_test_cases", "candidate_assertions", "error") if key in report}))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
