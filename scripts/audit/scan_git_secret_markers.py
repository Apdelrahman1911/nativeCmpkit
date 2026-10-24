#!/usr/bin/env python3
"""Read-only, redacted selected-marker scan of text blobs reachable from the archive.

This is not a comprehensive secret detector. It never prints matched values.
All listed archive Git objects must already be available in the local checkout.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
patterns = {
    "private-key-header": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"),
    "github-token-shaped": re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "github-fine-grained-token-shaped": re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    "aws-access-key-shaped": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "google-api-key-shaped": re.compile(rb"\bAIza[0-9A-Za-z_-]{35}\b"),
    "npm-token-shaped": re.compile(rb"\bnpm_[A-Za-z0-9]{30,}\b"),
}
refs = []
for line in (ROOT / "docs/migration/git/upstream-refs.txt").read_text().splitlines():
    oid = line.split()[0]
    if not re.fullmatch(r"[0-9a-f]{40}", oid):
        raise SystemExit("Invalid archived ref")
    refs.append(oid)
raw = subprocess.check_output(["git", "rev-list", "--objects", "--stdin"], input=("\n".join(refs)+"\n").encode(), cwd=ROOT)
objects = {}
for line in raw.splitlines():
    parts = line.split(b" ", 1)
    objects[parts[0].decode()] = parts[1].decode("utf-8", "replace") if len(parts) == 2 else ""
proc = subprocess.Popen(["git", "cat-file", "--batch"], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
result = {"scope": "All unique objects reachable from advertised refs recorded at migration; selected regex text markers only", "patterns": list(patterns), "objects_enumerated": len(objects), "text_blobs_scanned": 0, "binary_blobs_skipped": 0, "large_blobs_skipped": 0, "non_blob_objects": 0, "findings": [], "limitations": ["Not an entropy detector or proof that no secrets exist", "Binary blobs, blobs over 8 MiB and compressed archive contents are not scanned", "Deleted/server-unreachable objects are outside the advertised Git snapshot", "Never prints matched secret-like values; matches require private manual adjudication"]}
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
