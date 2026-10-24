#!/usr/bin/env python3
"""Read-only, redacted selected-marker scan of text blobs reachable from the archive.

This is not a comprehensive secret detector. It never prints matched values.
All listed archive Git objects must already be available in the local checkout.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--git-dir", type=Path, help="Existing bare repository or checkout containing all archived objects; read-only")
parser.add_argument("--include-supplemental", action="store_true", help="Also scan recovered metadata-referenced commit history")
args = parser.parse_args()
git_source = args.git_dir.resolve() if args.git_dir else ROOT
patterns = {
    "private-key-header": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"),
    "github-token-shaped": re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "github-fine-grained-token-shaped": re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    "aws-access-key-shaped": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "google-api-key-shaped": re.compile(rb"\bAIza[0-9A-Za-z_-]{35}\b"),
    "npm-token-shaped": re.compile(rb"\bnpm_[A-Za-z0-9]{30,}\b"),
}
refs = []
manifests = [ROOT / "docs/migration/git/upstream-refs.txt"]
if args.include_supplemental:
    manifests.append(ROOT / "docs/migration/git/referenced-commit-refs.txt")
for manifest in manifests:
    for line in manifest.read_text().splitlines():
        oid = line.split()[0]
        if not re.fullmatch(r"[0-9a-f]{40}", oid):
            raise SystemExit("Invalid archived ref")
        refs.append(oid)
raw = subprocess.check_output(["git", "rev-list", "--objects", "--stdin"], input=("\n".join(refs)+"\n").encode(), cwd=git_source)
objects = {}
for line in raw.splitlines():
    parts = line.split(b" ", 1)
    objects[parts[0].decode()] = parts[1].decode("utf-8", "replace") if len(parts) == 2 else ""
proc = subprocess.Popen(["git", "cat-file", "--batch"], cwd=git_source, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
result = {"scope": "All unique objects reachable from recorded advertised refs" + (" and supplemental recovered commits" if args.include_supplemental else "") + "; selected regex text markers only", "manifests": [{"file": str(p.relative_to(ROOT)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in manifests], "patterns": list(patterns), "objects_enumerated": len(objects), "text_blobs_scanned": 0, "binary_blobs_skipped": 0, "large_blobs_skipped": 0, "non_blob_objects": 0, "findings": [], "limitations": ["Not an entropy detector or proof that no secrets exist", "Binary blobs, blobs over 8 MiB and compressed archive contents are not scanned", "Objects unavailable even after archive recovery remain outside the scan", "Never prints matched secret-like values; matches require private manual adjudication"]}
try:
    for oid, path in objects.items():
        proc.stdin.write((oid+"\n").encode()); proc.stdin.flush()
        header = proc.stdout.readline().split()
        if len(header) != 3:
            raise RuntimeError("Missing/malformed Git object response: " + oid)
        typ = header[1]; size = int(header[2])
        data = proc.stdout.read(size)
        if proc.stdout.read(1) != b"\n" or len(data) != size:
            raise RuntimeError("Incomplete Git object response")
        if typ != b"blob":
            result["non_blob_objects"] += 1; continue
        if size > 8*1024*1024:
            result["large_blobs_skipped"] += 1; continue
        if b"\0" in data[:8192]:
            result["binary_blobs_skipped"] += 1; continue
        result["text_blobs_scanned"] += 1
        for kind, regex in patterns.items():
            for match in regex.finditer(data):
                result["findings"].append({"kind": kind, "blob": oid, "representative_path": path, "line": data.count(b"\n",0,match.start())+1, "matched_value": "REDACTED"})
finally:
    proc.stdin.close(); proc.stdout.close(); proc.wait()
print(json.dumps(result, indent=2))
