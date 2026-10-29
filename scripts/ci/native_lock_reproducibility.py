#!/usr/bin/env python3
"""Two genuinely empty-cache builds of both locked native crates on the actual host.

Reports only: no native payload upload, publication, GUI test or ABI certification.
Compare complete conservative Cargo graphs and recorded build metadata; record,
but do not invent, byte-for-byte reproducibility. Accepted UI suites are not run.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import platform as host
import re
import shutil
import subprocess
import sys
import tempfile

import library_tests as library

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "native"))
import artifacts as native

ROOT = Path(__file__).resolve().parents[2]
MODULES = ("calf-file-picker", "calf-share")
ATTEMPTS = 2
DEPENDENCY_PROBES = {"calf-file-picker": "raw-window-handle", "calf-share": "jni"}
RECIPE_INPUTS = (
    "scripts/ci/native_lock_reproducibility.py",
    "scripts/ci/test_native_lock_reproducibility.py",
    "scripts/ci/library_tests.py",
    ".github/workflows/build-native-libs.yml",
)


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def inputs(root: Path) -> dict[str, str]:
    result = {}
    for module in MODULES:
        result.update(native.expected_source_files(root, module))
    for path in RECIPE_INPUTS:
        result[path] = native.digest(native.safe_file(root, path))
    return dict(sorted(result.items()))


def plan(root: Path, platform: str) -> dict:
    if platform not in native.SUPPORTED_PLATFORMS:
        raise ValueError("Unsupported native builder; no target substitution")
    return {"schema_version": 1, "platform": platform,
            "rust_target": native.SUPPORTED_PLATFORMS[platform]["rustTarget"],
            "rust_toolchain": native.toolchain(root), "modules": list(MODULES),
            "attempts_per_module": ATTEMPTS, "cargo_profile": "release",
            "cargo_build_jobs": 2, "cargo_locked": True,
            "cargo_home_and_target_begin_empty_each_attempt": True,
            "accepted_native_UI_suites_replayed": False,
            "native_runtime_test_count": 0,
            "scope": "Clean-cache build/locked graph repeatability only; not JNI, GUI, minimum OS, provenance attestation or release"}


def lock_refusal(exit_code: int, stderr: str) -> bool:
    # Cargo 1.98 uses the first form; the second retains the established diagnostic.
    # Never treat an arbitrary network/manifest/compiler failure as lock enforcement.
    return exit_code == 101 and ("--locked was passed" in stderr and
            ("cannot update the lock file" in stderr or "needs to be updated" in stderr))


def remove_root_dependency(text: str, module: str) -> str:
    dependency = DEPENDENCY_PROBES[module]
    lines = text.splitlines(keepends=True)
    matches = [line for line in lines if re.fullmatch(re.escape(dependency) + r"\s*=.*\r?\n?", line)]
    if len(matches) != 1:
        raise ValueError("The finite root-dependency fixture no longer matches its owning manifest")
    return "".join(line for line in lines if line != matches[0])


def fixed_build_metadata(manifest: dict) -> dict:
    # PE timestamps/linker nondeterminism are not proof of changed resolution.
    # Hash and size comparisons remain explicit separate observations below.
    return {key: value for key, value in manifest.items() if key not in {"sha256", "size"}}


def compare_attempts(first: dict, second: dict) -> dict:
    if first["graph"] != second["graph"]:
        raise ValueError("Empty-cache attempts resolved different locked package graphs/features")
    if fixed_build_metadata(first["manifest"]) != fixed_build_metadata(second["manifest"]):
        raise ValueError("Empty-cache attempts recorded different source/compiler/build metadata")
    return {"locked_graphs_and_features_identical": True,
            "source_compiler_build_metadata_identical": True,
            "native_binary_bytes_identical": first["manifest"]["sha256"] == second["manifest"]["sha256"],
            "native_binary_sizes_identical": first["manifest"]["size"] == second["manifest"]["size"]}


def feature_graph(raw: dict) -> list[dict]:
    id_map = {package["id"]: package["name"] + "@" + package["version"] for package in raw["packages"]}
    if len(id_map) != len(raw["packages"]) or len(set(id_map.values())) != len(id_map):
        raise ValueError("Ambiguous Cargo feature-graph identities")
    nodes = raw["resolve"]["nodes"]
    result = []
    for node in nodes:
        features = node["features"]
        if (not isinstance(features, list) or any(not isinstance(f, str) for f in features)
                or len(set(features)) != len(features)):
            raise ValueError("Invalid actual Cargo feature graph")
        result.append({"id": id_map[node["id"]], "features": sorted(features)})
    if len({item["id"] for item in result}) != len(result):
        raise ValueError("Duplicate actual Cargo feature-graph node")
    return sorted(result, key=lambda item: item["id"])


def capture_metadata(root: Path, module: str, prefix: list[str], env: dict[str, str], private: Path,
                     *, offline: bool = False) -> dict:
    # Fetch the entire unfiltered lock union, not just the current host's build subset.
    # stdout has native cache paths and stays private; only the existing sanitizer
    # and the finite feature graph are exported. No build script/test is run here.
    raw_path = private / "metadata.private.json"
    with raw_path.open("wb") as out, (private / "metadata.private.log").open("wb") as err:
        completed = subprocess.run([*prefix, "cargo", "metadata", "--locked", "--format-version", "1",
                                    *(["--offline"] if offline else [])],
                                   cwd=root / module / "native", env=env, stdout=out, stderr=err, timeout=180)
    if completed.returncode:
        raise ValueError("Complete locked Cargo metadata acquisition failed")
    if raw_path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("Cargo metadata exceeds bounded size")
    features = feature_graph(json.loads(raw_path.read_bytes()))
    normalized = private / "normalized-metadata.json"
    with (private / "normalize.private.log").open("wb") as log:
        completed = subprocess.run([sys.executable, str(ROOT / "scripts/native/artifacts.py"), "metadata",
                                   "--root", str(root), "--module", module, "--output", str(normalized)],
                                  cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=180)
    if completed.returncode:
        raise ValueError("Complete locked Cargo metadata normalization failed")
    graph = json.loads(normalized.read_bytes())
    if {node["id"] for node in graph["resolve"]} != {node["id"] for node in features}:
        raise ValueError("Normalized Cargo graph/features disagree")
    graph["resolve_features"] = features
    return graph


def dependency_refusal(root: Path, module: str, prefix: list[str], env: dict[str, str], private: Path,
                       expected_graph: dict) -> dict:
    fixture = private / "fixture"
    crate = fixture / module / "native"
    source = root / module / "native"
    def ignored(directory: str, names: list[str]) -> set[str]:
        # A nested src/target is legitimate source, not the crate's build cache.
        return set(names) & ({"target", ".git"} if Path(directory) == source else {".git"})
    shutil.copytree(source, crate, ignore=ignored)
    shutil.copyfile(root / "rust-toolchain.toml", fixture / "rust-toolchain.toml")
    manifest = crate / "Cargo.toml"
    original = manifest.read_bytes()
    lock = (crate / "Cargo.lock").read_bytes()
    # A populated-cache, unchanged offline control proves the negative is not
    # simply an empty cache, unavailable registry or invalid source fixture.
    control = capture_metadata(fixture, module, prefix, env, private, offline=True)
    if control != expected_graph:
        raise ValueError("Unchanged copied-source Cargo control differs from the actual locked graph")
    manifest.write_text(remove_root_dependency(original.decode("utf-8"), module), encoding="utf-8")
    rejected = subprocess.run([*prefix, "cargo", "metadata", "--locked", "--offline", "--format-version", "1"],
                              cwd=crate, env=env, capture_output=True, timeout=60)
    (private / "lock-refusal.private.log").write_bytes(rejected.stderr)
    refused = lock_refusal(rejected.returncode, rejected.stderr.decode("utf-8", errors="replace"))
    if not refused or (crate / "Cargo.lock").read_bytes() != lock:
        raise ValueError("Changed dependency did not prove the exact no-update --locked refusal")
    manifest.write_bytes(original)
    restored = capture_metadata(fixture, module, prefix, env, private, offline=True)
    if restored != expected_graph or (crate / "Cargo.lock").read_bytes() != lock:
        raise ValueError("Restored owning manifest did not recover the original locked graph")
    return {"unchanged_control_passed": True, "root_dependency_removed": DEPENDENCY_PROBES[module],
            "offline_changed_dependency_exit_code": rejected.returncode,
            "failure_reason": "cargo-locked-refuses-required-lock-update", "lock_bytes_unchanged": True,
            "restored_control_passed": True, "production_manifest_never_modified": True}


def run(root: Path, platform: str, relative: str, reserve_mib: int) -> dict:
    if platform != native.current_platform():
        raise ValueError("Actual host differs from selected native builder; no cross-target substitution")
    output = library.safe_path(root, relative)
    allowed = root / "build/ci-verification"
    if output == allowed or not output.is_relative_to(allowed) or output.exists():
        raise ValueError("Use a new dedicated verification output; never overwrite old receipts/source/caches")
    revision, dirty = native.git_provenance(root)
    if dirty:
        raise ValueError("Native clean-cache verification requires an immutable clean checkout")
    before = inputs(root)
    recipe = plan(root, platform)
    env = native._build_environment()
    prefix = ["rustup", "run", native.toolchain(root)]
    output.mkdir(parents=True)
    write(output / "plan.json", recipe)
    write(output / "inputs-before.json", before)
    record = {"schema_version": 1, "started_at_utc": utc(), "source_revision": revision,
              "source_tree_dirty": False, "platform": platform, "plan": recipe, "modules": [],
              "host": {"system": host.system(), "architecture": host.machine(), "python": host.python_version()},
              "passed": False, "native_runtime_tests_executed": 0,
              "packages_releases_deployments_or_Pages_created": False, "release_readiness_certified": False}
    stage = "prepare"
    try:
        for module in MODULES:
            attempts = []
            for index in range(ATTEMPTS):
                print(f"Native locked-cache verification: {platform} {module} attempt {index + 1}/2", flush=True)
                with tempfile.TemporaryDirectory(prefix=".private-native-lock-", dir=output) as tmp:
                    private = Path(tmp)
                    home, target = private / "cargo-home", private / "target"
                    home.mkdir(); target.mkdir()
                    if list(home.iterdir()) or list(target.iterdir()):
                        raise ValueError("The cache/build target was not genuinely empty before invocation")
                    attempt_env = {**env, "CARGO_HOME": str(home), "CARGO_BUILD_JOBS": "2"}
                    resources = private / "resources"
                    args = ["scripts/native/artifacts.py", "build", "--module", module, "--platform", platform,
                            "--output", str(resources.relative_to(root)), "--cargo-target-dir", str(target.relative_to(root)),
                            "--version", "0.1.0-SNAPSHOT"]
                    stage = "empty-cache-native-build"
                    execution = library.execute(root, [sys.executable, *args],
                                                output / f"{module}-attempt{index + 1}.private.log",
                                                1200, reserve_mib, env=attempt_env)
                    write(output / f"{module}-attempt{index + 1}-execution.json",
                          {"interpreter": "same-python-as-controller", "arguments": args, **execution})
                    if execution["exit_code"] != 0:
                        raise ValueError("Native empty-cache build failed; no successful attempt is inferred")
                    try:
                        stage = "actual-native-manifest-validation"
                        manifest, = native.validate_bundle(root, module, resources, [platform], require_clean=True,
                                                           expected_revision=revision, expected_version="0.1.0-SNAPSHOT")
                        stage = "complete-locked-metadata"
                        graph = capture_metadata(root, module, prefix, attempt_env, private)
                        stage = "changed-dependency-refusal"
                        refusal = dependency_refusal(root, module, prefix, attempt_env, private, graph) if index == 0 else None
                    except BaseException:
                        diagnostics = output / ".private-diagnostics" / f"{module}-attempt{index + 1}"
                        diagnostics.mkdir(parents=True, exist_ok=True)
                        for log in private.glob("*.private.log"):
                            shutil.copyfile(log, diagnostics / log.name)
                        raise
                    attempt = {"attempt": index + 1, "cargo_home_started_empty": True, "target_started_empty": True,
                               "execution": execution, "manifest": manifest, "graph": graph,
                               "changed_dependency_probe": refusal}
                    write(output / f"{module}-attempt{index + 1}.json", attempt)
                    attempts.append(attempt)
                stage = "owned-cleanup-and-source-hold"
                if private.exists():
                    raise ValueError("Owned private caches/binary/source fixtures were not removed")
                if inputs(root) != before or native.git_provenance(root) != (revision, False):
                    raise ValueError("Source inputs/revision changed while native verification was running")
            stage = "compare-two-empty-cache-attempts"
            record["modules"].append({"module": module, "completed_empty_cache_builds": 2,
                                       "comparison": compare_attempts(*attempts),
                                       "exact_locked_dependency_refusal_verified": True,
                                       "owned_private_cache_and_binary_cleanup_verified": True})
        record["passed"] = True
    except (ValueError, OSError, subprocess.SubprocessError, KeyError, TypeError) as failure:
        # Finite stage/type only; arbitrary compiler/registry messages stay private.
        record["failure_type"] = type(failure).__name__
        record["failure_stage"] = stage
        record["failed_module"] = module
        record["failed_attempt"] = index + 1
    finally:
        try:
            after = inputs(root)
            final_identity = native.git_provenance(root)
        except (ValueError, OSError, subprocess.SubprocessError) as failure:
            after, final_identity = None, None
            record["final_source_capture_failure_type"] = type(failure).__name__
        write(output / "inputs-after.json", after)
        record.update(finished_at_utc=utc(), source_revision_after=final_identity[0] if final_identity else None,
                      input_hashes_before_after_match=before == after)
        if not record["input_hashes_before_after_match"] or final_identity != (revision, False):
            record["passed"] = False
        write(output / "receipt.json", record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True, choices=sorted(native.SUPPORTED_PLATFORMS))
    parser.add_argument("--output", required=True)
    parser.add_argument("--reserve-mib", type=int, default=8192)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    if args.reserve_mib < 8192:
        parser.error("Keep the mandated8GiB disk reserve")
    if args.plan:
        print(json.dumps(plan(ROOT, args.platform), indent=2, sort_keys=True))
        return 0
    result = run(ROOT, args.platform, args.output, args.reserve_mib)
    print(json.dumps({key: result[key] for key in ("platform", "passed", "modules", "native_runtime_tests_executed")}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
