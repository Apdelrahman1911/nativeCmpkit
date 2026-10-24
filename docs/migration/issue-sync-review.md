# Independent offline review of issue synchronization

Reviewed2026-10-24, before the lead's authorized remote application. This review
used **no network requests, credential access or actual GitHub mutations**. The
only full-script invocation against project data omitted `--apply` and generated
local drafts/plan. Fixture invocations with `--apply` replace every GitHub call,
sleep and subprocess entry point with controlled offline fakes.

## Result and evidence

The corrected script passes **25 offline unittest cases**. The current plan has
**170 unique keys:164 audit findings and6 standalone historical topics**. All170
draft bodies match their source finding/decision renderings and stored hashes.
All436 cited baseline locations were checked against preserved Git objects
(including one binary font without fictitious line anchors). The six historical
items' author, ID/node ID, dates, URL and observed state match the raw issue archive.

The plan contains37 High,107 Medium and26 Low issues, including three intentional
initial closures (`BUILD-008`, `BUILD-009`, `BUILD-011`) with migration-remediation
evidence. Maximum current body size is7,358 UTF-8 bytes; maximum title length127
characters. No current duplicate-key or source/metadata correspondence error was
found. This is evidence for a **supervised, single-process application**, not proof
that GitHub has accepted any issue or that every runtime finding was reproduced.

- Script: [`scripts/migration/sync_github_issues.py`](../../scripts/migration/sync_github_issues.py)
- Fixtures: [`test_sync_github_issues.py`](../../scripts/migration/test_sync_github_issues.py)
- Inspected test output: [`issue-sync-unittests.log`](../testing/evidence/issue-sync-unittests.log)
- Script/test hashes, counts and validation result: [`issue-sync-review.json`](../testing/evidence/issue-sync-review.json)
- Local plan: [`docs/audit/issue-plan.json`](../audit/issue-plan.json)

Reproduce the offline tests:

```sh
python3 -m unittest discover -s scripts/migration -p test_sync_github_issues.py -v
```

## Problems corrected during review

The initial reviewed script SHA256 was
`90396c566eff14888b25631dea0098deefd4ce120dac9a6b51fb84cfafbebfc2`.
These were migration-tool defects, corrected before the intended application,
not additional legacy library findings. The lead implemented the main safety
changes; the reviewer then received explicit authority for the small destination,
missing-marker and original-number fixes.

| Initial behavior | Corrected behavior / regression coverage |
|---|---|
| Every rerun reset issue state to the generated plan, potentially reopening an owner-closed issue | Initial remediation closure only for a newly created issue or its recorded interrupted initial-close operation; completed owner close/reopen choices remain untouched |
| Full label replacement discarded unrelated human labels | `merge_labels` owns only documented audit/priority/area/evidence classifications and preserves other labels |
| Any matching marker anywhere in a remote body could identify an issue | `managed_key` requires one valid marker on the first line; ambiguous/quoted/multiple markers fail closed; PRs are ignored and another author's managed marker is refused |
| Changed remote titles/bodies were overwritten | Existing generated content can be updated only when it still matches a prior receipt, or already exactly matches the desired rendering; human edits require reconciliation |
| Rebuilding the receipt could discard unprocessed earlier entries after interruption | Atomically replaced JSON receipt preserves prior unprocessed entries, records successful issue creation, and tracks pending initial closure |
| Same-topic historical entries used the first input item's issue number as identity; reordering could create duplicates, later originals were missing from the body | Stable `upstream-topic:<20 hex SHA256(topic)>` keys, deterministic grouping, all original provenance/assessments retained, highest group priority, repeated original numbers/final-key collisions rejected |
| A removed marker on an already receipted issue was treated as a new item | Missing previous marker fails closed instead of creating a replacement/duplicate; issue-number binding is also checked |
| Owner/fork checks alone accepted a redirect to another repository owned by the same account | Canonical `full_name` must match the fixed destination (case-insensitive as GitHub identities are), in addition to independent ownership and authenticated-owner checks |
| A regex extracted issue numbers from every referenced repository | `calf_upstream_numbers` only maps `MohamedRejeb/Calf` issue/PR URLs. Actual plan correction: `BUILD-012` retains the zbus#2043 URL as evidence but no longer mislabels2043 as an original Calf issue |

The six obsolete number-keyed local drafts were replaced before any corresponding
remote creation in this migration. Accepting legacy marker syntax does **not**
automatically associate an old number-keyed issue with a new topic key. If such
legacy remote issues/receipts exist in another future run, reconcile that migration
explicitly rather than assuming automatic adoption.

