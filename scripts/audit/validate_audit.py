#!/usr/bin/env python3
"""Validate persistent evidence structure; never claims to prove Kotlin correctness."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = {"id", "title", "priority", "status", "modules", "locations", "root_cause", "impact", "recommendation", "risks", "required_tests", "evidence", "upstream_refs", "effort", "dependencies"}
AREAS = {"IO", "PERM", "UI", "NATIVE", "NAV", "BUILD", "HIST"}
PRIORITIES = {"Critical", "High", "Medium", "Low"}
STATUSES = {"confirmed-source", "confirmed-test", "risk", "unverified", "improvement"}


def load_findings():
    result = []
    for file in sorted((ROOT / "docs/audit/findings").glob("*.json")):
        value = json.loads(file.read_text())
        if not isinstance(value, list):
            raise ValueError(f"{file.name}: finding area file must be an array")
        result.extend(value)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-incomplete", action="store_true", help="During review only: tolerate not-yet-authored area/index files")
    args = parser.parse_args()
    errors = []
    warnings = []
    checked_locations = 0
    try:
        identity = json.loads((ROOT / "docs/migration/identity.json").read_text())
        baseline = identity["source_baseline"]
        if not re.fullmatch(r"[0-9a-f]{40}", baseline):
            raise ValueError("invalid baseline")
        available = {p.stem for p in (ROOT / "docs/audit/findings").glob("*.json")}
        if not args.allow_incomplete and not AREAS <= available:
            errors.append("Missing area files: " + ", ".join(sorted(AREAS-available)))
        findings = load_findings()
        ids = [f.get("id") for f in findings]
        if len(set(ids)) != len(ids):
            errors.append("Duplicate finding IDs")
        line_counts = {}
        for item in findings:
            key = item.get("id", "UNKNOWN")
            missing = REQUIRED - item.keys()
            if missing:
                errors.append(f"{key}: missing {sorted(missing)}")
                continue
            if not re.fullmatch(r"[A-Z]+-[0-9]{3}", key):
                errors.append(f"{key}: malformed ID")
            if item["priority"] not in PRIORITIES or item["status"] not in STATUSES or item["effort"] not in {"S", "M", "L", "XL"}:
                errors.append(f"{key}: bad severity/status/effort")
            for field in ("title", "root_cause", "impact", "recommendation", "risks"):
                if not isinstance(item[field], str) or not item[field].strip():
                    errors.append(f"{key}: empty/non-string {field}")
            for field in ("modules", "locations", "required_tests", "evidence"):
                if not isinstance(item[field], list) or not item[field]:
                    errors.append(f"{key}: missing actionable {field}")
            for location in item["locations"]:
                path = location.get("path", "")
                if not path or path.startswith("/") or ".." in Path(path).parts:
                    errors.append(f"{key}: unsafe/absent location")
                    continue
                if path not in line_counts:
                    p = subprocess.run(["git", "show", baseline + ":" + path], cwd=ROOT, capture_output=True)
                    if p.returncode:
                        errors.append(f"{key}: location not present at baseline: {path}")
                        continue
                    line_counts[path] = len(p.stdout.splitlines())
                ranges = re.findall(r"\d+(?:\s*-\s*\d+)?", str(location.get("lines", "")))
                if not ranges or not location.get("symbol"):
                    errors.append(f"{key}: exact line/symbol evidence missing: {path}")
                for value in ranges:
                    ends = [int(x.strip()) for x in value.split("-")]
                    if min(ends) < 1 or max(ends) > line_counts[path] or ends != sorted(ends):
                        errors.append(f"{key}: out-of-range citation {path}:{value} (file has {line_counts[path]} lines)")
                checked_locations += 1
            for dependency in item["dependencies"]:
                if dependency == key or (dependency not in ids and not args.allow_incomplete):
                    errors.append(f"{key}: invalid dependency {dependency}")
        # Dependency cycles make roadmap sequencing impossible.
        graph = {x["id"]: x.get("dependencies", []) for x in findings}
        done, active = set(), set()
        def visit(key):
            if key in active:
                errors.append("Dependency cycle at " + key)
                return
            if key in done or key not in graph:
                return
            active.add(key)
            for child in graph[key]: visit(child)
            active.remove(key); done.add(key)
        for key in graph: visit(key)

        inventory = json.loads((ROOT / "docs/audit/source-inventory.json").read_text())
        if inventory["baseline_commit"] != baseline:
            errors.append("Inventory baseline mismatch")
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/audit/source_inventory.py"), "--check"], cwd=ROOT, capture_output=True, text=True)
        if proc.returncode:
            errors.append("Inventory reproduction failed: " + (proc.stdout+proc.stderr)[-2000:])
        if not args.allow_incomplete:
            required_docs = ["AGENTS.md", "README.md", "docs/architecture/README.md", "docs/modules/README.md", "docs/platforms/README.md", "docs/audit/README.md", "docs/audit/final-report.md", "docs/testing/README.md", "docs/decisions/README.md", "docs/roadmap/README.md", "docs/migration/README.md"]
            for path in required_docs:
                if not (ROOT / path).is_file(): errors.append("Missing documentation: " + path)
            # Validate local links in entry-point documents; archives retain their original broken links.
            for path in required_docs:
                file = ROOT / path
                if not file.is_file(): continue
                source = file.read_text()
                for link in re.findall(r"\]\(([^\s)]+)(?:\s+[^)]*)?\)", source):
                    if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", link) or link.startswith(("#", "//")):
                        continue
                    relative = unquote(link.split("#", 1)[0].split("?", 1)[0])
                    if relative and not (file.parent / relative).exists():
                        errors.append(f"Broken entry-point local link: {path} -> {link}")
        result = {"passed": not errors, "scope": "Structural evidence validation, not runtime/build proof", "baseline": baseline, "findings": len(findings), "locations_checked": checked_locations, "inventory_files": len(inventory["files"]), "errors": errors, "warnings": warnings}
    except Exception as exc:
        result = {"passed": False, "error": str(exc), "errors": errors}
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
