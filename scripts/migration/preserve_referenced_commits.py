#!/usr/bin/env python3
"""Archive commit objects referenced by public metadata but absent from advertised refs.

The default is a read-only missing-object inventory. --fetch reads upstream Git
and adds only local refs/archive/upstream/referenced-commits/* in the specified
migration mirror. No GitHub mutation, push, rebase, pruning, or history rewrite.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mirror", type=Path, required=True)
    p.add_argument("--fetch", action="store_true")
    args = p.parse_args()
    mirror = args.mirror.resolve()
    if not mirror.is_dir(): raise SystemExit("Mirror must already exist")
    def git(*argv, check=True, timeout=120):
        r = subprocess.run(["git", "--git-dir="+str(mirror), "-c", "gc.auto=0", *argv], capture_output=True, text=True, timeout=timeout)
        if check and r.returncode: raise RuntimeError("Git operation failed: " + r.stderr[-1500:])
        return r
    source = ROOT / "docs/migration/upstream-metadata/referenced-commits.json"
    raw = source.read_bytes(); data = json.loads(raw)
    entries = []
    for item in data:
        sha = item["sha"]
        if not re.fullmatch(r"[0-9a-f]{40}", sha): raise ValueError("Invalid metadata SHA")
        kind = git("cat-file", "-t", sha, check=False)
        present = kind.returncode == 0 and kind.stdout.strip() == "commit"
        entries.append({"sha": sha, "status": "already-present" if present else "missing", "metadata_references": len(item["references"])})
    missing = [e for e in entries if e["status"] == "missing"]
    receipt = {"observed_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"source_dataset":"docs/migration/upstream-metadata/referenced-commits.json", "source_dataset_sha256":hashlib.sha256(raw).hexdigest(), "candidate_count":len(entries), "initially_missing_count":len(missing), "fetch_requested":args.fetch, "upstream":"https://github.com/MohamedRejeb/Calf.git", "entries":entries}
    output = ROOT / "docs/migration/git/referenced-commits-verification.json"
    def save(): output.write_text(json.dumps(receipt,indent=2)+"\n")
    save()
    print(json.dumps({"candidates":len(entries),"missing":len(missing),"fetch":args.fetch}),flush=True)
    if not args.fetch: return
    # Explicit upstream URL avoids relying on mutable remote names or credentials in URLs.
    for index, entry in enumerate(missing, 1):
        sha = entry["sha"]
        try:
            r = git("fetch", "--no-tags", "--no-write-fetch-head", "https://github.com/MohamedRejeb/Calf.git", sha, check=False)
            if r.returncode:
                entry.update(status="unavailable-or-fetch-failed",exit_code=r.returncode,detail=r.stderr[-1200:])
            else:
                kind = git("cat-file", "-t", sha).stdout.strip()
                if kind != "commit":
                    entry.update(status="not-a-commit",object_type=kind)
                else:
                    ref="refs/archive/upstream/referenced-commits/"+sha
                    git("update-ref",ref,sha)
                    entry.update(status="fetched-and-archived",archive_ref=ref)
        except subprocess.TimeoutExpired:
            entry.update(status="fetch-timeout",detail="120-second per-object read timeout; no automatic retry")
        save()
        if index % 10 == 0 or index == len(missing):
            print(json.dumps({"processed":index,"missing_total":len(missing),"last_status":entry["status"]}),flush=True)
    refs=git("for-each-ref","--format=%(refname)","refs/archive/upstream/referenced-commits/").stdout.splitlines()
    receipt["archival_refs_count"]=len(refs)
    if refs:
        bundle=ROOT/"docs/migration/git/referenced-commits.bundle"
        git("bundle","create",str(bundle),*refs)
        git("bundle","verify",str(bundle))
        checksum=hashlib.sha256(bundle.read_bytes()).hexdigest()
        (ROOT/"docs/migration/git/referenced-commits.bundle.sha256").write_text(checksum+"  docs/migration/git/referenced-commits.bundle\n")
        refs_file=ROOT/"docs/migration/git/referenced-commit-refs.txt"
        refs_file.write_text(git("for-each-ref","--format=%(objectname) %(objecttype) %(refname)","refs/archive/upstream/referenced-commits/").stdout)
        receipt.update(bundle="docs/migration/git/referenced-commits.bundle",bundle_sha256=checksum,bundle_verified=True)
    receipt["completed_at_utc"]=dt.datetime.now(dt.timezone.utc).isoformat()
    receipt["statuses"]={status:sum(e["status"]==status for e in entries) for status in sorted({e["status"] for e in entries})}
    save(); print(json.dumps({"statuses":receipt["statuses"],"archive_refs":len(refs)}),flush=True)

if __name__=="__main__": main()