## Fixture coverage

- Default dry-run makes no API request; rendered body hashes and immutable encoded
  source links are exact; binary source links omit `#L` anchors.
- Duplicate finding IDs, invalid/repeated historical identities and oversized
  bodies reject; covered/nonactionable historical requests are not recreated.
- Grouped topics are independent of input order and keep their identity when
  membership grows; every original URL/author remains visible.
- First simulated apply creates once; an identical rerun performs no mutations.
  Pagination, marked-PR exclusion, duplicate markers, destination/author binding
  and delay clamping are exercised.
- Owner labels/lifecycle survive; managed generator changes update from known
  receipts; human-edited body/title, removed marker and changed issue number reject.
- A simulated POST that commits remotely but loses its response is **not retried
  in the same run**; a fresh run reconciles by marker without another POST.
- Initial closed findings close once; manual reopening after completion survives.
  A successful POST followed by interruption preserves pending-close receipt;
  a close that commits but loses its response reconciles without a second PATCH.
- Interrupted updates retain unprocessed earlier receipts rather than truncating
  the map. Atomic rename is exercised at the file level, not a power-loss test.

## Cross-area deduplication assessment

The finding titles/root causes and high-overlap source boundaries were compared;
this check does not replace the individual implementation reviews. Related items
below need cross-references, not blind merging:

| Related items | Why the root causes/remedies remain distinct |
|---|---|
| NAV-013 / IO-021 | Sample export job concurrency, bounds, errors and image pipeline versus library/Coil eager reads and scheduling contract. NAV evidence explicitly cross-references IO-021 |
| NAV-015 / PERM-024 | Sample Call menu lacks CALL_PHONE; permission documentation separately promises all-files behavior that WriteStorage does not implement. Broad declarations are context in NAV, not a second all-files issue |
| NAV-014 / IO-009,IO-021 | Synchronous sample count loop lacks cancellation checks versus browser FileReader failure/cancellation and eager-buffering implementation |
| NAV-010 / UI-029 | Font glyph Text semantics versus missing actionable slider/switch semantics; different components and acceptance tests |
| NATIVE-033 / PERM-007 | Caller-side mobile operation thread affinity versus permission callback dispatch, disposal and status-update order. A future shared policy can help both but does not make their fixes interchangeable |
| UI-012 / UI-015 | Presented UIAlertController retains old callbacks even when input changes; properties helper independently ignores new textFields when remembering. Fixing only one layer does not repair the other |
| Upstream#471 / UI-035 | Remaining native-bar typography/appearance capability versus already-accepted button/slider/switch parameters dropped by implementations |
| Upstream#34 / camera-module findings | Camera capture originating inside WKWebView is an unverified historical report, not a current Calf camera-launcher reproduction |
| Upstream#343 / NATIVE-027 | Requested native file-preview API versus a share fallback that opens files; do not present the unsafe/incorrect fallback as fulfillment of preview support |

No additional exact same-root/same-remedy issue requiring removal was found in
these overlapping groups. Broader lifecycle, callback, thread-affinity and bounded
I/O themes should remain linked in the roadmap rather than erase platform-specific
implementation evidence.

## Operating limits and application precautions

1. **Single writer only.** There is no inter-process remote lock or conditional
   HTTP ETag update. Concurrent sync processes could race creation, and an owner
   edit made after the read snapshot but before PATCH is not protected by the
   offline content comparison. Do not run another sync or edit managed fields
   during the supervised batch; stop/reconcile if that coordination changes.
2. **Errors stop, not automatically retry POST.** Read the receipt/remote state
   before a new explicit invocation. Unknown failures are not evidence of failed
   creation. A pending initial-close receipt represents an interrupted authorized
   action; reconcile it explicitly if the owner's intention has changed.
3. **Partial progress is possible.** Missing classification labels can be created
   before a later issue-marker/content conflict is discovered; earlier completed
   items and receipts remain. A failed run is not a transaction rollback.
4. **External conditions remain external.** Fakes do not prove token scopes,
   GitHub rate limits, API consistency, actual response availability or delivery.
   Current fields/sizes were checked, but future larger grouped titles/bodies need
   fresh plan validation. Never interpret a rendered plan or this report as a
   successfully migrated issue list.
5. **The fixed destination is intentional.** The tool cannot mutate upstream or
   publish packages/releases via its implemented endpoints. Owner authorization
   to execute the migration remains separate from this offline verification.
