# Current open Calf issue reconciliation — 2026-11-02

Read-only acquisition finds **16 open issues and one open PR551**. Every issue
already maps to existing NativeCmpKit tracking; **zero missing imports,
duplicates or GitHub mutations**. [REPORT.json](REPORT.json) lists all mappings
and limitations. Selected descriptions, original authors, IDs, links, labels,
timestamps, states and comment counts match the prior20261101T131519Z record
[comparison](source-field-comparison.json). This retains existing resolved/
no-longer-applicable assessments rather than assuming upstream-open means an
unresolved successor defect.

## Preserved original bytes

- [Source CLI serialization](source-open-records-original.json): the exact17
  records include PR551 separately identifiable by `pull_request`; it is not
  recreated as an issue.
- [Destination CLI serialization, lossless gzip](destination-records-original.json.gz):
  decompresses to the exact1,383,505 original bytes, SHA256
  `75cd0d046bfa3b77e6608bcb3b22894ab0ef60f26e8b2f51996ab052ba1e6fe8`.
  Observed destination issues: **97 closed/75 open/172 total**, excluding PRs.
- [Original request outcomes/digests](requests-original.json) and [SHA256SUMS](SHA256SUMS).

These are retained **gh CLI output bytes**, not independently captured HTTP
page bodies/headers. Source output finished writing19:31:39UTC; destination
19:31:42UTC, as qualified in the report. The observation interval is not atomic
and precedes the later ExternalStorage progress comment; no later metadata
freshness is inferred.

The first parser incorrectly assumed every `gh --paginate` serialized array
contained at most100 records. Both GETs had already succeeded; the installed CLI
combined destination pages into one172-record array. The [original refusal](FIRST-READBACK-REFUSAL.json)
is preserved. Recovery used the same cached bytes with **zero repeated network
requests**, not a replacement acquisition.

Comments/timelines were **not reacquired**: unchanged counts/fields are not proof
of unchanged discussion bodies or a fresh full-history archive. Prior discussion
archives remain available. No source repository modification, issue creation/
closure, release/package/deployment/Pages/main integration or readiness waiver.
