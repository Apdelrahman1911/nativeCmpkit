#!/usr/bin/env python3
"""Single-writer, opt-in posting of reviewed upstream context; never mutates Calf.

Dry-run by default. Unknown POST outcomes stop; a subsequent explicit invocation
reconciles the stable marker before considering another POST. Existing human edits
are never overwritten. Original issue bodies, labels and states stay intact.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/migration"))
from github_json import json_pages

REPO = "Apdelrahman1911/nativeCmpkit"
SOURCE = "MohamedRejeb/Calf"


def sha256(data: str | bytes) -> str:
    return hashlib.sha256(data.encode() if isinstance(data, str) else data).hexdigest()


def api(endpoint: str, method: str = "GET", data=None, paginate=False):
    if not endpoint.startswith(f"repos/{REPO}/") and endpoint != f"repos/{REPO}":
        raise ValueError("Only the fixed destination may be accessed by this writer")
    if method not in {"GET", "POST"} or (method == "POST" and not re.fullmatch(rf"repos/{REPO}/issues/[0-9]+/comments", endpoint)):
        raise ValueError("Only issue-context comment creation is authorized here")
    args = ["gh", "api", endpoint, "--method", method]
    if paginate:
        args.append("--paginate")
    if data is not None:
        args += ["--input", "-"]
    result = subprocess.run(args, input=json.dumps(data) if data is not None else None,
                            capture_output=True, text=True, cwd=ROOT)
    if result.returncode:
        raise RuntimeError(f"GitHub {method} failed/unknown (exit {result.returncode}); reconcile markers before retrying")
    if paginate:
        pages = json_pages(result.stdout)
        if not all(isinstance(page, list) for page in pages):
            raise ValueError("Expected paginated comment arrays")
        return [item for page in pages for item in page]
    return json.loads(result.stdout)


def render(operation: dict, token: str, commit: str) -> str:
    if operation.get("operation") != "create_issue_comment" or operation.get("repository") != REPO:
        raise ValueError("Unexpected operation/destination")
    if not isinstance(operation.get("issue_number"), int) or operation["issue_number"] <= 0:
        raise ValueError("Invalid destination issue number")
    marker = operation["dedupe_marker"]
    expected = f"<!-- nativecmpkit-upstream-sync:674932206:{operation['source_number']} -->"
    if marker != expected or operation["body"].count(marker) != 1:
        raise ValueError("Invalid stable source marker")
    if sha256(operation["body"]) != operation["body_sha256"]:
        raise ValueError("Draft changed after review")
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or not token or token not in operation["body"]:
        raise ValueError("Missing immutable archive binding")
    body = operation["body"].replace(token, commit)
    if len(body) > 65536:
        raise ValueError("Comment exceeds GitHub length limit; preserve via an archive rather than truncate")
    return body


def reconcile(operation: dict, issue: dict, comments: list, body: str):
    if (issue.get("id") != operation["expected_issue_id"]
            or issue.get("number") != operation["issue_number"]
            or issue.get("html_url") != f"https://github.com/{REPO}/issues/{operation['issue_number']}"
            or "pull_request" in issue):
        raise ValueError("Destination issue identity differs")
    if sha256(issue.get("body") or "") != operation["expected_issue_body_sha256"]:
        raise ValueError("Destination technical body changed; manual reconciliation required")
    if issue.get("state") != operation["expected_issue_state"]:
        raise ValueError("Destination lifecycle changed; do not silently substitute a new state")
    matches = [comment for comment in comments if operation["dedupe_marker"] in (comment.get("body") or "")]
    if len(matches) > 1:
        raise ValueError("Duplicate source-context markers require review")
    if matches and matches[0].get("body") != body:
        raise ValueError("Existing context was edited or differs; preserve it and require review")
    return matches[0] if matches else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handoff", type=Path, required=True)
    parser.add_argument("--archive-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    plan = json.loads(args.handoff.read_text())
    if plan.get("destination") != REPO or plan.get("source") != SOURCE or plan.get("create_issue_operations"):
        raise ValueError("This writer accepts reviewed context-only plans for the fixed repositories")
    if not re.fullmatch(r"[0-9a-f]{40}", args.archive_commit):
        raise ValueError("Full archive commit SHA required")
    subprocess.run(["git", "merge-base", "--is-ancestor", args.archive_commit, "HEAD"], cwd=ROOT, check=True)
    snapshot = plan["snapshot_path"]
    if not re.fullmatch(r"docs/migration/upstream-updates/[0-9]{8}T[0-9]{6}Z", snapshot):
        raise ValueError("Unexpected archive path")
    for name, key in [("receipt.json", "snapshot_receipt_sha256"), ("SHA256SUMS", "snapshot_sha256sums_sha256")]:
        data = subprocess.check_output(["git", "show", f"{args.archive_commit}:{snapshot}/{name}"], cwd=ROOT)
        if sha256(data) != plan[key]:
            raise ValueError("Immutable archive differs from reviewed snapshot")
    identity = api(f"repos/{REPO}")
    if identity.get("full_name") != REPO or identity.get("fork") is not False:
        raise ValueError("Unexpected destination repository")
    report = {"schema_version": 1, "repository": REPO, "source": SOURCE,
              "started_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "archive_commit": args.archive_commit, "apply": args.apply,
              "handoff_sha256": sha256(args.handoff.read_bytes()), "complete": False, "items": []}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def save():
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    save()
    try:
        for operation in plan["comment_operations"]:
            body = render(operation, plan["archive_commit_token"], args.archive_commit)
            endpoint = f"repos/{REPO}/issues/{operation['issue_number']}"
            issue = api(endpoint)
            comments = api(endpoint + "/comments?per_page=100", paginate=True)
            existing = reconcile(operation, issue, comments, body)
            outcome = "existing-identical" if existing else "planned"
            if args.apply and not existing:
                existing = api(endpoint + "/comments", "POST", {"body": body})
                outcome = "created"
            if existing:
                check = api(f"repos/{REPO}/issues/comments/{existing['id']}")
                if check.get("body") != body or check.get("issue_url") != f"https://api.github.com/{endpoint}":
                    raise ValueError("Comment readback differs; do not retry POST")
            # Explicitly prove that posting did not replace the original body/state/labels.
            after = api(endpoint) if args.apply else issue
            for field in ("id", "body", "title", "state"):
                if after.get(field) != issue.get(field):
                    raise ValueError(f"Issue {field} changed during context posting; preserve and review")
            if {x["name"] for x in after["labels"]} != {x["name"] for x in issue["labels"]}:
                raise ValueError("Issue labels changed during context posting")
            item = {"source_number": operation["source_number"], "issue_number": operation["issue_number"],
                    "source_disposition": operation["source_disposition"], "outcome": outcome,
                    "body_sha256": sha256(body), "comment_id": existing["id"] if existing else None,
                    "comment_url": existing["html_url"] if existing else None, "readback_verified": bool(existing)}
            report["items"].append(item)
            save()
            print(f"Calf#{item['source_number']} -> nativeCmpkit#{item['issue_number']}: {outcome}", flush=True)
        report["complete"] = True
        report["completed_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        report["new_issues_created"] = 0
        save()
    except Exception as error:
        report["error"] = str(error)
        save()
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
