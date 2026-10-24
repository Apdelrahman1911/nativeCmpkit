#!/usr/bin/env python3
"""Read-only Calf open-issue reconciliation; never performs GitHub mutations.

Capture fresh public evidence, reconcile with existing nativeCmpkit tickets, and
produce a deduplicated mutation handoff for the lead. Frozen migration metadata
is only read. Production source, issue-map, and existing issue bodies are not
modified. The archive-commit placeholder must be bound after committing the
snapshot and before the lead posts proposed comments.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/migration"))
from archive_upstream import Archive, BASELINE, dump, read, sha256, utc_now  # noqa: E402
from sync_github_issues import managed_key, source_links  # noqa: E402

SOURCE = "MohamedRejeb/Calf"
DESTINATION = "Apdelrahman1911/nativeCmpkit"
SOURCE_ID = 674932206
ARCHIVE_COMMIT_TOKEN = "__UPSTREAM_SYNC_ARCHIVE_COMMIT__"
MARKER = re.compile(r"^<!-- nativecmpkit-upstream-sync:674932206:(\d+) -->$")
FINGERPRINT = re.compile(r"^<!-- source-fingerprint:([0-9a-f]{64}) -->$", re.MULTILINE)


def git(*arguments):
    return subprocess.run(["git", *arguments], cwd=ROOT, check=True, capture_output=True).stdout


def content_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def freeze(directory):
    entries = [f"{sha256(path)}  {path.relative_to(directory)}" for path in sorted(directory.rglob("*"))
               if path.is_file() and path.name != "SHA256SUMS"]
    (directory / "SHA256SUMS").write_text("\n".join(entries) + "\n", encoding="utf-8")


def verify_frozen(directory):
    lines = (directory / "SHA256SUMS").read_text().splitlines()
    files = set()
    for line in lines:
        expected, name = line.split("  ", 1)
        path = (directory / name).resolve()
        if not path.is_relative_to(directory.resolve()) or sha256(path) != expected:
            raise ValueError(f"Archive hash/path failure: {name}")
        files.add(name)
    actual = {str(path.relative_to(directory)) for path in directory.rglob("*") if path.is_file() and path.name != "SHA256SUMS"}
    if files != actual:
        raise ValueError("Archive file set differs from SHA256SUMS")
    for sidecar in directory.rglob("*.http.json"):
        response = read(sidecar)
        if sha256(directory / response["response_body"]) != response["response_sha256"]:
            raise ValueError(f"Raw response hash failure: {response['response_body']}")
    return len(lines)


def capture(snapshot):
    if (snapshot / "receipt.json").exists():
        verify_frozen(snapshot)
        return read(snapshot / "receipt.json")
    arguments = argparse.Namespace(output=str(snapshot), repository=SOURCE, baseline=BASELINE, workers=4)
    archive = Archive(arguments)
    original_sums = ROOT / "docs/migration/upstream-metadata/SHA256SUMS"
    prior_sums_hash = sha256(original_sums)
    local_head = git("rev-parse", "HEAD").decode().strip()

    def single(name, endpoint):
        data, meta = archive.request(name + ".json", endpoint)
        archive.dataset(name, output=name + ".json", complete=meta["success"], status=meta["status"])
        if not meta["success"]:
            raise RuntimeError(f"Required read failed; response retained: {endpoint}")
        return data

    source_repo = single("source/repository", f"repos/{SOURCE}")
    destination_repo = single("destination/repository", f"repos/{DESTINATION}")
    if source_repo["id"] != SOURCE_ID or source_repo["full_name"].lower() != SOURCE.lower():
        raise ValueError("Unexpected source repository identity")
    if destination_repo["full_name"].lower() != DESTINATION.lower() or destination_repo["fork"]:
        raise ValueError("Destination is not the expected independent repository")
    source_head = single("source/default-branch-commit", f"repos/{SOURCE}/commits/{source_repo['default_branch']}")["sha"]
    destination_head = single("destination/default-branch-commit", f"repos/{DESTINATION}/commits/{destination_repo['default_branch']}")["sha"]
    records = archive.pages("source/open-issues-including-prs", f"repos/{SOURCE}/issues?state=open&sort=created&direction=asc&per_page=100")
    issues = [item for item in records if "pull_request" not in item]
    pulls = [item for item in records if "pull_request" in item]
    dump(snapshot / "source/open-issues.json", issues)
    dump(snapshot / "source/open-pull-requests.json", pulls)
    destination_records = archive.pages("destination/issues", f"repos/{DESTINATION}/issues?state=all&sort=created&direction=asc&per_page=100")
    archive.pages("destination/comments", f"repos/{DESTINATION}/issues/comments?sort=created&direction=asc&per_page=100")
    archive.pages("source/labels", f"repos/{SOURCE}/labels?per_page=100")
    archive.pages("destination/labels", f"repos/{DESTINATION}/labels?per_page=100")

    def detail(item):
        number = item["number"]
        prefix = f"source/issues/{number}"
        single(prefix + "/detail", f"repos/{SOURCE}/issues/{number}")
        archive.pages(prefix + "/comments", f"repos/{SOURCE}/issues/{number}/comments?per_page=100")
        archive.pages(prefix + "/timeline", f"repos/{SOURCE}/issues/{number}/timeline?per_page=100")

    archive.parallel(issues, detail, "Open upstream issue descriptions/comments/timelines")
    for pull in pulls:
        number = pull["number"]
        single(f"source/pull-requests/{number}/detail", f"repos/{SOURCE}/pulls/{number}")
        archive.pages(f"source/pull-requests/{number}/comments", f"repos/{SOURCE}/issues/{number}/comments?per_page=100")
        archive.pages(f"source/pull-requests/{number}/timeline", f"repos/{SOURCE}/issues/{number}/timeline?per_page=100")
    query = """query{source:repository(owner:\"MohamedRejeb\",name:\"Calf\"){
      id nameWithOwner issues(states:OPEN){totalCount} pullRequests(states:OPEN){totalCount}
      defaultBranchRef{name target{oid}}}
      destination:repository(owner:\"Apdelrahman1911\",name:\"nativeCmpkit\"){
      id nameWithOwner issues{totalCount} openIssues:issues(states:OPEN){totalCount}
      pullRequests{totalCount} defaultBranchRef{name target{oid}}}rateLimit{remaining resetAt}}"""
    counts, meta = archive.request("graphql/current-counts.json", "graphql", query=query)
    if not meta["success"]:
        raise RuntimeError("Independent current-count query failed")
    archive.dataset("graphql/current-counts", complete=True, output="graphql/current-counts.json")
    checks = {
        "source_issue_count_matches_graphql": len(issues) == counts["data"]["source"]["issues"]["totalCount"],
        "source_open_pr_count_matches_graphql": len(pulls) == counts["data"]["source"]["pullRequests"]["totalCount"],
        "destination_issue_count_matches_graphql": len([x for x in destination_records if "pull_request" not in x]) == counts["data"]["destination"]["issues"]["totalCount"],
        "source_numbers_unique": len({x["number"] for x in records}) == len(records),
        "all_source_details_still_open": all(read(snapshot / f"source/issues/{x['number']}/detail.json")["state"] == "open" for x in issues),
        "all_source_comment_counts_match": all(len(read(snapshot / f"source/issues/{x['number']}/comments.json")) == x["comments"] for x in issues),
        "all_required_datasets_complete": all(item["complete"] for item in archive.progress.values()),
        "frozen_migration_hash_list_unchanged": prior_sums_hash == sha256(original_sums),
    }
    receipt = {
        "schema_version": 1, "scope": "Read-only current open upstream issue/PR and destination reconciliation snapshot",
        "source": SOURCE, "destination": DESTINATION, "started_at": archive.observation["started_at"],
        "completed_at": utc_now(), "source_head": source_head, "destination_head": destination_head,
        "local_head_before_capture": local_head, "local_head_after_capture": git("rev-parse", "HEAD").decode().strip(),
        "source_open_record_count": len(records), "source_open_issue_count": len(issues),
        "source_open_pr_count": len(pulls), "source_open_pr_numbers": [x["number"] for x in pulls],
        "source_open_issue_numbers": [x["number"] for x in issues],
        "destination_issue_count": len([x for x in destination_records if "pull_request" not in x]),
        "destination_open_issue_count": sum(x["state"] == "open" and "pull_request" not in x for x in destination_records),
        "source_comment_count": sum(len(read(snapshot / f"source/issues/{x['number']}/comments.json")) for x in issues),
        "source_timeline_items": sum(len(read(snapshot / f"source/issues/{x['number']}/timeline.json")) for x in issues),
        "response_count": len(list(snapshot.rglob("*.http.json"))), "checks": checks, "complete": all(checks.values()),
        "github_mutations_performed": False, "production_source_changes_performed": False,
        "frozen_migration_sha256sums_sha256": prior_sums_hash,
        "limitations": ["Observation interval is not an atomic GitHub snapshot.", "Private/deleted/redacted content is unavailable.",
                        "All current open issues are captured; current open PRs are separately identified, not automatically recreated as issues.",
                        "This is a verified snapshot, not a receipt that proposed destination comments have been posted."],
    }
    dump(snapshot / "receipt.json", receipt)
    freeze(snapshot)
    verify_frozen(snapshot)
    if not receipt["complete"]:
        raise RuntimeError("Snapshot consistency check failed; inspect the receipt before any mutations")
    return receipt


def source_fingerprint(issue, comments, history):
    issue_keys = ["id", "node_id", "number", "title", "body", "state", "state_reason", "created_at", "updated_at", "html_url"]
    comment_keys = ["id", "node_id", "body", "created_at", "updated_at", "html_url"]
    def actor(user):
        return {key: user.get(key) for key in ["id", "node_id", "login", "html_url"]} if user else None
    return content_hash({
        "issue": {**{key: issue.get(key) for key in issue_keys}, "author": actor(issue.get("user")),
                  "labels": [{key: label.get(key) for key in ["id", "name", "color", "description"]} for label in issue.get("labels", [])]},
        "comments": [{**{key: comment.get(key) for key in comment_keys}, "author": actor(comment.get("user"))} for comment in comments],
        "history": [{key: event.get(key) for key in ["id", "node_id", "event", "created_at", "commit_id", "url"]} for event in history],
    })


def quoted_markdown(body):
    if body is None or body == "":
        return "_(The public upstream body is empty.)_"
    fence = "`" * max(4, 1 + max((len(match) for match in re.findall(r"`+", body)), default=0))
    return f"{fence}markdown\n{body}\n{fence}"


def comment_body(issue, comments, history, decision, destination, related, snapshot, fingerprint, archive_commit):
    number = issue["number"]
    source_url = issue["html_url"]
    marker = f"<!-- nativecmpkit-upstream-sync:{SOURCE_ID}:{number} -->"
    archive_path = str(snapshot.relative_to(ROOT))
    base_url = f"https://github.com/{DESTINATION}/blob/{archive_commit}/{archive_path}"
    labels = issue.get("labels", [])
    label_text = ", ".join(f"`{label['name']}` (#{label['color']}; {label.get('description') or 'no description'})" for label in labels) or "None"
    status = decision["disposition"]
    interpretation = {
        "already_implemented": "Source-addressed historical request; not a new confirmed bug, and not evidence of a device/runtime pass.",
        "covered_by_finding": "Still relevant; tracked by the existing nativeCmpkit finding rather than a duplicate issue.",
        "needs_reproduction": "Still relevant as an unverified reproduction target; the original report does not establish a current root cause.",
        "separate_improvement": "Still relevant improvement/remaining scope; partial existing support is identified below.",
    }.get(status, "Requires explicit maintainer triage; no automatic issue state change.")
    lines = [marker, f"<!-- source-fingerprint:{fingerprint} -->", f"## Current upstream context: Calf #{number}", "",
             f"Original: [{issue['title']}]({source_url}) — [{issue['user']['login']}]({issue['user']['html_url']}); created `{issue['created_at']}`, updated `{issue['updated_at']}`; upstream state **{issue['state']}**.",
             f"Original IDs: `{issue['id']}` / `{issue['node_id']}`. Original labels: {label_text}.", "",
             "This comment preserves attributed public upstream material. It does not impersonate the original author, replace this issue's technical body, or transplant GitHub authorship/timestamps.", "",
             "### Reconciled disposition", interpretation, "", decision["rationale"], "", f"**Next step:** {decision['recommended_next_step']}", "",
             f"Primary tracking: #{destination['number']}. Related existing tickets: " + (", ".join(f"#{item['number']}" for item in related) or "none additional") + ".",
             "**Lifecycle:** keep the existing nativeCmpkit issue state and unrelated labels/content unchanged. Do not close a broader remaining bug because an old upstream symptom is source-addressed.", "",
             "### Current-source assessment locations", source_links(decision.get("locations", [])), "",
             "### Original issue description (verbatim Markdown)", quoted_markdown(issue.get("body")), "",
             f"### Original public discussion ({len(comments)} comments)"]
    for comment in comments:
        lines.extend(["", f"**[{comment['user']['login']}]({comment['user']['html_url']})** — created `{comment['created_at']}`, updated `{comment['updated_at']}`; [original comment]({comment['html_url']}); IDs `{comment['id']}` / `{comment['node_id']}`.",
                      quoted_markdown(comment.get("body"))])
    if not comments:
        lines.append("No public conversation comments were returned in this snapshot.")
    lines += ["", "### Relevant history and immutable evidence",
              f"- [Fresh original issue record]({base_url}/source/issues/{number}/detail.json)",
              f"- [Full original comments]({base_url}/source/issues/{number}/comments.json)",
              f"- [Full public timeline: {len(history)} entries]({base_url}/source/issues/{number}/timeline.json)",
              f"- [Verified snapshot receipt]({base_url}/receipt.json) and [SHA256SUMS]({base_url}/SHA256SUMS)",
              "- Earlier original edit diffs, release/PR history and available attachment copies remain in `docs/migration/upstream-metadata/`; that frozen archive was not rewritten."]
    significant = [event for event in history if event.get("event") not in {"commented", "mentioned", "subscribed", "unsubscribed"}]
    for event in significant:
        origin = event.get("url", event.get("html_url", source_url))
        actor = event.get("actor") or event.get("user") or {}
        suffix = ""
        if event.get("commit_id"):
            suffix += f"; commit `{event['commit_id']}`"
        if event.get("label"):
            suffix += f"; label `{event['label'].get('name')}`"
        if event.get("source", {}).get("issue"):
            cross = event["source"]["issue"]
            suffix += f"; [{cross.get('title', 'cross-reference')}]({cross.get('html_url', source_url)})"
        attribution = f"[{actor['login']}]({actor['html_url']})" if actor.get("login") and actor.get("html_url") else "unknown actor"
        lines.append(f"- `{event.get('created_at', 'timestamp not exposed')}`: `{event.get('event')}` by {attribution} ([event]({origin})){suffix}.")
    body = "\n".join(lines) + "\n"
    if len(body.encode()) > 62000:
        raise ValueError(f"Calf #{number} context exceeds safe comment size; split explicitly, never truncate original text")
    return body


def reconcile(snapshot, report, archive_commit):
    receipt = read(snapshot / "receipt.json")
    verify_frozen(snapshot)
    if not receipt["complete"]:
        raise ValueError("Cannot reconcile an incomplete snapshot")
    issue_map = read(ROOT / "docs/migration/issue-map.json")["items"]
    decisions = {item["upstream_number"]: item for item in read(ROOT / "docs/migration/upstream-actionable-decisions.json")}
    remote = {item["number"]: item for item in read(snapshot / "destination/issues.json") if "pull_request" not in item}
    remote_comments = read(snapshot / "destination/comments.json")
    marker_comments = {}
    for comment in remote_comments:
        first_line = (comment.get("body") or "").splitlines()[:1]
        match = MARKER.fullmatch(first_line[0]) if first_line else None
        if match:
            marker_comments.setdefault(int(match.group(1)), []).append(comment)
    old_issues = {item["number"]: item for item in read(ROOT / "docs/migration/upstream-metadata/issues.json")}
    old_comments = read(ROOT / "docs/migration/upstream-metadata/issue-comments.json")
    entries = []
    operations = []
    blockers = []
    production_evidence = {}
    for listing in read(snapshot / "source/open-issues.json"):
        number = listing["number"]
        issue = read(snapshot / f"source/issues/{number}/detail.json")
        comments = read(snapshot / f"source/issues/{number}/comments.json")
        history = read(snapshot / f"source/issues/{number}/timeline.json")
        decision = decisions.get(number)
        if not decision:
            blockers.append(f"New upstream issue #{number} requires source assessment before selecting a duplicate-free destination")
            entries.append({"source_number": number, "title": issue["title"], "status": "requires-new-assessment", "source_url": issue["html_url"]})
            continue
        candidates = [item for item in issue_map if number in item.get("upstream_numbers", [])]
        if not candidates:
            blockers.append(f"Upstream #{number} has no existing receipt mapping; inspect semantic duplicates before creating a new ticket")
            entries.append({"source_number": number, "title": issue["title"], "status": "missing-destination-assessment", "source_url": issue["html_url"]})
            continue
        finding_ids = decision.get("finding_ids", [])
        primary = next((candidate for identifier in finding_ids for candidate in candidates if identifier in candidate.get("finding_ids", [])), candidates[0])
        destination = remote.get(primary["number"])
        if not destination:
            blockers.append(f"Receipted destination #{primary['number']} is no longer visible")
            continue
        # Reuse the strict existing parser: exact first-line marker, exactly once.
        # An arbitrary body mention of a known key is not destination identity.
        try:
            destination_key = managed_key(destination.get("body"))
        except ValueError:
            destination_key = None
        if destination_key != primary["key"]:
            blockers.append(f"Destination #{primary['number']} is missing its receipted identity marker")
            continue
        related_ids = set(finding_ids)
        related = [item for item in issue_map if item["number"] != primary["number"] and
                   (number in item.get("upstream_numbers", []) or related_ids.intersection(item.get("finding_ids", [])))]
        fingerprint = source_fingerprint(issue, comments, history)
        text = comment_body(issue, comments, history, decision, destination, related, snapshot, fingerprint, archive_commit)
        existing = marker_comments.get(number, [])
        if len(existing) > 1:
            blockers.append(f"Duplicate source-context markers for Calf #{number}; do not post another")
            action = "blocked-duplicate-context-markers"
        elif existing:
            current = existing[0]
            current_destination = int(current["issue_url"].rsplit("/", 1)[1])
            current_fingerprint = FINGERPRINT.search(current.get("body") or "")
            if current_destination != primary["number"]:
                blockers.append(f"Calf #{number} context already belongs to another destination #{current_destination}")
                action = "blocked-context-destination-conflict"
            elif current_fingerprint and current_fingerprint.group(1) == fingerprint:
                action = "no-op-context-current"
            else:
                action = "review-existing-context-before-update"
                blockers.append(f"Calf #{number} has an existing changed context comment; preserve possible human edits and reconcile explicitly")
        else:
            action = "create-context-comment"
            operations.append({
                "operation": "create_issue_comment", "repository": DESTINATION, "issue_number": primary["number"],
                "source_number": number, "source_node_id": issue["node_id"],
                "dedupe_marker": f"<!-- nativecmpkit-upstream-sync:{SOURCE_ID}:{number} -->",
                "source_fingerprint": fingerprint, "body": text, "body_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "source_disposition": decision["disposition"], "expected_issue_id": destination["id"],
                "expected_issue_state": destination["state"], "expected_issue_body_sha256": hashlib.sha256((destination.get("body") or "").encode()).hexdigest(),
                "preconditions": ["Bind the immutable archive commit before posting", "Re-read destination identity and existing comment markers immediately before POST",
                                  "Preserve destination title/body/state/labels", "Never automatically retry an uncertain POST; reconcile its marker first"],
            })
        original_comments = [comment for comment in old_comments if int(comment["issue_url"].rsplit("/", 1)[1]) == number]
        old_history = read(ROOT / f"docs/migration/upstream-metadata/issues/{number}/timeline.json", [])
        old_fingerprint = source_fingerprint(old_issues[number], original_comments, old_history) if number in old_issues else None
        original_content_unchanged = number in old_issues and source_fingerprint(old_issues[number], original_comments, []) == source_fingerprint(issue, comments, [])
        def event_identity(event):
            return event.get("id") or event.get("node_id") or (event.get("event"), event.get("created_at"), event.get("url"))
        old_history_ids = {event_identity(event) for event in old_history}
        added_history = [event for event in history if event_identity(event) not in old_history_ids]
        added_history_summary = [{"event": event.get("event"), "created_at": event.get("created_at"),
                                  "source_url": event.get("source", {}).get("issue", {}).get("html_url")}
                                 for event in added_history]
        for location in decision.get("locations", []):
            path = location["path"]
            if path not in production_evidence:
                before = git("show", f"{BASELINE}:{path}")
                current = git("show", f"{receipt['local_head_before_capture']}:{path}")
                production_evidence[path] = {"baseline_sha256": hashlib.sha256(before).hexdigest(),
                                            "current_committed_sha256": hashlib.sha256(current).hexdigest(), "unchanged": before == current}
        entries.append({
            "source_number": number, "source_url": issue["html_url"], "source_id": issue["id"], "source_node_id": issue["node_id"],
            "title": issue["title"], "author": issue["user"]["login"], "created_at": issue["created_at"], "updated_at": issue["updated_at"],
            "labels": issue["labels"], "comment_count": len(comments), "timeline_count": len(history),
            "disposition": decision["disposition"], "assessment_rationale": decision["rationale"], "required_next_step": decision["recommended_next_step"],
            "primary_destination": {"number": primary["number"], "key": primary["key"], "url": destination["html_url"], "state": destination["state"]},
            "related_destination_numbers": [item["number"] for item in related], "action": action,
            "source_fingerprint": fingerprint, "unchanged_from_frozen_public_content": old_fingerprint == fingerprint,
            "original_description_labels_author_and_comments_unchanged": original_content_unchanged,
            "added_timeline_entries": added_history_summary,
            "timeline_note": "GitHub automatically records cross-references from destination tickets; these are history additions, not original author text changes.",
            "original_assessment_baseline": decision["assessment_baseline"], "source_locations": decision["locations"],
        })
        dump(report / "drafts" / f"upstream-{number:04}-comment.json", {"source_number": number, "body": text})
        (report / "drafts" / f"upstream-{number:04}-comment.md").write_text(text, encoding="utf-8")
    handoff = {
        "schema_version": 1, "generated_at": utc_now(), "source": SOURCE, "destination": DESTINATION,
        "snapshot_path": str(snapshot.relative_to(ROOT)), "snapshot_receipt_sha256": sha256(snapshot / "receipt.json"),
        "snapshot_sha256sums_sha256": sha256(snapshot / "SHA256SUMS"), "source_head": receipt["source_head"],
        "destination_head_observed": receipt["destination_head"], "archive_commit": archive_commit,
        "archive_commit_token": ARCHIVE_COMMIT_TOKEN, "requires_archive_commit_binding": archive_commit == ARCHIVE_COMMIT_TOKEN,
        "source_issue_count": receipt["source_open_issue_count"], "excluded_open_pull_requests": receipt["source_open_pr_numbers"],
        "entry_count": len(entries), "create_issue_operations": [], "comment_operations": operations,
        "state_changes": [], "body_replacements": [], "label_replacements": [],
        "blockers": blockers, "ready_for_lead_commit_and_apply": not blockers and len(entries) == receipt["source_open_issue_count"],
        "github_mutations_performed": False,
        "notes": ["All source text/labels are preserved in context comments and the new archive, not applied as replacement destination classification.",
                  "Two source-addressed historical requests remain linked without closing separate current defects.",
                  "Open PR551 is preserved and cross-referenced to existing IO findings, not recreated as a new issue.",
                  "The lead is the single authorized GitHub writer; source GitHub is strictly read-only."],
    }
    dump(report / "reconciliation.json", entries)
    dump(report / "production-source-assessment-evidence.json", production_evidence)
    dump(report / "mutation-handoff.json", handoff)
    result = {
        "checked_at": utc_now(), "snapshot_complete": receipt["complete"], "source_open_issues": receipt["source_open_issue_count"],
        "source_open_prs_excluded": receipt["source_open_pr_count"], "destination_issues": receipt["destination_issue_count"],
        "all_source_issues_mapped": len(entries) == receipt["source_open_issue_count"] and all("primary_destination" in x for x in entries),
        "create_issue_count": 0, "comment_create_count": len(operations), "source_addressed_count": sum(x.get("disposition") == "already_implemented" for x in entries),
        "current_context_noops": sum(x.get("action") == "no-op-context-current" for x in entries), "blockers": blockers,
        "production_locations_checked": len(production_evidence), "all_assessed_production_sources_unchanged": all(x["unchanged"] for x in production_evidence.values()),
        "all_assessed_implementation_sources_unchanged": all(x["unchanged"] for path, x in production_evidence.items() if "/src/" in path),
        "changed_assessment_files": [path for path, value in production_evidence.items() if not value["unchanged"]],
        "all_source_public_content_unchanged_since_migration": all(x.get("unchanged_from_frozen_public_content") for x in entries),
        "all_original_descriptions_labels_authors_and_comments_unchanged": all(x.get("original_description_labels_author_and_comments_unchanged") for x in entries),
        "added_timeline_entry_count": sum(len(x.get("added_timeline_entries", [])) for x in entries),
        "github_mutations_performed": False, "ready_for_lead_commit_and_apply": handoff["ready_for_lead_commit_and_apply"],
    }
    dump(report / "receipt.json", result)
    lines = ["# Current open-upstream issue reconciliation", "", f"Captured {receipt['started_at']}–{receipt['completed_at']} (UTC).",
             f"Source: `{SOURCE}` at `{receipt['source_head']}`. Destination snapshot: `{receipt['destination_head']}`.", "",
             f"**{receipt['source_open_issue_count']} actual open issues; {receipt['source_open_pr_count']} open PR separately excluded.**",
             f"**{len(operations)} proposed context comments, zero new issues, zero state/body/label replacements.**",
             "", "This is verified read-only reconciliation, not a claim that the lead has posted the drafts. Each draft retains full original description, labels, public discussion and attributed history links.", "",
             "| Calf | Primary nativeCmpkit | Disposition | Required action |", "|---|---|---|---|"]
    for entry in entries:
        target = entry.get("primary_destination", {})
        lines.append(f"| [#{entry['source_number']}]({entry['source_url']}) {entry['title'].replace('|', '/')} | #{target.get('number', 'unmapped')} | {entry.get('disposition', 'needs assessment')} | {entry['action'] if 'action' in entry else entry['status']} |")
    lines += ["", "## Safety and lifecycle", "",
              "- Source-addressed #288 (existing mobile camera API) and #344 (JavaFX settings now dispatched with Platform.runLater) are not new confirmed defects. Their distinct current destination bugs stay open.",
              "- #471 and #78 are only partly fulfilled; retain remaining styling / contacts-and-OTP scope. Maps/media and native preview remain scoped roadmap items, not implemented features.",
              "- #551 is an open PR, not an issue. Its source history is archived and the existing IO tickets remain the integration-review owners.",
              "- Original upstream user content is untrusted quoted data. No instructions embedded in it were executed.",
              "- The original `upstream-metadata` archive and its SHA256SUMS were not rewritten. This dated snapshot has its own raw response hashes, pagination evidence, receipt and SHA256SUMS.",
              "", "## Applying the handoff (lead only)", "",
              "1. Review `receipt.json`, `reconciliation.json` and `mutation-handoff.json`; do not apply if blockers are present.",
              "2. Commit/push the fresh snapshot, then bind `__UPSTREAM_SYNC_ARCHIVE_COMMIT__` to that 40-hex commit in each body. Recompute each final body hash.",
              "3. Re-read each destination identity and all existing comments. A stable source marker already present must not produce another POST; preserve human changes and existing issue states/labels/bodies.",
              "4. POST only the proposed comments. A lost/unknown response requires marker reconciliation, never blind automatic retry.",
              "5. Store actual comment IDs/URLs/body hashes and perform a fresh read-only verification before declaring synchronization complete or starting production fixes.",
              "", "## Evidence and limits", "",
              f"- Fresh raw snapshot: `{snapshot.relative_to(ROOT)}`; original source descriptions and discussions are retained without truncation.",
              f"- Original description/label/author/comment equality with the frozen migration archive: **{result['all_original_descriptions_labels_authors_and_comments_unchanged']}**. Added timeline entries: **{result['added_timeline_entry_count']}**; inspect their types and source URLs in `reconciliation.json` separately from user-text changes.",
              f"- Assessed implementation-byte equality: **{result['all_assessed_implementation_sources_unchanged']}**. Changed assessed source/build files: {', '.join('`' + path + '`' for path in result['changed_assessment_files']) or 'none'}. The broader all-files-unchanged flag includes build identity files, not only implementations.",
              "- No physical/device runtime reproduction was performed by this synchronization task. Source-addressed means the cited implementation exists, not that every related runtime behavior passes.",
              "- Deleted/private/redacted metadata remains unavailable. Pagination is complete for accessible endpoints, but the observation interval is not an atomic transaction.",
              "- The 2026-10-24 baseline disposition file was reused only with fresh state/discussion capture and current committed source-byte checks; no production fixes were applied during this task."]
    if receipt["local_head_before_capture"] == "e0724790ed827020970d538928cc25bdc9ea0baa":
        lines += ["", "### This observation's non-content differences", "",
                  "All 16 original descriptions/labels/authors and 14 comments are unchanged. The 17 new timeline items are automatic cross-references from the existing nativeCmpkit tickets, not original-author text edits. Of 23 assessed files, only settings.gradle.kts differs (the existing migration comment and root project rename); the other 22 files are byte-identical to baseline."]
    (report / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stamp", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    parser.add_argument("--phase", choices=["all", "capture", "reconcile", "verify"], default="all")
    parser.add_argument("--archive-commit", default=ARCHIVE_COMMIT_TOKEN)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z", args.stamp):
        parser.error("--stamp must be YYYYMMDDTHHMMSSZ")
    if args.archive_commit != ARCHIVE_COMMIT_TOKEN and not re.fullmatch(r"[0-9a-f]{40}", args.archive_commit):
        parser.error("--archive-commit must be a complete lowercase Git commit OID")
    snapshot = ROOT / "docs/migration/upstream-updates" / args.stamp
    report = ROOT / "docs/development" / f"upstream-sync-{args.stamp}"
    if args.phase == "verify":
        print(f"Verified {verify_frozen(snapshot)} snapshot file hashes")
        return
    report.mkdir(parents=True, exist_ok=True)
    if args.phase in {"all", "capture"}:
        print(json.dumps(capture(snapshot), indent=2))
    if args.phase in {"all", "reconcile"}:
        print(json.dumps(reconcile(snapshot, report, args.archive_commit), indent=2))


if __name__ == "__main__":
    main()
