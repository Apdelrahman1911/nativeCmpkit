#!/usr/bin/env python3
"""Read-only verification of destination issues against the preserved plan/map."""
import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
from sync_github_issues import ROOT, REPO, gh, flat_pages, managed_key


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    plan = json.loads((ROOT / "docs/audit/issue-plan.json").read_text())
    mapping = json.loads((ROOT / "docs/migration/issue-map.json").read_text())
    errors = []
    if plan["repository"] != REPO or mapping["repository"] != REPO or not mapping.get("complete"):
        raise SystemExit("Missing complete fixed-destination issue map")
    state = gh("repos/" + REPO)
    if state["full_name"] != REPO or state["fork"]:
        raise SystemExit("Unexpected destination")
    issues = [issue for issue in flat_pages(gh(f"repos/{REPO}/issues?state=all&per_page=100", paginate=True)) if "pull_request" not in issue]
    remote = {}
    for issue in issues:
        key = managed_key(issue.get("body"))
        if key:
            if key in remote: errors.append("Duplicate remote marker: " + key)
            remote[key] = issue
    saved = {item["key"]: item for item in mapping["items"]}
    expected = {item["key"]: item for item in plan["items"]}
    if set(expected) != set(saved): errors.append("Plan/map key sets differ")
    if set(expected) != set(remote): errors.append("Plan/remote managed key sets differ")
    checked = []
    for key, item in expected.items():
        issue, receipt = remote.get(key), saved.get(key)
        if not issue or not receipt: continue
        body_hash = hashlib.sha256((issue.get("body") or "").encode()).hexdigest()
        conditions = {
            "number": issue["number"] == receipt["number"],
            "url": issue["html_url"] == receipt["url"],
            "title": issue["title"] == item["title"],
            "body_hash": body_hash == item["body_sha256"] == receipt["body_sha256"],
            "labels": set(item["labels"]) <= {x["name"] for x in issue["labels"]},
            "state_at_sync": issue["state"] == receipt["actual_state"],
            "author": issue["user"]["login"] == receipt["github_author"] == "Apdelrahman1911",
            "timestamp": issue["created_at"] == receipt["github_created_at"],
            "no_pending_initial_closure": not receipt.get("pending_initial_close", False),
        }
        errors.extend(key + ": " + name for name, value in conditions.items() if not value)
        checked.append({"key": key, "number": issue["number"], "url": issue["html_url"], "state": issue["state"], "body_sha256": body_hash, "checks_passed": all(conditions.values())})
    report = {"checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "repository": REPO, "scope": "Read-only remote issue identity/body/label/lifecycle receipt validation; not code or runtime proof", "plan_count": len(expected), "remote_managed_count": len(remote), "unmanaged_issues_untouched": len(issues) - len(remote), "states": dict(Counter(x["state"] for x in checked)), "passed": not errors, "errors": errors, "items": checked}
    output = json.dumps(report, indent=2) + "\n"
    if args.output: args.output.write_text(output)
    print(output)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
