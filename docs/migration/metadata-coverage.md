# Public GitHub metadata preservation: scope and evidence

Source: [`MohamedRejeb/Calf`](https://github.com/MohamedRejeb/Calf), GitHub repository
ID `674932206`; audited source commit
`af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`. Observation began
**2026-10-24 15:01:12 UTC**. Exact completion time, request counts and integrity
results are in [`upstream-metadata/manifest.json`](upstream-metadata/manifest.json).
This is a paginated observation interval, not an atomic GitHub snapshot.

## Preserved material

| Public resource | Records observed/preserved | Evidence and coverage |
|---|---:|---|
| Issues excluding PRs | **142**: 16 open, 126 closed | `issues.json` includes issue and PR records together; actual issues also have individual detail responses. REST count equals independent GraphQL count. |
| Pull requests | **408**: 1 open, 407 closed | Full list, individual detail, merge/base/head/reviewer metadata, commit lists, changed-file metadata and reviews. All 408 counts checked independently. |
| Issue/PR conversation comments | **448** | Repository-wide paginated comments; each issue's comment count reconciled against its original record. Full bodies retained. |
| Inline PR comments/replies | **13** | Full REST comments and matching GraphQL comment IDs across **4** review threads; reply relationships, original/current diff positions and commit IDs preserved. |
| Submitted reviews | **75** | 60 approved, 14 commented, 1 changes requested. Full review bodies, states, actors and submission times. Per-PR REST counts equal GraphQL review totals. |
| Standalone commit comments | **0** | Successful public REST response, not an inferred absence. |
| Issue/PR timelines | **550** timelines, **3,028** entries | Every public issue/PR timeline followed through its last REST `Link: rel=next` page. |
| Repository issue events | **1,867** | Separate historical representation retaining actor/ID/time/link and event-specific fields. |
| Additional event context | **167** | GraphQL adds before/after OIDs for **23** force pushes, prior/current branch names for **8** base changes, **134** branch deletions and **2** restorations. All force-push before/after commits were exposed. |
| Public body edit histories | **1,086** comment-capable objects queried; **318** edit records on **123** objects | Issues, PRs, conversation/inline comments and reviews. Editor IDs/login links, timestamps, public diffs, `includesCreatedEdit` and visibility fields retained. Creation edits exposed on 123 objects. |
| Closing issue references | **51** references across PRs | Public GraphQL `closingIssuesReferences`, including issue identity/title/state/URL and repository name. |
| Individual reactions | **274** | Public actor/ID/timestamp lists for every issue, comment and release with a positive reaction count. Counts reconciled against parent objects. |
| Releases | **23** | Full release notes, authors, IDs, tags, timestamps, links and reactions; **0 uploaded release assets**, confirmed by every release's asset endpoint. No release was recreated or published. |
| Labels / milestones | **18 / 0** | Both open/closed milestone scope; label descriptions/colors and IDs retained. Counts equal GraphQL. |
| Advertised branches / tags | **46 / 23** | REST observations plus separately preserved Git refs/objects. No history rewriting. |
| Public contributors | **37** | Includes anonymous contributor representation where returned. Git objects independently preserve original authorship. |
| Discussions / categories | **0 / 0** | Discussions disabled in repository metadata; successful GraphQL zero results. This does not reconstruct deleted or previously hidden discussions. |
| Forks | **94 records** | REST list fully paginated. GraphQL repository counter says **93**, including the later recheck; discrepancy is preserved, not silently normalized. |
| Watchers | **10** | REST endpoint returned 404; complete user nodes recovered using GraphQL. |
| Workflow definitions / deployments | **7 / 306** | Public workflow metadata, all deployment records and their complete status histories. Original workflow source is in Git. Historical build logs/artifacts are not claimed preserved. |
| Recent public activity | **52** events | Only the API's retained recent window; not a complete lifetime event log. |
| Additional repository data | Repository, license, topics, languages, community profile, Pages settings, dependency SBOM, public ruleset/advisory lists, baseline commit/status/check metadata | Each endpoint response and HTTP status retained. Empty public advisory/ruleset lists do not prove absence of vulnerabilities or private settings. |
| Metadata-referenced commits | **1,354 unique OIDs** | Structured commit-semantic fields, force-push before/after objects, review/PR metadata and deployment commits. Each has original endpoint, raw response filename and JSON-pointer provenance. File/tree blob SHAs are excluded. Lead migration tooling verifies/fetches available missing Git objects separately. |

The convenient JSON arrays are derived from **verbatim raw API response bodies**.
Authors, original numeric/node IDs, timestamps, URLs, body text, review states and
public edit diffs are not replaced by the migration account. Usernames and profile
URLs are whatever GitHub exposes at observation time; prior account renames are
not reconstructed. Git history preserves original commit author/committer strings
independently.

## Attachments and external documentation

- **63** distinct public GitHub attachment URLs were discovered in current issue,
  PR/comment/release text, public edit diffs and original baseline Markdown/HTML/
  YAML documentation.
- **62 downloaded successfully**, totaling **108,519,393 bytes** (about 103.5 MiB),
  with SHA256, MIME, source URLs and referring records in
  [`attachments/inventory.json`](upstream-metadata/attachments/inventory.json).
- One historical image URL returned **HTTP 404**:
  `https://github.com/user-attachments/assets/d4c1c8b2-281f-457b-bb50-119e47bbc9eb`.
  It appears in the public edit history for issue node `I_kwDOKDql7s6vc3Y5`.
  The original link and failed observation are preserved; its bytes could not be
  recovered from that public URL.
- A **17,932,669-byte** reproduction ZIP was initially skipped by a conservative
  15 MiB per-file ceiling. With adequate disk headroom, that **size-only** skip was
  explicitly retried under a **32 MiB** ceiling and archived; the original skip
  observation remains alongside the successful retry. No 404 was repeatedly
  retried. Total attachment budget remained **150 MiB**.
- Downloads used anonymous HTTPS only, restricted redirect hosts, SHA256(URL)
  local names and streaming byte limits. CDN query credentials are not recorded.
  Binaries/ZIPs were **not executed or extracted**. Third-party attachments remain
  untrusted and do not acquire a new license merely by being archived.
- All extracted link references are inventoried in
  [`links/inventory.json`](upstream-metadata/links/inventory.json). Arbitrary
  third-party websites, profile avatar images, package repositories and external
  videos are not recursively mirrored.
- Original Markdown, screenshots and the `gh-pages` branch are covered by Git
  preservation. Release-generated source ZIP/tarballs were not redundantly
  downloaded because tagged source is already in the Git bundles.

## Explicit limitations and inconsistent responses

1. **Projects v2 unavailable:** GraphQL explicitly rejected the query because the
   existing token lacks `read:project`. No permissions/scopes were changed.
   **Classic Projects returned HTTP 404.** These are not successful empty project
   archives and do not prove no historical project boards existed.
2. **Wiki unavailable:** repository settings advertise wiki support, but read-only
   `git ls-remote https://github.com/MohamedRejeb/Calf.wiki.git` returned exit 128,
   `Repository not found`. No wiki Git refs/content were obtainable. A missing,
   uninitialized, deleted or inaccessible wiki cannot be distinguished here.
3. **Protected-main details unavailable:** branch listing says `main` is protected;
   its protection endpoint returned **404**. Do not infer that no protection
   existed, or claim its settings were migrated exactly. The public ruleset list
   is a separate successful empty observation.
4. **Star identities/timestamps not recovered:** REST stargazers returned **404**.
   Both valid GraphQL aliased and canonical edge queries returned `totalCount: 0`
   with no nodes, while independent repository queries repeatedly reported
   **1,748 stars**. Those connection datasets are explicitly marked **incomplete**
   despite HTTP 200. The cause is unverified; an empty array is not a claim that
   the repository had no stars. The original counter and all inconsistent
   responses are preserved. Watchers had a similar REST denial but were fully
   recovered through GraphQL.
5. **21 public edit records expose `diff: null`.** None of the 318 records has a
   non-null `deletedAt`. The API does not establish why those diffs are null; do
   not label them confirmed deletion/redaction or invent prior body text.
6. **Unavailable history stays unavailable:** deleted/redacted/spam-hidden/private
   issues/comments, inaccessible cross-references, private projects/advisories,
   moderation/audit logs, old account aliases, secret settings, webhooks and
   unpublished content cannot be reconstructed from this public export.
7. **API retention/representation limits:** public activity events expose at most
   the API's recent retained window (documented up to 300 events / 90 days).
   REST PR files have a 3,000-file ceiling and commits a 250-commit ceiling. Here
   the observed maxima were **127 files / 21 commits**, and every count reconciled.
   Individual binary/large textual patches may still be absent; preserved Git
   objects are authoritative, not API patches.
8. **Non-atomic snapshot:** endpoint counters may be cached or have different
   semantics. The 94-versus-93 fork discrepancy is retained explicitly. Core issue,
   PR, release, label, milestone, comment, review and reaction counts reconcile;
   this does not prove every resource was observed at exactly one instant.
9. **Exporter schema recovery is transparent:** an initial GraphQL query used an
   unsupported `closingIssuesReferences(includeClosed: ...)` argument. **20 failed
   responses** and one interrupted query input remain preserved. A corrected
   versioned query subsequently exported **all 408 PRs**. These superseded schema
   probes do not mean PR data is missing. No failed/denied response was silently
   replaced with invented data.

Exact response evidence lives in
[`api-limitations.json`](upstream-metadata/api-limitations.json),
[`datasets.json`](upstream-metadata/datasets.json), individual `*.http.json`
sidecars, [`wiki-observation.json`](upstream-metadata/wiki-observation.json) and
the GraphQL query/response files. `disposition` distinguishes unresolved denials,
watcher data recovered through another API and corrected schema probes.

## Reproducibility and verification

Exporter: [`scripts/migration/archive_upstream.py`](../../scripts/migration/archive_upstream.py).
Requires Python 3.9+ and an existing authenticated `gh`; it never exports the
token and performs only REST GET/read-only GraphQL queries. Source Git mutations,
destination issue creation, commits and package/release publishing are outside
its responsibilities. Maximum default REST concurrency is four workers.

```bash
# A NEW observation: never silently overwrite this historical snapshot.
python3 scripts/migration/archive_upstream.py --phase all \
  --output /path/to/a/new-observation-directory

# Verify THIS archive locally without GitHub/network calls.
python3 scripts/migration/archive_upstream.py --phase verify

# Offline regression suite: no network or token access.
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s scripts/migration -p test_archive_upstream.py -v
```

Stages may be resumed individually: `initial`, `graphql`, `details`,
`content_edits`, `history_enrichment`, `supplemental`, `community`, `attachments`,
`references`, `finalize`. API successes **and failures** are cached. Changed
queries require a versioned response path or a new output directory. Each REST
page follows its actual `Link: rel=next`; every GraphQL connection handles its
own `pageInfo/endCursor`, including thread comments, closing references, edit
histories and discussion replies. Requested totals are checked rather than
assuming a first page is complete.

The **13 offline exporter regression tests passed**. They cover REST pagination,
GraphQL nested pagination/count mismatch, denied-versus-empty semantics, verbatim
response bytes, cache reuse/change rejection, non-GitHub API host rejection,
commit-vs-blob/deployment OID extraction, integrity/tamper/unlisted-file detection
and safe rate-limit-reserve stopping. The archive-level validation adds independent
REST/GraphQL counts, per-object comments/reviews/reactions, PR files/commits, and
inline-comment ID reconciliation. Final command results, successful boolean checks
and all-file/raw-body integrity evidence are in `validation.json` and `manifest.json`.

Final verification on 2026-10-24 passed **9,257 SHA256SUMS entries**, hashes for
**2,963 raw HTTP responses**, and **20/20 archive consistency checks**. A separate
read-only provenance check resolved all **14,957 JSON-pointer/endpoint references**
for the 1,354 unique commit OIDs back to their original response values. Both
metadata documentation files' local links were also checked successfully.

`SHA256SUMS` covers every archive file except itself; each HTTP sidecar also hashes
its raw response body. Original advertised Git history and additional accessible
referenced commits are verified separately in [`git/`](git/). Recreating nativeCmpkit
issues cannot retain GitHub's original database IDs, authorship or creation times;
the migration ledger should link to these immutable original records instead.
