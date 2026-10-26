#!/usr/bin/env python3
"""Validate the offline development ledgers and render a hash-bound status index.

Default: validate only. --write regenerates docs/development/status.{json,md}.
--check is read-only and returns 2 for a missing/stale/edited generated index.
Invalid input returns 1. No network, Gradle, Git, issue mutation or status inference.

This checks structure and references, NOT whether a claimed test passed. In
particular, a structurally valid `verified` record still requires human review.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_FINDINGS = 164
BASELINE = "af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6"
REPOSITORY = "Apdelrahman1911/nativeCmpkit"
PRIORITIES = ("Critical", "High", "Medium", "Low")
STATUSES = ("implemented", "partially-verified", "verified", "unresolved", "not-applicable")
EVIDENCE_STATUSES = ("confirmed-source", "confirmed-test", "risk", "unverified", "improvement")
EFFORTS = ("S", "M", "L", "XL")
ID_PATTERN = re.compile(r"[A-Z][A-Z0-9_]*-[0-9]{3}\Z")
FINDING_DIR = "docs/audit/findings"
LEDGER_DIR = "docs/development/resolutions"
ROADMAP = "docs/roadmap/backlog.json"
ISSUE_MAP = "docs/migration/issue-map.json"
OUTPUT_JSON = "docs/development/status.json"
OUTPUT_MD = "docs/development/status.md"
GENERATOR = "scripts/development/validate_resolutions.py"


class ValidationError(ValueError):
    """Malformed/inconsistent input; no generated output should be written."""


class StaleSnapshotError(ValidationError):
    """Input changed while it was being read, validated or rendered."""


def require(condition: bool, where: str, message: str) -> None:
    if not condition:
        raise ValidationError(f"{where}: {message}")


def string(value: Any, where: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), where, "expected a nonempty string")
    return value


def strings(value: Any, where: str, *, nonempty: bool = False) -> list[str]:
    require(isinstance(value, list), where, "expected an array of strings")
    require(not nonempty or bool(value), where, "expected a nonempty array")
    for index, entry in enumerate(value):
        string(entry, f"{where}[{index}]")
    return value


def object_fields(value: Any, fields: tuple[str, ...], where: str) -> dict[str, Any]:
    require(isinstance(value, dict), where, "expected an object")
    missing = sorted(set(fields) - value.keys())
    require(not missing, where, "missing required fields: " + ", ".join(missing))
    return value


def choice(value: Any, allowed: tuple[str, ...], where: str) -> str:
    string(value, where)
    require(value in allowed, where, "expected one of " + ", ".join(allowed))
    return value


def integer(value: Any, where: str, *, minimum: int = 0) -> int:
    # bool is an int subclass in Python, but is not an issue number/test count.
    require(type(value) is int and value >= minimum, where, f"expected an integer >= {minimum}")
    return value


def finding_id(value: Any, where: str) -> str:
    string(value, where)
    require(ID_PATTERN.fullmatch(value) is not None, where, "invalid stable finding ID")
    return value


def reference_path(value: Any, where: str) -> str:
    string(value, where)
    path = PurePosixPath(value)
    require(not path.is_absolute() and ".." not in path.parts and "\\" not in value
            and "\x00" not in value and ":" not in value,
            where, "expected a repository-relative POSIX path without traversal")
    # Historical/deleted source locations are legal; existence is not inferred.
    return value


def issue_url(value: Any, number: int, where: str) -> str:
    expected = f"https://github.com/{REPOSITORY}/issues/{number}"
    require(value == expected, where, f"expected the mapped repository/issue URL {expected}")
    return value


def dependency_list(value: Any, where: str) -> list[str]:
    strings(value, where)
    for index, item in enumerate(value):
        finding_id(item, f"{where}[{index}]")
    require(len(set(value)) == len(value), where, "duplicate dependency IDs")
    return value


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise ValidationError(f"non-JSON numeric constant {value}")


def finite_float(value: str) -> float:
    number = float(value)
    require(math.isfinite(number), "JSON number", "numeric value exceeds finite float range")
    return number


def decode_json(raw: bytes, where: str) -> Any:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                           parse_constant=reject_constant, parse_float=finite_float)
        # Escaped lone surrogates can parse as JSON but cannot be rendered to
        # UTF-8 JSON/Markdown. Reject them even in preserved extension fields.
        canonical(value)
        return value
    except (UnicodeError, ValueError) as error:
        raise ValidationError(f"{where}: invalid JSON: {error}") from error


def inside_root(root: Path, relative: str) -> Path:
    path = root / relative
    try:
        resolved = path.resolve()
    except (OSError, RuntimeError) as error:
        raise ValidationError(f"{relative}: cannot resolve input/output path: {error}") from error
    require(resolved.is_relative_to(root), relative, "symlink/path escapes repository root")
    return path


def discover(root: Path) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for name, directory in (("findings", FINDING_DIR), ("ledgers", LEDGER_DIR)):
        folder = inside_root(root, directory)
        require(folder.is_dir(), directory, "missing input directory")
        files = sorted(str(path.relative_to(root)) for path in folder.glob("*.json"))
        require(bool(files), directory, "no JSON input files")
        for relative in files:
            require(inside_root(root, relative).is_file(), relative, "expected a regular JSON file")
        groups[name] = files
    groups["metadata"] = [ROADMAP, ISSUE_MAP]
    for relative in groups["metadata"]:
        require(inside_root(root, relative).is_file(), relative, "missing metadata input")
    return groups


def fingerprint(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def read_inputs(root: Path) -> tuple[dict[str, list[str]], dict[str, bytes]]:
    groups = discover(root)
    files = sorted(path for paths in groups.values() for path in paths)
    try:
        return groups, {path: inside_root(root, path).read_bytes() for path in files}
    except OSError as error:
        raise ValidationError(f"could not read inputs: {error}") from error


def assert_inputs_current(root: Path, model: dict[str, Any]) -> None:
    try:
        groups, raw = read_inputs(root)
        generator_hash = fingerprint(Path(__file__).read_bytes())
    except (ValidationError, OSError) as error:
        raise StaleSnapshotError(f"input set changed during validation: {error}") from error
    hashes = {path: fingerprint(value) for path, value in raw.items()}
    if groups != model["input_sets"] or hashes != model["input_sha256"]:
        raise StaleSnapshotError("inputs changed during validation; freeze ledgers and rerun")
    if generator_hash != model["generator"]["sha256"]:
        raise StaleSnapshotError("generator changed during validation; freeze tooling and rerun")


def validate_baselines(raw: dict[str, bytes], paths: list[str]) -> tuple[dict[str, Any], dict[str, str]]:
    records: dict[str, Any] = {}
    sources: dict[str, str] = {}
    fields = ("id", "title", "priority", "status", "modules", "locations", "root_cause",
              "impact", "recommendation", "risks", "required_tests", "evidence", "upstream_refs",
              "effort", "dependencies")
    for path in paths:
        rows = decode_json(raw[path], path)
        require(isinstance(rows, list), path, "expected a finding array")
        for index, row in enumerate(rows):
            where = f"{path}[{index}]"
            object_fields(row, fields, where)
            fid = finding_id(row["id"], where + ".id")
            require(fid not in records, where, f"duplicate baseline ID {fid}")
            for key in ("title", "root_cause", "impact", "recommendation", "risks"):
                string(row[key], where + "." + key)
            choice(row["priority"], PRIORITIES, where + ".priority")
            choice(row["status"], EVIDENCE_STATUSES, where + ".status")
            choice(row["effort"], EFFORTS, where + ".effort")
            for key in ("modules", "required_tests", "evidence", "upstream_refs"):
                strings(row[key], where + "." + key, nonempty=key in ("modules", "required_tests"))
            dependency_list(row["dependencies"], where + ".dependencies")
            require(isinstance(row["locations"], list) and bool(row["locations"]), where + ".locations", "expected nonempty locations")
            for i, location in enumerate(row["locations"]):
                here = f"{where}.locations[{i}]"
                object_fields(location, ("path", "lines", "symbol"), here)
                reference_path(location["path"], here + ".path")
                string(location["lines"], here + ".lines")
                string(location["symbol"], here + ".symbol")
            records[fid], sources[fid] = row, path
    for fid, row in records.items():
        require(fid not in row["dependencies"], fid, "self dependency")
        missing = sorted(set(row["dependencies"]) - records.keys())
        require(not missing, fid, "unknown dependencies: " + ", ".join(missing))
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(fid: str) -> None:
        require(fid not in visiting, fid, "dependency cycle")
        if fid in visited:
            return
        visiting.add(fid)
        for dep in records[fid]["dependencies"]:
            visit(dep)
        visiting.remove(fid)
        visited.add(fid)

    for fid in records:
        visit(fid)
    return records, sources


def validate_ledgers(raw: dict[str, bytes], paths: list[str], baselines: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    records: dict[str, Any] = {}
    sources: dict[str, str] = {}
    fields = ("id", "status", "changes", "affected_paths", "tests", "remaining", "compatibility")
    for path in paths:
        rows = decode_json(raw[path], path)
        require(isinstance(rows, list), path, "expected a resolution array")
        for index, row in enumerate(rows):
            where = f"{path}[{index}]"
            object_fields(row, fields, where)
            fid = finding_id(row["id"], where + ".id")
            require(fid not in records, where, f"duplicate resolution ID {fid}")
            require(fid in baselines, where, f"unknown resolution ID {fid}")
            choice(row["status"], STATUSES, where + ".status")
            for key in ("changes", "affected_paths", "remaining"):
                strings(row[key], where + "." + key, nonempty=key == "affected_paths")
            for i, affected in enumerate(row["affected_paths"]):
                reference_path(affected, f"{where}.affected_paths[{i}]")
            if isinstance(row["compatibility"], list):
                strings(row["compatibility"], where + ".compatibility", nonempty=True)
            else:
                string(row["compatibility"], where + ".compatibility")
            for key in ("title", "priority", "verification_scope", "original_finding", "required_tests_review"):
                if key in row:
                    string(row[key], where + "." + key)
            for key in ("title", "priority"):
                if key in row:
                    require(row[key] == baselines[fid][key], where + "." + key, "differs from immutable baseline")
            require(isinstance(row["tests"], list), where + ".tests", "expected a test-record array")
            has_evidence = False
            for i, test in enumerate(row["tests"]):
                here = f"{where}.tests[{i}]"
                object_fields(test, ("command", "result", "evidence"), here)
                string(test["command"], here + ".command")
                string(test["result"], here + ".result")
                evidence = test["evidence"]
                if isinstance(evidence, list):
                    strings(evidence, here + ".evidence")
                else:
                    string(evidence, here + ".evidence")
                has_evidence = has_evidence or bool(evidence)
                for key in ("test_count", "report_count", "failures", "errors", "skipped"):
                    if key in test:
                        integer(test[key], here + "." + key)
                for key in ("scoped_tasks", "applicable_passed_cases", "key_passed_cases"):
                    if key in test:
                        strings(test[key], here + "." + key)
                for key in ("scope", "input_state", "checkpoint", "prior_failure_retained", "tracker_test_sha256"):
                    if key in test:
                        string(test[key], here + "." + key)
            if row["status"] == "verified":
                require(not row["remaining"], where, "verified records must have no remaining checks")
                require(has_evidence, where, "verified records require explicit nonempty tests[].evidence")
            # Test prose, evidence paths and historical issue state never promote status.
            records[fid], sources[fid] = row, path
    missing = sorted(baselines.keys() - records.keys())
    require(not missing, LEDGER_DIR, "missing resolution IDs: " + ", ".join(missing))
    return records, sources


def validate_mapping(value: Any, baselines: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    object_fields(value, ("schema_version", "repository", "baseline", "complete", "items"), ISSUE_MAP)
    require(type(value["schema_version"]) is int and value["schema_version"] == 1, ISSUE_MAP, "unsupported schema_version")
    require(value["repository"] == REPOSITORY, ISSUE_MAP, "unexpected repository")
    require(value["baseline"] == BASELINE, ISSUE_MAP, "unexpected baseline revision")
    require(value["complete"] is True, ISSUE_MAP, "mapping is not recorded complete")
    require(isinstance(value["items"], list), ISSUE_MAP + ".items", "expected an array")
    by_key: dict[str, Any] = {}
    by_finding: dict[str, Any] = {}
    numbers: set[int] = set()
    for index, item in enumerate(value["items"]):
        where = f"{ISSUE_MAP}.items[{index}]"
        object_fields(item, ("key", "finding_ids", "number", "url", "title", "state"), where)
        key = string(item["key"], where + ".key")
        require(key not in by_key, where, "duplicate issue mapping key")
        number = integer(item["number"], where + ".number", minimum=1)
        require(number not in numbers, where, "duplicate issue number")
        issue_url(item["url"], number, where + ".url")
        string(item["title"], where + ".title")
        choice(item["state"], ("open", "closed"), where + ".state")
        if "actual_state" in item:
            choice(item["actual_state"], ("open", "closed"), where + ".actual_state")
        fids = dependency_list(item["finding_ids"], where + ".finding_ids")
        if key.startswith("audit:"):
            require(fids == [key.removeprefix("audit:")], where, "audit key must map its one matching finding ID")
        else:
            require(key.startswith("upstream-topic:") and not fids, where, "expected an audit mapping or separate upstream topic")
        for fid in fids:
            require(fid in baselines, where, f"unknown mapped finding ID {fid}")
            require(fid not in by_finding, where, f"finding mapped more than once: {fid}")
            by_finding[fid] = item
        by_key[key] = item
        numbers.add(number)
    missing = sorted(baselines.keys() - by_finding.keys())
    require(not missing, ISSUE_MAP, "unmapped finding IDs: " + ", ".join(missing))
    return by_key, by_finding


def validate_roadmap(value: Any, baselines: dict[str, Any], mapping: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    object_fields(value, ("baseline", "ordering", "phases", "items"), ROADMAP)
    require(value["baseline"] == BASELINE, ROADMAP, "unexpected baseline revision")
    string(value["ordering"], ROADMAP + ".ordering")
    require(isinstance(value["phases"], dict) and bool(value["phases"]), ROADMAP + ".phases", "expected phase labels")
    for phase, label in value["phases"].items():
        require(phase.isdigit(), ROADMAP + ".phases", "phase keys must be nonnegative integers as strings")
        string(label, ROADMAP + f".phases[{phase}]")
    require(isinstance(value["items"], list), ROADMAP + ".items", "expected an array")
    records: dict[str, Any] = {}
    topics: list[dict[str, Any]] = []
    keys: set[str] = set()
    orders: set[int] = set()
    fields = ("order", "key", "title", "phase", "priority", "evidence_status", "effort", "dependencies",
              "workstream", "state", "issue_url", "required_tests")
    for index, item in enumerate(value["items"]):
        where = f"{ROADMAP}.items[{index}]"
        object_fields(item, fields, where)
        key = string(item["key"], where + ".key")
        order = integer(item["order"], where + ".order", minimum=1)
        require(key not in keys, where, "duplicate roadmap key")
        require(order not in orders, where, "duplicate roadmap order")
        require(key in mapping, where, "roadmap key has no existing issue mapping")
        issue_url(item["issue_url"], mapping[key]["number"], where + ".issue_url")
        phase = integer(item["phase"], where + ".phase")
        require(str(phase) in value["phases"], where + ".phase", "undefined roadmap phase")
        for field in ("title", "workstream"):
            string(item[field], where + "." + field)
        choice(item["priority"], PRIORITIES, where + ".priority")
        choice(item["evidence_status"], EVIDENCE_STATUSES, where + ".evidence_status")
        # Historical topics deliberately have no finding/module assignment yet.
        # Their archived estimate is `triage-first`, not an audit S/M/L/XL value.
        efforts = EFFORTS if "finding" in item else (*EFFORTS, "triage-first")
        choice(item["effort"], efforts, where + ".effort")
        choice(item["state"], ("open", "closed"), where + ".state")
        dependency_list(item["dependencies"], where + ".dependencies")
        if "modules" in item:
            strings(item["modules"], where + ".modules", nonempty=True)
        strings(item["required_tests"], where + ".required_tests", nonempty=True)
        if "finding" in item:
            object_fields(item, ("modules",), where)
            fid = finding_id(item["finding"], where + ".finding")
            require(fid in baselines, where, f"unknown roadmap finding {fid}")
            require(fid not in records, where, f"duplicate roadmap finding {fid}")
            require(mapping[key]["finding_ids"] == [fid], where, "roadmap finding/mapping mismatch")
            baseline = baselines[fid]
            for field in ("title", "priority", "effort", "dependencies", "modules", "required_tests"):
                require(item[field] == baseline[field], where + "." + field, "differs from immutable baseline finding")
            require(item["evidence_status"] == baseline["status"], where + ".evidence_status", "differs from baseline")
            records[fid] = item
        else:
            require(not mapping[key]["finding_ids"], where, "missing roadmap finding ID for audit item")
            require(set(item["dependencies"]) <= baselines.keys(), where, "unknown topic dependencies")
            topics.append(item)
        keys.add(key)
        orders.add(order)
    require(keys == mapping.keys(), ROADMAP, "roadmap and issue mapping key coverage differ")
    missing = sorted(baselines.keys() - records.keys())
    require(not missing, ROADMAP, "missing roadmap findings: " + ", ".join(missing))
    for fid, item in records.items():
        for dep in item["dependencies"]:
            require(records[dep]["order"] < item["order"], fid, f"dependency {dep} follows its dependent in original roadmap order")
    return records, sorted(topics, key=lambda item: item["order"])


def build_snapshot(root: Path, *, expected_count: int = EXPECTED_FINDINGS) -> dict[str, Any]:
    """Read one stable input set. The smaller count override is for fixture tests only."""
    root = root.resolve()
    groups, raw = read_inputs(root)
    baselines, baseline_sources = validate_baselines(raw, groups["findings"])
    require(len(baselines) == expected_count, FINDING_DIR, f"expected exactly {expected_count} unique baseline IDs, found {len(baselines)}")
    resolutions, ledger_sources = validate_ledgers(raw, groups["ledgers"], baselines)
    mapping_doc = decode_json(raw[ISSUE_MAP], ISSUE_MAP)
    mapping, issue_for = validate_mapping(mapping_doc, baselines)
    roadmap_doc = decode_json(raw[ROADMAP], ROADMAP)
    roadmap, topics = validate_roadmap(roadmap_doc, baselines, mapping)
    hashes = {path: fingerprint(value) for path, value in raw.items()}
    entries = []
    for fid in sorted(baselines, key=lambda item: roadmap[item]["order"]):
        baseline, current, plan, issue = baselines[fid], resolutions[fid], roadmap[fid], issue_for[fid]
        entries.append({
            "id": fid, "title": baseline["title"], "priority": baseline["priority"],
            "original_order": plan["order"], "original_phase": plan["phase"],
            "original_phase_label": roadmap_doc["phases"][str(plan["phase"])],
            "original_effort": baseline["effort"], "workstream": plan["workstream"],
            "original_evidence_status": baseline["status"], "modules": baseline["modules"],
            "baseline_file": baseline_sources[fid], "baseline_locations": baseline["locations"],
            "original_required_tests": baseline["required_tests"],
            "original_dependencies": baseline["dependencies"],
            "dependencies": [{"id": dep, "original_order": roadmap[dep]["order"],
                              "reported_status": resolutions[dep]["status"],
                              "issue_url": issue_for[dep]["url"]} for dep in baseline["dependencies"]],
            "issue": {"number": issue["number"], "url": issue["url"], "mapping_key": issue["key"],
                      "historical_mapping_state": issue.get("actual_state", issue["state"])},
            "reported_status": current["status"], "owner_ledger": ledger_sources[fid],
            "owner_record_sha256": fingerprint(canonical(current)), "owner_record": current,
            "closure_or_release_authorized_by_index": False,
        })
    counted = Counter(row["status"] for row in resolutions.values())
    model = {
        "schema_version": 1, "kind": "offline-development-status-index",
        "generator": {"path": GENERATOR, "sha256": fingerprint(Path(__file__).read_bytes())},
        "baseline_revision": BASELINE, "repository": REPOSITORY,
        "scope": "Structural validation and content-addressed snapshot only. No test execution/evidence certification, status promotion, live issue query, automatic closure or release authorization.",
        "snapshot_freshness": "Run validate_resolutions.py --check. Any input-byte/input-set/generator/output difference makes the index stale; this file cannot update itself when ledgers change.",
        "freshness_scope": "Only the listed metadata/ledger inputs and generator are hashed. Referenced source, test, log/XML and evidence files are not rehashed or certified; they can change while this ledger index remains CURRENT.",
        "input_sets": groups, "input_sha256": hashes,
        "input_fingerprint": fingerprint(canonical(hashes)),
        "counts": {"baseline_findings": len(baselines), "unique_resolution_ids": len(resolutions),
                   "mapped_findings": len(issue_for), "imported_topics_without_finding_ids": len(topics),
                   "reported_statuses": {status: counted[status] for status in STATUSES},
                   "automatic_closures": 0, "status_promotions": 0},
        "original_roadmap_ordering": roadmap_doc["ordering"],
        "original_phase_labels": roadmap_doc["phases"],
        "requirements_policy": "original_required_tests are copied verbatim from the immutable baseline and checked equal to the original roadmap. Owner remaining/tests are retained separately; no string matching infers which original requirement passed.",
        "verified_schema_policy": "A reported verified status requires explicit nonempty tests[].evidence and an empty remaining array. Evidence strings/prose and test outcomes are not independently validated; human review is still mandatory.",
        "items": entries,
        "imported_topics_without_resolution_ids": topics,
    }
    assert_inputs_current(root, model)
    return model


def md_text(value: str) -> str:
    """Render record text inertly, including pipes/HTML/Markdown control characters."""
    escaped = html.escape(value, quote=False).replace("\\", "\\\\")
    escaped = re.sub(r"([`*_[\]{}|])", r"\\\1", escaped)
    return escaped.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def doc_link(path: str) -> str:
    prefix = "docs/development/"
    if path.startswith(prefix):
        relative = path[len(prefix):]
    elif path.startswith("docs/"):
        # MkDocs resolves links inside docs_dir before repository-link rewriting.
        # Leaving docs_dir and re-entering via ../../docs is not a site-local link.
        relative = "../" + path[len("docs/"):]
    else:
        relative = "../../" + path
    return f"[{md_text(path)}]({quote(relative, safe='/')})"


def render_markdown(model: dict[str, Any]) -> bytes:
    counts = model["counts"]
    lines = [
        "# Development status and dependency-ordered roadmap", "",
        "Generated by `scripts/development/validate_resolutions.py`; do not edit these index files manually.", "",
        "**This is a ledger snapshot, not a new test result or issue-closure decision.** "
        "The original findings, roadmap and issue map are unchanged. "
        "Reported statuses are copied verbatim, never inferred from PASS text, compilation, source changes or historical issue state.", "",
        "```sh", "python3 scripts/development/validate_resolutions.py          # validate only",
        "python3 scripts/development/validate_resolutions.py --check  # read-only; fails if stale",
        "python3 scripts/development/validate_resolutions.py --write  # regenerate after review",
        "python3 -m unittest discover -s scripts/development -p 'test_validate_resolutions.py' -v",
        "```", "",
        "`--check` returns 2 for missing/stale/edited generated files and 1 for invalid current inputs. "
        "It makes no network calls. A changed ledger, added/removed input, generator change or index edit invalidates the snapshot. "
        "No timestamps are embedded: unchanged inputs render byte-identical outputs.", "",
        "Freshness covers only the listed metadata/ledger inputs and generator. "
        "Referenced source, tests, logs/XML and evidence files are **not rehashed or certified**. "
        "They can change while this ledger index remains `CURRENT`; owner acceptance review must still check exact source/evidence receipts.", "",
        f"Baseline: `{model['baseline_revision']}`. Input fingerprint: `{model['input_fingerprint']}`.", "",
        f"Generator SHA256: `{model['generator']['sha256']}`.", "",
        f"**{counts['unique_resolution_ids']}/{counts['baseline_findings']} unique finding IDs** have a structurally valid owner record "
        f"and existing issue mapping. **{counts['imported_topics_without_finding_ids']} separate imported topics** are not miscounted as findings. "
        "**Zero statuses promoted; zero automatic closures.**", "",
        "## Reported status summary", "", "| Owner-ledger status | Findings |", "|---|---:|",
    ]
    lines += [f"| {status} | {count} |" for status, count in counts["reported_statuses"].items()]
    lines += ["", "`implemented` means a recorded source repair, not verified runtime behavior. "
              "`partially-verified` preserves target/scenario limits. `unresolved` and `not-applicable` remain explicit owner dispositions. "
              "A `verified` record is accepted structurally only with nonempty explicit evidence and no remaining checks; "
              "this validator does not read test prose as proof or certify the evidence. The lead must review original acceptance requirements.", "",
              "## Original roadmap order", "", md_text(model["original_roadmap_ordering"]), "",
              "Historical phase labels are reproduced for traceability, **not a fresh verification claim**:", ""]
    lines += [f"- **{phase}:** {md_text(label)}" for phase, label in model["original_phase_labels"].items()]
    lines += ["", "| Order | ID / existing issue | Priority | Phase | Effort | Reported status | Original dependencies | Required tests / owner remaining |",
              "|---:|---|---|---:|---|---|---|---:|"]
    for item in model["items"]:
        deps = ", ".join(item["original_dependencies"]) or "—"
        lines.append(f"| {item['original_order']} | [{item['id']}]({item['issue']['url']}) | {item['priority']} | "
                     f"{item['original_phase']} | {item['original_effort']} | {item['reported_status']} | {deps} | "
                     f"{len(item['original_required_tests'])} / {len(item['owner_record']['remaining'])} |")
    lines += ["", "Counts are requirement/remaining-text entries, **not test executions or a proof of completed gates**. "
              "Dependencies keep their original IDs/order; a dependency's reported status is not automatically treated as satisfied.", "",
              "## Original acceptance requirements and current remaining gates", "",
              "Every baseline test requirement is retained below and verbatim in `status.json`. "
              "Owner tests/results/evidence, changes, paths and compatibility are preserved separately in the JSON owner record. "
              "No matching or omission assumes an original requirement passed merely because the owner described it differently.", ""]
    for item in model["items"]:
        issue, current = item["issue"], item["owner_record"]
        lines += [f"### {item['original_order']}. {item['id']} — {md_text(item['title'])}", "",
                  f"**{item['priority']} · {item['reported_status']} · original effort {item['original_effort']}** "
                  f"— [nativeCmpkit #{issue['number']}]({issue['url']}); owner {doc_link(item['owner_ledger'])}; "
                  f"baseline {doc_link(item['baseline_file'])}.", "",
                  "**Original dependencies:** " + (", ".join(
                      f"[{dep['id']}]({dep['issue_url']}) ({dep['reported_status']}; original order {dep['original_order']})"
                      for dep in item["dependencies"]) or "none") + ".", "",
                  "**Original required tests (not auto-dispositioned):**", ""]
        lines += ["- " + md_text(test) for test in item["original_required_tests"]]
        lines += ["", "**Owner-recorded remaining gates:**", ""]
        lines += ["- " + md_text(gate) for gate in current["remaining"]] or [
            "- None recorded. This does not itself prove the original requirements passed."]
        if "verification_scope" in current:
            lines += ["", "**Owner verification scope:** " + md_text(current["verification_scope"])]
        compatibility = current["compatibility"]
        if isinstance(compatibility, str):
            compatibility = [compatibility]
        lines += ["", "**Compatibility / scope:** " + " ".join(md_text(text) for text in compatibility), ""]
    lines += ["## Separate imported topics", "",
              "These historical topics have existing issues but no finding ID/owner resolution record. "
              "They remain outside the denominator above; feature availability must not be inferred from audit repair statuses.", "",
              "| Original order | Topic | Existing issue | Priority |", "|---:|---|---|---|"]
    for item in model["imported_topics_without_resolution_ids"]:
        number = item["issue_url"].rsplit("/", 1)[1]
        lines.append(f"| {item['order']} | {md_text(item['title'])} | [#{number}]({item['issue_url']}) | {item['priority']} |")
    lines += ["", "## Snapshot input hashes", "",
              "The JSON also preserves all input sets/hashes and the generator hash. `--check` reconstructs the expected output, "
              "rather than trusting a manually edited freshness flag.", "", "| Input | SHA256 |", "|---|---|"]
    lines += [f"| {doc_link(path)} | `{digest}` |" for path, digest in model["input_sha256"].items()]
    lines += ["", "No source/build/GitHub changes, tests, releases or packages are executed by generation. "
              "Use the area ledgers and exact archived command/input receipts for human acceptance review.", ""]
    return "\n".join(lines).encode("utf-8")


def rendered_outputs(model: dict[str, Any]) -> dict[str, bytes]:
    return {OUTPUT_JSON: canonical(model), OUTPUT_MD: render_markdown(model)}


def check_outputs(root: Path, model: dict[str, Any]) -> list[str]:
    root = root.resolve()
    assert_inputs_current(root, model)
    stale = []
    for relative, expected in rendered_outputs(model).items():
        path = inside_root(root, relative)
        require(not path.is_symlink(), relative, "refusing to follow a symlink output")
        if not path.is_file() or path.read_bytes() != expected:
            stale.append(relative)
    assert_inputs_current(root, model)
    return stale


def write_outputs(root: Path, model: dict[str, Any]) -> None:
    root = root.resolve()
    outputs = rendered_outputs(model)
    # Validate both destinations before replacing either. Never follow an output symlink.
    for relative in outputs:
        path = inside_root(root, relative)
        require(not path.is_symlink(), relative, "refusing to replace a symlink output")
        require(not path.exists() or path.is_file(), relative, "expected a file output")
    assert_inputs_current(root, model)
    for relative, raw in outputs.items():
        path = inside_root(root, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".status-", suffix=".tmp", delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(raw)
            os.replace(temporary, path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
    # A later edit can always stale a snapshot; report an observed write-time race.
    assert_inputs_current(root, model)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root (default: script's repository)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write the two generated status index files")
    mode.add_argument("--check", action="store_true", help="read-only freshness/content check of both generated files")
    args = parser.parse_args(argv)
    try:
        model = build_snapshot(args.root)
        counts = model["counts"]
        if args.write:
            write_outputs(args.root, model)
            print(f"WROTE {OUTPUT_JSON} and {OUTPUT_MD}")
        elif args.check:
            stale = check_outputs(args.root, model)
            if stale:
                print("STALE: " + ", ".join(stale) + "; review inputs and regenerate with --write", file=sys.stderr)
                return 2
            print("CURRENT: both generated files match all input and generator hashes")
        print(f"VALID: {counts['unique_resolution_ids']}/{counts['baseline_findings']} unique resolutions/mappings; "
              + ", ".join(f"{status}={count}" for status, count in counts["reported_statuses"].items()))
        print("Structural checks only; no evidence certification, status promotion or automatic issue closure.")
        return 0
    except StaleSnapshotError as error:
        print(f"STALE: {error}", file=sys.stderr)
        return 2
    except (ValidationError, OSError) as error:
        prefix = "STALE / INVALID INPUT" if args.check else "INVALID"
        print(f"{prefix}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
