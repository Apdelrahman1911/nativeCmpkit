#!/usr/bin/env python3
"""Discover Apple allocation-tool support with an owned PUBLIC C probe only.

This runs on the already selected Apple verification host, not another CI job.
The probe is NOT NativeCmpKit/UIKit/GC execution or memory-safety certification.
Private traces, executables, logs and exported allocation rows never leave the
runner. Only source-bound tool outcomes, schema names/counts and hashes survive.
Unsupported tooling is reported explicitly, never converted into a library pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET

import library_tests as lt
import runtime_context as runtime

OUTPUT = "build/ci-verification/apple-memory-discovery"
MAX_XML_BYTES = 16 * 1024**2
MAX_PRIVATE_BYTES = 256 * 1024**2
MAX_PRIVATE_ENTRIES = 4096
MAX_TABLES = 12
SCHEMA = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,127}\Z")
PROBE_SYMBOL = "nativecmpkit_allocation_probe"
PROBE_SOURCE = r"""/* Public, bounded tool-discovery fixture. NOT library/native UI evidence. */
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
static volatile unsigned char witness;
__attribute__((noinline)) static void nativecmpkit_allocation_probe(void) {
    void *objects[128] = {0};
    for (int n = 0; n < 128; ++n) {
        objects[n] = malloc(65536);
        if (!objects[n]) _exit(3);
        memset(objects[n], n, 65536);
        witness ^= ((unsigned char *)objects[n])[0];
    }
    usleep(200000);
    for (int n = 0; n < 128; ++n) free(objects[n]);
}
int main(void) {
    for (int n = 0; n < 20; ++n) nativecmpkit_allocation_probe();
    return witness == 255 ? 1 : 0;
}
"""


def bounded_xml(path: Path) -> tuple[ET.Element, bytes]:
    stat = path.stat()
    if not path.is_file() or path.is_symlink() or stat.st_nlink != 1 or not 1 <= stat.st_size <= MAX_XML_BYTES:
        raise ValueError("Expected bounded regular private tool XML")
    payload = path.read_bytes()
    if b"<!DOCTYPE" in payload.upper() or b"<!ENTITY" in payload.upper():
        raise ValueError("Tool XML DTD/entities are not permitted")
    after = path.stat()
    if (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError("Tool XML changed during inspection")
    return ET.fromstring(payload), payload


def allocation_schemas(toc: ET.Element) -> list[str]:
    values = []
    for node in toc.iter():
        if node.tag.rsplit("}", 1)[-1] != "table":
            continue
        value = node.get("schema", "")
        if not SCHEMA.fullmatch(value):
            raise ValueError("Unreviewable allocation-tool schema identity")
        if re.search(r"alloc|heap|leak", value, re.I) and value not in values:
            values.append(value)
    if len(values) > MAX_TABLES:
        raise ValueError("Allocation export table selection exceeds its bound")
    return values


def allocation_summary(path: Path) -> dict:
    tree, payload = bounded_xml(path)
    rows = sum(node.tag.rsplit("}", 1)[-1] == "row" for node in tree.iter())
    # Inspect only this owned public probe's fixed symbol; never export frame
    # strings/addresses/values/paths from a trace or attempt general scrubbing.
    symbol = any(PROBE_SYMBOL in (node.text or "") or
                 any(PROBE_SYMBOL in value for value in node.attrib.values()) for node in tree.iter())
    return {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
            "rows": rows, "owned_public_probe_symbol_seen": symbol,
            "raw_rows_addresses_values_or_trace_uploaded": False}


def private_inventory(root: Path, private: Path) -> dict:
    files, total = 0, 0
    for path in private.rglob("*"):
        lt.safe_path(root, path.relative_to(root).as_posix())
        files += 1
        if files > MAX_PRIVATE_ENTRIES:
            raise ValueError("Private discovery tree exceeds its entry bound")
        if path.is_file():
            if path.stat().st_nlink != 1:
                raise ValueError("Private discovery file is shared")
            total += path.stat().st_size
        elif not path.is_dir():
            raise ValueError("Unexpected private discovery entry type")
        if total > MAX_PRIVATE_BYTES:
            raise ValueError("Private discovery tree exceeds its byte bound")
    return {"entries": files, "bytes": total, "raw_files_uploaded": False}


def discover(root: Path, simulator: str) -> dict:
    if not runtime.UUID.fullmatch(simulator):
        raise ValueError("Use the exact already selected Apple simulator")
    output = lt.safe_path(root, OUTPUT)
    if output.exists():
        raise ValueError("Never overwrite or automatically repeat discovery")
    context = runtime.capture(expected_arch="arm64", apple=True, device=simulator,
                              require_booted=True, require_clean=True)
    if context["host"]["system"] != "Darwin":
        raise ValueError("Apple tool discovery requires the actual Apple host")
    if shutil.disk_usage(root).free < 8192 * 1024**2 + MAX_PRIVATE_BYTES:
        raise OSError("Discovery must preserve the production 8 GiB reserve")
    before = lt.snapshot_inputs(root)
    output.mkdir(parents=True)
    private = output / "private"
    private.mkdir(mode=0o700)
    record = {"schema_version": 1, "started_at_utc": lt.utc_now(),
              "source_revision": context["source_revision"], "runtime": context,
              "supported": False, "commands": [], "exports": [], "errors": [],
              "probe_source_sha256": hashlib.sha256(PROBE_SOURCE.encode()).hexdigest(),
              "library_test_executions": 0, "UIKit_GC_or_ASan_verified": False,
              "release_readiness_certified": False, "raw_files_uploaded": False,
              "scope": "Informational Apple SDK allocation-tool discovery using an owned public HOST C probe, NOT iOS/UIKit/library behavior or a release/memory-safety gate"}

    def execute(command: list[str], name: str, timeout: int = 120) -> dict:
        result = lt.execute(root, command, private / (name + ".log"), timeout, 8192)
        record["commands"].append({"command": command, **result})
        private_inventory(root, private)
        if result["exit_code"] != 0 or result.get("stop_reason"):
            raise RuntimeError("Actual allocation-tool command failed; discovery is unsupported/unverified")
        return result

    try:
        source, binary, trace = private / "probe.c", private / "NativeCmpkitAllocationProbe", private / "probe.trace"
        source.write_text(PROBE_SOURCE)
        execute(["/usr/bin/xcrun", "clang", "-g", "-O0", str(source), "-o", str(binary)], "compile-probe")
        record["actual_probe_binary_sha256"] = lt.sha256(binary)
        execute(["/usr/bin/xcrun", "xctrace", "record", "--template", "Allocations", "--time-limit", "8s",
                 "--output", str(trace), "--launch", "--", str(binary)], "record-allocations", 180)
        toc = private / "toc.xml"
        execute(["/usr/bin/xcrun", "xctrace", "export", "--input", str(trace), "--toc", "--output", str(toc)], "export-toc")
        tree, body = bounded_xml(toc)
        record["toc_sha256"] = hashlib.sha256(body).hexdigest()
        schemas = allocation_schemas(tree)
        record["actual_allocation_schemas"] = schemas
        for index, schema in enumerate(schemas):
            exported = private / ("allocations-" + str(index) + ".xml")
            xpath = "//table[@schema='" + schema + "']"
            execute(["/usr/bin/xcrun", "xctrace", "export", "--input", str(trace), "--xpath", xpath,
                     "--output", str(exported)], "export-" + str(index))
            record["exports"].append({"schema": schema, **allocation_summary(exported)})
        record["supported"] = any(row["rows"] > 0 and row["owned_public_probe_symbol_seen"] for row in record["exports"])
        if not record["supported"]:
            record["errors"].append({"error": "No actual allocation rows containing the owned public probe symbol; NOT native/library evidence"})
    except (OSError, ValueError, RuntimeError, ET.ParseError) as error:
        record["errors"].append({"error_type": type(error).__name__, "native_library_pass_inferred": False})
    finally:
        after = lt.snapshot_inputs(root)
        record.update(finished_at_utc=lt.utc_now(), input_digest_before=lt.input_digest(before),
                      input_digest_after=lt.input_digest(after), all_inputs_held=before == after)
        if before != after:
            record["supported"] = False
            record["errors"].append({"error": "Discovery inputs changed; no trusted source-bound support observation"})
        try:
            record["private_inventory"] = private_inventory(root, private)
            if private != lt.safe_path(root, OUTPUT + "/private") or private.is_symlink():
                raise ValueError("Private discovery ownership changed")
            shutil.rmtree(private)
            record["owned_private_tree_removed"] = not private.exists()
        except (OSError, ValueError) as error:
            record["owned_private_tree_removed"] = False
            record["supported"] = False
            record["errors"].append({"cleanup_error_type": type(error).__name__})
        lt.write_json(output / "discovery.json", record)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulator", required=True)
    options = parser.parse_args()
    result = discover(lt.ROOT, options.simulator)
    print(json.dumps(result, indent=2, sort_keys=True))
    # Discovery is informational; it cannot fail or certify the independent
    # sample build. Its explicit supported=false remains a native gate blocker.


if __name__ == "__main__":
    main()
