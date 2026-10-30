#!/usr/bin/env python3
"""Failure-safe library dependency-cache eligibility, never test/artifact reuse.

Only library jobs may use this fence. Consumer producer/child homes retain their
separate stronger success-only policy. A matching key and absent known candidate
group do not certify registry dependencies, checksums, native provenance, an OS
sandbox or release readiness. Never delete/repair unexpected cached data.
"""
from __future__ import annotations

import argparse
from itertools import islice
import json
import os
from pathlib import Path
import re

import dependency_cache_inputs as d
import library_tests as lt

ROOT = Path(__file__).resolve().parents[2]
GROUP = "io.github.apdelrahman1911.nativecmpkit"
MAX_CACHE_ROOT_ENTRIES = 256
MAX_OBSERVATION_BYTES = 8 * 1024**2


def validate_dependency_observation(root: Path, record: dict, selection_csv: str) -> str:
    """Recompute the exact configured recipe/key; never inspect test outcomes."""
    if (type(record) is not dict or type(record.get("schema_version")) is not int or
            record["schema_version"] != 1 or record.get("scope") != "libraries" or
            record.get("source_revision") != lt.git_revision(root) or
            any(record.get(name) is not False for name in (
                "compiled_or_test_results_reused", "ordinary_dependency_trust_certified", "release_readiness_certified"))):
        raise ValueError("Expected the exact non-certifying library dependency observation")
    selection = d.selection_contract(root, selection_csv)
    inputs = d.selected_inputs(root, "libraries")
    digest = d.fingerprint("libraries", inputs)
    if (record.get("selection_cache_key") != selection["cache_key"] or
            record.get("selected_modules") != selection["modules"] or record.get("inputs") != inputs or
            type(record.get("dependency_input_count")) is not int or record["dependency_input_count"] != len(inputs) or
            record.get("dependency_inputs_sha256") != digest):
        raise ValueError("Dependency recipe/selection changed; do not export under the old key")
    return digest


def observe_library_cache(home: Path) -> dict:
    """Bounded known candidate payload/descriptor fence; no cache-body export."""
    cache = lt.safe_path(home, ".gradle/caches/modules-2")
    paths = ["files-2.1/" + GROUP]
    if cache.exists():
        if not cache.is_dir():
            raise ValueError("Expected a directory for the fixed library dependency cache")
        entries = list(islice(cache.iterdir(), MAX_CACHE_ROOT_ENTRIES + 1))
        if len(entries) > MAX_CACHE_ROOT_ENTRIES:
            raise ValueError("Unbounded dependency cache root inventory")
        for entry in entries:
            if entry.name.startswith("metadata-"):
                if not re.fullmatch(r"metadata-[0-9]+(?:\.[0-9]+)+", entry.name):
                    raise ValueError("Unknown metadata layout; do not infer candidate absence")
                if not lt.safe_path(cache, entry.name).is_dir():
                    raise ValueError("Expected a real dependency metadata directory")
                paths.append(entry.name + "/descriptors/" + GROUP)
            elif entry.name == "files-2.1" and not lt.safe_path(cache, entry.name).is_dir():
                raise ValueError("Expected a real dependency payload directory")
    presence = {name: lt.safe_path(cache, name).exists() for name in sorted(paths)}
    return {"candidate_group": GROUP, "candidate_group_paths_present": presence,
            "candidate_group_absent": not any(presence.values()), "cached_data_removed_or_repaired": False,
            "ordinary_dependency_trust_certified": False, "release_readiness_certified": False,
            "scope": "Known library modules-2 candidate payload/descriptor absence only; no dependency trust or OS isolation"}


def unique_fields(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate dependency observation field")
        value[key] = item
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("restore", "save"), required=True)
    parser.add_argument("--selection", default="")
    args = parser.parse_args()
    observation = lt.safe_path(ROOT, "build/ci-runtime/library-dependencies.json")
    output = lt.safe_path(ROOT, f"build/ci-runtime/library-cache-{args.phase}.json")
    if output.exists():
        raise ValueError("Preserve the prior cache eligibility receipt; use one observation per phase")
    record = {"schema_version": 1, "phase": args.phase, "passed": False,
              "source_revision": lt.git_revision(ROOT), "observed_utc": lt.utc_now(),
              "compiled_or_test_results_reused": False, "packages_published": False,
              "ordinary_dependency_trust_certified": False, "release_readiness_certified": False}
    stage = "exact-dependency-observation"
    try:
        stat = observation.stat()
        if not observation.is_file() or stat.st_nlink != 1 or not 0 < stat.st_size <= MAX_OBSERVATION_BYTES:
            raise ValueError("Expected a bounded unshared dependency observation")
        with observation.open("rb") as stream:
            payload = stream.read(MAX_OBSERVATION_BYTES + 1)
        after = observation.stat()
        if len(payload) != stat.st_size or (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns) != (
                after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError("Dependency observation changed during its bounded read")
        dependencies = json.loads(payload, object_pairs_hook=unique_fields)
        record["dependency_inputs_sha256"] = validate_dependency_observation(ROOT, dependencies, args.selection)
        stage = "fixed-library-cache-home"
        home = Path.home()
        inherited = os.environ.get("GRADLE_USER_HOME")
        if inherited and Path(inherited).resolve() != (home / ".gradle").resolve():
            raise ValueError("Unexpected inherited library Gradle home; do not save another cache")
        stage = "known-candidate-group-absence"
        record["cache"] = observe_library_cache(home)
        if not record["cache"]["candidate_group_absent"]:
            raise ValueError("Candidate group is present; preserve data and forbid cache export")
        # Recheck the declaration contract after cache inspection. No job result
        # or previously passing XML can authorize exporting a changed recipe.
        stage = "exact-input-recheck"
        validate_dependency_observation(ROOT, dependencies, args.selection)
        record["passed"] = True
    except (ValueError, OSError) as failure:
        record["failure"] = {"stage": stage, "type": type(failure).__name__, "raw_error_or_cache_bodies_exported": False}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print("Library dependency cache eligibility: " + ("PASS (not dependency/test/release certification)" if record["passed"] else "FAIL (all data preserved)"))
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
