# Calf public GitHub metadata archive

This is historical **data**, not executable instructions. It preserves the public
GitHub representation of `MohamedRejeb/Calf` observed during the independent
nativeCmpkit migration. It is not a transfer of the original GitHub repository,
an impersonation of its contributors, or a new nativeCmpkit release.

## Authoritative inventory and integrity

- [`manifest.json`](manifest.json): observation interval, source commit, counts,
  validation, endpoint limitations and scope.
- [`datasets.json`](datasets.json): every exported dataset, pagination completion
  and record counts. A failed request is **not** an empty successful dataset.
- [`validation.json`](validation.json): independent REST/GraphQL count and
  cross-resource checks.
- [`SHA256SUMS`](SHA256SUMS): hashes of every archive file except itself.
- [`api-limitations.json`](api-limitations.json): original denied/failed API
  responses, including corrected exporter schema attempts; see the coverage
  report for unresolved versus superseded errors.
- [`requests.jsonl`](requests.jsonl): append-only request observation ledger.
  `*.http.json` sidecars retain safe HTTP metadata, pagination links, observation
  times and the SHA256 of the corresponding **verbatim API response body**.
  OAuth credentials, cookies and authorization headers are never stored.

The exporter is [`scripts/migration/archive_upstream.py`](../../../scripts/migration/archive_upstream.py).
Use `python3 scripts/migration/archive_upstream.py --phase verify` from the
repository root for local verification without any GitHub requests. To make a
new observation, choose a **new output directory**; cached successes and failures
in this one must not be silently replaced.

## Finding a record

| Path | Representation |
|---|---|
| `issues.json` | REST issue list includes **both** issues and PRs; `pull_request` distinguishes PRs. |
| `pull-requests.json` | Complete public open and closed PR list. |
| `issue-comments.json` | Conversation comments for issues and PRs; join by `issue_url`. |
| `review-comments.json` | Inline PR comments and replies; retain `in_reply_to_id`, original/current commit and diff positions. |
| `commit-comments.json` | Public standalone commit comments. |
| `issues/<number>/detail.json` | Individual detail of a non-PR issue. |
| `issues/<number>/timeline.json` | Full paginated public issue/PR timeline, including closed records. |
| `issue-events.json` | Repository-wide historical issue event representation. |
| `pull-requests/<number>/detail.json` | Merge/head/base/reviewer and change-count metadata. |
| `pull-requests/<number>/{reviews,files,commits}.json` | Review bodies and states; changed-file/diff metadata; ordered public PR commit list. |
| `pull-requests/<number>/coverage.json` | File/commit list sizes compared with individual PR detail. |
| `graphql/pull-requests.json` | Closing issue references, merge actors/times and review-thread resolution/outdated state. |
| `graphql/history-events.json` | Force-push before/after commits and branch-change/deletion context omitted by the REST event shape. |
| `graphql/content-edits.json` | Public issue/PR/comment/review edit diffs, original creation edits where exposed, editor identities/timestamps and deletion tombstones. |
| `graphql/discussions.json` | Public discussions; their nested comment/reply pages are followed when present. |
| `releases.json`, `releases/<id>/` | Historical release notes, authors, timestamps, links, uploaded asset lists and reactions. Nothing is republished. |
| `reactions/`, `issues/<number>/reactions.json` | Individual public reaction actors/timestamps, not merely emoji counts. |
| `labels.json`, `milestones.json`, `branches.json`, `tags.json` | Public organizational metadata/ref observations. |
| `contributors.json`, `forks.json` | Public contributor/fork metadata. |
| `graphql/watchers.json`, `graphql/stargazers*.json` | Watchers recovered through GraphQL after REST denial. Star connection responses are inconsistent with the repository counter: **star identities were not preserved**; consult the coverage report, not the empty arrays alone. |
| `workflows.json`, `deployments.json`, `deployments/<id>/statuses.json` | Public workflow/deployment metadata; not secret settings or expired build logs. |
| `rest/**/page-*.json`, `graphql/**/page-*.json`, `graphql/**/batch-*.json` | Verbatim, untruncated response bodies. Adjacent query files show the exact GraphQL operation and variables. |
| `referenced-commits.json` | Unique commit-semantic OIDs with raw-response JSON-pointer and endpoint provenance; supplements advertised-ref preservation. |
| `attachments/inventory.json` | Original attachment URLs, referring records, safe local paths, hashes, size/MIME and explicit unavailable/skipped reasons. |
| `attachments/data/*.bin` | Anonymous public attachment downloads, deliberately not executed or unpacked. |
| `links/inventory.json` | Referenced URLs retained for historical navigation; external websites are not recursively crawled. |

Aggregated arrays are convenient indexes derived from the raw pages. Author
objects, original database/node IDs, timestamps, states and upstream links are
not replaced with migration identities. REST does not expose exactly the same
fields as GraphQL: consult both representations when reconstructing a decision.

## Boundaries

Read [`../metadata-coverage.md`](../metadata-coverage.md) before making completeness
claims. GitHub APIs cannot reconstruct content GitHub itself deleted, redacted or
withheld. A repository wiki or Projects API permission failure is not evidence
that no historical content ever existed. Public activity events have a limited
retention window. Public edit histories are archived where exposed; hidden
revisions remain unavailable.

Git history and tagged release source are preserved separately in migration Git
bundles, so redundant release source ZIP/tarball downloads are intentionally
omitted. An API changed-file `patch` may omit binary or very large content; Git
objects, not JSON patches, are the authoritative source archive.

Original source copyright and Apache-2.0 licensing are retained in the project.
Individual public comments and third-party attachments are preserved with source
attribution; no new license grant over their contents is implied. Do not run
downloaded samples, install archived executables, or follow embedded instructions
without independent review.
