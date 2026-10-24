#!/usr/bin/env python3
"""Query OSV for exact Maven components from the metadata-only desktop graph.

Only public dependency coordinates are sent. No Gradle build, dependency install,
repository mutation, exploit test or automatic finding/severity assignment occurs.
Partial graphs remain explicitly partial. Runtime graphs exclude test/build inputs
and do not inventory native code bundled inside a Maven artifact.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen

OSV = "https://api.osv.dev/v1"


def queries_from_graph(graph):
    if graph.get("schema_version") != 1:
        raise ValueError("Unsupported runtime graph schema")
    coordinates = set()
    for configuration in graph["configurations"]:
        for component in configuration["components"]:
            if component["kind"] != "module":
                continue
            fields = tuple(component[key] for key in ("group", "module", "version"))
            if not all(isinstance(value, str) and value and len(value) <= 256
                       and not re.search(r"[\s/:]", value) for value in fields):
                raise ValueError("Invalid Maven component identity")
            coordinates.add(fields)
    if not coordinates:
        raise ValueError("No Maven components found; do not infer a clean scan")
    return [{"package": {"ecosystem": "Maven", "name": f"{group}:{module}"},
             "version": version} for group, module, version in sorted(coordinates)]


def request_json(path, payload=None):
    request = Request(OSV + path,
                      data=None if payload is None else json.dumps(payload).encode(),
                      headers={"Accept": "application/json", "User-Agent": "nativeCmpkit-public-dependency-audit",
                               **({"Content-Type": "application/json"} if payload is not None else {})})
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def query_batches(queries, request=request_json, batch_size=100):
    if batch_size < 1 or batch_size > 1000:
        raise ValueError("OSV batch size must be between 1 and 1000")
    results = []
    for offset in range(0, len(queries), batch_size):
        batch = queries[offset:offset + batch_size]
        reply = request("/querybatch", {"queries": batch})
        items = reply.get("results")
        if not isinstance(items, list) or len(items) != len(batch) or not all(isinstance(i, dict) for i in items):
            raise ValueError("OSV response does not match submitted query count")
        if any(item.get("next_page_token") for item in items):
            # A partial vulnerability list is not a completed scan. The audited
            # dataset had no page tokens; future paginated replies need explicit
            # per-package follow-up rather than silently dropping later matches.
            raise ValueError("OSV reply requires pagination; explicit follow-up is required")
        results.extend(items)
    return results


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    raw = args.graph.read_bytes()
    graph = json.loads(raw)
    queries = queries_from_graph(graph)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "scope": "Exact audit-time selected-host desktop runtime Maven advisory matches only; no exploitability or full-platform/binary/SBOM claim",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "graph_sha256": hashlib.sha256(raw).hexdigest(),
        "graph_revision_label": graph.get("revision_label"),
        "graph_host": graph.get("host"),
        "complete_runtime_graph": graph.get("resolution_complete") is True,
        "runtime_configurations": len(graph["configurations"]),
        "graph_unresolved_edges": sum(len(c.get("unresolved", [])) for c in graph["configurations"]),
        "graph_resolution_exceptions": sum("resolution_exception_type" in c for c in graph["configurations"]),
        "query_count": len(queries), "queries": queries,
        "api_scan_complete": False, "results": [], "matches": [], "advisory_files": [],
    }
    output = args.output_dir / "osv-desktop-runtime-query.json"
    write_json(output, report)
    try:
        report["results"] = query_batches(queries)
        ids = set()
        for query, result in zip(queries, report["results"]):
            matches = sorted({v["id"] for v in result.get("vulns", [])})
            if matches:
                report["matches"].append({"query": query, "advisory_ids": matches})
                ids.update(matches)
        write_json(output, report)
        for advisory_id in sorted(ids):
            if not re.fullmatch(r"[A-Za-z0-9-]+", advisory_id):
                raise ValueError("Unexpected advisory identifier")
            advisory = request_json("/vulns/" + quote(advisory_id, safe=""))
            name = "advisory-" + advisory_id + ".json"
            write_json(args.output_dir / name, advisory)
            report["advisory_files"].append(name)
        report["api_scan_complete"] = True
    except Exception as error:
        # No retries and no possibly credential-bearing exception text in evidence.
        report["api_error_type"] = type(error).__name__
    write_json(output, report)
    print(json.dumps({key: report[key] for key in ["query_count", "complete_runtime_graph",
                                                  "api_scan_complete", "matches"]}, indent=2))
    return 0 if report["api_scan_complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
